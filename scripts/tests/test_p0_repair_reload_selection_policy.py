"""Source/ARM-data checks only; does not execute native collection code."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from collection_membership_scope_contract import pre_collection_membership, pre_collection_membership_bytes, ENTRY_PATH
from test_p0_repair_checksum_routing import original_fragment

UI = 'replica/Sources/Pasto/UI/ReplicaUIController.swift'
HOST = 'replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift'


class ReloadSelectionPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-22'
        cls.proof = json.loads((cls.phase / 'reload-root-contract.json').read_text())
        cls.ui = pre_collection_membership((ROOT / UI).read_text())
        cls.host = pre_collection_membership((ROOT / HOST).read_text())

    def original(self, address):
        r = next(r for r in self.proof['original_fragments'] if r['address'] == address)
        return original_fragment((ROOT / r['path']).read_text(), address[2:])

    def test_original_c_fragments_are_bound(self):
        for r in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / r['path'])[r['address']]['sha256'], r['sha256'])

    def test_original_reload_branch_and_static_first_index_array_are_bound(self):
        data = (ROOT / self.proof['binary']['path']).read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), self.proof['binary']['sha256'])
        for r in self.proof['machine_ranges']:
            raw = data[r['file_offset']:r['file_offset'] + r['length']]
            self.assertEqual(raw.hex(), r['hex'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), r['sha256'])
        self.assertEqual(struct.unpack_from('<QQQ', data, 0xfb7720), (1, 2, 0))
        self.assertEqual(data[0x22c0e0:0x22c0e4].hex(), 'f50100b4')  # zero count -> empty
        self.assertEqual(data[0x22c144:0x22c148].hex(), '605500a9')  # selected array/count write
        self.assertEqual(data[0x22c15c:0x22c160].hex(), '84f3ff97')  # immediate visible-cell delivery
        self.assertEqual(data[0x22c1a0:0x22c1a8].hex(), '00e4006f01e4006f')  # zero origin

    def test_original_mutates_applier_before_reload_and_calls_onupdate_after(self):
        callback = self.original('0x100223430')
        self.assertLess(callback.index('(*param_6)()'), callback.index('if (param_1 == 0)'))
        self.assertIn('FUN_10022be98()', callback)
        complete = self.original('0x1001b9b78')
        self.assertLess(complete.index('FUN_1001b9f80,auStack_a0)'),
                        complete.index('pcVar4 = (code *)unaff_x20[3]'))
        self.assertIn('lVar5 = unaff_x20[4]', complete)
        reload = self.original('0x10022be98')
        order = ['CollectionView::cellCount) = IVar12', 'if (IVar12 == 0)',
                 '*pIVar2 = (ID)puVar11', 'FUN_100228f6c()', 'objc_stub::setBounds_(IVar12,0,0)']
        positions = [reload.index(t) for t in order]
        self.assertEqual(positions, sorted(positions))

    def test_full_reload_uses_current_items_without_selection_equality_or_fallback(self):
        method = body(self.ui, 'func applyFullCollectionReload(items: [ClipboardItem])')
        order = ['let firstID = items.first?.id', 'allowsEmptySelection = false',
                 'applyOrderedSelection(firstID.map { [$0] } ?? [], anchor: firstID, primary: firstID)']
        self.assertEqual([method.index(t) for t in order], sorted(method.index(t) for t in order))
        for text in ['guard', 'expected', 'return', 'collectionSelectionSnapshot()', 'visibleItems', 'pendingListFocus']:
            self.assertNotIn(text, method)
        self.assertNotIn('ifSelectionUnchangedFrom', self.ui + self.host)

    def test_pending_snapshot_retains_data_changes_without_selection_veto(self):
        pending = body(self.host, 'private struct PendingSnapshot')
        self.assertIn('let items: [ClipboardItem]', pending)
        self.assertIn('let changedIDs: Set<UUID>', pending)
        self.assertNotIn('selection', pending)
        update = body(self.host, 'func update(state: ReplicaUIState, cardSide: CGFloat)')
        self.assertIn('(pendingSnapshot?.changedIDs ?? []).union(changedIDs)', update)
        self.assertNotIn('collectionSelectionSnapshot()', update)
        self.assertNotIn('applyFullCollectionReload(', update)

    def test_real_drain_keeps_reload_reset_and_scroll_before_pending_neighbor(self):
        drain = body(self.host, 'private func drainCollectionSnapshots()')
        branch = body(drain, 'if requiresReload')
        order = ['items = pending.items', 'layoutCollection()',
                 'state.applyFullCollectionReload(items: items)',
                 'scrollView.contentView.bounds.origin = .zero', 'consumePendingNeighborSelection']
        self.assertEqual([drain.index(t) for t in order], sorted(drain.index(t) for t in order))
        self.assertLess(branch.index('state.applyFullCollectionReload(items: items)'),
                        branch.index('state.collectionOwner === self'))
        self.assertIn('collectionOwnerGeneration == ownerGeneration, self.state === state', branch)
        self.assertIn('tileCells()', branch)

    def test_changed_selection_counterexample_is_tied_to_before_gate_and_actual_reload_threshold(self):
        old = (self.phase / 'before' / UI).read_text()
        old_method = body(old, 'func applyFullCollectionReload(items: [ClipboardItem],')
        self.assertIn('guard collectionSelectionSnapshot() == expected else { return false }', old_method)
        case = self.proof['source_gate_counterexample']
        self.assertNotEqual(case['selection_at_enqueue'], case['selection_at_drain'])
        self.assertEqual(case['structural_insertions'], 301)
        self.assertGreater(case['structural_insertions'], 300)
        self.assertEqual(case['after_selected'], ['F0'])
        self.assertEqual(case['before_selected'], ['B'])
        self.assertEqual(case['classification'], 'source_contract_case_not_runtime_reproduction')

    def test_phase22_patch_is_bound_and_current_full_reload_remains_unchanged(self):
        old = (self.phase / 'before' / UI).read_text()
        old_method = body(old, 'func applyFullCollectionReload(items: [ClipboardItem],')
        new_method = body(self.ui, 'func applyFullCollectionReload(items: [ClipboardItem])')
        self.assertEqual(old_method.replace('        guard collectionSelectionSnapshot() == expected else { return false }\n', '')
                         .replace('        return true\n', ''), new_method)
        reconstructed = old.replace('    @discardableResult\n    func applyFullCollectionReload(items: [ClipboardItem], ifSelectionUnchangedFrom expected: CollectionSelectionSnapshot) -> Bool',
                                    '    func applyFullCollectionReload(items: [ClipboardItem])', 1)
        reconstructed = reconstructed.replace(old_method, new_method, 1)
        checkpoint = ROOT / '.local/p0-repair/phase-23/before'
        frozen_report = json.loads((ROOT / 'reports/replica/p0-p1-repair-round22.json').read_text())
        for path in [UI, HOST]:
            self.assertEqual(hashlib.sha256((checkpoint / path).read_bytes()).hexdigest(),
                             frozen_report['current_production_hashes'][path])
        self.assertEqual(reconstructed, (checkpoint / UI).read_text())
        self.assertEqual(body((checkpoint / UI).read_text(), 'func applyFullCollectionReload(items: [ClipboardItem])'),
                         new_method)
        before_host = (self.phase / 'before' / HOST).read_text()
        expected = before_host.replace('        let selection: ReplicaUIState.CollectionSelectionSnapshot\n', '', 1)
        expected = expected.replace('// A selection-only redraw must not replace the guard captured by an earlier snapshot.',
                                    '// Selection-only redraws do not change the pending data or its changed IDs.', 1)
        expected = expected.replace('            let selection = pendingSnapshot?.items == incomingItems ? pendingSnapshot?.selection : nil\n', '', 1)
        expected = expected.replace('                selection: selection ?? state.collectionSelectionSnapshot(),\n', '', 1)
        expected = expected.replace('            if requiresReload, state.applyFullCollectionReload(items: items,\n'
                                    '                ifSelectionUnchangedFrom: pending.selection) {',
                                    '            if requiresReload {\n                state.applyFullCollectionReload(items: items)', 1)
        self.assertEqual(expected, (checkpoint / HOST).read_text())

    def test_normalization_and_replacement_boundaries_remain_unclosed(self):
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertEqual(self.proof['new_fixed_record_count'], 0)
        self.assertIn('self?.normalizeSelection()', body(self.ui, 'searchIndex.onUpdate ='))
        query = body(self.ui, 'collectionQueryObservation = searchQueryChanges')
        self.assertIn('self.normalizeSelection()', query)
        self.assertTrue(self.proof['retained_partial_contracts'])


if __name__ == '__main__':
    unittest.main()
