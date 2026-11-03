"""Native descriptor/batch success boundaries; no compiler, SDK, OCR or clock execution."""
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


class SnapshotBatchRetryContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-53'
        cls.proof = json.loads((cls.phase / 'snapshot-batch-retry-contract.json').read_text())
        cls.path = 'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift'
        cls.source = (ROOT / cls.path).read_text()
        cls.before = (cls.phase / 'before' / cls.path).read_text()
        cls.snapshot = body(cls.source, 'private func indexInitialSnapshot(')
        cls.retry = body(cls.snapshot, 'try await retryTransientIndexErrors')
        cls.original = {r['address']: original_fragment((ROOT / r['path']).read_text(), r['address'][2:])
                        for r in cls.proof['original_fragments']}

    def test_original_fragment_and_shared_retry_proof_hashes_are_bound(self):
        self.assertEqual(len(self.proof['original_fragments']), 15)
        for row in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / row['path'])[row['address']]['sha256'], row['sha256'])
        for row in self.proof['prior_contracts']:
            self.assertEqual(hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest(), row['sha256'])
        frozen = self.phase / 'after' / self.path
        self.assertEqual(hashlib.sha256(frozen.read_bytes()).hexdigest(), self.proof['current_sources'][self.path])
        historical_snapshot = body(frozen.read_text(), 'private func indexInitialSnapshot(')
        normalize = lambda text: '\n'.join(line.strip() for line in text.splitlines())
        assert_write_scope_only(self, normalize(self.retry), normalize(body(historical_snapshot, 'try await retryTransientIndexErrors')))
        self.assertLess(self.snapshot.index('enqueueOCR(live)'), self.snapshot.index('try await retryTransientIndexErrors'))

    def test_retry_descriptor_captures_batch_operation_not_clear_or_whole_reset(self):
        wanted = {'0x100c3e850': '0x1002eb704', '0x100c3e860': '0x1002eb754'}
        for row in self.proof['async_descriptors']:
            delta, frame = struct.unpack('<iI', bytes.fromhex(row['bytes']))
            self.assertEqual((hex(int(row['address'], 16) + delta), frame), (wanted[row['address']], 32))
        native = self.original['0x1002e8de0']
        tokens = ['FUN_1002ec26c(', '&DAT_100c3e850', 'FUN_1002e7914(']
        offsets = [native.index(t) for t in tokens]
        self.assertEqual(offsets, sorted(offsets))
        self.assertIn('&DAT_100c3e860', native[native.index('FUN_1002e7914('):])
        self.assertIn('FUN_1002ea1c0(uVar1,uVar2)', self.original['0x1002eb704'])
        self.assertIn('_swift_task_switch(FUN_1002ea1d8', self.original['0x1002ea1c0'])
        self.assertIn('FUN_1002e1bac(0,0,*(undefined8 *)(unaff_x22 + 0x18),0)', self.original['0x1002ea1d8'])

    def test_actual_retry_wraps_only_nonempty_batch_sdk_build_and_write(self):
        self.assertIn('let changed = live.map { searchableItem($0, isUpdate: false) }', self.retry)
        self.assertIn('Self.writeSearchableItems(changed, index: resolveWriteIndex())', self.retry)
        self.assertIn('continuation.resume(throwing: error)', body(self.source, 'private static func writeSearchableItems('))
        for token in ['liveEntries(', 'enqueueOCR(', 'stateStore.save(', 'state.indexedItems',
                      'indexInitialSnapshot(', 'clearIndex()', 'deleteAll', 'startOCRWorker()']:
            self.assertNotIn(token, self.retry)
        branch = body(self.snapshot, 'if !live.isEmpty')
        self.assertEqual(branch.count('try await retryTransientIndexErrors'), 1)
        self.assertEqual(self.snapshot.count('try await retryTransientIndexErrors'), 1)

    def test_single_fetch_and_enqueue_before_retries_and_state_commit_after_success(self):
        tokens = ['try liveEntries(', 'enqueueOCR(live)', 'try await retryTransientIndexErrors',
                  'state.indexedItems += live.count', 'state.oldestTimestamp =', 'try stateStore.save(state)']
        offsets = [self.snapshot.index(t) for t in tokens]
        self.assertEqual(offsets, sorted(offsets))
        self.assertEqual(self.snapshot.count('try liveEntries('), 1)
        self.assertEqual(self.snapshot.count('enqueueOCR(live)'), 1)
        self.assertNotIn('try?', self.retry)
        self.assertNotIn('catch', self.retry)
        self.assertNotIn('stateStore', self.retry)
        self.assertIn('pcVar1 = FUN_1002e96ac', self.original['0x1002e9628'])
        self.assertIn('pcVar1 = FUN_1002e9d54', self.original['0x1002e9628'])

    def test_success_counter_and_resume_tail_unchanged_and_failed_batch_never_advances(self):
        previous = body(self.before, 'private func indexInitialSnapshot(')
        marker = 'state.indexedItems += live.count'
        current_loop = body(self.snapshot, 'for lowerBound in stride(')
        previous_loop = body(previous, 'for lowerBound in stride(')
        self.assertEqual(current_loop[current_loop.index(marker):], previous_loop[previous_loop.index(marker):])
        # Source-bound failure/retry trace, not execution of Swift closures/SDK.
        for outcomes, expected_attempts, expected_commits in [(['ok'], 1, 1),
                (['transient', 'ok'], 2, 1), (['transient'] * 3, 3, 0), (['ordinary'], 1, 0)]:
            attempts = 0
            commits = 0
            for outcome in outcomes:
                attempts += 1
                if outcome == 'ok':
                    commits += 1
                    break
                if outcome != 'transient' or attempts == 3:
                    break
            self.assertEqual((attempts, commits), (expected_attempts, expected_commits))

    def test_existing_transient_policy_and_all_other_real_index_methods_are_unchanged(self):
        markers = ['private func retryTransientIndexErrors(', 'private static func isTransientIndexError(',
                   'private func reindexTargets(', 'private func drainOCRQueue()', 'private func enqueueOCR(',
                   'private func startOCRWorker()', 'private func stopIndexing()', 'private func clearIndex()',
                   'private func applyHistoryChanges(', 'private func initializeIndexIfNeeded(',
                   'private func resetIndex(', 'private func drain() async', 'private func replaceQuery(']
        historical = (ROOT / '.local/p0-repair/phase-54/before' / self.path).read_text()
        for marker in markers:
            source = historical if marker == 'private func initializeIndexIfNeeded(' else self.source
            if marker in ['private func clearIndex()', 'private func replaceQuery(']:
                source = (ROOT / '.local/p0-repair/phase-55/before/replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text()
            assert_write_scope_only(self, body(source, marker), body(self.before, marker))
        initialize = body(self.source, 'private func initializeIndexIfNeeded(')
        self.assertIn('if try await indexInitialSnapshot(currentEntries, resuming: resumeState)', method_body(initialize, 'if usesSnapshot {'))
        self.assertEqual(body(initialize, 'catch'), body(body(historical, 'private func initializeIndexIfNeeded('), 'catch'))
        self.assertNotIn('retryTransientIndexErrors', body(self.source, 'private func drainOCRQueue()'))
        self.assertNotIn('retryTransientIndexErrors', body(self.source, 'private func reindexTargets('))

    def test_normal_initialization_does_not_gain_whole_snapshot_outer_retry(self):
        initialize = body(self.source, 'private func initializeIndexIfNeeded(')
        self.assertNotIn('retryTransientIndexErrors', initialize)
        self.assertIn('if try await indexInitialSnapshot(currentEntries, resuming: resumeState)', initialize)
        self.assertEqual(self.source.count('try await retryTransientIndexErrors'), 3)
        self.assertIn('defer { startOCRWorker() }', self.snapshot)

    def test_old_missing_boundary_is_real_and_only_finite_contract_is_closed(self):
        self.assertNotIn('retryTransientIndexErrors', body(self.before, 'private func indexInitialSnapshot('))
        self.assertEqual([r['function_id'] for r in self.proof['contracts']], ['Paste:0x1002e8de0'])
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertEqual(self.proof['function_map_markers_upgraded'], 0)
        self.assertTrue(any('e9d54' in p for p in self.proof['retained_partial_contracts']))


if __name__ == '__main__':
    unittest.main()
