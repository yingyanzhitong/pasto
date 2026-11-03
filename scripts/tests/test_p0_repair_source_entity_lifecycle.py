"""Source class/model/constructor wiring, preserving native data's non-Syncable base."""
from pathlib import Path
import hashlib,json,re,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from item_data_constructor_scope_contract import pre_item_data_constructor,pre_item_data_constructor_bytes
from source_entity_lifecycle_scope_contract import CHANGES,FACTORY_CHANGES,pre_source_entity_lifecycle,pre_source_entity_lifecycle_bytes

class SourceEntityLifecycle(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.phase=ROOT/'.local/p0-repair/phase-152';cls.p=json.loads((cls.phase/'source-entity-lifecycle-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.src={Path(p).stem:pre_item_data_constructor((ROOT/p).read_text())for p in cls.p['current_sources']};cls.entities=cls.src['OriginalManagedItem'];cls.source=cls.src['ClipboardSourcePersistence'];cls.persistence=cls.src['ClipboardPersistence'];cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
 def test_nine_original_functions_binary_prior_model_and_class_inventory_bound(self):
  self.assertEqual(len(self.p['original_fragments']),9)
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for r in [self.p['binary'],self.p['decoder'],self.p['prior_evidence'],self.p['original_model'],self.p['class_inventory']]:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
 def test_real_source_class_parent_tables_and_no_own_class_default_override(self):
  for c in self.p['original_classes'][:2]:
   self.assertEqual(int.from_bytes(bytes.fromhex(c['class_data']['bytes'])[8:16],'little')&((1<<36)-1),0xf98690);self.assertEqual(len(c['methods']),1);self.assertEqual(c['methods'][0]['selector'],'initWithEntity:insertIntoManagedObjectContext:');self.assertEqual(c['class_methods'],[])
   for k in ['class_data','class_ro','metaclass','metaclass_ro']:
    v=c[k];self.assertEqual(self.n['read'](int(v['address'],16),len(bytes.fromhex(v['bytes']))).hex(),v['bytes'])
 def test_ItemData_true_NSManagedObject_import_and_model_has_no_date_fields(self):
  r=self.p['ItemData_parent_import'];self.assertEqual(r['symbol'],'_OBJC_CLASS_$_NSManagedObject');v=r['pointer'];self.assertEqual(self.n['read'](int(v['address'],16),8).hex(),v['bytes']);self.assertTrue(int.from_bytes(bytes.fromhex(v['bytes']),'little')>>63)
  fields=self.p['original_model']['schemas'];self.assertNotIn('createdAt',fields['ItemDataEntity']);self.assertNotIn('updatedAt',fields['ItemDataEntity'])
  for c in ['ApplicationEntity','DeviceEntity']:self.assertEqual(fields[c]['createdAt']['NSAttributeType'],900);self.assertEqual(fields[c]['updatedAt']['NSAttributeType'],900)
 def test_five_actual_typed_subclasses_and_same_shared_willSave_body(self):
  names=re.findall(r'class (\w+): PastoManagedObject\s*\{',self.entities);self.assertEqual(names,self.p['actual_subclasses']);self.assertEqual(len(names),5);self.assertEqual(self.entities.count('override func willSave()'),1);callback=body(body(self.entities,'class PastoManagedObject:'),'override func willSave()');self.assertEqual(hashlib.sha256(callback.encode()).hexdigest(),self.p['shared_callback_sha256'])
  for name,physical in [('PastoApplicationEntity','ApplicationEntity'),('PastoDeviceEntity','DeviceEntity')]:
   cls=body(self.entities,'class '+name+':');self.assertIn('override class var entityName: String { "'+physical+'" }',cls);self.assertEqual(body(cls,'override func awakeFromInsert()').strip(),'{\n        super.awakeFromInsert()\n        setPrimitiveValue(Date(), forKey: "createdAt")\n    }');self.assertNotIn('defaultSortDescriptors',cls);self.assertNotIn('defaultPredicate',cls)
 def test_model_current_source_flag_registers_both_classes_without_changing_old_schema(self):
  self.assertIn('includeTypedSources: Bool = true',self.persistence);s=body(self.persistence,'private static func makeModel(');gate=body(s,'if includeNativeSources && includeTypedSources');self.assertEqual(gate.count('managedObjectClassName = NSStringFromClass'),2);self.assertIn('PastoApplicationEntity.self',gate);self.assertIn('PastoDeviceEntity.self',gate);self.assertEqual(body(self.source,'static func addEntities('),body((self.phase/'before'/'replica/Sources/PastoCore/ClipboardSourcePersistence.swift').read_text(),'static func addEntities('))
 def test_all_eleven_legacy_models_preserve_ten_previous_descriptions_and_migration_tail(self):
  s=body(self.persistence,'private static func migrateLegacyStoreIfNeeded(');old=body((self.phase/'before'/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text(),'private static func migrateLegacyStoreIfNeeded(');a,rest=s.split('        let legacyCandidates = [',1);rows,tail=rest.split('\n        ]',1);b,rest=old.split('        let legacyCandidates = [',1);oldrows,oldtail=rest.split('\n        ]',1);self.assertEqual((a,tail),(b,oldtail));lines=rows.splitlines();calls=[v for v in lines if'makeModel('in v];self.assertEqual(len(calls),11);self.assertTrue(all('includeTypedSources: false'in v for v in calls));self.assertEqual('\n'.join(lines[2:]).replace(', includeTypedSources: false',''),oldrows.lstrip('\n'))
 def test_typed_first_and_current_device_use_real_factory_defaults_preserve_predicate_and_errors(self):
  first=body(self.source,'private func first<Entity:');self.assertIn('OriginalManagedFetchRequest.make(for: entity)',first);self.assertIn('request.predicate = NSPredicate(format: "%K == %@", key, value)',first);self.assertIn('request.fetchLimit = 1',first);self.assertIn('request.fetchOffset = 0',first);self.assertIn('return try context.fetch(request).first',first);self.assertNotIn('try?',first)
  current=body(self.source,'func currentDevice()');self.assertIn('OriginalManagedFetchRequest.make(for: PastoDeviceEntity.self)',current);self.assertIn('(try? context.fetch(request))?.first',current);self.assertIn('identifier == %@',current);self.assertIn('OriginalLocalDevice.f_1000f35e0()',current)
  generic=body(self.entities,'static func make<Entity:');self.assertIn('request.fetchBatchSize = 20',generic)
 def test_helpers_no_longer_write_late_creation_dates_but_keep_names_ids_color_type_and_legacy_UUID(self):
  for marker in ['func application(','func currentDevice()','private func device(named']:
   s=body(self.source,marker);self.assertNotIn('Date()',s);self.assertNotIn('forKey: "createdAt"',s)
  app=body(self.source,'func application(');self.assertIn('first(PastoApplicationEntity.self, key: "bundleIdentifier"',app);self.assertIn('forKey: "rawIcon"',app);self.assertIn('forKey: "rawColor"',app)
  legacy=body(self.source,'private func device(named');self.assertIn('first(PastoDeviceEntity.self, key: "name"',legacy);self.assertIn('UUID().uuidString',legacy);self.assertIn('object.setValue(name, forKey: "name")',legacy)
 def test_seven_other_source_operations_and_five_shared_production_files_unchanged(self):
  self.assertEqual(len(self.p['unchanged_source_methods']),7)
  for r in self.p['unchanged_source_methods']:self.assertEqual(hashlib.sha256(body(self.source,r['symbol']).encode()).hexdigest(),r['sha256'])
  for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_item_data_constructor_bytes(ROOT/p)).hexdigest(),h)
  self.assertFalse(self.p['runtime_executed']);self.assertFalse(self.p['full_function_migration_verified']);self.assertEqual(self.p['new_difference_records'],0)
 def test_twelve_exact_hunks_three_files_and_four_factories_reverse247_files_idempotently(self):
  self.assertEqual(len(CHANGES),12);self.assertEqual(sum(c[3]for c in CHANGES),12);self.assertEqual(len(FACTORY_CHANGES),4);changed=[]
  for p,h in self.base['production'].items():
   if hashlib.sha256(pre_item_data_constructor_bytes(ROOT/p)).hexdigest()!=h:changed.append(p)
   self.assertEqual(hashlib.sha256(pre_source_entity_lifecycle_bytes(ROOT/p)).hexdigest(),h)
  self.assertEqual(set(changed),set(self.p['current_sources']))
  for p in changed:self.assertEqual(pre_source_entity_lifecycle((ROOT/p).read_text()),(self.phase/'before'/p).read_text());self.assertEqual(pre_source_entity_lifecycle((self.phase/'before'/p).read_text()),(self.phase/'before'/p).read_text())

if __name__=='__main__':unittest.main()
