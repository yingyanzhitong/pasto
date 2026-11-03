"""Source and original-data checks for selection input; no native UI execution."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from modal_restore_scope_contract import pre_modal_restore
from test_p0_repair_checksum_routing import original_fragment


class SelectionSnapshotConsumers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-15'
        cls.proof = json.loads((cls.phase / 'selection-root-contract.json').read_text())
        cls.ui = pre_modal_restore((ROOT / 'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text())
        cls.native = (ROOT / 'replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift').read_text()

    def original(self, address):
        r = next(r for r in self.proof['original_fragments'] if r['address'] == address)
        return original_fragment((ROOT / r['path']).read_text(), address[2:])

    def test_original_fragments_and_prior_datasource_proof_are_bound(self):
        for r in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / r['path'])[r['address']]['sha256'], r['sha256'])
        r = self.proof['prior_datasource_proof']
        self.assertEqual(hashlib.sha256((ROOT / r['path']).read_bytes()).hexdigest(), r['sha256'])

    def test_original_range_bound_and_manager_count_machine_data_are_bound(self):
        binary = (ROOT / self.proof['binary']['path']).read_bytes()
        self.assertEqual(hashlib.sha256(binary).hexdigest(), self.proof['binary']['sha256'])
        for r in self.proof['machine_ranges']:
            start, end = int(r['start'], 16), int(r['end'], 16)
            self.assertEqual(hashlib.sha256(binary[start - 0x100000000:end - 0x100000000]).hexdigest(), r['sha256'])
        self.assertEqual(binary[0x22b22c:0x22b230].hex(), 'e10315aa')  # x1 = manager count
        self.assertEqual(binary[0x228f08:0x228f0c].hex(), '000080d2')  # lower bound 0

    def test_original_select_all_uses_manager_count_and_sets_last_endpoint(self):
        original = self.original('0x100228ee8')
        self.assertLess(original.index('FUN_10022b1cc()'), original.index('FUN_100229138()'))
        for token in ['plVar1[1] = param_2', 'plVar1[2] = lVar6', 'lVar5 == 0', 'FUN_100228f6c()']:
            self.assertIn(token, original)
        range_ = self.original('0x100229138')
        self.assertIn('lVar3 = param_2 - param_1', range_)
        self.assertIn('param_1 + lVar7', range_)
        self.assertIn('_TtC7PasteUI14CollectionView::dataSource', self.original('0x10022be98'))
        self.assertIn('pIVar2[1] = IVar12', self.original('0x10022be98'))
        self.assertIn('_TtC5Paste18ItemCollectionView::applier', self.original('0x10006e188'))
        anchor = self.original('0x10022df78')
        self.assertIn("(char)unaff_x20[3] != '\\x01'", anchor)
        self.assertIn('uVar13 = unaff_x20[2]', anchor)

    def test_select_all_uses_real_owner_and_replaces_both_endpoints_with_last_applied_id(self):
        select = body(self.ui, 'func selectAll()')
        order = ['guard let items = collectionOwner?.appliedItems(for: self)',
                 'cancelPendingNeighborSelection()', 'let ids = items.map(\.id)',
                 'applyOrderedSelection(ids, anchor: ids.last, primary: ids.last)']
        positions = [select.index(t) for t in order]
        self.assertEqual(positions, sorted(positions))
        for token in ['visibleItems', 'primary: primaryID', 'reveal', 'async']:
            self.assertNotIn(token, select)

    def test_adjacent_navigation_uses_applied_last_endpoint(self):
        move = body(self.ui, 'func moveSelection(_ offset: Int, extending: Bool = false)')
        order = ['collectionOwner?.appliedItems(for: self)', 'guard !items.isEmpty',
                 'let endpoint = orderedSelectionIDs.last', 'items.firstIndex(where:',
                 'let next = current + offset', 'selectIndex(next, mode: extending ? 2 : 0, items: items)']
        positions = [move.index(t) for t in order]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn('visibleItems', move)
        self.assertNotIn('primaryID', move)

    def test_boundary_navigation_uses_applied_count_without_animation(self):
        move = body(self.ui, 'func moveSelectionToBoundary(last: Bool, extending: Bool = false)')
        self.assertIn('collectionOwner?.appliedItems(for: self)', move)
        self.assertIn('guard !items.isEmpty', move)
        self.assertIn('selectIndex(last ? items.count - 1 : 0, mode: extending ? 2 : 0, items: items, animated: false)', move)
        self.assertNotIn('visibleItems', move)

    def test_native_action_reaches_same_selection_and_synchronous_cell_consumer(self):
        self.assertIn('state?.selectAll()', body(self.native, 'override func selectAll(_ sender: Any?)'))
        apply = body(self.ui, 'private func applyOrderedSelection(_ ids: [UUID], anchor: UUID?, primary: UUID?)')
        self.assertIn('collectionOwner?.applySelection(state: self)', apply)
        cells = body(self.native, 'func applySelection(state: ReplicaUIState)')
        self.assertIn('self.state === state, state.collectionOwner === self', cells)
        self.assertIn('cell.isSelected = state.selection.contains(items[index].id)', cells)
        self.assertNotIn('async', cells)

    def test_return_paste_preserves_applied_order_and_empty_guard(self):
        paste = body(self.ui, 'func pasteSelection(plainTextOnly: Bool)')
        self.assertIn('let items = appliedSelectionItems()', paste)
        self.assertIn('guard !items.isEmpty else { return }', paste)
        self.assertIn('paste(ids: items.map(\.id), plainTextOnly: plainTextOnly)', paste)
        self.assertNotIn('state.selectedItems', paste)
        selection = body(self.ui, 'private func appliedSelectionItems()')
        self.assertIn('collection.appliedSelectedItems(for: state,', selection)
        self.assertIn('orderedIDs: state.collectionSelectionSnapshot().orderedIDs', selection)

    def test_space_uses_last_applied_selection_without_changing_preview_timing(self):
        handle = body(self.ui, 'private func handleKey(_ event: NSEvent)')
        space = body(handle, 'if event.keyCode == 49, !isEditing')
        self.assertIn('appliedSelectionItems().last', space)
        self.assertIn('showPreview(item: item)', space)
        self.assertNotIn('async', space)
        self.assertNotIn('state.selectedItems', space)
        before = (self.phase / 'before/replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
        expected = body(before, 'func showPreview(item: ClipboardItem)')
        lazy_before = (ROOT / '.local/p0-repair/phase-29/before/replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
        self.assertEqual(expected, body(lazy_before, 'func showPreview(item: ClipboardItem)'))
        expected = expected.replace('if panel.isVisible, !isPanelClosing',
                                    'if isPanelOrderedVisible, !isPanelClosing')
        self.assertEqual(expected, body(self.ui, 'func showPreview(item: ClipboardItem)'))

    def test_hotkey_status_facade_is_consumed_and_unchanged(self):
        for path in ['replica/Sources/PastoCore/OriginalGlobalShortcutMonitor.swift', 'replica/Sources/Pasto/GlobalHotKey.swift']:
            checkpoint = ROOT / '.local/p0-repair/phase-37/before' / path
            self.assertEqual(checkpoint.read_bytes(), (self.phase / 'before' / path).read_bytes())
        facade = (ROOT / 'replica/Sources/Pasto/GlobalHotKey.swift').read_text()
        self.assertIn('let status = monitor.registerShortcut', facade)
        self.assertIn('if status == noErr { registeredShortcut = shortcut }', facade)
        self.assertIn('return status', facade)


if __name__ == '__main__':
    unittest.main()
