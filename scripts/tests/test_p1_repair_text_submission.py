"""Text editing repository handoff and shared content replacement, source/static only."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment
from text_submission_scope_contract import CHANGES,pre_text_submission
from item_observation_scope_contract import NEW_PATH,pre_item_observation,pre_item_observation_bytes

class TextSubmissionContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-88'
        cls.proof=json.loads((cls.phase/'text-edit-contract.json').read_text())
        cls.base=json.loads((cls.phase/'baseline.json').read_text())
        cls.store=pre_item_observation((ROOT/'replica/Sources/PastoCore/ClipboardStore.swift').read_text())
        cls.submission=(ROOT/'replica/Sources/PastoCore/OriginalTextPreviewSubmission.swift').read_text()
        cls.persistence=pre_item_observation((ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text())
        cls.graph=(ROOT/'replica/Sources/PastoCore/ClipboardItemDataPersistence.swift').read_text()
        cls.adapter=pre_item_observation((ROOT/'replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift').read_text())
        cls.edit=body(cls.store,'public func updateTextPreviewItem(')
        cls.operation=body(cls.edit,'try mutateInTransaction')
        ns={};exec((ROOT/cls.proof['decoder']['path']).read_text().split("idx={r['address']",1)[0],ns);cls.ns=ns
    def original(self,address):
        r=next(r for r in self.proof['original_fragments']if r['address']==address)
        return original_fragment((ROOT/r['path']).read_text(),address[2:])
    def order(self,source,tokens):
        positions=[source.index(t)for t in tokens];self.assertEqual(positions,sorted(positions))

    def test_thirteen_fragments_and_supporting_shared_evidence_bound(self):
        self.assertEqual(len(self.proof['original_fragments']),13)
        for r in self.proof['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for r in [self.proof['binary'],self.proof['decoder']]+self.proof['reused_evidence']:
            self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])

    def test_content_writer_uses_real_writing_slot_eighteen(self):
        s=self.proof['writing_content_slot'];self.assertEqual(s['address'],'0x100ecca68');v,ch=self.ns['reachable_pointer'](int(s['address'],16));self.assertEqual(ch,s['chain']);self.assertEqual(self.ns['read'](int(s['address'],16),8).hex(),s['bytes']);self.assertEqual(hex(self.ns['base']+(v&((1<<36)-1))),s['target']);self.assertEqual(s['target'],'0x100363ff0')
        self.assertIn('FUN_100360ff8()',self.original('0x100363ff0'))
        o=self.original('0x1003c0e50');self.assertEqual(o.count('+ 0x18))('),2)

    def test_fourteen_real_calls_and_eight_indirect_handoff_words_bound(self):
        self.assertEqual(len(self.proof['ARM_calls']),14);self.assertEqual(len(self.proof['ARM_words']),8)
        for r in self.proof['ARM_calls']:
            pc=int(r['address'],16);raw=self.ns['read'](pc,4);self.assertEqual(raw.hex(),r['bytes']);w=int.from_bytes(raw,'little');self.assertEqual(w&0x7c000000,0x14000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(pc+4*d,int(r['target'],16))
        for r in self.proof['ARM_words']:self.assertEqual(self.ns['read'](int(r['address'],16),4).hex(),r['bytes'])
        self.assertEqual(next(r['bytes']for r in self.proof['ARM_words']if r['address']=='0x1003c11a0'),'1f010039')

    def test_seven_native_selector_calls_bound_and_data_precedes_preview(self):
        self.assertEqual(len(self.proof['content_selectors']),7)
        for s in self.proof['content_selectors']:
            stub=int(s['target'],16);self.assertEqual(self.ns['read'](stub,20).hex(),s['stub_bytes']);v,ch=self.ns['reachable_pointer'](int(s['pointer'],16));self.assertEqual(ch,s['chain']);self.assertEqual(self.ns['read'](int(s['pointer'],16),8).hex(),s['pointer_bytes']);target=self.ns['base']+(v&((1<<36)-1));self.assertEqual(hex(target),s['selector_address']);self.assertEqual(self.ns['read'](target,100).split(b'\0')[0].decode(),s['selector'])
        set_data=next(int(r['address'],16)for r in self.proof['content_selectors']if r['selector']=='setData:')
        preview=next(int(r['address'],16)for r in self.proof['ARM_calls']if r['function']=='0x100360ff8'and r['target']=='0x100322504')
        self.assertLess(set_data,preview)

    def test_original_content_primitive_skips_nil_and_does_not_write_other_metadata(self):
        source=self.original('0x100360ff8')
        self.order(source,['FUN_10032362c()','FUN_1003216bc(param_2)','if (uVar5 != 0)','objc_stub::setRawType_','objc_stub::setChecksum_','objc_stub::deleteObject_','FUN_10031a8e8()','objc_stub::setData_','FUN_100322504('])
        for t in ['setTitle_','setSourceApplication_','setTimestamp_','Date::']:self.assertNotIn(t,source)

    def test_actual_editor_exits_editable_before_read_and_submit_not_at_callback_output(self):
        source=self.original('0x1003ec0ac');self.order(source,['FUN_1002131bc(0)','FUN_100212ccc(uVar1)','FUN_1003c0e08(uVar1)','FUN_1003eb330(0)'])
        self.assertIn('objc_stub::setEditable_',self.original('0x1002131bc'))
        self.assertNotIn('setEditable',self.original('0x1003c0e50'))
        commit=body(self.adapter,'func commitPreviewEditing()')
        self.order(commit,['text.isEditable = false','updateTextPreviewItem(id: itemID','OriginalPreviewAttributedText.f_100212ccc(editor: text)','reloadStoredContent()'])
        self.assertIn('catch { state.controller?.presentError(error) }',commit)

    def test_representation_classification_and_checksum_are_inside_one_transaction(self):
        self.assertTrue(self.edit.lstrip().startswith('{\n        try mutateInTransaction'))
        self.order(self.operation,['guard let i = state.items.firstIndex','OriginalTextPreviewSubmission.makeItem(attributedString)','let items = [representation]','OriginalPasteboardClassification.f_10032362c(items)','guard let checksum = OriginalPasteboardChecksums.f_1003216bc(items, kind: nativeKind) else { return }','prepareHistoryItems([id])','transaction.repository.replaceCapturedItemData('])
        self.assertEqual(self.edit.count('mutateInTransaction'),1);self.assertNotIn('try mutate {',self.edit)
        for t in ['persistence.commit','context.save','historyAction:','restoringItemIDs:']:self.assertNotIn(t,self.edit)

    def test_data_update_is_forced_before_preview_even_when_payloads_equal(self):
        self.order(self.operation,['item.rawPreview = nil','transaction.repository.replaceCapturedItemData(','item = Self.withPreviewMetadata(item,','return item.rawPreview','state.items[i] = item'])
        self.assertNotIn('== payloads',self.edit);self.assertNotIn('!= payloads',self.edit)
        self.assertIn('useBinaryPlist: preferences.useBinaryPlist',self.edit)
        self.assertIn('preferQuickLookThumbnails: preferences.fileQuickLookThumbnailsEnabled',self.edit)
        replace=body(self.graph,'func replace(')
        self.order(replace,['forKey: "rawType"','forKey: "nativeChecksum"','context.delete(old)','insertNewObject(forEntityName: "ItemDataEntity"','OriginalPasteboardDataCodec.f_10031a8e8(','object.setValue(data, forKey: "data")','object.setValue(preview(), forKey: "rawPreview")'])

    def test_shared_replacement_marker_prevents_commit_second_data_replacement(self):
        worker=body(self.persistence,'func replaceCapturedItemData(')
        self.order(worker,['itemData.replace(','replacedItemDataIDs.insert(target.id)'])
        commit=body(self.persistence,'func commit<T>(')
        self.assertIn('let replacements = transaction.repository.replacedItemDataIDs',commit)
        self.assertIn('updatingKeys: replacements.map(\\.uuidString)',commit)
        self.assertIn('if !replacements.contains(item.id) && (old?.payloads != item.payloads || object.value(forKey: "data") == nil)',commit)

    def test_text_payload_type_mapping_retains_original_rtf_or_plain_preparation(self):
        self.assertIn('payloads[Self.orderedPasteboardTypesPayloadKey] = try JSONEncoder().encode(types)',self.edit)
        self.assertIn('item.plainText = attributedString.string',self.edit)
        self.assertIn('types.contains(NSPasteboard.PasteboardType.rtf.rawValue) ? .richText : .text',self.edit)
        prep=body(self.submission,'public static func makeItem(')
        self.order(prep,['content.enumerateAttributes(','guard isRich else','forType: UTType.rtf.identifier','forType: UTType.utf8PlainText.identifier'])

    def test_current_attribute_dictionary_finishes_after_requesting_enumeration_stop(self):
        source=body(self.submission,'public static func f_1003c14d0(')
        self.assertIn('for (key, value) in attributes',source);self.assertIn('symbolicTraits.rawValue & 3 == 0',source);self.assertIn('key != .underlineStyle && key != .strikethroughStyle',source)
        self.order(source,['isRich = true','stop.pointee = true']);self.assertNotIn('return',source);self.assertNotIn('break',source)
        original=self.original('0x1003c14d0');self.assertIn('goto LAB_1003c1584',original);self.assertIn('} while( true );',original)

    def test_existing_local_content_clock_and_identity_are_explicit_adaptations(self):
        self.assertIn('item.updatedAt = Date()',self.edit);self.assertIn('item.nativeChecksum = checksum',self.edit)
        for t in ['item.createdAt =','item.isInHistory =','item.nativeIdentifier =','item.title =','item.sourceName =','item.sourceDevice =']:self.assertNotIn(t,self.edit)
        self.assertTrue(any('conflict/version clock' in r for r in self.proof['remaining']))
        self.assertFalse(self.proof['full_function_migration_verified']);self.assertFalse(self.proof['runtime_executed']);self.assertEqual(self.proof['new_difference_records'],0)

    def test_two_reviewed_deltas_and_244_other_production_files_are_unchanged(self):
        self.assertEqual(len(CHANGES),2)
        changed=set(self.proof['current_sources']);sha=lambda p:hashlib.sha256(pre_item_observation_bytes(ROOT/p)).hexdigest()
        current={str(p.relative_to(ROOT))for p in (ROOT/'replica/Sources').rglob('*')if p.is_file() and str(p.relative_to(ROOT)) != NEW_PATH}
        self.assertEqual(current,set(self.base['production']));self.assertEqual({p for p,h in self.base['production'].items()if sha(p)!=h},changed)
        for p,_,_ in CHANGES:self.assertEqual(pre_text_submission((ROOT/p).read_text()),(self.phase/'before'/p).read_text())
        for group in ['current_sources','shared_sources']:
            for p,h in self.proof[group].items():self.assertEqual(sha(p),h)
        for p,h in self.proof['shared_sources'].items():self.assertEqual(h,self.base['production'][p])
        for p in ['replica/Package.swift','package.json']:self.assertEqual(sha(p),self.base['other'][p])
