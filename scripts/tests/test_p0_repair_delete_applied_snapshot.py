"""Original C/ARM and production call-chain checks; no native execution."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment

UI = 'replica/Sources/Pasto/UI/ReplicaUIController.swift'
HOST = 'replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift'


class DeleteAppliedSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-21'
        cls.proof = json.loads((cls.phase / 'data-delete-root-contract.json').read_text())
        cls.ui = (ROOT / UI).read_text()
        cls.host = (ROOT / HOST).read_text()

    def original(self, address):
        r = next(r for r in self.proof['original_fragments'] if r['address'] == address)
        return original_fragment((ROOT / r['path']).read_text(), address[2:])

    def test_original_fragments_are_bound(self):
        for r in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / r['path'])[r['address']]['sha256'], r['sha256'])

    def test_actual_selected_indexes_call_and_thunk_are_bound(self):
        raw = (ROOT / self.proof['binary']['path']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), self.proof['binary']['sha256'])
        for r in self.proof['machine_ranges']:
            data = raw[r['file_offset']:r['file_offset'] + r['length']]
            self.assertEqual(hashlib.sha256(data).hexdigest(), r['sha256'])
            self.assertEqual(data.hex(), r['hex'])
        # BL thunk -> B actual selected-index getter; caller consumes returned x0.
        self.assertEqual(raw[0x68ddc:0x68de0].hex(), 'd5060794')
        self.assertEqual(raw[0x22a930:0x22a934].hex(), '27020014')
        self.assertEqual(raw[0x68dec:0x68df0].hex(), '150840f9')
        self.assertIn('___lazy_storage___cellSelectionManager', self.original('0x10022b1cc'))

    def test_original_delete_resolves_indexes_against_applier_before_confirmation(self):
        f = self.original('0x100068db8')
        order = ['thunk_FUN_10022b1cc()', '_TtC5Paste18ItemCollectionView::applier',
                 'FUN_1001b9698(&local_70,uVar21', 'FUN_1003ba464',
                 'FUN_1000691c8()', 'FUN_1003ba5c4(&local_68']
        positions = [f.index(t) for t in order]
        self.assertEqual(positions, sorted(positions))
        lookup = self.original('0x1001b9698')
        self.assertIn('local_80 = unaff_x20[2]', lookup)
        self.assertIn('(param_2 < local_98) || (local_90 <= param_2)', lookup)
        self.assertIn('get_subscript(lVar4,param_2,unaff_x20[2],lVar2)', lookup)

    def test_delete_uses_live_owner_applied_snapshot_without_projection_fallback(self):
        f = body(self.ui, 'func deleteSelection()')
        order = ['guard let before = collectionOwner?.appliedItems(for: self)',
                 'guard !hasPendingDeletion', 'cancelPendingNeighborSelection()',
                 'let visibleIDs = Set(before.map(\\.id))',
                 'let orderedIDs = orderedSelectionIDs.filter', 'ItemDeletionRequest(']
        self.assertEqual([f.index(t) for t in order], sorted(f.index(t) for t in order))
        for token in ['visibleItems', 'selectedItems', 'primaryItem', 'store.items', 'async']:
            self.assertNotIn(token, f)
        applied = body(self.host, 'func appliedItems(for state: ReplicaUIState)')
        self.assertIn('guard self.state === state, state.collectionOwner === self', applied)
        self.assertIn('return items', applied)

    def test_order_neighbor_and_request_share_the_same_applied_items(self):
        f = body(self.ui, 'func deleteSelection()')
        self.assertIn('selection.contains($0) && visibleIDs.contains($0)', f)
        self.assertIn('let indexes = before.indices.filter { ids.contains(before[$0].id) }', f)
        self.assertIn('neighborID = [last + 1, first - 1].first', f)
        self.assertIn('before.indices.contains($0) && !ids.contains(before[$0].id)', f)
        self.assertIn('beforeIDs: before.map(\\.id), neighborID: neighborID', f)
        original = self.original('0x1000691c8')
        self.assertIn('local_70[0] = lVar5 + 1', original)
        self.assertIn('local_70[1] = lVar16 + -1', original)
        self.assertIn('_TtC5Paste18ItemCollectionView::applier', original)

    def test_phase21_delete_patch_is_bound_and_delete_method_remains_unchanged(self):
        before = (self.phase / 'before' / UI).read_text()
        old = body(before, 'func deleteSelection()')
        expected = old.replace('guard collectionOwner != nil else { return }',
            'guard let before = collectionOwner?.appliedItems(for: self) else { return }')
        expected = expected.replace('        let before = visibleItems\n', '')
        expected = expected.replace('// 0x100068db8 deletes selected indexes, never a fallback primary item.',
            '// 0x100068db8 resolves selected indexes and their neighbor in the applied\n'
            '        // collection, before a queued query result replaces that snapshot.')
        current = body(self.ui, 'func deleteSelection()')
        lazy_before = (ROOT / '.local/p0-repair/phase-29/before' / UI).read_text()
        self.assertEqual(expected, body(lazy_before, 'func deleteSelection()'))
        self.assertEqual(expected.replace('controller?.panel.makeFirstResponder(nil)',
                                          'controller?.clearPanelFirstResponder()'), current)
        checkpoint = ROOT / '.local/p0-repair/phase-22/before' / UI
        frozen_report = json.loads((ROOT / 'reports/replica/p0-p1-repair-round21.json').read_text())
        self.assertEqual(hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
                         frozen_report['current_production_hashes'][UI])
        self.assertEqual(before.replace(old, expected, 1), checkpoint.read_text())

    def test_history_chain_reuses_existing_store_list_and_transaction_methods(self):
        for p in self.proof['reused_current_sources']:
            current = ROOT / p
            if p.endswith('ClipboardListPersistence.swift'):
                current = ROOT / '.local/p0-repair/phase-40/before' / p
            if p in ['replica/Sources/PastoCore/ClipboardStore.swift',
                     'replica/Sources/PastoCore/ClipboardPersistence.swift']:
                current = ROOT / '.local/p0-repair/phase-31/before' / p
            if p.endswith('OriginalPinboardAttributes.swift'):
                for marker in ['private static func f_1003245fc(', 'public static func colorCode(', 'public static func clipboardCapacity(', 'static func encodedClipboard(', 'static func encoded(colorCode:', 'static func parsedColorCode(']:
                    self.assertEqual(body(current.read_text(), marker), body((self.phase / 'before' / p).read_text(), marker))
            else:
                self.assertEqual(current.read_bytes(), (self.phase / 'before' / p).read_bytes())
        store = (ROOT / 'replica/Sources/PastoCore/ClipboardStore.swift').read_text()
        restore = body(store, 'func recordRestoredItems(_ ids: [UUID])')
        self.assertIn('try mutate(historyAction: true, restoringItemIDs: ids)', restore)
        persistence = (ROOT / 'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text()
        native_restore = body(persistence, 'func restoreHistoryItems(')
        self.assertIn('for (id, object) in targets.reversed()', native_restore)
        self.assertIn('let timestamp = Date()', native_restore)
        mutate = body(store, 'private func mutateInTransaction<T>(historyAction: Bool = false,')
        self.assertIn('if let capacity = lists.historyCapacity(of: history)', mutate)
        self.assertIn('expireHistory(&state, capacity: capacity)', mutate)
        lists = (ROOT / 'replica/Sources/PastoCore/ClipboardListPersistence.swift').read_text()
        self.assertIn('context.refresh(history, mergeChanges: true)', body(lists, 'func refreshHistoryIfNeeded()'))
        commit = body((ROOT / 'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text(),
                      'func commit<T>(previous: StoreState?, deletingItemIDs: [UUID] = [],')
        self.assertLess(commit.index('try transaction.repository.lists.refreshHistoryIfNeeded()'),
                        commit.index('if context.hasChanges'))

    def test_network_shared_permission_is_not_claimed_as_migrated(self):
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertEqual(self.proof['contracts'][0]['function_id'], 'Paste:0x100068db8')
        self.assertTrue(self.proof['retained_partial_contracts'])
        f = self.original('0x1003ba4d0')
        self.assertIn('objc_stub::list(self)', f)
        self.assertIn('FUN_1003250f0()', f)
        self.assertIn('FUN_100328f38()', f)


if __name__ == '__main__':
    unittest.main()
