"""Static source checks for the bounded P0 collection-responder routing repair."""
import hashlib
import re
import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
UI_PATH = "replica/Sources/Pasto/UI/ReplicaUIController.swift"
UI = ROOT / UI_PATH
ORIGINALS = {
    "0x100069fe0": ("decompiled/Paste/part-0035.c", "c7457bcee6863fb71878ee74a20394a338dc36bbf11e7cfdb281d46dc0f34832"),
    "0x100074bac": ("decompiled/Paste/part-0037.c", "9c1403773c7c4273e67a8228c18e41f21b87f0b1a5f66ecec1bf84453419b2f9"),
    "0x100074dcc": ("decompiled/Paste/part-0037.c", "c802b7daf3738a57daf34e7e1b3b02219c88f4b3f7a03b247701bb1f26ccd98d"),
    "0x10008be54": ("decompiled/Paste/part-0046.c", "b62b67f392608fbf3b56b484517907da35b87065531d4666243074b1d3d1eef3"),
}
ARM_CALLS = {
    0x10006A00C: 0x100BF717C,
    0x10006A058: 0x100BF71C4,
    0x10006A0A4: 0x100BF7224,
    0x10006A0F8: 0x100074BAC,
    0x10006A100: 0x100074DCC,
    0x10006A10C: 0x10008BE54,
}


def original_fragment(path: Path, address: str) -> str:
    source = path.read_text()
    headers = list(re.finditer(r"^/\* Address: (0x[0-9a-f]+) \| .*? \*/$", source, re.M))
    for index, match in enumerate(headers):
        if match.group(1) == address:
            end = headers[index + 1].start() if index + 1 < len(headers) else len(source)
            return source[match.start():end].rstrip() + "\n"
    raise AssertionError(f"Original function not found: {path} {address}")


def swift_method(source: str, signature: str, next_signature: str) -> str:
    start = source.index(signature)
    end = source.index(next_signature, start + len(signature))
    return source[start:end]


def arm_bl_target(image: bytes, address: int) -> int:
    word = struct.unpack_from("<I", image, address - 0x100000000)[0]
    immediate = word & 0x03FFFFFF
    if immediate & (1 << 25):
        immediate -= 1 << 26
    return address + immediate * 4


class P0KeyResponderRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ui = UI.read_text()
        cls.method = swift_method(
            cls.ui,
            "    private func handleKey(_ event: NSEvent) -> Bool",
            "    func cancelSearchOrPanel()",
        )

    def test_original_function_fragments_and_arm_calls_are_bound(self):
        for address, (relative_path, expected_hash) in ORIGINALS.items():
            fragment = original_fragment(ROOT / relative_path, address)
            self.assertEqual(hashlib.sha256(fragment.encode()).hexdigest(), expected_hash)
        image = (ROOT / ".local/targets/Paste.arm64").read_bytes()
        for address, target in ARM_CALLS.items():
            self.assertEqual(arm_bl_target(image, address), target, hex(address))

    def test_non_owner_keeps_only_exact_configured_numeric_shortcut_exception(self):
        body = self.method
        responder_check = "collection.window === panel"
        self.assertIn(responder_check, body)
        self.assertIn("ownsCollectionFocus = panel.firstResponder === collection", body)
        action_at = body.index("let quickPasteAction = OriginalCollectionShortcutActions.quickPasteAction")
        non_owner_at = body.index("if !ownsCollectionFocus {")
        numeric_guard_at = body.index("guard let quickPasteAction else { return false }", non_owner_at)
        owner_gate_at = body.index("if !state.searchVisible {", non_owner_at)
        self.assertLess(action_at, non_owner_at)
        self.assertLess(non_owner_at, numeric_guard_at)
        self.assertLess(numeric_guard_at, owner_gate_at)
        self.assertIn("performQuickPaste(quickPasteAction)", body[non_owner_at:owner_gate_at])
        self.assertIn("if !isEditing, let action = quickPasteAction", body[owner_gate_at:])

    def test_collection_shortcuts_are_behind_owner_gate_but_pending_and_escape_remain_first(self):
        body = self.method
        pending_at = body.index("if state.hasPendingDeletion")
        escape_at = body.index("if event.keyCode == 53", pending_at + 1)
        non_owner_at = body.index("if !ownsCollectionFocus {")
        group_shortcut_at = body.index("previousPinboardShortcut?.matches(event)")
        copy_at = body.index("OriginalCollectionShortcutActions.copyOptions")
        self.assertLess(pending_at, escape_at)
        self.assertLess(escape_at, non_owner_at)
        self.assertLess(non_owner_at, group_shortcut_at)
        self.assertLess(non_owner_at, copy_at)
        self.assertIn("guard let quickPasteAction else { return false }", body)

    def test_panel_dispatch_and_downstream_key_consumers_remain_bounded(self):
        send_event = swift_method(self.ui, "    override func sendEvent(_ event: NSEvent)", "}\n\n@MainActor\nprivate final class ReplicaEditorWindow")
        self.assertLess(send_event.index("tabTitleEditingOwner?.ownsEditor"), send_event.index("keyHandler?(event)"))
        self.assertLess(send_event.index("keyHandler?(event)"), send_event.index("super.sendEvent(event)", send_event.index("keyHandler?(event)")))
        native = (ROOT / "replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift").read_text()
        key_down = swift_method(native, "    override func keyDown(with event: NSEvent)", "    override func selectAll(_ sender: Any?)")
        self.assertIn("case .backspace, .delete, .deleteForward:", key_down)
        self.assertIn("state?.deleteSelection()", key_down)
        self.assertIn("super.keyDown(with: event)", key_down)
        monitor_start = self.ui.index("panelEscapeMonitor = NSEvent.addLocalMonitorForEvents(matching: .keyDown)")
        monitor = self.ui[monitor_start:self.ui.index("let mouseDown:", monitor_start)]
        self.assertIn("event.keyCode == 53", monitor)
        self.assertNotIn("quickPasteAction", monitor)


if __name__ == "__main__":
    unittest.main()
