"""Native local filter images and first-name readers; never executes AppKit/CoreData."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from suggestion_filter_icon_scope_contract import CHANGES,HISTORICAL_TEST_CHANGES,pre_suggestion_filter_icon,pre_suggestion_filter_icon_bytes,pre_suggestion_filter_icon_history_bytes
from suggestion_description_scope_contract import pre_suggestion_description_bytes, pre_suggestion_description_history_bytes
class SuggestionFilterIconContracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ph=ROOT/'.local/p0-repair/phase-185';cls.p=json.loads((cls.ph/'suggestion-filter-icon-contract.json').read_text());cls.b=json.loads((cls.ph/'baseline.json').read_text());cls.source=(ROOT/'replica/Sources/PastoCore/ClipboardSourcePersistence.swift').read_text();cls.persistence=(ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text();cls.store=(ROOT/'replica/Sources/PastoCore/ClipboardStore.swift').read_text();cls.ui=(ROOT/'replica/Sources/Pasto/UI/FilterBrowser.swift').read_text();cls.icon=body(cls.ui,'private static func f_1000546e0(');cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
 def word(self,a):return struct.unpack('<I',self.n['read'](a,4))[0]
 def order(self,s,tokens):
  values=[s.index(t)for t in tokens];self.assertEqual(values,sorted(values))
 def test31_original_fragments_binary_and_decoder_fresh(self):
  self.assertEqual(len(self.p['original_fragments']),31)
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for key in ['binary','decoder']:
   r=self.p[key];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
 def test14_ranges208_direct_branches_bound(self):
  self.assertEqual(len(self.p['machine_ranges']),14);self.assertEqual(len(self.p['branches']),208)
  for r in self.p['machine_ranges']:
   d=self.n['read'](int(r['address'],16),int(r['end'],16)-int(r['address'],16));self.assertEqual(d.hex(),r['bytes']);self.assertEqual(hashlib.sha256(d).hexdigest(),r['sha256'])
  for r in self.p['branches']:
   a=int(r['call'],16);w=self.word(a);self.assertEqual(hex(w),r['word']);v=w&0x3ffffff;v=v-(1<<26)if v&(1<<25)else v;self.assertEqual(hex(a+4*v),r['target'])
 def test25_real_ARC_and_error_release_imports(self):
  self.assertEqual(len(self.p['imports']),25)
  for r in self.p['imports']:
   v,c=self.n['reachable_pointer'](int(r['pointer'],16));self.assertEqual(c,r['chain']);self.assertTrue(v>>63);f=self.n['fixup'][0];raw=self.n['raw'];h=struct.unpack_from('<7I',raw,f);e=struct.unpack_from('<I',raw,f+h[2]+4*(v&0xffffff))[0];o=f+h[3]+(e>>9);self.assertEqual(raw[o:raw.index(b'\0',o)].decode(),r['symbol'])
  self.assertIn(('0x10032af24','_swift_errorRelease'),[(r['call'],r['symbol'])for r in self.p['imports']])
 def test9_real_selector_fixups_not_Ghidra_veneer_names(self):
  self.assertEqual(len(self.p['selectors']),9)
  for r in self.p['selectors']:
   v,c=self.n['reachable_pointer'](int(r['pointer'],16));self.assertEqual(c,r['chain']);self.assertFalse(v>>63);dest=self.n['base']+(v&((1<<36)-1));self.assertEqual(hex(dest),r['target']);self.assertEqual(self.n['read'](dest,len(r['name'])+1),r['name'].encode()+b'\0')
  self.assertTrue({'rawIcon','rawType','setFetchLimit:','setFetchOffset:','setFetchBatchSize:'}<={r['name']for r in self.p['selectors']})
 def test_two_actual_reader_witness_slots_bind_name_functions(self):
  self.assertEqual([r['target']for r in self.p['reader_slots']],['0x10035fa18','0x10035fe08'])
  for r in self.p['reader_slots']:
   v,c=self.n['reachable_pointer'](int(r['address'],16));self.assertEqual(c,r['chain']);self.assertFalse(v>>63);self.assertEqual(hex(self.n['base']+(v&((1<<36)-1))),r['target'])
 def test_two_native_predicate_strings_are_decoded_from_MOV_words(self):
  self.assertEqual(len(self.p['predicates']),2)
  for r in self.p['predicates']:
   words=[self.word(int(r['address'],16)+4*i)for i in range(8)];self.assertEqual([hex(w)for w in words],r['words']);values=[]
   for group,reg in [(words[:4],8),(words[4:],9)]:
    value=0
    for w in group:
     self.assertEqual(w&31,reg);kind=w&0x7f800000;self.assertIn(kind,[0x52800000,0x72800000]);shift=((w>>21)&3)*16;part=(w>>5)&65535;value=part<<shift if kind==0x52800000 else(value&~(65535<<shift))|(part<<shift)
    values.append(value)
   data=struct.pack('<QQ',*values);self.assertEqual(data.hex(),r['bytes']);self.assertEqual(data[:13],b'name ==[c] %@')
 def test_device_and_required_fallback_names_match_native_static_bytes(self):
  self.assertEqual([r['name']for r in self.p['symbols']],['iphone','ipad','macbook','questionmark.square'])
  for r in self.p['symbols']:
   d=self.n['read'](int(r['target'],16),len(bytes.fromhex(r['bytes'])));self.assertEqual(d.hex(),r['bytes']);self.assertEqual(d[:len(r['name'])].decode(),r['name'])
 def test_first_name_lookup_preserves_native_class_defaults_case_option_and_first_only(self):
  s=body(self.source,'private func firstNamed<');self.order(s,['OriginalManagedFetchRequest.make(for: entity)','NSPredicate(format: "name ==[c] %@", name)','request.fetchLimit = 1','request.fetchOffset = 0','return (try? context.fetch(request))?.first'])
  for t in ['items.@count','MATCHES','UUID','lowercased','sortDescriptors =','fetchBatchSize =','insertNewObject','setValue']:self.assertNotIn(t,s)
  factory=body((ROOT/'replica/Sources/PastoCore/OriginalManagedItem.swift').read_text(),'static func make<Entity:');self.assertIn('request.fetchBatchSize = 20',factory);self.assertIn('entity.defaultSortDescriptors',factory)
 def test_application_entity_missing_differs_from_missing_or_corrupt_raw_icon(self):
  s=body(self.source,'func applicationImage(named');self.order(s,['guard let application = firstNamed(PastoApplicationEntity.self, name: name) else { return nil }','application.value(forKey: "rawIcon")','flatMap(NSImage.init(data:)) ?? NSImage()'])
  for t in ['sourceApplications','NSWorkspace','items','insertNewObject','setValue','snapshot']:self.assertNotIn(t,s)
 def test_device_unsigned_native_domain_and_local_read_do_not_create_rows(self):
  self.assertEqual(self.word(0x10031213c),0xf100081f);self.assertEqual(self.word(0x100312140),0x54000068);self.assertEqual(self.word(0x10031214c),0xd4200020)
  s=body(self.source,'func deviceType(named');self.order(s,['firstNamed(PastoDeviceEntity.self, name: name)','device.value(forKey: "rawType")','precondition(rawType >= 0 && rawType < 3)','return UInt8(rawType)'])
  for t in ['device(named:','currentDevice','insertNewObject','setValue','modelName']:self.assertNotIn(t,s)
 def test_store_delegates_to_same_persistence_queue_without_DTO_fallbacks(self):
  for name,source in [('searchApplicationImage','applicationImage'),('searchDeviceType','deviceType')]:
   facade=body(self.store,'public func '+name+'(');self.assertIn('persistence.'+name+'(named: name)',facade);inner=body(self.persistence,'func '+name+'(');self.assertIn('context.performAndWait { sources.'+source+'(named: name) }',inner)
   for t in ['sourceApplications','items','NSWorkspace','Task','DispatchQueue']:self.assertNotIn(t,facade+inner)
 def test_local_color_device_and_app_branches_precede_generic_fallback(self):
  self.order(self.icon,['kind == 5','store.tabListTarget(identifier: value)?.colorCode','OriginalPinboardHeaderIcon.image(height: 12, shared: false','OriginalPinboardColor(canonicalColorCode: colorCode).color()','kind == 4','store.searchDeviceType(named: value)','type == 0 ? "iphone" : type == 1 ? "ipad" : "macbook"','kind == 0','store.searchApplicationImage(named: value)','guard let symbol = OriginalSearchFilterSymbols.f_100054b2c']);self.assertIn('return systemImage(symbol)',self.icon[self.icon.index('guard let symbol ='):])
  self.assertEqual(body(self.icon,'guard let symbol ='),'{ return nil }')
 def test_real_color_12_point_wrapper_and_device_symbol_calls_are_bound(self):
  calls={r['call']:r['target']for r in self.p['branches']};self.assertEqual(calls['0x10005479c'],'0x10031212c');self.assertEqual(calls['0x1000547b0'],'0x10020d228');self.assertEqual(calls['0x1000548ac'],'0x10020d244');self.assertEqual(calls['0x1000548e8'],'0x10020d410');self.assertEqual(calls['0x1000548b8'],'0x1003de9a0');self.assertEqual(calls['0x1000548d0'],'0x1003ecffc');self.assertEqual(self.word(0x1000548c8),0x1e651000)
 def test_symbol_probe_recreate_fallback_and_trap_are_not_collapsed(self):
  s=body(self.ui,'private static func systemImage(');self.assertEqual(s.count('OriginalSystemImageFunctions.f_1000f653c(name)'),2);self.order(s,['if OriginalSystemImageFunctions.f_1000f653c(name) != nil','return OriginalSystemImageFunctions.f_1000f653c(name)!','return OriginalSystemImageFunctions.f_1000f653c("questionmark.square")!'])
  calls={r['call']:r['target']for r in self.p['branches']}
  for a in ['0x10005484c','0x100054860','0x100054894','0x100054910','0x100054924','0x100054950']:self.assertEqual(calls[a],'0x1000f653c')
  for a in [0x100054868,0x10005492c,0x100054980,0x100054984]:self.assertEqual(self.word(a),0xd4200020)
 def test_original_caption_after_image_and_raw_input_repairs_are_kept(self):
  s=body(self.ui,'static func chip(');self.order(s,['value = rawValue','let image = f_1000546e0(kind: selection.group, value: value, store: store)','let title = OriginalSearchSuggestions.f_1002ddc10','store.tabListTarget(identifier: $0)?.name','return ReplicaSearchFilterChip'])
  for t in ['NSWorkspace','store.items','store.sourceApplications']:self.assertNotIn(t,s+self.icon)
 def test18_neighbor_methods_and11_shared_sources_unchanged(self):
  self.assertEqual(len(self.p['unchanged_methods']),18)
  for r in self.p['unchanged_methods']:self.assertEqual(hashlib.sha256(body((ROOT/r['path']).read_text(),r['symbol']).encode()).hexdigest(),r['body_sha256'])
  r=self.p['reused_drawing_helper'];self.assertEqual(source_fragments(ROOT/r['original_path'])['0x1003ed004']['sha256'],r['original_sha256']);self.assertEqual(hashlib.sha256(body((ROOT/r['source_path']).read_text(),r['source_symbol']).encode()).hexdigest(),r['source_body_sha256'])
  self.assertEqual(len(self.p['shared_sources']),11)
  for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_suggestion_description_bytes(ROOT/p)).hexdigest(),h)
 def test7_exact_hunks_reverse247_sources_and_prior_snapshots_idempotently(self):
  self.assertEqual(len(CHANGES),7);self.assertEqual(CHANGES,json.loads((self.ph/'production-changes.json').read_text()));changed=[]
  for p,h in self.b['production'].items():
   if hashlib.sha256(pre_suggestion_description_bytes(ROOT/p)).hexdigest()!=h:changed.append(p)
   self.assertEqual(hashlib.sha256(pre_suggestion_filter_icon_bytes(ROOT/p)).hexdigest(),h,p);old=(self.ph/'before'/p).read_bytes();self.assertEqual(pre_suggestion_filter_icon(old.decode()).encode()if p.endswith('.swift')else old,old,p)
  self.assertEqual(set(changed),set(self.p['current_sources']));self.assertEqual(len(changed),4)
 def test9_historical_patterns_restore362_Python_inputs(self):
  self.assertEqual(len(HISTORICAL_TEST_CHANGES),9);self.assertEqual(HISTORICAL_TEST_CHANGES,self.p['historical_test_changes']);expected={}
  for p,old,new,count in HISTORICAL_TEST_CHANGES:
   if p not in expected:expected[p]=(self.ph/'before'/p).read_text()
   self.assertEqual(expected[p].count(old),count);expected[p]=expected[p].replace(old,new)
  self.assertEqual(len(expected),3)
  for p,h in self.b['tests'].items():self.assertEqual(pre_suggestion_description_history_bytes(ROOT/p).decode(),expected.get(p,(self.ph/'before'/p).read_text()),p);self.assertEqual(hashlib.sha256(pre_suggestion_filter_icon_history_bytes(ROOT/p)).hexdigest(),h,p)
 def test_protocol_source_results_and_image_factory_call_counts(self):
  # Source-bound protocol model; no image decoder, Foundation comparison or CoreData execution.
  for entity in [None,{'raw':None},{'raw':'bad'},{'raw':'valid'}]:
   result=None if entity is None else'icon'if entity['raw']=='valid'else'empty-image'
   self.assertEqual(result,{None:None,'none':'empty-image','bad':'empty-image','valid':'icon'}[None if entity is None else entity['raw']or'none'])
  def symbol(probe,second=None,fallback='fallback'):
   calls=['name']
   if probe:
    calls.append('name');return second,calls
   calls.append('questionmark.square');return fallback,calls
  self.assertEqual(symbol(True,'image'),('image',['name','name']));self.assertEqual(symbol(False),('fallback',['name','questionmark.square']));self.assertIsNone(symbol(True,None)[0]);self.assertIn('f_1000f653c(name)!',body(self.ui,'private static func systemImage('))
 def test_CKShare_subchain_explicitly_excluded_and_whole_migration_open(self):
  self.assertEqual([r['function_id']for r in self.p['contracts']],['Paste:0x1000546e0','Paste:0x10035fa18','Paste:0x10035fe08']);self.assertFalse(self.p['runtime_executed']);self.assertFalse(self.p['full_function_migration_verified']);self.assertIn('0f733c',self.p['remaining'][0]);ex=self.p['excluded_subchains'][0];self.assertEqual(ex['root_function_id'],'Paste:0x100328e60');self.assertIn('CKShare',ex['reason']);self.assertIn('shared: false',self.icon)
if __name__=='__main__':unittest.main()
