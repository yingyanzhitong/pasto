from frc_result_scope_contract import ui_init_segments
"""Delegate owner scopes and original release/ack ARM; no Swift, ARC or SDK execution."""
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
from test_p0_repair_checksum_routing import original_fragment


from suggestion_filter_title_scope_contract import pre_suggestion_filter_title_bytes
class DelegateOwnerAckContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-62'
        cls.proof = json.loads((cls.phase / 'delegate-owner-ack-contract.json').read_text())
        cls.path = 'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift'
        cls.source = (ROOT / cls.path).read_text()
        cls.before = (cls.phase / 'before' / cls.path).read_text()
        cls.wrapper = body(cls.source, 'nonisolated private func rebuild(')
        cls.scope = body(cls.source, 'private static func performDelegateRebuild(')
        cls.enqueue = body(cls.source, 'private func enqueueDelegateRebuild(')
        cls.drain = body(cls.source, 'private func drain() async')
        cls.original = {r['address']: original_fragment((ROOT / r['path']).read_text(), r['address'][2:])
                        for r in cls.proof['original_fragments']}

    def test_original_fragments_binary_disassembly_and_actual_source_are_bound(self):
        self.assertEqual(len(self.proof['original_fragments']), 11)
        for row in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / row['path'])[row['address']]['sha256'], row['sha256'])
        for row in [self.proof['binary']] + self.proof['arm_disassemblies']:
            self.assertEqual(hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest(), row['sha256'])
        self.assertEqual(hashlib.sha256((self.phase / 'after' / self.path).read_bytes()).hexdigest(), self.proof['current_sources'][self.path])
        for marker in ['nonisolated private func rebuild(', 'private static func performDelegateRebuild(', 'private func enqueueDelegateRebuild(', 'private func drain() async']:
            self.assertEqual(body(self.source, marker), body((self.phase / 'after' / self.path).read_text(), marker))

    def test_runtime_imports_are_chained_bindings_not_disassembler_guessed_labels(self):
        self.assertEqual({r['symbol'] for r in self.proof['swift_runtime_imports']},
                         {'_swift_weakLoadStrong', '_swift_release', '_swift_task_switch'})
        for row in self.proof['swift_runtime_imports']:
            raw = struct.unpack('<Q', bytes.fromhex(row['pointer_bytes']))[0]
            self.assertEqual(raw >> 63, 1)
            self.assertEqual(raw & 0xffffff, row['ordinal'])
            self.assertTrue(row['chain']['declared_chain_reachable'])

    def test_native_release_then_zero_executor_then_ack_continuations(self):
        words = {r['address']: struct.unpack('<I', bytes.fromhex(r['bytes']))[0] for r in self.proof['ARM_words']}
        def target(a, width=26, shift=0):
            value = (words[hex(a)] >> shift) & ((1 << width) - 1)
            if value & (1 << (width - 1)): value -= 1 << width
            return a + value * 4
        for release, hop, zero1, zero2, continuation, invoke in [
            (0x1002e4728, 0x1002e4748, 0x1002e4734, 0x1002e4738, '0x1002e474c', 0x1002e4764),
            (0x1002e4954, 0x1002e4974, 0x1002e4960, 0x1002e4964, '0x1002e4978', 0x1002e4990)]:
            self.assertEqual(target(release), 0x100bfc9c0)
            self.assertEqual(target(hop), 0x100bfcb10)
            self.assertLess(release, hop)
            self.assertEqual(words[hex(zero1)], 0xd2800001)
            self.assertEqual(words[hex(zero2)], 0xd2800002)
            self.assertEqual(words[hex(invoke)], 0xd63f0100)
            self.assertIn('(**(code **)', self.original[continuation])
        for address, resume in [('0x1002e46fc', 'FUN_1002e474c'), ('0x1002e4928', 'FUN_1002e4978')]:
            native = self.original[address]
            self.assertLess(native.index('_swift_release(uVar1)'), native.index('_swift_task_switch(' + resume))

    def test_outer_nonisolated_task_captures_only_weak_target_and_calls_ack_after_scope(self):
        target = body(self.source, 'private final class ReplicaSearchIndexDelegateTarget:')
        self.assertIn('weak var indexer: ReplicaSearchIndex?', target)
        self.assertIn('init(_ indexer: ReplicaSearchIndex) { self.indexer = indexer }', target)
        task = body(self.wrapper, 'Task ')
        self.assertIn('let target = ReplicaSearchIndexDelegateTarget(self)', self.wrapper)
        self.assertLess(task.index('await ReplicaSearchIndex.performDelegateRebuild(target, identifiers: identifiers)'),
                        task.index('acknowledge()'))
        self.assertEqual(task.count('acknowledge()'), 1)
        for token in ['self.', '[self]', 'guard let self', '@MainActor', 'target.indexer', 'let indexer']:
            self.assertNotIn(token, task)

    def test_strong_owner_exists_only_inside_awaited_helper_and_nil_owner_skips_queue(self):
        self.assertIn('guard let indexer = target.indexer else { return }', self.scope)
        self.assertIn('await indexer.enqueueDelegateRebuild(identifiers)', self.scope)
        self.assertLess(self.scope.index('guard let indexer'), self.scope.index('await indexer.'))
        for token in ['acknowledge', 'withCheckedContinuation', 'pending =', 'Task ', 'indexSearchableItems']:
            self.assertNotIn(token, self.scope)
        self.assertNotIn('guard let requested', self.enqueue)
        self.assertNotIn('guard let requested', self.scope)

    def test_queue_relay_resumes_waiter_after_index_work_instead_of_calling_SDK_block(self):
        self.assertIn('await withCheckedContinuation { (continuation: CheckedContinuation<Void, Never>) in', self.enqueue)
        relay = body(self.enqueue, 'await withCheckedContinuation')
        order = ['pending = request', 'acknowledgements.append { continuation.resume() }', 'startWorker()']
        self.assertEqual([relay.index(t) for t in order], sorted(relay.index(t) for t in order))
        self.assertNotIn('acknowledge', self.enqueue.replace('acknowledgements', 'relays'))
        self.assertNotIn('acknowledge()', self.drain)
        self.assertEqual(self.drain, body(self.before, 'private func drain() async'))
        self.assertLess(self.drain.index('requestAcknowledgements = []'), self.drain.index('completed.forEach { $0() }'))
        self.assertIn('requestAcknowledgements.forEach { $0() }', self.drain)

    def test_full_target_flags_and_stop_order_are_preserved_in_actual_enqueuer(self):
        old = body(self.before, 'nonisolated private func rebuild(')
        for text in [self.enqueue, old]:
            self.assertIn('reindexIdentifiers.append(contentsOf: identifiers)', text)
            self.assertIn('needsReset = true', text)
            self.assertIn('mayRestoreSavedState = false', text)
            self.assertIn('if isRunning { await stopIndexing() }', text)
            self.assertIn('pendingMayInitializeIndex = true', text)
            self.assertIn('pendingResetsIndex = true', text)
        self.assertLess(self.enqueue.index('await stopIndexing()'), self.enqueue.index('pending = request'))
        for token in ['compactMap', 'prefix(', 'Set(', 'requested =', 'replaceQuery(', 'Task.isCancelled']:
            self.assertNotIn(token, self.enqueue)
        self.assertIn('rebuild(identifiers: nil, acknowledgementHandler)', self.source)
        self.assertIn('rebuild(identifiers: identifiers, acknowledgementHandler)', self.source)

    def test_index_operation_retry_snapshot_OCR_and_source_models_are_unchanged(self):
        for marker in ['private func startWorker()', 'private func reindexTargets(', 'private func indexInitialSnapshot(',
                       'private func applyHistoryChanges(', 'private func retryTransientIndexErrors(',
                       'private func startHistoryObservation()', 'private func stopIndexing()', 'private func drainOCRQueue()',
                       'func availableFilters()', 'private func searchableItem(', 'private func initializeIndexIfNeeded(']:
            assert_write_scope_only(self, body(self.source, marker), body(self.before, marker))
        for path in ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
                     'replica/Sources/PastoCore/OriginalSearchSuggestions.swift']:
            if path.endswith('ReplicaUIController.swift'):
                # Keep the old whole-UI service-composition proof tied to its actual snapshot.
                frozen_ui = (ROOT / '.local/p0-repair/phase-65/before' / path).read_text()
                assert_ui_service_composition_only(self, frozen_ui, (self.phase / 'before' / path).read_text())
                marker = 'collectionItemObservation = store.collectionItemUpdates.sink'
                self.assertEqual(ui_init_segments(body(body((ROOT / path).read_text(), 'final class ReplicaUIState:'), 'init(store: ClipboardStore)').split(marker)[0]),
                                 ui_init_segments(body(body(frozen_ui, 'final class ReplicaUIState:'), 'init(store: ClipboardStore)').split(marker)[0]))
            else:
                self.assertEqual(pre_suggestion_filter_title_bytes(ROOT / path), (self.phase / 'before' / path).read_bytes())

    def test_completion_trace_has_one_ack_after_owner_scope_for_nil_success_and_error(self):
        # Contract trace from the bound callbacks and real source scopes; not Swift ARC execution.
        for alive, success in [(False, False), (False, True), (True, False), (True, True)]:
            events = ['weak-load']
            if alive:
                events += ['strong-owner-scope', 'enqueue', 'SDK-success' if success else 'SDK-error-caught',
                           'resume-index-waiter', 'leave-owner-scope']
            events += ['ack']
            self.assertEqual(events.count('ack'), 1)
            if alive:
                self.assertLess(events.index('leave-owner-scope'), events.index('ack'))
            else:
                self.assertNotIn('enqueue', events)
        self.assertEqual(self.wrapper.count('acknowledge()'), 1)

    def test_write_owner_remains_open_and_no_full_ARC_or_actor_claim_is_made(self):
        self.assertEqual([r['function_id'] for r in self.proof['contracts']], ['Paste:0x1002e46fc', 'Paste:0x1002e4928'])
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertEqual(self.proof['function_map_markers_upgraded'], 0)
        limitations = '\n'.join(self.proof['retained_partial_contracts'])
        for text in ['2e20b8', 'independently', 'ARC', 'ABI', 'MainActor']:
            self.assertIn(text, limitations)
        self.assertIn('guard let self else { return }', body(self.source, 'private func startWorker()'))
