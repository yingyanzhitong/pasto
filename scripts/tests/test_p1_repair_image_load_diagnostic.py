"""Exact local image-load warning and actual deferred consumer; no context/framework execution."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from preview_commit_error_scope_contract import pre_preview_commit_error_bytes
from image_load_diagnostic_scope_contract import CHANGES,pre_image_load_diagnostic,pre_image_load_diagnostic_bytes
class ImageLoadDiagnostic(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.phase=ROOT/'.local/p0-repair/phase-156';cls.p=json.loads((cls.phase/'image-load-diagnostic-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.path=next(iter(cls.p['current_sources']));cls.s=(ROOT/cls.path).read_text();cls.read=body(cls.s,'private func read<T>');cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
 def test_six_original_fragments_binary_decoder_and_prior_content_evidence_bound(self):
  self.assertEqual(len(self.p['original_fragments']),6)
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for k in ['binary','decoder','prior_content_evidence']:
   r=self.p[k];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
 def test_real_ARM_existing_object_raw_reader_image_extractor_and_warning_calls(self):
  self.assertEqual(len(self.p['ARM_calls']),5)
  for r in self.p['ARM_calls']:
   a=int(r['address'],16);b=self.n['read'](a,4);self.assertEqual(b.hex(),r['bytes']);w=int.from_bytes(b,'little');self.assertEqual(w&0xfc000000,0x94000000);d=w&0x3ffffff;d=d-(1<<26)if d&(1<<25)else d;self.assertEqual(a+4*d,int(r['target'],16))
  for r in self.p['ARM_words']:self.assertEqual(self.n['read'](int(r['address'],16),4).hex(),r['bytes'])
 def test_exact_original_name_image_warning_prefix_and_warning_level_two(self):
  self.assertEqual([r['value']for r in self.p['strings']],['init(_:coordinator:)','Failed to load image content: ','search-indexer.imageContent'])
  for r in self.p['strings']:self.assertEqual(self.n['read'](int(r['address'],16),120).split(b'\0')[0].decode(),r['value'])
  self.assertIn('imageDiagnostics.f_1000d468c().f_1000d4df0("Failed to load image content: \\(error.localizedDescription)")',self.read);local=(ROOT/'replica/Sources/PastoCore/OriginalLocalDiagnostics.swift').read_text();self.assertIn('emit(level: 2, message: message)',body(local,'public func f_1000d4df0('))
 def test_actual_image_consumer_reuses_held_wrapper_and_preserves_first_non_nil_image_extraction(self):
  image=body(self.s,'func imageData()');self.assertIn('read(imageDiagnostics: contentDiagnostics) { _, items in items.compactMap { $0.f_10037d5c4() }.first }',image);self.assertNotIn('OriginalNamedDiagnostic.f_',image);self.assertNotIn('Task',image);self.assertIn('private let contentDiagnostics = OriginalNamedDiagnostic.f_1000d4624(name: "init(_:coordinator:)")',self.s)
 def test_failed_load_warns_and_returns_nil_before_outer_generic_error_while_wrong_type_stays_silent_for_image(self):
  s=self.read;tokens=['do { object = try context.existingObject(with: objectID) }','catch {','guard let contentDiagnostics else {','if let imageDiagnostics {','Failed to load image content:','return nil','throw error','Failed to load item content:','return nil','guard object.entity.name == "Item"'];pos=0
  for t in tokens:pos=s.index(t,pos)+len(t)
  wrong=body(s,'guard object.entity.name == "Item" else');self.assertIn('contentDiagnostics?.',wrong);self.assertNotIn('imageDiagnostics',wrong)
 def test_each_evaluation_still_builds_private_context_before_queue_confined_object_and_raw_data_read(self):
  s=self.read;tokens=['NSManagedObjectContext(concurrencyType: .privateQueueConcurrencyType)','context.persistentStoreCoordinator = coordinator','context.performAndWait','OriginalObjCExceptionBridge.withResult','context.existingObject(with: objectID)','object.value(forKey: "data") as? NSManagedObject','ClipboardItemDataPersistence.readRepresentations(from: data','return try project(object, items)'];pos=0
  for t in tokens:pos=s.index(t,pos)+len(t)
  self.assertEqual(s.count('NSManagedObjectContext('),1);self.assertNotIn('context.save',s);self.assertNotIn('context.reset',s)
 def test_six_neighbor_methods_seven_shared_sources_and_no_telemetry_effects_are_preserved(self):
  for r in self.p['unchanged_methods']:self.assertEqual(hashlib.sha256(body((ROOT/r['path']).read_text(),r['symbol']).encode()).hexdigest(),r['sha256'])
  for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_preview_commit_error_bytes(ROOT/p)).hexdigest(),h)
  self.assertEqual(len(self.p['unchanged_methods']),6);self.assertEqual(len(self.p['shared_sources']),7);self.assertNotIn('search-indexer.imageContent',self.s)
  for k in ['after_local_warning_dependency_call','indirect_sink_call']:
   r=self.p['telemetry_excluded'][k];self.assertEqual(self.n['read'](int(r['address'],16),4).hex(),r['bytes'])
 def test_three_exact_hunks_one_source_reverse247_current_files_without_full_migration_claim(self):
  self.assertEqual(len(CHANGES),3);self.assertEqual(sum(v[3]for v in CHANGES),3);changed=[]
  for p,h in self.base['production'].items():
   if hashlib.sha256(pre_preview_commit_error_bytes(ROOT/p)).hexdigest()!=h:changed.append(p)
   self.assertEqual(hashlib.sha256(pre_image_load_diagnostic_bytes(ROOT/p)).hexdigest(),h)
  self.assertEqual(changed,[self.path]);self.assertEqual(pre_image_load_diagnostic((self.phase/'before'/self.path).read_text()),(self.phase/'before'/self.path).read_text());self.assertFalse(self.p['full_function_migration_verified']);self.assertFalse(self.p['runtime_executed'])
if __name__=='__main__':unittest.main()
