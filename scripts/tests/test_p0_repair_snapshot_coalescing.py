"""Original queue/drain and current production wiring, static data/source checks only."""
import hashlib
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body

class SnapshotCoalescing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=(ROOT/'replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift').read_text()
        cls.original=json.loads((ROOT/'.local/p0-repair/phase-3-snapshot-readonly.json').read_text())

    def test_original_queue_and_clear_before_apply_are_bound_to_actual_binary(self):
        for r in self.original['original_fragments']:
            self.assertEqual(source_fragments(ROOT/r['path'])[r['function_id'].split(':')[1]]['sha256'],r['sha256'])
        data=(ROOT/'.local/paste-arm64-static.bin').read_bytes()
        for r in self.original['supporting_arm_evidence']:
            actual=data[r['file_offset']:r['file_offset']+r['length']]
            self.assertEqual(actual.hex(),r['bytes'])
            self.assertEqual(hashlib.sha256(actual).hexdigest(),r['sha256'])
        original=(ROOT/'decompiled/Paste/part-0146.c').read_text()
        start=original.index('void FUN_1001b95bc(')
        fragment=original[start:original.index('/* Address:',start)]
        self.assertLess(fragment.index('*(long *)(unaff_x20 + 0x48) = 0'),fragment.index('FUN_1001b9b78(lVar1,uVar2)'))
        self.assertIn('lVar1 = *(long *)(unaff_x20 + 0x48)',fragment)

    def test_producer_only_replaces_pending_snapshot_without_consuming_initial_state(self):
        update=body(self.source,'func update(state: ReplicaUIState, cardSide: CGFloat)')
        self.assertIn('pendingSnapshot = PendingSnapshot(items: incomingItems',update)
        self.assertIn('if pendingSnapshot?.items != incomingItems',update)
        self.assertNotIn('hasReceivedCollectionSnapshot = true',update)
        self.assertNotIn('items = incomingItems',update)
        self.assertNotIn('applyFullCollectionReload',update)
        self.assertNotIn('pendingSnapshot?.selection',update)
        self.assertNotIn('collectionSelectionSnapshot()',update)
        self.assertIn('scheduleSnapshotDrain()',update)

    def test_one_main_queue_drain_uses_owner_epoch_not_each_snapshot_generation(self):
        schedule=body(self.source,'private func scheduleSnapshotDrain()')
        self.assertIn('!snapshotDrainScheduled, !isDrainingSnapshots, pendingSnapshot != nil',schedule)
        self.assertLess(schedule.index('snapshotDrainScheduled = true'),schedule.index('DispatchQueue.main.async'))
        self.assertLess(schedule.index('self.collectionOwnerGeneration == ownerGeneration'),schedule.index('self.snapshotDrainScheduled = false'))
        self.assertIn('self.drainCollectionSnapshots()',schedule)
        self.assertNotIn('collectionSnapshotGeneration',self.source)

    def test_drain_clears_slot_before_applying_and_rechecks_after_callbacks(self):
        drain=body(self.source,'private func drainCollectionSnapshots()')
        self.assertIn('!isDrainingSnapshots',drain)
        self.assertIn('while collectionOwnerGeneration == ownerGeneration',drain)
        self.assertIn('let pending = pendingSnapshot',drain)
        self.assertLess(drain.index('pendingSnapshot = nil'),drain.index('items = pending.items'))
        self.assertLess(drain.index('let previousIDs = items.map'),drain.index('items = pending.items'))
        self.assertLess(drain.index('items = pending.items'),drain.index('state.applyFullCollectionReload'))
        self.assertLess(drain.index('state.applyFullCollectionReload'),drain.index('consumePendingNeighborSelection'))
        self.assertIn('defer {\n            isDrainingSnapshots = false\n            scheduleSnapshotDrain()',drain)
        self.assertNotIn('DispatchQueue.main.async',drain)

    def test_empty_first_and_large_then_small_compare_against_last_applied_snapshot(self):
        drain=body(self.source,'private func drainCollectionSnapshots()')
        self.assertLess(drain.index('let isInitialSnapshot = !hasReceivedCollectionSnapshot'),drain.index('hasReceivedCollectionSnapshot = true'))
        self.assertIn('isInitialSnapshot || (selectionRelevantSnapshotChanged',drain)
        self.assertIn('OriginalCollectionSnapshot.requiresFullReload(from: previousIDs, to: incomingIDs)',drain)
        self.assertNotIn('!pending.items.isEmpty',drain)
        self.assertIn('if requiresReload {\n                state.applyFullCollectionReload(items: items)',drain)
        self.assertNotIn('ifSelectionUnchangedFrom',drain)

    def test_owner_replacement_and_detach_cancel_old_queue_only(self):
        update=body(self.source,'func update(state: ReplicaUIState, cardSide: CGFloat)')
        reset=body(update.split('        self.state = state', 1)[0],'if replacesState')
        for text in ['collectionOwnerGeneration &+= 1','pendingSnapshot = nil','snapshotDrainScheduled = false','hasReceivedCollectionSnapshot = false']:
            self.assertIn(text,reset)
        self.assertEqual(update.count('collectionOwnerGeneration &+= 1'),1)
        detach=body(self.source,'func detachObservers()')
        for text in ['collectionOwnerGeneration &+= 1','pendingSnapshot = nil','state.collectionOwner === self']:
            self.assertIn(text,detach)

    def test_weak_owner_is_rechecked_after_layout_and_before_on_update(self):
        drain=body(self.source,'private func drainCollectionSnapshots()')
        after_layout=drain[drain.index('layoutCollection()'):drain.index('if requiresReload {')]
        self.assertIn('collectionOwnerGeneration == ownerGeneration, self.state === state',after_layout)
        self.assertIn('state.collectionOwner === self else { continue }',after_layout)
        callback=drain[drain.index('// f1b9b78 calls onUpdate'):]
        self.assertLess(callback.index('state.collectionOwner === self'),callback.index('consumePendingNeighborSelection'))
        schedule=body(self.source,'private func scheduleSnapshotDrain()')
        self.assertIn('[weak self]',schedule)
        focus=body(self.source,'private func restorePendingListFocus(state: ReplicaUIState)')
        self.assertIn('self.state === state, state.collectionOwner === self',focus)

    def test_preview_adapter_flush_is_separate_from_applied_input_reveal(self):
        method=body(self.source,'func previewAnchor(for itemID:')
        self.assertLess(method.index('update(state: state'),method.index('drainCollectionSnapshots()'))
        self.assertLess(method.index('drainCollectionSnapshots()'),method.index('items.firstIndex'))
        reveal=body(self.source,'func revealSelection(state:')
        self.assertIn('self.state === state, state.collectionOwner === self',reveal)
        self.assertLess(reveal.index('items.firstIndex'),reveal.index('revealPrimaryCard(at: index'))
        self.assertNotIn('update(state:',reveal)
        self.assertNotIn('drainCollectionSnapshots()',reveal)
        update=body(self.source,'func update(state: ReplicaUIState, cardSide: CGFloat)')
        self.assertNotIn('drainCollectionSnapshots()',update)

if __name__=='__main__':unittest.main()
