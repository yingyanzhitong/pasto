"""Selected live payloads use the applied epoch; source-only, not native execution."""
from native_title_scope_contract import NEW_PATH as NATIVE_TITLE_PATH
from item_observation_scope_contract import NEW_PATH as ITEM_OBSERVATION_PATH
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts/tests')]
from test_offline_p0_contracts import body
from collection_membership_scope_contract import ENTRY_PATH, pre_collection_membership_bytes
from modal_restore_scope_contract import RESTORE_ITEM_PATH, pre_modal_restore, pre_modal_restore_bytes
from live_item_selection_scope_contract import pre_live_selection
from resolved_copy_scope_contract import pre_resolved_copy, pre_resolved_copy_bytes


class LiveItemSelectionContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-75'
        cls.proof = json.loads((cls.phase / 'live-selection-contract.json').read_text())
        cls.base = json.loads((cls.phase / 'baseline.json').read_text())
        cls.paths = dict(host='replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift',
                         ui='replica/Sources/Pasto/UI/ReplicaUIController.swift')
        cls.source = {k: pre_resolved_copy((ROOT / p).read_text()) for k, p in cls.paths.items()}

    def before(self, key): return (self.phase / 'before' / self.paths[key]).read_text()

    def test_original_live_getter_evidence_and_two_production_sources_are_bound(self):
        old = self.proof['original_proof']
        self.assertEqual(hashlib.sha256((ROOT / old['path']).read_bytes()).hexdigest(), old['sha256'])
        for path, digest in self.proof['current_sources'].items():
            self.assertEqual(hashlib.sha256(pre_resolved_copy_bytes(ROOT / path)).hexdigest(), digest)
            self.assertEqual(pre_resolved_copy_bytes(ROOT / path), (self.phase / 'after' / path).read_bytes())

    def test_host_owner_gate_precedes_applied_identity_lookup(self):
        selected = body(self.source['host'], 'func appliedSelectedItems(for state:')
        self.assertIn('guard self.state === state, state.collectionOwner === self else { return nil }', selected)
        self.assertLess(selected.index('guard self.state === state'), selected.index('let positions ='))
        self.assertIn('items.enumerated().map { ($0.element.id, $0.offset) }', selected)
        for token in ['visibleItems', 'collectionItemReferences', 'store.items', 'pendingSnapshot', 'source.value']:
            self.assertNotIn(token, selected)

    def test_requested_order_and_missing_ID_filter_precede_selected_only_live_read(self):
        selected = body(self.source['host'], 'func appliedSelectedItems(for state:')
        order = ['return orderedIDs.compactMap', 'guard let index = positions[identifier] else { return nil }',
                 'return renderedItem(at: index)']
        self.assertEqual([selected.index(t) for t in order], sorted(selected.index(t) for t in order))
        for token in ['.sorted', 'Set(orderedIDs)', 'items.map { renderedItem', 'items.indices.map', 'save(', 'reset(']:
            self.assertNotIn(token, selected)

    def test_state_selection_filters_active_selection_and_uses_applied_owner_without_projection_fallback(self):
        selected = body(self.source['ui'], 'var selectedItems:')
        self.assertIn('let ids = orderedSelectionIDs.filter { selection.contains($0) }', selected)
        self.assertIn('if let collectionOwner { return collectionOwner.appliedSelectedItems(for: self, orderedIDs: ids) ?? [] }', selected)
        self.assertLess(selected.index('if let collectionOwner'), selected.index('let byID ='))
        self.assertNotIn('if let items = collectionOwner?', selected)

    def test_ownerless_projection_resolves_only_selected_members_with_current_handles(self):
        selected = body(self.source['ui'], 'var selectedItems:')
        self.assertIn('let references = collectionItemReferences', selected)
        self.assertIn('return ids.compactMap', selected)
        self.assertLess(selected.index('guard let item = byID[identifier] else { return nil }'),
                        selected.index('references[identifier]?.requiredItem() ?? item'))
        self.assertNotIn('visibleItems.map { $0.requiredItem', selected)

    def test_controller_selection_uses_existing_panel_actual_window_and_applied_host(self):
        selected = body(self.source['ui'], 'private func appliedSelectionItems()')
        for token in ['guard let panel = loadedPanel', 'collectionFocusTarget as? ReplicaNativeCollectionHost',
                      'collection.window === panel else { return [] }', 'collection.appliedSelectedItems(for: state,',
                      'orderedIDs: state.collectionSelectionSnapshot().orderedIDs) ?? []']:
            self.assertIn(token, selected)
        for token in ['visibleItems', 'store.items', 'appliedCollectionItems()', 'ensurePanel', '.sorted']:
            self.assertNotIn(token, selected)

    def test_copy_and_paste_keep_existing_empty_guards_and_ID_dispatch(self):
        for signature in ['func copySelection(plainTextOnly:', 'func pasteSelection(plainTextOnly:',
                          'func copy(ids:', 'func paste(ids:', 'private func performCopy(']:
            self.assertEqual(body(self.source['ui'], signature), body(self.before('ui'), signature))
        copy = body(self.source['ui'], 'func copySelection(plainTextOnly:')
        self.assertIn('let items = appliedSelectionItems()', copy)
        self.assertIn('guard !items.isEmpty else { NSSound.beep(); return }', copy)

    def test_open_edit_write_and_space_keep_real_applied_selection_consumers(self):
        ui = self.source['ui']
        self.assertIn('let selected = appliedSelectionItems()', body(ui, 'private func openAppliedSelection()'))
        self.assertIn('appliedSelectionItems().filter', body(ui, 'private func writeAppliedSelection()'))
        keys = body(ui, 'private func handleKey(')
        self.assertIn('editItems(appliedSelectionItems())', keys)
        self.assertIn('appliedSelectionItems().last', keys)
        self.assertEqual(keys, body(self.before('ui'), 'private func handleKey('))

    def test_drag_reads_selected_live_values_at_applied_preview_indexes(self):
        drag = body(self.source['host'], 'private func beginNativeDrag(')
        order = ['let positions = Dictionary', 'let indexes = state.orderedSelectionIDs.filter',
                 'let selected = indexes.map { renderedItem(at: $0) }', 'dragPasteboardGroups(for: selected',
                 'selected.map { ReplicaNativeDragItemReference($0) }', 'zip(indexes, draggingWriters)']
        self.assertEqual([drag.index(t) for t in order], sorted(drag.index(t) for t in order))
        self.assertNotIn('drainCollectionSnapshots()', drag)
        self.assertNotIn('state.visibleItems', drag)

    def test_metadata_applier_and_all_other_methods_are_preserved(self):
        for key in self.paths:
            self.assertEqual(pre_live_selection(self.source[key]), self.before(key))
        for signature in ['func appliedItems(', 'private func drainCollectionSnapshots()', 'private func tileCells()']:
            self.assertEqual(body(self.source['host'], signature), body(self.before('host'), signature))
        self.assertEqual(body(self.source['ui'], 'var visibleItems:'), body(self.before('ui'), 'var visibleItems:'))

    def test_only_two_existing_UI_files_change_without_provider_model_or_writer_edits(self):
        sha = lambda p: hashlib.sha256(pre_resolved_copy_bytes(ROOT / p)).hexdigest()
        self.assertEqual({p for p, h in self.base['production'].items() if sha(p) != h}, set(self.paths.values()))
        self.assertEqual({str(p.relative_to(ROOT)) for p in (ROOT / 'replica/Sources').rglob('*') if p.is_file()} - {NATIVE_TITLE_PATH, ITEM_OBSERVATION_PATH} - {RESTORE_ITEM_PATH, ENTRY_PATH}, set(self.base['production']))
        for p in ['replica/Package.swift', 'package.json']:
            self.assertEqual(sha(p), self.base['other'][p])

    def test_restoration_writer_and_metadata_gap_are_not_marked_complete(self):
        writer = (ROOT / 'replica/Sources/PastoCore/Pasteboard.swift').read_text()
        restore = body(writer, 'private func writeToPasteboard(ids:')
        self.assertIn('try reload()', restore)
        self.assertIn('items.first(where:', restore)
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertEqual(self.proof['remaining_confirmed_differences'], ['Paste:0x1003544dc'])
        self.assertEqual(self.proof['repaired_finite_contracts'], [])


if __name__ == '__main__':
    unittest.main()
