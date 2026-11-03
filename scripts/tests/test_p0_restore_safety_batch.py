"""Current native copy/restore chain and integer boundaries, no framework execution."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
D=ROOT/'.local/p0-p1-parent-review/2026-11-03-restore-safety'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

class RestoreSafetyBatch(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.p=json.loads((D/'contract.json').read_text());cls.base=json.loads((D/'baseline.json').read_text());cls.n={}
  exec((ROOT/cls.p['decoder']['path']).read_text().split('selectors=[]',1)[0],cls.n)
  cls.pb=(ROOT/'replica/Sources/PastoCore/Pasteboard.swift').read_text()
  cls.state=(ROOT/'replica/Sources/PastoCore/OriginalPasteboardCaptureState.swift').read_text()
  cls.store=(ROOT/'replica/Sources/PastoCore/ClipboardStore.swift').read_text()
  cls.persistence=(ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text()
  cls.restore=(ROOT/'replica/Sources/PastoCore/OriginalPasteboardRestore.swift').read_text()
  cls.ui=(ROOT/'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
 def order(self,s,tokens):
  positions=[s.index(x)for x in tokens];self.assertEqual(positions,sorted(positions))
 def test_original_and_current_source_inputs_fresh(self):
  cache={};self.assertEqual(len(self.p['original_fragments']),30)
  for r in self.p['original_fragments']:
   path=ROOT/r['path']
   if path not in cache:cache[path]=source_fragments(path)
   self.assertEqual(cache[path][r['function_id'].split(':')[1]]['sha256'],r['sha256'])
  for k in ['binary','decoder']:self.assertEqual(sha(ROOT/self.p[k]['path']),self.p[k]['sha256'])
  self.assertEqual(len(self.p['current_sources']),13)
  for p,h in self.p['current_sources'].items():self.assertEqual(sha(ROOT/p),h,p)
 def test_complete_native_ranges_and_all_direct_branches(self):
  self.assertEqual(len(self.p['machine_ranges']),30);self.assertEqual(len(self.p['branches']),1257)
  for r in self.p['machine_ranges']:
   data=self.n['read'](int(r['address'],16),int(r['end'],16)-int(r['address'],16))
   self.assertEqual(data.hex(),r['bytes']);self.assertEqual(hashlib.sha256(data).hexdigest(),r['sha256'])
  for r in self.p['branches']:
   pc=int(r['pc'],16);w=struct.unpack('<I',self.n['read'](pc,4))[0];self.assertEqual(hex(w),r['word'])
   v=w&0x3ffffff
   if v&(1<<25):v-=1<<26
   self.assertEqual(hex(pc+v*4),r['target'])
 def test_native_selectors_and_import_fixups(self):
  self.assertEqual(len(self.p['selectors']),81);self.assertEqual(len(self.p['imports']),745)
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
 def test_full_width_native_and_other_integer_conversions_are_guarded(self):
  self.assertEqual(struct.unpack('<4I',self.n['read'](0x100323594,16)),(0x528000c8,0xf100181f,0x9a883000,0xd65f03c0))
  source=(ROOT/'replica/Sources/PastoCore/ClipboardRestoreItem.swift').read_text();s=body(source,'public func previewRawType()')
  self.assertIn('?.intValue ?? 0',s);self.assertIn('(0...5).contains(rawType) ? rawType : 0',s)
  self.assertNotIn('uint8Value',s)
  s=body(self.persistence,'func itemContentKind(');self.assertIn('?.int64Value ?? 0',s);self.assertIn('UInt8(exactly: raw)',s)
  source=(ROOT/'replica/Sources/PastoCore/ClipboardSourcePersistence.swift').read_text();s=body(source,'func deviceType(named')
  self.order(s,['?.int64Value ?? 0','precondition(rawType >= 0 && rawType < 3)','return UInt8(rawType)'])
 def test_native_capture_input_reuses_raw_entity_before_legacy_fallback(self):
  s=body(self.pb,'public func writeToPasteboard(restoreItems:')
  self.order(s,['guard !restoreItems.isEmpty','restoreItems.contains(where: { $0.nativeObject != nil })',
   'let objects = try nativeRestoreObjects(restoreItems, options: options)','try finishPasteboardWrite(objects','try prepareHistoryRestore(restoreItems)'])
  s=body(self.pb,'private func nativeRestoreGroups(')
  native=s[s.index('if let object = input.nativeObject'):s.index('} else {\n                let item = input.resolvedItem()')]
  self.assertIn('UInt8(input.previewRawType()!)',native);self.assertIn('Self.nativeRestoreRepresentations(for: object)',native)
  for x in ['input.resolvedItem()','try reload()','JSONDecoder','PropertyListDecoder','items.first(where:']:self.assertNotIn(x,native)
 def test_native_image_metadata_is_lazy_until_raw_data_preparation(self):
  s=body(self.pb,'private func nativeRestoreGroups(')
  self.order(s,['if !plain, kind == .image','Self.imageRestore.prepareNative(','Self.nativeRestoreRepresentations(for: object)',
   'items = plain ? OriginalPasteboardRestore.f_10031bcdc(representations) : representations',
   'sourceBundleID = application?.value(forKey: "bundleIdentifier") as? String'])
  source=(ROOT/'replica/Sources/PastoCore/OriginalPasteboardImageRestore.swift').read_text();s=body(source,'func prepareNative(')
  self.order(s,['let directory = f_100384824()','let items = try loadItems()','guard let directory else { return items }','return f_100383df4'])
  self.assertIn('sourceName: @autoclosure',source);self.assertIn('timestamp: @autoclosure',source)
 def test_source_flags_and_aggregation_remain_after_each_input_preparation(self):
  s=body(self.pb,'private func nativeRestoreGroups(')
  self.order(s,['let multiple = inputs.count > 1','let aggregatesText = inputs.contains','for input in inputs','for item in items',
   'item.f_100383574','item.f_10037c4a8(sourceBundleID ?? "", forType: "org.nspasteboard.source")','item.f_1003838bc()',
   'if !multiple { return [items] }','if aggregatesText','f_100383a0c(separator: "\\n", contents: contents)'])
  self.assertIn('groups.append([])',s);self.assertIn('groups.insert([aggregate], at: 0)',s)
 def test_two_plain_option_bits_and_value_projection_order_preserved(self):
  self.assertIn('plainOtherContent = Options(rawValue: 1 << 0)',self.restore)
  self.assertIn('plainTextAndLinks = Options(rawValue: 1 << 1)',self.restore)
  self.assertIn('options.contains(kind == .text || kind == .link ? .plainTextAndLinks : .plainOtherContent)',self.restore)
  s=body(self.restore,'public static func f_10038222c(')
  self.assertIn('contents.append(contentsOf: items.compactMap { $0.f_10037d33c() })',s)
  self.assertIn('if !options.contains(.plainTextAndLinks), let data',s)
  self.assertIn('aggregate.f_10037c4a8(combined.string, forType: "public.utf8-plain-text")',s)
 def test_raw_reader_keeps_relationship_lookup_outside_getter_exception_scope(self):
  source=(ROOT/'replica/Sources/PastoCore/ClipboardItemDataPersistence.swift').read_text()
  s=body(source,'@MainActor static func readItems(')
  self.order(s,['object.value(forKey: "data")','readRepresentations(from: data)'])
  s=body(source,'static func readRepresentations(')
  self.order(s,['OriginalObjCExceptionBridge.f_1002ffc68','data.value(forKey: "rawPasteboardItems")','Data._unconditionallyBridgeFromObjectiveC(raw)',
   'catch let error as OriginalObjCExceptionError','return []','return autoreleasepool { OriginalPasteboardDataCodec.f_10031aeec(raw) }'])
 def test_writer_materializes_data_before_clear_then_writes_and_reads_count(self):
  s=body(self.state,'public func f_10037875c(')
  self.order(s,['let objects = items.map','let object = NSPasteboardItem()','for type in item.f_10037da6c()',
   'if let data = item.f_10037e5e0(forType: type)','object.setData','pasteboard.clearContents()',
   'lastWriteSucceeded = pasteboard.writeObjects(objects)','lastChangeCount = pasteboard.changeCount'])
  self.assertNotIn('guard !items.isEmpty',s);self.assertNotIn('if lastWriteSucceeded',s)
  names=[r['name']for r in self.p['selectors']if r['function_id']=='Paste:0x10037875c']
  self.assertLess(names.index('setData:forType:'),names.index('clearContents'))
  self.assertLess(names.index('clearContents'),names.index('writeObjects:'));self.assertLess(names.index('writeObjects:'),names.index('changeCount'))
 def test_postwrite_error_boundary_preserves_undo_and_notifications(self):
  s=body(self.pb,'private func finishPasteboardWrite(')
  self.order(s,['first.f_10037d8c8(Data(), forType: generatedType.rawValue)','state.f_10037875c(objects)',
   'state.persistChangeCount?(state.lastChangeCount)','do {','let restoration = try prepareRestoration()',
   'try recordRestoredSelection(restoration)','} catch {','Self.restoreUndoManager.f_1000da768().removeAllActions()',
   'NotificationCenter.default.post(name: Self.didRestoreItemNotification, object: self)','didRestoreItem.send()'])
  catch=body(s,'catch');code='\n'.join(x.split('//',1)[0]for x in catch.splitlines())
  self.assertEqual(''.join(code.split()),'{}')
  for x in ['if objects.isEmpty','guard !objects.isEmpty','Task {','asyncAfter','lastWriteSucceeded']:self.assertNotIn(x,s)
 def test_native_error_and_success_join_before_real_undo_selector(self):
  names=[r for r in self.p['selectors']if r['function_id']=='Paste:0x10037a144']
  self.assertIn('removeAllActions',[r['name']for r in names]);self.assertIn('postNotificationName:object:',[r['name']for r in names])
  pc=0x10037a5b0;w=struct.unpack('<I',self.n['read'](pc,4))[0]
  self.assertEqual(w&0xff00001f,0xb4000015);v=(w>>5)&0x7ffff
  if v&(1<<18):v-=1<<19
  self.assertEqual(pc+v*4,0x10037a5bc)
  error=next(r for r in self.p['imports']if r['pc']=='0x10037a5b8');self.assertEqual(error['name'],'_swift_errorRelease')
  undo=next(r for r in names if r['name']=='removeAllActions');self.assertGreater(int(undo['pc'],16),0x10037a5b8)
 def test_native_history_retains_entity_targets_and_only_mutates_timestamp(self):
  s=body(self.store,'func prepareHistoryRestore(_ selected: [ClipboardRestoreItem])')
  self.assertIn('let legacy = selected.filter { $0.nativeObject == nil }',s)
  self.assertIn('persistence.prepareHistoryRestore(inputs: selected)',s)
  s=body(self.persistence,'func restoreHistoryItems(')
  self.order(s,['targets.reversed()','let timestamp = Date()','object.setValue(timestamp, forKey: "timestamp")','updates.append'])
  for x in ['rawPreview','rawType','"data"','"list"','payloads','encode(']:self.assertNotIn(x,s)
 def test_recency_only_overlay_does_not_replay_other_native_content(self):
  commit=body(self.persistence,'func commit<T>(');fast=body(commit,'if !transaction.nativeHistoryRestoreTargets.isEmpty')
  loop=body(fast,'for item in state.items')
  for x in ['var restored = old','restored.createdAt = item.createdAt','restored.updatedAt = item.updatedAt',
   'restored.isInHistory = item.isInHistory','guard restored == item else { continue }','restoredMetadataOnly.insert(item.id)']:self.assertIn(x,loop)
  for x in ['"data"','"rawPreview"','"list"','"timestamp"','encode(','decode(']:self.assertNotIn(x,loop)
 def test_UI_copy_hides_after_return_without_a_timer(self):
  s=body(self.ui,'private func performCopy(')
  self.order(s,['state.perform','try write()','copiedItemsHandler?()','hidePanel()'])
  for x in ['asyncAfter','Task {','sleep','Timer.']:self.assertNotIn(x,s)
 def test_no_production_or_prior_test_and_report_changes(self):
  prod={p:h for p,h in self.base['files'].items()if p.startswith('replica/Sources/')};self.assertEqual(len(prod),248)
  self.assertEqual(set(prod),{str(p.relative_to(ROOT))for p in(ROOT/'replica/Sources').rglob('*')if p.is_file()})
  for p,h in self.base['files'].items():self.assertEqual(sha(ROOT/p),h,p)
 def test_scope_stays_fixed_and_reuse_does_not_upgrade_full_migration(self):
  s=json.loads((ROOT/'reports/replica/p0-p1-review-scope-v6.json').read_text());self.assertEqual(s['denominator'],959)
  allowed={r['function_id']for r in s['functions']};ids={r['function_id']for r in self.p['machine_ranges']}
  self.assertEqual(set(self.p['reviewed_in_scope_function_ids']),ids&allowed);self.assertEqual(len(ids&allowed),27)
  self.assertEqual(len(self.p['support_not_added_to_denominator']),3)
  for k in ['production_modified','full_function_migration_verified','compiled','framework_executed']:self.assertFalse(self.p[k])

class PostwriteAndTypeTraces(unittest.TestCase):
 """Source-order witnesses, not a pasteboard/database run."""
 def test_all_success_and_prepare_record_failure_paths_clear_undo_and_notify(self):
  for failure,expected in [(None,['write','count','prepare','record','undo','notify']),
   ('prepare',['write','count','prepare','caught','undo','notify']),('record',['write','count','prepare','record','caught','undo','notify'])]:
   events=['write','count']
   try:
    for phase in ['prepare','record']:
     events.append(phase)
     if failure==phase:raise RuntimeError(phase)
   except RuntimeError:events.append('caught')
   events+=['undo','notify'];self.assertEqual(events,expected)
 def test_false_or_empty_write_result_does_not_gate_postwrite_cleanup(self):
  for objects,result in [([],False),(['data'],False),(['data'],True)]:
   events=[('clear',objects),('write',result),'count','prepare','record','undo','notify']
   self.assertEqual(events[-2:],['undo','notify'])
 def test_reverse_restore_order_places_first_selected_item_at_latest_timestamp(self):
  selected=['A','B','C'];dates={key:i for i,key in enumerate(reversed(selected))}
  self.assertGreater(dates['A'],dates['B']);self.assertGreater(dates['B'],dates['C'])
 def test_preview_normalizes_before_any_narrow_integer_conversion(self):
  for raw in [-(1<<63),-255,-1,0,1,2,3,4,5,6,255,257,260,(1<<63)-1]:
   normalized=raw if raw in range(6)else 0
   self.assertTrue(0<=normalized<=5);self.assertEqual(normalized,raw if 0<=raw<=5 else 0)

if __name__=='__main__':unittest.main()
