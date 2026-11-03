"""Current local-device source and actual original bytes, no framework/hardware runtime."""
from pathlib import Path
import hashlib,json,re,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from raw_data_diagnostic_scope_contract import pre_raw_data_diagnostic
from test_offline_p0_contracts import body
from source_entity_lifecycle_scope_contract import pre_source_entity_lifecycle
from local_device_scope_contract import CHANGES,pre_local_device
class LocalDeviceContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-126';cls.p=json.loads((cls.phase/'local-device-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.device=(ROOT/cls.p['device_provider_file']).read_text();cls.src=(ROOT/'replica/Sources/PastoCore/ClipboardSourcePersistence.swift').read_text();cls.repo=(ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text();cls.store=(ROOT/'replica/Sources/PastoCore/ClipboardStore.swift').read_text();cls.factory=body(cls.src,'func currentDevice()');cls.capture=body(cls.store,'func addWithInsertionResult(');cls.ns={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.ns)
    def order(self,s,seq):
        p=0
        for t in seq:p=s.index(t,p)+len(t)
    def test_fourteen_original_fragments_and_static_binary_are_bound(self):
        self.assertEqual(len(self.p['original_fragments']),14)
        for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for r in [self.p['binary'],self.p['decoder'],self.p['sdk_header']]:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_eleven_actual_factory_registry_model_and_capture_calls(self):
        self.assertEqual(len(self.p['ARM_calls']),11)
        for r in self.p['ARM_calls']:
            a=int(r['address'],16);b=self.ns['read'](a,4);w=int.from_bytes(b,'little');self.assertEqual(b.hex(),r['bytes']);self.assertEqual(w&0x7c000000,0x14000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(a+4*d,int(r['target'],16))
    def test_factory_setter_selectors_decode_actual_chain_not_stub_names(self):
        self.assertEqual([r['selector']for r in self.p['selectors']],['initWithContext:','setRawType:','setIdentifier:','setName:'])
        for r in self.p['selectors']:
            self.assertEqual(self.ns['read'](int(r['stub_address'],16),20).hex(),r['bytes']);v,c=self.ns['reachable_pointer'](int(r['pointer_address'],16));self.assertEqual(hex(v),r['pointer_raw']);self.assertEqual(self.ns['base']+(v&((1<<36)-1)),int(r['target'],16));self.assertEqual(self.ns['read'](int(r['target'],16),100).split(b'\0')[0].decode(),r['selector'])
    def test_registry_serial_property_key_and_expert_service_actual_characters(self):
        for r in self.p['strings']:self.assertEqual(self.ns['read'](int(r['address'],16),r['length']).decode(),r['value'])
        self.assertIn('"IOPlatformSerialNumber" as CFString',self.device);self.assertNotIn('IOPlatformUUID',self.device)
        a=0x1000f3620;w=int.from_bytes(self.ns['read'](a,4),'little');v=int.from_bytes(self.ns['read'](a+4,4),'little');i=((w>>5)&0x7ffff)*4+((w>>29)&3)
        if i&0x100000:i-=0x200000
        self.assertEqual((a&~4095)+(i<<12)+((v>>10)&0xfff),0x100d906f0)
    def test_actual_fallback_mov_words_spell_Unknown_and_error_words_remain_bound(self):
        for r in self.p['ARM_words']:self.assertEqual(self.ns['read'](int(r['address'],16),4).hex(),r['bytes'])
        value=0
        for a in range(0x1000f36b8,0x1000f36c8,4):
            w=int.from_bytes(self.ns['read'](a,4),'little');value|=((w>>5)&0xffff)<<(16*((w>>21)&3))
        self.assertEqual(value.to_bytes(8,'little').rstrip(b'\0'),b'Unknown')
    def test_registry_read_each_request_no_value_cache_or_UUID_substitute(self):
        s=body(self.device,'static func f_1000f35e0()');self.order(s,['IOServiceGetMatchingService(kIOMainPortDefault, IOServiceMatching("IOPlatformExpertDevice"))','defer { _ = IOObjectRelease(service) }','guard service != 0','IORegistryEntryCreateCFProperty','takeRetainedValue() as? String','return "Unknown"','return value'])
        for t in ['static let','UUID','NSHost','cached','isEmpty']:self.assertNotIn(t,s)
    def test_hit_returns_unchanged_and_does_not_read_model_or_mutate_device(self):
        self.order(self.factory,['f_1000f35e0()','OriginalManagedFetchRequest.make(for: PastoDeviceEntity.self)','NSPredicate(format: "identifier == %@", identifier)','request.fetchLimit = 1','request.fetchOffset = 0','(try? context.fetch(request))?.first { return existing }','f_1000f36ec()','insertNewObject'])
        self.assertNotIn('UUID',self.factory);self.assertNotIn('name ==',self.factory)
        managed=(ROOT/'replica/Sources/PastoCore/OriginalManagedItem.swift').read_text();self.assertIn('request.fetchBatchSize = 20',body(managed,'static func make<Entity:'))

    def test_miss_field_order_and_required_createdAt_adapter_are_explicit(self):
        self.order(self.factory,['let name =','insertNewObject','setValue(Int64(2), forKey: "rawType")','setValue(identifier, forKey: "identifier")','setValue(name, forKey: "name")','return object']);self.assertNotIn('throws',self.src[self.src.index('func currentDevice()'):self.src.index('func currentDevice()')+50])
        managed=(ROOT/'replica/Sources/PastoCore/OriginalManagedItem.swift').read_text();device=body(managed,'class PastoDeviceEntity:');self.assertIn('setPrimitiveValue(Date(), forKey: "createdAt")',body(device,'override func awakeFromInsert()'));self.assertIn('NSStringFromClass(PastoDeviceEntity.self)',self.repo)

    def test_fetch_error_is_local_empty_fallback_not_throw_or_old_name_lookup(self):
        self.assertIn('try? context.fetch(request)',self.factory);self.assertNotIn('device(named:',self.factory)
        a=0x10032af1c;w=int.from_bytes(self.ns['read'](a,4),'little');d=(w>>5)&0x7ffff
        if d&0x40000:d-=0x80000
        self.assertEqual(a+4*d,0x10032af30);self.assertEqual(int.from_bytes(self.ns['read'](0x10032af2c,4),'little')&0xffc00000,0xf9400000)
    def test_capture_new_target_assigns_same_device_then_content_and_preserves_hit_device(self):
        self.order(self.capture,['if capturedTarget == nil','sourceDevice = transaction.repository.initializeCapturedDevice(target!)','Self.originalPasteboardItems(from:','replaceCapturedItemData(target!','applyCapturedSources(target!','preserveDevice: true'])
        s=body(self.repo,'func initializeCapturedDevice(');self.order(s,['let device = sources.currentDevice()','target.object.setValue(device, forKey: "device")','return device.value(forKey: "name") as? String ?? ""']);self.assertEqual(self.capture.count('initializeCapturedDevice('),1)
    def test_legacy_name_UUID_helper_and_ten_neighbor_methods_unchanged(self):
        self.assertEqual(len(self.p['source_refs']),10)
        for r in self.p['source_refs']:self.assertEqual(hashlib.sha256(body(pre_source_entity_lifecycle((ROOT/r['path']).read_text()),r['symbol']).encode()).hexdigest(),r['sha256'])
        s=body(self.src,'private func device(named name:');self.assertIn('UUID().uuidString',s);self.assertIn('key: "name"',s)
    def test_model_uses_hw_model_and_trims_edges_only_before_five_mappings(self):
        self.assertIn('modelName(f_1000f4774("hw.model"))',self.device);s=body(self.device,'static func modelName(');self.order(s,['trimmingCharacters(in: CharacterSet.letters.inverted)','switch trimmed.lowercased()','default: return trimmed']);self.assertNotIn('.filter',s);self.assertNotIn('Unknown',s)
        self.assertEqual(dict(re.findall(r'case "([a-z]+)": return "([^"]+)"',s)),{'macbook':'MacBook','macbookpro':'MacBook Pro','macbookair':'MacBook Air','imac':'iMac','macpro':'Mac Pro'})
    def test_model_examples_are_derived_from_current_source_map_and_edge_trim(self):
        s=body(self.device,'static func modelName(');mapping=dict(re.findall(r'case "([a-z]+)": return "([^"]+)"',s))
        def model(v):
            i=0;j=len(v)
            while i<j and not v[i].isalpha():i+=1
            while j>i and not v[j-1].isalpha():j-=1
            v=v[i:j];return mapping.get(v.lower(),v)
        for v,w in [('MacBookPro18,3','MacBook Pro'),('MacBookAir10,1','MacBook Air'),('Macmini9,1','Macmini'),('Mac_Pro1,1','Mac_Pro'),('123',''),('iMac21,1','iMac'),('Mac14,7','Mac')]:self.assertEqual(model(v),w)
    def test_sysctl_two_ignored_status_reads_size_zero_buffer_and_UTF8_NUL_prefix(self):
        s=body(self.device,'static func f_1000f4774(');self.assertEqual(s.count('_ = sysctlbyname('),2);self.order(s,['var size = 0','sysctlbyname(key, nil, &size, nil, 0)','[UInt8](repeating: 0, count: size)','withUnsafeMutableBytes','sysctlbyname(key, buffer.baseAddress, &size, nil, 0)','String(bytes: bytes.prefix { $0 != 0 }, encoding: .utf8) ?? ""']);self.assertNotIn('guard',s)
    def test_zero_NUL_and_invalid_UTF8_examples_follow_allocated_buffer_not_new_size(self):
        def decode(v):
            try:return v.split(b'\0')[0].decode('utf8')
            except UnicodeDecodeError:return ''
        for v,w in [(b'',''),(b'\0abc',''),(b'Mac14,7\0xx','Mac14,7'),(b'\xff',''),(b'Mac','Mac')]:self.assertEqual(decode(v),w)
        self.assertIn('bytes.prefix { $0 != 0 }',self.device);self.assertNotIn('bytes.prefix(size)',self.device)
    def test_five_hunks_inverse_all247_existing_production_sources_exactly(self):
        self.assertEqual(len(CHANGES),5)
        for p,h in self.base['production'].items():
            b=(ROOT/p).read_bytes();b=pre_local_device(b.decode()).encode()if p.endswith('.swift')else b;self.assertEqual(hashlib.sha256(b).hexdigest(),h)
        self.assertEqual(len(self.base['production']),247)
    def test_shared_sources_and_current_three_source_hashes_bound(self):
        self.assertEqual(len(self.p['current_sources']),3)
        for p,h in dict(self.p['shared_sources'],**self.p['current_sources']).items():self.assertEqual(hashlib.sha256(pre_raw_data_diagnostic((ROOT/p).read_text()).encode()).hexdigest(),h)
    def test_only_finite_device_contracts_and_no_claim_of_runtime_or_P0_completion(self):
        self.assertEqual(len(self.p['contracts']),4);self.assertEqual(self.p['new_difference_records'],4);self.assertFalse(self.p['full_function_migration_verified']);self.assertFalse(self.p['runtime_executed']);self.assertEqual(len(self.p['remaining']),3)
if __name__=='__main__':unittest.main()
