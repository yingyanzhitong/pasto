"""Actual list keyboard attachment and weak menu close callbacks; source/Mach-O only."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment
from suggestion_list_lifecycle_scope_contract import CHANGES,HISTORICAL_TEST_CHANGES,pre_suggestion_list_lifecycle,pre_suggestion_list_lifecycle_bytes,pre_suggestion_list_lifecycle_history_bytes
from suggestion_filter_title_scope_contract import pre_suggestion_filter_title_bytes, pre_suggestion_filter_title_history_bytes
class SuggestionListLifecycleContracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ph=ROOT/'.local/p0-repair/phase-183';cls.p=json.loads((cls.ph/'suggestion-list-lifecycle-contract.json').read_text());cls.b=json.loads((cls.ph/'baseline.json').read_text());cls.s=(ROOT/'replica/Sources/Pasto/UI/ReplicaSearchSuggestionsMenu.swift').read_text();cls.menu=body(cls.s,'final class ReplicaSearchSuggestionsMenu:');cls.scroller=body(cls.s,'private final class SuggestionsScroller:');cls.list=body(cls.s,'private final class SuggestionsList:');cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
 def word(self,a):return struct.unpack('<I',self.n['read'](a,4))[0]
 def order(self,s,tokens):
  values=[s.index(t)for t in tokens];self.assertEqual(values,sorted(values))
 def original(self,a):
  r=next(x for x in self.p['original_fragments']if x['address']==a);return original_fragment((ROOT/r['path']).read_text(),a[2:])
 def test22_original_fragments_binary_and_decoder_are_fresh(self):
  self.assertEqual(len(self.p['original_fragments']),22)
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for key in ['binary','decoder']:
   r=self.p[key];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
 def test13_machine_ranges_and335_direct_branches_are_bound(self):
  self.assertEqual(len(self.p['machine_ranges']),13);self.assertEqual(len(self.p['branches']),335)
  for r in self.p['machine_ranges']:
   d=self.n['read'](int(r['address'],16),int(r['end'],16)-int(r['address'],16));self.assertEqual(d.hex(),r['bytes']);self.assertEqual(hashlib.sha256(d).hexdigest(),r['sha256'])
  for r in self.p['branches']:
   a=int(r['call'],16);w=self.word(a);self.assertEqual(hex(w),r['word']);self.assertEqual(w&0x7c000000,0x14000000);v=w&0x3ffffff;v=v-(1<<26)if v&(1<<25)else v;self.assertEqual(hex(a+4*v),r['target'])
 def test62_real_weak_ARC_super_and_block_imports(self):
  self.assertEqual(len(self.p['imports']),62)
  for r in self.p['imports']:
   v,chain=self.n['reachable_pointer'](int(r['pointer'],16));self.assertEqual(chain,r['chain']);self.assertTrue(v>>63);f=self.n['fixup'][0];raw=self.n['raw'];h=struct.unpack_from('<7I',raw,f);e=struct.unpack_from('<I',raw,f+h[2]+4*(v&0xffffff))[0];o=f+h[3]+(e>>9);self.assertEqual(raw[o:raw.index(b'\0',o)].decode(),r['symbol'])
 def test12_real_monitor_window_and_observer_selector_bindings(self):
  self.assertEqual(len(self.p['selectors']),12)
  for r in self.p['selectors']:
   v,chain=self.n['reachable_pointer'](int(r['pointer'],16));self.assertEqual(chain,r['chain']);self.assertFalse(v>>63);dest=self.n['base']+(v&((1<<36)-1));self.assertEqual(hex(dest),r['target']);self.assertEqual(self.n['read'](dest,len(r['name'])+1),r['name'].encode()+b'\0')
 def test_native_constructor_and_actual_show_delay_controls_until_needed(self):
  init=self.original('0x10005b1cc');self.assertIn('::suggestionsView) = 0',init);self.assertIn('::suggestionsScrollView) = 0',init);self.assertNotIn('FUN_1000496ac',init)
  show=self.original('0x100059c6c');self.order(show,['if (lVar5 == 0)','FUN_10002ebe4()','FUN_1000496ac()','::onEscapePressed','FUN_10002ee40(param_5)','FUN_10005ad00('])
  ctor=body(self.menu,'init()');self.assertNotIn('SuggestionsScroller()',ctor);self.assertNotIn('contentView',ctor);self.assertIn('storedScroller?.dispose()',body(self.menu,'deinit'))
  get=body(self.menu,'private func suggestionScroller()');self.order(get,['if let storedScroller { return storedScroller }','let scroller = SuggestionsScroller()','storedScroller = scroller','return scroller'])
 def test_attachment_occurs_after_host_exists_and_before_screen_resolution(self):
  show=body(self.menu,'func show(rows:');self.order(show,['let scroller = suggestionScroller()','scroller.onEscape = onEscape','scroller.setRows(rows, onAccept: onAccept)','guard let parent = anchorView.window','contentView = scroller','let width =','guard let screen =','orderFront(nil)','installMonitors(parent: parent, anchorView: anchorView)'])
  self.assertEqual(body(show,'guard let parent ='),'{ return }');self.assertNotIn('rows.isEmpty',show)
 def test_native_List_attachment_and_dealloc_remove_monitor_before_reinstall(self):
  self.order(self.original('0x10003002c'),['_objc_msgSendSuper2(&local_50,"viewDidMoveToWindow")','FUN_10002f574()','objc_stub::window(param_1)','FUN_10002f750(0)']);self.order(self.original('0x10002f67c'),['FUN_10002f574()','"dealloc"'])
  attached=body(self.list,'override func viewDidMoveToWindow()');self.order(attached,['super.viewDidMoveToWindow()','removeKeyboardMonitor()','if window != nil { installKeyboardMonitor() }']);self.assertIn('removeKeyboardMonitor()',body(self.list,'deinit'));self.assertNotIn('isVisible',attached)
 def test_key_monitor_is_weak_List_scoped_and_removed_token_is_nil(self):
  install=body(self.list,'private func installKeyboardMonitor()');self.assertIn('rawValue: 0x400',install);self.assertIn('[weak self]',install);self.assertIn('self?.handleKeyDown(event) ?? false',install);self.assertIn('return handled ? nil : event',install);self.assertNotIn('keyboardMonitor',self.menu)
  remove=body(self.list,'private func removeKeyboardMonitor()');self.order(remove,['NSEvent.removeMonitor(keyboardMonitor)','self.keyboardMonitor = nil'])
 def test_List_navigation_acceptance_and_cooldown_have_same_owner(self):
  for token in ['private var selectedIndex: Int?','private var mouseSelectionCooldown: DispatchWorkItem?','private var keyboardMonitor: Any?']:self.assertIn(token,self.list);self.assertNotIn(token,self.menu)
  key=body(self.list,'private func handleKeyDown(');self.assertNotIn('isVisible',key)
  for token in ['case .down: moveSelection(by: 1)','case .up: moveSelection(by: -1)','case .home: moveSelection(by: -items.count)','case .end: moveSelection(by: items.count)','case .pageUp: moveSelection(by: -5)','case .pageDown: moveSelection(by: 5)','guard let selectedIndex else { return false }','default: return false']:self.assertIn(token,key)
  move=body(self.list,'private func moveSelection(');self.order(move,['guard !items.isEmpty','mouseSelectionCooldown?.cancel()','selectedIndex.map','select(index)','revealSelection()','let cooldown = DispatchWorkItem { [weak self]','mouseSelectionCooldown = cooldown','DispatchQueue.main.asyncAfter(deadline: .now() + 0.1'])
 def test_rows_capture_individual_actions_and_keyboard_uses_same_current_item(self):
  row=body(self.list,'func setRows(');self.order(row,['items = values.enumerated().map','Item(row: row, onAccept: { onAccept(index) })','select(nil)','rows.forEach','rows = items.enumerated().map','row.onAccept = item.onAccept']);self.assertNotIn('self?.onAccept?',row)
  accept=body(self.list,'private func acceptRow(');self.order(accept,['guard index < items.count else { return }','precondition(index >= 0)','items[index].onAccept()']);self.assertNotIn('Menu',accept)
 def test_hover_and_exit_share_same_List_cooldown(self):
  rows=body(self.list,'func setRows(');self.assertEqual(rows.count('self.mouseSelectionCooldown == nil'),2);self.assertIn('self.select(index)',body(rows,'row.onHover ='));self.assertIn('self.select(nil)',body(rows,'row.onExit ='))
 def test_user_ESC_panel_adapter_preserved_without_pre_dismiss(self):
  key=body(self.list,'private func handleKeyDown(');esc=key[key.index('        case .escape:'):key.index('        default:')];self.order(esc,['let parent = window?.parent','let forwardToPanel = parent is ReplicaPanel','onEscape?()','return !forwardToPanel']);self.assertNotIn('dismiss',esc);self.assertNotIn('cancel()',esc)
 def test_mouse_anchor_is_strongly_captured_by_monitor_with_weak_menu(self):
  install=body(self.menu,'private func installMonitors(');self.order(install,['removeMonitors()','mouseMonitor = NSEvent.addLocalMonitorForEvents','Self.handleMouseDown(event, anchorView: anchorView, owner: { [weak self] in self })','lostFocusObserver = NotificationCenter.default.addObserver']);self.assertIn('rawValue: 0x200000a',install);self.assertNotIn('private weak var anchorView',self.menu);self.assertNotIn('self.anchorView',self.menu)
  original=self.original('0x10005a3b8');self.assertIn('*(undefined8 *)(puVar3 + 0x18) = param_2',original)
 def test_native_mouse_has_two_weak_loads_and_releases_owners_before_callback(self):
  imports={r['call']:r['symbol']for r in self.p['imports']};self.assertEqual(imports['0x10005a6b4'],'_swift_unknownObjectWeakLoadStrong');self.assertEqual(imports['0x10005a808'],'_swift_unknownObjectWeakLoadStrong')
  for a in ['0x10005a700','0x10005a834','0x10005a864']:self.assertEqual(imports[a],'_objc_release')
  self.assertEqual(self.word(0x10005a86c),0xd63f02c0)
  first=body(self.menu,'private static func isMenuWindow(');self.assertIn('let menu: NSWindow? = owner()',first);self.assertIn('return event.window == menu',first);read=body(self.menu,'private static func escapeCallback(');self.assertIn('owner()?.storedScroller?.onEscape',read);self.assertEqual(self.menu.count('@inline(never)'),2)
 def test_mouse_exemption_requires_non_nil_windows_and_callback_snapshot_does_not_close(self):
  s=body(self.menu,'private static func handleMouseDown(');self.order(s,['if isMenuWindow(event, owner: owner)','if let eventWindow = event.window, let anchorWindow = anchorView.window','eventWindow == anchorWindow','anchorView.bounds.contains','let callback = escapeCallback(owner: owner)','callback?()'])
  for t in ['guard let self','isVisible','dismiss()','orderOut','removeMonitors','suggestionScroller()']:self.assertNotIn(t,s)
  focus=body(self.menu,'private func installMonitors(');focus=focus[focus.index('lostFocusObserver ='):];self.order(focus,['object: parent, queue: .main','let callback = Self.escapeCallback(owner: { [weak self] in self })','callback?()'])
  close=body(self.menu,'func dismiss()');self.order(close,['removeMonitors()','removeChildWindow(self)','orderOut(nil)']);self.assertNotIn('onEscape',close)
 def test16_neighbor_methods_and10_shared_sources_stay_unchanged(self):
  self.assertEqual(len(self.p['unchanged_methods']),16)
  for r in self.p['unchanged_methods']:
   s=body((ROOT/r['path']).read_text(),r['scope']);self.assertEqual(hashlib.sha256(body(s,r['symbol']).encode()).hexdigest(),r['body_sha256'])
  self.assertEqual(len(self.p['shared_sources']),10)
  for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_suggestion_filter_title_bytes(ROOT/p)).hexdigest(),h)
 def test20_exact_hunks_reverse_all247_sources_and_old_input_is_idempotent(self):
  self.assertEqual(len(CHANGES),20);self.assertEqual(CHANGES,json.loads((self.ph/'production-changes.json').read_text()));changed=[]
  for p,h in self.b['production'].items():
   if hashlib.sha256(pre_suggestion_filter_title_bytes(ROOT/p)).hexdigest()!=h:changed.append(p)
   self.assertEqual(hashlib.sha256(pre_suggestion_list_lifecycle_bytes(ROOT/p)).hexdigest(),h,p);old=(self.ph/'before'/p).read_bytes();self.assertEqual(pre_suggestion_list_lifecycle(old.decode()).encode()if p.endswith('.swift')else old,old,p)
  self.assertEqual(changed,list(self.p['current_sources']));self.assertEqual(len(changed),1)
 def test8_history_patterns_restore358_frozen_Python_inputs(self):
  self.assertEqual(len(HISTORICAL_TEST_CHANGES),8);self.assertEqual(HISTORICAL_TEST_CHANGES,self.p['historical_test_changes']);expected={}
  for p,old,new,count in HISTORICAL_TEST_CHANGES:
   if p not in expected:expected[p]=(self.ph/'before'/p).read_text()
   self.assertEqual(expected[p].count(old),count);expected[p]=expected[p].replace(old,new)
  self.assertEqual(len(expected),3)
  for p,h in self.b['tests'].items():self.assertEqual(pre_suggestion_filter_title_history_bytes(ROOT/p).decode(),expected.get(p,(self.ph/'before'/p).read_text()),p);self.assertEqual(hashlib.sha256(pre_suggestion_list_lifecycle_history_bytes(ROOT/p)).hexdigest(),h,p)
 def test_protocol_attachment_and_weak_callback_reentrancy_boundaries(self):
  # Source-bound event protocol model, explicitly no NSView/NSEvent execution.
  events=[];token=None
  def attach(window):
   nonlocal token
   if token is not None:events.append(('remove',token));token=None
   if window is not None:token=window;events.append(('install',window))
  for w in ['a','a',None,'b',None]:attach(w)
  self.assertEqual(events,[('install','a'),('remove','a'),('install','a'),('remove','a'),('install','b'),('remove','b')]);self.assertIsNone(token)
  state={'owner':{'callback':lambda:events.append('callback')}}
  def read():return state['owner']['callback']if state['owner']else None
  callback=read();state['owner']=None;callback();self.assertEqual(events[-1],'callback');self.assertIsNone(read())
 def test_finite_scope_keeps_unknown_and_whole_parent_goal_open(self):
  self.assertEqual([r['function_id']for r in self.p['contracts']],['Paste:0x10003002c','Paste:0x10005a618','Paste:0x10005a918']);self.assertEqual(self.p['additional_contracts'][0]['function_id'],'Paste:0x100059c6c');self.assertFalse(self.p['runtime_executed']);self.assertFalse(self.p['full_function_migration_verified']);self.assertIn('0f733c',self.p['remaining'][0])
if __name__=='__main__':unittest.main()
