"""First panel construction and observation: C/ARM/static production paths only."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from macho_imports import _chained_bindings
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment


class LazyPanelController(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proof = json.loads((ROOT / '.local/p0-repair/phase-29/lazy-panel-contract.json').read_text())
        cls.ui = (ROOT / 'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
        cls.app = (ROOT / 'replica/Sources/Pasto/AppMain.swift').read_text()
        cls.raw = (ROOT / cls.proof['binary']['path']).read_bytes()

    def native(self, a):
        r = next(r for r in self.proof['original_fragments'] if r['address'] == a)
        return original_fragment((ROOT / r['path']).read_text(), a[2:])

    def offset(self, a):
        s = next(s for s in self.proof['file_backed_segments'] if s['vmaddr'] <= a < s['vmaddr'] + s['filesize'])
        return s['fileoff'] + a - s['vmaddr']

    def test_original_fragment_and_machine_data_hashes_are_bound(self):
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

    def test_actual_main_controller_superclass_is_appkit_not_a_guessed_name(self):
        ref = self.proof['superclass_proof']
        self.assertEqual(hashlib.sha256((ROOT / ref['path']).read_bytes()).hexdigest(), ref['sha256'])
        p = json.loads((ROOT / ref['path']).read_text())
        bindings, _ = _chained_bindings(self.raw, p['chained_range'], p['segments'], p['dylibs'])
        self.assertEqual(bindings[int(p['superclass_slot'], 16)], p['binding'])
        self.assertEqual(p['binding']['symbol'], '_OBJC_CLASS_$_NSWindowController')
        self.assertIn('AppKit.framework', p['binding']['dylib']['install_name'])
        descriptor = 0x100000000 + (struct.unpack_from('<Q', self.raw, self.offset(int(p['class_metadata'], 16) + 64))[0] & ((1 << 36) - 1))
        self.assertEqual(descriptor, int(p['class_descriptor'], 16))

    def test_original_modal_gate_precedes_lazy_controller_and_subscription(self):
        source = self.native('0x1000a56f4')
        order = ['objc_stub::modalWindow(', 'objc_stub::activateIgnoringOtherApps_',
                 'IVar6 = *(ID *)(unaff_x20 + 0xd0)', 'if (IVar6 == 0)',
                 '::onDidShow', '::onWillClose', 'Combine::Published::_get_projectedValue',
                 'Publisher::_sink()', 'FUN_1000192b0(']
        self.assertEqual([source.index(s) for s in order], sorted(source.index(s) for s in order))

    def test_ui_init_and_appearance_do_not_load_native_window(self):
        init = body(self.ui[self.ui.index('final class ReplicaUIController'):], 'init(store: ClipboardStore)')
        for forbidden in ['ReplicaPanel(', 'NSWindowController(', 'NSHostingView(', 'restorePanelFrame()', 'loadPanel()']:
            self.assertNotIn(forbidden, init)
        appearance = body(self.ui, 'private func applyAppearance()')
        self.assertIn('loadedPanel?.appearance = appearance', appearance)
        self.assertIn('if isPanelOrderedVisible { positionPanel() }', appearance)
        self.assertNotIn('panel.appearance', appearance)

    def test_first_load_caches_native_objects_before_reentrant_setup_or_hook(self):
        load = body(self.ui, 'private func loadPanel() -> NSPanel')
        order = ['if let loadedPanel { return loadedPanel }', 'let panel = ReplicaPanel(',
                 'loadedPanel = panel', 'mainWindowController = NSWindowController(window: panel)',
                 'let hosting = NSHostingView(', 'panel.keyHandler =', 'panelDidLoad?()', 'return panel']
        self.assertEqual([load.index(s) for s in order], sorted(load.index(s) for s in order))
        self.assertEqual(load.count('panelDidLoad?()'), 1)
        self.assertEqual(self.ui.count('NSWindowController(window: panel)'), 1)

    def test_actual_load_hook_installs_visibility_sink_without_startup_registration(self):
        self.assertIn('ui.panelDidLoad = { [weak self] in self?.installPanelVisibilityObservation() }', self.app)
        self.assertEqual(self.app.count('installPanelVisibilityObservation()'), 2)
        sink = body(self.app, 'private func installPanelVisibilityObservation()')
        self.assertIn('panelVisibilityObservation = ui.$isPanelVisible.sink', sink)
        self.assertIn('self?.panelVisibilityChanged(visible)', sink)
        self.assertEqual(self.app.count('panelVisibilityObservation = ui.$isPanelVisible.sink'), 1)

    def test_modal_show_never_reaches_loading_and_parent_show_is_used(self):
        show = body(self.ui, 'func showPanel()')
        modal = body(show, 'guard NSApp.modalWindow == nil else')
        self.assertIn('NSApp.activate(ignoringOtherApps: true)', modal)
        self.assertIn('return', modal)
        self.assertNotIn('self.panel', modal)
        order = ['guard NSApp.modalWindow == nil', 'let panel = self.panel',
                 'guard let screen', 'cancelClosedState()', 'mainWindowController?.showWindow(nil)']
        self.assertEqual([show.index(s) for s in order], sorted(show.index(s) for s in order))
        self.assertNotIn('panel.makeKeyAndOrderFront', show)
        self.assertIn('"showWindow:"', self.native('0x1000192b0'))

    def test_hide_before_load_is_noop_and_completion_uses_parent_close(self):
        hide = body(self.ui, 'func hidePanel()')
        self.assertLess(hide.index('guard let panel = loadedPanel'), hide.index('guard panel.isVisible'))
        completion = hide.split('completion:', 1)[1]
        self.assertLess(completion.index('generation == self.panelTransitionGeneration'), completion.index('self.mainWindowController?.close()'))
        self.assertLess(completion.index('self.mainWindowController?.close()'), completion.index('self.isPanelVisible = false'))
        self.assertIn('"close"', self.native('0x100019e2c'))

    def test_status_key_target_and_responder_queries_do_not_force_panel_loading(self):
        for signature in ['var isPanelOrderedVisible: Bool', 'var isPanelKeyWindow: Bool',
                          'fileprivate func clearPanelFirstResponder()', 'private func appliedCollectionItems()']:
            source = body(self.ui, signature)
            self.assertIn('loadedPanel', source)
            self.assertNotIn('loadPanel()', source)
        self.assertNotIn('ui.panel.isVisible', self.app)
        self.assertNotIn('ui.panel.isKeyWindow', self.app)
        self.assertIn('guard !ui.isPanelOrderedVisible else { return }', self.app)

    def test_existing_native_factory_configuration_is_preserved_after_extraction(self):
        load = body(self.ui, 'private func loadPanel() -> NSPanel')
        for token in ['panel.isReleasedWhenClosed = false', 'panel.contentView = content',
                      'panel.delegate = panel', 'panel.closeRequested =', 'restorePanelFrame()',
                      'installPanelResizeHandle()', 'sharingPolicy.apply(to: panel)', 'applyAppearance()']:
            self.assertIn(token, load)
        self.assertIn('state.controller = self', self.ui)
        self.assertIn('preferenceObservation = store.$preferences.sink', self.ui)

    def test_startup_modal_first_show_and_reuse_cases_are_not_runtime_claims(self):
        case = self.proof['counterexample']
        self.assertEqual(case['original_controller_creation_counts'], [0, 0, 0, 1, 1])
        self.assertEqual(case['original_visibility_subscription_counts'], [0, 0, 0, 1, 1])
        self.assertEqual(case['after_controller_creation_counts'], case['original_controller_creation_counts'])
        self.assertEqual(case['after_visibility_subscription_counts'], case['original_visibility_subscription_counts'])
        self.assertNotEqual(case['before_controller_creation_counts'], case['original_controller_creation_counts'])

    def test_original_full_state_model_and_abi_are_still_partial(self):
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertTrue(any('ReplicaUIState' in s for s in self.proof['retained_partial_contracts']))
        self.assertTrue(any('ABI' in s for s in self.proof['retained_partial_contracts']))
        self.assertEqual(self.proof['contracts'][0]['function_id'], 'Paste:0x1000a56f4')


if __name__ == '__main__':
    unittest.main()
