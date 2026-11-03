"""Deletion transaction callback contracts; source and ARM64 data only."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "scripts/tests")]
from function_ledger import source_fragments
from macho_imports import parse_macho
from test_offline_p0_contracts import body

UI = ROOT / "replica/Sources/Pasto/UI/ReplicaUIController.swift"
HOST = ROOT / "replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift"
STORE = ROOT / "replica/Sources/PastoCore/ClipboardStore.swift"


class DeleteCompletion(unittest.TestCase):
    def test_native_save_error_releases_error_and_joins_optional_callback(self):
        data = (ROOT / ".local/paste-arm64-static.bin").read_bytes()
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
        self.assertEqual(branch(0x1003baaf8), 0x1002ff310)
        self.assertEqual(word(0x1003baafc), 0xb4000075)
        self.assertEqual(branch(0x1003bab04), 0x100bfc708)
        self.assertEqual(parse_macho(ROOT / ".local/paste-arm64-static.bin")["stubs"]["0x100bfc708"]["symbol"], "_swift_errorRelease")
        self.assertEqual(word(0x1003bab08), 0xb4000053)
        self.assertEqual(word(0x1003bab0c), 0xd63f0260)  # blr x19, after either error branch

    def test_transaction_reports_error_then_invokes_optional_void_completion_once(self):
        execute = body(UI.read_text(), "private func executeItemDeletion(")
        catch = body(execute, "catch")
        self.assertIn("itemDeletionError = error.localizedDescription", catch)
        self.assertNotIn("return", catch)
        self.assertNotIn("throw", catch)
        self.assertEqual(execute.count("completion?()"), 1)
        self.assertTrue(execute.rstrip().endswith("completion?()\n    }"))
        self.assertIn("completion: (() -> Void)?", UI.read_text())

    def test_actual_operation_reads_current_context_and_preserves_order(self):
        ui = UI.read_text()
        execute = body(ui, "private func executeItemDeletion(")
        self.assertIn("store.permanentlyDelete(orderedIDs: request.orderedIDs)", execute)
        self.assertIn("store.delete(orderedIDs: request.orderedIDs, currentPinboardID: { [self] in pinboardID })", execute)
        mutation = body(STORE.read_text(), "public func delete(orderedIDs: [UUID], currentPinboardID:")
        self.assertLess(mutation.index("try mutate(deletingItemIDs: orderedIDs,"), mutation.index("let contextPinboardID = currentPinboardID()"))
        self.assertNotIn("request.contextPinboardID", execute)

    def test_weak_view_owner_gates_action_and_completion(self):
        ui = UI.read_text()
        self.assertIn("weak var collectionOwner: ReplicaNativeCollectionHost?", ui)
        self.assertIn("guard let before = collectionOwner?.appliedItems(for: self) else { return }",
                      body(ui, "func deleteSelection()"))
        applied = body(HOST.read_text(), "func appliedItems(for state: ReplicaUIState)")
        self.assertIn("self.state === state, state.collectionOwner === self", applied)
        confirm = body(ui, "func confirmItemDeletion()")
        self.assertIn("[weak self, weak owner = collectionOwner]", confirm)
        self.assertLess(confirm.index("self.collectionOwner === owner"), confirm.index("self.completeItemDeletion(request)"))
        host = HOST.read_text()
        self.assertIn("state.collectionOwner = self", body(host, "func update(state: ReplicaUIState, cardSide: CGFloat)"))
        detach = body(host, "func detachObservers()")
        self.assertIn("state.collectionOwner === self", detach)
        self.assertIn("state.collectionOwner = nil", detach)

    def test_failure_keeps_panel_error_but_still_queues_pending_id_for_real_update(self):
        ui = UI.read_text()
        complete = body(ui, "private func completeItemDeletion(")
        success = body(complete, "if itemDeletionError == nil")
        self.assertIn("cancelItemDeletion()", success)
        self.assertNotIn("pendingNeighborSelection =", success)
        self.assertIn("if let neighborID = request.neighborID", complete)
        self.assertIn("pendingNeighborSelection = PendingNeighborSelection", complete)
        update = body(HOST.read_text(), "private func drainCollectionSnapshots()")
        self.assertIn("incomingIDs != neighbor.beforeIDs", update)
        for forbidden in ["hidePanel(", "runModal(", "presentError("]:
            self.assertNotIn(forbidden, complete)

    def test_context_cancellation_and_user_selection_guards_are_retained(self):
        ui = UI.read_text()
        for signature in ["func applySearchInput(nodes:", "private func applySelectedList(_ id:",
                          "@Published var query =", "@Published var searchFilters:",
                          "@Published var pinboardID:", "@Published var showDeleted ="]:
            self.assertIn("cancelItemDeletion()", body(ui, signature))
        self.assertIn("cancelPendingNeighborSelection()", body(ui, "private func selectIndex("))
        update = body(HOST.read_text(), "private func drainCollectionSnapshots()")
        self.assertIn("state.collectionOwner === self", update)


if __name__ == "__main__":
    unittest.main()
