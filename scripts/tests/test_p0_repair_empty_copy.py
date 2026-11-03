from native_restore_writer_scope_contract import pre_native_restore_writer
"""Static source checks for the P0 empty-selection copy beep repair."""
import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / ".local/p0-repair/phase-1/empty-copy-result.json"
UI_PATH = "replica/Sources/Pasto/UI/ReplicaUIController.swift"


def original_fragment(path: Path, address: str) -> str:
    source = path.read_text()
    headers = list(re.finditer(r"^/\* Address: (0x[0-9a-f]+) \| .*? \*/$", source, re.M))
    for index, match in enumerate(headers):
        if match.group(1) == address:
            end = headers[index + 1].start() if index + 1 < len(headers) else len(source)
            return source[match.start():end].rstrip() + "\n"
    raise AssertionError(f"Original function not found: {path} {address}")


class EmptyCopyBeepTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads(RESULT.read_text())
        cls.ui = pre_native_restore_writer((ROOT / UI_PATH).read_text())

    def test_original_direct_caller_empty_all_satisfy_and_predicate_hashes(self):
        for row in [self.result["original"], *self.result["supporting_original_fragments"]]:
            fragment = original_fragment(ROOT / row["path"], row["function_id"].split(":", 1)[1])
            self.assertEqual(hashlib.sha256(fragment.encode()).hexdigest(), row["sha256"])
        caller = original_fragment(ROOT / "decompiled/Paste/part-0035.c", "0x100065ed8")
        self.assertIn("FUN_1003b936c", caller)
        self.assertIn("NSSound::beep()", caller)
        self.assertLess(caller.index("if (((ulong)puVar7 & 1) == 0)"), caller.index("NSSound::beep()"))
        predicate = original_fragment(ROOT / "decompiled/Paste/part-0294.c", "0x1003b936c")
        self.assertIn("FUN_10031c4c4", predicate)
        self.assertIn("return ((uint)uVar1 ^ 0xffffffff) & 1", predicate)
        all_satisfy = original_fragment(ROOT / "decompiled/Paste/part-0257.c", "0x10031c4c4")
        self.assertIn("Sequence::_allSatisfy", all_satisfy)

    def test_empty_selection_beeps_and_nonempty_route_remains_copy(self):
        start = self.ui.index("func copySelection(plainTextOnly: Bool)")
        body_start = self.ui.index("{", start)
        depth = 0
        for index in range(body_start, len(self.ui)):
            depth += (self.ui[index] == "{") - (self.ui[index] == "}")
            if depth == 0:
                body = self.ui[body_start:index + 1]
                break
        else:
            self.fail("copySelection body is unclosed")
        self.assertIn("let items = appliedSelectionItems()", body)
        self.assertIn("guard !items.isEmpty else { NSSound.beep(); return }", body)
        self.assertIn("performCopy {", body)
        self.assertIn("store.writeToPasteboard(selectedItems: items, pasteboard: pasteboard, plainTextOnly: plainTextOnly)", body)
        self.assertEqual(body.count("NSSound.beep()"), 1)
        self.assertIn("guard !ids.isEmpty else { return }", self.ui)

    def test_result_binds_real_current_consumer_and_source_hash(self):
        ref = self.result["current_reference"]
        self.assertEqual(ref["path"], UI_PATH)
        self.assertEqual(ref["symbol"], "func copySelection(plainTextOnly: Bool)")
        self.assertIn(ref["symbol"], self.ui)


if __name__ == "__main__":
    unittest.main()
