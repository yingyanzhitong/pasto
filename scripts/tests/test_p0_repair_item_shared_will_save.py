"""Item gains the actual native parent callback; code and metadata comparisons only."""
from pathlib import Path
import hashlib,json,re,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from save_failure_rollback_scope_contract import pre_save_failure_rollback
from test_offline_p0_contracts import body
from source_entity_lifecycle_scope_contract import pre_source_entity_lifecycle,pre_source_entity_lifecycle_bytes
from item_shared_will_save_scope_contract import CHANGES,pre_item_shared_will_save,pre_item_shared_will_save_bytes

class ItemSharedWillSave(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.phase=ROOT/'.local/p0-repair/phase-151';cls.p=json.loads((cls.phase/'item-shared-will-save-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.path='replica/Sources/PastoCore/OriginalManagedItem.swift';cls.s=pre_source_entity_lifecycle((ROOT/cls.path).read_text());cls.before=(cls.phase/'before'/cls.path).read_text();cls.baseclass=body(cls.s,'class PastoManagedObject:');cls.callback=body(cls.baseclass,'override func willSave()');cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
 def test_original_fragments_prior_real_parent_callback_and_same_baseline_are_bound(self):
  self.assertEqual(len(self.p['original_fragments']),4)
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for r in [self.p['binary'],self.p['decoder'],self.p['prior_evidence']]:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
  old=json.loads((ROOT/self.p['prior_evidence']['path']).read_text());self.assertEqual(hashlib.sha256(self.before.encode()).hexdigest(),old['current_sources'][self.path])
 def test_Item_actual_class_parent_and_complete_one_entry_instance_method_table(self):
  r=self.p['original_Item'];self.assertEqual(r['class_name'],'_TtC9PasteCore10ItemEntity');self.assertEqual(r['parent'],'0x100f98690');self.assertEqual(r['single_method'],'initWithEntity:insertIntoManagedObjectContext:');self.assertEqual(r['single_imp'],'0x10032029c')
  for key in ['class_data','class_ro','method_list']:
   v=r[key];self.assertEqual(self.n['read'](int(v['address'],16),len(bytes.fromhex(v['bytes']))).hex(),v['bytes'])
  self.assertEqual(int.from_bytes(bytes.fromhex(r['class_data']['bytes'])[8:16],'little')&((1<<36)-1),0xf98690);self.assertEqual(struct.unpack_from('<I',bytes.fromhex(r['method_list']['bytes']),4)[0],1)
 def test_real_dispatch_is_one_common_override_and_exactly_three_known_subclasses(self):
  self.assertEqual(self.s.count('override func willSave()'),1);names=re.findall(r'class (\w+): PastoManagedObject\s*\{',self.s);self.assertEqual(names,['PastoItemEntity','PastoListEntity','PastoListMetadataEntity'])
  for name in names:self.assertNotIn('override func willSave()',body(self.s,'class '+name+':'))
  model=(ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text();self.assertIn('NSStringFromClass(PastoItemEntity.self)',model);self.assertIn('NSStringFromClass(PastoListEntity.self)',model);self.assertIn('NSStringFromClass(PastoListMetadataEntity.self)',model)
 def test_callback_only_inherits_into_models_with_updatedAt_no_global_managed_object_change(self):
  persistence=(ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text();lists=(ROOT/'replica/Sources/PastoCore/ClipboardListPersistence.swift').read_text();self.assertIn('attribute("updatedAt", .dateAttributeType)',body(persistence,'private static func makeModel('));self.assertEqual(body(lists,'static func addEntities(').count('attribute("updatedAt", .dateAttributeType, optional: true)'),2)
  self.assertNotIn('override func awakeFromInsert()',self.baseclass);self.assertNotIn('createdAt',self.baseclass)
  raw=(ROOT/'replica/Sources/PastoCore/ClipboardItemDataPersistence.swift').read_text();self.assertIn('data.managedObjectClassName = "NSManagedObject"',raw);self.assertNotIn('updatedAt',body(raw,'static func addEntity('))
 def test_native_writers_and_native_index_version_reader_remain_unchanged(self):
  for r in self.p['unchanged_native_methods']:
   s=body(pre_save_failure_rollback((ROOT/r['path']).read_text()),r['symbol']);self.assertEqual(hashlib.sha256(s.encode()).hexdigest(),r['sha256'])
  p=(ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text();restore=body(p,'func restoreHistoryItems(');self.assertIn('object.setValue(timestamp, forKey: "timestamp")',restore);self.assertNotIn('updatedAt',restore);self.assertIn('nativeRestoreWithoutValue',body(p,'func commit<T>'))
  move=body((ROOT/'replica/Sources/PastoCore/ClipboardListPersistence.swift').read_text(),'func moveItems(');self.assertIn('item.setValue(pinboard, forKey: "list")',move);self.assertNotIn('updatedAt',move)
 def test_existing_List_Metadata_callback_bodies_identical_after_inheritance(self):
  digest=hashlib.sha256(self.callback.encode()).hexdigest();self.assertEqual(digest,self.p['shared_callback_sha256'])
  for cls in ['class PastoListEntity:','class PastoListMetadataEntity:']:
   old=body(self.before,cls);self.assertEqual(self.callback,body(old,'override func willSave()'));self.assertEqual(body(self.s,cls),old.replace(CHANGES[0][1],CHANGES[0][2],1))
  self.assertEqual(body(self.s,'class PastoItemEntity:'),body(self.before,'class PastoItemEntity:'));self.assertEqual(body(self.s,'enum OriginalManagedFetchRequest'),body(self.before,'enum OriginalManagedFetchRequest'))
 def test_original_gates_primitive_date_and_super_kept_no_extra_actor_or_save(self):
  for t in ['let isSyncApply = managedObjectContext?.transactionAuthor == "syncApply"','if !isInserted && !isSyncApply && !changedValues().isEmpty','setPrimitiveValue(Date(), forKey: "updatedAt")','super.willSave()']:self.assertIn(t,self.callback)
  for t in ['try ','save(','Task','DispatchQueue','isDeleted','return','hasChanges','createdAt','context.save']:self.assertNotIn(t,self.callback)
  self.assertEqual(self.p['priority'],'P0');self.assertFalse(self.p['runtime_executed']);self.assertFalse(self.p['full_function_migration_verified']);self.assertEqual(self.p['new_difference_records'],0);self.assertEqual(self.p['additional_repaired_contracts'],1)
 def test_two_patterns_three_hunks_reverse247_files_and_six_shared_sources(self):
  self.assertEqual(len(CHANGES),2);self.assertEqual(sum(v[3]for v in CHANGES),3);changed=[]
  for p,h in self.base['production'].items():
   if hashlib.sha256(pre_source_entity_lifecycle_bytes(ROOT/p)).hexdigest()!=h:changed.append(p)
   self.assertEqual(hashlib.sha256(pre_item_shared_will_save_bytes(ROOT/p)).hexdigest(),h)
  self.assertEqual(changed,[self.path]);self.assertEqual(pre_item_shared_will_save(self.s),self.before);self.assertEqual(pre_item_shared_will_save(self.before),self.before)
  self.assertEqual(len(self.p['shared_sources']),6)
  for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_source_entity_lifecycle_bytes(ROOT/p)).hexdigest(),h)

if __name__=='__main__':unittest.main()
