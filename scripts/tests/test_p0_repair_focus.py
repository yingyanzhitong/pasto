from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
APP_MAIN = ROOT / "replica/Sources/Pasto/AppMain.swift"
UI_CONTROLLER = ROOT / "replica/Sources/Pasto/UI/ReplicaUIController.swift"


def swift_method(source: str, signature: str, next_signature: str) -> str:
    start = source.index(signature)
    end = source.index(next_signature, start + len(signature))
    return source[start:end]


class P0FocusRepairTests(unittest.TestCase):
    def test_frontmost_pasto_does_not_fall_back_to_old_target(self):
        source = APP_MAIN.read_text()
        body = swift_method(
            source,
            "    private func rememberPanelApplication()",
            "    private func restorePanelApplication(",
        )
        self.assertIn("if app?.processIdentifier != ProcessInfo.processInfo.processIdentifier", body)
        self.assertIn("handoffPreviousApplication = app", body)
        self.assertNotIn("handoffPreviousApplication = targetApplication", body)

    def test_close_attempts_activation_for_saved_terminated_application(self):
        source = APP_MAIN.read_text()
        body = swift_method(
            source,
            "    private func restorePanelApplication(restore: Bool)",
            "    private func ",
        )
        self.assertIn("defer { handoffPreviousApplication = nil }", body)
        self.assertIn("guard restore, let previous = handoffPreviousApplication", body)
        self.assertNotIn("previous.isTerminated", body)
        self.assertIn("previous.activate(options: .activateIgnoringOtherApps)", body)

    def test_panel_callbacks_reach_the_two_repaired_gates(self):
        app_main = APP_MAIN.read_text()
        ui = UI_CONTROLLER.read_text()
        self.assertIn("ui.panelDidShow = { [weak self] in self?.rememberPanelApplication() }", app_main)
        self.assertIn("ui.panelWillClose = { [weak self] restore in self?.restorePanelApplication(restore: restore) }", app_main)
        self.assertIn("self.panelDidShow?()", ui)
        self.assertIn("panelWillClose?(previewRegistry.windows.isEmpty)", ui)


if __name__ == "__main__":
    unittest.main()
