"""Optional suggestion anchor and menu retention: source/ARM and protocol models, no UI runtime."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from suggestion_anchor_owner_scope_contract import CHANGES,pre_suggestion_anchor_owner,pre_suggestion_anchor_owner_bytes,pre_suggestion_anchor_owner_history_bytes
from suggestion_menu_prepare_scope_contract import pre_suggestion_menu_prepare_bytes, pre_suggestion_menu_prepare_history_bytes
class SuggestionAnchorOwnerContracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ph=ROOT/'.local/p0-repair/phase-181';cls.p=json.loads((cls.ph/'suggestion-anchor-contract.json').read_text());cls.b=json.loads((cls.ph/'baseline.json').read_text());cls.editor=(ROOT/'replica/Sources/Pasto/UI/SearchEditor.swift').read_text();cls.bar=body((ROOT/'replica/Sources/Pasto/UI/OriginalPanelToolbar.swift').read_text(),'final class OriginalPanelSearchBar:');cls.load=body(cls.editor,'func performSuggestionRequest(');cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
 def word(self,a):return struct.unpack('<I',self.n['read'](a,4))[0]
 def order(self,s,tokens):
  p=[s.index(t)for t in tokens];self.assertEqual(p,sorted(p))
 def test_eleven_original_fragments_binary_decoder_and_candidate_are_fresh(self):
  self.assertEqual(len(self.p['original_fragments']),11)
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for key in ['binary','decoder','prior_candidate']:
   r=self.p[key];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
 def test_eight_machine_ranges_and190_direct_branches_are_bound(self):
  self.assertEqual(len(self.p['machine_ranges']),8);self.assertEqual(len(self.p['branches']),190)
  for r in self.p['machine_ranges']:
   data=self.n['read'](int(r['address'],16),int(r['end'],16)-int(r['address'],16));self.assertEqual(data.hex(),r['bytes']);self.assertEqual(hashlib.sha256(data).hexdigest(),r['sha256'])
  for r in self.p['branches']:
   a=int(r['call'],16);w=self.word(a);self.assertEqual(hex(w),r['word']);self.assertEqual(w&0x7c000000,0x14000000);v=w&0x3ffffff;v=v-(1<<26)if v&(1<<25)else v;self.assertEqual(hex(a+4*v),r['target'])
 def test_four_weak_and_ARC_imports_use_actual_dyld_bindings(self):
  self.assertEqual(len(self.p['imports']),4)
  for r in self.p['imports']:
   value,chain=self.n['reachable_pointer'](int(r['pointer'],16));self.assertEqual(chain,r['chain']);self.assertTrue(value>>63);fo=self.n['fixup'][0];raw=self.n['raw'];h=struct.unpack_from('<7I',raw,fo);e=struct.unpack_from('<I',raw,fo+h[2]+4*(value&0xffffff))[0];o=fo+h[3]+(e>>9);self.assertEqual(raw[o:raw.index(b'\0',o)].decode(),r['symbol'])
 def test_three_real_AppKit_selectors_are_resolved_not_guessed(self):
  self.assertEqual([r['name']for r in self.p['selectors']],['textLayoutManager','layoutViewport','convertRect:toView:'])
  for r in self.p['selectors']:
   value,chain=self.n['reachable_pointer'](int(r['pointer'],16));self.assertEqual(chain,r['chain']);self.assertFalse(value>>63);target=self.n['base']+(value&((1<<36)-1));self.assertEqual(hex(target),r['target']);self.assertEqual(self.n['read'](target,len(r['name'])+1),r['name'].encode()+b'\0')
 def test_native_anchor_separates_nil_owner_nil_manager_and_valid_zero_rectangle(self):
  for a,w in [(0x100040834,0xb4000880),(0x100040884,0xb4000678),(0x100040930,0x52800008),(0x100040944,0x52800028),(0x100040958,0x52800028),(0x100040968,0x39008268),(0x100040900,0xaa1503e2)]:self.assertEqual(self.word(a),w)
  branches={r['call']:r['target']for r in self.p['branches']};self.assertEqual(branches['0x1000408b4'],'0x100046e28');self.assertEqual(self.word(0x1002f7e80),0xa945d818);self.assertEqual(self.word(0x1002f7ea8),0xd63f0300)
 def test_native_menu_is_stored_before_anchor_call_and_nil_skips_cleanup(self):
  self.assertEqual(self.word(0x1000414a4),0xf8386ae0);self.assertEqual(self.word(0x1000414bc),0xd63f0120);self.assertEqual(self.word(0x1000414c8),0x54000081);self.assertIn(dict(call='0x1000414d4',word=hex(self.word(0x1000414d4)),target='0x100041448'),self.p['branches']);self.assertLess(0x1000414a4,0x1000414bc)
 def test_real_SearchBar_configures_weak_optional_anchor_on_initial_and_update_paths(self):
  self.assertIn('var onSuggestionAnchor: (NSRange) -> NSRect? = { _ in nil }',self.editor);s=body(self.bar,'func configure(button:');self.order(s,['specification.onSuggestionAnchor = { [weak self] range in self?.suggestionAnchor(for: range) }','if let field, let coordinator','specification.updateField','ReplicaSearchEditor.Coordinator(specification)']);self.assertNotIn('toolbarOwner',s)
 def test_live_anchor_only_gets_geometry_when_manager_exists_and_keeps_zero_valid(self):
  s=body(self.bar,'func suggestionAnchor(for range:');self.order(s,['let (field, _) = inputPair()','field.f_100045c2c().f_100041f9c()','guard let manager = editor.textLayoutManager else { return nil }','manager.textViewportLayoutController.layoutViewport()','OriginalSearchSuggestionAnchor.f_100046e28(manager, range: range)','return editor.convert(rect, to: field)'])
  for token in ['.isEmpty','.zero','dismiss','suggestionMenu','suggestionTask','history']:self.assertNotIn(token,s)
 def test_nonempty_menu_reuse_precedes_optional_anchor_and_only_valid_anchor_shows(self):
  self.order(self.load,['guard !Task.isCancelled, !candidates.isEmpty','let entries =','guard !entries.isEmpty else','let menu = self.suggestionMenu ?? ReplicaSearchSuggestionsMenu()','self.suggestionMenu = menu','guard let anchorRect = parent.onSuggestionAnchor(context.anchorRange) else { return }','menu.show(rows:']);self.assertEqual(self.load.count('self.suggestionMenu = menu'),1);nil=body(self.load,'guard let anchorRect =');self.assertEqual(nil,'{ return }');self.assertNotIn('textLayoutManager',self.load)
 def test_remove_unused_eager_editor_argument_and_preserve_actual_request_owner(self):
  sig=self.editor[self.editor.index('        func performSuggestionRequest('):self.editor.index('            let candidates =',self.editor.index('        func performSuggestionRequest('))];self.assertNotIn('editor:',sig);s=body(self.bar,'func performSuggestionRequest(');self.assertIn('coordinator.performSuggestionRequest(context, field: field)',s);self.assertNotIn('f_100041f9c()',s);self.assertIn('withExtendedLifetime(owner)',body(self.editor,'private func updateSuggestions('))
 def test_fourteen_neighbors_and_eleven_shared_sources_keep_prior_repairs(self):
  self.assertEqual(len(self.p['unchanged_methods']),14)
  for r in self.p['unchanged_methods']:
   s=(ROOT/r['path']).read_text();s=body(s,r['scope'])if 'scope'in r else s;self.assertEqual(hashlib.sha256(body(s,r['symbol']).encode()).hexdigest(),r['body_sha256'])
  self.assertEqual(len(self.p['shared_sources']),11)
  for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_suggestion_menu_prepare_bytes(ROOT/p)).hexdigest(),h)
 def test_six_exact_hunks_reverse247_sources_and_keep_historical_snapshots(self):
  self.assertEqual(len(CHANGES),6);changed=[]
  for p,h in self.b['production'].items():
   if hashlib.sha256(pre_suggestion_menu_prepare_bytes(ROOT/p)).hexdigest()!=h:changed.append(p)
   self.assertEqual(hashlib.sha256(pre_suggestion_anchor_owner_bytes(ROOT/p)).hexdigest(),h,p);old=(self.ph/'before'/p).read_bytes();self.assertEqual(pre_suggestion_anchor_owner(old.decode()).encode()if p.endswith('.swift')else old,old,p)
  self.assertEqual(sorted(changed),sorted(self.p['current_sources']));self.assertEqual(len(changed),2)
 def test_eight_exact_test_edits_restore354_old_Python_inputs(self):
  a=json.loads((self.ph/'test-scope-adjustments.json').read_text());self.assertEqual(a,self.p['historical_test_changes']);self.assertEqual(len(a),8);expected={}
  for p,old,new,count in a:
   if p not in expected:expected[p]=(self.ph/'before'/p).read_text()
   self.assertEqual(expected[p].count(old),count);expected[p]=expected[p].replace(old,new)
  self.assertEqual(len(expected),3)
  for p,h in self.b['tests'].items():self.assertEqual(pre_suggestion_menu_prepare_history_bytes(ROOT/p).decode(),expected.get(p,(self.ph/'before'/p).read_text()),p);self.assertEqual(hashlib.sha256(pre_suggestion_anchor_owner_history_bytes(ROOT/p)).hexdigest(),h,p)
 def present(self,state,anchor):
  if state['menu']is None:state['menu']=dict(rows=[],visible=False)
  state['events'].append('anchor');rect=anchor()
  if rect is None:return
  state['menu']['rows']=['new'];state['menu']['visible']=True
 def test_protocol_missing_anchor_retains_existing_menu_rows_and_task(self):
  old=dict(rows=['old'],visible=True);state=dict(menu=old,task='newer',events=[]);self.present(state,lambda:None);self.assertIs(state['menu'],old);self.assertEqual(state['menu'],dict(rows=['old'],visible=True));self.assertEqual(state['task'],'newer')
 def test_protocol_initial_missing_anchor_allocates_unshown_menu_before_querying_anchor(self):
  state=dict(menu=None,events=[])
  def anchor():self.assertIsNotNone(state['menu']);self.assertEqual(state['menu']['rows'],[]);return None
  self.present(state,anchor);self.assertEqual(state['menu'],dict(rows=[],visible=False));self.assertEqual(state['events'],['anchor'])
 def test_protocol_some_zero_is_valid_and_later_valid_anchor_reuses_same_object(self):
  state=dict(menu=None,events=[]);self.present(state,lambda:None);menu=state['menu'];self.present(state,lambda:(0,0,0,0));self.assertIs(state['menu'],menu);self.assertTrue(menu['visible']);self.assertEqual(menu['rows'],['new'])
 def test_actual_axis_aligned_view_coordinate_composition_is_preserved(self):
  field_to_bar=lambda p:(p[0]+12,40-p[1]);bar_to_window=lambda p:(p[0]+30,500-p[1]);field_to_window=lambda p:(p[0]+42,p[1]+460)
  for p in [(0,0),(10,5),(-3,30)]:self.assertEqual(bar_to_window(field_to_bar(p)),field_to_window(p))
 def test_finite_anchor_contract_keeps_unknown_context_and_other_menu_consumers_open(self):
  self.assertEqual([r['function_id']for r in self.p['contracts']],['Paste:0x1000407f8']);self.assertEqual(self.p['additional_contracts'][0]['function_id'],'Paste:0x100041190');self.assertFalse(self.p['runtime_executed']);self.assertFalse(self.p['full_function_migration_verified']);self.assertIn('0f733c',self.p['remaining'][0]);self.assertIn('context',self.p['remaining'][1]);self.assertIn('installed live request',self.p['remaining'][1])
if __name__=='__main__':unittest.main()
