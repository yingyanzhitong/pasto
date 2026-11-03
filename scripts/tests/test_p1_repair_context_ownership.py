from native_restore_writer_scope_contract import pre_native_restore_writer
from native_title_scope_contract import pre_native_title_bytes
from item_order_scope_contract import without_list_request
from frc_result_scope_contract import assert_factory_addition_only
"""Source/static contracts only; no Swift/CoreData/framework/database/app execution."""
import hashlib
import json
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment
from snapshot_read_scope_contract import READ_NAMES, projection_spelling, commit_business_body, assert_history_queue_only


class ContextOwnershipContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-67'
        cls.proof = json.loads((cls.phase / 'context-ownership-contract.json').read_text())
        cls.paths = {name: 'replica/Sources/PastoCore/' + name + '.swift' for name in
                     ['ClipboardPersistence', 'ClipboardSnapshotReader', 'ClipboardListPersistence', 'OriginalSearchHistory']}
        cls.current = {name: pre_native_restore_writer((ROOT / path).read_text()) for name, path in cls.paths.items()}
        cls.old = {name: (cls.phase / 'before' / path).read_text() for name, path in cls.paths.items() if name != 'ClipboardSnapshotReader'}
        cls.view = cls.current['ClipboardPersistence']; cls.reader = cls.current['ClipboardSnapshotReader']
        cls.original = {r['address']: original_fragment((ROOT / r['path']).read_text(), r['address'][2:]) for r in cls.proof['original_fragments']}

    def test_original_static_inputs_and_all_changed_production_sources_are_bound(self):
        self.assertEqual(len(self.proof['original_fragments']), 9)
        for row in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / row['path'])[row['address']]['sha256'], row['sha256'])
        for row in [self.proof['binary']] + self.proof['sdk_headers']:
            self.assertEqual(hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest(), row['sha256'])
        for path, digest in self.proof['current_sources'].items():
            frozen = (self.phase / 'after' / path).read_bytes()
            self.assertEqual(hashlib.sha256(frozen).hexdigest(), digest)
            if path == self.paths['ClipboardPersistence']:
                assert_factory_addition_only(self, (ROOT / path).read_text(), frozen.decode())
            elif path == self.paths['ClipboardListPersistence']:
                self.assertEqual(without_list_request((ROOT / path).read_text()), frozen.decode())
            else:
                self.assertEqual(pre_native_title_bytes(ROOT / path), frozen)

    def test_original_main_view_policy_and_private_history_context_have_real_bindings(self):
        original = self.original['0x10035cc80']
        steps = ['LAB_10035d920:', 'objc_stub::viewContext(', 'objc_stub::FUN_100c0a9e0(IVar5,1)', 'objc_stub::setMergePolicy_', 'PTR__NSMergeByPropertyStoreTrumpMergePolicy_100ea9a08', 'FUN_100370e8c()']
        start = 0
        for step in steps:
            start = original.index(step, start) + len(step)
        selector = self.proof['selector']; policy = self.proof['merge_policy']
        self.assertEqual(selector['selector'], 'setAutomaticallyMergesChangesFromParent:')
        self.assertEqual(bytes.fromhex(selector['selector_bytes']), selector['selector'].encode() + b'\0')
        self.assertEqual(policy['symbol'], '_NSMergeByPropertyStoreTrumpMergePolicy')
        self.assertTrue(selector['chain']['declared_chain_reachable'] and policy['chain']['declared_chain_reachable'])
        native = self.original['0x100370e8c']
        self.assertIn('initWithConcurrencyType_((ID)puVar3,1)', native)
        self.assertIn('setPersistentStoreCoordinator_(self,param_1)', native)
        sdk = next((ROOT / r['path']).read_text() for r in self.proof['sdk_headers'] if r['path'].endswith('NSManagedObjectContext.h'))
        self.assertRegex(sdk, r'NSPrivateQueueConcurrencyType\s*= 0x01')

    def test_view_context_never_resets_and_keeps_existing_main_actor_consumers(self):
        self.assertIn('@MainActor\nfinal class ClipboardPersistence', self.view)
        self.assertIn('NSManagedObjectContext(concurrencyType: .mainQueueConcurrencyType)', self.view)
        self.assertNotIn('context.reset()', self.view)
        self.assertIn('managedContext.automaticallyMergesChangesFromParent = true', self.view)
        self.assertIn('managedContext.mergePolicy = NSMergeByPropertyStoreTrumpMergePolicy', self.view)
        for marker in ['func observeListAttributes(', 'func localListMenuState(', 'private func publishChangedItemIDs(', 'func prepareHistoryRestore(']:
            self.assertEqual(body(self.view, marker), body(self.old['ClipboardPersistence'], marker))
        for text in ['lists = ClipboardListPersistence(context: managedContext)', 'sources = ClipboardSourcePersistence(context: managedContext)', 'object: managedContext']:
            self.assertIn(text, self.view)

    def test_all_six_real_read_entrypoints_forward_without_swallowing_errors(self):
        for name in READ_NAMES:
            wrapper = body(self.view, 'func ' + name + '(')
            self.assertIn('try snapshotReader.' + name + '(', wrapper)
            for forbidden in ['try?', 'catch', 'context.reset()', 'fatalError', 'context.fetch']:
                self.assertNotIn(forbidden, wrapper)
            if name != 'revision':
                self.assertEqual(wrapper.count('snapshotReader.'), 1)
                self.assertEqual(wrapper.count('\n'), 2)
        self.assertIn('snapshotReader = ClipboardSnapshotReader(coordinator: coordinator)', self.view)

    def test_moved_read_bodies_preserve_all_queries_errors_and_projection_except_named_changes(self):
        for name in READ_NAMES:
            current = body(self.reader, 'func ' + name + '(')
            previous = body(self.old['ClipboardPersistence'], 'func ' + name + '(')
            self.assertEqual(projection_spelling(current), projection_spelling(previous), name)
        for marker in ['private func fetch(', 'private func root()', 'private func perform<T>(', 'private func documents(']:
            self.assertEqual(projection_spelling(body(self.reader, marker)), projection_spelling(body(self.old['ClipboardPersistence'], marker)))

    def test_managed_read_values_reset_on_success_empty_early_return_and_failure(self):
        for name in ['read', 'searchItems', 'searchNativeItems', 'searchIndexRecords']:
            method = body(self.reader, 'func ' + name + '(')
            steps = ['try perform', 'context.reset()', 'defer { context.reset() }']
            self.assertEqual([method.index(s) for s in steps], sorted(method.index(s) for s in steps))
            self.assertEqual(method.count('context.reset()'), 2)
        self.assertIn('catch { context.rollback(); throw error }', body(self.reader, 'private func perform<T>('))
        initializer = body(self.reader, 'init(coordinator:')
        self.assertIn('NSManagedObjectContext(concurrencyType: .privateQueueConcurrencyType)', initializer)
        self.assertNotIn('@MainActor', self.reader)
        self.assertIn('lists = ClipboardListPersistence(context: context)', initializer)

    def test_index_fetch_error_remains_logged_empty_not_mistaken_for_fatal_FRC_error(self):
        method = body(self.reader, 'func searchIndexRecords(')
        failure = body(method, 'catch')
        self.assertIn('guard identifiers != nil else { throw error }', failure)
        self.assertIn('searchLogger.error(', failure)
        self.assertIn('return []', failure)
        self.assertNotIn('decode(', body(method, 'do '))
        self.assertNotIn('fatalError', self.reader)
        self.assertIn('Error::get_localizedDescription()', self.original['0x10036dc00'])
        self.assertIn('_assertionFailure', self.original['0x100365e18'])

    def test_shared_projection_is_nonisolated_pure_and_same_actual_implementation(self):
        for old, new in [('private func item(', 'nonisolated static func item('), ('private func decode<T:', 'nonisolated static func decode<T:')]:
            actual = body(self.view, new); previous = body(self.old['ClipboardPersistence'], old)
            self.assertEqual(projection_spelling(actual), projection_spelling(previous))
            for token in ['self.', 'context.', 'snapshotReader', 'Task {', 'UserDefaults']:
                self.assertNotIn(token, actual)
        self.assertIn('nonisolated static func projectNativePasteboardItems(', (ROOT / 'replica/Sources/PastoCore/Pasteboard.swift').read_text())

    def test_list_helper_changes_only_class_actor_marker_and_queue_contract_comment(self):
        previous = self.old['ClipboardListPersistence']
        expected = previous.replace('@MainActor\n', '', 1).replace('/// Local managed list relationships.', '/// Access on the supplied context queue.', 1)
        self.assertEqual(without_list_request(self.current['ClipboardListPersistence']), expected)

    def test_view_revision_merges_before_cache_and_cursor_advances_only_after_all_merges(self):
        revision = body(self.view, 'func revision()')
        expected = ['let revision = try snapshotReader.revision()', 'if revision != viewRevision', 'try mergeViewChanges()', 'viewRevision = revision', 'return revision']
        self.assertEqual([revision.index(x) for x in expected], sorted(revision.index(x) for x in expected))
        merge = body(self.view, 'private func mergeViewChanges()')
        expected = ['try snapshotReader.transactions(after: viewHistoryToken)', 'context.performAndWait', 'for transaction in transactions', 'context.mergeChanges(fromContextDidSave: transaction.objectIDNotification())', 'if let token = transactions.last?.token { viewHistoryToken = token }']
        self.assertEqual([merge.index(x) for x in expected], sorted(merge.index(x) for x in expected))
        for forbidden in ['catch', 'try?', 'UserDefaults', 'reset()', 'save()', 'viewRevision =']:
            self.assertNotIn(forbidden, merge)

    def test_bootstrap_and_own_commit_cursors_remain_within_existing_store_lock(self):
        initializer = body(self.view, 'init(directoryURL:')
        for start, end in [('try bootstrapListsIfNeeded()', 'viewHistoryToken = coordinator.currentPersistentHistoryToken(fromStores: nil)'), ('viewHistoryToken = coordinator.currentPersistentHistoryToken(fromStores: nil)', 'viewRevision = try context.performAndWait')]:
            self.assertLess(initializer.index(start), initializer.index(end))
        self.assertEqual(commit_business_body(self.view), commit_business_body(self.old['ClipboardPersistence']))
        commit = body(self.view, 'func commit<T>(')
        order = ['if context.hasChanges', 'try OriginalObjCExceptionBridge.f_1002ff9c8 { try context.save() }', 'viewHistoryToken = context.persistentStoreCoordinator?.currentPersistentHistoryToken(fromStores: nil)', 'viewRevision = root.value(forKey: "revision") as? UUID', 'return outcome']
        self.assertEqual([commit.index(x) for x in order], sorted(commit.index(x) for x in order))
        store = (ROOT / 'replica/Sources/PastoCore/ClipboardStore.swift').read_text()
        for marker in ['private func mutateInTransaction<T>(', 'public init(directoryURL:']:
            method = body(store, marker)
            self.assertIn('persistence.commit(', method)
            self.assertLess(method.index('withLock'), method.index('persistence.commit('))
        initializer = body(store, 'public init(directoryURL:')
        self.assertLess(initializer.index('Self.withLock(directoryURL:'), initializer.index('ClipboardPersistence(directoryURL:'))
        assert_factory_addition_only(self, store, (self.phase / 'before/replica/Sources/PastoCore/ClipboardStore.swift').read_text(), public=True)

    def test_history_keeps_real_consumers_errors_ack_and_global_token_lifecycle(self):
        history = self.current['OriginalSearchHistory']
        self.assertIn('@MainActor\nfinal class OriginalSearchHistory', history)
        self.assertIn('searchHistory = OriginalSearchHistory(reader: snapshotReader)', self.view)
        assert_history_queue_only(self, history, self.old['OriginalSearchHistory'])
        self.assertNotIn('context.', history)
        fetched = body(self.reader, 'func transactions(')
        self.assertLess(fetched.index('context.reset()'), fetched.index('context.execute(request)'))
        self.assertNotIn('OriginalObjCExceptionBridge', fetched)
        self.assertNotIn('try?', fetched)
        identifier = body(self.reader, 'func searchIdentifier(')
        self.assertIn('context.performAndWait', identifier)
        self.assertIn('try? context.existingObject(with: objectID)', identifier)
        self.assertIn('return nativeIdentifier', identifier)
        self.assertNotIn('isEmpty', identifier)

    def test_history_values_are_sdk_NSAObject_values_not_context_registered_managed_objects(self):
        headers = {Path(r['path']).stem: (ROOT / r['path']).read_text() for r in self.proof['sdk_headers']}
        self.assertIn('@interface NSPersistentHistoryTransaction : NSObject <NSCopying>', headers['NSPersistentHistoryTransaction'])
        self.assertIn('- (NSNotification *) objectIDNotification;', headers['NSPersistentHistoryTransaction'])
        self.assertIn('@interface NSPersistentHistoryToken : NSObject', headers['NSPersistentHistoryToken'])
        self.assertIn('currentPersistentHistoryTokenFromStores', headers['NSPersistentStoreCoordinator'])
        self.assertIn('mergeChangesFromContextDidSaveNotification', headers['NSManagedObjectContext'])
        self.assertIn('changedObjectID', headers['NSPersistentHistoryChange'])

    def test_view_adapter_failure_and_empty_batch_semantics_source_bound_table(self):
        # Python semantic fixtures tied to actual order asserted above; not CoreData execution.
        for changed, failure, batches, expected in [
            (False, None, [1], ('old', 0)), (True, 'fetch', [1], ('old', 0)),
            (True, 'merge', [1], ('old', 0)), (True, None, [], ('new', 0)),
            (True, None, [1, 2], ('new', 2))]:
            revision, token = 'old', 0
            try:
                if changed:
                    if failure == 'fetch': raise RuntimeError()
                    for _ in batches:
                        if failure == 'merge': raise RuntimeError()
                    if batches: token = batches[-1]
                    revision = 'new'
            except RuntimeError: pass
            self.assertEqual((revision, token), expected)

    def test_FRC_and_full_parent_contracts_remain_unscored_open(self):
        self.assertEqual(self.proof['contracts'], [])
        self.assertEqual(self.proof['partial_unscored_repairs'][0]['function_id'], 'Paste:0x100365e18')
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertEqual(self.proof['function_map_markers_upgraded'], 0)
        self.assertNotIn('NSFetchedResultsController', self.reader + self.view)
        self.assertIn('original actor/DI/ABI', ' '.join(self.proof['retained_partial_contracts']))


if __name__ == '__main__': unittest.main()
