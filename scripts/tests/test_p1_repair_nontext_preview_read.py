"""Native color/link metadata and event contracts: source/Mach-O checks only."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment
from nontext_preview_read_scope_contract import CHANGES,pre_nontext_preview_read
from image_preview_read_scope_contract import pre_image_preview_read,pre_image_preview_read_bytes

class NontextPreviewReadContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-102';cls.proof=json.loads((cls.phase/'nontext-preview-read-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.src={p:pre_image_preview_read((ROOT/p).read_text())for p in cls.proof['current_sources']}
        cls.handle=cls.src['replica/Sources/PastoCore/ClipboardRestoreItem.swift'];cls.adapter=cls.src['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift'];cls.color=cls.src['replica/Sources/Pasto/UI/ReplicaColorPreviewContent.swift'];cls.link=cls.src['replica/Sources/Pasto/UI/ReplicaLinkPreviewContent.swift']
        ns={};exec((ROOT/cls.proof['decoder']['path']).read_text().split("idx={r['address']",1)[0],ns);cls.ns=ns
    def original(self,a):
        r=next(r for r in self.proof['original_fragments']if r['address']==a);return original_fragment((ROOT/r['path']).read_text(),a[2:])
    def order(self,s,tokens):
        pos=[s.index(t)for t in tokens];self.assertEqual(pos,sorted(pos))
    def test_original_fragments_binary_and_reused_observers_bound(self):
        self.assertEqual(len(self.proof['original_fragments']),21)
        for r in self.proof['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for r in [self.proof['binary'],self.proof['decoder']]+self.proof['reused_evidence']:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_seventeen_actual_ARM_calls_bind_model_metadata_and_UI_consumers(self):
        self.assertEqual(len(self.proof['ARM_calls']),17)
        for r in self.proof['ARM_calls']:
            pc=int(r['address'],16);b=self.ns['read'](pc,4);self.assertEqual(b.hex(),r['bytes']);w=int.from_bytes(b,'little');self.assertEqual(w&0x7c000000,0x14000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(pc+4*d,int(r['target'],16))
    def test_actual_entity_store_precedes_callback_and_editing_gate_precedes_redraw(self):
        words={r['address']:r['bytes']for r in self.proof['ARM_words']};self.assertEqual(len(words),10)
        for a,b in words.items():self.assertEqual(self.ns['read'](int(a,16),4).hex(),b)
        self.assertEqual(words['0x1003bbf88'],'142800f9');self.assertEqual(words['0x1003bbfec'],'a0023fd6');self.assertEqual(words['0x1003e16e0'],'28010037')
        s=self.original('0x1003bbf5c');self.order(s,['*(undefined8 *)(lVar1 + 0x50) = param_1','_swift_beginAccess(param_3 + 0x10','(*pcVar3)()']);self.assertNotIn('isDeleted',s)
    def test_original_metadata_getter_reads_rawPreview_not_raw_pasteboard_items(self):
        s=self.original('0x10031ebc8');self.assertIn('objc_stub::rawPreview',s);self.assertNotIn('objc_stub::data(',s)
        for a in ['0x1003bbc20','0x1003bf65c']:self.assertIn('FUN_10031ebc8',self.original(a))
        self.assertIn('not Item.data',self.proof['correction'])
    def test_native_color_reader_uses_canonical_metadata_and_black_fallback(self):
        s=body(self.handle,'public func previewColor()');self.order(s,['guard let object = nativeObject','decodeColor(object.value(forKey: "rawPreview")','return .black','OriginalColorPreviewMetadataGenerator.color(metadata.code)'])
        for t in ['resolvedItem','store.','UUID','ClipboardPersistence','fetch(']:self.assertNotIn(t,s)
        self.assertIn('objc_stub::blackColor',self.original('0x1003bbc20'))
    def test_native_link_reader_requires_canonical_current_metadata_without_stale_fallback(self):
        s=body(self.handle,'public func previewLinkURL()');self.order(s,['guard let object = nativeObject','decodeLink(object.value(forKey: "rawPreview")','preconditionFailure("Link preview requires canonical link metadata")','return metadata.url'])
        for t in ['resolvedItem','store.','UUID','ClipboardPersistence','try?']:self.assertNotIn(t,s)
        self.assertIn('SoftwareBreakpoint',self.original('0x1003bf65c'))
    def test_native_color_factory_reads_type_once_and_needs_no_DTO(self):
        s=body(self.adapter,'func makeOriginalReplicaNativePreview(');self.assertEqual(s.count('input.previewRawType()'),1);self.order(s,['let rawType = input.previewRawType()','if rawType == 5','if rawType == 2','ReplicaColorPreviewContent(state: state, item: nil, input: input)','makeReplicaContentPreview(state: state, item: nil, input: input','return makeOriginalReplicaPreview(state: state, item: input.resolvedItem()'])
        self.assertNotIn('resolvedItem',body(s,'if rawType == 2'));self.assertNotIn('ClipboardItem(',s)
    def test_shared_nontext_chrome_is_exact_old_factory_tail(self):
        old=body((self.phase/'before/replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift').read_text(),'func makeOriginalReplicaPreview(');tail=old[old.index('    let header ='):];self.assertEqual(body(self.adapter,'private func makeReplicaContentPreview('),'{\n'+tail)
        factory=body(self.adapter,'func makeOriginalReplicaPreview(');self.assertIn('return makeReplicaContentPreview(state: state, item: item, input: input',factory)
    def test_native_color_optional_constructor_needs_handle_identity_only(self):
        s=body(self.color,'init(state: ReplicaUIState, item: ClipboardItem?, input: ClipboardRestoreItem? = nil)');self.order(s,['guard let itemID = input?.id ?? item?.id','self.itemID = itemID','editInput = input','super.init','input?.observeChanges','receiveNativeModel(input)'])
        self.assertNotIn('resolvedItem',s);self.assertIn('item: ClipboardItem?',self.color)
    def test_both_observers_subscribe_before_initial_read_and_keep_legacy_branch(self):
        for s in [self.color,self.link]:
            init=body(s,'init(state: ReplicaUIState, item:');self.order(init,['itemObservation = input?.observeChanges','self?.receiveNativeModel(current)','if itemObservation != nil, let input','receiveNativeModel(input)','} else {','itemObservation = state.store.$items.sink'])
            self.assertIn('[weak self] current in',init);self.assertIn('items.first(where: { $0.id == self.itemID })',init)
    def test_color_receives_current_entity_before_editing_display_gate(self):
        s=body(self.color,'private func receiveNativeModel(');self.order(s,['editInput = input','guard !editing else { return }','display(currentModelColor())'])
        for t in ['isDeleted','store.','resolvedItem','removeDuplicates','DispatchQueue']:self.assertNotIn(t,s)
        read=body(self.color,'private func currentModelColor()');self.order(read,['editInput?.previewColor()','return color','return state?.store.items.first'])
        orig=self.original('0x1003e16b4');self.order(orig,['ColorItemContentView::isEditing','FUN_1003bbc20()','FUN_1003e1724()'])
    def test_color_edit_cancel_and_comparison_read_new_model_without_overwriting_active_display(self):
        for signature in ['func beginPreviewEditing()','func cancelPreviewEditing()','@objc private func colorChanged()']:self.assertIn('currentModelColor()',body(self.color,signature))
        for editing in [False,True]:
            model='old';display='editing'if editing else'old';model='new'
            if not editing:display=model
            self.assertEqual(model,'new');self.assertEqual(display,'editing'if editing else'new')
    def test_link_event_refreshes_metadata_after_entity_update_without_editor_write(self):
        s=body(self.link,'private func receiveNativeModel(');self.order(s,['editInput = input','updateMetadata(currentURL())'])
        for t in ['textView','showContent','isDeleted','resolvedItem','store.','editing']:self.assertNotIn(t,s)
        read=body(self.link,'private func currentURL()');self.order(read,['editInput?.previewLinkURL()','return url','return state?.store.items.first'])
        self.assertNotIn('setText_',self.original('0x1003e8640'))
    def test_link_open_edit_cancel_and_commit_use_current_URL_and_keep_write_identity(self):
        init=body(self.link,'init(state: ReplicaUIState, item:');self.assertIn('self?.currentURL()',init)
        for signature in ['func beginPreviewEditing()','func cancelPreviewEditing()','func commitPreviewEditing()']:self.assertIn('currentURL()',body(self.link,signature))
        self.assertIn('private var editInput: ClipboardRestoreItem?',self.color);self.assertIn('private var editInput: ClipboardRestoreItem?',self.link)
        self.assertIn('updateColorItem(editInput',body(self.color,'func commitPreviewEditing()'));self.assertIn('updateLinkItem(editInput',body(self.link,'func commitPreviewEditing()'))
    def test_public_getters_and_cross_file_factories_have_real_declarations(self):
        self.assertIn('import AppKit',self.handle);self.assertIn('public func previewColor() -> NSColor?',self.handle);self.assertIn('public func previewLinkURL() -> URL?',self.handle)
        codec=(ROOT/'replica/Sources/PastoCore/OriginalImagePreviewMetadataCodec.swift').read_text()
        for name in ['decodeColor','decodeLink']:self.assertIn('public static func '+name+'(',codec)
        self.assertIn('item: ClipboardItem?, input: ClipboardRestoreItem?',self.adapter)
    def test_seventeen_existing_methods_and_ten_shared_sources_remain_unchanged(self):
        self.assertEqual(len(self.proof['unchanged_methods']),17);self.assertEqual(len(self.proof['shared_sources']),10)
        for r in self.proof['unchanged_methods']:
            s=body(pre_image_preview_read((ROOT/r['path']).read_text()),r['symbol']);self.assertEqual(hashlib.sha256(s.encode()).hexdigest(),r['sha256']);self.assertEqual(s,body((self.phase/'before'/r['path']).read_text(),r['symbol']))
        for p,h in self.proof['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_image_preview_read_bytes(ROOT/p)).hexdigest(),h);self.assertEqual(h,self.base['production'][p])
    def test_eleven_hunks_four_files_and_historical_reversal_are_exact(self):
        self.assertEqual(len(CHANGES),11);sha=lambda p:hashlib.sha256(pre_image_preview_read_bytes(ROOT/p)).hexdigest();files={str(p.relative_to(ROOT))for p in(ROOT/'replica/Sources').rglob('*')if p.is_file()};self.assertEqual(files,set(self.base['production']))
        self.assertEqual({p for p,h in self.base['production'].items()if sha(p)!=h},set(self.src))
        for p,s in self.src.items():
            old=(self.phase/'before'/p).read_text();self.assertEqual(pre_nontext_preview_read(s),old);self.assertEqual(pre_nontext_preview_read(old),old);self.assertEqual(sha(p),self.proof['current_sources'][p])
    def test_finite_reads_events_and_color_creation_do_not_claim_full_deletion_or_codec(self):
        self.assertEqual(self.proof['new_difference_records'],3);self.assertEqual({r['function_id']for r in self.proof['contracts']},{'Paste:0x1003bbc20','Paste:0x1003bf65c','Paste:0x1003bbf5c'});self.assertTrue(self.proof['finite_contract_verified']);self.assertFalse(self.proof['full_function_migration_verified']);self.assertFalse(self.proof['runtime_executed'])
        for t in ['Link readonly','deletion','DI/ABI','Image','04430c']:self.assertTrue(any(t in s for s in self.proof['remaining']),t)
