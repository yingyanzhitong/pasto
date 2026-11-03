"""Offline panel source contracts, not AppKit interaction or animation tests."""
import json
import struct
import unittest

from test_offline_p0_contracts import ROOT, body


class PanelLifecycleContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ui = (ROOT / "replica/Sources/Pasto/UI/ReplicaUIController.swift").read_text()
        cls.index = {r["address"]: r for r in json.loads((ROOT / "reports/Paste/function-index.json").read_text())}

    @classmethod
    def original(cls, address):
        text = (ROOT / cls.index[address]["file"]).read_text()
        start = text.index("/* Address: " + address + " |")
        end = text.find("/* Address:", start + 1)
        return text[start:end if end != -1 else None]

    def test_original_context_metadata_names_search_history_pinboard_in_order(self):
        proof = json.loads((ROOT / "reports/replica/offline-migration-p0-round9.json").read_text())["static_bindings"]
        context = proof["context"]
        descriptor = bytes.fromhex(context["descriptor_bytes"])
        self.assertEqual(struct.unpack_from("<I", descriptor)[0] & 31, 18)  # Enum descriptor
        self.assertEqual(struct.unpack_from("<I", descriptor, 20)[0], 3)  # Three payload cases
        self.assertEqual(struct.unpack_from("<I", descriptor, 24)[0], 0)  # No empty cases
        self.assertEqual(context["field_kind"], 3)
        self.assertEqual(context["record_size"], 12)
        self.assertEqual([r["case"] for r in context["cases"]], ["search", "history", "pinboard"])
        self.assertIn("if (uVar9 >> 0x3e == 0)", self.original("0x100037704"))
        context_provider = self.original("0x10007df7c")
        self.assertLess(context_provider.index("FUN_1002ddcf0()"), context_provider.index("::searchViewModel"))

    def test_original_cancel_clears_query_and_dismisses_search_only_in_search_context(self):
        original = self.original("0x100037704")
        search = body(original, "if (uVar9 >> 0x3e == 0)")
        self.assertLess(search.index("FUN_1002ddf60()"), search.index("Combine::Published::_set_subscript"))
        self.assertLess(search.index("Combine::Published::_set_subscript"), search.index("SearchBar::onDismiss"))
        self.assertNotIn("performClose_", search)
        self.assertIn("objc_stub::performClose_(self,lVar4)", original)
        self.assertIn("PTR___swiftEmptyArrayStorage", self.original("0x1002ddf4c"))

    def test_cancel_search_returns_before_panel_close_and_preserves_board_and_data(self):
        cancel = body(self.ui, "func cancelSearchOrPanel()")
        search = body(cancel, "if !state.isCollectionSearchQueryEmpty")
        expected = ["state.applySearchInput(nodes: [], text: \"\", filters: [])",
                    "state.searchVisible = false", "panel.makeFirstResponder(nil)", "return"]
        self.assertEqual([search.index(t) for t in expected], sorted(search.index(t) for t in expected))
        self.assertNotIn("hidePanel()", search)
        for token in ["chooseBoard(", "pinboardID =", "store.", "showDeleted ="]:
            self.assertNotIn(token, search)
        self.assertTrue(cancel.rstrip().endswith("hidePanel()\n    }"))

    def test_pending_confirmation_still_consumes_escape_before_search(self):
        cancel = body(self.ui, "func cancelSearchOrPanel()")
        self.assertLess(cancel.index("if state.hasPendingDeletion"), cancel.index("guard canDismissPanelForInteraction"))
        self.assertIn("cancelPendingDeletion(); return", cancel)
        handle = body(self.ui, "private func handleKey(_ event: NSEvent)")
        pending = body(handle, "if state.hasPendingDeletion")
        self.assertIn("if event.keyCode == 53 { cancelPendingDeletion(); return true }", pending)

    def test_escape_consumers_reach_same_cancel_entry(self):
        handle = body(self.ui, "private func handleKey(_ event: NSEvent)")
        self.assertIn("cancelSearchOrPanel()", handle)
        install = body(self.ui, "private func installPanelDismissMonitors()")
        self.assertIn("self.cancelSearchOrPanel()", install)
        panel = (ROOT / "replica/Sources/Pasto/UI/PanelViews.swift").read_text()
        self.assertIn("onCancel: { state.controller?.cancelSearchOrPanel() }", panel)

    def test_show_invalidates_close_completion_and_cancels_closed_state(self):
        show = body(self.ui, "func showPanel()")
        order = ["panelTransitionGeneration += 1", "let generation = panelTransitionGeneration",
                 "isPanelClosing = false", "cancelClosedState()", "mainWindowController?.showWindow(nil)"]
        self.assertEqual([show.index(t) for t in order], sorted(show.index(t) for t in order))
        completion = show[show.index("completion:"):]
        self.assertLess(completion.index("generation == self.panelTransitionGeneration"),
                        completion.index("panel.backgroundColor = .windowBackgroundColor"))
        self.assertIn("OriginalViewAnimation.f_10021cadc(duration: 0.15", show)
        self.assertIn("controlPoints: 0.2, 0.8, 0.2, 1", show)
        original = self.original("0x1000192b0")
        self.assertIn("transitionGeneration) + 1", original)
        self.assertIn("FUN_10021cadc(0x3fc3333333333333", original)

    def test_close_guards_and_callbacks_precede_animation(self):
        close = body(self.ui, "func hidePanel()")
        order = ["guard panel.isVisible", "guard !isPanelClosing", "panelTransitionGeneration += 1",
                 "panel.makeFirstResponder(nil)", "beginClosedState()", "isPanelClosing = true",
                 "NotificationCenter.default.post(", "panelWillClose?(",
                 "content.superview?.clipsToBounds = false", "OriginalViewAnimation.f_10021cadc"]
        self.assertEqual([close.index(t) for t in order], sorted(close.index(t) for t in order))
        self.assertIn("OriginalViewAnimation.f_10021cadc(duration: 0.2", close)
        self.assertIn("OriginalViewAnimation.f_10021cf38()", close)
        original = self.original("0x100019a84")
        self.assertIn("lVar2 = _TtC5Paste20MainWindowController::closing", original)
        self.assertLess(original.index("FUN_100021518()"), original.index("*(undefined1 *)(unaff_x20 + lVar2) = 1"))
        self.assertLess(original.index("::onWillClose"), original.index("FUN_10021cadc("))
        self.assertIn("PTR__kCAMediaTimingFunctionEaseInEaseOut", self.original("0x10021cf38"))

    def test_stale_close_completion_cannot_close_reopened_panel(self):
        close = body(self.ui, "func hidePanel()")
        completion = close[close.index("completion:"):]
        order = ["generation == self.panelTransitionGeneration", "self.mainWindowController?.close()",
                 "self.originalPanelScreen = nil", "self.isPanelClosing = false",
                 "content.superview?.clipsToBounds = true"]
        self.assertEqual([completion.index(t) for t in order], sorted(completion.index(t) for t in order))
        original = self.original("0x100019e2c")
        gated = body(original, "if (param_1 == *(long *)(param_2 + _TtC5Paste20MainWindowController::transitionGeneration))")
        self.assertIn('"close"', gated)
        self.assertIn("::originalScreen,0", gated)
        self.assertIn("::closing) = 0", gated)

    def test_closed_search_timeout_is_ten_seconds_and_search_only(self):
        closed = body(self.ui, "private func beginClosedState()")
        self.assertIn("withTimeInterval: 10, repeats: false", closed)
        timeout = closed[closed.index("closedSearchTimer = Timer."):]
        self.assertLess(timeout.index("!self.state.isCollectionSearchQueryEmpty"), timeout.index("applySearchInput(nodes: []"))
        self.assertNotIn("hidePanel()", timeout)
        self.assertIn("FUN_100385984(0x4024000000000000", self.original("0x100021518"))
        self.assertIn("if (uVar7 >> 0x3e == 0)", self.original("0x100021b04"))

    def test_restore_does_not_change_search_or_board_context(self):
        closed = body(self.ui, "private func beginClosedState()")
        restore = closed[closed.index("closedRestoreObservation ="):closed.index("closedSearchTimer = Timer.")]
        self.assertLess(restore.index("self.state.isCollectionSearchQueryEmpty, self.state.pinboardID == nil"),
                        restore.index("self.state.chooseBoard(nil)"))
        self.assertIn("FUN_100021908(0,1)", self.original("0x100021a34"))
        self.assertIn("if (uVar6 >> 0x3e != 1)", self.original("0x100021908"))

    def test_reopen_removes_closed_observers_and_timer_without_clearing_search(self):
        cancel = body(self.ui, "private func cancelClosedState()")
        for token in ["closedSearchTimer?.invalidate()", "closedSearchTimer = nil",
                      "closedCreateObservation?.cancel()",
                      "closedCreateObservation = nil", "closedRestoreObservation?.cancel()",
                      "closedRestoreObservation = nil"]:
            self.assertIn(token, cancel)
        self.assertNotIn("applySearchInput(", cancel)
        self.assertNotIn("chooseBoard(", cancel)

    def test_nil_responder_fallback_is_shared_by_open_close_and_search_cancel(self):
        responder = body(self.ui, "override func makeFirstResponder(_ responder: NSResponder?)")
        self.assertIn("if let responder { return super.makeFirstResponder(responder) }", responder)
        self.assertIn("return super.makeFirstResponder(initialFirstResponder ?? contentView)", responder)
        for signature in ["func showPanel()", "func hidePanel()", "func cancelSearchOrPanel()"]:
            self.assertIn("panel.makeFirstResponder(nil)", body(self.ui, signature))


if __name__ == "__main__":
    unittest.main()
