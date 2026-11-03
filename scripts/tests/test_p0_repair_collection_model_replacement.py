"""Original C/ARM and real source-install paths; no Swift/AppKit execution."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from list_attributes_scope_contract import pre_attributes_host
from test_p0_repair_checksum_routing import original_fragment

UI = 'replica/Sources/Pasto/UI/ReplicaUIController.swift'
HOST = 'replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift'


class CollectionModelReplacement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-24'
        cls.proof = json.loads((cls.phase / 'replacement-root-contract.json').read_text())
        cls.ui = (ROOT / UI).read_text()
        cls.host = (ROOT / HOST).read_text()

    def original(self, address):
        r = next(r for r in self.proof['original_fragments'] if r['address'] == address)
        return original_fragment((ROOT / r['path']).read_text(), address[2:])

    def test_original_fragments_and_machine_data_are_bound(self):
        for r in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / r['path'])[r['address']]['sha256'], r['sha256'])
        raw = (ROOT / self.proof['binary']['path']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), self.proof['binary']['sha256'])
        for r in self.proof['machine_ranges']:
            data = raw[r['file_offset']:r['file_offset'] + r['length']]
            self.assertEqual(data.hex(), r['hex'])
            self.assertEqual(hashlib.sha256(data).hexdigest(), r['sha256'])

    def test_original_new_applier_is_empty_and_its_first_accepted_snapshot_is_full(self):
        constructor = self.original('0x1001b8ddc')
        self.assertIn('_allocateUninitialized(0,uVar5)', constructor)
        self.assertIn('unaff_x20[2] = tVar7._0_8_', constructor)
        self.assertIn('*(undefined4 *)(unaff_x20 + 0xb) = 0', constructor)
        callback = self.original('0x1001b9b78')
        self.assertIn("*(char *)((long)unaff_x20 + 0x5a) == '\\x01'", callback)
        self.assertIn('(*pcVar4)(0,0,0,0', callback)
        view = self.original('0x100223430')
        self.assertIn('if (param_1 == 0)', view)
        self.assertIn('FUN_10022be98()', view)

    def test_original_weak_old_applier_and_weak_update_owner_are_distinct(self):
        queued = self.original('0x1001ba02c')
        self.assertIn('FUN_1001b9ab0(', queued)
        weak = self.original('0x1001b9ab0')
        self.assertIn('_swift_weakLoadStrong()', weak)
        self.assertLess(weak.index('if (pMVar6 != (MainActor *)0x0)'), weak.index('FUN_1001b95bc()'))
        install = self.original('0x100067c84')
        self.assertLess(install.index('PTR___swiftEmptySetSingleton'), install.index('FUN_10022338c()'))
        self.assertIn('*(code **)(lVar16 + 0x18) = FUN_1000765b8', install)
        self.assertNotIn('pendingNeighborSelectionID', install)

    def test_real_replacement_resets_source_data_and_epoch_without_selection_or_focus(self):
        method = body(self.host, 'func replaceCollectionModel(state: ReplicaUIState)')
        order = ['guard self.state === state, state.collectionOwner === self',
                 'collectionOwnerGeneration &+= 1', 'pendingSnapshot = nil',
                 'snapshotDrainScheduled = false', 'hasReceivedCollectionSnapshot = false',
                 'items = []', 'update(state: state, cardSide: cardSide)']
        self.assertEqual([method.index(t) for t in order], sorted(method.index(t) for t in order))
        for text in ['makeFirstResponder', 'applyOrderedSelection', 'cancelPendingNeighborSelection',
                     'consumePendingNeighborSelection', 'drainCollectionSnapshots()', 'scrollView', 'isDrainingSnapshots =']:
            self.assertNotIn(text, method)

    def test_query_and_board_consumers_install_models_instead_of_every_redraw(self):
        installation = body(self.ui, 'private func installSearchQueryDelivery()')
        query = installation[installation.index('collectionQueryObservation = searchQueryChanges'):]
        order = ['.debounce(for: .milliseconds(120)', '.removeDuplicates()',
                 'self.collectionSearchQueryNodes = nodes', 'self.normalizeSelection()',
                 'self.collectionOwner?.replaceCollectionModel(state: self)']
        self.assertEqual([query.index(t) for t in order], sorted(query.index(t) for t in order))
        board = body(self.ui, 'private func applySelectedList(_ id: UUID?)')
        self.assertLess(board.index('normalizeProjectedSelection()'), board.index('replaceCollectionModel(state: self)'))
        cleanup = body(self.ui, 'func normalizeSelection()')
        self.assertNotIn('if let pinboardID, !store.pinboards.contains', cleanup)
        native = body(self.ui, 'private func reconcileTabListSelection()')
        self.assertIn('snapshot.index(of: selected)', native)
        self.assertIn('selectListIdentifier(target.identifier, force: false)', native)
        choose = body(self.ui, 'func chooseBoard(_ id: UUID?)')
        self.assertIn('selectListIdentifier(id?.uuidString ?? ClipboardStore.historyListIdentifier, force: true)', choose)
        delivery = body(self.ui, 'private func installListSelectionDelivery()')
        self.assertIn('self.applySelectedList(id)', delivery)
        self.assertEqual(self.ui.count('.replaceCollectionModel(state: self)'), 2)

    def test_ordinary_data_and_selection_updates_do_not_reset_the_applier(self):
        for signature in ['searchIndex.onUpdate =', 'observation = store.objectWillChange.sink',
                          'private func refreshSearch()', 'private func applyOrderedSelection(']:
            self.assertNotIn('replaceCollectionModel', body(self.ui, signature))
        update = body(self.host, 'func update(state: ReplicaUIState, cardSide: CGFloat)')
        reset = body(update.split('        self.state = state', 1)[0], 'if replacesState')
        self.assertIn('items = []', reset)
        self.assertNotIn('hasReceivedCollectionSnapshot = false', update.replace(reset, ''))
        self.assertNotIn('collectionOwnerGeneration &+= 1', update.replace(reset, ''))
        self.assertNotIn('replaceCollectionModel', update)

    def test_old_queued_epoch_cannot_consume_or_unschedule_the_new_source(self):
        schedule = body(self.host, 'private func scheduleSnapshotDrain()')
        self.assertIn('[weak self]', schedule)
        self.assertLess(schedule.index('self.collectionOwnerGeneration == ownerGeneration'),
                        schedule.index('self.snapshotDrainScheduled = false'))
        drain = body(self.host, 'private func drainCollectionSnapshots()')
        self.assertIn('while collectionOwnerGeneration == ownerGeneration', drain)
        self.assertIn('defer {\n            isDrainingSnapshots = false\n            scheduleSnapshotDrain()', drain)
        replacement = body(self.host, 'func replaceCollectionModel(state: ReplicaUIState)')
        self.assertNotIn('isDrainingSnapshots = false', replacement)

    def test_same_identity_source_counterexample_is_tied_to_before_reset_gate(self):
        old_host = (self.phase / 'before' / HOST).read_text()
        self.assertNotIn('func replaceCollectionModel(', old_host)
        old_query = body((self.phase / 'before' / UI).read_text(), 'collectionQueryObservation = searchQueryChanges')
        self.assertNotIn('replaceCollectionModel', old_query)
        case = self.proof['source_gate_counterexample']
        self.assertEqual(case['before_applied_ids'], case['next_source_ids'])
        self.assertEqual(case['before_selected'], ['B'])
        self.assertEqual(case['original_selected'], ['A'])
        self.assertEqual(case['after_selected'], ['A'])
        self.assertFalse(case['ui_state_identity_changes'])
        self.assertEqual(case['classification'], 'source_contract_case_not_runtime_reproduction')

    def test_existing_drain_and_weak_onupdate_delivery_are_reused(self):
        before = (self.phase / 'before' / HOST).read_text()
        for signature in ['private func scheduleSnapshotDrain()', 'private func drainCollectionSnapshots()', 'func detachObservers()']:
            self.assertEqual(body(before, signature), body(pre_attributes_host(self, self.host), signature))
        old_ui = (self.phase / 'before' / UI).read_text()
        for signature in ['func applyFullCollectionReload(items:', 'func applyIncrementalCollectionSnapshot(items:',
                          'func consumePendingNeighborSelection(token:']:
            self.assertEqual(body(old_ui, signature), body(self.ui, signature))

    def test_conditional_boundaries_are_retained_instead_of_full_migration_claim(self):
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertEqual(self.proof['contracts'][0]['function_id'], 'Paste:0x100067c84')
        self.assertTrue(self.proof['retained_partial_contracts'])
        self.assertTrue(self.proof['adaptations'])
        self.assertIn('double_reset_on_stale_board_query', self.proof['retained_source_cases'])


if __name__ == '__main__':
    unittest.main()
