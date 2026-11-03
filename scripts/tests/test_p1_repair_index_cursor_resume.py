"""Original-bound source/byte contracts; no Swift, preferences or native index execution."""
import hashlib
import json
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


class IndexCursorResumeContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-46'
        cls.proof = json.loads((cls.phase / 'cursor-resume-contract.json').read_text())
        cls.source = (ROOT / 'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text()
        cls.initialization = body(cls.source, 'private func initializeIndexIfNeeded(')
        cls.initial = body(cls.source, 'private func indexInitialSnapshot(')
        cls.gate = body(cls.source, 'private func savedStateForRestore(')
        cls.original = {r['address']: original_fragment((ROOT / r['path']).read_text(), r['address'][2:])
                        for r in cls.proof['original_fragments']}

    def test_original_fragments_and_prior_state_proof_are_hash_bound(self):
        for row in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / row['path'])[row['address']]['sha256'], row['sha256'])
        prior = self.proof['prior_state_and_batch_proof']
        self.assertEqual(hashlib.sha256((ROOT / prior['path']).read_bytes()).hexdigest(), prior['sha256'])

    def test_original_clear_descriptor_reaches_actual_delete_all_worker(self):
        descriptor = self.proof['clear_operation_descriptor']
        relative, frame_size = struct.unpack('<iI', bytes.fromhex(descriptor['bytes']))
        self.assertEqual(hex(int(descriptor['address'], 16) + relative), descriptor['relative_target'])
        self.assertEqual(frame_size, 32)
        self.assertEqual(descriptor['relative_target'], '0x1002f3a60')
        self.assertIn('FUN_1002e267c(', self.original['0x1002f3a60'])
        reset = self.original['0x1002f00dc']
        self.assertLess(reset.rindex('FUN_1002cb5a0('), reset.index('FUN_1002ef5d0(&DAT_100c3eb50'))

    def test_original_resume_reads_optional_date_and_old_counters_before_full_work(self):
        restore = self.original['0x1002f00dc']
        self.assertIn('FUN_1002eb7dc(', restore)
        self.assertIn('lVar21 = *(long *)(lVar14 + 8)', restore)
        self.assertIn('lVar14 = *(long *)(lVar14 + 0x10)', restore)
        self.assertIn('if (lVar14 < lVar21)', restore)
        self.assertIn('plVar16[1] = (long)FUN_1002f177c', restore)
        work = self.original['0x1002f177c']
        self.assertIn('FUN_1002e87e4(param_1,uVar2,lVar9)', work)

    def test_state_gate_reads_once_and_rejects_schema_or_two_non_nil_identity_mismatch(self):
        self.assertEqual(self.gate.count('stateStore.savedState'), 1)
        self.assertIn('state.schemaVersion == OriginalSearchIndexingState.currentSchemaVersion else { return nil }', self.gate)
        self.assertIn('if let previous = stateStore.indexedStoreID, let current = sourceIdentifier, previous != current { return nil }', self.gate)
        self.assertIn('return state', self.gate)
        self.assertEqual(self.initialization.count('savedStateForRestore('), 1)
        self.assertNotIn('stateStore.savedState', self.initialization)

    def test_actual_partial_branch_keeps_index_without_health_probe(self):
        partial = method_body(self.initialization, 'if saved.indexedItems < saved.totalItems {')
        self.assertIn('resumeState = saved', partial)
        self.assertIn('needsReset = false', partial)
        for forbidden in ['await', 'save(', 'deleteAll', 'restoreCompletedStateIfHealthy']:
            self.assertNotIn(forbidden, partial)
        self.assertLess(self.initialization.index('resumeState = saved'), self.initialization.index('let usesSnapshot = !restoredCompletedState'))
        self.assertLess(self.initialization.index('let usesSnapshot = !restoredCompletedState'), self.initialization.index('if needsReset {'))

    def test_completed_branch_keeps_previous_health_and_explicit_reset_protection(self):
        completed = self.initialization[self.initialization.index('let healthy = await'):self.initialization.index('mayRestoreSavedState = false')]
        self.assertIn('restoreCompletedStateIfHealthy(saved)', completed)
        self.assertIn('restoredCompletedState = healthy && mayRestoreSavedState', completed)
        restore = body(self.source, 'private func restoreCompletedStateIfHealthy(')
        self.assertIn('state.indexedItems >= state.totalItems, state.totalItems > 0', restore)
        self.assertIn('return !found.isEmpty', restore)
        self.assertIn('return true', body(restore, 'catch'))
        rebuild = body(self.source, 'private func enqueueDelegateRebuild(')
        full = method_body(rebuild, '} else {')
        self.assertIn('needsReset = true', full)
        self.assertIn('mayRestoreSavedState = false', full)

    def test_resume_is_passed_to_real_snapshot_call_and_not_just_saved_in_a_model(self):
        self.assertIn('let usesSnapshot = !restoredCompletedState', self.initialization)
        self.assertIn('if try await indexInitialSnapshot(currentEntries, resuming: resumeState)', self.initialization)
        self.assertIn('let before = saved?.oldestTimestamp', self.initial)
        self.assertIn('try store?.searchIndexIdentifiers(before: before)', self.initial)
        self.assertNotIn('searchIndexIdentifiers(before: nil)', self.initial)

    def test_native_cursor_is_strict_date_query_and_no_arbitrary_limit(self):
        persistence = (ROOT / 'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text()
        fetch = body(persistence, 'func searchIndexIdentifiers(')
        self.assertIn('if let timestamp { request.predicate = NSPredicate(format: "timestamp < %@", timestamp as NSDate) }', fetch)
        self.assertIn('NSSortDescriptor(key: "timestamp", ascending: false)', fetch)
        self.assertNotIn('fetchLimit', fetch)
        self.assertNotIn('timestamp <=', fetch)
        self.assertNotIn('timestamp ??', fetch)

    def test_storeless_fallback_preserves_nil_cursor_and_strict_optional_date_semantics(self):
        fallback = body(self.initial, 'fallback.filter')
        self.assertIn('guard let before else { return true }', fallback)
        self.assertIn('guard let timestamp = entry.modified else { return false }', fallback)
        self.assertIn('return timestamp < before', fallback)
        # A branch fixture tied to those three guards, not a native fetch execution.
        dates = [None, 8, 7, 6]
        for cursor, wanted in [(None, dates), (7, [6]), (0, [])]:
            found = [date for date in dates if cursor is None or (date is not None and date < cursor)]
            self.assertEqual(found, wanted)

    def test_original_invalid_count_adjusts_total_only_for_zero_indexed_base(self):
        original = self.original['0x1002e8934']
        for token in ['lVar18 = *(long *)(unaff_x22 + 0x380)',
                      'lVar25 = uVar24 - lVar28',
                      'lVar15 = *(long *)(unaff_x22 + 0x388)',
                      'if ((lVar18 < 1) && (bVar6 = SBORROW8(lVar15,lVar25), lVar15 = lVar15 - lVar25',
                      'puVar19[1] = lVar15', 'puVar19[2] = uVar31']:
            self.assertIn(token, original)
        for token in ['let input = allIDs.filter { !$0.isEmpty }', 'let invalid = allIDs.count - input.count',
                      'let indexedBefore = saved?.indexedItems ?? 0', 'var total = saved?.totalItems ?? allIDs.count',
                      'if indexedBefore < 1 { total -= invalid }']:
            self.assertIn(token, self.initial)

    def test_resumed_pass_recomputes_invalid_and_resets_current_batch_date(self):
        self.assertIn('totalItems: total, indexedItems: indexedBefore, oldestTimestamp: nil, invalidItems: invalid', self.initial)
        self.assertNotIn('saved?.invalidItems', self.initial)
        self.assertNotIn('oldestTimestamp: saved', self.initial)
        # Saved counters are pass inputs; no subtraction on an already-progressed pass.
        for indexed, total, ids, wanted in [(0, 4, ['a', '', 'b', ''], (0, 2, 2)),
                                           (3, 8, ['a', '', 'b', ''], (3, 8, 2)),
                                           (0, 8, ['', ''], (0, 6, 2))]:
            invalid = len(ids) - sum(bool(value) for value in ids)
            self.assertEqual((indexed, total - invalid if indexed < 1 else total, invalid), wanted)

    def test_empty_ids_returns_before_constructing_or_saving_new_state(self):
        empty = self.initial.index('guard !allIDs.isEmpty else { return false }')
        self.assertLess(empty, self.initial.index('var state = OriginalSearchIndexingState'))
        self.assertLess(empty, self.initial.index('stateStore.save('))
        original = self.original['0x1002f177c']
        self.assertIn('lVar9 = *(long *)(param_1 + 0x10)', original)
        self.assertIn('if (lVar9 != 0)', original)
        # Original only invokes the new pass in that nonempty branch.
        nonempty = method_body(original, 'if (lVar9 != 0) {')
        self.assertIn('FUN_1002e87e4(', nonempty)
        self.assertNotIn('FUN_1002e87e4(', original[original.index(nonempty) + len(nonempty):])

    def test_batch_success_cancellation_and_finalization_are_unchanged_from_prior_proven_chain(self):
        previous = (self.phase / 'before/replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text()
        old = body(previous, 'private func indexInitialSnapshot(')
        marker = 'for lowerBound in stride('
        historical = (ROOT / '.local/p0-repair/phase-49/before/replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text()
        historical_initial = body(historical, 'private func indexInitialSnapshot(')
        self.assertEqual(old[old.index(marker):], historical_initial[historical_initial.index(marker):])
        current_loop = body(self.initial, marker)
        previous_loop = body(historical_initial, marker)
        suffix = 'let upperBound = min('
        proven_source = (ROOT / '.local/p0-repair/phase-53/before/replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text()
        proven_loop = body(body(proven_source, 'private func indexInitialSnapshot('), marker)
        self.assertEqual(proven_loop[proven_loop.index(suffix):].replace('            enqueueOCR(live)\n', '', 1), previous_loop[previous_loop.index(suffix):])
        save = 'state.indexedItems += live.count'
        self.assertEqual(current_loop[current_loop.index(save):], proven_loop[proven_loop.index(save):])
        self.assertIn('guard isRunning, !Task.isCancelled else { break }', current_loop)
        self.assertIn('guard isRunning, !Task.isCancelled else { return true }', self.initial)
        self.assertIn('state.indexedItems += live.count', self.initial)
        self.assertIn('state.indexedItems = state.totalItems', self.initial)

    def test_restore_decision_table_excludes_explicit_full_reset_and_mismatches(self):
        # Original-bound state decision fixture. SDK probe errors retain valid complete state.
        def decision(allowed, saved, previous, current, probe):
            if not allowed or saved is None or saved[0] != 5:
                return 'clear'
            if previous is not None and current is not None and previous != current:
                return 'clear'
            _, indexed, total = saved
            if indexed < total:
                return 'resume'
            return 'reuse' if total > 0 and (probe == 'error' or bool(probe)) else 'clear'
        rows = [(True, None, None, 'B', [], 'clear'),
                (True, (6, 1, 8), 'A', 'A', [], 'clear'),
                (True, (5, 1, 8), 'A', 'B', [], 'clear'),
                (False, (5, 1, 8), 'A', 'A', [], 'clear'),
                (True, (5, 1, 8), 'A', None, [], 'resume'),
                (True, (5, 0, 8), None, 'B', 'error', 'resume'),
                (True, (5, 8, 8), 'A', 'A', [], 'clear'),
                (True, (5, 8, 8), 'A', 'A', ['id'], 'reuse'),
                (True, (5, 9, 8), 'A', 'A', 'error', 'reuse'),
                (True, (5, 0, 0), 'A', 'A', 'error', 'clear')]
        for *inputs, expected in rows:
            self.assertEqual(decision(*inputs), expected)
        self.assertIn('if needsReset && mayRestoreSavedState,', self.initialization)

    def test_only_two_shared_finite_recovery_records_close_and_lifecycle_stays_open(self):
        self.assertEqual([r['function_id'] for r in self.proof['contracts']],
                         ['Paste:0x1002efba0', 'Paste:0x1002f2280'])
        self.assertTrue(all(not r['full_function_migration_verified'] for r in self.proof['contracts']))
        self.assertEqual(self.proof['function_map_markers_upgraded'], 0)
        self.assertFalse(self.proof['full_function_migration_verified'])
        historical = (ROOT / '.local/p0-repair/phase-48/before/replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text()
        self.assertIn('if !journalCompleted { needsReset = true }', body(historical, 'private func drain() async'))
        limitations = ' '.join(self.proof['retained_partial_contracts'])
        for token in ['isRunning/stop/wait', 'weak-owner/ack', 'same-process interrupted']:
            self.assertIn(token, limitations)


if __name__ == '__main__':
    unittest.main()
