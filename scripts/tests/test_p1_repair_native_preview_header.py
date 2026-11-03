"""Native preview header source dependency contracts; no framework execution."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment
from native_preview_header_scope_contract import CHANGES,pre_native_preview_header
from text_preview_creation_scope_contract import pre_text_preview_creation,pre_text_preview_creation_bytes

class NativePreviewHeaderContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-99';cls.proof=json.loads((cls.phase/'native-preview-header-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text())
        cls.src={p:pre_text_preview_creation((ROOT/p).read_text())for p in cls.proof['current_sources']}
        cls.handle=cls.src['replica/Sources/PastoCore/ClipboardRestoreItem.swift'];cls.data=cls.src['replica/Sources/PastoCore/ClipboardItemDataPersistence.swift'];cls.observer=cls.src['replica/Sources/PastoCore/ClipboardItemObservation.swift'];cls.adapter=cls.src['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift']
        cls.header=cls.adapter[cls.adapter.index('private final class ReplicaInlinePreviewHeader:'):];cls.init=body(cls.header,'init(state: ReplicaUIState, item: ClipboardItem, input: ClipboardRestoreItem?)')
        ns={};exec((ROOT/cls.proof['decoder']['path']).read_text().split("idx={r['address']",1)[0],ns);cls.ns=ns
    def original(self,a):
        r=next(r for r in self.proof['original_fragments']if r['address']==a);return original_fragment((ROOT/r['path']).read_text(),a[2:])
    def order(self,s,tokens):
        pos=[s.index(t)for t in tokens];self.assertEqual(pos,sorted(pos))
    def test_original_fragments_and_evidence_are_current(self):
        self.assertEqual(len(self.proof['original_fragments']),14)
        for r in self.proof['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for r in [self.proof['binary'],self.proof['decoder']]+self.proof['reused_evidence']:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_actual_ARM_header_getters_and_share_click_calls(self):
        self.assertEqual(len(self.proof['ARM_calls']),12)
        for r in self.proof['ARM_calls']:
            pc=int(r['address'],16);b=self.ns['read'](pc,4);self.assertEqual(b.hex(),r['bytes']);w=int.from_bytes(b,'little');self.assertEqual(w&0x7c000000,0x14000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(pc+4*d,int(r['target'],16))
    def test_original_header_reads_metadata_before_share_enable(self):
        self.order(self.original('0x100011e00'),['FUN_100309008()','FUN_10023b600(','FUN_100308f88(','FUN_10023b214(','FUN_10031bc94()','FUN_100320cc0()'])
        self.assertIn('objc_stub::title',self.original('0x100308f88'));self.assertIn('if (uVar1 != 0)',self.original('0x100308f88'))
    def test_title_reads_native_fields_without_DTO_projection(self):
        s=body(self.handle,'public func previewTitle()');self.order(s,['guard let object = nativeObject','value(forKey: "rawType")','rawType == 3','decodeFiles(object.value(forKey: "rawPreview")','f_100309008','f_100308f88(object.value(forKey: "title")'])
        for token in ['resolvedItem','ClipboardPersistence','sourceApplication','displayOrder','fetch(','store.','UUID()']:self.assertNotIn(token,s)
    def test_new_cross_file_API_symbols_exist_with_accessible_signatures(self):
        codec=(ROOT/'replica/Sources/PastoCore/OriginalImagePreviewMetadataCodec.swift').read_text()
        self.assertIn('public enum OriginalImagePreviewMetadataCodec',codec);self.assertIn('public static func decodeFiles(',codec)
        self.assertNotIn('OriginalItemPreviewMetadataCodec',self.handle)
        self.assertIn('@MainActor static func readItems(from object: PastoItemEntity)',self.data)
        for name in ['previewTitle','previewPinboard','previewSharingContent']:self.assertIn('public func '+name+'()',self.handle)
    def test_owner_must_be_native_pinboard_type_before_attributes(self):
        s=body(self.handle,'public func previewPinboard()');self.order(s,['guard let object = nativeObject','value(forKey: "list")','value(forKey: "rawType")','== 2','return (false, nil)','OriginalPinboardAttributes.colorCode'])
        self.assertNotIn('store.',s);self.assertNotIn('resolvedItem',s)
        self.assertIn('objc_stub::list',self.original('0x10031bc94'));self.assertIn('return IVar1 == 2',self.original('0x1003250f0'))
    def test_shared_reader_extraction_preserves_prior_exception_policy(self):
        old=body((self.phase/'before/replica/Sources/PastoCore/ClipboardItemObservation.swift').read_text(),'public var attributedText:')
        expected=old.replace('        guard !object.isDeleted else { return nil }\n','').replace('return NSAttributedString(string: "")','return []').replace('        let items = autoreleasepool { OriginalPasteboardDataCodec.f_10031aeec(raw) }\n        return items.first?.f_10037d33c() ?? NSAttributedString(string: "")','        return autoreleasepool { OriginalPasteboardDataCodec.f_10031aeec(raw) }')
        s=body(self.data,'@MainActor static func readItems(');self.assertEqual(s,expected)
        self.order(s,['object.value(forKey: "data")','OriginalObjCExceptionBridge','data.value(forKey: "rawPasteboardItems")','catch is OriginalObjCExceptionError','return []','catch { return nil }','autoreleasepool'])
    def test_text_observer_keeps_deleted_guard_and_first_representation_semantics(self):
        s=body(self.observer,'public var attributedText:');self.order(s,['guard !object.isDeleted','ClipboardItemDataPersistence.readItems(from: object)','items.first?.f_10037d33c()','NSAttributedString(string: "")'])
        self.assertNotIn('resolvedItem',s);self.assertNotIn('ClipboardPersistence',s)
    def test_native_sharing_reads_same_entity_archive_and_type(self):
        s=body(self.handle,'public func previewSharingContent()');self.order(s,['guard let object = nativeObject','object.value(forKey: "rawType")','ClipboardItemDataPersistence.readItems(from: object) ?? []','rawType: rawType'])
        for token in ['store.','resolvedItem','ClipboardPersistence','UUID','Date()']:self.assertNotIn(token,s)
    def test_delete_closes_before_native_refresh_and_legacy_fallback(self):
        s=body(self.init,'let receive: (ClipboardRestoreItem) -> Void =');self.order(s,['if current.isDeleted','f_100011d28()','performClose(nil)','\n                return\n','if let title = current.previewTitle()','current.previewPinboard()','current.previewSharingContent()','} else {','update(current.resolvedItem())'])
        self.assertNotIn('resolvedItem',body(s,'if let title = current.previewTitle()'));self.assertIn('[weak self, weak share]',s)
    def test_initial_and_later_entity_events_share_the_native_consumer(self):
        tail=self.init[self.init.index('itemObservation = input?.observeChanges(receive)'):]
        self.order(tail,['input?.observeChanges(receive)','if itemObservation != nil, let input','receive(input)','} else {','state.store.$items.sink'])
        self.assertIn('self.input = input',self.init);self.assertIn('private let input: ClipboardRestoreItem?',self.header)
    def test_group_signal_avoids_deleted_native_reads_and_stale_store_join(self):
        s=body(self.init,'pinboardObservation = state.store.$pinboards.sink');self.order(s,['self.input?.isDeleted != true','if let pin = self.input?.previewPinboard()','refreshNativePinAppearance','} else if let item = self.state?.store.items.first'])
        self.assertNotIn('store.',body(s,'if let pin = self.input?.previewPinboard()'))
        native=body(self.header,'private func refreshNativePinAppearance(');self.assertIn('isPinned ? "circle.fill" : "circle.dashed"',native);self.assertIn('OriginalPinboardColor(canonicalColorCode: $0).color()',native)
    def test_share_click_uses_captured_entity_before_legacy_cache_lookup(self):
        s=body(self.header,'private func showSharingPicker(');self.order(s,['if let content = input?.previewSharingContent()','OriginalPreviewSharing.f_1000183e0([content])','sharingPicker = picker','picker.show(relativeTo: .zero, of: button, preferredEdge: .minY)','return','state.store.items.first'])
        self.order(self.original('0x10007a948'),['+ 0x70))()','FUN_1000183e0()','objc_stub::showRelativeToRect_ofView_preferredEdge_'])
    def test_ten_exact_hunks_four_files_and_shared_helpers_unchanged(self):
        self.assertEqual(len(CHANGES),10);files={str(p.relative_to(ROOT))for p in(ROOT/'replica/Sources').rglob('*')if p.is_file()};self.assertEqual(files,set(self.base['production']))
        sha=lambda p:hashlib.sha256(pre_text_preview_creation_bytes(ROOT/p)).hexdigest()
        self.assertEqual({p for p,h in self.base['production'].items()if sha(p)!=h},set(self.src))
        for p,s in self.src.items():self.assertEqual(pre_native_preview_header(s),(self.phase/'before'/p).read_text());self.assertEqual(sha(p),self.proof['current_sources'][p])
        for p,h in self.proof['shared_sources'].items():self.assertEqual(sha(p),h);self.assertEqual(h,self.base['production'][p])
        for r in self.proof['unchanged_methods']:self.assertEqual(hashlib.sha256(body(pre_text_preview_creation((ROOT/r['path']).read_text()),r['symbol']).encode()).hexdigest(),r['sha256'])
    def test_finite_dependency_fix_does_not_claim_entire_header_or_runtime_equivalence(self):
        self.assertEqual(self.proof['function_id'],'Paste:0x100011e00');self.assertEqual(self.proof['new_difference_records'],1);self.assertTrue(self.proof['finite_contract_verified']);self.assertFalse(self.proof['full_function_migration_verified']);self.assertFalse(self.proof['runtime_executed'])
        for token in ['Missing data','permissions','pinboards','04430c']:self.assertTrue(any(token in r for r in self.proof['remaining']),token)
