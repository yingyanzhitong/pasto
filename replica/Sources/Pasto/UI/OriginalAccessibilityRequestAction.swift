import AppKit
import ApplicationServices
import IOKit.hidsystem

/// The system action performed by an explicit permission button, separate from modal results.
@MainActor
enum OriginalAccessibilityRequestAction {
    static let settingsURL = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility")!

    static func perform() {
        NSApp.deactivate()
        perform(accessStatus: IOHIDCheckAccess(kIOHIDRequestTypePostEvent), requestAccess: {
            _ = AXIsProcessTrusted()
            _ = IOHIDRequestAccess(kIOHIDRequestTypePostEvent)
        }, openSettings: openSettings)
    }

    static func openSettings(_ url: URL) {
        NSWorkspace.shared.open(url, configuration: NSWorkspace.OpenConfiguration()) { application, _ in
            application?.activate(options: [.activateAllWindows])
        }
    }

    static func perform(accessStatus: IOHIDAccessType, requestAccess: () -> Void, openSettings: (URL) -> Void) {
        if accessStatus == kIOHIDAccessTypeUnknown {
            requestAccess()
        }
        // First use also navigates directly; requesting event access alone may show no settings window.
        openSettings(settingsURL)
    }
}
