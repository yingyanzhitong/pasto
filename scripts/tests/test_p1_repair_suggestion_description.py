"""Registered description and query formatting: static evidence/models, no Swift or frameworks."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from suggestion_description_scope_contract import CHANGES,HISTORICAL_TEST_CHANGES,pre_suggestion_description,pre_suggestion_description_bytes,pre_suggestion_description_history_bytes
from text_edit_mode_scope_contract import pre_text_edit_mode_bytes, pre_text_edit_mode_history_bytes
class SuggestionDescriptionContracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ph=ROOT/'.local/p0-repair/phase-186';cls.p=json.loads((cls.ph/'suggestion-description-contract.json').read_text());cls.b=json.loads((cls.ph/'baseline.json').read_text());cls.core=(ROOT/'replica/Sources/PastoCore/OriginalSearchSuggestions.swift').read_text();cls.formatter=body(cls.core,'public static func f_1002dc9b8(_ suggestion: Suggestion,\n                                  listName: (String) -> String? = { resolveListName($0) }) -> String');cls.caption=body(cls.core,'public static func f_1002ddc10(kind: UInt8, value: String,\n                                  listName: (String) -> String? = { resolveListName($0) }) -> String');cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
 def test_original_fragments_and_reused_machine_evidence_remain_fresh(self):
  self.assertEqual(len(self.p['original_fragments']),14)
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for r in [self.p['binary'],self.p['decoder']]+self.p['reused_original_evidence']:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
 def test_ten_ranges_and_eighty_actual_direct_branches(self):
  self.assertEqual(len(self.p['machine_ranges']),10);self.assertEqual(len(self.p['branches']),80)
  for r in self.p['machine_ranges']:
   data=self.n['read'](int(r['address'],16),int(r['end'],16)-int(r['address'],16));self.assertEqual(data.hex(),r['bytes']);self.assertEqual(hashlib.sha256(data).hexdigest(),r['sha256'])
  for r in self.p['branches']:
   a=int(r['call'],16);w=struct.unpack('<I',self.n['read'](a,4))[0];self.assertEqual(hex(w),r['word']);v=w&0x3ffffff;v=v-(1<<26)if v&(1<<25)else v;self.assertEqual(hex(a+v*4),r['target'])
 def test_real_resilient_conformance_and_nested_type_metadata(self):
  for r in self.p['metadata_ranges']:
   data=self.n['read'](int(r['address'],16),len(bytes.fromhex(r['bytes'])));self.assertEqual(data.hex(),r['bytes']);self.assertEqual(hashlib.sha256(data).hexdigest(),r['sha256'])
  self.assertEqual(struct.unpack('<I',self.n['read'](0x100c3e22c,4))[0],0x30000);self.assertEqual(struct.unpack('<I',self.n['read'](0x100c3e230,4))[0],1);self.assertEqual(self.n['read'](0x100c3e24c,11),b'Suggestion\0');self.assertEqual(self.n['read'](0x100c3e448,12),b'SearchQuery\0')
 def test_protocol_and_description_requirement_resolve_actual_dyld_imports(self):
  self.assertEqual(len(self.p['relative_links']),7)
  for r in self.p['relative_links']:
   a=int(r['address'],16);data=self.n['read'](a,4);self.assertEqual(data.hex(),r['bytes']);v=struct.unpack('<i',data)[0];self.assertEqual(v,r['relative']);self.assertEqual(hex(a+(v&~1 if r.get('indirect')else v)),r['target'])
   if r.get('indirect'):
    v,c=self.n['reachable_pointer'](int(r['target'],16));self.assertEqual(c,r['chain'])
    if v>>63:
     f=self.n['fixup'][0];raw=self.n['raw'];h=struct.unpack_from('<7I',raw,f);e=struct.unpack_from('<I',raw,f+h[2]+4*(v&0xffffff))[0];o=f+h[3]+(e>>9);self.assertEqual(raw[o:raw.index(b'\0',o)].decode(),r['symbol'])
    else:self.assertEqual(hex(self.n['base']+(v&((1<<36)-1))),r['pointee'])
  self.assertEqual([r['symbol']for r in self.p['relative_links']if 'symbol'in r],['_$ss23CustomStringConvertibleMp','_$ss23CustomStringConvertibleP11descriptionSSvgTq'])
 def test_registered_witness_is_actual_tail_delegate_to_formatter(self):
  link=self.p['relative_links'][3];self.assertEqual(link['address'],'0x100c3e238');self.assertEqual(link['target'],'0x1002dcc94');tail=[r for r in self.p['branches']if 0x1002dcc94<=int(r['call'],16)<0x1002dcca4];self.assertEqual([r['target']for r in tail],['0x1002dc9b8'])
 def test_semantic_enum_has_real_protocol_requirement(self):
  self.assertIn('public enum Suggestion: Equatable, Sendable, CustomStringConvertible',self.core);self.assertIn('OriginalSearchSuggestions.f_1002dc9b8(self)',body(self.core,'public var description: String'));self.assertEqual(self.core.count('public var description:'),1)
 def test_query_node_order_raw_text_empty_components_and_space_join(self):
  s=self.formatter;self.assertIn('return nodes.map { node in',s);self.assertIn('case let .text(text): return text',s);self.assertIn('}.joined(separator: " ")',s)
  for t in ['trim','split','filter {','Set(','normalize','lowercase','UUID','String(describing:']:self.assertNotIn(t,s)
 def test_exact_six_filter_prefixes_and_literal_colon(self):
  s=self.formatter
  for tag,name in enumerate(['app','type','title','date','device']):self.assertIn('case '+str(tag)+': prefix = "'+name+'"',s)
  self.assertIn('default: prefix = "pinboard"',s);self.assertIn('return prefix + ":" + f_1002ddc10(kind: kind, value: value, listName: listName)',s)
 def test_standalone_filter_and_query_share_caption_contract(self):
  self.assertIn('case let .filter(kind, value):\n            return f_1002ddc10(kind: kind, value: value, listName: listName)',self.formatter);self.assertEqual(self.formatter.count('f_1002ddc10(kind: kind, value: value, listName: listName)'),2)
 def test_only_list_and_date_are_resolved_nil_and_empty_distinguished(self):
  s=self.caption;self.assertIn('case 5: return listName(value) ?? value',s);self.assertIn('case 3: return OriginalSearchDateEncoding.f_1002d8e9c(value) ?? value',s);self.assertIn('default: return value',s)
  for t in ['isEmpty','displayName','pinboards','UUID','lowercase']:self.assertNotIn(t,s)
 def test_each_default_list_invocation_snapshots_current_callback(self):
  self.assertEqual(self.core.count('private static var listNameResolver: ((String) -> String?)?'),1);s=body(self.core,'public static func resolveListName(');self.assertIn('let resolver = listNameResolver\n        return resolver?(identifier)',s);self.assertIn('listNameResolver = resolver',body(self.core,'public static func setListNameResolver('));self.assertEqual(self.core.count('= { resolveListName($0) }) -> String'),2)
 def test_native_list_reader_factory_is_non_actor_and_queue_confined(self):
  source=(ROOT/'replica/Sources/PastoCore/ClipboardListPersistence.swift').read_text();s=body(source,'func searchListNameResolver()');self.assertIn('self.context.performAndWait {',s);self.assertIn('guard let list = self.tabList(identifier: identifier) else { return nil }',s);self.assertIn('String._unconditionallyBridgeFromObjectiveC(list.value(forKey: "name") as? NSString)',s)
  for t in ['UUID','pinboards','items','Task','DispatchQueue','setValue','insertNewObject','MainActor']:self.assertNotIn(t,s)
  tab=body(source,'func tabList(identifier:');self.assertIn('NSPredicate(format: "identifier == %@", identifier)',tab);self.assertIn('(try? context.fetch(request))?.first',tab);self.assertNotIn('@MainActor\nfinal class ClipboardListPersistence',source)
 def test_actual_startup_registers_same_store_native_name_callback(self):
  store=(ROOT/'replica/Sources/PastoCore/ClipboardStore.swift').read_text();persistence=(ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text();self.assertIn('persistence.makeSearchListNameResolver()',body(store,'public func makeSearchListNameResolver()'));self.assertIn('lists.searchListNameResolver()',body(persistence,'func makeSearchListNameResolver()'));ui=(ROOT/'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text();self.assertEqual(ui.count('OriginalSearchSuggestions.setListNameResolver(store.makeSearchListNameResolver())'),1);self.assertLess(ui.index('searchIndex = ReplicaSearchIndex(service: service, store: store)'),ui.index('OriginalSearchSuggestions.setListNameResolver('))
 def test_fourteen_neighbor_methods_eight_shared_sources_preserved(self):
  self.assertEqual(len(self.p['unchanged_methods']),14);self.assertEqual(len(self.p['shared_sources']),8)
  for r in self.p['unchanged_methods']:self.assertEqual(hashlib.sha256(body((ROOT/r['path']).read_text(),r['symbol']).encode()).hexdigest(),r['body_sha256'])
  for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),h)
 def test_exact_seven_hunks_five_sources_and247_inverse_idempotence(self):
  self.assertEqual(len(CHANGES),7);self.assertEqual(CHANGES,json.loads((self.ph/'production-changes.json').read_text()));expected={}
  for p,old,new,count in CHANGES:
   if p not in expected:expected[p]=(self.ph/'before'/p).read_text()
   self.assertEqual(expected[p].count(old),count);expected[p]=expected[p].replace(old,new)
  self.assertEqual(len(expected),5)
  for p,h in self.b['production'].items():
   self.assertEqual(hashlib.sha256(pre_suggestion_description_bytes(ROOT/p)).hexdigest(),h,p);old=(self.ph/'before'/p).read_bytes();self.assertEqual(pre_suggestion_description(old.decode()).encode()if p.endswith('.swift')else old,old,p)
   if p in expected:self.assertEqual((ROOT/p).read_text(),expected[p])
 def test_historical_adjustments_exactly_restore364_python_inputs(self):
  self.assertEqual(len(self.b['tests']),364);self.assertEqual(HISTORICAL_TEST_CHANGES,json.loads((self.ph/'test-scope-adjustments.json').read_text()));expected={}
  for p,old,new,count in HISTORICAL_TEST_CHANGES:
   if p not in expected:expected[p]=(self.ph/'before'/p).read_text()
   self.assertEqual(expected[p].count(old),count);expected[p]=expected[p].replace(old,new)
  for p,h in self.b['tests'].items():self.assertEqual(pre_text_edit_mode_history_bytes(ROOT/p).decode(),expected.get(p,(self.ph/'before'/p).read_text()),p);self.assertEqual(hashlib.sha256(pre_suggestion_description_history_bytes(ROOT/p)).hexdigest(),h,p)
 def test_source_bound_format_model_preserves_whitespace_case_empty_and_unicode(self):
  def caption(k,v,names,dates):return names.get(v,v)if k==5 else dates.get(v,v)if k==3 else v
  def fmt(nodes,names={},dates={}):return ' '.join(v if k is None else(['app','type','title','date','device'][k]if k<5 else'pinboard')+':'+caption(k,v,names,dates)for k,v in nodes)
  self.assertEqual(fmt([]),'');self.assertEqual(fmt([(None,''),(None,'x'),(None,'')]),' x ');self.assertEqual(fmt([(None,' A  中\n'),(1,'iMaGe')]),' A  中\n type:iMaGe');self.assertEqual(fmt([(5,'raw'),(5,'empty'),(5,'missing')],{'raw':'分组','empty':''}),'pinboard:分组 pinboard: pinboard:missing');self.assertEqual(fmt([(3,'invalid'),(3,'today')],{}, {'today':'今天'}),'date:invalid date:今天')
  for k in range(256):self.assertEqual(fmt([(k,'X')]),(['app','type','title','date','device'][k]if k<5 else'pinboard')+':X')
 def test_live_per_node_callback_read_survives_reentrant_replacement(self):
  trace=[];slot={}
  def replacement(identifier):trace.append(('new',identifier));return ''
  def first(identifier):trace.append(('old',identifier));slot['resolver']=replacement;return 'renamed'
  def resolve(identifier):callback=slot.get('resolver');return callback(identifier)if callback else None
  slot['resolver']=first;results=[resolve('same'),resolve('same')];self.assertEqual(results,['renamed','']);self.assertEqual(trace,[('old','same'),('new','same')]);slot['resolver']=None;self.assertIsNone(resolve('same'));self.assertIn('let resolver = listNameResolver',body(self.core,'public static func resolveListName('))
 def test_only_real_protocol_contract_added_query_branch_reuses_prior_record(self):
  self.assertEqual([r['function_id']for r in self.p['contracts']],['Paste:0x1002dcc94']);self.assertEqual([r['function_id']for r in self.p['additional_contracts']],['Paste:0x1002dc9b8','Paste:0x10007d740']);self.assertFalse(self.p['full_function_migration_verified']);self.assertFalse(self.p['runtime_executed']);self.assertIn('0x1000f733c',self.p['remaining'][0]);self.assertEqual(self.p['unchanged_production_files'],242)
if __name__=='__main__':unittest.main()
