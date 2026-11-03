"""Published lifecycle and original real Stack-shortcut consumer; static only."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from macho_imports import parse_macho
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment


class PanelVisibilityShortcut(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proof = json.loads((ROOT / '.local/p0-repair/phase-28/panel-visibility-contract.json').read_text())
        cls.ui = (ROOT / 'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
        cls.app = (ROOT / 'replica/Sources/Pasto/AppMain.swift').read_text()
        cls.raw = (ROOT / cls.proof['binary']['path']).read_bytes()

    def offset(self, a):
        s = next(s for s in self.proof['file_backed_segments'] if s['vmaddr'] <= a < s['vmaddr'] + s['filesize'])
        return s['fileoff'] + a - s['vmaddr']

    def relative(self, a):
        return a + struct.unpack_from('<i', self.raw, self.offset(a))[0]

    def string(self, a):
        p = self.offset(a)
        return self.raw[p:self.raw.index(b'\0', p)].decode()

    def native(self, address):
        r = next(r for r in self.proof['original_fragments'] if r['address'] == address)
        return original_fragment((ROOT / r['path']).read_text(), address[2:])

    def test_original_fragments_and_machine_bytes_are_bound(self):
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(), self.proof['binary']['sha256'])
        for r in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / r['path'])[r['address']]['sha256'], r['sha256'])
        for r in self.proof['machine_ranges']:
            self.assertEqual(self.offset(int(r['start'], 16)), r['file_offset'])
            raw = self.raw[r['file_offset']:r['file_offset'] + r['length']]
            self.assertEqual(raw.hex(), r['hex'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), r['sha256'])
            if 'instruction_count' in r:
                self.assertEqual(r['instruction_count'], r['length'] // 4)

    def test_field128_is_stack_shortcut_from_real_class_descriptor_and_offset_vector(self):
        c = self.proof['class_binding']
        descriptor = int(c['descriptor'], 16)
        self.assertEqual(self.string(self.relative(descriptor + 8)), 'AppCoordinator')
        self.assertEqual(self.relative(descriptor + 16), int(c['field_descriptor'], 16))
        metadata = int(c['metadata'], 16)
        ptr = 0x100000000 + (struct.unpack_from('<Q', self.raw, self.offset(metadata + 64))[0] & ((1 << 36) - 1))
        self.assertEqual(ptr, descriptor)
        for r in c['fields']:
            self.assertEqual(self.string(self.relative(int(r['field_record_address'], 16) + 8)), r['name'])
            actual = struct.unpack_from('<Q', self.raw, self.offset(int(c['field_vector'], 16) + r['index'] * 8))[0]
            self.assertEqual(actual, r['instance_offset'])
        self.assertEqual((c['fields'][26]['name'], c['fields'][26]['instance_offset']), ('_activationShortcut', 0xf0))
        self.assertEqual((c['fields'][27]['name'], c['fields'][27]['instance_offset']), ('_pasteStackShortcut', 0x128))

    def test_actual_published_projection_and_sink_imports_are_bound(self):
        stubs = parse_macho(ROOT / self.proof['binary']['path'])['stubs']
        for r in self.proof['sdk_imports']:
            self.assertEqual(stubs[r['address']], r)
        self.assertIn('projectedValue', stubs['0x100bf555c']['symbol'])
        self.assertIn('sink', stubs['0x100bf5658']['symbol'])
        self.assertIn('FUN_1000a8378()', self.native('0x1000a9970'))

    def test_visibility_initial_false_and_true_published_before_focus_and_didshow(self):
        self.assertIn('@Published private(set) var isPanelVisible = false', self.ui)
        native = self.native('0x1000187d0')
        self.assertIn('local_61 = 0', native)
        self.assertIn('Combine::Published::init', native)
        completion = body(self.ui, 'func showPanel()').split('completion:', 1)[1]
        order = ['generation == self.panelTransitionGeneration', 'panel.backgroundColor = .windowBackgroundColor',
                 'self.isPanelVisible = true', 'self.state.searchFocus = UUID()', 'self.panelDidShow?()']
        self.assertEqual([completion.index(s) for s in order], sorted(completion.index(s) for s in order))
        original = self.native('0x100019790')
        self.assertLess(original.index('local_51 = 1'), original.index('Combine::Published::_set_subscript'))
        self.assertLess(original.index('Combine::Published::_set_subscript'), original.index('FUN_10000cd7c'))
        self.assertLess(original.index('FUN_10000cd7c'), original.index('::onDidShow'))

    def test_close_publishes_false_after_cleanup_only_in_current_generation_completion(self):
        close = body(self.ui, 'func hidePanel()')
        before, completion = close.split('completion:', 1)
        self.assertNotIn('isPanelVisible = false', before)
        order = ['generation == self.panelTransitionGeneration', 'self.mainWindowController?.close()', 'self.originalPanelScreen = nil',
                 'self.isPanelClosing = false', 'self.isPanelVisible = false', 'content.superview?.clipsToBounds = true']
        self.assertEqual([completion.index(s) for s in order], sorted(completion.index(s) for s in order))
        original = self.native('0x100019e2c')
        self.assertLess(original.index('::closing) = 0'), original.index('local_51 = 0'))
        self.assertLess(original.index('local_51 = 0'), original.index('Combine::Published::_set_subscript'))

    def test_original_consumer_registers_when_hidden_and_unregisters_when_visible(self):
        native = self.native('0x1000a8378')
        self.assertIn('param_2 + 0x128', native)
        self.assertIn("if (local_a8 != '\\x01')", native)
        self.assertIn("if (cVar1 == '\\0')", native)
        self.assertLess(native.index('FUN_1001eaa64('), native.index('FUN_1001eae90('))
        consumer = body(self.app, 'private func panelVisibilityChanged(_ visible: Bool)')
        self.assertIn('guard let shortcut = store.preferences.stackShortcut else { return }', consumer)
        self.assertIn('if visible {\n            stackHotKey.unregister()', consumer)
        self.assertIn('stackHotKey.register(keyCode: shortcut.keyCode, modifiers: shortcut.modifiers, identifier: 2)', consumer)
        self.assertNotIn('hotKey.unregister()', consumer)
        self.assertNotIn('stackPasteHotKey', consumer)
        self.assertNotIn('historyShortcut', consumer)

    def test_real_sink_consumes_emitted_value_without_willset_storage_reread(self):
        sink = body(self.app, 'private func installPanelVisibilityObservation()')
        self.assertIn('[weak self] visible in', sink)
        self.assertIn('self?.panelVisibilityChanged(visible)', sink)
        self.assertNotIn('ui.isPanelVisible', sink)
        self.assertNotIn('removeDuplicates', sink)
        self.assertNotIn('DispatchQueue', sink)
        self.assertIn('private var panelVisibilityObservation: AnyCancellable?', self.app)

    def test_toggle_still_uses_native_visibility_and_closing_not_published_state(self):
        toggle = body(self.ui, 'func togglePanel()')
        self.assertIn('isPanelOrderedVisible && !isPanelClosing ? hidePanel() : showPanel()', toggle)
        self.assertIn('loadedPanel?.isVisible == true', body(self.ui, 'var isPanelOrderedVisible: Bool'))
        self.assertNotIn('isPanelVisible', toggle)
        native = self.native('0x1000a5300')
        self.assertIn('objc_stub::isVisible(IVar1)', native)
        self.assertIn('MainWindowController::closing', native)
        self.assertNotIn('Published', native)

    def test_existing_recording_and_disabled_hotkey_policies_are_retained(self):
        consumer = body(self.app, 'private func panelVisibilityChanged(_ visible: Bool)')
        self.assertIn('!isRecordingHotKey, !arguments.contains("--no-global-hotkey")', consumer)
        self.assertIn('shortcut.isValidGlobal', consumer)
        self.assertIn('OSStatus(-50)', consumer)
        self.assertIn('updateStatus()', consumer)
        self.assertTrue(any('lazy' in s for s in self.proof['retained_partial_contracts']))

    def test_pending_show_and_close_visibility_event_case_is_finite_and_not_runtime_claim(self):
        case = self.proof['counterexample']
        self.assertEqual(case['original_visibility'], [False, False, True, True, False])
        self.assertEqual(case['after_stack_registered'], case['original_stack_registered'])
        self.assertNotEqual(case['before_stack_registered'], case['original_stack_registered'])
        self.assertFalse(self.proof['full_function_migration_verified'])


if __name__ == '__main__':
    unittest.main()
