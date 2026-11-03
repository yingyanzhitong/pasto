from item_order_scope_contract import without_order_model, assert_order_migration_only
"""Typed managed Item/fetch defaults and legacy source models; no CoreData/Swift runtime."""
import hashlib
import json
import re
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from list_insert_validation_scope_contract import pre_list_insert_validation
from snapshot_read_scope_contract import body, projection_spelling
from test_p0_repair_checksum_routing import original_fragment


class TypedItemFactoryContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-63'
        cls.proof = json.loads((cls.phase / 'typed-item-factory-contract.json').read_text())
        cls.item_path = 'replica/Sources/PastoCore/OriginalManagedItem.swift'
        cls.persistence_path = 'replica/Sources/PastoCore/ClipboardPersistence.swift'
        cls.list_path = 'replica/Sources/PastoCore/ClipboardListPersistence.swift'
        cls.item = (ROOT / cls.item_path).read_text()
        cls.persistence = (ROOT / cls.persistence_path).read_text()
        cls.lists = (ROOT / cls.list_path).read_text()
        cls.before = (cls.phase / 'before' / cls.persistence_path).read_text()
        cls.original = {r['address']: original_fragment((ROOT / r['path']).read_text(), r['address'][2:])
                        for r in cls.proof['original_fragments']}

    def test_original_inputs_metadata_and_actual_source_are_bound(self):
        self.assertEqual(len(self.proof['original_fragments']), 9)
        for row in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / row['path'])[row['address']]['sha256'], row['sha256'])
        for row in [self.proof['binary'], self.proof['sdk_typed_fetch_count']] + self.proof['prior_contracts'] + self.proof['arm_disassemblies']:
            self.assertEqual(hashlib.sha256((ROOT / row['path'] if not Path(row['path']).is_absolute() else Path(row['path'])).read_bytes()).hexdigest(), row['sha256'])
        for path, digest in self.proof['current_sources'].items():
            frozen = (self.phase / 'after' / path).read_text()
            self.assertEqual(hashlib.sha256((self.phase / 'after' / path).read_bytes()).hexdigest(), digest)
            if path.endswith('ClipboardPersistence.swift'):
                for marker in ['private static func makeModel(', 'private static func migrateLegacyStoreIfNeeded(', 'func searchIndexRecords(', 'func searchItems(', 'func searchNativeItems(', 'private func fetch(']:
                    if marker == 'private static func migrateLegacyStoreIfNeeded(':
                        assert_order_migration_only(self, body((ROOT / path).read_text(), marker), body(frozen, marker))
                    else:
                        self.assertEqual(without_order_model(projection_spelling(body((ROOT / path).read_text(), marker))), projection_spelling(body(frozen, marker)))
            else:
                current = pre_list_insert_validation((ROOT / path).read_text())
                if path == self.list_path:
                    from item_order_scope_contract import without_list_request
                    self.assertEqual(without_list_request(current), frozen.replace('@MainActor\n', '', 1).replace('/// Local managed list relationships.', '/// Access on the supplied context queue.'))
                else:
                    self.assertEqual(current, frozen)
            self.assertEqual(hashlib.sha256((self.phase / 'after' / path).read_bytes()).hexdigest(), digest)

    def test_original_metatype_accessor_resolves_actual_Item_class_not_a_guessed_name(self):
        words = {r['address']: int.from_bytes(bytes.fromhex(r['bytes']), 'little') for r in self.proof['ARM_words']}
        adrp = words['0x1003214b0']; add = words['0x1003214b4']
        imm = ((adrp >> 5) & 0x7ffff) * 4 + ((adrp >> 29) & 3)
        if imm & (1 << 20): imm -= 1 << 21
        address = (0x1003214b0 & ~4095) + (imm << 12) + ((add >> 10) & 4095)
        self.assertEqual(address, 0x100f97da8)
        item = self.proof['item_hierarchy'][0]
        self.assertEqual(int(item['class_pointer'], 16), address)
        self.assertEqual(bytes.fromhex(item['name']['bytes']).rstrip(b'\0'), b'_TtC9PasteCore10ItemEntity')
        parent = self.proof['item_hierarchy'][1]
        self.assertEqual(parent['decoded_name'], '_TtC9PasteCore21SyncableManagedObject')
        self.assertEqual(int.from_bytes(bytes.fromhex(item['class_data']['bytes'])[8:16], 'little') & ((1 << 36) - 1),
                         int(parent['class_pointer'], 16) - 0x100000000)

    def test_native_class_overrides_sort_and_inherits_nil_predicate_category(self):
        item, parent = self.proof['item_hierarchy']
        overrides = {m['selector']: m for m in item['methods']}
        self.assertEqual(set(overrides), {'defaultSortDescriptors'})
        self.assertEqual(overrides['defaultSortDescriptors']['imp'], '0x10031f2a4')
        entry = overrides['defaultSortDescriptors']['entry']
        imp = int(entry['address'], 16) + 8 + struct.unpack_from('<i', bytes.fromhex(entry['bytes']), 8)[0]
        self.assertEqual(imp, 0x10031f2a4)
        self.assertEqual(parent['methods'], [])
        defaults = {m['selector']: m['imp'] for m in self.proof['base_category']['methods']}
        self.assertEqual(defaults['defaultPredicate'], '0x10032c5c8')
        self.assertEqual(defaults['defaultSortDescriptors'], '0x10032c5c4')
        for a in ['0x10032c5c4', '0x10032c5c8', '0x10032b760']:
            self.assertIn('return 0;', self.original[a])

    def test_timestamp_descending_and_base_nil_defaults_match_original_bytes(self):
        words = struct.unpack('<6I', bytes.fromhex(self.proof['sort_key']['bytes']))
        first = sum(((word >> 5) & 65535) << (16 * i) for i, word in enumerate(words[:4]))
        second = ((words[4] >> 5) & 65535) | (((words[5] >> 5) & 65535) << 48)
        self.assertEqual((first.to_bytes(8, 'little') + second.to_bytes(8, 'little'))[:9], b'timestamp')
        self.assertEqual(bytes.fromhex(self.proof['sort_descending']['bytes']), struct.pack('<I', 0x52800003))
        self.assertIn('[NSSortDescriptor(key: "timestamp", ascending: false)]', self.item)
        self.assertIn('@objc class var defaultSortDescriptors: [NSSortDescriptor]? { nil }', self.item)
        self.assertIn('@objc class var defaultPredicate: NSPredicate? { nil }', self.item)

    def test_six_native_factory_selectors_and_batch_twenty_are_bound(self):
        names = [r['selector'] for r in self.proof['selector_bindings']]
        self.assertEqual(names, ['initWithEntityName:', 'defaultSortDescriptors', 'setSortDescriptors:',
                                 'defaultPredicate', 'setPredicate:', 'setFetchBatchSize:'])
        for row in self.proof['selector_bindings']:
            self.assertTrue(row['chain']['declared_chain_reachable'])
            self.assertEqual(bytes.fromhex(row['selector_bytes']['bytes']).rstrip(b'\0').decode(), row['selector'])
        batch = next(r for r in self.proof['ARM_words'] if r['address'] == '0x100329964')
        word = int.from_bytes(bytes.fromhex(batch['bytes']), 'little')
        self.assertEqual((word >> 5) & 65535, 20)
        self.assertEqual(word & 31, 2)

    def test_generic_factory_reads_metatype_defaults_before_returning_typed_request(self):
        factory = body(self.item, 'static func make<Entity: PastoManagedObject>(')
        steps = ['NSFetchRequest<Entity>(entityName: entity.entityName)',
                 'request.sortDescriptors = entity.defaultSortDescriptors',
                 'request.predicate = entity.defaultPredicate', 'request.fetchBatchSize = 20', 'return request']
        self.assertEqual([factory.index(t) for t in steps], sorted(factory.index(t) for t in steps))
        for token in ['context.', 'save(', 'fetch(', 'catch', 'try?', 'timestamp', '"Item"', 'fetchLimit', 'reset(']:
            self.assertNotIn(token, factory)
        native = self.original['0x1003298a0']
        expected = ['(*param_2)()', 'Swift::__typeName', 'initWithEntityName_', 'FUN_100c00de0(',
                    'FUN_100c0dbc0(', 'FUN_100c00d80(', 'setPredicate_', 'FUN_100c0bb60(self_00,0x14)', 'return self_00']
        self.assertEqual([native.index(t) for t in expected], sorted(native.index(t) for t in expected))

    def test_Item_wrapper_and_actual_readers_use_real_typed_factory(self):
        wrapper = body(self.item, 'static func defaultFetchRequest()')
        self.assertIn('OriginalManagedFetchRequest.make(for: PastoItemEntity.self)', wrapper)
        self.assertIn('FUN_1003298a0(0,FUN_1003214a8)', self.original['0x100329754'])
        for marker in ['func searchIndexRecords(', 'func searchItems(', 'func searchNativeItems(']:
            self.assertIn('let request = PastoItemEntity.defaultFetchRequest()', body(self.persistence, marker))
        generic = body(self.persistence, 'private func fetch(')
        self.assertIn('if entity == PastoItemEntity.entityName', generic)
        self.assertIn('let request = PastoItemEntity.defaultFetchRequest()', generic)
        self.assertIn('PastoItemEntity.defaultFetchRequest()', body(self.lists, 'func menuState('))

    def test_read_predicates_empty_inputs_error_and_projection_tails_are_unchanged(self):
        old_request = 'let request = NSFetchRequest<NSManagedObject>(entityName: "Item")'
        new_request = 'let request = PastoItemEntity.defaultFetchRequest()'
        for marker in ['func searchIndexRecords(', 'func searchItems(', 'func searchNativeItems(']:
            previous = body(self.before, marker); current = body(self.persistence, marker)
            old_head, _, old_tail = previous.partition(old_request)
            new_head, _, new_tail = current.partition(new_request)
            self.assertEqual(tuple(map(projection_spelling, (old_head, old_tail))), tuple(map(projection_spelling, (new_head, new_tail))))
            self.assertIn('request.predicate =', current)
            self.assertIn('context.fetch(request)', current)
        old_lists = (self.phase / 'before' / self.list_path).read_text()
        previous = body(old_lists, 'func menuState('); current = body(self.lists, 'func menuState(')
        old_head, _, old_tail = previous.partition('let request = NSFetchRequest<NSFetchRequestResult>(entityName: "Item")')
        new_head, _, new_tail = current.partition(new_request)
        self.assertEqual(tuple(map(projection_spelling, (old_head, old_tail))), tuple(map(projection_spelling, (new_head, new_tail))))

    def test_current_model_binds_class_only_under_explicit_flag_and_keeps_physical_schema(self):
        self.assertIn('includeTypedItem: Bool = true', self.persistence)
        model = body(self.persistence, 'private static func makeModel(')
        typed = body(model, 'if includeTypedItem')
        self.assertEqual(typed.strip(), '{\n            model.entitiesByName["Item"]!.managedObjectClassName = NSStringFromClass(PastoItemEntity.self)\n        }')
        before = body(self.before, 'private static func makeModel(')
        self.assertEqual(without_order_model(model).replace('        if includeTypedItem ' + typed + '\n', '', 1), before)
        self.assertIn('override class var entityName: String { "Item" }', self.item)
        self.assertIn('@objc(PastoItemEntity)', self.item)
        self.assertIn('class PastoItemEntity: PastoManagedObject', self.item)
        self.assertIn('class PastoManagedObject: NSManagedObject', self.item)

    def test_every_prior_model_description_stays_in_legacy_candidates_with_typed_flag_false(self):
        migration = body(self.persistence, 'private static func migrateLegacyStoreIfNeeded(')
        before = body(self.before, 'private static func migrateLegacyStoreIfNeeded(')
        def candidates(s): return s.split('let legacyCandidates = [', 1)[1].split('\n        ]', 1)[0]
        actual = candidates(migration); old = candidates(before)
        self.assertEqual(actual.count('makeModel('), 8)
        self.assertEqual(actual.count('includeTypedItem: false'), 7)
        for line in old.splitlines():
            if 'makeModel(' in line:
                self.assertIn(line.rstrip(',').replace(')', ', includeTypedItem: false, includeItemOrder: false)'), actual)
        self.assertIn('makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, includeTypedItem: false, includeItemOrder: false)', actual)
        tail = '        // The older history-retention variants'
        self.assertEqual(migration[migration.index(tail):], before[before.index(tail):])
        self.assertNotIn('destroyPersistentStore', migration)

    def test_sdk_overlay_supports_typed_fetch_and_count_without_erased_request_cast(self):
        sdk = Path(self.proof['sdk_typed_fetch_count']['path']).read_text()
        self.assertIn('public func fetch<T>(_ request: CoreData.NSFetchRequest<T>) throws -> [T]', sdk)
        self.assertIn('public func count<T>(for request: CoreData.NSFetchRequest<T>) throws -> Swift.Int', sdk)
        self.assertNotIn('as! NSFetchRequest', self.persistence + self.lists + self.item)
        self.assertIn('return try context.fetch(request)', body(self.persistence, 'private func fetch('))

    def test_only_finite_type_factory_records_close_and_FRC_model_lifecycle_stays_open(self):
        self.assertEqual([r['function_id'] for r in self.proof['contracts']],
                         ['Paste:0x1003214a8', 'Paste:0x100329754', 'Paste:0x1003298a0'])
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertEqual(self.proof['function_map_markers_upgraded'], 0)
        limitations = '\n'.join(self.proof['retained_partial_contracts'])
        for text in ['FRC', 'ItemMetadata', 'ABI', 'physical entity name Item', 'No model hash']:
            self.assertIn(text, limitations)
        self.assertNotIn('NSFetchedResultsController', self.item)
