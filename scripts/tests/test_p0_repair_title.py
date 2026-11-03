"""Static source checks for the P0 explicit-title clearing repair."""
from native_title_scope_contract import pre_native_title
import hashlib
import json
import re
import unittest
from pathlib import Path
from resolved_copy_scope_contract import pre_resolved_copy


ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / ".local/p0-repair/phase-1/baseline.json"
RESULT = ROOT / ".local/p0-repair/phase-1/title-result.json"
STORE_PATH = "replica/Sources/PastoCore/ClipboardStore.swift"
UI_PATH = "replica/Sources/Pasto/UI/ReplicaUIController.swift"
MODEL_PATH = "replica/Sources/PastoCore/Models.swift"
BASELINE_UPDATE_ITEM_BODY_SHA256 = "247b4501aec7e2dba36ff2163b32dcb08327a43ac9448f5f4c287860d01596ee"
BASELINE_RENAME_ITEM_BODY_SHA256 = "dfb94054da48ab025c770bbd33d210f40691da0096c74f314879e85f0447d926"
BASELINE_PROMPT_BODY_SHA256 = "2294c201116ab22a0333c4c3f4f5fa47667e5bd699dccbb5785527866873172d"
BASELINE_COPY_SELECTION_BODY_SHA256 = "a1a824551aa88ca505c7ce0f66139b35e9f31dc527d59edb1fe9a407026aa580"


def swift_body(source: str, signature: str) -> str:
    """Return a Swift brace-delimited body, ignoring braces in strings/comments."""
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


def function_fragment(path: Path, address: str) -> str:
    source = path.read_text()
    headers = list(re.finditer(r"^/\* Address: (0x[0-9a-f]+) \| .*? \*/$", source, re.M))
    for index, match in enumerate(headers):
        if match.group(1) == address:
            end = headers[index + 1].start() if index + 1 < len(headers) else len(source)
            return source[match.start():end].rstrip() + "\n"
    raise AssertionError(f"Original function not found: {path} {address}")


class P0TitleRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline = json.loads(BASELINE.read_text())
        cls.result = json.loads(RESULT.read_text())
        cls.store = pre_native_title((ROOT / STORE_PATH).read_text())
        cls.ui = pre_resolved_copy((ROOT / UI_PATH).read_text())
        cls.models = (ROOT / MODEL_PATH).read_text()

    def test_baseline_hashes_bind_the_two_owned_source_files(self):
        before = json.loads((ROOT / ".local/p0-review/production-before.json").read_text())
        self.assertEqual(self.baseline["production"], before)
        for relative in (STORE_PATH, UI_PATH):
            self.assertIn(relative, self.baseline["production"])
        baseline_methods = {
            "ClipboardStore.updateItem": BASELINE_UPDATE_ITEM_BODY_SHA256,
            "ReplicaUIController.renameItem": BASELINE_RENAME_ITEM_BODY_SHA256,
            "ReplicaUIController.prompt": BASELINE_PROMPT_BODY_SHA256,
            "ReplicaUIController.copySelection": BASELINE_COPY_SELECTION_BODY_SHA256,
        }
        store_method = swift_body(self.store, "public func updateItem(id: UUID, title: String? = nil, text: String? = nil) throws")
        self.assertEqual(store_method.count("state.items[i].hasExplicitTitle = !title.isEmpty"), 1)
        baseline_store_method = store_method.replace("state.items[i].hasExplicitTitle = !title.isEmpty", "state.items[i].hasExplicitTitle = true").replace(
            "\n                Self.refreshNativeChecksum(&state.items[i])", "")
        rename = swift_body(self.ui, "func renameItem(_ item: ClipboardItem)").replace(
            "initial: item.title, allowsEmpty: true)", "initial: item.title)")
        prompt = swift_body(self.ui, "private func prompt(title: String, message: String, initial: String, allowsEmpty: Bool = false)")
        prompt = prompt.replace(
            "private func prompt(title: String, message: String, initial: String, allowsEmpty: Bool = false)",
            "private func prompt(title: String, message: String, initial: String)",
        ).replace("return name.isEmpty && !allowsEmpty ? nil : name", "return name.isEmpty ? nil : name")
        copy = swift_body(self.ui, "func copySelection(plainTextOnly: Bool)").replace(
            "guard !items.isEmpty else { NSSound.beep(); return }", "guard !items.isEmpty else { return }").replace(
            "let items = appliedSelectionItems()", "let items = state.selectedItems")
        reconstructed = {
            "ClipboardStore.updateItem": baseline_store_method,
            "ReplicaUIController.renameItem": rename,
            "ReplicaUIController.prompt": prompt,
            "ReplicaUIController.copySelection": copy,
        }
        for name, source in reconstructed.items():
            digest = hashlib.sha256(source.encode()).hexdigest()
            self.assertEqual(digest, baseline_methods[name])
            self.assertEqual(self.result["baseline_method_sha256"][name], digest)

    def test_original_function_hashes_match_full_fragments(self):
        for fragment in self.result["original_fragments"]:
            normalized = function_fragment(ROOT / fragment["path"], fragment["function_id"].split(":", 1)[1])
            self.assertEqual(hashlib.sha256(normalized.encode()).hexdigest(), fragment["sha256"])
        self.assertEqual(
            {row["function_id"] for row in self.result["original_fragments"]},
            {"Paste:0x100364ab4", "Paste:0x1003bae08", "Paste:0x10006e0dc"},
        )

    def test_nil_title_is_still_noop_and_explicit_empty_clears_flag(self):
        body = swift_body(self.store, "public func updateItem(id: UUID, title: String? = nil, text: String? = nil) throws")
        self.assertIn(
            "if let title {\n                state.items[i].title = title\n"
            "                state.items[i].hasExplicitTitle = !title.isEmpty\n            }",
            body,
        )

    def test_model_maps_cleared_explicit_title_to_nil(self):
        body = swift_body(self.models, "public var originalTitle: String?")
        self.assertIn("if hasExplicitTitle == false", body)
        self.assertIn("return nil", body)

    def test_only_item_rename_opts_into_empty_prompt(self):
        rename = swift_body(self.ui, "func renameItem(_ item: ClipboardItem)")
        self.assertIn("allowsEmpty: true", rename)
        self.assertIn("updateItem(id: item.id, title: title, text: nil)", rename)
        call_sites = re.findall(r"(?<!func )prompt\(title:", self.ui)
        self.assertEqual(len(call_sites), 3)
        self.assertEqual(self.ui.count("allowsEmpty: true"), 1)

    def test_prompt_rejects_empty_by_default_and_cancel_returns_nil(self):
        prompt = swift_body(self.ui, "private func prompt(title: String, message: String, initial: String, allowsEmpty: Bool = false)")
        self.assertIn("guard alert.runModal() == .alertFirstButtonReturn else { return nil }", prompt)
        self.assertIn("return name.isEmpty && !allowsEmpty ? nil : name", prompt)
        self.assertIn("initial: store.preferences.historyTitle)", self.ui)
        self.assertIn("initial: board.name)", self.ui)


if __name__ == "__main__":
    unittest.main()
