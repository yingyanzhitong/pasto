"""Show-completion focus contracts; inspect sources, never invoke AppKit."""
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body


class DidShowFocusContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ui = (ROOT / 'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
        cls.app = (ROOT / 'replica/Sources/Pasto/AppMain.swift').read_text()
        cls.show = body(cls.ui, 'func showPanel()')
        cls.proof = json.loads((ROOT / '.local/p0-repair/phase-10/didshow-focus-proof.json').read_text())

    def original(self, address):
        record = next(r for r in self.proof['original_fragments'] if r['address'] == address)
        text = (ROOT / record['path']).read_text()
        start = text.index('/* Address: ' + address + ' |')
        end = text.find('/* Address:', start + 1)
        return text[start:end if end >= 0 else None]

    def test_original_callback_chain_is_bound(self):
        for record in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / record['path'])[record['address']]['sha256'],
                             record['sha256'], record['address'])
        self.assertIn('FUN_1000a8280()', self.original('0x1000a9960'))
        self.assertIn('pcVar1 = *(code **)(param_1 + 0x78)', self.original('0x1000a8280'))
        self.assertIn('*(code **)(lVar6 + 0x78) = FUN_1000b2630', self.original('0x1000b07f0'))
        self.assertIn('FUN_1000b098c()', self.original('0x1000b2630'))

    def test_original_samples_frontmost_before_activation_after_show_completion(self):
        original = self.original('0x1000b098c')
        order = ['NSWorkspace::frontmostApplication(', '::handoffPreviousApp) = IVar3',
                 'objc_stub::activate(']
        positions = [original.index(t) for t in order]
        self.assertEqual(positions, sorted(positions))
        completion = self.original('0x100019790')
        self.assertLess(completion.index('::transitionGeneration'), completion.index('::onDidShow'))
        self.assertLess(completion.index('Combine::Published::_set_subscript'), completion.index('::onDidShow'))
        self.assertNotIn('objc_stub::activate', self.original('0x1000192b0'))

    def test_original_show_duration_is_point_fifteen(self):
        original = self.original('0x1000192b0')
        self.assertIn('FUN_10021cadc(0x3fc3333333333333', original)
        self.assertEqual(struct.unpack('<d', struct.pack('<Q', 0x3fc3333333333333))[0], 0.15)
        self.assertIn('OriginalViewAnimation.f_10021cadc(duration: 0.15', self.show)

    def test_normal_show_does_not_activate_before_completion(self):
        modal = body(self.show, 'guard NSApp.modalWindow == nil else')
        self.assertIn('NSApp.activate(ignoringOtherApps: true)', modal)
        self.assertIn('return', modal)
        normal = self.show[self.show.index('guard let screen'):]
        self.assertNotIn('NSApp.activate', normal)
        self.assertNotIn('panelWillShow', self.ui)
        self.assertIn('styleMask: [.borderless, .nonactivatingPanel]', self.ui)

    def test_didshow_runs_once_only_in_current_generation_completion_after_focus(self):
        completion = self.show[self.show.index('completion:'):]
        order = ['guard generation == self.panelTransitionGeneration',
                 'panel.backgroundColor = .windowBackgroundColor',
                 'self.state.searchFocus = UUID()', 'self.panelDidShow?()']
        positions = [completion.index(t) for t in order]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(self.show.count('panelDidShow?()'), 1)
        self.assertNotIn('panelDidShow', self.show[:self.show.index('completion:')])

    def test_actual_consumer_samples_then_activates_without_old_target_fallback(self):
        self.assertIn('ui.panelDidShow = { [weak self] in self?.rememberPanelApplication() }', self.app)
        remember = body(self.app, 'private func rememberPanelApplication()')
        order = ['NSWorkspace.shared.frontmostApplication',
                 'if app?.processIdentifier != ProcessInfo.processInfo.processIdentifier',
                 'handoffPreviousApplication = app', 'NSApp.activate()']
        positions = [remember.index(t) for t in order]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn('targetApplication', remember)
        self.assertNotIn('activate(ignoringOtherApps:', remember)

    def test_sdk_supports_the_exact_activation_selector_at_app_minimum(self):
        header = ROOT / '.local/toolchains/xcode-26.5/sdk/Payload/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk/System/Library/Frameworks/AppKit.framework/Versions/C/Headers/NSApplication.h'
        self.assertIn('- (void)activate API_AVAILABLE(macos(14.0));', header.read_text())
        self.assertIn('platforms: [.macOS(.v14)]', (ROOT / 'replica/Package.swift').read_text())

    def test_close_before_show_completion_invalidates_the_callback(self):
        close = body(self.ui, 'func hidePanel()')
        self.assertIn('panelTransitionGeneration += 1', close)
        self.assertIn('generation == self.panelTransitionGeneration', self.show)
        self.assertIn('ui.panelWillClose = { [weak self] restore in self?.restorePanelApplication(restore: restore) }', self.app)
        self.assertIn('panelWillClose?(previewRegistry.windows.isEmpty)', close)

    def test_saved_old_source_has_the_actual_early_activation_and_hook(self):
        previous = (ROOT / '.local/p0-repair/phase-10/before/replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
        old = body(previous, 'func showPanel()')
        self.assertLess(old.index('panelWillShow?()'), old.index('panel.makeKeyAndOrderFront(nil)'))
        self.assertLess(old.index('NSApp.activate(ignoringOtherApps: true)', old.index('guard let screen')),
                        old.index('NSAnimationContext.runAnimationGroup'))


if __name__ == '__main__':
    unittest.main()
