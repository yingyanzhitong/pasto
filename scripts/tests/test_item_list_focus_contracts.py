"""Production source and bound decompiler checks; no Swift or app execution."""
import hashlib
import json
import unittest
from pathlib import Path
from test_offline_p0_contracts import body

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / 'replica/Sources/Pasto/UI'


class ItemListFocusContracts(unittest.TestCase):
    def setUp(self):
        self.state = (UI / 'ReplicaUIController.swift').read_text()
        self.host = (UI / 'ReplicaNativeCardCollection.swift').read_text()

    def test_real_keyboard_route_uses_exact_command_g_and_propagates_no_target(self):
        handler = body(self.state, 'private func handleKey(_ event:')
        route = handler[handler.index('if !isEditing, signature.keyCode == OriginalShortcutFunctions.f_1001e94d4("g")'):]
        route = route[:route.index('\n        if signature.keyCode')]
        self.assertIn('signature.modifierRawValue == NSEvent.ModifierFlags.command.rawValue', route)
        self.assertIn('return revealSelectedItemInList()', route)
        self.assertNotIn('contains(', route)
        reveal = body(self.state, 'private func revealSelectedItemInList()')
        self.assertIn('guard !lists.isEmpty, let input = appliedRestoreItems().first else { return false }', reveal)
        self.assertNotIn('selectedItems', reveal)
        self.assertNotIn('resolvedItem', reveal)
        self.assertNotIn('beep()', reveal)

    def test_single_item_candidates_use_history_then_owner_excluding_current_scope(self):
        candidates = body(self.state, 'func selectedItemTargetLists()')
        self.assertIn('guard inputs.count == 1 else { return [] }', candidates)
        self.assertIn('collectionOwner.appliedRestoreItems(for: self, orderedIDs: ids)', candidates)
        native = body(candidates, 'if let membership = input.listNavigationMembership()')
        self.assertIn('membership.isInHistory, isSearching || pinboardID != nil', native)
        self.assertIn('isSearching || ownerID != pinboardID', native)
        self.assertLess(native.index('lists.append(nil)'), native.index('lists.append(ownerID)'))
        self.assertNotIn('resolvedItem', native)
        self.assertNotIn('store.', native)
        self.assertIn('let isSearching = !isCollectionSearchQueryEmpty', candidates)
        self.assertIn('if item.isInHistory, isSearching || pinboardID != nil { lists.append(nil) }', candidates)
        self.assertIn('store.pinboardOwner(for: item), owner.rawType == 2', candidates)
        self.assertIn('isSearching || owner.id != pinboardID', candidates)
        self.assertLess(candidates.index('lists.append(nil)'), candidates.index('lists.append(owner.id)'))
        self.assertNotIn('pinboardIDs.first', candidates)

    def test_capture_precedes_callback_and_only_locator_clears_query(self):
        reveal = body(self.state, 'private func revealSelectedItemInList()')
        self.assertLess(reveal.index('horizontalOffsetForVisibleItem'), reveal.index('state.pendingListFocus ='))
        self.assertLess(reveal.index('state.pendingListFocus ='), reveal.index('state.chooseListForItemReveal'))
        choose = body(self.state, 'func chooseListForItemReveal(_ id:')
        self.assertLess(choose.index('applySearchInput(nodes: [], text: "", filters: [])'), choose.index('chooseBoard(id)'))
        ordinary = body(self.state, 'func chooseBoard(_ id:')
        self.assertNotIn('applySearchInput', ordinary)
        self.assertNotIn('query =', ordinary)

    def test_pending_focus_waits_for_context_then_clears_before_resolving_new_snapshot(self):
        consume = body(self.state, 'func consumePendingListFocus(itemIDs:')
        self.assertIn('isCollectionSearchQueryEmpty', consume)
        self.assertIn('!showDeleted, pinboardID == request.pinboardID else { return nil }', consume)
        self.assertLess(consume.index('pinboardID =='), consume.index('pendingListFocus = nil'))
        self.assertLess(consume.index('pendingListFocus = nil'), consume.index('itemIDs.firstIndex(of: request.itemID)'))
        self.assertIn('applyOrderedSelection([request.itemID], anchor: request.itemID, primary: request.itemID)', consume)
        self.assertNotIn('revealSelection(', consume)
        self.assertNotIn('visibleItems.first', consume)

    def test_offset_requires_live_cell_and_uses_viewport_relative_min_x(self):
        capture = body(self.host, 'func horizontalOffsetForVisibleItem(_ itemID:')
        self.assertIn('visibleSelectionAnchor(at: index, itemID: itemID)', capture)
        self.assertIn('else { return nil }', capture)
        self.assertIn('cell.frame.minX - scrollView.contentView.bounds.minX', capture)
        self.assertNotIn('cardFrame(', capture)
        anchor = body(self.host, 'func visibleSelectionAnchor(at index:')
        for guard in ['items[index].id == itemID', 'cell.itemID == itemID', 'cell.superview === document', 'cell.window === window']:
            self.assertIn(guard, anchor)

    def test_update_consumes_matching_snapshot_after_swiftui_transaction_without_timer(self):
        update = body(self.host, 'func update(state: ReplicaUIState, cardSide: CGFloat)')
        self.assertIn('let incomingItems = state.visibleItems', update)
        self.assertIn('pendingSnapshot = PendingSnapshot(items: incomingItems', update)
        self.assertIn('scheduleSnapshotDrain()', update)
        self.assertNotIn('items = incomingItems', update)
        schedule = body(self.host, 'private func scheduleSnapshotDrain()')
        self.assertIn('DispatchQueue.main.async { [weak self]', schedule)
        self.assertIn('self.collectionOwnerGeneration == ownerGeneration', schedule)
        self.assertIn('self.drainCollectionSnapshots()', schedule)
        drain = body(self.host, 'private func drainCollectionSnapshots()')
        self.assertIn('self.state === state', drain)
        self.assertIn('state.collectionOwner === self', drain)
        self.assertLess(drain.index('items = pending.items'), drain.index('layoutCollection()'))
        self.assertIn('state.pinboardID == request.pinboardID', drain)
        self.assertLess(drain.index('needsPrimaryReveal = false'), drain.index('layoutCollection()'))
        self.assertLess(drain.index('layoutCollection()'), drain.index('restorePendingListFocus(state: state)'))
        restore = body(self.host, 'private func restorePendingListFocus(state:')
        self.assertLess(restore.index('itemIDs == state.visibleItems.map('), restore.index('state.consumePendingListFocus('))
        self.assertLess(restore.index('state.consumePendingListFocus('), restore.index('lastPrimaryID = state.primaryID'))
        self.assertIn('needsPrimaryReveal = false', restore)
        self.assertIn('x: cardFrame(pendingFocus.index).minX - offset, y: 0', restore)
        self.assertIn('revealPrimaryCard(at: pendingFocus.index, animated: false)', restore)
        for wrong in ['Timer', 'asyncAfter', 'scrollAnimator.setContentOffset', 'min(max(', 'max(0,']:
            self.assertNotIn(wrong, update + schedule + drain + restore)

    def test_bound_original_fragments_match_current_files_and_expose_real_consumers(self):
        report = json.loads((ROOT / 'reports/replica/offline-migration-p0-round13.json').read_text())
        for row in report['functions']:
            address = row['function_id'].split(':')[1]
            text = (ROOT / row['original']['path']).read_text()
            start = text.index('/* Address: ' + address + ' |')
            end = text.find('/* Address:', start + 1)
            fragment = text[start:end if end != -1 else None].rstrip() + '\n'
            self.assertEqual(hashlib.sha256(fragment.encode()).hexdigest(), row['original']['sha256'])
            for ref in row['source_references']:
                self.assertIn(ref['symbol'], (ROOT / ref['path']).read_text())
        key = (ROOT / 'decompiled/Paste/part-0035.c').read_text()
        self.assertIn('FUN_1003b83c4(_Var31.unknown,lVar26,puVar46,puVar30)', key)
        self.assertIn('FUN_10006c338(uVar39,uVar42)', key)
        self.assertIn('FUN_100228c78(plVar12,0,0)', key)
        self.assertIn('FUN_10022cce0(uVar20,plVar12)', key)


if __name__ == '__main__':
    unittest.main()
