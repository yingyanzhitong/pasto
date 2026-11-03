from native_title_scope_contract import pre_native_title_bytes
from item_order_scope_contract import assert_common_FRC_ctor_only, without_order_persistence, without_list_factory, without_list_UI_insertions
"""Real FRC source/consumer contracts and source-bound semantic fixtures; no native execution."""
import hashlib
import itertools
import json
import struct
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment
from frc_result_scope_contract import assert_factory_addition_only, assert_query_result_only, assert_ui_frc_only, assert_visible_order_only, assert_list_context_only
from live_item_render_scope_contract import pre_live_render


class FRCResultSourceContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-68'
        cls.proof = json.loads((cls.phase / 'FRC-result-contract.json').read_text())
        cls.base = json.loads((cls.phase / 'baseline.json').read_text())
        cls.paths = dict(source='replica/Sources/PastoCore/ClipboardSearchCollection.swift',
                         view='replica/Sources/PastoCore/ClipboardPersistence.swift',
                         store='replica/Sources/PastoCore/ClipboardStore.swift',
                         index='replica/Sources/Pasto/UI/ReplicaSearchIndex.swift',
                         ui='replica/Sources/Pasto/UI/ReplicaUIController.swift')
        cls.sources = {k: pre_live_render((ROOT / p).read_text()) for k, p in cls.paths.items()}
        cls.source = cls.sources['source']; cls.index = cls.sources['index']; cls.ui = cls.sources['ui']
        cls.original = {r['address']: original_fragment((ROOT / r['path']).read_text(), r['address'][2:]) for r in cls.proof['original_fragments']}

    def before(self, key): return (self.phase / 'before' / self.paths[key]).read_text()

    def test_fifteen_original_fragments_sdk_headers_and_five_production_files_are_bound(self):
        self.assertEqual(len(self.proof['original_fragments']), 15)
        for row in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / row['path'])[row['address']]['sha256'], row['sha256'])
        for row in [self.proof['binary']] + self.proof['sdk_headers'] + self.proof['arm_disassemblies']:
            self.assertEqual(hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest(), row['sha256'])
        for path, digest in self.proof['current_sources'].items():
            frozen = (self.phase / 'after' / path).read_bytes()
            self.assertEqual(hashlib.sha256(frozen).hexdigest(), digest)
            if path == self.paths['ui']:
                # phase69 type routing plus phase70 ordinary-source additions are explicitly delimited.
                current = without_list_UI_insertions((ROOT / path).read_text()); old = without_list_UI_insertions(frozen.decode())
                from item_order_scope_contract import assert_history_list_projection_only
                cv = body(current, 'var visibleItems:'); ov = body(old, 'var visibleItems:')
                assert_history_list_projection_only(self, cv, ov)
                for a, b in zip(current.split(cv), old.split(ov)):
                    if 'private func installListSelectionDelivery()' in a: assert_list_context_only(self, a, b)
                    else: self.assertEqual(a, b)
            elif path == self.paths['view']:
                self.assertEqual(without_order_persistence((ROOT / path).read_text()), frozen.decode())
            elif path == self.paths['store']:
                self.assertEqual(without_list_factory((ROOT / path).read_text(), public=True), frozen.decode())
            elif path == self.paths['source']:
                current = pre_live_render((ROOT / path).read_text())
                assert_common_FRC_ctor_only(self, current, frozen.decode())
                for marker in ['private func receive(', 'private func flushPending()', 'private func objectsDidChange(', 'nonisolated func controller(']:
                    self.assertEqual(body(current, marker), body(frozen.decode(), marker))
            else:
                self.assertEqual(pre_live_render((ROOT / path).read_text()).encode(), frozen)

    def test_real_runtime_method_table_selects_difference_not_snapshot_or_legacy(self):
        delegate = self.proof['difference_delegate']
        flags, count = struct.unpack('<II', bytes.fromhex(delegate['method_list']['bytes'])[:8])
        self.assertEqual(count, 3); self.assertTrue(flags & 0x80000000)
        callbacks = [r for r in delegate['methods'] if r['selector'].startswith('controller:')]
        self.assertEqual([(r['selector'], r['imp']) for r in callbacks], [('controller:didChangeContentWithDifference:', '0x100354f90')])
        entry, = callbacks
        address = int(entry['entry']['address'], 16)
        _, _, imp = struct.unpack('<iii', bytes.fromhex(entry['entry']['bytes']))
        self.assertEqual(hex(address + 8 + imp), entry['imp'])
        self.assertEqual(bytes.fromhex(entry['selector_bytes']['bytes']), entry['selector'].encode() + b'\0')
        self.assertIn('didChangeContentWith diff: CollectionDifference<NSManagedObjectID>', self.source)
        for forbidden in ['didChangeContentWithSnapshot', 'didChange anObject', 'controllerDidChangeContent']:
            self.assertNotIn(forbidden, self.source)

    def test_seven_actual_selectors_and_updated_refreshed_imports_have_dyld_chains(self):
        self.assertEqual([r['selector'] for r in self.proof['selector_bindings']], [
            'initWithFetchRequest:managedObjectContext:sectionNameKeyPath:cacheName:', 'performFetch:',
            'fetchedObjects', 'sections', 'numberOfObjects', 'setDelegate:', 'setFetchBatchSize:'])
        for row in self.proof['selector_bindings']:
            self.assertTrue(row['chain']['declared_chain_reachable'])
            self.assertEqual(bytes.fromhex(row['selector_bytes']['bytes']), row['selector'].encode() + b'\0')
        self.assertEqual([r['symbol'] for r in self.proof['context_key_bindings']], [
            '_NSUpdatedObjectsKey', '_NSRefreshedObjectsKey', '_NSManagedObjectContextObjectsDidChangeNotification'])
        for row in self.proof['context_key_bindings']:
            self.assertTrue(row['chain']['declared_chain_reachable'])
            self.assertEqual(struct.unpack('<Q', bytes.fromhex(row['bytes']))[0] & 0xffffff, row['ordinal'])

    def test_fetch_error_branch_precedes_delegate_in_actual_ARM(self):
        words = {int(r['address'], 16): struct.unpack('<I', bytes.fromhex(r['bytes']))[0] for r in self.proof['ARM_words']}
        call = words[0x100365f9c]; displacement = call & ((1 << 26) - 1)
        if displacement & (1 << 25): displacement -= 1 << 26
        self.assertEqual(0x100365f9c + 4 * displacement, 0x100c07c00)
        branch = words[0x100365fb0]; displacement = (branch >> 5) & 0x7ffff
        if displacement & (1 << 18): displacement -= 1 << 19
        self.assertEqual(0x100365fb0 + 4 * displacement, 0x100366284)
        native = self.original['0x100365e18']
        self.assertLess(native.index('FUN_100c07c00'), native.index('if ((int)IVar8 == 0)'))
        failure = native[native.index('if ((int)IVar8 == 0)'):native.index('FUN_100366344();')]
        self.assertIn('Foundation::__convertNSErrorToError()', failure)
        self.assertIn('Swift::_assertionFailure', failure)
        self.assertLess(native.index('FUN_100366344();'), native.index('objc_stub::setDelegate_'))

    def test_real_initializer_fetch_delegate_initial_publish_then_context_observer(self):
        init = body(self.source, 'init(context: NSManagedObjectContext, request:')
        order = ['NSFetchedResultsController(fetchRequest:',
                 'sectionNameKeyPath: nil, cacheName: nil)', 'try controller.performFetch()',
                 'catch { fatalError(', 'let initial = initialObjectIDs()',
                 'ClipboardSearchDifferenceDelegate(ids: initial)', 'differenceDelegate = delegate', 'controller.delegate = delegate',
                 'pending = (initial, [])', 'flushPending()', 'objectsObservation = NotificationCenter.default']
        self.assertEqual([init.index(t) for t in order], sorted(init.index(t) for t in order))
        for forbidden in ['try?', 'throws', 'context.reset()', 'context.save()', 'needsReset', 'acknowledge']:
            self.assertNotIn(forbidden, init)
        self.assertEqual(self.source.count('controller.performFetch()'), 1)
        self.assertIn('private var differenceDelegate: ClipboardSearchDifferenceDelegate?', self.source)

    def test_empty_array_is_nil_source_and_raw_native_identifiers_are_not_preprocessed(self):
        factory = body(self.sources['view'], 'func makeSearchCollection(')
        self.assertLess(factory.index('guard !identifiers.isEmpty else { return nil }'), factory.index('ClipboardSearchCollection(context: context, identifiers: identifiers)'))
        self.assertIn('nativeIdentifier IN %@ OR (nativeIdentifier == nil AND key IN %@)', self.source)
        init = body(self.source, 'convenience init(context:')
        for token in ['Set(identifiers)', 'UUID(uuidString:', 'identifiers.filter', 'identifiers.compactMap', 'fetchLimit', 'request.sortDescriptors =']:
            self.assertNotIn(token, init)
        self.assertIn('request.fetchBatchSize = 20', (ROOT / 'replica/Sources/PastoCore/OriginalManagedItem.swift').read_text())
        self.assertIn('NSSortDescriptor(key: "timestamp", ascending: false)', (ROOT / 'replica/Sources/PastoCore/OriginalManagedItem.swift').read_text())
        self.assertIn('if (lVar11 == 0)', self.original['0x100360808'])
        self.assertIn('FUN_100c0bb60(self,0x14)', self.original['0x100360808'])

    def test_difference_uses_original_empty_guard_apply_count_and_fetched_fallback(self):
        callback = body(self.source, 'nonisolated func controller(')
        order = ['MainActor.assumeIsolated', 'guard !diff.isEmpty else { return }', 'controller.sections?.first?.numberOfObjects',
                 'if let next = ids.applying(diff), expectedCount == nil || next.count == expectedCount',
                 'ids = next', 'controller.fetchedObjects as? [NSManagedObject]', 'handler(ids)']
        self.assertEqual([callback.index(t) for t in order], sorted(callback.index(t) for t in order))
        for token in ['fatalError', 'throw', 'performFetch', 'context.reset', 'Task {']:
            self.assertNotIn(token, callback)
        native = self.original['0x100354800']
        for token in ['if (local_68 == local_70)', 'RangeReplaceableCollection::_applying', 'if (IVar5 == IVar11)', 'FUN_100c023c0(param_1)', '(*pcVar2)(uVar10,puVar6)']:
            self.assertIn(token, native)

    def test_object_changes_only_reload_visible_updated_or_refreshed_IDs(self):
        observer = body(self.source, 'private func objectsDidChange(')
        for token in ['let ids = pending?.ids ?? objectIDs', 'NSUpdatedObjectsKey', 'NSRefreshedObjectsKey',
                      'Set(updated.union(refreshed).map(\\.objectID)).intersection(membership)', 'if !changed.isEmpty { receive(ids: ids, updated: changed) }']:
            self.assertIn(token, observer)
        for token in ['NSInsertedObjectsKey', 'NSDeletedObjectsKey', 'NSInvalidatedObjectsKey', 'save()', 'reset()']:
            self.assertNotIn(token, observer)
        self.assertIn('object: context', body(self.source, 'init(context: NSManagedObjectContext, request:'))

    def test_pending_accumulates_before_single_scheduled_weak_delivery_and_clears_before_send(self):
        receive = body(self.source, 'private func receive(')
        order = ['let schedulesDelivery = pending == nil', 'pending = (ids, (pending?.updated ?? []).union(updated))',
                 'if schedulesDelivery', 'context.perform { [weak self]', 'self?.flushPending()']
        self.assertEqual([receive.index(t) for t in order], sorted(receive.index(t) for t in order))
        flush = body(self.source, 'private func flushPending()')
        self.assertLess(flush.index('pending = nil'), flush.index('objectIDs = value.ids'))
        self.assertLess(flush.index('objectIDs = value.ids'), flush.index('subject.send('))
        self.assertNotIn('DispatchQueue', self.source)
        native = self.original['0x100366b38']
        self.assertLess(native.index('*(ulong *)(unaff_x20 + 0x48) = 0'), native.index('CurrentValueSubject::send'))

    def test_actual_source_retention_and_initial_cache_subscription_have_no_ownership_cycle(self):
        self.assertIn('private var resultSource: ClipboardSearchCollection?', self.index)
        self.assertIn('private var resultObservation: AnyCancellable?', self.index)
        install = body(self.index, 'private func installResultSource(')
        order = ['resultObservation = nil', 'resultSource = source', 'orderedIdentifiers = source?.value.identifiers ?? []',
                 'identifiers = Set(orderedIdentifiers)', 'source?.publisher.dropFirst().sink { [weak self] snapshot',
                 'self.orderedIdentifiers = snapshot.identifiers', 'self.identifiers = Set(snapshot.identifiers)',
                 'self.onCollectionUpdate?(snapshot.updatedIdentifiers)']
        self.assertEqual([install.index(t) for t in order], sorted(install.index(t) for t in order))
        self.assertIn('import Combine\n', self.index)
        self.assertIn('private let subject = CurrentValueSubject<Snapshot, Never>', self.source)
        self.assertIn('public var value: Snapshot { subject.value }', self.source)
        self.assertIn('{ [weak self] ids in', self.source)
        self.assertIn('.sink { [weak self] notification in', self.source)

    def test_query_success_empty_error_and_cancellation_use_real_source_boundary(self):
        query = body(self.index, 'private func replaceQuery(')
        assert_query_result_only(self, query, body(self.before('index'), 'private func replaceQuery('))
        self.assertLess(query.index('try Task.checkCancellation()'), query.index('store.makeSearchCollection('))
        self.assertLess(query.index('installResultSource(store.makeSearchCollection('), query.index('onUpdate?()'))
        cancellation = query.split('catch is CancellationError {', 1)[1].split('} catch {', 1)[0]
        self.assertNotIn('installResultSource', cancellation)
        failure = query.split('} catch {', 1)[1]
        self.assertLess(failure.index('guard !Task.isCancelled'), failure.index('installResultSource(nil)'))
        fallback = query.split('} else {', 1)[1].split('                error = nil', 1)[0]
        self.assertLess(fallback.index('installResultSource(nil)'), fallback.index('orderedIdentifiers = entries.filter'))
        self.assertNotIn('searchNativeItems', query)
        self.assertEqual(body(self.index, 'nonisolated private static func matchingIdentifiers('), body(self.before('index'), 'nonisolated private static func matchingIdentifiers('))

    def test_actual_UI_visible_items_preserve_FRC_order_and_existing_deleted_compatibility(self):
        visible = body(self.ui, 'var visibleItems:')
        assert_visible_order_only(self, visible, body(self.before('ui'), 'var visibleItems:'))
        self.assertNotIn('.sorted', visible)
        self.assertNotIn('searchIndex.identifiers.contains', visible)
        callback = body(self.ui, 'searchIndex.onCollectionUpdate =')
        self.assertIn('!self.isCollectionSearchQueryEmpty', callback)
        self.assertIn('self.pendingCollectionChangedIDs.formUnion(identifiers)', callback)
        self.assertIn('self.objectWillChange.send()', callback)
        for token in ['normalizeSelection', 'applyOrderedSelection', 'replaceCollectionModel', 'save()']:
            self.assertNotIn(token, callback)
        host = (ROOT / 'replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift').read_text()
        self.assertIn('let incomingItems = state.visibleItems', host)
        self.assertIn('state.takeCollectionChangedIDs(owner: self)', host)

    def test_schemas_snapshots_index_error_and_other_UI_lifecycle_are_unchanged(self):
        assert_factory_addition_only(self, self.sources['view'], self.before('view'))
        assert_factory_addition_only(self, self.sources['store'], self.before('store'), public=True)
        assert_ui_frc_only(self, self.ui, self.before('ui'))
        snapshot = 'replica/Sources/PastoCore/ClipboardSnapshotReader.swift'
        self.assertEqual(hashlib.sha256(pre_native_title_bytes(ROOT / snapshot)).hexdigest(), self.base['production'][snapshot])
        self.assertIn('guard identifiers != nil else { throw error }', (ROOT / snapshot).read_text())
        self.assertNotIn('fatalError', (ROOT / snapshot).read_text())
        for marker in ['private func drain() async', 'private func liveEntries(', 'private func retryTransientIndexErrors(', 'private func stopIndexing()', 'private func searchableItem(', 'private static func writeSearchableItems(']:
            self.assertEqual(body(self.index, marker), body(self.before('index'), marker))

    def test_delta_and_projection_fixtures_cover_apply_failure_count_mismatch_and_empty_diff(self):
        # Branch table is tied to the production method above, not execution of Swift/CoreData.
        fixtures = [(False, ['B'], 1, ['B']), (False, None, 1, ['fallback']),
                    (False, ['B'], 2, ['fallback']), (False, ['B'], None, ['B']),
                    (True, ['B'], 1, ['old'])]
        for empty, applied, count, wanted in fixtures:
            actual = ['old']
            if not empty:
                actual = applied if applied is not None and (count is None or len(applied) == count) else ['fallback']
            self.assertEqual(actual, wanted)
        # UI projection retains source order while mapping only available local DTOs.
        values = {'A': False, 'B': True, 'C': False}
        for deleted in [False, True]:
            actual = [i for i in ['C', 'missing', 'B', 'A'] if i in values and values[i] == deleted]
            self.assertEqual(actual, ['B'] if deleted else ['C', 'A'])

    def test_pending_batch_and_reentry_semantics_keep_newest_order_union_and_one_schedule(self):
        for orders in itertools.permutations([('A', 'B'), ('B',), ('C', 'B')]):
            pending = None; schedules = 0
            for n, ids in enumerate(orders):
                schedules += pending is None
                pending = (ids, (pending[1] if pending else set()) | {str(n)})
            self.assertEqual(schedules, 1)
            self.assertEqual(pending, (orders[-1], {'0', '1', '2'}))
            sent = pending; pending = None
            # Flush clears first; a subscriber can queue a fresh batch without losing it.
            pending = (('reentered',), {'next'}) if pending is None else None
            self.assertEqual(sent[0], orders[-1]);self.assertEqual(pending[0], ('reentered',))

    def test_fixed_finite_closure_does_not_claim_original_complete_parent_or_native_execution(self):
        row, = self.proof['contracts']
        self.assertEqual(row['function_id'], 'Paste:0x100365e18')
        self.assertFalse(row['full_function_migration_verified'])
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertEqual(self.proof['function_map_markers_upgraded'], 0)
        self.assertIn('different producer36dc00', self.proof['comparison_correction'])
        limits = ' '.join(self.proof['retained_partial_contracts'])
        for token in ['witness+8', 'not proven API', 'no compile/typecheck', 'Unknown04430c/0f733c', 'general history/group']:
            self.assertIn(token, limits)


if __name__ == '__main__': unittest.main()
