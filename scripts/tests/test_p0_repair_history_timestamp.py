from item_order_scope_contract import without_order_model
"""Source/data checks only: no Swift or Core Data execution."""
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from mixed_restore_scope_contract import pre_mixed_restore
from snapshot_read_scope_contract import body, projection_spelling
from test_p0_repair_checksum_routing import original_fragment


class HistoryTimestampContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-13'
        cls.proof = json.loads((cls.phase / 'timestamp-root-contract.json').read_text())
        cls.persistence = (ROOT / 'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text()
        cls.store = (ROOT / 'replica/Sources/PastoCore/ClipboardStore.swift').read_text()

    def test_original_fragments_are_bound(self):
        for r in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / r['path'])[r['address']]['sha256'], r['sha256'])

    def test_original_model_timestamp_is_optional_date(self):
        model = self.proof['model_resource']
        for path, digest in [(model['path'], model['sha256']), (model['schema_path'], model['schema_sha256'])]:
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), digest)
        prop = json.loads((ROOT / model['schema_path']).read_text())['ItemEntity']['timestamp']
        self.assertEqual(prop, {'NSAttributeType': 900, 'NSIsOptional': True, 'NSDefaultValue': '$null'})

    def test_history_delete_and_restore_have_original_nil_and_date_setters(self):
        fragments = {r['address']: original_fragment((ROOT / r['path']).read_text(), r['address'][2:])
                     for r in self.proof['original_fragments']}
        self.assertIn('objc_stub::setTimestamp_((ID)puVar4,0)', fragments['0x100363004'])
        restore = fragments['0x100361ec0']
        self.assertLess(restore.index('FUN_100364108()'), restore.index('Date::init()'))
        self.assertIn('objc_stub::setTimestamp_(self,pNVar5)', restore)
        reverse = fragments['0x100364108']
        self.assertIn('uVar10 >> 1', reverse)
        self.assertIn('uVar10 - (lVar11 + -3)', reverse)

    def test_optional_model_keeps_exact_legacy_attribute_construction(self):
        factory = body(self.persistence, 'private static func makeModel(includeNativeIdentity: Bool,')
        before = body((self.phase / 'before/replica/Sources/PastoCore/ClipboardPersistence.swift').read_text(),
                      'private static func makeModel(includeNativeIdentity: Bool,')
        block = body(factory, 'if includeOptionalTimestamp')
        old_shape = factory.replace('if includeOptionalTimestamp ' + block, '')
        old_shape = old_shape.replace('attribute("timestamp", .dateAttributeType, optional: includeOptionalTimestamp)',
                                      'attribute("timestamp", .dateAttributeType)')
        native = body(old_shape, 'if includeNativeItemData')
        old_shape = old_shape.replace('if includeNativeItemData ' + native, '')
        sources = body(old_shape, 'if includeNativeSources')
        old_shape = old_shape.replace('if includeNativeSources ' + sources, '')
        typed = body(old_shape, 'if includeTypedItem')
        # Historical model shape is the real includeTypedItem=false branch.
        old_shape = old_shape.replace('if includeTypedItem ' + typed, '')
        compact = lambda s: re.sub(r'\s+', ' ', s).strip()
        self.assertEqual(compact(without_order_model(old_shape)), compact(before))

    def test_all_four_legacy_schema_candidates_are_nonoptional(self):
        migration = body(self.persistence, 'private static func migrateLegacyStoreIfNeeded(at storeURL: URL,')
        for native, preserve, lists in [('true', 'true', 'true'), ('true', 'true', 'false'),
                                       ('false', 'true', 'false'), ('false', 'false', 'false')]:
            self.assertIn(f'makeModel(includeNativeIdentity: {native}, preserveItemKeyInHistory: {preserve}, '
                          f'includeLists: {lists}, includeOptionalTimestamp: false, includeNativeItemData: false, includeNativeSources: false, includeTypedItem: false, includeItemOrder: false)', migration)
        self.assertEqual(migration.count('includeOptionalTimestamp: false'), 4)
        self.assertLess(migration.index('try manager.migrateStore'), migration.index('try coordinator.replacePersistentStore'))
        self.assertNotIn('destroyPersistentStore', migration)

    def test_read_uses_actual_timestamp_for_membership_and_preserves_detached_display_date(self):
        read = body(self.persistence, 'private func item(_ object: NSManagedObject)')
        self.assertIn('let timestamp = object.value(forKey: "timestamp") as? Date', read)
        self.assertIn('timestamp ?? object.value(forKey: "localCreatedAt") as? Date', read)
        self.assertIn('item.isInHistory = timestamp != nil', read)
        self.assertNotIn('object.value(forKey: "inHistory")', read)
        self.assertIn('throw CocoaError(.fileReadCorruptFile)', read)

    def test_bootstrap_copies_old_date_before_clearing_nonhistory_timestamp(self):
        bootstrap = body(self.persistence, 'private func bootstrapHistoryTimestamps() throws')
        order = ['NSPredicate(format: "localCreatedAt == nil")', 'for object in try context.fetch(request)',
                 'guard let timestamp = object.value(forKey: "timestamp") as? Date',
                 'object.setValue(timestamp, forKey: "localCreatedAt")',
                 'if !inHistory { object.setValue(nil, forKey: "timestamp") }']
        positions = [bootstrap.index(t) for t in order]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn('forKey: "content"', bootstrap)
        self.assertNotIn('context.save()', bootstrap)

    def test_bootstrap_existing_lists_do_not_skip_timestamp_backfill_or_split_its_save(self):
        bootstrap = body(self.persistence, 'private func bootstrapListsIfNeeded() throws')
        graph = body(bootstrap, 'if try lists.historyList() == nil')
        self.assertNotIn('bootstrapHistoryTimestamps', graph)
        self.assertLess(bootstrap.index('try bootstrapHistoryTimestamps()'), bootstrap.index('if context.hasChanges'))
        self.assertEqual(bootstrap.count('try context.save()'), 1)
        self.assertEqual(bootstrap.count('try perform'), 1)
        self.assertNotIn('forKey: "content"', bootstrap)

    def test_commit_writes_nil_on_history_removal_and_date_on_restore_independent_of_display_date(self):
        commit = body(self.persistence, 'func commit<T>(previous: StoreState?, deletingItemIDs: [UUID] = [],')
        self.assertIn('let timestamp = item.isInHistory ? item.createdAt : nil', commit)
        write = body(commit, 'if old.flatMap({ $0.isInHistory ? $0.createdAt : nil }) != timestamp')
        self.assertIn('object.setValue(timestamp, forKey: "timestamp")', write)
        display = body(commit, 'if old?.createdAt != item.createdAt')
        self.assertIn('object.setValue(item.createdAt, forKey: "localCreatedAt")', display)
        self.assertNotIn('forKey: "timestamp"', display)
        self.assertLess(commit.index('object.setValue(timestamp, forKey: "timestamp")'),
                        commit.index('try transaction.repository.lists.refreshHistoryIfNeeded()'))

    def test_value_layer_delete_restore_and_image_date_have_actual_new_storage_consumer(self):
        delete = body(self.store, 'public func delete(orderedIDs: [UUID], currentPinboardID: () -> UUID?)')
        self.assertIn('else { state.items[i].isInHistory = false }', delete)
        erase = body(self.store, 'public func eraseHistory() throws')
        self.assertIn('for i in state.items.indices { state.items[i].isInHistory = false }', erase)
        restore = body(self.store, 'func recordRestoredItems(_ ids: [UUID])')
        self.assertIn('try mutate(historyAction: true, restoringItemIDs: ids)', restore)
        self.assertIn('state.items[index].isInHistory = true',
                      body(self.store, 'private func mutateInTransaction<T>(historyAction: Bool = false,'))
        pasteboard = pre_mixed_restore((ROOT / 'replica/Sources/PastoCore/Pasteboard.swift').read_text())
        self.assertEqual(pasteboard.count('timestamp: item.isInHistory ? item.createdAt : nil'), 2)

    def test_date_only_changes_still_avoid_content_reencoding(self):
        content = body(self.persistence, 'private func content(_ item: ClipboardItem)')
        self.assertIn('value.createdAt = Date(timeIntervalSinceReferenceDate: 0)', content)
        self.assertIn('value.updatedAt = value.createdAt; value.isInHistory = false', content)
        commit = body(self.persistence, 'func commit<T>(previous: StoreState?, deletingItemIDs: [UUID] = [],')
        encoded = body(commit, 'if old.map(content) != content(item)')
        self.assertIn('object.setValue(try encode(content(item)), forKey: "content")', encoded)
        self.assertNotIn('forKey: "content"', body(commit, 'if old.flatMap({ $0.isInHistory ? $0.createdAt : nil }) != timestamp'))

    def test_business_transaction_does_not_reset_its_context_before_callback(self):
        commit = body(self.persistence, 'func commit<T>(previous: StoreState?, deletingItemIDs: [UUID] = [],')
        self.assertNotIn('context.reset()', commit)
        order = ['let transaction = preparedTransaction ?? Transaction(context: context)', 'withExtendedLifetime(transaction)',
                 'try context.performAndWait', 'let outcome = try operation(transaction)', 'if context.hasChanges',
                 'try context.save()', 'return outcome']
        positions = [commit.index(t) for t in order]
        self.assertEqual(positions, sorted(positions))
        self.assertIn('0x1002ff310', {r['address'] for r in self.proof['original_fragments']})
        self.assertIn('0x100302b78', {r['address'] for r in self.proof['original_fragments']})

    def test_this_patch_leaves_network_code_and_value_entrypoints_unchanged(self):
        before = (self.phase / 'before/replica/Sources/PastoCore/ClipboardPersistence.swift').read_text()
        for signature in ['private func documents(_ entity: String)', 'private func journalHeader(_ journal: OriginalCloudKitJournal?)']:
            self.assertEqual(projection_spelling(body(before, signature)), projection_spelling(body(self.persistence, signature)))
        # Preserve the historical phase20 constant-only check against the phase31
        # baseline, then delimit the only newly permitted store edits precisely.
        checkpoint = (ROOT / '.local/p0-repair/phase-31/before/replica/Sources/PastoCore/ClipboardStore.swift').read_text()
        declaration = '    public static let didRestoreItemNotification = Notification.Name("pasteboardHistoryManagerDidRestoreItem")\n'
        self.assertEqual(self.store.count(declaration), 1)
        self.assertEqual((self.phase / 'before/replica/Sources/PastoCore/ClipboardStore.swift').read_text(),
                         checkpoint.replace(declaration, '', 1))
        # The later phase32 checksum repair is separately checked against this
        # complete checkpoint; this test still freezes the phase31 restore edit.
        restored = (ROOT / '.local/p0-repair/phase-32/before/replica/Sources/PastoCore/ClipboardStore.swift').read_text()
        for signature in ['private func mutate<T>(historyAction: Bool = false,',
                          'func recordRestoredItems(_ ids: [UUID])']:
            current_body = body(restored, signature)
            restored = restored.replace(current_body, body(checkpoint, signature), 1)
        restored = restored.replace(', restoringItemIDs: [UUID] = []', '', 1)
        self.assertEqual(restored, checkpoint)


if __name__ == '__main__':
    unittest.main()
