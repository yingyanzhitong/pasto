"""Native query/record/OCR contracts and raw-type regression; Python/source only."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
D=ROOT/'.local/p0-p1-parent-review/2026-11-03-search-ocr'
SOURCE='replica/Sources/PastoCore/ClipboardSnapshotReader.swift'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

class SearchOCRBatch(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.p=json.loads((D/'contract.json').read_text());cls.base=json.loads((D/'baseline.json').read_text());cls.n={}
  exec((ROOT/cls.p['decoder']['path']).read_text().split('selectors=[]',1)[0],cls.n)
  cls.snapshot=(ROOT/SOURCE).read_text();cls.index=(ROOT/'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text()
  cls.record=(ROOT/'replica/Sources/PastoCore/ClipboardSearchRecord.swift').read_text()
  cls.engine=(ROOT/'replica/Sources/PastoCore/OCR.swift').read_text()
  cls.query=(ROOT/'replica/Sources/PastoCore/OriginalSearchQuery.swift').read_text()
  cls.suggestions=(ROOT/'replica/Sources/PastoCore/OriginalSearchSuggestions.swift').read_text()
 def order(self,s,tokens):
  positions=[s.index(x)for x in tokens];self.assertEqual(positions,sorted(positions))
 def test_original_fragments_and_current_source_inputs_fresh(self):
  cache={};self.assertEqual(len(self.p['original_fragments']),59)
  for r in self.p['original_fragments']:
   path=ROOT/r['path']
   if path not in cache:cache[path]=source_fragments(path)
   self.assertEqual(cache[path][r['function_id'].split(':')[1]]['sha256'],r['sha256'])
  for k in ['binary','decoder']:self.assertEqual(sha(ROOT/self.p[k]['path']),self.p[k]['sha256'])
  self.assertEqual(len(self.p['current_sources']),14)
  for p,h in self.p['current_sources'].items():self.assertEqual(sha(ROOT/p),h,p)
 def test_complete_native_ranges_and_direct_branches(self):
  self.assertEqual(len(self.p['machine_ranges']),59);self.assertEqual(len(self.p['branches']),2080)
  for r in self.p['machine_ranges']:
   data=self.n['read'](int(r['address'],16),int(r['end'],16)-int(r['address'],16))
   self.assertEqual(data.hex(),r['bytes']);self.assertEqual(hashlib.sha256(data).hexdigest(),r['sha256'])
  for r in self.p['branches']:
   pc=int(r['pc'],16);w=struct.unpack('<I',self.n['read'](pc,4))[0];self.assertEqual(hex(w),r['word'])
   v=w&0x3ffffff
   if v&(1<<25):v-=1<<26
   self.assertEqual(hex(pc+v*4),r['target'])
 def test_native_import_and_selector_fixups(self):
  self.assertEqual(len(self.p['selectors']),67);self.assertEqual(len(self.p['imports']),1215)
  raw=self.n['raw'];fixup=self.n['fixup'][0];h=struct.unpack_from('<7I',raw,fixup)
  for r in self.p['selectors']+self.p['imports']:
   value,chain=self.n['reachable_pointer'](int(r['pointer'],16));self.assertEqual(chain,r['chain'])
   if 'ordinal'in r:
    self.assertTrue(value>>63);self.assertEqual(value&0xffffff,r['ordinal'])
    e=struct.unpack_from('<I',raw,fixup+h[2]+4*r['ordinal'])[0];at=fixup+h[3]+(e>>9)
    self.assertEqual(raw[at:raw.index(b'\0',at)].decode(),r['name'])
   else:
    self.assertFalse(value>>63);at=self.n['base']+(value&((1<<36)-1))
    self.assertEqual(hex(at),r['target']);self.assertEqual(self.n['read'](at,len(r['name'])+1),r['name'].encode()+b'\0')
 def test_actual_constructor_calls_full_width_validator_immediately_after_raw_getter(self):
  r=self.p['raw_type_validation'];self.assertEqual(self.n['read'](int(r['address'],16),16).hex(),r['bytes'])
  self.assertEqual(struct.unpack('<4I',bytes.fromhex(r['bytes'])),(0x528000c8,0xf100181f,0x9a883000,0xd65f03c0))
  self.assertEqual(r['selector_call'],'0x100371cd8');self.assertEqual(r['caller'],'0x100371cdc')
  call=next(x for x in self.p['branches']if x['pc']==r['caller']);self.assertEqual(call['target'],'0x100323594')
  self.assertEqual(next(x['name']for x in self.p['selectors']if x['pc']==r['selector_call']),'rawType')
 def test_raw_type_no_longer_wraps_before_enum_validation(self):
  s=body(self.snapshot,'func searchIndexRecords(')
  self.assertIn('let rawType = (object.value(forKey: "rawType") as? NSNumber)?.int64Value ?? 0',s)
  self.assertIn('let kind = UInt8(exactly: rawType).flatMap { OriginalPasteboardContentKind(rawValue: $0) } ?? .unknown',s)
  self.assertNotIn('.uint8Value',s)
  before=(D/'before'/SOURCE).read_text();self.assertIn('?.uint8Value ?? 0',body(before,'func searchIndexRecords('))
  persistence=(ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text()
  self.assertIn('guard let value = UInt8(exactly: raw)',body(persistence,'func itemContentKind('))
 def test_only_two_lines_changed_and_all_other_production_and_old_tests_preserved(self):
  files=self.base['files'];prod={p:h for p,h in files.items()if p.startswith('replica/Sources/')}
  self.assertEqual(len(prod),248)
  self.assertEqual({p for p,h in prod.items()if sha(ROOT/p)!=h},{SOURCE})
  self.assertEqual(set(prod),{str(p.relative_to(ROOT))for p in(ROOT/'replica/Sources').rglob('*')if p.is_file()})
  for p,h in files.items():
   if p!=SOURCE:self.assertEqual(sha(ROOT/p),h,p)
  before=(D/'before'/SOURCE).read_text();expected=before.replace('let rawType = (object.value(forKey: "rawType") as? NSNumber)?.uint8Value ?? 0',
   'let rawType = (object.value(forKey: "rawType") as? NSNumber)?.int64Value ?? 0',1).replace('let kind = OriginalPasteboardContentKind(rawValue: rawType) ?? .unknown',
   'let kind = UInt8(exactly: rawType).flatMap { OriginalPasteboardContentKind(rawValue: $0) } ?? .unknown',1)
  self.assertEqual(self.snapshot,expected)
 def test_query_tag_grouping_escaping_and_OS_specific_content_field_preserved(self):
  s=body(self.query,'public static func f_1002f45b0(')
  self.assertIn('rawValue.trimmingCharacters(in: .whitespaces)',s)
  for x in ['var fields = ["title", "textContent"]','majorVersion: 26, minorVersion: 4','fields.append("contentDescription")',
   'groups[tag, default: []].append(predicate)','group.joined(separator: " || ")','predicates.joined(separator: " && ")']:self.assertIn(x,s)
  s=body(self.query,'public static func f_1002f3d94(')
  for x in ['value.trimmingCharacters(in: .whitespaces)','guard !value.isEmpty','case 0: field = "pasteApp"','case 1: field = "pasteType"',
   'case 2: field = "title"','case 4: field = "pasteDevice"','default: field = "pastePinboard"']:self.assertIn(x,s)
 def test_suggestion_sources_are_independent_and_filter_exclusion_precedes_limit(self):
  s=body(self.suggestions,'public static func f_1002df190(')
  self.order(s,['(0, provider.app)','(1, provider.type)','(4, provider.device)','(5, { try provider.pinboard'])
  self.assertIn('catch {\n                continue',s)
  self.order(s,['let candidates = try source(query)','.filter { !applied.contains($0) }','.prefix(30)'])
  s=body(self.index,'func suggestions(contextNode:')
  for group in ['app','type','device','pinboard']:self.assertIn('self.suggestionDataSource?.'+group+'($0)',s)
 def test_native_record_captures_kind_but_defers_content_and_image_reads(self):
  s=body(self.snapshot,'func searchIndexRecords(')
  for x in ['ClipboardSearchRecordReader(coordinator: coordinator, objectID: object.objectID, kind: kind)',
   'content: kind == .image ? nil : { reader.content() }','imageData: kind == .image ? { reader.imageData() } : nil']:self.assertIn(x,s)
  for x in ['ClipboardPersistence.decode(','rawPasteboardItems','f_10037d33c(','.prefix(5000)']:self.assertNotIn(x,s)
  s=body(self.record,'final class ClipboardSearchRecordReader')
  self.assertIn('private let coordinator: NSPersistentStoreCoordinator',s);self.assertIn('private let objectID: NSManagedObjectID',s)
  self.assertIn('private let kind: OriginalPasteboardContentKind',s)
 def test_each_content_read_uses_new_private_context_and_shared_raw_decoder(self):
  s=body(self.record,'private func read<T>(')
  self.order(s,['NSManagedObjectContext(concurrencyType: .privateQueueConcurrencyType)','context.persistentStoreCoordinator = coordinator',
   'try context.performAndWait','try OriginalObjCExceptionBridge.withResult','context.existingObject(with: objectID)',
   'object.entity.name == "Item"','!object.isDeleted','object.value(forKey: "data")','ClipboardItemDataPersistence.readRepresentations','return try project(object, items)'])
  for x in ['context.save()','context.reset()','rollback()','ClipboardPersistence.decode(']:self.assertNotIn(x,s)
 def test_typed_empty_fallback_and_raw_getter_error_do_not_restore_legacy_blob(self):
  s=body(self.record,'static func nativeText(')
  for x in ['legacyPreviewFallback: { "" }','guard kind != .unknown','guard metadata.length != 0',
   'fallback = items.first?.f_10037d33c()?.string','fallback = values.joined(separator: " ")','metadata.paths.joined(separator: " ")']:self.assertIn(x,s)
  self.assertNotIn('.plainText',s)
  s=body(self.record,'func content()');self.assertIn('if items.isEmpty { diagnoseEmptyRepresentations(for: object) }',s)
 def test_OCR_queue_uses_existing_set_before_union_and_pops_before_live_fetch(self):
  s=body(self.index,'private func enqueueOCR(')
  self.order(s,['entries.filter','$0.imageData != nil','!ocrQueuedIdentifiers.contains','ocrQueuedIdentifiers.formUnion(added)','ocrQueue.append(contentsOf: added)'])
  self.assertNotIn('readImage()',s)
  s=body(self.index,'private func drainOCRQueue()')
  self.order(s,['ocrQueue.removeFirst()','ocrQueuedIdentifiers.remove(identifier)','liveEntries(identifiers: [identifier]).first',
   'try Task.checkCancellation()','let data = readImage()','ImageTextRecognizer.recognizeWords(imageData: data, maximumDimension: 1024)',
   'words.map(\.text).joined(separator: " ")','entry.record.appendingRecognizedText(text)','writeSearchableItems([item]','ContinuousClock().sleep(for: .seconds(2))'])
 def test_stop_cancels_and_awaits_OCR_without_clearing_pending_queue(self):
  s=body(self.index,'private func stopIndexing()')
  self.order(s,['isRunning = false','historyTask?.cancel()','ocrTask.cancel()','await ocrTask.value','ocrTask = nil'])
  self.assertNotIn('ocrQueue.removeAll',s);self.assertNotIn('ocrQueuedIdentifiers.removeAll',s)
  s=body(self.index,'private func startOCRWorker()')
  self.assertIn('ocrTask == nil || ocrTask?.isCancelled == true',s);self.assertIn('Task(priority: .low)',s)
 def test_word_only_engine_has_single_candidate_string_read_and_forward_cursor(self):
  s=body(self.engine,'public static func recognizeWords(')
  self.assertIn('includeFullText: false',s)
  s=body(self.engine,'public static func f_1002d576c(')
  self.assertEqual(s.count('observation.topCandidates(1)'),1);self.assertEqual(s.count('candidate.string'),1)
  self.order(s,['guard let candidate','let text = candidate.string','recognizedText?(text)','var cursor = text.startIndex',
   'text.range(of: word, options: [], range: cursor..<text.endIndex','try? candidate.boundingBox(for: range)','words.append','cursor = range.upperBound'])
 def test_OCR_request_flags_pool_and_image_threshold_are_preserved(self):
  s=body(self.engine,'public static func f_1002d4738(')
  self.order(s,['guard !imageData.isEmpty','try autoreleasepool','try f_1002d4830'])
  s=body(self.engine,'public static func f_1002d4ba0(')
  self.assertIn('width > 10, height > 10',s);self.assertIn('if max(width, height) <= maximumDimension { return imageData }',s)
  s=body(self.engine,'public static func f_1002d4830(')
  for x in ['request.automaticallyDetectsLanguage = true','request.usesLanguageCorrection = true',
   'request.preferBackgroundProcessing = true','try handler.perform([request])']:self.assertIn(x,s)
 def test_ocr_update_keeps_record_metadata_drops_image_and_sdk_caps_after_callback(self):
  s=body(self.record,'public func appendingRecognizedText(')
  for x in ['let existing = content?() ?? ""','existing + "\\n" + text','content: { combined }, imageData: nil','modified: modified','pinboard: pinboard']:self.assertIn(x,s)
  s=body(self.index,'private func searchableItem(')
  self.order(s,['let content = entry.content?()','String($0.prefix(5000))','attributes.textContent = text','item.isUpdate = isUpdate'])
  s=body(self.index,'private static func writeSearchableItems(')
  self.order(s,['guard let index else { return nil }','withCheckedThrowingContinuation','index.indexSearchableItems'])
 def test_same_existing_repair_record_no_scope_or_repaired_function_inflation(self):
  scope=json.loads((ROOT/'reports/replica/p0-p1-review-scope-v6.json').read_text());self.assertEqual(scope['denominator'],959)
  allowed={r['function_id']for r in scope['functions']};ids={r['function_id']for r in self.p['machine_ranges']}
  self.assertEqual(set(self.p['reviewed_in_scope_function_ids']),allowed&ids);self.assertEqual(len(allowed&ids),36)
  self.assertEqual(len(self.p['support_not_added_to_denominator']),23)
  self.assertEqual(self.p['repaired_existing_function_ids'],['Paste:0x100371998']);self.assertEqual(self.p['new_repaired_function_count'],0)
  previous=json.loads((ROOT/'reports/replica/p0-p1-repair-round188.json').read_text())
  self.assertIn('Paste:0x100371998',previous['cumulative_repaired_function_ids'])
  self.assertFalse(self.p['full_function_migration_verified']);self.assertFalse(self.p['compiled']);self.assertFalse(self.p['framework_executed'])

class RawTypeAndQueueTraceModels(unittest.TestCase):
 """Finite integer/queue witnesses describe Swift source semantics, not CoreData execution."""
 def test_all_signed_16bit_values_match_native_full_width_unsigned_guard(self):
  native=lambda raw:raw if (raw&((1<<64)-1))<6 else 0
  current=lambda raw:raw if 0<=raw<=255 and raw<6 else 0
  for raw in range(-32768,32768):self.assertEqual(current(raw),native(raw),raw)
 def test_old_byte_wrap_reproduces_1275_wrong_nonunknown_aliases(self):
  def old(raw):
   value=raw&255;return value if value<6 else 0
  mismatches=[raw for raw in range(-32768,32768)if old(raw)!=(raw if 0<=raw<6 else 0)]
  self.assertEqual(len(mismatches),1275)
  for raw,wrong in [(257,1),(-255,1),(260,4),(-251,5)]:self.assertEqual(old(raw),wrong);self.assertIn(raw,mismatches)
 def test_extreme_64bit_and_valid_values_do_not_wrap_into_known_types(self):
  for raw in [-(1<<63),-(1<<63)+1,-257,-256,-255,-1,0,1,2,3,4,5,6,255,256,257,261,(1<<63)-1]:
   result=raw if 0<=raw<=255 and raw<6 else 0
   self.assertEqual(result,raw if 0<=raw<6 else 0)
 def test_same_batch_duplicates_and_inflight_reenqueue_are_preserved(self):
  pending={'old'};queue=['old'];incoming=['old','new','new','other']
  added=[x for x in incoming if x not in pending];pending.update(added);queue.extend(added)
  self.assertEqual(queue,['old','new','new','other']);self.assertEqual(pending,{'old','new','other'})
  first=queue.pop(0);pending.remove(first);self.assertNotIn('old',pending)
 def test_OCR_nil_or_missing_input_skips_and_nonempty_text_is_word_joined(self):
  events=[]
  for exists,image,words in [(False,None,[]),(True,None,[]),(True,b'bytes',['one','two'])]:
   if not exists or image is None:continue
   text=' '.join(words)
   if text:events.append(('write',text))
   events.append('cooldown')
  self.assertEqual(events,[('write','one two'),'cooldown'])

if __name__=='__main__':unittest.main()
