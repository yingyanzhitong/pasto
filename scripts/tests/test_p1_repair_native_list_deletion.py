"""Local rawType2 pinboard deletion only; source/Mach-O checks without framework execution."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts/tests'),str(ROOT/'scripts')]
from function_ledger import source_fragments
from native_list_reorder_scope_contract import pre_native_list_reorder_bytes
from test_offline_p0_contracts import body
from native_list_deletion_scope_contract import CHANGES,pre_native_list_deletion_bytes

class NativeListDeletion(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ph=ROOT/'.local/p0-repair/phase-166';cls.p=json.loads((cls.ph/'native-list-deletion-contract.json').read_text());cls.base=json.loads((cls.ph/'baseline.json').read_text());cls.s={Path(p).stem:(ROOT/p).read_text()for p in cls.p['current_sources']};cls.l=cls.s['ClipboardListPersistence'];cls.repo=body(cls.s['ClipboardPersistence'],'final class ManagedRepository');cls.store=cls.s['ClipboardStore'];cls.panel=cls.s['PanelViews'];cls.ui=cls.s['ReplicaUIController'];cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
 def order(self,s,tokens):
  p=[s.index(t)for t in tokens];self.assertEqual(p,sorted(p))
 def test_original_fragments_inputs_and_complete_machine_ranges(self):
  self.assertEqual(len(self.p['original_fragments']),15)
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for k in ['binary','decoder']:
   r=self.p[k];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
  self.assertEqual(len(self.p['machine_ranges']),5)
  for r in self.p['machine_ranges']:
   a=int(r['start'],16);b=int(r['end'],16);self.assertEqual(hashlib.sha256(self.n['read'](a,b-a)).hexdigest(),r['sha256'])
 def test_native_delete_witness_and102_real_calls_are_bound(self):
  for r in self.p['pointers']:
   a=int(r['address'],16);v,c=self.n['reachable_pointer'](a);self.assertEqual(self.n['read'](a,8).hex(),r['bytes']);self.assertFalse(v>>63);self.assertEqual(c,r['chain']);self.assertEqual(hex(self.n['base']+(v&((1<<36)-1))),r['target'])
  self.assertEqual(self.p['pointers'][-1]['target'],'0x1003687f8');self.assertEqual(len(self.p['calls']),102)
  calls={}
  for r in self.p['calls']:
   a=int(r['address'],16);w=int.from_bytes(self.n['read'](a,4),'little');self.assertEqual(w.to_bytes(4,'little').hex(),r['bytes']);self.assertEqual(w&0xfc000000,0x94000000);d=w&0x3ffffff;d=d-(1<<26)if d&(1<<25)else d;self.assertEqual(hex(a+4*d),r['target']);calls[a]=a+4*d
  self.assertEqual(calls[0x1003689bc],0x100363004);self.assertEqual(calls[0x1003688d8],0x100bfc708);self.assertEqual(calls[0x1003689e0],0x100c00f00)
 def test_true_owner_context_timestamp_and_delete_selectors(self):
  for r in self.p['selectors']:
   a=int(r['stub'],16);x,y=struct.unpack('<II',self.n['read'](a,8));self.assertEqual(self.n['read'](a,8).hex(),r['bytes']);imm=((x>>5)&0x7ffff)*4+((x>>29)&3);imm=imm-(1<<21)if imm&(1<<20)else imm;q=(a&~4095)+(imm<<12)+((y>>10)&0xfff)*8;self.assertEqual(hex(q),r['pointer']);v,c=self.n['reachable_pointer'](q);self.assertEqual(c,r['chain']);t=self.n['base']+(v&((1<<36)-1));self.assertEqual(hex(t),r['selector_address']);self.assertEqual(self.n['read'](t,100).split(b'\0')[0].decode(),r['selector'])
  self.assertEqual([r['selector']for r in self.p['selectors']],['managedObjectContext','deleteObject:','list','setList:','timestamp'])
 def test_fetch_error_real_machine_path_rejoins_empty_sequence_then_deletes_same_list(self):
  for r in self.p['words']:self.assertEqual(self.n['read'](int(r['address'],16),4).hex(),r['bytes'])
  # Both missing context and caught fetch error converge at the original empty sequence path.
  self.assertEqual(int.from_bytes(self.n['read'](0x1003688a0,4),'little'),0xb4000260)
  self.assertEqual(int.from_bytes(self.n['read'](0x1003688d0,4),'little'),0xb4000395)
  r=self.p['error_release_import'];self.assertEqual(r['symbol'],'_swift_errorRelease');self.assertEqual(self.n['read'](int(r['stub']['address'],16),12).hex(),r['stub']['bytes'])
  s=body(self.l,'func removePinboard(_ list:');self.order(s,['if let context = list.managedObjectContext','items = (try? context.fetch(itemRequest(for: list))) ?? []','for item in items','list.managedObjectContext?.delete(list)','return items'])
  self.assertIn('else { items = [] }',s)
 def test_local_group_owner_must_equal_target_and_only_orphans_are_deleted_from_own_context(self):
  s=body(self.l,'func removePinboard(_ list:');self.order(s,['int64Value == 2','let owner = item.value(forKey: "list") as? NSManagedObject, owner.isEqual(list)','item.setValue(nil, forKey: "list")','if item.value(forKey: "timestamp") == nil, item.value(forKey: "list") == nil','item.managedObjectContext?.delete(item)','list.managedObjectContext?.delete(list)'])
  for t in ['UUID','compactMap','Set(','Date()','context.save','context.reset','throw','rawType", on:','forKey: "timestamp")\n']:self.assertNotIn(t,s)
  request=body(self.l,'func itemRequest(for list:');self.assertIn('request.predicate = NSPredicate(format: "list == %@", list)',request);self.assertIn('NSSortDescriptor(key: "displayOrderInPinboard", ascending: true)',request)
 def test_all_native_mutations_precede_compatibility_identifiers_and_write_suppression(self):
  s=body(self.repo,'func removePinboard(_ list:');self.order(s,['let affected = lists.removePinboard(list)','for object in affected','object.value(forKey: "key")','UUID(uuidString: key)','assignedItemIDs.insert(id)','unassignedItemIDs.insert(id)','if object.isDeleted { alreadyDeletedItemIDs.insert(id) }','return affected'])
  self.assertNotIn('context.fetch',s);self.assertNotIn('lists.list(identifier:',s)
 def test_value_projection_follows_native_delete_and_keeps_unfetched_orphans_on_fetch_failure(self):
  s=body(self.store,'public func removeList(');self.order(s,['try mutateInTransaction','let affected = transaction.repository.removePinboard(target.nativeObject)','if let id = UUID(uuidString: identifier)','state.pinboards.removeAll','for object in affected','if object.isDeleted','state.items.removeAll { $0.id == id }','item.isInHistory = object.value(forKey: "timestamp") != nil'])
  self.assertNotIn('!$0.isInHistory && $0.pinboardIDs.isEmpty',s);self.assertIn('ownerID',s);self.assertIn('ClipboardItemOrderPersistence.project(&item, from: object)',s)
  before=s[:s.index('let affected = transaction.repository.removePinboard(target.nativeObject)')]
  for t in ['UUID(','firstIndex','pinboardNotFound','guard let','contains']:self.assertNotIn(t,before)
 def test_menu_and_pending_confirmation_retain_same_native_target_without_value_cache_gate(self):
  m=body(self.panel,'private func localListMenu(');self.order(m,['else if list.rawType == 2','title: list.isEmpty ? "删除" : "删除…"','state.controller?.removePinboard(target)']);self.assertNotIn('if let board',m)
  self.assertIn('@Published var pendingPinboardDeletion: ClipboardListTarget?',self.ui);self.assertIn('pinboardDeletionConfirmation(target)',self.panel);self.assertIn('\\(target.name)',body(self.panel,'private func pinboardDeletionConfirmation('))
  for s in [body(self.ui,'func removePinboard(_ target:'),body(self.ui,'func confirmPinboardRemoval()'),body(self.panel,'private func pinboardDeletionConfirmation(')]:
   for t in ['store.pinboards','uuidString','UUID(uuidString:','pinboardDeletionID']:self.assertNotIn(t,s)
 def test_empty_group_deletes_immediately_nonempty_group_stays_in_panel_and_failure_stays_inline(self):
  s=body(self.ui,'func removePinboard(_ target:');self.order(s,['state.cancelItemDeletion()','state.pendingPinboardDeletion = target','if store.localListMenuState(target).isEmpty','confirmPinboardRemoval()','panel.makeFirstResponder(nil)'])
  c=body(self.ui,'func confirmPinboardRemoval()');self.order(c,['guard let target = state.pendingPinboardDeletion','try store.removeList(target)','cancelPinboardRemoval()','catch','state.pinboardDeletionError = error.localizedDescription'])
  code='\n'.join(l for l in (s+c).splitlines()if not l.lstrip().startswith('//'))
  for t in ['state.chooseBoard(nil)','NSAlert','runModal','hidePanel','presentError']:self.assertNotIn(t,code)
  self.assertIn('pendingPinboardDeletion = nil',body(self.ui,'func cancelPinboardRemoval()'));self.assertIn('pendingPinboardDeletion?.isDeleted == true',body(self.ui,'func normalizeSelection()'))
 def test_native_delete_does_not_depend_on_compatibility_confirmation_lookup(self):
  overlay=body(self.panel,'if state.hasPendingDeletion');self.assertIn('if let target = state.pendingPinboardDeletion',overlay);self.assertNotIn('store.pinboards.first',overlay)
  self.assertIn('public var isDeleted: Bool { nativeObject.isDeleted }',body(self.l,'public struct ClipboardListTarget'))
  self.assertIn('pendingPinboardDeletion != nil || pendingItemDeletion != nil',self.ui)
 def test_exact_scope_preserves_other_sources_legacy_history_and_reorder_and_does_not_claim_parent_completion(self):
  self.assertEqual(len(CHANGES),16);changed=[]
  for p,h in self.base['production'].items():
   if hashlib.sha256(pre_native_list_reorder_bytes(ROOT/p)).hexdigest()!=h:changed.append(p)
   self.assertEqual(hashlib.sha256(pre_native_list_deletion_bytes(ROOT/p)).hexdigest(),h)
  self.assertEqual(set(changed),set(self.p['current_sources']));self.assertEqual(len(changed),5)
  for r in self.p['unchanged_methods']:self.assertEqual(hashlib.sha256(body((ROOT/r['path']).read_text(),r['symbol']).encode()).hexdigest(),r['sha256'])
  self.assertEqual(self.p['excluded_subchains'][0]['function_id'],'Paste:0x1003acd8c');self.assertIn('state.moveList(identifier: String(value.dropFirst(15)), to: target)',self.panel);self.assertFalse(self.p['finite_contract_completed']);self.assertFalse(self.p['runtime_executed']);self.assertFalse(self.p['full_function_migration_verified'])

if __name__=='__main__':unittest.main()
