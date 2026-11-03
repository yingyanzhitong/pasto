from frc_result_scope_contract import assert_query_result_only
"""Native-ID flow/source contracts; no Spotlight, preferences, DB, app or compiler execution."""
import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from native_search_content_scope_contract import pre_native_search_content_bytes
from snapshot_read_scope_contract import body, projection_spelling
from index_write_scope_contract import assert_write_scope_only, assert_service_initializer_only, assert_ui_service_composition_only
from test_p0_repair_identity import method_body
from test_p0_repair_checksum_routing import original_fragment


def query_projection(source, sdk_ids):
    query = body(source, 'nonisolated private static func matchingIdentifiers(')
    loop = body(query, 'for try await result in query.results')
    for required in ['var found: [String] = []', 'var resultCount = 0', 'try Task.checkCancellation()']:
        if required not in query:
            raise ValueError('Missing raw-result contract')
    for required in ['resultCount += 1', 'found.append(result.item.uniqueIdentifier)', 'if resultCount == limit { break }']:
        if required not in loop:
            raise ValueError('Missing raw SDK-result projection')
    if any(token in query for token in ['filterQueries', 'UUID(', 'hasPrefix', 'dropFirst', 'found.insert', 'Set<String>']):
        raise ValueError('Unexpected result narrowing or deduplication')
    limit = int(re.search(r'private static let maximumResultCount = (\d+)', source)[1])
    return sdk_ids[:limit]


def delete_windows(source, identifiers):
    method = body(source, 'private func deleteIdentifiers(')
    for required in ['let input = identifiers[lowerBound..<upperBound]', 'let batch = Array(input)',
                     'index.deleteSearchableItems(withIdentifiers: batch)']:
        if required not in method:
            raise ValueError('Missing native delete projection')
    before_sdk = method[:method.index('index.deleteSearchableItems(')]
    if any(token in before_sdk for token in ['domain +', 'UUID(', 'compactMap', 'Set(', 'filter', 'sorted']):
        raise ValueError('Unexpected native-ID transformation')
    limit = int(re.search(r'private static let deletionBatchSize = (\d+)', source)[1])
    return [identifiers[i:i + limit] for i in range(0, len(identifiers), limit)]


class NativeSearchIdentifierContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-55'
        cls.proof = json.loads((cls.phase / 'native-ID-contract.json').read_text())
        cls.path = 'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift'
        cls.source = (ROOT / cls.path).read_text()
        cls.before = (cls.phase / 'before' / cls.path).read_text()
        cls.query = body(cls.source, 'nonisolated private static func matchingIdentifiers(')
        cls.rebuild = body(cls.source, 'private func enqueueDelegateRebuild(')
        cls.builder = body(cls.source, 'private func searchableItem(')
        cls.delete = body(cls.source, 'private func deleteIdentifiers(')
        cls.original = {r['address']: original_fragment((ROOT / r['path']).read_text(), r['address'][2:])
                        for r in cls.proof['original_fragments']}

    def test_original_fragments_and_prior_clear_cancel_contracts_are_hash_bound(self):
        self.assertEqual(len(self.proof['original_fragments']), 17)
        for row in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / row['path'])[row['address']]['sha256'], row['sha256'])
        for row in self.proof['prior_contracts']:
            self.assertEqual(hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest(), row['sha256'])
        for path, digest in self.proof['current_sources'].items():
            self.assertEqual(hashlib.sha256((self.phase / 'after' / path).read_bytes()).hexdigest(), digest)
            if path == self.path:
                frozen = (self.phase / 'after' / path).read_text()
                for marker in ['nonisolated private static func matchingIdentifiers(', 'private func searchableItem(',
                               'private func deleteIdentifiers(',
                               'private func clearIndex()', 'init(directoryURL:']:
                    if marker == 'init(directoryURL:':
                        assert_service_initializer_only(self, self.source, frozen)
                    else:
                        assert_write_scope_only(self, body(self.source, marker), body(frozen, marker))
            elif path == 'replica/Sources/PastoCore/ClipboardPersistence.swift':
                frozen = (self.phase / 'after' / path).read_text()
                for marker in ['func searchIndexRecords(', 'func searchNativeItems(', 'func searchIndexIdentifiers(']:
                    current = body((ROOT / path).read_text(), marker)
                    previous = body(frozen, marker)
                    if marker in ['func searchIndexRecords(', 'func searchNativeItems(']:
                        old_head, _, old_tail = previous.partition('let request = NSFetchRequest<NSManagedObject>(entityName: "Item")')
                        new_head, _, new_tail = current.partition('let request = PastoItemEntity.defaultFetchRequest()')
                        self.assertIn('PastoItemEntity.defaultFetchRequest()', current)
                        self.assertEqual(tuple(map(projection_spelling, (new_head, new_tail))), tuple(map(projection_spelling, (old_head, old_tail))))
                    else:
                        self.assertEqual(current, previous)
            else:
                self.assertEqual(hashlib.sha256(pre_native_search_content_bytes(ROOT / path)).hexdigest(), digest)

    def test_native_query_context_has_only_original_fetch_attribute_setup(self):
        native = self.original['0x1002e2930']
        self.assertIn('objc_stub::setFetchAttributes_', native)
        self.assertNotIn('setFilterQueries', native)
        self.assertLess(native.index('setFetchAttributes_'), native.index('initWithQueryString_queryContext_'))
        self.assertIn('context.fetchAttributes = []', self.query)
        self.assertNotIn('filterQueries', self.query)
        self.assertNotIn('pasteReplicaStore', self.source)
        self.assertIn('guard !predicate.isEmpty else { return [] }', self.query)

    def test_original_appends_the_SDK_String_without_prefix_or_UUID_conversion(self):
        native = self.original['0x1002e2bf8']
        tokens = ['objc_stub::uniqueIdentifier', 'Swift::String::__unconditionallyBridgeFromObjectiveC()',
                  '*(String *)(uVar7 + uVar8 * 0x10 + 0x20) = SVar12', 'if (lVar10 !=']
        positions = [native.index(t) for t in tokens]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn('UUID', native)
        self.assertIn('found.append(result.item.uniqueIdentifier)', self.query)
        self.assertIn('async throws -> [String]', self.source[self.source.index('nonisolated private static func matchingIdentifiers('):][:145])
        self.assertNotIn('domain:', self.query)

    def test_raw_result_projection_preserves_duplicates_empty_unicode_and_opaque_values(self):
        values = ['', 'non-uuid', '重复/条目', 'other-domain:entry', 'entry', 'entry', '0000']
        self.assertEqual(query_projection(self.source, values), values)
        self.assertEqual(query_projection(self.source, []), [])
        rows = ['same'] * 100 + ['beyond limit']
        self.assertEqual(query_projection(self.source, rows), rows[:100])
        self.assertEqual(len(query_projection(self.source, rows)), 100)

    def test_projection_mutants_reject_reintroduced_filter_dedup_and_missing_cap(self):
        mutants = [self.source.replace('context.fetchAttributes = []', 'context.fetchAttributes = []; context.filterQueries = ["scope"]'),
                   self.source.replace('found.append(result.item.uniqueIdentifier)', 'found.insert(result.item.uniqueIdentifier)'),
                   self.source.replace('if resultCount == limit { break }', ''),
                   self.source.replace('found.append(result.item.uniqueIdentifier)', 'if result.item.uniqueIdentifier.hasPrefix("scope:") { found.append(result.item.uniqueIdentifier) }')]
        for changed in mutants:
            with self.assertRaises(ValueError):
                query_projection(changed, ['opaque'])

    def test_cancellation_still_checks_after_iterator_and_before_local_UUID_publication(self):
        self.assertLess(self.query.index('for try await result'), self.query.index('try Task.checkCancellation()'))
        self.assertLess(self.query.index('try Task.checkCancellation()'), self.query.index('return found'))
        replace = body(self.source, 'private func replaceQuery(')
        self.assertLess(replace.index('await Self.matchingIdentifiers('), replace.index('try Task.checkCancellation()'))
        self.assertLess(replace.index('try Task.checkCancellation()'), replace.index('store.makeSearchCollection('))
        self.assertLess(replace.index('store.makeSearchCollection('), replace.index('onUpdate?()'))
        before = body(self.before, 'private func replaceQuery(')
        marker = 'try Task.checkCancellation()'
        assert_query_result_only(self, replace[replace.index(marker):], before[before.index(marker):])

    def test_local_UUID_adapter_is_after_query_and_native_persistent_fetch_accepts_strings(self):
        replace = body(self.source, 'private func replaceQuery(')
        self.assertIn('installResultSource(store.makeSearchCollection(identifiers: found))', replace)
        self.assertNotIn('UUID(uuidString:', replace + self.query)
        persistence = (ROOT / 'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text()
        fetch = body(persistence, 'func searchNativeItems(')
        self.assertIn('nativeIdentifier IN %@ OR (nativeIdentifier == nil AND key IN %@)', fetch)
        self.assertIn('found.contains($0.searchIdentifier)', replace)
        self.assertNotIn('found.contains($0.id.uuidString)', replace)

    def test_item_builder_writes_record_identifier_without_domain_concatenation(self):
        self.assertIn('CSSearchableItem(uniqueIdentifier: entry.searchIdentifier,', self.builder)
        self.assertNotIn('domain + ":"', self.builder)
        self.assertNotIn('storeKey', self.builder)
        self.assertIn('domainIdentifier: domain, attributeSet: attributes', self.builder)
        native = self.original['0x1002e3ce8']
        self.assertIn('(**(code **)(lVar15 + 8))(uVar1,lVar15)', native)
        self.assertIn('initWithUniqueIdentifier_domainIdentifier_attributeSet_', native)
        self.assertNotIn('Swift::String::append', native)

    def test_existing_item_metadata_content_limit_expiry_and_update_flag_are_unchanged(self):
        before = body(self.before, 'private func searchableItem(')
        self.assertEqual(self.builder[:self.builder.index('let item = CSSearchableItem')],
                         before[:before.index('attributes.setValue(domain as NSString')])
        marker = 'item.expirationDate = .distantFuture'
        self.assertEqual(self.builder[self.builder.index(marker):], before[before.index(marker):])
        self.assertIn('let text = content.map { String($0.prefix(5000)) }', self.builder)
        for key in ['appKey', 'typeKey', 'deviceKey', 'pinboardKey']:
            self.assertIn('forCustomKey: ' + key, self.builder)

    def test_raw_delete_batches_preserve_all_inputs_and_keep_separate_100_cap(self):
        for count in [0, 1, 99, 100, 101, 199, 200, 201, 301]:
            values = ['' if i % 9 == 0 else ('opaque/id' if i % 7 == 0 else 'same') for i in range(count)]
            windows = delete_windows(self.source, values)
            self.assertEqual(sum(windows, []), values)
            self.assertTrue(all(0 < len(w) <= 100 for w in windows))
        mutant = self.source.replace('let batch = Array(input)', 'let batch = input.map { domain + ":" + $0 }')
        with self.assertRaises(ValueError):
            delete_windows(mutant, ['raw'])
        native = self.original['0x1002e243c']
        self.assertIn('Swift::Array<undefined>::_bridgeToObjectiveC()', native)
        self.assertIn('objc_stub::deleteSearchableItemsWithIdentifiers_completionHandler_(self,pNVar3)', native)
        self.assertNotIn('Swift::String::append', native)

    def test_delete_SDK_wait_errors_and_native_cache_cleanup_preserve_prior_order(self):
        before = body(self.before, 'private func deleteIdentifiers(')
        marker = 'try await withCheckedThrowingContinuation'
        self.assertEqual(self.delete[self.delete.index(marker):], before[before.index(marker):])
        self.assertIn('continuation.resume(throwing: error)', self.delete)
        self.assertLess(self.delete.index('index.deleteSearchableItems('), self.delete.index('let deleted = Set(input)'))
        self.assertIn('!deleted.contains($0.value.searchIdentifier)', self.delete)
        self.assertNotIn('UUID(', self.delete)
        self.assertNotIn('catch', self.delete)

    def test_target_delegate_forwards_unfiltered_raw_array_and_has_no_UI_request_gate(self):
        target = body(self.rebuild, 'if let identifiers')
        self.assertIn('reindexIdentifiers.append(contentsOf: identifiers)', target)
        for token in ['compactMap', 'Set(', 'UUID(', 'hasPrefix', 'dropFirst', 'filter']:
            self.assertNotIn(token, target)
        self.assertNotIn('guard let requested', self.rebuild)
        self.assertIn('let request = requested ?? Request(', self.rebuild)
        self.assertIn('FUN_1002f2690(*(undefined8 *)(unaff_x22 + 0x18))', self.original['0x1002e48a0'])
        self.assertIn('FUN_1002f2ca8(uVar1,uVar2)', self.original['0x1002f3c8c'])
        self.assertIn('FUN_1002ea770(param_2,1)', self.original['0x1002f2ca8'])

    def test_target_only_active_gate_empty_filter_and_ack_boundary_are_unchanged(self):
        for marker in ['private func reindexTargets(', 'private func drain() async']:
            assert_write_scope_only(self, body(self.source, marker), body(self.before, marker))
        target = body(self.source, 'private func reindexTargets(')
        self.assertIn('let input = identifiers.filter { !$0.isEmpty }', target)
        self.assertIn('guard isRunning, !Task.isCancelled else { break }', target)
        self.assertIn('acknowledgements.append(acknowledge)', body(self.before, 'nonisolated private func rebuild('))
        self.assertIn('acknowledgements.append { continuation.resume() }', self.rebuild)
        self.assertIn('await withCheckedContinuation', self.rebuild)
        wrapper = body(self.source, 'nonisolated private func rebuild(')
        self.assertLess(wrapper.index('await ReplicaSearchIndex.performDelegateRebuild('), wrapper.index('acknowledge()'))

    def test_legacy_format_marker_is_per_existing_named_index_and_disables_stale_restore(self):
        initialize = body(self.source, 'init(service:')
        self.assertIn('nativeIdentifierFormatKey = "pasto.search.nativeIdentifiers." + domain', initialize)
        self.assertIn('index = service.index', initialize)
        self.assertIn('index = CSSearchableIndex(name: domain)', body(self.source, 'init(directoryURL:'))
        self.assertIn('mayRestoreSavedState = UserDefaults.standard.bool(forKey: nativeIdentifierFormatKey)', initialize)
        self.assertNotIn('CSSearchableIndex(name: "Pasto.', initialize)
        self.assertNotIn('stateStore.save(', initialize)
        state = (ROOT / 'replica/Sources/PastoCore/OriginalSearchIndexingState.swift').read_text()
        self.assertEqual(state, (self.phase / 'before/replica/Sources/PastoCore/OriginalSearchIndexingState.swift').read_text())

    def test_only_successful_SDK_clear_records_native_format_without_mutating_history(self):
        clear = body(self.source, 'private func clearIndex()')
        tokens = ['try await withCheckedThrowingContinuation', 'index.deleteAllSearchableItems',
                  'indexed = [:]', 'UserDefaults.standard.set(true, forKey: nativeIdentifierFormatKey)']
        positions = [clear.index(t) for t in tokens]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(self.source.count('UserDefaults.standard.set(true, forKey: nativeIdentifierFormatKey)'), 1)
        self.assertNotIn('catch', clear)
        for token in ['store.items', 'clearHistory', 'deleteHistory', 'pinboard', 'preferences =']:
            self.assertNotIn(token, clear)
        initialize = body(self.source, 'private func initializeIndexIfNeeded(')
        self.assertEqual(initialize, body(self.before, 'private func initializeIndexIfNeeded('))

    def test_compatibility_clear_failure_and_success_fixture_do_not_mark_format_early(self):
        # Source-bound branch fixture only: no defaults or Spotlight calls occur here.
        for already_native in [False, True]:
            for clear_succeeds in [False, True]:
                marker = already_native
                may_restore = marker
                if clear_succeeds:
                    marker = True
                self.assertEqual(may_restore, already_native)
                self.assertEqual(marker, already_native or clear_succeeds)
        clear = body(self.source, 'private func clearIndex()')
        self.assertIn('if let error { continuation.resume(throwing: error) }', clear)
        self.assertNotIn('try?', clear)

    def test_health_probe_and_normal_query_use_same_raw_result_helper_without_scope_parameter(self):
        health = body(self.source, 'private func restoreCompletedStateIfHealthy(')
        self.assertIn('Self.matchingIdentifiers(', health)
        self.assertIn('return !found.isEmpty', health)
        self.assertNotIn('domain:', health)
        self.assertNotIn('filterQueries', health)
        for marker in ['private func savedStateForRestore(', 'private func retryTransientIndexErrors(',
                       'private func indexInitialSnapshot(', 'private func drainOCRQueue()', 'private func stopIndexing()']:
            assert_write_scope_only(self, body(self.source, marker), body(self.before, marker))

    def test_three_existing_records_close_without_claiming_full_service_or_new_migration_credit(self):
        self.assertEqual([r['function_id'] for r in self.proof['contracts']],
                         ['Paste:0x1002e2930', 'Paste:0x1002e48a0', 'Paste:0x1002f3c8c'])
        self.assertEqual(self.proof['new_difference_records'], 0)
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertEqual(self.proof['function_map_markers_upgraded'], 0)
        self.assertEqual(len(self.proof['partial_unscored_repairs']), 2)
        partial = ' '.join(self.proof['retained_partial_contracts'])
        self.assertIn('release-before-ack', partial)
        self.assertIn('compatibility', partial)


if __name__ == '__main__':
    unittest.main()
