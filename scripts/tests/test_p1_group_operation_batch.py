"""Current local group operation contracts; no CoreData or application execution."""
from pathlib import Path
import hashlib,json,re,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
D=ROOT/'.local/p0-p1-parent-review/2026-11-03-groups'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

class GroupOperationBatch(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.p=json.loads((D/'contract.json').read_text());cls.base=json.loads((D/'baseline.json').read_text());cls.n={}
  exec((ROOT/cls.p['decoder']['path']).read_text().split('selectors=[]',1)[0],cls.n)
  cls.lists=(ROOT/'replica/Sources/PastoCore/ClipboardListPersistence.swift').read_text()
  cls.store=(ROOT/'replica/Sources/PastoCore/ClipboardStore.swift').read_text()
  cls.ui=(ROOT/'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
  cls.panel=(ROOT/'replica/Sources/Pasto/UI/PanelViews.swift').read_text()
 def order(self,s,tokens):
  indices=[s.index(x)for x in tokens];self.assertEqual(indices,sorted(indices))
 def test_original_fragments_binary_decoder_and_current_sources_fresh(self):
  cache={};self.assertEqual(len(self.p['original_fragments']),20)
  for r in self.p['original_fragments']:
   path=ROOT/r['path']
   if path not in cache:cache[path]=source_fragments(path)
   self.assertEqual(cache[path][r['function_id'].split(':')[1]]['sha256'],r['sha256'])
  for k in ['binary','decoder']:self.assertEqual(sha(ROOT/self.p[k]['path']),self.p[k]['sha256'])
  self.assertEqual(len(self.p['current_sources']),13)
  for p,h in self.p['current_sources'].items():self.assertEqual(sha(ROOT/p),h,p)
 def test_complete_machine_ranges_and_all_direct_branches(self):
  self.assertEqual(len(self.p['machine_ranges']),20);self.assertEqual(len(self.p['branches']),394)
  for r in self.p['machine_ranges']:
   data=self.n['read'](int(r['address'],16),int(r['end'],16)-int(r['address'],16))
   self.assertEqual(data.hex(),r['bytes']);self.assertEqual(hashlib.sha256(data).hexdigest(),r['sha256'])
  for r in self.p['branches']:
   pc=int(r['pc'],16);w=struct.unpack('<I',self.n['read'](pc,4))[0];self.assertEqual(hex(w),r['word'])
   v=w&0x3ffffff
   if v&(1<<25):v-=1<<26
   self.assertEqual(hex(pc+v*4),r['target'])
 def test_native_selector_and_import_fixups(self):
  self.assertEqual(len(self.p['selectors']),42);self.assertEqual(len(self.p['imports']),224)
  raw=self.n['raw'];fixup=self.n['fixup'][0];h=struct.unpack_from('<7I',raw,fixup)
  for r in self.p['selectors']+self.p['imports']:
   value,chain=self.n['reachable_pointer'](int(r['pointer'],16));self.assertEqual(chain,r['chain'])
   if 'ordinal'in r:
    self.assertTrue(value>>63);self.assertEqual(value&0xffffff,r['ordinal'])
    e=struct.unpack_from('<I',raw,fixup+h[2]+4*r['ordinal'])[0];at=fixup+h[3]+(e>>9)
    self.assertEqual(raw[at:raw.index(b'\0',at)].decode(),r['name'])
   else:
    self.assertFalse(value>>63);at=self.n['base']+(value&((1<<36)-1))
    self.assertEqual(hex(at),r['target']);self.assertEqual(self.n['read'](at,len(r['name'])+1),r['name'].encode()+b'\0')
 def test_actual_reorder_installed_callbacks_and_two_weak_reads(self):
  self.assertEqual({r['target']for r in self.p['installed_callbacks']},{'0x10036c25c','0x10036c290','0x10036cbd4'})
  for r in self.p['installed_callbacks']:
   pc=int(r['address'],16);data=self.n['read'](pc,8);self.assertEqual(data.hex(),r['bytes']);a,b=struct.unpack('<2I',data)
   v=((a>>5)&0x7ffff)*4+((a>>29)&3)
   if v&(1<<20):v-=1<<21
   self.assertEqual(hex((pc&~4095)+(v<<12)+((b>>10)&4095)),r['target'])
  for fid,pc in [('Paste:0x1003695b4','0x1003695d4'),('Paste:0x10036964c','0x100369670')]:
   self.assertEqual([r['pc']for r in self.p['imports']if r['function_id']==fid and r['name']=='_swift_weakLoadStrong'],[pc])
  edges={(r['function_id'],r['target'])for r in self.p['branches']}
  for pair in [('Paste:0x10036c25c','0x100369500'),('Paste:0x10036c290','0x1003695b4'),('Paste:0x10036cbd4','0x10036964c')]:self.assertIn(pair,edges)
 def test_original_palette_matches_all_eight_current_codes(self):
  p=self.p['palette'];data=self.n['read'](int(p['address'],16),64);self.assertEqual(data.hex(),p['bytes'])
  source=(ROOT/'replica/Sources/PastoCore/OriginalPinboardColor.swift').read_text()
  s=body(source,'public var canonicalColorCode:')
  values=[int(x,16)for x in re.findall(r'return (0x[0-9a-f]+)',s)]
  self.assertEqual(values,list(struct.unpack('<8Q',data)));self.assertEqual(values,p['values'])
 def test_create_permanent_id_error_does_not_skip_attributes_and_type(self):
  s=body(self.lists,'func insertPinboard(identifier:')
  self.order(s,['let list = PastoListEntity(context: context)','list.setValue(identifier, forKey: "identifier")',
   'list.setValue(name, forKey: "name")','try? context.obtainPermanentIDs(for: [list])','let attributes = try? encodeAttributes()',
   'list.setValue(attributes, forKey: "rawAttributes")','list.setValue(Int64(2), forKey: "rawType")','return (list, attributes)'])
  names=[r['name']for r in self.p['selectors']if r['function_id']=='Paste:0x100368560']
  self.assertEqual(names,['initWithContext:','setIdentifier:','setName:','obtainPermanentIDsForObjects:error:','setRawAttributes:','setRawType:'])
 def test_rename_callback_then_fresh_name_compare_and_set(self):
  s=body(self.lists,'func updateName(on list:')
  self.assertEqual(s.count('list.value(forKey: "name")'),2)
  self.order(s,['var value = String._unconditionallyBridgeFromObjectiveC','update(&value)','let current = String._unconditionallyBridgeFromObjectiveC','if current != value','list.setValue(value, forKey: "name")'])
  self.assertEqual([r['name']for r in self.p['selectors']if r['function_id']=='Paste:0x10036c448'],['name','name','setName:'])
  p=(ROOT/'replica/Sources/PastoCore/OriginalPinboardTitle.swift').read_text()
  s=body(p,'public static func normalizedRename(')
  self.assertIn('value.isEmpty ? String(localized: OriginalPreviewLocalization.f_1001c6aa4()) : value',s)
  self.assertNotIn('trimmingCharacters',s)
 def test_color_only_decoded_pinboard_and_changed_code_writes_optional_encoded_data(self):
  s=body(self.lists,'func updateColor(on list:')
  self.order(s,['guard case let .pinboard(old)?','var value = old','update(&value)','guard old != value else { return }','try? OriginalPinboardAttributes.encoded(colorCode: value)','list.setValue(attributes, forKey: "rawAttributes")'])
  self.assertEqual(s.count('list.value(forKey: "rawAttributes")'),1)
  self.assertNotIn('rawType',s)
  names=[r['name']for r in self.p['selectors']if r['function_id']=='Paste:0x10036c614']
  self.assertEqual(names,['rawAttributes','setRawAttributes:'])
 def test_store_rename_and_color_keep_native_target_inside_transaction(self):
  for sig,action in [('public func renameList(','lists.updateName(on: target.nativeObject)'),('public func updateListColor(','lists.updateColor(on: target.nativeObject)')]:
   s=body(self.store,sig)
   self.order(s,['try mutateInTransaction','lists.retainNativeList(target.nativeObject)',action,'projectNativeList(target, into: &state)'])
   self.assertNotIn('tabListTarget(',s);self.assertNotIn('list(identifier:',s)
 def test_reorder_uses_native_equality_current_order_and_changed_positions_only(self):
  s=body(self.lists,'func moveList(_ target:')
  self.order(s,['NSSortDescriptor(key: "metadata.index", ascending: true)','context.performAndWait','(try? context.fetch(request)) ?? []',
   'ordered.firstIndex(where: { $0.isEqual(target) })','ordered.move(fromOffsets: IndexSet(integer: source), toOffset: offset)',
   'let background = NSManagedObjectContext','for (index, object) in ordered.enumerated()','if current != Int64(index)',
   'setValue(Int64(index), forKey: "index")','background.performAndWait','background.object(with: object.objectID)',
   'list.willChangeValue(forKey: "metadata")','list.didChangeValue(forKey: "metadata")'])
 def test_reorder_observer_install_save_rollback_and_removal_order(self):
  s=body(self.lists,'func moveList(_ target:')
  self.order(s,['let observer = NotificationCenter.default.addObserver','object: background, queue: nil','guard let context = self?.context',
   'context.performAndWait { [weak self] in','self?.context.mergeChanges(fromContextDidSave: notification)',
   'guard background.hasChanges','try OriginalObjCExceptionBridge.f_1002ff9c8 { try background.save() }',
   'background.rollback()','Self.reorderDiagnostics','NotificationCenter.default.removeObserver(observer)','return ordered'])
  self.assertNotIn('Task',s);self.assertNotIn('asyncAfter',s)
 def test_local_delete_detaches_owner_then_deletes_unowned_historyless_items_then_list(self):
  s=body(self.lists,'func removePinboard(_ list:')
  self.order(s,['if let context = list.managedObjectContext','(try? context.fetch(itemRequest(for: list))) ?? []','for item in items',
   'int64Value == 2','owner.isEqual(list)','item.setValue(nil, forKey: "list")',
   'item.value(forKey: "timestamp") == nil, item.value(forKey: "list") == nil','item.managedObjectContext?.delete(item)',
   'list.managedObjectContext?.delete(list)','return items'])
  self.assertNotIn('context.save()',s);self.assertNotIn('pinboardIDs',s)
 def test_actual_UI_actions_use_selected_native_targets(self):
  self.assertIn('try? state.store.renameList(target, rawName: value)',self.panel)
  s=body(self.panel,'private func localListMenu(for target:')
  self.assertIn('state.store.updateListColor(target, colorCode: color.canonicalColorCode)',s)
  self.assertIn('state.controller?.removePinboard(target)',s)
  s=body(self.ui,'func confirmPinboardRemoval()')
  self.order(s,['guard let target = state.pendingPinboardDeletion','try store.removeList(target)','cancelPinboardRemoval()'])
  s=body(self.store,'public func moveList(_ target:')
  self.assertIn('lists.moveList(target.nativeObject, toOffset: offset)',s)
 def test_selected_displayed_order_and_local_move_even_after_transaction_error(self):
  s=body(self.ui,'func moveList(identifier:')
  self.assertIn('try? self.store.moveList(source, toOffset: offset)',s)
  tab=(ROOT/'replica/Sources/Pasto/UI/OriginalPanelTabBar.swift').read_text();s=body(tab,'func moveList(_ source:')
  self.order(s,['keys.firstIndex(of: source.objectID)','keys.firstIndex(of: target.objectID)','isPerformingLocalMutation = true',
   'persist(sourceIndex < destinationIndex ? destinationIndex + 1 : destinationIndex)','keys.remove(at: sourceIndex)',
   'keys.insert(key, at: min(destinationIndex, keys.count))','isPerformingLocalMutation = false','scheduleSnapshotDrain()'])
 def test_user_unused_palette_and_inline_delete_adaptations_are_preserved(self):
  s=body(self.store,'private func insertPinboard(name:')
  self.assertIn('let unused = OriginalPinboardColor.allCases.filter { !used.contains($0) }',s)
  self.assertIn('let palette = unused.isEmpty ? OriginalPinboardColor.allCases : unused',s)
  s=body(self.ui,'func removePinboard(_ target:')
  self.assertIn('state.pendingPinboardDeletion = target',s);self.assertIn('if store.localListMenuState(target).isEmpty',s)
  code=re.sub(r'//[^\n]*','',s)
  self.assertNotIn('runModal',code);self.assertNotIn('NSAlert',code)
  self.assertIn('state.pinboardDeletionError = error.localizedDescription',body(self.ui,'func confirmPinboardRemoval()'))
 def test_empty_count_errors_and_no_context_take_empty_branch(self):
  s=body(self.lists,'func menuState(for list:')
  self.assertIn('guard let context = list.managedObjectContext else { return (rawType, true) }',s)
  self.assertIn('(try? context.count(for: request)) ?? 0',s);self.assertIn('return (rawType, count == 0)',s)
 def test_entire_existing_production_and_all_old_inputs_are_unchanged(self):
  prod={p:h for p,h in self.base['files'].items()if p.startswith('replica/Sources/')}
  self.assertEqual(len(prod),248)
  actual={str(p.relative_to(ROOT))for p in(ROOT/'replica/Sources').rglob('*')if p.is_file()}
  self.assertEqual(actual,set(prod))
  for p,h in self.base['files'].items():self.assertEqual(sha(ROOT/p),h,p)
 def test_reuse_does_not_inflate_scope_repair_counts_or_full_migration(self):
  scope=json.loads((ROOT/'reports/replica/p0-p1-review-scope-v6.json').read_text())
  self.assertEqual(scope['denominator'],959);allowed={r['function_id']for r in scope['functions']}
  self.assertEqual(len(self.p['reviewed_in_scope_function_ids']),8)
  self.assertEqual(set(self.p['reviewed_in_scope_function_ids']),{r['function_id']for r in self.p['machine_ranges']} & allowed)
  self.assertEqual(len(self.p['support_not_added_to_denominator']),12)
  for k in ['production_modified','full_function_migration_verified','compiled','framework_executed']:self.assertFalse(self.p[k])

class GroupOperationTraceModels(unittest.TestCase):
 """Finite operation traces only; not CoreData/Swift execution."""
 def test_rename_fresh_read_can_avoid_redundant_set_after_reentrant_callback(self):
  events=[];name=['old'];value=name[0];events.append('read-first')
  value='new';name[0]='new';events.append('callback');current=name[0];events.append('read-second')
  if current!=value:events.append('set')
  self.assertEqual(events,['read-first','callback','read-second'])
 def test_delete_history_or_other_owner_survives_only_group_orphan_is_deleted(self):
  for timestamp,owner,expected in [(True,'target',False),(False,'target',True),(False,'other',False),(False,None,True)]:
   if owner=='target':owner=None
   self.assertEqual(not timestamp and owner is None,expected)
 def test_nil_outer_owner_skips_schedule_and_nil_inner_owner_skips_merge(self):
  for outer,inner,expected in [(False,False,[]),(False,True,[]),(True,False,['schedule']),(True,True,['schedule','merge'])]:
   events=[]
   if outer:
    events.append('schedule')
    if inner:events.append('merge')
   self.assertEqual(events,expected)
 def test_unused_colors_exhaust_then_return_to_full_palette(self):
  palette=list(range(8))
  for used in [set(),{0},set(range(7)),set(range(8))]:
   unused=[x for x in palette if x not in used];choices=unused or palette
   self.assertEqual(set(choices),set(palette)-used if len(used)<8 else set(palette))

if __name__=='__main__':unittest.main()
