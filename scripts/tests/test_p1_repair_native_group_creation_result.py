from native_restore_writer_scope_contract import pre_native_restore_writer
"""Native creation result/consumer/error continuation bindings; no Swift or framework execution."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from native_stack_rendering_scope_contract import pre_native_stack_rendering
from native_owner_type_scope_contract import pre_native_owner_type
from test_offline_p0_contracts import body
from native_group_creation_result_scope_contract import CHANGES,pre_native_group_creation_result

class NativeGroupCreationResultContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-112';cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.proof=json.loads((cls.phase/'native-group-creation-result-contract.json').read_text());cls.src={Path(p).stem:(ROOT/p).read_text()for p in cls.proof['current_sources']};cls.ns={};exec((ROOT/cls.proof['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.ns)
    def order(self,s,tokens):
        cursor=0
        for t in tokens:cursor=s.index(t,cursor)+len(t)
    def test_seventeen_original_fragments_and_reused_inputs_current(self):
        self.assertEqual(len(self.proof['original_fragments']),17)
        for r in self.proof['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for r in [self.proof['binary'],self.proof['decoder']]+self.proof['reused_evidence']:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_fourteen_actual_branches_bind_both_create_consumers(self):
        self.assertEqual(len(self.proof['ARM_calls']),14)
        for r in self.proof['ARM_calls']:
            pc=int(r['address'],16);data=self.ns['read'](pc,4);self.assertEqual(data.hex(),r['bytes']);w=int.from_bytes(data,'little');self.assertEqual(w&0x7c000000,0x14000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(pc+4*d,int(r['target'],16))
    def test_actual_Writing_plus8_factory_pointer_chain_bound(self):
        self.assertEqual([(r['address'],r['target'])for r in self.proof['pointers']],[('0x100eccd68','0x100eccda0'),('0x100eccda8','0x100368540')])
        for r in self.proof['pointers']:
            a=int(r['address'],16);v,c=self.ns['reachable_pointer'](a);self.assertEqual(c,r['chain']);self.assertEqual(self.ns['read'](a,8).hex(),r['bytes']);self.assertEqual(self.ns['base']+(v&((1<<36)-1)),int(r['target'],16))
    def test_eighteen_actual_return_and_encode_error_words_bound(self):
        self.assertEqual(len(self.proof['ARM_words']),18)
        for r in self.proof['ARM_words']:self.assertEqual(self.ns['read'](int(r['address'],16),4).hex(),r['bytes']);self.assertEqual(int.from_bytes(bytes.fromhex(r['bytes']),'little'),int(r['word'],16))
    def test_real_attribute_and_type_setter_selectors_bound(self):
        self.assertEqual({r['selector']for r in self.proof['selectors']},{'setRawAttributes:','setRawType:'})
        for r in self.proof['selectors']:
            a=int(r['pointer'],16);v,c=self.ns['reachable_pointer'](a);self.assertEqual(c,r['chain']);self.assertEqual(self.ns['read'](a,8).hex(),r['pointer_bytes']);t=self.ns['base']+(v&((1<<36)-1));o=self.ns['offset'](t);self.assertEqual(self.ns['raw'][o:self.ns['raw'].index(b'\0',o)].decode(),r['selector'])
    def test_repository_returns_same_inserted_object_and_optional_attributes(self):
        s=body(self.src['ClipboardListPersistence'],'func insertPinboard(');self.order(s,['let list = PastoListEntity(context: context)','try? context.obtainPermanentIDs(for: [list])','let attributes = try? encodeAttributes()','list.setValue(attributes, forKey: "rawAttributes")','list.setValue(Int64(2), forKey: "rawType")','return (list, attributes)']);self.assertIn('throws -> (object: NSManagedObject, attributes: Data?)',self.src['ClipboardListPersistence'])
        for t in ['list(identifier:','allLists()','context.delete','rollback','throw ']:self.assertNotIn(t,s)
    def test_encoding_failure_continues_with_nil_instead_of_stopping_before_type2(self):
        s=body(self.src['ClipboardListPersistence'],'func insertPinboard(');self.assertIn('let attributes = try? encodeAttributes()',s);self.assertNotIn('let attributes = try encodeAttributes()',s);self.assertNotIn('guard let attributes',s);self.assertNotIn('if let attributes',s);self.assertIn('return (list, attributes)',s)
    def test_native_target_facade_returns_created_target_without_UUID_lookup(self):
        s=body(self.src['ClipboardStore'],'public func createPinboardTarget(');self.assertIn('guard !name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty',s);self.assertIn('return try insertPinboard(name: name, colorHex: nil).target',s)
        for t in ['persistence.','list(identifier:','pinboards.first','UUID(','makePinboardCollection']:self.assertNotIn(t,s)
    def test_single_store_transaction_returns_value_and_same_native_object(self):
        s=body(self.src['ClipboardStore'],'private func insertPinboard(');self.order(s,['let result: (board: Pinboard, target: ClipboardPinboardTarget) = try mutateInTransaction','let id = UUID()','let created = try transaction.repository.lists.insertPinboard(identifier: id.uuidString','let board = Pinboard(id: id','rawAttributes: created.attributes','state.pinboards.append(board)','return (board, ClipboardPinboardTarget(id: id, object: created.object))']);self.assertEqual(s.count('UUID()'),1);self.assertNotIn('list(identifier:',s)
    def test_existing_value_create_apis_keep_their_validation_and_result_type(self):
        s=self.src['ClipboardStore'];a=body(s,'public func createPinboard(name:');self.assertIn('guard !name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty',a);self.assertIn('return try insertPinboard(name: name, colorHex: colorHex).board',a);a=body(s,'public func createPinboardFromIntent(');self.assertIn('guard !name.isEmpty',a);self.assertNotIn('trimmingCharacters',a);self.assertIn('return try insertPinboard(name: name, colorHex: nil).board',a)
    def test_list_create_and_assign_forwards_captured_inputs_to_same_target(self):
        s=body(self.src['ReplicaUIController'],'func createPinboard(assignSelection:');self.order(s,['let ids = selectionItems?.map','state.perform','let board = try store.createPinboardTarget(name: name)','if assignSelection','if let selectionItems','store.assign(items: selectionItems, to: board)','store.assign(orderedIDs: ids, to: board.id)']);self.assertNotIn('store.assign(items: selectionItems, to: board.id)',s)
    def test_preview_reads_current_item_after_creation_and_passes_native_target(self):
        a=body(self.src['OriginalReplicaPreviewAdapter'],'private func createPinboardForCurrentItem()');s=a[:a.index('let alert = NSAlert()')];self.order(s,['if input?.hasNativeEntity == true','state.perform','state.store.createPinboardTarget(name:','guard let current = self.input','state.store.assign(items: [current], to: board)','return']);self.assertNotIn('to: board.id',s)
    def test_preview_legacy_modal_tail_is_byte_preserved(self):
        p='replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift';marker='private func createPinboardForCurrentItem()';a=body(self.src['OriginalReplicaPreviewAdapter'],marker);b=body((self.phase/'before'/p).read_text(),marker);self.assertEqual(a[a.index('let alert = NSAlert()'):],b[b.index('let alert = NSAlert()'):])
    def test_unused_color_rule_and_native_metadata_validation_sequence(self):
        p='replica/Sources/PastoCore/ClipboardStore.swift';a=body(self.src['ClipboardStore'],'private func insertPinboard(');b=body((self.phase/'before'/p).read_text(),'private func insertPinboard(');self.assertEqual(a[a.index('let code: UInt64?'):a.index('let id = UUID()')],b[b.index('let code: UInt64?'):b.index('let id = UUID()')]);s=body(self.src['ClipboardListPersistence'],'func insertPinboard(');self.order(s,['list.setValue(name, forKey: "name")','try? context.obtainPermanentIDs','try? encodeAttributes()']);self.assertNotIn('Date()',s);self.assertNotIn('forKey: "metadata"',s)
    def test_existing_native_assignment_overload_consumes_object_directly(self):
        s=body(self.src['ClipboardStore'],'public func assign(items: [ClipboardRestoreItem], to target:');self.assertIn('nativePinboard: target.nativeObject',s);s=body(self.src['ClipboardStore'],'private func assign(items: [ClipboardRestoreItem], pinboardID:');self.assertIn('if let nativePinboard {\n                pinboard = nativePinboard',s)
    def test_seven_other_methods_and_five_shared_sources_unchanged(self):
        self.assertEqual(len(self.proof['unchanged_methods']),7);self.assertEqual(len(self.proof['shared_sources']),5)
        for r in self.proof['unchanged_methods']:self.assertEqual(hashlib.sha256(body(pre_native_restore_writer((ROOT/r['path']).read_text()),r['symbol']).encode()).hexdigest(),r['sha256'])
        for p,h in self.proof['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_native_owner_type((ROOT/p).read_text()).encode()).hexdigest(),h);self.assertEqual(h,self.base['production'][p])
    def test_ten_hunks_reverse_exactly_without_other_production_changes(self):
        self.assertEqual(len(CHANGES),10)
        for p,h in self.base['production'].items():
            data=(ROOT/p).read_bytes();data=pre_native_group_creation_result(data.decode()).encode()if p.endswith('.swift')else data;self.assertEqual(hashlib.sha256(data).hexdigest(),h)
        for p,h in self.proof['current_sources'].items():self.assertEqual(hashlib.sha256(pre_native_stack_rendering((ROOT/p).read_text()).encode()).hexdigest(),h)
    def test_reverse_is_idempotent_for_pre_creation_result_source(self):
        for p in self.proof['current_sources']:
            before=(self.phase/'before'/p).read_text();self.assertEqual(pre_native_group_creation_result((ROOT/p).read_text()),before);self.assertEqual(pre_native_group_creation_result(before),before)
    def test_original_encode_error_and_Ghidra_return_alias_corrections_explicit(self):
        self.assertIn('not the UUID String',self.proof['correction']);self.assertIn('Supersedes phase57 assertions',self.proof['correction']);self.assertEqual({r['function_id']for r in self.proof['partial_unscored_repairs']},{'Paste:0x100368560','Paste:0x1003c36f0'})
    def test_full_errors_context_and_model_not_falsely_certified(self):
        self.assertFalse(self.proof['full_function_migration_verified']);self.assertFalse(self.proof['runtime_executed']);self.assertEqual(len(self.proof['contracts']),2);self.assertEqual(len(self.proof['remaining']),4);self.assertIn('transaction error path traps',self.proof['remaining'][1]);self.assertIn('unused colors',self.proof['remaining'][2])

if __name__=='__main__':unittest.main()
