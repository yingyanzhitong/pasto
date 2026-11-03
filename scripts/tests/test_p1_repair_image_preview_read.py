"""Native image explicit reads/size/refresh: source and Mach-O contracts only."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from native_group_write_scope_contract import pre_native_group_write_bytes
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment
from image_preview_read_scope_contract import CHANGES,pre_image_preview_read

class ImagePreviewReadContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-103';cls.proof=json.loads((cls.phase/'image-preview-read-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.src={p:(ROOT/p).read_text()for p in cls.proof['current_sources']};cls.handle=cls.src['replica/Sources/PastoCore/ClipboardRestoreItem.swift'];cls.image=cls.src['replica/Sources/Pasto/UI/ReplicaImagePreviewContent.swift'];cls.adapter=cls.src['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift']
        ns={};exec((ROOT/cls.proof['decoder']['path']).read_text().split("idx={r['address']",1)[0],ns);cls.ns=ns
    def original(self,a):
        r=next(r for r in self.proof['original_fragments']if r['address']==a);return original_fragment((ROOT/r['path']).read_text(),a[2:])
    def order(self,s,tokens):
        cursor=0
        for token in tokens:cursor=s.index(token,cursor)+len(token)
    def test_twenty_one_original_fragments_binary_and_shared_contracts_bound(self):
        self.assertEqual(len(self.proof['original_fragments']),21)
        for r in self.proof['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for r in [self.proof['binary'],self.proof['decoder']]+self.proof['reused_evidence']:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_twenty_actual_calls_bind_reader_size_initial_cancel_and_commit(self):
        self.assertEqual(len(self.proof['ARM_calls']),20)
        for r in self.proof['ARM_calls']:
            pc=int(r['address'],16);b=self.ns['read'](pc,4);self.assertEqual(b.hex(),r['bytes']);w=int.from_bytes(b,'little');self.assertEqual(w&0x7c000000,0x14000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(pc+4*d,int(r['target'],16))
    def test_complete_constructor_commit_cancel_direct_call_inventories_are_bound(self):
        self.assertEqual(len(self.proof['direct_call_inventories']),3)
        for row in self.proof['direct_call_inventories']:
            calls=[]
            for pc in range(int(row['function'],16),int(row['end'],16),4):
                b=self.ns['read'](pc,4);w=int.from_bytes(b,'little')
                if w&0xfc000000!=0x94000000:continue
                d=w&0x3ffffff
                if d&0x2000000:d-=0x4000000
                calls.append(dict(address=hex(pc),bytes=b.hex(),target=hex(pc+4*d)))
            self.assertEqual(calls,row['calls'])
        ctor,commit,cancel=self.proof['direct_call_inventories']
        self.assertFalse({r['target']for r in ctor['calls']}&{'0x1003c1c60','0x1003c1c84','0x100355fb8'})
        self.assertNotIn('0x1003bd9cc',{r['target']for r in commit['calls']});self.assertIn('0x1003bd9cc',{r['target']for r in cancel['calls']})
    def test_parent_header_observer_is_preserved_not_misreported_absent(self):
        self.assertIn('FUN_1003c1c60',self.original('0x1003c25dc'));self.assertIn('objc_stub::isDeleted',self.original('0x10007b8cc'));self.assertIn('FUN_100011e00',self.original('0x10007b8cc'))
        self.assertIn('___lazy_storage___contentView',self.original('0x10007ac34'))
        header=self.adapter[self.adapter.index('private final class ReplicaInlinePreviewHeader:'):];self.assertIn('input?.observeChanges(receive)',header);self.assertIn('self.window?.performClose(nil)',header)
        self.assertIn('parent ItemPreviewViewModel still observes',self.proof['correction'])
    def test_image_reader_depends_only_on_native_data_and_ordered_representations(self):
        s=body(self.handle,'public func previewImage()');self.order(s,['guard let object = nativeObject','ClipboardItemDataPersistence.readItems(from: object)','for item in items','guard let data = item.f_10037d5c4()','NSImage(data: data) != nil','return item.f_10037d5c4().flatMap(NSImage.init(data:))','return nil'])
        self.assertEqual(s.count('f_10037d5c4'),2)
        for t in ['resolvedItem','ClipboardPersistence','rawPreview','state.','UUID','sourceApplication','observeChanges']:self.assertNotIn(t,s)
    def test_original_reader_uses_data_and_repeats_successful_representation_getter(self):
        s=self.original('0x1003bd9cc');self.order(s,['objc_stub::data','FUN_10031b218()','FUN_10037d5c4()','objc_stub::initWithData_','if (IVar10 != 0)','FUN_10037d5c4()'])
        self.assertEqual(s.count('FUN_10037d5c4()'),2)
        for valid in [(False,False),(False,True),(True,False),(True,True)]:self.assertEqual(next((i for i,v in enumerate(valid)if v),None),0 if valid[0]else 1 if valid[1]else None)
    def test_size_reads_current_rawPreview_with_zero_fallback_and_no_image_decode(self):
        s=body(self.handle,'public func previewImageSize()');self.order(s,['guard let object = nativeObject','OriginalImagePreviewMetadataCodec.decode(object.value(forKey: "rawPreview")','?.size ?? .zero'])
        for t in ['previewImage()','NSImage(','resolvedItem','store.','readItems']:self.assertNotIn(t,s)
        self.assertIn('FUN_10031ebc8',self.original('0x1003bd784'));self.assertIn('FUN_1003bd784',self.original('0x1003bd740'))
    def test_native_preferred_size_reuses_exact_existing_scaling_body(self):
        now=body(self.image,'var preferredPreviewSize:');old=body((self.phase/'before/replica/Sources/Pasto/UI/ReplicaImagePreviewContent.swift').read_text(),'var preferredPreviewSize:');self.assertEqual(now,old.replace('let imageSize = imageMetadataSize','let imageSize = editInput?.previewImageSize() ?? imageMetadataSize'))
        self.assertIn('NSScreen.main!.frame.size',now);self.assertNotIn('previewImage()',now)
    def test_native_image_factory_uses_handle_without_DTO_before_shared_chrome(self):
        s=body(self.adapter,'func makeOriginalReplicaNativePreview(');self.assertEqual(s.count('input.previewRawType()'),1);self.order(s,['if rawType == 1','ReplicaImagePreviewContent(state: state, item: nil, input: input)','makeReplicaContentPreview(state: state, item: nil, input: input','return makeOriginalReplicaPreview(state: state, item: input.resolvedItem()'])
        self.assertNotIn('resolvedItem',body(s,'if rawType == 1'))
    def test_optional_native_constructor_does_not_require_legacy_value(self):
        init=body(self.image,'init(state: ReplicaUIState, item: ClipboardItem?, input: ClipboardRestoreItem? = nil)');self.order(init,['guard let itemID = input?.id ?? item?.id','self.itemID = itemID','editInput = input','super.init','if input?.hasNativeEntity == true'])
        native=body(init,'if input?.hasNativeEntity == true');self.order(native,['zoomView.f_100240a64(input?.previewImage())','zoomView.f_100240be8(false)','updateMetadataAndCommitState()'])
        for t in ['store.','resolvedItem','itemObservation','performClose','observeChanges']:self.assertNotIn(t,native)
    def test_native_initial_and_cancel_are_explicit_reads_legacy_keeps_subscription(self):
        init=body(self.image,'init(state: ReplicaUIState, item:');self.order(init,['if input?.hasNativeEntity == true','else if let item = item ?? input?.resolvedItem()','replaceDisplayedItem(item)','itemObservation = state.store.$items.sink','self.window?.performClose(nil)'])
        cancel=body(self.image,'func cancelPreviewEditing()');self.assertIn('finishEditing(reloadNativeImage: true)',cancel)
        self.assertNotIn('observeChanges',self.image)
    def test_native_commit_does_not_decode_saved_pixels_again(self):
        commit=body(self.image,'func commitPreviewEditing()');self.order(commit,['zoomView.f_100240a18()','updateImagePreviewItem(editInput','finishEditing(reloadNativeImage: false)']);self.assertNotIn('previewImage()',commit)
        finish=body(self.image,'private func finishEditing(reloadNativeImage: Bool)');native=body(finish,'if editInput?.hasNativeEntity == true');self.assertIn('if reloadNativeImage { zoomView.f_100240a64(editInput?.previewImage()) }',native)
        self.assertEqual(native.count('previewImage()'),1);self.assertNotIn('store.',native)
        self.assertNotIn('FUN_1003bd9cc',self.original('0x1003e5dd4'));self.assertIn('FUN_1003bd9cc',self.original('0x1003e5cf0'))
    def test_finish_preserves_canvas_commit_and_clears_editing_before_metadata(self):
        s=body(self.image,'private func finishEditing(reloadNativeImage: Bool)');native=body(s,'if editInput?.hasNativeEntity == true');self.order(native,['if reloadNativeImage','zoomView.f_100240be8(false)','quarterTurns = 0','editingUndoManager.removeAllActions()','updateMetadataAndCommitState()','return'])
        self.assertIn('isEditing = false',s[:s.index('if editInput?')]);self.assertNotIn('encodedPayloads',native)
    def test_legacy_finish_tail_retains_old_force_reload(self):
        now=body(self.image,'private func finishEditing(reloadNativeImage: Bool)');old=body((self.phase/'before/replica/Sources/Pasto/UI/ReplicaImagePreviewContent.swift').read_text(),'private func finishEditing()');marker='        quarterTurns = 0\n';legacy=now[now.index(marker,now.index('            return\n')):];self.assertEqual(legacy,old[old.index(marker):])
    def test_public_getters_and_identity_gate_have_real_accessible_definitions(self):
        self.assertIn('public var hasNativeEntity: Bool { nativeObject != nil }',self.handle);self.assertIn('public func previewImage() -> NSImage?',self.handle);self.assertIn('public func previewImageSize() -> NSSize?',self.handle)
        self.assertIn('import AppKit',self.handle);reader=(ROOT/'replica/Sources/PastoCore/ClipboardItemDataPersistence.swift').read_text();self.assertIn('@MainActor static func readItems(from object: PastoItemEntity)',reader)
    def test_fourteen_methods_and_seven_shared_sources_remain_unchanged(self):
        self.assertEqual(len(self.proof['unchanged_methods']),14);self.assertEqual(len(self.proof['shared_sources']),7)
        for r in self.proof['unchanged_methods']:
            s=body((ROOT/r['path']).read_text(),r['symbol']);self.assertEqual(hashlib.sha256(s.encode()).hexdigest(),r['sha256']);self.assertEqual(s,body((self.phase/'before'/r['path']).read_text(),r['symbol']))
        for p,h in self.proof['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_native_group_write_bytes(ROOT/p)).hexdigest(),h);self.assertEqual(h,self.base['production'][p])
    def test_nine_exact_hunks_three_files_and_historical_reversal_are_idempotent(self):
        self.assertEqual(len(CHANGES),9);sha=lambda p:hashlib.sha256(pre_native_group_write_bytes(ROOT/p)).hexdigest();files={str(p.relative_to(ROOT))for p in(ROOT/'replica/Sources').rglob('*')if p.is_file()};self.assertEqual(files,set(self.base['production']));self.assertEqual({p for p,h in self.base['production'].items()if sha(p)!=h},set(self.src))
        for p,s in self.src.items():
            old=(self.phase/'before'/p).read_text();self.assertEqual(pre_image_preview_read(s),old);self.assertEqual(pre_image_preview_read(old),old);self.assertEqual(sha(p),self.proof['current_sources'][p])
    def test_three_finite_contracts_leave_full_task_undo_codec_and_DI_open(self):
        self.assertEqual(self.proof['new_difference_records'],3);self.assertEqual({r['function_id']for r in self.proof['contracts']},{'Paste:0x1003bd9cc','Paste:0x1003bd740','Paste:0x1003e5dd4'});self.assertTrue(self.proof['finite_contract_verified']);self.assertFalse(self.proof['full_function_migration_verified']);self.assertFalse(self.proof['runtime_executed'])
        for t in ['Link readonly','debounce','Invalid native','04430c']:self.assertTrue(any(t in s for s in self.proof['remaining']),t)
