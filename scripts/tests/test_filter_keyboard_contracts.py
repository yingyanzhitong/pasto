"""Bound source and ARM64 instruction contracts; no executable or UI is run."""
import hashlib
import json
import re
import struct
import unittest
from test_offline_p0_contracts import ROOT, body

UI = ROOT / 'replica/Sources/Pasto/UI'


def branch_target(address, word):
    if word >> 26 != 0b100101:
        raise ValueError('Expected arm64 BL')
    immediate = word & ((1 << 26) - 1)
    if immediate & (1 << 25): immediate -= 1 << 26
    return address + 4 * immediate


def event_based_tab(text):
    method = body(text, 'private func handleMonitoredKey(')
    return ('OriginalNavigationKey.f_100219ddc(event)' in method
            and 'event.modifierFlags.intersection([.shift, .option])' in method
            and 'NSEvent.modifierFlags' not in method)


class FilterKeyboardContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (UI / 'FilterBrowser.swift').read_text()
        cls.keys = (UI / 'OriginalNavigationKey.swift').read_text()
        cls.report = json.loads((ROOT / 'reports/replica/offline-migration-p0-round15.json').read_text())

    def test_monitor_lifecycle_matches_presentation_and_installs_on_each_request(self):
        self.assertIn('.onAppear { focused = true; installKeyboardMonitor() }', self.source)
        self.assertIn('.onDisappear { removeKeyboardMonitor() }', self.source)
        install = body(self.source, 'private func installKeyboardMonitor()')
        self.assertNotIn('guard keyboardMonitor == nil', install)
        self.assertIn('NSEvent.addLocalMonitorForEvents(matching: .keyDown)', install)
        self.assertIn('MainActor.assumeIsolated { handleMonitoredKey(event) ? nil : event }', install)
        remove = body(self.source, 'private func removeKeyboardMonitor()')
        self.assertLess(remove.index('NSEvent.removeMonitor(keyboardMonitor)'), remove.index('keyboardMonitor = nil'))
        self.assertNotIn('addGlobalMonitor', install)

    def test_only_physical_return_and_tab_are_consumed(self):
        route = body(self.source, 'private func handleMonitoredKey(')
        self.assertEqual(re.findall(r'case \.(\w+):', route), ['enter', 'tab'])
        self.assertEqual(route.count('return true'), 2)
        self.assertIn('default: return false', route)
        self.assertNotIn('.onKeyPress(.return)', self.source)
        self.assertNotIn('.onKeyPress(.tab)', self.source)
        physical = body(self.keys, 'static func f_100219df4(')
        pairs = re.findall(r'case (0x[0-9a-f]+): return \.(\w+)', physical)
        self.assertEqual([(int(a,16),b) for a,b in pairs], [
            (36,'enter'),(48,'tab'),(49,'space'),(53,'escape'),(115,'home'),(116,'pageUp'),
            (119,'end'),(121,'pageDown'),(123,'left'),(124,'right'),(125,'down'),(126,'up')])
        self.assertIn('default: return .other', physical)
        self.assertNotIn('case 0x4c:', physical)  # The original does not classify keypad Enter as Return.

    def test_tab_uses_event_flags_and_rejects_global_state_counterexample(self):
        self.assertTrue(event_based_tab(self.source))
        self.assertFalse(event_based_tab(self.source.replace('event.modifierFlags.intersection', 'NSEvent.modifierFlags.intersection')))
        route = body(self.source, 'private func handleMonitoredKey(')
        self.assertIn('move(event.modifierFlags.intersection([.shift, .option]).isEmpty ? .right : .left)', route)

    def test_return_captures_flags_and_mouse_fallback_remains_separate(self):
        route = body(self.source, 'private func handleMonitoredKey(')
        self.assertIn('if let index = selectedIndex, allEntries.indices.contains(index)', route)
        self.assertIn('activate(allEntries[index], modifierFlags: event.modifierFlags)', route)
        activate = body(self.source, 'private func activate(')
        keyboard = body(activate, 'if let modifierFlags')
        self.assertIn('if !modifierFlags.contains(.command) { close() }', keyboard)
        self.assertNotIn('NSEvent.modifierFlags', keyboard)
        self.assertIn('else if !NSEvent.modifierFlags.contains(.command) { close() }', activate)
        self.assertLess(activate.index('model.toggleSearchFilter(selection)'), activate.index('if let modifierFlags'))
        expand = body(activate, 'guard let selection = entry.selection else')
        self.assertNotIn('close()', expand)

    def test_valid_grid_domain_reuses_original_wrap_and_incomplete_row_formulas(self):
        move = body(self.source, 'private func move(')
        for guard in ['guard total > 0 else { selectedIndex = nil; return }',
                      'guard let selectedIndex else { self.selectedIndex = 0; return }',
                      'let current = min(selectedIndex, total - 1)']:
            self.assertIn(guard, move)
        for formula in ['(current - 1 + total) % total', '(current + 1) % total',
                        'if local >= 3 { self.selectedIndex = current - 3 }',
                        'else if section == 0 { self.selectedIndex = total - 1 }',
                        '((previousCount - 1) / 3) * 3', 'min(column, (previousCount - 1) % 3)',
                        'min(current + 3, offset + count - 1)',
                        'offset + count + min(column, counts[section + 1] - 1)',
                        'else { self.selectedIndex = 0 }']:
            self.assertIn(formula, move)
        self.assertIn('let counts = visibleSections.map { $0.entries.count }', move)
        self.assertIn('private var allEntries: [Entry] { visibleSections.flatMap(\\.entries) }', self.source)

    def test_original_instructions_bind_classifier_modifier_source_and_mask(self):
        instructions = self.report['static_bindings']['instructions']
        call = instructions['physical_classifier_call']
        word, = struct.unpack('<I', bytes.fromhex(call['bytes']))
        self.assertEqual(branch_target(int(call['address'],16), word), 0x100219ddc)
        enter = instructions['enter_modifier_then_activation']
        words = struct.unpack('<4I', bytes.fromhex(enter['bytes']))
        self.assertEqual(words[0], 0xaa1303e0)  # x0 <- captured NSEvent x19
        self.assertEqual(branch_target(int(enter['address'],16)+12, words[3]), 0x100032094)
        mask = struct.unpack('<3I', bytes.fromhex(instructions['shift_option_mask']['bytes']))
        self.assertEqual(((mask[0]>>5)&65535) << (16*((mask[0]>>21)&3)), 0xa0000)
        self.assertEqual(mask[1], 0xea09001f)  # tst x0,x9: flags of this event
        self.assertEqual(self.report['static_bindings']['monitor_event_mask'], 0x400)

    def test_original_coordinate_tuple_and_clamps_are_bound_without_running_binary(self):
        instructions = self.report['static_bindings']['instructions']
        coordinates = struct.unpack('<8I', bytes.fromhex(instructions['coordinates_tuple_return']['bytes']))
        self.assertEqual(coordinates[:3], (0xd1000500, 0x9ac20d21, 0x9b02a422))  # section, row, remainder
        self.assertEqual(coordinates[4:7], (0xd2800000, 0xd2800001, 0xd2800002))  # no match -> tuple zeros
        previous = struct.unpack('<11I', bytes.fromhex(instructions['up_previous_row_column_clamp']['bytes']))
        self.assertEqual(previous[-1], 0x9a82b122)  # signed min(previous last-row column, current column)
        following = struct.unpack('<7I', bytes.fromhex(instructions['down_next_section_clamp']['bytes']))
        self.assertEqual(following[4], 0x9a96b102)  # signed min(next section count-1, current column)

    def test_original_fragments_and_real_source_consumers_remain_bound(self):
        for row in self.report['functions']:
            text = (ROOT / row['original']['path']).read_text()
            address = row['function_id'].split(':')[1]
            start = text.index('/* Address: '+address+' |');end = text.find('/* Address:',start+1)
            fragment = text[start:end if end!=-1 else None].rstrip()+'\n'
            self.assertEqual(hashlib.sha256(fragment.encode()).hexdigest(), row['original']['sha256'])
            for ref in row['source_references']:
                self.assertIn(ref['symbol'], (ROOT / ref['path']).read_text())


if __name__ == '__main__':
    unittest.main()
