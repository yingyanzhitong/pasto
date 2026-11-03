# coding: utf-8
"""Original/source contracts for capture checksum lookup; no Swift/app execution."""
import hashlib,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from native_capture_lookup_scope_contract import pre_native_capture_lookup
from snapshot_read_scope_contract import body
from test_p0_repair_checksum_routing import original_fragment

class CaptureChecksumLookupContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-32'
        cls.proof=json.loads((cls.phase/'capture-checksum-contract.json').read_text())
        cls.store=pre_native_capture_lookup((ROOT/'replica/Sources/PastoCore/ClipboardStore.swift').read_text())
        cls.add=body(cls.store,'func addWithInsertionResult(')
        cls.lookup=body(cls.add,'if let i = state.items.firstIndex(where:')
        cls.capture=body(cls.lookup,'if recordCapture')
        cls.persistence=(ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text()

    def test_original_checksum_query_is_bound_and_uses_checksum_predicate(self):
        for r in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        original=original_fragment((ROOT/'decompiled/Paste/part-0258.c').read_text(),'1003214c8')
        order=['FUN_10032362c()','FUN_1003216bc()','if (lVar1 == 0)',
               '0x6d75736b63656863','FUN_100328950(ppuVar4,0,param_2)']
        positions=[original.index(t)for t in order];self.assertEqual(positions,sorted(positions))
        self.assertEqual((0x6d75736b63656863).to_bytes(8,'little'),b'checksum')
        self.assertIn('ppuVar4 = (undefined **)0x0',original)

    def test_capture_compares_saved_checksum_and_rejects_nil_without_fallback(self):
        self.assertIn('guard let checksum else { return false }',self.capture)
        self.assertIn('return previous.nativeChecksum == checksum',self.capture)
        self.assertLess(self.capture.index('guard let checksum'),self.capture.index('previous.nativeChecksum'))
        for token in ['previous.payloads','knownPasteboardChecksum','try?','hasSamePasteboardRepresentations','plainText','nativeIdentifier']:
            self.assertNotIn(token,self.capture)
        self.assertLess(self.lookup.index('if recordCapture'),self.lookup.index('if let checksum'))

    def test_real_capture_computes_new_checksum_throwing_before_lookup_and_overrides_incoming_metadata(self):
        operation=self.add[self.add.index('return try mutateInTransaction('):]
        preflight=body(operation[:operation.index('if let sourceApplication')],'if recordCapture')
        order=['checksum = try Self.knownPasteboardChecksum(from: item.payloads)',
               'guard item.nativeIdentifier != nil || checksum != nil','item.nativeChecksum = checksum']
        indexes=[preflight.index(t)for t in order];self.assertEqual(indexes,sorted(indexes))
        self.assertNotIn('try?',preflight)
        self.assertNotIn('checksum = item.nativeChecksum',preflight)
        self.assertLess(self.add.index('return try mutateInTransaction('),self.add.index('checksum = try Self.knownPasteboardChecksum'))
        self.assertLess(self.add.index('checksum = try Self.knownPasteboardChecksum'),self.add.index('state.items.firstIndex(where:'))
        pasteboard=(ROOT/'replica/Sources/PastoCore/Pasteboard.swift').read_text()
        capture=body(pasteboard,'func captureWithInsertionResult(')
        self.assertIn('sourceApplication: sourceApplication, recordCapture: true',capture)
        known=body(pasteboard,'public nonisolated static func knownPasteboardChecksum(')
        self.assertIn('return OriginalPasteboardChecksums.f_1003216bc(items, kind: kind)',known)
        self.assertNotIn('kind != .unknown',known)

    def test_persisted_candidate_field_is_read_and_written_without_rederiving_at_read(self):
        item=body(self.persistence,'private func item(_ object: NSManagedObject)')
        self.assertIn('item.nativeChecksum = object.value(forKey: "nativeChecksum") as? String',item)
        self.assertNotIn('knownPasteboardChecksum',item)
        commit=body(self.persistence,'func commit<T>(previous: StoreState?, deletingItemIDs: [UUID] = [],')
        checksum=body(commit,'if old?.nativeChecksum != item.nativeChecksum')
        self.assertIn('object.setValue(item.nativeChecksum, forKey: "nativeChecksum")',checksum)

    def test_only_capture_candidate_gate_changed_and_value_import_compatibility_is_preserved(self):
        checkpoint=(self.phase/'before/replica/Sources/PastoCore/ClipboardStore.swift').read_text()
        gate='''                if recordCapture {
                    guard let checksum else { return false }
                    return previous.nativeChecksum == checksum
                }
'''
        current=(ROOT/'.local/p0-repair/phase-34/before/replica/Sources/PastoCore/ClipboardStore.swift').read_text()
        self.assertEqual(self.store.count(gate),1)
        self.assertEqual(current.replace(gate,'',1),checkpoint)
        remainder=self.lookup.replace('if recordCapture '+self.capture,'',1)
        before=body(body(checkpoint,'func addWithInsertionResult('),'if let i = state.items.firstIndex(where:')
        self.assertEqual(''.join(remainder.split()),''.join(before.split()))
        for p in self.proof['current_sources']:
            if not p.endswith('ClipboardStore.swift'):
                current_path=ROOT/p
                if p.endswith('ClipboardPersistence.swift') or p.endswith('Pasteboard.swift'):
                    current_path=ROOT/'.local/p0-repair/phase-34/before'/p
                current=current_path.read_bytes()
                if p.endswith('OriginalPasteboard.swift'):
                    current=current.replace(b'@objc(_TtC9PasteCore14PasteboardItem)\n',b'',1)
                if p.endswith('OriginalPasteboardArchive.swift'):
                    for name in ['PastoCore.OriginalPasteboardItem','_TtC9PastoCore22OriginalPasteboardItem']:
                        current=current.replace(('            decoder.setClass(OriginalPasteboardItem.self, forClassName: "'+name+'")\n').encode(),b'',1)
                self.assertEqual(current,(self.phase/'before'/p).read_bytes())

    def test_hit_keeps_existing_identity_and_no_match_retains_normal_creation(self):
        self.assertIn('result = (i, false)',self.add)
        self.assertIn('state.items.append(item)',self.add)
        self.assertIn('result = (state.items.count - 1, true)',self.add)
        self.assertIn('return (state.items[result.index].id, result.isNew)',self.add)
        self.assertNotIn('state.items[i].id =',self.add)
        self.assertNotIn('state.items[i].title =',self.add)
        self.assertNotIn('state.items[i].sourceDevice =',self.add)
        self.assertFalse(self.proof['full_function_migration_verified'])
        cases=self.proof['source_cases'];self.assertEqual(len(cases),2)
        for case in cases:
            self.assertEqual(case['original'],case['after'])
            self.assertNotEqual(case['original'],case['before'])

if __name__=='__main__':unittest.main()
