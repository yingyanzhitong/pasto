"""Actual visible-card live references; source/static checks only, actions remain open."""
from native_title_scope_contract import NEW_PATH as NATIVE_TITLE_PATH
from item_observation_scope_contract import NEW_PATH as ITEM_OBSERVATION_PATH
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from collection_membership_scope_contract import ENTRY_PATH, pre_collection_membership_bytes
from modal_restore_scope_contract import RESTORE_ITEM_PATH, pre_modal_restore, pre_modal_restore_bytes
from live_item_render_scope_contract import pre_live_render, REFERENCE_PATH
from live_item_selection_scope_contract import pre_live_selection, pre_live_selection_bytes


class LiveItemRenderContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-74'
        cls.proof = json.loads((cls.phase / 'live-item-render-contract.json').read_text())
        cls.base = json.loads((cls.phase / 'baseline.json').read_text())
        cls.paths = dict(reference=REFERENCE_PATH, source='replica/Sources/PastoCore/ClipboardSearchCollection.swift',
            index='replica/Sources/Pasto/UI/ReplicaSearchIndex.swift',
            ui='replica/Sources/Pasto/UI/ReplicaUIController.swift',
            host='replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift')
        cls.source = {k: pre_live_selection((ROOT / p).read_text()) for k, p in cls.paths.items()}

    def before(self, key): return (self.phase / 'before' / self.paths[key]).read_text()

    def test_original_live_getter_evidence_and_five_actual_sources_are_bound(self):
        old = self.proof['original_proof']
        self.assertEqual(hashlib.sha256((ROOT / old['path']).read_bytes()).hexdigest(), old['sha256'])
        self.assertEqual(hashlib.sha256((ROOT / self.proof['binary']['path']).read_bytes()).hexdigest(), self.proof['binary']['sha256'])
        for row in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / row['path'])[row['address']]['sha256'], row['sha256'])
        for p, digest in self.proof['current_sources'].items():
            self.assertEqual(hashlib.sha256(pre_live_selection_bytes(ROOT / p)).hexdigest(), digest)
            self.assertEqual(pre_live_selection_bytes(ROOT / p), (self.phase / 'after' / p).read_bytes())

    def test_reference_stores_actual_context_and_object_ID_without_payload_cache(self):
        ref = self.source['reference']
        self.assertIn('private let context: NSManagedObjectContext', ref)
        self.assertIn('private let objectID: NSManagedObjectID', ref)
        init = body(ref, 'init(context:')
        self.assertIn('self.context = context', init);self.assertIn('self.objectID = objectID', init)
        for token in ['existingObject', 'ClipboardPersistence.item', 'context.fetch', 'Store', 'UUID']:
            self.assertNotIn(token, init)
        self.assertNotIn('private var', ref)
        self.assertIn('lhs.context === rhs.context && lhs.objectID == rhs.objectID', ref)

    def test_optional_live_read_checks_class_and_reuses_existing_projection(self):
        ref = self.source['reference'];lookup = body(ref, 'public func item()')
        self.assertIn('@MainActor public func item()', ref)
        self.assertIn('(try? context.existingObject(with: objectID)) as? PastoItemEntity else { return nil }', lookup)
        self.assertIn('return try? ClipboardPersistence.item(object)', lookup)
        for token in ['fatalError', 'refresh(', 'reset(', 'save(', 'store.items', 'object(with:', 'context.fetch']:
            self.assertNotIn(token, lookup)

    def test_required_and_indexed_access_keep_nil_and_array_bounds_failures_distinct(self):
        required = body(self.source['reference'], 'public func requiredItem()')
        self.assertIn('guard let item = item() else { fatalError(', required)
        self.assertIn('return item', required)
        lookup = body(self.source['source'], 'public func item(at index:')
        order = ['let identifier = identifiers[index]', 'itemReferences[identifier]', 'fatalError(', 'reference.requiredItem()']
        self.assertEqual([lookup.index(t) for t in order], sorted(lookup.index(t) for t in order))
        self.assertNotIn('compactMap', lookup)

    def test_flush_builds_handles_from_same_published_IDs_without_decoding_content(self):
        flush = body(self.source['source'], 'private func flushPending()')
        self.assertLess(flush.index('pending = nil'), flush.index('var references:'))
        self.assertIn('for objectID in value.ids', flush)
        self.assertIn('guard let identifier = keys[objectID] else { continue }', flush)
        self.assertIn('references[identifier] = ClipboardCollectionItemReference(context: context, objectID: objectID)', flush)
        self.assertLess(flush.index('references[identifier] ='), flush.index('subject.send('))
        self.assertIn('itemReferences: references', flush)
        for token in ['ClipboardPersistence.item', 'requiredItem()', '.payloads', 'JSONDecoder']:
            self.assertNotIn(token, flush)

    def test_ordinary_search_and_trash_routes_supply_only_corresponding_reference_maps(self):
        self.assertIn('var resultItemReferences: [UUID: ClipboardCollectionItemReference] { resultSource?.value.itemReferences ?? [:] }', self.source['index'])
        getter = body(self.source['ui'], 'var collectionItemReferences:')
        self.assertIn('guard !showDeleted else { return [:] }', getter)
        self.assertIn('isCollectionSearchQueryEmpty ? (listCollection?.value.itemReferences ?? [:]) : searchIndex.resultItemReferences', getter)
        for token in ['store.items', '.item()', 'requiredItem()', '.map']:
            self.assertNotIn(token, getter)

    def test_pending_snapshot_captures_reference_epoch_even_for_equal_cached_values(self):
        update = body(self.source['host'], 'func update(state: ReplicaUIState, cardSide: CGFloat)')
        self.assertIn('let incomingItemReferences = state.collectionItemReferences', update)
        self.assertIn('|| pendingSnapshot?.itemReferences != incomingItemReferences', update)
        self.assertIn('itemReferences: incomingItemReferences', update)
        self.assertLess(update.index('let incomingItemReferences'), update.index('pendingSnapshot = PendingSnapshot('))
        pending = body(self.source['host'], 'private struct PendingSnapshot')
        self.assertIn('let itemReferences: [UUID: ClipboardCollectionItemReference]', pending)
        for token in ['requiredItem()', '.item()', 'ClipboardPersistence.item']:
            self.assertNotIn(token, update)

    def test_applier_installs_captured_handles_before_layout_without_current_source_lookup(self):
        drain = body(self.source['host'], 'private func drainCollectionSnapshots()')
        order = ['pendingSnapshot = nil', 'items = pending.items', 'itemReferences = pending.itemReferences', 'layoutCollection()']
        self.assertEqual([drain.index(t) for t in order], sorted(drain.index(t) for t in order))
        self.assertNotIn('state.collectionItemReferences', drain)
        self.assertNotIn('requiredItem()', drain)

    def test_visible_render_and_focus_refresh_use_required_live_item_when_handle_exists(self):
        host = self.source['host'];render = body(host, 'private func renderedItem(at index:')
        self.assertIn('let item = items[index]', render)
        self.assertIn('return itemReferences[item.id]?.requiredItem() ?? item', render)
        tile = body(host, 'private func tileCells()')
        self.assertLess(tile.index('for index in desired.sorted()'), tile.index('let item = renderedItem(at: index)'))
        self.assertIn('cell.update(state: state, item: item,', tile)
        refresh = body(host, 'private func refreshCellRoots()')
        self.assertIn('cell.update(state: state, item: renderedItem(at: index),', refresh)
        # A present handle's required lookup traps; the old DTO is only the absent-handle adapter.
        self.assertNotIn('try?', render)
        self.assertNotIn('?.item()', render)

    def test_owner_replacement_model_replacement_and_detach_clear_applied_handles(self):
        host = self.source['host']
        update = body(host, 'func update(state: ReplicaUIState, cardSide: CGFloat)')
        prelude = update[:update.index('        self.state = state')]
        self.assertIn('itemReferences = [:]', body(prelude, 'if replacesState'))
        for signature in ['func replaceCollectionModel(', 'func detachObservers()']:
            method = body(host, signature)
            self.assertIn('itemReferences = [:]', method)
            self.assertLess(method.index('pendingSnapshot = nil'), method.index('itemReferences = [:]'))

    def test_all_previous_methods_are_identical_outside_explicit_reference_render_blocks(self):
        for key in ['source', 'index', 'ui', 'host']:
            self.assertEqual(pre_live_render(self.source[key]), self.before(key))
        for marker in ['private func receive(', 'private func objectsDidChange(', 'nonisolated func controller(']:
            self.assertEqual(body(self.source['source'], marker), body(self.before('source'), marker))

    def test_metadata_selection_and_action_migration_remains_open_not_silently_completed(self):
        ui = self.source['ui'];host = self.source['host']
        self.assertEqual(body(ui, 'var visibleItems:'), body(self.before('ui'), 'var visibleItems:'))
        self.assertEqual(body(ui, 'var selectedItems:'), body(self.before('ui'), 'var selectedItems:'))
        self.assertEqual(body(host, 'func appliedItems('), body(self.before('host'), 'func appliedItems('))
        self.assertEqual(self.proof['remaining_confirmed_differences'], ['Paste:0x1003544dc'])
        self.assertEqual(self.proof['repaired_finite_contracts'], [])
        self.assertFalse(self.proof['full_function_migration_verified'])

    def test_only_four_existing_production_files_and_one_reference_adapter_change(self):
        sha = lambda p: hashlib.sha256(pre_live_selection_bytes(ROOT / p)).hexdigest()
        changed = {p for p, digest in self.base['production'].items() if sha(p) != digest}
        self.assertEqual(changed, {self.paths[k] for k in ['source', 'index', 'ui', 'host']})
        current = {str(p.relative_to(ROOT)) for p in (ROOT / 'replica/Sources').rglob('*') if p.is_file()}
        self.assertEqual(current - {NATIVE_TITLE_PATH, ITEM_OBSERVATION_PATH} - set(self.base['production']), {REFERENCE_PATH, RESTORE_ITEM_PATH, ENTRY_PATH})
        for p in ['replica/Package.swift', 'package.json']:
            self.assertEqual(sha(p), self.base['other'][p])


if __name__ == '__main__':
    unittest.main()
