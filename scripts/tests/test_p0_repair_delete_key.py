"""Static source checks for responder-scoped collection deletion keys."""
import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / ".local/p0-repair/phase-1/delete-key-result.json"
UI_PATH = "replica/Sources/Pasto/UI/ReplicaUIController.swift"
COLLECTION_PATH = "replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift"


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


class CollectionDeleteKeyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads(RESULT.read_text())
        cls.ui = (ROOT / UI_PATH).read_text()
        cls.collection = (ROOT / COLLECTION_PATH).read_text()

    def test_original_keydown_fragment_hash_and_special_key_branch(self):
        row = self.result["original"]
        fragment = original_fragment(ROOT / row["path"], row["function_id"].split(":", 1)[1])
        self.assertEqual(hashlib.sha256(fragment.encode()).hexdigest(), row["sha256"])
        for key in ["SpecialKey::_get_backspace", "SpecialKey::_get_delete(", "SpecialKey::_get_deleteForward"]:
            self.assertIn(key, fragment)
        self.assertIn("FUN_100066068(local_100.cache,uVar20,0)", fragment)
        self.assertIn("FUN_100068db8()", fragment)

    def test_global_key_handler_no_longer_owns_delete_keys(self):
        body = swift_body(self.ui, "private func handleKey(_ event: NSEvent) -> Bool")
        for forbidden in [".backspace", ".deleteForward", "state.deleteSelection()"]:
            self.assertNotIn(forbidden, body)
        self.assertIn("case .carriageReturn, .enter:", body)
        self.assertIn("copySelection(plainTextOnly:", body)
        self.assertIn("handleSearchCommand()", body)
        self.assertIn("state.confirmItemDeletion()", body)

    def test_collection_responder_consumes_only_three_delete_keys(self):
        key_down = swift_body(self.collection, "override func keyDown(with event: NSEvent)")
        self.assertIn("case .backspace, .delete, .deleteForward:", key_down)
        self.assertIn("state?.deleteSelection()", key_down)
        self.assertIn("super.keyDown(with: event)", key_down)
        self.assertEqual(self.collection.count("override func keyDown(with event: NSEvent)"), 1)

    def test_window_event_path_routes_other_responder_keys_through(self):
        send_event = swift_body(self.ui, "override func sendEvent(_ event: NSEvent)")
        self.assertIn("keyHandler?(event) == true", send_event)
        self.assertIn("super.sendEvent(event)", send_event)
        search_event = swift_body(
            (ROOT / "replica/Sources/Pasto/UI/ReplicaPanelContentView.swift").read_text(),
            "func tryInterpretSearchKeyEvent(_ event: NSEvent) -> Bool",
        )
        self.assertIn("event.specialKey == nil", search_event)
        for row in self.result["current_references"]:
            source = (ROOT / row["path"]).read_text()
            self.assertIn(row["symbol"], source)


if __name__ == "__main__":
    unittest.main()
