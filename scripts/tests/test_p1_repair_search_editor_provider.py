"""Current source contracts plus frozen patch/Mach-O evidence, no native execution."""
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
from supplied_input_scope_contract import pre_supplied_input_adapters
from test_p0_repair_checksum_routing import original_fragment


class SearchEditorProviderContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-40'
        cls.proof = json.loads((cls.phase / 'editor-provider-contract.json').read_text())
        cls.editor = (ROOT / 'replica/Sources/Pasto/UI/SearchEditor.swift').read_text()
        cls.propose = body(cls.editor, 'private func propose(')
        cls.restore = body(cls.editor, 'private func restore(')
        cls.lists = (ROOT / 'replica/Sources/PastoCore/ClipboardListPersistence.swift').read_text()
        cls.fetch = body(cls.lists, 'func searchPinboardNames(matching query:')

    def snapshot(self, kind, path):
        return (self.phase / kind / path).read_text()

    def test_original_proposal_has_guarded_history_and_normalized_callback_order(self):
        text = original_fragment((ROOT / 'decompiled/Paste/part-0245.c').read_text(), '1002f7370')
        self.assertIn('if ((*(byte *)(unaff_x20 + 0x70) & 1) == 0)', text)
        order = ['*(ulong *)(unaff_x20 + 0x10) = uVar8', 'FUN_1002f5e18()',
                 'unaff_x20 + 0x48', 'unaff_x20 + 0x28', 'unaff_x20 + 0x18))(uVar8)',
                 'unaff_x20 + 0x38', 'return 0']
        self.assertEqual([text.index(t) for t in order], sorted(text.index(t) for t in order))

    def test_original_undo_sets_restoring_flag_before_callbacks_and_clears_after(self):
        text = original_fragment((ROOT / 'decompiled/Paste/part-0245.c').read_text(), '1002f7c14')
        order = ['*(undefined1 *)(unaff_x20 + 0x70) = 1', '*(undefined8 *)(unaff_x20 + 0x10) = param_1',
                 'unaff_x20 + 0x48', 'unaff_x20 + 0x28', 'unaff_x20 + 0x18', 'unaff_x20 + 0x38',
                 '*(undefined1 *)(unaff_x20 + 0x70) = 0']
        self.assertEqual([text.index(t) for t in order], sorted(text.index(t) for t in order))

    def test_actual_normalization_publishes_after_display_then_clears_suggestions(self):
        ordinary = body(self.propose, 'guard value.needsNormalization else')
        normalized = self.propose.replace(ordinary, '{}', 1)
        order = ['let previousNodes = currentNodes', 'currentNodes = value.nodes', 'history.f_1002f5e18(',
                 'attributedString(value.nodes', 'display(rendered,', 'publish(value)', 'dismissSuggestions()', 'return false']
        self.assertEqual([normalized.index(t) for t in order], sorted(normalized.index(t) for t in order))

    def test_unchanged_and_marked_text_early_paths_have_no_publication(self):
        first = self.propose.index('let previousNodes = currentNodes')
        prefix = self.propose[:first]
        self.assertIn('guard !editor.hasMarkedText() else { return true }', prefix)
        self.assertIn('guard value.nodes != currentNodes else { return true }', prefix)
        self.assertNotIn('publish(', prefix)
        self.assertNotIn('history.f_', prefix)

    def test_non_normalized_edit_publishes_without_builder_or_suggestion_clear(self):
        branch = body(self.propose, 'guard value.needsNormalization else')
        self.assertIn('publish(value)', branch)
        self.assertIn('return true', branch)
        self.assertNotIn('attributedString', branch)
        self.assertNotIn('dismissSuggestions', branch)

    def test_restore_flag_only_suppresses_history_and_comparison_uses_prior_nodes(self):
        guard = body(self.propose, 'if !restoringHistory')
        self.assertEqual(self.propose.count('history.f_1002f5e18('), 1)
        self.assertIn('history.f_1002f5e18(', guard)
        self.assertIn('filterCount(value.nodes) != filterCount(previousNodes)', guard)
        self.assertNotIn('return', guard)

    def test_actual_undo_state_precedes_builder_and_clear_happens_after_publish(self):
        order = ['guard let snapshot else { return false }', 'restoringHistory = true', 'defer { restoringHistory = false }',
                 'currentNodes = snapshot.nodes', 'attributedString(snapshot.nodes',
                 'display(rendered, selection: snapshot.selection', 'parent.onInputChange(', 'dismissSuggestions()', 'return true']
        self.assertEqual([self.restore.index(t) for t in order], sorted(self.restore.index(t) for t in order))
        self.assertNotIn('history.f_1002f5e18', self.restore)

    def test_actual_delegate_and_undo_redo_dispatch_keep_range_and_handled_result(self):
        attach = body(self.editor, 'func attach(_ field: SearchField,')
        self.assertIn('return self.propose(proposed, selection: selection, field: field, editor: editor)', attach)
        self.assertIn('return self.restore(self.history.f_1002f61f0(), field: field, editor: editor)', attach)
        self.assertIn('return self.restore(self.history.f_1002f63b8(), field: field, editor: editor)', attach)
        delegate = (ROOT / 'replica/Sources/PastoCore/OriginalSearchEditing.swift').read_text()
        self.assertIn('return onTextShouldChange?(proposed, selection) ?? true', delegate)

    def test_patch_only_changes_two_editor_methods_one_flag_and_throwing_provider(self):
        path = 'replica/Sources/Pasto/UI/SearchEditor.swift'
        previous = self.snapshot('before', path)
        after = self.snapshot('after', path)
        for signature in ['private func propose(', 'private func restore(']:
            after = after.replace(body(after, signature), body(previous, signature), 1)
        after = after.replace('        private var restoringHistory = false\n', '', 1)
        after = after.replace('pinboard: { try ReplicaSearchSuggestionSource.pinboards(', 'pinboard: { ReplicaSearchSuggestionSource.pinboards(', 1)
        self.assertEqual(after, previous)

    def test_original_fetch_dictionary_sort_and_projection_selectors_are_real(self):
        selectors = self.proof['native_selector_bindings']
        self.assertEqual([x['selector'] for x in selectors], ['setResultType:', 'setPropertiesToFetch:', 'setSortDescriptors:'])
        raw = (ROOT / self.proof['binary']['path']).read_bytes()
        for binding in selectors:
            self.assertTrue(binding['chain']['declared_chain_reachable'])
            self.assertEqual(binding['chain']['pointer_format'], 6)
            start = int(binding['stub_address'], 16) - 0x100000000
            self.assertEqual(raw[start:start + 20].hex(), binding['stub_bytes'])
        header = self.proof['sdk_fetch_request']
        data = Path(header['path']).read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), header['sha256'])
        self.assertRegex(data, rb'NSDictionaryResultType\s+API_AVAILABLE\([^\n]+\)\s*= 0x02')

    def test_native_query_uses_dictionary_identifier_name_and_native_name_sort(self):
        order = ['NSFetchRequest<NSDictionary>(entityName: "ListEntity")', 'request.resultType = .dictionaryResultType',
                 'request.propertiesToFetch = ["identifier", "name"]', 'request.sortDescriptors = [NSSortDescriptor(key: "name", ascending: true)]',
                 'return try context.fetch(request).compactMap']
        self.assertEqual([self.fetch.index(t) for t in order], sorted(self.fetch.index(t) for t in order))
        for token in ['returnsDistinctResults', 'fetchLimit', 'Set(', '.sorted', 'state.pinboards', 'store.pinboards']:
            self.assertNotIn(token, self.fetch)

    def test_empty_query_fetches_all_rawtype_two_and_nonempty_uses_original_regex(self):
        branch = body(self.fetch, 'if query.isEmpty')
        self.assertIn('NSPredicate(format: "rawType == %d", 2)', branch)
        self.assertNotIn('MATCHES', branch)
        self.assertIn('NSPredicate(format: "rawType == %d AND name MATCHES[cd] %@", 2,', self.fetch)
        self.assertIn('OriginalSearchSuggestions.f_1002f5100(query)', self.fetch)
        self.assertNotIn('items.@count', self.fetch, 'The original group source includes empty groups')

    def test_row_projection_skips_missing_or_nonstring_fields_without_deduplicating_names(self):
        mapping = body(self.fetch, 'return try context.fetch(request).compactMap')
        self.assertIn('row["identifier"] as? String', mapping)
        self.assertIn('row["name"] as? String', mapping)
        self.assertIn('else { return nil }', mapping)
        self.assertIn('return (identifier: identifier, name: name)', mapping)
        for token in ['isEmpty', 'UUID(', 'Set(', 'uniqueKeysWithValues']:
            self.assertNotIn(token, mapping)

    def test_native_query_error_propagates_through_actual_context_and_store_facades(self):
        persistence = (ROOT / 'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text()
        store = (ROOT / 'replica/Sources/PastoCore/ClipboardStore.swift').read_text()
        provider = (ROOT / 'replica/Sources/Pasto/UI/ReplicaSearchSuggestionSource.swift').read_text()
        methods = [self.fetch, body(persistence, 'func searchPinboardNames(matching query:'),
                   body(store, 'public func searchPinboardNames(matching query:'), body(provider, 'static func pinboards(')]
        self.assertIn('try context.performAndWait { try lists.searchPinboardNames(matching: query) }', methods[1])
        self.assertIn('try persistence.searchPinboardNames(matching: query)', methods[2])
        self.assertIn('try store.searchPinboardNames(matching: query)', methods[3])
        for method in methods:
            for token in ['try?', 'catch', 'rollback', 'reset()', 'reload()', 'save()']:
                self.assertNotIn(token, method)

    def test_suggestion_consumer_propagates_to_per_source_catch_and_browser_owns_ui_fallback(self):
        self.assertIn('parent.onLoadSuggestions(context)', self.editor)
        index = (ROOT / 'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text()
        self.assertIn('pinboard: { try self.suggestionDataSource?.pinboard($0) ?? [] }', body(index, 'func suggestions(contextNode:'))
        suggestions = (ROOT / 'replica/Sources/PastoCore/OriginalSearchSuggestions.swift').read_text()
        candidates = body(suggestions, 'public static func f_1002df190(')
        self.assertIn('(5, { try provider.pinboard($0).map { $0.identifier } })', candidates)
        self.assertIn('let candidates = try source(query)', candidates)
        self.assertIn('} catch {\n                continue', candidates)
        browser = (ROOT / 'replica/Sources/Pasto/UI/FilterBrowser.swift').read_text()
        self.assertIn('filters: state.availableSearchFilters()', body(browser, 'func showFilterBrowser('))
        load = body(suggestions, 'public static func f_1002e00a0(')
        self.assertIn('try? (provider()?.pinboard("") ?? [])', load)

    def test_existing_native_graph_is_reused_and_model_is_not_changed(self):
        signature = 'static func addEntities(to model:'
        path = 'replica/Sources/PastoCore/ClipboardListPersistence.swift'
        self.assertEqual(body(self.snapshot('after', path), signature), body(self.snapshot('before', path), signature))
        self.assertIn('let list = entity("ListEntity")', self.lists)
        self.assertIn('attribute("identifier", .stringAttributeType)', self.lists)
        self.assertIn('attribute("name", .stringAttributeType)', self.lists)
        self.assertIn('attribute("rawType", .integer64AttributeType', self.lists)

    def test_new_wrappers_do_not_modify_restore_transactions_or_other_candidate_sources(self):
        store = (ROOT / 'replica/Sources/PastoCore/ClipboardStore.swift').read_text()
        old_store = self.snapshot('before', 'replica/Sources/PastoCore/ClipboardStore.swift')
        for signature in ['private func mutateInTransaction<T>(', 'func recordRestoredSelection(', 'func prepareHistoryRestore(']:
            self.assertEqual(body(pre_supplied_input_adapters(store), signature), body(old_store, signature))
        provider = (ROOT / 'replica/Sources/Pasto/UI/ReplicaSearchSuggestionSource.swift').read_text()
        previous = self.snapshot('before', 'replica/Sources/Pasto/UI/ReplicaSearchSuggestionSource.swift')
        for signature in ['static func applications(', 'static func devices(']:
            checkpoint = self.snapshot('before', 'replica/Sources/Pasto/UI/ReplicaSearchSuggestionSource.swift')
            latest = (ROOT / '.local/p0-repair/phase-41/before/replica/Sources/Pasto/UI/ReplicaSearchSuggestionSource.swift').read_text()
            self.assertEqual(body(latest, signature), body(checkpoint, signature))
        signature = 'static func applicationNames(for items:'
        self.assertEqual(body(provider, signature), body(previous, signature))

    def test_original_and_patch_evidence_are_bound_without_claiming_native_execution(self):
        for row in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / row['path'])[row['address']]['sha256'], row['sha256'])
        for path, digest in self.proof['current_sources'].items():
            self.assertEqual(hashlib.sha256((self.phase / 'after' / path).read_bytes()).hexdigest(), digest)
        self.assertEqual(len(self.proof['contracts']), 5)
        self.assertFalse(self.proof['full_function_migration_verified'])


if __name__ == '__main__':
    unittest.main()
