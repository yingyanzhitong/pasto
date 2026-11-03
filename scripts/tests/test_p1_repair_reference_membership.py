"""Reference-backed membership and actual consumers; no Swift/framework/runtime execution."""
from native_title_scope_contract import NEW_PATH as NATIVE_TITLE_PATH
from item_observation_scope_contract import NEW_PATH as ITEM_OBSERVATION_PATH
import hashlib
import json
from pathlib import Path
from entity_lookup_scope_contract import pre_entity_lookup
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from supplied_input_scope_contract import pre_supplied_input_adapters, pre_supplied_input_adapters_bytes
from test_p0_repair_checksum_routing import original_fragment
from collection_membership_scope_contract import ENTRY_PATH, CHANGES, pre_collection_membership


from suggestion_index_source_scope_contract import pre_suggestion_index_source

class ReferenceMembershipContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-79'
        cls.proof = json.loads((cls.phase / 'reference-membership-contract.json').read_text())
        cls.base = json.loads((cls.phase / 'baseline.json').read_text())
        cls.paths = dict(entry=ENTRY_PATH, ui='replica/Sources/Pasto/UI/ReplicaUIController.swift',
                         host='replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift')
        cls.source = {k: pre_supplied_input_adapters((ROOT / p).read_text()) for k, p in cls.paths.items()}
        cls.ui = cls.source['ui'];cls.host = cls.source['host'];cls.entry = cls.source['entry']

    def before(self, key): return (self.phase / 'before' / self.paths[key]).read_text()

    def test_original_provider_evidence_fourteen_fragments_and_binary_are_bound(self):
        r = self.proof['original_live_provider_proof']
        self.assertEqual(hashlib.sha256((ROOT / r['path']).read_bytes()).hexdigest(), r['sha256'])
        self.assertEqual(len(self.proof['original_fragments']), 14)
        for r in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / r['path'])[r['address']]['sha256'], r['sha256'])
        r = self.proof['binary']
        self.assertEqual(hashlib.sha256((ROOT / r['path']).read_bytes()).hexdigest(), r['sha256'])

    def test_original_membership_is_cached_ids_and_indexed_content_is_separate_required_lookup(self):
        refs = {r['address']: r for r in self.proof['original_fragments']}
        def f(address):
            r = refs[address];return original_fragment((ROOT / r['path']).read_text(), address[2:])
        ids = f('0x1003543a4');indexed = f('0x10035440c');lookup = f('0x1003544dc')
        self.assertIn('_swift_bridgeObjectRetain(*(undefined8 *)(lVar1 + 0x10))', ids)
        self.assertNotIn('existingObject', ids)
        self.assertIn('if ((long)param_1 < 0)', indexed)
        self.assertIn('FUN_1003544dc()', indexed)
        self.assertIn('SoftwareBreakpoint', indexed)
        self.assertIn('objc_stub::FUN_100c02080(local_58,param_1,&local_78)', lookup)
        prior = json.loads((ROOT / self.proof['original_live_provider_proof']['path']).read_text())
        self.assertIn('existingObjectWithID:error:', json.dumps(prior))

    def test_current_three_files_and_after_snapshots_are_bound(self):
        self.assertEqual(set(self.proof['current_sources']), set(self.paths.values()))
        for p, h in self.proof['current_sources'].items():
            raw = pre_supplied_input_adapters_bytes(ROOT / p)
            self.assertEqual(hashlib.sha256(raw).hexdigest(), h)
            self.assertEqual(raw, (self.phase / 'after' / p).read_bytes())

    def test_native_entry_initialization_retains_identity_and_reference_without_payload(self):
        self.assertIn('public struct ClipboardCollectionEntry: Identifiable, Equatable', self.entry)
        f = body(self.entry, 'public init(id: UUID, reference:')
        self.assertIn('self.id = id', f);self.assertIn('self.reference = reference', f)
        self.assertIn('legacyItem = nil', f)
        for token in ['requiredItem(', 'resolvedItem(', 'existingObject', 'ClipboardPersistence', 'payload', 'UUID()']:
            self.assertNotIn(token, f)
        self.assertIn('private let reference: ClipboardCollectionItemReference?', self.entry)

    def test_native_entry_content_is_required_and_does_not_fall_back_on_resolution_failure(self):
        f = body(self.entry, 'public func requiredItem()')
        self.assertLess(f.index('if let reference { return reference.requiredItem() }'), f.index('guard let legacyItem'))
        self.assertIn('fatalError("Missing collection entry")', f)
        self.assertIn('return legacyItem', f)
        self.assertNotIn('try?', f);self.assertNotIn('??', f)

    def test_restore_entry_holds_entity_without_eager_payload_read(self):
        f = body(self.entry, 'public func requiredRestoreItem()')
        self.assertIn('reference.requiredRestoreItem(id: id)', f)
        self.assertIn('ClipboardRestoreItem(item: legacyItem)', f)
        for token in ['requiredItem()', 'resolvedItem()', 'ClipboardPersistence', 'store.items']:
            self.assertNotIn(token, f)
        holder = pre_entity_lookup((ROOT / 'replica/Sources/PastoCore/ClipboardCollectionItemReference.swift').read_text())
        hold = body(holder, 'public func requiredRestoreItem(id:')
        self.assertIn('ClipboardRestoreItem(id: id, object: object)', hold)
        self.assertNotIn('ClipboardPersistence.item', hold)

    def test_member_factory_never_requires_presence_in_cached_value_dictionary(self):
        f = body(self.ui, 'private func collectionEntries(')
        self.assertIn('identifiers.filter { !deleted.contains($0) }.map { identifier in', f)
        self.assertIn('references[identifier]', f)
        self.assertIn('ClipboardCollectionEntry(id: identifier, reference: reference)', f)
        self.assertIn('fatalError("Missing collection item reference")', f)
        for token in ['items[identifier]', 'items.first', 'compactMap', 'requiredItem(', 'decode(', '.payloads', 'UUID(uuidString:']:
            self.assertNotIn(token, f)
        self.assertIn('let deleted = Set(store.items.filter(\\.isDeleted).map(\\.id))', f)
        # A source ID absent from Store has no membership-presence guard in the production factory.
        self.assertNotIn('contains(identifier)', f)

    def test_ordinary_list_uses_one_captured_snapshot_for_both_order_and_references(self):
        visible = body(self.ui, 'var visibleItems:')
        self.assertEqual(visible.count('listCollection?.value'), 1)
        self.assertIn('let snapshot = listCollection?.value', visible)
        self.assertIn('collectionEntries(identifiers: snapshot?.identifiers ?? [],', visible)
        self.assertIn('references: snapshot?.itemReferences ?? [:]', visible)
        self.assertNotIn('identifiers.compactMap { items[$0] }', visible)
        self.assertIn('return native', visible)

    def test_search_membership_uses_retained_result_ids_and_references(self):
        visible = body(self.ui, 'var visibleItems:')
        self.assertIn('return collectionEntries(identifiers: searchIndex.orderedIdentifiers,', visible)
        self.assertIn('references: searchIndex.resultItemReferences)', visible)
        search = pre_suggestion_index_source((ROOT / 'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text())
        self.assertIn('orderedIdentifiers = source?.value.identifiers ?? []', search)
        self.assertIn('resultSource?.value.itemReferences ?? [:]', search)
        self.assertEqual(hashlib.sha256(search.encode()).hexdigest(), self.base['production']['replica/Sources/Pasto/UI/ReplicaSearchIndex.swift'])

    def test_legacy_secondary_membership_retains_archive_order_without_dropping_new_native_ids(self):
        f = body(self.ui, 'var visibleItems:')
        for token in ['let archived = store.items(in: pinboardID)',
                      'let legacy = archived.filter { $0.pinboardOwnerID != pinboardID }',
                      'let merged = archived.filter { retained.contains($0.id) }.map',
                      'byID[$0.id] ?? ClipboardCollectionEntry(item: $0)',
                      'return merged + native.filter { !included.contains($0.id) }']:
            self.assertIn(token, f)
        self.assertIn('with secondary memberships', f)

    def test_legacy_trash_keeps_frozen_value_entries_and_explicit_local_filter(self):
        f = body(self.entry, 'public init(item: ClipboardItem)')
        self.assertIn('reference = nil', f);self.assertIn('legacyItem = item', f)
        visible = body(self.ui, 'var visibleItems:')
        self.assertIn('.filter(\\.isDeleted).map { ClipboardCollectionEntry(item: $0) }', visible)
        self.assertIn('guard let item = archived[identifier], item.isDeleted else { return nil }', visible)
        self.assertTrue(any('tombstones' in s for s in self.proof['adaptations']))

    def test_eight_identity_only_selection_helpers_change_only_array_type(self):
        for marker in ['func selectFirstAppliedItem(', 'func selectAppliedItem(', 'func applyFullCollectionReload(',
                       'func applyIncrementalCollectionSnapshot(', 'private func selectIndex(',
                       'private var pointerSelectionItems:', 'func consumePendingNeighborSelection(',
                       'private func appliedCollectionItems()']:
            actual = body(self.ui, marker)
            self.assertEqual(actual, body(self.before('ui'), marker))
            for token in ['requiredItem(', 'resolvedItem(', '.payloads', 'decode(', 'fetch(']:
                self.assertNotIn(token, actual)
        self.assertIn('private var pointerSelectionItems: [ClipboardCollectionEntry]', self.ui)
        self.assertIn('private func appliedCollectionItems() -> [ClipboardCollectionEntry]?', self.ui)

    def test_primary_resolves_only_requested_applied_entry_before_selected_and_first_fallback(self):
        f = body(self.ui, 'var primaryItem:')
        self.assertIn('let items = pointerSelectionItems', f)
        self.assertIn('items.first { $0.id == primaryID }?.requiredItem()', f)
        self.assertIn('?? selectedItems.first ?? items.first?.requiredItem()', f)
        self.assertNotIn('visibleItems', f)
        pointer = body(self.ui, 'private var pointerSelectionItems:')
        self.assertIn('guard let collectionOwner else { return visibleItems }', pointer)
        self.assertIn('collectionOwner.appliedItems(for: self) ?? []', pointer)

    def test_owner_and_ownerless_selected_values_use_applied_or_same_entry_reference(self):
        f = body(self.ui, 'var selectedItems:')
        self.assertIn('if let collectionOwner { return collectionOwner.appliedSelectedItems(for: self, orderedIDs: ids) ?? [] }', f)
        self.assertIn('return ids.compactMap { byID[$0]?.requiredItem() }', f)
        self.assertNotIn('collectionItemReferences', f)
        self.assertNotIn('store.items', f)
        host = body(self.host, 'func appliedSelectedItems(for state:')
        self.assertIn('self.state === state, state.collectionOwner === self', host)
        self.assertIn('return renderedItem(at: index)', host)

    def test_applier_captures_reference_entries_and_preserves_full_update_selection_timing(self):
        self.assertIn('private var items: [ClipboardCollectionEntry] = []', self.host)
        pending = body(self.host, 'private struct PendingSnapshot')
        self.assertIn('let items: [ClipboardCollectionEntry]', pending)
        for marker in ['func update(state: ReplicaUIState, cardSide: CGFloat)', 'private func drainCollectionSnapshots()',
                       'private func restorePendingListFocus(state:', 'private func scheduleSnapshotDrain()']:
            self.assertEqual(body(self.host, marker), body(self.before('host'), marker))
        f = body(self.host, 'func appliedItems(for state:')
        self.assertIn('return items', f)
        self.assertNotIn('requiredItem', f)

    def test_render_drag_and_selected_consumers_read_only_requested_entry_values(self):
        self.assertEqual(body(self.host, 'private func renderedItem(at index:').strip(), '{\n        items[index].requiredItem()\n    }')
        for marker in ['private func tileCells()', 'private func refreshCellRoots()', 'private func beginNativeDrag(']:
            self.assertEqual(body(self.host, marker), body(self.before('host'), marker))
        self.assertIn('let selected = indexes.map { renderedItem(at: $0) }', body(self.host, 'private func beginNativeDrag('))
        self.assertIn('let item = renderedItem(at: index)', body(self.host, 'private func tileCells()'))

    def test_item_id_paste_route_preserves_previous_hold_and_compatibility_contract(self):
        thin = body(self.ui, 'func paste(item:')
        self.assertEqual(thin.strip(), '{\n        paste(itemID: item.id, plainTextOnly: plainTextOnly)\n    }')
        direct = body(self.ui, 'func paste(itemID:')
        self.assertEqual(direct.replace('itemID', 'item.id'), body(self.before('ui'), 'func paste(item:'))
        f = body(self.host, 'func appliedRestoreItems(for state:')
        self.assertIn('return items[index].requiredRestoreItem()', f)
        self.assertNotIn('ClipboardRestoreItem(item:', f)
        self.assertNotIn('renderedItem(', f)

    def test_double_and_numeric_actions_pass_applied_identity_without_eager_all_item_reads(self):
        mouse = body(self.host, 'override func mouseDown(with event:')
        self.assertIn('paste(itemID: current[index].id, plainTextOnly:', mouse)
        handle = body(self.ui, 'private func handleKey(')
        quick = body(handle, 'func performQuickPaste(')
        self.assertIn('paste(itemID: items[action.index].id, plainTextOnly:', quick)
        self.assertEqual(quick.count('appliedCollectionItems()'), 2)
        self.assertIn('state.selectFirstAppliedItem(items: appliedItems)', quick)
        for f in [quick, mouse]: self.assertNotIn('.map { $0.requiredItem()', f)
        self.assertEqual(pre_collection_membership(handle), body(self.before('ui'), 'private func handleKey('))

    def test_only_reviewed_membership_deltas_and_one_entry_type_change_production(self):
        self.assertEqual(len(CHANGES), 23)
        for key in ['ui', 'host']:
            self.assertEqual(pre_collection_membership(self.source[key]), self.before(key))
        sha = lambda p: hashlib.sha256(pre_supplied_input_adapters_bytes(ROOT / p)).hexdigest()
        self.assertEqual({p for p, h in self.base['production'].items() if sha(p) != h}, {self.paths['ui'], self.paths['host']})
        files = {str(p.relative_to(ROOT)) for p in (ROOT / 'replica/Sources').rglob('*') if p.is_file()}
        self.assertEqual(files - {NATIVE_TITLE_PATH, ITEM_OBSERVATION_PATH} - set(self.base['production']), {ENTRY_PATH})
        for p in ['replica/Package.swift', 'package.json']:
            self.assertEqual(sha(p), self.base['other'][p])
        # No save/restore/model implementation is altered by changing collection metadata representation.
        for p in ['replica/Sources/PastoCore/Pasteboard.swift', 'replica/Sources/PastoCore/ClipboardPersistence.swift',
                  'replica/Sources/Pasto/AppMain.swift']:
            self.assertEqual(sha(p), self.base['production'][p])

    def test_finite_full_provider_and_unknown_contracts_are_not_silently_closed(self):
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertEqual(self.proof['repaired_finite_contracts'], [])
        self.assertEqual(self.proof['remaining_confirmed_differences'], ['Paste:0x1003544dc'])
        self.assertTrue(any('persistence' in r for r in self.proof['remaining_work']))
        self.assertTrue(any('Unknown04430c/0f733c' in r for r in self.proof['remaining_work']))


if __name__ == '__main__': unittest.main()
