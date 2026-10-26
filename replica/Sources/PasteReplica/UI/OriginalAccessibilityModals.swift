import AppKit
import Combine
import IOKit.hidsystem
import PasteReplicaCore
import SwiftUI

@MainActor
enum OriginalPasteToOtherAppsModal {
    static func run() -> UInt8 {
        let session = AccessibilityModalSession(initialResult: 2, styleMask: [.titled, .fullSizeContentView],
                                                animation: 5, material: 6)
        session.window.backgroundColor = .clear
        let appName = NSWorkspace.shared.menuBarOwningApplication?.localizedName
            ?? OriginalSettingsLocalization.text("general.current-app")
        session.setContent(PasteToOtherAppsContent(appName: appName) { [weak session] in session?.complete($0) })
        return session.run()
    }
}

@MainActor
enum OriginalEnableAccessibilityModal {
    static func run() -> UInt8 {
        let session = AccessibilityModalSession(initialResult: 1,
                                                styleMask: [.titled, .closable, .fullSizeContentView],
                                                animation: 3, material: 21)
        let model = EnableAccessibilityModel { [weak session] in session?.complete($0) }
        session.setContent(EnableAccessibilityContent(model: model))
        session.window.setContentSize(NSSize(width: 544, height: 680))
        model.window = session.window
        model.begin()
        let result = session.run()
        model.stop()
        return result
    }
}

@MainActor
private final class AccessibilityModalSession: NSObject, NSWindowDelegate {
    let window: NSWindow
    private var result: UInt8

    init(initialResult: UInt8, styleMask: NSWindow.StyleMask, animation: Int, material: Int) {
        result = initialResult
        window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 100, height: 100),
                          styleMask: styleMask, backing: .buffered, defer: false)
        super.init()
        window.isReleasedWhenClosed = false
        window.isMovableByWindowBackground = true
        window.titleVisibility = .hidden
        window.titlebarAppearsTransparent = true
        window.animationBehavior = .init(rawValue: animation)!
        if #unavailable(macOS 26) {
            let firstEffect = {
                self.window.contentView?.superview?.subviews.compactMap { $0 as? NSVisualEffectView }.first
            }
            firstEffect()?.material = .init(rawValue: material)!
            firstEffect()?.blendingMode = .behindWindow
            firstEffect()?.state = .active
        }
        window.delegate = self
    }

    func setContent<Content: View>(_ content: Content) {
        let host = NSHostingView(rootView: content)
        window.contentView = host
        window.setContentSize(host.fittingSize)
    }

    func run() -> UInt8 {
        window.center()
        window.makeKeyAndOrderFront(nil)
        NSApp.runModal(for: window)
        return result
    }

    func complete(_ value: UInt8) {
        result = value
        window.close()
    }

    func windowWillClose(_ notification: Notification) {
        NSApp.stopModal()
    }
}

@MainActor
private struct PasteToOtherAppsContent: View {
    let appName: String
    let complete: (UInt8) -> Void
    @State private var doNotAskAgain = false

    var body: some View {
        VStack(spacing: 32) {
            VStack(spacing: 8) {
                Text(String(format: OriginalSettingsLocalization.text("accessibility-access.paste-to-other-apps.title"), appName))
                    .font(.title2.bold())
                Text(ReplicaBrand.replacingOriginalName(in: OriginalSettingsLocalization.text("accessibility-access.paste-to-other-apps.description")))
                    .font(.body)
            }
            .multilineTextAlignment(.center)
            VStack(spacing: 8) {
                VStack(spacing: 16) {
                    Button { complete(2) } label: {
                        Text(OriginalSettingsLocalization.text("accessibility-access.paste-to-other-apps.enable-accessibility-access"))
                            .frame(maxWidth: .infinity)
                    }
                    .keyboardShortcut(.defaultAction)
                    Button { complete(doNotAskAgain ? 1 : 0) } label: {
                        Text(OriginalSettingsLocalization.text("accessibility-access.paste-to-other-apps.copy-to-clipboard"))
                            .frame(maxWidth: .infinity)
                    }
                    .keyboardShortcut(.cancelAction)
                }
                .buttonStyle(.bordered)
                .controlSize(.large)
                Toggle(OriginalSettingsLocalization.text("general.do-not-ask-again"), isOn: $doNotAskAgain)
            }
        }
        .padding([.leading, .bottom, .trailing], 16)
        .frame(width: 280)
    }
}

@MainActor
private final class EnableAccessibilityModel: ObservableObject {
    @Published var isAccessRequested: Bool
    @Published var isAccessEnabled = false
    weak var window: NSWindow?
    private let service = OriginalAccessibilityService()
    private var observation: AnyCancellable?
    private let complete: (UInt8) -> Void

    init(complete: @escaping (UInt8) -> Void) {
        self.complete = complete
        isAccessRequested = IOHIDCheckAccess(kIOHIDRequestTypePostEvent) != kIOHIDAccessTypeUnknown
    }

    func begin() {
        let subscription = service.f_100ae5e90().sink { [weak self] enabled in
            MainActor.assumeIsolated {
                guard let self, enabled, !self.isAccessEnabled else { return }
                self.stop()
                NSApp.activate(ignoringOtherApps: true)
                self.isAccessEnabled = true
                self.window?.level = NSWindow.Level(rawValue: 8)
                self.window?.styleMask.remove(.closable)
                Task { @MainActor [weak self] in
                    try? await Task.sleep(for: .seconds(1))
                    self?.complete(0)
                }
            }
        }
        if isAccessEnabled { subscription.cancel() }
        else { observation = subscription }
    }

    func request() {
        OriginalAccessibilityRequestAction.perform()
        Task { @MainActor [weak self] in
            self?.window?.level = .normal
            self?.isAccessRequested = true
        }
    }

    func stop() {
        observation?.cancel()
        observation = nil
    }
}

@MainActor
private struct EnableAccessibilityContent: View {
    @ObservedObject var model: EnableAccessibilityModel

    var body: some View {
        VStack {
            Spacer()
            if model.isAccessEnabled {
                Image(systemName: "checkmark.circle")
                    .font(.system(size: 64))
                    .foregroundStyle(.green)
            } else {
                Image(nsImage: NSApp.applicationIconImage)
                    .resizable(resizingMode: .stretch)
                    .frame(width: 80, height: 80)
                    .padding(.bottom, 8)
                Text(OriginalSettingsLocalization.text("accessibility-access.enable-accessibility-access.title"))
                    .font(.title.bold())
                Text(ReplicaBrand.replacingOriginalName(in: OriginalSettingsLocalization.text("accessibility-access.enable-accessibility-access.subtitle")))
                    .font(.body)
                    .multilineTextAlignment(.center)
                Button(action: model.request) {
                    Text(OriginalSettingsLocalization.text(model.isAccessRequested
                        ? "accessibility-access.enable-accessibility-access.open-system-settings"
                        : "accessibility-access.enable-accessibility-access.allow-access"))
                        .padding(.horizontal, 8)
                }
                .keyboardShortcut(.defaultAction)
            }
            Spacer()
        }
        .frame(width: 544, height: 680)
    }
}
