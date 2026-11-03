from item_order_scope_contract import without_list_route
from item_order_scope_contract import without_list_route
from frc_result_scope_contract import assert_visible_order_only, assert_list_context_only
"""Optional-list force-selection source/ARM checks; does not execute Combine or Swift."""
import hashlib
import json
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from collection_membership_scope_contract import pre_collection_membership, pre_collection_membership_bytes, ENTRY_PATH
from list_attributes_scope_contract import pre_attributes_host
from test_p0_repair_checksum_routing import original_fragment


class ListSelectionContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-59'
        cls.proof = json.loads((cls.phase / 'list-selection-contract.json').read_text())
        cls.ui_path = 'replica/Sources/Pasto/UI/ReplicaUIController.swift'
        cls.store_path = 'replica/Sources/PastoCore/ClipboardStore.swift'
        cls.ui = pre_collection_membership((ROOT / cls.ui_path).read_text())
        cls.choose = body(cls.ui, 'func chooseBoard(')
        cls.select = body(cls.ui, 'private func selectListIdentifier(')
        cls.delivery = body(cls.ui, 'private func installListSelectionDelivery()')
        cls.consumer = body(cls.ui, 'private func applySelectedList(')
        cls.original = {r['address']: original_fragment((ROOT / r['path']).read_text(), r['address'][2:])
                        for r in cls.proof['original_fragments']}

    def test_evidence_and_actual_production_inputs_are_bound(self):
        self.assertEqual(len(self.proof['original_fragments']), 13)
        for row in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / row['path'])[row['address']]['sha256'], row['sha256'])
        for row in [self.proof['binary']] + self.proof['arm_disassemblies']:
            self.assertEqual(hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest(), row['sha256'])
        for path, digest in self.proof['current_sources'].items():
            frozen = (self.phase / 'after' / path).read_text()
            self.assertEqual(hashlib.sha256((self.phase / 'after' / path).read_bytes()).hexdigest(), digest)
            markers = {self.ui_path: ['func chooseBoard(', 'private func selectListIdentifier(',
                       'private func installListSelectionDelivery()', 'private func applySelectedList('],
                       self.store_path: ['public func localListMenuState(pinboardID:']}[path]
            for marker in markers:
                (assert_list_context_only if marker == 'private func installListSelectionDelivery()' else lambda t, a, b: t.assertEqual(without_list_route(a), b))(self, body((ROOT / path).read_text(), marker), body(frozen, marker))

    def test_native_conditional_nil_then_unconditional_target_setters_are_distinct(self):
        words = {r['address']: int.from_bytes(bytes.fromhex(r['bytes']), 'little') for r in self.proof['ARM_words']}
        def target(address):
            word = words[hex(address)]
            if word & 0x7c000000 == 0x14000000:
                shift, width = 0, 26
            elif word & 0x7e000000 == 0x36000000:
                shift, width = 5, 14
            else:
                shift, width = 5, 19
            offset = (word >> shift) & ((1 << width) - 1)
            if offset & (1 << (width - 1)):
                offset -= 1 << width
            return address + 4 * offset
        self.assertEqual(target(0x100039d38), 0x100039dc8)
        self.assertEqual(target(0x100039d58), 0x100039d88)
        for a in [0x100039d80, 0x100039d84]:
            self.assertEqual(target(a), 0x100039dc8)
        self.assertEqual(words['0x100039da8'], 0xa9027fff)  # stp xzr,xzr
        self.assertEqual(words['0x100039de8'], 0xa9024ff6)  # stp target words
        for a in [0x100039dc4, 0x100039e10]:
            self.assertEqual(target(a), 0x1002cb5a0)
        self.assertEqual(target(0x10003a99c), 0x10003a9e0)  # nil consumer skips resolution
        self.assertEqual(target(0x10003a9b8), 0x10003a9fc)
        self.assertEqual(target(0x10003aa48), 0x10003ab14)  # unresolved skips publication

    def test_force_gate_reads_real_subject_state_and_always_delivers_target(self):
        self.assertIn('private let listIdentifierChanges = CurrentValueSubject<String?, Never>(ClipboardStore.historyListIdentifier)', self.ui)
        self.assertIn('if let current = listIdentifierChanges.value, current == identifier, force', self.select)
        self.assertEqual(self.select.count('listIdentifierChanges.send(nil)'), 1)
        self.assertEqual(self.select.count('listIdentifierChanges.send(identifier)'), 1)
        self.assertLess(self.select.index('send(nil)'), self.select.index('send(identifier)'))
        self.assertNotIn('pinboardID =', self.select)
        self.assertNotIn('replaceCollectionModel', self.select)
        self.assertNotIn('return', self.select)
        native = self.original['0x100039c50']
        self.assertIn('if (local_a8.unknown != (undefined *)0x0)', native)
        self.assertIn('if ((param_3 & 1) != 0)', native)
        self.assertEqual(native.count('FUN_1002cb5a0(&local_b0)'), 2)

    def test_real_subscription_installed_and_retained_after_dependencies_before_search(self):
        self.assertIn('private var listIdentifierObservation: AnyCancellable?', self.ui)
        init = body(body(self.ui, 'final class ReplicaUIState: ObservableObject'), 'init(store: ClipboardStore)')
        steps = ['searchIndex = ReplicaSearchIndex(', 'installListSelectionDelivery()', 'installSearchQueryDelivery()']
        self.assertEqual([init.index(t) for t in steps], sorted(init.index(t) for t in steps))
        self.assertIn('listIdentifierObservation = listIdentifierChanges.sink { [weak self] identifier in', self.delivery)
        self.assertIn('guard let self, let identifier else { return }', self.delivery)
        self.assertNotIn('removeDuplicates', self.delivery)
        self.assertNotIn('Task', self.delivery)
        self.assertNotIn('DispatchQueue', self.delivery)

    def test_nil_and_unresolved_events_cannot_masquerade_as_history(self):
        self.assertLess(self.delivery.index('guard let self, let identifier else { return }'),
                        self.delivery.index('identifier == ClipboardStore.historyListIdentifier'))
        self.assertIn('self.store.pinboards.first(where: { $0.id.uuidString == identifier }) else { return }', self.delivery)
        self.assertLess(self.delivery.index('id = board.id'), self.delivery.index('self.applySelectedList(id)'))
        self.assertEqual(self.delivery.count('self.applySelectedList(id)'), 1)
        self.assertNotIn('?? nil', self.delivery)
        self.assertIn('public static let historyListIdentifier = ClipboardListPersistence.historyIdentifier', (ROOT / self.store_path).read_text())
        self.assertIn('static let historyIdentifier = "sharedPasteboardHistory"',
                      (ROOT / 'replica/Sources/PastoCore/ClipboardListPersistence.swift').read_text())

    def test_successful_selection_tail_is_reused_exactly_not_run_on_nil(self):
        previous = (self.phase / 'before' / self.ui_path).read_text()
        self.assertEqual(without_list_route(self.consumer), body(previous, 'func chooseBoard('))
        for token in ['cancelItemDeletion()', 'pinboardID = id', 'selection = []',
                      'normalizeProjectedSelection()', 'collectionOwner?.replaceCollectionModel(state: self)']:
            self.assertIn(token, self.consumer)
            self.assertNotIn(token, self.select + self.delivery)
        self.assertIn('FUN_10003a9fc(param_3,param_4)', self.original['0x10003a900'])
        self.assertIn('if (local_48 != 0)', self.original['0x10003a9fc'])
        self.assertIn('Combine::Published::_set_subscript()', self.original['0x10003a9fc'])

    def test_tab_reveal_and_fallback_reach_actual_identifier_entry(self):
        self.assertIn('selectListIdentifier(id?.uuidString ?? ClipboardStore.historyListIdentifier, force: true)', self.choose)
        for address in ['0x100099adc', '0x10007d9c8', '0x1000a1cb0']:
            native = self.original[address]
            self.assertRegex(native, r'FUN_100039c50\([^;]+,1\)')
        reveal = body(self.ui, 'func chooseListForItemReveal(')
        self.assertLess(reveal.index('applySearchInput(nodes: [], text: "", filters: [])'), reveal.index('chooseBoard(id)'))
        fallback = body(self.ui, 'func normalizeSelection()')
        self.assertIn('selectListIdentifier(ClipboardStore.historyListIdentifier, force: false)', fallback)
        self.assertNotIn('self.pinboardID = nil', fallback)

    def test_query_delivery_and_existing_collection_lifecycle_are_unchanged(self):
        previous = (self.phase / 'before' / self.ui_path).read_text()
        for marker in ['private func installSearchQueryDelivery()', 'var visibleItems:',
                       'func consumePendingListFocus(', 'func applyFullCollectionReload(',
                       'func applyIncrementalCollectionSnapshot(', 'func selectedItemTargetLists()']:
            (assert_visible_order_only if marker == 'var visibleItems:' else lambda t, a, b: t.assertEqual(without_list_route(a), b))(self, body(self.ui, marker), body(previous, marker))
        self.assertEqual(pre_attributes_host(self, (ROOT / 'replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift').read_text()).encode(),
                         (self.phase / 'before/replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift').read_bytes())
        for text in [self.choose, self.select, self.delivery, self.consumer]:
            self.assertNotIn('applySearchInput(', text)
            self.assertNotIn('searchInputChanged()', text)

    def test_force_transition_fixture_distinguishes_nil_identifier_from_history_view(self):
        # Original-bound event trace, not execution of the Swift subscriber.
        def trace(current, target, force, resolved):
            events = ([None] if current is not None and current == target and force else []) + [target]
            return events, [e for e in events if e is not None and e in resolved]
        for current in [None, 'history', 'A', 'B']:
            for target in ['history', 'A', 'missing']:
                for force in [False, True]:
                    events, lists = trace(current, target, force, {'history', 'A', 'B'})
                    self.assertEqual(events[-1], target)
                    self.assertEqual(events.count(None), int(current is not None and current == target and force))
                    self.assertEqual(lists, [] if target == 'missing' else [target])
        events, lists = trace('A', 'A', True, {'history', 'A'})
        self.assertEqual(events, [None, 'A'])
        self.assertEqual(lists, ['A'])  # no intermediate history or empty collection

    def test_finite_contract_is_not_claimed_as_full_storage_provider_migration(self):
        self.assertEqual([r['function_id'] for r in self.proof['contracts']], ['Paste:0x100039c50'])
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertEqual(self.proof['function_map_markers_upgraded'], 0)
        limitations = '\n'.join(self.proof['retained_partial_contracts'])
        for token in ['persistent wrapper', 'FRC/provider', 'UUID', 'ABI']:
            self.assertIn(token, limitations)
