"""Bind the ordinary list reading witness to its real FRC consumer; static only."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from collection_membership_scope_contract import pre_collection_membership, pre_collection_membership_bytes, ENTRY_PATH
from test_p0_repair_checksum_routing import original_fragment


class ListProviderDispatchContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proof = json.loads((ROOT / '.local/p0-repair/phase-71/list-provider-dispatch-contract.json').read_text())
        decoder = ROOT / cls.proof['decoder']['path']
        assert hashlib.sha256(decoder.read_bytes()).hexdigest() == cls.proof['decoder']['sha256']
        cls.decoder = {}
        exec(decoder.read_text().split("idx={r['address']", 1)[0], cls.decoder)
        cls.read = staticmethod(cls.decoder['read'])
        cls.original = {r['address']: original_fragment((ROOT / r['path']).read_text(), r['address'][2:])
                        for r in cls.proof['original_fragments']}
        cls.sources = {Path(p).name: pre_collection_membership((ROOT / p).read_text()) for p in cls.proof['current_sources']}

    def test_original_twelve_fragments_and_static_disassembly_inputs_are_bound(self):
        self.assertEqual(len(self.proof['original_fragments']), 12)
        for row in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / row['path'])[row['address']]['sha256'], row['sha256'])
        for row in [self.proof['binary']] + self.proof['disassemblies']:
            self.assertEqual(hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest(), row['sha256'])

    def test_actual_reading_table_slot_is_collection_factory_not_writing_slot(self):
        rows = self.proof['witness_tables']
        self.assertEqual([(r['address'], r['target']) for r in rows], [
            ('0x100eccaa0', '0x100c42e20'), ('0x100eccab0', '0x100363d58'),
            ('0x100ecca50', '0x100c42e10'), ('0x100ecca60', '0x100363fcc')])
        for row in rows:
            a = int(row['address'], 16)
            value, chain = self.decoder['reachable_pointer'](a)
            self.assertEqual(chain, row['chain'])
            self.assertEqual(self.read(a, 8).hex(), row['bytes'])
            self.assertEqual(value >> 63, 0)
            self.assertEqual(self.decoder['base'] + (value & ((1 << 36) - 1)), int(row['target'], 16))

    def test_relative_protocol_descriptors_bind_both_tables_to_real_ItemRepository(self):
        def relative(a):
            return a + struct.unpack('<i', self.read(a, 4))[0]
        for row in self.proof['conformances']:
            a = int(row['address'], 16)
            self.assertEqual(relative(a), int(row['protocol']['address'], 16))
            self.assertEqual(relative(a + 4), int(row['type']['address'], 16))
            self.assertEqual(relative(a + 8), int(row['table'], 16))
            for key in ['protocol', 'type']:
                d = row[key]
                self.assertEqual(self.read(int(d['address'], 16), len(bytes.fromhex(d['bytes']))).hex(), d['bytes'])
                n = relative(int(d['address'], 16) + 8)
                self.assertEqual(n, int(d['name_address'], 16))
                self.assertEqual(self.read(n, len(d['name']) + 1), d['name'].encode() + b'\0')
        self.assertEqual([r['protocol']['name'] for r in self.proof['conformances']],
                         ['ItemRepositoryReading', 'ItemRepositoryWriting'])

    def test_repository_getter_really_supplies_reading_table_to_existential_cache(self):
        row = self.proof['reading_table_argument']
        a = int(row['address'], 16)
        w0, w1 = struct.unpack('<II', self.read(a, 8))
        self.assertEqual(w0 & 0x9f00001f, 0x90000003)
        self.assertEqual(w1 & 0xffc003ff, 0x91000063)
        imm = ((w0 >> 5) & 0x7ffff) * 4 + ((w0 >> 29) & 3)
        if imm & (1 << 20): imm -= 1 << 21
        target = (a & ~4095) + (imm << 12) + ((w1 >> 10) & 0xfff)
        self.assertEqual(target, 0x100eccaa0)
        self.assertIn('&PTR_PTR_100eccaa0', self.original['0x1003594c0'])
        self.assertIn('param_1[4] = param_5;', self.original['0x1003594e4'])

    def test_real_branches_link_request_before_FRC_collection_construction(self):
        for row in self.proof['branches']:
            a = int(row['address'], 16)
            word = struct.unpack('<I', self.read(a, 4))[0]
            self.assertEqual(word & 0xfc000000, 0x94000000 if row['kind'] == 'BL' else 0x14000000)
            imm = word & 0x3ffffff
            if imm & 0x2000000: imm -= 0x4000000
            self.assertEqual(a + 4 * imm, int(row['target'], 16))
        original = self.original['0x100363d58']
        self.assertLess(original.index('FUN_100329088()'), original.index('FUN_100365db4()'))
        self.assertLess(original.index('FUN_100365db4()'), original.index('FUN_1001ae768('))
        self.assertIn('FUN_100365e18(param_1,', self.original['0x100365db4'])

    def test_distinct_witness_calls_and_request_context_registers_are_byte_bound(self):
        words = self.proof['ARM_words']
        self.assertEqual(len(words), 14)
        for row in words:
            self.assertEqual(self.read(int(row['address'], 16), 4).hex(), row['bytes'])
        by_address = {int(r['address'], 16): struct.unpack('<I', bytes.fromhex(r['bytes']))[0] for r in words}
        self.assertEqual(by_address[0x1003bb598], 0xf9400b08)  # x24 reading witness
        self.assertEqual(by_address[0x100365d28], 0xf9400ac8)  # x22 context witness
        self.assertEqual(by_address[0x100365d00], 0xf9401293)  # request at instance+0x20
        self.assertEqual(by_address[0x100365d4c], 0xaa1303e2)  # request -> x2
        self.assertEqual(by_address[0x100365d50], 0xaa1403e3)  # context -> x3

    def test_FRC_selector_requires_saved_request_then_context_and_nil_section_cache(self):
        row = self.proof['FRC_selector']
        self.assertEqual(row['name'], 'initWithFetchRequest:managedObjectContext:sectionNameKeyPath:cacheName:')
        self.assertEqual(self.read(int(row['name_address'], 16), len(row['name']) + 1), row['name'].encode() + b'\0')
        self.assertEqual(self.read(int(row['pointer']['address'], 16), 8).hex(), row['pointer']['bytes'])
        self.assertTrue(row['chain']['declared_chain_reachable'])
        ctor = body(self.sources['ClipboardSearchCollection.swift'], 'init(context: NSManagedObjectContext, request:')
        self.assertIn('NSFetchedResultsController(fetchRequest: request, managedObjectContext: context,', ctor)
        self.assertIn('sectionNameKeyPath: nil, cacheName: nil', ctor)
        self.assertLess(ctor.index('controller = NSFetchedResultsController'), ctor.index('controller.performFetch()'))
        self.assertNotIn('PastoItemEntity.defaultFetchRequest', ctor)

    def test_existing_real_factory_uses_list_request_and_stable_supplied_context(self):
        store = body(self.sources['ClipboardStore.swift'], 'public func makeListCollection(')
        self.assertIn('persistence.makeListCollection(identifier: pinboardID?.uuidString ?? Self.historyListIdentifier)', store)
        factory = body(self.sources['ClipboardPersistence.swift'], 'func makeListCollection(identifier:')
        self.assertIn('context.performAndWait', factory)
        self.assertIn('guard let list = try? lists.list(identifier: identifier) else { return nil }', factory)
        self.assertIn('ClipboardSearchCollection(context: context, request: lists.itemRequest(for: list))', factory)
        for token in ['reset(', 'snapshotReader', 'NSManagedObjectContext(', 'save(', 'async', 'Task {']:
            self.assertNotIn(token, factory)

    def test_existing_request_keeps_real_history_and_group_predicates(self):
        request = body(self.sources['ClipboardListPersistence.swift'], 'func itemRequest(for list:')
        for token in ['PastoItemEntity.defaultFetchRequest()', 'case 1:', 'case 2:', 'default: break',
                      'NSSortDescriptor(key: "timestamp", ascending: false)',
                      'NSPredicate(format: "timestamp != nil")',
                      'NSSortDescriptor(key: "displayOrderInPinboard", ascending: true)',
                      'NSPredicate(format: "list == %@", list)']:
            self.assertIn(token, request)
        self.assertNotIn('metadata.index', request)
        self.assertNotIn('store.items', request)

    def test_actual_UI_retains_factory_source_and_consumes_its_ordered_snapshot(self):
        ui = self.sources['ReplicaUIController.swift']
        install = body(ui, 'private func installListCollectionSource(')
        self.assertLess(install.index('listCollectionObservation = nil'), install.index('store.makeListCollection'))
        self.assertIn('listCollection = source', install)
        self.assertIn('source?.publisher.dropFirst().sink', install)
        self.assertIn('pendingCollectionChangedIDs.formUnion(snapshot.updatedIdentifiers)', install)
        visible = body(ui, 'var visibleItems:')
        self.assertIn('let identifiers = listCollection?.value.identifiers ?? []', visible)
        self.assertIn('let native = identifiers.compactMap { items[$0] }', visible)
        self.assertIn('return native', visible)

    def test_cache_bytes_do_not_prove_full_model_replacement_or_ID_getter_contract(self):
        self.assertIn('if (pcVar1 == (code *)0x0)', self.original['0x1003b8bfc'])
        self.assertIn('*(code **)(unaff_x20 + 0x10) = pcVar2;', self.original['0x1003b8bfc'])
        self.assertEqual(self.proof['finite_difference_records_added'], 0)
        self.assertEqual(self.proof['finite_difference_records_repaired'], 0)
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertIsNone(self.proof['full_priority_completion_percent'])
        self.assertTrue(any('366344' in s for s in self.proof['remaining_limits']))


if __name__ == '__main__':
    unittest.main()
