"""Current native search metadata/empty outputs and original bytes; no Swift/framework execution."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from deferred_raw_error_scope_contract import pre_deferred_raw_error
from test_offline_p0_contracts import body
from native_search_content_scope_contract import CHANGES,pre_native_search_content
class NativeSearchContentContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-130';cls.p=json.loads((cls.phase/'native-search-content-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.s=(ROOT/'replica/Sources/PastoCore/ClipboardSearchRecord.swift').read_text();cls.r=(ROOT/'replica/Sources/PastoCore/ClipboardSnapshotReader.swift').read_text();cls.native=body(cls.s,'static func nativeText(');cls.build=body(cls.r,'func searchIndexRecords(');cls.ns={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.ns)
    def order(self,s,seq):
        p=0
        for t in seq:p=s.index(t,p)+len(t)
    def test_original_eight_fragments_and_previous_actual_entry_audit_bound(self):
        self.assertEqual(len(self.p['original_fragments']),8)
        for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for key in ['binary','decoder','reused_P1_entry_audit']:
            r=self.p[key];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_six_real_original_preview_metadata_and_rich_reader_call_targets(self):
        self.assertEqual(len(self.p['ARM_calls']),6)
        for r in self.p['ARM_calls']:
            a=int(r['address'],16);b=self.ns['read'](a,4);w=int.from_bytes(b,'little');self.assertEqual(b.hex(),r['bytes']);self.assertEqual(w&0xfc000000,0x94000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(a+4*d,int(r['target'],16))
    def test_original_unknown_nil_exit_and_typed_expected_length_zero_gate_bound(self):
        for r in self.p['ARM_words']:self.assertEqual(self.ns['read'](int(r['address'],16),4).hex(),r['bytes'])
        self.assertEqual(int.from_bytes(self.ns['read'](0x100373888,4),'little'),0xa9007edf)
        a=0x100373eec;w=int.from_bytes(self.ns['read'](a,4),'little');d=(w>>5)&0x7ffff
        if d&0x40000:d-=0x80000
        self.assertEqual(a+4*d,0x100373858)
    def test_native_metadata_uses_native_identity_date_title_type_relations_without_DTO(self):
        self.order(self.build,['guard let key = object.value(forKey: "key") as? String','UUID(uuidString: key)','object.value(forKey: "updatedAt") as? Date','let rawType','let reader = ClipboardSearchRecordReader','sourceApplication','device','list','ClipboardSearchRecord.make(id: id','originalTitle: object.value(forKey: "title") as? String','contentVersion: contentVersion'])
        for t in ['decode(ClipboardItem','PropertyListDecoder','project(&value','value.updatedAt','value.originalTitle','object.value(forKey: "content")']:self.assertNotIn(t,self.build)
    def test_native_invalid_local_key_or_date_retains_explicit_error_not_random_replacement(self):
        s=body(self.build,'guard let key =');self.assertIn('throw CocoaError(.fileReadCorruptFile)',s)
        for t in ['UUID()','Date()','distantPast','try?']:self.assertNotIn(t,s)
    def test_native_capabilities_remain_lazy_with_original_image_split_and_native_title_nil(self):
        self.assertIn('content: kind == .image ? nil : { reader.content() }',self.build);self.assertIn('imageData: kind == .image ? { reader.imageData() } : nil',self.build);self.assertIn('title: originalTitle ?? name',body(self.s,'static func make('));self.assertNotIn('reader.content()',self.build.split('content: kind == .image')[0])
    def test_native_content_reader_never_reads_compatibility_blob(self):
        s=body(self.s,'func content()');self.assertIn('ClipboardSearchRecordContent.nativeText(items',s);self.assertIn('object.value(forKey: "rawPreview") as? Data',s)
        for t in ['content"','ClipboardItem','PropertyListDecoder','plainText']:self.assertNotIn(t,s)
    def test_shared_primary_extractor_is_reused_before_empty_and_unknown_nil_gates(self):
        self.order(self.native,['text(items, kind: kind, preview: preview, legacyPreviewFallback: { "" })','guard value.isEmpty else { return value }','guard kind != .unknown else { return nil }','decodeText(preview)'])
    def test_text_typed_fallback_uses_nonzero_expected_length_and_full_first_representation(self):
        s=body(self.native,'if let metadata = OriginalImagePreviewMetadataCodec.decodeText');self.order(s,['guard metadata.length != 0 else { return nil }','items.first?.f_10037d33c()?.string']);self.assertNotIn('metadata.text',s);self.assertNotIn('prefix(',s);self.assertNotIn('metadata.length > 0',s)
    def test_link_typed_fallback_uses_URL_length_before_optional_name_and_space_join(self):
        s=body(self.native,'if let metadata = OriginalImagePreviewMetadataCodec.decodeLink');self.order(s,['guard !metadata.url.absoluteString.isEmpty else { return nil }','var values = [metadata.url.absoluteString]','if let name = metadata.name { values.append(name) }','values.joined(separator: " ")'])
    def test_files_typed_fallback_zero_length_gate_is_not_item_count_or_spaced_length(self):
        s=body(self.native,'if let metadata = OriginalImagePreviewMetadataCodec.decodeFiles');self.order(s,['let joinedPaths = metadata.paths.joined()','guard !joinedPaths.isEmpty else { return nil }','fallback = metadata.paths.joined(separator: " ")']);self.assertNotIn('paths.count',s)
    def test_unsupported_image_color_metadata_and_missing_metadata_have_distinct_exits(self):
        self.assertIn('OriginalImagePreviewMetadataCodec.decode(preview) != nil',self.native);self.assertIn('OriginalImagePreviewMetadataCodec.decodeColor(preview) != nil',self.native);self.assertIn('fallback = nil',self.native);self.assertIn('} else { return nil }',self.native);self.assertIn('guard let fallback, !fallback.isEmpty else { return value }',self.native)
    def test_original_raw_unknown_and_typed_metadata_empty_gate_source_matrix(self):
        # Supplemental model derives the gates from actual production tokens; it does not execute Swift.
        self.assertIn('guard kind != .unknown else { return nil }',self.native);self.assertIn('guard metadata.length != 0',self.native);self.order(self.native,['let joinedPaths = metadata.paths.joined()','guard !joinedPaths.isEmpty'])
        def output(kind,primary,tag,expected,fallback):
            if primary is None or primary!='':return primary
            if kind=='unknown'or tag is None:return None
            if tag in ['text','link','files']and expected==0:return None
            return fallback if fallback else primary
        cases=[('unknown','',None,0,None,None),('text','',None,0,None,None),('text','','text',4,'full','full'),('text','','text',0,'full',None),('text','','text',4,None,''),('files','','files',0,' ',None),('link','','link',0,' name',None),('link','','link',9,'url','url'),('color','','color',-1,None,''),('text','primary',None,0,None,'primary')]
        for kind,primary,tag,n,value,result in cases:self.assertEqual(output(kind,primary,tag,n,value),result)
    def test_scalar_record_factory_is_exact_old_body_with_only_id_title_parameter_replacement(self):
        p='replica/Sources/PastoCore/ClipboardSearchRecord.swift';old=body((self.phase/'before'/p).read_text(),'static func make(');new=body(self.s,'static func make(');self.assertEqual(new,old.replace('value.id','id').replace('value.originalTitle','originalTitle'));self.assertEqual(hashlib.sha256(new.encode()).hexdigest(),self.p['equivalence']['scalar_record_factory_body_sha256'])
    def test_value_snapshot_compatibility_and_primary_extraction_remain_exact(self):
        p='replica/Sources/PastoCore/ClipboardSearchRecord.swift';old=(self.phase/'before'/p).read_text();self.assertEqual(body(self.s,'public static func snapshot('),body(old,'public static func snapshot(').replace('make(value,','make(id: value.id, originalTitle: value.originalTitle,'));self.assertEqual(body(self.s,'static func text('),body(old,'static func text('))
    def test_eleven_methods_and_six_shared_sources_protect_queries_raw_reads_and_P0(self):
        self.assertEqual(len(self.p['source_refs']),11)
        for r in self.p['source_refs']:self.assertEqual(hashlib.sha256(body(pre_deferred_raw_error((ROOT/r['path']).read_text()),r['symbol']).encode()).hexdigest(),r['sha256'])
        self.assertEqual(len(self.p['shared_sources']),6)
        for p,h in dict(self.p['shared_sources'],**self.p['current_sources']).items():self.assertEqual(hashlib.sha256(pre_deferred_raw_error((ROOT/p).read_text()).encode()).hexdigest(),h)
    def test_eight_exact_hunks_inverse_all247_production_files_and_preserve_users_changes(self):
        self.assertEqual(len(CHANGES),8)
        for p,h in self.base['production'].items():
            b=(ROOT/p).read_bytes();b=pre_native_search_content(b.decode()).encode()if p.endswith('.swift')else b;self.assertEqual(hashlib.sha256(b).hexdigest(),h)
    def test_exact_reversal_is_idempotent_and_only_two_additional_contracts_closed(self):
        for p in self.p['current_sources']:
            before=(self.phase/'before'/p).read_text();self.assertEqual(pre_native_search_content((ROOT/p).read_text()),before);self.assertEqual(pre_native_search_content(before),before)
        self.assertEqual([r['function_id']for r in self.p['closed_additional_contracts']],['Paste:0x100371998','Paste:0x1003724f0']);self.assertEqual(self.p['new_difference_records'],0);self.assertFalse(self.p['full_function_migration_verified']);self.assertFalse(self.p['runtime_executed']);self.assertEqual(len(self.p['remaining']),3)
if __name__=='__main__':unittest.main()
