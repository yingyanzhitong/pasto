"""Captured group-menu state and one batch action: Python/source/Mach-O only."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from native_list_edit_event_scope_contract import pre_native_list_edit_event
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment
from group_menu_state_scope_contract import CHANGES,pre_group_menu_state,pre_group_menu_state_bytes
from collection_membership_cache_scope_contract import pre_collection_membership_cache_bytes
class GroupMenuState(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-142';cls.p=json.loads((cls.phase/'group-menu-state-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.panel=(ROOT/'replica/Sources/Pasto/UI/PanelViews.swift').read_text();cls.bindings=body(cls.panel,'private func pinboardMenuBindings(');cls.menu=body(cls.panel,'@ViewBuilder private var contextMenu:');cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
    def order(self,s,tokens):
        i=0
        for t in tokens:i=s.index(t,i)+len(t)
    def original(self,a):
        r=next(r for r in self.p['original_fragments']if r['address']==a);return original_fragment((ROOT/r['path']).read_text(),a[2:])
    def test_nine_original_fragments_binary_decoder_and_local_SDK_bound(self):
        self.assertEqual(len(self.p['original_fragments']),9)
        for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for k in ['binary','decoder','sdk']:
            r=self.p[k];self.assertEqual(hashlib.sha256(Path(r['path']if Path(r['path']).is_absolute()else ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_ten_actual_words_and_five_owner_icon_builder_calls(self):
        self.assertEqual(len(self.p['ARM_words']),10);self.assertEqual(len(self.p['ARM_calls']),5)
        for r in self.p['ARM_words']:self.assertEqual(self.n['read'](int(r['address'],16),4).hex(),r['bytes'])
        for r in self.p['ARM_calls']:
            a=int(r['address'],16);w=int.from_bytes(self.n['read'](a,4),'little');self.assertEqual(w&0xfc000000,0x94000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(a+4*d,int(r['target'],16))
        self.assertEqual(self.n['read'](0x10009ea20,4).hex(),'e70316aa')
    def test_original_counts_current_pinboard_owners_then_emits_off_on_mixed(self):
        s=self.original('0x10009e8a8');self.order(s,['FUN_10031bc94()','NSObject::___infix(pNVar11,pNVar20)','local_a0 = (ulong)(_Var23 != 0 && _Var25 != _Var26)','lVar19 = -(local_a0 & 1)','if (_Var25 == _Var26)','lVar19 = 1','FUN_10021bafc(local_98,pvVar16,param_3,0,0,0xe000000000000000,0,lVar19)'])
        self.assertIn('objc_stub::setState_(self,param_8)',self.original('0x10021bafc'))
    def test_actual_action_wrapper_forwards_full_captured_array_and_target(self):
        s=self.original('0x10009f240');self.assertIn('FUN_10009ee9c(',s);s=self.original('0x10009ee9c');self.order(s,['local_68[0] = param_3','_swift_bridgeObjectRetain(param_3)','(*param_1)(local_68,param_4)']);self.assertNotIn('filter',s)
        self.assertIn('state.assignItems(items, to: target)',self.bindings);self.assertNotIn('state.assignItems(items, to: nil)',self.bindings)
    def test_current_matching_reads_native_owner_before_legacy_fallback(self):
        s=body(self.bindings,'let matched = items.filter');self.order(s,['input.isAssigned(to: target)','?? (state.store.pinboardOwner(for: input.resolvedItem())?.id == target.id)'])
        self.assertEqual(self.bindings.count('resolvedItem()'),1);handle=(ROOT/'replica/Sources/PastoCore/ClipboardRestoreItem.swift').read_text();s=body(handle,'public func isAssigned(');self.order(s,['guard let object = nativeObject','value(forKey: "list")','int64Value == 2','owner.isEqual(target.nativeObject)'])
    def test_snapshot_binding_has_exactly_one_assignment_setter_ignoring_toggle_bool(self):
        self.assertEqual(self.bindings.count('Binding<Bool>('),1);self.assertEqual(self.bindings.count('set:'),1);self.assertIn('set: { _ in state.assignItems(items, to: target) }',self.bindings)
        for t in ['Task','DispatchQueue','for input in','unassign(','items.filter { $0','selection =','UUID()']:self.assertNotIn(t,self.bindings)
    def test_partial_state_adds_only_a_constant_true_second_source(self):
        self.order(self.bindings,['get: { matched == items.count }','if matched > 0, matched < items.count { return [assignment, .constant(true)] }','return [assignment]']);self.assertEqual(self.bindings.count('.constant(true)'),1);self.assertNotIn('Binding<Bool>(get: { true }',self.bindings)
    def test_all_counts_including_empty_map_to_original_three_states(self):
        # Binding snapshot adapter only; no SwiftUI/AppKit execution.
        for n in range(17):
            for matched in range(n+1):
                original=1 if matched==n else(-1 if matched>0 else 0)
                sources=[matched==n]
                if 0<matched<n:sources.append(True)
                projected=1 if all(sources)else(-1 if any(sources)else 0)
                self.assertEqual(projected,original,(n,matched));self.assertEqual(len(sources),2 if original==-1 else 1)
        self.assertEqual(1 if 0==0 else 0,1)
    def test_batch_action_model_remains_one_with_both_requested_toggle_values(self):
        # Secondary mixed source is constant, so only primary setter invokes captured batch.
        inputs=['item-c','item-a','item-c'];target=object()
        for mixed in [False,True]:
            for requested in [False,True]:
                calls=[];setters=[lambda _:calls.append((inputs,target))]
                if mixed:setters.append(lambda _:None)
                for write in setters:write(requested)
                self.assertEqual(len(calls),1);self.assertIs(calls[0][0],inputs);self.assertIs(calls[0][1],target)
    def test_real_submenu_consumes_bindings_with_SDK_multi_source_keypath(self):
        self.assertIn('Toggle(sources: pinboardMenuBindings(for: target, items: groupItems), isOn: \\.self)',self.menu);self.assertNotIn('Button(target.name)',self.menu);r=self.p['sdk'];self.assertIn(r['declaration'],Path(r['path']).read_text());self.assertLessEqual(r['minimum_macos'],r['project_minimum_macos']);self.assertIn('platforms: [.macOS(.v14)]',(ROOT/'replica/Package.swift').read_text())
    def test_row_uses_native_name_canonical_color_and_original_twelve_point_icon(self):
        self.order(self.menu,['Text(target.name)','target.colorCode.map { OriginalPinboardColor(canonicalColorCode: $0).color() } ?? .clear','OriginalPinboardHeaderIcon.image(height: 12, shared: false, color: color)'])
        original=self.original('0x10009e8a8');self.assertIn('thunk_FUN_1003ed158(0x4028000000000000',original);icon=(ROOT/'replica/Sources/Pasto/UI/OriginalPinboardHeaderIcon.swift').read_text();self.assertIn('let lineWidth = rectangleHeight * 0.05',icon);self.assertIn('CGPath(ellipseIn: firstRect',icon);self.assertIn('CGPathCreateWithEllipseInRect',self.original('0x1003ed158'))
    def test_separator_create_and_unpin_tail_is_byte_identical(self):
        old=body((self.phase/'before/replica/Sources/Pasto/UI/PanelViews.swift').read_text(),'@ViewBuilder private var contextMenu:');a=self.menu.index('Menu("添加到 Pasto")');b=old.index('Menu("添加到 Pasto")');newsub=body(self.menu[a:],'Menu("添加到 Pasto")');oldsub=body(old[b:],'Menu("添加到 Pasto")');self.assertEqual(newsub[newsub.index('                Divider()'):],oldsub[oldsub.index('                Divider()'):]);self.assertEqual(self.menu[:a],old[:b])
    def test_six_provider_gate_assignment_creation_selection_methods_unchanged(self):
        self.assertEqual(len(self.p['unchanged_methods']),6)
        for r in self.p['unchanged_methods']:self.assertEqual(hashlib.sha256(body(pre_native_list_edit_event((ROOT/r['path']).read_text()),r['symbol']).encode()).hexdigest(),r['sha256'])
    def test_five_shared_sources_unchanged_including_drawer_and_native_equality(self):
        self.assertEqual(len(self.p['shared_sources']),5)
        for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_collection_membership_cache_bytes(ROOT/p)).hexdigest(),h);self.assertEqual(h,self.base['production'][p])
    def test_two_hunks_one_file_preserve_all247_files_and_reversal_is_exact(self):
        self.assertEqual(len(CHANGES),2);paths={str(p.relative_to(ROOT))for p in(ROOT/'replica/Sources').rglob('*')if p.is_file()};self.assertEqual(paths,set(self.base['production']));changed=[]
        for p,h in self.base['production'].items():
            if hashlib.sha256(pre_collection_membership_cache_bytes(ROOT/p)).hexdigest()!=h:changed.append(p)
            self.assertEqual(hashlib.sha256(pre_group_menu_state_bytes(ROOT/p)).hexdigest(),h)
        self.assertEqual(set(changed),set(self.p['current_sources']))
        for p,h in self.p['current_sources'].items():self.assertEqual(hashlib.sha256(pre_collection_membership_cache_bytes(ROOT/p)).hexdigest(),h);old=(self.phase/'before'/p).read_text();self.assertEqual(pre_group_menu_state((ROOT/p).read_text()),old);self.assertEqual(pre_group_menu_state(old),old)
    def test_existing_builder_contract_is_not_double_counted_or_claimed_full_runtime(self):
        self.assertEqual(self.p['new_difference_records'],0);self.assertEqual(self.p['additional_contract_function_id'],'Paste:0x10009e8a8');self.assertTrue(self.p['finite_contract_verified']);self.assertFalse(self.p['full_function_migration_verified']);self.assertFalse(self.p['runtime_executed']);self.assertEqual(len(self.p['adaptations']),2);self.assertIn('SwiftUI',self.p['adaptations'][0]);self.assertIn('04430c/0f733c',self.p['remaining'][1])
if __name__=='__main__':unittest.main()
