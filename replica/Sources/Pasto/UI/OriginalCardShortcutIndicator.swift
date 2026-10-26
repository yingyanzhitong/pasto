import AppKit
import PastoCore

@MainActor
final class OriginalCardShortcutIndicatorView: OriginalLayerBackedView {
    private let plainTextIndicator: NSImageView
    private let quickPasteIndicator = NSTextField(labelWithString: "")
    private var index: Int?
    private var enabled = true
    private var provider: (() -> (plain: UInt, quick: UInt))?
    private var textColor = OriginalToolbarAppearance.secondaryForeground()
    private var modifierMonitor: Any?
    private var keyWindowObserver: NSObjectProtocol?

    override init(frame frameRect: NSRect) {
        let image: NSImage
        if NSImage(systemSymbolName: "text.justify.leading", accessibilityDescription: nil) == nil {
            image = NSImage(systemSymbolName: "questionmark.square", accessibilityDescription: nil)!
        } else {
            image = NSImage(systemSymbolName: "text.justify.leading", accessibilityDescription: nil)!
        }
        let configuration = NSImage.SymbolConfiguration(textStyle: .footnote)
        plainTextIndicator = NSImageView(image: image.withSymbolConfiguration(configuration) ?? image)
        super.init(frame: frameRect)

        quickPasteIndicator.font = NSFont.preferredFont(forTextStyle: .callout, options: [:])
        OriginalViewLayerFunctions.f_10021d49c(4, curve: .circular, view: self)
        backgroundColor = OriginalPreviewTextColors.f_100219bc4().pointee!
        let stack = NSStackView(views: [plainTextIndicator, quickPasteIndicator])
        stack.orientation = .horizontal
        stack.spacing = 4
        addSubview(stack)
        stack.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            stack.topAnchor.constraint(equalTo: topAnchor, constant: 0.5),
            stack.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 4),
            stack.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -0.5),
            stack.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -4),
            stack.heightAnchor.constraint(equalToConstant: 18)
        ])
        modifierMonitor = NSEvent.addLocalMonitorForEvents(matching: .flagsChanged) { [weak self] event in
            MainActor.assumeIsolated { self?.refresh() }
            return event
        }
        keyWindowObserver = NotificationCenter.default.addObserver(
            forName: NSWindow.didBecomeKeyNotification, object: window, queue: nil
        ) { [weak self] _ in
            MainActor.assumeIsolated { self?.refresh() }
        }
        refresh()
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    func configure(index: Int?, isEnabled: Bool, provider: (() -> (plain: UInt, quick: UInt))?,
                   textColor: NSColor) {
        self.index = index
        enabled = isEnabled
        self.provider = provider
        self.textColor = textColor
        refresh()
    }

    private func refresh() {
        plainTextIndicator.contentTintColor = textColor.withAlphaComponent(0.65)
        quickPasteIndicator.textColor = textColor
        quickPasteIndicator.stringValue = index.map(String.init) ?? ""
        guard enabled, let provider else {
            isHidden = true
            return
        }
        let modifiers = provider()
        let modifierFlags = NSEvent.modifierFlags.rawValue
        plainTextIndicator.isHidden = modifiers.plain & ~modifierFlags != 0
        quickPasteIndicator.isHidden = modifiers.quick & ~modifierFlags != 0 || index == nil
        isHidden = plainTextIndicator.isHidden && quickPasteIndicator.isHidden
    }

    deinit {
        MainActor.assumeIsolated {
            if let modifierMonitor { NSEvent.removeMonitor(modifierMonitor) }
            if let keyWindowObserver { NotificationCenter.default.removeObserver(keyWindowObserver) }
        }
    }
}
