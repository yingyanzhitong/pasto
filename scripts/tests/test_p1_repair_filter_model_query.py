"""Filter-query ownership/proposal source and ARM contracts; never executes Swift/UI."""
from pathlib import Path
import hashlib,json,struct,sys,unittest,weakref
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from filter_model_query_scope_contract import CHANGES,pre_filter_model_query,pre_filter_model_query_bytes,pre_filter_model_query_history_bytes

from suggestion_proposal_scope_contract import pre_suggestion_proposal, pre_suggestion_proposal_bytes, pre_suggestion_proposal_history_bytes

from suggestion_filter_title_scope_contract import pre_suggestion_filter_title_bytes
class FilterModelQueryContracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ph=ROOT/'.local/p0-repair/phase-177';cls.p=json.loads((cls.ph/'filter-model-query-contract.json').read_text());cls.b=json.loads((cls.ph/'baseline.json').read_text());cls.browser=(ROOT/'replica/Sources/Pasto/UI/FilterBrowser.swift').read_text();cls.model=body(cls.browser,'private final class ReplicaFilterBrowserModel:');cls.opening=body(cls.browser,'func showFilterBrowser(');cls.bar=body((ROOT/'replica/Sources/Pasto/UI/OriginalPanelToolbar.swift').read_text(),'final class OriginalPanelSearchBar:');cls.editor=(ROOT/'replica/Sources/Pasto/UI/SearchEditor.swift').read_text();cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
 def word(self,a):return struct.unpack('<I',self.n['read'](a,4))[0]
 def order(self,s,tokens):
  actual=[s.index(x)for x in tokens];self.assertEqual(actual,sorted(actual))
 def test_ten_original_fragments_binary_decoder_and_frozen_gap_are_fresh(self):
  self.assertEqual(len(self.p['original_fragments']),10)
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for k in ['binary','decoder','prior_gap']:
   r=self.p[k];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
 def test_five_complete_machine_ranges_and_all160_direct_branches_are_bound(self):
  self.assertEqual(len(self.p['machine_ranges']),5);self.assertEqual(len(self.p['branches']),160)
  for r in self.p['machine_ranges']:
   data=self.n['read'](int(r['address'],16),int(r['end'],16)-int(r['address'],16));self.assertEqual(data.hex(),r['bytes']);self.assertEqual(hashlib.sha256(data).hexdigest(),r['sha256'])
  for r in self.p['branches']:
   a=int(r['call'],16);w=self.word(a);self.assertEqual(hex(w),r['word']);self.assertEqual(w&0x7c000000,0x14000000);v=w&0x3ffffff;v=v-(1<<26)if v&(1<<25)else v;self.assertEqual(hex(a+4*v),r['target'])
 def test_weak_capture_load_ARC_imports_resolve_real_dyld_ordinal(self):
  self.assertEqual(len(self.p['imports']),5)
  for r in self.p['imports']:
   v,c=self.n['reachable_pointer'](int(r['pointer'],16));self.assertEqual(c,r['chain']);self.assertTrue(v>>63);fo=self.n['fixup'][0];raw=self.n['raw'];h=struct.unpack_from('<7I',raw,fo);e=struct.unpack_from('<I',raw,fo+h[2]+4*(v&0xffffff))[0];off=fo+h[3]+(e>>9);self.assertEqual(raw[off:raw.index(b'\0',off)].decode(),r['symbol'])
 def test_native_opening_reads_coordinator_internal_query_before_flag_and_weak_capture(self):
  expected={0x10003f0c0:0x910042c0,0x10003f0d4:0xf9400ad6,0x10003f104:0xd3534c19,0x10003f120:0x91004000,0x10003f128:0xaa1403e1,0x10003f170:0xaa1603e0,0x10003f174:0xaa1903e1,0x10003f178:0xaa1803e3}
  for a,w in expected.items():self.assertEqual(self.word(a),w)
  w=self.word(0x10003f16c);self.assertEqual((w>>10)&0xfff,0xe08);self.assertEqual(w&31,2)
 def test_native_model_sets_Published_then_rereads_before_callback(self):
  branches={r['call']:r['target']for r in self.p['branches']};self.assertEqual(branches['0x100007274'],'0x100bf558c');self.assertEqual(branches['0x1000072c0'],'0x100bf5580');self.assertEqual(self.word(0x100007284),0xa9405116);self.assertEqual(self.word(0x1000072dc),0xd63f02c0)
 def test_native_weak_owner_nil_returns_coordinator_nil_traps_mode_is_zero(self):
  self.assertEqual(self.word(0x10004187c),0xb4000240);self.assertEqual(self.word(0x1000418a0),0xb40001b4);self.assertEqual(self.word(0x1000418a8),0x52800001);self.assertEqual(self.word(0x1000418d4),0xd4200020);self.assertIn(dict(call='0x1000418ac',word=hex(self.word(0x1000418ac)),target='0x1002f7744'),self.p['branches'])
 def test_model_initial_query_callback_and_strong_loading_task_are_real_properties(self):
  self.assertIn('@Published private(set) var query: [OriginalSearchQueryNode]',self.model);self.assertIn('private let onQueryChanged: ([OriginalSearchQueryNode]) -> Void',self.model);s=body(self.model,'init(query:');self.order(s,['self.query = query','self.onQueryChanged = onQueryChanged','Task { @MainActor [self] in sections = load() }']);self.assertNotIn('searchQueryNodes',self.model);self.assertNotIn('toolbarOwner',self.model)
 def test_real_anchor_resolves_actual_SearchBar_not_global_owner(self):
  self.order(self.opening,['filterBrowserPopover.isDisplayed','var ancestor: NSView? = button','ancestor = view.superview','guard let searchBar = ancestor as? OriginalPanelSearchBar else { return }','let initialQuery = searchBar.filterQuerySnapshot','NSEvent.modifierFlags','ReplicaFilterBrowserModel(query: initialQuery','[weak searchBar] query in searchBar?.applySearchQuery(query)','popover.present(controller, relativeTo: button)']);self.assertNotIn('toolbarOwner',self.opening);self.assertNotIn('state.toggleSearchFilter',self.browser)
 def test_snapshot_exposes_internal_nodes_without_reconstruction_or_fallback(self):
  s=body(self.bar,'var filterQuerySnapshot:');self.assertIn('guard let coordinator else { preconditionFailure(',s);self.assertIn('return coordinator.querySnapshot',s);self.assertEqual(body(self.editor,'var querySnapshot:'),'{ currentNodes }')
  for token in ['searchFilters','text','normalize','?? []']:self.assertNotIn(token,s)
 def test_checked_hidden_and_activation_all_read_same_model(self):
  self.assertIn('query.contains(selection.queryNode)',body(self.model,'func hasSearchFilter('));self.assertIn('!hideApplied || !model.hasSearchFilter($0)',body(self.browser,'private var visibleSections:'));self.assertIn('applied: model.hasSearchFilter(selection)',body(self.browser,'@ViewBuilder private func entryView('));s=body(self.browser,'private func activate(');self.order(s,['model.toggleSearchFilter(selection)','if let modifierFlags']);self.assertNotIn('state.hasSearchFilter(',self.browser)
 def test_toggle_removes_all_exact_nodes_or_appends_then_publishes_and_rereads(self):
  s=body(self.model,'func toggleSearchFilter(');self.order(s,['let filter = selection.queryNode','var nodes = query','if nodes.contains(filter)','nodes.removeAll { $0 == filter }','nodes.append(filter)','query = nodes','onQueryChanged(query)'])
  for token in ['UUID','firstIndex','normalize','applySearchInput','onQueryChanged(nodes)','Task','DispatchQueue']:self.assertNotIn(token,s)
 def test_actual_callback_enters_existing_mode0_normalization_history_publish(self):
  s=body(self.bar,'func applySearchQuery(');self.order(s,['let (field, coordinator) = inputPair()','coordinator.applyProgrammaticQuery(nodes, field: field, editor: editor)']);s=body(self.editor,'func applyProgrammaticQuery(');self.assertIn('suggestionsEnabled: false',s);s=body(self.editor,'private func replaceQuery(');self.order(s,['let normalized','currentNodes = normalized','attributedString(normalized','history.f_1002f5e18(','display(rendered','publishCurrentQuery()','dismissSuggestions()'])
 def test_sixteen_neighbor_methods_and_seven_shared_sources_are_unchanged(self):
  self.assertEqual(len(self.p['unchanged_methods']),16)
  for r in self.p['unchanged_methods']:
   s=pre_suggestion_proposal((ROOT/r['path']).read_text());s=body(s,r['scope'])if 'scope'in r else s;self.assertEqual(hashlib.sha256(body(s,r['symbol']).encode()).hexdigest(),r['body_sha256'])
  self.assertEqual(len(self.p['shared_sources']),7)
  for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_suggestion_filter_title_bytes(ROOT/p)).hexdigest(),h)
 def test_eight_exact_hunks_reverse247_and_do_not_mutate_prior_baseline(self):
  self.assertEqual(len(CHANGES),8);self.assertEqual(sum(x[3]for x in CHANGES),9);changed=[]
  for p,h in self.b['production'].items():
   current=pre_suggestion_proposal_bytes(ROOT/p);old=(self.ph/'before'/p).read_bytes()
   if hashlib.sha256(current).hexdigest()!=h:changed.append(p)
   self.assertEqual(hashlib.sha256(pre_filter_model_query_bytes(ROOT/p)).hexdigest(),h,p);self.assertEqual(pre_filter_model_query(old.decode()).encode()if p.endswith('.swift')else old,old,p)
  self.assertEqual(sorted(changed),sorted(self.p['current_sources']));self.assertEqual(len(changed),4)
 def test_historical_test_adjustments_replay_exactly_and_restore346_inputs(self):
  adjust=json.loads((self.ph/'test-scope-adjustments.json').read_text());expected={};self.assertEqual(adjust,self.p['historical_test_changes'])
  for p,old,new,count in adjust:
   if p not in expected:expected[p]=(self.ph/'before'/p).read_text()
   self.assertEqual(expected[p].count(old),count);expected[p]=expected[p].replace(old,new)
  for p,h in self.b['tests'].items():self.assertEqual(pre_suggestion_proposal_history_bytes(ROOT/p).decode(),expected.get(p,(self.ph/'before'/p).read_text()),p);self.assertEqual(hashlib.sha256(pre_filter_model_query_history_bytes(ROOT/p)).hexdigest(),h,p)
 def test_protocol_snapshot_survives_global_change_and_removes_all_exact_matches(self):
  f=('filter',5,'Raw-ID');other=('filter',4,'Raw-ID');q=[('text','before'),f,other,f,('text','after')];global_query=[('text','external')];proposed=[x for x in q if x!=f];self.assertEqual(proposed,[('text','before'),other,('text','after')]);appended=q+[('filter',5,'raw-id')];self.assertEqual(appended[:-1],q);self.assertEqual(appended[-1],('filter',5,'raw-id'));self.assertEqual(appended.count(f),2);self.assertNotEqual(proposed,[x for x in global_query if x!=f]);self.assertNotEqual(f,('filter',5,'raw-id'))
 def test_protocol_weak_origin_is_not_replaced_by_current_global_or_kept_alive(self):
  class Owner:
   def __init__(self):self.delivered=[]
   def apply(self,q):self.delivered.append(list(q))
  origin=Owner();current=Owner();ref=weakref.ref(origin);model_query=[('text','initial')]
  def send(q):
   actual=ref()
   if actual is not None:actual.apply(q)
  model_query.append(('filter',5,'raw'));send(model_query);self.assertEqual(origin.delivered,[model_query]);self.assertEqual(current.delivered,[]);del origin;self.assertIsNone(ref());model_query.append(('filter',5,'next'));send(model_query);self.assertEqual(len(model_query),3);self.assertEqual(current.delivered,[])
 def test_protocol_publication_reentry_requires_rereading_model_query_for_proposal(self):
  class Model:pass
  model=Model();nodes=[('filter',5,'chosen')];model.query=list(nodes)
  def during_publication():model.query.append(('text','reentrant'))
  during_publication();proposal=list(model.query);self.assertEqual(proposal,[('filter',5,'chosen'),('text','reentrant')]);self.assertNotEqual(proposal,nodes)
 def test_finite_contract_keeps_unknown_and_broader_source_goal_open(self):
  self.assertFalse(self.p['runtime_executed']);self.assertFalse(self.p['full_function_migration_verified']);self.assertIn('0f733c',self.p['remaining'][0]);self.assertIn('constructor',self.p['adaptations'][1]);self.assertEqual(self.p['function_id'],'Paste:0x100006e80')
if __name__=='__main__':unittest.main()
