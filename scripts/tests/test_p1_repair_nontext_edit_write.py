"""Nontext captured-entity writes: source/Mach-O checks, never framework execution."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment
from nontext_edit_write_scope_contract import CHANGES,pre_nontext_edit_write
from nontext_preview_read_scope_contract import pre_nontext_preview_read,pre_nontext_preview_read_bytes

class NontextEditWriteContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-101';cls.proof=json.loads((cls.phase/'nontext-edit-write-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.src={p:pre_nontext_preview_read((ROOT/p).read_text())for p in cls.proof['current_sources']}
        cls.store=cls.src['replica/Sources/PastoCore/ClipboardStore.swift'];cls.transaction=body(cls.store,'private func replacePreviewContent(')
        ns={};exec((ROOT/cls.proof['decoder']['path']).read_text().split("idx={r['address']",1)[0],ns);cls.ns=ns
    def original(self,a):
        r=next(r for r in self.proof['original_fragments']if r['address']==a);return original_fragment((ROOT/r['path']).read_text(),a[2:])
    def order(self,s,tokens):
        pos=[s.index(t)for t in tokens];self.assertEqual(pos,sorted(pos))
    def test_twenty_five_original_fragments_and_reused_contracts_are_bound(self):
        self.assertEqual(len(self.proof['original_fragments']),25)
        for r in self.proof['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for r in [self.proof['binary'],self.proof['decoder']]+self.proof['reused_evidence']:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_actual_ARM_calls_bind_three_representation_writers_and_shared_backend(self):
        self.assertEqual(len(self.proof['ARM_calls']),20)
        for r in self.proof['ARM_calls']:
            pc=int(r['address'],16);b=self.ns['read'](pc,4);self.assertEqual(b.hex(),r['bytes']);w=int.from_bytes(b,'little');self.assertEqual(w&0x7c000000,0x14000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(pc+4*d,int(r['target'],16))
    def test_default_repository_and_writing_content_slots_have_actual_chain_targets(self):
        self.assertIn('&PTR_PTR_100eccad0',self.original('0x100357cf0'))
        rows=self.proof['repository_writing_pointers'];self.assertEqual(len(rows),2);self.assertEqual([(r['address'],r['target'])for r in rows],[('0x100eccae0','0x100ecca50'),('0x100ecca68','0x100363ff0')])
        for r in rows:
            a=int(r['address'],16);v,ch=self.ns['reachable_pointer'](a);self.assertEqual(ch,r['chain']);self.assertEqual(self.ns['read'](a,8).hex(),r['bytes']);self.assertEqual(self.ns['base']+(v&((1<<36)-1)),int(r['target'],16))
        self.assertIn('FUN_100360ff8()',self.original('0x100363ff0'))
    def test_VM_constructors_and_ARM_handoffs_keep_captured_entities(self):
        for a in ['0x1003bc2e8','0x1003bffac']:self.assertIn('*(undefined8 *)(param_3 + 0x50) = param_1',self.original(a))
        words={r['address']:r['bytes']for r in self.proof['ARM_words']};self.assertEqual(len(words),16)
        for a,b in words.items():self.assertEqual(self.ns['read'](int(a,16),4).hex(),b)
        for a,b in {'0x1003bdf20':'180b40f9','0x1003bdff8':'e00318aa','0x1003be008':'00013fd6','0x1003bc0e4':'342b40f9','0x1003bc22c':'e0031baa','0x1003bc238':'00013fd6','0x1003bfc18':'732a40f9','0x1003bfca0':'e00313aa','0x1003bfcb0':'00013fd6'}.items():self.assertEqual(words[a],b)
    def test_actual_factory_passes_input_to_all_three_UI_classes(self):
        s=self.src['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift'];factory=body(s,'func makeOriginalReplicaPreview(')
        for kind in ['Image','Color','Link']:self.assertIn('Replica'+kind+'PreviewContent(state: state, item: item, input: input)',factory)
        for kind in ['Image','Color','Link']:
            s=self.src['replica/Sources/Pasto/UI/Replica'+kind+'PreviewContent.swift'];self.assertIn('private let editInput: ClipboardRestoreItem?',s);init=body(s,'init(state: ReplicaUIState, item: ClipboardItem, input: ClipboardRestoreItem? = nil)');self.order(init,['itemID = item.id','editInput = input'])
    def test_shared_transaction_is_exact_previous_text_body_with_deferred_reads(self):
        old=body((self.phase/'before/replica/Sources/PastoCore/ClipboardStore.swift').read_text(),'private func updateTextPreviewItem(');expected=old.replace('OriginalTextPreviewSubmission.makeItem(attributedString)','makeRepresentation()').replace('item.plainText = attributedString.string','item.plainText = plainText()');self.assertEqual(self.transaction,expected)
        self.assertIn('plainText: @autoclosure () -> String?',self.store)
        wrapper=body(self.store,'private func updateTextPreviewItem(');self.assertIn('plainText: attributedString.string',wrapper);self.assertIn('OriginalTextPreviewSubmission.makeItem(attributedString)',wrapper)
    def test_checksum_nil_gate_precedes_projection_and_all_native_mutations(self):
        self.order(self.transaction,['try mutateInTransaction','let representation = makeRepresentation()','f_10032362c(items)','guard let checksum = OriginalPasteboardChecksums.f_1003216bc','else { return }','if let nativeObject, let input','item = input.resolvedItem()','item.payloads = payloads','replaceCapturedItemData'])
        early=self.transaction[:self.transaction.index('guard let checksum')]
        for token in ['state.items.append','item.payloads =','replaceCapturedItemData','setValue','Date()']:self.assertNotIn(token,early)
    def test_native_target_uses_same_object_and_cache_miss_does_not_reject(self):
        native=body(self.transaction,'if let nativeObject, let input');self.order(native,['target = (id: id, object: nativeObject)','item = input.resolvedItem()','if index == nil','state.items.append(item)'])
        self.assertNotIn('prepareHistoryItems',native);self.assertNotIn('first(where:',native)
        self.assertIn('target = try transaction.repository.prepareHistoryItems([id]).first!',self.transaction)
    def test_native_recency_is_preserved_and_legacy_clock_is_explicit(self):
        self.assertEqual(self.transaction.count('Date()'),1);self.assertIn('if nativeObject == nil { item.updatedAt = Date() }',self.transaction)
        for name in ['updateImagePreviewItem','updateColorItem','updateLinkItem']:
            s=body(self.store,'public func '+name+'(_ input:');self.assertNotIn('Date()',s)
    def test_data_replacement_precedes_preview_generation_and_cached_assignment(self):
        self.order(self.transaction,['item.rawPreview = nil','item.nativeChecksum = checksum','transaction.repository.replaceCapturedItemData(target, items: items','item = Self.withPreviewMetadata(item','return item.rawPreview','state.items[i] = item'])
        self.assertEqual(self.transaction.count('Self.withPreviewMetadata'),1);self.assertNotIn('save(',self.transaction)
        original=self.original('0x100360ff8');self.order(original,['FUN_1003216bc(','if (uVar5 != 0)','objc_stub::setRawType_','objc_stub::deleteObject_','objc_stub::setData_','FUN_100322504(','FUN_10031ed94('])
    def test_native_image_uses_ordered_PNG_JPEG_or_empty_representation(self):
        s=body(self.store,'public func updateImagePreviewItem(_ input:');self.order(s,['guard input.nativeObject != nil','updateImagePreviewItem(id: input.id','let imageTypes =','let types = imageTypes.filter','replacePreviewContent(id: input.id, input: input, plainText: nil)','OriginalPasteboardItem(types: types, dataByType: payloads)','startBackgroundTextRecognition(id: input.id)'])
        image=self.src['replica/Sources/Pasto/UI/ReplicaImagePreviewContent.swift'];encode=body(image,'private static func encodedPayloads(');self.order(encode,['OriginalPasteboardImageEncoding.f_1003c89c8','PasteboardType.png','f_1003c8b58(image, compression: 0.5)','public.jpeg','return [:]'])
        self.assertIn('guard !types.isEmpty || payloads.isEmpty else',s);self.assertIn('throw OriginalPasteboardItemCreationError.unsupportedContent',s)
        self.assertIn('FUN_100381528',self.original('0x1003bded4'));self.assertIn('FUN_100381534',self.original('0x1003bded4'))
    def test_native_link_name_comes_from_captured_metadata_and_preserves_nil(self):
        s=body(self.store,'public func updateLinkItem(_ input:');self.order(s,['guard let object = input.nativeObject','updateLinkItem(id: input.id','decodeLink(object.value(forKey: "rawPreview")','name = previous.name','else { name = "" }','replacePreviewContent(id: input.id, input: input, plainText: url.absoluteString)','OriginalPasteboardItem.f_10037c7bc(url, title: name)'])
        for token in ['state.items','first(where:','resolvedItem','previous.name ??']:self.assertNotIn(token,s)
    def test_native_color_uses_same_HEX_plain_representation_without_UUID_selection(self):
        s=body(self.store,'public func updateColorItem(_ input:');self.order(s,['guard input.nativeObject != nil','updateColorItem(id: input.id','replacePreviewContent(id: input.id, input: input, plainText: text)','OriginalPasteboardItem.f_10037c6d4(text)'])
        ui=self.src['replica/Sources/Pasto/UI/ReplicaColorPreviewContent.swift'];commit=body(ui,'func commitPreviewEditing()');self.order(commit,['editing = false','colorPanel.orderOut(nil)','f_100206b5c(displayedColor).uppercased()','if let editInput','updateColorItem(editInput, text: text)','else { try state.store.updateColorItem(id: itemID, text: text)'])
    def test_each_UI_commit_calls_handle_overload_and_retains_legacy_fallback(self):
        for kind,name in [('Image','updateImagePreviewItem'),('Color','updateColorItem'),('Link','updateLinkItem')]:
            s=self.src['replica/Sources/Pasto/UI/Replica'+kind+'PreviewContent.swift'];commit=body(s,'func commitPreviewEditing()');self.order(commit,['if let editInput','state.store.'+name+'(editInput','state.store.'+name+'(id: itemID','state.normalizeSelection()'])
            self.assertNotIn('ClipboardRestoreItem(item:',s)
    def test_legacy_APIs_and_eighteen_unrelated_methods_are_unchanged(self):
        self.assertEqual(len(self.proof['unchanged_methods']),18)
        for r in self.proof['unchanged_methods']:
            s=body(pre_nontext_preview_read((ROOT/r['path']).read_text()),r['symbol']);self.assertEqual(hashlib.sha256(s.encode()).hexdigest(),r['sha256']);self.assertEqual(s,body((self.phase/'before'/r['path']).read_text(),r['symbol']))
    def test_new_cross_file_API_and_representation_initializers_exist(self):
        for name in ['updateImagePreviewItem','updateColorItem','updateLinkItem']:self.assertIn('public func '+name+'(_ input: ClipboardRestoreItem',self.store)
        pasteboard=(ROOT/'replica/Sources/PastoCore/OriginalPasteboard.swift').read_text();self.assertIn('    init(types: [String], dataByType: [String: Data])',pasteboard);self.assertNotIn('private init(types:',pasteboard)
        self.assertIn('public static func f_10037c6d4(',pasteboard);self.assertIn('public static func f_10037c7bc(',pasteboard)
    def test_twenty_one_deltas_only_five_files_and_reversal_is_idempotent(self):
        self.assertEqual(len(CHANGES),21);sha=lambda p:hashlib.sha256(pre_nontext_preview_read_bytes(ROOT/p)).hexdigest();files={str(p.relative_to(ROOT))for p in(ROOT/'replica/Sources').rglob('*')if p.is_file()};self.assertEqual(files,set(self.base['production']))
        self.assertEqual({p for p,h in self.base['production'].items()if sha(p)!=h},set(self.src))
        for p,s in self.src.items():
            before=(self.phase/'before'/p).read_text();self.assertEqual(pre_nontext_edit_write(s),before);self.assertEqual(pre_nontext_edit_write(before),before);self.assertEqual(sha(p),self.proof['current_sources'][p])
        for p,h in self.proof['shared_sources'].items():self.assertEqual(sha(p),h);self.assertEqual(h,self.base['production'][p])
    def test_three_finite_writes_do_not_claim_full_async_reader_DI_or_runtime(self):
        self.assertEqual(self.proof['new_difference_records'],3);self.assertEqual({r['function_id']for r in self.proof['contracts']},{'Paste:0x1003bded4','Paste:0x1003bc060','Paste:0x1003bfb8c'});self.assertTrue(self.proof['finite_contract_verified']);self.assertFalse(self.proof['full_function_migration_verified']);self.assertFalse(self.proof['runtime_executed'])
        for token in ['Nontext','debounce','Missing fields','+58','04430c']:self.assertTrue(any(token in r for r in self.proof['remaining']),token)
