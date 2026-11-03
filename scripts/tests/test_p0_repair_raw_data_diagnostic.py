"""Original local logger error branch and current data-object ownership, source only."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from deferred_raw_error_scope_contract import pre_deferred_raw_error
from test_offline_p0_contracts import body
from item_creation_date_scope_contract import pre_item_creation_date
from raw_data_diagnostic_scope_contract import CHANGES,pre_raw_data_diagnostic
class RawDataDiagnosticContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-127';cls.p=json.loads((cls.phase/'raw-data-diagnostic-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.path=next(iter(cls.p['current_sources']));cls.s=pre_deferred_raw_error((ROOT/cls.path).read_text());cls.reader=body(cls.s,'static func readItems(');cls.logger=body(cls.s,'private static func diagnostics(');cls.ns={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.ns)
    def order(self,s,seq):
        p=0
        for t in seq:p=s.index(t,p)+len(t)
    def test_seven_original_fragments_and_static_inputs_bound(self):
        self.assertEqual(len(self.p['original_fragments']),7)
        for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for r in [self.p['binary'],self.p['decoder'],self.p['sdk_header']]:self.assertEqual(hashlib.sha256(Path(r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_original_real_logger_factory_getter_emitter_and_separate_DI_calls(self):
        self.assertEqual(len(self.p['ARM_calls']),5)
        for r in self.p['ARM_calls']:
            a=int(r['address'],16);b=self.ns['read'](a,4);w=int.from_bytes(b,'little');self.assertEqual(b.hex(),r['bytes']);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(a+4*d,int(r['target'],16))
    def test_removed_Ghidra_error_block_is_real_nonzero_error_branch_not_dead(self):
        for r in self.p['ARM_words']:self.assertEqual(self.ns['read'](int(r['address'],16),4).hex(),r['bytes'])
        a=0x10031b250;w=int.from_bytes(self.ns['read'](a,4),'little');d=(w>>5)&0x7ffff
        if d&0x40000:d-=0x80000
        self.assertEqual(a+4*d,0x10031b3f0);self.assertEqual(w&31,21)
    def test_constructor_name_immediates_decode_ItemDataEntity(self):
        chunks=[]
        for start in [0x10031b4c8,0x10031b4d8]:
            v=0
            for a in range(start,start+16,4):
                w=int.from_bytes(self.ns['read'](a,4),'little');v|=((w>>5)&0xffff)<<(16*((w>>21)&3))
            chunks.append(v.to_bytes(8,'little'))
        self.assertEqual((chunks[0]+chunks[1])[:14],b'ItemDataEntity')
    def test_actual_field_offsets_and_error_level_are_separate_from_telemetry(self):
        r=self.p['logger_field_offsets'];self.assertEqual(self.ns['read'](int(r['address'],16),24).hex(),r['bytes']);self.assertEqual([r[k]for k in ['logger','telemetry','itemSerializationFormat']],[8,16,24]);self.assertEqual(int.from_bytes(self.ns['read'](0x1000d4e20,4),'little'),0x52800060)
        self.assertIn('emit(level: 3, message: message)',(ROOT/'replica/Sources/PastoCore/OriginalLocalDiagnostics.swift').read_text())
    def test_original_message_prefix_uses_actual_chars_not_bridge_minus32_address(self):
        r=self.p['message_prefix'];self.assertEqual(self.ns['read'](int(r['address'],16),r['length']).decode(),r['text']);self.assertEqual(r['length'],34);self.assertIn('f_1000d4e0c("Unreadable pasteboard items blob: \(error)")',self.reader)
    def test_current_error_logs_same_data_named_sink_before_empty_return(self):
        self.order(self.reader,['guard let data =','OriginalObjCExceptionBridge.f_1002ffc68','data.value(forKey: "rawPasteboardItems")','catch let error as OriginalObjCExceptionError','diagnostics(for: data).f_1000d468c().f_1000d4e0c','return []','catch { return nil }','autoreleasepool']);self.assertEqual(self.reader.count('diagnostics(for:'),1)
    def test_normal_read_missing_graph_and_other_error_paths_remain_exact(self):
        old=body((self.phase/'before'/self.path).read_text(),'static func readItems(');self.assertEqual(body(pre_raw_data_diagnostic(self.s),'static func readItems('),old);self.assertIn('guard let data = object.value(forKey: "data") as? NSManagedObject else { return nil }',self.reader)
    def test_logger_is_retained_by_data_object_and_reused_before_factory_call(self):
        self.order(self.logger,['objc_getAssociatedObject(data, &diagnosticsKey)','return existing','OriginalNamedDiagnostic.f_1000d4624(name: "ItemDataEntity")','objc_setAssociatedObject(data, &diagnosticsKey, diagnostics, .OBJC_ASSOCIATION_RETAIN_NONATOMIC)','return diagnostics']);self.assertIn('@MainActor private static var diagnosticsKey: UInt8 = 0',self.s);self.assertIn('@MainActor private static func diagnostics',self.s)
        for t in ['[UUID:','ObjectIdentifier','static let diagnostics','Notification','Task','DispatchQueue','Timer']:self.assertNotIn(t,self.logger)
    def test_existing_named_logger_resolves_sink_lazily_and_caches_under_lock(self):
        s=(ROOT/'replica/Sources/PastoCore/OriginalLocalDiagnostics.swift').read_text();self.assertIn('self.cached = nil',body(s,'private init(name:'));self.order(body(s,'public func f_1000d468c()'),['lock.withLockUnchecked','if let cached { return cached }','Self.factoryDependency.f_1000da768()(name)','cached = sink','return sink'])
    def test_existing_model_replace_and_migration_methods_remain_unchanged(self):
        self.assertEqual(len(self.p['source_refs']),3)
        for r in self.p['source_refs']:self.assertEqual(hashlib.sha256(body(pre_item_creation_date((ROOT/r['path']).read_text()),r['symbol']).encode()).hexdigest(),r['sha256'])
        self.assertIn('data.managedObjectClassName = "NSManagedObject"',self.s);self.assertNotIn('objc_removeAssociatedObjects',self.s)
    def test_seven_shared_sources_no_DI_codec_copy_device_or_bridge_edits(self):
        self.assertEqual(len(self.p['shared_sources']),7)
        for p,h in dict(self.p['shared_sources'],**self.p['current_sources']).items():self.assertEqual(hashlib.sha256(pre_deferred_raw_error((ROOT/p).read_text()).encode()).hexdigest(),h)
    def test_three_hunks_reverse_all247_production_files_without_erasing_user_changes(self):
        self.assertEqual(len(CHANGES),3)
        for p,h in self.base['production'].items():
            b=(ROOT/p).read_bytes();b=pre_raw_data_diagnostic(b.decode()).encode()if p.endswith('.swift')else b;self.assertEqual(hashlib.sha256(b).hexdigest(),h)
    def test_partial_scope_keeps_constructor_error_rendering_and_extra_callback_limits(self):
        self.assertEqual(self.p['new_difference_records'],0);self.assertFalse(self.p['full_function_migration_verified']);self.assertFalse(self.p['runtime_executed']);self.assertEqual(len(self.p['remaining']),3);self.assertIn('lazily on first exception',self.p['remaining'][0]);self.assertIn('error interpolation',self.p['remaining'][1]);self.assertNotIn('telemetry',self.logger)
if __name__=='__main__':unittest.main()
