from native_restore_only_scope_contract import pre_native_restore_only
# coding: utf-8
"""Source/C/Mach-O contracts only; does not execute Swift or Core Data."""
import hashlib,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment

class NativeHistoryRestoreContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-31'
        cls.proof=json.loads((cls.phase/'native-history-restore-contract.json').read_text())
        cls.store=(ROOT/'replica/Sources/PastoCore/ClipboardStore.swift').read_text()
        cls.persistence=pre_native_restore_only((ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text())
        cls.mutate=body(cls.store,'private func mutateInTransaction<T>(historyAction: Bool = false,')
        cls.prepare=body(cls.persistence,'func prepareHistoryItems(')
        cls.restore=body(cls.persistence,'func restoreHistoryItems(')
        cls.commit=body(cls.persistence,'func commit<T>(previous: StoreState?, deletingItemIDs: [UUID] = [],')
        cls.original=original_fragment((ROOT/'decompiled/Paste/part-0275.c').read_text(),'100361ec0')

    def test_original_fragments_and_binary_are_bound(self):
        for r in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        binary=self.proof['binary'];raw=(ROOT/binary['path']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),binary['sha256'])
        for r in self.proof['machine_ranges']:
            chunk=raw[r['file_offset']:r['file_offset']+r['length']]
            self.assertEqual(chunk.hex(),r['hex'])
            self.assertEqual(hashlib.sha256(chunk).hexdigest(),r['sha256'])

    def test_original_loop_interleaves_date_and_native_setter_before_cleanup(self):
        order=['FUN_100364108()','Date::init()','Date::_bridgeToObjectiveC','objc_stub::setTimestamp_(self,pNVar5)',
               'while (IVar11 != IVar12)','FUN_1003293c4()','FUN_100363810()','FUN_1003646ec()',
               'FUN_100328bb4(ppuVar8,0,IVar11)','objc_stub::FUN_100c08be0(IVar11,ppuVar8,1)']
        indexes=[self.original.index(s)for s in order];self.assertEqual(indexes,sorted(indexes))
        self.assertEqual([r['symbol']for r in self.proof['sdk_imports']],
                         ['_$s10Foundation4DateVACycfC','_$s10Foundation4DateV19_bridgeToObjectiveCSo6NSDateCyF'])
        self.assertEqual(self.proof['selector']['name'],'setTimestamp:')

    def test_original_reverse_swaps_both_ends_without_deduplication(self):
        reverse=original_fragment((ROOT/'decompiled/Paste/part-0275.c').read_text(),'100364108')
        for token in ['uVar10 >> 1','uVar10 - (lVar11 + -3)',
                      '*(ulong *)(uVar12 + lVar11 * 8) = uVar9','*(ulong *)(uVar12 + uVar1 * 8 + 0x20) = uVar3']:
            self.assertIn(token,reverse)
        self.assertIn('return try ids.map { id in',self.prepare)
        self.assertNotIn('Set(',self.prepare)
        self.assertNotIn('Set(',self.restore)
        self.assertNotIn('sorted(',self.restore)

    def test_invalid_or_deleted_targets_fail_before_native_changes(self):
        order=['let result = try change(&state, transaction)','let available = Set(state.items.filter { !$0.isDeleted }.map(\\.id))',
               'guard restoringItemIDs.allSatisfy({ available.contains($0) })',
               'throw ClipboardStoreError.itemNotFound','try validate(state)','try lists.synchronize(',
               'transaction.repository.prepareHistoryItems(restoringItemIDs)']
        positions=[self.mutate.index(t)for t in order];self.assertEqual(positions,sorted(positions))

    def test_existing_targets_reuse_handles_and_unsaved_duplicate_uses_one_handle(self):
        self.assertIn('try fetchObjects("Item", keys: ids.map(\\.uuidString))',self.prepare)
        order=['if let object = objects[id.uuidString] { return (id: id, object: object) }',
               'NSEntityDescription.insertNewObject(forEntityName: "Item", into: context)',
               'try context.obtainPermanentIDs(for: [object])','object.setValue(id.uuidString, forKey: "key")',
               'objects[id.uuidString] = object','return (id: id, object: object)']
        positions=[self.prepare.index(t)if n!=5 else self.prepare.rindex(t)for n,t in enumerate(order)]
        self.assertEqual(positions,sorted(positions))
        self.assertNotIn('NSManagedObjectContext(',self.prepare)

    def test_reverse_date_setter_occurs_inside_single_loop_not_after_materialization(self):
        order=['for (id, object) in targets.reversed()','let timestamp = Date()',
               'object.setValue(timestamp, forKey: "timestamp")','updates.append((id: id, timestamp: timestamp))']
        positions=[self.restore.index(t)for t in order];self.assertEqual(positions,sorted(positions))
        self.assertEqual(self.restore.count('Date()'),1)
        self.assertNotIn('Date()',body(self.store,'func recordRestoredItems(_ ids: [UUID])'))
        self.assertNotIn('Date()',self.mutate)
        for token in ['.async','context.save','context.reset','performAndWait','try?']:
            self.assertNotIn(token,self.restore+self.prepare)

    def test_native_timestamp_consumes_same_transaction_before_cleanup_and_save(self):
        order=['let targets = try preparedRestore?.native.targets ?? transaction.repository.prepareHistoryItems(restoringItemIDs)',
               'for update in transaction.repository.restoreHistoryItems(targets)',
               'state.items[index].createdAt = update.timestamp','state.items[index].updatedAt = update.timestamp',
               'state.items[index].isInHistory = true','expireHistory(&state, capacity: capacity)',
               'lists.refreshHistoryAfterOperation =','return (state: state, result: result)','publish(state)']
        positions=[self.mutate.index(t)for t in order];self.assertEqual(positions,sorted(positions))
        order=['let transaction = preparedTransaction ?? Transaction(context: context)','try context.performAndWait',
               'let outcome = try operation(transaction)','try transaction.repository.update(state.items',
               'try transaction.repository.lists.refreshHistoryIfNeeded()','if context.hasChanges','try context.save()']
        positions=[self.commit.index(t)for t in order];self.assertEqual(positions,sorted(positions))

    def test_generic_commit_skips_same_timestamp_but_keeps_nil_history_removal(self):
        self.assertIn('let timestamp = item.isInHistory ? item.createdAt : nil',self.commit)
        self.assertIn('if old.flatMap({ $0.isInHistory ? $0.createdAt : nil }) != timestamp,\n'
                      '                       (object.value(forKey: "timestamp") as? Date) != timestamp {',self.commit)
        setter=body(self.commit,'(object.value(forKey: "timestamp") as? Date) != timestamp')
        self.assertIn('object.setValue(timestamp, forKey: "timestamp")',setter)
        self.assertNotIn('Date()',setter)
        old=body((self.phase/'before/replica/Sources/PastoCore/ClipboardPersistence.swift').read_text(),
                 'func commit<T>(previous: StoreState?, deletingItemIDs: [UUID] = [],')
        current_checkpoint=(ROOT/'.local/p0-repair/phase-34/before/replica/Sources/PastoCore/ClipboardPersistence.swift').read_text()
        checkpoint_commit=body(current_checkpoint,'func commit<T>(previous: StoreState?, deletingItemIDs: [UUID] = [],')
        reconstructed=checkpoint_commit.replace(',\n                       (object.value(forKey: "timestamp") as? Date) != timestamp','',1)
        self.assertEqual(reconstructed,old)
        checkpoint=(self.phase/'before/replica/Sources/PastoCore/ClipboardPersistence.swift').read_text()
        reconstructed=current_checkpoint
        for signature in ['func prepareHistoryItems(', 'func restoreHistoryItems(']:
            method=body(reconstructed,signature)
            start=reconstructed.index('        '+signature)
            end=reconstructed.index(method,start)+len(method)
            reconstructed=reconstructed[:start]+reconstructed[end+2:]
        reconstructed=reconstructed.replace(',\n                       (object.value(forKey: "timestamp") as? Date) != timestamp','',1)
        self.assertEqual(reconstructed,checkpoint)

    def test_empty_input_returns_before_transaction_and_current_facade_is_explicit(self):
        restore=body(self.store,'func recordRestoredItems(_ ids: [UUID])')
        self.assertLess(restore.index('guard !ids.isEmpty else { return }'),
                        restore.index('try mutate(historyAction: true, restoringItemIDs: ids)'))
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertGreater(len(self.proof['retained_partial_contracts']),1)
        before=self.phase/'before/replica/Sources/PastoCore'
        for name in ['ClipboardListPersistence.swift','Pasteboard.swift']:
            current=ROOT/'replica/Sources/PastoCore'/name
            if name=='Pasteboard.swift':current=ROOT/'.local/p0-repair/phase-34/before/replica/Sources/PastoCore'/name
            if name == 'ClipboardListPersistence.swift':
                current = ROOT / '.local/p0-repair/phase-40/before/replica/Sources/PastoCore' / name
            self.assertEqual(current.read_bytes(),(before/name).read_bytes())

    def test_source_case_exposes_old_interleaving_difference(self):
        case=self.proof['source_case'];self.assertEqual(case['kind'],'source_contract_case_not_runtime_reproduction')
        self.assertEqual(case['original_events'],case['after_events'])
        self.assertNotEqual(case['original_events'],case['before_events'])
        self.assertLess(case['before_events'].index('cleanup'),case['before_events'].index('set A'))
        self.assertLess(case['after_events'].index('set A'),case['after_events'].index('cleanup'))
        # Source-only finite domain: repeated targets share the native object and
        # the last reversed occurrence supplies the final timestamp, without Set.
        writes=[(target,n)for n,target in enumerate(reversed(['A','B','A']),1)]
        self.assertEqual(writes,[('A',1),('B',2),('A',3)])
        self.assertEqual(dict(writes),{'A':3,'B':2})

if __name__=='__main__':unittest.main()
