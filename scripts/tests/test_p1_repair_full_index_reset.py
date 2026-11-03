"""Real descriptor/source flow checks; no Swift, SDK, sleeps or Core Data execution."""
import hashlib
import json
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from test_p0_repair_identity import method_body
from test_p0_repair_checksum_routing import original_fragment


class FullIndexResetContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-51'
        cls.proof = json.loads((cls.phase / 'full-reset-contract.json').read_text())
        cls.source = (ROOT / 'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text()
        cls.before = (cls.phase / 'before/replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text()
        cls.reset = body(cls.source, 'private func resetIndex(')
        cls.initialize = body(cls.source, 'private func initializeIndexIfNeeded(')
        cls.clear = body(cls.source, 'private func clearIndex()')
        cls.drain = body(cls.source, 'private func drain() async')
        cls.rebuild = body(cls.source, 'private func enqueueDelegateRebuild(')
        cls.original = {r['address']: original_fragment((ROOT / r['path']).read_text(), r['address'][2:])
                        for r in cls.proof['original_fragments']}

    def test_original_fragments_and_prior_retry_contract_are_hash_bound(self):
        self.assertEqual(len(self.proof['original_fragments']), 26)
        for row in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / row['path'])[row['address']]['sha256'], row['sha256'])
        prior = self.proof['prior_retry_contract']
        self.assertEqual(hashlib.sha256((ROOT / prior['path']).read_bytes()).hexdigest(), prior['sha256'])

    def test_full_operation_descriptor_is_not_the_prestart_clear_descriptor(self):
        descriptors = {row['address']: row for row in self.proof['async_descriptors']}
        expected = {'0x100c3ec18': '0x1002f3cdc', '0x100c3ec20': '0x1002eb754',
                    '0x100c3ec28': '0x1002f3a60', '0x100c3eb50': '0x1002f3a60'}
        for address, target in expected.items():
            delta, frame = struct.unpack('<iI', bytes.fromhex(descriptors[address]['bytes']))
            self.assertEqual(hex(int(address, 16) + delta), target)
            self.assertEqual(frame, 32)
        self.assertNotEqual(expected['0x100c3ec18'], expected['0x100c3ec28'])

    def test_original_retry_wrapper_dispatches_the_nested_full_operation(self):
        full = self.original['0x1002f2280']
        self.assertIn('*(undefined **)(unaff_x22 + 0x20) = &DAT_100c3ec18', full)
        self.assertIn('&DAT_100c3ec20', full)
        self.assertIn('FUN_1002e7914(', full)
        self.assertIn('FUN_1002e7838(', self.original['0x1002eb754'])
        dispatch = self.original['0x1002e7838']
        self.assertIn('iVar1 = *param_4', dispatch)
        self.assertIn('(*(code *)((long)iVar1 + (long)param_4))()', dispatch)
        self.assertIn('FUN_1002f2648()', self.original['0x1002f3cdc'])
        self.assertIn('FUN_1002f1c30()', self.original['0x1002f2648'])

    def test_original_reset_preclear_success_then_start_and_nil_state_clear_are_distinct(self):
        reset = self.original['0x1002f1ca0']
        self.assertIn('FUN_1002cb5a0(', reset)
        self.assertIn('&DAT_100c3ec28', reset)
        self.assertIn('FUN_1002e267c(', self.original['0x1002f3a60'])
        self.assertIn('_swift_task_switch(FUN_1002f20a0', self.original['0x1002f201c'])
        self.assertIn('FUN_1002efba0()', self.original['0x1002f20a0'])
        self.assertIn('&DAT_100c3eb50', self.original['0x1002f00dc'])

    def test_actual_reset_clears_before_activating_normal_initialization(self):
        order = ['if isRunning { await stopIndexing() }', 'try stateStore.save(nil)',
                 'try await clearIndex()', 'needsReset = true', 'mayRestoreSavedState = false',
                 'try await initializeIndexIfNeeded(request)']
        offsets = [self.reset.index(token) for token in order]
        self.assertEqual(offsets, sorted(offsets))
        self.assertNotIn('isRunning = true', self.reset)
        self.assertNotIn('catch', self.reset)
        self.assertNotIn('Task {', self.reset)

    def test_actual_clear_waits_for_completion_and_updates_cache_only_after_success(self):
        order = ['try await withCheckedThrowingContinuation', 'index.deleteAllSearchableItems',
                 'continuation.resume(throwing: error)', 'indexed = [:]']
        offsets = [self.clear.index(token) for token in order]
        self.assertEqual(offsets, sorted(offsets))
        self.assertIn('else { continuation.resume() }', self.clear)
        for token in ['isRunning = true', 'stateStore.save', 'catch', 'withDomainIdentifiers:']:
            self.assertNotIn(token, self.clear)

    def test_clear_failure_prevents_start_in_original_and_current_paths(self):
        native = self.original['0x1002f201c']
        failure = method_body(native, 'if (unaff_x20 != 0) {')
        self.assertIn('return;', failure)
        self.assertNotIn('FUN_1002f20a0', failure)
        self.assertLess(self.reset.index('try await clearIndex()'), self.reset.index('try await initializeIndexIfNeeded('))
        self.assertNotIn('try?', self.reset)
        drain_failure = self.drain[self.drain.rindex('} catch {'):]
        self.assertIn('logger.error(', drain_failure)
        self.assertNotIn('needsReset =', drain_failure)
        self.assertNotIn('pending =', drain_failure)

    def test_full_retry_repeats_entire_reset_including_preclear_and_initialization(self):
        full = body(self.drain, 'if resetsIndex')
        wrapper = body(full, 'try await retryTransientIndexErrors')
        self.assertIn('try await resetIndex(request)', wrapper)
        self.assertNotIn('index.deleteAllSearchableItems', wrapper)
        self.assertIn('try await initializeIndexIfNeeded(request)', self.reset)
        self.assertEqual(self.drain.count('try await retryTransientIndexErrors'), 2)

    def test_ordinary_initialization_has_no_new_outer_retry(self):
        ordinary = body(self.drain, 'else if mayInitializeIndex')
        self.assertIn('try await initializeIndexIfNeeded(request)', ordinary)
        self.assertNotIn('retryTransientIndexErrors', ordinary)
        self.assertNotIn('resetIndex(', ordinary)
        self.assertLess(self.drain.index('if resetsIndex'), self.drain.index('else if mayInitializeIndex'))

    def test_reset_request_flag_is_captured_before_await_and_coalesced_full_request_is_preserved(self):
        self.assertIn('private var pendingResetsIndex = false', self.source)
        full = method_body(self.rebuild, '} else {')
        self.assertIn('pendingResetsIndex = true', full)
        target = body(self.rebuild, 'if let identifiers')
        self.assertNotIn('pendingResetsIndex', target)
        request = self.drain[self.drain.index('guard let request = pending'):]
        order = ['let resetsIndex = pendingResetsIndex', 'pendingResetsIndex = false', 'if resetsIndex', 'await ']
        offsets = [request.index(token) for token in order]
        self.assertEqual(offsets, sorted(offsets))
        self.assertNotIn('pendingResetsIndex = true', body(self.source, 'func update(items:'))

    def test_extracted_initializer_keeps_active_gate_success_and_failed_state(self):
        guard = self.initialize.index('guard !isRunning else { return }')
        self.assertLess(guard, self.initialize.index('isRunning = true'))
        self.assertLess(self.initialize.index('isRunning = true'), self.initialize.index('CSSearchableIndex.isIndexingAvailable()'))
        failure = body(self.initialize, 'catch')
        self.assertIn('isRunning = false', failure)
        self.assertIn('throw error', failure)
        self.assertNotIn('needsReset =', failure)
        self.assertNotIn('isRunning = false', body(self.initialize, 'do '))

    def test_nil_state_initialization_preserves_independent_second_clear(self):
        reset = method_body(self.initialize, 'if needsReset {')
        self.assertLess(reset.index('try stateStore.save(nil)'), reset.index('try await clearIndex()'))
        self.assertLess(self.initialize.index('try await clearIndex()'), self.initialize.index('startHistoryObservation()'))
        self.assertLess(self.initialize.index('startHistoryObservation()'), self.initialize.index('try await indexInitialSnapshot('))
        self.assertIn('restoredCompletedState = healthy && mayRestoreSavedState', self.initialize)

    def test_target_wrapper_and_ack_remain_after_successful_full_or_normal_initialization(self):
        target = body(self.drain, 'if !forcedIdentifiers.isEmpty')
        self.assertIn('try await reindexTargets(forcedIdentifiers)', body(target, 'try await retryTransientIndexErrors'))
        order = ['try await resetIndex(request)', 'try await initializeIndexIfNeeded(request)',
                 'try await reindexTargets(forcedIdentifiers)', 'completed.forEach']
        offsets = [self.drain.index(token) for token in order]
        self.assertEqual(offsets, sorted(offsets))
        self.assertEqual(self.drain.count('requestAcknowledgements.forEach { $0() }'), 1)

    def test_existing_retry_classifier_batch_content_and_query_methods_are_unchanged(self):
        historical = (ROOT / '.local/p0-repair/phase-52/before/replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text()
        for marker in ['private func retryTransientIndexErrors(', 'private static func isTransientIndexError(',
                       'private func reindexTargets(', 'private func indexInitialSnapshot(',
                       'private func searchableItem(', 'private func replaceQuery(',
                       'nonisolated private static func matchingIdentifiers(']:
            source = historical if marker in ['private func reindexTargets(', 'private func indexInitialSnapshot(', 'private func stopIndexing()'] else self.source
            if marker in ['private func searchableItem(', 'private func replaceQuery(', 'nonisolated private static func matchingIdentifiers(']:
                source = (ROOT / '.local/p0-repair/phase-55/before/replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text()
            self.assertEqual(body(source, marker), body(self.before, marker))

    def test_fault_trace_fixture_requires_repeating_the_preclear_and_does_not_start_after_failed_clear(self):
        # Original-bound trace fixture only, not SDK/Swift execution.
        def attempt(preclear_ok, initialize_ok):
            trace = ['inactive', 'state-nil', 'preclear']
            if not preclear_ok:
                return trace, 'error'
            trace += ['start', 'nil-state-clear', 'snapshot']
            return trace, 'success' if initialize_ok else 'error'
        self.assertEqual(attempt(False, True), (['inactive', 'state-nil', 'preclear'], 'error'))
        first, status = attempt(True, False)
        second, outcome = attempt(True, True)
        self.assertEqual((status, outcome), ('error', 'success'))
        self.assertEqual((first + second).count('preclear'), 2)
        self.assertEqual((first + second).count('nil-state-clear'), 2)

    def test_only_finite_deletion_error_record_closes_while_OCR_stop_parent_remains_open(self):
        self.assertEqual([r['function_id'] for r in self.proof['contracts']], ['Paste:0x1002f201c'])
        self.assertTrue(all(not r['full_function_migration_verified'] for r in self.proof['contracts']))
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertEqual(self.proof['function_map_markers_upgraded'], 0)
        partial = ' '.join(self.proof['retained_partial_contracts'])
        self.assertIn('OCR task cancellation/await', partial)
        self.assertIn('A child interpretation conflating these was rejected', partial)
        self.assertEqual(len(self.proof['partial_unscored_repairs']), 2)


if __name__ == '__main__':
    unittest.main()
