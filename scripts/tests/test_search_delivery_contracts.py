"""Static search delivery/result contracts; never runs Combine, Spotlight or Swift."""
import json
import struct
import unittest

from test_offline_p0_contracts import ROOT, body


def valid_delivery(text):
    try:
        delivery = body(text, "private func installSearchQueryDelivery()")
        query, collection = delivery.split("collectionQueryObservation =", 1)
        debounce = ".debounce(for: .milliseconds(120), scheduler: RunLoop.main)"
        return (query.index(debounce) < query.index(".removeDuplicates()") < query.index(".sink")
                and ".prepend(" not in query
                and collection.index(debounce) < collection.index(".prepend([OriginalSearchQueryNode]())")
                < collection.index(".removeDuplicates()") < collection.index(".sink")
                and "self.indexedSearchQueryNodes = nodes" in query
                and "self.collectionSearchQueryNodes = nodes" in collection)
    except ValueError:
        return False


class SearchDeliveryContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ui = (ROOT / "replica/Sources/Pasto/UI/ReplicaUIController.swift").read_text()
        cls.index = (ROOT / "replica/Sources/Pasto/UI/ReplicaSearchIndex.swift").read_text()
        cls.original_index = {r["address"]: r for r in json.loads((ROOT / "reports/Paste/function-index.json").read_text())}

    @classmethod
    def original(cls, address):
        text = (ROOT / cls.original_index[address]["file"]).read_text()
        start = text.index("/* Address: " + address + " |")
        end = text.find("/* Address:", start + 1)
        return text[start:end if end != -1 else None]

    def test_both_original_delays_are_bound_to_real_runloop_millisecond_import(self):
        proof = json.loads((ROOT / "reports/replica/offline-migration-p0-round11.json").read_text())["static_bindings"]
        for row in proof["debounce_milliseconds"]:
            word, call = struct.unpack("<II", bytes.fromhex(row["bytes"]))
            self.assertEqual(word, 0x52800f00)  # mov w0, #120
            self.assertEqual(int(row["address"], 16) + 4 + ((call & 0x3ffffff) << 2), 0x100bf915c)
        binding = proof["milliseconds_stub"]["dyld_binding"]
        self.assertIn("RunLoop", binding["symbol"])
        self.assertIn("milliseconds", binding["symbol"])
        self.assertEqual(binding["mechanism"], "LC_DYLD_CHAINED_FIXUPS")

    def test_original_query_and_collection_pipelines_have_distinct_prepend_order(self):
        original_query = self.original("0x10007e194")
        original_collection = self.original("0x10007daa8")
        for text in [original_query, original_collection]:
            self.assertLess(text.index("_milliseconds(0x78"), text.index("_debounce"))
            self.assertLess(text.index("_debounce"), text.index("_removeDuplicates"))
            self.assertIn("NSRunLoop::mainRunLoop", text)
        self.assertNotIn("_prepend", original_query)
        order = ["_debounce", "FUN_1002ddf60()", "_prepend", "_removeDuplicates", "::_map()"]
        self.assertEqual([original_collection.index(t) for t in order], sorted(original_collection.index(t) for t in order))
        self.assertIn("Combine::Publishers::CombineLatest::init", original_query)

    def test_production_delivery_uses_two_retained_weak_subscriptions(self):
        self.assertTrue(valid_delivery(self.ui))
        self.assertIn("private var searchQueryObservation: AnyCancellable?", self.ui)
        self.assertIn("private var collectionQueryObservation: AnyCancellable?", self.ui)
        delivery = body(self.ui, "private func installSearchQueryDelivery()")
        self.assertEqual(delivery.count(".sink { [weak self] nodes in"), 2)
        self.assertNotIn("Task.sleep", delivery)
        self.assertNotIn(".throttle", delivery)

    def test_guard_rejects_wrong_delay_duplicate_order_or_missing_initial_route(self):
        for changed in [self.ui.replace(".milliseconds(120)", ".milliseconds(100)"),
                        self.ui.replace(".prepend([OriginalSearchQueryNode]())", ""),
                        self.ui.replace(".removeDuplicates()", "")]:
            self.assertFalse(valid_delivery(changed))

    def test_raw_input_sends_once_after_atomic_projection_and_does_not_submit_query(self):
        apply = body(self.ui, "func applySearchInput(nodes:")
        self.assertEqual(apply.count("searchInputChanged()"), 1)
        self.assertLess(apply.index("isApplyingSearchInput = false"), apply.index("searchInputChanged()"))
        self.assertNotIn("refreshSearch()", apply)
        changed = body(self.ui, "private func searchInputChanged()")
        self.assertIn("searchQueryChanges.send(searchQueryNodes)", changed)
        self.assertNotIn("searchIndex.update", changed)

    def test_store_refresh_uses_delivered_query_without_restarting_debounce(self):
        refresh = body(self.ui, "private func refreshSearch()")
        self.assertIn("searchIndex.update(items: store.items, nodes: indexedSearchQueryNodes)", refresh)
        self.assertNotIn("searchQueryChanges.send", refresh)
        state = body(self.ui, "final class ReplicaUIState: ObservableObject")
        init = body(state, "init(store: ClipboardStore)")
        self.assertLess(init.index("installSearchQueryDelivery()"), init.index("refreshSearch()"))
        observation = init[init.index("observation = store.objectWillChange.sink"):]
        self.assertIn("self?.refreshSearch()", observation)
        self.assertNotIn("searchInputChanged()", observation)

    def test_visible_and_delete_scopes_follow_delivered_collection_not_edit_buffer(self):
        visible = body(self.ui, "var visibleItems: [ClipboardItem]")
        self.assertIn("if isCollectionSearchQueryEmpty", visible)
        self.assertNotIn("if isSearchQueryEmpty", visible)
        self.assertLess(visible.index("if isCollectionSearchQueryEmpty"), visible.index("if let pinboardID"))
        delete = body(self.ui, "func deleteSelection()")
        self.assertIn("permanently: showDeleted || !isCollectionSearchQueryEmpty", delete)
        delivery = body(self.ui, "private func installSearchQueryDelivery()")
        collection = delivery[delivery.index("collectionQueryObservation ="):]
        self.assertLess(collection.index("cancelPendingDeletion()"), collection.index("self.collectionSearchQueryNodes = nodes"))

    def test_real_drag_and_drop_gates_follow_same_collection_context(self):
        for file in ["PanelViews.swift", "ReplicaNativeCardCollection.swift"]:
            source = (ROOT / "replica/Sources/Pasto/UI" / file).read_text()
            self.assertIn("state.isCollectionSearchQueryEmpty, !state.showDeleted", source)
            self.assertNotIn("state.isSearchQueryEmpty, !state.showDeleted", source)

    def test_escape_and_closed_history_routing_read_collection_context(self):
        cancel = body(self.ui, "func cancelSearchOrPanel()")
        self.assertIn("if !state.isCollectionSearchQueryEmpty", cancel)
        closed = body(self.ui, "private func beginClosedState()")
        self.assertIn("self.state.isCollectionSearchQueryEmpty, self.state.pinboardID == nil", closed)
        self.assertIn("guard let self, !self.state.isCollectionSearchQueryEmpty", closed)
        panel = (ROOT / "replica/Sources/Pasto/UI/PanelViews.swift").read_text()
        self.assertIn("searchFocused || state.searchVisible || !state.isSearchQueryEmpty", panel)

    def test_starting_query_does_not_discard_previous_identifiers(self):
        update = body(self.index, "func update(items:")
        replace = body(self.index,"private func replaceQuery(with nodes:")
        self.assertIn("replaceQuery(with: nodes)", update)
        self.assertIn("queryTask?.cancel()", replace)
        self.assertNotIn("identifiers = []", update)
        self.assertIn("error = nil", replace)
        original = self.original("0x1003600a0")
        self.assertIn("Swift::Task::cancel", original)
        self.assertNotIn("CurrentValueSubject::send", original)
        self.assertIn("CurrentValueSubject::send", self.original("0x100360808"))

    def test_cancellation_is_ignored_but_real_error_still_publishes_empty_results(self):
        replace = body(self.index,"private func replaceQuery(with nodes:")
        self.assertIn("catch is CancellationError", replace)
        failure = replace[replace.index("} catch {"):]
        self.assertIn("guard !Task.isCancelled else { return }",failure)
        self.assertIn("self.error = error",failure)
        self.assertIn("identifiers = []",failure)
        self.assertIn("onUpdate?()",failure)
        original = self.original("0x1003602fc")
        self.assertIn("_swift_dynamicCast", original)
        self.assertIn("goto LAB_1003606c8", original)
        self.assertIn("Swift::CancellationError::typeMetadataAccessor", self.original("0x1003601e0"))

    def test_default_sort_key_and_descending_flag_are_bound_to_original_bytes(self):
        proof = json.loads((ROOT / "reports/replica/offline-migration-p0-round11.json").read_text())["static_bindings"]
        words = struct.unpack("<6I", bytes.fromhex(proof["sort_key"]["bytes"]))
        x0 = sum(((word >> 5) & 0xffff) << (i * 16) for i, word in enumerate(words[:4]))
        x1 = ((words[4] >> 5) & 0xffff) + (((words[5] >> 5) & 0xffff) << 48)
        self.assertEqual((x0.to_bytes(8, "little") + x1.to_bytes(8, "little"))[:9], b"timestamp")
        self.assertEqual(struct.unpack("<I", bytes.fromhex(proof["sort_descending"]["bytes"])), (0x52800003,))
        self.assertEqual(proof["sort_selector"]["selector"], "defaultSortDescriptors")
        self.assertIn("FUN_100329754()", self.original("0x100360808"))
        self.assertIn('FUN_1000037f0("identifier IN %@"', self.original("0x100360808"))

    def test_search_order_uses_history_timestamp_and_places_missing_timestamp_after_it(self):
        visible = body(self.ui, "var visibleItems: [ClipboardItem]")
        self.assertIn("if $0.isInHistory != $1.isInHistory { return $0.isInHistory }", visible)
        self.assertIn("guard $0.isInHistory else { return false }", visible)
        self.assertIn("return $0.createdAt > $1.createdAt", visible)
        self.assertNotIn("updatedAt", visible)


if __name__ == "__main__":
    unittest.main()
