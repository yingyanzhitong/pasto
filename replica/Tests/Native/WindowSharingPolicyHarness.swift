import AppKit
import Foundation
import PastoCore

@main
struct WindowSharingPolicyHarness {
    @MainActor static func main() throws {
        _ = NSApplication.shared
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: directory) }
        let store = try ClipboardStore(directoryURL: directory)
        let policy = WindowSharingPolicy(store: store)
        let panel = NSPanel(contentRect: .init(x: 0, y: 0, width: 100, height: 100),
                            styleMask: [.borderless], backing: .buffered, defer: false)
        let window = NSWindow(contentRect: .init(x: 0, y: 0, width: 100, height: 100),
                              styleMask: [.titled], backing: .buffered, defer: false)
        policy.apply(to: panel)
        policy.apply(to: window)
        precondition(panel.sharingType == .readOnly && window.sharingType == .readOnly)
        store.preferences.showDuringScreenSharing = false
        RunLoop.main.run(until: Date().addingTimeInterval(0.1))
        precondition(panel.sharingType == .none && window.sharingType == .none)
        let laterWindow = NSWindow(contentRect: .init(x: 0, y: 0, width: 80, height: 80),
                                   styleMask: [.titled], backing: .buffered, defer: false)
        policy.apply(to: laterWindow)
        precondition(laterWindow.sharingType == .none)
        store.preferences.showDuringScreenSharing = true
        RunLoop.main.run(until: Date().addingTimeInterval(0.1))
        precondition([panel, window, laterWindow].allSatisfy { $0.sharingType == .readOnly })
        print("{\"passed\":true,\"checks\":[\"all existing windows follow preferences\",\"new windows follow current policy\"],\"scope\":\"Native NSWindow sharingType state only; no actual screen capture, window display, or system permission changes\"}")
    }
}
