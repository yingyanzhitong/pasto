"""Supplied List name/color writes, matched to original branches; no framework execution."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts/tests'),str(ROOT/'scripts')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from native_list_name_color_scope_contract import CHANGES,pre_native_list_name_color_bytes
from native_list_deletion_scope_contract import pre_native_list_deletion_bytes

class NativeListNameColor(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ph=ROOT/'.local/p0-repair/phase-165';cls.p=json.loads((cls.ph/'native-list-name-color-contract.json').read_text());cls.base=json.loads((cls.ph/'baseline.json').read_text());cls.s={Path(p).stem:(ROOT/p).read_text()for p in cls.p['current_sources']};cls.l=cls.s['ClipboardListPersistence'];cls.store=cls.s['ClipboardStore'];cls.panel=cls.s['PanelViews'];cls.persistence=cls.s['ClipboardPersistence'];cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
 def order(self,s,tokens):
  pos=[s.index(t)for t in tokens];self.assertEqual(pos,sorted(pos))
 def test_original_fragments_binary_decoder_and_complete_machine_ranges(self):
  self.assertEqual(len(self.p['original_fragments']),22)
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for k in ['binary','decoder']:
   r=self.p[k];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
  self.assertEqual(len(self.p['machine_ranges']),6)
  for r in self.p['machine_ranges']:
   a=int(r['start'],16);b=int(r['end'],16);self.assertEqual(hashlib.sha256(self.n['read'](a,b-a)).hexdigest(),r['sha256'])
 def test_true_repository_write_slots_select_name_and_color_thunks(self):
  for r in self.p['pointers']:
   a=int(r['address'],16);v,c=self.n['reachable_pointer'](a);self.assertEqual(self.n['read'](a,8).hex(),r['bytes']);self.assertFalse(v>>63);self.assertEqual(c,r['chain']);self.assertEqual(hex(self.n['base']+(v&((1<<36)-1))),r['target'])
  self.assertEqual([(r['address'],r['target'])for r in self.p['pointers'][-2:]],[('0x100eccdc0','0x10036908c'),('0x100eccdd0','0x100369304')])
  for a,t in [(0x10036908c,0x10036c448),(0x100369304,0x10036c614)]:
   w=int.from_bytes(self.n['read'](a,4),'little');self.assertEqual(w&0xfc000000,0x14000000);d=w&0x3ffffff;d=d-(1<<26)if d&(1<<25)else d;self.assertEqual(a+4*d,t)
 def test_original_calls_and_actual_objc_selectors(self):
  self.assertEqual(len(self.p['calls']),45)
  for r in self.p['calls']:
   a=int(r['address'],16);w=int.from_bytes(self.n['read'](a,4),'little');self.assertEqual(w.to_bytes(4,'little').hex(),r['bytes']);self.assertEqual(w&0xfc000000,0x94000000);d=w&0x3ffffff;d=d-(1<<26)if d&(1<<25)else d;self.assertEqual(hex(a+4*d),r['target'])
  for r in self.p['selectors']:
   a=int(r['stub'],16);x,y=struct.unpack('<II',self.n['read'](a,8));self.assertEqual(self.n['read'](a,8).hex(),r['bytes']);imm=((x>>5)&0x7ffff)*4+((x>>29)&3);imm=imm-(1<<21)if imm&(1<<20)else imm;q=(a&~4095)+(imm<<12)+((y>>10)&0xfff)*8;self.assertEqual(hex(q),r['pointer']);v,c=self.n['reachable_pointer'](q);self.assertEqual(c,r['chain']);target=self.n['base']+(v&((1<<36)-1));self.assertEqual(hex(target),r['selector_address']);self.assertEqual(self.n['read'](target,100).split(b'\0')[0].decode(),r['selector'])
  self.assertEqual([r['selector']for r in self.p['selectors']],['name','setName:','setRawAttributes:'])
 def test_machine_error_release_and_nil_encode_path_are_real_not_deadcode_guesses(self):
  for r in self.p['words']:self.assertEqual(self.n['read'](int(r['address'],16),4).hex(),r['bytes'])
  # Failed encode zeroes the actual NSData argument and still joins setRawAttributes:.
  self.assertEqual(int.from_bytes(self.n['read'](0x10036c7ac,4),'little'),0xd2800014)
  self.assertEqual(int.from_bytes(self.n['read'](0x10036c7b0,4),'little'),0x1400000c)
  for a in [0x1003c4a64,0x1003c4c08,0x10036c6b4,0x10036c7a0]:
   w=int.from_bytes(self.n['read'](a,4),'little');d=w&0x3ffffff;d=d-(1<<26)if d&(1<<25)else d;self.assertEqual(a+4*d,0x100bfc708)
  r=self.p['error_release_import'];self.assertEqual(r['symbol'],'_swift_errorRelease');self.assertEqual(self.n['read'](int(r['stub']['address'],16),12).hex(),r['stub']['bytes'])
 def test_name_callback_compares_against_fresh_second_read_and_keeps_empty_only_mapping(self):
  s=body(self.l,'func updateName(on:')if 'func updateName(on:'in self.l else body(self.l,'func updateName(on list:')
  self.assertEqual(s.count('list.value(forKey: "name")'),2);self.order(s,['var value = String._unconditionallyBridgeFromObjectiveC','update(&value)','let current = String._unconditionallyBridgeFromObjectiveC','if current != value { list.setValue(value, forKey: "name") }'])
  t=(ROOT/'replica/Sources/PastoCore/OriginalPinboardTitle.swift').read_text();self.assertIn('value.isEmpty ?',t);self.assertNotIn('trimmingCharacters',t)
 def test_color_decode_case_and_equality_guards_precede_encode_and_nil_setter(self):
  s=body(self.l,'func updateColor(on list:');self.order(s,['guard case let .pinboard(old)? = OriginalPinboardAttributes.decoded(','from: list.value(forKey: "rawAttributes") as? Data) else { return }','var value = old','update(&value)','guard old != value else { return }','let attributes = try? OriginalPinboardAttributes.encoded(colorCode: value)','list.setValue(attributes, forKey: "rawAttributes")'])
  for token in ['rawType','Date()','context.fetch','context.save','guard let attributes','throw','catch','Task']:self.assertNotIn(token,s)
 def test_store_mutates_supplied_object_before_optional_compatibility_projection(self):
  for signature,operation in [('public func renameList(','lists.updateName(on: target.nativeObject)'),('public func updateListColor(','lists.updateColor(on: target.nativeObject)')]:
   s=body(self.store,signature);self.order(s,['try mutateInTransaction','lists.retainNativeList(target.nativeObject)',operation,'projectNativeList(target, into: &state)'])
   for t in ['first(where:','UUID(','list(identifier:','pinboardNotFound','guard let','context.fetch']:self.assertNotIn(t,s)
  self.assertIn('OriginalPinboardTitle.normalizedRename(rawName)',body(self.store,'public func renameList('))
 def test_compatibility_projection_does_not_gate_native_mutation_or_replace_unrelated_colors(self):
  s=body(self.store,'private func projectNativeList(');self.order(s,['target.identifier == Self.historyListIdentifier','state.preferences.historyTitle = target.name','guard let id = UUID(uuidString: target.identifier)','state.pinboards.firstIndex','if let board = target.pinboardValue','state.pinboards[index].name = target.name'])
  self.assertIn('if state.pinboards[index].rawAttributes != attributes',s);self.assertIn('if let color = OriginalPinboardAttributes.colorCode(from: attributes)',s);self.assertIn('target.nativeObject.value(forKey: "metadata")',s)
 def test_native_marker_prevents_stale_name_type_attributes_and_index_replay(self):
  s=body(self.l,'func synchronize(');self.order(s,['if nativeLists[identifier] === list { continue }','set(board.name, key: "name", on: list)','set(Int64(board.rawType ?? 2), key: "rawType", on: list)','set(board.rawAttributes, key: "rawAttributes", on: list)','guard let metadata = list.value(forKey: "metadata")','throw CocoaError(.fileReadCorruptFile)'])
  self.assertIn('private var nativeLists: [String: NSManagedObject] = [:]',self.l);self.assertIn('nativeLists[identifier] = list',body(self.l,'func retainNativeList('));self.assertIn('nativeLists[identifier] = list',body(self.l,'func insertPinboard('))
 def test_menu_count_and_rename_use_same_list_and_native_event(self):
  m=body(self.panel,'private func localListMenu(');self.assertIn('requestTabRename(target)',m);self.assertIn('state.store.localListMenuState(target)',m);self.assertIn('target.colorCode.map',m)
  r=body(self.panel,'private func requestTabRename(');self.assertIn('state.beginEditingListSubject.send(target)',r);self.assertNotIn('uuidString',r)
  self.assertIn('persistence.localListMenuState(target)',body(self.store,'public func localListMenuState(_ target:'))
  self.assertIn('context.performAndWait { lists.menuState(for: target.nativeObject) }',body(self.persistence,'func localListMenuState(_ target:'))
 def test_panel_error_consumption_and_weak_menu_cancellation_keep_original_order(self):
  m=body(self.panel,'private func localListMenu(');self.order(m,['{ [weak menu] in','try? state.store.updateListColor(target, colorCode: color.canonicalColorCode)','menu?.cancelTracking()'])
  commit=body(body(self.panel,'private func boardButton('),'onCommit:');self.assertIn('{ value in',commit);self.order(commit,['try? state.store.renameList(target, rawName: value)','return target.name'])
  for token in ['presentError','state.perform','NSAlert','Task','DispatchQueue']:self.assertNotIn(token,commit+m)
 def test_success_only_projection_and_original_save_error_rollback_remain(self):
  s=body(self.persistence,'func commit<T>(previous:');self.order(s,['try context.save()','context.rollback()','throw error','viewHistoryToken =','projectNativePinboards(outcome.state.pinboards)','return outcome'])
  current=body(body(s,'if context.hasChanges'),'try context.save() }\n                    } catch');old=body(body(body((self.ph/'before/replica/Sources/PastoCore/ClipboardPersistence.swift').read_text(),'func commit<T>(previous:'),'if context.hasChanges'),'try context.save() }\n                    } catch');self.assertEqual(current,old)
 def test_exact_deltas_preserve_other_sources_and_legacy_delete_reorder_remain_pending(self):
  self.assertEqual(len(CHANGES),24);changed=[]
  for p,h in self.base['production'].items():
   if hashlib.sha256(pre_native_list_deletion_bytes(ROOT/p)).hexdigest()!=h:changed.append(p)
   self.assertEqual(hashlib.sha256(pre_native_list_name_color_bytes(ROOT/p)).hexdigest(),h)
  self.assertEqual(set(changed),set(self.p['current_sources']));self.assertEqual(len(changed),4)
  for r in self.p['unchanged_methods']:self.assertEqual(hashlib.sha256(body((ROOT/r['path']).read_text(),r['symbol']).encode()).hexdigest(),r['sha256'])
  self.assertIn('state.controller?.removePinboard(target)',self.panel);self.assertIn('state.moveList(identifier: String(value.dropFirst(15)), to: target)',self.panel);self.assertFalse(self.p['finite_contract_completed']);self.assertFalse(self.p['full_function_migration_verified']);self.assertFalse(self.p['runtime_executed'])

if __name__=='__main__':unittest.main()
