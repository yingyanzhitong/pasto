from frc_result_scope_contract import assert_query_result_only
"""Original availability/observer gates with native descriptor evidence; no runtime execution."""
import hashlib
import itertools
import json
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from index_write_scope_contract import assert_write_scope_only, assert_service_initializer_only, assert_ui_service_composition_only
from test_p0_repair_identity import method_body
from test_p0_repair_checksum_routing import original_fragment


class ObserverReplacementContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-56'
        cls.proof = json.loads((cls.phase / 'observer-replacement-contract.json').read_text())
        cls.path = 'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift'
        cls.source = (ROOT / cls.path).read_text()
        cls.before = (cls.phase / 'before' / cls.path).read_text()
        cls.observer = body(cls.source, 'private func startHistoryObservation()')
        cls.initialize = body(cls.source, 'private func initializeIndexIfNeeded(')
        cls.original = {r['address']: original_fragment((ROOT / r['path']).read_text(), r['address'][2:])
                        for r in cls.proof['original_fragments']}

    def test_originals_descriptor_and_actor_offsets_are_bound_to_original_inputs(self):
        self.assertEqual(len(self.proof['original_fragments']), 11)
        for row in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / row['path'])[row['address']]['sha256'], row['sha256'])
        for row in self.proof['prior_contracts']:
            self.assertEqual(hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest(), row['sha256'])
        actor = json.loads((ROOT / self.proof['prior_contracts'][0]['path']).read_text())['actor_metadata']
        offsets = {r['name']: r['offset'] for r in actor['fields']}
        self.assertEqual(offsets['changeObserverTask'], '0x120')
        self.assertEqual(offsets['ocrTask'], '0xf8')
        descriptor = self.proof['async_descriptor']
        delta, frame = struct.unpack('<iI', bytes.fromhex(descriptor['bytes']))
        self.assertEqual((hex(int(descriptor['address'], 16) + delta), frame), ('0x1002f3b00', 32))
        self.assertIn('FUN_1002f340c(', self.original['0x1002f3b00'])

    def test_native_clear_and_healthy_initialization_paths_assign_new_observer_handle(self):
        native = self.original['0x1002f14cc']
        tokens = ['_swift_weakInit(', 'FUN_100076688(lVar9 + 0x98', '&DAT_100c3eb68',
                  'uVar10 = *(undefined8 *)(lVar9 + 0x120)', '*(undefined8 *)(lVar9 + 0x120) = uVar8',
                  '_swift_release(uVar10)']
        positions = [native.index(t) for t in tokens]
        self.assertEqual(positions, sorted(positions))
        self.assertIn('&DAT_100c3eb68', self.original['0x1002f00dc'])
        self.assertIn('*(undefined8 *)(lVar14 + 0x120) = uVar15', self.original['0x1002f00dc'])
        for token in ['+ 0xf0', 'Task::cancel', 'Task::_get_isCancelled']:
            self.assertNotIn(token, native)

    def test_actual_observer_has_no_added_active_or_existing_task_gate(self):
        self.assertIn('guard let store else { return }', self.observer)
        self.assertIn('historyTask = Task { @MainActor [weak self] in', self.observer)
        for token in ['guard isRunning', 'historyTask == nil', 'if historyTask', 'historyTask?.cancel()',
                      'await historyTask', 'stopIndexing()', 'queryTask']:
            self.assertNotIn(token, self.observer)
        self.assertEqual(self.observer.count('historyTask = Task'), 1)

    def test_actual_callback_and_serial_ack_logic_are_unchanged(self):
        previous = body(self.before, 'private func startHistoryObservation()')
        marker = 'historyTask = Task'
        self.assertEqual(self.observer[self.observer.index(marker):], previous[previous.index(marker):])
        for token in ['await store.observeSearchChanges { [weak self] changes in',
                      'guard let self else { throw CancellationError() }',
                      'pendingHistory.append(HistoryWork(changes: changes)', 'startWorker()']:
            self.assertIn(token, self.observer)
        self.assertIn('if let error { continuation.resume(throwing: error) }', self.observer)
        self.assertNotIn('try?', self.observer)
        self.assertEqual(body(self.source, 'private func drain() async'), body(self.before, 'private func drain() async'))

    def test_installation_gate_fixture_includes_old_handle_and_stop_during_await(self):
        # Source-bound creation policy only; does not execute tasks, observation or ARC.
        for has_store, active, old_handle in itertools.product([False, True], repeat=3):
            current_installs = has_store
            previous_installs = has_store and active and not old_handle
            self.assertEqual(current_installs, has_store)
            if has_store and (not active or old_handle):
                self.assertTrue(current_installs)
                self.assertFalse(previous_installs)
        self.assertNotIn('isRunning', self.observer)
        self.assertNotIn('historyTask == nil', self.observer)

    def test_unavailable_original_does_throw_and_parent_clears_active(self):
        native = self.original['0x1002efccc']
        self.assertIn('CSSearchableIndex::isIndexingAvailable', native)
        available = method_body(native, 'if ((IVar5 & 1) != 0) {')
        self.assertIn('FUN_1002f00dc', available)
        failure = native[native.index(available) + len(available):]
        self.assertIn('_swift_willThrow()', failure)
        self.assertNotIn('FUN_1002f00dc', failure)
        self.assertIn('+ 0xf0) = 0', self.original['0x1002f2214'])
        self.assertIn('if needsReset && !CSSearchableIndex.isIndexingAvailable() { throw IndexingError.unavailable }', self.initialize)
        self.assertIn('isRunning = false', body(self.initialize, 'catch'))
        self.assertIn('throw error', body(self.initialize, 'catch'))

    def test_reused_availability_gate_precedes_config_reset_observer_and_snapshot(self):
        gate = self.initialize.index('CSSearchableIndex.isIndexingAvailable()')
        for token in ['savedStateForRestore(', 'stateStore.indexedStoreID = current', 'try stateStore.save(nil)',
                      'try await clearIndex()', 'startHistoryObservation()', 'try await indexInitialSnapshot(']:
            self.assertLess(gate, self.initialize.index(token))
        self.assertLess(self.initialize.index('isRunning = true'), gate)
        # This existing initializer was not rewritten in the observer patch.
        self.assertEqual(self.initialize, body(self.before, 'private func initializeIndexIfNeeded('))

    def test_constructor_creation_is_not_a_false_availability_difference(self):
        native = self.original['0x1002e19c8']
        self.assertIn('objc_stub::initWithName_', native)
        self.assertNotIn('isIndexingAvailable', native)
        current = body(self.source, 'init(directoryURL:')
        self.assertIn('index = CSSearchableIndex(name: domain)', current)
        self.assertIn('index.indexDelegate = self', body(self.source, 'init(service:'))
        self.assertNotIn('isIndexingAvailable', current)
        self.assertIn('isIndexingAvailable', self.initialize)
        self.assertEqual(body(self.source, 'private func resetIndex('), body(self.before, 'private func resetIndex('))

    def test_stop_explicitly_cancels_current_observer_but_factory_does_not_cancel_previous(self):
        stop = body(self.source, 'private func stopIndexing()')
        tokens = ['isRunning = false', 'historyTask?.cancel()', 'historyTask = nil', 'ocrTask.cancel()', 'await ocrTask.value']
        positions = [stop.index(t) for t in tokens]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(stop, body(self.before, 'private func stopIndexing()'))
        self.assertNotIn('cancel()', self.observer)
        self.assertIn('Swift::Task::cancel', self.original['0x1002f2d18'])

    def test_clear_and_healthy_reuse_both_reach_observer_before_native_ids(self):
        self.assertLess(self.initialize.index('try await clearIndex()'), self.initialize.index('startHistoryObservation()'))
        self.assertLess(self.initialize.index('startHistoryObservation()'), self.initialize.index('if usesSnapshot {'))
        self.assertEqual(self.initialize.count('startHistoryObservation()'), 1)
        self.assertNotIn('usesSnapshot', self.observer)
        for marker in ['private func indexInitialSnapshot(', 'private func retryTransientIndexErrors(',
                       'private func replaceQuery(', 'private func drainOCRQueue()', 'private func clearIndex()']:
            (assert_query_result_only if marker == 'private func replaceQuery(' else assert_write_scope_only)(self, body(self.source, marker), body(self.before, marker))

    def test_only_one_new_finite_record_and_reused_old_gate_close_not_full_observer(self):
        self.assertEqual(self.proof['new_function_ids'], ['Paste:0x1002f14cc'])
        self.assertEqual(self.proof['reused_existing_function_ids'], ['Paste:0x1002efccc'])
        self.assertEqual(len(self.proof['contracts']), 2)
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertEqual(self.proof['function_map_markers_upgraded'], 0)
        self.assertTrue(any('old/current task lifecycle' in r for r in self.proof['retained_partial_contracts']))


if __name__ == '__main__':
    unittest.main()
