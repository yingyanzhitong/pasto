from native_restore_writer_scope_contract import pre_native_restore_writer
"""Native owner type gate across shared value readers; static only."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from native_search_content_scope_contract import pre_native_search_content
from native_stack_rendering_scope_contract import pre_native_stack_rendering
from test_offline_p0_contracts import body
from native_owner_type_scope_contract import CHANGES,pre_native_owner_type

class NativeOwnerTypeContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-113';cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.proof=json.loads((cls.phase/'native-owner-type-contract.json').read_text());cls.p='replica/Sources/PastoCore/ClipboardPersistence.swift';cls.source=(ROOT/cls.p).read_text();cls.item=body(cls.source,'nonisolated static func item(_ object:');cls.ns={};exec((ROOT/cls.proof['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.ns)
    def test_two_original_fragments_and_binary_inputs_current(self):
        for r in self.proof['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for r in [self.proof['binary'],self.proof['decoder']]:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_three_real_owner_and_type_calls_bound(self):
        self.assertEqual(len(self.proof['ARM_calls']),3)
        for r in self.proof['ARM_calls']:
            pc=int(r['address'],16);data=self.ns['read'](pc,4);self.assertEqual(data.hex(),r['bytes']);w=int.from_bytes(data,'little');self.assertEqual(w&0x7c000000,0x14000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(pc+4*d,int(r['target'],16))
    def test_original_nil_and_exact_type2_branches_bound(self):
        self.assertEqual(len(self.proof['ARM_words']),5)
        for r in self.proof['ARM_words']:self.assertEqual(self.ns['read'](int(r['address'],16),4).hex(),r['bytes'])
    def test_owner_type_precedes_identifier_and_membership_projection(self):
        s=self.item;tokens=['if let list = object.value(forKey: "list")','(list.value(forKey: "rawType") as? NSNumber)?.int64Value == 2','let identifier = list.value(forKey: "identifier")','let owner = UUID(uuidString: identifier)','item.pinboardOwnerID = owner','item.pinboardIDs.insert(owner)'];cursor=0
        for t in tokens:cursor=s.index(t,cursor)+len(t)
        self.assertEqual(s.count('list.value(forKey: "rawType")'),1);self.assertIn('else { item.pinboardOwnerID = nil }',s)
    def test_legacy_memberships_not_cleared_or_rewritten_by_this_gate(self):
        s=self.item;self.assertIn('var item = try Self.decode(ClipboardItem.self, object)',s);self.assertIn('item.pinboardIDs.insert(owner)',s)
        for t in ['pinboardIDs =','pinboardIDs.removeAll','pinboardIDs.remove(','setValue(','delete(','save(','reset(','rollback(']:self.assertNotIn(t,s)
    def test_search_record_projection_and_value_projection_use_same_type_condition(self):
        p=ROOT/'replica/Sources/PastoCore/ClipboardSnapshotReader.swift';s=body(p.read_text(),'func searchIndexRecords(');self.assertIn('(list?.value(forKey: "rawType") as? NSNumber)?.int64Value == 2',s);self.assertIn('int64Value == 2',self.item)
    def test_all_shared_consumers_and_sources_unchanged(self):
        self.assertEqual(len(self.proof['unchanged_consumer_methods']),7);self.assertEqual(len(self.proof['shared_sources']),4)
        for r in self.proof['unchanged_consumer_methods']:self.assertEqual(hashlib.sha256(body(pre_native_search_content((ROOT/r['path']).read_text()),r['symbol']).encode()).hexdigest(),r['sha256'])
        for p,h in self.proof['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_native_stack_rendering((ROOT/p).read_text()).encode()).hexdigest(),h);self.assertEqual(h,self.base['production'][p])
    def test_one_hunk_exact_reverse_preserves_all_247_production_files(self):
        self.assertEqual(len(CHANGES),1)
        for p,h in self.base['production'].items():
            data=(ROOT/p).read_bytes();data=pre_native_owner_type(data.decode()).encode()if p.endswith('.swift')else data;self.assertEqual(hashlib.sha256(data).hexdigest(),h)
        for p,h in self.proof['current_sources'].items():self.assertEqual(hashlib.sha256(pre_native_restore_writer((ROOT/p).read_text()).encode()).hexdigest(),h)
    def test_reverse_is_idempotent_on_historical_item_reader(self):
        old=(self.phase/'before'/self.p).read_text();self.assertEqual(pre_native_owner_type(self.source),old);self.assertEqual(pre_native_owner_type(old),old)
    def test_compatibility_full_reader_and_function_count_not_falsely_completed(self):
        self.assertEqual(self.proof['new_records'],0);self.assertFalse(self.proof['full_function_migration_verified']);self.assertFalse(self.proof['runtime_executed']);self.assertEqual(len(self.proof['remaining']),3);self.assertIn('Legacy valid archive memberships',self.proof['remaining'][0]);self.assertIn('Do not remove compatibility blob writes',self.proof['remaining'][1])

if __name__=='__main__':unittest.main()
