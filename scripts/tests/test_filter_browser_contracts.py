"""Source/decompiler/static-data checks only; does not run Swift or UI."""
import hashlib
import json
import re
import struct
import unittest
from test_offline_p0_contracts import ROOT, body

UI = ROOT / 'replica/Sources/Pasto/UI'


def preserves_query_order(source):
    method = body(source, 'func updateContents(')
    return ('f_1002da16c(parent.queryNodes, flag: 0)' in method
            and 'selections.map(\\.queryNode)' not in method
            and 'f_1002f8760' not in method)


class FilterBrowserContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.state = (UI / 'ReplicaUIController.swift').read_text()
        cls.browser = (UI / 'FilterBrowser.swift').read_text()
        cls.provider = (UI / 'ReplicaSearchSuggestionSource.swift').read_text()
        cls.editor = (UI / 'SearchEditor.swift').read_text()
        cls.report = json.loads((ROOT / 'reports/replica/offline-migration-p0-round14.json').read_text())

    def test_section_order_and_type_names_decode_from_original_bytes(self):
        proof = self.report['static_bindings']
        self.assertEqual(list(bytes.fromhex(proof['section_order']['bytes'])), [1, 0, 5, 3, 4])
        opening = body(self.browser, 'private static func filterBrowserSections(')
        self.assertEqual([int(v) for v in re.findall(r'\.init\(id: (\d+), title:', opening)], [1, 0, 5, 3, 4])
        data = bytes.fromhex(proof['type_static_object']['bytes'])
        count, = struct.unpack_from('<Q', data, 16)
        values = [data[32+i*16:48+i*16][:data[47+i*16]&15].decode() for i in range(count)]
        self.assertEqual(values, ['Unknown', 'Image', 'Color', 'File', 'Link', 'Text'])
        factory = (ROOT / 'replica/Sources/PastoCore/OriginalSearchSuggestions.swift').read_text()
        self.assertIn('type: @escaping (String) throws -> [String] = OriginalSearchSuggestions.f_10030f3e0', factory)
        self.assertIn('filters[1] ?? []', opening)
        self.assertIn('value == "File" ? "files" : value.lowercased()', opening)
        self.assertNotIn('[ClipboardKind.text, .link', opening)

    def test_real_provider_type_witness_and_static_object_input(self):
        proof = self.report['static_bindings']
        conformance = proof['provider_conformance']
        self.assertEqual(conformance['type_name'], 'CoreDataSuggestionDataSource')
        raw = bytes.fromhex(conformance['bytes']); address = int(conformance['address'], 16)
        self.assertEqual(address+8+struct.unpack_from('<i', raw, 8)[0], int(conformance['witness_table'], 16))
        targets = []
        for slot in proof['provider_slots']:
            self.assertEqual(slot['pointer_format'], 6)
            self.assertTrue(slot['declared_chain_reachable'])
            pointer, = struct.unpack('<Q', bytes.fromhex(slot['bytes']))
            self.assertEqual(pointer >> 63, 0)
            targets.append(0x100000000 + (pointer & ((1<<36)-1)))
        self.assertEqual(targets, [0x10030f380, 0x10030e6a8, 0x10030f3a0, 0x10030f3c0])
        words = struct.unpack('<3I', bytes.fromhex(proof['static_object_input_instructions']['bytes']))
        adrp, add, _ = words
        immediate = ((adrp>>5)&0x7ffff)*4 + ((adrp>>29)&3)
        if immediate & (1<<20): immediate -= 1<<21
        page = int(proof['static_object_input_instructions']['address'],16) & ~4095
        self.assertEqual(page+(immediate<<12)+((add>>10)&4095), 0x100fbed58)

    def test_browser_reuses_actual_provider_and_name_order_not_panel_sort_order(self):
        opening = body(self.browser, 'private static func filterBrowserSections(')
        self.assertIn('filters: state.availableSearchFilters()', body(self.browser, 'func showFilterBrowser('))
        factory = body((ROOT / 'replica/Sources/PastoCore/ClipboardStore.swift').read_text(), 'public func makeSearchSuggestionProvider()')
        for group in ['Application', 'Device', 'Pinboard']:
            self.assertIn('try persistence.search' + group + 'Names(matching: $0)', factory)
        self.assertNotIn('sortOrder', opening)
        self.assertNotIn('Set(store.items.map', opening)
        boards = body(self.provider, 'static func pinboards(')
        self.assertIn('try store.searchPinboardNames(matching: query)', boards)
        lists = (ROOT / 'replica/Sources/PastoCore/ClipboardListPersistence.swift').read_text()
        fetch = body(lists, 'func searchPinboardNames(matching query:')
        self.assertIn('rawType == %d AND name MATCHES[cd] %@', fetch)
        self.assertIn('NSSortDescriptor(key: "name", ascending: true)', fetch)
        devices = body(self.provider, 'static func devices(')
        self.assertIn('try store.searchDeviceNames(matching: query)', devices)
        sources = (ROOT / 'replica/Sources/PastoCore/ClipboardSourcePersistence.swift').read_text()
        self.assertIn('request.returnsDistinctResults = true', sources)
        self.assertIn('items.@count > 0', sources)

    def test_toggle_preserves_model_nodes_and_delivers_before_coordinator_normalization(self):
        model = body(self.browser, 'private final class ReplicaFilterBrowserModel:')
        toggle = body(model, 'func toggleSearchFilter(')
        for token in ['let filter = selection.queryNode', 'var nodes = query',
                      'nodes.removeAll { $0 == filter }', 'nodes.append(filter)']:
            self.assertIn(token, toggle)
        self.assertLess(toggle.index('query = nodes'), toggle.index('onQueryChanged(query)'))
        for wrong in ['firstIndex', 'normalizeSelection()', 'f_1002da16c', 'applySearchInput(', 'toolbarOwner']:
            self.assertNotIn(wrong, toggle)
        self.assertIn('query.contains(selection.queryNode)', body(model, 'func hasSearchFilter('))

    def test_editor_receives_ordered_nodes_from_real_panel_and_rejects_old_reordering(self):
        self.assertTrue(preserves_query_order(self.editor))
        old = 'func updateContents() { var nodes = selections.map(\\.queryNode); f_1002f8760(&text, into: &nodes) }'
        self.assertFalse(preserves_query_order(old))
        panel = (UI / 'PanelViews.swift').read_text()
        self.assertIn('queryNodes: state.searchQueryNodes', panel)
        update = body(self.editor, 'func updateContents(')
        self.assertIn('guard previous.nodes != nodes || previous.needsNormalization else { return }', update)
        self.assertIn('currentNodes = nodes', update)
        self.assertIn('history.f_1002f5e18(.init(nodes: nodes, selection: selection), immediate: true)', update)

    def test_activation_uses_canonical_identity_and_command_preserves_popover(self):
        visible = body(self.browser, 'private var visibleSections:')
        self.assertIn('!hideApplied || !model.hasSearchFilter($0)', visible)
        entry = body(self.browser, '@ViewBuilder private func entryView(')
        self.assertIn('applied: model.hasSearchFilter(selection)', entry)
        activate = body(self.browser, 'private func activate(')
        self.assertIn('model.toggleSearchFilter(selection)', activate)
        self.assertIn('if !NSEvent.modifierFlags.contains(.command) { close() }', activate)
        self.assertIn('if !modifierFlags.contains(.command) { close() }', activate)
        self.assertNotIn('searchFilters.remove', activate)
        self.assertNotIn('normalizeSelection()', activate)

    def test_existing_collapse_and_expansion_contracts_are_reused(self):
        visible = body(self.browser, 'private var visibleSections:')
        self.assertIn('choices.count >= 11 && !expanded.contains(section.id)', visible)
        self.assertIn('Array(choices.prefix(8))', visible)
        self.assertIn('if choices.count >= 11 { entries.append(', visible)
        activate = body(self.browser, 'private func activate(')
        expansion = body(activate, 'guard let selection = entry.selection else')
        self.assertIn('expanded.remove(entry.section)', expansion)
        self.assertIn('expanded.insert(entry.section)', expansion)
        self.assertIn('selectedIndex = nil', expansion)
        self.assertNotIn('close()', expansion)

    def test_original_fragment_and_current_production_symbols_are_bound(self):
        for row in self.report['functions']:
            address = row['function_id'].split(':')[1]
            text = (ROOT / row['original']['path']).read_text()
            start = text.index('/* Address: '+address+' |')
            end = text.find('/* Address:', start+1)
            fragment = text[start:end if end!=-1 else None].rstrip()+'\n'
            self.assertEqual(hashlib.sha256(fragment.encode()).hexdigest(), row['original']['sha256'])
            for ref in row['source_references']:
                current = (ROOT / ref['path']).read_text()
                if ref['symbol'] == '($0.rawType ?? 2) == 2 && matches($0.name, query: query)':
                    checkpoint = ROOT / '.local/p0-repair/phase-40/before' / ref['path']
                    self.assertIn(ref['symbol'], checkpoint.read_text())
                    self.assertIn('try store.searchPinboardNames(matching: query)', body(current, 'static func pinboards('))
                elif ref['symbol'] == 'OriginalSearchSuggestions.f_1002f5100(query)' and ref['path'].endswith('ReplicaSearchSuggestionSource.swift'):
                    checkpoint = ROOT / '.local/p0-repair/phase-41/before' / ref['path']
                    self.assertIn(ref['symbol'], checkpoint.read_text())
                    self.assertIn(ref['symbol'], (ROOT / 'replica/Sources/PastoCore/ClipboardSourcePersistence.swift').read_text())
                elif ref['path'].endswith('FilterBrowser.swift') and ref['symbol'] in [
                    'OriginalSearchSuggestions.f_10030f3e0("")',
                    'ReplicaSearchSuggestionSource.applications("", store: store)',
                    'ReplicaSearchSuggestionSource.devices("", store: store)',
                    'ReplicaSearchSuggestionSource.pinboards("", store: store)']:
                    frozen = ROOT / '.local/p0-repair/phase-61/before' / ref['path']
                    self.assertIn(ref['symbol'], frozen.read_text())
                    self.assertIn('filters: state.availableSearchFilters()', body(current, 'func showFilterBrowser('))
                elif ref['symbol'] == 'let sections: [ReplicaFilterBrowser.Section]':
                    checkpoint = ROOT / '.local/p0-repair/phase-60/before' / ref['path']
                    self.assertIn(ref['symbol'], checkpoint.read_text())
                    self.assertIn('@Published private(set) var sections: [ReplicaFilterBrowser.Section] = []', current)
                    self.assertIn('return [', body(current, 'private static func filterBrowserSections('))
                elif ref['path'].endswith('ReplicaUIController.swift') and ref['symbol'] in [
                    'func hasSearchFilter(', 'func toggleSearchFilter(',
                    'applySearchInput(nodes: nodes, text: query, filters: filters)']:
                    frozen = ROOT / '.local/p0-repair/phase-177/before' / ref['path']
                    self.assertIn(ref['symbol'], frozen.read_text())
                    model = body(self.browser, 'private final class ReplicaFilterBrowserModel:')
                    if ref['symbol'].startswith('func '):
                        self.assertIn(ref['symbol'], model)
                    else:
                        self.assertIn('onQueryChanged(query)', model)
                        self.assertIn('[weak searchBar] query in searchBar?.applySearchQuery(query)', self.browser)
                elif ref['path'].endswith('FilterBrowser.swift') and ref['symbol'] in ['state.hasSearchFilter($0)', 'state.toggleSearchFilter(selection)']:
                    frozen = ROOT / '.local/p0-repair/phase-177/before' / ref['path']
                    self.assertIn(ref['symbol'], frozen.read_text())
                    self.assertIn(ref['symbol'].replace('state.', 'model.'), current)
                elif ref['path'].endswith('SearchEditor.swift') and ref['symbol'] == 'private func accept(':
                    frozen = ROOT / '.local/p0-repair/phase-178/before' / ref['path']
                    self.assertIn(ref['symbol'], frozen.read_text())
                    proposal = body(current, 'private static func accept(')
                    self.assertIn('OriginalSearchSuggestions.f_1002dcca4(suggestion', proposal)
                    self.assertIn('apply(nodes)', proposal)
                    self.assertIn('Self.accept(entries[index].0, context: context, apply: applySuggestion)', current)
                elif ref['path'].endswith('SearchEditor.swift') and ref['symbol'] == 'OriginalSearchSuggestions.f_1002df190(':
                    frozen = ROOT / '.local/p0-repair/phase-180/before' / ref['path']
                    self.assertIn(ref['symbol'], frozen.read_text())
                    self.assertIn('parent.onLoadSuggestions(context)', current)
                    index = (ROOT / 'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text()
                    self.assertIn(ref['symbol'], body(index, 'func suggestions(contextNode:'))
                else:
                    self.assertIn(ref['symbol'], current)


if __name__ == '__main__':
    unittest.main()
