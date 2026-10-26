import AppKit

@MainActor
public enum OriginalToolbarAppearance {
    private static let secondary: NSColor = {
        let light = NSColor.black.withAlphaComponent(0.5)
        let dark = NSColor.white.withAlphaComponent(0.55)
        return NSColor(name: nil) { OriginalSearchAppearance.f_1001ff49c(appearance: $0, dark: dark, light: light) }
    }()
    private static let border: NSColor = {
        let light = NSColor.black.withAlphaComponent(0.05)
        let dark = NSColor.white.withAlphaComponent(0.05)
        return NSColor(name: nil) { OriginalSearchAppearance.f_1001ff49c(appearance: $0, dark: dark, light: light) }
    }()
    private static let label = NSColor.labelColor
    private static let secondaryLabel = NSColor.secondaryLabelColor
    public static func secondaryForeground() -> NSColor { secondary }
    public static func borderAndHover() -> NSColor { border }
    public static func labelForeground() -> NSColor { label }
    public static func secondaryLabelForeground() -> NSColor { secondaryLabel }
}

/// The recovered layered NSButton, used by the preview's native editing controls.
@MainActor
public final class OriginalToolbarButton: NSButton {
    public enum Size: UInt8 { case normal = 0, large = 1 }
    public var symbol: String? { didSet { f_10023ce40() } }
    public var hasPullDownArrow = false { didSet { f_10023ce40() } }
    public var isPrimary = false { didSet { f_10023d784() } }
    public var isSelected = false { didSet { f_10023d784() } }
    public let size: Size
    public var buttonAction: (OriginalToolbarButton) -> Void
    private var isHovered = false
    private var isPressed = false
    private var storedIconView: NSImageView?
    private var storedTitleLabel: NSTextField?
    private var recoveredTrackingArea: NSTrackingArea?
    private let pullDownArrowView: NSImageView
    private let stackView: NSStackView

    public init(symbol: String? = nil, title: String = "", size: Size = .normal,
                shortcut: OriginalShortcutValue? = nil,
                toolTip: String? = nil, action: @escaping (OriginalToolbarButton) -> Void) {
        self.symbol = symbol
        self.size = size
        buttonAction = action
        pullDownArrowView = NSImageView(image: Self.requiredImage("chevron.down"))
        pullDownArrowView.contentTintColor = OriginalSearchAppearance.f_1001fec18()
        stackView = NSStackView()
        stackView.orientation = .horizontal
        stackView.spacing = 4
        stackView.distribution = .fillProportionally
        stackView.alignment = .centerY
        super.init(frame: .zero)
        super.title = title
        f_10023ce40()
        isTransparent = true
        wantsLayer = true
        target = self
        self.action = #selector(performAction)
        stackView.translatesAutoresizingMaskIntoConstraints = false
        addSubview(stackView)
        NSLayoutConstraint.activate(f_10023e080())
        if let shortcut {
            keyEquivalent = OriginalShortcutFunctions.f_1001e8098(keyCode: shortcut.keyCode)
            keyEquivalentModifierMask = .init(rawValue: shortcut.internalModifiers)
        }
        if let toolTip {
            self.toolTip = shortcut.map { toolTip + " (" + $0.description + ")" } ?? toolTip
        }
        f_10023ce40()
        f_10023d784()
    }

    public required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    private static func requiredImage(_ symbol: String) -> NSImage {
        if NSImage(systemSymbolName: symbol, accessibilityDescription: nil) == nil {
            return NSImage(systemSymbolName: "questionmark.square", accessibilityDescription: nil)!
        }
        return NSImage(systemSymbolName: symbol, accessibilityDescription: nil)!
    }

    public func f_10023cc80() -> NSImageView {
        if let storedIconView { return storedIconView }
        let view = NSImageView()
        storedIconView = view
        return view
    }

    public func f_10023deb4() -> NSTextField {
        if let storedTitleLabel { return storedTitleLabel }
        let view = NSTextField(labelWithString: "")
        view.font = NSFont.preferredFont(forTextStyle: size == .normal ? .body : .title3, options: [:])
        view.alignment = .right
        storedTitleLabel = view
        return view
    }

    public override var contentTintColor: NSColor? {
        get { super.contentTintColor }
        set {
            super.contentTintColor = newValue
            f_10023cc80().contentTintColor = super.contentTintColor
        }
    }

    public override var title: String {
        get { super.title }
        set { super.title = newValue; f_10023ce40() }
    }

    public override var isEnabled: Bool {
        get { super.isEnabled }
        set { super.isEnabled = newValue; f_10023d784() }
    }

    public func f_10023ce40() {
        let icon = f_10023cc80()
        if let symbol {
            icon.image = Self.requiredImage(symbol).withSymbolConfiguration(
                NSImage.SymbolConfiguration(textStyle: size == .normal ? .body : .title2))
            stackView.addArrangedSubview(icon)
        } else {
            icon.image = nil
            icon.removeFromSuperview()
        }
        let label = f_10023deb4()
        if super.title.isEmpty {
            label.stringValue = ""
            label.removeFromSuperview()
        } else {
            label.stringValue = super.title
            stackView.addArrangedSubview(label)
        }
        if hasPullDownArrow { stackView.addArrangedSubview(pullDownArrowView) }
        else { pullDownArrowView.removeFromSuperview() }
    }

    public func f_10023fb74(padding: CGFloat) -> [NSLayoutConstraint] {
        [stackView.leadingAnchor.constraint(equalTo: leadingAnchor, constant: padding),
         stackView.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -padding)]
    }

    public func f_10023e080() -> [NSLayoutConstraint] {
        var result: [NSLayoutConstraint]
        if size == .large {
            result = [widthAnchor.constraint(equalToConstant: 32), heightAnchor.constraint(equalToConstant: 32)]
        } else {
            result = [heightAnchor.constraint(equalToConstant: 22), widthAnchor.constraint(greaterThanOrEqualToConstant: 32)]
        }
        result += f_10023fb74(padding: size == .large ? 0 : 8)
        result += [stackView.centerYAnchor.constraint(equalTo: centerYAnchor),
                   pullDownArrowView.widthAnchor.constraint(equalToConstant: 8),
                   pullDownArrowView.heightAnchor.constraint(equalToConstant: 8)]
        return result
    }

    public func f_10023d784() {
        layer?.borderWidth = super.title.isEmpty ? 0 : 1
        if #available(macOS 26, *) { layer?.cornerRadius = bounds.height * 0.5 }
        else { layer?.cornerRadius = size == .normal ? 5 : 6 }
        effectiveAppearance.performAsCurrentDrawingAppearance { self.f_10023f230() }
    }

    private func applyForeground(_ color: NSColor) {
        f_10023deb4().textColor = color
        pullDownArrowView.contentTintColor = color
        f_10023cc80().contentTintColor = super.contentTintColor ?? color
    }

    public func f_10023f230() {
        if isPrimary {
            let effect: NSColor.SystemEffect = !super.isEnabled ? .disabled : (isPressed ? .pressed : .none)
            layer?.backgroundColor = NSColor.controlAccentColor.withSystemEffect(effect).cgColor
            applyForeground(NSColor.white.withSystemEffect(effect))
            return
        }
        layer?.backgroundColor = NSColor.clear.cgColor
        let base: NSColor
        if #available(macOS 26, *) { base = OriginalSearchAppearance.f_1001fec18()! }
        else { base = OriginalToolbarAppearance.secondaryForeground() }
        applyForeground(base)
        layer?.borderColor = super.title.isEmpty ? nil : OriginalToolbarAppearance.borderAndHover().cgColor
        if !super.isEnabled {
            applyForeground(OriginalToolbarAppearance.secondaryLabelForeground().withSystemEffect(.disabled))
        } else if isPressed {
            layer?.backgroundColor = OriginalSearchSurfaceAppearance.f_1001ff0d0().pointee?.withAlphaComponent(0.15).cgColor
            applyForeground(isSelected ? OriginalToolbarAppearance.secondaryLabelForeground() : OriginalToolbarAppearance.labelForeground())
        } else if isSelected {
            layer?.backgroundColor = OriginalSearchSurfaceAppearance.f_1001ff0d0().pointee?.cgColor
            applyForeground(OriginalToolbarAppearance.labelForeground())
        } else if isHovered {
            layer?.backgroundColor = OriginalToolbarAppearance.borderAndHover().cgColor
        }
    }

    public override func updateLayer() { f_10023d784() }

    public override func updateTrackingAreas() {
        super.updateTrackingAreas()
        if let recoveredTrackingArea { removeTrackingArea(recoveredTrackingArea) }
        let area = NSTrackingArea(rect: bounds, options: .init(rawValue: 0x481), owner: self, userInfo: nil)
        recoveredTrackingArea = area
        addTrackingArea(area)
        isHovered = NSEvent.pressedMouseButtons == 0 && bounds.contains(convert(NSEvent.mouseLocation, from: nil))
        f_10023d784()
        isPressed = false
        f_10023d784()
    }

    public override func mouseEntered(with event: NSEvent) {
        super.mouseEntered(with: event)
        isHovered = true
        f_10023d784()
    }

    public override func mouseExited(with event: NSEvent) {
        super.mouseExited(with: event)
        isHovered = false
        f_10023d784()
        isPressed = false
        f_10023d784()
    }

    public override func mouseDown(with event: NSEvent) {
        isPressed = true
        f_10023d784()
        super.mouseDown(with: event)
        isPressed = false
        f_10023d784()
    }

    public override func viewDidChangeEffectiveAppearance() {
        super.viewDidChangeEffectiveAppearance()
        f_10023d784()
    }

    @objc public func performAction() { buttonAction(self) }
}
