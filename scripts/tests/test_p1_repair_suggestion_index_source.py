"""Actual nonempty suggestion source delivery; source/ARM and protocol fixtures only."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from suggestion_index_source_scope_contract import CHANGES,pre_suggestion_index_source,pre_suggestion_index_source_bytes,pre_suggestion_index_source_history_bytes
from suggestion_anchor_owner_scope_contract import pre_suggestion_anchor_owner, pre_suggestion_anchor_owner_bytes, pre_suggestion_anchor_owner_history_bytes
class SuggestionIndexSourceContracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ph=ROOT/'.local/p0-repair/phase-180';cls.p=json.loads((cls.ph/'suggestion-index-source-contract.json').read_text());cls.b=json.loads((cls.ph/'baseline.json').read_text());cls.editor=(ROOT/'replica/Sources/Pasto/UI/SearchEditor.swift').read_text();cls.index=(ROOT/'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text();cls.state=(ROOT/'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text();cls.panel=(ROOT/'replica/Sources/Pasto/UI/PanelViews.swift').read_text();cls.core=(ROOT/'replica/Sources/PastoCore/OriginalSearchSuggestions.swift').read_text();cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
 def word(self,a):return struct.unpack('<I',self.n['read'](a,4))[0]
 def order(self,s,tokens):
  p=[s.index(t)for t in tokens];self.assertEqual(p,sorted(p))
 def test_thirteen_native_fragments_and_reused_actual_service_binding_are_fresh(self):
  self.assertEqual(len(self.p['original_fragments']),13)
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for key in ['binary','decoder','prior_service']:
   r=self.p[key];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
  old=json.loads((ROOT/self.p['prior_service']['path']).read_text())
  for r in old['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
 def test_seven_complete_machine_ranges_and49_direct_branches_are_bound(self):
  self.assertEqual(len(self.p['machine_ranges']),7);self.assertEqual(len(self.p['branches']),49)
  for r in self.p['machine_ranges']:
   data=self.n['read'](int(r['address'],16),int(r['end'],16)-int(r['address'],16));self.assertEqual(data.hex(),r['bytes']);self.assertEqual(hashlib.sha256(data).hexdigest(),r['sha256'])
  for r in self.p['branches']:
   a=int(r['call'],16);w=self.word(a);self.assertEqual(hex(w),r['word']);self.assertEqual(w&0x7c000000,0x14000000);v=w&0x3ffffff;v=v-(1<<26)if v&(1<<25)else v;self.assertEqual(hex(a+4*v),r['target'])
 def test_native_caller_passes_same_lazy_receiver_and_captured_node_payload_to_generator(self):
  branches={r['call']:r['target']for r in self.p['branches']};self.assertEqual(branches['0x10004112c'],'0x1000da768');self.assertEqual(branches['0x100041148'],'0x1002df190');self.assertEqual(self.word(0x100041130),0xf9401ed4)
  for a,w in [(0x100041134,0xaa1803e0),(0x100041138,0xaa1703e1),(0x10004113c,0xaa1503e2),(0x100041140,0xaa1903e3),(0x100041144,0xaa1303e4)]:self.assertEqual(self.word(a),w)
 def test_four_group_calls_reread_optional_source_and_correct_witness_slot(self):
  self.assertEqual([r['witness_slot']for r in self.p['source_gates']],[8,16,24,32])
  for r in self.p['source_gates']:
   self.assertEqual(self.word(int(r['optional_value'],16)),0xf94022e8);a=int(r['gate'],16);w=self.word(a);self.assertEqual(w&0x7f00001f,0x34000008);v=(w>>5)&0x7ffff;v=v-(1<<19)if v&(1<<18)else v;self.assertEqual(hex(a+4*v),r['nil_target']);w=self.word(int(r['witness_load'],16));self.assertEqual(w&0xffc003ff,0xf9400308);self.assertEqual(((w>>10)&0xfff)*8,r['witness_slot']);self.assertEqual(self.word(int(r['invoke'],16)),0xd63f0100)
 def test_required_loader_and_sole_real_constructor_deliver_actual_state(self):
  line=next(x for x in self.editor.splitlines()if 'var onLoadSuggestions:'in x);self.assertNotIn('=',line);self.assertIn('onLoadSuggestions: { state.searchSuggestions(for: $0) }',body(self.panel,'private var searchField:'))
  count=sum((ROOT/p).read_text().count('ReplicaSearchEditor(store:')for p in self.b['production']if p.endswith('.swift'));self.assertEqual(count,1);s=body(self.editor,'func performSuggestionRequest(');self.order(s,['let candidates = parent.onLoadSuggestions(context)','guard !Task.isCancelled','let entries =']);self.assertNotIn('OriginalSearchSuggestions.Provider(',self.editor);self.assertNotIn('ReplicaSearchSuggestionSource.applications',self.editor)
 def test_actual_state_forwards_captured_node_index_and_whole_query_to_same_index(self):
  s=body(self.state,'func searchSuggestions(for context:');self.assertIn('searchIndex.suggestions(contextNode: context.nodes[context.nodeIndex], currentNodes: context.nodes)',s)
  for t in ['queryNodes','UUID','normalize','store.','guard']:self.assertNotIn(t,s)
  init=body(body(self.state,'final class ReplicaUIState: ObservableObject'),'init(store: ClipboardStore)');self.assertIn('searchIndex.setSuggestionDataSource(store.makeSearchSuggestionProvider())',init);self.assertIn('searchIndex.availableFilters()',body(self.state,'func availableSearchFilters()'))
 def test_index_reads_each_installed_optional_source_live_instead_of_cached_provider(self):
  s=body(self.index,'func suggestions(contextNode:')
  for name in ['app','type','device','pinboard']:self.assertIn('try self.suggestionDataSource?.'+name+'($0) ?? []',s)
  self.assertEqual(s.count('self.suggestionDataSource?'),4);self.assertIn('contextNode: contextNode, currentNodes: currentNodes, provider: provider',s)
  for t in ['guard let','let source =','let installed =','store.','f_10030f3e0','catch','Set(','sorted(']:self.assertNotIn(t,s)
 def test_type_source_has_no_unconditional_static_default_on_missing_or_replaced_source(self):
  s=body(self.index,'func suggestions(contextNode:');self.assertIn('type: { try self.suggestionDataSource?.type($0) ?? [] }',s);self.assertIn('suggestionDataSource = provider',body(self.index,'func setSuggestionDataSource('));self.assertIn('provider: { suggestionDataSource }',body(self.index,'func availableFilters()'))
 def test_existing_core_per_group_errors_order_cap_exclusion_and_dates_are_reused(self):
  s=body(self.core,'public static func f_1002df190(');self.order(s,['(0, provider.app)','(1, provider.type)','(4, provider.device)','(5, { try provider.pinboard','let candidates = try source(query)','for dateFilter in dateFilters ??']);self.assertIn('.prefix(30)',s);self.assertIn('if !applied.contains(node)',s);self.assertIn('continue',body(s,'catch'));self.assertNotIn('provider.app',s[s.index('for dateFilter'):])
 def test_owner_cancel_and_accept_delivery_tail_is_identical_to_prior_repair(self):
  s=body(pre_suggestion_anchor_owner(self.editor),'func performSuggestionRequest(');tail=s[s.index('            guard !Task.isCancelled'):];self.assertEqual(hashlib.sha256(tail.encode()).hexdigest(),self.p['request_delivery_tail_sha256']);self.assertIn('withExtendedLifetime(owner)',body(self.editor,'private func updateSuggestions('));self.assertIn('apply(nodes)',body(self.editor,'private static func accept('))
 def test_eleven_neighbor_methods_and_nine_shared_sources_are_unchanged(self):
  self.assertEqual(len(self.p['unchanged_methods']),11)
  for r in self.p['unchanged_methods']:self.assertEqual(hashlib.sha256(body((ROOT/r['path']).read_text(),r['symbol']).encode()).hexdigest(),r['body_sha256'])
  self.assertEqual(len(self.p['shared_sources']),9)
  for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_suggestion_anchor_owner_bytes(ROOT/p)).hexdigest(),h)
 def test_five_exact_hunks_reverse247_current_files_and_preserve_prior_snapshots(self):
  self.assertEqual(len(CHANGES),5);changed=[]
  for p,h in self.b['production'].items():
   if hashlib.sha256(pre_suggestion_anchor_owner_bytes(ROOT/p)).hexdigest()!=h:changed.append(p)
   self.assertEqual(hashlib.sha256(pre_suggestion_index_source_bytes(ROOT/p)).hexdigest(),h,p);old=(self.ph/'before'/p).read_bytes();self.assertEqual(pre_suggestion_index_source(old.decode()).encode()if p.endswith('.swift')else old,old,p)
  self.assertEqual(sorted(changed),sorted(self.p['current_sources']));self.assertEqual(len(changed),4)
 def test_fifteen_test_adjustments_replay_and_restore352_historical_Python_inputs(self):
  a=json.loads((self.ph/'test-scope-adjustments.json').read_text());self.assertEqual(a,self.p['historical_test_changes']);self.assertEqual(len(a),15);expected={}
  for p,old,new,count in a:
   if p not in expected:expected[p]=(self.ph/'before'/p).read_text()
   self.assertEqual(expected[p].count(old),count);expected[p]=expected[p].replace(old,new)
  self.assertEqual(len(expected),7)
  for p,h in self.b['tests'].items():self.assertEqual(pre_suggestion_anchor_owner_history_bytes(ROOT/p).decode(),expected.get(p,(self.ph/'before'/p).read_text()),p);self.assertEqual(hashlib.sha256(pre_suggestion_index_source_history_bytes(ROOT/p)).hexdigest(),h,p)
 def collect(self,state,query,dates):
  result=[]
  for tag,key in [(0,'app'),(1,'type'),(4,'device'),(5,'pinboard')]:
   source=state['provider'];callback=None if source is None else source.get(key)
   try:values=[]if callback is None else callback(query)
   except ValueError:continue
   result.extend((tag,value)for value in values[:30])
  return result+[(3,value)for value in dates]
 def test_protocol_nil_provider_keeps_date_candidates_and_does_not_add_default_types(self):
  self.assertEqual(self.collect(dict(provider=None),'Image',['today']),[(3,'today')]);self.assertNotIn((1,'Image'),self.collect(dict(provider=None),'Image',[]))
 def test_protocol_reentrant_source_replacement_is_seen_by_later_groups(self):
  state={};calls=[]
  def app(q):
   calls.append(('old-app',q));state['provider']={'type':lambda q:['Image'],'device':lambda q:['replacement'],'pinboard':lambda q:['raw-id']};return ['first']
  state['provider']={'app':app,'type':lambda q:['stale']};self.assertEqual(self.collect(state,'original',[]),[(0,'first'),(1,'Image'),(4,'replacement'),(5,'raw-id')]);self.assertEqual(calls,[('old-app','original')])
 def test_protocol_source_error_is_local_removal_is_live_and_later_date_still_exists(self):
  state={}
  def failing(q):raise ValueError('source error')
  def device(q):state['provider']=None;return ['mac']
  state['provider']={'app':failing,'type':lambda q:['Text'],'device':device,'pinboard':lambda q:['stale']};self.assertEqual(self.collect(state,'text',['week']),[(1,'Text'),(4,'mac'),(3,'week')])
 def test_finite_bridge_does_not_claim_private_lazy_class_or_full_menu_lifecycle(self):
  self.assertEqual([r['function_id']for r in self.p['contracts']],['Paste:0x1000410ec','Paste:0x1002dfc64']);self.assertFalse(self.p['runtime_executed']);self.assertFalse(self.p['full_function_migration_verified']);self.assertIn('0f733c',self.p['remaining'][0]);self.assertIn('anchor',self.p['remaining'][1]);self.assertIn('instead of cloning',self.p['adaptations'][0])
if __name__=='__main__':unittest.main()
