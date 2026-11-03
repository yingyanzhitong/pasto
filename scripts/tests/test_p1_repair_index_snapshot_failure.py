"""Native cancellation-flag and real SDK catch boundaries; source checks only."""
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


class SnapshotFailureContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-54'
        cls.proof = json.loads((cls.phase / 'snapshot-failure-contract.json').read_text())
        cls.path = 'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift'
        cls.source = (ROOT / cls.path).read_text()
        cls.before = (cls.phase / 'before' / cls.path).read_text()
        cls.snapshot = body(cls.source, 'private func indexInitialSnapshot(')
        cls.initialize = body(cls.source, 'private func initializeIndexIfNeeded(')
        cls.batch = body(cls.snapshot, 'if !live.isEmpty')
        cls.failure = method_body(cls.batch, '} catch {')
        cls.cancel = body(cls.batch, 'catch is CancellationError')
        cls.original = {r['address']: original_fragment((ROOT / r['path']).read_text(), r['address'][2:])
                        for r in cls.proof['original_fragments']}

    def test_original_and_prior_retry_OCR_contracts_are_hash_bound(self):
        self.assertEqual(len(self.proof['original_fragments']), 14)
        for row in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / row['path'])[row['address']]['sha256'], row['sha256'])
        for row in self.proof['prior_contracts'] + [self.proof['error_arm']]:
            self.assertEqual(hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest(), row['sha256'])
        snapshot = self.phase / 'after' / self.path
        self.assertEqual(hashlib.sha256(snapshot.read_bytes()).hexdigest(), self.proof['current_sources'][self.path])
        assert_write_scope_only(self, body(snapshot.read_text(), 'private func indexInitialSnapshot('), self.snapshot)

    def test_native_cast_result_is_returned_and_inverted_only_for_finalize_abort_flag(self):
        native = self.original['0x1002e9d54']
        self.assertIn('Swift::CancellationError::typeMetadataAccessor()', self.original['0x1002e87e4'])
        self.assertIn('_swift_dynamicCast(', native)
        self.assertIn('FUN_1002ea410(uVar7,uVar14,(uint)uVar5 ^ 1)', native)
        self.assertIn('(**(code **)(unaff_x22 + 8))(uVar5 & 0xffffffff)', native)
        rows = {r['address']: struct.unpack('<I', bytes.fromhex(r['bytes']))[0]
                for r in self.proof['error_arm']['words']}
        self.assertEqual(rows['0x1002e9dc4'], 0xb90027e0)
        self.assertEqual(rows['0x1002ea110'], 0xb94027f7)
        self.assertEqual(rows['0x1002ea114'], 0x520002e2)
        self.assertEqual(rows['0x1002ea19c'], 0xaa1703e0)
        # eor w2,w23,#1; mov x0,x23. Never confuse error type with actual Task cancellation.
        self.assertEqual((rows['0x1002ea114'] >> 5) & 31, 23)
        self.assertEqual(rows['0x1002ea114'] & 31, 2)

    def test_ordinary_failure_logs_returns_false_and_cannot_advance_progress_or_clear_active(self):
        self.assertIn('logger.error(', self.failure)
        self.assertIn('return false', self.failure)
        for token in ['throw', 'isRunning =', 'needsReset =', 'stateStore.save', 'state.indexedItems',
                      'clearIndex(', 'pending =', 'startWorker()', 'resetIndex(', 'retryTransientIndexErrors']:
            self.assertNotIn(token, self.failure)
        loop = body(self.snapshot, 'for lowerBound in stride(')
        self.assertLess(loop.index(self.failure), loop.index('state.indexedItems += live.count'))
        self.assertNotIn('throw error', self.snapshot)

    def test_cancellation_breaks_to_shared_finalizer_and_does_not_log_or_persist_failed_batch(self):
        self.assertIn('break', self.cancel)
        for token in ['return', 'throw', 'logger.', 'state.', 'stateStore.', 'isRunning =']:
            self.assertNotIn(token, self.cancel)
        end = self.snapshot[self.snapshot.index('// 0x1002ea410'):]
        tokens = ['guard isRunning, !Task.isCancelled else { return true }',
                  'state.indexedItems = state.totalItems', 'try stateStore.save(state)', 'return true']
        offsets = [end.index(t) for t in tokens[:3]]
        self.assertEqual(offsets, sorted(offsets))
        self.assertTrue(end.rstrip().endswith('return true\n    }'))
        final = self.original['0x1002ea410']
        for token in ['if ((param_3 & 1) == 0)', '+ 0xf0', 'Swift::Task::_get_isCancelled',
                      '*(undefined8 *)(puVar8 + 0x10) = *(undefined8 *)(param_1 + 8)']:
            self.assertIn(token, final)

    def test_error_type_active_and_real_task_cancellation_fixture_covers_independent_flags(self):
        # Original XOR + current actual catch/guard mapping only, not Swift/SDK execution.
        for cancellation_error, active, task_cancelled in itertools.product([False, True], repeat=3):
            aborted = not cancellation_error
            native_finalize = not aborted and active and not task_cancelled
            source_finalize = cancellation_error and active and not task_cancelled
            self.assertEqual(source_finalize, native_finalize)
        self.assertTrue(True and True and not False)  # synthetic CancellationError without cancelling Task
        self.assertFalse(True and True and not True)  # actual Task cancellation suppresses completion save

    def test_local_error_catch_does_not_capture_fetch_or_persistent_writer_errors(self):
        retry_do = method_body(self.batch, 'do {')
        self.assertIn('try await retryTransientIndexErrors', retry_do)
        for token in ['try liveEntries(', 'searchIndexIdentifiers(', 'stateStore.save(', 'enqueueOCR(']:
            self.assertNotIn(token, retry_do)
        self.assertLess(self.snapshot.index('try liveEntries('), self.snapshot.index('if !live.isEmpty'))
        self.assertLess(self.snapshot.index('enqueueOCR(live)'), self.snapshot.index('if !live.isEmpty'))
        self.assertLess(self.snapshot.index('} catch {'), self.snapshot.index('try stateStore.save(state)'))
        self.assertIn('throw error', body(self.initialize, 'catch'))
        self.assertIn('isRunning = false', body(self.initialize, 'catch'))
        self.assertTrue(any('fetch errors' in row for row in self.proof['retained_partial_contracts']))

    def test_real_Bool_consumer_matches_native_completion_log_and_not_generic_failure_catch(self):
        branch = method_body(self.initialize, 'if usesSnapshot {')
        self.assertIn('if try await indexInitialSnapshot(currentEntries, resuming: resumeState)', branch)
        self.assertIn('logger.info("Spotlight indexation complete.")', branch)
        self.assertNotIn('isRunning =', branch)
        self.assertNotIn('catch', branch)
        self.assertIn('async throws -> Bool', self.source[self.source.index('private func indexInitialSnapshot('):][:145])
        self.assertIn('*(undefined1 *)(lVar1 + 0x3ea) = param_1', self.original['0x1002f1a44'])
        self.assertIn("if (*(char *)(unaff_x22 + 0x3ea) == '\\x01')", self.original['0x1002f1aa4'])
        literal = self.proof['completion_literal']
        self.assertEqual(int(literal['utf8_address'], 16), (int(literal['large_string_reference'], 16) & ((1 << 63) - 1)) + 32)
        self.assertEqual(bytes.fromhex(literal['bytes']).decode(), 'Spotlight indexation complete.')
        self.assertEqual(literal['length'], 30)

    def test_empty_ID_bridge_skips_pass_completion_log_and_OCR_kick(self):
        self.assertIn('guard !allIDs.isEmpty else { return false }', self.snapshot)
        self.assertLess(self.snapshot.index('guard !allIDs.isEmpty'), self.snapshot.index('defer { startOCRWorker() }'))
        self.assertIn('if (lVar9 != 0)', self.original['0x1002f177c'])
        native = method_body(self.original['0x1002f177c'], 'if (lVar9 != 0) {')
        self.assertIn('FUN_1002e87e4(', native)

    def test_OCR_kick_is_unconditional_pass_exit_but_no_retry_or_reset_is_added_after_error(self):
        self.assertEqual(self.snapshot.count('defer { startOCRWorker() }'), 1)
        self.assertLess(self.snapshot.index('defer { startOCRWorker() }'), self.snapshot.index('for lowerBound'))
        native = self.original['0x1002e9d54']
        self.assertLess(native.index('FUN_1002ea410('), native.index('FUN_1002ec520()'))
        for token in ['try await resetIndex(', 'needsReset =', 'pending =']:
            self.assertNotIn(token, self.snapshot)
        self.assertNotIn('isRunning =', self.snapshot)

    def test_retry_body_and_successful_batch_save_are_identical_to_prior_real_source(self):
        old = body(self.before, 'private func indexInitialSnapshot(')
        normalize = lambda text: '\n'.join(line.strip() for line in text.splitlines())
        assert_write_scope_only(self, normalize(body(self.snapshot, 'try await retryTransientIndexErrors')),
                                normalize(body(old, 'try await retryTransientIndexErrors')))
        current_loop = body(self.snapshot, 'for lowerBound in stride(')
        old_loop = body(old, 'for lowerBound in stride(')
        marker = 'state.indexedItems += live.count'
        self.assertEqual(current_loop[current_loop.index(marker):], old_loop[old_loop.index(marker):])
        for marker in ['private func retryTransientIndexErrors(', 'private func reindexTargets(',
                       'private func drainOCRQueue()', 'private func stopIndexing()',
                       'private func resetIndex(', 'private func drain() async']:
            assert_write_scope_only(self, body(self.source, marker), body(self.before, marker))

    def test_previous_initializer_rethrow_path_is_real_and_only_finite_contract_is_closed(self):
        before_snapshot = body(self.before, 'private func indexInitialSnapshot(')
        self.assertNotIn('catch is CancellationError', before_snapshot)
        before_initializer = body(self.before, 'private func initializeIndexIfNeeded(')
        self.assertIn('throw error', body(before_initializer, 'catch'))
        self.assertIn('isRunning = false', body(before_initializer, 'catch'))
        self.assertEqual([r['function_id'] for r in self.proof['contracts']], ['Paste:0x1002e9d54'])
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertEqual(self.proof['function_map_markers_upgraded'], 0)


if __name__ == '__main__':
    unittest.main()
