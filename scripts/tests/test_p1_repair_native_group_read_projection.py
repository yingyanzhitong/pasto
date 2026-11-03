"""Native tab-source discrepancy and partial shared read projection, without UI/framework execution."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts/tests'),str(ROOT/'scripts')]
from function_ledger import source_fragments
from native_list_name_color_scope_contract import pre_native_list_name_color
from native_tab_list_delivery_scope_contract import pre_native_tab_list_delivery, pre_native_tab_list_delivery_bytes
from test_offline_p0_contracts import body
from native_group_read_projection_scope_contract import CHANGES,pre_native_group_read_projection,pre_native_group_read_projection_bytes
class NativeGroupReadProjection(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ph=ROOT/'.local/p0-repair/phase-163';cls.p=json.loads((cls.ph/'native-tab-source-contract.json').read_text());cls.base=json.loads((cls.ph/'baseline.json').read_text());cls.path=next(iter(cls.p['current_sources']));cls.s=(ROOT/cls.path).read_text();cls.project=body(cls.s,'func project(_');cls.before=body((cls.ph/'before'/cls.path).read_text(),'func project(_');cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
 def test_twelve_original_fragments_and_static_binary_decoder_are_bound(self):
  self.assertEqual(len(self.p['original_fragments']),12)
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for k in ['binary','decoder']:
   r=self.p[k];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
 def test_true_protocol_pointer_chain_distinguishes_all_lists_from_group_menu(self):
  for r in self.p['pointers']:
   a=int(r['address'],16);self.assertEqual(self.n['read'](a,8).hex(),r['bytes']);v,c=self.n['reachable_pointer'](a);self.assertFalse(v>>63);self.assertEqual(c,r['chain']);self.assertEqual(hex(self.n['base']+(v&((1<<36)-1))),r['target'])
  self.assertEqual([(r['address'],r['target'])for r in self.p['pointers']], [('0x100eccd70','0x100c42f30'),('0x100eccd80','0x100367f78'),('0x100eccd88','0x10036805c')])
 def test_original_tab_constructor_uses_class_default_request_then_native_FRC(self):
  for r in self.p['calls']:
   a=int(r['address'],16);w=int.from_bytes(self.n['read'](a,4),'little');self.assertEqual(w.to_bytes(4,'little').hex(),r['bytes']);self.assertEqual(w&0xfc000000,0x94000000);d=w&0x3ffffff;d=d-(1<<26)if d&(1<<25)else d;self.assertEqual(hex(a+d*4),r['target'])
  m=self.p['tab_constructor'];self.assertEqual(hashlib.sha256(self.n['read'](int(m['start'],16),int(m['end'],16)-int(m['start'],16))).hexdigest(),m['sha256'])
 def test_all_preexisting_legacy_mapping_branches_stay_identical_before_native_augmentation(self):
  prefix=self.project[:self.project.index('\n        // A native List')];old=self.before[:self.before.rfind('\n    }')];self.assertEqual(prefix.replace('var values = pinboards.map','return pinboards.map'),old)
  self.assertIn('guard let list = lists[board.id.uuidString] else { return board }',prefix);self.assertIn('Int16(exactly: rawType) ?? 0',prefix)
 def test_only_missing_undeleted_exact_type2_UUID_native_groups_are_added_without_deduplicating_existing_rows(self):
  s=self.project[self.project.index('var represented = Set(values.map(\\.id))'):];tokens=['for list in lists.values','guard !list.isDeleted','int64Value == 2','let identifier = list.value(forKey: "identifier") as? String','let id = UUID(uuidString: identifier), represented.insert(id).inserted','values.append(Pinboard(id: id'];pos=[s.index(t)for t in tokens];self.assertEqual(pos,sorted(pos));self.assertNotIn('values = Array(Set',s);self.assertNotIn('Dictionary(uniqueKeysWithValues',s);self.assertNotIn('rawType == 1',s)
 def test_added_fields_use_native_name_attributes_and_index_then_existing_value_sort(self):
  s=self.project[self.project.index('var represented'):]
  for t in ['list.value(forKey: "rawAttributes") as? Data','OriginalPinboardAttributes.colorCode(from: attributes)','list.value(forKey: "metadata") as? NSManagedObject','metadata?.value(forKey: "index")','name: list.value(forKey: "name") as? String ?? ""','rawType: 2, rawAttributes: attributes','return values.sorted','$0.id.uuidString < $1.id.uuidString']:self.assertIn(t,s)
  for t in ['insertNewObject','setValue(','context.save','validateForInsert','Date()','UUID()','try?']:self.assertNotIn(t,self.project)
  defaults=(ROOT/'replica/Sources/PastoCore/Models.swift').read_text();self.assertIn('colorHex: String = "#FF9500"',defaults);self.assertIn('?? "#FF9500"',s)
 def test_shared_snapshot_read_and_prior_tab_gate_remain_bound_as_historical_evidence(self):
  for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_native_tab_list_delivery_bytes(ROOT/p)).hexdigest(),h)
  reader=(ROOT/'replica/Sources/PastoCore/ClipboardSnapshotReader.swift').read_text();self.assertIn('pinboards: lists.project(fetch("Pinboard").map',body(reader,'func read()'))
  ui=(ROOT/'.local/p0-repair/phase-164/before/replica/Sources/Pasto/UI/PanelViews.swift').read_text();self.assertIn('for board in state.store.pinboards.sorted',body(ui,'private var boardTabs:'));state=(ROOT/'.local/p0-repair/phase-164/before/replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text();self.assertIn('self.store.pinboards.first',body(state,'private func installListSelectionDelivery()'));self.assertFalse(self.p['finite_contract_completed']);self.assertEqual(self.p['new_confirmed_pending_records'],1)
 def test_six_creation_neighbor_methods_and_all247_sources_are_exactly_bound_without_runtime_completion_claim(self):
  self.assertEqual(len(self.p['unchanged_methods']),6)
  for r in self.p['unchanged_methods']:self.assertEqual(hashlib.sha256(body(pre_native_list_name_color((ROOT/r['path']).read_text()),r['symbol']).encode()).hexdigest(),r['sha256'])
  self.assertEqual(len(CHANGES),1);changed=[]
  for p,h in self.base['production'].items():
   if hashlib.sha256(pre_native_tab_list_delivery_bytes(ROOT/p)).hexdigest()!=h:changed.append(p)
   self.assertEqual(hashlib.sha256(pre_native_group_read_projection_bytes(ROOT/p)).hexdigest(),h)
  self.assertEqual(changed,[self.path]);self.assertFalse(self.p['runtime_executed']);self.assertFalse(self.p['full_function_migration_verified'])
if __name__=='__main__':unittest.main()
