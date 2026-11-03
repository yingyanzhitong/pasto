from native_title_scope_contract import pre_native_title
# coding: utf-8
"""Capture C/native source ordering. No Swift, Core Data or application execution."""
import hashlib,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment

class CaptureNativeFlowContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-35'
        cls.proof=json.loads((cls.phase/'capture-native-flow-contract.json').read_text())
        cls.store=pre_native_title((ROOT/'replica/Sources/PastoCore/ClipboardStore.swift').read_text())
        cls.persistence=(ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text()
        cls.graph=(ROOT/'replica/Sources/PastoCore/ClipboardItemDataPersistence.swift').read_text()
        cls.add=body(cls.store,'func addWithInsertionResult(')
        cls.worker=body(cls.store,'private func mutateInTransaction<T>(')
        cls.commit=body(cls.persistence,'func commit<T>(previous: StoreState?, deletingItemIDs: [UUID] = [],')

    def test_original_fragments_and_preview_type_metadata_are_bound(self):
        for r in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        b=self.proof['original_binary'];raw=(ROOT/b['path']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),b['sha256'])
        for r in self.proof['original_metadata_blocks']:
            v=raw[r['file_offset']:r['file_offset']+r['length']]
            self.assertEqual(v.hex(),r['bytes']);self.assertEqual(hashlib.sha256(v).hexdigest(),r['sha256'])
        self.assertEqual([t['name']for t in self.proof['preview_types']],['LinkPreview','TextPreview','ItemPreview'])

    def test_real_value_entry_forwards_all_policies_to_single_context_worker(self):
        forward=body(self.store,'private func mutate<T>(')
        for token in ['mutateInTransaction(historyAction: historyAction, deletingItemIDs: deletingItemIDs,',
                      'restoringItemIDs: restoringItemIDs, refreshHistoryAfterChange: refreshHistoryAfterChange)',
                      'try change(&state)']:
            self.assertIn(token,forward)
        self.assertNotIn('persistence.commit',forward);self.assertNotIn('publish(',forward)
        self.assertEqual(self.worker.count('persistence.commit('),1)
        self.assertEqual(self.commit.count('try context.performAndWait'),1)
        self.assertIn('let result = try change(&state, transaction)',self.worker)
        self.assertIn('return try mutateInTransaction(historyAction: recordCapture || item.isInHistory) { state, transaction in',self.add)

    def test_capture_checksum_and_candidate_matching_happen_inside_worker(self):
        entry=self.add.index('return try mutateInTransaction(')
        operation=self.add[entry:];preflight=body(operation[:operation.index('if let sourceApplication')],'if recordCapture')
        self.assertIn('checksum = try Self.knownPasteboardChecksum(from: item.payloads)',preflight)
        self.assertIn('item.nativeChecksum = checksum',preflight)
        self.assertIn('item.rawPreview = nil',preflight)
        self.assertIn('item.imagePreviewMetadata = nil',preflight)
        self.assertNotIn('try?',preflight)
        self.assertLess(entry,self.add.index('checksum = try Self.knownPasteboardChecksum'))
        self.assertLess(self.add.index('checksum = try Self.knownPasteboardChecksum'),self.add.index('state.items.firstIndex(where:'))
        lookup=body(body(self.add,'if let i = state.items.firstIndex(where:'),'if recordCapture')
        self.assertIn('guard let checksum else { return false }',lookup)
        self.assertIn('return previous.nativeChecksum == checksum',lookup)

    def test_native_content_replacement_occurs_before_capture_preview_generation(self):
        start=self.add.index('let target: (id: UUID, object: NSManagedObject)?')
        native=self.add[start:self.add.index('if let sourceProvider',start)]
        order=['prepareHistoryItems([state.items[result.index].id])','OriginalPasteboardClassification.f_10032362c(items)',
               'OriginalPasteboardChecksums.f_1003216bc(items, kind: kind)',
               'transaction.repository.replaceCapturedItemData(target!',
               'value = Self.withPreviewMetadata(value,','return value.rawPreview','state.items[result.index] = value']
        positions=[native.index(t)for t in order];self.assertEqual(positions,sorted(positions))
        replace=body(self.graph,'func replace(')
        order=['forKey: "rawType"','forKey: "nativeChecksum"','context.delete(old)',
               'insertNewObject(forEntityName: "ItemDataEntity"','OriginalPasteboardDataCodec.f_10031a8e8(',
               'object.setValue(data, forKey: "data")','object.setValue(preview(), forKey: "rawPreview")']
        positions=[replace.index(t)for t in order];self.assertEqual(positions,sorted(positions))
        self.assertEqual(replace.count('preview()'),1)

    def test_source_sampling_and_native_timestamp_follow_preview(self):
        order=['transaction.repository.replaceCapturedItemData(target!', 'value = Self.withPreviewMetadata(value,',
               'if let sourceProvider','let source = sourceProvider()',
               'state.items[result.index].sourceName = source.name',
               'transaction.repository.restoreHistoryItems([target!])[0].timestamp',
               'state.items[result.index].createdAt = timestamp','state.items[result.index].isInHistory = true',
               'return (state.items[result.index].id, result.isNew)']
        positions=[self.add.index(t)for t in order];self.assertEqual(positions,sorted(positions))
        stamp=body(self.add[self.add.rindex('if recordCapture'):],'if recordCapture')
        self.assertNotIn('Date()',stamp)
        restore=body(self.persistence,'func restoreHistoryItems(')
        self.assertLess(restore.index('let timestamp = Date()'),restore.index('object.setValue(timestamp, forKey: "timestamp")'))
        self.assertIn('if !recordCapture { state.items[i].updatedAt = max(Date(), item.updatedAt) }',self.add)

    def test_replacement_tracker_uses_the_actual_same_managed_target(self):
        replace=body(self.persistence,'func replaceCapturedItemData(')
        self.assertIn('itemData.replace(on: target.object,',replace)
        self.assertIn('useBinaryPlist: useBinaryPlist, preview: preview)',replace)
        self.assertLess(replace.index('itemData.replace('),replace.index('replacedItemDataIDs.insert(target.id)'))
        self.assertIn('private(set) var replacedItemDataIDs: Set<UUID> = []',self.persistence)
        self.assertNotIn('replacingItemDataIDs',self.store+self.persistence)
        self.assertLess(self.commit.index('var outcome = try operation(transaction)'),self.commit.index('let replacements = transaction.repository.replacedItemDataIDs'))
        self.assertIn('updatingKeys: replacements.map(\\.uuidString)',self.commit)

    def test_generic_commit_does_not_replace_or_replay_native_fields_twice(self):
        self.assertIn('if !replacements.contains(item.id) && (old?.payloads != item.payloads || object.value(forKey: "data") == nil)',self.commit)
        self.assertIn('(object.value(forKey: "timestamp") as? Date) != timestamp',self.commit)
        self.assertIn('(object.value(forKey: "nativeIdentifier") as? String) != item.nativeIdentifier',self.commit)
        self.assertIn('(object.value(forKey: "nativeChecksum") as? String) != item.nativeChecksum',self.commit)
        update=body(self.persistence,'func update<T: Equatable>(')
        self.assertIn('if (object.value(forKey: "key") as? String) != id { object.setValue(id, forKey: "key") }',update)
        self.assertIn('before[key($0)] != $0 || forced.contains(key($0))',update)

    def test_new_target_gets_permanent_id_and_identifier_before_content(self):
        prepare=body(self.persistence,'func prepareHistoryItems(')
        self.assertLess(prepare.index('try context.obtainPermanentIDs(for: [object])'),prepare.index('object.setValue(id.uuidString, forKey: "key")'))
        start=self.add.index('let target: (id: UUID, object: NSManagedObject)?')
        native=self.add[start:]
        self.assertLess(native.index('if target!.object.value(forKey: "nativeIdentifier") == nil'),native.index('replaceCapturedItemData('))
        for token in ['state.items[i].id =','state.items[i].title =','state.items[i].sourceDevice =']:
            self.assertNotIn(token,self.add)
        self.assertIn('result = (i, false)',self.add);self.assertIn('result = (state.items.count - 1, true)',self.add)

    def test_non_capture_preview_and_input_identity_compatibility_remain(self):
        header=self.add[:self.add.index('return try mutateInTransaction(')]
        value=body(header,'if !recordCapture')
        self.assertIn('checksum = try? Self.knownPasteboardChecksum(from: item.payloads)',value)
        self.assertIn('if item.nativeIdentifier == nil { item.nativeIdentifier = item.id.uuidString }',value)
        operation=self.add[self.add.index('return try mutateInTransaction('):]
        early=operation[:operation.index('if let sourceApplication')]
        value=early.split('} else {',1)[1]
        self.assertIn('item = Self.withPreviewMetadata(item,',value)
        before=(self.phase/'before/replica/Sources/PastoCore/ClipboardStore.swift').read_text()
        for sig in ['public func createIntentText(', 'private static func withPreviewMetadata(',
                    'public func updateItem(', 'public func importOriginalArchive(']:
            if sig in before:self.assertEqual(body(self.store,sig),body(before,sig))

    def test_errors_and_publication_stay_at_original_transaction_boundary(self):
        self.assertNotIn('catch',self.worker);self.assertNotIn('try?',self.worker)
        self.assertNotIn('context.reset()',self.commit);self.assertNotIn('context.rollback()',self.commit.replace(body(self.commit,'if context.hasChanges'),''))
        self.assertEqual(self.commit.count('try context.save()'),1)
        self.assertIn('OriginalObjCExceptionBridge.f_1002ff9c8 { try context.save() }',self.commit)
        self.assertNotIn('publish(',self.commit)
        order=['try persistence.commit(', 'let result = try change(&state, transaction)',
               'try validate(state)','expireHistory(&state, capacity: capacity)',
               'diskRevision = try revision()','publish(state)']
        positions=[self.worker.index(t)for t in order];self.assertEqual(positions,sorted(positions))
        self.assertNotIn('Task',self.worker+self.commit)

    def test_prior_network_methods_and_all_other_store_methods_are_exactly_unchanged(self):
        before=(self.phase/'before/replica/Sources/PastoCore/ClipboardStore.swift').read_text()
        current=(ROOT/'.local/p0-repair/phase-38/before/replica/Sources/PastoCore/ClipboardStore.swift').read_text()
        worker=body(current,'private func mutateInTransaction<T>(')
        start=current.index('    private func mutateInTransaction<T>(');end=current.index(worker,start)+len(worker)
        current=current[:start]+current[end+2:]
        for sig in ['private func mutate<T>(', 'func addWithInsertionResult(']:
            new=body(current,sig);current=current.replace(new,body(before,sig),1)
        current=current.replace('import CoreData\n','',1)
        declaration='                           replacingItemDataIDs: ((T) -> [UUID])? = nil,\n'
        marker='    private func mutate<T>(historyAction: Bool = false, deletingItemIDs: [UUID] = [], restoringItemIDs: [UUID] = [],\n'
        current=current.replace(marker,marker+declaration,1)
        self.assertEqual(current,before)
        # The schema and migration relationship policy retain the phase34 layout.
        old_graph=(self.phase/'before/replica/Sources/PastoCore/ClipboardItemDataPersistence.swift').read_text()
        self.assertEqual(body(self.graph,'static func addEntity('),body(old_graph,'static func addEntity('))

    def test_original_immediate_flow_and_excluded_link_provider_are_distinguished(self):
        original=original_fragment((ROOT/'decompiled/Paste/part-0275.c').read_text(),'100360ff8')
        order=['setRawType_','setChecksum_','deleteObject_','initWithContext_','FUN_10031a8e8()',
               'setData_','FUN_100322504(','FUN_10031ed94(']
        positions=[original.index(t)for t in order];self.assertEqual(positions,sorted(positions))
        preview=original_fragment((ROOT/'decompiled/Paste/part-0258.c').read_text(),'100322504')
        self.assertIn('if (uVar1 == 4)',preview);self.assertIn('FUN_100319778(',preview)
        self.assertIn('FUN_100312ae4()',preview)
        self.assertEqual(self.proof['preview_types'][0]['name'],'LinkPreview')
        self.assertEqual(self.proof['source_case']['original_order'],self.proof['source_case']['after_order'])
        self.assertNotEqual(self.proof['source_case']['original_order'],self.proof['source_case']['before_order'])
        self.assertFalse(self.proof['full_function_migration_verified'])

if __name__=='__main__':unittest.main()
