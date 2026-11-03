from native_restore_only_scope_contract import pre_native_restore_only
"""Source and original ARM data contracts; no Swift/Core Data execution."""
import hashlib
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body as current_body
from test_offline_p0_contracts import body

class TransactionBoundary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.persistence=pre_native_restore_only((ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text())
        cls.store=(ROOT/'replica/Sources/PastoCore/ClipboardStore.swift').read_text()
        cls.commit=body(cls.persistence,'func commit<T>(previous: StoreState?, deletingItemIDs: [UUID] = [],')
        cls.mutate=body(cls.store,'private func mutateInTransaction<T>(historyAction: Bool = false,')

    def test_original_operation_save_gate_proof_is_bound_to_real_fragments_and_bytes(self):
        proof=json.loads((ROOT/'.local/p0-repair/phase-4/transaction-original-proof.json').read_text())
        for r in proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT/r['path'])[r['function_id'].split(':')[1]]['sha256'],r['sha256'])
        binary=(ROOT/'.local/paste-arm64-static.bin').read_bytes()
        for r in proof['machine_evidence']['segments']:
            offset=int(r['file_offset'],16)
            actual=binary[offset:offset+r['length']]
            self.assertEqual(actual.hex(),r['hex'])
            self.assertEqual(hashlib.sha256(actual).hexdigest(),r['sha256'])
        original=(ROOT/'decompiled/Paste/part-0249.c').read_text()
        start=original.index('void FUN_100302b78(')
        fragment=original[start:original.index('/* Address:',start)]
        self.assertLess(fragment.index('(*param_1)(param_3)'),fragment.index('objc_stub::hasChanges(param_4)'))
        self.assertIn('unaff_x21 == 0',fragment)
        self.assertIn('FUN_1002ff9c8',fragment)

    def test_store_business_operation_is_produced_inside_commit_not_before_it(self):
        mutation=body(self.mutate,'try persistence.commit(previous: remote, deletingItemIDs: deletingItemIDs,')
        for token in ['merge(local, onto: remote)','try change(&state, transaction)','try validate(state)',
                      'normalize(&state)','expireHistory(&state, capacity: capacity)','return (state: state, result: result)']:
            self.assertIn(token,mutation)
        outer=self.mutate.replace(mutation,'')
        self.assertNotIn('try change(&state, transaction)',outer)
        self.assertNotIn('normalize(&state)',outer)
        self.assertIn('publish(state)',outer)
        self.assertLess(self.mutate.index('try persistence.commit('),self.mutate.index('publish(state)'))

    def test_business_delta_and_save_share_one_perform_and_wait_boundary(self):
        transaction=body(self.commit,'try context.performAndWait')
        self.assertNotIn('context.reset()', self.commit)
        order=['let outcome = try operation(transaction)','let state = outcome.state',
               'try transaction.repository.update(state.items','if context.hasChanges','try context.save()','return outcome']
        positions=[transaction.index(token) for token in order]
        self.assertEqual(positions,sorted(positions))
        self.assertEqual(self.commit.count('try context.performAndWait'),1)
        self.assertNotIn('context.performAndWait',transaction)
        self.assertNotIn('try perform',transaction)
        save=body(transaction,'try OriginalObjCExceptionBridge.f_1002ff9c8')
        self.assertIn('try context.save()',save)
        self.assertNotIn('try operation(transaction)',save)

    def test_operation_error_does_not_enter_delta_or_unconditional_save(self):
        self.assertIn('let outcome = try operation(transaction)',self.commit)
        self.assertEqual(self.commit.count('try context.save()'),1)
        conditional=body(self.commit,'if context.hasChanges')
        self.assertIn('root.setValue(UUID(), forKey: "revision")',conditional)
        self.assertIn('try context.save()',conditional)
        outside=self.commit.replace(conditional,'')
        self.assertNotIn('try context.save()',outside)
        self.assertNotIn('try?',self.commit)
        self.assertNotIn('catch',outside)
        self.assertNotIn('rollback',outside)
        self.assertIn('context.rollback()',current_body((ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text(),'func commit<T>(previous:'))
        self.assertNotIn('try perform',self.commit)

    def test_store_publishes_only_after_successful_commit_and_revision_read(self):
        self.assertNotIn('publish(',body(self.mutate,'try persistence.commit(previous:'))
        order=['let (state, result) = try persistence.commit(',
               'diskRevision = try revision()','publish(state)','return result']
        self.assertEqual([self.mutate.index(t) for t in order],sorted(self.mutate.index(t) for t in order))
        self.assertNotIn('catch',self.mutate)
        self.assertNotIn('try?',self.mutate)
        self.assertIn('return try withLock',self.mutate)

    def test_legacy_initialization_wrapper_reuses_the_same_transaction(self):
        wrapper=body(self.persistence,'func commit(_ state: StoreState, previous: StoreState?, deletingItemIDs: [UUID] = []) throws')
        self.assertIn('try commit(previous: previous, deletingItemIDs: deletingItemIDs)',wrapper)
        self.assertIn('(state: state, result: ())',wrapper)
        self.assertNotIn('context.save()',wrapper)
        self.assertNotIn('try perform',wrapper)
        init=body(self.store,'public init(directoryURL: URL) throws')
        self.assertIn('try persistence.commit(state, previous: nil)',init)

    def test_all_existing_local_value_mutation_order_is_preserved(self):
        before=(ROOT/'.local/p0-repair/phase-4/before/replica/Sources/PastoCore/ClipboardStore.swift').read_text()
        old=body(before,'private func mutate<T>(historyAction: Bool = false,')
        new=body(self.mutate,'try persistence.commit(previous: remote, deletingItemIDs: deletingItemIDs,')
        order=['merge(local, onto: remote)','try change(&state)','try validate(state)',
               'normalize(&state)','expireHistory(&state)','Self.captureCloudKit(&state, previous: remote)']
        for source in [old,new.replace('expireHistory(&state, capacity: capacity)', 'expireHistory(&state)').replace('try change(&state, transaction)', 'try change(&state)')]:
            positions=[source.index(token) for token in order]
            self.assertEqual(positions,sorted(positions))
        self.assertIn('if state.cloudKitJournal != nil { try Self.captureCloudKit(&state, previous: remote) }',new)
        self.assertIn('let remote = try preparedRestore?.previous ?? latestState()',self.mutate)
        self.assertNotIn('Task',self.commit)
        self.assertNotIn('async',self.commit)

if __name__=='__main__':unittest.main()
