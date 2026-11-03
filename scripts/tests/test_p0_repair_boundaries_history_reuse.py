from native_restore_writer_scope_contract import pre_native_restore_writer
# coding: utf-8
"""C/Swift/static binary contracts only; does not invoke Carbon or Core Data."""
import hashlib,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment

class BoundariesHistoryReuseContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-36'
        cls.proof=json.loads((cls.phase/'p0-boundaries-and-history-reuse-contract.json').read_text())
        cls.key=(ROOT/'replica/Sources/PastoCore/OriginalPasteKeyTranslation.swift').read_text()
        cls.bridge=(ROOT/'replica/Sources/PastoObjC/PastoKeyTranslation.m').read_text()
        cls.restore=pre_native_restore_writer((ROOT/'replica/Sources/PastoCore/OriginalPasteboardImageRestore.swift').read_text())
        cls.pasteboard=(ROOT/'replica/Sources/PastoCore/Pasteboard.swift').read_text()
        cls.store=(ROOT/'replica/Sources/PastoCore/ClipboardStore.swift').read_text()
        cls.persistence=(ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text()
        cls.lists=(ROOT/'replica/Sources/PastoCore/ClipboardListPersistence.swift').read_text()

    def test_original_fragments_prior_proofs_and_sdk_headers_are_bound(self):
        for r in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for p,h in {**self.proof['prior_proofs'],**self.proof['sdk_headers']}.items():
            path=Path(p)if Path(p).is_absolute()else ROOT/p
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),h)
        b=self.proof['original_binary'];self.assertEqual(hashlib.sha256((ROOT/b['path']).read_bytes()).hexdigest(),b['sha256'])
        self.assertEqual({r['symbol']for r in self.proof['native_imports']},
                         {'_TISGetInputSourceProperty','_CFDataGetBytePtr','_UCKeyTranslate','_LMGetKbdType'})

    def test_key_translation_retains_explicit_missing_source_failure(self):
        original=original_fragment((ROOT/'decompiled/Paste/part-1008.c').read_text(),'100ae6678')
        order=['_TISCopyCurrentASCIICapableKeyboardLayoutInputSource()','if (lVar5 == 0)',
               '_TISGetInputSourceProperty()','_CFDataGetBytePtr()','_LMGetKbdType()','_UCKeyTranslate(']
        positions=[original.index(t)for t in order];self.assertEqual(positions,sorted(positions))
        key=body(self.key,'public static func f_100ae6678(')
        self.assertIn('guard let source = TISCopyCurrentASCIICapableKeyboardLayoutInputSource()?.takeRetainedValue()',key)
        self.assertIn('preconditionFailure("ASCII-capable keyboard layout input source is missing")',key)
        self.assertIn('let property = TISGetInputSourceProperty(source, kTISPropertyUnicodeKeyLayoutData)',key)

    def test_property_and_byte_pointer_have_no_invented_nil_result_branch(self):
        key=body(self.key,'public static func f_100ae6678(')
        for token in ['guard let property','guard let bytes','property!','Unmanaged<CFData>','CFDataGetBytePtr(']:
            self.assertNotIn(token,key)
        self.assertIn('PastoTranslateASCIIKeyLayoutData(property, keyCode, buffer.baseAddress!, UInt64(buffer.count), &length)',key)
        bridge=body(self.bridge,'int32_t PastoTranslateASCIIKeyLayoutData(')
        self.assertIn('CFDataGetBytePtr((CFDataRef)layoutData)',bridge)
        self.assertLess(bridge.index('CFDataGetBytePtr('),bridge.index('UCKeyTranslate('))
        self.assertNotRegex(bridge,r'\bif\s*\(')
        for token in ['return nil','return NULL','return paramErr','__builtin_trap']:
            self.assertNotIn(token,bridge)

    def test_bridge_preserves_native_translate_arguments_buffer_and_result_filter(self):
        bridge=body(self.bridge,'int32_t PastoTranslateASCIIKeyLayoutData(')
        for token in ['UInt32 deadKeyState = 0','UniCharCount actualLength = 0',
                      'UCKeyTranslate(layout, keyCode, kUCKeyActionDisplay, 0, LMGetKbdType(), 0,',
                      '&deadKeyState, (UniCharCount)capacity, &actualLength, characters)',
                      '*length = (uint64_t)actualLength','return status']:
            self.assertIn(token,bridge)
        key=body(self.key,'public static func f_100ae6678(')
        self.assertIn('var length: UInt64 = 0',key)
        self.assertIn('[UniChar](repeating: 0, count: 4)',key)
        self.assertIn('withExtendedLifetime(source)',key)
        self.assertIn('guard status == noErr, length > 0,',key)
        self.assertIn('UnicodeScalar(UInt32(characters[0]))',key)
        self.assertIn('return String(scalar)',key)
        sdk=next(p for p in self.proof['sdk_headers']if p.endswith('UnicodeUtilities.h'))
        self.assertRegex(Path(sdk).read_bytes(),rb'kUCKeyActionDisplay\s*=\s*3')

    def test_bridge_is_exported_to_actual_swift_leaf_without_changing_event_sender(self):
        header=(ROOT/'replica/Sources/PastoObjC/include/PastoKeyTranslation.h').read_text()
        module=(ROOT/'replica/Sources/PastoObjC/include/module.modulemap').read_text()
        self.assertIn('void * _Nullable layoutData',header)
        self.assertIn('uint16_t *characters, uint64_t capacity, uint64_t *length',header)
        self.assertIn('header "PastoKeyTranslation.h"',module)
        self.assertIn('import PastoObjC',self.key)
        before=(self.phase/'before/replica/Sources/PastoCore/OriginalPasteKeyTranslation.swift').read_text()
        leaf=body(self.key,'public static func f_100ae6678(')
        reconstructed=self.key.replace(leaf,body(before,'public static func f_100ae6678('),1).replace('import PastoObjC\n','',1)
        self.assertEqual(reconstructed,before)

    def test_production_image_directory_uses_default_root_without_namespace(self):
        self.assertIn('public init(temporaryRoot: URL? = nil)',self.restore)
        self.assertIn('private let temporaryRoot: URL?',self.restore)
        directory=body(self.restore,'public func f_100384824()')
        self.assertIn('(temporaryRoot ?? FileManager.default.temporaryDirectory).appendingPathComponent("images")',directory)
        self.assertIn('if !directory.hasDirectoryPath',directory)
        self.assertIn('createDirectory(at: directory, withIntermediateDirectories: false)',directory)
        self.assertIn('return directory',directory)
        self.assertNotIn('fileExists(at:',directory)
        self.assertNotRegex(directory,r'appendingPathComponent\([^)]*isDirectory:')
        self.assertIn('private static let imageRestore = OriginalPasteboardImageRestore()',self.pasteboard)
        self.assertNotIn('appendingPathComponent("PasteReplica", isDirectory: true)',self.pasteboard)

    def test_default_root_is_not_precreated_and_explicit_test_root_still_works(self):
        prepare=body(self.restore,'public func prepare(sourceName: String?, timestamp: Date?,')
        custom=body(prepare,'if let temporaryRoot')
        self.assertIn('createDirectory(at: temporaryRoot, withIntermediateDirectories: true)',custom)
        outer=prepare.replace('if let temporaryRoot '+custom,'',1)
        self.assertNotIn('createDirectory',outer)
        self.assertIn('return try f_100383df4(sourceName:',outer)
        before=(self.phase/'before/replica/Sources/PastoCore/OriginalPasteboardImageRestore.swift').read_text()
        for sig in ['private func f_100383df4(', 'public func f_100384aac()', 'public static func f_100384e6c(']:
            self.assertEqual(body(self.restore,sig),body(before,sig))

    def test_actual_pasteboard_caller_only_changes_root_constructor(self):
        before=(self.phase/'before/replica/Sources/PastoCore/Pasteboard.swift').read_text()
        old='    private static let imageRestore = OriginalPasteboardImageRestore(\n'
        old+='        temporaryRoot: FileManager.default.temporaryDirectory.appendingPathComponent("PasteReplica", isDirectory: true))'
        new='    private static let imageRestore = OriginalPasteboardImageRestore()'
        self.assertEqual(self.pasteboard.count(new),1)
        checkpoint=(ROOT/'.local/p0-repair/phase-37/before/replica/Sources/PastoCore/Pasteboard.swift').read_text()
        self.assertEqual(checkpoint.replace(new,old,1),before)
        init_calls=[]
        for p in (ROOT/'replica/Sources').rglob('*.swift'):
            if 'OriginalPasteboardImageRestore('in p.read_text():init_calls.append(str(p.relative_to(ROOT)))
        self.assertEqual(init_calls,['replica/Sources/PastoCore/Pasteboard.swift'])

    def test_no_share_restore_gate_reuses_bound_native_pass_through_not_guess_clone(self):
        p=ROOT/'.local/p0-repair/phase-14/restore-local-gate-root.json';gate=json.loads(p.read_text())
        raw=(ROOT/self.proof['original_binary']['path']).read_bytes()
        for r in gate['machine_ranges']:
            # The selected ranges are in the original __TEXT segment, whose
            # file offset is vmaddr - preferred text base on this bound image.
            a=int(r['start'],16)-0x100000000;b=int(r['end'],16)-0x100000000
            self.assertEqual(hashlib.sha256(raw[a:b]).hexdigest(),r['sha256'])
        for r in gate['original_fragments']:
            self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        self.assertIn('目标和全部来源均无share',gate['conclusions'][3])
        prepare=body(self.persistence,'func prepareHistoryItems(')
        self.assertIn('return try ids.map { id in',prepare)
        self.assertIn('if let object = objects[id.uuidString] { return (id: id, object: object) }',prepare)
        self.assertNotIn('Set(',prepare)

    def test_actual_restore_entry_reaches_native_timestamp_then_capacity_then_refresh(self):
        entry=body(self.store,'func recordRestoredItems(')
        self.assertLess(entry.index('guard !ids.isEmpty else { return }'),entry.index('mutate(historyAction: true, restoringItemIDs: ids)'))
        worker=body(self.store,'private func mutateInTransaction<T>(')
        order=['let result = try change(&state, transaction)','let history = try lists.synchronize(',
               'prepareHistoryItems(restoringItemIDs)','restoreHistoryItems(targets)',
               'lists.historyCapacity(of: history)','expireHistory(&state, capacity: capacity)',
               'lists.refreshHistoryAfterOperation =']
        positions=[worker.index(t)for t in order];self.assertEqual(positions,sorted(positions))
        restore=body(self.persistence,'func restoreHistoryItems(')
        self.assertLess(restore.index('targets.reversed()'),restore.index('let timestamp = Date()'))
        self.assertLess(restore.index('let timestamp = Date()'),restore.index('object.setValue(timestamp, forKey: "timestamp")'))

    def test_capacity_and_first_history_refresh_are_real_managed_consumers(self):
        capacity=body(self.lists,'func historyCapacity(of history: NSManagedObject)')
        self.assertIn('history.value(forKey: "rawAttributes") as? Data',capacity)
        refresh=body(self.lists,'func refreshHistoryIfNeeded()')
        self.assertIn('guard let history = try historyList() else { return }',refresh)
        self.assertIn('context.refresh(history, mergeChanges: true)',refresh)
        fetch=body(self.lists,'func firstList(')
        for token in ['entityName: "ListEntity"','request.fetchLimit = 1','request.fetchOffset = 0',
                      'request.fetchBatchSize = 20','NSSortDescriptor(key: "metadata.index", ascending: true)']:
            self.assertIn(token,fetch)
        commit=body(self.persistence,'func commit<T>(previous: StoreState?, deletingItemIDs: [UUID] = [],')
        self.assertLess(commit.index('try transaction.repository.lists.refreshHistoryIfNeeded()'),commit.index('if context.hasChanges'))

    def test_delete_reads_live_context_once_and_distinguishes_history_group_refresh(self):
        delete=body(self.store,'public func delete(orderedIDs: [UUID], currentPinboardID: () -> UUID?)')
        self.assertEqual(delete.count('currentPinboardID()'),1)
        self.assertIn('refreshHistoryAfterChange:',delete)
        self.assertIn('state.items[i].isInHistory = false',delete)
        worker=body(self.store,'private func mutateInTransaction<T>(')
        self.assertIn('historyAction || (refreshHistoryAfterChange?() ?? false)',worker)
        self.assertLess(delete.index('currentPinboardID()'),delete.index('for i in state.items.indices'))
        self.assertIn('contextPinboardID == nil',delete)
        original=original_fragment((ROOT/'decompiled/Paste/part-0275.c').read_text(),'1003636b4')
        self.assertIn('FUN_100328bb4(',original)
        self.assertIn('objc_stub::FUN_100c08be0',original)

    def test_forwarder_records_bind_repaired_real_consumers_not_new_stub_functions(self):
        s=(ROOT/'decompiled/Paste/part-0275.c').read_text()
        self.assertIn('FUN_1003614c0()',original_fragment(s,'100364014'))
        self.assertIn('FUN_1003636b4()',original_fragment(s,'100364074'))
        contracts=self.proof['contracts']
        self.assertEqual(sum(r['kind']=='source_repair'for r in contracts),2)
        self.assertEqual(sum(r['kind']=='revalidated_existing_repair'for r in contracts),3)
        self.assertEqual(self.proof['new_difference_records'],0)
        self.assertEqual(self.proof['new_function_map_markers'],0)
        self.assertFalse(self.proof['full_function_migration_verified'])
        for r in contracts:self.assertFalse(r['full_function_migration_verified'])

    def test_reused_history_production_files_are_unchanged_from_current_baseline(self):
        for name in ['ClipboardStore.swift','ClipboardPersistence.swift','ClipboardListPersistence.swift']:
            p='replica/Sources/PastoCore/'+name
            self.assertEqual((ROOT/'.local/p0-repair/phase-38/before'/p).read_bytes(),(self.phase/'before'/p).read_bytes())
        self.assertEqual(self.proof['reused_existing_records'],3)
        self.assertEqual(len(self.proof['source_cases']),3)

if __name__=='__main__':unittest.main()
