from item_order_scope_contract import without_list_route
"""Real optional provider registration and consumers, native error/date branches; source only."""
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

from pinboard_filter_identity_scope_contract import pre_pinboard_filter_identity_bytes

class SuggestionSourceServiceContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-61'
        cls.proof = json.loads((cls.phase / 'suggestion-source-service-contract.json').read_text())
        cls.paths = {name: 'replica/Sources/' + path for name, path in {
            'core': 'PastoCore/OriginalSearchSuggestions.swift', 'store': 'PastoCore/ClipboardStore.swift',
            'index': 'Pasto/UI/ReplicaSearchIndex.swift', 'state': 'Pasto/UI/ReplicaUIController.swift',
            'browser': 'Pasto/UI/FilterBrowser.swift'}.items()}
        cls.sources = {k: (ROOT / p).read_text() for k, p in cls.paths.items()}
        cls.load = body(cls.sources['core'], 'public static func f_1002e00a0(')
        cls.original = {r['address']: original_fragment((ROOT / r['path']).read_text(), r['address'][2:])
                        for r in cls.proof['original_fragments']}

    def test_original_binary_fragments_prior_contracts_and_real_source_hashes(self):
        self.assertEqual(len(self.proof['original_fragments']), 11)
        for row in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / row['path'])[row['address']]['sha256'], row['sha256'])
        for row in [self.proof['binary'], self.proof['arm_disassembly']] + self.proof['prior_contracts']:
            self.assertEqual(hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest(), row['sha256'])
        for path, digest in self.proof['current_sources'].items():
            frozen = (self.phase / 'after' / path).read_text()
            self.assertEqual(hashlib.sha256((self.phase / 'after' / path).read_bytes()).hexdigest(), digest)
            if path == self.paths['index']:
                for marker in ['func setSuggestionDataSource(', 'func availableFilters()']:
                    self.assertEqual(body((ROOT / path).read_text(), marker), body(frozen, marker))
            elif path.endswith('ReplicaUIController.swift'):
                frozen_ui = (ROOT / '.local/p0-repair/phase-65/before' / path).read_text()
                assert_ui_service_composition_only(self, frozen_ui, frozen)
                for marker in ['private func installSearchQueryDelivery()', 'func availableSearchFilters()']:
                    self.assertEqual(without_list_route(body((ROOT / path).read_text(), marker)), body(frozen_ui, marker))
            elif path.endswith('ClipboardStore.swift'):
                for marker in ['public func makeSearchSuggestionProvider()', 'public func searchPinboardNames(', 'public func searchApplicationNames(', 'public func searchDeviceNames(']:
                    self.assertEqual(body((ROOT / path).read_text(), marker), body(frozen, marker))
            else:
                self.assertEqual(pre_pinboard_filter_identity_bytes(ROOT / path), (self.phase / 'after' / path).read_bytes())

    def test_native_startup_keypath_registration_witness_and_context_provider_remain_bound(self):
        prior = json.loads((ROOT / self.proof['prior_contracts'][0]['path']).read_text())
        names = {r['value']: [x['value'] for x in r['fields']] for r in prior['nominal_types']}
        self.assertEqual(names['SearchService'], ['index', 'logger'])
        self.assertIn('suggestionDataSource', names['SpotlightIndex'])
        self.assertEqual(names['CoreDataSuggestionDataSource'], ['managedObjectContext'])
        witness = prior['suggestion_data_source']['concrete_witness']
        raw = bytes.fromhex(witness['bytes'])
        targets = [0x100000000 + (struct.unpack_from('<Q', raw, offset)[0] & ((1 << 36) - 1)) for offset in [8, 16, 24, 32]]
        self.assertEqual(targets, [0x10030f380, 0x10030e6a8, 0x10030f3a0, 0x10030f3c0])
        self.assertIn('FUN_1002fd914()', self.original['0x10007d73c'])
        self.assertIn('FUN_1002fd934(FUN_10030f5a8', self.original['0x1002fd914'])
        self.assertIn('objc_stub::viewContext(', self.original['0x1002fd99c'])
        self.assertIn('FUN_1001a7c4c(auStack_38,unaff_x20 + 0x28', self.original['0x1002e1b54'])

    def test_each_native_source_optional_and_error_branch_clears_only_that_result(self):
        def word(row): return struct.unpack('<I', bytes.fromhex(row['bytes']))[0]
        for row in self.proof['source_gates']:
            self.assertEqual(word(row['optional_gate']) & 31, 8)
            self.assertEqual(word(row['error_check']) & 31, 21)
            self.assertEqual(word(row['error_empty_result']), 0xd2800016)  # mov x22,0
            call = word(row['error_release']) & ((1 << 26) - 1)
            if call & (1 << 25): call -= 1 << 26
            self.assertEqual(int(row['error_release']['address'], 16) + call * 4, 0x100bfc708)
            branch = word(row['continue_after_error'])
            self.assertEqual(branch & 0xfc000000, 0x14000000)
        self.assertEqual([r['witness_slot'] for r in self.proof['source_gates']], [16, 8, 24, 32])

    def test_core_source_order_and_live_optional_reads_are_not_cached_snapshots(self):
        self.assertIn('provider: () -> Provider?', self.sources['core'])
        tokens = ['provider()?.type("")', 'provider()?.app("")', 'provider()?.device("")',
                  'OriginalSearchDateRanges.f_1002d8ce0()', 'provider()?.pinboard("")']
        self.assertEqual([self.load.index(t) for t in tokens], sorted(self.load.index(t) for t in tokens))
        self.assertEqual(self.load.count('provider()?'), 4)
        for source in ['type', 'app', 'device', 'pinboard']:
            self.assertIn('try? (provider()?.' + source + '("") ?? [])', self.load)
        for token in ['prefix(', 'Set(', '.sorted', 'store.items', 'sourceName', 'f_10030f3e0', 'catch', 'return [:]']:
            self.assertNotIn(token, self.load)
        self.assertIn('pinboards.map { $0.map { .filter(5, $0.identifier) } }', self.load)

    def test_error_result_omits_key_but_missing_provider_keeps_empty_candidate_array(self):
        # f2e0a08 removes nil group input; a nonnil empty array remains a value.
        native = self.original['0x1002e0a08']
        self.assertIn('if (param_1 == 0)', native)
        self.assertIn('FUN_1002fa178(param_2,lVar2)', native)
        for name, tag in [('types', 1), ('apps', 0), ('devices', 4), ('pinboards', 5)]:
            self.assertIn('filters[' + str(tag) + '] = ' + name + '.map { $0.map', self.load)
        self.assertNotIn('?? []).map', self.load)
        # try? covers the coalescing expression: nil source yields [], throw yields nil.
        self.assertIn('let apps = try? (provider()?.app("") ?? [])', self.load)

    def test_date_endpoints_follow_native_truncation_and_remain_available_without_provider(self):
        self.assertIn('filters[3] = (dateFilters ?? OriginalSearchDateRanges.f_1002d8ce0()).map', self.load)
        self.assertIn('Int(date.range.lowerBound.timeIntervalSince1970)', self.load)
        self.assertIn('Int(date.range.upperBound.timeIntervalSince1970)', self.load)
        for token in ['rounded(', 'f_1002d9d2c', 'guard let provider', 'if let provider']:
            self.assertNotIn(token, self.load)
        words = {r['address']: struct.unpack('<I', bytes.fromhex(r['bytes']))[0] for r in self.proof['ARM_words']}
        self.assertEqual(words['0x1002e0710'], 0x9e780108)  # fcvtzs x8,d8
        self.assertEqual(words['0x1002e0714'], 0x9e780016)  # fcvtzs x22,d0
        cases = [(-1.9, -0.1, '-1 0'), (0.1, 0.9, '0 0'), (-0.9, 1.9, '0 1')]
        for start, end, expected in cases:
            self.assertEqual(str(int(start)) + ' ' + str(int(end)), expected)

    def test_factory_captures_real_persistence_and_forwards_errors_without_memory_fallback(self):
        factory = body(self.sources['store'], 'public func makeSearchSuggestionProvider()')
        self.assertIn('let persistence = self.persistence', factory)
        for kind in ['Application', 'Device', 'Pinboard']:
            self.assertIn('try persistence.search' + kind + 'Names(matching: $0)', factory)
        for token in ['store.items', 'self.items', 'sourceName', 'try?', 'catch', 'weak', 'Set(']:
            self.assertNotIn(token, factory)
        before = (self.phase / 'before' / self.paths['store']).read_text()
        for marker in ['public func searchApplicationNames(', 'public func searchDeviceNames(', 'public func searchPinboardNames(']:
            self.assertEqual(body(self.sources['store'], marker), body(before, marker))

    def test_real_index_owner_property_setter_and_startup_registration_precede_consumers(self):
        self.assertIn('private var suggestionDataSource: OriginalSearchSuggestions.Provider?', self.sources['index'])
        setter = body(self.sources['index'], 'func setSuggestionDataSource(')
        self.assertEqual(setter.strip(), '{\n        suggestionDataSource = provider\n    }')
        service = body(self.sources['index'], 'func availableFilters()')
        self.assertIn('OriginalSearchSuggestions.f_1002e00a0(provider: { suggestionDataSource })', service)
        init = body(body(self.sources['state'], 'final class ReplicaUIState: ObservableObject'), 'init(store: ClipboardStore)')
        tokens = ['searchIndex = ReplicaSearchIndex(', 'searchIndex.setSuggestionDataSource(store.makeSearchSuggestionProvider())',
                  'installListSelectionDelivery()', 'installSearchQueryDelivery()']
        self.assertEqual([init.index(t) for t in tokens], sorted(init.index(t) for t in tokens))

    def test_actual_presented_browser_task_reaches_service_then_renders_returned_nodes(self):
        facade = body(self.sources['state'], 'func availableSearchFilters()')
        self.assertIn('searchIndex.availableFilters()', facade)
        opening = body(self.sources['browser'], 'func showFilterBrowser(')
        self.assertIn('load: { Self.filterBrowserSections(filters: state.availableSearchFilters()) }', opening)
        model = body(self.sources['browser'], 'private final class ReplicaFilterBrowserModel: ObservableObject')
        self.assertIn('Task { @MainActor [self] in sections = load() }', model)
        builder = body(self.sources['browser'], 'private static func filterBrowserSections(')
        for tag in [1, 0, 5, 3, 4]: self.assertIn('filters[' + str(tag) + '] ?? []', builder)
        for token in ['ReplicaSearchSuggestionSource.', 'store.items', 'store.pinboards', 'try?', 'f_10030f3e0("")']:
            self.assertNotIn(token, builder)
        self.assertNotIn('UUID(uuidString: value)', builder)
        self.assertIn('return .pinboard(value)', builder)
        self.assertIn('start <= end', builder)  # retain valid sub-second ranges after integer truncation

    def test_group_errors_nil_and_reentrant_replacement_fixture_follows_native_source_reads(self):
        # Original-bound source projection; does not execute CoreData/Swift callbacks.
        events = []
        state = {'provider': {'type': ['Text', 'Text'], 'app': ValueError('fetch'), 'device': ['D'], 'pinboard': ['raw-id']}}
        def fetch(name):
            events.append(name)
            provider = state['provider']
            if provider is None: return []
            value = provider[name]
            if name == 'type': state['provider'] = None
            if isinstance(value, Exception): return []
            return value
        result = {1: fetch('type'), 0: fetch('app'), 4: fetch('device'), 3: ['dates'], 5: fetch('pinboard')}
        self.assertEqual(events, ['type', 'app', 'device', 'pinboard'])
        self.assertEqual(result, {1: ['Text', 'Text'], 0: [], 4: [], 3: ['dates'], 5: []})
        self.assertEqual(self.load.count('provider()?'), 4)

    def test_old_suggestion_editor_and_index_worker_logic_are_reused(self):
        self.assertEqual(pre_pinboard_filter_identity_bytes(ROOT / 'replica/Sources/Pasto/UI/SearchEditor.swift'),
                         (self.phase / 'before/replica/Sources/Pasto/UI/SearchEditor.swift').read_bytes())
        before = (self.phase / 'before' / self.paths['index']).read_text()
        for marker in ['private func startWorker()', 'private func drain()', 'private func startHistoryObservation()',
                       'private func stopIndexing()', 'private func searchableItem(']:
            self.assertEqual(body(self.sources['index'], marker), body(before, marker))
        old_core = (self.phase / 'before' / self.paths['core']).read_text()
        for marker in ['public static func f_10030f3e0(', 'public static func f_1002df190(']:
            self.assertEqual(body(self.sources['core'], marker), body(old_core, marker))

    def test_finite_data_source_records_do_not_close_native_actor_DI_or_FRC_lifecycle(self):
        self.assertEqual([r['function_id'] for r in self.proof['contracts']], ['Paste:0x10007d0e0', 'Paste:0x1002e00a0'])
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertEqual(self.proof['function_map_markers_upgraded'], 0)
        for word in ['DI', 'ABI', 'FRC', 'SDK owner/ack']:
            self.assertIn(word, '\n'.join(self.proof['retained_partial_contracts']))
