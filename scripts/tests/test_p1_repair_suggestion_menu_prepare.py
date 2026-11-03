"""Menu state survives missing placement hosts; source/Mach-O checks, no AppKit execution."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment
from suggestion_menu_prepare_scope_contract import CHANGES,HISTORICAL_TEST_CHANGES,pre_suggestion_menu_prepare,pre_suggestion_menu_prepare_bytes,pre_suggestion_menu_prepare_history_bytes
from suggestion_list_lifecycle_scope_contract import pre_suggestion_list_lifecycle, pre_suggestion_list_lifecycle_bytes, pre_suggestion_list_lifecycle_history_bytes
class SuggestionMenuPrepareContracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ph=ROOT/'.local/p0-repair/phase-182';cls.p=json.loads((cls.ph/'suggestion-menu-prepare-contract.json').read_text());cls.b=json.loads((cls.ph/'baseline.json').read_text());cls.source=pre_suggestion_list_lifecycle((ROOT/'replica/Sources/Pasto/UI/ReplicaSearchSuggestionsMenu.swift').read_text());cls.show=body(cls.source,'func show(rows:');cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
 def word(self,a):return struct.unpack('<I',self.n['read'](a,4))[0]
 def order(self,s,tokens):
  positions=[s.index(t)for t in tokens];self.assertEqual(positions,sorted(positions))
 def original(self,a):
  row=next(r for r in self.p['original_fragments']if r['address']==a);return original_fragment((ROOT/row['path']).read_text(),a[2:])
 def test_original_fragments_binary_and_decoder_are_bound(self):
  self.assertEqual(len(self.p['original_fragments']),14)
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for key in ['binary','decoder']:
   r=self.p[key];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
 def test_five_native_ranges_and221_direct_branches(self):
  self.assertEqual(len(self.p['machine_ranges']),5);self.assertEqual(len(self.p['branches']),221)
  for r in self.p['machine_ranges']:
   data=self.n['read'](int(r['address'],16),int(r['end'],16)-int(r['address'],16));self.assertEqual(data.hex(),r['bytes']);self.assertEqual(hashlib.sha256(data).hexdigest(),r['sha256'])
  for r in self.p['branches']:
   a=int(r['call'],16);w=self.word(a);self.assertEqual(hex(w),r['word']);v=w&0x3ffffff;v=v-(1<<26)if v&(1<<25)else v;self.assertEqual(hex(a+v*4),r['target'])
 def test_real_window_and_contentView_selector_fixups(self):
  self.assertEqual([r['name']for r in self.p['selectors']],['window','setContentView:'])
  for r in self.p['selectors']:
   value,chain=self.n['reachable_pointer'](int(r['pointer'],16));self.assertEqual(chain,r['chain']);self.assertFalse(value>>63);dest=self.n['base']+(value&((1<<36)-1));self.assertEqual(hex(dest),r['target']);self.assertEqual(self.n['read'](dest,len(r['name'])+1),r['name'].encode()+b'\0')
 def test_original_escape_rows_and_nil_selection_precede_native_window_gate(self):
  self.order(self.original('0x100059c6c'),['::onEscapePressed','*puVar1 = param_7','FUN_10002ee40(param_5)','FUN_10005ad00(']);self.order(self.original('0x10002ee40'),['::items) = param_1','::selectedIndex','*pIVar3 = 0','*(undefined1 *)(pIVar3 + 1) = 1','FUN_10002e80c('])
  calls={r['call']:r['target']for r in self.p['branches']};self.assertEqual(calls['0x100059e58'],'0x10002ee40');self.assertEqual(calls['0x100059ea4'],'0x10005ad00');self.assertEqual(self.word(0x100059e1c),0xa9005d18);self.assertEqual(self.word(0x10002ee90),0xf900011f);self.assertEqual(self.word(0x10002ee9c),0x39002109);self.assertEqual(self.word(0x10005ad60),0xb4000e40)
 def test_preparation_replaces_state_before_window_read_and_no_empty_dismiss(self):
  self.order(self.show,['escape = onEscape','self.rows = rows','accept = onAccept','selectedIndex = nil','scroller.setRows(rows)','scroller.select(selectedIndex)','guard let parent = anchorView.window','let width = max(120','orderFront(nil)','self.anchorView = anchorView','installMonitors(parent: parent)'])
  for token in ['rows.isEmpty','dismiss()','cancel()','removeMonitors()']:self.assertNotIn(token,self.show)
 def test_missing_window_return_has_no_placement_or_monitor_side_effects(self):
  gate=body(self.show,'guard let parent = anchorView.window');self.assertEqual(gate,'{ return }');prefix=self.show[:self.show.index('guard let parent =')]
  for token in ['setFrame(','orderFront(','installMonitors(','removeMonitors(','self.anchorView =','orderOut(']:self.assertNotIn(token,prefix)
  self.assertNotIn('window',self.original('0x100059c6c'));self.assertNotIn('isEmpty',self.original('0x100059c6c'))
 def test_mouse_anchor_changes_only_after_successful_screen_and_display(self):
  self.order(self.show,['guard let parent =','guard let screen =','if self.parent !== parent','display()','orderFront(nil)','self.anchorView = anchorView','installMonitors(parent: parent)']);self.assertEqual(self.show.count('self.anchorView ='),1)
 def test_upstream_candidate_empty_dismiss_and_optional_anchor_retention_preserved(self):
  s=body((ROOT/'replica/Sources/Pasto/UI/SearchEditor.swift').read_text(),'func performSuggestionRequest(');self.order(s,['guard !Task.isCancelled, !candidates.isEmpty','dismissSuggestionMenu()','let entries =','guard !entries.isEmpty','self.suggestionMenu = menu','guard let anchorRect = parent.onSuggestionAnchor','menu.show(rows:'])
 def test_keyboard_navigation_and_ESC_panel_adaptation_unchanged(self):
  s=body(self.source,'func handleKeyDown(')
  for token in ['case .down: moveSelection(by: 1)','case .up: moveSelection(by: -1)','case .home: moveSelection(by: -rows.count)','case .end: moveSelection(by: rows.count)','case .pageUp: moveSelection(by: -5)','case .pageDown: moveSelection(by: 5)','return !forwardToPanel']:self.assertIn(token,s)
  move=body(self.source,'private func moveSelection(');self.assertIn('.now() + 0.1',move);self.assertIn('mouseSelectionCooldown?.cancel()',move)
 def test_ten_neighbor_methods_and_ten_shared_sources_remain_unchanged(self):
  self.assertEqual(len(self.p['unchanged_methods']),10)
  for r in self.p['unchanged_methods']:
   s=pre_suggestion_list_lifecycle((ROOT/r['path']).read_text());s=body(s,r['scope'])if 'scope'in r else s;self.assertEqual(hashlib.sha256(body(s,r['symbol']).encode()).hexdigest(),r['body_sha256'])
  self.assertEqual(len(self.p['shared_sources']),10)
  for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_suggestion_list_lifecycle_bytes(ROOT/p)).hexdigest(),h)
 def test_two_exact_hunks_restore_all247_production_inputs_idempotently(self):
  self.assertEqual(len(CHANGES),2);changed=[]
  for p,h in self.b['production'].items():
   if hashlib.sha256(pre_suggestion_list_lifecycle_bytes(ROOT/p)).hexdigest()!=h:changed.append(p)
   self.assertEqual(hashlib.sha256(pre_suggestion_menu_prepare_bytes(ROOT/p)).hexdigest(),h,p);old=(self.ph/'before'/p).read_bytes();self.assertEqual(pre_suggestion_menu_prepare(old.decode()).encode()if p.endswith('.swift')else old,old,p)
  self.assertEqual(changed,list(self.p['current_sources']));self.assertEqual(len(changed),1)
 def test_six_exact_historical_edits_restore356_Python_inputs(self):
  self.assertEqual(len(HISTORICAL_TEST_CHANGES),6);self.assertEqual(HISTORICAL_TEST_CHANGES,self.p['historical_test_changes']);expected={}
  for p,old,new,count in HISTORICAL_TEST_CHANGES:
   if p not in expected:expected[p]=(self.ph/'before'/p).read_text()
   self.assertEqual(expected[p].count(old),count);expected[p]=expected[p].replace(old,new)
  self.assertEqual(len(expected),2)
  for p,h in self.b['tests'].items():self.assertEqual(pre_suggestion_list_lifecycle_history_bytes(ROOT/p).decode(),expected.get(p,(self.ph/'before'/p).read_text()),p);self.assertEqual(hashlib.sha256(pre_suggestion_menu_prepare_history_bytes(ROOT/p)).hexdigest(),h,p)
 def test_prepare_and_placement_boundary_allows_missing_host_and_empty_input(self):
  # A source-bound protocol model checks observable states, not an execution claim.
  def model(rows,host,screen):
   state=dict(rows=['old'],escape='old',accept='old',selected=4,anchor='old',visible=True,monitors='old')
   state.update(escape='new',rows=rows,accept='new',selected=None)
   if not host:return state
   if not screen:return state
   state.update(anchor='new',visible=True,monitors='new');return state
  for rows in [[],['new'],['a','b']]:
   for host,screen in [(False,False),(True,False),(True,True)]:
    state=model(rows,host,screen);self.assertEqual(state['rows'],rows);self.assertEqual(state['escape'],'new');self.assertEqual(state['accept'],'new');self.assertIsNone(state['selected']);self.assertTrue(state['visible']);self.assertEqual(state['anchor'],'new'if host and screen else'old');self.assertEqual(state['monitors'],state['anchor'])
 def test_finite_scope_does_not_claim_constructor_monitor_or_whole_app_equivalence(self):
  self.assertEqual([r['function_id']for r in self.p['contracts']],['Paste:0x100059c6c']);self.assertFalse(self.p['runtime_executed']);self.assertFalse(self.p['full_function_migration_verified']);self.assertIn('0f733c',self.p['remaining'][0]);self.assertIn('keyboard monitor',self.p['remaining'][1])
if __name__=='__main__':unittest.main()
