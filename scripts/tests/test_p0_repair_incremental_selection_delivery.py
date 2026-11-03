from item_order_scope_contract import without_list_route
"""C/ARM and source-contract checks; no Swift/AppKit execution."""
import hashlib
import itertools
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from collection_membership_scope_contract import pre_collection_membership, pre_collection_membership_bytes, ENTRY_PATH
from list_attributes_scope_contract import pre_attributes_host
from test_p0_repair_checksum_routing import original_fragment

UI = 'replica/Sources/Pasto/UI/ReplicaUIController.swift'
HOST = 'replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift'


class IncrementalSelectionDelivery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-23'
        cls.proof = json.loads((cls.phase / 'incremental-root-contract.json').read_text())
        cls.ui = pre_collection_membership((ROOT / UI).read_text())
        cls.host = pre_collection_membership((ROOT / HOST).read_text())

    def original(self, address):
        r = next(r for r in self.proof['original_fragments'] if r['address'] == address)
        return original_fragment((ROOT / r['path']).read_text(), address[2:])

    def test_original_fragments_and_manager_write_machine_range_are_bound(self):
        for r in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / r['path'])[r['address']]['sha256'], r['sha256'])
        raw = (ROOT / self.proof['binary']['path']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), self.proof['binary']['sha256'])
        for r in self.proof['machine_ranges']:
            data = raw[r['file_offset']:r['file_offset'] + r['length']]
            self.assertEqual(data.hex(), r['hex'])
            self.assertEqual(hashlib.sha256(data).hexdigest(), r['sha256'])
        self.assertEqual(raw[0x22377c:0x223780].hex(), 'aa0000b4')  # empty result, not index0 fallback
        self.assertEqual(raw[0x2237a8:0x2237ac].hex(), '6a0900f9')  # last transformed index -> manager+16

    def test_original_final_selection_uses_transformed_order_and_last_endpoint(self):
        incremental = self.original('0x1002234e0')
        order = ['FUN_1002258ac()', 'FUN_100223f2c()', 'lVar12 = *(long *)(lVar8 + 0x10)',
                 '*plVar1 = lVar8', 'plVar1[2] = lVar13', 'FUN_100228f6c()']
        self.assertEqual([incremental.index(t) for t in order], sorted(incremental.index(t) for t in order))
        self.assertIn('lVar13 = *(long *)(lVar8 + lVar12 * 8 + 0x18)', incremental)
        self.assertIn('*(bool *)(plVar1 + 3) = lVar12 == 0', incremental)
        self.assertIn("(char)unaff_x20[3] != '\\x01'", self.original('0x10022df78'))
        self.assertIn('uVar13 = unaff_x20[2]', self.original('0x10022df78'))

    def test_native_data_application_delivers_incremental_selection_before_neighbor(self):
        drain = body(self.host, 'private func drainCollectionSnapshots()')
        order = ['items = pending.items', 'layoutCollection()',
                 'state.applyFullCollectionReload(items: items)',
                 'state.applyIncrementalCollectionSnapshot(items: items)',
                 'state.consumePendingNeighborSelection']
        self.assertEqual([drain.index(t) for t in order], sorted(drain.index(t) for t in order))
        self.assertIn('} else {\n                state.applyIncrementalCollectionSnapshot(items: items)', drain)
        self.assertIn('state.collectionOwner === self else { continue }', drain)
        self.assertLess(drain.index('if !isInitialSnapshot && !selectionRelevantSnapshotChanged && !hasRelevantChanges'),
                        drain.index('state.applyIncrementalCollectionSnapshot'))

    def test_live_projection_normalization_keeps_housekeeping_but_defers_selection(self):
        normalize = body(self.ui, 'func normalizeSelection()')
        for token in ['pendingPinboardDeletionID = nil', 'selectListIdentifier(ClipboardStore.historyListIdentifier, force: false)', 'cancelItemDeletion()']:
            self.assertLess(normalize.index(token), normalize.index('guard collectionOwner == nil'))
        self.assertLess(normalize.index('guard collectionOwner == nil'), normalize.index('normalizeProjectedSelection()'))
        self.assertNotIn('applyOrderedSelection(', normalize)
        self.assertNotIn('selection =', normalize)
        for signature in ['searchIndex.onUpdate =', 'collectionQueryObservation = searchQueryChanges']:
            self.assertIn('normalizeSelection()', body(self.ui, signature))

    def test_incremental_has_no_default_selection_and_uses_last_surviving_endpoint(self):
        method = body(self.ui, 'func applyIncrementalCollectionSnapshot(items: [ClipboardItem])')
        self.assertIn('let visible = Set(items.map(\\.id))', method)
        self.assertIn('orderedSelectionIDs.filter { selection.contains($0) && visible.contains($0) }', method)
        self.assertIn('allowsEmptySelection = ids.isEmpty', method)
        self.assertIn('applyOrderedSelection(ids, anchor: ids.last, primary: ids.last)', method)
        for token in ['items.first', 'visibleItems', 'rangeAnchorID', 'selectIndex(', 'cancelPendingNeighborSelection', 'async']:
            self.assertNotIn(token, method)

    def test_empty_full_then_insert_counterexample_uses_live_before_and_after_consumers(self):
        before = (self.phase / 'before' / UI).read_text()
        full = body(before, 'func applyFullCollectionReload(items: [ClipboardItem])')
        self.assertIn('allowsEmptySelection = false', full)
        old_normalize = body(before, 'func normalizeSelection()')
        self.assertIn('if ids.isEmpty, !allowsEmptySelection, let first = items.first', old_normalize)
        self.assertNotIn('guard collectionOwner == nil', old_normalize)
        old_drain = body((self.phase / 'before' / HOST).read_text(), 'private func drainCollectionSnapshots()')
        self.assertNotIn('applyIncrementalCollectionSnapshot', old_drain)
        case = self.proof['source_gate_counterexample']
        self.assertEqual(case['initial_full_items'], [])
        self.assertEqual(case['next_incremental_items'], ['A'])
        self.assertEqual(case['before_selected'], ['A'])
        self.assertEqual(case['original_selected'], case['after_selected'])
        self.assertEqual(case['after_selected'], [])

    def test_unattached_and_explicit_board_projection_keep_the_legacy_policy(self):
        current = body(self.ui, 'private func normalizeProjectedSelection()')
        old = body((self.phase / 'before' / UI).read_text(), 'func normalizeSelection()')
        old_core = old[old.index('        let items = visibleItems'):old.index('        if let pinboardID,')]
        old_core = old_core.replace('        if let request = pendingItemDeletion, !request.ids.isSubset(of: visible) {\n'
                                    '            cancelItemDeletion()\n        }\n', '')
        self.assertEqual('{\n' + old_core + '    }', current)
        board = body(self.ui, 'private func applySelectedList(_ id: UUID?)')
        old_board = body((self.phase / 'before' / UI).read_text(), 'func chooseBoard(_ id: UUID?)')
        expected = old_board.replace('normalizeSelection()', 'normalizeProjectedSelection()')
        expected = expected.replace('        normalizeProjectedSelection()\n',
                                    '        normalizeProjectedSelection()\n'
                                    '        collectionOwner?.replaceCollectionModel(state: self)\n')
        self.assertEqual(expected, without_list_route(board))

    def test_unique_id_no_move_domain_matches_original_delete_insert_index_arithmetic(self):
        # A pure Python model of 1b2a90 -> 1b2cc0, with no moves/reloads and
        # unique item identities. This is not execution of the Swift mapper.
        old = ('A', 'B', 'C')
        checked = 0
        for size in range(6):
            for new in itertools.permutations(old + ('X', 'Y'), size):
                retained = tuple(v for v in new if v in old)
                if retained != tuple(v for v in old if v in new):
                    continue
                removed = [i for i, value in enumerate(old) if value not in new]
                inserted = [i for i, value in enumerate(new) if value not in old]
                for count in range(4):
                    for selected in itertools.permutations(range(3), count):
                        transformed = []
                        for index in selected:
                            if index in removed:
                                continue
                            offset = index - sum(value < index for value in removed)
                            for insertion in inserted:
                                if insertion <= offset:
                                    offset += 1
                            transformed.append(offset)
                        reference_ids = [new[i] for i in transformed]
                        projected_ids = [old[i] for i in selected if old[i] in new]
                        self.assertEqual(reference_ids, projected_ids)
                        checked += 1
        self.assertGreater(checked, 1000)
        self.assertIn('cVar4 == \'\\x02\'', self.original('0x100223f2c'))
        self.assertIn('cVar4 == \'\\x01\'', self.original('0x100223f2c'))

    def test_full_reload_and_owner_cancellation_contracts_remain_unchanged(self):
        before_ui = (self.phase / 'before' / UI).read_text()
        self.assertEqual(body(before_ui, 'func applyFullCollectionReload(items: [ClipboardItem])'),
                         body(self.ui, 'func applyFullCollectionReload(items: [ClipboardItem])'))
        before_host = (self.phase / 'before' / HOST).read_text()
        for signature in ['func update(state: ReplicaUIState, cardSide: CGFloat)',
                          'private func scheduleSnapshotDrain()', 'func detachObservers()']:
            expected = body(before_host, signature)
            if signature.startswith('func update('):
                expected = expected.replace('            snapshotDrainScheduled = false\n',
                                            '            snapshotDrainScheduled = false\n            items = []\n', 1)
            self.assertEqual(expected, body(pre_attributes_host(self, self.host), signature))
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertEqual(self.proof['new_fixed_record_count'], 0)

    def test_installation_mapping_uses_correct_closures_and_tuple_fallback(self):
        self.assertIn('compactMap', self.proof['sdk_imports']['0x100bf55b0']['symbol'])
        self.assertIn('3map', self.proof['sdk_imports']['0x100bf55d4']['symbol'])
        raw = (ROOT / self.proof['binary']['path']).read_bytes()
        self.assertEqual(raw[0x7e89c:0x7e8a0].hex(), '00200291')  # x0 += 0x88 ->7e088 compactMap
        self.assertEqual(raw[0x7e974:0x7e978].hex(), '00002b91')  # x0 += 0xac0 ->7eac0 map
        self.assertEqual(raw[0x7ead8:0x7eadc].hex(), '155840a9')  # load tuple first/second words
        self.assertEqual(raw[0x7eb54:0x7eb58].hex(), '950000b5')  # retain first if nonnil
        self.assertIn('lVar2 = param_2[1]', self.original('0x10007eac0'))
        self.assertIn('if (lVar1 == 0)', self.original('0x10007eac0'))
        self.assertIn('lVar8 = lVar2', self.original('0x10007eac0'))


if __name__ == '__main__':
    unittest.main()
