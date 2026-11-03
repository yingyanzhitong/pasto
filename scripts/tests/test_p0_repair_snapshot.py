"""Static checks for collection snapshot reload and selection state migration."""
import hashlib
import json
import re
import unittest
from pathlib import Path
from collection_membership_scope_contract import pre_collection_membership


ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / ".local/p0-repair/phase-2/snapshot-result.json"


def original_fragment(path: Path, address: str) -> str:
    source = path.read_text()
    headers = list(re.finditer(r"^/\* Address: (0x[0-9a-f]+) \| .*? \*/$", source, re.M))
    for index, match in enumerate(headers):
        if match.group(1) == address:
            end = headers[index + 1].start() if index + 1 < len(headers) else len(source)
            return source[match.start():end].rstrip() + "\n"
    raise AssertionError(f"Original function not found: {path} {address}")


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


class CollectionSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads(RESULT.read_text())
        cls.controller_path = ROOT / "replica/Sources/Pasto/UI/ReplicaUIController.swift"
        cls.host_path = ROOT / "replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift"
        cls.algorithm_path = ROOT / "replica/Sources/PastoCore/OriginalCollectionSnapshot.swift"
        cls.controller = pre_collection_membership(cls.controller_path.read_text())
        cls.host = cls.host_path.read_text()
        cls.algorithm = cls.algorithm_path.read_text()

    def test_original_first_snapshot_diff_threshold_and_reload_selection_evidence(self):
        for row in self.result["original_fragments"]:
            fragment = original_fragment(ROOT / row["path"], row["function_id"].split(":", 1)[1])
            self.assertEqual(hashlib.sha256(fragment.encode()).hexdigest(), row["sha256"])
        applier = original_fragment(ROOT / "decompiled/Paste/part-0147.c", "0x1001b9b78")
        self.assertIn("FUN_1001b5a8c()", applier)
        self.assertIn("if (unaff_x20[6] < lVar5 + lVar2)", applier)
        self.assertIn("uVar3 = 0;\n      param_1 = 0;\n      param_2 = 0;\n      uVar6 = 0;", applier)
        self.assertIn("(*pcVar4)(0,0,0,0", applier)
        threshold = original_fragment(ROOT / "decompiled/Paste/part-0146.c", "0x1001b8ddc")
        self.assertIn("unaff_x20[6] = 300", threshold)
        diff_builder = original_fragment(ROOT / "decompiled/Paste/part-0145.c", "0x1001b5a8c")
        self.assertIn("BidirectionalCollection::_difference", diff_builder)
        self.assertIn("CollectionDifference::_inferringMoves", diff_builder)
        self.assertIn("CollectionDifference::_get_removals", diff_builder)
        self.assertIn("CollectionDifference::_get_insertions", diff_builder)
        self.assertIn('"offset element associatedWith "', diff_builder)
        self.assertIn("FUN_1001b0218", diff_builder)
        self.assertIn("FUN_1001b02ec", diff_builder)
        single_index_set = original_fragment(ROOT / "decompiled/Paste/part-0144.c", "0x1001b0218")
        move_pair_set = original_fragment(ROOT / "decompiled/Paste/part-0144.c", "0x1001b02ec")
        self.assertIn("FUN_1001b044c(param_2", single_index_set)
        self.assertIn("FUN_1001b0554(param_2,param_3", move_pair_set)
        bridge = original_fragment(ROOT / "decompiled/Paste/part-0187.c", "0x100223430")
        self.assertIn("if (param_1 == 0)", bridge)
        self.assertIn("FUN_10022be98()", bridge)
        self.assertIn("FUN_1002234e0", bridge)
        reload_body = original_fragment(ROOT / "decompiled/Paste/part-0189.c", "0x10022be98")
        self.assertIn("PTR___swiftEmptyDictionarySingleton", reload_body)
        self.assertIn("_TtC7PasteUI14CollectionView::dataSource", reload_body)
        self.assertIn("___lazy_storage___cellSelectionManager", reload_body)
        self.assertIn("objc_stub::setBounds_(IVar12,0,0)", reload_body)
        incremental = original_fragment(ROOT / "decompiled/Paste/part-0187.c", "0x1002234e0")
        self.assertIn("FUN_1002258ac()", incremental)
        self.assertIn("FUN_100223f2c()", incremental)
        self.assertIn("___lazy_storage___cellSelectionManager", incremental)
        selection_snapshot = original_fragment(ROOT / "decompiled/Paste/part-0187.c", "0x1002258ac")
        self.assertIn("FUN_1001b2a0c", selection_snapshot)
        selection_transform = original_fragment(ROOT / "decompiled/Paste/part-0145.c", "0x1001b2a0c")
        for callee in ["FUN_1001b2a90", "FUN_1001b2cc0", "FUN_1001b2fe4", "FUN_1001b3404"]:
            self.assertIn(callee, selection_transform)
        selection_setter = original_fragment(ROOT / "decompiled/Paste/part-0188.c", "0x100228ee8")
        self.assertIn("___lazy_storage___cellSelectionManager", selection_setter)

    def test_algorithm_uses_identity_difference_and_strict_300_cutover(self):
        self.assertIn("fullReloadThreshold = 300", self.algorithm)
        self.assertIn("currentIDs.difference(from: previousIDs).inferringMoves()", self.algorithm)
        self.assertIn("case let .remove(_, _, associatedWith)", self.algorithm)
        self.assertIn("case let .insert(_, _, associatedWith)", self.algorithm)
        self.assertIn("return removals + insertions + moves", self.algorithm)
        self.assertIn("structuralChangeCount(from: previousIDs, to: currentIDs) > fullReloadThreshold", self.algorithm)
        self.assertIn("guard previousIDs != currentIDs else { return 0 }", self.algorithm)

    def test_host_distinguishes_first_equal_incremental_and_full_snapshot_paths(self):
        update = swift_body(self.host, "func update(state: ReplicaUIState, cardSide: CGFloat)")
        drain = swift_body(self.host, "private func drainCollectionSnapshots()")
        self.assertNotIn("items = incomingItems", update)
        self.assertIn("scheduleSnapshotDrain()", update)
        self.assertIn("let isInitialSnapshot = !hasReceivedCollectionSnapshot", drain)
        self.assertIn("let selectionRelevantSnapshotChanged = previousIDs != incomingIDs", drain)
        self.assertIn("isInitialSnapshot || (selectionRelevantSnapshotChanged", drain)
        self.assertIn("OriginalCollectionSnapshot.requiresFullReload", drain)
        self.assertLess(drain.index("items = pending.items"), drain.index("layoutCollection()"))
        self.assertLess(drain.index("layoutCollection()"), drain.index("state.applyFullCollectionReload"))
        self.assertIn("scrollView.contentView.bounds.origin = .zero", drain)
        self.assertLess(drain.index("state.applyFullCollectionReload"), drain.index("state.consumePendingNeighborSelection"))

    def test_new_view_model_and_explicit_model_install_restart_the_first_snapshot(self):
        main_view_setter = original_fragment(ROOT / "decompiled/Paste/part-0020.c", "0x100036ee0")
        self.assertIn("FUN_100036234()", main_view_setter)
        self.assertIn("ItemCollectionView::viewModel) = uVar7", main_view_setter)
        self.assertIn("FUN_100067c84()", main_view_setter)
        lazy_collection = original_fragment(ROOT / "decompiled/Paste/part-0020.c", "0x100036234")
        self.assertIn("___lazy_storage___collectionView", lazy_collection)
        self.assertIn("FUN_1000671a8()", lazy_collection)
        constructor = original_fragment(ROOT / "decompiled/Paste/part-0035.c", "0x1000671a8")
        self.assertIn("ItemCollectionView::applier) = 0", constructor)
        self.assertIn("ItemCollectionView::viewModel) = param_1", constructor)
        self.assertIn("FUN_100067c84(0)", constructor)
        update = swift_body(self.host, "func update(state: ReplicaUIState, cardSide: CGFloat)")
        owner_reset = update.index("if replacesState")
        assign_new_owner = update.index("self.state = state")
        self.assertLess(owner_reset, assign_new_owner)
        reset_block = update[owner_reset:assign_new_owner]
        self.assertIn("previousState.cancelPendingNeighborSelection()", reset_block)
        self.assertIn("hasReceivedCollectionSnapshot = false", reset_block)
        self.assertIn("collectionOwnerGeneration &+= 1", reset_block)
        self.assertIn("items = []", reset_block)
        replacement = swift_body(self.host, "func replaceCollectionModel(state: ReplicaUIState)")
        self.assertIn("hasReceivedCollectionSnapshot = false", replacement)
        self.assertIn("items = []", replacement)
        self.assertIn("previousIDs != incomingIDs", swift_body(self.host, "private func drainCollectionSnapshots()"))

    def test_full_reload_resets_selection_without_a_pending_selection_equality_gate(self):
        state = swift_body(self.controller, "func applyFullCollectionReload(items: [ClipboardItem])")
        self.assertNotIn("expected", state)
        self.assertNotIn("guard", state)
        self.assertIn("let firstID = items.first?.id", state)
        self.assertIn("applyOrderedSelection(firstID.map { [$0] } ?? [], anchor: firstID, primary: firstID)", state)
        self.assertIn("struct CollectionSelectionSnapshot: Equatable", self.controller)

    def test_incremental_snapshot_drops_deleted_selection_without_fallback(self):
        normalize = swift_body(self.controller, "func applyIncrementalCollectionSnapshot(items: [ClipboardItem])")
        self.assertIn("orderedSelectionIDs.filter { selection.contains($0) && visible.contains($0) }", normalize)
        self.assertIn("allowsEmptySelection = ids.isEmpty", normalize)
        self.assertIn("applyOrderedSelection(ids, anchor: ids.last, primary: ids.last)", normalize)
        self.assertNotIn("items.first", normalize)
        self.assertNotIn("cancelPendingNeighborSelection()", normalize)

    def test_report_binds_live_method_references_and_static_check(self):
        for row in self.result["current_references"]:
            path = ROOT / row["path"]
            source = pre_collection_membership(path.read_text())
            if row["symbol"] == "func applyFullCollectionReload(items: [ClipboardItem], ifSelectionUnchangedFrom expected: CollectionSelectionSnapshot) -> Bool":
                historical = ROOT / ".local/p0-repair/phase-3/before" / row["path"]
                self.assertIn(row["symbol"], historical.read_text())
                self.assertNotIn(row["symbol"], source)
                self.assertIn("func applyFullCollectionReload(items: [ClipboardItem])", source)
            else:
                self.assertIn(row["symbol"], source)
            frozen = json.loads((ROOT / "reports/replica/p0-p1-repair-round2.json").read_text())
            self.assertEqual(frozen["current_production_hashes"][row["path"]], row["sha256"])
            before = ROOT / ".local/p0-repair/phase-3/before" / row["path"]
            self.assertEqual(hashlib.sha256(before.read_bytes()).hexdigest(), row["sha256"])
        self.assertEqual(self.result["checks"]["test_file"], "scripts/tests/test_p0_repair_snapshot.py")


if __name__ == "__main__":
    unittest.main()
