"""Original closure release fields and current per-evaluation context structure, static only."""
from pathlib import Path
import hashlib,json,struct,re,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
class DeferredContextOwnership(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.phase=ROOT/'.local/p0-repair/phase-157';cls.p=json.loads((cls.phase/'deferred-context-ownership-review.json').read_text());cls.s=(ROOT/'replica/Sources/PastoCore/ClipboardSearchRecord.swift').read_text();cls.producer=(ROOT/'replica/Sources/PastoCore/ClipboardSnapshotReader.swift').read_text();cls.reader=body(cls.s,'final class ClipboardSearchRecordReader');cls.read=body(cls.reader,'private func read<T>');cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
 def test_ten_original_fragments_binary_decoder_and_prior_warning_bound(self):
  self.assertEqual(len(self.p['original_fragments']),10)
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for k in ['binary','decoder','prior_image_warning']:
   r=self.p[k];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
 def test_three_actual_dyld_import_slots_and_true_names_not_disassembler_labels(self):
  self.assertEqual([r['symbol']for r in self.p['imports'][:2]],['_objc_release','_swift_release']);self.assertIn('performAndWait',self.p['imports'][2]['symbol'])
  f=self.n['fixup'][0];h=struct.unpack('<7I',self.n['raw'][f:f+28])
  for r in self.p['imports']:
   for k in ['stub','pointer']:
    v=r[k];self.assertEqual(self.n['read'](int(v['address'],16),len(bytes.fromhex(v['bytes']))).hex(),v['bytes'])
   v,c=self.n['reachable_pointer'](int(r['pointer']['address'],16));self.assertEqual(c,r['chain']);self.assertTrue(v>>63);self.assertEqual(v&0xffffff,r['ordinal']);entry=struct.unpack_from('<I',self.n['raw'],f+h[2]+4*r['ordinal'])[0];o=f+h[3]+(entry>>9);self.assertEqual(self.n['raw'][o:self.n['raw'].index(b'\0',o)].decode(),r['symbol'])
 def test_eight_actual_release_and_perform_calls_are_live_machine_edges(self):
  self.assertEqual(len(self.p['ARM_calls']),8)
  for r in self.p['ARM_calls']:
   a=int(r['address'],16);b=self.n['read'](a,4);self.assertEqual(b.hex(),r['bytes']);w=int.from_bytes(b,'little');self.assertEqual(w&0xfc000000,0x94000000);d=w&0x3ffffff;d=d-(1<<26)if d&(1<<25)else d;self.assertEqual(a+4*d,int(r['target'],16))
 def test_original_environment_field_offsets_sizes_and_private_queue_arguments_bound(self):
  for r in self.p['ARM_words']:self.assertEqual(self.n['read'](int(r['address'],16),4).hex(),r['bytes'])
  for a,offset in [(0x100375420,16),(0x100375428,24),(0x100375430,32),(0x100375438,40)]:
   w=int.from_bytes(self.n['read'](a,4),'little');self.assertEqual((w>>5)&31,20);self.assertEqual(((w>>10)&0xfff)*8,offset)
  self.assertEqual(int.from_bytes(self.n['read'](0x1003753f0,4),'little'),0x52800620);self.assertEqual(int.from_bytes(self.n['read'](0x100375408,4),'little'),0x52800600)
  for a in [0x100372478,0x100371f60]:self.assertEqual(int.from_bytes(self.n['read'](a,4),'little'),0x52800022)
 def test_current_reader_owns_ids_and_coordinator_without_stored_materialized_object_or_context(self):
  for t in ['private let coordinator: NSPersistentStoreCoordinator','private let objectID: NSManagedObjectID','private let kind: OriginalPasteboardContentKind']:self.assertIn(t,self.reader)
  declarations=re.findall(r'^    private (?:let|var) (\w+): ([^\n]+)',self.reader,re.M);self.assertNotIn('NSManagedObjectContext',[v[1]for v in declarations]);self.assertNotIn('NSManagedObject',[v[1]for v in declarations]);self.assertNotIn('private var context',self.reader);self.assertNotIn('private let context',self.reader)
 def test_actual_record_producer_defers_both_capabilities_and_captures_only_reader(self):
  p=body(self.producer,'func searchIndexRecords(');self.assertIn('ClipboardSearchRecordReader(coordinator: coordinator, objectID: object.objectID, kind: kind)',p);self.assertIn('content: kind == .image ? nil : { reader.content() }',p);self.assertIn('imageData: kind == .image ? { reader.imageData() } : nil',p);self.assertNotIn('reader.content()',p[:p.index('content: kind == .image')]);self.assertNotIn('reader.imageData()',p[:p.index('imageData: kind == .image')])
 def test_current_context_remains_local_fresh_and_synchronously_delivers_raw_project_result(self):
  s=self.read;tokens=['let context = NSManagedObjectContext(concurrencyType: .privateQueueConcurrencyType)','context.persistentStoreCoordinator = coordinator','return try context.performAndWait','OriginalObjCExceptionBridge.withResult','context.existingObject(with: objectID)','ClipboardItemDataPersistence.readRepresentations','return try project(object, items)'];pos=0
  for t in tokens:pos=s.index(t,pos)+len(t)
  self.assertEqual(s.count('NSManagedObjectContext('),1)
  for t in ['Task {','DispatchQueue','self.context','context.save()','context.reset()','context.rollback()']:self.assertNotIn(t,s)
  self.assertIn('read(contentDiagnostics: contentDiagnostics)',body(self.s,'func content()'));self.assertIn('read(imageDiagnostics: contentDiagnostics)',body(self.s,'func imageData()'))
 def test_partial_boundaries_keep_unknowns_and_no_runtime_or_full_migration_claim(self):
  self.assertEqual(self.p['production_changes'],0);self.assertEqual(self.p['new_difference_records'],0);self.assertFalse(self.p['full_function_migration_verified']);self.assertFalse(self.p['runtime_executed']);self.assertIn('0f733c',self.p['boundaries'][2]);self.assertIn('04430c',self.p['boundaries'][2]);self.assertIn('nm',self.p['boundaries'][2]);self.assertIn('ARC',self.p['boundaries'][0])
if __name__=='__main__':unittest.main()
