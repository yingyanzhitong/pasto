"""Required native creation field and original insertion callback, with lossless old-store boundary checks."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from raw_data_nil_bridge_scope_contract import pre_raw_data_nil_bridge
from image_load_diagnostic_scope_contract import pre_image_load_diagnostic,pre_image_load_diagnostic_bytes
from item_creation_date_scope_contract import CHANGES,pre_item_creation_date,pre_item_creation_date_bytes
class ItemCreationDate(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.phase=ROOT/'.local/p0-repair/phase-155';cls.p=json.loads((cls.phase/'item-creation-date-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.entities=(ROOT/'replica/Sources/PastoCore/OriginalManagedItem.swift').read_text();cls.repo=(ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text();cls.data=(ROOT/'replica/Sources/PastoCore/ClipboardItemDataPersistence.swift').read_text();cls.policy=body(cls.data,'override func createRelationships(')
 def test_four_original_fragments_model_parent_and_diagnostic_evidence_bound(self):
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  self.assertEqual(len(self.p['original_fragments']),4)
  for k in ['binary','decoder','original_Item_class_evidence','original_awake_evidence','original_diagnostic_evidence','original_model']:
   r=self.p[k];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
 def test_original_model_createdAt_required_date_and_timestamp_optional_separate(self):
  fields=self.p['original_model']['ItemEntity_fields'];self.assertEqual(fields['createdAt']['NSAttributeType'],900);self.assertFalse(fields['createdAt'].get('NSIsOptional',False));self.assertTrue(fields['timestamp']['NSIsOptional']);self.assertEqual(fields['timestamp']['NSAttributeType'],900)
  model=body(self.repo,'private static func makeModel(');self.assertIn('if includeNativeCreationDate { itemAttributes.append(attribute("createdAt", .dateAttributeType)) }',model);self.assertIn('value.isOptional = optional',model);self.assertIn('optional: Bool = false',model);self.assertIn('attribute("timestamp", .dateAttributeType, optional: includeOptionalTimestamp)',model)
 def test_actual_Item_insertion_callback_matches_existing_original_parent_body(self):
  item=body(self.entities,'class PastoItemEntity:');aw=body(item,'override func awakeFromInsert()');self.assertEqual(aw,body(body(self.entities,'class PastoListEntity:'),'override func awakeFromInsert()'));self.assertLess(aw.index('super.awakeFromInsert()'),aw.index('setPrimitiveValue(Date(), forKey: "createdAt")'));self.assertNotIn('timestamp',aw);self.assertNotIn('updatedAt',aw)
  p=json.loads((ROOT/self.p['original_Item_class_evidence']['path']).read_text());self.assertIn('original_Item',p)
 def test_existing_empty_content_diagnostic_KVC_now_has_a_real_field_and_does_not_use_recency_fallback(self):
  src=pre_image_load_diagnostic((ROOT/'replica/Sources/PastoCore/ClipboardSearchRecord.swift').read_text());diag=body(src,'private func diagnoseEmptyContent(');self.assertIn('object.value(forKey: "createdAt") as? Date',diag);self.assertNotIn('localCreatedAt',diag);self.assertNotIn('timestamp',diag);self.assertIn('attribute("createdAt", .dateAttributeType)',self.repo);self.assertEqual(hashlib.sha256(src.encode()).hexdigest(),self.p['shared_sources']['replica/Sources/PastoCore/ClipboardSearchRecord.swift'])
 def test_all_thirteen_legacy_models_explicitly_restore_old_creation_field_shape(self):
  migration=body(self.repo,'private static func migrateLegacyStoreIfNeeded(');rows=[x for x in migration.splitlines()if x.strip().startswith('makeModel(')];self.assertEqual(len(rows),13);self.assertTrue(all('includeNativeCreationDate: false'in row for row in rows));before=(self.phase/'before/replica/Sources/PastoCore/ClipboardPersistence.swift').read_text();self.assertEqual(pre_item_creation_date(self.repo),before)
 def test_mapping_policy_attaches_when_either_required_native_field_or_data_graph_is_missing(self):
  m=body(self.repo,'private static func migrateLegacyStoreIfNeeded(');gate='sourceModel.entitiesByName["ItemDataEntity"] == nil\n            || sourceModel.entitiesByName["Item"]?.attributesByName["createdAt"] == nil';self.assertIn(gate,m);self.assertIn('where entity.destinationEntityName == "Item"',m);self.assertIn('entity.entityMigrationPolicyClassName = NSStringFromClass(PastoItemDataMigrationPolicy.self)',m);self.assertLess(m.index('try manager.migrateStore('),m.index('try coordinator.replacePersistentStore('))
 def test_backfill_uses_single_associated_source_old_local_date_then_timestamp_before_existing_data_exit(self):
  s=self.policy;tokens=['try super.createRelationships','manager.sourceModel.entitiesByName["Item"]?.attributesByName["createdAt"] == nil','manager.sourceInstances(forEntityMappingName: mapping.name, destinationInstances: [object])','sources.count == 1','source.entity.attributesByName["localCreatedAt"] != nil','source.value(forKey: "localCreatedAt") as? Date','localDate ?? source.value(forKey: "timestamp") as? Date','object.setPrimitiveValue(createdAt, forKey: "createdAt")','guard object.value(forKey: "data") == nil else { return }'];positions=[s.index(t)for t in tokens];self.assertEqual(positions,sorted(positions));date=s[:s.index('guard object.value(forKey: "data")')];self.assertEqual(date.count('throw CocoaError(.fileReadCorruptFile)'),2)
  for t in ['Date()','Date(timeIntervalSince','reset()','rollback()','context.save','manager.sourceContext.save']:self.assertNotIn(t,date)
 def test_five_native_writer_projection_raw_methods_and_four_shared_files_unchanged(self):
  self.assertEqual(len(self.p['unchanged_methods']),5)
  for r in self.p['unchanged_methods']:self.assertEqual(hashlib.sha256(body(pre_raw_data_nil_bridge((ROOT/r['path']).read_text()),r['symbol']).encode()).hexdigest(),r['sha256'])
  for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_image_load_diagnostic_bytes(ROOT/p)).hexdigest(),h)
  store=(ROOT/'replica/Sources/PastoCore/ClipboardStore.swift').read_text();self.assertNotIn('forKey: "createdAt"',store)
 def test_sdk_association_and_pre_validation_policy_contract_are_local_headers_only(self):
  for p,h in self.p['SDK_headers'].items():self.assertEqual(hashlib.sha256(pre_image_load_diagnostic_bytes(ROOT/p)).hexdigest(),h)
  headers='\n'.join((ROOT/p).read_text()for p in self.p['SDK_headers']);self.assertIn('sourceInstancesForEntityMappingNamed:',headers);self.assertIn('destinationInstances:',headers);self.assertIn('createRelationshipsForDestinationInstance:',headers);self.assertFalse(self.p['runtime_executed']);self.assertFalse(self.p['full_function_migration_verified'])
 def test_seven_exact_hunks_reverse_all247_sources_with_only_three_files_changed(self):
  self.assertEqual(len(CHANGES),7);self.assertEqual(sum(x[3]for x in CHANGES),7);changed=[]
  for p,h in self.base['production'].items():
   if hashlib.sha256(pre_image_load_diagnostic_bytes(ROOT/p)).hexdigest()!=h:changed.append(p)
   self.assertEqual(hashlib.sha256(pre_item_creation_date_bytes(ROOT/p)).hexdigest(),h)
  self.assertEqual(set(changed),set(self.p['current_sources']))
  for p in changed:self.assertEqual(pre_item_creation_date((self.phase/'before'/p).read_text()),(self.phase/'before'/p).read_text())
if __name__=='__main__':unittest.main()
