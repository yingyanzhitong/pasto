"""Shared queue-confined raw exception continuation and real unknown ObjC metadata; static only."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from raw_data_nil_bridge_scope_contract import pre_raw_data_nil_bridge
from deferred_raw_error_scope_contract import CHANGES,pre_deferred_raw_error
from content_load_diagnostic_scope_contract import pre_content_load_diagnostic
class DeferredRawErrorContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-131';cls.p=json.loads((cls.phase/'deferred-raw-error-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.d=(ROOT/'replica/Sources/PastoCore/ClipboardItemDataPersistence.swift').read_text();cls.s=pre_content_load_diagnostic((ROOT/'replica/Sources/PastoCore/ClipboardSearchRecord.swift').read_text());cls.shared=body(cls.d,'static func readRepresentations(');cls.read=body(cls.s,'private func read<T>');cls.ns={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.ns)
    def order(self,s,seq):
        p=0
        for t in seq:p=s.index(t,p)+len(t)
    def test_thirteen_original_fragments_binary_decoder_and_three_calls_bound(self):
        self.assertEqual(len(self.p['original_fragments']),13)
        for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for key in ['binary','decoder']:
            r=self.p[key];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
        for r in self.p['ARM_calls']:
            a=int(r['address'],16);b=self.ns['read'](a,4);w=int.from_bytes(b,'little');self.assertEqual(b.hex(),r['bytes']);self.assertEqual(w&0xfc000000,0x94000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(a+4*d,int(r['target'],16))
    def test_original_error_branch_releases_error_and_returns_empty_array_before_search_fallback(self):
        for r in self.p['ARM_words']:self.assertEqual(self.ns['read'](int(r['address'],16),4).hex(),r['bytes'])
        self.assertEqual(int.from_bytes(self.ns['read'](0x10031b3e8,4),'little'),0xf9406c00);self.assertEqual(self.p['additional_finite_repair']['function_id'],'Paste:0x1003724f0')
    def test_shared_decoder_is_old_main_body_literal_move_except_diagnostic_resolver(self):
        p='replica/Sources/PastoCore/ClipboardItemDataPersistence.swift';old=body((self.phase/'before'/p).read_text(),'static func readItems(');tail=old[old.index('        let raw: Data'):].replace('diagnostics(for: data).f_1000d468c()','diagnostics().f_1000d468c()');self.assertEqual(pre_raw_data_nil_bridge(self.shared),'{\n'+tail);self.assertEqual(hashlib.sha256(pre_raw_data_nil_bridge(self.shared).encode()).hexdigest(),self.p['shared_raw_reader_body_sha256'])
    def test_main_copy_keeps_same_data_and_existing_per_data_logger_resolver(self):
        s=body(cls_source:=self.d,'static func readItems(');self.order(s,['object.value(forKey: "data") as? NSManagedObject','return readRepresentations(from: data) { diagnostics(for: data) }']);self.assertNotIn('OriginalNamedDiagnostic.f_1000d4624',s);self.assertIn('@MainActor static func readItems',cls_source)
    def test_helper_has_no_actor_hop_and_log_precedes_some_empty_return(self):
        self.assertIn('static func readRepresentations(from data: NSManagedObject,',self.d);self.assertIn('diagnostics: () -> OriginalNamedDiagnostic',self.d);self.order(self.shared,['OriginalObjCExceptionBridge.f_1002ffc68','rawPasteboardItems','catch let error as OriginalObjCExceptionError','diagnostics().f_1000d468c().f_1000d4e0c','return []','catch { return nil }','autoreleasepool'])
        for t in ['Task','MainActor.','DispatchQueue','context.save','context.reset','rollback']:self.assertNotIn(t,self.shared)
    def test_search_fetch_and_shared_read_and_projection_stay_on_same_private_context_queue(self):
        self.order(self.read,['NSManagedObjectContext(concurrencyType: .privateQueueConcurrencyType)','context.persistentStoreCoordinator = coordinator','context.performAndWait','OriginalObjCExceptionBridge.withResult','context.existingObject(with: objectID)','object.value(forKey: "data") as? NSManagedObject','ClipboardItemDataPersistence.readRepresentations(from: data','return try project(object, items)']);self.assertEqual(self.read.count('readRepresentations('),1);self.assertNotIn('rawPasteboardItems',self.read)
    def test_background_diagnostic_is_lazy_named_per_fresh_context_not_a_global_pool(self):
        self.assertIn('OriginalNamedDiagnostic.f_1000d4624(name: "ItemDataEntity")',self.read);self.assertNotIn('static let diagnostics',self.s);self.assertNotIn('diagnosticsKey',self.read);self.assertEqual(self.read.count('NSManagedObjectContext('),1)
    def test_nullable_raw_uses_original_bridge_and_typed_error_reaches_projection_not_outer_catch(self):
        self.assertIn('Data._unconditionallyBridgeFromObjectiveC(raw)',self.shared);self.assertNotIn('throw CocoaError',self.shared);self.assertIn('catch { return nil }',self.shared);self.assertIn('}) else { return nil }',self.read);self.order(self.read,['readRepresentations(from: data','return try project(object, items)','} catch {','logger.error','return nil']);self.assertIn('return []',body(self.shared,'catch let error as OriginalObjCExceptionError'))
    def test_current_native_typed_fallback_and_image_projection_remain_exact(self):
        for marker in ['static func nativeText(','func content()','func imageData()']:
            p='replica/Sources/PastoCore/ClipboardSearchRecord.swift';self.assertEqual(body(self.s,marker),body((self.phase/'before'/p).read_text(),marker))
    def test_eleven_methods_and_six_sources_protect_storage_main_logger_and_unknowns(self):
        self.assertEqual(len(self.p['source_refs']),11)
        for r in self.p['source_refs']:self.assertEqual(hashlib.sha256(body(pre_content_load_diagnostic((ROOT/r['path']).read_text()),r['symbol']).encode()).hexdigest(),r['sha256'])
        for p,h in dict(self.p['shared_sources'],**self.p['current_sources']).items():self.assertEqual(hashlib.sha256(pre_content_load_diagnostic((ROOT/p).read_text()).encode()if p.endswith('.swift')else(ROOT/p).read_bytes()).hexdigest(),h)
    def test_ObjC_category_and_selector_and_types_are_real_chained_relative_data(self):
        p=self.p['objc_setter_metadata']
        for key in ['category','name_pointer','method_list','selector_pointer']:
            r=p[key];v,c=self.ns['reachable_pointer'](int(r['address'],16));self.assertEqual(hex(v),r['raw']);self.assertEqual(c,r['chain']);self.assertEqual(self.ns['base']+(v&((1<<36)-1)),int(r['target'],16))
        for r in p['relative_method_fields']:
            a=int(r['address'],16);b=self.ns['read'](a,4);self.assertEqual(b.hex(),r['bytes']);self.assertEqual(a+struct.unpack('<i',b)[0],int(r['target'],16))
        self.assertEqual(p['selector'],'setText:');self.assertEqual(p['types'],'v24@0:8@16');self.assertEqual(p['objc_IMP'],'0x1000f72a4');self.assertNotEqual(p['objc_IMP'],p['swift_helper'])
    def test_actual_category_class_import_is_NSTextView_not_guessed_from_adjacent_function(self):
        r=self.p['objc_setter_metadata']['class_bind'];v,c=self.ns['reachable_pointer'](int(r['address'],16));self.assertEqual(hex(v),r['raw']);self.assertEqual(v&0xffffff,r['import_ordinal']);fix=self.ns['fixup'][0];h=struct.unpack_from('<7I',self.ns['raw'],fix);self.assertEqual(h[5],1);w=struct.unpack_from('<I',self.ns['raw'],fix+h[2]+4*(v&0xffffff))[0];self.assertEqual(hex(w),r['import_word']);a=fix+h[3]+(w>>9);raw=self.ns['raw'];self.assertEqual(raw[a:raw.index(b'\0',a)].decode(),'_OBJC_CLASS_$_NSTextView')
    def test_unknowns_not_silently_upgraded_by_void_ObjC_setter_or_absent_Nib(self):
        self.assertTrue(self.p['objc_setter_metadata']['swift_helper_not_directly_linked_by_this_method_list']);self.assertEqual(self.p['unknown_review']['addresses'],['Paste:0x10004430c','Paste:0x1000f733c']);self.assertIn('no inference from missingresources',self.p['unknown_review']['coder']);self.assertFalse(self.p['full_function_migration_verified']);self.assertFalse(self.p['runtime_executed'])
    def test_three_hunks_exactly_reverse_all247_sources_and_preserve_user_changes(self):
        self.assertEqual(len(CHANGES),3)
        for p,h in self.base['production'].items():
            b=(ROOT/p).read_bytes();b=pre_deferred_raw_error(b.decode()).encode()if p.endswith('.swift')else b;self.assertEqual(hashlib.sha256(b).hexdigest(),h)
        self.assertEqual(self.p['new_difference_records'],0);self.assertEqual(len(self.p['remaining']),3)
if __name__=='__main__':unittest.main()
