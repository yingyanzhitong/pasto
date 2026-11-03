# -*- coding: utf-8 -*-
"""Finite normal-domain history, zero-match and multi-item content evidence checks."""
import hashlib
import json
import struct
import subprocess
import unittest
from collections import Counter

from test_offline_p0_contracts import ROOT, body
from test_p0_p1_review_round2 import digest, fragment


class P0P1ReviewRound18(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((ROOT/'reports/replica/p0-p1-review-round18.json').read_text())
        cls.prior=json.loads((ROOT/'reports/replica/p0-p1-review-round17.json').read_text())
        cls.rows={x['function_id']:x for x in cls.report['records']}
        cls.proof=json.loads((ROOT/cls.report['static_proof']['path']).read_text())
        cls.binary=(ROOT/cls.proof['binary_path']).read_bytes()
        cls.index={x['address']:x for x in json.loads((ROOT/'reports/Paste/function-index.json').read_text())}

    def native(self,a):return fragment(a,self.index[a]['file'])
    def offset(self,a):
        for s in self.proof['segments']:
            if s['vmaddr']<=a<s['vmaddr']+s['filesize']:return s['fileoff']+a-s['vmaddr']
        self.fail(hex(a))
    def word(self,a):return struct.unpack_from('<I',self.binary,self.offset(a))[0]
    def pointer(self,a):return 0x100000000+(struct.unpack_from('<Q',self.binary,self.offset(a))[0]&((1<<36)-1))
    def relative(self,a):return a+struct.unpack_from('<i',self.binary,self.offset(a))[0]
    def string(self,a):
        o=self.offset(a);return self.binary[o:self.binary.index(b'\0',o)].decode()
    def branch(self,a):
        v=self.word(a);self.assertEqual(v>>26,0b100101);imm=v&0x3ffffff
        return a+(imm-(1<<26)if imm&(1<<25)else imm)*4

    def test_scope_stays_646_and_only_12_previously_unknown_addresses_are_revisited(self):
        old={x['function_id']:x for x in self.prior['records']};changed=set(self.report['round_delta']['reviewed_function_ids'])
        self.assertEqual(set(old),set(self.rows));self.assertEqual(len(self.rows),646)
        self.assertEqual(len(changed),12);self.assertEqual(self.report['round_delta']['scope_added'],0)
        self.assertEqual(self.report['scope_manifest_sha256'],self.prior['scope_manifest_sha256'])
        for fid in old:
            if fid in changed:self.assertEqual(old[fid]['status'],'unclosed')
            else:self.assertEqual(old[fid],self.rows[fid])
        self.assertEqual(self.report['round_delta']['newly_resolved'],4)
        self.assertFalse(any(x['full_function_migration_verified']for x in self.rows.values()))
        self.assertIsNone(self.report['full_priority_completion_percent'])

    def test_source_fragments_literal_consumers_and_new_static_proof_have_matching_hashes(self):
        for p,h in self.report['source_inputs'].items():self.assertEqual(digest(p),h,p)
        self.assertEqual(digest(self.report['static_proof']['path']),self.report['static_proof']['sha256'])
        self.assertEqual(hashlib.sha256(self.binary).hexdigest(),self.proof['binary_sha256'])
        for fid in self.report['round_delta']['reviewed_function_ids']:
            row=self.rows[fid]
            for ref in [dict(row['original'],function_id=fid)]+row.get('supporting_original_fragments',[]):
                a=ref.get('address')or ref['function_id'].split(':')[1]
                self.assertEqual(hashlib.sha256(fragment(a,ref['path']).encode()).hexdigest(),ref['sha256'])
            for ref in row['current_references']:
                self.assertEqual(digest(ref['path']),ref['sha256'])
                self.assertIn(ref['symbol'],(ROOT/ref['path']).read_text())
        for part in ['history_preference','multi_text']:
            for value in self.proof[part].values():
                if isinstance(value,dict)and 'bytes'in value:
                    start=self.offset(int(value['address'],16));encoded=bytes.fromhex(value['bytes'])
                    self.assertEqual(self.binary[start:start+len(encoded)],encoded)

    def test_clear_history_normal_domain_preserves_grouped_items_and_removes_only_history_orphans(self):
        native=self.native('0x100363004');delete=self.native('0x1003646ec')
        self.assertIn('if (IVar6 == 1)',native)
        self.assertIn('objc_stub::setTimestamp_((ID)puVar4,0)',native)
        self.assertIn('IVar6 = objc_stub::list((ID)puVar4)',native)
        self.assertIn('if (IVar6 == 0)',native);self.assertIn('FUN_1003646ec(puVar10)',native)
        self.assertIn('objc_stub::deleteObject_(self_00,self)',delete)
        current=(ROOT/'replica/Sources/PastoCore/ClipboardStore.swift').read_text()
        clear=body(current,'public func eraseHistory() throws')
        self.assertIn('state.items.removeAll { $0.isInHistory && $0.pinboardIDs.isEmpty }',clear)
        self.assertIn('state.items[i].isInHistory = false',clear)
        persistence=(ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text()
        self.assertIn('object.setValue(item.createdAt, forKey: "timestamp")',persistence)
        self.assertIn('object.setValue(item.isInHistory, forKey: "inHistory")',persistence)
        row=self.rows['Paste:0x100024274'];self.assertEqual(row['status'],'local_contract_consistent')
        self.assertIn('所有相关历史记录均isDeleted==false',row['contract'])
        self.assertIn('当前SQLite.timestamp仍保存createdAt',row['contract'])
        self.assertTrue(any('soft-deleted'in x for x in row['coverage_boundaries']['not_verified']))
        for fid in ['Paste:0x1003594e4','Paste:0x100368250']:self.assertEqual(self.rows[fid]['status'],'unclosed')

    def test_successful_nonempty_zero_match_query_is_real_nil_producer_not_initial_nil_or_sink_optional(self):
        producer=self.native('0x100360808');mapper=self.native('0x100355a98')
        self.assertIn('lVar11 = *(long *)(param_1 + 0x10)',producer)
        self.assertIn('if (lVar11 == 0)',producer);self.assertIn('local_a0[0] = 0',producer)
        self.assertIn('Combine::CurrentValueSubject::send',producer)
        self.assertIn('if (*param_2 == 0)',mapper);self.assertIn('PTR___swiftEmptySetSingleton',mapper)
        self.assertIn('Combine::Just::init',mapper)
        query=(ROOT/'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text()
        replace=body(query,'private func replaceQuery(with nodes: [OriginalSearchQueryNode])')
        self.assertLess(replace.index('identifiers = found'),replace.index('onUpdate?()'))
        current=(ROOT/'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
        self.assertIn('searchIndex.identifiers.contains(item.id)',current)
        normalize=body(current,'func normalizeSelection()')
        self.assertIn('selection.contains($0) && visible.contains($0)',normalize)
        self.assertIn('let first = items.first',normalize)
        self.assertEqual(self.rows['Paste:0x100355874']['status'],'local_contract_consistent')
        for fid in ['Paste:0x100223430','Paste:0x1002234e0','Paste:0x10022be98']:
            self.assertEqual(self.rows[fid]['status'],'unclosed')

    def test_history_actor_fields_and_preference_factory_are_bound_to_the_real_keypaths(self):
        proof=self.proof['history_actor'];m=int(proof['metadata'],16);n=self.pointer(m+0x40)
        self.assertEqual(n,int(proof['nominal'],16));self.assertEqual(self.string(self.relative(n+8)),'CDSearchIndexerDataSource')
        f=self.relative(n+16);size,count=struct.unpack_from('<HI',self.binary,self.offset(f)+10)
        vector=self.word(n+40)
        actual={self.string(self.relative(f+16+size*i+8)):struct.unpack_from('<Q',self.binary,self.offset(m+vector*8+i*8))[0]for i in range(count)}
        self.assertEqual(actual['_historyTokenData'],0x80);self.assertEqual(actual['historyToken'],0xb8)
        self.assertEqual(actual['context'],0x78);self.assertEqual(actual['coordinator'],0x70)
        self.assertEqual(self.relative(0x100c43274),0x1003707a8)
        self.assertEqual(self.relative(0x100c43278),0x100371394)
        self.assertEqual(self.relative(0x100c3ce20),0x1002ca5a0)
        self.assertIn('&DAT_100c43258',self.native('0x100370e8c'))
        self.assertIn('FUN_1002ca718',self.native('0x1002cbe9c'))
        self.assertIn('&DAT_100c3ce00',self.native('0x1002ca718'))
        self.assertIn('standardUserDefaults',self.native('0x1002cd57c'))

    def test_history_token_storage_partition_difference_is_identity_policy_not_brand_prefix(self):
        self.assertEqual(self.string(0x100da3390),'indexHistoryTokenData')
        factory=self.native('0x1003707a8')
        self.assertIn('FUN_1002ccc34(local_40,0xd000000000000015,0x8000000100da3370',factory)
        self.assertNotIn('coordinator',factory);self.assertNotIn('identifier(',factory)
        current=(ROOT/'replica/Sources/PastoCore/OriginalSearchHistory.swift').read_text()
        observe=body(current,'func observe(_ consume: @escaping ([OriginalSearchHistoryChange]) async throws -> Void) async')
        self.assertIn('persistentStores.first?.identifier',observe)
        self.assertIn('"pasto.search.history-token." + $0',observe)
        self.assertIn('guard let key else { return }',observe)
        # Derived key-domain example, not a live UserDefaults/Core Data test.
        fixed=self.proof['history_preference']['key']
        self.assertEqual([fixed for _ in ['store-a','store-b']],[fixed,fixed])
        self.assertNotEqual('pasto.search.history-token.store-a','pasto.search.history-token.store-b')
        row=self.rows['Paste:0x10036e4f4'];self.assertEqual(row['status'],'difference_confirmed')
        self.assertIn('runtime_token_invalidity_or_history_loss',row['coverage_boundaries']['not_verified'])

    def test_valid_multi_plain_text_items_are_joined_by_original_but_only_first_is_indexed_currently(self):
        original=self.native('0x1003724f0')
        self.assertIn('if (param_6 == 5) goto LAB_100373188;',original)
        self.assertIn('FUN_10037c9a8()',original)
        self.assertIn('separator.str = (char *)0x20',original)
        self.assertIn('LAB_100373804:\n  *param_1 = SVar65;',original)
        self.assertEqual(self.branch(0x1003731d4),0x10037c9a8)
        self.assertEqual(self.word(0x1003732a8),0x52800400)  # mov w0,#0x20 ASCII space
        self.assertEqual(self.word(0x1003732ac),0xd2fc2001)  # one-character small String header
        self.assertEqual(self.branch(0x1003732b4),0x100bf7a04)
        from macho_imports import parse_macho
        stub=parse_macho(ROOT/self.proof['binary_path'])['stubs']['0x100bf7a04']
        self.assertEqual(stub,self.proof['multi_text']['join_stub'])
        self.assertEqual(stub['symbol'],'_$sSKsSS7ElementRtzrlE6joined9separatorS2S_tF')
        capture=body((ROOT/'replica/Sources/PastoCore/Pasteboard.swift').read_text(),'func captureWithInsertionResult(pasteboard: NSPasteboard, sourceName: String, sourceBundleID: String?,')
        self.assertIn('capturedItems.lazy.compactMap { $0.f_10037c9a8() }.first',capture)
        self.assertIn('if capturedItems.count > 1',capture)
        self.assertIn('OriginalPasteboardDataCodec.f_10031a8e8(capturedItems',capture)
        current=(ROOT/'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text()
        self.assertIn('text = String(indexedText.prefix(5000))',current)
        self.assertIn('attributes.textContent = entry.text',current)
        value=self.proof['multi_text'];items=value['input_strings']
        self.assertEqual(' '.join(items),value['original_projection'])
        self.assertEqual(items[0],value['current_projection'])
        self.assertNotEqual(value['original_projection'],value['current_projection'])
        self.assertLess(len(' '.join(items)),5000)
        self.assertEqual(self.rows['Paste:0x1003724f0']['status'],'difference_confirmed')

    def test_counts_and_unchanged_production_ledger_head_and_unknown_cancel_gates(self):
        counts=Counter(x['status']for x in self.rows.values());self.assertEqual(dict(counts),self.report['outcomes'])
        self.assertEqual(646-counts['unclosed'],634)
        self.assertEqual(self.report['resolved_comparison_percent'],round(634/646*100,2))
        self.assertEqual(self.report['p0_component']['unclosed'],2)
        self.assertEqual(self.report['p1_additional_component']['unclosed'],10)
        for fid in ['Paste:0x1000403f4','Paste:0x100041190','Paste:0x1002e1b54']:
            self.assertEqual(self.rows[fid]['status'],'unclosed')
        before=json.loads((ROOT/'.local/p0-review/production-before.json').read_text())
        now={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in (ROOT/'replica/Sources').rglob('*')if p.is_file()}
        self.assertEqual(now,before);self.assertEqual(len(now),218)
        self.assertEqual(digest('replica/function-map.json'),self.report['function_map_sha256'])
        self.assertEqual(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'050e6878a5a52f96fe33aa40f48bb8a056cd0f05')
        for flag in ['production_source_edited','compiled','application_executed','committed','pushed']:self.assertFalse(self.report[flag])


if __name__=='__main__':unittest.main()
