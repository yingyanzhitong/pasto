"""Current ordered-selection and native Stack consumer contracts; no framework execution."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
D=ROOT/'.local/p0-p1-parent-review/2026-11-03-stack-selection'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

class StackSelectionBatch(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.p=json.loads((D/'contract.json').read_text());cls.base=json.loads((D/'baseline.json').read_text());cls.n={}
  exec((ROOT/cls.p['decoder']['path']).read_text().split('selectors=[]',1)[0],cls.n)
  cls.ui=(ROOT/'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
  cls.app=(ROOT/'replica/Sources/Pasto/AppMain.swift').read_text()
  cls.table=(ROOT/'replica/Sources/PastoCore/OriginalStackTableController.swift').read_text()
  cls.aux=(ROOT/'replica/Sources/Pasto/UI/AuxiliaryViews.swift').read_text()
 def order(self,s,tokens):
  positions=[s.index(x)for x in tokens];self.assertEqual(positions,sorted(positions))
 def test_original_fragments_native_image_and_current_production_bindings(self):
  cache={};self.assertEqual(len(self.p['original_fragments']),31)
  for r in self.p['original_fragments']:
   path=ROOT/r['path']
   if path not in cache:cache[path]=source_fragments(path)
   self.assertEqual(cache[path][r['function_id'].split(':')[1]]['sha256'],r['sha256'])
  for k in ['binary','decoder']:self.assertEqual(sha(ROOT/self.p[k]['path']),self.p[k]['sha256'])
  self.assertEqual(len(self.p['current_sources']),12)
  for p,h in self.p['current_sources'].items():self.assertEqual(sha(ROOT/p),h,p)
 def test_complete_ranges_and_all_direct_call_targets(self):
  self.assertEqual(len(self.p['machine_ranges']),31);self.assertEqual(len(self.p['branches']),499)
  for r in self.p['machine_ranges']:
   data=self.n['read'](int(r['address'],16),int(r['end'],16)-int(r['address'],16))
   self.assertEqual(data.hex(),r['bytes']);self.assertEqual(hashlib.sha256(data).hexdigest(),r['sha256'])
  for r in self.p['branches']:
   pc=int(r['pc'],16);w=struct.unpack('<I',self.n['read'](pc,4))[0];self.assertEqual(hex(w),r['word'])
   v=w&0x3ffffff
   if v&(1<<25):v-=1<<26
   self.assertEqual(hex(pc+v*4),r['target'])
 def test_selector_and_import_fixups(self):
  self.assertEqual(len(self.p['selectors']),19);self.assertEqual(len(self.p['imports']),287)
  raw=self.n['raw'];fixup=self.n['fixup'][0];h=struct.unpack_from('<7I',raw,fixup)
  for r in self.p['selectors']+self.p['imports']:
   value,chain=self.n['reachable_pointer'](int(r['pointer'],16));self.assertEqual(chain,r['chain'])
   if 'ordinal'in r:
    self.assertTrue(value>>63);self.assertEqual(value&0xffffff,r['ordinal'])
    entry=struct.unpack_from('<I',raw,fixup+h[2]+4*r['ordinal'])[0];at=fixup+h[3]+(entry>>9)
    self.assertEqual(raw[at:raw.index(b'\0',at)].decode(),r['name'])
   else:
    self.assertFalse(value>>63);at=self.n['base']+(value&((1<<36)-1))
    self.assertEqual(hex(at),r['target']);self.assertEqual(self.n['read'](at,len(r['name'])+1),r['name'].encode()+b'\0')
 def test_real_native_head_is_popped_before_restoration_not_success_gated(self):
  calls=[r for r in self.p['branches']if r['function_id']=='Paste:0x100083e58']
  pcs={r['target']:int(r['pc'],16)for r in calls}
  self.assertLess(pcs['0x10008413c'],pcs['0x100082c68']);self.assertLess(pcs['0x100082c68'],pcs['0x100085a6c'])
  edges={(r['function_id'],r['target'])for r in self.p['branches']}
  self.assertIn(('Paste:0x10008413c','0x100089bec'),edges)
  self.assertIn(('Paste:0x100086960','0x100083df8'),edges)
  self.assertIn(('Paste:0x100086968','0x100083e58'),edges)
 def test_applied_owner_and_explicit_order_feed_restore_inputs(self):
  s=body(self.ui,'private func appliedRestoreItems(orderedIDs:')
  self.order(s,['guard let panel = loadedPanel','collectionFocusTarget as? ReplicaNativeCollectionHost','collection.window === panel',
   'collection.appliedRestoreItems(for: state,','orderedIDs: orderedIDs ?? state.collectionSelectionSnapshot().orderedIDs'])
  native=(ROOT/'replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift').read_text()
  s=body(native,'func appliedRestoreItems(for state:')
  self.order(s,['self.state === state, state.collectionOwner === self','let positions = Dictionary','return orderedIDs.compactMap',
   'guard let index = positions[identifier]','items[index].restoreItem()'])
  self.assertNotIn('sorted',s);self.assertNotIn('Set(',s)
 def test_select_all_preserves_applied_array_and_last_anchor(self):
  s=body(self.ui,'func selectAll()')
  self.order(s,['collectionOwner?.appliedItems(for: self)','cancelPendingNeighborSelection()','let ids = items.map(\.id)',
   'applyOrderedSelection(ids, anchor: ids.last, primary: ids.last)'])
  s=body(self.ui,'private func applyOrderedSelection(')
  self.assertLess(s.index('orderedSelectionIDs = ids'),s.index('selection = Set(ids)'))
  self.assertIn('collectionOwner?.applySelection(state: self)',s)
 def test_copy_paste_and_add_use_the_same_applied_order(self):
  for sig in ['func copySelection(plainTextOnly:','func pasteSelection(plainTextOnly:']:
   s=body(self.ui,sig);self.assertIn('let items = appliedRestoreItems()',s);self.assertNotIn('state.selectedItems',s)
   self.assertNotIn('Array(state.selection)',s);self.assertNotIn('sorted(',s)
  s=body(self.ui,'func addSelectionToStack()')
  self.order(s,['for input in appliedRestoreItems()','state.addToStack(input)','showStack()'])
 def test_capture_uses_fresh_history_first_native_entity_without_value_decode(self):
  s=body(self.ui,'private func captureLatestItemIntoStack()')
  self.order(s,['guard isStackVisible','store.makeListCollection(pinboardID: nil)','let snapshot = collection.value',
   'snapshot.identifiers.first','snapshot.itemReferences[identifier]','reference.requiredRestoreItem(id: identifier)','state.addToStack(input)'])
  for x in ['resolvedItem()','store.items','store.search','asyncAfter']:self.assertNotIn(x,s)
 def test_insert_keeps_repeated_occurrences_and_direction(self):
  s=body(self.ui,'private func insertStackItem(id:')
  self.order(s,['let previousIDs = stackItemIDs','stackRestoreInputs[id] = input','let append = store.preferences.stackReversed',
   'stackIDs.insert(id, at: append ? stackIDs.count : 0)','didInsertNativeSnippet(previousIDs: previousIDs'])
  for x in ['contains(id)','Set(','removeAll']:self.assertNotIn(x,s)
  s=body(self.ui,'@Published var stackIDs:')
  self.assertIn('stackRestoreInputs = stackRestoreInputs.filter { retainedIDs.contains($0.key) }',s)
  self.assertNotIn('stackIDs = Array(Set',s)
 def test_reverse_mutates_array_before_toggling_direction(self):
  s=body(self.ui,'func reverseStack()')
  self.order(s,['f_10008468c(&stackIDs)','store.preferences.stackReversed.toggle()','try store.save()','updateNativeSnippets(stackSnippetInputs)'])
  source=(ROOT/'replica/Sources/PastoCore/OriginalStackFunctions.swift').read_text()
  self.assertIn('func f_10008468c<T>(_ values: inout [T]) { values.reverse() }',source)
  edges={(r['function_id'],r['target'])for r in self.p['branches']};self.assertIn(('Paste:0x1000844fc','0x10008468c'),edges)
 def test_global_paste_captures_native_input_then_pops_before_request_and_closes_empty(self):
  s=body(self.app,'stackPasteHotKey.action =')
  self.order(s,['if NSApp.isActive','NSApp.sendAction','stackItemIDs.first','let input = self.ui.state.stackRestoreItem(for: first)',
   'self.targetApplication = NSWorkspace.shared.frontmostApplication','self.ui.consumeStackHead()',
   '_ = self.paste(ids: [first], plain: false, forceDirect: true, restoreItems: input.map { [$0] })',
   'if self.ui.state.stackItemIDs.isEmpty { self.ui.hideStack() }'])
  self.assertNotIn('if self.paste(',s)
  s=body(self.ui,'func consumeStackHead()')
  self.assertIn('stackIDs.remove(at: index)',s);self.assertNotIn('removeAll',s)
 def test_shortcut_queue_registration_is_not_blocked_by_accessibility_probe(self):
  s=body(self.app,'private func configureStackPasteShortcut()')
  for x in ['ui.isStackVisible','!ui.state.stackItemIDs.isEmpty','!isRecordingHotKey','--no-global-hotkey',
   'pasteboard.name == NSPasteboard.general.name','keyCode: 9, modifiers: .command, identifier: 3']:self.assertIn(x,s)
  self.assertNotIn('accessibilityService',s)
  names=[r['name']for r in self.p['imports']if r['function_id']=='Paste:0x1001eb8d0']
  self.assertIn('_RegisterEventHotKey',names)
 def test_native_handle_precedes_uuid_legacy_fallback_and_is_forwarded(self):
  s=body(self.ui,'func pasteStackItem(id:')
  self.order(s,['state.stackRestoreItem(for: id)','paste(restoreItems: [input], plainTextOnly: plainTextOnly)',
   'paste(ids: [id], plainTextOnly: plainTextOnly)'])
  s=body(self.ui,'var stackSnippetInputs:')
  self.assertIn('stackIDs.compactMap',s);self.assertIn('if let input = stackRestoreInputs[id] { return input }',s)
 def test_arbitrary_row_removal_is_index_based_and_reentrancy_guarded(self):
  s=body(self.table,'public func removeRow(at row:')
  self.order(s,['snippetIDs == expectedIDs','snippetInputs.indices.contains(row)','let revision = snippetsRevision',
   'removeSnippet(expectedIDs, row), snippetsRevision == revision','snippetInputs.remove(at: row)','tableView.removeRows'])
  self.assertNotIn('removeAll',s)
  s=body(self.aux,'struct ReplicaStackTable:')
  self.assertIn('state.stackIDs.remove(at: visibleOffsets[row])',s)
  self.assertIn('visibleOffsets.map({ state.stackIDs[$0] }) == expectedIDs',s)
 def test_row_paste_extension_removes_only_on_true_and_retains_captured_index(self):
  s=body(self.aux,'struct ReplicaStackTable:')
  self.assertIn('if state.controller?.pasteStackItem(id: input.id, plainTextOnly: false) == true',s)
  self.assertIn('controller?.removeRow(at: row, expectedIDs: expectedIDs)',s)
  self.assertIn('controller.makeNativeCell = { [weak controller] input, row in',s)
 def test_close_clears_only_transient_session_and_saved_queue_is_not_reloaded(self):
  s=body(self.ui,'func hideStack()')
  self.order(s,['closingController.close()','stackWindowController = nil','closingController.contentViewController = nil',
   'closingWindow?.contentView = nil','stackWindow = nil','stackTableController = nil',
   'NotificationCenter.default.removeObserver(stackCaptureObserver)','stackCaptureObserver = nil','state.stackIDs.removeAll()'])
  self.assertNotIn('store.save()',s);self.assertNotIn('store.preferences.stackItemIDs',self.ui)
  self.assertIn('@Published var stackIDs: [UUID] = []',self.ui)
 def test_window_key_policy_is_original_false_not_an_unimplemented_stub(self):
  source=(ROOT/'replica/Sources/PastoCore/OriginalStackFunctions.swift').read_text()
  self.assertIn('func f_1000114fc() -> Bool { false }',source)
  self.assertIn('override var canBecomeKey: Bool { OriginalStackFunctions.f_1000114f4() }',self.ui)
  self.assertIn('override var canBecomeMain: Bool { OriginalStackFunctions.f_1000114ec() }',self.ui)
 def test_every_existing_production_and_old_test_file_preserved(self):
  prod={p:h for p,h in self.base['files'].items()if p.startswith('replica/Sources/')};self.assertEqual(len(prod),248)
  self.assertEqual(set(prod),{str(p.relative_to(ROOT))for p in(ROOT/'replica/Sources').rglob('*')if p.is_file()})
  for p,h in self.base['files'].items():self.assertEqual(sha(ROOT/p),h,p)
 def test_only_existing_scope_reused_no_function_count_or_full_claim_increase(self):
  s=json.loads((ROOT/'reports/replica/p0-p1-review-scope-v6.json').read_text());self.assertEqual(s['denominator'],959)
  allowed={r['function_id']for r in s['functions']};ids={r['function_id']for r in self.p['machine_ranges']}
  self.assertEqual(set(self.p['reviewed_in_scope_function_ids']),ids&allowed);self.assertEqual(len(ids&allowed),11)
  self.assertEqual(len(self.p['support_not_added_to_denominator']),20)
  for x in ['production_modified','full_function_migration_verified','compiled','framework_executed']:self.assertFalse(self.p[x])

class StackTraceModels(unittest.TestCase):
 """Python witnesses for ordered queues; not Swift/NSPasteboard execution."""
 def test_duplicate_head_removal_keeps_later_occurrence_and_native_handle(self):
  queue=['A','B','A'];a=object();handles={'A':a,'B':object()};queue.pop(0)
  handles={key:value for key,value in handles.items()if key in set(queue)}
  self.assertEqual(queue,['B','A']);self.assertIs(handles['A'],a)
 def test_arbitrary_remove_uses_occurrence_not_entity_equality(self):
  queue=['A','B','A'];queue.pop(2);self.assertEqual(queue,['A','B'])
 def test_global_failed_restore_still_consumes_one_head(self):
  for success in [False,True]:
   queue=['A','B'];head=queue.pop(0);events=[('pop',head),('restore',success)]
   self.assertEqual(queue,['B']);self.assertEqual(events[0],('pop','A'))
 def test_direction_and_multi_add_order_are_not_deduplicated(self):
  for append,expected in [(False,['C','A','B','A']),(True,['A','B','A','C'])]:
   queue=[]
   for value in ['A','B','A','C']:queue.insert(len(queue)if append else 0,value)
   self.assertEqual(queue,expected)
  queue=['A','B','A','C'];queue.reverse();self.assertEqual(queue,['C','A','B','A'])
 def test_ordered_selection_not_visible_array_or_set_drives_output(self):
  applied={'A':'native-A','B':'native-B','C':'native-C'};selection=['C','A']
  self.assertEqual([applied[x]for x in selection if x in applied],['native-C','native-A'])
 def test_row_paste_extension_failure_keeps_queue(self):
  queue=['A','B','A'];success=False
  if success:queue.pop(2)
  self.assertEqual(queue,['A','B','A'])

if __name__=='__main__':unittest.main()
