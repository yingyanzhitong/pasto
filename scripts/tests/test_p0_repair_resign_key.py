"""Offline resign-key contract checks. No AppKit execution or compilation."""
import hashlib
import json
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body


class ResignKeyContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proof = json.loads((ROOT / '.local/p0-repair/phase-10/resign-original-proof.json').read_text())
        cls.ui = (ROOT / 'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
        cls.resign = body(cls.ui, 'private func panelDidResignKey()')

    def original(self, address):
        record = next(r for r in self.proof['original_fragments'] if r['address'] == address)
        text = (ROOT / record['path']).read_text()
        start = text.index('/* Address: ' + address + ' |')
        end = text.find('/* Address:', start + 1)
        return text[start:end if end >= 0 else None]

    def test_original_fragments_are_bound(self):
        for record in self.proof['original_fragments']:
            actual = source_fragments(ROOT / record['path'])[record['address']]['sha256']
            self.assertEqual(actual, record['sha256'])

    def test_round_peer_proofs_bind_original_and_sdk_inputs(self):
        phase = ROOT / '.local/p0-repair/phase-10'
        for name in ['edit-action-proof.json', 'shift-edit-proof.json',
                     'writing-tools-consumer-proof.json', 'resign-peer-review.json']:
            proof = json.loads((phase / name).read_text())
            for record in proof['original_fragments']:
                address = record.get('address') or record['id'].split(':')[-1]
                actual = source_fragments(ROOT / record['path'])[address]['sha256']
                self.assertEqual(actual, record['sha256'], (name, address))
            for record in proof.get('sdk_bindings', []):
                self.assertEqual(hashlib.sha256((ROOT / record['path']).read_bytes()).hexdigest(),
                                 record['sha256'], (name, record['path']))

    def test_original_machine_ranges_are_bound(self):
        binary = (ROOT / self.proof['binary_path']).read_bytes()
        self.assertEqual(hashlib.sha256(binary).hexdigest(), self.proof['binary_sha256'])
        for record in self.proof['machine_segments']:
            segment = binary[record['file_offset']:record['file_offset'] + record['length']]
            self.assertEqual(segment.hex(), record['hex'])
            self.assertEqual(hashlib.sha256(segment).hexdigest(), record['sha256'])

    def test_original_delegate_directly_calls_weak_owner_thunk(self):
        init = self.original('0x1000187d0')
        self.assertLess(init.index('_swift_unknownObjectWeakInit(puVar4 + 0x10,IVar9)'),
                        init.index('*puVar1 = FUN_10001a77c'))
        dispatch = self.original('0x100077e68')
        self.assertIn('pcVar8 = *(code **)(param_1 + *param_5)', dispatch)
        self.assertIn('(*pcVar8)()', dispatch)
        self.assertNotIn('async', dispatch)
        thunk = self.original('0x10001a77c')
        self.assertIn('FUN_100018c84()', thunk)
        binary = (ROOT / self.proof['binary_path']).read_bytes()
        word = struct.unpack_from('<I', binary, 0x1a780)[0]
        offset = word & 0x3ffffff
        if offset & 0x2000000:
            offset -= 0x4000000
        self.assertEqual(word >> 26, 0b000101)  # Direct B, not BL/async dispatch.
        self.assertEqual(0x10001a780 + offset * 4, 0x100018c84)

    def test_original_orders_suppression_sheet_modal_then_close(self):
        original = self.original('0x100018c84')
        order = ['_swift_unknownObjectWeakLoadStrong()', '::pendingResignKeyCloseSuppression',
                 'objc_stub::window(', 'objc_stub::sheets(', 'objc_stub::modalWindow(',
                 'FUN_100019a84()']
        positions = [original.index(token) for token in order]
        self.assertEqual(positions, sorted(positions))
        self.assertIn('if (_Var5 == 0)', original)
        self.assertIn('if (IVar3 == 0)', original)

    def test_handoff_suppression_is_excluded_instead_of_invented_local_state(self):
        original = self.original('0x1000b2114')
        self.assertIn('Paste/AppDelegate+Handoff.swift', original)
        self.assertIn('::pendingResignKeyCloseSuppression) =\n           1', original)
        self.assertNotIn('pendingResignKeyCloseSuppression =', self.ui)
        self.assertIn('Handoff', self.resign)

    def test_live_delegate_uses_weak_owner_and_synchronous_entry(self):
        self.assertIn('func windowDidResignKey(_ notification: Notification) { didResignKey?() }', self.ui)
        self.assertIn('panel.didResignKey = { [weak self] in self?.panelDidResignKey() }', self.ui)
        self.assertNotIn('DispatchQueue', self.resign)
        self.assertNotIn('Task', self.resign)

    def test_current_guard_precedes_close_without_extra_focus_or_menu_exclusions(self):
        self.assertLess(self.resign.index('guard panel.sheets.isEmpty, NSApp.modalWindow == nil else { return }'),
                        self.resign.index('hidePanel()'))
        for token in ['canDismissPanelForInteraction', 'isKeyWindow', 'isPanelInteractionWindow',
                      'menuTrackingDepth', 'previewPopover', 'NSApp.keyWindow']:
            self.assertNotIn(token, self.resign)
        self.assertEqual(self.resign.count('hidePanel()'), 1)

    def test_regression_is_detectable_in_saved_previous_source(self):
        previous = (ROOT / '.local/p0-repair/phase-10/before/replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
        old = body(previous, 'private func panelDidResignKey()')
        self.assertIn('DispatchQueue.main.async', old)
        self.assertIn('!self.panel.isKeyWindow', old)
        self.assertNotEqual(old, self.resign)

    def test_close_keeps_visible_and_transition_guards(self):
        close = body(self.ui, 'func hidePanel()')
        order = ['guard panel.isVisible', 'guard !isPanelClosing', 'panelTransitionGeneration += 1',
                 'panel.makeFirstResponder(nil)', 'beginClosedState()', 'isPanelClosing = true',
                 'panelWillClose?(', 'OriginalViewAnimation.f_10021cadc']
        positions = [close.index(token) for token in order]
        self.assertEqual(positions, sorted(positions))
        self.assertIn('generation == self.panelTransitionGeneration', close)


if __name__ == '__main__':
    unittest.main()
