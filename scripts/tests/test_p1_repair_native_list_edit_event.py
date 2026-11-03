"""Same-native-List editing event and existing-cell consumer; no AppKit/CoreData execution."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts/tests'),str(ROOT/'scripts')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from native_list_edit_event_scope_contract import CHANGES,pre_native_list_edit_event,pre_native_list_edit_event_bytes

from native_tab_source_renderer_scope_contract import pre_native_tab_source_renderer, pre_native_tab_source_renderer_bytes

class NativeListEditEvent(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ph=ROOT/'.local/p0-repair/phase-168';cls.p=json.loads((cls.ph/'native-list-edit-event-contract.json').read_text());cls.base=json.loads((cls.ph/'baseline.json').read_text());cls.s={Path(p).stem:(ROOT/p).read_text()for p in cls.p['current_sources']};cls.l=cls.s['ClipboardListPersistence'];cls.ui=cls.s['ReplicaUIController'];cls.panel=cls.s['PanelViews'];cls.toolbar=cls.s['OriginalPanelToolbar'];cls.tabs=cls.s['OriginalPanelTabBar'];cls.title=cls.s['OriginalPinboardTabTitle'];cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
 def order(self,s,tokens):
  p=[s.index(t)for t in tokens];self.assertEqual(p,sorted(p))
 def test_original_fragments_binary_decoder_and_complete_machine_ranges(self):
  self.assertEqual(len(self.p['original_fragments']),22)
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for k in ['binary','decoder']:
   r=self.p[k];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
  self.assertEqual(len(self.p['machine_ranges']),8)
  for r in self.p['machine_ranges']:
   a=int(r['start'],16);b=int(r['end'],16);self.assertEqual(hashlib.sha256(self.n['read'](a,b-a)).hexdigest(),r['sha256'])
 def test_actual_calls_bind_objectID_lookup_animation_and_label_editor(self):
  self.assertEqual(len(self.p['calls']),74);calls={}
  for r in self.p['calls']:
   a=int(r['address'],16);w=int.from_bytes(self.n['read'](a,4),'little');self.assertEqual(w.to_bytes(4,'little').hex(),r['bytes']);self.assertEqual(w&0xfc000000,0x94000000);d=w&0x3ffffff;d=d-(1<<26)if d&(1<<25)else d;self.assertEqual(hex(a+4*d),r['target']);calls[a]=a+4*d
  self.assertEqual(calls[0x100099890],0x1003541f4);self.assertEqual(calls[0x10009989c],0x100095040);self.assertEqual(calls[0x1000998c8],0x10009727c);self.assertEqual(calls[0x1000999c0],0x10021cadc)
 def test_asyncAfter_subject_send_and_weak_owner_are_true_sdk_imports(self):
  for r in self.p['sdk_imports']:
   a=int(r['stub'],16);x,y=struct.unpack('<II',self.n['read'](a,8));self.assertEqual(self.n['read'](a,12).hex(),r['bytes']);imm=((x>>5)&0x7ffff)*4+((x>>29)&3);imm=imm-(1<<21)if imm&(1<<20)else imm;q=(a&~4095)+(imm<<12)+((y>>10)&0xfff)*8;self.assertEqual(hex(q),r['pointer']);v,c=self.n['reachable_pointer'](q);self.assertTrue(v>>63);self.assertEqual(c,r['chain']);f=self.n['fixup'][0];h=struct.unpack_from('<7I',self.n['raw'],f);entry=struct.unpack_from('<I',self.n['raw'],f+h[2]+4*(v&0xffffff))[0];o=f+h[3]+(entry>>9);self.assertEqual(self.n['raw'][o:self.n['raw'].index(b'\0',o)].decode(),r['symbol'])
  names=' '.join(r['symbol']for r in self.p['sdk_imports']);self.assertIn('PassthroughSubjectC4send',names);self.assertIn('asyncAfter',names);self.assertIn('_swift_unknownObjectWeakLoadStrong',names)
 def test_delay_animation_and_callback_argument_are_bound_to_actual_words(self):
  for r in self.p['words']:self.assertEqual(self.n['read'](int(r['address'],16),4).hex(),r['bytes'])
  value=0x9999999999999999
  self.assertEqual(int.from_bytes(self.n['read'](0x1000397a4,4),'little'),0xb201e7e8)
  for a in [0x1000397a8,0x1000397ac]:
   w=int.from_bytes(self.n['read'](a,4),'little');shift=((w>>21)&3)*16;value=(value&~(0xffff<<shift))|(((w>>5)&0xffff)<<shift)
  self.assertEqual(struct.unpack('<d',value.to_bytes(8,'little'))[0],0.2)
  w=int.from_bytes(self.n['read'](0x1000999a8,4),'little');value=(0x3333333333333333&((1<<48)-1))|(((w>>5)&0xffff)<<48);self.assertEqual(struct.unpack('<d',value.to_bytes(8,'little'))[0],0.15)
  x,y=struct.unpack('<II',self.n['read'](0x10009aac0,8));imm=((x>>5)&0x7ffff)*4+((x>>29)&3);imm=imm-(1<<21)if imm&(1<<20)else imm;self.assertEqual((0x10009aac0&~4095)+(imm<<12)+((y>>10)&0xfff),0x100099838)
 def test_created_List_is_retained_across_delay_and_only_owner_is_weak(self):
  s=body(self.ui,'func createPinboard(assignSelection:');self.order(s,['let board = try store.createPinboardTarget(name: name)','if assignSelection','let target = board.listTarget','DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) { [weak self, target] in','self?.state.beginEditingListSubject.send(target)'])
  for t in ['store.pinboards.contains','tabRenameRequest','board.id.uuidString','target.isDeleted','Task']:self.assertNotIn(t,s)
  self.assertIn('ClipboardListTarget(object: nativeObject)',body(self.l,'public struct ClipboardPinboardTarget'))
 def test_menu_reuses_native_event_instead_of_string_token_pending_state(self):
  m=body(self.panel,'private func localListMenu(');self.assertIn('requestTabRename(target)',m);f=body(self.panel,'private func requestTabRename(');self.assertIn('state.beginEditingListSubject.send(target)',f);self.assertNotIn('UUID',f);self.assertNotIn('identifier',f)
  self.assertNotIn('tabRenameRequest',self.ui+self.panel);self.assertIn('let beginEditingListSubject = PassthroughSubject<ClipboardListTarget, Never>()',self.ui)
  self.assertIn('beginRequest: nil',body(self.panel,'private func boardButton('));self.assertIn('onEnd: {}',body(self.panel,'private func boardButton('))
 def test_live_subscription_setup_weak_owner_and_explicit_teardown(self):
  make=body(self.toolbar,'func makeNSView(');self.order(make,['updateNSView(view, context: context)','view.observeListEditing(state.beginEditingListSubject.eraseToAnyPublisher())','return view'])
  s=body(self.toolbar,'func observeListEditing(');self.order(s,['publisher.sink { [weak self] target in','MainActor.assumeIsolated { self?.tabBar.beginEditingList(target) }'])
  for t in ['receive(on:','DispatchQueue','Task','dropFirst','store.']:self.assertNotIn(t,s)
  self.assertIn('view.stopObservingListEditing()',body(self.toolbar,'static func dismantleNSView('));stop=body(self.toolbar,'func stopObservingListEditing()');self.order(stop,['listEditingObservation?.cancel()','listEditingObservation = nil'])
 def test_cells_retain_native_target_and_objectID_match_does_not_use_string_or_uuid(self):
  self.assertIn('tab.menuProvider = { localListMenu(for: target) }',body(self.panel,'private func boardTab('));self.assertIn('keys: [NSManagedObjectID]',self.tabs);self.assertIn('keys.firstIndex(of: target.objectID)',body(self.tabs,'func beginEditingList('))
  f=body(self.l,'public func hasSameObjectID(');self.assertIn('nativeObject.objectID.isEqual(other.nativeObject.objectID)',f);self.assertNotIn('identifier',f)
 def test_existing_cell_consumer_scrolls_then_edits_with_strong_completion_capture(self):
  f=body(self.tabs,'func beginEditingList(');self.order(f,['keys.firstIndex(of: target.objectID)','cell(at: index)','else { return }','window?.makeFirstResponder(nil)','cell.frame.insetBy(dx: -17, dy: 0)','duration: 0.15','OriginalViewAnimation.f_10021ccd4()','animations: { self.f_10009ac24(rect) }','completion: { cell.titleView.beginEditingFromListRequest() }'])
  for t in ['[weak cell]','UUID','target.identifier','store.','pending','DispatchQueue']:self.assertNotIn(t,f)
 def test_label_editor_and_user_unused_color_policy_are_reused_not_reimplemented(self):
  s=body(self.title,'func beginEditingFromListRequest()');self.assertEqual(s.strip(),'{ beginEditing() }')
  store=(ROOT/'replica/Sources/PastoCore/ClipboardStore.swift').read_text();create=body(store,'private func insertPinboard(name:');self.assertIn('let unused = OriginalPinboardColor.allCases.filter { !used.contains($0) }',create);self.assertIn('let palette = unused.isEmpty ? OriginalPinboardColor.allCases : unused',create)
  for r in self.p['unchanged_methods']:
   from native_tab_applier_scope_contract import pre_native_tab_applier
   s=pre_native_tab_applier((ROOT/r['path']).read_text());s=body(s,r['within'])if r['within']else s;self.assertEqual(hashlib.sha256(body(s,r['symbol']).encode()).hexdigest(),r['sha256'])
 def test_missing_target_event_is_dropped_without_replay_or_value_cache_fallback(self):
  f=body(self.tabs,'func beginEditingList(');self.assertIn('else { return }',f);self.assertNotIn('keys.append',f);self.assertNotIn('lastRequest',f);self.assertNotIn('pendingBegin',f)
  declaration=next(s for s in self.ui.splitlines()if 'let beginEditingListSubject ='in s);self.assertNotIn('@Published',declaration);self.assertNotIn('CurrentValueSubject',declaration)
 def test_exact_hunks_historical_method_bodies_and247_source_hashes_are_preserved(self):
  self.assertEqual(len(CHANGES),17);changed=[]
  for p,h in self.base['production'].items():
   if hashlib.sha256(pre_native_tab_source_renderer_bytes(ROOT/p)).hexdigest()!=h:changed.append(p)
   self.assertEqual(hashlib.sha256(pre_native_list_edit_event_bytes(ROOT/p)).hexdigest(),h)
   if p.endswith('.swift'):
    before=(self.ph/'before'/p).read_text();self.assertEqual(pre_native_list_edit_event(before),before)
  for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_native_tab_source_renderer_bytes(ROOT/p)).hexdigest(),h)
  before=(self.ph/'before/replica/Sources/Pasto/UI/PanelViews.swift').read_text();self.assertEqual(pre_native_list_edit_event(body(self.panel,'private func boardButton(')),body(before,'private func boardButton('));self.assertEqual(len(changed),6);self.assertEqual(set(changed),set(self.p['current_sources']));self.assertFalse(self.p['finite_contract_completed']);self.assertFalse(self.p['full_function_migration_verified']);self.assertFalse(self.p['runtime_executed'])

if __name__=='__main__':unittest.main()
