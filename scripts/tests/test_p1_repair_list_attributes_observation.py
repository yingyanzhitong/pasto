from item_order_scope_contract import without_list_route
from frc_result_scope_contract import assert_visible_order_only, assert_ui_frc_only, assert_list_context_only
"""Original-bound list observation contracts; Python/source/Mach-O checks, no native execution."""
import hashlib
import json
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from native_tab_list_delivery_scope_contract import pre_native_tab_list_delivery
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment
from list_attributes_scope_contract import pre_attributes_host
from card_title_input_scope_contract import pre_card_title_input


class ListAttributesObservationContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-65'
        cls.proof = json.loads((cls.phase / 'list-attributes-contract.json').read_text())
        cls.paths = {'observer': 'replica/Sources/PastoCore/ClipboardListAttributesObservation.swift',
                     'attributes': 'replica/Sources/PastoCore/OriginalPinboardAttributes.swift',
                     'persistence': 'replica/Sources/PastoCore/ClipboardPersistence.swift',
                     'store': 'replica/Sources/PastoCore/ClipboardStore.swift',
                     'state': 'replica/Sources/Pasto/UI/ReplicaUIController.swift',
                     'host': 'replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift',
                     'card': 'replica/Sources/Pasto/UI/PanelViews.swift'}
        cls.sources = {k: (ROOT / p).read_text() for k, p in cls.paths.items()}
        cls.original = {r['address']: original_fragment((ROOT / r['path']).read_text(), r['address'][2:])
                        for r in cls.proof['original_fragments']}
        cls.words = {int(r['address'], 16): struct.unpack('<I', bytes.fromhex(r['bytes']))[0]
                     for r in cls.proof['ARM_words']}
        cls.observer = cls.sources['observer']
        cls.consume = body(cls.observer, 'private static func consume(')
        cls.host = cls.sources['host']
        cls.state = body(cls.sources['state'], 'final class ReplicaUIState:')
        cls.install = body(cls.host, 'private func installListAttributesObservation(')

    def before(self, key):
        return (self.phase / 'before' / self.paths[key]).read_text()

    def test_original_binary_eighteen_fragments_seven_sources_and_arm_are_hash_bound(self):
        self.assertEqual(len(self.proof['original_fragments']), 18)
        for row in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / row['path'])[row['address']]['sha256'], row['sha256'])
        for row in [self.proof['binary']] + self.proof['arm_disassemblies']:
            self.assertEqual(hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest(), row['sha256'])
        self.assertEqual(set(self.proof['current_sources']), set(self.paths.values()))
        for path, digest in self.proof['current_sources'].items():
            frozen = (self.phase / 'after' / path).read_text()
            self.assertEqual(hashlib.sha256((self.phase / 'after' / path).read_bytes()).hexdigest(), digest)
            if path in [self.paths['persistence'], self.paths['store']]:
                marker = 'func observeListAttributes('
                self.assertEqual(body((ROOT / path).read_text(), marker), body(frozen, marker))
            elif path == self.paths['state']:
                assert_ui_frc_only(self, (ROOT / path).read_text(), frozen)
            elif path == self.paths['host']:
                from live_item_render_scope_contract import pre_live_render
                self.assertEqual(pre_live_render((ROOT / path).read_text()), frozen)
            else:
                from stack_native_input_scope_contract import pre_stack_native_inputs
                self.assertEqual(pre_stack_native_inputs((ROOT / path).read_text()), frozen)

    def test_real_context_imports_bind_four_keys_and_exact_event_types(self):
        rows = self.proof['context_key_bindings']
        self.assertEqual([(r['symbol'], r['event']) for r in rows],
                         [('_NSInsertedObjectsKey', 0), ('_NSUpdatedObjectsKey', 2),
                          ('_NSDeletedObjectsKey', 1), ('_NSRefreshedObjectsKey', 3)])
        for row in rows + [self.proof['notification_binding']]:
            self.assertTrue(row['chain']['declared_chain_reachable'])
            pointer, = struct.unpack('<Q', bytes.fromhex(row['bytes']))
            self.assertEqual(pointer >> 63, 1)
            self.assertEqual(pointer & 0xffffff, row['ordinal'])
        self.assertEqual(self.proof['notification_binding']['symbol'], '_NSManagedObjectContextObjectsDidChangeNotification')

    def test_original_nonsearch_subject_gate_and_delete_skip_are_real_instructions(self):
        self.assertEqual(self.words[0x1003b927c], 0xd37efea8)
        self.assertEqual(self.words[0x1003b9280], 0xb40006c8)
        self.assertIn('FUN_1003b9264()', self.original['0x1003bb7bc'])
        self.assertIn('uVar6 >> 0x3e', self.original['0x1003b9264'])
        self.assertEqual(self.words[0x1003bb740], 0x7100051f)
        self.assertIn("if (param_2 != '\\x01')", self.original['0x1003bb73c'])
        self.assertLess(self.original['0x1003bb73c'].index('_swift_release();'),
                        self.original['0x1003bb73c'].index('FUN_1003293c4()'))

    def test_true_attribute_sink_is_force_visible_cells_not_adjacent_sidecar(self):
        self.assertEqual(self.words[0x1000681f0], 0xd0000060)
        self.assertEqual((self.words[0x1000681f4] >> 10) & 0xfff, 0x60c)
        self.assertIn('FUN_1000687d4()', self.original['0x10007660c'])
        self.assertEqual(self.words[0x100068888], 0xf9413d08)
        slot = self.proof['visible_cell_virtual_slot']
        self.assertEqual(slot['slot'], '0x100f91580')
        self.assertEqual(slot['target'], '0x10022c22c')
        self.assertTrue(slot['chain']['declared_chain_reachable'])
        prior = slot['class_identity_prior']
        self.assertEqual(hashlib.sha256((ROOT / prior['path']).read_bytes()).hexdigest(), prior['sha256'])
        self.assertIn('FUN_100221d34(1)', self.original['0x10022c22c'])
        self.assertIn('FUN_10006869c(', self.original['0x100076640'])
        self.assertNotIn('FUN_10006869c(', self.original['0x10007660c'])

    def test_semantic_equatable_attributes_use_existing_original_decoder_without_raw_data_dedup(self):
        source = self.sources['attributes']
        self.assertIn('public enum Value: Equatable', source)
        self.assertIn('case clipboard(capacity: Int)', source)
        self.assertIn('case pinboard(colorCode: UInt64)', source)
        decoded = body(source, 'public static func decoded(')
        self.assertIn('try? JSONDecoder().decode(Attributes.self, from: data)', decoded)
        self.assertIn('return f_1003245fc(attributes)', decoded)
        self.assertIn('else { return nil }', decoded)
        for marker in ['private static func f_1003245fc(', 'public static func colorCode(',
                       'public static func clipboardCapacity(', 'static func encodedClipboard(',
                       'static func encoded(colorCode:', 'static func parsedColorCode(']:
            self.assertEqual(body(source, marker), body(self.before('attributes'), marker))

    def test_store_to_actual_managed_list_factory_keeps_history_identifier_and_context_queue(self):
        store = body(self.sources['store'], 'public func observeListAttributes(')
        self.assertIn('pinboardID?.uuidString ?? Self.historyListIdentifier', store)
        self.assertIn('persistence.observeListAttributes(identifier:', store)
        factory = body(self.sources['persistence'], 'func observeListAttributes(')
        order = ['context.performAndWait', 'try? lists.list(identifier: identifier)',
                 'ClipboardListAttributesObservation(list: list)']
        self.assertEqual([factory.index(t) for t in order], sorted(factory.index(t) for t in order))
        self.assertIn('else { return nil }', factory)
        self.assertIn('guard let context = list.managedObjectContext else', self.observer)
        self.assertIn('preconditionFailure(', self.observer)

    def test_subject_initialization_and_context_object_id_capture_precede_notifications(self):
        initialize = body(self.observer, 'init(list: NSManagedObject)')
        order = ['subject = CurrentValueSubject(OriginalPinboardAttributes.decoded(',
                 'let objectID = list.objectID', '.publisher(for: .NSManagedObjectContextObjectsDidChange, object: context)',
                 '.sink { [weak self]', 'let subject = self?.subject', 'Self.consume(notification, objectID: objectID, subject: subject)']
        self.assertEqual([initialize.index(t) for t in order], sorted(initialize.index(t) for t in order))
        for forbidden in ['private let list:', 'private var list:', 'NSManagedObject?']:
            self.assertNotIn(forbidden, self.observer)
        self.assertNotIn('self', self.consume)
        self.assertIn('guard let subject else { return }', self.consume)

    def test_notification_dispatch_uses_current_event_object_exact_key_priority_and_delete_skip(self):
        self.assertIn('for key in [NSInsertedObjectsKey, NSUpdatedObjectsKey, NSDeletedObjectsKey, NSRefreshedObjectsKey]', self.consume)
        self.assertIn('objects.first(where: { $0.objectID == objectID }) else { continue }', self.consume)
        gate = body(self.consume, 'if key != NSDeletedObjectsKey')
        self.assertIn('subject.send(OriginalPinboardAttributes.decoded(from: list.value(forKey: "rawAttributes") as? Data))', gate)
        self.assertTrue(self.consume.rstrip().endswith('return\n        }\n    }'))
        for forbidden in ['reset(', 'rollback(', 'save(', 'fetch(', 'Task', 'DispatchQueue', 'objectWillChange', 'NSInvalidated']:
            self.assertNotIn(forbidden, self.consume)

    def test_subject_publisher_deduplicates_semantic_optional_before_host_skips_initial(self):
        self.assertIn('CurrentValueSubject<OriginalPinboardAttributes.Value?, Never>', self.observer)
        self.assertEqual(body(self.observer, 'public var publisher:'),
                         '{\n        subject.removeDuplicates().eraseToAnyPublisher()\n    }')
        value = body(self.observer, 'public var value:')
        self.assertIn('context.performAndWait', value)
        self.assertIn('try? context.existingObject(with: objectID), !list.isDeleted', value)
        self.assertIn('OriginalPinboardAttributes.decoded(from: list.value(forKey: "rawAttributes") as? Data)', value)
        self.assertNotIn('subject.value', value)
        for forbidden in ['reset(', 'rollback(', 'save(']:
            self.assertNotIn(forbidden, value)
        self.assertIn('source.publisher.dropFirst().sink', self.install)
        self.assertIn('Combine::Publisher::_removeDuplicates()', self.original['0x1003b8ffc'])
        self.assertIn('Combine::Publisher::dropFirst(1)', self.original['0x100067c84'])

    def test_actual_host_state_and_model_replacement_preserve_applier_lifecycle(self):
        pre_attributes_host(self, self.host)
        update = body(self.host, 'func update(state: ReplicaUIState, cardSide: CGFloat)')
        self.assertIn('if replacesState { installListAttributesObservation(state: state) }', update)
        replacement = body(self.host, 'func replaceCollectionModel(')
        self.assertLess(replacement.index('installListAttributesObservation(state: state)'), replacement.index('update(state: state'))
        self.assertIn('weak var listAttributesSource: ClipboardListAttributesObservation?', self.state)
        self.assertIn('private var listAttributesSource: ClipboardListAttributesObservation?', self.host)

    def test_installer_cancels_old_stream_before_gate_and_installs_real_weak_reload_consumer(self):
        order = ['listAttributesSubscription = nil', 'listAttributesSource = nil', 'state.listAttributesSource = nil',
                 'guard state.isCollectionSearchQueryEmpty, !state.showDeleted,',
                 'state.store.observeListAttributes(pinboardID: state.pinboardID)', 'listAttributesSource = source',
                 'state.listAttributesSource = source', 'source.publisher.dropFirst().sink { [weak self]',
                 'self?.reloadCellsForListAttributes()']
        self.assertEqual([self.install.index(t) for t in order], sorted(self.install.index(t) for t in order))
        for forbidden in ['normalizeSelection', 'refreshSearch', 'replaceCollectionModel(', 'DispatchQueue', 'Task {']:
            self.assertNotIn(forbidden, self.install)
        detached = body(self.host, 'func detachObservers()')
        self.assertIn('listAttributesSubscription = nil', detached)
        self.assertIn('state.listAttributesSource = nil', detached)

    def test_force_reload_recycles_and_invalidates_actual_visible_roots_without_snapshot_or_selection(self):
        reload = body(self.host, 'private func reloadCellsForListAttributes()')
        order = ['for cell in cells.values', 'cell.removeFromSuperview()', 'cell.invalidateRendering()',
                 'recycledCells.append(cell)', 'cells.removeAll()', 'tileCells()']
        self.assertEqual([reload.index(t) for t in order], sorted(reload.index(t) for t in order))
        self.assertIn('func invalidateRendering() { renderingSignature = nil }', self.host)
        for forbidden in ['selection', 'items =', 'pendingSnapshot', 'collectionOwnerGeneration', 'normalize', 'DispatchQueue']:
            self.assertNotIn(forbidden, reload)
        self.assertIn('cell.update(state: state, item: item, side: cardSide, index: index)', body(pre_card_title_input(self.host), 'private func tileCells()'))

    def test_renderer_reads_matching_current_subject_even_for_nil_instead_of_stale_store_payload(self):
        getter = body(self.state, 'func listAttributes(for pinboard: Pinboard)')
        self.assertIn('source.identifier == pinboard.id.uuidString { return source.value }', getter)
        self.assertIn('return OriginalPinboardAttributes.decoded(from: pinboard.rawAttributes)', getter)
        self.assertNotIn('??', getter)
        color = body(self.sources['card'], 'private var pinboardHeaderColor:')
        self.assertIn('case let .pinboard(code)? = state.listAttributes(for: owner)', color)
        self.assertIn('OriginalPinboardColor(canonicalColorCode: code).color()', color)
        self.assertNotIn('owner.rawAttributes', color)

    def test_global_UI_forwarder_cannot_refresh_search_or_selection_for_pure_attributes(self):
        initialize = body(self.state, 'init(store: ClipboardStore)')
        start = initialize.index('observation = store.objectWillChange.sink')
        forward = body(initialize[start:], 'observation = store.objectWillChange.sink')
        self.assertEqual(forward, '{ [weak self] _ in\n            self?.objectWillChange.send()\n        }')
        adapter = initialize[initialize.index('collectionSourceObservation = store.$items'):]
        self.assertIn('.combineLatest(store.$sourceApplications, store.$pinboards.map { Set($0.map(\.id)) })', adapter)
        self.assertIn('.removeDuplicates { lhs, rhs in lhs.0 == rhs.0 && lhs.1 == rhs.1 && lhs.2 == rhs.2 }', adapter)
        self.assertIn('.dropFirst()', adapter)
        self.assertIn('DispatchQueue.main.async { [weak self]', adapter)
        self.assertIn('self?.refreshSearch()', adapter)
        self.assertIn('self?.normalizeSelection()', adapter)
        for forbidden in ['rawAttributes', '.name', '$preferences']:
            self.assertNotIn(forbidden, adapter)

    def test_read_reset_commit_and_store_producers_remain_unchanged_outside_new_factory(self):
        for key, marker in [('persistence', 'func observeListAttributes('), ('store', 'public func observeListAttributes(')]:
            # The round65 insertion-only proof remains tied to its real post-edit snapshot;
            # round66 adds an independent rawType getter. Bind the actual observer factory too.
            current, previous = (self.phase / 'after' / self.paths[key]).read_text(), self.before(key)
            self.assertEqual(body(self.sources[key], marker), body(current, marker))
            start = current.index('    ' + marker)
            method = body(current, marker)
            end = current.index(method, start) + len(method) + (2 if key == 'persistence' else 1)
            self.assertEqual((current[:start], current[end:]), (previous[:start], previous[start:]))
        for marker in ['private func installSearchQueryDelivery()', 'private func applySelectedList(',
                       'private func installListSelectionDelivery()', 'func normalizeSelection(', 'var visibleItems:']:
            (assert_visible_order_only if marker == 'var visibleItems:' else assert_list_context_only if marker == 'private func installListSelectionDelivery()' else lambda t, a, b: t.assertEqual(without_list_route(pre_native_tab_list_delivery(a)), b))(self, body(self.state, marker), body(body(self.before('state'), 'final class ReplicaUIState:'), marker))

    def test_only_six_existing_sources_and_one_real_observer_added_no_FRC_claim(self):
        base = json.loads((self.phase / 'baseline.json').read_text())
        changed = {p for p, digest in base['production'].items() # Historical round65 exact edit set, before round66's separate Stack migration.
                   if hashlib.sha256((ROOT / '.local/p0-repair/phase-66/before' / p).read_bytes()).hexdigest() != digest}
        self.assertEqual(changed, set(self.paths.values()) - {self.paths['observer']})
        self.assertFalse((self.phase / 'before' / self.paths['observer']).exists())
        self.assertEqual([r['function_id'] for r in self.proof['contracts']], ['Paste:0x1003b9264', 'Paste:0x1003bb7bc'])
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertEqual(self.proof['function_map_markers_upgraded'], 0)
        self.assertTrue(any('365e18 FRC' in p for p in self.proof['retained_partial_contracts']))


if __name__ == '__main__':
    unittest.main()
