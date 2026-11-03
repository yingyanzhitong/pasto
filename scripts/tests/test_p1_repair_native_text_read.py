"""Native text source dependencies and updates: static source/ARM tests only."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2]
from text_preview_creation_scope_contract import pre_text_preview_creation
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment
from native_text_read_scope_contract import CHANGES,pre_native_text_read
from native_preview_header_scope_contract import pre_native_preview_header,pre_native_preview_header_bytes

class NativeTextReadContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-98';cls.proof=json.loads((cls.phase/'native-text-read-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text())
        cls.paths=dict(observer='replica/Sources/PastoCore/ClipboardItemObservation.swift',adapter='replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift')
        cls.src={k:pre_native_preview_header((ROOT/p).read_text())for k,p in cls.paths.items()};cls.reader=body(cls.src['observer'],'public var attributedText:');cls.consume=body(cls.src['observer'],'private func consume(')
        start=cls.src['adapter'].index('private final class ReplicaInlineTextPreviewContent:');end=cls.src['adapter'].index('private final class ReplicaPreviewActionMenuItem:',start);cls.text=cls.src['adapter'][start:end]
        ns={};exec((ROOT/cls.proof['decoder']['path']).read_text().split("idx={r['address']",1)[0],ns);cls.ns=ns
    def original(self,a):
        r=next(r for r in self.proof['original_fragments']if r['address']==a);return original_fragment((ROOT/r['path']).read_text(),a[2:])
    def order(self,s,tokens):
        pos=[s.index(t)for t in tokens];self.assertEqual(pos,sorted(pos))

    def test_twelve_original_fragments_binary_and_prior_entity_contracts_bound(self):
        self.assertEqual(len(self.proof['original_fragments']),12)
        for r in self.proof['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for r in [self.proof['binary'],self.proof['decoder']]+self.proof['reused_evidence']:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])

    def test_thirteen_actual_calls_bind_native_data_read_shared_formats_and_notification(self):
        self.assertEqual(len(self.proof['ARM_calls']),13)
        for r in self.proof['ARM_calls']:
            pc=int(r['address'],16);b=self.ns['read'](pc,4);self.assertEqual(b.hex(),r['bytes']);w=int.from_bytes(b,'little');self.assertEqual(w&0x7c000000,0x14000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(pc+4*d,int(r['target'],16))

    def test_raw_pasteboard_selector_is_bound_to_real_dyld_chain(self):
        r=self.proof['raw_selector'];self.assertEqual(self.ns['read'](int(r['stub'],16),20).hex(),r['stub_bytes']);a=int(r['pointer'],16);v,ch=self.ns['reachable_pointer'](a);self.assertEqual(ch,r['chain']);self.assertEqual(self.ns['read'](a,8).hex(),r['pointer_bytes']);target=self.ns['base']+(v&((1<<36)-1));self.assertEqual(target,int(r['selector_address'],16));self.assertEqual(self.ns['read'](target,30).split(b'\0')[0],b'rawPasteboardItems')

    def test_hidden_ARM_bridge_exception_branch_returns_actual_empty_storage(self):
        words={r['address']:r['bytes']for r in self.proof['ARM_words']}
        for a,b in words.items():self.assertEqual(self.ns['read'](int(a,16),4).hex(),b)
        self.assertEqual(words['0x10031b250'],'150d00b4');self.assertEqual(words['0x10031b3e0'],'ca842394');self.assertEqual(words['0x10031b3e8'],'006c40f9');self.assertEqual(words['0x10031b3ec'],'0e000014')
        r=self.proof['bridge_error_empty_array'];a=int(r['pointer'],16);v,ch=self.ns['reachable_pointer'](a);self.assertEqual(ch,r['chain']);self.assertEqual(self.ns['read'](a,8).hex(),r['bytes']);self.assertEqual(v&0xffffff,r['ordinal']);self.assertEqual(v>>63,1)
        raw=self.ns['raw'];off=r['import_record_offset'];self.assertEqual(raw[off:off+4].hex(),r['import_record_bytes']);encoded=struct.unpack_from('<I',raw,off)[0];self.assertGreater(encoded>>9,0);off=r['symbol_file_offset'];self.assertEqual(raw[off:raw.index(b'\0',off)].decode(),r['symbol']);self.assertEqual(r['symbol'],'__swiftEmptyArrayStorage')

    def test_original_text_reader_uses_current_data_first_item_and_shared_rich_plain_paths(self):
        s=self.original('0x1003c05d4');self.order(s,['objc_stub::data(*(ID *)(unaff_x20 + 0x38))','FUN_10031b218()','if (lVar4 == 0)','FUN_10037ebdc(','FUN_10037c9a8()'])
        self.assertIn('FUN_10031b1bc(',self.original('0x10031bc34'));self.assertIn('objc_stub::FUN_100c08760',self.original('0x10031b1bc'))
        for token in ['sourceApplication','timestamp','displayOrderInPinboard','ClipboardItem']:self.assertNotIn(token,s)

    def test_native_reader_avoids_archived_DTO_source_order_and_Date_dependencies(self):
        self.order(self.reader,['guard !object.isDeleted','object.value(forKey: "data")','OriginalObjCExceptionBridge.f_1002ffc68','data.value(forKey: "rawPasteboardItems")','autoreleasepool { OriginalPasteboardDataCodec.f_10031aeec(raw) }','items.first?.f_10037d33c()'])
        for token in ['ClipboardPersistence','resolvedItem','sourceApplication','timestamp','updatedAt','displayOrder','content"','UUID','Date()','fetch(','state.store']:self.assertNotIn(token,self.reader)
        self.assertEqual(self.reader.count('rawPasteboardItems'),1);self.assertNotIn('compactMap',self.reader)

    def test_exception_boundary_only_wraps_raw_getter_and_ObjC_error_emits_empty(self):
        self.order(self.reader,['guard let data = object.value(forKey: "data")','do {','raw = try OriginalObjCExceptionBridge','throw CocoaError(.fileReadCorruptFile)','catch is OriginalObjCExceptionError','return NSAttributedString(string: "")','catch { return nil }'])
        self.assertNotIn('try?',self.reader)
        s=body(self.consume,'for key in [NSInsertedObjectsKey');self.assertIn('if let attributedText { onTextChange?(attributedText) }',s)
        self.assertNotIn('attributedText.length',s)

    def test_text_notification_updates_current_entity_then_text_before_optional_DTO_adapter(self):
        self.order(self.consume,['let currentItem = current as! PastoItemEntity','guard !currentItem.isDeleted else { return }','object = currentItem','if let attributedText { onTextChange?(attributedText) }','if onChange != nil, let value { onChange?(value) }','\n            return\n'])
        self.assertEqual(self.consume.count('onTextChange?'),1);self.assertNotIn('DispatchQueue',self.consume);self.assertNotIn('removeDuplicates',self.consume)
        self.assertIn('public var onChange: ((ClipboardItem) -> Void)?',self.src['observer'])

    def test_actual_text_initializer_reads_native_text_after_subscribing_same_source(self):
        s=body(self.text,'init(state: ReplicaUIState, item: ClipboardItem, input: ClipboardRestoreItem?)')
        self.order(s,['if let input { nativeSource = input.observeItem() }','nativeItemObservation = nativeSource','initial = nativeSource.attributedText','originalText = initial','OriginalPreviewAttributedText.normalizedEditingText(initial)','nativeSource.onTextChange = { [weak self] current in','self?.receiveStoredText(current)'])
        self.assertNotIn('nativeSource.value',s);self.assertNotIn('nativeSource.onChange',s)

    def test_reload_and_event_update_both_baselines_and_preserve_active_editor(self):
        reload=body(self.text,'private func reloadStoredContent()');self.order(reload,['if let nativeItemObservation','nativeItemObservation.attributedText','replaceStoredText(current)','} else {','state?.store.items.first','replaceStoredModel(item)','displayStoredModel()'])
        receive=body(self.text,'private func receiveStoredText(');self.order(receive,['replaceStoredText(text)','if !self.text.isEditable { displayStoredModel() }'])
        replace=body(self.text,'private func replaceStoredText(');self.order(replace,['originalText = text','editingText = OriginalPreviewAttributedText.normalizedEditingText(originalText)'])
        self.assertNotIn('displayStoredModel',replace)

    def test_legacy_DTO_input_and_optional_client_adapter_keep_existing_semantics(self):
        self.assertIn('replaceStoredText(Self.attributedContent(item))',body(self.text,'private func replaceStoredModel('))
        init=body(self.text,'init(state: ReplicaUIState, item: ClipboardItem, input: ClipboardRestoreItem?)');self.assertIn('else { initial = Self.attributedContent(item) }',init);self.assertIn('itemObservation = state.store.$items.sink',init)
        value=body(self.src['observer'],'public var value:');self.assertIn('try? ClipboardPersistence.item(object)',value)
        self.assertIn('if onChange != nil, let value',self.consume)

    def test_rich_text_decoder_and_normalization_helpers_are_reused_unchanged(self):
        rich=(ROOT/'replica/Sources/PastoCore/OriginalPasteboard.swift').read_text();s=body(rich,'public func f_10037d33c()');self.order(s,['f_10037ebdc([.flatRTFD, .rtfd, .rtf])','f_10037c9a8()','NSMutableAttributedString','Self.f_100309924'])
        codec=(ROOT/'replica/Sources/PastoCore/OriginalPasteboardDataCodec.swift').read_text();self.assertIn('decodeIfValid(data) ?? []',body(codec,'public static func f_10031aeec('))
        for p,h in self.proof['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_native_preview_header_bytes(ROOT/p)).hexdigest(),h)

    def test_nine_existing_commit_lifecycle_and_header_methods_are_unchanged(self):
        self.assertEqual(len(self.proof['unchanged_methods']),9)
        for r in self.proof['unchanged_methods']:
            now=body(pre_text_preview_creation((ROOT/r['path']).read_text()),r['symbol']);self.assertEqual(hashlib.sha256(now.encode()).hexdigest(),r['sha256']);self.assertEqual(now,body((self.phase/'before'/r['path']).read_text(),r['symbol']))

    def test_eight_exact_hunks_two_existing_files_no_writer_model_version_changes(self):
        self.assertEqual(len(CHANGES),8);sha=lambda p:hashlib.sha256(pre_native_preview_header_bytes(ROOT/p)).hexdigest()
        files={str(p.relative_to(ROOT))for p in(ROOT/'replica/Sources').rglob('*')if p.is_file()};self.assertEqual(files,set(self.base['production']));self.assertEqual({p for p,h in self.base['production'].items()if sha(p)!=h},set(self.paths.values()))
        for key,p in self.paths.items():self.assertEqual(pre_native_text_read(self.src[key]),(self.phase/'before'/p).read_text())
        for group in ['current_sources','shared_sources']:
            for p,h in self.proof[group].items():self.assertEqual(sha(p),h)
        for p,h in self.proof['shared_sources'].items():self.assertEqual(h,self.base['production'][p])
        for p in ['replica/Package.swift','package.json']:self.assertEqual(sha(p),self.base['other'][p])

    def test_new_finite_dependency_contract_does_not_claim_complete_decoder_or_preview(self):
        self.assertEqual(self.proof['function_id'],'Paste:0x1003c05d4');self.assertEqual(self.proof['new_difference_records'],1);self.assertTrue(self.proof['finite_contract_verified']);self.assertFalse(self.proof['full_function_migration_verified']);self.assertFalse(self.proof['runtime_executed'])
        for token in ['Missing data','malformed','Header/card/factory','04430c']:self.assertTrue(any(token in r for r in self.proof['remaining']),token)
