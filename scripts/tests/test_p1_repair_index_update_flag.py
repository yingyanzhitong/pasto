"""Original/Mach-O/SDK source contracts; never executes Spotlight or Swift."""
import hashlib
import json
import re
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from index_write_scope_contract import assert_write_scope_only, assert_service_initializer_only, assert_ui_service_composition_only
from test_p0_repair_checksum_routing import original_fragment


class IndexUpdateFlagContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-42'
        cls.proof = json.loads((cls.phase / 'update-flag-contract.json').read_text())
        cls.path = 'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift'
        cls.source = (ROOT / cls.path).read_text()
        cls.before = (cls.phase / 'before' / cls.path).read_text()
        cls.fragments = {r['address']: original_fragment((ROOT / r['path']).read_text(), r['address'][2:])
                         for r in cls.proof['original_fragments']}

    def test_all_original_fragments_and_read_only_decoder_are_bound(self):
        for row in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / row['path'])[row['address']]['sha256'], row['sha256'])
        row = self.proof['decoder']
        self.assertEqual(hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest(), row['sha256'])

    def test_original_targeted_worker_forces_one_through_saved_continuation_bit(self):
        self.assertIn('FUN_1002ea770(param_2,1)', self.fragments['0x1002f2ca8'])
        self.assertIn('*(undefined1 *)(unaff_x22 + 0x118) = param_2', self.fragments['0x1002ea770'])
        self.assertIn('FUN_1002e1bac(lVar17,uVar14,param_1.unknown,*(undefined1 *)(lVar13 + 0x118))',
                      self.fragments['0x1002eaa10'])
        self.assertIn('(uint)param_4 & 1', self.fragments['0x1002e1bac'])
        self.assertIn('objc_stub::setIsUpdate_(IVar6,(ulong)(param_2 & 1))', self.fragments['0x1002e3ce8'])

    def test_original_ordinary_snapshot_path_passes_zero_explicitly(self):
        self.assertIn('FUN_1002e1bac(0,0,*(undefined8 *)(unaff_x22 + 0x18),0)', self.fragments['0x1002ea1d8'])

    def test_actual_arm_masks_bit_zero_and_calls_reachable_selector(self):
        evidence = self.proof['mask_and_setter']
        words = struct.unpack('<3I', bytes.fromhex(evidence['bytes']))
        self.assertEqual(words[:2], (0x12000262, 0xaa1603e0))  # and w2,w19,#1; receiver x22
        delta = words[2] & ((1 << 26) - 1)
        if delta & (1 << 25):
            delta -= 1 << 26
        self.assertEqual(int(evidence['setter_call'], 16) + delta * 4, int(evidence['setter_target'], 16))
        selector, = self.proof['native_selector_bindings']
        self.assertEqual(selector['selector'], 'setIsUpdate:')
        self.assertEqual(selector['stub_address'], evidence['setter_target'])
        self.assertTrue(selector['chain']['declared_chain_reachable'])
        self.assertEqual(selector['chain']['pointer_format'], 6)

    def test_local_sdk_exposes_flag_without_dynamic_bridge_or_os_gate(self):
        sdk = self.proof['sdk']
        raw = Path(sdk['path']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), sdk['sha256'])
        self.assertIn(b'BOOL isUpdate API_AVAILABLE(macos(10.11)', raw)

    def test_targeted_batch_converts_live_records_with_update_true_before_sdk(self):
        def valid(text):
            target = body(text, 'private func reindexTargets(')
            batch = body(target, 'for lowerBound in stride(')
            try:
                ordered = ['guard isRunning, !Task.isCancelled else { break }', 'try liveEntries(',
                           'let changed = live.map { searchableItem($0, isUpdate: true) }',
                           'Self.writeSearchableItems(changed, index: resolveWriteIndex())']
                offsets = [batch.index(t) for t in ordered]
                return offsets == sorted(offsets) and 'indexed[$0.id] !=' not in batch
            except ValueError:
                return False
        self.assertTrue(valid(self.source))
        self.assertFalse(valid(self.before))
        self.assertFalse(valid(self.source.replace('isUpdate: true', 'isUpdate: false')))

    def test_builder_explicitly_writes_flag_before_return_without_altering_attributes(self):
        current = body(self.source, 'private func searchableItem(')
        before = body(self.before, 'private func searchableItem(')
        addition = '        // 0x1002f2ca8 → 0x1002ea770 → 0x1002e1bac → 0x1002e3ce8.\n        item.isUpdate = isUpdate\n'
        historical = (ROOT / '.local/p0-repair/phase-43/before' / self.path).read_text()
        self.assertEqual(body(historical, 'private func searchableItem(').replace(addition, '', 1), before)
        self.assertLess(current.index('item.expirationDate = .distantFuture'), current.index('item.isUpdate = isUpdate'))
        self.assertLess(current.index('item.isUpdate = isUpdate'), current.index('return item'))
        self.assertNotIn('if ', current[current.index('item.expirationDate'):])

    def test_all_builder_call_sites_choose_flag_and_no_default_hides_choice(self):
        calls = re.findall(r'searchableItem\(\$0, isUpdate: (true|false)\)', self.source)
        self.assertEqual(calls.count('true'), 1)
        self.assertEqual(calls.count('false'), 2)
        self.assertNotIn('.map(searchableItem)', self.source)
        self.assertIn('private func searchableItem(_ entry: Entry, isUpdate: Bool)', self.source)
        self.assertNotIn('isUpdate: Bool =', self.source)

    def test_delegate_queue_batch_ack_and_errors_are_unchanged(self):
        for marker in ['nonisolated private func rebuild(', 'private func deleteIdentifiers(']:
            # Keep the old flag-only proof bound to its actual pre-ID-migration source.
            current = body((ROOT / '.local/p0-repair/phase-55/before/replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text(), marker)
            if marker.startswith('nonisolated'):
                # Freeze the historical whole-method proof before removal of the UI-snapshot gate.
                historical = (ROOT / '.local/p0-repair/phase-47/before/replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text()
                before_delegate = body(historical, marker)
                self.assertEqual(body(current, 'if let identifiers'), body(before_delegate, 'if let identifiers'))
                self.assertEqual(current[current.index('acknowledgements.append(acknowledge)'):],
                                 before_delegate[before_delegate.index('acknowledgements.append(acknowledge)'):])
                current = before_delegate
                current = current.replace('                mayRestoreSavedState = false\n', '', 1)
            assert_write_scope_only(self, current, body(self.before, marker))
        target = body(self.source, 'private func reindexTargets(')
        previous = body(self.before, 'private func reindexTargets(')
        historical = (ROOT / '.local/p0-repair/phase-48/before/replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text()
        historical_target = body(historical, 'private func reindexTargets(')
        self.assertEqual(historical_target.replace('live.map { searchableItem($0, isUpdate: true) }', 'live.map(searchableItem)'), previous)
        suffix = 'let upperBound = min('
        assert_write_scope_only(self, target[target.index(suffix):].replace('            enqueueOCR(live)\n', '', 1).replace('        startOCRWorker()\n', '', 1), historical_target[historical_target.index(suffix):])
        self.assertIn('let forcedIdentifiers = reindexIdentifiers', self.source)
        self.assertIn('try await reindexTargets(forcedIdentifiers)', self.source)

    def test_shared_flag_records_do_not_claim_five_defects_or_full_projection_migration(self):
        self.assertEqual(len(self.proof['contracts']), 5)
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertEqual(self.proof['function_map_markers_upgraded'], 0)
        self.assertTrue(all(not r['full_function_migration_verified'] for r in self.proof['contracts']))
        historical = (ROOT / '.local/p0-repair/phase-43/before' / self.path).read_text()
        self.assertIn('text = String(indexedText.prefix(5000))', historical)
        self.assertIn('let pinboards: [String]', historical)
        self.assertIn('let device: String', historical)


if __name__ == '__main__':
    unittest.main()
