"""Initial FRC IDs: original branches, real constructor and source-only fixtures."""
from native_title_scope_contract import NEW_PATH as NATIVE_TITLE_PATH
from item_observation_scope_contract import NEW_PATH as ITEM_OBSERVATION_PATH
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
from collection_membership_scope_contract import ENTRY_PATH, pre_collection_membership_bytes
from modal_restore_scope_contract import RESTORE_ITEM_PATH, pre_modal_restore, pre_modal_restore_bytes
from test_p0_repair_checksum_routing import original_fragment
from collection_initial_ids_scope_contract import assert_initial_ID_route_only
from live_item_render_scope_contract import pre_live_render, pre_live_render_bytes, REFERENCE_PATH


class CollectionInitialIDContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-72'
        cls.proof = json.loads((cls.phase / 'initial-ID-contract.json').read_text())
        cls.base = json.loads((cls.phase / 'baseline.json').read_text())
        cls.path = 'replica/Sources/PastoCore/ClipboardSearchCollection.swift'
        cls.source = pre_live_render((ROOT / cls.path).read_text())
        cls.before = (cls.phase / 'before' / cls.path).read_text()
        cls.original = {r['address']: original_fragment((ROOT / r['path']).read_text(), r['address'][2:])
                        for r in cls.proof['original_fragments']}
        decoder = ROOT / '.local/p0-repair/phase-40/bind-contract.py'
        assert hashlib.sha256(decoder.read_bytes()).hexdigest() == 'a8633b85511ba71520454e870fcf76f6403f2c3f457be1c63a06b4bafeadff2d'
        cls.decoder = {}
        exec(decoder.read_text().split("idx={r['address']", 1)[0], cls.decoder)
        cls.read = staticmethod(cls.decoder['read'])

    def test_six_original_fragments_binary_SDK_and_ARM_artifacts_are_bound(self):
        self.assertEqual(len(self.proof['original_fragments']), 6)
        for row in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / row['path'])[row['address']]['sha256'], row['sha256'])
        for row in [self.proof['binary'], self.proof['sdk_header']] + self.proof['arm_disassemblies']:
            p = Path(row['path']) if Path(row['path']).is_absolute() else ROOT / row['path']
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), row['sha256'])
        self.assertEqual(hashlib.sha256(self.source.encode()).hexdigest(), self.proof['current_sources'][self.path])
        self.assertEqual((self.phase / 'after' / self.path).read_text(), self.source)

    def test_real_selectors_include_ID_query_shape_and_FRC_endpoints(self):
        rows = self.proof['selector_bindings']
        self.assertEqual([r['selector'] for r in rows], ['hasChanges', 'entityName', 'predicate', 'sortDescriptors',
            'setPredicate:', 'setSortDescriptors:', 'setResultType:', 'fetchedObjects', 'sections',
            'numberOfObjects', 'objectAtIndexPath:', 'objectID'])
        for row in rows:
            for key in ['stub', 'pointer', 'selector_bytes']:
                b = row[key]
                self.assertEqual(self.read(int(b['address'], 16), len(bytes.fromhex(b['bytes']))).hex(), b['bytes'])
            self.assertTrue(row['chain']['declared_chain_reachable'])
            self.assertEqual(bytes.fromhex(row['selector_bytes']['bytes']), row['selector'].encode() + b'\0')

    def test_ID_query_error_fallthrough_is_real_despite_Ghidra_unreachable_warning(self):
        native = self.original['0x100367014']
        self.assertIn('Removing unreachable block', native)
        words = {int(r['address'], 16): struct.unpack('<I', bytes.fromhex(r['bytes']))[0] for r in self.proof['ARM_words']}
        for row in self.proof['ARM_words']:
            self.assertEqual(self.read(int(row['address'], 16), 4).hex(), row['bytes'])
        branch = words[0x10036711c]
        self.assertEqual(branch & 0xff00001f, 0xb4000015)  # CBZ x21 error register
        self.assertEqual(0x10036711c + 4 * ((branch >> 5) & 0x7ffff), 0x10036714c)
        self.assertEqual(words[0x100367114], 0xd2800015)
        call = words[0x100367124]
        self.assertEqual(0x100367124 + (call & 0x3ffffff) * 4, 0x100bfc708)
        self.assertEqual(words[0x100367144], 0xf9406c00)

    def test_throwing_fetch_and_error_release_are_actual_imports(self):
        rows = self.proof['imports']
        self.assertIn('NSManagedObjectContextC8CoreDataE5fetch', rows[0]['symbol'])
        self.assertEqual(rows[1]['symbol'], '_swift_errorRelease')
        for row in rows:
            b = row['pointer'];value, chain = self.decoder['reachable_pointer'](int(b['address'], 16))
            self.assertEqual(chain, row['chain']);self.assertEqual(value >> 63, 1)
            self.assertEqual(value & 0xffffff, row['ordinal'])
            self.assertEqual(self.read(int(b['address'], 16), 8).hex(), b['bytes'])

    def test_actual_constructor_uses_ID_route_after_fetch_before_delegate_and_publish(self):
        ctor = body(self.source, 'init(context: NSManagedObjectContext, request:')
        order = ['try controller.performFetch()', 'catch { fatalError(', 'let initial = initialObjectIDs()',
                 'ClipboardSearchDifferenceDelegate(ids: initial)', 'controller.delegate = delegate',
                 'pending = (initial, [])', 'flushPending()', 'objectsObservation = NotificationCenter.default']
        self.assertEqual([ctor.index(t) for t in order], sorted(ctor.index(t) for t in order))
        native = self.original['0x100365e18']
        self.assertLess(native.index('FUN_100c07c00'), native.index('FUN_100366344();'))
        self.assertLess(native.index('FUN_100366344();'), native.index('objc_stub::setDelegate_'))

    def test_dirty_context_maps_FRC_before_any_ID_only_query(self):
        load = body(self.source, 'private func initialObjectIDs()')
        self.assertIn('guard !context.hasChanges else { return (controller.fetchedObjects ?? []).map(\\.objectID) }', load)
        self.assertLess(load.index('guard !context.hasChanges'), load.index('let ids = fetchInitialObjectIDs()'))
        self.assertEqual(load.count('fetchInitialObjectIDs()'), 1)
        self.assertIn('objc_stub::hasChanges', self.original['0x100366344'])

    def test_ID_request_copies_only_entity_predicate_and_sort_with_ID_result_type(self):
        fetch = body(self.source, 'private func fetchInitialObjectIDs()')
        for token in ['NSFetchRequest<NSManagedObjectID>(entityName: entityName)',
                      'request.predicate = controller.fetchRequest.predicate',
                      'request.sortDescriptors = controller.fetchRequest.sortDescriptors',
                      'request.resultType = .managedObjectIDResultType']:
            self.assertIn(token, fetch)
        for forbidden in ['.copy(', 'fetchLimit', 'fetchOffset', 'fetchBatchSize', 'includesPendingChanges',
                          'propertiesToFetch', 'affectedStores', 'returnsObjectsAsFaults']:
            self.assertNotIn(forbidden, fetch)
        sdk = Path(self.proof['sdk_header']['path']).read_text()
        self.assertIn('NSManagedObjectIDResultType\t\t= 0x01', sdk)

    def test_missing_entity_is_fatal_but_ID_query_error_is_empty_candidate(self):
        fetch = body(self.source, 'private func fetchInitialObjectIDs()')
        self.assertIn('guard let entityName = controller.fetchRequest.entityName else { fatalError(', fetch)
        self.assertIn('return (try? context.fetch(request)) ?? []', fetch)
        self.assertNotIn('logger', fetch)
        self.assertLess(fetch.index('fatalError'), fetch.index('NSFetchRequest<NSManagedObjectID>'))
        self.assertEqual(self.source.count('controller.performFetch()'), 1)

    def test_count_first_and_last_guards_preserve_FRC_fallback_and_zero_count(self):
        load = body(self.source, 'private func initialObjectIDs()')
        order = ['let ids = fetchInitialObjectIDs()', 'let count = controller.sections?.first?.numberOfObjects',
                 'ids.count == count', 'ids.first == fetchedObjectID(at: 0)',
                 'ids.last == fetchedObjectID(at: ids.count - 1)',
                 'return (controller.fetchedObjects ?? []).map(\\.objectID)', 'return ids']
        # The first fallback belongs to dirty-context guard; inspect only the clean path here.
        clean = load[load.index('let ids = fetchInitialObjectIDs()'):]
        self.assertEqual([clean.index(t) for t in order], sorted(clean.index(t) for t in order))
        for forbidden in ['ids.isEmpty', 'ids ==', 'Set(ids)', '.sorted', 'ids.allSatisfy', 'save(', 'reset(']:
            self.assertNotIn(forbidden, clean)

    def test_endpoint_lookup_checks_negative_missing_section_and_upper_bound(self):
        lookup = body(self.source, 'private func fetchedObjectID(at index:')
        self.assertIn('guard index >= 0, let count = controller.sections?.first?.numberOfObjects, index < count else { return nil }', lookup)
        self.assertIn('controller.object(at: IndexPath(indexes: [0, index])).objectID', lookup)
        self.assertNotIn('fetchedObjects', lookup)
        self.assertNotIn('context.fetch', lookup)
        self.assertIn('if (-1 < param_1)', self.original['0x100367184'])
        self.assertIn('if (param_1 < (long)IVar6)', self.original['0x100367184'])

    def test_subject_value_pending_notification_and_difference_methods_remain_unchanged(self):
        assert_initial_ID_route_only(self, self.source, self.before)
        for signature in ['private func receive(', 'private func flushPending()', 'private func objectsDidChange(',
                          'nonisolated func controller(', 'convenience init(context:']:
            self.assertEqual(body(self.source, signature), body(self.before, signature))
        self.assertIn('public var value: Snapshot { subject.value }', self.source)

    def test_static_branch_table_keeps_endpoint_only_shortcut_not_full_ID_comparison(self):
        # Scalar fixtures describe the proven branches; they do not execute Swift/CoreData.
        fixtures = [
            (False, ['A', 'B'], ['A', 'B'], 2, 'ids'),
            (True, ['A', 'B'], ['A', 'B'], 2, 'frc'),
            (False, [], [], 0, 'ids'),
            (False, [], [], None, 'frc'),
            (False, [], ['A'], 1, 'frc'),
            (False, ['X'], ['A'], 1, 'frc'),
            (False, ['A', 'X'], ['A', 'B'], 2, 'frc'),
            (False, ['A', 'X', 'C'], ['A', 'B', 'C'], 3, 'ids')]
        def at(values, count, index):
            return values[index] if count is not None and 0 <= index < count else None
        for dirty, ids, frc, count, expected in fixtures:
            first = ids[0] if ids else None;last = ids[-1] if ids else None
            use_ids = not dirty and count is not None and len(ids) == count and first == at(frc, count, 0) and last == at(frc, count, len(ids) - 1)
            self.assertEqual('ids' if use_ids else 'frc', expected)

    def test_one_production_file_changed_without_schema_storage_or_UI_edits(self):
        changed = [p for p, h in self.base['production'].items() if hashlib.sha256(pre_live_render_bytes(ROOT / p)).hexdigest() != h]
        self.assertEqual(changed, [self.path])
        self.assertEqual({str(p.relative_to(ROOT)) for p in (ROOT / 'replica/Sources').rglob('*') if p.is_file()} - {NATIVE_TITLE_PATH, ITEM_OBSERVATION_PATH} - {REFERENCE_PATH, RESTORE_ITEM_PATH, ENTRY_PATH}, set(self.base['production']))
        for p in ['replica/Package.swift', 'package.json']:
            self.assertEqual(hashlib.sha256((ROOT / p).read_bytes()).hexdigest(), self.base['other'][p])

    def test_backlog_adds_only_initialization_gap_and_retains_old161_records(self):
        old = json.loads((ROOT / 'reports/replica/p0-p1-difference-backlog-v14.json').read_text())
        current = json.loads((ROOT / 'reports/replica/p0-p1-difference-backlog-v15.json').read_text())
        self.assertEqual(current['groups'][:-1], old['groups'])
        self.assertEqual(current['added_function_ids'], ['Paste:0x100366344'])
        self.assertEqual(current['counts']['difference_records'], 162)
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertEqual(self.proof['function_map_markers_upgraded'], 0)


if __name__ == '__main__':
    unittest.main()
