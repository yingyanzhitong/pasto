"""Round129 readonly evidence of two reopened P1 source branches; no production execution."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from native_search_content_scope_contract import pre_native_search_content,pre_native_search_content_bytes
from test_offline_p0_contracts import body
class P1EntryAuditContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=json.loads((ROOT/'.local/p0-repair/phase-129/p1-entry-audit-contract.json').read_text());cls.ns={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.ns);cls.record=pre_native_search_content((ROOT/'replica/Sources/PastoCore/ClipboardSearchRecord.swift').read_text());cls.reader=pre_native_search_content((ROOT/'replica/Sources/PastoCore/ClipboardSnapshotReader.swift').read_text())
    def test_twenty_two_original_fragments_and_binary_decoder_bound(self):
        self.assertEqual(len(self.p['original_fragments']),22)
        for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for key in ['binary','decoder']:
            r=self.p[key];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_nine_original_empty_gate_words_and_actual_metadata_getter_call(self):
        for r in self.p['ARM_words']:self.assertEqual(self.ns['read'](int(r['address'],16),4).hex(),r['bytes'])
        r=self.p['ARM_call'];a=int(r['address'],16);b=self.ns['read'](a,4);w=int.from_bytes(b,'little');self.assertEqual(b.hex(),r['bytes']);self.assertEqual(w&0xfc000000,0x94000000);d=w&0x3ffffff
        if d&0x2000000:d-=0x4000000
        self.assertEqual(a+4*d,int(r['target'],16))
    def test_raw_type_zero_empty_reaches_nil_exit_while_nonzero_reads_current_metadata(self):
        a=0x100373814;w=int.from_bytes(self.ns['read'](a,4),'little');self.assertEqual(w&0xff00001f,0x54000000);d=(w>>5)&0x7ffff
        if d&0x40000:d-=0x80000
        self.assertEqual(a+4*d,0x100373870);self.assertEqual(int.from_bytes(self.ns['read'](0x100373888,4),'little'),0xa9007edf)
    def test_current_metadata_constructor_decodes_compat_archive_before_reader_and_relations(self):
        s=body(self.reader,'func searchIndexRecords(');tokens=['try ClipboardPersistence.decode(ClipboardItem.self, object)','ClipboardItemTitlePersistence.project(&value, from: object)','let reader = ClipboardSearchRecordReader(','sourceApplication','ClipboardSearchRecord.make(value'];p=0
        for token in tokens:p=s.index(token,p)+len(token)
        source=(ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text();self.assertIn('key: String = \"content\"',source);d=body(source,'static func decode<T: Decodable>');self.assertIn('object.value(forKey: key) as? Data',d);self.assertIn('throw CocoaError',d)
    def test_current_unknown_empty_returns_empty_string_instead_of_original_nil(self):
        s=body(self.record,'static func text(');self.assertIn('if !value.isEmpty || kind == .unknown { return value }',s);self.assertEqual(int.from_bytes(self.ns['read'](0x100373888,4),'little'),0xa9007edf)
    def test_current_native_empty_text_fallback_uses_DTO_not_typed_raw_preview(self):
        s=body(self.record,'func content()');self.assertIn('ClipboardSearchRecordContent.text(items',s);self.assertIn('PropertyListDecoder().decode(ClipboardItem.self, from: raw)',s);self.assertIn('?.plainText',s);self.assertNotIn('decodeText',s);self.assertIn('return legacyPreviewFallback() ?? value',body(self.record,'static func text('))
    def test_sixteen_real_current_entry_methods_bound_across_five_modules(self):
        self.assertEqual(len(self.p['source_refs']),16)
        for r in self.p['source_refs']:self.assertEqual(hashlib.sha256(body(pre_native_search_content((ROOT/r['path']).read_text()),r['symbol']).encode()).hexdigest(),r['sha256'])
    def test_visionkit_selection_and_extra_full_image_OCR_are_separate_consumers(self):
        s=(ROOT/'replica/Sources/Pasto/UI/OriginalImageTextSelection.swift').read_text();self.assertIn('overlay.preferredInteractionTypes = .automatic',s);rows=self.p['module_rows'];row=next(r for r in rows if r['module']=='图片与 OCR');self.assertEqual(row['result'],'separate_system_selection_and_whole_image_extension');self.assertIn('not original selected-range operation',row['detail'])
    def test_all247_production_sources_unchanged_in_readonly_P1_check(self):
        self.assertEqual(len(self.p['current_production_hashes']),247)
        for p,h in self.p['current_production_hashes'].items():self.assertEqual(hashlib.sha256(pre_native_search_content_bytes(ROOT/p)).hexdigest(),h)
    def test_exactly_two_reopened_contracts_five_rows_and_parent_unknowns_stay_open(self):
        self.assertEqual(self.p['reopened_existing_function_ids'],['Paste:0x100371998','Paste:0x1003724f0']);self.assertEqual(len(self.p['module_rows']),5);self.assertEqual(self.p['new_difference_records'],0);self.assertFalse(self.p['full_function_migration_verified']);self.assertFalse(self.p['full_P1_completion']);self.assertFalse(self.p['runtime_executed']);self.assertEqual(len(self.p['remaining']),3)
if __name__=='__main__':unittest.main()
