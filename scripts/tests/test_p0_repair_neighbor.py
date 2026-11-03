"""Static source checks for post-update pending neighbor selection."""
import hashlib
import json
import re
import unittest
from pathlib import Path
from collection_membership_scope_contract import pre_collection_membership


ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / ".local/p0-repair/phase-1/neighbor-result.json"
CONTROLLER = ROOT / "replica/Sources/Pasto/UI/ReplicaUIController.swift"
COLLECTION = ROOT / "replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift"
REPRESENTABLE = ROOT / "replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift"


def swift_body(source: str, signature: str) -> str:
    if source.count(signature) != 1:
        raise AssertionError(f"Expected one declaration: {signature}")
    start = source.index("{", source.index(signature) + len(signature))
    token = r'"(?:\\.|[^"\\])*"|//[^\n]*|/\*[\s\S]*?\*/'
    masked = re.sub(token, lambda match: " " * len(match.group()), source)
    depth = 0
    for index in range(start, len(masked)):
        depth += (masked[index] == "{") - (masked[index] == "}")
        if depth == 0:
            return source[start:index + 1]
    raise AssertionError(f"Unclosed Swift body: {signature}")


def original_fragment(path: Path, address: str) -> str:
    source = path.read_text()
    headers = list(re.finditer(r"^/\* Address: (0x[0-9a-f]+) \| .*? \*/$", source, re.M))
    for index, match in enumerate(headers):
        if match.group(1) == address:
            end = headers[index + 1].start() if index + 1 < len(headers) else len(source)
            return source[match.start():end].rstrip() + "\n"
    raise AssertionError(f"Original function not found: {path} {address}")


class PendingNeighborTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads(RESULT.read_text())
        cls.controller = pre_collection_membership(CONTROLLER.read_text())
        cls.collection = COLLECTION.read_text()

    def test_original_pending_id_is_set_then_consumed_by_applier_update(self):
        for row in [self.result["original"], *self.result["supporting_original_fragments"]]:
            fragment = original_fragment(ROOT / row["path"], row["function_id"].split(":", 1)[1])
            self.assertEqual(hashlib.sha256(fragment.encode()).hexdigest(), row["sha256"])
        update = original_fragment(ROOT / "decompiled/Paste/part-0035.c", "0x1000684f8")
        self.assertIn("pendingNeighborSelectionID", update)
        self.assertIn("*puVar1 = 0;\n    puVar1[1] = 0;", update)
        self.assertLess(update.index("*puVar1 = 0;"), update.index("FUN_1003b8bfc()"))
        self.assertIn("FUN_1001b9830", update)
        setter = original_fragment(ROOT / "decompiled/Paste/part-0035.c", "0x100069158")
        self.assertIn("*puVar1 = param_2", setter)
        self.assertIn("puVar1[1] = param_3", setter)
        install = original_fragment(ROOT / "decompiled/Paste/part-0035.c", "0x100067c84")
        self.assertIn("*(code **)(lVar16 + 0x18) = FUN_1000765b8", install)
        wrapper = original_fragment(ROOT / "decompiled/Paste/part-0038.c", "0x1000765b8")
        self.assertIn("FUN_1000684f8()", wrapper)

    def test_completion_queues_request_without_selecting_before_collection_update(self):
        confirm = swift_body(self.controller, "func confirmItemDeletion()")
        self.assertIn("executeItemDeletion(request)", confirm)
        self.assertIn("self.completeItemDeletion(request)", confirm)
        complete = swift_body(self.controller, "private func completeItemDeletion(")
        self.assertIn("pendingNeighborSelection = PendingNeighborSelection", complete)
        self.assertIn("if let neighborID = request.neighborID", complete)
        self.assertNotIn("selectIndex(", confirm)
        self.assertNotIn("selectIndex(", complete)
        request = swift_body(self.controller, "func deleteSelection()")
        self.assertIn("neighborID = [last + 1, first - 1].first", request)
        self.assertIn("beforeIDs: before.map(\\.id)", request)

    def test_collection_update_defers_to_main_queue_with_owner_token_and_current_ids(self):
        update = swift_body(self.collection, "func update(state: ReplicaUIState, cardSide: CGFloat)")
        schedule = swift_body(self.collection, "private func scheduleSnapshotDrain()")
        drain = swift_body(self.collection, "private func drainCollectionSnapshots()")
        self.assertIn("scheduleSnapshotDrain()", update)
        self.assertIn("DispatchQueue.main.async", schedule)
        self.assertIn("self.collectionOwnerGeneration == ownerGeneration", schedule)
        self.assertIn("self.state === state", drain)
        self.assertIn("incomingIDs == state.visibleItems.map(\\.id)", drain)
        self.assertLess(drain.index("layoutCollection()"), drain.index("state.consumePendingNeighborSelection"))
        self.assertIn("state.consumePendingNeighborSelection(token: neighbor.token, items: items)", drain)
        representable = swift_body(self.collection, "func updateNSView(_ nsView: ReplicaNativeCollectionHost, context: Context)")
        self.assertIn("nsView.update(state: state, cardSide: cardSide)", representable)

    def test_consumer_clears_before_resolving_target_and_has_no_fallback(self):
        consume = swift_body(self.controller, "func consumePendingNeighborSelection(token: UUID, items: [ClipboardItem])")
        self.assertLess(consume.index("pendingNeighborSelection = nil"), consume.index("items.firstIndex(where: { $0.id == request.id })"))
        self.assertIn("items.map(\\.id) != request.beforeIDs", consume)
        self.assertIsNone(re.search(r"items\.first\b", consume))
        self.assertNotIn("primaryItem", consume)
        self.assertIn("selectIndex(index, mode: 0, items: items)", consume)

    def test_stale_cancellation_and_explicit_selection_do_not_cancel_confirmation(self):
        cancel_pending = swift_body(self.controller, "func cancelPendingNeighborSelection(token: UUID? = nil)")
        self.assertIn("guard let request = pendingNeighborSelection", cancel_pending)
        self.assertIn("token == nil || request.token == token", cancel_pending)
        self.assertLess(cancel_pending.index("guard let request"), cancel_pending.index("pendingNeighborSelection = nil"))
        cancel = swift_body(self.controller, "func cancelItemDeletion()")
        self.assertIn("cancelPendingNeighborSelection()", cancel)
        for signature in [
            "private func selectIndex(",
            "func selectAll()",
            "func deselectAll()",
            "func selectForDoubleClick(at index: Int)",
        ]:
            self.assertIn("cancelPendingNeighborSelection()", swift_body(self.controller, signature))
        detach = swift_body(self.collection, "func detachObservers()")
        self.assertIn("state.collectionOwner === self", detach)
        self.assertIn("state.cancelPendingNeighborSelection()", detach)
        normalize = swift_body(self.controller, "func normalizeSelection()")
        self.assertNotIn("cancelPendingNeighborSelection()", normalize)
        self.assertNotIn("cancelItemDeletion()", swift_body(self.controller, "func selectAll()"))
        self.assertNotIn("cancelItemDeletion()", swift_body(self.controller, "func deselectAll()"))

    def test_report_binds_live_current_references_and_test_contract(self):
        for row in self.result["current_references"]:
            path = ROOT / row["path"]
            self.assertTrue(path.is_file())
            source = pre_collection_membership(path.read_text())
            self.assertIn(row["symbol"], source)


if __name__ == "__main__":
    unittest.main()
