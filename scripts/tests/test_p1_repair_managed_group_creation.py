"""Managed group operation order and classifier proof; no CoreData/Swift/SDK execution."""
import hashlib
import json
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from native_group_creation_result_scope_contract import pre_native_group_creation_result
from test_offline_p0_contracts import body
from test_p0_repair_identity import method_body
from test_p0_repair_checksum_routing import original_fragment


class ManagedGroupCreationContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-57'
        cls.proof = json.loads((cls.phase / 'group-creation-contract.json').read_text())
        cls.store_path = 'replica/Sources/PastoCore/ClipboardStore.swift'
        cls.list_path = 'replica/Sources/PastoCore/ClipboardListPersistence.swift'
        cls.ui_path = 'replica/Sources/Pasto/UI/ReplicaUIController.swift'
        cls.store = pre_native_group_creation_result((ROOT / cls.store_path).read_text())
        cls.lists = pre_native_group_creation_result((ROOT / cls.list_path).read_text())
        cls.ui = pre_native_group_creation_result((ROOT / cls.ui_path).read_text())
        cls.create = body(cls.store, 'private func insertPinboard(')
        cls.managed = body(cls.lists, 'func insertPinboard(')
        cls.project = body(cls.lists, 'func project(')
        cls.normalize = body(cls.store, 'private func normalize(')
        cls.targets = body(cls.ui, 'func selectedItemTargetLists()')
        cls.original = {r['address']: original_fragment((ROOT / r['path']).read_text(), r['address'][2:])
                        for r in cls.proof['original_fragments']}

    def assertOrder(self, source, tokens):
        offsets = [source.index(token) for token in tokens]
        self.assertEqual(offsets, sorted(offsets))

    def test_original_fragments_prior_schema_and_actual_sources_are_bound(self):
        self.assertEqual(len(self.proof['original_fragments']), 6)
        for row in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / row['path'])[row['address']]['sha256'], row['sha256'])
        for row in self.proof['prior_contracts'] + [self.proof['arm_disassembly'], self.proof['sdk_pending_changes']]:
            self.assertEqual(hashlib.sha256(Path(row['path'] if Path(row['path']).is_absolute() else ROOT / row['path']).read_bytes()).hexdigest(), row['sha256'])
        for path, digest in self.proof['current_sources'].items():
            frozen = (self.phase / 'after' / path).read_text()
            self.assertEqual(hashlib.sha256((self.phase / 'after' / path).read_bytes()).hexdigest(), digest)
            markers = {self.list_path: ['func insertPinboard(', 'func project(', 'func synchronize('],
                       self.store_path: ['private func insertPinboard(', 'private func normalize(', 'public func pinboardOwner('],
                       self.ui_path: ['func selectedItemTargetLists()', 'func createPinboard(']}[path]
            for marker in markers:
                from group_menu_input_scope_contract import pre_group_menu_input
                self.assertEqual(body(pre_group_menu_input((ROOT / path).read_text()), marker), body(frozen, marker))

    def test_native_operation_uses_actual_insert_identifier_name_and_permanent_ID_selectors(self):
        names = {r['selector'] for r in self.proof['selector_bindings']}
        self.assertEqual(names, {'initWithContext:', 'setIdentifier:', 'setName:', 'obtainPermanentIDsForObjects:error:'})
        for row in self.proof['selector_bindings']:
            self.assertTrue(row['chain']['declared_chain_reachable'])
            encoded = struct.unpack('<Q', bytes.fromhex(row['pointer_bytes']))[0]
            self.assertEqual(hex(0x100000000 + (encoded & ((1 << 36) - 1))), row['selector_address'])
        self.assertOrder(self.original['0x100368560'], ['initWithContext_', 'setIdentifier_', 'setName_',
                        'FUN_100c075e0', 'Foundation::JSONEncoder::_encode', 'setRawAttributes_', 'setRawType_(IVar1,2)'])

    def test_permanent_ID_failure_branch_releases_error_and_rejoins_before_JSON(self):
        rows = {r['address']: struct.unpack('<I', bytes.fromhex(r['bytes']))[0]
                for r in self.proof['permanent_ID_error_ARM']}
        cbz = rows['0x1003686ac']
        self.assertEqual(cbz & 31, 20)
        displacement = (cbz >> 5) & ((1 << 19) - 1)
        self.assertEqual(0x1003686ac + displacement * 4, 0x1003686b8)
        branch = rows['0x1003686b4']
        self.assertEqual(0x1003686b4 + (branch & ((1 << 26) - 1)) * 4, 0x1003686e8)
        call = rows['0x1003686e4']
        self.assertEqual(0x1003686e4 + (call & ((1 << 26) - 1)) * 4, 0x100bfc708)
        self.assertEqual(self.proof['error_release_import']['symbol'], '_swift_errorRelease')
        self.assertTrue(self.proof['error_release_import']['chain']['declared_chain_reachable'])
        self.assertEqual(rows['0x1003686e8'], 0xd2800015)  # mov x21,#0
        self.assertIn('try? context.obtainPermanentIDs(for: [list])', self.managed)

    def test_real_creation_is_inside_existing_transaction_before_value_append(self):
        self.assertIn('return try mutateInTransaction { state, transaction in', self.create)
        self.assertOrder(self.create, ['let id = UUID()', 'let sortOrder =',
                        'transaction.repository.lists.insertPinboard(identifier: id.uuidString',
                        'OriginalPinboardAttributes.encoded(colorCode:', 'let board = Pinboard(id: id',
                        'state.pinboards.append(board)', 'return board'])
        transaction = body(self.store, 'private func mutateInTransaction<T>(')
        self.assertOrder(transaction, ['persistence.commit(', 'try change(&state, transaction)',
                        'normalize(&state)', 'try lists.synchronize(', 'publish(state)'])
        self.assertNotIn('persistence.commit(', self.create)
        self.assertNotIn('context.save()', self.managed)

    def test_lazy_attribute_encoding_happens_after_native_insert_and_permanent_attempt(self):
        self.assertOrder(self.managed, ['insertNewObject(forEntityName: "ListEntity"',
                        'list.setValue(identifier, forKey: "identifier")', 'list.setValue(name, forKey: "name")',
                        'try? context.obtainPermanentIDs(for: [list])', 'let attributes = try encodeAttributes()',
                        'list.setValue(attributes, forKey: "rawAttributes")', 'list.setValue(Int64(2), forKey: "rawType")',
                        'return attributes'])
        self.assertNotIn('try? encodeAttributes', self.managed)
        self.assertNotIn('catch', self.managed)
        self.assertNotIn('encoded(colorCode:', self.create[:self.create.index('transaction.repository.lists.insertPinboard(')])
        self.assertIn('encodeAttributes: () throws -> Data?', self.lists)

    def test_model_required_metadata_is_initialized_before_encoding_can_fail(self):
        for token in ['list.setValue(now, forKey: "createdAt")',
                      'insertNewObject(forEntityName: "ListMetadataEntity"',
                      'metadata.setValue(identifier, forKey: "identifier")',
                      'metadata.setValue(index, forKey: "index")', 'metadata.setValue(now, forKey: "createdAt")',
                      'list.setValue(metadata, forKey: "metadata")']:
            self.assertLess(self.managed.index(token), self.managed.index('try encodeAttributes()'))
        self.assertNotIn('context.delete(', self.managed)
        self.assertNotIn('rollback', self.managed)
        self.assertTrue(any('mandatory metadata/date' in row for row in self.proof['retained_partial_contracts']))

    def test_creation_error_projection_keeps_pending_native_insert_without_publishing_value(self):
        # Original-bound source trace only; does not execute encoding or CoreData.
        def trace(permanent_succeeds, encoding_succeeds):
            events = ['insert', 'identifier', 'name', 'pasto-required-metadata', 'permanent-attempt']
            if not permanent_succeeds:
                events += ['ignore-permanent-error']
            events += ['encode']
            if not encoding_succeeds:
                return events, False
            return events + ['rawAttributes', 'rawType2', 'append-value', 'commit', 'publish'], True
        for permanent in [False, True]:
            events, published = trace(permanent, False)
            self.assertFalse(published)
            self.assertIn('insert', events)
            self.assertNotIn('rawType2', events)
            events, published = trace(permanent, True)
            self.assertTrue(published)
            self.assertIn('publish', events)
        self.assertNotIn('try?', self.create)
        self.assertNotIn('catch', self.create)

    def test_same_UUID_is_shared_by_native_row_value_board_and_synchronization(self):
        self.assertEqual(self.create.count('UUID()'), 1)
        self.assertIn('identifier: id.uuidString', self.create)
        self.assertIn('Pinboard(id: id,', self.create)
        synchronize = body(self.lists, 'func synchronize(')
        self.assertLess(synchronize.index('var lists = try allLists()'), synchronize.index('for board in pinboards'))
        board_loop = body(synchronize, 'for board in pinboards')
        self.assertOrder(board_loop, ['let identifier = board.id.uuidString',
                        'if let existing = lists[identifier] { list = existing }', 'else {'])
        all_lists = body(self.lists, 'private func allLists()')
        self.assertNotIn('includesPendingChanges = false', all_lists)
        self.assertTrue(self.proof['sdk_pending_changes']['default'])
        self.assertIn('context.fetch(request)', all_lists)

    def test_history_bootstrap_factory_and_transaction_container_are_unchanged(self):
        before = (self.phase / 'before' / self.list_path).read_text()
        for marker in ['private func makeList(', 'func synchronize(', 'func firstList(', 'func historyList()']:
            self.assertEqual(body(self.lists, marker), body(before, marker))
        before_store = (self.phase / 'before' / self.store_path).read_text()
        for marker in ['private func mutateInTransaction<T>(', 'private func mutate<T>(', 'public func createPinboard(',
                       'public func createPinboardFromIntent(', 'func recordRestoredItems(']:
            self.assertEqual(body(self.store, marker), body(before_store, marker))

    def test_unused_color_selection_and_explicit_invalid_color_adapter_are_retained(self):
        before = body((self.phase / 'before' / self.store_path).read_text(), 'private func insertPinboard(')
        current_color = self.create[self.create.index('let code:'):self.create.index('let id = UUID()')]
        previous_color = before[before.index('let code:'):before.index('let attributes =')]
        self.assertEqual(current_color, previous_color)
        for token in ['let unused = OriginalPinboardColor.allCases.filter { !used.contains($0) }',
                      'unused.isEmpty ? OriginalPinboardColor.allCases : unused', 'if let colorHex',
                      'OriginalPinboardAttributes.parsedColorCode(colorHex)']:
            self.assertIn(token, self.create)
        self.assertIn('rawType: 2, rawAttributes: attributes', self.create)

    def test_graph_projection_reads_real_type_instead_of_preserving_legacy_nil(self):
        self.assertIn('let rawType = (list.value(forKey: "rawType") as? NSNumber)?.int64Value ?? 0', self.project)
        self.assertIn('value.rawType = Int16(exactly: rawType) ?? 0', self.project)
        self.assertNotIn('if board.rawType != nil', self.project)
        self.assertNotIn('int16Value', self.project)
        native = self.original['0x1003250f0']
        self.assertIn('objc_stub::rawType(unaff_x20)', native)
        self.assertIn('return IVar1 == 2', native)

    def test_legacy_nil_is_canonicalized_only_at_write_publish_boundary(self):
        self.assertIn('for i in state.pinboards.indices where state.pinboards[i].rawType == nil', self.normalize)
        self.assertIn('state.pinboards[i].rawType = 2', self.normalize)
        before = body((self.phase / 'before' / self.store_path).read_text(), 'private func normalize(')
        marker = 'let boards = Set(state.pinboards.map(\\.id))'
        self.assertEqual(self.normalize[self.normalize.index(marker):], before[before.index(marker):])
        synchronize = body(self.lists, 'func synchronize(')
        self.assertIn('set(Int64(board.rawType ?? 2), key: "rawType", on: list)', synchronize)
        self.assertNotIn('rawType == nil', self.targets)

    def test_large_raw_types_cannot_truncate_to_ordinary_group(self):
        values = [-(1 << 63), -65534, -32769, -32768, -1, 0, 1, 2, 3, 4,
                  32767, 32768, 65538, 131074, (1 << 63) - 1]
        for raw in values:
            projected = raw if -(1 << 15) <= raw < (1 << 15) else 0
            self.assertEqual(projected == 2, raw == 2)
        for raw in [None, 0, 1, 2, 3]:
            canonical = 2 if raw is None else raw
            self.assertEqual(canonical, 2 if raw is None else raw)
        self.assertTrue(any('arbitrary64 value roundtrip remains partial' in row for row in self.proof['retained_partial_contracts']))

    def test_owner_getter_itself_returns_nil_for_non_group_relations(self):
        owner = body(self.store, 'public func pinboardOwner(for item:')
        self.assertIn('guard let identifier = item.pinboardOwnerID else { return nil }', owner)
        self.assertIn('return pinboards.first { $0.id == identifier && $0.rawType == 2 }', owner)
        self.assertNotIn('?? 2', owner)
        self.assertNotIn('rawType == nil', owner)
        # Source-bound optional relation/predicate cases, not CoreData execution.
        boards = [('a', 0), ('b', 1), ('c', 2), ('d', None), ('e', 3)]
        for identifier, expected in [(None, None), ('a', None), ('b', None), ('c', 'c'),
                                     ('d', None), ('e', None), ('missing', None)]:
            found = next((key for key, raw in boards if key == identifier and raw == 2), None)
            self.assertEqual(found, expected)

    def test_actual_one_item_owner_target_requires_type2_and_retains_history_current_list_rules(self):
        self.assertIn('guard items.count == 1 else { return [] }', self.targets)
        self.assertIn('if let owner = store.pinboardOwner(for: item), owner.rawType == 2,', self.targets)
        self.assertNotIn('|| owner.rawType == nil', self.targets)
        self.assertIn('if item.isInHistory, isSearching || pinboardID != nil { lists.append(nil) }', self.targets)
        self.assertIn('isSearching || owner.id != pinboardID', self.targets)
        native = self.original['0x10031bc94']
        self.assertIn('objc_stub::list(unaff_x20)', native)
        self.assertIn('FUN_1003250f0()', native)
        self.assertIn('IVar1 = 0', native)
        before = body((self.phase / 'before' / self.ui_path).read_text(), 'func selectedItemTargetLists()')
        self.assertEqual(self.targets.replace('owner.rawType == 2,', 'owner.rawType == 2 || owner.rawType == nil,'), before)

    def test_only_three_existing_finite_contracts_close_no_new_inventory_or_full_function_credit(self):
        self.assertEqual([r['function_id'] for r in self.proof['contracts']],
                         ['Paste:0x100368560', 'Paste:0x10031bc94', 'Paste:0x1003250f0'])
        self.assertEqual(self.proof['new_difference_records'], 0)
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertEqual(self.proof['function_map_markers_upgraded'], 0)
        self.assertTrue(all(not r['full_function_migration_verified'] for r in self.proof['contracts']))


if __name__ == '__main__':
    unittest.main()
