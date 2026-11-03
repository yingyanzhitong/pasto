"""Writing Tools source/data checks; no Framework or Swift execution."""
import hashlib
from edit_entity_input_scope_contract import pre_edit_entity_input
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from macho_imports import parse_macho
from test_offline_p0_contracts import body


class WritingToolsContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-11'
        cls.ui = pre_edit_entity_input((ROOT / 'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text())
        cls.tools = (ROOT / 'replica/Sources/PastoCore/OriginalWritingTools.swift').read_text()
        cls.write = body(cls.ui, 'private func writeAppliedSelection() -> Bool')
        cls.proof = json.loads((cls.phase / 'writing-tools-root-contract.json').read_text())

    def test_canonical_fragments_and_sdk_inputs_are_bound(self):
        for name in ['writing-tools-contract.json', 'writing-tools-machine-proof.json']:
            proof = json.loads((self.phase / name).read_text())
            for record in proof['original_fragments']:
                self.assertEqual(source_fragments(ROOT / record['path'])[record['address']]['sha256'],
                                 record['sha256'], (name, record['address']))
        for record in self.proof['sdk_bindings']:
            self.assertEqual(hashlib.sha256((ROOT / record['path']).read_bytes()).hexdigest(), record['sha256'])

    def test_machine_ranges_bind_zero_argument_task_copy_and_both_continuations(self):
        proof = json.loads((self.phase / 'writing-tools-machine-proof.json').read_text())
        binary = (ROOT / proof['binary']['path']).read_bytes()
        self.assertEqual(hashlib.sha256(binary).hexdigest(), proof['binary']['sha256'])
        for record in proof['machine_ranges']:
            actual = binary[record['file_offset']:record['file_offset'] + record['length']]
            self.assertEqual(actual.hex(), record['hex'], record['name'])
            self.assertEqual(hashlib.sha256(actual).hexdigest(), record['sha256'])
        names = {r['name'] for r in proof['machine_ranges']}
        self.assertTrue({'shortcut_zero_buffer_and_call', 'task_box_copies_input',
                         'success_continuation_nil_sender', 'error_continuation_nil_sender'} <= names)

    def test_availability_uses_frozen_single_payload_shape_and_exact_imports(self):
        interface = self.proof['availability_interface']
        self.assertIn('@frozen public enum Availability', interface)
        self.assertIn('case available', interface)
        self.assertIn('case unavailable(FoundationModels.SystemLanguageModel.Availability.UnavailableReason)', interface)
        stubs = parse_macho(ROOT / '.local/paste-arm64-static.bin')['stubs']
        for address, record in self.proof['import_bindings'].items():
            self.assertEqual(stubs[address]['symbol'], record['symbol'])
            self.assertEqual(stubs[address]['body_hex'], record['body_hex'])
            self.assertEqual(stubs[address]['pointer_raw_value'], record['pointer_raw'])
        self.assertIn('UnavailableReasonOMa', stubs['0x100bf4fe0']['symbol'])
        self.assertIn('AvailabilityO2eeoiySb', stubs['0x100bf4fec']['symbol'])

    def test_current_capability_checks_model_on_26_and_selector_on_15_point_2(self):
        available = body(self.tools, 'public static func isAvailable() -> Bool')
        order = ['if #available(macOS 26, *)', 'SystemLanguageModel.default.availability == .available',
                 'guard #available(macOS 15.2, *) else { return false }',
                 'NSText.instancesRespond(to: NSSelectorFromString("showWritingTools:"))']
        positions = [available.index(t) for t in order]
        self.assertEqual(positions, sorted(positions))
        self.assertIn('#if canImport(FoundationModels)', self.tools)
        self.assertNotIn('LanguageModelSession', self.tools)

    def test_shortcut_is_exact_command_shift_e_after_collection_owner_gate(self):
        handle = body(self.ui, 'private func handleKey(_ event: NSEvent) -> Bool')
        signature = ('if !isEditing, signature.keyCode == OriginalShortcutFunctions.f_1001e94d4("e"),\n'
                     '           signature.modifierRawValue == NSEvent.ModifierFlags.command.union(.shift).rawValue')
        branch = body(handle, signature)
        self.assertIn('return writeAppliedSelection()', branch)
        self.assertLess(handle.index('if !ownsCollectionFocus'), handle.index(signature))

    def test_capability_failure_returns_before_reading_selection(self):
        order = ['guard OriginalWritingTools.isAvailable() else { return false }',
                 'appliedSelectionItems().filter']
        self.assertLess(self.write.index(order[0]), self.write.index(order[1]))
        self.assertNotIn('state.selectedItems', self.write)
        self.assertNotIn('visibleItems', self.write)

    def test_text_only_selection_guard_is_silent_and_precedes_routing(self):
        self.assertIn('Self.allowsContentEditing($0) && ($0.kind == .text || $0.kind == .richText)', self.write)
        self.assertLess(self.write.index('guard !items.isEmpty else { return false }'),
                        self.write.index('editItems(items)'))
        self.assertNotIn('beep', self.write)

    def test_routing_and_second_eligibility_filter_precede_scheduling(self):
        order = ['editItems(items)', 'OriginalWritingTools.showAfterDelay()', 'return true']
        positions = [self.write.index(t) for t in order]
        self.assertEqual(positions, sorted(positions))
        edit = body(self.ui, 'private func editItems(_ items: [ClipboardItem])')
        self.assertIn('items.filter(Self.allowsContentEditing)', edit)
        self.assertIn('for item in editable { presentEditingPreview(item: item) }', edit)

    def test_task_uses_continuous_clock_and_does_not_suppress_action_on_cancel_or_error(self):
        task = body(self.tools, 'public static func showAfterDelay()')
        order = ['Task { @MainActor in', 'try? await ContinuousClock().sleep(for: .milliseconds(500))',
                 'if #available(macOS 15.2, *)',
                 'NSApp.sendAction(NSSelectorFromString("showWritingTools:"), to: nil, from: nil)']
        positions = [task.index(t) for t in order]
        self.assertEqual(positions, sorted(positions))
        for token in ['Task.isCancelled', '[weak self]', 'NSApp.activate', 'makeFirstResponder', 'return']:
            self.assertNotIn(token, task)

    def test_original_success_and_error_resume_both_send_the_system_action(self):
        proof = json.loads((self.phase / 'writing-tools-machine-proof.json').read_text())
        for address in ['0x1002163c4', '0x1002164e8']:
            record = next(r for r in proof['original_fragments'] if r['address'] == address)
            text = (ROOT / record['path']).read_text()
            start = text.index('/* Address: ' + address + ' |')
            end = text.find('/* Address:', start + 1)
            original = text[start:end if end >= 0 else None]
            self.assertIn('"showWritingTools:"', original)
            self.assertIn('sendAction_to_from_', original)
            self.assertIn('_stdlib_isOSVersionAtLeast(0xf,2,0)', original)


if __name__ == '__main__':
    unittest.main()
