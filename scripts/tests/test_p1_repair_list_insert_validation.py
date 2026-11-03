"""Native List insertion hook and original error branches; source/Mach-O only."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from source_entity_lifecycle_scope_contract import pre_source_entity_lifecycle,pre_source_entity_lifecycle_bytes
from item_shared_will_save_scope_contract import pre_item_shared_will_save
from list_insert_validation_scope_contract import CHANGES,pre_list_insert_validation,pre_list_insert_validation_bytes

class ListInsertValidation(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.phase=ROOT/'.local/p0-repair/phase-149';cls.p=json.loads((cls.phase/'list-insert-validation-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.src={Path(p).stem:pre_source_entity_lifecycle((ROOT/p).read_text())for p in cls.p['current_sources']};cls.list=body(cls.src['OriginalManagedItem'],'class PastoListEntity:');cls.meta=body(cls.src['OriginalManagedItem'],'class PastoListMetadataEntity:');cls.validator=body(cls.list,'override func validateForInsert()');cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
 def order(self,s,tokens):
  pos=0
  for t in tokens:pos=s.index(t,pos)+len(t)
 def test_seventeen_original_fragments_and_prior_missing_hook_evidence_bound(self):
  self.assertEqual(len(self.p['original_fragments']),17)
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for r in [self.p['binary'],self.p['decoder'],self.p['prior_evidence']]+self.p['sdk']:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
 def test_actual_List_and_Metadata_parent_has_no_custom_super_validator(self):
  classes=self.p['original_classes'];self.assertEqual(len(classes),3)
  for c in classes:
   for r in [c['class_data'],c['ro'],c['method_list']]:self.assertEqual(self.n['read'](int(r['address'],16),len(bytes.fromhex(r['bytes']))).hex(),r['bytes'])
  for c in classes[:2]:self.assertEqual(int.from_bytes(bytes.fromhex(c['class_data']['bytes'])[8:16],'little')&((1<<36)-1),0xf98690)
  self.assertIn(('validateForInsert:','0x100329ec0'),[(m['selector'],m['implementation'])for m in classes[0]['methods']]);self.assertNotIn('validateForInsert:',[m['selector']for m in classes[-1]['methods']])
 def test_fetch_failure_ARM_releases_error_and_loads_real_empty_array_import(self):
  self.assertEqual(len(self.p['extra_ARM_words']),21)
  for r in self.p['extra_ARM_words']:self.assertEqual(self.n['read'](int(r['address'],16),4).hex(),r['bytes'])
  r=self.p['fetch_error_fallback'];self.assertEqual(self.n['read'](int(r['pointer']['address'],16),8).hex(),r['pointer']['bytes']);self.assertIn('swiftEmptyArrayStorage',r['symbol']);self.assertEqual(int.from_bytes(self.n['read'](0x10032af1c,4),'little')&0x7f000000,0x34000000)
 def test_original_small_strings_bind_index_sort_and_createdAt(self):
  def small(addresses):return sum(((int.from_bytes(self.n['read'](a,4),'little')>>5)&65535)<<(16*i)for i,a in enumerate(addresses)).to_bytes(8,'little')
  self.assertEqual(small([0x10032b504,0x10032b508,0x10032b50c])[:5],b'index');self.assertEqual(small([0x1003b4924,0x1003b4928,0x1003b492c,0x1003b4930]),b'createdA');self.assertEqual((int.from_bytes(self.n['read'](0x1003b4934,4),'little')>>5)&65535,ord('t'))
 def test_real_subclasses_supply_defaults_and_same_generic_factory(self):
  self.assertIn('@objc(PastoListEntity)',self.src['OriginalManagedItem']);self.assertIn('@objc(PastoListMetadataEntity)',self.src['OriginalManagedItem'])
  self.assertIn('[NSSortDescriptor(key: "metadata.index", ascending: true)]',self.list);self.assertIn('[NSSortDescriptor(key: "index", ascending: true)]',self.meta)
  self.assertIn('OriginalManagedFetchRequest.make(for: PastoListEntity.self)',body(self.list,'static func listFetchRequest()'));self.assertIn('OriginalManagedFetchRequest.make(for: PastoListMetadataEntity.self)',body(self.meta,'static func metadataFetchRequest()'))
  factory=body(self.src['OriginalManagedItem'],'static func make<Entity:');self.order(factory,['entity.entityName','entity.defaultSortDescriptors','entity.defaultPredicate','request.fetchBatchSize = 20','return request'])
 def test_current_model_binds_two_actual_classes_only_under_current_flag(self):
  s=self.src['ClipboardPersistence'];self.assertIn('includeTypedLists: Bool = true',s);model=body(s,'private static func makeModel(');typed=body(model,'if includeLists && includeTypedLists');self.assertEqual(typed.count('managedObjectClassName = NSStringFromClass'),2);self.assertIn('PastoListEntity.self',typed);self.assertIn('PastoListMetadataEntity.self',typed)
  self.assertEqual(pre_list_insert_validation(s),(self.phase/'before'/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text())
 def test_all_ten_legacy_models_retain_untyped_source_classes_and_original_tail(self):
  s=body(self.src['ClipboardPersistence'],'private static func migrateLegacyStoreIfNeeded(');old=body((self.phase/'before'/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text(),'private static func migrateLegacyStoreIfNeeded(')
  a,rest=s.split('        let legacyCandidates = [',1);rows,tail=rest.split('\n        ]',1);b,rest=old.split('        let legacyCandidates = [',1);oldrows,oldtail=rest.split('\n        ]',1);self.assertEqual((a,tail),(b,oldtail));lines=rows.splitlines();calls=[v for v in lines if 'makeModel('in v];self.assertEqual(len(calls),10);self.assertTrue(all('includeTypedLists: false'in v for v in calls));self.assertEqual('\n'.join(lines[2:]).replace(', includeTypedLists: false',''),oldrows.lstrip('\n'))
 def test_outer_guard_keeps_existing_deleted_and_detached_inputs_on_super_tail(self):
  s=self.validator;self.assertIn('if !isDeleted, value(forKey: "metadata") == nil, let context = managedObjectContext',s);self.assertTrue(s.rstrip().endswith('try super.validateForInsert()\n    }'));self.assertNotIn('return',s)
 def test_lookup_uses_original_String_bridge_identifier_limit_offset_and_sync_context(self):
  s=self.validator;self.order(s,['"list:" + String._unconditionallyBridgeFromObjectiveC','value(forKey: "identifier") as? NSString','PastoListMetadataEntity.metadataFetchRequest()','request.predicate = NSPredicate(format: "identifier == %@", identifier)','request.fetchLimit = 1','request.fetchOffset = 0','context.performAndWait { existing = (try? context.fetch(request))?.first }','if let existing'])
 def test_existing_metadata_is_only_attached_without_renumbering_or_recreation(self):
  self.assertEqual(body(self.validator,'if let existing').strip(),'{\n                setValue(existing, forKey: "metadata")\n            }')
 def test_new_metadata_all_query_has_default_ascending_order_without_limit(self):
  s=self.validator[self.validator.index('let all ='):];self.order(s,['PastoListMetadataEntity.metadataFetchRequest()','all.fetchOffset = 0','context.performAndWait { values = (try? context.fetch(all)) ?? [] }','values.last'])
  for t in ['all.predicate =','all.fetchLimit =','sorted(','max(','min(']:self.assertNotIn(t,s)
 def test_last_index_empty_scalar_default_and_checked_add_precede_allocation(self):
  s=self.validator;self.order(s,['if let last = values.last','last.value(forKey: "index") as? NSNumber','int64Value ?? 0','lastIndex = -1','let nextIndex = lastIndex + 1','let metadata = PastoListMetadataEntity(context: context)'])
  for t in ['&+','addingReportingOverflow','wrapping','clamped']:self.assertNotIn(t,s)
 def test_new_metadata_sets_identity_owner_and_index_before_attaching_and_awake_calls_super(self):
  s=self.validator;self.order(s,['metadata.setValue(identifier, forKey: "identifier")','metadata.setValue(self, forKey: "list")','metadata.setValue(nextIndex, forKey: "index")','setValue(metadata, forKey: "metadata")','try super.validateForInsert()'])
  for cls in [self.list,self.meta]:self.assertEqual(body(cls,'override func awakeFromInsert()').strip(),'{\n        super.awakeFromInsert()\n        setPrimitiveValue(Date(), forKey: "createdAt")\n    }')
 def test_actual_menu_FRC_producer_and_optional_class_lookup_use_typed_List(self):
  self.assertIn('-> NSFetchRequest<PastoListEntity>',self.src['ClipboardListPersistence']);req=body(self.src['ClipboardListPersistence'],'func pinboardRequest()');self.order(req,['PastoListEntity.listFetchRequest()','rawType == %d','return request']);col=body(self.src['ClipboardSearchCollection'],'public final class ClipboardPinboardCollection');self.assertIn('NSFetchedResultsController<PastoListEntity>',col);self.assertIn('request: NSFetchRequest<PastoListEntity>',col);self.assertIn('(try? context.existingObject(with: objectID)) as? PastoListEntity',col)
 def test_eight_hunks_four_files_and247_inverse_keep_ten_methods_and_five_consumers(self):
  self.assertEqual(len(CHANGES),8);self.assertEqual(len(set(r[0]for r in CHANGES)),4);changed=[]
  for p,h in self.base['production'].items():
   if hashlib.sha256(pre_source_entity_lifecycle_bytes(ROOT/p)).hexdigest()!=h:changed.append(p)
   self.assertEqual(hashlib.sha256(pre_list_insert_validation_bytes(ROOT/p)).hexdigest(),h)
  self.assertEqual(set(changed),set(self.p['current_sources']))
  for r in self.p['unchanged_methods']:self.assertEqual(hashlib.sha256(body(pre_item_shared_will_save((ROOT/r['path']).read_text()),r['symbol']).encode()).hexdigest(),r['sha256'])
  for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_source_entity_lifecycle_bytes(ROOT/p)).hexdigest(),h)
 def test_super_error_not_swallowed_and_no_runtime_model_claim(self):
  self.assertEqual(self.validator.count('try super.validateForInsert()'),1);self.assertNotIn('try? super',self.validator);self.assertNotIn('catch',self.validator);self.assertEqual(self.validator.count('try? context.fetch'),2)
  self.assertFalse(self.p['runtime_executed']);self.assertFalse(self.p['full_function_migration_verified']);self.assertEqual(self.p['repaired_existing_records'],1);self.assertEqual(self.p['new_difference_records'],0)

if __name__=='__main__':unittest.main()
