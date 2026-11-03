"""Native all-List tab input and selection contracts; static source/Mach-O checks only."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts/tests'),str(ROOT/'scripts')]
from function_ledger import source_fragments
from native_list_reorder_scope_contract import pre_native_list_reorder_bytes
from native_list_name_color_scope_contract import pre_native_list_name_color
from test_offline_p0_contracts import body
from native_tab_list_delivery_scope_contract import CHANGES,pre_native_tab_list_delivery,pre_native_tab_list_delivery_bytes
class NativeTabListDelivery(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ph=ROOT/'.local/p0-repair/phase-164';cls.p=json.loads((cls.ph/'native-tab-delivery-contract.json').read_text());cls.base=json.loads((cls.ph/'baseline.json').read_text());cls.sources={Path(p).stem:(ROOT/p).read_text()for p in cls.p['current_sources']};cls.lists=cls.sources['ClipboardListPersistence'];cls.persistence=cls.sources['ClipboardPersistence'];cls.store=cls.sources['ClipboardStore'];cls.state=cls.sources['ReplicaUIController'];cls.panel=cls.sources['PanelViews'];cls.collection=body(cls.sources['ClipboardSearchCollection'],'public final class ClipboardPinboardCollection');cls.snapshot=body(cls.collection,'public struct ListSnapshot');cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
 def order(self,s,tokens):
  positions=[s.index(t)for t in tokens];self.assertEqual(positions,sorted(positions))
 def test_twenty_original_fragments_decoder_binary_and_four_complete_machine_ranges(self):
  self.assertEqual(len(self.p['original_fragments']),20)
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for k in ['binary','decoder']:
   r=self.p[k];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
  for r in self.p['machine_ranges']:self.assertEqual(hashlib.sha256(self.n['read'](int(r['start'],16),int(r['end'],16)-int(r['start'],16))).hexdigest(),r['sha256'])
 def test_true_protocol_slots_keep_tab_allLists_menu_type2_and_identifier_lookup_distinct(self):
  for r in self.p['pointers']:
   a=int(r['address'],16);self.assertEqual(self.n['read'](a,8).hex(),r['bytes']);v,c=self.n['reachable_pointer'](a);self.assertFalse(v>>63);self.assertEqual(c,r['chain']);self.assertEqual(hex(self.n['base']+(v&((1<<36)-1))),r['target'])
  self.assertEqual([r['target']for r in self.p['pointers']],['0x100367f78','0x10036805c','0x100368060']);self.assertEqual(body(self.lists,'func tabListRequest()').strip(),'{ PastoListEntity.listFetchRequest() }');self.assertNotIn('predicate',body(self.lists,'func tabListRequest()'));self.assertIn('request.predicate = NSPredicate(format: "rawType == %d", 2)',body(self.lists,'func pinboardRequest()'))
 def test_actual_objectID_index_clamp_and_optional_lookup_calls_are_bound(self):
  for r in self.p['calls']:
   a=int(r['address'],16);w=int.from_bytes(self.n['read'](a,4),'little');self.assertEqual(w.to_bytes(4,'little').hex(),r['bytes']);self.assertEqual(w&0xfc000000,0x94000000);d=w&0x3ffffff;d=d-(1<<26)if d&(1<<25)else d;self.assertEqual(hex(a+4*d),r['target'])
  for r in self.p['words']:self.assertEqual(self.n['read'](int(r['address'],16),4).hex(),r['bytes'])
  self.assertEqual(self.n['read'](0x10003a6ec,4).hex(),'e80600f1');self.assertEqual(self.n['read'](0x10003a6f8,4).hex(),'16b1999a')
 def test_snapshot_keeps_raw_identifier_count_and_optional_lookup_positions(self):
  s=self.snapshot;self.assertIn('public let identifiers: [NSManagedObjectID]',s);self.assertIn('public var count: Int { identifiers.count }',s);self.assertIn('identifiers.firstIndex { $0.isEqual(target.nativeObject.objectID) }',s)
  lookup=body(s,'public func target(at index:');self.order(lookup,['identifiers.indices.contains(index)','return target(for: identifiers[index])']);self.assertNotIn('UUID',lookup);self.assertIn('context.existingObject(with: objectID)',body(s,'public func target(for'));self.assertIn('identifiers.indices.compactMap { target(at: $0) }',s)
  publisher=body(self.collection,'public var listPublisher:');self.assertIn('ListSnapshot(identifiers: snapshot.identifiers, updatedIdentifiers: snapshot.updatedIdentifiers, context: context)',publisher);self.assertNotIn('subject.value',publisher);self.assertNotIn('receive(on:',publisher);self.assertNotIn('Task',publisher)
 def test_native_lookup_fetches_by_string_without_a_value_cache_or_early_limit(self):
  lookup=body(self.lists,'func tabList(identifier:');self.order(lookup,['PastoListEntity.listFetchRequest()','request.predicate = NSPredicate(format: "identifier == %@", identifier)','return (try? context.fetch(request))?.first'])
  for t in ['fetchLimit','fetchOffset','UUID','Pinboard','throw']:self.assertNotIn(t,lookup)
  wrapper=body(self.persistence,'func tabListTarget(identifier:');self.order(wrapper,['context.performAndWait','lists.tabList(identifier: identifier)','ClipboardListTarget(object: $0)']);self.assertIn('String._unconditionallyBridgeFromObjectiveC',body(self.lists,'public struct ClipboardListTarget'))
 def test_tab_factory_and_string_content_adapter_reuse_same_context_and_real_requests(self):
  make=body(self.persistence,'func makeTabListCollection()');self.order(make,['context.performAndWait','ClipboardPinboardCollection(context: context, request: lists.tabListRequest())']);self.assertNotIn('NSManagedObjectContext(',make);self.assertIn('persistence.makeListCollection(identifier: identifier)',body(self.store,'public func makeListCollection(identifier:'))
  source=body(self.state,'private func installListCollectionSource()');self.assertIn('store.makeListCollection(identifier: selectedCollectionIdentifier)',source);self.assertNotIn('pinboardID: pinboardID',source)
 def test_initial_list_snapshot_and_default_reconciliation_precede_identifier_subscription(self):
  init=body(body(self.state,'final class ReplicaUIState'),'init(store:');self.order(init,['installTabListDelivery()','installListSelectionDelivery()','installSearchQueryDelivery()'])
  f=body(self.state,'private func installTabListDelivery()');self.order(f,['let snapshot = tabListCollection.listSnapshot','tabListSnapshot = snapshot','reconcileTabListSelection()','tabListCollection.listPublisher.dropFirst()']);self.assertIn('self.tabListSnapshot = snapshot',f);self.assertNotIn('tabListTargets',f);self.assertNotIn('DispatchQueue',f);self.assertNotIn('removeDuplicates',f)
 def test_selectedID_survival_reindexes_and_missingID_clamps_raw_order_without_collapsing_holes(self):
  f=body(self.state,'private func reconcileTabListSelection()');self.order(f,['guard let selected = selectedTabList, let previousIndex = selectedTabIndex','selectListIdentifier(ClipboardStore.historyListIdentifier, force: false)','guard let snapshot = tabListSnapshot','if let index = snapshot.index(of: selected)','selectedTabIndex = index','let index = min(previousIndex, snapshot.count - 1)','guard let target = snapshot.target(at: index) else { return }','selectListIdentifier(target.identifier, force: false)'])
  self.assertNotIn('tabListTargets.count',f);self.assertNotIn('store.pinboards',f);self.assertNotIn('compactMap',f)
 def test_identifier_delivery_uses_native_context_and_keeps_published_selection_before_index_update(self):
  f=body(self.state,'private func installListSelectionDelivery()');self.order(f,['guard let self, let identifier','self.store.tabListTarget(identifier: identifier)','OriginalCollectionListContext.f_1003b80f0(identifier: target.identifier','rawType: target.rawType','self.selectedTabList = target','self.applySelectedList(id)','self.selectedTabIndex = self.tabListSnapshot?.index(of: target)'])
  self.assertIn('self.selectedCollectionIdentifier = identifier',f)
  for t in ['store.pinboards','removeDuplicates','DispatchQueue','guard let id = UUID']:self.assertNotIn(t,f)
  force=body(self.state,'private func selectListIdentifier(');self.order(force,['current == identifier, force','listIdentifierChanges.send(nil)','listIdentifierChanges.send(identifier)'])
 def test_cache_guard_and_manual_post_delete_history_override_do_not_cancel_native_neighbor_selection(self):
  normalize=body(self.state,'func normalizeSelection()');self.assertNotIn('if let pinboardID, !store.pinboards.contains',normalize);self.assertNotIn('selectListIdentifier',normalize)
  confirm=body(self.state,'func confirmPinboardRemoval()');self.assertIn('try store.removeList(target)',confirm);self.assertNotIn('state.chooseBoard(nil)',confirm);self.assertIn('state.pinboardDeletionError = error.localizedDescription',confirm)
 def test_panel_tabs_render_live_native_order_and_native_identifiers_without_synthetic_history_row(self):
  tabs=body(self.panel,'private func boardTab(');self.assertIn('tabConfiguration: boardTab',self.panel);self.assertIn('boardButton(target.name, board: board, target: target)',tabs)
  for t in ['store.pinboards','var history','sortOrder <','preferences.historyTitle']:self.assertNotIn(t,tabs)
  button=body(self.panel,'private func boardButton(');self.assertNotIn('let key =',button);self.assertIn('isSelected: state.selectedTabList?.hasSameObjectID(as: target) == true',button);self.assertEqual(button.count('state.chooseList(identifier: target.identifier)'),2);self.assertIn('state.beginEditingListSubject.send(target)',body(self.panel,'private func requestTabRename('))
 def test_keyboard_wraps_raw_list_snapshot_and_skips_unresolved_target(self):
  f=body(self.state,'func switchBoard(_ offset:');self.order(f,['guard let snapshot = tabListSnapshot','let current = snapshot.index(of: selected)','switch offset','snapshot.count) % snapshot.count','guard let target = snapshot.target(at: next) else { return }','chooseList(identifier: target.identifier)']);self.assertNotIn('store.pinboards',f);self.assertNotIn('[nil]',f)
 def test_fifteen_previous_methods_six_files_and_seventeen_exact_deltas_preserve_user_state(self):
  self.assertEqual(len(self.p['unchanged_methods']),15)
  for r in self.p['unchanged_methods']:
   s=pre_native_list_name_color((ROOT/r['path']).read_text());s=body(s,'public final class ClipboardPinboardCollection')if r['within']else s;self.assertEqual(hashlib.sha256(body(s,r['symbol']).encode()).hexdigest(),r['sha256'])
  self.assertEqual(len(CHANGES),17);changed=[]
  for p,h in self.base['production'].items():
   if hashlib.sha256(pre_native_list_reorder_bytes(ROOT/p)).hexdigest()!=h:changed.append(p)
   self.assertEqual(hashlib.sha256(pre_native_tab_list_delivery_bytes(ROOT/p)).hexdigest(),h)
  self.assertEqual(set(changed),set(self.p['current_sources']));self.assertEqual(len(changed),6)
 def test_native_tab_parent_does_not_get_completion_credit_before_remaining_consumers(self):
  menu=body(self.panel,'private func localListMenu(');self.assertIn('state.controller?.removePinboard(target)',menu);self.assertIn('state.moveList(identifier: String(value.dropFirst(15)), to: target)',self.panel);self.assertIn('state.pendingPinboardDeletion = target',body(self.state,'func removePinboard(_ target:'));self.assertNotIn('store.pinboards.contains',body(self.state,'func removePinboard(_ target:'));self.assertFalse(self.p['finite_contract_completed']);self.assertFalse(self.p['full_function_migration_verified']);self.assertFalse(self.p['runtime_executed']);self.assertEqual(self.p['new_difference_records'],0)
if __name__=='__main__':unittest.main()
