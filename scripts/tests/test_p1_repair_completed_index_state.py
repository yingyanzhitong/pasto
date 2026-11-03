"""Source/Mach-O/JSON fixtures only; never runs Swift, UserDefaults or native indexes."""
import hashlib
import json
import re
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from snapshot_read_scope_contract import body
from test_p0_repair_identity import method_body
from test_p0_repair_checksum_routing import original_fragment


class CompletedIndexStateContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-45'
        cls.proof = json.loads((cls.phase / 'completed-state-contract.json').read_text())
        cls.state = (ROOT / 'replica/Sources/PastoCore/OriginalSearchIndexingState.swift').read_text()
        cls.persistence = (ROOT / 'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text()
        cls.store = (ROOT / 'replica/Sources/PastoCore/ClipboardStore.swift').read_text()
        cls.index = (ROOT / 'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text()
        cls.restore = body(cls.index, 'private func restoreCompletedStateIfHealthy(')
        cls.initial = body(cls.index, 'private func indexInitialSnapshot(')
        cls.initialization = body(cls.index, 'private func initializeIndexIfNeeded(')
        cls.original = {r['address']: original_fragment((ROOT / r['path']).read_text(), r['address'][2:])
                        for r in cls.proof['original_fragments']}

    def test_original_fragments_and_prior_binary_state_schema_are_bound(self):
        for row in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / row['path'])[row['address']]['sha256'], row['sha256'])
        meta = self.proof['prior_state_metadata']
        self.assertEqual(hashlib.sha256((ROOT / meta['path']).read_bytes()).hexdigest(), meta['sha256'])

    def test_state_has_exact_original_five_codable_fields_with_separate_identity(self):
        record = body(self.state, 'public struct OriginalSearchIndexingState:')
        fields = re.findall(r'public var (\w+): ([^\n{]+)\n', record)
        self.assertEqual(fields, [('schemaVersion', 'Int'), ('totalItems', 'Int'), ('indexedItems', 'Int'),
                                  ('oldestTimestamp', 'Date?'), ('invalidItems', 'Int')])
        self.assertIn('Codable, Equatable', self.state)
        self.assertNotIn('indexedStoreID', record)
        self.assertEqual([f[0] for f in fields], self.proof['prior_state_metadata']['field_order'])

    def test_schema_version_uses_original_runtime_26_4_boundary(self):
        version = body(self.state, 'public static var currentSchemaVersion:')
        self.assertIn('majorVersion: 26, minorVersion: 4, patchVersion: 0', version)
        self.assertIn('? 6 : 5', version)
        original = self.original['0x1002e1234']
        self.assertIn('_stdlib_isOSVersionAtLeast(0x1a,4,0)', original)
        self.assertIn('DAT_101057930 = 5', original)
        self.assertIn('DAT_101057930 = 6', original)

    def test_storage_uses_original_json_state_key_and_unencoded_separate_string_key(self):
        self.assertIn('defaults.data(forKey: "indexingState")', self.state)
        self.assertIn('JSONDecoder().decode(OriginalSearchIndexingState.self, from: data)', self.state)
        self.assertIn('defaults.set(try JSONEncoder().encode(state), forKey: "indexingState")', self.state)
        identity = body(self.state, 'public var indexedStoreID:')
        self.assertIn('defaults.string(forKey: "indexedStoreID")', identity)
        self.assertIn('defaults.set(newValue, forKey: "indexedStoreID")', identity)
        self.assertNotIn('JSONEncoder', identity)
        self.assertNotIn('domain', self.state)

    def test_completed_restore_requires_schema_completion_and_positive_total(self):
        gate = body(self.index, 'private func savedStateForRestore(')
        for token in ['stateStore.savedState', 'state.schemaVersion == OriginalSearchIndexingState.currentSchemaVersion']:
            self.assertIn(token, gate)
        self.assertIn('state.indexedItems >= state.totalItems, state.totalItems > 0 else { return false }', self.restore)
        self.assertIn('if let previous = stateStore.indexedStoreID, let current = sourceIdentifier, previous != current', gate)
        self.assertNotIn('invalidItems == 0', self.restore)

    def test_health_query_literal_is_original_and_probe_error_reuses_state(self):
        predicate = self.proof['health_predicate']
        self.assertEqual(bytes.fromhex(predicate['bytes']).decode('ascii'), predicate['value'])
        self.assertIn('predicate: "' + predicate['value'] + '"', self.restore)
        self.assertIn('return !found.isEmpty', self.restore)
        failure = body(self.restore, 'catch')
        self.assertIn('logger.error(', failure)
        self.assertIn('return true', failure)
        original = self.original['0x1002f32d4']
        self.assertIn('bVar3 = lVar7 == 0', original)
        self.assertIn('bVar3 = false', original)

    def test_restore_branch_table_is_bound_to_source_guards_not_a_runtime_claim(self):
        # Original-bound normal-domain fixture, not execution of Swift or CoreSpotlight.
        def reuse(schema, indexed, total, previous, current, probe):
            valid = schema == 5 and indexed >= total and total > 0
            mismatch = previous is not None and current is not None and previous != current
            return valid and not mismatch and (probe == 'error' or bool(probe))
        rows = [(5, 4, 4, 'A', 'A', ['id'], True), (5, 5, 4, 'A', None, ['id'], True),
                (5, 4, 4, None, 'B', ['id'], True), (5, 4, 4, 'A', 'B', ['id'], False),
                (6, 4, 4, 'A', 'A', ['id'], False), (5, 3, 4, 'A', 'A', ['id'], False),
                (5, 0, 0, 'A', 'A', ['id'], False), (5, 4, 4, 'A', 'A', [], False),
                (5, 4, 4, 'A', 'A', 'error', True)]
        for *inputs, wanted in rows:
            self.assertEqual(reuse(*inputs), wanted)

    def test_real_cold_start_restores_before_delete_and_skips_snapshot_writes_on_health(self):
        self.assertIn('lastSourceIdentifier = stateStore.indexedStoreID', body(self.index, 'init(service:'))
        check = self.initialization.index('await restoreCompletedStateIfHealthy(')
        self.assertLess(check, self.initialization.index('try await clearIndex()'))
        self.assertIn('if restoredCompletedState { needsReset = false }', self.initialization)
        self.assertIn('let usesSnapshot = !restoredCompletedState', self.initialization)
        self.assertIn('if try await indexInitialSnapshot(currentEntries, resuming: resumeState)', self.initialization)
        self.assertIn('startHistoryObservation()', self.initialization)

    def test_explicit_reset_overrides_pending_health_probe_reuse(self):
        rebuild = body(self.index, 'private func enqueueDelegateRebuild(')
        full = method_body(rebuild, '} else {')
        self.assertIn('needsReset = true', full)
        self.assertIn('mayRestoreSavedState = false', full)
        self.assertIn('restoredCompletedState = healthy && mayRestoreSavedState', self.initialization)
        self.assertLess(self.initialization.index('let healthy = await'), self.initialization.index('restoredCompletedState = healthy'))

    def test_reset_clears_persisted_optional_state_before_actual_sdk_clear(self):
        reset = method_body(self.initialization, 'if needsReset {')
        self.assertLess(reset.index('try stateStore.save(nil)'), reset.index('try await clearIndex()'))
        clear = body(self.index, 'private func clearIndex()')
        self.assertLess(clear.index('index.deleteAllSearchableItems'), clear.index('indexed = [:]'))
        self.assertIn('try await initializeIndexIfNeeded(request)', body(self.index, 'private func drain() async'))

    def test_ids_query_is_dictionary_only_with_original_timestamp_order_and_strict_before(self):
        request = body(self.persistence, 'func searchIndexIdentifiers(')
        for token in ['NSFetchRequest<NSDictionary>(entityName: "Item")', 'request.resultType = .dictionaryResultType',
                      'request.propertiesToFetch = ["nativeIdentifier", "key"]',
                      'NSSortDescriptor(key: "timestamp", ascending: false)',
                      'if let timestamp { request.predicate = NSPredicate(format: "timestamp < %@", timestamp as NSDate) }']:
            self.assertIn(token, request)
        self.assertNotIn('fetchLimit', request)
        self.assertNotIn('decode(', request)
        self.assertNotIn('rawPasteboardItems', request)
        self.assertIn('(row["nativeIdentifier"] as? String) ?? (row["key"] as? String)', request)
        selectors = {r['selector'] for r in self.proof['native_selector_bindings']}
        self.assertEqual(selectors, {'setResultType:', 'setPropertiesToFetch:', 'setSortDescriptors:', 'initWithKey:ascending:'})

    def test_actual_full_pass_uses_store_id_query_before_independent_100_id_batches(self):
        facade = body(self.store, 'public func searchIndexIdentifiers(')
        self.assertIn('try persistence.searchIndexIdentifiers(before: timestamp)', facade)
        self.assertIn('try store?.searchIndexIdentifiers(before: before)', self.initial)
        self.assertIn('let input = allIDs.filter { !$0.isEmpty }', self.initial)
        self.assertIn('totalItems: total, indexedItems: indexedBefore, oldestTimestamp: nil, invalidItems: invalid', self.initial)
        self.assertIn('if indexedBefore < 1 { total -= invalid }', self.initial)
        self.assertIn('stride(from: 0, to: input.count, by: Self.indexingBatchSize)', self.initial)
        self.assertIn('try liveEntries(identifiers: Array(input[lowerBound..<upperBound]))', self.initial)
        self.assertNotIn('changedEntries.count', self.initial)

    def test_batch_state_is_saved_after_sdk_success_and_counts_live_rows_not_input_ids(self):
        loop = body(self.initial, 'for lowerBound in stride(')
        order = ['guard isRunning, !Task.isCancelled else { break }', 'try liveEntries(', 'searchableItem($0, isUpdate: false)',
                 'Self.writeSearchableItems(changed, index: resolveWriteIndex())', 'state.indexedItems += live.count',
                 'state.oldestTimestamp = live.compactMap(\.modified).min()', 'try stateStore.save(state)']
        offsets = [loop.index(t) for t in order]
        self.assertEqual(offsets, sorted(offsets))
        self.assertIn('continuation.resume(throwing: error)', body(self.index, 'private static func writeSearchableItems('))
        self.assertIn('catch is CancellationError', loop)
        self.assertIn('return false', method_body(loop, '} catch {'))
        self.assertNotIn('throw error', method_body(loop, '} catch {'))
        self.assertIn('if !live.isEmpty', loop)
        self.assertNotIn('state.indexedItems += upperBound', loop)

    def test_non_cancelled_finish_marks_complete_using_proven_first_three_state_fields(self):
        meta = self.proof['prior_state_metadata']
        self.assertEqual(meta['first_three_int_offsets'], [0, 8, 16])
        self.assertEqual(meta['field_order'][:3], ['schemaVersion', 'totalItems', 'indexedItems'])
        final = self.original['0x1002ea410']
        self.assertIn('if ((param_3 & 1) == 0)', final)
        self.assertIn('if (!bVar1)', final)
        self.assertIn('*(undefined8 *)(puVar8 + 0x10) = *(undefined8 *)(param_1 + 8)', final)
        end = self.initial[self.initial.index('// 0x1002ea410'):]
        self.assertLess(end.index('guard isRunning, !Task.isCancelled else { return true }'), end.index('state.indexedItems = state.totalItems'))
        self.assertLess(end.index('state.indexedItems = state.totalItems'), end.index('try stateStore.save(state)'))

    def test_per_batch_config_keypath_is_saved_state_not_metrics_dictionary(self):
        native = self.original['0x1002e96ac']
        self.assertIn('&DAT_100c3e870', native)
        self.assertIn('FUN_1002cb5a0(uVar19,uVar14,puVar12)', native)
        self.assertIn('FUN_1002f36d4()', self.original['0x1002eb87c'])
        self.assertIn('(lVar1 + 0x128)', self.original['0x1002f36d4'])
        self.assertIn('FUN_1002ca7e0(param_1)', self.original['0x1002f36d4'])
        self.assertIn('FUN_1002cb5a0(', self.original['0x1002f37c0'])

    def test_writer_captures_complete_sdk_array_including_empty_text_not_diagnostic_filter(self):
        rows = {r['label']: r for r in self.proof['sdk_array_capture']}
        load, = struct.unpack('<I', bytes.fromhex(rows['load_complete_sdk_array_x21']['bytes']))
        capture, = struct.unpack('<I', bytes.fromhex(rows['capture_complete_array_in_block']['bytes']))
        self.assertEqual(load, 0xf9400ff5)  # ldr x21,[sp,#0x18]
        self.assertEqual(capture & 31, 23)
        self.assertEqual((capture >> 10) & 31, 21)
        self.assertEqual((capture >> 5) & 31, 0)  # stp x23,x21,[x0,#0x10]
        self.assertTrue(bytes.fromhex(rows['terminal_continuation_epilogue']['bytes']).endswith(bytes.fromhex('00001fd6')))
        self.assertNotIn('textContent', self.initial)
        self.assertNotIn('filter {', self.initial[self.initial.index('let live ='):])

    def test_only_completed_health_record_is_closed_cursor_and_worker_lifecycle_stay_open(self):
        row, = self.proof['contracts']
        self.assertEqual(row['function_id'], 'Paste:0x1002f00dc')
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertFalse(row['full_function_migration_verified'])
        historical = (ROOT / '.local/p0-repair/phase-46/before/replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text()
        self.assertIn('before: nil', body(historical, 'private func indexInitialSnapshot('))
        self.assertIn('let before = saved?.oldestTimestamp', self.initial)
        self.assertEqual(self.proof['function_map_markers_upgraded'], 0)


if __name__ == '__main__':
    unittest.main()
