"""Historical P1 review snapshot contracts; no native APIs or compilation."""
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body


class P1ReviewRound29(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p1-review/round-1'
        cls.review = json.loads((cls.phase / 'review-contract.json').read_text())

    def source(self, name):
        prefix = 'replica/Sources/Pasto/' if name.startswith('UI/') else 'replica/Sources/PastoCore/'
        return (self.phase / 'sources' / (prefix + name)).read_text()

    def test_fixed_scope_is_81_with_8_old_repairs_and_73_revalidated_records(self):
        self.assertEqual(self.review['p1_total'], 81)
        self.assertEqual(len(set(self.review['historical_repaired_function_ids'])), 8)
        self.assertEqual(len({r['function_id'] for r in self.review['records']}), 73)
        self.assertTrue(all(r['review_status'] == 'difference_revalidated' for r in self.review['records']))
        self.assertEqual(self.review['progress']['total']['repaired'], 77)

    def test_twelve_clusters_cover_every_record_once_without_claiming_full_migration(self):
        clusters = self.review['review_clusters']
        ids = [a for g in clusters.values() for a in g['function_ids']]
        self.assertEqual(len(clusters), 12)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(ids), {r['function_id'] for r in self.review['records']})
        self.assertFalse(self.review['full_function_migration_verified'])
        self.assertFalse(self.review['full_P1_function_migration_verified'])

    def test_original_hashes_and_prior_comparison_baselines_are_still_exact(self):
        for r in self.review['records']:
            old = r['original']
            self.assertEqual(source_fragments(ROOT / old['path'])[r['function_id'].split(':')[1]]['sha256'], old['sha256'])
            for ref in r['current_references']:
                if not ref['path'].startswith('replica/'):
                    continue
                before = ROOT / '.local/p0-repair/phase-1/before' / ref['path']
                self.assertEqual(hashlib.sha256(before.read_bytes()).hexdigest(), ref['prior_reference_sha256'])
                snapshot = self.phase / 'sources' / ref['path']
                self.assertEqual(hashlib.sha256(snapshot.read_bytes()).hexdigest(), ref['current_file_sha256'])

    def test_changed_sources_are_bound_to_actual_method_bodies_not_literal_presence(self):
        for group in self.review['review_clusters'].values():
            for anchor in group['anchors']:
                text = (self.phase / 'sources' / anchor['path']).read_text()
                method = body(text, anchor['symbol'])
                self.assertEqual(hashlib.sha256(method.encode()).hexdigest(), anchor['body_sha256'])
        stats = self.review['reference_check_statistics']
        self.assertEqual(stats['baseline_hash_bound'], 269)
        self.assertEqual(stats['historical_literal_needs_actual_rebinding'], 14)

    def test_filter_browser_still_uses_static_sources_and_duplicate_install_gate(self):
        text = self.source('UI/FilterBrowser.swift')
        self.assertIn('let sections: [Section]', text)
        self.assertIn('guard keyboardMonitor == nil else { return }', body(text, 'private func installKeyboardMonitor()'))
        self.assertIn('ReplicaSearchSuggestionSource.applications("", store: store)', text)

    def test_original_focus_ring_difference_is_present_in_both_actual_controls(self):
        self.assertIn('focusRingType = .none', body(self.source('OriginalSearchTextScroller.swift'), 'public init(textView:'))
        self.assertIn('focusRingType = .none', body(self.source('OriginalSearchTextView.swift'), 'public func f_100042fc8()'))

    def test_memory_candidate_source_has_no_native_fetch_or_throwing_return(self):
        text = self.source('UI/ReplicaSearchSuggestionSource.swift')
        for signature in ['static func applications(', 'static func devices(', 'static func pinboards(']:
            method = body(text, signature)
            self.assertNotIn('context.fetch', method)
            self.assertNotIn('throw', method)
        self.assertIn('($0.rawType ?? 2) == 2', text)

    def test_timer_still_weakly_captures_owner_inside_scheduled_task(self):
        method = body(self.source('OriginalSearchInputHistory.swift'), 'public func f_1002f60fc()')
        self.assertIn('Timer.scheduledTimer(withTimeInterval: interval, repeats: false) { [weak self]', method)
        self.assertIn('Task { @MainActor [weak self] in self?.f_1002f5fe8() }', method)

    def test_sdk_update_flag_and_persistent_index_state_are_still_missing(self):
        text = self.source('UI/ReplicaSearchIndex.swift')
        self.assertNotIn('.isUpdate', body(text, 'private func searchableItem('))
        self.assertIn('guard let requested else { acknowledge(); return }', body(text, 'nonisolated private func rebuild('))
        self.assertIn('index.deleteSearchableItems(withDomainIdentifiers: [domain])', body(text, 'private func drain() async'))
        self.assertNotIn('isIndexingAvailable', body(text, 'init(directoryURL: URL, store:'))

    def test_entry_still_has_eager_truncated_text_nonoptional_device_and_multiboard(self):
        text = self.source('UI/ReplicaSearchIndex.swift')
        entry = body(text, 'private struct Entry: Equatable')
        for token in ['let device: String', 'let pinboards: [String]', 'text = String(indexedText.prefix(5000))', '(item.plainText ?? "")']:
            self.assertIn(token, entry)
        self.assertIn('attributes.setValue(entry.pinboards as NSArray', text)

    def test_edit_publication_and_undo_dismissal_order_have_not_changed(self):
        text = self.source('UI/SearchEditor.swift')
        propose = body(text, 'private func propose(')
        self.assertLess(propose.index('publish(value)'), propose.index('guard value.needsNormalization'))
        restore = body(text, 'private func restore(')
        self.assertLess(restore.index('dismissSuggestions()'), restore.index('attributedString('))

    def test_menu_and_owner_creation_still_have_the_recorded_local_differences(self):
        tabs = body(self.source('UI/PanelViews.swift'), 'private var boardTabs:')
        self.assertIn('title: "删除历史…"', tabs)
        self.assertNotIn('managedObjectContext', tabs)
        owner = body(self.source('ClipboardStore.swift'), 'public func pinboardOwner(for item:')
        self.assertNotIn('rawType', owner)
        create = body(self.source('ClipboardStore.swift'), 'private func insertPinboard(')
        self.assertLess(create.index('OriginalPinboardAttributes.encoded('), create.index('state.pinboards.append(board)'))

    def test_native_search_fetch_and_token_partition_still_differ_from_original(self):
        method = body(self.source('ClipboardPersistence.swift'), 'func searchNativeItems(identifiers:')
        self.assertIn('context.reset()', method)
        self.assertIn('return try context.fetch(request).map(item)', method)
        self.assertNotIn('catch', method)
        history = body(self.source('OriginalSearchHistory.swift'), 'func observe(_ consume:')
        self.assertIn('"pasto.search.history-token." + $0', history)

    def test_collection_and_stack_consumers_still_use_their_actual_adapter(self):
        ui = self.source('UI/ReplicaUIController.swift')
        choose = body(ui, 'func chooseBoard(_ id: UUID?)')
        self.assertNotIn('pinboardID = nil', choose)
        self.assertIn('observation = store.objectWillChange.sink', ui)
        auxiliary = self.source('UI/AuxiliaryViews.swift')
        self.assertIn('OriginalStackSnippetCellView(item: item, imageProvider:', auxiliary)
        self.assertIn('application.rawIcon.flatMap(NSImage.init(data:))', auxiliary)


if __name__ == '__main__':
    unittest.main()
