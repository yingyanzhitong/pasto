"""Suggestion proposals use weak originating SearchBar and one coordinator pipeline; source/ARM only."""
from pathlib import Path
import hashlib,json,struct,sys,unittest,weakref
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from suggestion_proposal_scope_contract import CHANGES,pre_suggestion_proposal,pre_suggestion_proposal_bytes,pre_suggestion_proposal_history_bytes
from suggestion_task_scope_contract import pre_suggestion_task, pre_suggestion_task_bytes, pre_suggestion_task_history_bytes
from suggestion_index_source_scope_contract import pre_suggestion_index_source_bytes
from suggestion_list_lifecycle_scope_contract import pre_suggestion_list_lifecycle
class SuggestionProposalContracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ph=ROOT/'.local/p0-repair/phase-178';cls.p=json.loads((cls.ph/'suggestion-proposal-contract.json').read_text());cls.b=json.loads((cls.ph/'baseline.json').read_text());cls.editor=(ROOT/'replica/Sources/Pasto/UI/SearchEditor.swift').read_text();cls.bar=body((ROOT/'replica/Sources/Pasto/UI/OriginalPanelToolbar.swift').read_text(),'final class OriginalPanelSearchBar:');cls.helper=(ROOT/'replica/Sources/PastoCore/OriginalSearchSuggestions.swift').read_text();cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
 def word(self,a):return struct.unpack('<I',self.n['read'](a,4))[0]
 def order(self,s,tokens):
  positions=[s.index(t)for t in tokens];self.assertEqual(positions,sorted(positions))
 def test_thirteen_original_fragments_and_native_inputs_are_bound(self):
  self.assertEqual(len(self.p['original_fragments']),13)
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for k in ['binary','decoder','prior_candidate']:
   r=self.p[k];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
 def test_eight_complete_native_ranges_and125_direct_branches_are_fresh(self):
  self.assertEqual(len(self.p['machine_ranges']),8);self.assertEqual(len(self.p['branches']),125)
  for r in self.p['machine_ranges']:
   data=self.n['read'](int(r['address'],16),int(r['end'],16)-int(r['address'],16));self.assertEqual(data.hex(),r['bytes']);self.assertEqual(hashlib.sha256(data).hexdigest(),r['sha256'])
  for r in self.p['branches']:
   a=int(r['call'],16);w=self.word(a);self.assertEqual(hex(w),r['word']);self.assertEqual(w&0x7c000000,0x14000000);v=w&0x3ffffff;v=v-(1<<26)if v&(1<<25)else v;self.assertEqual(hex(a+4*v),r['target'])
 def test_eight_weak_init_load_and_ARC_imports_resolve_real_fixups(self):
  self.assertEqual(len(self.p['imports']),8)
  for r in self.p['imports']:
   v,c=self.n['reachable_pointer'](int(r['pointer'],16));self.assertEqual(c,r['chain']);self.assertTrue(v>>63);fo=self.n['fixup'][0];raw=self.n['raw'];h=struct.unpack_from('<7I',raw,fo);e=struct.unpack_from('<I',raw,fo+h[2]+4*(v&0xffffff))[0];off=fo+h[3]+(e>>9);self.assertEqual(raw[off:raw.index(b'\0',off)].decode(),r['symbol'])
 def test_original_candidate_captures_same_context_value_and_weak_owner(self):
  expected={0x1000412f8:0xaa1603e1,0x100041318:0xad408281,0x10004131c:0x3dc00282,0x100041320:0xad008402,0x100041324:0x3d800c00,0x100041328:0xa9046c1c,0x10004132c:0xf9002819,0x100041330:0x3901601a,0x100041334:0xf9003013}
  for a,w in expected.items():self.assertEqual(self.word(a),w)
  for a,v in [(0x1000413a0,0xde0),(0x1000415c4,0xdf8)]:self.assertEqual((self.word(a)>>10)&0xfff,v)
 def test_original_accept_merges_before_weak_load_then_same_coordinator_mode0(self):
  branches={r['call']:r['target']for r in self.p['branches']};self.assertEqual(branches['0x100041df4'],'0x10004160c');self.assertEqual(branches['0x10004163c'],'0x1002dcca4');self.assertEqual(branches['0x100041648'],'0x100bfcbb8');self.assertEqual(branches['0x10004167c'],'0x1002f7744');self.assertEqual(self.word(0x100041638),0x52800005);self.assertEqual(self.word(0x100041678),0x52800001);self.assertEqual(self.word(0x10004164c),0xb4000280);self.assertEqual(self.word(0x100041670),0xb4000214);self.assertEqual(self.word(0x1000416b0),0xd4200020)
 def test_original_dismiss_callback_is_distinct_weak_owner_and_nil_context(self):
  branches={r['call']:r['target']for r in self.p['branches']};self.assertEqual(branches['0x100041dfc'],'0x1000416b4');self.assertEqual(branches['0x1000416e4'],'0x1000403f4');self.assertEqual(self.word(0x1000416cc),0xb4000180);self.assertEqual(self.word(0x1000416d4),0x6f00e400);self.assertEqual(self.word(0x1000416d8),0xad0083e0);self.assertEqual(self.word(0x1000416dc),0x3d8003e0)
 def test_real_SearchBar_installs_weak_callbacks_before_initial_and_update_paths(self):
  s=body(self.bar,'func configure(button:');self.order(s,['var specification = specification','specification.onApplySuggestion = { [weak self] nodes in self?.applySearchQuery(nodes) }','specification.onDismissSuggestions = { [weak self] in self?.coordinator?.dismissSuggestions() }','if let field, let coordinator','specification.updateField(field, coordinator: coordinator)','ReplicaSearchEditor.Coordinator(specification)','specification.makeField(coordinator: coordinator)']);self.assertNotIn('toolbarOwner',s)
 def test_real_rows_capture_context_callbacks_without_extra_live_editor_gate(self):
  s=body(self.editor,'func performSuggestionRequest(');self.assertIn('node -> (OriginalSearchSuggestions.Suggestion, ReplicaSearchFilterChip)?',s);self.assertIn('return (.filter(tag, value), chip)',s);self.order(s,['let applySuggestion = self.parent.onApplySuggestion','let dismissSuggestions = self.parent.onDismissSuggestions','menu.show(rows:','Self.accept(entries[index].0, context: context, apply: applySuggestion)','onEscape: dismissSuggestions']);callback=body(s,'onAccept:');self.assertIn('guard entries.indices.contains(index) else { return }',callback)
  for t in ['weak self','weak field','weak editor','self.accept','field:','editor:']:self.assertNotIn(t,callback)
 def test_acceptance_uses_full_Suggestion_contract_and_only_merges_then_proposes(self):
  s=body(self.editor,'private static func accept(');self.order(s,['OriginalSearchSuggestions.f_1002dcca4(suggestion','index: context.nodeIndex, addMode: 0, nodes: context.nodes','apply(nodes)'])
  for t in ['guard case','normalize','history.','currentNodes','display(','parent.','dismissSuggestions','UUID']:self.assertNotIn(t,s)
  helper=body(self.helper,'public static func f_1002dcca4(');self.assertIn('case let .query(query):\n            return query',helper);self.assertIn('guard !nodes.contains(filter)',helper)
 def test_same_mode0_pipeline_writes_internal_query_before_builder_history_and_display(self):
  s=body(self.bar,'func applySearchQuery(');self.assertIn('coordinator.applyProgrammaticQuery(nodes, field: field, editor: editor)',s);self.assertIn('suggestionsEnabled: false',body(self.editor,'func applyProgrammaticQuery('));s=body(self.editor,'private func replaceQuery(');self.order(s,['let normalized','guard normalized != currentNodes else { return }','currentNodes = normalized','attributedString(normalized','if !restoringHistory','history.f_1002f5e18(','display(rendered','publishCurrentQuery()','dismissSuggestions()'])
 def test_native_restore_flag_skips_only_history_then_still_displays_and_publishes(self):
  self.assertEqual(self.word(0x1002f7844),0x3941c268);self.assertEqual(self.word(0x1002f7848),0x370001c8);self.assertEqual(self.word(0x1002f7c40),0x3901c288);s=body(self.editor,'private func replaceQuery(');guard=body(s,'if !restoringHistory');self.assertIn('history.f_1002f5e18(.init(nodes: normalized, selection: selection), immediate: true)',guard)
  for t in ['currentNodes =','display(','publishCurrentQuery','dismissSuggestions']:self.assertNotIn(t,guard)
  r=body(self.editor,'private func restore(');self.order(r,['restoringHistory = true','defer { restoringHistory = false }','display(','parent.onInputChange'])
 def test_dismissal_cancels_task_and_closes_menu_without_query_or_history_effects(self):
  s=body(self.editor,'func dismissSuggestions()');self.order(s,['suggestionTask?.cancel()','suggestionTask = nil','dismissSuggestionMenu()']);menu_only=body(self.editor,'private func dismissSuggestionMenu()');self.order(menu_only,['suggestionMenu?.dismiss()','suggestionMenu = nil'])
  for t in ['currentNodes','history.','publishCurrentQuery','onInputChange']:self.assertNotIn(t,s)
  m=pre_suggestion_list_lifecycle((ROOT/'replica/Sources/Pasto/UI/ReplicaSearchSuggestionsMenu.swift').read_text());self.assertIn('accept?(index)',body(m,'private func acceptRow('));self.order(body(m,'private func cancel()'),['let callback = escape','dismiss()','callback?()'])
 def test_fourteen_neighbor_methods_and_nine_shared_sources_are_preserved(self):
  self.assertEqual(len(self.p['unchanged_methods']),14)
  for r in self.p['unchanged_methods']:
   s=pre_suggestion_task((ROOT/r['path']).read_text());s=body(s,r['scope'])if 'scope'in r else s;self.assertEqual(hashlib.sha256(body(s,r['symbol']).encode()).hexdigest(),r['body_sha256'])
  self.assertEqual(len(self.p['shared_sources']),9)
  for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_suggestion_index_source_bytes(ROOT/p)).hexdigest(),h)
 def test_six_exact_hunks_restore247_files_and_do_not_touch_old_snapshots(self):
  self.assertEqual(len(CHANGES),6);changed=[]
  for p,h in self.b['production'].items():
   old=(self.ph/'before'/p).read_bytes()
   if hashlib.sha256(pre_suggestion_task_bytes(ROOT/p)).hexdigest()!=h:changed.append(p)
   self.assertEqual(hashlib.sha256(pre_suggestion_proposal_bytes(ROOT/p)).hexdigest(),h,p);self.assertEqual(pre_suggestion_proposal(old.decode()).encode()if p.endswith('.swift')else old,old,p)
  self.assertEqual(sorted(changed),sorted(self.p['current_sources']));self.assertEqual(len(changed),2)
 def test_eight_historical_test_edits_replay_and_restore348_prior_Python_files(self):
  adjust=json.loads((self.ph/'test-scope-adjustments.json').read_text());self.assertEqual(adjust,self.p['historical_test_changes']);self.assertEqual(len(adjust),8);expected={}
  for p,old,new,count in adjust:
   if p not in expected:expected[p]=(self.ph/'before'/p).read_text()
   self.assertEqual(expected[p].count(old),count);expected[p]=expected[p].replace(old,new)
  self.assertEqual(len(expected),3)
  for p,h in self.b['tests'].items():self.assertEqual(pre_suggestion_task_history_bytes(ROOT/p).decode(),expected.get(p,(self.ph/'before'/p).read_text()),p);self.assertEqual(hashlib.sha256(pre_suggestion_proposal_history_bytes(ROOT/p)).hexdigest(),h,p)
 def test_protocol_captured_context_filter_and_full_query_merges_use_original_inputs(self):
  captured=[('text','old'),('filter',5,'opaque')];global_now=[('text','new')];filter_node=('filter',5,'Raw-ID');proposal=list(captured);proposal[0]=filter_node;self.assertEqual(proposal,[filter_node,('filter',5,'opaque')]);self.assertNotEqual(proposal,[filter_node]);self.assertNotEqual(proposal,global_now);query=[('text','chosen'),filter_node];self.assertEqual(query,[('text','chosen'),('filter',5,'Raw-ID')]);self.assertNotEqual(query,captured)
 def test_protocol_weak_owner_does_not_redirect_and_merge_precedes_nil_skip(self):
  class Owner:
   def __init__(self):self.applied=[]
   def apply(self,q):self.applied.append(q)
  origin=Owner();other=Owner();ref=weakref.ref(origin);events=[]
  def apply(q):
   actual=ref()
   if actual is not None:actual.apply(q)
  def accept():events.append('merge');q=[('filter',5,'raw')];apply(q)
  accept();self.assertEqual(len(origin.applied),1);self.assertEqual(other.applied,[]);del origin;self.assertIsNone(ref());accept();self.assertEqual(events,['merge','merge']);self.assertEqual(other.applied,[])
 def test_protocol_restore_reentry_keeps_display_publication_but_no_second_history_record(self):
  def replace(old,new,restoring):
   if old==new:return []
   effects=['write','builder']
   if not restoring:effects.append('history')
   return effects+['display','publish','suggestions']
  before=[('text','before')];after=[('filter',5,'group')];self.assertEqual(replace(before,after,True),['write','builder','display','publish','suggestions']);self.assertEqual(replace(before,after,False),['write','builder','history','display','publish','suggestions']);self.assertEqual(replace(after,after,True),[])
 def test_full_producer_unknown_setter_and_runtime_claims_stay_open(self):
  self.assertEqual(len(self.p['contracts']),2);self.assertEqual(self.p['additional_contracts'][0]['function_id'],'Paste:0x1002f7744');self.assertFalse(self.p['full_function_migration_verified']);self.assertFalse(self.p['runtime_executed']);self.assertIn('0f733c',self.p['remaining'][0]);self.assertIn('041190',self.p['remaining'][1]);self.assertIn('query-suggestion sources',self.p['adaptations'][1])
if __name__=='__main__':unittest.main()
