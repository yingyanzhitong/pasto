import AppKit
import Combine
import PastoCore

@MainActor
final class PastoAboutWindowController: NSWindowController {
    private let checker: PastoUpdateChecker
    private let installUpdate: () throws -> Void
    private var observation: AnyCancellable?
    let statusLabel = NSTextField(wrappingLabelWithString: "")
    let checkButton = NSButton()
    let downloadButton = NSButton()

    init(checker: PastoUpdateChecker, installUpdate: @escaping () throws -> Void) {
        self.checker = checker
        self.installUpdate = installUpdate
        let window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 360, height: 320),
                              styleMask: [.titled, .closable], backing: .buffered, defer: false)
        window.title = OriginalSettingsLocalization.text("updates.about-title")
        window.identifier = NSUserInterfaceItemIdentifier("pasto-about-window")
        window.isReleasedWhenClosed = false
        window.center()
        super.init(window: window)
        configureContent()
        observation = checker.$state.sink { [weak self] state in
            MainActor.assumeIsolated { self?.refresh(state) }
        }
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    override func showWindow(_ sender: Any?) {
        super.showWindow(sender)
        window?.makeKeyAndOrderFront(sender)
        NSApp.activate(ignoringOtherApps: true)
        Task { await checker.check() }
    }

    private func configureContent() {
        guard let content = window?.contentView else { return }
        let icon = NSImageView()
        icon.image = NSApp.applicationIconImage
        icon.imageScaling = .scaleProportionallyDown
        let name = NSTextField(labelWithString: "Pasto")
        name.font = .systemFont(ofSize: 22, weight: .semibold)
        let version = NSTextField(labelWithString: text("updates.current-version") + " " + checker.currentVersion)
        version.font = .systemFont(ofSize: 13)
        version.textColor = .secondaryLabelColor
        version.setAccessibilityIdentifier("about-current-version")
        let description = NSTextField(labelWithString: text("updates.description"))
        description.font = .systemFont(ofSize: 12)
        description.textColor = .secondaryLabelColor
        let divider = NSBox()
        divider.boxType = .separator
        statusLabel.alignment = .center
        statusLabel.font = .systemFont(ofSize: 12)
        statusLabel.maximumNumberOfLines = 3
        statusLabel.preferredMaxLayoutWidth = 320
        statusLabel.setAccessibilityIdentifier("about-update-status")
        checkButton.title = text("updates.check")
        checkButton.target = self
        checkButton.action = #selector(check)
        checkButton.bezelStyle = .rounded
        checkButton.setAccessibilityIdentifier("about-check-updates")
        downloadButton.title = text("updates.download")
        downloadButton.target = self
        downloadButton.action = #selector(download)
        downloadButton.bezelStyle = .rounded
        downloadButton.bezelColor = .controlAccentColor
        downloadButton.setAccessibilityIdentifier("about-download-update")
        let actions = NSStackView(views: [checkButton, downloadButton])
        actions.spacing = 8
        actions.detachesHiddenViews = true
        let stack = NSStackView(views: [icon, name, version, description, divider, statusLabel, actions])
        stack.orientation = .vertical
        stack.alignment = .centerX
        stack.spacing = 10
        stack.translatesAutoresizingMaskIntoConstraints = false
        content.addSubview(stack)
        NSLayoutConstraint.activate([
            stack.leadingAnchor.constraint(equalTo: content.leadingAnchor, constant: 20),
            stack.trailingAnchor.constraint(equalTo: content.trailingAnchor, constant: -20),
            stack.centerYAnchor.constraint(equalTo: content.centerYAnchor),
            stack.topAnchor.constraint(greaterThanOrEqualTo: content.topAnchor, constant: 20),
            stack.bottomAnchor.constraint(lessThanOrEqualTo: content.bottomAnchor, constant: -20),
            icon.widthAnchor.constraint(equalToConstant: 64),
            icon.heightAnchor.constraint(equalToConstant: 64),
            divider.widthAnchor.constraint(equalTo: stack.widthAnchor),
            statusLabel.widthAnchor.constraint(equalTo: stack.widthAnchor),
            statusLabel.heightAnchor.constraint(equalToConstant: 42)
        ])
    }

    private func refresh(_ state: PastoUpdateChecker.State) {
        checkButton.isEnabled = state != .checking
        downloadButton.isHidden = true
        downloadButton.isEnabled = false
        statusLabel.textColor = .secondaryLabelColor
        switch state {
        case .idle: statusLabel.stringValue = text("updates.check")
        case .checking: statusLabel.stringValue = text("updates.checking")
        case .upToDate: statusLabel.stringValue = text("updates.up-to-date")
        case let .available(update):
            statusLabel.stringValue = text("updates.available") + " " + update.version
            downloadButton.isHidden = false
            downloadButton.isEnabled = true
        case let .failed(message):
            statusLabel.stringValue = message
            statusLabel.textColor = .systemRed
        }
    }

    @objc func check() {
        Task { await checker.check(force: true) }
    }

    @objc func download() {
        guard case .available = checker.state else { return }
        do {
            try installUpdate()
            refresh(checker.state)
        } catch {
            statusLabel.stringValue = error.localizedDescription
            statusLabel.textColor = .systemRed
        }
    }

    private func text(_ key: String) -> String { OriginalSettingsLocalization.text(key) }
}
