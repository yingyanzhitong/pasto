"""Static restore-contract checks; no Swift, AppKit, application or network execution."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "scripts/tests")]
from test_offline_p0_contracts import body
from macho_imports import parse_macho
from resolved_copy_scope_contract import pre_resolved_copy

SOURCE = "replica/Sources/PastoCore/Pasteboard.swift"
SIGNATURE = "private func writeToPasteboard(ids:"
OLD = """        try recordRestoredItems(ids)
        Self.restoreUndoManager.f_1000da768().removeAllActions()
        didRestoreItem.send()"""
NEW = """        do {
            try recordRestoredItems(ids)
        } catch {
            // Original 0x10037a144 releases the transaction error and continues below.
        }
        Self.restoreUndoManager.f_1000da768().removeAllActions()
        // 37a144 posts process-wide with the restoring manager as object.
        // Keep the legacy subject for the existing local sound subscriber.
        NotificationCenter.default.post(name: Self.didRestoreItemNotification, object: self)
        didRestoreItem.send()"""


class RestoreRepair(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current = pre_resolved_copy((ROOT / SOURCE).read_text())
        cls.method = body(cls.current, SIGNATURE)

    def test_only_restore_failure_followup_tail_changed(self):
        baseline = ROOT / ".local/p0-repair/phase-1/before" / SOURCE
        old = body(baseline.read_text(), SIGNATURE)
        marker = "// 0x10037a144: performAndWait + save"
        self.assertEqual(old.count(OLD), 1)
        self.assertEqual(self.method[self.method.index(marker):],
                         old[old.index(marker):].replace(OLD, NEW, 1).replace("recordRestoredItems(ids)", "recordRestoredSelection(restoration)", 1))

    def test_writer_precedes_save_and_success_side_effects(self):
        markers = ["try reload()", "let selected = try ids.map", "let selections = try selected.map",
                   "writer.f_10037875c(objects)", "try recordRestoredSelection(restoration)",
                   "removeAllActions()", "didRestoreItem.send()"]
        positions = [self.method.index(marker) for marker in markers]
        self.assertEqual(positions, sorted(positions))

    def test_save_failure_joins_undo_and_notification(self):
        catch = self.method.split("} catch {", 1)[1].split("}", 1)[0]
        statements = "".join(line.split("//", 1)[0] for line in catch.splitlines())
        self.assertFalse(statements.strip())
        self.assertIn(NEW.replace("recordRestoredItems(ids)", "recordRestoredSelection(restoration)", 1), self.method)
        self.assertEqual(self.method.count("removeAllActions()"), 1)
        self.assertEqual(self.method.count("didRestoreItem.send()"), 1)

    def test_pre_writer_errors_remain_outside_save_catch(self):
        prefix = self.method.split("        do {", 1)[0]
        self.assertIn("throw ClipboardStoreError.itemNotFound", prefix)
        self.assertIn("throw RecognizedImageTextCopyError.imageChanged", prefix)
        self.assertIn("throw RecognizedImageTextCopyError.noRecognizedText", prefix)
        self.assertNotIn("try? reload", prefix)
        self.assertEqual(prefix.count("catch"), 0)

    def test_original_native_error_branch_and_undo_chain(self):
        binary = ROOT / ".local/paste-arm64-static.bin"
        data = binary.read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(),
                         "871f00354fbb1c165d858a98e6d19d6f43cb9d3f9f958b3e07c7f07eb5c19afb")
        segments = json.loads((ROOT / "reports/replica/p0-p1-review-round27-static-proof.json").read_text())["file_backed_segments"]
        def word(address):
            segment = next(s for s in segments if s["vmaddr"] <= address < s["vmaddr"] + s["filesize"])
            return struct.unpack_from("<I", data, segment["fileoff"] + address - segment["vmaddr"])[0]
        def branch(address):
            value = word(address)
            self.assertEqual(value & 0xfc000000, 0x94000000)
            value &= 0x3ffffff
            return address + (value - (1 << 26) if value & (1 << 25) else value) * 4
        self.assertEqual(word(0x10037a5b0), 0xb4000075)  # cbz x21, common continuation
        self.assertEqual(branch(0x10037a5b8), 0x100bfc708)
        self.assertEqual(parse_macho(binary)["stubs"]["0x100bfc708"]["symbol"], "_swift_errorRelease")
        self.assertEqual(branch(0x10037a5c4), 0x1000da768)
        self.assertEqual(branch(0x10037a5d0), 0x100c08e80)


if __name__ == "__main__":
    unittest.main()
