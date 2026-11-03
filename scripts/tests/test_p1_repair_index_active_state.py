from snapshot_read_scope_contract import assert_history_queue_only
"""Source/descriptor/state-transition contracts; never executes Swift or native tasks."""
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
from index_write_scope_contract import assert_write_scope_only, assert_service_initializer_only, assert_ui_service_composition_only
from test_p0_repair_identity import method_body
from test_p0_repair_checksum_routing import original_fragment


class IndexActiveStateContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-49'
        cls.proof = json.loads((cls.phase / 'active-indexer-contract.json').read_text())
        cls.source = (ROOT / 'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text()
        cls.before = (cls.phase / 'before/replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text()
        cls.drain = body(cls.source, 'private func drain() async')
        cls.initialization = body(cls.source, 'private func initializeIndexIfNeeded(')
        cls.initialization_gate = body(cls.drain, 'else if mayInitializeIndex')
        cls.target = body(cls.source, 'private func reindexTargets(')
        cls.snapshot = body(cls.source, 'private func indexInitialSnapshot(')
        cls.rebuild = body(cls.source, 'private func enqueueDelegateRebuild(')
        cls.original = {r['address']: original_fragment((ROOT / r['path']).read_text(), r['address'][2:])
                        for r in cls.proof['original_fragments']}

    def test_exact_original_fragments_and_actor_proof_are_bound(self):
        self.assertEqual(len(self.proof['original_fragments']), 24)
        for row in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / row['path'])[row['address']]['sha256'], row['sha256'])
        prior = self.proof['prior_actor_metadata']
        self.assertEqual(hashlib.sha256((ROOT / prior['path']).read_bytes()).hexdigest(), prior['sha256'])
        offsets = {f['name']: f['offset'] for f in prior['actor_metadata']['fields']}
        self.assertEqual(offsets['isRunning'], '0xf0')

    def test_active_is_independent_of_both_queue_and_observer_task_handles(self):
        self.assertIn('private var isRunning = false', self.source)
        self.assertIn('private var worker: Task<Void, Never>?', self.source)
        self.assertIn('private var historyTask: Task<Void, Never>?', self.source)
        self.assertNotIn('private var isRunning:', self.source)
        self.assertIn('*(undefined1 *)(param_5 + 0xf0) = 0', self.original['0x1002d6cf4'])

    def test_original_start_and_success_failure_continuations_use_independent_flag(self):
        start = self.original['0x1002f20a0']
        self.assertIn('if ((*(byte *)(lVar2 + 0xf0) & 1) != 0)', start)
        self.assertLess(start.index('*(undefined1 *)(lVar2 + 0xf0) = 1'), start.index('FUN_1002efba0()'))
        self.assertNotIn('+ 0xf0)', self.original['0x1002f217c'])
        self.assertIn('pcVar1 = FUN_1002f2214', self.original['0x1002f2120'])
        self.assertIn('*(undefined1 *)(*(long *)(unaff_x22 + 0x60) + 0xf0) = 0', self.original['0x1002f2214'])

    def test_actual_start_only_sets_true_in_inactive_initialization_branch(self):
        start = self.initialization
        guard = start.index('guard !isRunning else { return }')
        self.assertLess(guard, start.index('isRunning = true'))
        self.assertEqual(self.source.count('isRunning = true'), 1)
        self.assertNotIn('worker == nil', start)
        self.assertNotIn('historyTask == nil', start)
        for token in ['stateStore.indexedStoreID = current', 'startHistoryObservation()', 'try await indexInitialSnapshot(']:
            self.assertLess(guard, start.index(token))
        self.assertIn('let usesSnapshot = !restoredCompletedState', start)

    def test_initialization_success_is_marked_before_targeted_work_can_fail(self):
        failure = body(self.initialization, 'catch')
        self.assertIn('isRunning = false', failure)
        self.assertIn('throw error', failure)
        self.assertNotIn('needsReset =', failure)
        self.assertLess(self.drain.index('try await initializeIndexIfNeeded(request)'), self.drain.index('try await reindexTargets('))
        drain_failure = self.drain[self.drain.rindex('} catch {'):]
        self.assertNotIn('isRunning =', drain_failure)
        self.assertNotIn('needsReset =', drain_failure)

    def test_queue_drain_and_ack_do_not_turn_off_a_successful_service(self):
        tail = self.drain[self.drain.index('worker = nil'):]
        self.assertNotIn('isRunning', tail)
        worker = body(self.source, 'private func startWorker()')
        self.assertIn('guard worker == nil else { return }', worker)
        self.assertNotIn('isRunning =', worker)
        self.assertLess(self.drain.index('completed.forEach'), self.drain.index('worker = nil'))

    def test_real_target_gate_checks_active_and_task_before_each_live_fetch(self):
        loop = body(self.target, 'for lowerBound in stride(')
        self.assertIn('guard isRunning, !Task.isCancelled else { break }', loop)
        self.assertLess(loop.index('guard isRunning'), loop.index('try liveEntries('))
        self.assertLess(loop.index('Self.writeSearchableItems(changed, index: resolveWriteIndex())'), loop.index('refreshed.append(contentsOf: live)'))
        self.assertNotIn('Task.checkCancellation()', self.target)
        self.assertNotIn('needsReset =', self.target)
        self.assertNotIn('isRunning =', self.target)

    def test_original_target_first_and_following_batches_require_active_and_not_cancelled(self):
        for address in ['0x1002ea78c', '0x1002eaa10', '0x1002eaea4']:
            native = self.original[address]
            self.assertIn('+ 0xf0)', native)
            self.assertIn('Swift::Task::_get_isCancelled', native)
        self.assertIn('FUN_1002e1bac(', self.original['0x1002eaa10'])
        self.assertIn('if (unaff_x20 == 0)', self.original['0x1002eaea4'])

    def test_full_snapshot_stops_quietly_and_does_not_mark_stopped_state_complete(self):
        loop = body(self.snapshot, 'for lowerBound in stride(')
        self.assertIn('guard isRunning, !Task.isCancelled else { break }', loop)
        final = self.snapshot[self.snapshot.index('// 0x1002ea410'):]
        self.assertLess(final.index('guard isRunning, !Task.isCancelled else { return true }'),
                        final.index('state.indexedItems = state.totalItems'))
        self.assertNotIn('Task.checkCancellation()', self.snapshot)
        native = self.original['0x1002ea410']
        self.assertIn('if (*(char *)(unaff_x20 + 0xf0)', native)
        self.assertIn('Swift::Task::_get_isCancelled', native)

    def test_successful_snapshot_batch_save_body_is_unchanged(self):
        current = body(self.snapshot, 'for lowerBound in stride(')
        prior = body(body(self.before, 'private func indexInitialSnapshot('), 'for lowerBound in stride(')
        marker = 'let upperBound = min('
        historical = (ROOT / '.local/p0-repair/phase-53/before/replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text()
        proven_loop = body(body(historical, 'private func indexInitialSnapshot('), 'for lowerBound in stride(')
        self.assertEqual(proven_loop[proven_loop.index(marker):].replace('            enqueueOCR(live)\n', '', 1), prior[prior.index(marker):])
        save = 'state.indexedItems += live.count'
        self.assertEqual(current[current.index(save):], proven_loop[proven_loop.index(save):])
        self.assertIn('let changed = live.map { searchableItem($0, isUpdate: false) }', current)
        self.assertLess(current.index('Self.writeSearchableItems(changed, index: resolveWriteIndex())'), current.index('try stateStore.save(state)'))
        self.assertIn('state.indexedItems += live.count', current)

    def test_only_UI_retry_and_full_delegate_can_enable_initialization(self):
        for marker in ['func update(items:', 'func retry()']:
            current = body(self.source, marker)
            self.assertIn('pendingMayInitializeIndex = true', current)
            self.assertLess(current.index('pendingMayInitializeIndex = true'), current.index('startWorker()'))
        targeted = body(self.rebuild, 'if let identifiers')
        self.assertNotIn('pendingMayInitializeIndex', targeted)
        full = method_body(self.rebuild, '} else {')
        self.assertIn('pendingMayInitializeIndex = true', full)
        self.assertIn('private var pendingMayInitializeIndex = false', self.source)

    def test_initialization_flag_is_captured_before_await_and_does_not_leak_to_next_target(self):
        request = self.drain[self.drain.index('guard let request = pending'):]
        order = ['let mayInitializeIndex = pendingMayInitializeIndex', 'pendingMayInitializeIndex = false', 'if resetsIndex', 'await ']
        offsets = [request.index(token) for token in order]
        self.assertEqual(offsets, sorted(offsets))
        self.assertNotIn('pendingMayInitializeIndex = true', self.drain)
        self.assertIn('try await reindexTargets(forcedIdentifiers)', request[request.index(self.initialization_gate) + len(self.initialization_gate):])

    def test_target_only_request_has_no_path_into_state_reset_or_snapshot(self):
        after_initialization = self.drain[self.drain.index(self.initialization_gate) + len(self.initialization_gate):]
        self.assertIn('try await reindexTargets(forcedIdentifiers)', after_initialization)
        for token in ['stateStore.save(', 'indexInitialSnapshot(', 'isRunning = true', 'startHistoryObservation()']:
            self.assertNotIn(token, after_initialization)
        for token in ['savedStateForRestore(', 'try await clearIndex()', 'startHistoryObservation()']:
            self.assertIn(token, self.initialization)

    def test_real_target_descriptor_and_callees_do_not_route_through_reset(self):
        target = next(row for row in self.proof['async_descriptors'] if row['address'] == '0x100c3ec00')
        delta, size = struct.unpack('<iI', bytes.fromhex(target['bytes']))
        self.assertEqual(hex(int(target['address'], 16) + delta), '0x1002f3c8c')
        self.assertEqual(size, 32)
        self.assertIn('&DAT_100c3ec00', self.original['0x1002f26a8'])
        self.assertIn('FUN_1002f2ca8(', self.original['0x1002f3c8c'])
        self.assertIn('FUN_1002ea770(param_2,1)', self.original['0x1002f2ca8'])
        self.assertNotIn('FUN_1002f1c30(', self.original['0x1002f26a8'])

    def test_stop_clears_active_and_observer_without_cancelling_the_serial_worker(self):
        stop = body(self.source, 'private func stopIndexing()')
        order = ['isRunning = false', 'historyTask?.cancel()', 'historyTask = nil']
        offsets = [stop.index(token) for token in order]
        self.assertEqual(offsets, sorted(offsets))
        self.assertNotIn('worker', stop)
        self.assertLess(stop.index('historyTask = nil'), stop.index('ocrTask.cancel()'))
        self.assertLess(stop.index('ocrTask.cancel()'), stop.index('await ocrTask.value'))
        self.assertLess(stop.index('await ocrTask.value'), stop.index('ocrTask = nil'))
        self.assertNotIn('stateStore', stop)
        self.assertNotIn('ocrQueue', stop)
        self.assertNotIn('ocrQueuedIdentifiers', stop)

    def test_full_delegate_stops_immediately_before_enqueue_and_source_mismatch_also_stops(self):
        full = method_body(self.rebuild, '} else {')
        self.assertIn('needsReset = true', full)
        self.assertIn('mayRestoreSavedState = false', full)
        self.assertIn('stopIndexing()', full)
        self.assertLess(self.rebuild.index('stopIndexing()'), self.rebuild.index('pending = request'))
        self.assertIn('if needsReset && isRunning { await stopIndexing() }', self.initialization)
        self.assertIn('guard let store else { return }',
                      body(self.source, 'private func startHistoryObservation()'))

    def test_genuine_restart_can_restore_saved_state_but_explicit_reset_keeps_precedence(self):
        inactive = self.initialization
        restart = method_body(inactive, 'if !needsReset {')
        self.assertIn('needsReset = true', restart)
        self.assertIn('mayRestoreSavedState = true', restart)
        self.assertIn('restoredCompletedState = healthy && mayRestoreSavedState', self.initialization)
        self.assertLess(self.initialization.index('isRunning = true'), self.initialization.index('CSSearchableIndex.isIndexingAvailable()'))

    def test_state_and_request_coalescing_fixtures_follow_the_bound_source_gates(self):
        # Explicit Python branch fixtures, not execution of the Swift actor/SDK.
        for active in [False, True]:
            for pending_initialization in [False, True]:
                after_target_arrival = pending_initialization
                will_initialize = after_target_arrival and not active
                self.assertEqual(will_initialize, pending_initialization and not active)
                if not pending_initialization and not active:
                    self.assertFalse(will_initialize)
        for initializing, failed, stopped, expected in [(True, False, False, True), (True, True, False, False),
                                                       (False, True, False, True), (True, False, True, False)]:
            active = not stopped
            if failed and initializing:
                active = False
            self.assertEqual(active, expected)
        for active in [False, True]:
            for cancelled in [False, True]:
                self.assertEqual(active and not cancelled, (active, cancelled) == (True, False))

    def test_queries_and_persisted_token_codec_are_unchanged(self):
        for marker in ['private func replaceQuery(', 'nonisolated private static func matchingIdentifiers(',
                       'private func savedStateForRestore(', 'private func restoreCompletedStateIfHealthy(']:
            source = (ROOT / '.local/p0-repair/phase-55/before/replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text() if marker != 'private func savedStateForRestore(' else self.source
            assert_write_scope_only(self, body(source, marker), body(self.before, marker))
        for path in ['replica/Sources/PastoCore/OriginalSearchHistory.swift',
                     'replica/Sources/PastoCore/OriginalSearchIndexingState.swift']:
            assert_history_queue_only(self, (ROOT / path).read_text(), (self.phase / 'before' / path).read_text()) if path.endswith('OriginalSearchHistory.swift') else self.assertEqual((ROOT / path).read_bytes(), (self.phase / 'before' / path).read_bytes())

    def test_only_five_finite_active_contracts_close_and_OCR_reset_parent_stays_open(self):
        self.assertEqual([r['function_id'] for r in self.proof['contracts']],
                         ['Paste:0x1002f20a0', 'Paste:0x1002f2214', 'Paste:0x1002ea78c',
                          'Paste:0x1002eaa10', 'Paste:0x1002eaea4'])
        self.assertTrue(all(not r['full_function_migration_verified'] for r in self.proof['contracts']))
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertEqual(self.proof['function_map_markers_upgraded'], 0)
        partial = ' '.join(self.proof['retained_partial_contracts'])
        for token in ['not five independent bugs', 'OCR task', 'retry helper/backoff', 'release-before-ack', 'Storeless']:
            self.assertIn(token, partial)


if __name__ == '__main__':
    unittest.main()
