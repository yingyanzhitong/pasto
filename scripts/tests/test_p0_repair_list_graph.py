"""Local List graph/source contracts. Does not instantiate Core Data or run Swift."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from macho_imports import parse_macho
from snapshot_read_scope_contract import body


class ListGraphContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-12'
        cls.lists = (ROOT / 'replica/Sources/PastoCore/ClipboardListPersistence.swift').read_text()
        cls.persistence = (ROOT / 'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text()
        cls.store = (ROOT / 'replica/Sources/PastoCore/ClipboardStore.swift').read_text()
        cls.attributes = (ROOT / 'replica/Sources/PastoCore/OriginalPinboardAttributes.swift').read_text()
        cls.proof = json.loads((cls.phase / 'list-root-contract.json').read_text())
        cls.schema = json.loads((cls.phase / 'model-offline-schema.json').read_text())

    def test_original_fragments_and_prior_first_fetch_proofs_are_bound(self):
        for name, key in [('list-root-contract.json', 'original_fragments'),
                          ('list-refresh-proof.json', 'original_fragments'),
                          ('list-attributes-model-proof.json', 'original_function_fragments')]:
            proof = json.loads((self.phase / name).read_text())
            for r in proof[key]:
                address = r.get('address') or r['function_id'].split(':')[-1]
                self.assertEqual(source_fragments(ROOT / r['path'])[address]['sha256'], r['sha256'])
        for path, digest in self.proof['prior_first_fetch_proofs'].items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), digest)

    def test_model_resource_and_decoded_schema_are_bound(self):
        resource = self.proof['model_resource']
        self.assertEqual(hashlib.sha256((ROOT / resource['path']).read_bytes()).hexdigest(), resource['sha256'])
        self.assertEqual(resource['sha256'], '25ee25cb8d2e5745c2d258e278ea5a64c72e1f1124f07392dcfdc21e39febc95')
        self.assertEqual(hashlib.sha256((ROOT / resource['decoded_schema_path']).read_bytes()).hexdigest(),
                         resource['decoded_schema_sha256'])

    def test_resource_relations_are_cascade_metadata_deny_inverse_and_nullify_items(self):
        self.assertEqual(self.schema['ListEntity']['metadata']['NSDeleteRule'], 2)
        self.assertEqual(self.schema['ListMetadataEntity']['list']['NSDeleteRule'], 3)
        self.assertEqual(self.schema['ListEntity']['items']['NSDeleteRule'], 1)
        self.assertEqual(self.schema['ItemEntity']['list']['NSDeleteRule'], 1)
        self.assertEqual(self.schema['ListEntity']['items']['NSMaxCount'], 0)
        self.assertEqual(self.schema['ItemEntity']['list']['NSMaxCount'], 1)
        self.assertEqual(self.schema['ListEntity']['metadata']['_NSDestinationEntityName'], 'ListMetadataEntity')
        self.assertEqual(self.schema['ItemEntity']['list']['_NSInverseRelationshipName'], 'items')

    def test_new_graph_uses_real_inverse_managed_relationships(self):
        graph = body(self.lists, 'static func addEntities(to model: NSManagedObjectModel, item: NSEntityDescription)')
        for token in ['entity("ListEntity")', 'entity("ListMetadataEntity")',
                      'rule: .cascadeDeleteRule', 'rule: .denyDeleteRule',
                      'listMetadata.inverseRelationship = metadataList', 'metadataList.inverseRelationship = listMetadata',
                      'items.inverseRelationship = owner', 'owner.inverseRelationship = items',
                      'item.properties.append(owner)', 'model.entities += [list, metadata]']:
            self.assertIn(token, graph)
        self.assertEqual(graph.count('rule: .nullifyDeleteRule'), 2)

    def test_native_model_field_types_and_optional_attributes_match_offline_resource(self):
        self.assertEqual(self.schema['ListEntity']['rawAttributes']['NSAttributeType'], 1000)
        self.assertTrue(self.schema['ListEntity']['rawAttributes']['NSIsOptional'])
        self.assertEqual(self.schema['ListEntity']['rawType']['NSAttributeType'], 300)
        self.assertEqual(self.schema['ListMetadataEntity']['index']['NSAttributeType'], 300)
        for token in ['attribute("rawAttributes", .binaryDataAttributeType, optional: true)',
                      'attribute("rawType", .integer64AttributeType, defaultValue: 0)',
                      'attribute("index", .integer64AttributeType, defaultValue: 0)']:
            self.assertIn(token, self.lists)
        self.assertIn('model.entitiesByName["Item"]!', self.persistence)

    def test_first_list_has_original_default_sort_optional_override_and_fetch_configuration(self):
        fetch = body(self.lists, 'func firstList(predicate: NSPredicate?, sortDescriptors: [NSSortDescriptor]? = nil)')
        order = ['NSFetchRequest<NSManagedObject>(entityName: "ListEntity")', 'request.predicate = predicate',
                 'sortDescriptors ?? [NSSortDescriptor(key: "metadata.index", ascending: true)]',
                 'request.fetchLimit = 1', 'request.fetchOffset = 0', 'request.fetchBatchSize = 20',
                 'return try context.fetch(request).first']
        positions = [fetch.index(t) for t in order]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn('State', fetch)
        self.assertNotIn('try?', fetch)

    def test_history_lookup_uses_the_fixed_original_identifier(self):
        self.assertIn('static let historyIdentifier = "sharedPasteboardHistory"', self.lists)
        history = body(self.lists, 'func historyList() throws')
        self.assertIn('firstList(predicate: NSPredicate(format: "identifier == %@", Self.historyIdentifier))', history)

    def test_refresh_fetches_real_list_and_merges_only_when_marked_and_present(self):
        refresh = body(self.lists, 'func refreshHistoryIfNeeded() throws')
        order = ['guard refreshHistoryAfterOperation else { return }',
                 'guard let history = try historyList() else { return }', 'context.refresh(history, mergeChanges: true)']
        positions = [refresh.index(t) for t in order]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn('root()', refresh)
        self.assertNotIn('"State"', refresh)

    def test_legacy_model_migration_recognizes_native_identity_and_both_earlier_variants(self):
        migration = body(self.persistence, 'private static func migrateLegacyStoreIfNeeded(at storeURL: URL,')
        for native, preserve in [('true', 'true'), ('false', 'true'), ('false', 'false')]:
            self.assertIn(f'makeModel(includeNativeIdentity: {native}, preserveItemKeyInHistory: {preserve}, includeLists: false, includeOptionalTimestamp: false, includeNativeItemData: false, includeNativeSources: false, includeTypedItem: false, includeItemOrder: false)', migration)
        self.assertIn('makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, includeLists: true, includeOptionalTimestamp: false, includeNativeItemData: false, includeNativeSources: false, includeTypedItem: false, includeItemOrder: false)', migration)
        self.assertIn('includeLists: Bool = true', self.persistence)
        self.assertLess(migration.index('try manager.migrateStore'), migration.index('try coordinator.replacePersistentStore'))
        self.assertNotIn('destroyPersistentStore', migration)
        self.assertNotIn('removeItem(at: storeURL)', migration)

    def test_bootstrap_runs_before_observation_and_preserves_encoded_content(self):
        init = body(self.persistence, 'init(directoryURL: URL) throws')
        self.assertLess(init.index('try bootstrapListsIfNeeded()'), init.index('contextChangesObservation ='))
        bootstrap = body(self.persistence, 'private func bootstrapListsIfNeeded() throws')
        self.assertIn('guard let root = try root() else { return }', bootstrap)
        self.assertIn('if try lists.historyList() == nil', bootstrap)
        self.assertLess(bootstrap.index('try bootstrapHistoryTimestamps()'), bootstrap.index('try context.save()'))
        self.assertIn('decode(ClipboardItem.self, object)', bootstrap)
        self.assertIn('object.setValue(owner, forKey: "list")', bootstrap)
        self.assertNotIn('forKey: "content"', bootstrap)
        self.assertNotIn('pinboardIDs =', bootstrap)
        self.assertNotIn('context.reset()', bootstrap)
        self.assertIn('try perform', bootstrap)

    def test_new_list_objects_get_permanent_ids_before_required_fields_and_relations(self):
        make = body(self.lists, 'private func makeList(identifier: String, name: String, rawType: Int64,')
        order = ['insertNewObject(forEntityName: "ListEntity"', 'insertNewObject(forEntityName: "ListMetadataEntity"',
                 'try context.obtainPermanentIDs(for: [list, metadata])', 'let now = Date()',
                 'list.setValue(identifier, forKey: "identifier")', 'metadata.setValue(index, forKey: "index")',
                 'list.setValue(metadata, forKey: "metadata")']
        positions = [make.index(t) for t in order]
        self.assertEqual(positions, sorted(positions))
        self.assertIn('forKey: "createdAt"', make)

    def test_actual_read_consumers_project_metadata_attributes_and_relationship_owner(self):
        read = body(self.persistence, 'func read() throws -> StoreState')
        self.assertIn('preferences.historyRetentionDays = try lists.historyCapacity() ?? 30', read)
        self.assertIn('pinboards: lists.project(', read)
        item = body(self.persistence, 'private func item(_ object: NSManagedObject)')
        self.assertIn('object.value(forKey: "list") as? NSManagedObject', item)
        self.assertIn('item.pinboardOwnerID = owner', item)
        self.assertIn('item.pinboardIDs.insert(owner)', item)
        self.assertNotIn('item.pinboardIDs = []', item)
        project = body(self.lists, 'func project(_ pinboards: [Pinboard])')
        for token in ['value.name = list.value(forKey: "name")',
                      'value.rawAttributes = list.value(forKey: "rawAttributes")', 'metadata.value(forKey: "index")']:
            self.assertIn(token, project)

    def test_attributes_none_and_invalid_do_not_become_decoded_default_capacity(self):
        capacity = body(self.attributes, 'public static func clipboardCapacity(from data: Data?)')
        self.assertIn('guard let data, let attributes = try? JSONDecoder().decode(Attributes.self, from: data) else { return nil }', capacity)
        self.assertIn('guard case let .clipboard(capacity) = f_1003245fc(attributes) else { return nil }', capacity)
        value = body(self.attributes, 'private static func f_1003245fc(_ attributes: Attributes)')
        self.assertIn('if attributes.type == "pinboard"', value)
        self.assertIn('.clipboard(capacity: attributes.capacity ?? 30)', value)
        self.assertIn('.pinboard(colorCode: attributes.colorCode ?? 0)', value)

    def test_history_writer_preserves_unrelated_invalid_attributes_and_the_user_week_default(self):
        sync = body(self.lists, 'func synchronize(pinboards: [Pinboard], preferences: AppPreferences, previous: StoreState?)')
        guarded = body(sync, 'if previous?.preferences.historyRetentionDays != preferences.historyRetentionDays')
        self.assertIn('encodedClipboard(capacity: preferences.historyRetentionDays)', guarded)
        self.assertNotIn('encodedClipboard(capacity: 30)', sync)
        self.assertIn('historyRetentionDays: Int = 7', (ROOT / 'replica/Sources/PastoCore/Models.swift').read_text())
        encode = body(self.attributes, 'static func encodedClipboard(capacity: Int)')
        self.assertIn('Attributes(type: "clipboard", capacity: capacity, colorCode: nil)', encode)

    def test_mutation_prepares_native_list_then_reads_its_attributes_without_extra_fetch(self):
        mutate = body(self.store, 'private func mutateInTransaction<T>(historyAction: Bool = false,')
        order = ['try change(&state, transaction)', 'normalize(&state)', 'let lists = transaction.repository.lists',
                 'let history = try lists.synchronize(', 'if let capacity = lists.historyCapacity(of: history)',
                 'expireHistory(&state, capacity: capacity)', 'lists.refreshHistoryAfterOperation =']
        positions = [mutate.index(t) for t in order]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn('try lists.historyCapacity()', mutate)
        capacity = body(self.lists, 'func historyCapacity(of history: NSManagedObject)')
        self.assertIn('history.value(forKey: "rawAttributes") as? Data', capacity)
        self.assertNotIn('fetch', capacity)

    def test_expiration_has_original_checked_day_arithmetic_date_constructor_and_group_guard(self):
        expire = body(self.store, 'private func expireHistory(_ state:')
        for token in ['guard capacity > 0 else { return }', 'let interval = -capacity * 24 * 60 * 60',
                      'Date(timeIntervalSinceNow: Double(interval))',
                      '$0.isInHistory && $0.pinboardIDs.isEmpty && $0.createdAt < cutoff']:
            self.assertIn(token, expire)
        imported = parse_macho(ROOT / '.local/paste-arm64-static.bin')['stubs'][self.proof['date_import']['address']]
        self.assertEqual(imported['symbol'], self.proof['date_import']['symbol'])
        self.assertIn('DateV20timeIntervalSinceNow', imported['symbol'])

    def test_empty_restore_returns_before_transaction_and_nonempty_preserves_reverse_recency(self):
        restore = body(self.store, 'func recordRestoredItems(_ ids: [UUID])')
        self.assertLess(restore.index('guard !ids.isEmpty else { return }'),
                        restore.index('try mutate(historyAction: true, restoringItemIDs: ids)'))
        native_restore = body(self.persistence, 'func restoreHistoryItems(')
        self.assertIn('for (id, object) in targets.reversed()', native_restore)
        self.assertIn('let timestamp = Date()', native_restore)

    def test_history_delete_including_empty_reads_context_once_before_marking_refresh(self):
        delete = body(self.store, 'public func delete(orderedIDs: [UUID], currentPinboardID: () -> UUID?)')
        self.assertEqual(delete.count('currentPinboardID()'), 1)
        order = ['var refreshHistory = false', 'try mutate(deletingItemIDs: orderedIDs, refreshHistoryAfterChange: { refreshHistory })',
                 'let contextPinboardID = currentPinboardID()', 'refreshHistory = contextPinboardID == nil',
                 'for i in state.items.indices']
        positions = [delete.index(t) for t in order]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn('guard !orderedIDs.isEmpty', delete)
        mutate = body(self.store, 'private func mutateInTransaction<T>(historyAction: Bool = false,')
        self.assertIn('historyAction || (refreshHistoryAfterChange?() ?? false)', mutate)

    def test_relation_writes_and_refresh_precede_conditional_save_in_same_transaction(self):
        commit = body(self.persistence, 'func commit<T>(previous: StoreState?, deletingItemIDs: [UUID] = [],')
        order = ['let outcome = try operation(transaction)', 'transaction.repository.update(state.items',
                 'object.setValue(owner, forKey: "list")', 'try transaction.repository.lists.refreshHistoryIfNeeded()',
                 'if context.hasChanges', 'try context.save()', 'return outcome']
        positions = [commit.index(t) for t in order]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(commit.count('try context.performAndWait'), 1)

    def test_initial_commit_also_builds_the_graph_without_a_history_refresh_flag(self):
        wrapper = body(self.persistence, 'func commit(_ state: StoreState, previous: StoreState?, deletingItemIDs: [UUID] = [])')
        self.assertIn('try transaction.repository.lists.synchronize(', wrapper)
        self.assertNotIn('refreshHistoryAfterOperation = true', wrapper)
        self.assertIn('var refreshHistoryAfterOperation = false', self.lists)


if __name__ == '__main__':
    unittest.main()
