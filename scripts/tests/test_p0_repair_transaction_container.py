from native_restore_only_scope_contract import pre_native_restore_only
"""Per-operation container/cache lifetime contracts using source and original bytes."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body as current_body
from test_offline_p0_contracts import body

class TransactionContainer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=pre_native_restore_only((ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text())
        cls.commit=body(cls.source,'func commit<T>(previous: StoreState?, deletingItemIDs: [UUID] = [],')
        cls.container=body(cls.source,'final class Transaction')

    def test_native_restore_callback_preserves_explicit_operation_argument_as_cache_receiver(self):
        proof=json.loads((ROOT/'.local/p0-repair/phase-4/restore-container-arm-proof.json').read_text())
        rows=proof.get('original_fragments',proof.get('source_fragments'))
        for r in rows:
            self.assertEqual(source_fragments(ROOT/r['path'])[r['function_id'].split(':')[1]]['sha256'],r['sha256'])
        data=(ROOT/'.local/paste-arm64-static.bin').read_bytes()
        def word(address):return struct.unpack_from('<I',data,address-0x100000000)[0]
        # The callback leaves x0 intact while filling x1/x2 from its captured environment.
        self.assertEqual(word(0x10037b628),0xa9410a81)
        # The receiver is the operation's x0, separate from the captured owner's x2.
        self.assertEqual(word(0x10037ae04),0xaa0203f6)
        self.assertEqual(word(0x10037ae10),0xaa0003f4)
        self.assertEqual(word(0x100359514),0x91006280)
        self.assertEqual(word(0x100359570),0xf9400a98)
        self.assertEqual(word(0x10035958c),0xf9000818)
        self.assertEqual(word(0x1003595c4),0x91006281)
        # Hidden result buffer is x8; the generic descriptor argument x0 is not the instance cache.
        self.assertEqual(word(0x100359510),0xaa0803f6)

    def test_each_commit_creates_a_container_before_the_perform_boundary_and_passes_same_instance(self):
        self.assertIn('operation: (Transaction) throws -> (state: StoreState, result: T)',self.source)
        order=['let transaction = preparedTransaction ?? Transaction(context: context)',
               'return try withExtendedLifetime(transaction)', 'try context.performAndWait',
               'let outcome = try operation(transaction)',
               'try transaction.repository.update(state.items','try context.save()','return outcome']
        positions=[self.commit.index(t) for t in order]
        self.assertEqual(positions,sorted(positions))
        self.assertEqual(self.commit.count('Transaction(context: context)'),1)
        self.assertNotIn('static var transaction',self.source)

    def test_repository_is_initialized_lazily_from_the_same_context_and_cached_per_instance(self):
        getter=body(self.container,'var repository: ManagedRepository')
        order=['if let cachedRepository { return cachedRepository }',
               'let repository = ManagedRepository(context: context)',
               'cachedRepository = repository','return repository']
        positions=[getter.index(t) for t in order]
        self.assertEqual(positions,sorted(positions))
        self.assertIn('private var cachedRepository: ManagedRepository?',self.container)
        self.assertIn('let context: NSManagedObjectContext',self.container)
        init=body(self.container,'init(context: NSManagedObjectContext)')
        self.assertIn('self.context = context',init)
        self.assertNotIn('ManagedRepository(',init)
        self.assertNotIn('static',self.container)

    def test_repository_is_connected_to_real_delta_writes_and_shares_one_context(self):
        repository=body(self.source,'final class ManagedRepository')
        self.assertIn('private let context: NSManagedObjectContext',repository)
        update=body(repository,'func update<T: Equatable>(')
        for token in ['try fetchObjects(entity, keys: keys)', 'object.managedObjectContext?.delete(object)',
                      'NSEntityDescription.insertNewObject(forEntityName: entity, into: context)',
                      'try context.obtainPermanentIDs(for: [object])','try apply(value, before[id], object)']:
            self.assertIn(token,update)
        self.assertIn('transaction.repository.update(state.items',self.commit)
        self.assertIn('transaction.repository.update(state.pinboards',self.commit)
        self.assertIn('transaction.repository.update(state.sourceApplications',self.commit)
        self.assertNotIn('context.save()',repository)
        self.assertNotIn('context.performAndWait',repository)

    def test_container_lifetime_wraps_save_and_error_conversion_without_publication_inside(self):
        lifetime=body(self.commit,'return try withExtendedLifetime(transaction)')
        self.assertIn('try context.performAndWait',lifetime)
        self.assertIn('try context.save()',lifetime)
        self.assertNotIn('publish(',lifetime)
        save=body(lifetime,'try OriginalObjCExceptionBridge.f_1002ff9c8')
        self.assertIn('try context.save()',save)
        self.assertNotIn('try operation(transaction)',save)
        conditional=body(lifetime,'if context.hasChanges')
        self.assertNotIn('rollback',lifetime.replace(conditional,''))
        self.assertIn('context.rollback()',current_body((ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text(),'func commit<T>(previous:'))
        self.assertNotIn('Task',self.commit)
        self.assertNotIn('async',self.commit)

if __name__=='__main__':unittest.main()
