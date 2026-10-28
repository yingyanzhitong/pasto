import AppKit
import Foundation
import SwiftUI
import PastoCore
import PastoObjC
import IOKit.hidsystem

@main
struct AccessibilityModalHarness {
    struct Failure: Error, CustomStringConvertible { let description: String }

    static func require(_ condition: @autoclosure () -> Bool, _ message: String) throws {
        if !condition() { throw Failure(description: message) }
    }

    @MainActor static func main() {
        do { try run() }
        catch {
            let result: [String: Any] = ["passed": false, "error": String(describing: error)]
            print(String(data: try! JSONSerialization.data(withJSONObject: result), encoding: .utf8)!)
            exit(1)
        }
    }

    @MainActor static func settle(_ view: NSView) {
        view.layoutSubtreeIfNeeded()
        view.window?.displayIfNeeded()
        RunLoop.main.run(until: Date().addingTimeInterval(0.2))
        view.layoutSubtreeIfNeeded()
    }

    @MainActor static func glass(above view: NSView) -> NSView? {
        var candidate: NSView? = view.superview
        while let current = candidate {
            if NSStringFromClass(type(of: current)) == "NSGlassEffectView" { return current }
            candidate = current.superview
        }
        return nil
    }

    @MainActor static func run() throws {
        let app = NSApplication.shared
        app.setActivationPolicy(.accessory)
        app.finishLaunching()
        let session = AccessibilityModalSession(initialResult: 2,
            styleMask: [.titled, .fullSizeContentView], animation: 5, material: 6)
        session.window.backgroundColor = .clear
        defer { session.window.orderOut(nil) }
        var results: [UInt8] = []
        let preview = ProcessInfo.processInfo.environment["PASTO_MODAL_PREVIEW"] == "1"
        var settingsNavigationEnabled = false
        func install() {
            session.setContent(PasteToOtherAppsContent(appName: "文本编辑") {
                results.append($0)
                if preview { print("ACTION \($0)"); fflush(stdout) }
                if settingsNavigationEnabled && $0 == 2 {
                    OriginalAccessibilityRequestAction.openSettings(OriginalAccessibilityRequestAction.settingsURL)
                }
            }, alertContainer: true)
        }
        install()
        let initialHost = session.window.contentView!
        settle(initialHost)
        var nativeGlass = false
        if #available(macOS 26, *) {
            try require(session.window is PRGlassBackgroundWindow, "Tahoe modal is not a glass window")
            guard let firstGlass = glass(above: initialHost) else {
                throw Failure(description: "Hosting content has no native NSGlassEffectView ancestor")
            }
            try require(firstGlass.value(forKey: "contentView") as? NSView === initialHost,
                        "Glass contentView does not contain the hosting view")
            try require((firstGlass.value(forKey: "cornerRadius") as? NSNumber)?.doubleValue == 26,
                        "Original glass corner radius is not 26")
            try require(session.window.toolbar?.allowsDisplayModeCustomization == false &&
                        session.window.toolbar?.allowsUserCustomization == false &&
                        session.window.toolbar?.displayMode == .labelOnly &&
                        session.window.toolbarStyle == .unified, "Original toolbar configuration differs")
            install()
            let replacementHost = session.window.contentView!
            settle(replacementHost)
            try require(replacementHost !== initialHost && glass(above: replacementHost) === firstGlass,
                        "Replacing content discarded the glass surface")
            try require(firstGlass.value(forKey: "contentView") as? NSView === replacementHost,
                        "Replacement content was not forwarded into glass")
            nativeGlass = true
            try require(!session.window.isOpaque, "Glass window must not leave an opaque rectangular backing")
        }
        guard let container = session.window.contentView as? OriginalAlertContentHostingView<PasteToOtherAppsContent> else {
            throw Failure(description: "Original native alert content wrapper is missing")
        }
        let host = container.host
        session.window.title = "Test Pasto Permission"
        let screens = NSScreen.screens
        session.window.setFrameOrigin(NSPoint(x: (screens.map { $0.frame.maxX }.max() ?? 0) + 200,
                                              y: (screens.map { $0.frame.maxY }.max() ?? 0) + 200))
        session.window.makeKeyAndOrderFront(nil)
        settle(host)
        try require(abs(host.bounds.width - 280) < 1 && host.bounds.height > 160,
                    "Natural modal content size is invalid: \(host.bounds)")
        try require(session.window.alphaValue == 1, "Modal must not fade all content via window alpha")
        try require(PasteToOtherAppsContent.illustration?.size == NSSize(width: 280, height: 160),
                    "Original hero illustration was not loaded at 280×160 points")
        func key(_ characters: String, _ code: UInt16, result: UInt8) throws -> Bool {
            let event = NSEvent.keyEvent(with: .keyDown, location: .zero, modifierFlags: [], timestamp: 0,
                windowNumber: session.window.windowNumber, context: nil, characters: characters,
                charactersIgnoringModifiers: characters, isARepeat: false, keyCode: code)!
            let before = results.count
            let handled = host.performKeyEquivalent(with: event)
            settle(host)
            if results.count > before {
                try require(results.count == before + 1 && results.last == result,
                            "Keyboard action \(code) returned an unexpected result")
            }
            return handled && results.count == before + 1
        }
        let returnVerified = try key("\r", 36, result: 2)
        let escapeVerified = try key("\u{1b}", 53, result: 0)
        try require(returnVerified && escapeVerified, "Default and cancel keyboard actions must both execute")
        for status in [kIOHIDAccessTypeUnknown, kIOHIDAccessTypeDenied, kIOHIDAccessTypeGranted] {
            var actions: [String] = []
            OriginalAccessibilityRequestAction.perform(accessStatus: status, requestAccess: {
                actions.append("request")
            }, openSettings: { url in
                actions.append(url.absoluteString)
            })
            let expected = (status == kIOHIDAccessTypeUnknown ? ["request"] : []) +
                ["x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"]
            try require(actions == expected, "Permission button must open Accessibility settings for status \(status)")
        }
        let report: [String: Any] = ["passed": true, "native_glass": nativeGlass,
            "content_size": [host.bounds.width, host.bounds.height], "window_is_opaque": session.window.isOpaque,
            "action_results": results.map(Int.init), "return_key_verified": returnVerified,
            "escape_key_verified": escapeVerified,
            "control_ax_status": "unavailable in local hosting accessibility tree; not verified",
            "chinese_text_clipping_status": "not verified; requires visible preview inspection",
            "checked_copy_result_1_status": "not verified; requires visible preview checkbox/action",
            "checks": ["native glass content replacement retains surface", "original toolbar and radius 26",
                       "hero resource and natural content size", "all permission states navigate to Accessibility settings"],
            "limits": ["Real offscreen window and local key-equivalent attempts only; no runModal, permission request, system settings or cross-process AX action",
                       "No screenshot or backdrop transparency acceptance in the default run"]]
        print(String(data: try JSONSerialization.data(withJSONObject: report, options: [.sortedKeys]), encoding: .utf8)!)
        fflush(stdout)
        if preview {
            install()
            settingsNavigationEnabled = ProcessInfo.processInfo.environment["PASTO_MODAL_OPEN_SETTINGS"] == "1"
            let delegate = ModalPreviewDelegate()
            session.window.delegate = delegate
            app.setActivationPolicy(.accessory)
            session.window.center()
            session.window.makeKeyAndOrderFront(nil)
            app.activate(ignoringOtherApps: true)
            print("PREVIEW " + Bundle.main.bundlePath + " windowNumber=" + String(session.window.windowNumber))
            fflush(stdout)
            let timer = Timer.scheduledTimer(withTimeInterval: 90, repeats: false) { _ in NSApp.terminate(nil) }
            app.run()
            withExtendedLifetime((timer, delegate, session)) {}
        }
    }
}

@MainActor
private final class ModalPreviewDelegate: NSObject, NSWindowDelegate {
    func windowWillClose(_ notification: Notification) { NSApp.terminate(nil) }
}
