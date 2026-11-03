"""Original all-List move, context/KVO/save order, and current consumers; static checks only."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts/tests'),str(ROOT/'scripts')]
from function_ledger import source_fragments
from native_list_edit_event_scope_contract import pre_native_list_edit_event,pre_native_list_edit_event_bytes
from test_offline_p0_contracts import body
from native_list_reorder_scope_contract import CHANGES,pre_native_list_reorder,pre_native_list_reorder_bytes

from native_tab_source_renderer_scope_contract import pre_native_tab_source_renderer, pre_native_tab_source_renderer_bytes

class NativeListReorder(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ph=ROOT/'.local/p0-repair/phase-167';cls.p=json.loads((cls.ph/'native-list-reorder-contract.json').read_text());cls.base=json.loads((cls.ph/'baseline.json').read_text());cls.s={Path(p).stem:(ROOT/p).read_text()for p in cls.p['current_sources']};cls.l=cls.s['ClipboardListPersistence'];cls.move=body(cls.l,'func moveList(_ target:');cls.ui=cls.s['ReplicaUIController'];cls.store=cls.s['ClipboardStore'];cls.panel=cls.s['PanelViews'];cls.title=cls.s['OriginalPinboardTabTitle'];cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
 def order(self,s,tokens):
  pos=[s.index(t)for t in tokens];self.assertEqual(pos,sorted(pos))
 def test_original_fragments_and_complete_machine_ranges_are_bound(self):
  self.assertEqual(len(self.p['original_fragments']),26)
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for k in ['binary','decoder']:
   r=self.p[k];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
  self.assertEqual(len(self.p['machine_ranges']),9)
  for r in self.p['machine_ranges']:
   a=int(r['start'],16);b=int(r['end'],16);self.assertEqual(hashlib.sha256(self.n['read'](a,b-a)).hexdigest(),r['sha256'])
 def test_actual_write_and_context_provider_slots_and119_calls(self):
  for r in self.p['pointers']:
   a=int(r['address'],16);v,c=self.n['reachable_pointer'](a);self.assertEqual(self.n['read'](a,8).hex(),r['bytes']);self.assertFalse(v>>63);self.assertEqual(c,r['chain']);self.assertEqual(hex(self.n['base']+(v&((1<<36)-1))),r['target'])
  self.assertEqual([r['target']for r in self.p['pointers']],['0x100368a10','0x10035de70','0x10035de90']);self.assertEqual(len(self.p['calls']),119)
  for r in self.p['calls']:
   a=int(r['address'],16);w=int.from_bytes(self.n['read'](a,4),'little');self.assertEqual(w.to_bytes(4,'little').hex(),r['bytes']);self.assertEqual(w&0xfc000000,0x94000000);d=w&0x3ffffff;d=d-(1<<26)if d&(1<<25)else d;self.assertEqual(hex(a+4*d),r['target'])
 def test_sdk_move_performAndWait_and_error_release_are_true_imports(self):
  for r in self.p['sdk_imports']:
   a=int(r['stub'],16);x,y=struct.unpack('<II',self.n['read'](a,8));self.assertEqual(self.n['read'](a,12).hex(),r['bytes']);imm=((x>>5)&0x7ffff)*4+((x>>29)&3);imm=imm-(1<<21)if imm&(1<<20)else imm;q=(a&~4095)+(imm<<12)+((y>>10)&0xfff)*8;self.assertEqual(hex(q),r['pointer']);v,c=self.n['reachable_pointer'](q);self.assertTrue(v>>63);self.assertEqual(c,r['chain']);ordinal=v&0xffffff;self.assertEqual(ordinal,r['ordinal']);f=self.n['fixup'][0];h=struct.unpack_from('<7I',self.n['raw'],f);self.assertEqual(h[5],1);entry=struct.unpack_from('<I',self.n['raw'],f+h[2]+4*ordinal)[0];o=f+h[3]+(entry>>9);symbol=self.n['raw'][o:self.n['raw'].index(b'\0',o)].decode();self.assertEqual(symbol,r['symbol'])
  self.assertIn('SwiftUIE4move11fromOffsets8toOffset',self.p['sdk_imports'][0]['symbol']);self.assertIn('CoreDataE14performAndWait',self.p['sdk_imports'][1]['symbol']);self.assertEqual(self.p['sdk_imports'][2]['symbol'],'_swift_errorRelease')
 def test_real_selectors_and_metadata_key_and_save_error_machine_blocks(self):
  for r in self.p['selectors']:
   a=int(r['stub'],16);x,y=struct.unpack('<II',self.n['read'](a,8));self.assertEqual(self.n['read'](a,8).hex(),r['bytes']);imm=((x>>5)&0x7ffff)*4+((x>>29)&3);imm=imm-(1<<21)if imm&(1<<20)else imm;q=(a&~4095)+(imm<<12)+((y>>10)&0xfff)*8;v,c=self.n['reachable_pointer'](q);self.assertEqual(hex(q),r['pointer']);self.assertEqual(c,r['chain']);t=self.n['base']+(v&((1<<36)-1));self.assertEqual(self.n['read'](t,150).split(b'\0')[0].decode(),r['selector'])
  for r in self.p['words']:self.assertEqual(self.n['read'](int(r['address'],16),4).hex(),r['bytes'])
  # These actual MOV/MOVK words construct the KVO key, not the nested index key.
  value=0
  for a in [0x100369548,0x10036954c,0x100369550,0x100369554]:
   w=int.from_bytes(self.n['read'](a,4),'little');shift=((w>>21)&3)*16;value=(value&~(0xffff<<shift))|(((w>>5)&0xffff)<<shift)
  self.assertEqual(value.to_bytes(8,'little'),b'metadata')
  for r in self.p['strings']:self.assertEqual(self.n['read'](int(r['address'],16),r['length']).decode(),r['text'])
 def test_full_native_List_fetch_find_and_sdk_move_precede_background_creation(self):
  s=self.move;self.order(s,['PastoListEntity.listFetchRequest()','NSSortDescriptor(key: "metadata.index", ascending: true)','context.performAndWait { ordered = (try? context.fetch(request)) ?? [] }','guard let source = ordered.firstIndex(where: { $0.isEqual(target) }) else { return [] }','ordered.move(fromOffsets: IndexSet(integer: source), toOffset: offset)','let background = NSManagedObjectContext(concurrencyType: .privateQueueConcurrencyType)'])
  for t in ['rawType','UUID','fetchLimit','firstIndex(of: target.identifier)','clamped','min(offset','max(offset']:self.assertNotIn(t,s)
  self.assertIn('import SwiftUI',self.l)
 def test_index_changes_stay_in_original_context_and_background_only_touches_same_List_metadata(self):
  loop=body(self.move,'for (index, object) in ordered.enumerated()');self.order(loop,['retainNativeList(object)','let current = ((object.value(forKey: "metadata")','int64Value ?? 0','if current != Int64(index)','(object.value(forKey: "metadata") as? NSManagedObject)?.setValue(Int64(index), forKey: "index")','background.performAndWait','background.object(with: object.objectID)','list.willChangeValue(forKey: "metadata")','list.didChangeValue(forKey: "metadata")'])
  self.assertEqual(loop.count('object.value(forKey: "metadata")'),2);inside=body(loop,'background.performAndWait');self.assertNotIn('setValue',inside);self.assertNotIn('forKey: "index"',inside);self.assertNotIn('existingObject',inside);self.assertNotIn('obtainPermanentIDs',inside)
 def test_background_setup_and_object_filtered_observer_preserve_two_weak_owner_gates(self):
  s=self.move;self.order(s,['background.persistentStoreCoordinator = context.persistentStoreCoordinator','background.mergePolicy = NSMergeByPropertyStoreTrumpMergePolicy','for (index, object) in ordered.enumerated()','let observer = NotificationCenter.default.addObserver(forName: .NSManagedObjectContextDidSave','object: background, queue: nil) { [weak self] notification in','guard let context = self?.context else { return }','context.performAndWait { [weak self] in','self?.context.mergeChanges(fromContextDidSave: notification)','guard background.hasChanges else { return }','try background.save()','NotificationCenter.default.removeObserver(observer)','return ordered'])
  for t in ['Task','DispatchQueue','async','context.reset','automaticallyMergesChangesFromParent =']:self.assertNotIn(t,s)
 def test_background_save_error_rolls_back_logs_and_is_consumed_before_outer_index_save(self):
  s=self.move;self.order(s,['guard background.hasChanges else { return }','try OriginalObjCExceptionBridge.f_1002ff9c8 { try background.save() }','catch','background.rollback()','Self.reorderDiagnostics.f_1000d468c().f_1000d4e0c("Error saving managed object context: \\(error)")','NotificationCenter.default.removeObserver(observer)'])
  self.assertNotIn('throw error',s);self.assertIn('name: "NSManagedObjectContext"',self.l)
  outer=(ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text();commit=body(outer,'func commit<T>(previous:');self.order(commit,['var outcome = try operation(transaction)','if context.hasChanges','try context.save()'])
 def test_real_store_consumer_projects_only_after_move_and_keeps_native_write_markers(self):
  s=body(self.store,'public func moveList(_ target:');self.order(s,['try mutateInTransaction','let ordered = transaction.repository.lists.moveList(target.nativeObject, toOffset: offset)','for object in ordered','projectNativeList(ClipboardListTarget(object: object), into: &state)'])
  for t in ['UUID','Set(','sortOrder =','firstIndex','pinboardNotFound']:self.assertNotIn(t,s)
  self.assertIn('if nativeLists[identifier] === list { continue }',body(self.l,'func synchronize('))
 def test_native_string_drag_consumer_uses_raw_ID_indices_and_original_destination_offset(self):
  tabs=body(self.panel,'private func boardTab(');self.assertIn('tab.dragString = "paste-pinboard:" + target.identifier',tabs);self.assertIn('return state.moveList(identifier: String(value.dropFirst(15)), to: target)',tabs);self.assertNotIn('if let board',tabs)
  dragged=body(self.title,'private func draggedGroup(');self.assertNotIn('UUID(',dragged);self.assertIn('value.hasPrefix("paste-pinboard:")',dragged)
  s=body(self.ui,'func moveList(identifier:');self.order(s,['store.tabListTarget(identifier: identifier)','toolbarOwner?.moveList(source, to: target, persist: { offset in','try? self.store.moveList(source, toOffset: offset)']);self.assertNotIn('tabListSnapshot',s);self.assertIn('}) ?? false',s);self.assertNotIn('store.pinboards',s);self.assertNotIn('guard sourceIndex !=',s);self.assertNotIn('func movePinboard(id:',self.ui)
 def test_eight_exact_deltas_and_idempotent_inverse_preserve247_sources_and_shared_history(self):
  self.assertEqual(len(CHANGES),8);changed=[]
  for p,h in self.base['production'].items():
   if hashlib.sha256(pre_native_list_edit_event_bytes(ROOT/p)).hexdigest()!=h:changed.append(p)
   self.assertEqual(hashlib.sha256(pre_native_list_reorder_bytes(ROOT/p)).hexdigest(),h)
   if p.endswith('.swift'):
    before=(self.ph/'before'/p).read_text();self.assertEqual(pre_native_list_reorder(before),before)
  legacy=(ROOT/'replica/Tests/Native/UIInteractionHarness.swift').read_text();self.assertEqual(pre_native_list_reorder(legacy),legacy)
  self.assertEqual(set(changed),set(self.p['current_sources']));self.assertEqual(len(changed),5)
  for r in self.p['unchanged_methods']:self.assertEqual(hashlib.sha256(body(pre_native_list_edit_event((ROOT/r['path']).read_text()),r['symbol']).encode()).hexdigest(),r['sha256'])
  for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_native_tab_source_renderer_bytes(ROOT/p)).hexdigest(),h)
  self.assertFalse(self.p['finite_contract_completed']);self.assertFalse(self.p['runtime_executed']);self.assertFalse(self.p['full_function_migration_verified']);self.assertIn('1b9460',' '.join(self.p['remaining']))

if __name__=='__main__':unittest.main()
