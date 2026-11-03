"""Native transaction/error scope against original C/ARM. No Swift/framework execution."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body as current_body
from snapshot_read_scope_contract import body, projection_spelling
from test_p0_repair_checksum_routing import original_fragment


class TransactionErrorContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-14'
        cls.proof = json.loads((cls.phase / 'transaction-error-proof.json').read_text())
        cls.persistence = (ROOT / 'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text()
        cls.commit = body(cls.persistence, 'func commit<T>(previous: StoreState?, deletingItemIDs: [UUID] = [],')

    def test_original_transaction_and_save_fragments_are_bound(self):
        for r in self.proof['original_fragments']:
            address = r.get('address') or r['function_id'].split(':')[-1]
            self.assertEqual(source_fragments(ROOT / r['path'])[address]['sha256'], r['sha256'])

    def test_original_operation_error_exit_and_save_machine_ranges_are_bound(self):
        binary = (ROOT / self.proof['original_binary']['path']).read_bytes()
        self.assertEqual(hashlib.sha256(binary).hexdigest(), self.proof['original_binary']['sha256'])
        for r in self.proof['machine_evidence']:
            start, end = (int(a, 16) for a in r['range'].split('..'))
            actual = binary[start - 0x100000000:end - 0x100000000]
            self.assertEqual(hashlib.sha256(actual).hexdigest(), r['sha256'])

    def test_original_operation_precedes_success_and_changes_gate_not_exception_bridge(self):
        records = {r.get('address') or r['function_id'].split(':')[-1]: r for r in self.proof['original_fragments']}
        r = records['0x100302b78']
        original = original_fragment((ROOT / r['path']).read_text(), '100302b78')
        self.assertLess(original.index('(*param_1)(param_3)'), original.index('unaff_x21 == 0'))
        self.assertLess(original.index('objc_stub::hasChanges(param_4)'), original.index('FUN_1002ff9c8'))
        self.assertNotIn('catchExceptionIn_', original)
        self.assertNotIn('rollback', original)  # Ghidra removed this block; round160 binds the real rollback selector.
        proof = json.loads((ROOT / '.local/p0-repair/phase-160/save-failure-contract.json').read_text())
        self.assertIn('rollback', [r['selector'] for r in proof['selectors']])

    def test_actual_transaction_is_synchronous_same_container_with_only_save_error_rollback(self):
        order = ['let transaction = preparedTransaction ?? Transaction(context: context)', 'withExtendedLifetime(transaction)',
                 'try context.performAndWait', 'let outcome = try operation(transaction)',
                 'try transaction.repository.update(state.items', 'if context.hasChanges',
                 'try OriginalObjCExceptionBridge.f_1002ff9c8', 'try context.save()', 'return outcome']
        positions = [self.commit.index(t) for t in order]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(self.commit.count('try context.performAndWait'), 1)
        outside_save = self.commit.replace(body(self.commit, 'if context.hasChanges'), '')
        for forbidden in ['try perform', 'rollback', 'context.reset', 'catch', 'try?', 'Task', 'async']:
            self.assertNotIn(forbidden, outside_save)
        self.assertIn('context.rollback()', current_body((ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text(),'func commit<T>(previous:'))

    def test_only_save_is_bridged_and_operation_failure_does_not_save(self):
        conditional = body(self.commit, 'if context.hasChanges')
        bridge = body(conditional, 'try OriginalObjCExceptionBridge.f_1002ff9c8')
        self.assertEqual(bridge.strip(), '{ try context.save() }')
        outside = self.commit.replace(conditional, '')
        self.assertNotIn('context.save()', outside)
        self.assertNotIn('f_1002ff9c8', outside)
        self.assertNotIn('operation(transaction)', bridge)
        self.assertLess(self.commit.index('try operation(transaction)'), self.commit.index('if context.hasChanges'))

    def test_existing_exception_bridge_preserves_swift_error_and_objc_name_reason(self):
        source = (ROOT / 'replica/Sources/PastoCore/OriginalObjCExceptionBridge.swift').read_text()
        wrapper = body(source, 'public static func f_1002ff9c8(_ operation: () throws -> Void)')
        self.assertIn('try withResult(operation)', wrapper)
        bridge = body(source, 'public static func withResult<T>(_ operation: () throws -> T)')
        for token in ['PRObjCExceptionCatcher.catchException', 'result = .success(try operation())',
                      'catch { result = .failure(error) }', 'if let exception',
                      'OriginalObjCExceptionError(name: exception.name.rawValue, reason: exception.reason)',
                      'return try result.get()']:
            self.assertIn(token, bridge)
        self.assertNotIn('rollback', source)

    def test_real_store_consumer_propagates_before_publishing_value_state(self):
        store = (ROOT / 'replica/Sources/PastoCore/ClipboardStore.swift').read_text()
        mutate = body(store, 'private func mutateInTransaction<T>(historyAction: Bool = false,')
        order = ['try persistence.commit(previous: remote', 'let result = try change(&state, transaction)',
                 'return (state: state, result: result)', 'diskRevision = try revision()', 'publish(state)']
        positions = [mutate.index(t) for t in order]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn('catch', mutate)
        self.assertNotIn('try?', mutate)
        self.assertNotIn('rollback', mutate)

    def test_read_bootstrap_and_cloud_adapters_are_unchanged_by_native_error_fix(self):
        before = (self.phase / 'before/replica/Sources/PastoCore/ClipboardPersistence.swift').read_text()
        for signature in ['private func perform<T>(_ operation:', 'private func bootstrapListsIfNeeded()',
                          'private func bootstrapHistoryTimestamps()', 'func revision() throws', 'func read() throws',
                          'func searchItems(identifiers:', 'func searchNativeItems(identifiers:',
                          'private func documents(_ entity:', 'private func journalHeader(_ journal:']:
            current = body(self.persistence, signature)
            if signature == 'private func bootstrapListsIfNeeded()':
                current = current.replace('            try bootstrapSourcesIfNeeded(root)\n', '', 1)
            previous = body(before, signature)
            if signature in ['func searchItems(identifiers:', 'func searchNativeItems(identifiers:']:
                old_request = 'let request = NSFetchRequest<NSManagedObject>(entityName: "Item")'
                new_request = 'let request = PastoItemEntity.defaultFetchRequest()'
                old_head, _, old_tail = previous.partition(old_request)
                new_head, _, new_tail = current.partition(new_request)
                self.assertIn(new_request, current)
                self.assertEqual(tuple(map(projection_spelling, (new_head, new_tail))), tuple(map(projection_spelling, (old_head, old_tail))))
            else:
                self.assertEqual(projection_spelling(previous), projection_spelling(current))
        self.assertIn('catch { context.rollback(); throw error }', body(self.persistence, 'private func perform<T>(_ operation:'))


if __name__ == '__main__':
    unittest.main()
