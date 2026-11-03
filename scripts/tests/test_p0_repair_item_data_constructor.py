"""Actual local entity wrapper ownership and both queue-confined readers, source only."""
from pathlib import Path
import hashlib,json,re,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from item_creation_date_scope_contract import pre_item_creation_date,pre_item_creation_date_bytes
from item_data_constructor_scope_contract import CHANGES,pre_item_data_constructor,pre_item_data_constructor_bytes
class ItemDataConstructor(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.phase=ROOT/'.local/p0-repair/phase-153';cls.p=json.loads((cls.phase/'item-data-constructor-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.data=pre_item_creation_date((ROOT/'replica/Sources/PastoCore/ClipboardItemDataPersistence.swift').read_text());cls.repo=pre_item_creation_date((ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text());cls.search=(ROOT/'replica/Sources/PastoCore/ClipboardSearchRecord.swift').read_text();cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split('idx={r[\'address\']',1)[0],cls.n)
 def test_six_original_fragments_and_previous_actual_class_evidence_bound(self):
  self.assertEqual(len(self.p['original_fragments']),6)
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for k in ['binary','decoder','original_class_evidence','prior_diagnostic_evidence']:
   r=self.p[k];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
 def test_original_actual_class_has_constructor_destructor_and_direct_nonSyncable_parent(self):
  c=self.p['original_class'];self.assertEqual(c['name'],'_TtC9PasteCore14ItemDataEntity');self.assertEqual({r['selector']:r['implementation']for r in c['methods']},{'initWithEntity:insertIntoManagedObjectContext:':'0x10031b440','.cxx_construct':'0x10031b494','.cxx_destruct':'0x10031b59c'})
  v=self.p['ItemData_parent_import']['pointer'];self.assertEqual(self.n['read'](int(v['address'],16),8).hex(),v['bytes']);self.assertEqual(self.p['ItemData_parent_import']['symbol'],'_OBJC_CLASS_$_NSManagedObject')
 def test_original_constructor_wrapper_call_and_destructor_release_calls_are_real_ARM(self):
  self.assertEqual(len(self.p['ARM_calls']),2)
  for r in self.p['ARM_calls']:
   a=int(r['address'],16);b=self.n['read'](a,4);self.assertEqual(b.hex(),r['bytes']);w=int.from_bytes(b,'little');self.assertEqual(w&0xfc000000,0x94000000);d=w&0x3ffffff;d=d-(1<<26)if d&(1<<25)else d;self.assertEqual(a+4*d,int(r['target'],16))
 def test_actual_class_owns_nonlazy_named_wrapper_without_date_or_sync_hooks(self):
  s=body(self.data,'final class PastoItemDataEntity:');self.assertIn('@objc(PastoItemDataEntity)',self.data);self.assertIn('final class PastoItemDataEntity: NSManagedObject',self.data);self.assertIn('let diagnostics = OriginalNamedDiagnostic.f_1000d4624(name: "ItemDataEntity")',s)
  for token in ['lazy var','static let','awakeFromInsert','willSave','createdAt','updatedAt','telemetry','useBinaryPlist']:self.assertNotIn(token,s)
  self.assertEqual(set(self.p['original_fields']),{'item','rawPasteboardItems'})
 def test_current_model_binds_actual_class_and_twelve_legacy_descriptions_keep_their_prior_bindings(self):
  model=body(self.repo,'private static func makeModel(');self.assertIn('includeNativeItemData && includeTypedItemData',model);self.assertIn('model.entitiesByName["ItemDataEntity"]!.managedObjectClassName = NSStringFromClass(PastoItemDataEntity.self)',model)
  migration=body(self.repo,'private static func migrateLegacyStoreIfNeeded(');calls=[x for x in migration.splitlines()if x.strip().startswith('makeModel(')];self.assertEqual(len(calls),12);self.assertTrue(all('includeTypedItemData: false'in x for x in calls))
  before=(self.phase/'before/replica/Sources/PastoCore/ClipboardPersistence.swift').read_text();old=body(before,'private static func migrateLegacyStoreIfNeeded(');self.assertEqual(migration[migration.index('        // The older history'):],old[old.index('        // The older history'):]);self.assertEqual(body(self.data,'static func addEntity('),body((self.phase/'before/replica/Sources/PastoCore/ClipboardItemDataPersistence.swift').read_text(),'static func addEntity('))
 def test_main_and_private_search_readers_use_the_same_actual_object_wrapper_before_old_fallback(self):
  main=body(self.data,'private static func diagnostics(');self.assertLess(main.index('data as? PastoItemDataEntity'),main.index('objc_getAssociatedObject'));self.assertIn('return data.diagnostics',main);self.assertIn('return readRepresentations(from: data) { diagnostics(for: data) }',body(self.data,'static func readItems('))
  search=body(self.search,'private func read<T>');self.assertLess(search.index('data as? PastoItemDataEntity'),search.index('OriginalNamedDiagnostic.f_1000d4624(name: "ItemDataEntity")'));self.assertIn('return data.diagnostics',search);self.assertIn('context.performAndWait',search);self.assertNotIn('diagnosticsKey',search)
 def test_raw_exception_decoder_and_lazy_sink_resolution_body_unchanged(self):
  s=body(self.data,'static func readRepresentations(');self.assertEqual(hashlib.sha256(s.encode()).hexdigest(),self.p['raw_reader_body_sha256']);self.assertIn('catch let error as OriginalObjCExceptionError',s);self.assertIn('return []',s)
  local=(ROOT/'replica/Sources/PastoCore/OriginalLocalDiagnostics.swift').read_text();factory=body(local,'public static func f_1000d4624(');self.assertNotIn('f_1000da768',factory);self.assertIn('OriginalNamedDiagnostic(name: name)',factory);self.assertIn('Self.factoryDependency.f_1000da768()(name)',body(local,'public func f_1000d468c('))
 def test_all247_production_files_exactly_reverse_with_only_three_changed_and_five_shared_unchanged(self):
  self.assertEqual(len(CHANGES),7);changed=[]
  for p,h in self.base['production'].items():
   if hashlib.sha256(pre_item_creation_date_bytes(ROOT/p)).hexdigest()!=h:changed.append(p)
   self.assertEqual(hashlib.sha256(pre_item_data_constructor_bytes(ROOT/p)).hexdigest(),h)
  self.assertEqual(set(changed),set(self.p['current_sources']))
  for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_item_creation_date_bytes(ROOT/p)).hexdigest(),h)
  for p in changed:self.assertEqual(pre_item_data_constructor((self.phase/'before'/p).read_text()),(self.phase/'before'/p).read_text())
  self.assertFalse(self.p['full_function_migration_verified']);self.assertFalse(self.p['runtime_executed'])
if __name__=='__main__':unittest.main()
