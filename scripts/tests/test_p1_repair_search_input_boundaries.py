"""Source/SDK contracts only. No AppKit, Timer or Task execution."""
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from filter_model_query_scope_contract import pre_filter_model_query
from test_p0_repair_checksum_routing import original_fragment


class SearchInputBoundaryContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-39'
        cls.core = ROOT / 'replica/Sources/PastoCore'
        cls.scroller = (cls.core / 'OriginalSearchTextScroller.swift').read_text()
        cls.text = (cls.core / 'OriginalSearchTextView.swift').read_text()
        cls.history = (cls.core / 'OriginalSearchInputHistory.swift').read_text()
        cls.browser = (ROOT / 'replica/Sources/Pasto/UI/FilterBrowser.swift').read_text()
        cls.proof = json.loads((cls.phase / 'search-input-boundaries-contract.json').read_text())

    def before(self, relative):
        return (self.phase / 'before' / relative).read_text()

    def test_original_controls_both_set_exterior_raw_value_two(self):
        original = (ROOT / 'decompiled/Paste/part-0025.c').read_text()
        self.assertIn('setFocusRingType_(self,2)', original_fragment(original, '100042edc'))
        self.assertIn('setFocusRingType_(unaff_x20,2)', original_fragment(original, '100042fc8'))
        header = Path(self.proof['sdk_focus_ring']['path'])
        self.assertEqual(hashlib.sha256(header.read_bytes()).hexdigest(), self.proof['sdk_focus_ring']['sha256'])
        self.assertIn('NSFocusRingTypeExterior = 2', header.read_text())
        self.assertIn('NSFocusRingTypeNone = 1', header.read_text())

    def test_actual_scroller_and_text_view_use_exterior(self):
        self.assertIn('focusRingType = .exterior', body(self.scroller, 'public init(textView: OriginalSearchTextView)'))
        self.assertIn('focusRingType = .exterior', body(self.text, 'public func f_100042fc8()'))

    def test_control_configuration_changes_are_exactly_one_enum_each(self):
        for name, current in [('OriginalSearchTextScroller.swift', self.scroller), ('OriginalSearchTextView.swift', self.text)]:
            previous = self.before('replica/Sources/PastoCore/' + name)
            self.assertEqual(previous.count('focusRingType = .none'), 1)
            self.assertEqual(current, previous.replace('focusRingType = .none', 'focusRingType = .exterior', 1))

    def test_real_textkit_constructors_and_configuration_consumer_are_retained(self):
        input_view = (self.core / 'OriginalSearchInputView.swift').read_text()
        editor = (ROOT / 'replica/Sources/Pasto/UI/SearchEditor.swift').read_text()
        self.assertIn('OriginalSearchTextView(usingTextLayoutManager: true)', input_view)
        self.assertIn('SearchTextView(usingTextLayoutManager: true)', editor)
        self.assertIn('textView.f_100042fc8()', body(self.scroller, 'public init(textView:'))
        self.assertEqual(input_view, self.before('replica/Sources/PastoCore/OriginalSearchInputView.swift'))
        self.assertEqual(body(editor, 'func makeField(coordinator:'), body(self.before('replica/Sources/Pasto/UI/SearchEditor.swift'), 'func makeField(coordinator:'))

    def test_original_keyboard_monitor_always_registers_then_stores_returned_token(self):
        original = original_fragment((ROOT / 'decompiled/Paste/part-0019.c').read_text(), '100031978')
        self.assertIn('0x400,aBlock', original)
        self.assertLess(original.index('addLocalMonitorForEventsMatchingMask_handler_'), original.index('State::set_wrappedValue'))
        self.assertNotIn('State::get_wrappedValue', original)

    def test_actual_keyboard_install_has_no_old_token_read_or_early_return(self):
        install = body(self.browser, 'private func installKeyboardMonitor()')
        self.assertIn('keyboardMonitor = NSEvent.addLocalMonitorForEvents(matching: .keyDown)', install)
        prefix = install[:install.index('keyboardMonitor = NSEvent.addLocalMonitorForEvents')]
        self.assertNotIn('keyboardMonitor', prefix)
        self.assertNotIn('return', prefix)
        self.assertIn('MainActor.assumeIsolated { handleMonitoredKey(event) ? nil : event }', install)

    def test_keyboard_only_removes_duplicate_gate_without_changing_filter_behavior(self):
        before = self.before('replica/Sources/Pasto/UI/FilterBrowser.swift')
        checkpoint = (ROOT / '.local/p0-repair/phase-40/before/replica/Sources/Pasto/UI/FilterBrowser.swift').read_text()
        self.assertEqual(checkpoint, before.replace('        guard keyboardMonitor == nil else { return }\n', '', 1))
        self.assertIn('.onAppear { focused = true; installKeyboardMonitor() }', self.browser)
        self.assertIn('.onDisappear { removeKeyboardMonitor() }', self.browser)
        for signature in ['private func removeKeyboardMonitor()', 'private func handleMonitoredKey(', 'private func activate(', 'private func move(']:
            self.assertEqual(body(pre_filter_model_query(self.browser), signature), body(before, signature))
        self.assertEqual(body(self.browser, 'private func installKeyboardMonitor()'), body(checkpoint, 'private func installKeyboardMonitor()'))

    def test_original_timer_is_weak_and_one_shot_but_its_task_owns_the_owner(self):
        original = (ROOT / 'decompiled/Paste/part-0244.c').read_text()
        timer = original_fragment(original, '1002f60fc')
        task = original_fragment(original, '1002f65e0')
        thunk = original_fragment(original, '1002f6f0c')
        self.assertIn('_swift_weakInit(', timer)
        self.assertIn('local_50 = FUN_1002f6f0c', timer)
        self.assertIn('uVar3,0,aBlock', timer)
        self.assertIn('FUN_1002f65e0();', thunk)
        self.assertLess(task.index('_swift_retain()'), task.index('0x20) = param_2'))
        self.assertLess(task.index('0x20) = param_2'), task.index('FUN_1002d6558('))

    def test_actual_timer_weakly_loads_before_scheduling_a_strong_mainactor_task(self):
        timer = body(self.history, 'public func f_1002f60fc()')
        order = ['timer?.invalidate()', 'Timer.scheduledTimer(withTimeInterval: interval, repeats: false) { [weak self]',
                 'guard let self else { return }', 'Task { @MainActor [self] in self.f_1002f5fe8() }']
        self.assertEqual([timer.index(t) for t in order], sorted(timer.index(t) for t in order))
        self.assertNotIn('Task { @MainActor [weak self]', timer)

    def test_timer_fix_does_not_flush_early_change_history_or_make_timer_own_self(self):
        before = self.before('replica/Sources/PastoCore/OriginalSearchInputHistory.swift')
        old = '            Task { @MainActor [weak self] in self?.f_1002f5fe8() }'
        new = '            guard let self else { return }\n            Task { @MainActor [self] in self.f_1002f5fe8() }'
        self.assertEqual(self.history, before.replace(old, new, 1))
        for signature in ['public func f_1002f5e18(', 'public func f_1002f5fe8()', 'public func f_1002f61f0()', 'public func f_1002f63b8()', 'public func f_1002f6550()']:
            self.assertEqual(body(self.history, signature), body(before, signature))
        self.assertIn('deinit { timer?.invalidate() }', self.history)

    def test_original_evidence_and_production_sources_match_current_inputs(self):
        for row in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / row['path'])[row['address']]['sha256'], row['sha256'])
        for path, digest in self.proof['current_sources'].items():
            current = ROOT / path
            if path.endswith('/UI/SearchEditor.swift') or path.endswith('/UI/FilterBrowser.swift'):
                current = ROOT / '.local/p0-repair/phase-40/before' / path
            self.assertEqual(hashlib.sha256(current.read_bytes()).hexdigest(), digest)
        self.assertEqual(len(self.proof['contracts']), 6)
        self.assertTrue(all(row['priority'] == 'P1' for row in self.proof['contracts']))
        self.assertFalse(self.proof['full_function_migration_verified'])


if __name__ == '__main__':
    unittest.main()
