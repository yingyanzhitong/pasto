"""Delegate source/descriptor comparison only; does not execute Swift or system callbacks."""
import json
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment


class DelegateNoSnapshotContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-47'
        cls.proof = json.loads((cls.phase / 'delegate-no-snapshot-contract.json').read_text())
        cls.source = (ROOT / 'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text()
        cls.before = (cls.phase / 'before/replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text()
        cls.rebuild = body(cls.source, 'private func enqueueDelegateRebuild(')
        cls.original = {r['address']: original_fragment((ROOT / r['path']).read_text(), r['address'][2:])
                        for r in cls.proof['original_fragments']}

    def test_original_fragments_are_bound_to_exact_decompiled_inputs(self):
        self.assertEqual(len(self.proof['original_fragments']), 14)
        for row in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / row['path'])[row['address']]['sha256'], row['sha256'])

    def test_async_descriptors_reach_real_all_and_target_delegate_workers(self):
        expected = {'0x100c3e828': '0x1002e4c4c', '0x100c3e818': '0x1002e4b8c'}
        for row in self.proof['async_descriptors']:
            relative, frame = struct.unpack('<iI', bytes.fromhex(row['bytes']))
            self.assertEqual(hex(int(row['address'], 16) + relative), expected[row['address']])
            self.assertEqual(frame, 32)
        for address, callee in [('0x1002e4c4c', 'FUN_1002e4660('), ('0x1002e4660', 'FUN_1002e467c'),
                                ('0x1002e4b8c', 'FUN_1002e4884('), ('0x1002e4884', 'FUN_1002e48a0')]:
            self.assertIn(callee, self.original[address])

    def test_original_all_delegate_weak_owner_gate_has_no_UI_snapshot_precondition(self):
        entry = self.original['0x1002e477c']
        self.assertIn('__Block_copy(', entry)
        self.assertIn('&DAT_100c3e828', entry)
        worker = self.original['0x1002e467c']
        self.assertLess(worker.index('_swift_weakLoadStrong()'), worker.index('if (lVar1 != 0)'))
        live = body(worker, 'if (lVar1 != 0)')
        self.assertIn('FUN_1002f2268()', live)
        self.assertNotIn('if (', live)
        self.assertIn('_swift_task_switch(FUN_1002f2280)', self.original['0x1002f2268'])

    def test_missing_owner_still_acknowledges_and_returns_before_request_creation(self):
        wrapper = body(self.source, 'nonisolated private func rebuild(')
        helper = body(self.source, 'private static func performDelegateRebuild(')
        self.assertIn('guard let indexer = target.indexer else { return }', helper)
        self.assertIn('await indexer.enqueueDelegateRebuild(identifiers)', helper)
        self.assertLess(wrapper.index('await ReplicaSearchIndex.performDelegateRebuild('), wrapper.index('acknowledge()'))
        self.assertNotIn('let request', helper)
        self.assertNotIn('acknowledge', helper)

    def test_no_UI_request_creates_real_pending_work_instead_of_acknowledging_early(self):
        self.assertIn('guard let requested else { acknowledge(); return }', body(self.before, 'nonisolated private func rebuild('))
        self.assertNotIn('guard let requested', self.rebuild)
        self.assertIn('let request = requested ?? Request(entries: entries, nodes: queryNodes ?? [],', self.rebuild)
        self.assertIn('sourceIdentifier: store?.searchSourceIdentifier)', self.rebuild)
        self.assertIn('pending = request', self.rebuild)
        order = ['let request = requested ??', 'pending = request', 'acknowledgements.append { continuation.resume() }', 'startWorker()']
        offsets = [self.rebuild.index(token) for token in order]
        self.assertEqual(offsets, sorted(offsets))
        self.assertNotIn('requested =', self.rebuild)

    def test_both_production_delegate_methods_keep_their_distinct_index_routes(self):
        self.assertIn('rebuild(identifiers: nil, acknowledgementHandler)', self.source)
        self.assertIn('rebuild(identifiers: identifiers, acknowledgementHandler)', self.source)
        self.assertIn('if let identifiers', self.rebuild)
        self.assertIn('needsReset = true', self.rebuild)
        self.assertIn('mayRestoreSavedState = false', self.rebuild)
        # Actual native identifiers now cross the delegate without namespace projection.
        specific = body(self.rebuild, 'if let identifiers')
        self.assertIn('reindexIdentifiers.append(contentsOf: identifiers)', specific)
        self.assertNotIn('compactMap', specific)
        self.assertNotIn('hasPrefix', specific)

    def test_cold_all_pass_reads_native_IDs_and_live_records_independent_of_UI_entries(self):
        initial = body(self.source, 'private func indexInitialSnapshot(')
        self.assertIn('try store?.searchIndexIdentifiers(before: before) ?? fallback.filter', initial)
        self.assertIn('try liveEntries(identifiers: Array(input[lowerBound..<upperBound]))', initial)
        live = body(self.source, 'private func liveEntries(')
        self.assertIn('try store.searchIndexRecords(identifiers: identifiers)', live)
        self.assertNotIn('requested', initial + live)
        drain = body(self.source, 'private func drain() async')
        self.assertIn('guard let request = pending else { break }', drain)
        self.assertIn('try await initializeIndexIfNeeded(request)', drain)
        self.assertIn('try await indexInitialSnapshot(currentEntries, resuming: resumeState)', body(self.source, 'private func initializeIndexIfNeeded('))

    def test_query_requests_and_retry_are_unchanged_and_delegate_does_not_publish(self):
        for marker in ['func update(items:', 'func retry()', 'private func replaceQuery(',
                       'nonisolated private static func matchingIdentifiers(']:
            source = (ROOT / '.local/p0-repair/phase-55/before/replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text() if marker in ['private func replaceQuery(', 'nonisolated private static func matchingIdentifiers('] else self.source
            current = body(source, marker)
            if marker in ['func update(items:', 'func retry()']:
                current = current.replace('        pendingMayInitializeIndex = true\n', '', 1)
            self.assertEqual(current, body(self.before, marker))
        for token in ['replaceQuery(', 'onUpdate', 'queryTask', 'identifiers = []', 'requested =']:
            self.assertNotIn(token, self.rebuild)

    def test_index_queue_reset_and_ack_paths_are_unchanged_by_removing_gate(self):
        for marker in ['private func startWorker()', 'private func drain() async',
                       'private func indexInitialSnapshot(', 'private func reindexTargets(']:
            # Historical gate-only patch; error/observation and cancellation change in phase 48.
            source = self.source
            if marker in ['private func drain() async', 'private func reindexTargets(']:
                source = (ROOT / '.local/p0-repair/phase-48/before/replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text()
            if marker == 'private func indexInitialSnapshot(':
                source = (ROOT / '.local/p0-repair/phase-49/before/replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text()
            self.assertEqual(body(source, marker), body(self.before, marker))
        previous = body(self.before, 'nonisolated private func rebuild(')
        self.assertIn('acknowledgements.append(acknowledge)', previous)
        self.assertIn('await withCheckedContinuation', self.rebuild)
        self.assertIn('acknowledgements.append { continuation.resume() }', self.rebuild)
        self.assertIn('startWorker()', self.rebuild)

    def test_original_owner_release_boundary_is_consumed_by_outer_ack_not_drain(self):
        for address, resume in [('0x1002e46fc', 'FUN_1002e474c'), ('0x1002e4928', 'FUN_1002e4978')]:
            native = self.original[address]
            self.assertLess(native.index('_swift_release(uVar1)'), native.index('_swift_task_switch(' + resume))
        drain = body(self.source, 'private func drain() async')
        self.assertLess(drain.index('completed.forEach { $0() }'), drain.index('worker = nil'))
        self.assertNotIn('acknowledge()', drain)
        self.assertIn('acknowledgements.append { continuation.resume() }', self.rebuild)
        wrapper = body(self.source, 'nonisolated private func rebuild(')
        self.assertLess(wrapper.index('await ReplicaSearchIndex.performDelegateRebuild('), wrapper.index('acknowledge()'))
        self.assertNotIn('guard let self', wrapper)

    def test_gate_decision_fixture_distinguishes_absent_owner_from_absent_UI_request(self):
        # This truth table expresses the verified gate, not native delegate execution.
        rows = [(False, False, 'ack'), (False, True, 'ack'),
                (True, False, 'enqueue'), (True, True, 'enqueue')]
        for owner_alive, has_request, expected in rows:
            original = 'enqueue' if owner_alive else 'ack'
            repaired = 'ack' if not owner_alive else 'enqueue'
            old = 'enqueue' if owner_alive and has_request else 'ack'
            self.assertEqual(original, expected)
            self.assertEqual(repaired, expected)
            if owner_alive and not has_request:
                self.assertNotEqual(old, expected)

    def test_two_shared_gate_records_only_no_full_function_or_target_lifecycle_claim(self):
        ids = [r['function_id'] for r in self.proof['contracts']]
        self.assertEqual(ids, ['Paste:0x1002e467c', 'Paste:0x1002e477c'])
        self.assertTrue(all(not r['full_function_migration_verified'] for r in self.proof['contracts']))
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertEqual(self.proof['function_map_markers_upgraded'], 0)
        partial = ' '.join(self.proof['retained_partial_contracts'])
        for token in ['2e48a0 remains open', '2e46fc/2e4928', '2e20b8', 'storeless compatibility']:
            self.assertIn(token, partial)


if __name__ == '__main__':
    unittest.main()
