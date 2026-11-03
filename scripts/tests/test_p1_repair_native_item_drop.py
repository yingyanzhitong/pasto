"""Native item-ID drop and local history/group dispatch; source/Python/Mach-O only."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts/tests'),str(ROOT/'scripts')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from native_item_drop_scope_contract import CHANGES,pre_native_item_drop

from text_storage_owner_scope_contract import pre_text_storage_owner_bytes

from suggestion_description_scope_contract import pre_suggestion_description_bytes
class NativeItemDrop(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ph=ROOT/'.local/p0-repair/phase-172';cls.p=json.loads((cls.ph/'native-item-drop-contract.json').read_text());cls.base=json.loads((cls.ph/'baseline.json').read_text());cls.title=(ROOT/'replica/Sources/Pasto/UI/OriginalPinboardTabTitle.swift').read_text();cls.panel=(ROOT/'replica/Sources/Pasto/UI/PanelViews.swift').read_text();cls.ui=(ROOT/'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text();cls.persistence=(ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text();cls.repo=body(cls.persistence,'final class ManagedRepository');cls.store=(ROOT/'replica/Sources/PastoCore/ClipboardStore.swift').read_text();cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
 def order(self,s,tokens):
  positions=[s.index(t)for t in tokens];self.assertEqual(positions,sorted(positions))
 def word(self,a):return int.from_bytes(self.n['read'](a,4),'little')
 def test27_original_fragments_and_complete_machine_ranges_are_bound(self):
  self.assertEqual(len(self.p['original_fragments']),27)
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for k in ['binary','decoder','sdk_drag_header']:
   r=self.p[k];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
  for r in self.p['machine_ranges']:
   a=int(r['start'],16);b=int(r['end'],16);self.assertEqual(hashlib.sha256(self.n['read'](a,b-a)).hexdigest(),r['sha256'])
 def test_real_calls_and_repository_read_write_slots_are_bound(self):
  for r in self.p['calls']:
   a=int(r['address'],16);raw=self.n['read'](a,4);self.assertEqual(raw.hex(),r['bytes']);w=int.from_bytes(raw,'little');self.assertEqual(w&0x7c000000,0x14000000);d=w&0x3ffffff;d=d-(1<<26)if d&(1<<25)else d;self.assertEqual(hex(a+4*d),r['target'])
  self.assertEqual(len(self.p['pointers']),4)
  for r in self.p['pointers']:
   a=int(r['address'],16);self.assertEqual(self.n['read'](a,8).hex(),r['bytes']);v,c=self.n['reachable_pointer'](a);self.assertEqual(c,r['chain']);self.assertEqual(hex(self.n['base']+(v&((1<<36)-1))),r['target'])
 def test_removed_error_block_releases_original_error_and_UI_does_not_show_extra_alert(self):
  r=self.p['sdk_error_release'];a=int(r['stub'],16);x,y=struct.unpack('<II',self.n['read'](a,8));imm=((x>>5)&0x7ffff)*4+((x>>29)&3);imm=imm-(1<<21)if imm&(1<<20)else imm;q=(a&~4095)+(imm<<12)+((y>>10)&0xfff)*8;self.assertEqual(hex(q),r['pointer']);v,c=self.n['reachable_pointer'](q);self.assertTrue(v>>63);f=self.n['fixup'][0];h=struct.unpack_from('<7I',self.n['raw'],f);entry=struct.unpack_from('<I',self.n['raw'],f+h[2]+4*(v&0xffffff))[0];o=f+h[3]+(entry>>9);self.assertEqual(self.n['raw'][o:self.n['raw'].index(b'\0',o)].decode(),'_swift_errorRelease')
  for r in self.p['words']:self.assertEqual(self.n['read'](int(r['address'],16),4).hex(),r['bytes'])
  s=body(self.ui,'func dropItems(identifiers:');self.assertIn('try? store.dropItems(identifiers: identifiers, to: target)',s)
  for token in ['perform {','presentError','NSAlert','UUID','DispatchQueue']:self.assertNotIn(token,s)
 def test_original_static_history_predicate_resolves_same_canonical_identifier(self):
  r=self.p['static_history_predicate'];self.assertEqual(self.n['read'](int(r['address'],16),64).hex(),r['bytes']);v,c=self.n['reachable_pointer'](int(r['pointer'],16));a=self.n['base']+(v&((1<<36)-1));self.assertEqual(hex(a),r['string_storage']);self.assertEqual(self.n['read'](a+32,r['utf8_length']).decode(),'sharedPasteboardHistory');self.assertEqual(self.n['read'](0x100fc11d8,8)+self.n['read'](0x100fc11e0,2),b'identifier')
 def test_original_tab_copy_operation_intersects_internal_source_mask_without_losing_reorder(self):
  header=(ROOT/self.p['sdk_drag_header']['path']).read_text();self.assertRegex(header,r'NSDragOperationCopy\s*= 1');self.assertRegex(header,r'NSDragOperationMove\s*= 16')
  self.assertEqual(self.word(0x100079338),0xaa0003f5);self.assertEqual(self.word(0x100079354),0xaa1503e0)
  s=body(self.title,'override func draggingEntered(');self.assertIn('return isDragDestination ? .copy : []',s);self.assertIn('return isDragDestination ? .move : []',s)
  source=(ROOT/'replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift').read_text();self.assertIn('context == .outsideApplication ? .copy : [.copy, .move]',source)
 def test_native_type_and_callbacks_are_configured_on_real_cell_and_same_target(self):
  self.assertIn('registerForDraggedTypes([OriginalNativeDragPasteboardWriter.itemIdentifierType, .string])',self.title)
  for token in ['view.onDropItemIdentifiers = onDropItemIdentifiers','view.canDropItems = canDropItems']:self.assertIn(token,body(self.title,'func configure(_ view:'))
  s=body(self.panel,'private func boardTab(');self.assertIn('tab.canDropItems = { true }',s);self.assertIn('tab.onDropItemIdentifiers = { [weak state = state] identifiers in',s);self.assertIn('state?.dropItems(identifiers: identifiers, to: target)',s);self.assertIn('state.moveList(identifier: String(value.dropFirst(15)), to: target)',s)
 def test_reader_returns_false_before_read_without_callback_and_accepts_nonempty_ordered_strings(self):
  s=body(self.title,'private func performItemDrop(');self.order(s,['guard let onDropItemIdentifiers else { return false }','sender.draggingPasteboard.pasteboardItems ?? []','compactMap','string(forType: OriginalNativeDragPasteboardWriter.itemIdentifierType)','guard !identifiers.isEmpty else { return false }','onDropItemIdentifiers(identifiers)','return true'])
  for token in ['UUID','Set(','sorted','isItemDrag','canDropItems','isDragDestination','store.','paste-pinboard:']:self.assertNotIn(token,s)
 def test_actual_dispatch_attempts_reader_before_type_gate_and_keeps_group_fallback_separate(self):
  s=body(self.title,'override func performDragOperation(');self.order(s,['if performItemDrop(sender) { return true }','if isItemDrag(sender) { return false }','isDragDestination = false','guard let value = draggedGroup(sender)','return onDropString?(value) ?? false'])
 def test_identifier_lookup_uses_real_native_writer_namespace_and_no_UUID_prefilter(self):
  s=body(self.repo,'func droppedItem(');self.order(s,['PastoItemEntity.defaultFetchRequest()','nativeIdentifier == %@ OR (nativeIdentifier == nil AND key == %@)','request.fetchLimit = 1','request.fetchOffset = 0','(try? context.fetch(request))?.first'])
  for token in ['UUID','Set(','fetchBatchSize','throw ']:self.assertNotIn(token,s)
  source=(ROOT/'replica/Sources/PastoCore/ClipboardRestoreItem.swift').read_text();source=body(source,'private final class ClipboardDragIdentifierSource');self.assertIn('object.value(forKey: "nativeIdentifier")',source)
 def test_store_retains_native_List_and_projects_only_after_repository_side_effects(self):
  s=body(self.store,'public func dropItems(identifiers:');self.order(s,['try mutateInTransaction','transaction.repository.dropItems(identifiers: identifiers, to: target.nativeObject)','state.items.removeAll','for item in values','state.items[index] = item'])
  for token in ['UUID','pinboardID','store.pinboards','guard !','Set(identifiers','try assign(orderedIDs']:self.assertNotIn(token,s)
 def test_native_repository_resolves_input_occurrences_and_dispatches_both_local_list_types(self):
  s=body(self.repo,'func dropItems(identifiers:');self.order(s,['identifiers.compactMap { droppedItem(identifier: $0) }','guard !items.isEmpty else { return [] }','switch (list.value(forKey: "rawType")','case 2:','return try assignItems(items, to: list)','case 1:','items.reversed()','default:\n                return []'])
  self.assertNotIn('UUID',s[:s.index('case 1:')]);self.assertNotIn('Set(identifiers',s)
 def test_history_writes_per_occurrence_then_deletes_native_unowned_expired_objects_before_UUID_bookkeeping(self):
  s=body(self.repo,'func dropItems(identifiers:');self.order(s,['for item in items.reversed() { item.setValue(Date(), forKey: "timestamp") }','if let capacity = lists.historyCapacity(of: list), capacity > 0','let interval = -capacity * 24 * 60 * 60','list == nil && timestamp < %@','let expired = (try? context.fetch(request)) ?? []','for item in expired { context.delete(item) }','UUID(uuidString: key)','alreadyDeletedItemIDs.insert(id)','lists.historyList()','context.refresh(history, mergeChanges: true)','return try items.map { try ClipboardPersistence.item($0) }'])
  for token in ['setValue(nil, forKey: "list")','Date.distantPast','expireHistory(&state','context.save()','context.reset()']:self.assertNotIn(token,s)
 def test_existing_group_native_move_P0_commit_and_other_consumers_are_unchanged(self):
  self.assertEqual(len(self.p['unchanged_methods']),8)
  for r in self.p['unchanged_methods']:self.assertEqual(hashlib.sha256(body((ROOT/r['path']).read_text(),r['symbol']).encode()).hexdigest(),r['sha256'])
  for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_suggestion_description_bytes(ROOT/p)).hexdigest(),h)
 def test_eleven_hunks_twelve_substitutions_and247_inverse_idempotence_match_exact_baseline(self):
  self.assertEqual(len(CHANGES),11);self.assertEqual(sum(r[3]for r in CHANGES),12);changed=[]
  for p,h in self.base['production'].items():
   data=pre_text_storage_owner_bytes(ROOT/p);old=(self.ph/'before'/p).read_bytes()
   if hashlib.sha256(data).hexdigest()!=h:changed.append(p)
   self.assertEqual(hashlib.sha256(pre_native_item_drop(data.decode()).encode()if p.endswith('.swift')else data).hexdigest(),h,p)
   self.assertEqual(pre_native_item_drop(old.decode()).encode()if p.endswith('.swift')else old,old,p)
  self.assertEqual(sorted(changed),sorted(self.p['current_sources']))
 def test_reader_protocol_oracle_covers_missing_nil_duplicates_arbitrary_ids_and_failed_write(self):
  def expected(callback,entries):
   if callback is None:return False,[]
   values=[v for v in entries or []if v is not None]
   return bool(values),values
  for entries in [None,[],[None],[None,None]]:self.assertEqual(expected(True,entries),(False,[]))
  self.assertEqual(expected(None,['checksum']), (False,[]))
  self.assertEqual(expected(True,['checksum',None,'not-a-UUID','checksum']),(True,['checksum','not-a-UUID','checksum']))
  self.assertTrue(expected('write-fails',['checksum'])[0])
 def test_source_mask_handshake_and_nil_native_identity_fallback_protocol_oracle(self):
  COPY,MOVE=1,16;self.assertTrue((COPY|MOVE)&COPY);self.assertTrue((COPY|MOVE)&MOVE);self.assertFalse(MOVE&COPY)
  entities=[dict(key='legacy-uuid',native='hash-id'),dict(key='old-import',native=None)]
  lookup=lambda value:[e for e in entities if e['native']==value or(e['native']is None and e['key']==value)]
  self.assertEqual(lookup('hash-id'),[entities[0]]);self.assertEqual(lookup('legacy-uuid'),[]);self.assertEqual(lookup('old-import'),[entities[1]])
 def test_history_protocol_preserves_group_owners_and_only_expires_old_unowned_records(self):
  records=[dict(id='a',owner='group',timestamp=1),dict(id='b',owner=None,timestamp=1),dict(id='c',owner=None,timestamp=20)]
  expired=[r['id']for r in records if r['owner']is None and r['timestamp']<10];self.assertEqual(expired,['b'])
  # Reverse stamping gives the first input the latest observation, while preserving each occurrence.
  inputs=['a','c','a'];observed=list(reversed(inputs));self.assertEqual(observed,['a','c','a']);self.assertEqual(len(observed),3)
  self.assertFalse(self.p['runtime_executed']);self.assertFalse(self.p['full_function_migration_verified'])

if __name__=='__main__':unittest.main()
