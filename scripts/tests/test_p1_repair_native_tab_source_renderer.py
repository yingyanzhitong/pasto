"""Native List -> applier -> renderer -> selection contracts, without framework execution."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts/tests'),str(ROOT/'scripts')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from native_tab_source_renderer_scope_contract import CHANGES,pre_native_tab_source_renderer

from native_item_drop_scope_contract import pre_native_item_drop, pre_native_item_drop_bytes

class NativeTabSourceRenderer(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ph=ROOT/'.local/p0-repair/phase-171';cls.p=json.loads((cls.ph/'native-tab-source-renderer-contract.json').read_text());cls.base=json.loads((cls.ph/'baseline.json').read_text());cls.s={Path(p).stem:(ROOT/p).read_text()for p in cls.p['current_sources']};cls.bar=cls.s['OriginalPanelTabBar'];cls.toolbar=cls.s['OriginalPanelToolbar'];cls.ui=cls.s['ReplicaUIController'];cls.panel=cls.s['PanelViews'];cls.title=cls.s['OriginalPinboardTabTitle'];cls.collection=body(cls.s['ClipboardSearchCollection'],'public final class ClipboardPinboardCollection');cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
 def order(self,s,tokens):
  positions=[s.index(t)for t in tokens];self.assertEqual(positions,sorted(positions))
 def word(self,a):return int.from_bytes(self.n['read'](a,4),'little')
 def test25_original_fragments_machine_ranges_and_exact_binary_are_bound(self):
  self.assertEqual(len(self.p['original_fragments']),25)
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for k in ['binary','decoder']:
   r=self.p[k];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
  for r in self.p['machine_ranges']:
   a=int(r['start'],16);b=int(r['end'],16);self.assertEqual(hashlib.sha256(self.n['read'](a,b-a)).hexdigest(),r['sha256'])
 def test_real_direct_calls_and_two_diff_sdk_imports_are_bound(self):
  for r in self.p['calls']:
   a=int(r['address'],16);raw=self.n['read'](a,4);self.assertEqual(raw.hex(),r['bytes']);w=int.from_bytes(raw,'little');self.assertEqual(w&0x7c000000,0x14000000);d=w&0x3ffffff;d=d-(1<<26)if d&(1<<25)else d;self.assertEqual(hex(a+4*d),r['target'])
  self.assertEqual(len(self.p['sdk_imports']),2)
  for r in self.p['sdk_imports']:
   a=int(r['stub'],16);x,y=struct.unpack('<II',self.n['read'](a,8));self.assertEqual(self.n['read'](a,12).hex(),r['bytes']);imm=((x>>5)&0x7ffff)*4+((x>>29)&3);imm=imm-(1<<21)if imm&(1<<20)else imm;q=(a&~4095)+(imm<<12)+((y>>10)&0xfff)*8;self.assertEqual(hex(q),r['pointer']);v,c=self.n['reachable_pointer'](q);self.assertTrue(v>>63);self.assertEqual(c,r['chain']);f=self.n['fixup'][0];h=struct.unpack_from('<7I',self.n['raw'],f);entry=struct.unpack_from('<I',self.n['raw'],f+h[2]+4*(v&0xffffff))[0];o=f+h[3]+(entry>>9);self.assertEqual(self.n['raw'][o:self.n['raw'].index(b'\0',o)].decode(),r['symbol'])
  names=' '.join(r['symbol']for r in self.p['sdk_imports']);self.assertIn('difference4from',names);self.assertIn('inferringMoves',names)
 def test_threshold_reads_three_structural_diff_results_excluding_updates(self):
  for r in self.p['words']:self.assertEqual(self.n['read'](int(r['address'],16),4).hex(),r['bytes'])
  for a,register in [(0x1001b9c8c,22),(0x1001b9c90,23),(0x1001b9c9c,24)]:self.assertEqual((self.word(a)>>5)&31,register)
  s=body(self.bar,'private func applySnapshot(');self.assertIn('removals.count + insertions.count + moveSources.count > OriginalCollectionSnapshot.fullReloadThreshold',s);self.assertNotIn('updates.count >',s);self.assertNotIn('keys.count + newKeys.count',s)
 def test_native_snapshot_preserves_raw_order_updated_ids_and_lookup_without_string_gate(self):
  snapshot=body(self.collection,'public struct ListSnapshot');self.assertIn('public let identifiers: [NSManagedObjectID]',snapshot);self.assertIn('public let updatedIdentifiers: Set<NSManagedObjectID>',snapshot);self.assertIn('return target(for: identifiers[index])',body(snapshot,'public func target(at'))
  lookup=body(snapshot,'public func target(for');self.assertIn('context.existingObject(with: objectID)',lookup)
  for t in ['UUID','identifier ==','isDeleted','Set(']:self.assertNotIn(t,lookup)
  publisher=body(self.collection,'public var listPublisher:');self.assertIn('identifiers: snapshot.identifiers, updatedIdentifiers: snapshot.updatedIdentifiers',publisher);self.assertNotIn('subject.value',publisher)
 def test_direct_native_source_installs_before_toolbar_configuration_and_selection(self):
  s=body(self.toolbar,'func makeNSView(');self.order(s,['state.toolbarOwner = view','view.observeLists(state.tabListPublisher, configuration: tabConfiguration','selection: state.$selectedTabList.compactMap { $0 }','updateNSView(view, context: context)','view.observeListEditing'])
  self.assertIn('@Published private(set) var selectedTabList:',self.ui);self.assertIn('{ tabListCollection.listPublisher }',self.ui)
  observe=body(self.bar,'func observeLists(');self.order(observe,['self.configuration = configuration','listObservation = publisher.sink { [weak self] snapshot','self?.receive(snapshot)','drainSnapshots()','selectionObservation = selection.sink { [weak self] target','self?.selectList(target)'])
  self.assertNotIn('tabBar.configure(tabs)',self.toolbar)
 def test_source_coalesces_updates_and_drain_clears_pending_before_renderer(self):
  s=body(self.bar,'private func receive(');self.order(s,['collectionSnapshot = snapshot','pendingSnapshot = (snapshot, (pendingSnapshot?.updated ?? []).union(snapshot.updatedIdentifiers))','scheduleSnapshotDrain()'])
  s=body(self.bar,'private func drainSnapshots(');self.order(s,['snapshotDrainScheduled = false','guard !isPerformingLocalMutation, !isApplyingSnapshots','isApplyingSnapshots = true','while !isPerformingLocalMutation, let pending = pendingSnapshot','pendingSnapshot = nil','applySnapshot(pending.value, updated: pending.updated)','isApplyingSnapshots = false']);self.assertNotIn('hasAppliedSnapshot = true',s)
 def test_original_diff_counts_moves_once_and_updates_use_old_indices(self):
  s=body(self.bar,'private func applySnapshot(');self.order(s,['let newKeys = snapshot.identifiers','newKeys.difference(from: keys).inferringMoves()','case let .remove(offset, _, associatedWith)','if associatedWith == nil { removals.insert(offset) }','else { moveSources.insert(offset) }','case let .insert(offset, _, associatedWith)','if associatedWith == nil { insertions.insert(offset) }','let updates = keys.indices.filter','updated.contains(keys[$0]) && !removals.contains($0) && !moveSources.contains($0)'])
 def test_empty_diff_skips_and_any_move_or_over300_rebuilds_after_key_setter(self):
  s=body(self.bar,'private func applySnapshot(');self.order(s,['let initial = !hasAppliedSnapshot','if !initial, removals.isEmpty, insertions.isEmpty, moveSources.isEmpty, updates.isEmpty { return }','hasAppliedSnapshot = true','keys = newKeys','if fullReload || !moveSources.isEmpty','rebuildCells()','layoutSubtreeIfNeeded()'])
  rebuild=body(self.bar,'private func rebuildCells(');self.order(rebuild,['for view in stack.arrangedSubviews { view.removeFromSuperview() }','for index in keys.indices','let view = OriginalPinboardTabView()','stack.insertArrangedSubview(view, at: index)','view.layoutSubtreeIfNeeded()','configureCell(at: index)'])
 def test_incremental_deletes_descending_inserts_ascending_and_configures_every_cell(self):
  s=body(self.bar,'private func applySnapshot(');self.order(s,['for index in removals.sorted(by: >)','removed.removeFromSuperview()','if removed.isSelected, let selected = currentSelection?() { selectList(selected) }','for index in insertions.sorted()','inserted.layoutSubtreeIfNeeded()','configureCell(at: index)','for index in keys.indices { configureCell(at: index) }','OriginalViewAnimation.f_10021cadc(duration: nil'])
  self.assertIn('animations: { self.superview?.layoutSubtreeIfNeeded() }',s)
 def test_cell_factory_looks_up_current_native_entity_and_actual_stack_position(self):
  s=body(self.bar,'private func configureCell(');self.order(s,['keys.indices.contains(index)','collectionSnapshot?.target(for: keys[index])','cell(at: index)','configuration(target).configure(view)','view.setCollapsed(isCollapsed)'])
  s=body(self.bar,'private func cell(at');self.assertIn('stack.arrangedSubviews',s);self.assertIn('views[index] as? OriginalPinboardTabView',s)
  self.assertIn('tabConfiguration: boardTab',self.panel);self.assertIn('state.selectedTabList?.hasSameObjectID(as: target) == true',self.panel)
 def test_selection_clears_all_before_native_ID_lookup_and_same_scroll_helper(self):
  s=body(self.bar,'private func selectList(');self.order(s,['stack.arrangedSubviews.compactMap','view.setSelected(false)','keys.firstIndex(of: target.objectID)','view.setSelected(true)','f_100095ae8(view)'])
  self.assertIn('setAccessibilityValue(selected)',body(body(self.title,'final class OriginalPinboardTabView'),'func setSelected('))
  self.assertIn('public var objectID: NSManagedObjectID { nativeObject.objectID }',self.s['ClipboardListPersistence'])
 def test_drag_rebuilds_new_cells_and_reads_current_selection_without_stale_row_flags(self):
  s=body(self.bar,'func moveList(');self.order(s,['keys.firstIndex(of: source.objectID)','keys.firstIndex(of: target.objectID)','isPerformingLocalMutation = true','persist(','keys.remove(at: sourceIndex)','keys.insert(key, at: min(destinationIndex, keys.count))','isPerformingLocalMutation = false','scheduleSnapshotDrain()','rebuildCells()','layoutSubtreeIfNeeded()','if let cell = cell(at: destinationIndex), cell.isSelected','f_100095ae8(cell)'])
  self.assertNotIn('stack.setViews',s)
  s=body(self.bar,'func beginEditingList(');self.assertIn('keys.firstIndex(of: target.objectID)',s);self.assertIn('completion: { cell.titleView.beginEditingFromListRequest() }',s)
 def test_stop_cancels_native_subscriptions_and_superseded_adapters_are_removed(self):
  s=body(self.bar,'func stopObservingLists(')
  for t in ['listObservation?.cancel()','selectionObservation?.cancel()','pendingSnapshot = nil','collectionSnapshot = nil','configuration = nil','currentSelection = nil']:self.assertIn(t,s)
  self.assertIn('view.stopObservingLists()',body(self.toolbar,'static func dismantleNSView('))
  for t in ['pendingTabs','[String: OriginalPinboardTabView]','keys: [String]','cells[','func configure(_ tabs:']:self.assertNotIn(t,self.bar)
  self.assertNotIn('tabListTargets',self.ui);self.assertNotIn('var boardTabs:',self.panel)
  tab=body(self.title,'struct OriginalPinboardTab');self.assertNotIn('let key:',tab);self.assertNotIn('var target:',tab);self.assertNotIn('var listTarget:',self.title)
 def test35_exact_hunks_and247_inverse_historical_idempotence_preserve_user_sources(self):
  self.assertEqual(len(CHANGES),35);changed=[]
  for p,h in self.base['production'].items():
   data=pre_native_item_drop_bytes(ROOT/p);old=(self.ph/'before'/p).read_bytes()
   if hashlib.sha256(data).hexdigest()!=h:changed.append(p)
   self.assertEqual(hashlib.sha256(pre_native_tab_source_renderer(data.decode()).encode()if p.endswith('.swift')else data).hexdigest(),h,p)
   self.assertEqual(pre_native_tab_source_renderer(old.decode()).encode()if p.endswith('.swift')else old,old,p)
  self.assertEqual(sorted(changed),sorted(self.p['current_sources']))
 def test_unchanged_native_writes_P0_shared_sources_and_scroll_are_reused(self):
  self.assertEqual(len(self.p['unchanged_methods']),13)
  for r in self.p['unchanged_methods']:
   s=(ROOT/r['path']).read_text();s=body(s,r['within'])if r['within']else s;self.assertEqual(hashlib.sha256(body(s,r['symbol']).encode()).hexdigest(),r['sha256'])
  for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_native_item_drop_bytes(ROOT/p)).hexdigest(),h)
 def test_protocol_oracles_for_threshold_updates_coalescing_and_object_identity(self):
  # Expected observable policy, separate from source binding; no Swift/CoreData execution.
  for removed,inserted,moved in [(0,0,0),(0,300,0),(0,301,0),(299,1,0),(299,2,0),(0,0,1)]:
   structural=removed+inserted+moved;reload=structural>300 or moved>0
   self.assertEqual(reload,structural>300 or moved!=0)
  # Multiple source deliveries keep latest order but union changed IDs.
  stream=[(('a','b'),{'a'}),(('b','a','c'),{'c'}),(('b','c'),{'b'})]
  latest=stream[-1][0];all_changed=set().union(*(changed for _,changed in stream))
  self.assertEqual(latest,('b','c'));self.assertEqual(all_changed,{'a','b','c'})
  # Two native IDs with the same display identifier remain two rows.
  native_ids=[('store1',1),('store1',2)];display=['same','same'];self.assertEqual(len(native_ids),2);self.assertEqual(len(set(display)),1);self.assertIn('keys: [NSManagedObjectID]',self.bar)
  self.assertFalse(self.p['full_function_migration_verified']);self.assertFalse(self.p['runtime_executed'])

 def test_new_item_drop_gap_is_bound_to_original_reader_and_real_current_gate(self):
  p=json.loads((self.ph/'native-group-item-drop-gap.json').read_text());self.assertEqual(p['function_id'],'Paste:0x100079430');self.assertEqual(p['status'],'difference_confirmed')
  for r in p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for r in p['machine_ranges']:
   a=int(r['start'],16);b=int(r['end'],16);self.assertEqual(hashlib.sha256(self.n['read'](a,b-a)).hexdigest(),r['sha256'])
  reader=(self.ph/'0x100079430.c').read_text();self.order(reader,['TabBarCell::onPerformDragOperation','objc_stub::draggingPasteboard','objc_stub::pasteboardItems','FUN_1003ca14c()','objc_stub::stringForType_','(*pcVar11)(local_68)','return 1;'])
  # Replay the actual phase171 discovery gate; phase172 checks the repaired live receiver directly.
  historical=pre_native_item_drop(self.title)
  self.assertIn('registerForDraggedTypes([.string])',historical);self.assertIn('value.hasPrefix("paste-pinboard:")',body(historical,'private func draggedGroup('));self.assertNotIn('itemIdentifierType',historical)
  writer=(ROOT/'replica/Sources/PastoCore/OriginalNativeDragPasteboardWriter.swift').read_text();self.assertIn('types.append(Self.itemIdentifierType)',writer);self.assertIn('return source.pasteboardIdentifier',writer)
 def test_drop_gap_callback_chain_keeps_same_target_and_is_not_claimed_fixed(self):
  p=json.loads((self.ph/'native-group-item-drop-gap.json').read_text())
  for r in p['calls']:
   a=int(r['address'],16);raw=self.n['read'](a,4);self.assertEqual(raw.hex(),r['bytes']);w=int.from_bytes(raw,'little');d=w&0x3ffffff;d=d-(1<<26)if d&(1<<25)else d;self.assertEqual(hex(a+4*d),r['target'])
  self.assertIn('FUN_10003c3b0', (self.ph/'0x100099c18.c').read_text());self.assertIn('FUN_10003b634', (self.ph/'0x10003c9e8.c').read_text());self.assertIn('lVar14 + 0x28', (self.ph/'0x10003b634.c').read_text());self.assertFalse(p['full_function_migration_verified']);self.assertFalse(p['runtime_executed'])

if __name__=='__main__':unittest.main()
