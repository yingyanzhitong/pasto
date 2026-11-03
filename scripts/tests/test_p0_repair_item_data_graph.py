from item_order_scope_contract import without_order_model
# coding: utf-8
"""Native data graph/migration/source contracts only; no Core Data execution."""
import hashlib,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from snapshot_read_scope_contract import body
from test_p0_repair_checksum_routing import original_fragment

class ItemDataGraphContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-34'
        cls.proof=json.loads((cls.phase/'item-data-lifecycle-contract.json').read_text())
        cls.schema=json.loads((ROOT/cls.proof['model']['schema_path']).read_text())
        cls.graph=(ROOT/'replica/Sources/PastoCore/ClipboardItemDataPersistence.swift').read_text()
        cls.persistence=(ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text()
        cls.store=(ROOT/'replica/Sources/PastoCore/ClipboardStore.swift').read_text()
        cls.pasteboard=(ROOT/'replica/Sources/PastoCore/Pasteboard.swift').read_text()
        cls.commit=body(cls.persistence,'func commit<T>(previous: StoreState?, deletingItemIDs: [UUID] = [],')
        cls.mutate=body(cls.store,'private func mutateInTransaction<T>(historyAction: Bool = false,')

    def test_original_fragments_model_resource_and_sdk_policy_declarations_are_bound(self):
        for r in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        resource=self.proof['model']
        for p,h in [(resource['path'],resource['sha256']),(resource['schema_path'],resource['schema_sha256']),*self.proof['sdk_headers'].items()]:
            path=Path(p)if Path(p).is_absolute()else ROOT/p
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),h)

    def test_real_model_is_required_data_with_inverse_cascade_and_deny(self):
        props=self.schema['ItemDataEntity']['properties'];relation=self.schema['ItemEntity']['properties']['data']
        self.assertEqual(props['rawPasteboardItems']['NSAttributeType'],1000)
        self.assertFalse(props['rawPasteboardItems'].get('NSIsOptional',False))
        self.assertEqual(props['rawPasteboardItems']['NSFlagsKey'],4)
        self.assertEqual(props['item']['NSDeleteRule'],3)
        self.assertTrue(props['item']['NSIsOptional']);self.assertEqual(props['item']['_NSInverseRelationshipName'],'data')
        self.assertEqual(relation['NSDeleteRule'],2);self.assertFalse(relation.get('NSIsOptional',False))
        self.assertEqual(relation['_NSDestinationEntityName'],'ItemDataEntity')
        factory=body(self.graph,'static func addEntity(')
        for token in ['data.name = "ItemDataEntity"','raw.isOptional = false; raw.allowsExternalBinaryDataStorage = true',
                      'owner.isOptional = true; owner.deleteRule = .denyDeleteRule',
                      'content.isOptional = false; content.deleteRule = .cascadeDeleteRule',
                      'content.inverseRelationship = owner; owner.inverseRelationship = content',
                      'item.properties += [kind, preview, content]','model.entities.append(data)']:
            self.assertIn(token,factory)

    def test_original_and_actual_replacement_share_delete_create_assign_order(self):
        original=original_fragment((ROOT/'decompiled/Paste/part-0275.c').read_text(),'100360ff8')
        order=['setRawType_','setChecksum_','objc_stub::data(param_1)','deleteObject_',
               'FUN_10031b5e4()','initWithContext_','FUN_10031a8e8()','setData_','FUN_100322504(']
        positions=[original.index(t)for t in order];self.assertEqual(positions,sorted(positions))
        replacement=body(self.graph,'func replace(')
        order=['forKey: "rawType"','forKey: "nativeChecksum"','object.value(forKey: "data")',
               'context.delete(old)','insertNewObject(forEntityName: "ItemDataEntity", into: context)',
               'OriginalPasteboardDataCodec.f_10031a8e8(','forKey: "rawPasteboardItems"',
               'object.setValue(data, forKey: "data")','object.setValue(preview(), forKey: "rawPreview")']
        positions=[replacement.index(t)for t in order];self.assertEqual(positions,sorted(positions))
        for token in ['forKey: "title"','forKey: "device"','forKey: "list"','forKey: "nativeIdentifier"',
                      'context.save','context.reset','context.rollback','Task','DispatchQueue']:
            self.assertNotIn(token,replacement)

    def test_capture_result_id_forces_replacement_even_for_equal_values(self):
        add=body(self.store,'func addWithInsertionResult(')
        self.assertIn('transaction.repository.replaceCapturedItemData(target!',add)
        self.assertIn('replacedItemDataIDs.insert(target.id)',self.persistence)
        self.assertIn('let replacements = transaction.repository.replacedItemDataIDs',self.commit)
        self.assertIn('updatingKeys: replacements.map(\\.uuidString)',self.commit)
        update=body(self.persistence,'func update<T: Equatable>(')
        self.assertIn('let forced = Set(updatingKeys)',update)
        self.assertIn('let changed = values.filter { before[key($0)] != $0 || forced.contains(key($0)) }',update)
        self.assertIn('if !replacements.contains(item.id) && (old?.payloads != item.payloads || object.value(forKey: "data") == nil)',self.commit)

    def test_native_update_is_guarded_by_checksum_and_uses_same_repository_context(self):
        repo=body(self.persistence,'final class ManagedRepository')
        self.assertIn('itemData = ClipboardItemDataPersistence(context: context)',repo)
        delta=body(self.commit,'if !replacements.contains(item.id)')
        guarded=body(delta,'if let checksum = OriginalPasteboardChecksums.f_1003216bc(items, kind: kind)')
        self.assertIn('transaction.repository.itemData.replace(on: object, items: items, kind: kind, checksum: checksum,',guarded)
        self.assertIn('useBinaryPlist: state.preferences.useBinaryPlist',guarded)
        self.assertNotIn('try?',delta)
        self.assertEqual(self.commit.count('try context.performAndWait'),1)
        self.assertLess(self.commit.index('let outcome = try operation(transaction)'),self.commit.index('itemData.replace'))
        self.assertLess(self.commit.index('itemData.replace'),self.commit.index('try transaction.repository.lists.refreshHistoryIfNeeded()'))
        self.assertLess(self.commit.index('try transaction.repository.lists.refreshHistoryIfNeeded()'),self.commit.index('try context.save()'))

    def test_timestamp_only_restore_still_skips_payload_and_content_encoding(self):
        restore=body(self.store,'func recordRestoredItems(')
        self.assertNotIn('replacingItemDataIDs',restore)
        self.assertIn('private(set) var replacedItemDataIDs: Set<UUID> = []',self.persistence)
        gate='!replacements.contains(item.id) && (old?.payloads != item.payloads || object.value(forKey: "data") == nil)'
        self.assertIn(gate,self.commit)
        self.assertIn('if old.map(content) != content(item)',self.commit)
        content=body(self.persistence,'private func content(')
        self.assertIn('value.updatedAt = value.createdAt; value.isInHistory = false',content)

    def test_read_consumes_native_data_and_preview_not_only_legacy_content(self):
        read=body(self.persistence,'private func item(_ object: NSManagedObject)')
        order=['try Self.decode(ClipboardItem.self, object)','object.value(forKey: "data") as? NSManagedObject',
               'data.value(forKey: "rawPasteboardItems") as? Data',
               'ClipboardStore.projectNativePasteboardItems(raw, onto: item.payloads)',
               'item.rawPreview = object.value(forKey: "rawPreview") as? Data',
               'OriginalImagePreviewMetadataCodec.decode(item.rawPreview)','return item']
        positions=[read.index(t)for t in order];self.assertEqual(positions,sorted(positions))
        self.assertIn('throw CocoaError(.fileReadCorruptFile)',read)
        project=body(self.pasteboard,'nonisolated static func projectNativePasteboardItems(')
        self.assertIn('OriginalPasteboardDataCodec.f_10031aeec(raw)',project)
        self.assertIn('first.f_10037da6c()',project)
        self.assertIn('first.f_10037d810(forType: type)',project)

    def test_projection_keeps_ordered_single_multi_raw_and_analysis_domains(self):
        project=body(self.pasteboard,'nonisolated static func projectNativePasteboardItems(')
        self.assertIn('previous.filter { analysisPayloadKeys.contains($0.key) }',project)
        self.assertIn('if let order = previous[orderedTypesPayloadKey]',project)
        self.assertIn('? order : try JSONEncoder().encode(first.f_10037da6c())',project)
        self.assertIn('JSONEncoder().encode(first.f_10037da6c())',project)
        self.assertIn('if previous[multiItemPayloadKey] != nil',project)
        self.assertIn('payloads[multiItemPayloadKey] = try encoder.encode(items)',project)
        self.assertIn('encoder.outputFormatting = [.sortedKeys]',project)
        self.assertIn('payloads[multiItemPayloadKey] = previous[multiItemPayloadKey]',project)
        self.assertIn('types == new.f_10037da6c() && types.allSatisfy',project)
        self.assertIn('previous[originalItemDataPayloadKey] != nil || items.count > 1',project)
        self.assertIn('payloads[originalItemDataPayloadKey] = raw',project)
        for token in ['Set(','.sorted(','UserDefaults','NSPasteboard.general']:
            self.assertNotIn(token,project)
        # The projection helper is the only addition to the original capture file.
        full='    nonisolated static func projectNativePasteboardItems'
        checkpoint=(ROOT/'.local/p0-repair/phase-36/before/replica/Sources/PastoCore/Pasteboard.swift').read_text()
        self.assertEqual(project,body(checkpoint,'nonisolated static func projectNativePasteboardItems('))
        start=checkpoint.index(full);content=body(checkpoint,'nonisolated static func projectNativePasteboardItems(')
        end=checkpoint.index(content,start)+len(content)
        self.assertEqual(checkpoint[:start]+checkpoint[end+2:],
                         (self.phase/'before/replica/Sources/PastoCore/Pasteboard.swift').read_text())

    def test_prior_models_are_preserved_with_new_graph_disabled(self):
        migration=body(self.persistence,'private static func migrateLegacyStoreIfNeeded(')
        candidates=migration.split('let legacyCandidates = [',1)[1].split('\n        ]',1)[0]
        self.assertEqual(candidates.count('makeModel('),8)
        self.assertEqual(candidates.count('includeTypedItem: false'),7)
        self.assertEqual(candidates.count('includeNativeItemData: false'),5)
        self.assertEqual(candidates.count('includeOptionalTimestamp: false'),4)
        self.assertEqual(candidates.count('includeNativeSources: false'),6)
        self.assertIn('makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, includeNativeItemData: false, includeNativeSources: false, includeTypedItem: false, includeItemOrder: false)',candidates)
        before=(self.phase/'before/replica/Sources/PastoCore/ClipboardPersistence.swift').read_text()
        old=body(before,'private static func makeModel(');current=body(self.persistence,'private static func makeModel(')
        addition='        if includeNativeItemData { ClipboardItemDataPersistence.addEntity(to: model, item: model.entitiesByName["Item"]!) }\n'
        sources='        if includeNativeSources { ClipboardSourcePersistence.addEntities(to: model, item: model.entitiesByName["Item"]!) }\n'
        typed = body(current, 'if includeTypedItem')
        legacy = current.replace('        if includeTypedItem ' + typed + '\n', '', 1)
        self.assertEqual(without_order_model(legacy).replace(addition,'',1).replace(sources,'',1),old)

    def test_policy_fills_required_relation_before_migration_validates_and_replaces_source(self):
        migration=body(self.persistence,'private static func migrateLegacyStoreIfNeeded(')
        order=['NSMappingModel.inferredMappingModel(', 'if sourceModel.entitiesByName["ItemDataEntity"] == nil',
               'entity.destinationEntityName == "Item"',
               'entity.entityMigrationPolicyClassName = NSStringFromClass(PastoItemDataMigrationPolicy.self)',
               'let manager = NSMigrationManager(', 'try manager.migrateStore(', 'try coordinator.replacePersistentStore(']
        positions=[migration.index(t)for t in order];self.assertEqual(positions,sorted(positions))
        self.assertNotIn('removeItem(at: storeURL)',migration);self.assertNotIn('destroyPersistentStore',migration)
        policy=body(self.graph,'override func createRelationships(')
        self.assertIn('try super.createRelationships(forDestination: object, in: mapping, manager: manager)',policy)
        self.assertIn('guard object.value(forKey: "data") == nil else { return }',policy)
        self.assertIn('ClipboardItemDataPersistence(context: manager.destinationContext).replace',policy)
        for token in ['sourceContext.save','sourceContext.delete','replacePersistentStore','FileManager', 'context.reset']:
            self.assertNotIn(token,policy)

    def test_migration_keeps_legacy_bytes_preview_preferences_and_identity(self):
        policy=body(self.graph,'override func createRelationships(')
        self.assertIn('try manager.sourceContext.fetch(request)',policy)
        self.assertIn('PropertyListDecoder().decode(AppPreferences.self, from: bytes).useBinaryPlist',policy)
        self.assertIn('guard roots.count <= 1',policy)
        self.assertIn('checksum: object.value(forKey: "nativeChecksum") as? String',policy)
        self.assertIn('value.rawPreview ?? OriginalImagePreviewMetadataCodec.encode(',policy)
        self.assertIn('if let raw = value.payloads[originalItemDataPayloadKey]',policy)
        self.assertIn('data.setValue(raw, forKey: "rawPasteboardItems")',policy)
        self.assertNotRegex(policy,r'setValue\([^)]*,\s*forKey: \"(?:content|key|nativeIdentifier|list)\"')
        self.assertNotIn('.setValue(',policy.split('let value =',1)[0])

    def test_parent_is_still_partial_and_network_functions_unchanged(self):
        self.assertEqual(self.proof['newly_closed_records'],[])
        self.assertEqual(self.proof['new_migration_markers'],0)
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertIn('Preview generation still precedes native replacement',self.proof['retained_partial_contracts'][0])
        before=(self.phase/'before/replica/Sources/PastoCore/ClipboardStore.swift').read_text()
        checkpoint=(ROOT/'.local/p0-repair/phase-35/before/replica/Sources/PastoCore/ClipboardStore.swift').read_text()
        reconstructed=checkpoint.replace('                           replacingItemDataIDs: ((T) -> [UUID])? = nil,\n','',1)
        reconstructed=reconstructed.replace('try persistence.commit(previous: remote, deletingItemIDs: deletingItemIDs,\n'
            '                                                       replacingItemDataIDs: replacingItemDataIDs)',
            'try persistence.commit(previous: remote, deletingItemIDs: deletingItemIDs)',1)
        reconstructed=reconstructed.replace('return try mutate(historyAction: recordCapture || item.isInHistory,\n'
            '                          replacingItemDataIDs: { recordCapture ? [$0.id] : [] })',
            'return try mutate(historyAction: recordCapture || item.isInHistory)',1)
        self.assertEqual(reconstructed,before)
        for signature in ['private static func cloudKitGraph(', 'private static func captureCloudKit(',
                          'public func prepareCloudKit(', 'public func mergeCloudKit(']:
            if signature not in before:continue
            self.assertEqual(body(self.store,signature),body(before,signature))

if __name__=='__main__':unittest.main()
