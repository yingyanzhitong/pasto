"""Source/ARM panel geometry, animation wrapper and captured owners; no AppKit run."""
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


class PanelTransitionAlignment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proof = json.loads((ROOT / '.local/p0-repair/phase-30/panel-transition-contract.json').read_text())
        cls.ui = (ROOT / 'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
        cls.animation = (ROOT / 'replica/Sources/PastoCore/OriginalViewAnimation.swift').read_text()
        cls.raw = (ROOT / cls.proof['binary']['path']).read_bytes()

    def native(self, a):
        r = next(r for r in self.proof['original_fragments'] if r['address'] == a)
        return original_fragment((ROOT / r['path']).read_text(), a[2:])

    def offset(self, a):
        s = next(s for s in self.proof['file_backed_segments'] if s['vmaddr'] <= a < s['vmaddr'] + s['filesize'])
        return s['fileoff'] + a - s['vmaddr']

    def word(self, a):
        return struct.unpack_from('<I', self.raw, self.offset(a))[0]

    def branch(self, a):
        word = self.word(a)
        self.assertEqual(word & 0xfc000000, 0x94000000)
        imm = word & 0x3ffffff
        if imm & (1 << 25):
            imm -= 1 << 26
        return a + 4 * imm

    def test_original_sources_and_machine_ranges_are_bound(self):
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

    def test_real_objc_selector_and_zero_display_argument_are_bound(self):
        selector = self.proof['selector']
        slot = int(selector['slot'], 16)
        target = 0x100000000 + (struct.unpack_from('<Q', self.raw, self.offset(slot))[0] & ((1 << 36) - 1))
        self.assertEqual(target, int(selector['string_address'], 16))
        p = self.offset(target)
        self.assertEqual(self.raw[p:self.raw.index(b'\0', p)].decode(), 'setFrame:display:')
        self.assertEqual(self.word(0x1000193cc), 0x52800002)  # w2 = false
        self.assertEqual(self.branch(0x1000193d0), int(selector['stub'], 16))

    def test_show_uses_current_content_height_without_preference_or_resize_guard(self):
        show = body(self.ui, 'func showPanel()')
        self.assertIn('let screenFrame = screen.frame', show)
        self.assertIn('width: screenFrame.width, height: content.frame.height), display: false)', show)
        self.assertNotIn('positionPanel()', show)
        self.assertNotIn('store.preferences.panelHeight', show)
        native = self.native('0x1000192b0')
        self.assertIn('objc_stub::frame(self_00)', native)
        self.assertIn('setFrame_display_(self,extraout_d0,param_2,uVar5,uVar11,0)', native)

    def test_content_frame_writes_follow_parent_show_and_precede_animation(self):
        show = body(self.ui, 'func showPanel()')
        order = ['mainWindowController?.showWindow(nil)', 'originalPanelScreen = screen',
                 'content.superview?.clipsToBounds = true', 'content.frame = panel.frame',
                 'content.frame.origin = NSPoint(x: 0, y: -content.frame.height)',
                 'OriginalViewAnimation.f_10021cadc(duration: 0.15']
        self.assertEqual([show.index(s) for s in order], sorted(show.index(s) for s in order))
        self.assertEqual(self.word(0x100019598), 0x6f00e400)  # zero x origin after first frame
        self.assertEqual(self.word(0x10001958c), 0x1e614008)  # negate current content height

    def test_original_show_and_close_capture_builders_retain_their_owners(self):
        stubs = parse_macho(ROOT / self.proof['binary']['path'])['stubs']
        for r in self.proof['sdk_imports']:
            self.assertEqual(stubs[r['address']], r)
        self.assertEqual(stubs['0x100bfbf70']['symbol'], '_objc_retain')
        for a in [0x100019620, 0x100019628, 0x100019ca4, 0x100019cac]:
            self.assertEqual(self.branch(a), 0x100bfbf70)
        self.assertIn('*(ID *)(puVar6 + 0x18) = unaff_x20', self.native('0x1000192b0'))
        self.assertIn('*(ID *)(puVar6 + 0x20) = self', self.native('0x100019a84'))

    def test_show_completion_holds_controller_and_window_not_weak_content(self):
        show = body(self.ui, 'func showPanel()')
        completion = show.split('completion:', 1)[1]
        self.assertIn('[self, panel]', completion)
        self.assertNotIn('weak', completion)
        order = ['guard generation == self.panelTransitionGeneration',
                 'panel.backgroundColor = .windowBackgroundColor', 'self.isPanelVisible = true',
                 'self.state.searchFocus = UUID()', 'self.panelDidShow?()']
        self.assertEqual([completion.index(s) for s in order], sorted(completion.index(s) for s in order))
        self.assertNotIn('clipsToBounds', completion)

    def test_close_completion_holds_controller_and_content_and_preserves_cleanup_order(self):
        hide = body(self.ui, 'func hidePanel()')
        completion = hide.split('completion:', 1)[1]
        self.assertIn('[self, content]', completion)
        self.assertNotIn('weak', completion)
        order = ['guard generation == self.panelTransitionGeneration', 'self.mainWindowController?.close()',
                 'self.originalPanelScreen = nil', 'self.isPanelClosing = false',
                 'self.isPanelVisible = false', 'content.superview?.clipsToBounds = true']
        self.assertEqual([completion.index(s) for s in order], sorted(completion.index(s) for s in order))

    def test_real_show_and_close_consumers_use_original_animation_wrapper(self):
        show = body(self.ui, 'func showPanel()')
        close = body(self.ui, 'func hidePanel()')
        self.assertIn('OriginalViewAnimation.f_10021cadc(duration: 0.15', show)
        self.assertIn('controlPoints: 0.2, 0.8, 0.2, 1', show)
        self.assertIn('OriginalViewAnimation.f_10021cadc(duration: 0.2', close)
        self.assertIn('OriginalViewAnimation.f_10021cf38(), animated: true', close)
        for source in [show, close]:
            self.assertNotIn('NSAnimationContext.runAnimationGroup', source)
        self.assertEqual(self.branch(0x100019ce8), 0x10021cadc)

    def test_animation_wrapper_still_delivers_sync_disabled_and_animated_completion(self):
        wrapper = body(self.animation, 'public static func f_10021cadc(')
        disabled = body(wrapper, 'if !animated')
        self.assertLess(disabled.index('animations()'), disabled.index('completion?()'))
        self.assertIn('f_10021cd10(context, duration: duration, timingFunction: timingFunction, animations: animations)', wrapper)
        self.assertIn('f_10021ce98(completion)', wrapper)
        native = self.native('0x10021cadc')
        self.assertIn('if ((param_4 & 1) == 0)', native)
        self.assertIn('NSAnimationContext::runAnimationGroup_completionHandler_', native)

    def test_ease_in_out_helper_is_original_support_without_extra_migration_count(self):
        helper = body(self.animation, 'public static func f_10021cf38()')
        self.assertIn('CAMediaTimingFunction(name: .easeInEaseOut)', helper)
        self.assertIn('PTR__kCAMediaTimingFunctionEaseInEaseOut', self.native('0x10021cf38'))
        self.assertFalse(self.proof['added_support_helper']['new_difference_record'])
        self.assertEqual(self.proof['added_support_helper']['new_migration_count'], 0)

    def test_existing_closed_state_notifications_and_callback_precede_animation(self):
        close = body(self.ui, 'func hidePanel()')
        order = ['guard panel.isVisible', 'guard !isPanelClosing', 'panelTransitionGeneration += 1',
                 'panel.makeFirstResponder(nil)', 'beginClosedState()', 'isPanelClosing = true',
                 'NotificationCenter.default.post(', 'panelWillClose?(',
                 'content.superview?.clipsToBounds = false', 'OriginalViewAnimation.f_10021cadc']
        self.assertEqual([close.index(s) for s in order], sorted(close.index(s) for s in order))

    def test_source_counterexample_and_remaining_class_contracts_are_explicit(self):
        case = self.proof['source_case']
        self.assertNotEqual(case['content_height'], case['preference_height'])
        self.assertEqual(case['after_show_height'], case['original_show_height'])
        self.assertEqual(case['after_display_flag'], case['original_display_flag'])
        self.assertNotEqual(case['before_show_capture'], case['original_show_capture'])
        self.assertEqual(case['after_show_capture'], case['original_show_capture'])
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertTrue(self.proof['retained_partial_contracts'])


if __name__ == '__main__':
    unittest.main()
