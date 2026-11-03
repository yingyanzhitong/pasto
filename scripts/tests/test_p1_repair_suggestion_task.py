"""Actual suggestion Task owner/cancellation contracts; source, ARM and protocol models only."""
from pathlib import Path
import hashlib,json,struct,sys,unittest,weakref
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from suggestion_task_scope_contract import CHANGES,pre_suggestion_task,pre_suggestion_task_bytes,pre_suggestion_task_history_bytes
from suggestion_index_source_scope_contract import pre_suggestion_index_source_bytes, pre_suggestion_index_source_history_bytes
class SuggestionTaskContracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ph=ROOT/'.local/p0-repair/phase-179';cls.p=json.loads((cls.ph/'suggestion-task-contract.json').read_text());cls.b=json.loads((cls.ph/'baseline.json').read_text());cls.editor=(ROOT/'replica/Sources/Pasto/UI/SearchEditor.swift').read_text();cls.bar=body((ROOT/'replica/Sources/Pasto/UI/OriginalPanelToolbar.swift').read_text(),'final class OriginalPanelSearchBar:');cls.update=body(cls.editor,'private func updateSuggestions(');cls.load=body(cls.editor,'func performSuggestionRequest(');cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
 def word(self,a):return struct.unpack('<I',self.n['read'](a,4))[0]
 def order(self,s,tokens):
  p=[s.index(t)for t in tokens];self.assertEqual(p,sorted(p))
 def test_fourteen_original_fragments_and_binary_decoder_candidate_are_fresh(self):
  self.assertEqual(len(self.p['original_fragments']),14)
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for k in ['binary','decoder','prior_candidate']:
   r=self.p[k];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
 def test_ten_full_machine_ranges_and118_direct_branches_are_bound(self):
  self.assertEqual(len(self.p['machine_ranges']),10);self.assertEqual(len(self.p['branches']),118)
  for r in self.p['machine_ranges']:
   data=self.n['read'](int(r['address'],16),int(r['end'],16)-int(r['address'],16));self.assertEqual(data.hex(),r['bytes']);self.assertEqual(hashlib.sha256(data).hexdigest(),r['sha256'])
  for r in self.p['branches']:
   a=int(r['call'],16);w=self.word(a);self.assertEqual(hex(w),r['word']);self.assertEqual(w&0x7c000000,0x14000000);v=w&0x3ffffff;v=v-(1<<26)if v&(1<<25)else v;self.assertEqual(hex(a+4*v),r['target'])
 def test_eight_actual_weak_ARC_task_imports_use_reachable_dyld_chains(self):
  self.assertEqual(len(self.p['imports']),8)
  for r in self.p['imports']:
   v,c=self.n['reachable_pointer'](int(r['pointer'],16));self.assertEqual(c,r['chain']);self.assertTrue(v>>63);fo=self.n['fixup'][0];raw=self.n['raw'];h=struct.unpack_from('<7I',raw,fo);e=struct.unpack_from('<I',raw,fo+h[2]+4*(v&0xffffff))[0];off=fo+h[3]+(e>>9);self.assertEqual(raw[off:raw.index(b'\0',off)].decode(),r['symbol'])
 def test_real_async_descriptor_and_post_child_owner_release_are_bound(self):
  r=self.p['async_descriptor'];data=self.n['read'](int(r['address'],16),8);self.assertEqual(data.hex(),r['bytes']);self.assertEqual(hex(int(r['address'],16)+struct.unpack_from('<i',data)[0]),'0x100041cc8');self.assertEqual(self.word(0x100040ee4),0xf9001ec0);self.assertEqual(self.word(0x100040ee8),0xb4000200);self.assertEqual(self.word(0x100040f60),0xa9438274);self.assertEqual(self.word(0x100040f6c),0xaa1403e0)
  branches={r['call']:r['target']for r in self.p['branches']};self.assertEqual(branches['0x100040f68'],'0x100bfcaa4');self.assertEqual(branches['0x100040f70'],'0x100bfbf64')
 def test_native_cancel_check_follows_generation_and_empty_joins_same_menu_branch(self):
  self.assertEqual(self.word(0x1000411cc),0x37001080);self.assertEqual(self.word(0x1000411d4),0xb4001055);self.assertEqual(self.word(0x1000413ec),0xf9425115);self.assertEqual(self.word(0x100041440),0xf8356a7f)
  cleanup=[r for r in self.p['branches']if 0x1000413dc<=int(r['call'],16)<0x100041470];self.assertNotIn('0x100bf8490',[r['target']for r in cleanup]);self.assertNotEqual((self.word(0x10004045c)>>10)&0xfff,(self.word(0x1000413ec)>>10)&0xfff)
 def test_actual_bar_is_weakly_installed_on_both_configure_paths_before_input_work(self):
  self.assertIn('weak var suggestionOwner: OriginalPanelSearchBar?',self.editor);s=body(self.bar,'func configure(button:');self.assertEqual(s.count('coordinator.suggestionOwner = self'),2);a=s.index('if let field, let coordinator');b=s.index('} else {',a);self.order(s[a:b],['coordinator.suggestionOwner = self','specification.updateField']);self.order(s[b:],['ReplicaSearchEditor.Coordinator(specification)','coordinator.suggestionOwner = self','specification.makeField'])
 def test_task_weak_loads_only_actual_owner_then_extends_lifetime_through_request(self):
  self.order(self.update,['suggestionTask?.cancel()','suggestionTask = nil','OriginalSearchInputContext.f_1002f78f8','Task { @MainActor [weak owner = suggestionOwner]','guard let owner else { return }','defer { withExtendedLifetime(owner) {} }','owner.performSuggestionRequest(context)']);task=body(self.update,'suggestionTask = Task')
  for t in ['weak self','weak field','weak editor','Task.isCancelled','toolbarOwner','Task.yield','sleep','DispatchQueue']:self.assertNotIn(t,task)
 def test_native_owner_delivers_context_through_its_installed_pair_without_weak_field_gates(self):
  s=body(self.bar,'func performSuggestionRequest(');self.order(s,['let (field, coordinator) = inputPair()','coordinator.performSuggestionRequest(context, field: field)']);self.assertNotIn('f_100041f9c()',s);self.assertNotIn('guard',s);self.assertNotIn('Task.isCancelled',s)
 def test_provider_runs_before_cancel_and_raw_empty_check_then_reuses_row_callbacks(self):
  self.order(self.load,['parent.onLoadSuggestions(context)','guard !Task.isCancelled, !candidates.isEmpty','let entries = candidates.compactMap','Self.accept(entries[index].0, context: context, apply: applySuggestion)']);self.assertEqual(self.load.count('parent.onLoadSuggestions(context)'),1);guard=body(self.load,'guard !Task.isCancelled, !candidates.isEmpty else');self.assertIn('dismissSuggestionMenu()',guard);self.assertNotIn('dismissSuggestions()',guard);self.assertNotIn('suggestionTask',guard)
 def test_menu_only_cleanup_does_not_cancel_or_clear_newer_task(self):
  s=body(self.editor,'private func dismissSuggestionMenu()');self.order(s,['suggestionMenu?.dismiss()','suggestionMenu = nil'])
  for t in ['suggestionTask','cancel()','currentNodes','history','publish']:self.assertNotIn(t,s)
  normal=body(self.editor,'func dismissSuggestions()');self.order(normal,['suggestionTask?.cancel()','suggestionTask = nil','dismissSuggestionMenu()'])
 def test_fourteen_neighbor_methods_and_nine_shared_sources_keep_prior_repairs(self):
  self.assertEqual(len(self.p['unchanged_methods']),14)
  for r in self.p['unchanged_methods']:
   s=(ROOT/r['path']).read_text();s=body(s,r['scope'])if 'scope'in r else s;self.assertEqual(hashlib.sha256(body(s,r['symbol']).encode()).hexdigest(),r['body_sha256'])
  self.assertEqual(len(self.p['shared_sources']),9)
  for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_suggestion_index_source_bytes(ROOT/p)).hexdigest(),h)
 def test_five_exact_hunks_reverse247_sources_and_preserve_old_snapshots(self):
  self.assertEqual(len(CHANGES),5);changed=[]
  for p,h in self.b['production'].items():
   if hashlib.sha256(pre_suggestion_index_source_bytes(ROOT/p)).hexdigest()!=h:changed.append(p)
   self.assertEqual(hashlib.sha256(pre_suggestion_task_bytes(ROOT/p)).hexdigest(),h,p);old=(self.ph/'before'/p).read_bytes();self.assertEqual(pre_suggestion_task(old.decode()).encode()if p.endswith('.swift')else old,old,p)
  self.assertEqual(sorted(changed),sorted(self.p['current_sources']));self.assertEqual(len(changed),2)
 def test_eight_test_adjustments_replay_and_restore350_old_Python_files(self):
  adjust=json.loads((self.ph/'test-scope-adjustments.json').read_text());self.assertEqual(adjust,self.p['historical_test_changes']);self.assertEqual(len(adjust),8);expected={}
  for p,old,new,count in adjust:
   if p not in expected:expected[p]=(self.ph/'before'/p).read_text()
   self.assertEqual(expected[p].count(old),count);expected[p]=expected[p].replace(old,new)
  self.assertEqual(len(expected),2)
  for p,h in self.b['tests'].items():self.assertEqual(pre_suggestion_index_source_history_bytes(ROOT/p).decode(),expected.get(p,(self.ph/'before'/p).read_text()),p);self.assertEqual(hashlib.sha256(pre_suggestion_task_history_bytes(ROOT/p)).hexdigest(),h,p)
 def test_protocol_actual_owner_survives_reentrant_external_release_until_child_finishes(self):
  class Owner:pass
  external=[Owner()];ref=weakref.ref(external[0]);events=[]
  def task():
   owner=ref()
   if owner is None:return
   external.clear();events.append(('provider',ref()is owner));events.append(('publish',ref()is owner))
  task();self.assertEqual(events,[('provider',True),('publish',True)]);self.assertIsNone(ref());task();self.assertEqual(len(events),2)
 def test_protocol_cancelled_request_generates_then_closes_menu_without_touching_new_task(self):
  state=dict(task='newer',menu='visible');events=[]
  def request(cancelled,candidates):
   events.append('provider')
   if cancelled or not candidates:state['menu']=None;events.append('close-menu');return
   events.append('show-menu')
  request(True,['candidate']);self.assertEqual(events,['provider','close-menu']);self.assertEqual(state['task'],'newer');self.assertIsNone(state['menu']);events.clear();request(False,[]);self.assertEqual(events,['provider','close-menu']);self.assertEqual(state['task'],'newer')
 def test_context_nodes_and_index_stay_captured_not_replaced_by_new_global_query(self):
  context=dict(nodes=[('text','original'),('filter',5,'raw')],index=0);global_query=[('text','new')];delivery=(context['nodes'][context['index']],context['nodes']);self.assertEqual(delivery[0],('text','original'));self.assertNotEqual(delivery[1],global_query);self.assertIn('owner.performSuggestionRequest(context)',self.update);self.assertIn('context.nodes[context.nodeIndex]',body((ROOT/'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text(),'func searchSuggestions(for context:'))
 def test_finite_task_contract_does_not_close_full_provider_anchor_or_unknown_setter(self):
  self.assertEqual([x['function_id']for x in self.p['contracts']],['Paste:0x100040ec4','Paste:0x100041190']);self.assertFalse(self.p['runtime_executed']);self.assertFalse(self.p['full_function_migration_verified']);self.assertIn('0f733c',self.p['remaining'][0]);self.assertIn('provider',self.p['remaining'][1]);self.assertIn('anchor',self.p['remaining'][1]);self.assertIn('No artificial',self.p['adaptations'][0])
if __name__=='__main__':unittest.main()
