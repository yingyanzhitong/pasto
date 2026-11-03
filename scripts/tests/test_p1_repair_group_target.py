"""Captured group List identity; source/Mach-O only, no Swift/native runtime."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from native_group_creation_result_scope_contract import pre_native_group_creation_result
from pinboard_collection_scope_contract import pre_pinboard_collection,pre_pinboard_collection_bytes
from test_offline_p0_contracts import body
from group_target_scope_contract import CHANGES,pre_group_target,pre_group_target_bytes

class GroupTargetContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-106';cls.proof=json.loads((cls.phase/'group-target-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.src={Path(p).stem:pre_pinboard_collection((ROOT/p).read_text())for p in cls.proof['current_sources']};ns={};exec((ROOT/cls.proof['decoder']['path']).read_text().split("idx={r['address']",1)[0],ns);cls.ns=ns
    def order(self,s,tokens):
        cursor=0
        for t in tokens:cursor=s.index(t,cursor)+len(t)
    def test_original_thirteen_fragments_and_static_input_bindings(self):
        self.assertEqual(len(self.proof['original_fragments']),13)
        for r in self.proof['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for r in [self.proof['binary'],self.proof['decoder']]+self.proof['reused_evidence']:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_actual_five_retention_and_forwarding_branches(self):
        self.assertEqual(len(self.proof['ARM_calls']),5)
        for r in self.proof['ARM_calls']:
            pc=int(r['address'],16);b=self.ns['read'](pc,4);self.assertEqual(b.hex(),r['bytes']);w=int.from_bytes(b,'little');self.assertEqual(w&0x7c000000,0x14000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(pc+d*4,int(r['target'],16))
    def test_thirteen_capture_register_and_callback_words(self):
        rows={r['address']:r for r in self.proof['ARM_words']};self.assertEqual(len(rows),13)
        for r in rows.values():self.assertEqual(self.ns['read'](int(r['address'],16),4).hex(),r['bytes']);self.assertEqual(int.from_bytes(bytes.fromhex(r['bytes']),'little'),int(r['word'],16))
        self.assertEqual(rows['0x10009e9cc']['word'],'0xa9026c15');self.assertEqual(rows['0x10009f244']['word'],'0xa9420e82');self.assertEqual(rows['0x10009ef14']['word'],'0xaa1303e1')
    def test_heap_metadata_destructor_and_actual_runtime_retention_names(self):
        r=self.proof['closure_destructor_pointer'];a=int(r['address'],16);v,chain=self.ns['reachable_pointer'](a);self.assertEqual(chain,r['chain']);self.assertEqual(self.ns['read'](a,8).hex(),r['bytes']);self.assertEqual(self.ns['base']+(v&((1<<36)-1)),int(r['target'],16));self.assertEqual(r['target'],'0x10009f20c');self.assertEqual(self.proof['runtime_symbol_names'],{'0x100bfbf70':'_objc_retain','0x100bfbf64':'_objc_release'})
    def test_native_target_is_a_strong_entity_not_object_id_or_resolver(self):
        s=self.src['ClipboardListPersistence'];start=s.index('@MainActor\npublic struct ClipboardPinboardTarget');end=s.index('/// Access on the supplied context',start);s=s[start:end];self.assertIn('public let id: UUID',s);self.assertIn('let nativeObject: NSManagedObject',s);self.assertIn('nativeObject = object',s)
        for t in ['weak ','unowned ','NSManagedObjectID','resolve','isDeleted']:self.assertNotIn(t,s)
    def test_native_target_type_visibility_and_actor_contract(self):
        s=self.src['ClipboardListPersistence'];self.assertIn('@MainActor\npublic struct ClipboardPinboardTarget',s);self.assertIn('import CoreData',s);self.assertIn('import Foundation',s);self.assertIn('import CoreData',self.src['ClipboardStore']);self.assertIn('public func assign(items: [ClipboardRestoreItem], to target: ClipboardPinboardTarget)',self.src['ClipboardStore'])
    def test_target_producer_uses_current_context_and_keeps_resolved_object(self):
        s=body(self.src['ClipboardPersistence'],'func pinboardAssignmentTarget(');self.order(s,['context.performAndWait','lists.list(identifier: id.uuidString)','ClipboardPinboardTarget(id: id, object: list)']);self.assertNotIn('existingObject',s);self.assertNotIn('objectID',s);self.assertNotIn('ClipboardItem',s)
    def test_store_target_producer_is_the_actual_persistence_facade(self):
        s=body(self.src['ClipboardStore'],'public func pinboardAssignmentTarget(');self.assertIn('persistence.pinboardAssignmentTarget(id: id)',s);self.assertNotIn('items',s)
    def test_menu_captures_target_before_button_action_not_at_click(self):
        s=body(self.src['PanelViews'],'@ViewBuilder private var contextMenu:');self.order(s,['let groupItems = state.controller?.contextMenuRestoreItems()','ForEach(state.store.pinboards)','let target = state.store.pinboardAssignmentTarget(id: board.id)','Button(board.name)','if let target { state.assignItems(groupItems, to: target) }']);self.assertEqual(s.count('pinboardAssignmentTarget'),1)
    def test_unavailable_target_fallback_does_not_change_existing_value_menu(self):
        s=body(self.src['PanelViews'],'@ViewBuilder private var contextMenu:');self.assertIn('else { state.assignItems(groupItems, to: board.id) }',s);self.assertIn('createPinboard(assignSelection: true, selectionItems: groupItems)',s)
    def test_ui_target_overload_passes_same_input_and_target_synchronously(self):
        s=body(self.src['ReplicaUIController'],'func assignItems(_ items: [ClipboardRestoreItem], to target: ClipboardPinboardTarget)');self.assertIn('perform { try store.assign(items: items, to: target) }',s)
        for t in ['.id','visibleItems','selection','Task','DispatchQueue']:self.assertNotIn(t,s)
    def test_public_target_route_forwards_native_object_without_query(self):
        s=body(self.src['ClipboardStore'],'public func assign(items: [ClipboardRestoreItem], to target: ClipboardPinboardTarget)');self.assertIn('try assign(items: items, pinboardID: target.id, nativePinboard: target.nativeObject)',s)
        for t in ['lists.list','existingObject','pinboards.first']:self.assertNotIn(t,s)
    def test_native_transaction_uses_captured_list_and_only_legacy_branch_fetches(self):
        s=body(self.src['ClipboardStore'],'private func assign(items: [ClipboardRestoreItem], pinboardID:');self.order(s,['try mutateInTransaction','if let nativePinboard','pinboard = nativePinboard','else','lists.list(identifier: pinboardID.uuidString)','pinboard = current','repository.assignItems(items.map { $0.nativeObject! }, to: pinboard)']);self.assertEqual(s.count('lists.list'),1)
    def test_existing_uuid_and_nil_value_entry_preserves_prior_adapter(self):
        s=body(self.src['ClipboardStore'],'public func assign(items: [ClipboardRestoreItem], to pinboardID: UUID?)');self.assertIn('try assign(items: items, pinboardID: pinboardID, nativePinboard: nil)',s);s=body(self.src['ClipboardStore'],'private func assign(items: [ClipboardRestoreItem], pinboardID:');self.order(s,['guard let pinboardID, items.allSatisfy','try assign(orderedIDs: items.map(\\.id), to: pinboardID)','return','guard !items.isEmpty else { return }'])
    def test_five_existing_mutation_and_creation_methods_unchanged(self):
        self.assertEqual(len(self.proof['unchanged_methods']),5)
        for r in self.proof['unchanged_methods']:
            s=body(pre_native_group_creation_result((ROOT/r['path']).read_text()),r['symbol']);self.assertEqual(s,body((self.phase/'before'/r['path']).read_text(),r['symbol']));self.assertEqual(hashlib.sha256(s.encode()).hexdigest(),r['sha256'])
    def test_seven_hunks_exact_reversal_and_no_unrelated_production_changes(self):
        self.assertEqual(len(CHANGES),7);self.assertEqual({r[0]for r in CHANGES},set(self.proof['current_sources']))
        files={str(p.relative_to(ROOT))for p in(ROOT/'replica/Sources').rglob('*')if p.is_file()};self.assertEqual(files,set(self.base['production']))
        for p,h in self.base['production'].items():self.assertEqual(hashlib.sha256(pre_group_target_bytes(ROOT/p)).hexdigest(),h)
        for p,h in self.proof['current_sources'].items():self.assertEqual(hashlib.sha256(pre_pinboard_collection_bytes(ROOT/p)).hexdigest(),h);self.assertEqual(pre_group_target(pre_group_target(pre_pinboard_collection((ROOT/p).read_text()))),(self.phase/'before'/p).read_text())
    def test_shared_reference_and_payload_helpers_are_unchanged(self):
        self.assertEqual(len(self.proof['shared_sources']),4)
        for p,h in self.proof['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_pinboard_collection_bytes(ROOT/p)).hexdigest(),h);self.assertEqual(h,self.base['production'][p])
    def test_no_complete_function_or_runtime_claim_and_open_boundaries_remain(self):
        self.assertFalse(self.proof['full_function_migration_verified']);self.assertFalse(self.proof['runtime_executed']);self.assertEqual(self.proof['new_difference_records'],1);self.assertEqual(self.proof['contracts'][0]['function_id'],'Paste:0x10009f240');self.assertEqual(len(self.proof['remaining']),4);self.assertIn('original native group collection producer',self.proof['remaining'][0])

if __name__=='__main__':unittest.main()
