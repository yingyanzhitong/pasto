"""Static checks for ordered selected-item deletion routing."""
import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / ".local/p0-repair/phase-2/ordered-delete-ui-result.json"
UI = ROOT / "replica/Sources/Pasto/UI/ReplicaUIController.swift"
STORE = ROOT / "replica/Sources/PastoCore/ClipboardStore.swift"


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


class OrderedDeleteUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads(RESULT.read_text())
        cls.ui = UI.read_text()
        cls.store = STORE.read_text()

    def test_original_selection_sequence_is_iterated_and_preserved_for_confirmation(self):
        for row in self.result["original_fragments"]:
            fragment = original_fragment(ROOT / row["path"], row["function_id"].split(":", 1)[1])
            self.assertEqual(hashlib.sha256(fragment.encode()).hexdigest(), row["sha256"])
        delete = original_fragment(ROOT / "decompiled/Paste/part-0035.c", "0x100068db8")
        self.assertIn("puVar20 = (undefined8 *)(param_1 + 0x20)", delete)
        self.assertIn("do {", delete)
        self.assertIn("FUN_1003b8bfc()", delete)
        self.assertIn("FUN_1001b9698(&local_70,uVar21", delete)
        self.assertIn("__appendElementAssumeUniqueAndCapacity(pMVar19,lVar3)", delete)
        self.assertIn("FUN_1003ba464", delete)
        self.assertIn("FUN_1000691c8()", delete)
        self.assertIn("FUN_1003ba5c4(&local_68", delete)

    def test_delete_request_captures_ordered_ids_with_set_only_for_membership(self):
        request = swift_body(self.ui, "struct ItemDeletionRequest")
        self.assertIn("let ids: Set<UUID>", request)
        self.assertIn("let orderedIDs: [UUID]", request)
        delete = swift_body(self.ui, "func deleteSelection()")
        self.assertIn("let orderedIDs = orderedSelectionIDs.filter { selection.contains($0) && visibleIDs.contains($0) }", delete)
        self.assertIn("let ids = Set(orderedIDs)", delete)
        self.assertIn("guard !orderedIDs.isEmpty else { return }", delete)
        self.assertIn("ItemDeletionRequest(ids: ids, orderedIDs: orderedIDs", delete)
        self.assertNotIn("selection.intersection", delete)

    def test_confirm_routes_same_order_to_both_store_apis(self):
        confirm = swift_body(self.ui, "func confirmItemDeletion()")
        self.assertIn("executeItemDeletion(request)", confirm)
        execute = swift_body(self.ui, "private func executeItemDeletion(")
        self.assertIn("store.permanentlyDelete(orderedIDs: request.orderedIDs)", execute)
        self.assertIn("store.delete(orderedIDs: request.orderedIDs, currentPinboardID: { [self] in pinboardID })", execute)
        self.assertIn("completion?()", execute)
        self.assertIn("func delete(orderedIDs: [UUID], contextPinboardID: UUID?) throws", self.store)
        self.assertIn("func permanentlyDelete(orderedIDs: [UUID]) throws", self.store)

    def test_report_binds_real_current_methods_and_sources(self):
        for row in self.result["current_references"]:
            path = ROOT / row["path"]
            source = path.read_text()
            self.assertIn(row["symbol"], source)
            frozen = json.loads((ROOT / "reports/replica/p0-p1-repair-round2.json").read_text())
            self.assertEqual(frozen["current_production_hashes"][row["path"]], row["sha256"])
            checkpoint = ROOT / ".local/p0-repair/phase-3/before" / row["path"]
            self.assertEqual(hashlib.sha256(checkpoint.read_bytes()).hexdigest(), row["sha256"])


if __name__ == "__main__":
    unittest.main()
