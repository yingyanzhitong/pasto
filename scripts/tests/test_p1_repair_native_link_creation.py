"""Link editor creation from native entity: source/Mach-O checks, no framework execution."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from preview_commit_error_scope_contract import pre_preview_commit_error
from test_p0_repair_checksum_routing import original_fragment
from native_link_creation_scope_contract import CHANGES,pre_native_link_creation
from native_list_navigation_scope_contract import pre_native_list_navigation_bytes
class NativeLinkCreationContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-139';cls.p=json.loads((cls.phase/'native-link-creation-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.src={p:(ROOT/p).read_text()for p in cls.p['current_sources']};cls.adapter=cls.src['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift'];cls.link=cls.src['replica/Sources/Pasto/UI/ReplicaLinkPreviewContent.swift'];cls.ro=cls.src['replica/Sources/Pasto/UI/ReplicaReadOnlyPreviewContent.swift'];cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
    def original(self,a):
        r=next(r for r in self.p['original_fragments']if r['address']==a);return original_fragment((ROOT/r['path']).read_text(),a[2:])
    def order(self,s,tokens):
        i=0
        for t in tokens:i=s.index(t,i)+len(t)
    def test_eight_original_fragments_binary_decoder_previous_leaf_proof_are_bound(self):
        self.assertEqual(len(self.p['original_fragments']),8)
        for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for k in ['binary','decoder','reused_evidence']:
            r=self.p[k];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_actual_factory_constructor_and_observer_branch_calls(self):
        self.assertEqual(len(self.p['ARM_calls']),3)
        for r in self.p['ARM_calls']:
            pc=int(r['address'],16);b=self.n['read'](pc,4);self.assertEqual(b.hex(),r['bytes']);w=int.from_bytes(b,'little');self.assertEqual(w&0xfc000000,0x94000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(pc+4*d,int(r['target'],16))
    def test_ten_ARM_words_bind_entity_transport_and_callback(self):
        self.assertEqual(len(self.p['ARM_words']),10)
        for r in self.p['ARM_words']:self.assertEqual(self.n['read'](int(r['address'],16),4).hex(),r['bytes'])
        self.assertEqual(self.n['read'](0x1003bfffc,4).hex(),'742a00f9')
        self.assertEqual(self.n['read'](0x1003c40b0,4).hex(),'e00316aa')
        self.assertEqual(self.n['read'](0x1003c0134,4).hex(),'e00316aa')
    def test_original_factory_routes_type_before_link_entity_constructor(self):
        s=self.original('0x1003c3c90');self.order(s,['objc_stub::rawType(local_58)','FUN_100323594()','if (uVar1 < 3)','if (uVar1 == 3)','FUN_1003c0184()','Combine::Published::_get_subscript(&local_58)','FUN_1003c00b8(local_58'])
        self.assertIn('if (uVar1 == 5)',s);self.assertIn('if (5 < IVar2)',self.original('0x10031eba8'))
    def test_original_initializer_stores_same_entity_and_observes_it(self):
        self.assertIn('FUN_1003bffac(param_1',self.original('0x1003c00b8'));s=self.original('0x1003bffac');self.order(s,['*(undefined8 *)(param_3 + 0x50) = param_1','FUN_1003c1c60(param_1,FUN_1003bc500'])
        for t in ['JSONDecoder','ClipboardItem','resolvedItem']:self.assertNotIn(t,s)
    def test_original_editor_reads_canonical_URL_not_readonly_network_loader(self):
        self.order(self.original('0x1003bf65c'),['FUN_10031ebc8','FUN_100317b10','_swift_getEnumCaseMultiPayload','Foundation::URL::typeMetadataAccessor'])
        self.assertIn('FUN_1003bf65c(',self.original('0x1003e944c'));self.assertIn('LinkItemContentView::viewModel',self.original('0x1003e8490'));self.assertIn('loadRequest',self.original('0x1003e8640'))
    def test_native_link_branch_precedes_old_archive_resolution_and_uses_same_handle(self):
        s=body(self.adapter,'func makeOriginalReplicaNativePreview(');b=body(s,'if rawType == 4');self.order(s,['if rawType == 4','ReplicaLinkPreviewContent(state: state, item: nil, input: input)','return makeOriginalReplicaPreview(state: state, item: input.resolvedItem(), input: input)'])
        for t in ['resolvedItem','store.items','ClipboardItem(','JSONDecoder']:self.assertNotIn(t,b)
        self.assertIn('makeReplicaContentPreview(state: state, item: nil, input: input, content: content',b)
    def test_constructor_gets_identity_without_materializing_optional_DTO(self):
        s=body(self.link,'init(state: ReplicaUIState, item: ClipboardItem?, input:');self.order(s,['guard let itemID = input?.id ?? item?.id','self.itemID = itemID','editInput = input','makeReplicaReadOnlyPreviewContent(store: state.store, itemID: itemID)','super.init'])
        self.assertIn('preconditionFailure("Link preview requires an item")',s)
        for t in ['resolvedItem','item.kind','JSONDecoder','item.content']:self.assertNotIn(t,s)
    def test_native_observer_is_preferred_and_initial_native_model_is_delivered(self):
        s=body(self.link,'init(state: ReplicaUIState, item: ClipboardItem?, input:');self.order(s,['itemObservation = input?.observeChanges','self?.receiveNativeModel(current)','if itemObservation != nil, let input','receiveNativeModel(input)','else {','state.store.$items.sink'])
    def test_begin_editing_reads_current_native_URL_and_receive_replaces_handle(self):
        s=body(self.link,'private func currentURL()');self.order(s,['editInput?.previewLinkURL()','return url','state?.store.items'])
        self.order(body(self.link,'private func receiveNativeModel('),['editInput = input','updateMetadata(currentURL())'])
        self.order(body(self.link,'func beginPreviewEditing()'),['textView.f_1000f733c(currentURL()?.absoluteString','showContent(textView)','updateCanCommit()','window?.makeFirstResponder(textView)'])
    def test_nine_existing_edit_write_cancel_and_metadata_methods_unchanged(self):
        self.assertEqual(len(self.p['unchanged_methods']),9)
        for r in self.p['unchanged_methods']:self.assertEqual(hashlib.sha256(body(pre_preview_commit_error((ROOT/r['path']).read_text()),r['symbol']).encode()).hexdigest(),r['sha256'])
    def test_readonly_view_remains_explicit_store_adapter_and_ID_overload_only(self):
        self.assertIn('makeReplicaReadOnlyPreviewContent(store: store, itemID: item.id)',body(self.ro,'func makeReplicaReadOnlyPreviewContent(store: ClipboardStore, item:'))
        s=body(self.ro,'func makeReplicaReadOnlyPreviewContent(store: ClipboardStore, itemID:');self.assertIn('NSHostingView(rootView: ReplicaReadOnlyPreviewContent(store: store, itemID: itemID))',s);self.assertNotIn('items.first',s)
        r=self.p['readonly_struct'];s=body(self.ro,r['symbol']);self.assertIn('store.items.first',s);self.assertEqual(hashlib.sha256(s.encode()).hexdigest(),r['sha256'])
    def test_current_handle_store_controller_and_popover_four_shared_sources_unchanged(self):
        self.assertEqual(len(self.p['shared_sources']),4)
        for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_native_list_navigation_bytes(ROOT/p)).hexdigest(),h);self.assertEqual(h,self.base['production'][p])
    def test_four_exact_hunks_only_three_sources_preserve_all247_files(self):
        self.assertEqual(len(CHANGES),4);paths={str(p.relative_to(ROOT))for p in(ROOT/'replica/Sources').rglob('*')if p.is_file()};self.assertEqual(paths,set(self.base['production']));changed=[]
        for p,h in self.base['production'].items():
            b=pre_native_list_navigation_bytes(ROOT/p)
            if hashlib.sha256(b).hexdigest()!=h:changed.append(p)
            restored=pre_native_link_creation(b.decode()).encode()if p.endswith('.swift')else b;self.assertEqual(hashlib.sha256(restored).hexdigest(),h)
        self.assertEqual(set(changed),set(self.p['current_sources']))
        for p,h in self.p['current_sources'].items():self.assertEqual(hashlib.sha256(pre_native_list_navigation_bytes(ROOT/p)).hexdigest(),h)
    def test_reversal_is_idempotent_and_old_compatibility_factory_is_unchanged(self):
        for p,s in self.src.items():
            old=(self.phase/'before'/p).read_text();self.assertEqual(pre_native_link_creation(s),old);self.assertEqual(pre_native_link_creation(old),old)
        p='replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift';self.assertEqual(body(self.adapter,'func makeOriginalReplicaPreview('),body((self.phase/'before'/p).read_text(),'func makeOriginalReplicaPreview('))
    def test_scope_does_not_double_count_existing_factory_or_claim_full_P1(self):
        self.assertEqual(self.p['new_difference_records'],0);self.assertEqual(self.p['additional_contract_function_id'],'Paste:0x1003c3c90');self.assertTrue(self.p['finite_contract_verified']);self.assertFalse(self.p['full_function_migration_verified']);self.assertFalse(self.p['runtime_executed']);self.assertEqual(len(self.p['adaptations']),2);self.assertIn('P2',self.p['remaining'][0]);self.assertIn('04430c/0f733c',self.p['remaining'][1])
if __name__=='__main__':unittest.main()
