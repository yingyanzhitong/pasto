from native_restore_only_scope_contract import pre_native_restore_only
"""Native-selection source checks; no Core Data or pasteboard execution."""
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from supplied_input_scope_contract import pre_supplied_input_adapters
from test_p0_repair_checksum_routing import original_fragment
from resolved_copy_scope_contract import pre_resolved_copy


class PrebuiltRestoreContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-38'
        cls.core = ROOT / 'replica/Sources/PastoCore'
        cls.store = pre_supplied_input_adapters((cls.core / 'ClipboardStore.swift').read_text())
        cls.persistence = pre_native_restore_only((cls.core / 'ClipboardPersistence.swift').read_text())
        cls.pasteboard = pre_resolved_copy((cls.core / 'Pasteboard.swift').read_text())
        cls.writer = body(cls.pasteboard, 'private func writeToPasteboard(ids: [UUID],')
        cls.worker = body(cls.store, 'private func mutateInTransaction<T>(')

    def previous(self, name):
        return (self.phase / 'before/replica/Sources/PastoCore' / name).read_text()

    def test_original_selected_sequence_survives_writer_to_transaction_then_undo(self):
        original = original_fragment((ROOT / 'decompiled/Paste/part-0281.c').read_text(), '10037a144')
        self.assertIn('FUN_10037a144(undefined *param_1,long param_2)', original)
        order = ['FUN_10037875c(puVar6)', 'local_90 = param_1', 'FUN_1002ff310(FUN_10037b620,local_a0)', 'removeAllActions']
        positions = [original.index(t) for t in order]
        self.assertEqual(positions, sorted(positions))

    def test_original_closure_passes_same_captured_sequence_to_repository_witness(self):
        source = (ROOT / 'decompiled/Paste/part-0281.c').read_text()
        thunk = original_fragment(source, '10037b620')
        self.assertIn('FUN_10037ade4(param_1,*(undefined8 *)(unaff_x20 + 0x10),*(undefined8 *)(unaff_x20 + 0x18))', thunk)
        restore = original_fragment(source, '10037ade4')
        for token in ['FUN_100357cf0(', '*(undefined8 *)(param_3 + 0xa0)', 'local_48 = param_2', '*(code **)(lVar4 + 0x28)', '(*pcVar5)(&local_48,uVar3,']:
            self.assertIn(token, restore)

    def test_actual_writer_prepares_objects_before_write_and_consumes_operation_after(self):
        order = ['guard !ids.isEmpty else { return }', 'try reload()', 'let selected = try ids.map',
                 'let selections = try selected.map', 'let restoration = try prepareHistoryRestore(selected)',
                 'writer.f_10037875c(objects)', 'try recordRestoredSelection(restoration)',
                 'removeAllActions()', 'NotificationCenter.default.post', 'didRestoreItem.send()']
        self.assertEqual([self.writer.index(t) for t in order], sorted(self.writer.index(t) for t in order))
        self.assertNotIn('recordRestoredItems(ids)', self.writer)
        self.assertEqual(self.writer.count('prepareHistoryRestore('), 1)

    def test_writer_unchanged_except_native_preparation_and_restore_argument(self):
        previous = self.previous('Pasteboard.swift')
        expected = previous.replace('        let writer = OriginalPasteboardWriter(pasteboard: pasteboard)',
                                    '        let restoration = try prepareHistoryRestore(selected)\n        let writer = OriginalPasteboardWriter(pasteboard: pasteboard)', 1)
        expected = expected.replace('try recordRestoredItems(ids)', 'try recordRestoredSelection(restoration)', 1)
        self.assertEqual(self.pasteboard, expected)

    def test_native_preparation_retains_transaction_and_real_targets_without_save(self):
        selection = body(self.persistence, 'struct HistoryRestoreSelection')
        self.assertIn('let transaction: Transaction', selection)
        self.assertIn('let targets: [(id: UUID, object: NSManagedObject)]', selection)
        prepare = body(self.persistence, 'func prepareHistoryRestore(ids: [UUID])')
        order = ['let transaction = Transaction(context: context)', 'try context.performAndWait',
                 'OriginalObjCExceptionBridge.withResult', 'HistoryRestoreSelection(transaction: transaction,',
                 'targets: try transaction.repository.prepareHistoryItems(ids)']
        self.assertEqual([prepare.index(t) for t in order], sorted(prepare.index(t) for t in order))
        for token in ['context.save()', 'context.reset()', 'context.rollback()', '.async', 'Date()', 'restoreHistoryItems(']:
            self.assertNotIn(token, prepare)

    def test_native_target_mapping_and_timestamp_algorithm_remain_unchanged(self):
        previous = self.previous('ClipboardPersistence.swift')
        for signature in ['func prepareHistoryItems(', 'func restoreHistoryItems(', 'final class Transaction']:
            self.assertEqual(body(self.persistence, signature), body(previous, signature))
        prepare = body(self.persistence, 'func prepareHistoryItems(')
        self.assertIn('return try ids.map { id in', prepare)
        self.assertNotIn('Set(', prepare)
        self.assertIn('for (id, object) in targets.reversed()', body(self.persistence, 'func restoreHistoryItems('))

    def test_store_operation_captures_snapshots_without_reloading_or_saving(self):
        operation = body(self.store, 'struct HistoryRestoreOperation')
        for token in ['let local: StoreState', 'let previous: StoreState', 'let native: ClipboardPersistence.HistoryRestoreSelection']:
            self.assertIn(token, operation)
        prepare = body(self.store, 'func prepareHistoryRestore(_ selected: [ClipboardItem])')
        self.assertLess(prepare.index('try validate(local)'), prepare.index('persistence.prepareHistoryRestore('))
        self.assertIn('guard selected.allSatisfy({ available.contains($0.id) })', prepare)
        self.assertIn('HistoryRestoreOperation(local: local, previous: baseline,', prepare)
        self.assertIn(r'ids: selected.map(\.id)', prepare)
        for token in ['reload()', 'latestState()', 'save()', 'Set(selected', '.async']:
            self.assertNotIn(token, prepare)

    def test_actual_restore_entry_forwards_exact_sequence_and_transaction_without_refetch(self):
        restore = body(self.store, 'func recordRestoredSelection(')
        self.assertIn('guard !operation.native.targets.isEmpty else { return }', restore)
        self.assertIn(r'restoringItemIDs: operation.native.targets.map(\.id)', restore)
        self.assertIn('preparedRestore: operation', restore)
        for token in ['reload()', 'latestState()', 'prepareHistoryItems(', 'fetch(', 'Date()']:
            self.assertNotIn(token, restore)

    def test_prepared_path_short_circuits_store_reload_merge_and_entity_resolution(self):
        for token in ['let local = preparedRestore?.local ?? current',
                      'let remote = try preparedRestore?.previous ?? latestState()',
                      'var state = preparedRestore?.local ?? merge(local, onto: remote)',
                      'preparedTransaction: preparedRestore?.native.transaction',
                      'let targets = try preparedRestore?.native.targets ?? transaction.repository.prepareHistoryItems(restoringItemIDs)']:
            self.assertIn(token, self.worker)
        # Swift ?? lazily evaluates its RHS; these fallbacks remain for ordinary mutations only.
        self.assertEqual(self.worker.count('latestState()'), 1)
        self.assertEqual(self.worker.count('prepareHistoryItems('), 1)

    def test_prepared_commit_reuses_same_container_and_keeps_existing_save_error_boundary(self):
        signature = 'func commit<T>(previous: StoreState?, deletingItemIDs: [UUID] = [],'
        current = body(self.persistence, signature)
        previous = body(self.previous('ClipboardPersistence.swift'), signature)
        checkpoint = (ROOT / '.local/p0-repair/phase-41/before/replica/Sources/PastoCore/ClipboardPersistence.swift').read_text()
        old_commit = body(checkpoint, signature)
        self.assertEqual(old_commit.replace('preparedTransaction ?? Transaction(context: context)', 'Transaction(context: context)', 1), previous)
        order = ['let transaction = preparedTransaction ?? Transaction(context: context)', 'withExtendedLifetime(transaction)',
                 'try context.performAndWait', 'let outcome = try operation(transaction)', 'if context.hasChanges', 'try context.save()']
        self.assertEqual([current.index(t) for t in order], sorted(current.index(t) for t in order))
        for token in ['context.reset()', 'rollback', 'catch', 'try?']:
            self.assertNotIn(token, current)

    def test_legacy_id_restore_and_all_unrelated_store_methods_are_unchanged(self):
        previous = self.previous('ClipboardStore.swift')
        self.assertEqual(body(self.store, 'func recordRestoredItems(_ ids: [UUID])'), body(previous, 'func recordRestoredItems(_ ids: [UUID])'))
        current = (ROOT / '.local/p0-repair/phase-40/before/replica/Sources/PastoCore/ClipboardStore.swift').read_text()
        start = current.index('    struct HistoryRestoreOperation {')
        end = current.index('    private func mutate<T>(', start)
        current = current[:start] + current[end:]
        start = current.index('    func recordRestoredSelection(')
        end = current.index('    public func save()', start)
        current = current[:start] + current[end:]
        start = current.index('    private func mutateInTransaction<T>(')
        end = current.index('    /// Restore promotes', start)
        old_start = previous.index('    private func mutateInTransaction<T>(')
        old_end = previous.index('    /// Restore promotes', old_start)
        current = current[:start] + previous[old_start:old_end] + current[end:]
        self.assertEqual(current, previous)
        latest = (ROOT / '.local/p0-repair/phase-40/before/replica/Sources/PastoCore/ClipboardStore.swift').read_text()
        for signature in ['private func mutateInTransaction<T>(', 'func recordRestoredSelection(', 'func prepareHistoryRestore(']:
            self.assertEqual(body(self.store, signature), body(latest, signature))

    def test_saving_failure_still_joins_undo_and_notification(self):
        tail = self.writer[self.writer.index('        do {'):]
        self.assertIn('try recordRestoredSelection(restoration)', tail)
        self.assertIn('} catch {', tail)
        self.assertLess(tail.index('} catch {'), tail.index('removeAllActions()'))
        self.assertNotIn('return', tail)
        self.assertNotIn('throw', tail)

    def test_original_evidence_and_current_source_snapshot_are_bound(self):
        proof = json.loads((self.phase / 'prebuilt-restore-contract.json').read_text())
        for r in proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / r['path'])[r['address']]['sha256'], r['sha256'])
        for p, digest in proof['current_sources'].items():
            checkpoint = ROOT / '.local/p0-repair/phase-40/before' / p
            self.assertEqual(hashlib.sha256(checkpoint.read_bytes()).hexdigest(), digest)
        self.assertFalse(proof['full_function_migration_verified'])


if __name__ == '__main__':
    unittest.main()
