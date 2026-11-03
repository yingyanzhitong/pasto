"""Empty decoded representations: source and ARM diagnostics, no Swift execution."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from empty_data_diagnostic_scope_contract import CHANGES,pre_empty_data_diagnostic
from empty_content_diagnostic_scope_contract import pre_empty_content_diagnostic
class EmptyDataDiagnosticContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-133';cls.p=json.loads((cls.phase/'empty-data-diagnostic-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.s=pre_empty_content_diagnostic((ROOT/cls.p['current_source']).read_text());cls.d=body(cls.s,'private func diagnoseEmptyRepresentations(');cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
    def order(self,s,seq):
        i=0
        for t in seq:i=s.index(t,i)+len(t)
    def test_eight_original_fragments_binary_and_decoder_bound(self):
        self.assertEqual(len(self.p['original_fragments']),8)
        for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for k in ['binary','decoder']:
            r=self.p[k];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_actual_error_empty_prefix_six_format_and_level_machine_words(self):
        self.assertEqual(len(self.p['ARM_words']),12)
        for r in self.p['ARM_words']:self.assertEqual(self.n['read'](int(r['address'],16),4).hex(),r['bytes'])
        self.assertEqual(int.from_bytes(self.n['read'](0x100372c20,4),'little'),0x528000c0)
        self.assertEqual(int.from_bytes(self.n['read'](0x1003718b4,4),'little'),0x528604a0)
        self.assertEqual(int.from_bytes(self.n['read'](0x1003718b8,4),'little'),0x72af0640)
    def test_prefix_literal_is_exact_and_remaining_fields_are_raw_size_and_prefix_only(self):
        r=self.p['prefix_literal'];self.assertEqual(self.n['read'](int(r['address'],16),100).split(b'\0')[0].decode(),r['value']);self.assertIn(r['value'],self.d)
        self.assertIn('\\(kind), rawSize: \\(raw.count), rawPrefix: \\(prefix))',self.d)
        for t in ['types:','previewLength','usedPreviewFallback']:self.assertNotIn(t,self.d)
    def test_kind_labels_come_from_original_real_enum_reflection_metadata(self):
        r=self.p['kind_metadata'];self.assertEqual(self.n['read'](int(r['address'],16),8).hex(),r['bytes']);self.assertEqual(self.n['read'](int(r['field_descriptor'],16),16).hex(),r['field_header']);self.assertEqual(struct.unpack('<iiHHI',bytes.fromhex(r['field_header']))[2:],(2,12,6))
        value=int.from_bytes(bytes.fromhex(r['bytes']),'little');self.assertEqual(self.n['base']+(value&((1<<36)-1)),int(r['descriptor'],16))
        self.assertEqual([x['value']for x in r['cases']],['unknown','image','color','files','link','text'])
        for x in r['cases']:
            a=int(x['relative_field'],16);b=self.n['read'](a,4);self.assertEqual(b.hex(),x['bytes']);self.assertEqual(a+struct.unpack('<i',b)[0],int(x['string'],16))
    def test_content_empty_array_only_runs_before_existing_typed_fallback(self):
        content=body(self.s,'func content()')
        self.order(content,['read(contentDiagnostics: contentDiagnostics)','if items.isEmpty { diagnoseEmptyRepresentations(for: object) }','return ClipboardSearchRecordContent.nativeText(items, kind: kind,','object.value(forKey: "rawPreview")'])
        self.assertEqual(content.count('diagnoseEmptyRepresentations'),1);self.assertNotIn('diagnoseEmptyRepresentations',body(self.s,'func imageData()'))
    def test_relation_getter_stays_outside_narrow_raw_exception_bridge(self):
        self.order(self.d,['guard let data = object.value(forKey: "data") as? NSManagedObject else { return }','let raw = (try? OriginalObjCExceptionBridge.f_1002ffc68 {','guard let raw = data.value(forKey: "rawPasteboardItems") as? Data','throw CocoaError(.fileReadCorruptFile)','return raw','}) ?? Data()'])
        inner=body(self.d,'OriginalObjCExceptionBridge.f_1002ffc68');self.assertNotIn('object.value(forKey: "data")',inner)
    def test_raw_is_reread_only_for_diagnostic_and_not_decoded_again(self):
        self.assertEqual(self.d.count('rawPasteboardItems'),1);self.assertNotIn('readRepresentations',self.d);self.assertNotIn('f_10031aeec',self.d);self.assertNotIn('ItemDataEntity',self.d)
        self.assertNotIn('return nil',self.d);self.assertIn('}) ?? Data()',self.d)
    def test_lowercase_two_digit_hex_and_limit_are_bound_to_actual_current_source(self):
        self.assertIn('raw.prefix(6).map { String(format: "%02x", $0) }.joined()',self.d)
        # Supplemental format fixtures; production is verified by source+machine words above.
        for raw,expected in [(b'',''),(bytes([0,1,15,16,171,255]),'00010f10abff'),(bytes(range(8)),'000102030405')]:self.assertEqual(''.join(f'{b:02x}'for b in raw[:6]),expected)
    def test_same_retained_named_receiver_emits_level2_before_continuation(self):
        self.assertIn('contentDiagnostics.f_1000d468c().f_1000d4df0(',self.d)
        for t in ['f_1000d4e0c','telemetry','Task','DispatchQueue','MainActor','context.save']:self.assertNotIn(t,self.d)
    def test_five_shared_methods_are_unchanged_in_current_production(self):
        self.assertEqual(len(self.p['unchanged_methods']),5)
        for r in self.p['unchanged_methods']:self.assertEqual(hashlib.sha256(body(pre_empty_content_diagnostic((ROOT/r['path']).read_text()),r['symbol']).encode()).hexdigest(),r['sha256'])
    def test_two_hunks_reverse_all247_sources_and_exactly_one_file_changes(self):
        self.assertEqual(len(CHANGES),2);diff=[]
        for p,h in self.base['production'].items():
            b=(ROOT/p).read_bytes();b=pre_empty_content_diagnostic(b.decode()).encode()if p.endswith('.swift')else b
            if hashlib.sha256(b).hexdigest()!=h:diff.append(p)
            b=pre_empty_data_diagnostic(b.decode()).encode()if p.endswith('.swift')else b;self.assertEqual(hashlib.sha256(b).hexdigest(),h)
        self.assertEqual(diff,[self.p['current_source']]);self.assertEqual(hashlib.sha256(self.s.encode()).hexdigest(),self.p['current_source_sha256'])
    def test_other_diagnostic_and_unknowns_not_closed_by_this_local_branch(self):
        self.assertEqual(len(self.p['remaining']),2);self.assertIn('still pending',self.p['remaining'][0]);self.assertFalse(self.p['runtime_executed']);self.assertFalse(self.p['full_function_migration_verified']);self.assertIn('only type/rawSize/rawPrefix',self.p['correction'])
if __name__=='__main__':unittest.main()
