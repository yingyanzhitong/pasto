import AppKit
import ApplicationServices
import IOKit.hidsystem

/// The system action performed by an explicit permission button, separate from modal results.
@MainActor
enum OriginalAccessibilityRequestAction {
    static func perform() {
        if IOHIDCheckAccess(kIOHIDRequestTypePostEvent) == kIOHIDAccessTypeUnknown {
            NSApp.deactivate()
            _ = AXIsProcessTrusted()
            _ = IOHIDRequestAccess(kIOHIDRequestTypePostEvent)
        } else {
            let workspace = NSWorkspace.shared
            let url = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility")!
            workspace.open(url)
            workspace.runningApplications.first {
                $0.bundleIdentifier == "com.apple.systempreferences"
            }?.activate(options: [.activateAllWindows])
        }
    }
}
