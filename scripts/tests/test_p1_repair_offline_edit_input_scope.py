"""Batch current-source audit of offline editor input and shared permission boundary."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_p0_repair_checksum_routing import original_fragment
from test_offline_p0_contracts import body
from native_list_navigation_scope_contract import pre_native_list_navigation_bytes
class OfflineEditInputScope(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-140';cls.p=json.loads((cls.phase/'offline-edit-input-scope-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.ui=(ROOT/'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text();cls.adapter=(ROOT/'replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift').read_text();cls.handle=(ROOT/'replica/Sources/PastoCore/ClipboardRestoreItem.swift').read_text()
    def original(self,a):
        r=next(r for r in self.p['original_fragments']if r['address']==a);return original_fragment((ROOT/r['path']).read_text(),a[2:])
    def order(self,s,tokens):
        i=0
        for t in tokens:i=s.index(t,i)+len(t)
    def test_twelve_original_fragments_and_three_prior_reachable_leaf_proofs_bound(self):
        self.assertEqual(len(self.p['original_fragments']),12);self.assertEqual(len(self.p['reused_evidence']),3)
        for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for r in self.p['reused_evidence']:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_original_complete_filter_precedes_empty_beep_and_per_item_router(self):
        self.order(self.original('0x1000655cc'),['FUN_10031c2ec()','if (lVar13 == 0)','NSSound::beep()','FUN_1003bb280(uVar6)'])
        self.assertIn('FUN_1003bb290(param_1,1)',self.original('0x1003bb280'));self.assertIn('(*pcVar6)(param_1,uVar5,param_2',self.original('0x1003bb290'))
    def test_current_native_eligibility_reads_type_before_legacy_fallback(self):
        s=body(self.ui,'private static func allowsEditingInput(');self.order(s,['if let rawType = input.previewRawType()','return [1, 2, 4, 5].contains(rawType)','return allowsContentEditing(input.resolvedItem())']);self.assertNotIn('resolvedItem',body(s,'if let rawType = input.previewRawType()'))
        s=body(self.handle,'public func previewRawType()');self.assertIn('value(forKey: "rawType")',s);self.assertNotIn('resolvedItem',s)
    def test_current_complete_filter_and_original_ordered_iteration_are_preserved(self):
        s=body(self.ui,'private func editItems(');self.order(s,['items.filter { Self.allowsEditingInput($0) }','guard !editable.isEmpty else { NSSound.beep(); return }','for input in editable { presentEditingPreview(input: input) }'])
        for token in ['Set(','sorted(','reversed(','resolvedItem','Task']:self.assertNotIn(token,s)
    def test_explicit_editor_holds_same_handle_through_registry_factory_and_events(self):
        s=body(self.ui,'private func presentEditingPreview(');self.order(s,['let itemIdentifier = input.previewIdentifier','registry.f_100086c10(window: window, itemIdentity: input.previewIdentity','makeOriginalReplicaNativePreview(state: state, input: input)','preview.onEndEditing','preview.onEditingStateChanged','itemIdentifier: input.previewIdentifier','preview.f_10007be8c()','transition.present(controller)'])
        for t in ['resolvedItem','state.store.items','ClipboardItem(']:self.assertNotIn(t,s)
    def test_four_native_factory_types_all_precede_archive_resolution(self):
        s=body(self.adapter,'func makeOriginalReplicaNativePreview(');fallback=s.index('input.resolvedItem()')
        for raw in [5,2,1,4]:
            b=body(s,'if rawType == '+str(raw));self.assertLess(s.index('if rawType == '+str(raw)),fallback);self.assertNotIn('resolvedItem',b);self.assertIn('input: input',b)
        self.assertIn('item: nil',body(s,'if rawType == 4'));self.assertIn('item: nil',body(s,'if rawType == 1'))
    def test_all_native_content_constructors_accept_handle_without_required_DTO(self):
        s=body(self.adapter,'private func makeReplicaTextPreview(');self.assertIn('ReplicaInlineTextPreviewContent(state: state, item: item, input: input)',s)
        for filename in ['ReplicaColorPreviewContent.swift','ReplicaImagePreviewContent.swift','ReplicaLinkPreviewContent.swift']:
            s=(ROOT/'replica/Sources/Pasto/UI'/filename).read_text();s=body(s,'init(state: ReplicaUIState, item: ClipboardItem?, input:');self.assertIn('input?.id ?? item?.id',s);self.assertNotIn('resolvedItem',s[:s.index('super.init')])
    def test_writing_tools_capability_and_type_filter_precede_edit_route(self):
        s=body(self.ui,'private func writeAppliedSelection()');self.order(s,['guard OriginalWritingTools.isAvailable()','appliedRestoreItems().filter','Self.allowsEditingInput($0)','if let rawType = $0.previewRawType() { return rawType == 5 }','guard !items.isEmpty','editItems(items)','OriginalWritingTools.showAfterDelay()'])
        self.order(self.original('0x10006bed8'),['FUN_10031c2ec()','FUN_10031eba8()','FUN_1000655cc(','FUN_1002160fc('])
    def test_original_extra_permission_is_after_type_and_only_pinboard_owner(self):
        s=self.original('0x10031c2ec');self.order(s,['objc_stub::rawType','if ((uVar4 & 1) == 0)','objc_stub::list','FUN_1003250f0()','FUN_100328f38()']);self.assertIn('if (uVar2 == 0)',s)
    def test_permission_positively_traces_share_record_and_CKShare_projection(self):
        s=self.original('0x100328f38');self.order(s,['FUN_1003b4444()','if (lVar4 == 0)','FUN_10032670c(','return bVar1 < 2']);self.assertTrue(s.rstrip().endswith('return true;\n}'))
        s=self.original('0x1003b4444');self.order(s,['objc_stub::managedObjectContext','objc_stub::cloudKitZoneOwnerName','objc_stub::shareRecordData','setRequiresSecureCoding_','_OBJC_CLASS___CKShare','initWithCoder_'])
        s=self.original('0x10032670c');self.assertIn('objc_stub::URL(param_2)',s);self.assertIn('Foundation::PersonNameComponents',s)
    def test_six_current_sources_ten_methods_and_all247_production_files_unchanged(self):
        self.assertEqual(len(self.p['current_sources']),6);self.assertEqual(len(self.p['current_methods']),10)
        for p,h in self.p['current_sources'].items():self.assertEqual(hashlib.sha256(pre_native_list_navigation_bytes(ROOT/p)).hexdigest(),h)
        for r in self.p['current_methods']:self.assertEqual(hashlib.sha256(body((ROOT/r['path']).read_text(),r['symbol']).encode()).hexdigest(),r['sha256'])
        actual={str(p.relative_to(ROOT)):hashlib.sha256(pre_native_list_navigation_bytes(p)).hexdigest()for p in(ROOT/'replica/Sources').rglob('*')if p.is_file()};self.assertEqual(actual,self.base['production']);self.assertEqual(len(actual),247)
    def test_scope_is_finite_and_next_module_not_false_whole_P1_completion(self):
        self.assertTrue(self.p['production_unchanged']);self.assertEqual(self.p['new_difference_records'],0);self.assertFalse(self.p['full_function_migration_verified']);self.assertFalse(self.p['runtime_executed']);self.assertEqual(len(self.p['verified_contracts']),4);self.assertEqual(len(self.p['remaining']),3);self.assertIn('cache',self.p['next_action']);self.assertIn('04430c/0f733c',self.p['remaining'][2])
if __name__=='__main__':unittest.main()
