"""Applied snapshot, changed-ID delivery and keyboard inputs: source/data only."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from modal_restore_scope_contract import pre_modal_restore


class AppliedSnapshotInputs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ui = pre_modal_restore((ROOT / 'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text())
        cls.host = (ROOT / 'replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift').read_text()
        cls.app = pre_modal_restore((ROOT / 'replica/Sources/Pasto/AppMain.swift').read_text())
        cls.handle = body(cls.ui, 'private func handleKey(_ event: NSEvent) -> Bool')

    def test_original_snapshot_and_shortcut_fragments_remain_bound(self):
        for name in ['.local/p0-repair/phase-3-snapshot-readonly.json',
                     '.local/p0-repair/phase-6/remaining-key-equivalents-proof.json']:
            proof = json.loads((ROOT / name).read_text())
            for ref in proof['original_fragments']:
                self.assertEqual(source_fragments(ROOT / ref['path'])[
                    ref['function_id'].split(':')[1]]['sha256'], ref['sha256'])

    def test_real_store_publisher_feeds_owner_guarded_union_and_draining_take(self):
        store = (ROOT / 'replica/Sources/PastoCore/ClipboardStore.swift').read_text()
        self.assertIn('public var collectionItemUpdates: AnyPublisher<Set<UUID>, Never> { persistence.collectionItemUpdates }', store)
        sink = body(self.ui, 'collectionItemObservation = store.collectionItemUpdates.sink')
        self.assertIn('[weak self]', sink)
        self.assertLess(sink.index('self.collectionOwner != nil'), sink.index('formUnion(identifiers)'))
        self.assertLess(sink.index('formUnion(identifiers)'), sink.index('self.objectWillChange.send()'))
        take = body(self.ui, 'func takeCollectionChangedIDs(owner:')
        self.assertLess(take.index('collectionOwner === owner'), take.index('pendingCollectionChangedIDs.removeAll()'))
        self.assertIn('let identifiers = pendingCollectionChangedIDs', take)
        self.assertIn('return identifiers', take)

    def test_coalescing_preserves_intermediate_changes_even_when_final_values_revert(self):
        update = body(self.host, 'func update(state: ReplicaUIState, cardSide: CGFloat)')
        self.assertIn('let changedIDs = state.takeCollectionChangedIDs(owner: self)', update)
        self.assertIn('pendingSnapshot?.items != incomingItems || !changedIDs.isEmpty', update)
        self.assertIn('(pendingSnapshot?.changedIDs ?? []).union(changedIDs)', update)
        self.assertNotIn('collectionSelectionSnapshot()', update)
        self.assertNotIn('pendingSnapshot?.selection', update)
        # Content equality is not used to reconstruct the set of changed IDs.
        self.assertNotIn('zip(', update)
        self.assertNotIn('filter {', update)

    def test_equal_diff_does_not_deliver_data_callback_but_keeps_layout_and_focus(self):
        drain = body(self.host, 'private func drainCollectionSnapshots()')
        guard = body(drain, 'if !isInitialSnapshot && !selectionRelevantSnapshotChanged && !hasRelevantChanges')
        self.assertIn('restorePendingListFocus(state: state)', guard)
        self.assertIn('continue', guard)
        self.assertNotIn('consumePendingNeighborSelection', guard)
        self.assertLess(drain.index('pendingSnapshot = nil'), drain.index('items = pending.items'))
        self.assertLess(drain.index('layoutCollection()'), drain.index(guard))
        self.assertLess(drain.index(guard), drain.index('state.applyFullCollectionReload'))
        self.assertLess(drain.index('state.applyFullCollectionReload'), drain.index('consumePendingNeighborSelection'))
        self.assertIn('!pending.changedIDs.isDisjoint(with: Set(incomingIDs))', drain)
        self.assertIn('OriginalCollectionSnapshot.requiresFullReload(from: previousIDs, to: incomingIDs)', drain)

    def test_applied_item_getter_checks_owner_without_flushing_pending_data(self):
        getter = body(self.host, 'func appliedItems(for state: ReplicaUIState)')
        self.assertIn('self.state === state, state.collectionOwner === self', getter)
        self.assertIn('return items', getter)
        for forbidden in ['visibleItems', 'update(', 'drainCollectionSnapshots', 'pendingSnapshot']:
            self.assertNotIn(forbidden, getter)
        getter = body(self.ui, 'private func appliedCollectionItems()')
        self.assertIn('collection.window === panel', getter)
        self.assertIn('collection.appliedItems(for: state)', getter)

    def test_numeric_action_reads_applied_items_before_and_after_paste_without_moving_responder(self):
        action = body(self.handle, 'func performQuickPaste(')
        self.assertEqual(action.count('appliedCollectionItems()'), 2)
        self.assertLess(action.index('guard let items = appliedCollectionItems()'), action.index('paste(item:'))
        self.assertLess(action.index('paste(item:'), action.index('if let appliedItems = appliedCollectionItems()'))
        self.assertIn('if items.indices.contains(action.index)', action)
        self.assertIn('state.selectFirstAppliedItem(items: appliedItems)', action)
        self.assertNotIn('visibleItems', action)
        self.assertNotIn('forceDirect', action)
        self.assertNotIn('NSSound.beep', action)
        selection = body(self.ui, 'func selectFirstAppliedItem(items:')
        self.assertIn('selectIndex(0, mode: 0, items: items)', selection)
        self.assertNotIn('makeFirstResponder', selection)

    def test_command_v_is_exact_owner_gated_and_uses_only_applied_selected_ids(self):
        branch = body(self.handle, 'if !isEditing, signature.keyCode == OriginalShortcutFunctions.f_1001e94d4("v")')
        self.assertLess(self.handle.index('if !ownsCollectionFocus'), self.handle.index(branch))
        self.assertIn('signature.modifierRawValue == NSEvent.ModifierFlags.command.rawValue', self.handle)
        self.assertIn('Set((appliedCollectionItems() ?? []).map(\\.id))', branch)
        self.assertIn('orderedIDs.filter { appliedIDs.contains($0) }', branch)
        self.assertIn('if !ids.isEmpty', branch)
        self.assertIn('directPasteItemsHandler(ids, false)', branch)
        self.assertIn('return true', branch)

    def test_forced_service_retains_permission_and_plain_preference_handling(self):
        self.assertIn('ui.directPasteItemsHandler = { [weak self] ids, plain in', self.app)
        self.assertIn('self?.paste(ids: ids, plain: plain, forceDirect: true) ?? false', self.app)
        paste = body(self.app, 'private func paste(ids: [UUID], plain: Bool, forceDirect: Bool = false)')
        self.assertIn('!(forceDirect || store.preferences.pasteToActiveApp)', paste)
        self.assertLess(paste.index('!hasAccessibilityAccess'), paste.index('store.writeToPasteboard'))
        self.assertIn('OriginalPasteToOtherAppsModal.run()', paste)
        self.assertIn('store.preferences.alwaysPastePlainText', paste)
        original = (ROOT / 'decompiled/Paste/part-0035.c').read_text()
        self.assertIn('((local_108 & 1) != 0) || ((local_11c & 1) != 0)', original)
        self.assertIn('local_11c = param_3', original)


if __name__ == '__main__':
    unittest.main()
