"""Native collection navigation source/data contracts; no Swift or AppKit execution."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from modal_restore_scope_contract import pre_modal_restore
from test_p0_repair_checksum_routing import original_fragment


class NavigationClassifierContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-16'
        cls.proof = json.loads((cls.phase / 'navigation-root-contract.json').read_text())
        cls.ui = pre_modal_restore((ROOT / 'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text())
        cls.handle = body(cls.ui, 'private func handleKey(_ event: NSEvent)')
        cls.classifier = (ROOT / 'replica/Sources/Pasto/UI/OriginalCollectionNavigation.swift').read_text()

    def original(self, address):
        r = next(r for r in self.proof['original_fragments'] if r['address'] == address)
        return original_fragment((ROOT / r['path']).read_text(), address[2:])

    def test_original_fragments_and_machine_ranges_are_bound(self):
        for r in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / r['path'])[r['address']]['sha256'], r['sha256'])
        binary = (ROOT / self.proof['binary']['path']).read_bytes()
        self.assertEqual(hashlib.sha256(binary).hexdigest(), self.proof['binary']['sha256'])
        for r in self.proof['machine_ranges']:
            a, b = int(r['start'], 16), int(r['end'], 16)
            self.assertEqual(hashlib.sha256(binary[a - 0x100000000:b - 0x100000000]).hexdigest(), r['sha256'])

    def test_control_bit_and_original_first_boundary_result_are_literal_machine_evidence(self):
        binary = (ROOT / self.proof['binary']['path']).read_bytes()
        self.assertEqual(binary[0x234b54:0x234b58].hex(), '3f036ef2')  # tst x25,#0x40000
        self.assertEqual(binary[0x235534:0x235538].hex(), '40008052')  # mov w0,#2
        self.assertEqual(binary[0x227c18:0x227c1c].hex(), '000080d2')  # first index 0
        self.assertEqual(binary[0x227c64:0x227c68].hex(), '02008052')  # boundary animation 0

    def test_classifier_uses_original_tags_lowercase_and_supported_alias_priority(self):
        self.assertIn('case forward = 0, backward = 1, first = 2, last = 3, unhandled = 4', self.classifier)
        classify = body(self.classifier, 'static func f_1002348a8(_ event: NSEvent)')
        self.assertIn('event.charactersIgnoringModifiers?.lowercased()', classify)
        order = ['key == "f"', '.rightArrow', 'return .forward', 'key == "b"', '.leftArrow', 'return .backward',
                 'key == "e"', '.downArrow', 'return .last', 'key == "a"', '.upArrow', 'return .first', 'return .unhandled']
        positions = [classify.index(t) for t in order]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(classify.count('modifiers.contains(.control)'), 4)
        self.assertEqual(classify.count('commandModifiers.contains(.command)'), 2)
        self.assertNotIn('.option', classify)
        self.assertNotIn('.shift', classify)

    def test_command_and_control_read_separate_original_modifier_snapshots(self):
        binary = (ROOT / self.proof['binary']['path']).read_bytes()
        for pc in [0x234aec, 0x234af8]:
            instruction = int.from_bytes(binary[pc:pc + 4], 'little')
            self.assertEqual(instruction & 0xfc000000, 0x94000000)
            immediate = instruction & 0x3ffffff
            if immediate & (1 << 25):
                immediate -= 1 << 26
            self.assertEqual(0x100000000 + pc + 4 * immediate, 0x100c06e00)
        classify = body(self.classifier, 'static func f_1002348a8(_ event: NSEvent)')
        self.assertEqual(classify.count('event.modifierFlags'), 2)
        order = ['let commandModifiers = event.modifierFlags', 'let modifiers = event.modifierFlags',
                 'event.charactersIgnoringModifiers?.lowercased()', 'let specialKey = event.specialKey']
        self.assertEqual([classify.index(t) for t in order], sorted(classify.index(t) for t in order))

    def test_real_consumer_classifies_once_after_existing_editing_and_paste_routes(self):
        self.assertEqual(self.handle.count('OriginalCollectionNavigation.f_1002348a8(event)'), 1)
        order = ['return writeAppliedSelection()', 'openAppliedSelection()',
                 'revealSelectedItemInList()', 'pasteSelection(plainTextOnly: plain)',
                 'let navigation = OriginalCollectionNavigation.f_1002348a8(event)', 'switch navigation']
        positions = [self.handle.index(t) for t in order]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn('let navigation: Int', self.handle)
        self.assertNotIn('control && key ==', self.handle)

    def test_adjacent_command_mode_falls_back_and_shift_overrides_it(self):
        tail = self.handle[self.handle.index('switch navigation'):]
        order = ['case .forward, .backward:', 'OriginalOrderedSelection.mode(modifierFlags: event.modifierFlags.rawValue)',
                 'guard mode != 1 else { return false }',
                 'state.moveSelection(navigation == .forward ? 1 : -1, extending: mode == 2)']
        positions = [tail.index(t) for t in order]
        self.assertEqual(positions, sorted(positions))
        core = (ROOT / 'replica/Sources/PastoCore/OriginalOrderedSelection.swift').read_text()
        mode = body(core, 'public static func mode(modifierFlags: UInt)')
        self.assertLess(mode.index('0x20000'), mode.index('0x100000'))
        self.assertIn('return 2', mode)
        self.assertIn('? 1 : 0', mode)

    def test_boundaries_ignore_command_mode_and_keep_nonanimated_applied_selection(self):
        tail = self.handle[self.handle.index('switch navigation'):]
        self.assertIn('case .first:\n            state.moveSelectionToBoundary(last: false, extending: shift)', tail)
        self.assertIn('case .last:\n            state.moveSelectionToBoundary(last: true, extending: shift)', tail)
        boundary = body(self.ui, 'func moveSelectionToBoundary(last: Bool, extending: Bool = false)')
        self.assertIn('collectionOwner?.appliedItems(for: self)', boundary)
        self.assertIn('animated: false', boundary)
        self.assertIn('mode: extending ? 2 : 0', boundary)

    def test_control_command_a_is_not_consumed_as_select_all(self):
        before = (self.phase / 'before/replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
        self.assertIn('case "a" where !isEditing: shift ? state.deselectAll() : state.selectAll(); return true', before)
        branch = 'case "a" where !isEditing && !modifiers.contains(.control) && !modifiers.contains(.option):'
        self.assertIn(branch, self.handle)
        self.assertLess(self.handle.index(branch), self.handle.index('OriginalCollectionNavigation.f_1002348a8(event)'))
        self.assertIn('key == "a"', self.classifier)
        self.assertEqual(self.proof['source_gate_counterexample']['original'], '2348a8→2；227b54→index0/mode0/animation0')

    def test_unsupported_keys_leave_existing_fallback_and_other_consumers_unchanged(self):
        self.assertIn('case .unhandled:\n            return false', self.handle)
        for key in ['.pageUp', '.pageDown', '.home', '.end', '.tab']:
            self.assertNotIn(key, self.classifier)
        before = (self.phase / 'before/replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
        for signature in ['func selectAll()', 'func moveSelection(_ offset:', 'func moveSelectionToBoundary(last:',
                          'func pasteSelection(plainTextOnly:', 'func showPreview(item:', 'private func openAppliedSelection()']:
            expected = body(before, signature)
            if signature == 'func showPreview(item:':
                lazy_before = (ROOT / '.local/p0-repair/phase-29/before/replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
                self.assertEqual(expected, body(lazy_before, signature))
                expected = expected.replace('if panel.isVisible, !isPanelClosing',
                                            'if isPanelOrderedVisible, !isPanelClosing')
            self.assertEqual(expected, body(self.ui, signature))


if __name__ == '__main__':
    unittest.main()
