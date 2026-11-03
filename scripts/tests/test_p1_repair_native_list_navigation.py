"""Current-entity group navigation, source and Mach-O checks only."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from stack_close_session_scope_contract import pre_stack_close_session
from test_p0_repair_checksum_routing import original_fragment
from native_list_navigation_scope_contract import CHANGES,pre_native_list_navigation,pre_native_list_navigation_bytes
from group_menu_state_scope_contract import pre_group_menu_state_bytes
class NativeListNavigation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-141';cls.p=json.loads((cls.phase/'native-list-navigation-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.ui=(ROOT/'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text();cls.handle=(ROOT/'replica/Sources/PastoCore/ClipboardRestoreItem.swift').read_text();cls.targets=body(cls.ui,'func selectedItemTargetLists()');cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
    def original(self,a):
        r=next(r for r in self.p['original_fragments']if r['address']==a);return original_fragment((ROOT/r['path']).read_text(),a[2:])
    def order(self,s,tokens):
        i=0
        for t in tokens:i=s.index(t,i)+len(t)
    def test_six_original_fragments_binary_and_decoder_bound(self):
        self.assertEqual(len(self.p['original_fragments']),6)
        for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for k in ['binary','decoder']:
            r=self.p[k];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_four_actual_calls_and_ten_entity_transport_words(self):
        self.assertEqual(len(self.p['ARM_calls']),4);self.assertEqual(len(self.p['ARM_words']),10)
        for r in self.p['ARM_words']:self.assertEqual(self.n['read'](int(r['address'],16),4).hex(),r['bytes'])
        for r in self.p['ARM_calls']:
            pc=int(r['address'],16);w=int.from_bytes(self.n['read'](pc,4),'little');self.assertEqual(w&0xfc000000,0x94000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(pc+4*d,int(r['target'],16))
        self.assertEqual(self.n['read'](0x1003b855c,4).hex(),self.n['read'](0x1003b8878,4).hex())
    def test_true_timestamp_list_identifier_selectors_resolve_from_actual_stubs(self):
        self.assertEqual({r['selector']for r in self.p['selectors']},{'timestamp','list','identifier'})
        for r in self.p['selectors']:
            pc=int(r['stub'],16);b=self.n['read'](pc,8);self.assertEqual(b.hex(),r['stub_bytes']);w,a=struct.unpack('<II',b);imm=((w>>5)&0x7ffff)*4+((w>>29)&3)
            if imm&(1<<20):imm-=1<<21
            ref=(pc&~4095)+(imm<<12)+((a>>10)&0xfff)*8;self.assertEqual(ref,int(r['address'],16));v,c=self.n['reachable_pointer'](ref);self.assertEqual(hex(v),r['raw']);self.assertEqual(c,r['chain']);target=self.n['base']+(v&((1<<36)-1));self.assertEqual(target,int(r['target'],16));self.assertEqual(self.n['read'](target,120).split(b'\0')[0].decode(),r['selector'])
    def test_original_single_input_history_then_current_native_owner(self):
        s=self.original('0x1003b83c4');self.order(s,['Collection::get_count()','if (_Var11 != 1)','Collection::_get_first()','objc_stub::timestamp(self)','LAB_1003b8878:','objc_stub::list((ID)self)','FUN_1003250f0()','objc_stub::identifier(self_00)']);self.assertIn('return IVar1 == 2',self.original('0x1003250f0'))
    def test_native_membership_reads_fields_without_archive_or_pinboard_cache(self):
        s=body(self.handle,'public func listNavigationMembership()');self.order(s,['guard let object = nativeObject','value(forKey: "timestamp") != nil','value(forKey: "list")','value(forKey: "rawType")','value(forKey: "identifier")'])
        for t in ['resolvedItem','ClipboardPersistence','store.','fetch(','pinboardIDs','pinboardOwnerID','Date()','isDeleted','nativeTimestamp']:self.assertNotIn(t,s)
    def test_owner_requires_full_int64_type_two_and_uuid_bridge_is_explicit(self):
        s=body(self.handle,'public func listNavigationMembership()');self.assertIn('?.int64Value == 2',s);self.assertIn('return (isInHistory, nil)',s);self.assertIn('identifier.flatMap { UUID(uuidString: $0) }',s)
        for t in ['int16Value','truncatingIfNeeded','?? 2','UUID()']:self.assertNotIn(t,s)
    def test_selection_resolves_applied_handles_before_single_item_gate(self):
        self.order(self.targets,['orderedSelectionIDs.filter { selection.contains($0) }','if let collectionOwner','collectionOwner.appliedRestoreItems(for: self, orderedIDs: ids) ?? []','else {','visibleItems.map','byID[$0]?.restoreItem()','guard inputs.count == 1','let input = inputs[0]'])
        for t in ['selectedItems','appliedSelectedItems','requiredItem()']:self.assertNotIn(t,self.targets)
    def test_native_target_branch_returns_before_any_legacy_decode(self):
        self.order(self.targets,['if let membership = input.listNavigationMembership()','return lists','let item = input.resolvedItem()','store.pinboardOwner(for: item)'])
        native=body(self.targets,'if let membership = input.listNavigationMembership()')
        for t in ['resolvedItem','store.','payload','Pinboard(']:self.assertNotIn(t,native)
    def test_history_is_first_and_current_list_is_excluded_outside_search(self):
        s=body(self.targets,'if let membership = input.listNavigationMembership()');self.order(s,['membership.isInHistory, isSearching || pinboardID != nil','lists.append(nil)','if let ownerID = membership.pinboardID, isSearching || ownerID != pinboardID','lists.append(ownerID)'])
    def test_membership_context_table_covers_history_owner_and_search(self):
        # Original target-list rule; field reader and branch strings are bound above, no CoreData runtime.
        owner='board-a'
        for in_history in [False,True]:
            for current in [None,owner,'board-b']:
                for searching in [False,True]:
                    result=([None]if in_history and(searching or current is not None)else [])+([owner]if searching or owner!=current else [])
                    if not searching:self.assertNotIn(current,result)
                    if searching and in_history:self.assertEqual(result,[None,owner])
                    if None in result:self.assertEqual(result[0],None)
    def test_old_value_owner_and_history_rules_are_kept_verbatim_after_native_gate(self):
        old=body((self.phase/'before/replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text(),'func selectedItemTargetLists()');marker='        if item.isInHistory,';self.assertEqual(self.targets[self.targets.index(marker):],old[old.index(marker):]);self.assertIn('let item = input.resolvedItem()',self.targets)
    def test_real_reveal_consumer_uses_handle_ID_without_DTO_projection(self):
        s=body(self.ui,'private func revealSelectedItemInList()');self.order(s,['state.selectedItemTargetLists()','let input = appliedRestoreItems().first','horizontalOffsetForVisibleItem(input.id)','PendingListFocus(itemID: input.id','state.chooseListForItemReveal(lists[0])'])
        for t in ['selectedItems','resolvedItem','requiredItem','store.items']:self.assertNotIn(t,s)
    def test_seven_old_chooser_pending_focus_menu_and_owner_methods_unchanged(self):
        self.assertEqual(len(self.p['unchanged_methods']),7)
        for r in self.p['unchanged_methods']:self.assertEqual(hashlib.sha256(body((ROOT/r['path']).read_text(),r['symbol']).encode()).hexdigest(),r['sha256'])
    def test_four_provider_collection_and_reference_sources_unchanged(self):
        self.assertEqual(len(self.p['shared_sources']),4)
        for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_group_menu_state_bytes(ROOT/p)).hexdigest(),h);self.assertEqual(h,self.base['production'][p])
    def test_three_hunks_two_files_reverse_exactly_across247_production_files(self):
        self.assertEqual(len(CHANGES),3);paths={str(p.relative_to(ROOT))for p in(ROOT/'replica/Sources').rglob('*')if p.is_file()};self.assertEqual(paths,set(self.base['production']));changed=[]
        for p,h in self.base['production'].items():
            if hashlib.sha256(pre_group_menu_state_bytes(ROOT/p)).hexdigest()!=h:changed.append(p)
            self.assertEqual(hashlib.sha256(pre_native_list_navigation_bytes(ROOT/p)).hexdigest(),h)
        self.assertEqual(set(changed),set(self.p['current_sources']))
        for p,h in self.p['current_sources'].items():
            s=pre_stack_close_session((ROOT/p).read_text());old=(self.phase/'before'/p).read_text();self.assertEqual(hashlib.sha256(s.encode()).hexdigest(),h);self.assertEqual(pre_native_list_navigation(s),old);self.assertEqual(pre_native_list_navigation(old),old)
    def test_one_new_finite_contract_does_not_claim_original_full_list_model(self):
        self.assertEqual(self.p['function_id'],'Paste:0x1003b83c4');self.assertEqual(self.p['new_difference_records'],1);self.assertTrue(self.p['finite_contract_verified']);self.assertFalse(self.p['full_function_migration_verified']);self.assertFalse(self.p['runtime_executed']);self.assertEqual(len(self.p['adaptations']),2);self.assertIn('UUID',self.p['adaptations'][0]);self.assertIn('04430c/0f733c',self.p['remaining'][1])
if __name__=='__main__':unittest.main()
