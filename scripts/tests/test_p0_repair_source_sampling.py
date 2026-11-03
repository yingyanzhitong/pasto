from pathlib import Path
import hashlib
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
PASTEBOARD = ROOT / "replica/Sources/PastoCore/Pasteboard.swift"
STORE = ROOT / "replica/Sources/PastoCore/ClipboardStore.swift"
ORIGINAL_FRAGMENTS = {
    "0x10035fbcc": ("decompiled/Paste/part-0274.c", "a46d7392de33b84487119e48f77904a091063f2612ea8624f6976d90392d7634"),
    "0x10037b034": ("decompiled/Paste/part-0281.c", "472bd2bc3fbc094ebeb47207e9491cd0d15c33c599a6043b074552125a0a26cf"),
    "0x10037b204": ("decompiled/Paste/part-0281.c", "0636ea17d63475345db6c47ac043dd9fbf5828a65c1e4afb5fdf817e9b2a9b10"),
    "0x10037c47c": ("decompiled/Paste/part-0282.c", "b8f348bd25063bf7f2ae9d57cd8ff909735dc811a2a7876a08d8d66259acf70c"),
    "0x10037c494": ("decompiled/Paste/part-0282.c", "3e14c2d8da9365f1e8f0e2a22cd8e609389c21d90bb9ce4795e10d041df6e8ec"),
    "0x100311e3c": ("decompiled/Paste/part-0254.c", "993189242d38b635d1c9530b7ab3ddc2aae5fbcb8c64744aea8e301d19f73cab"),
}


def swift_function(source: str, signature: str) -> str:
    start = source.index(signature)
    brace = source.index("{", start)
    depth = 0
    for index in range(brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start:index + 1]
    raise AssertionError(f"unterminated Swift function: {signature}")


class P0SourceSamplingTests(unittest.TestCase):
    def test_original_fragments_match_the_reviewed_full_function_hashes(self):
        for address, (relative_path, expected_hash) in ORIGINAL_FRAGMENTS.items():
            source = (ROOT / relative_path).read_text()
            headers = list(re.finditer(
                r'^/\* Address: (0x[0-9a-fA-F]+) \| [^*]+ \*/\s*$', source, re.MULTILINE
            ))
            index = next(i for i, header in enumerate(headers) if header.group(1).lower() == address.lower())
            end = headers[index + 1].start() if index + 1 < len(headers) else len(source)
            fragment = source[headers[index].start():end].rstrip() + "\n"
            self.assertEqual(hashlib.sha256(fragment.encode()).hexdigest(), expected_hash, address)

    def test_public_capture_and_add_keep_explicit_snapshot_contract(self):
        pasteboard = PASTEBOARD.read_text()
        store = STORE.read_text()
        capture = swift_function(pasteboard, "    public func capture(pasteboard:")
        add = swift_function(store, "    public func add(_ item:")
        self.assertIn("sourceApplication: SourceApplicationRecord? = nil", capture)
        self.assertNotIn("sourceProvider", capture)
        self.assertIn("sourceApplication: sourceApplication", capture)
        self.assertIn("sourceApplication: SourceApplicationRecord? = nil", add)
        self.assertNotIn("sourceProvider", add)

    def test_only_monitor_capture_supplies_late_source(self):
        pasteboard = PASTEBOARD.read_text()
        internal_capture = swift_function(pasteboard, "    func captureWithInsertionResult(pasteboard:")
        monitor_capture = swift_function(pasteboard, "    public func f_10037b034(_ items:")
        self.assertIn("sourceProvider:", internal_capture)
        self.assertIn("sourceProvider: sourceProvider", internal_capture)
        self.assertIn("guard !items.isEmpty", monitor_capture)
        self.assertIn("OriginalPasteboardChecksums.f_1003216bc", monitor_capture)
        self.assertLess(monitor_capture.index("OriginalPasteboardChecksums.f_1003216bc"),
                        monitor_capture.index("sourceProvider: {"))
        self.assertIn("let app = NSWorkspace.shared.frontmostApplication", monitor_capture)
        self.assertIn("OriginalSourceApplication.snapshot(app)", monitor_capture)

    def test_lazy_sample_updates_result_after_content_selection_before_capture_time(self):
        store = STORE.read_text()
        add = swift_function(store, "    func addWithInsertionResult(_ item:")
        selected = add.index("result = (state.items.count - 1, true)")
        sample = add.index("if let sourceProvider {")
        timestamp = add.index("transaction.repository.restoreHistoryItems([target!])")
        self.assertLess(selected, sample)
        self.assertLess(sample, timestamp)
        self.assertIn("sourceProvider()", add)
        self.assertIn("state.items[result.index].sourceApplicationRelationIsKnown = true", add)
        self.assertIn("if let application = source.application", add)
        self.assertIn("Self.upsertSourceApplication(application, in: &state)", add)


if __name__ == "__main__":
    unittest.main()
