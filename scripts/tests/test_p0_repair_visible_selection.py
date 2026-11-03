"""Selection setter's direct visible-cell delivery; source/original data only."""
import hashlib
import json
import struct
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body


class VisibleSelection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ui = (ROOT / 'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
        cls.host = (ROOT / 'replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift').read_text()

    def test_original_setter_calls_visible_cells_with_membership_flag(self):
        proof = json.loads((ROOT / '.local/p0-repair/phase-7/selection-manager-proof.json').read_text())
        ref = proof['original']
        self.assertEqual(source_fragments(ROOT / ref['path'])['0x100228ee8']['sha256'], ref['sha256_rstrip_newline'])
        for ref in proof['original']['supporting_original_fragments']:
            self.assertEqual(source_fragments(ROOT / ref['path'])[ref['address']]['sha256'], ref['sha256_rstrip_newline'])
        source = (ROOT / 'decompiled/Paste/part-0188.c').read_text()
        setter = source[source.index('void FUN_100228ee8('):source.index('/* Address: 0x100228f6c')]
        self.assertLess(setter.index('*(bool *)(plVar1 + 3) = lVar5 == 0'), setter.index('FUN_100228f6c()'))
        consumer = source[source.index('void FUN_100228f6c('):source.index('/* Address:', source.index('void FUN_100228f6c('))]
        self.assertIn('CollectionView::visibleCells', consumer)
        self.assertIn('(lVar3 + 0x10))(lVar10 != 0,uVar7,lVar3)', consumer)

    def test_ordered_setter_finishes_model_before_notifying_live_owner(self):
        setter = body(self.ui, 'private func applyOrderedSelection(')
        call = 'collectionOwner?.applySelection(state: self)'
        for value in ['orderedSelectionIDs = ids', 'rangeAnchorID = anchor', 'selection = Set(ids)',
                      'primaryID = primary', 'isApplyingSelection = false']:
            self.assertLess(setter.index(value), setter.index(call))
        self.assertEqual(setter.count(call), 1)
        for forbidden in ['DispatchQueue', 'Task {', 'makeFirstResponder', 'normalizeSelection']:
            self.assertNotIn(forbidden, setter)

    def test_external_selection_and_deselect_also_deliver_after_reconciliation(self):
        reconcile = body(self.ui, 'private func reconcileExternalSelection()')
        self.assertLess(reconcile.index('primaryID = orderedSelectionIDs.last'),
                        reconcile.index('collectionOwner?.applySelection(state: self)'))
        self.assertIn('didSet { if !isApplyingSelection { reconcileExternalSelection() } }', self.ui)
        for signature in ['func selectAll()', 'func deselectAll()', 'private func normalizeProjectedSelection()',
                          'func applyFullCollectionReload(items:', 'func applyIncrementalCollectionSnapshot(items:']:
            self.assertIn('applyOrderedSelection(', body(self.ui, signature))
        normalize = body(self.ui, 'func normalizeSelection()')
        self.assertLess(normalize.index('guard collectionOwner == nil'), normalize.index('normalizeProjectedSelection()'))

    def test_native_refresh_only_touches_visible_matching_cells_without_data_or_layout_mutation(self):
        refresh = body(self.host, 'func applySelection(state: ReplicaUIState)')
        self.assertIn('self.state === state, state.collectionOwner === self', refresh)
        self.assertIn('for (index, cell) in cells', refresh)
        self.assertIn('items.indices.contains(index) && cell.itemID == items[index].id', refresh)
        self.assertIn('cell.isSelected = state.selection.contains(items[index].id)', refresh)
        for forbidden in ['visibleItems', 'items =', 'pendingSnapshot', 'DispatchQueue',
                          'tileCells()', 'layoutCollection()', 'reveal', 'normalizeSelection']:
            self.assertNotIn(forbidden, refresh)

    def test_cell_setter_updates_cache_and_existing_root_signature_immediately(self):
        setter = body(self.host, 'var isSelected: Bool')
        self.assertIn('set { renderedSelection = newValue; updateRoot() }', setter)
        render = body(self.host, 'private func updateRoot()')
        self.assertIn('selected: renderedSelection', render)
        self.assertIn('selectionOverride: renderedSelection', render)
        self.assertLess(render.index('guard renderingSignature != signature'), render.index('hosting.rootView ='))

    def test_search_close_callback_is_an_animation_body_not_a_completion(self):
        proof = json.loads((ROOT / '.local/p0-repair/phase-7/search-animation-correction.json').read_text())
        for ref in proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / ref['path'])[ref['address']]['sha256'], ref['sha256'])
        data = (ROOT / proof['original_binary']['path']).read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), proof['original_binary']['sha256'])
        segment = proof['machine_segment']
        raw = data[segment['file_offset']:segment['file_offset'] + segment['length']]
        self.assertEqual(raw.hex(), segment['hex'])
        self.assertEqual(hashlib.sha256(raw).hexdigest(), segment['sha256'])
        def word(address):
            return struct.unpack_from('<I', data, address - 0x100000000)[0]
        self.assertEqual(word(0x10000e1dc), 0xd2800006)  # MOV x6, #0: completion function nil
        self.assertEqual(word(0x10000e1e0), 0xd2800007)  # MOV x7, #0: completion context nil
        self.assertEqual(word(0x10000e1d0), 0x52800021)  # optional duration nil tag
        self.assertEqual(word(0x10000e1d8), 0x52800023)  # animated=true


if __name__ == '__main__':
    unittest.main()
