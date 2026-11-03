"""Deferred filter browser candidate delivery; source/ARM only, no SwiftUI runtime."""
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
from native_application_scope_contract import pre_native_application_bytes
from filter_model_query_scope_contract import pre_filter_model_query
from test_p0_repair_checksum_routing import original_fragment


class FilterLoadingContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-60'
        cls.proof = json.loads((cls.phase / 'filter-loading-contract.json').read_text())
        cls.path = 'replica/Sources/Pasto/UI/FilterBrowser.swift'
        cls.source = (ROOT / cls.path).read_text()
        cls.before = (cls.phase / 'before' / cls.path).read_text()
        cls.model = body(cls.source, 'private final class ReplicaFilterBrowserModel: ObservableObject')
        cls.opening = body(cls.source, 'func showFilterBrowser(')
        cls.builder = body(cls.source, 'private static func filterBrowserSections(')
        cls.original = {r['address']: original_fragment((ROOT / r['path']).read_text(), r['address'][2:])
                        for r in cls.proof['original_fragments']}

    def test_native_proof_inputs_and_actual_source_are_bound(self):
        self.assertEqual(len(self.proof['original_fragments']), 6)
        for row in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / row['path'])[row['address']]['sha256'], row['sha256'])
        for row in [self.proof['binary']] + self.proof['arm_disassemblies']:
            self.assertEqual(hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest(), row['sha256'])
        frozen = (self.phase / 'after' / self.path).read_text()
        self.assertEqual(hashlib.sha256((self.phase / 'after' / self.path).read_bytes()).hexdigest(), self.proof['current_sources'][self.path])
        for marker in ['private final class ReplicaFilterBrowserModel: ObservableObject', 'private var visibleSections:',
                       'private func activate(', 'private func handleMonitoredKey(']:
            self.assertEqual(body(pre_filter_model_query(self.source), marker), body(frozen, marker))

    def test_descriptor_and_MainActor_hop_bind_real_task_provider_and_publication(self):
        descriptor = self.proof['async_descriptor']
        self.assertEqual(int(descriptor['address'], 16) + struct.unpack_from('<i', bytes.fromhex(descriptor['bytes']))[0],
                         int(descriptor['target'], 16))
        self.assertIn('FUN_100006104(', self.original['0x100008218'])
        self.assertIn('_swift_task_switch(FUN_100006184', self.original['0x100006104'])
        load = self.original['0x100006184']
        self.assertLess(load.index('FUN_1002e00a0()'), load.index('Combine::Published::_set_subscript('))
        words = {r['address']: int.from_bytes(bytes.fromhex(r['bytes']), 'little') for r in self.proof['ARM_words']}
        def call_target(a):
            value = words[hex(a)] & ((1 << 26) - 1)
            if value & (1 << 25): value -= 1 << 26
            return a + value * 4
        self.assertEqual(call_target(0x1000060d0), 0x1000645b0)
        self.assertEqual(call_target(0x1000061cc), 0x1002e00a0)
        self.assertEqual(call_target(0x100006218), 0x100bf558c)
        self.assertEqual(words['0x100005ffc'], 0x52800109)  # collapsed limit eight

    def test_actual_model_begins_empty_and_defers_provider_until_retained_task(self):
        self.assertIn('@Published private(set) var sections: [ReplicaFilterBrowser.Section] = []', self.model)
        self.assertIn('load: @escaping @MainActor () -> [ReplicaFilterBrowser.Section]', self.model)
        self.assertIn('Task { @MainActor [self] in sections = load() }', self.model)
        self.assertEqual(self.model.count('load()'), 1)
        for extra in ['[weak self]', 'try?', 'Task.isCancelled', 'deinit', '.cancel()', 'onAppear', 'DispatchQueue']:
            self.assertNotIn(extra, self.model)
        native = self.original['0x100005e1c']
        self.assertLess(native.index('::_availableFilters'), native.index('FUN_1000645b0('))
        self.assertLess(native.index('::_expandedSections'), native.index('FUN_1000645b0('))
        self.assertIn('*(MainActor **)(puVar2 + 0x20) = unaff_x20', native)

    def test_opening_passes_deferred_builder_not_materialized_source_arrays(self):
        self.assertIn('let state = self.state', self.opening)
        self.assertIn('load: { Self.filterBrowserSections(filters: state.availableSearchFilters()) }', self.opening)
        self.assertLess(self.opening.index('let hideApplied = NSEvent.modifierFlags.contains(.option)'),
                        self.opening.index('let model ='))
        self.assertLess(self.opening.index('let model ='), self.opening.index('popover.present(controller, relativeTo: button)'))
        for extra in ['ReplicaSearchSuggestionSource.applications(', 'ReplicaSearchSuggestionSource.devices(',
                      'ReplicaSearchSuggestionSource.pinboards(', 'let sources =', 'let sections:', 'sections: sections']:
            self.assertNotIn(extra, self.opening)
        self.assertIn('let content = ReplicaFilterBrowser(state: state, model: model,', self.opening)
        self.assertIn('hideApplied: hideApplied', self.opening)

    def test_same_observed_model_drives_visible_sections_after_publication(self):
        self.assertIn('@ObservedObject var model: ReplicaFilterBrowserModel', self.source)
        self.assertIn('private var sections: [Section] { model.sections }', self.source)
        visible = body(self.source, 'private var visibleSections:')
        self.assertIn('sections.compactMap { section in', visible)
        self.assertEqual(body(pre_filter_model_query(self.source), 'private var visibleSections:'), body(self.before, 'private var visibleSections:'))
        view = body(self.source, 'private struct ReplicaFilterBrowser: View')
        self.assertNotIn('ReplicaFilterBrowserModel(load:', view)
        self.assertNotIn('let sections: [Section]', view)

    def test_builder_reuses_source_service_and_keeps_frozen_prior_query_evidence(self):
        frozen = (self.phase / 'after' / self.path).read_text()
        previous_opening = body(self.before, 'func showFilterBrowser(')
        previous = previous_opening[previous_opening.index('        let sources ='):previous_opening.index('        let content =')]
        previous = previous.replace('        let sections: [ReplicaFilterBrowser.Section] = [', '        return [')
        self.assertEqual(body(frozen, 'private static func filterBrowserSections('), '{\n' + previous + '    }')
        self.assertIn('filters: state.availableSearchFilters()', self.opening)
        for tag in [1, 0, 5, 3, 4]:
            self.assertIn('filters[' + str(tag) + '] ?? []', self.builder)
        service = (ROOT / 'replica/Sources/PastoCore/OriginalSearchSuggestions.swift').read_text()
        load = body(service, 'public static func f_1002e00a0(')
        for source in ['app', 'type', 'device', 'pinboard']:
            self.assertIn('try? (provider()?.' + source + '(""', load)
        self.assertNotIn('store.items', self.builder)

    def test_existing_query_keyboard_expansion_and_close_consumers_are_unchanged(self):
        for marker in ['func handleSearchCommand()', 'private func activate(', 'private func move(',
                       'private func installKeyboardMonitor()', 'private func removeKeyboardMonitor()',
                       'private func handleMonitoredKey(', '@ViewBuilder private func entryView(']:
            self.assertEqual(body(pre_filter_model_query(self.source), marker), body(self.before, marker))
        self.assertEqual(body(self.opening, 'popover.onWillClose ='),
                         body(body(self.before, 'func showFilterBrowser('), 'popover.onWillClose ='))
        self.assertIn('@State private var expanded: Set<UInt8> = []', self.source)
        self.assertIn('Array(choices.prefix(8))', self.source)

    def test_source_service_and_model_limitations_stay_explicit(self):
        self.assertEqual([r['function_id'] for r in self.proof['contracts']],
                         ['Paste:0x100005e1c', 'Paste:0x100006184'])
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertEqual(self.proof['function_map_markers_upgraded'], 0)
        limitations = '\n'.join(self.proof['retained_partial_contracts'])
        for token in ['2e00a0/07d0e0', 'first-frame', 'ABI', 'try?']:
            self.assertIn(token, limitations)
        for path in ['replica/Sources/Pasto/UI/ReplicaSearchSuggestionSource.swift',
                     'replica/Sources/PastoCore/ClipboardSourcePersistence.swift']:
            self.assertEqual(pre_native_application_bytes(ROOT / path), (self.phase / 'before' / path).read_bytes())
