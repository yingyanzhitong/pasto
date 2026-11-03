from frc_result_scope_contract import assert_query_result_only, ui_init_segments
"""Source/static evidence checks only. Does not execute Swift, CoreData or Spotlight."""
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
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment
from index_write_scope_contract import (write_segments, assert_write_scope_only,
                                       assert_service_initializer_only, assert_ui_service_composition_only)


class WeakSDKWriteOwnerContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-64'
        cls.proof = json.loads((cls.phase / 'weak-sdk-write-contract.json').read_text())
        cls.path = 'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift'
        cls.ui_path = 'replica/Sources/Pasto/UI/ReplicaUIController.swift'
        cls.source = (ROOT / cls.path).read_text()
        cls.before = (cls.phase / 'before' / cls.path).read_text()
        cls.ui = (ROOT / cls.ui_path).read_text()
        cls.writer = body(cls.source, 'private static func writeSearchableItems(')
        cls.original = {r['address']: original_fragment((ROOT / r['path']).read_text(), r['address'][2:])
                        for r in cls.proof['original_fragments']}
        cls.words = {int(r['address'], 16): struct.unpack('<I', bytes.fromhex(r['bytes']))[0]
                     for r in cls.proof['ARM_words']}

    def test_original_binary_fragments_current_snapshots_and_disassemblies_are_bound(self):
        self.assertEqual(len(self.proof['original_fragments']), 14)
        for row in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / row['path'])[row['address']]['sha256'], row['sha256'])
        for row in [self.proof['binary']] + self.proof['arm_disassemblies']:
            self.assertEqual(hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest(), row['sha256'])
        for path, digest in self.proof['current_sources'].items():
            self.assertEqual(hashlib.sha256((self.phase / 'after' / path).read_bytes()).hexdigest(), digest)
            if path == self.path:
                frozen = (self.phase / 'after' / path).read_text()
                for marker in ['private static func writeSearchableItems(', 'private func searchableItem(']:
                    self.assertEqual(body((ROOT / path).read_text(), marker), body(frozen, marker))
                assert_query_result_only(self, body((ROOT / path).read_text(), 'private func replaceQuery('), body(frozen, 'private func replaceQuery('))
            else:
                composition = body(body((ROOT / path).read_text(), 'final class ReplicaUIState:'), 'init(store: ClipboardStore)')
                previous = body(body((self.phase / 'after' / path).read_text(), 'final class ReplicaUIState:'), 'init(store: ClipboardStore)')
                marker = 'collectionItemObservation = store.collectionItemUpdates.sink'
                self.assertEqual(ui_init_segments(composition.split(marker)[0]), ui_init_segments(previous.split(marker)[0]))

    def test_owner_operations_and_SDK_selector_use_real_chained_imports(self):
        self.assertEqual({r['symbol'] for r in self.proof['runtime_imports']},
                         {'_swift_weakLoadStrong', '_swift_release', '_objc_retain', '_objc_release'})
        for row in self.proof['runtime_imports']:
            self.assertTrue(row['chain']['declared_chain_reachable'])
            raw, = struct.unpack('<Q', bytes.fromhex(row['pointer_bytes']))
            self.assertEqual(raw >> 63, 1)
            self.assertEqual(raw & 0xffffff, row['ordinal'])
        selector = self.proof['selector_binding']
        self.assertTrue(selector['chain']['declared_chain_reachable'])
        self.assertEqual(selector['selector'], 'indexSearchableItems:completionHandler:')
        self.assertEqual(bytes.fromhex(selector['selector_bytes']), selector['selector'].encode() + b'\0')

    def test_native_weak_load_retains_native_index_then_releases_service_before_bridge(self):
        def bl(a):
            w = self.words[a]
            self.assertEqual(w >> 26, 0b100101)
            displacement = w & ((1 << 26) - 1)
            if displacement & (1 << 25): displacement -= 1 << 26
            return a + 4 * displacement
        self.assertEqual(bl(0x1002e2124), 0x100bfcc30)
        self.assertEqual(self.words[0x1002e212c], 0xf9400808)  # SDK field owner+0x10
        self.assertEqual(bl(0x1002e213c), 0x100bfbf70)
        self.assertEqual(bl(0x1002e2148), 0x100bfc9c0)
        self.assertEqual(bl(0x1002e2230), int(self.proof['selector_binding']['stub'], 16))
        self.assertLess(0x1002e2148, 0x1002e215c)
        descriptor = self.proof['async_descriptor']
        rel, = struct.unpack('<i', bytes.fromhex(descriptor['bytes'])[:4])
        self.assertEqual(int(descriptor['address'], 16) + rel, 0x1002e43a0)
        self.assertIn('FUN_1002e20b8(', self.original['0x1002e43a0'])

    def test_native_absent_service_returns_tag_one_without_SDK_or_throw(self):
        a = 0x1002e2128
        displacement = (self.words[a] >> 5) & ((1 << 19) - 1)
        if displacement & (1 << 18): displacement -= 1 << 19
        self.assertEqual(a + 4 * displacement, 0x1002e2264)
        self.assertEqual(self.words[0x1002e2264], 0x52800028)
        self.assertEqual(self.words[0x1002e2268], 0x390002a8)
        self.assertEqual(self.words[0x1002e2278], 0xd2800014)  # no Swift error
        self.assertEqual(self.words[0x1002e2294], 0xd61f0000)
        native = self.original['0x1002e20b8']
        absent = native[native.index('*param_1 = 1;'):]
        self.assertNotIn('indexSearchableItems', absent)
        self.assertNotIn('_swift_willThrow', absent)

    def test_native_success_zero_error_propagation_and_outer_result_discard(self):
        self.assertEqual(self.words[0x1002e2318], 0x3900011f)
        self.assertIn('_swift_willThrow()', self.original['0x1002e2348'])
        self.assertIn('if (param_2 == 0)', self.original['0x1002e23a8'])
        self.assertIn('Swift::CheckedContinuation::resume(&local_28,puVar1)', self.original['0x1002e23a8'])
        outer = self.original['0x1002e202c']
        self.assertIn('if (unaff_x20 == 0)', outer)
        self.assertIn('pcVar3 = FUN_1000e5808', outer)
        self.assertNotIn('undefined1', outer)
        self.assertEqual(self.words[0x1002e207c], 0xb4000094)

    def test_domain_defaults_delegate_and_format_marker_are_preserved_across_split(self):
        assert_service_initializer_only(self, self.source, self.before)
        self.assertIn('private let index: CSSearchableIndex', self.source)
        self.assertIn('private let resolveWriteIndex: () -> CSSearchableIndex?', self.source)
        self.assertIn('resolveWriteIndex = { [weak service] in service?.index }', self.source)
        indexer = body(self.source, 'final class ReplicaSearchIndex:')
        self.assertNotRegex(indexer, r'(?:let|var) \w+: ReplicaSpotlightService')
        self.assertNotIn('service:', self.writer)

    def test_real_UI_owns_service_independently_of_queued_indexer(self):
        frozen_ui = (self.phase / 'after' / self.ui_path).read_text()
        assert_ui_service_composition_only(self, frozen_ui, (self.phase / 'before' / self.ui_path).read_text())
        self.assertIn('private let searchService: ReplicaSpotlightService', self.ui)
        composition = body(body(self.ui, 'final class ReplicaUIState:'), 'init(store: ClipboardStore)')
        self.assertIn('searchService = service', composition)
        self.assertIn('searchIndex = ReplicaSearchIndex(service: service, store: store)', composition)
        self.assertEqual(self.ui.count('ReplicaSearchIndex('), 1)
        self.assertNotRegex(self.source, r'\[service\]')

    def test_shared_async_scope_contains_only_SDK_index_and_preserves_error_callback(self):
        self.assertTrue(self.writer.startswith('{\n        guard let index else { return nil }'))
        tokens = ['guard let index else { return nil }', 'try await withCheckedThrowingContinuation',
                  'index.indexSearchableItems(items)', 'if let error { continuation.resume(throwing: error) }',
                  'else { continuation.resume() }', 'return ()']
        offsets = [self.writer.index(t) for t in tokens]
        self.assertEqual(offsets, sorted(offsets))
        self.assertEqual(self.source.count('index.indexSearchableItems('), 1)
        for forbidden in ['self.', 'service', 'Task.isCancelled', 'isRunning', 'try?', 'catch', '.filter', '.compactMap', 'retry']:
            self.assertNotIn(forbidden, self.writer)

    def test_four_real_consumers_keep_prepared_items_and_every_nonwrite_segment(self):
        expected = {'private func reindexTargets(': ['changed'],
                    'private func applyHistoryChanges(': ['live.map { searchableItem($0, isUpdate: false) }'],
                    'private func indexInitialSnapshot(': ['changed'],
                    'private func drainOCRQueue()': ['[item]']}
        for marker, args in expected.items():
            current, previous = body(self.source, marker), body(self.before, marker)
            assert_write_scope_only(self, current, previous)
            self.assertEqual(write_segments(current)[1], args)
            self.assertIn('_ = try await Self.writeSearchableItems(', current)
        self.assertEqual(self.source.count('_ = try await Self.writeSearchableItems('), 4)
        self.assertNotIn('index.indexSearchableItems(', body(self.source, 'private func startWorker()'))

    def test_queue_delegate_retry_stop_query_and_content_building_remain_identical(self):
        for marker in ['private func startWorker()', 'private func drain() async',
                       'private func retryTransientIndexErrors(', 'private static func isTransientIndexError(',
                       'private func deleteIdentifiers(', 'private func clearIndex()', 'private func stopIndexing()',
                       'private func startHistoryObservation()', 'private func initializeIndexIfNeeded(',
                       'private func searchableItem(', 'private func replaceQuery(',
                       'nonisolated private static func matchingIdentifiers(', 'nonisolated private func rebuild(',
                       'private static func performDelegateRebuild(', 'private func enqueueDelegateRebuild(']:
            (assert_query_result_only if marker == 'private func replaceQuery(' else lambda t, a, b: t.assertEqual(a, b))(self, body(self.source, marker), body(self.before, marker))
        self.assertEqual(self.source.count('try await retryTransientIndexErrors'), 3)
        self.assertNotIn('retryTransientIndexErrors', body(self.source, 'private func drainOCRQueue()'))

    def test_segment_comparison_rejects_narrowed_inputs_or_hidden_old_callback_logic(self):
        current = body(self.source, 'private func reindexTargets(')
        previous = body(self.before, 'private func reindexTargets(')
        with self.assertRaises(AssertionError):
            write_segments(current.replace('writeSearchableItems(changed,', 'writeSearchableItems(changed.filter { _ in true },'))
        with self.assertRaises(AssertionError):
            write_segments(previous.replace('else { continuation.resume() }', 'else { continuation.resume(); indexed = [:] }'))
        with self.assertRaises(AssertionError):
            assert_write_scope_only(self, current.replace('refreshed.append(contentsOf: live)', 'indexed = [:]'), previous)

    def test_finite_record_only_no_FRC_or_entity_context_repair_is_claimed(self):
        row, = self.proof['contracts']
        self.assertEqual(row['function_id'], 'Paste:0x1002e20b8')
        self.assertFalse(row['full_function_migration_verified'])
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertEqual(self.proof['function_map_markers_upgraded'], 0)
        self.assertEqual(self.proof['new_difference_records'], 0)
        base = json.loads((self.phase / 'baseline.json').read_text())
        changed = {path for path, digest in base['production'].items()
                   # Historical round64's exact edit set; round65 has additional legitimate source edits.
                   if hashlib.sha256((ROOT / '.local/p0-repair/phase-65/before' / path).read_bytes()).hexdigest() != digest}
        self.assertEqual(changed, {self.path, self.ui_path})
        self.assertTrue(any('FRC/' in text for text in self.proof['retained_partial_contracts']))


if __name__ == '__main__':
    unittest.main()
