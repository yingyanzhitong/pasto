from native_restore_writer_scope_contract import pre_native_restore_writer
from native_title_scope_contract import pre_native_title
from item_order_scope_contract import without_order_model, without_order_projection
"""Source/MOM/Mach-O contracts only; never opens Core Data or user history."""
import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from new_capture_recovery_scope_contract import pre_new_capture_recovery
from native_application_scope_contract import pre_native_application_bytes
from test_p0_repair_checksum_routing import original_fragment


class NativeSourcesContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-41'
        cls.proof = json.loads((cls.phase / 'native-sources-contract.json').read_text())
        cls.source = pre_new_capture_recovery((ROOT / 'replica/Sources/PastoCore/ClipboardSourcePersistence.swift').read_text())
        cls.persistence = pre_native_title((ROOT / 'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text())
        cls.store = pre_native_restore_writer((ROOT / 'replica/Sources/PastoCore/ClipboardStore.swift').read_text())
        cls.provider = (ROOT / 'replica/Sources/Pasto/UI/ReplicaSearchSuggestionSource.swift').read_text()
        cls.commit = body(cls.persistence, 'func commit<T>(previous:')

    def before(self, path):
        return (self.phase / 'before' / path).read_text()

    def test_original_model_defines_source_entities_and_nullify_inverse_relations(self):
        original = self.proof['original_model']
        self.assertEqual(hashlib.sha256((ROOT / original['path']).read_bytes()).hexdigest(), original['sha256'])
        schema = original['schema']
        self.assertEqual(schema['ApplicationEntity']['unique_tuples'], [['bundleIdentifier']])
        self.assertEqual(schema['DeviceEntity']['unique_tuples'], [['identifier']])
        self.assertTrue(schema['ApplicationEntity']['fields']['bundleIdentifier']['NSIsIndexed'])
        self.assertTrue(schema['DeviceEntity']['fields']['identifier']['NSIsIndexed'])
        for relation, destination in [('sourceApplication', 'ApplicationEntity'), ('device', 'DeviceEntity')]:
            field = schema['ItemEntity']['fields'][relation]
            self.assertEqual((field['NSMaxCount'], field['NSDeleteRule'], field['NSIsOptional']), (1, 1, True))
            self.assertEqual(field['_NSDestinationEntityName'], destination)
            self.assertEqual(field['_NSInverseRelationshipName'], 'items')
            self.assertEqual(schema[destination]['fields']['items']['NSDeleteRule'], 1)

    def test_native_entity_attributes_match_original_source_fields(self):
        application = self.source.split('let application = entity(', 1)[1].split('let device = entity(', 1)[0]
        device = self.source.split('let device = entity(', 1)[1].split('connect("sourceApplication"', 1)[0]
        for name, text in [('ApplicationEntity', application), ('DeviceEntity', device)]:
            expected = set(self.proof['original_model']['schema'][name]['fields']) - {'items'}
            self.assertEqual(set(re.findall(r'attribute\("([^"]+)"', text)), expected)
        self.assertIn('key: "bundleIdentifier"', application)
        self.assertIn('key: "identifier"', device)
        self.assertIn('properties.first(where: { $0.name == key })?.isIndexed = true', self.source)
        factory = body(self.source, 'func entity(_ name: String, key: String,')
        self.assertLess(factory.index('value.properties = properties'), factory.index('value.uniquenessConstraints = [[key]]'))
        self.assertIn('attribute("rawType", .integer64AttributeType, defaultValue: 0)', device)
        self.assertIn('attribute("appVersion", .stringAttributeType, defaultValue: "")', device)

    def test_inverse_relationships_are_optional_nullify_and_attach_to_actual_item_model(self):
        graph = body(self.source, 'static func addEntities(')
        connect = body(graph, 'func connect(')
        for token in ['owner.destinationEntity = source', 'owner.maxCount = 1', 'owner.isOptional = true',
                      'items.destinationEntity = item', 'items.maxCount = 0', 'items.isOptional = true',
                      'owner.inverseRelationship = items; items.inverseRelationship = owner']:
            self.assertIn(token, connect)
        self.assertEqual(connect.count('.nullifyDeleteRule'), 2)
        self.assertIn('connect("sourceApplication", source: application)', graph)
        self.assertIn('connect("device", source: device)', graph)
        self.assertIn('ClipboardSourcePersistence.addEntities(to: model, item: model.entitiesByName["Item"]!)', self.persistence)

    def test_old_descriptor_construction_is_unchanged_when_sources_are_disabled(self):
        signature = 'private static func makeModel(includeNativeIdentity:'
        before = body(self.before('replica/Sources/PastoCore/ClipboardPersistence.swift'), signature)
        current = body(self.persistence, signature)
        addition = '        if includeNativeSources { ClipboardSourcePersistence.addEntities(to: model, item: model.entitiesByName["Item"]!) }\n'
        typed = body(current, 'if includeTypedItem')
        legacy = current.replace('        if includeTypedItem ' + typed + '\n', '', 1)
        self.assertEqual(without_order_model(legacy).replace(addition, '', 1), before)
        self.assertIn('entity("Application", [attribute("content", .binaryDataAttributeType)])', current)
        self.assertIn('sourceGraphVersion', self.source)

    def test_six_legacy_model_variants_are_explicitly_preserved(self):
        migration = body(self.persistence, 'private static func migrateLegacyStoreIfNeeded(')
        candidates = migration.split('let legacyCandidates = [', 1)[1].split('\n        ]', 1)[0]
        self.assertEqual(candidates.count('makeModel('), 8)
        self.assertEqual(candidates.count('includeTypedItem: false'), 7)
        self.assertEqual(candidates.count('includeNativeSources: false'), 6)
        self.assertEqual(candidates.count('includeNativeItemData: false'), 5)
        self.assertIn('makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, includeNativeSources: false, includeTypedItem: false, includeItemOrder: false)', candidates)
        order = ['NSMappingModel.inferredMappingModel(', 'manager.migrateStore(', 'coordinator.replacePersistentStore(']
        self.assertEqual([migration.index(t) for t in order], sorted(migration.index(t) for t in order))
        self.assertIn('NSStringFromClass(PastoItemDataMigrationPolicy.self)', migration)

    def test_bootstrap_marker_guards_all_decoding_and_is_written_after_relationships(self):
        bootstrap = body(self.persistence, 'private func bootstrapSourcesIfNeeded(')
        order = ['guard (root.value(forKey: ClipboardSourcePersistence.versionKey)',
                 'let applications = try fetch("Application")', 'for application in applications',
                 'for object in try fetch("Item")', 'try sources.apply(value, applications: applications, to: object)',
                 'root.setValue(1, forKey: ClipboardSourcePersistence.versionKey)']
        self.assertEqual([bootstrap.index(t) for t in order], sorted(bootstrap.index(t) for t in order))
        self.assertIn('?.intValue != 1 else { return }', bootstrap)
        self.assertNotIn('try?', bootstrap)
        self.assertNotIn('context.save()', bootstrap)
        outer = body(self.persistence, 'private func bootstrapListsIfNeeded()')
        self.assertLess(outer.index('try bootstrapSourcesIfNeeded(root)'), outer.index('if context.hasChanges'))
        self.assertLess(outer.index('if context.hasChanges'), outer.index('try context.save()'))

    def test_legacy_device_identity_is_local_persistent_and_not_claimed_vendor_identity(self):
        device = body(self.source, 'private func device(named name: String)')
        order = ['first("DeviceEntity", key: "name", value: name)', 'NSEntityDescription.insertNewObject(',
                 'object.setValue(UUID().uuidString, forKey: "identifier")', 'object.setValue(name, forKey: "name")']
        self.assertEqual([device.index(t) for t in order], sorted(device.index(t) for t in order))
        self.assertNotIn('Host.', device)
        self.assertNotIn('currentDevice', device)
        models = ROOT / 'replica/Sources/PastoCore/Models.swift'
        self.assertEqual(pre_native_application_bytes(models), (self.phase / 'before' / models.relative_to(ROOT)).read_bytes())

    def test_application_metadata_reuses_bundle_identity_and_avoids_equal_field_writes(self):
        application = body(self.source, 'func application(_ value:')
        self.assertIn('first("ApplicationEntity", key: "bundleIdentifier", value: value.bundleIdentifier)', application)
        self.assertIn('if (object.value(forKey: "name") as? String) != value.name', application)
        self.assertIn('if (object.value(forKey: "rawIcon") as? Data) != value.rawIcon', application)
        self.assertIn('Int64(bitPattern: value.rawColor ?? 0)', application)
        app_updates = body(self.commit, 'try transaction.repository.update(state.sourceApplications, previous: previous?.sourceApplications ?? [], entity: "Application", key: { $0.bundleIdentifier })')
        self.assertIn('object.setValue(try encode(value), forKey: "content")', app_updates)
        self.assertIn('try transaction.repository.sources.application(value)', app_updates)

    def test_apply_preserves_missing_application_relation_and_sets_real_inverse_owners(self):
        apply = body(self.source, 'func apply(_ item:')
        self.assertIn('if let identifier = item.sourceApplicationBundleID', apply)
        self.assertIn('throw ClipboardStoreError.invalidSourceApplication', apply)
        self.assertIn('} else { source = nil }', apply)
        self.assertIn('object.setValue(source, forKey: "sourceApplication")', apply)
        self.assertIn('let device = try device(named: item.sourceDevice)', apply)
        self.assertIn('object.setValue(device, forKey: "device")', apply)
        self.assertNotIn('item.sourceName', apply)
        self.assertNotIn('sourceBundleID', apply)

    def test_capture_native_sources_follow_preview_and_sampling_but_precede_timestamp(self):
        capture = body(self.store, 'func addWithInsertionResult(')
        order = ['transaction.repository.replaceCapturedItemData(', 'let source = sourceProvider()',
                 'try transaction.repository.applyCapturedSources(',
                 'transaction.repository.restoreHistoryItems([target!])']
        self.assertEqual([capture.index(t) for t in order], sorted(capture.index(t) for t in order))
        repository = body(self.persistence, 'final class ManagedRepository')
        apply = body(repository, 'func applyCapturedSources(')
        self.assertLess(apply.index('try sources.apply('), apply.index('sourcedItemIDs.insert(target.id)'))
        self.assertIn('to: target.object', apply)

    def test_generic_commit_skips_already_captured_sources_and_recency_only_changes(self):
        self.assertLess(self.commit.index('let outcome = try operation(transaction)'), self.commit.index('let sourced = transaction.repository.sourcedItemIDs'))
        gate = body(self.commit, 'if !sourced.contains(item.id), object.isInserted')
        self.assertIn('try transaction.repository.sources.apply(item, applications: state.sourceApplications, to: object)', gate)
        self.assertIn('|| old?.sourceApplicationBundleID != item.sourceApplicationBundleID', self.commit)
        self.assertIn('|| old?.sourceDevice != item.sourceDevice', self.commit)
        self.assertNotIn('createdAt', gate)
        self.assertNotIn('timestamp', gate)
        self.assertEqual(self.commit.count('try transaction.repository.sources.apply('), 1)

    def test_source_wrappers_share_the_real_context_without_cached_native_objects(self):
        self.assertIn('sources = ClipboardSourcePersistence(context: managedContext)', self.persistence)
        self.assertIn('sources = ClipboardSourcePersistence(context: context)', body(self.persistence, 'final class ManagedRepository'))
        self.assertNotIn('private var ', self.source)
        for kind in ['Application', 'Device']:
            wrapper = body(self.persistence, 'func search' + kind + 'Names(')
            self.assertIn('try context.performAndWait', wrapper)
            for token in ['reset()', 'rollback', 'save()', 'try?']:
                self.assertNotIn(token, wrapper)

    def test_native_queries_match_original_distinct_nonempty_name_predicates_and_sort(self):
        query = body(self.source, 'private func names(in entity:')
        for token in ['NSFetchRequest<NSDictionary>(entityName: entity)', 'request.resultType = .dictionaryResultType',
                      'request.returnsDistinctResults = true', 'request.propertiesToFetch = ["name"]',
                      'NSPredicate(format: "items.@count > 0")',
                      'NSPredicate(format: "name MATCHES[cd] %@ AND items.@count > 0",',
                      'OriginalSearchSuggestions.f_1002f5100(query)', 'NSSortDescriptor(key: "name", ascending: true)',
                      'return try context.fetch(request).compactMap { $0["name"] as? String }.filter { !$0.isEmpty }']:
            self.assertIn(token, query)
        for token in ['try?', 'catch', 'Set(', '.sorted', 'fetchLimit', 'store.items', 'state.items']:
            self.assertNotIn(token, query)
        self.assertIn('try names(in: "ApplicationEntity", matching: query)', self.source)
        self.assertIn('try names(in: "DeviceEntity", matching: query)', self.source)

    def test_original_source_queries_have_same_predicate_distinct_and_empty_name_filter(self):
        source = (ROOT / 'decompiled/Paste/part-0253.c').read_text()
        for suffix in ['10030e070', '10030ed6c']:
            function = original_fragment(source, suffix)
            for token in ['FUN_100c0d760((ID)self.unknown,2)', 'FUN_100c0d780((ID)self.unknown,1)',
                          'name MATCHES[cd] %@ AND items.@count > 0', 'FUN_1002f5100()', 'while (uVar13 == 0)']:
                self.assertIn(token, function)

    def test_real_provider_chain_is_throwing_and_has_no_legacy_source_name_fallback(self):
        for method, kind in [('applications', 'Application'), ('devices', 'Device')]:
            current = body(self.provider, 'static func ' + method + '(')
            self.assertIn('try store.search' + kind + 'Names(matching: query)', current)
            self.assertNotIn('store.items', current)
            self.assertNotIn('sourceName', current)
            self.assertNotIn('Set(', current)
            wrapper = body(self.store, 'public func search' + kind + 'Names(')
            self.assertIn('try persistence.search' + kind + 'Names(matching: query)', wrapper)

    def test_error_handling_stays_at_suggestion_group_or_browser_presentation_boundary(self):
        editor = (ROOT / 'replica/Sources/Pasto/UI/SearchEditor.swift').read_text()
        self.assertIn('parent.onLoadSuggestions(context)', editor)
        index = (ROOT / 'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text()
        for source in ['app', 'device']:
            self.assertIn('try self.suggestionDataSource?.' + source + '($0) ?? []', body(index, 'func suggestions(contextNode:'))
        browser = (ROOT / 'replica/Sources/Pasto/UI/FilterBrowser.swift').read_text()
        self.assertIn('filters: state.availableSearchFilters()', browser)
        load = body((ROOT / 'replica/Sources/PastoCore/OriginalSearchSuggestions.swift').read_text(), 'public static func f_1002e00a0(')
        self.assertIn('try? (provider()?.app("") ?? [])', load)
        self.assertIn('try? (provider()?.device("") ?? [])', load)
        suggestions = (ROOT / 'replica/Sources/PastoCore/OriginalSearchSuggestions.swift').read_text()
        self.assertIn('let candidates = try source(query)', suggestions)
        self.assertIn('} catch {\n                continue', suggestions)

    def test_bootstrap_and_generic_commit_only_publish_marker_with_the_successful_save(self):
        marker = body(self.commit, 'if (root.value(forKey: ClipboardSourcePersistence.versionKey)')
        self.assertIn('root.setValue(1, forKey: ClipboardSourcePersistence.versionKey)', marker)
        self.assertLess(self.commit.index('try transaction.repository.update(state.items'), self.commit.index(marker))
        self.assertLess(self.commit.index(marker), self.commit.index('if context.hasChanges'))
        self.assertNotIn('catch', self.commit)
        self.assertNotIn('rollback', self.commit)

    def test_legacy_records_and_restore_business_algorithms_are_not_rewritten(self):
        previous = self.before('replica/Sources/PastoCore/ClipboardStore.swift')
        for signature in ['private func mutateInTransaction<T>(', 'func recordRestoredSelection(', 'private func merge(']:
            self.assertEqual(body(self.store, signature), body(previous, signature))
        previous = self.before('replica/Sources/PastoCore/ClipboardPersistence.swift')
        for signature in ['func restoreHistoryItems(', 'func prepareHistoryItems(', 'private func content(']:
            self.assertEqual(without_order_projection(body(self.persistence, signature)), body(previous, signature))

    def test_original_binary_selector_mom_and_patch_snapshots_remain_bound(self):
        for row in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / row['path'])[row['address']]['sha256'], row['sha256'])
        binary = self.proof['binary']
        self.assertEqual(hashlib.sha256((ROOT / binary['path']).read_bytes()).hexdigest(), binary['sha256'])
        self.assertEqual({x['selector'] for x in self.proof['native_selector_bindings']},
                         {'setResultType:', 'setReturnsDistinctResults:', 'setPropertiesToFetch:', 'setSortDescriptors:'})
        for row in self.proof['native_selector_bindings']:
            self.assertTrue(row['chain']['declared_chain_reachable'])
            self.assertEqual(row['chain']['pointer_format'], 6)
        for path, digest in self.proof['current_sources'].items():
            self.assertEqual(hashlib.sha256((self.phase / 'after' / path).read_bytes()).hexdigest(), digest)
        self.assertEqual(len(self.proof['contracts']), 6)
        self.assertFalse(self.proof['full_function_migration_verified'])


if __name__ == '__main__':
    unittest.main()
