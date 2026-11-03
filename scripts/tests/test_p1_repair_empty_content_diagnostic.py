"""Detailed primary-empty local diagnostic gates and actual consumers; static only."""
from pathlib import Path
import hashlib,json,plistlib,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from item_data_constructor_scope_contract import pre_item_data_constructor
from empty_content_diagnostic_scope_contract import CHANGES,pre_empty_content_diagnostic
from supplied_preview_input_scope_contract import pre_supplied_preview_input
class EmptyContentDiagnosticContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-134';cls.p=json.loads((cls.phase/'empty-content-diagnostic-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.s=pre_item_data_constructor((ROOT/cls.p['current_source']).read_text());cls.native=body(cls.s,'static func nativeText(');cls.d=body(cls.s,'private func diagnoseEmptyContent(');cls.query=body(cls.s,'private func hasObjectMetadata(');cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
    def order(self,s,seq):
        i=0
        for t in seq:i=s.index(t,i)+len(t)
    def test_thirteen_original_fragments_binary_decoder_and_metadata_dump_bound(self):
        self.assertEqual(len(self.p['original_fragments']),13)
        for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for k in ['binary','decoder','metadata_dump','original_model']:
            r=self.p[k];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_actual_zero_length_gate_item_type_limits_query_and_warning_words(self):
        self.assertEqual(len(self.p['ARM_words']),18)
        for r in self.p['ARM_words']:self.assertEqual(self.n['read'](int(r['address'],16),4).hex(),r['bytes'])
        self.assertEqual(self.n['read'](0x100373eec,4).hex(),'74cbffb4');self.assertEqual(self.n['read'](0x100374ed4,4).hex(),'49018052')
    def test_createdAt_and_fetchOffset_selectors_are_real_chained_selector_refs(self):
        self.assertEqual([r['value']for r in self.p['selectors']],['createdAt','setFetchOffset:'])
        for r in self.p['selectors']:
            v,c=self.n['reachable_pointer'](int(r['address'],16));self.assertEqual(hex(v),r['raw']);self.assertEqual(c,r['chain']);t=self.n['base']+(v&((1<<36)-1));self.assertEqual(t,int(r['target'],16));self.assertEqual(self.n['read'](t,100).split(b'\0')[0].decode(),r['value'])
    def test_prefix_field_names_and_ObjectMetadata_real_name_not_guessed(self):
        for r in self.p['strings']:self.assertEqual(self.n['read'](int(r['address'],16),90).split(b'\0')[0].decode(),r['value'])
        self.assertIn('synced:',self.d);self.assertIn('types:',self.d);self.assertNotIn('dataTypes:',self.d)
        dump=(ROOT/self.p['metadata_dump']['path']).read_text();section=dump[dump.index('0000000100f45d78'):];self.assertIn('_TtC9PasteCore14ObjectMetadata',section[:4500]);self.assertIn('objectURI',section[:4500]);m=self.p['original_model'];o=plistlib.loads((ROOT/m['path']).read_bytes())['$objects'];entity=o[m['ObjectMetadata_object_index']];self.assertEqual(o[entity['NSEntityName'].data],'ObjectMetadata');self.assertEqual(o[entity['NSClassNameForEntity'].data],m['class_name'])
    def test_normal_unknown_and_nil_content_exit_before_callback(self):
        self.order(self.native,['guard let value = text(','guard value.isEmpty else { return value }','guard kind != .unknown else { return nil }','let fallback: String?','diagnoseEmpty?(previewLength, fallback)'])
        self.assertEqual(self.native.count('diagnoseEmpty?('),1)
    def test_zero_expected_length_and_missing_metadata_never_invoke_callback(self):
        for token in ['guard metadata.length != 0 else { return nil }','guard !metadata.url.absoluteString.isEmpty else { return nil }','guard !joinedPaths.isEmpty else { return nil }','} else { return nil }']:self.assertLess(self.native.index(token),self.native.index('diagnoseEmpty?('))
    def test_expected_lengths_and_image_color_sentinel_match_original_branch_join(self):
        for token in ['previewLength = metadata.length','previewLength = metadata.url.absoluteString.count','let joinedPaths = metadata.paths.joined()','previewLength = joinedPaths.count','previewLength = -1']:self.assertIn(token,self.native)
        self.assertNotIn('metadata.paths.count',self.native)
    def test_successful_fallback_is_diagnosed_before_final_nonempty_selection(self):
        self.order(self.native,['diagnoseEmpty?(previewLength, fallback)','guard let fallback, !fallback.isEmpty else { return value }','return fallback'])
        self.assertIn('let usedPreviewFallback = fallback.map { !$0.isEmpty } ?? false',self.d)
    def test_real_deferred_content_consumer_passes_object_items_and_fallback_state(self):
        c=body(self.s,'func content()');self.order(c,['if items.isEmpty { diagnoseEmptyRepresentations(for: object) }','ClipboardSearchRecordContent.nativeText','diagnoseEmpty: { previewLength, fallback in','self.diagnoseEmptyContent(for: object, items: items, previewLength: previewLength, fallback: fallback)'])
        self.assertNotIn('diagnoseEmpty',body(self.s,'func imageData()'))
    def test_diagnostic_samples_five_items_ten_ordered_types_and_actual_data_sizes(self):
        self.order(self.d,['items.prefix(5).enumerated().map','item.f_10037da6c().prefix(10).map','item.f_10037d810(forType: type)?.count ?? 0','joined(separator: ", ")','return "item[\\(index)]={\\(values)}"','joined(separator: "; ")'])
        for token in ['Set(','sorted(','unique','flatMap']:self.assertNotIn(token,self.d)
    def test_synced_uses_same_context_object_uri_limit_one_offset_zero_local_fetch(self):
        self.order(self.query,['object.managedObjectContext','managedObjectModel.entitiesByName["ObjectMetadata"]','let request = NSFetchRequest<NSManagedObject>()','request.entity = entity','NSPredicate(format: "objectURI == %@", object.objectID.uriRepresentation().absoluteString)','request.fetchLimit = 1','request.fetchOffset = 0','return (try? context.fetch(request).first) != nil'])
        for token in ['CKContainer','CloudJournal','URLSession','Task','MainActor','context.save','reset()']:self.assertNotIn(token,self.query)
    def test_missing_model_guard_is_explicit_adapter_not_misrepresented_CloudKit_sync(self):
        self.assertIn('return false',self.query);self.assertIn('offline model',self.p['adaptations'][0]);self.assertIn('does not connect',self.p['adaptations'][0]);self.assertFalse(self.p['full_function_migration_verified'])
    def test_message_uses_native_metadata_and_excludes_telemetry_only_fields(self):
        for token in ['value(forKey: "nativeIdentifier")','value(forKey: "createdAt")','value(forKey: "sourceApplication")','value(forKey: "name")','?? "nil"','contentDiagnostics.f_1000d468c().f_1000d4df0(']:self.assertIn(token,self.d)
        for token in ['hasAttributedString','pasteboardItemCount','source:item-content.getter','f_10037d33c','telemetry']:self.assertNotIn(token,self.d)
    def test_five_existing_methods_are_preserved_and_one_file_eight_hunks_reverse_exactly(self):
        self.assertEqual(len(self.p['unchanged_methods']),5)
        for r in self.p['unchanged_methods']:self.assertEqual(hashlib.sha256(body(pre_item_data_constructor((ROOT/r['path']).read_text()),r['symbol']).encode()).hexdigest(),r['sha256'])
        self.assertEqual(len(CHANGES),8);changed=[]
        for p,h in self.base['production'].items():
            b=(ROOT/p).read_bytes();b=pre_supplied_preview_input(b.decode()).encode()if p.endswith('.swift')else b
            if hashlib.sha256(b).hexdigest()!=h:changed.append(p)
            b=pre_empty_content_diagnostic(b.decode()).encode()if p.endswith('.swift')else b;self.assertEqual(hashlib.sha256(b).hexdigest(),h)
        self.assertEqual(changed,[self.p['current_source']]);self.assertEqual(hashlib.sha256(self.s.encode()).hexdigest(),self.p['current_source_sha256'])
    def test_old_normal_value_paths_remain_literal_except_expected_length_and_callback(self):
        old=body((ROOT/self.p['primary_projection_before']).read_text(),'static func nativeText(');current=self.native
        current=current.replace('        let previewLength: Int\n','').replace('            previewLength = metadata.length\n','').replace('            previewLength = metadata.url.absoluteString.count\n','').replace('            previewLength = -1\n','').replace('            previewLength = joinedPaths.count\n','').replace('            let joinedPaths = metadata.paths.joined()\n','').replace('guard !joinedPaths.isEmpty','guard !metadata.paths.joined().isEmpty').replace('        diagnoseEmpty?(previewLength, fallback)\n','');self.assertEqual(current,old)
    def test_no_compilation_runtime_or_full_parent_completion_claim(self):
        self.assertFalse(self.p['runtime_executed']);self.assertFalse(self.p['full_function_migration_verified']);self.assertEqual(len(self.p['adaptations']),3);self.assertIn('complete P1 parent',self.p['remaining'][0])
if __name__=='__main__':unittest.main()
