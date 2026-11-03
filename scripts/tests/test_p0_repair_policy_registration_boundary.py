from capture_lifecycle_scope_contract import pre_capture_lifecycle
"""Source contracts only: no Carbon, AppKit or persistent-store execution."""
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from modal_restore_scope_contract import pre_modal_restore
from test_p0_repair_checksum_routing import original_fragment


class PolicyRegistrationBoundaryContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-37'
        cls.core = ROOT / 'replica/Sources/PastoCore'
        cls.monitor = (cls.core / 'OriginalGlobalShortcutMonitor.swift').read_text()
        cls.pasteboard = pre_capture_lifecycle((cls.core / 'Pasteboard.swift').read_text())
        cls.facade = (ROOT / 'replica/Sources/Pasto/GlobalHotKey.swift').read_text()
        cls.before = cls.phase / 'before'

    def test_original_registration_is_void_and_side_effect_order_is_bound(self):
        original = original_fragment((ROOT / 'decompiled/Paste/part-0157.c').read_text(), '1001eaa64')
        self.assertIn('void FUN_1001eaa64(', original)
        order = ['FUN_1001eae90();', 'FUN_1001eb8d0(', 'FUN_1001eb1e4(']
        self.assertEqual([original.index(t) for t in order], sorted(original.index(t) for t in order))
        self.assertIn('if (*(int *)(uVar3 + 0x24) == 0)', original)

    def test_original_entry_exposes_void_and_shares_actual_registration_worker(self):
        signature = 'public func f_1001eaa64(shortcut: OriginalShortcutValue, action: @escaping () -> Void)'
        self.assertIn(signature + ' {', self.monitor)
        self.assertEqual(body(self.monitor, signature).strip(), '{\n        _ = registerShortcut(shortcut: shortcut, action: action)\n    }')
        self.assertNotIn('func f_1001eaa64(shortcut: OriginalShortcutValue, action: @escaping () -> Void) ->', self.monitor)

    def test_keyboard_original_entry_also_returns_void(self):
        signature = 'public func f_1001eaa64(shortcut: KeyboardShortcut, action: @escaping () -> Void)'
        self.assertIn(signature + ' {', self.monitor)
        self.assertIn('f_1001eaa64(shortcut: OriginalShortcutValue(', body(self.monitor, signature))

    def test_registration_algorithm_is_unchanged_and_not_duplicated(self):
        before = (self.before / 'replica/Sources/PastoCore/OriginalGlobalShortcutMonitor.swift').read_text()
        old = body(before, 'public func f_1001eaa64(shortcut: OriginalShortcutValue, action: @escaping () -> Void) -> OSStatus')
        new = body(self.monitor, 'private func registerShortcut(shortcut: OriginalShortcutValue, action: @escaping () -> Void) -> OSStatus')
        self.assertEqual(old, new)
        self.assertEqual(self.monitor.count('let registration = OriginalShortcutRegistration('), 1)

    def test_status_adapter_preserves_exact_per_attempt_status_without_shared_slot(self):
        adapter = body(self.monitor, 'public func registerShortcut(shortcut: KeyboardShortcut,')
        self.assertIn('registerShortcut(shortcut: OriginalShortcutValue(', adapter)
        worker = body(self.monitor, 'private func registerShortcut(shortcut: OriginalShortcutValue,')
        self.assertIn('return registration.status', worker)
        before = (self.before / 'replica/Sources/PastoCore/OriginalGlobalShortcutMonitor.swift').read_text()
        self.assertEqual(body(self.monitor, 'public final class OriginalShortcutRegistration'), body(before, 'public final class OriginalShortcutRegistration'))
        self.assertNotIn('lastStatus', self.monitor)

    def test_real_ui_status_consumer_only_renames_the_adapter_call(self):
        before = (self.before / 'replica/Sources/Pasto/GlobalHotKey.swift').read_text()
        self.assertEqual(self.facade.replace('monitor.registerShortcut(', 'monitor.f_1001eaa64(', 1), before)
        self.assertIn('if status == noErr { registeredShortcut = shortcut }', self.facade)

    def test_policy_has_no_extra_persistent_read_before_data_acceptance(self):
        for signature in ['fileprivate func allowsPasteboardCapture(', 'public func originalPasteboardShouldRead(']:
            policy = body(self.pasteboard, signature)
            self.assertNotIn('reload()', policy)
            self.assertNotIn('latestState()', policy)
            self.assertNotIn('persistence.', policy)
        delegate = body(self.pasteboard, 'public func originalPasteboardShouldRead(')
        self.assertIn('OriginalPasteboardPolicies.f_10037ba14(', delegate)
        self.assertIn('return try store.allowsPasteboardCapture(', delegate)

    def test_gates_and_pause_expiry_are_unchanged_except_extra_reload(self):
        before = (self.before / 'replica/Sources/PastoCore/Pasteboard.swift').read_text()
        signature = 'fileprivate func allowsPasteboardCapture('
        self.assertEqual(body(self.pasteboard, signature), body(before, signature).replace('        try reload()\n', '', 1))
        policy = body(self.pasteboard, signature)
        self.assertEqual(policy.count('try save()'), 1)
        expiry = body(policy, 'if let until = preferences.pauseUntil')
        self.assertIn('if until > Date() { return false }', expiry)
        self.assertIn('try save()', expiry)

    def test_in_memory_preferences_and_existing_background_refresh_remain_live(self):
        main = pre_modal_restore((ROOT / 'replica/Sources/Pasto/AppMain.swift').read_text())
        refresh = body(main, 'refreshTimer = Timer.scheduledTimer(withTimeInterval: 1, repeats: true)')
        self.assertIn('try self.store.reload()', refresh)
        self.assertEqual(main, (self.before / 'replica/Sources/Pasto/AppMain.swift').read_text())
        store = (self.core / 'ClipboardStore.swift').read_text()
        self.assertIn('@Published public var preferences = AppPreferences()', store)
        self.assertEqual((ROOT / '.local/p0-repair/phase-38/before/replica/Sources/PastoCore/ClipboardStore.swift').read_text(), (self.before / 'replica/Sources/PastoCore/ClipboardStore.swift').read_text())
        self.assertEqual(body(store, 'public func reload() throws'), body((self.before / 'replica/Sources/PastoCore/ClipboardStore.swift').read_text(), 'public func reload() throws'))

    def test_actual_read_pipeline_and_readonly_policy_implementation_are_retained(self):
        before = (self.before / 'replica/Sources/PastoCore/Pasteboard.swift').read_text()
        self.assertEqual(body(self.pasteboard, 'private func synchronizePasteboard()'), body(before, 'private func synchronizePasteboard()'))
        path = 'replica/Sources/PastoCore/OriginalPasteboardPolicies.swift'
        self.assertEqual((ROOT / path).read_bytes(), (self.before / path).read_bytes())

    def test_original_capture_and_policy_fragments_remain_bound(self):
        proof = json.loads((self.phase / 'policy-registration-contract.json').read_text())
        for r in proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / r['path'])[r['address']]['sha256'], r['sha256'])
        raw = (ROOT / proof['binary']['path']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), proof['binary']['sha256'])


if __name__ == '__main__':
    unittest.main()
