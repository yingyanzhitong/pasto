import AppKit

/// The native text-field wrapper used by the recovered preview title.
@MainActor
public final class OriginalPreviewTextField: NSView, NSTextFieldDelegate {
    public var onDidEndEditing: (() -> Void)?
    private var storedTextField: NSTextField?

    public init() {
        super.init(frame: .zero)
        let field = f_10023adf0()
        field.translatesAutoresizingMaskIntoConstraints = false
        addSubview(field)
        NSLayoutConstraint.activate([
            field.leadingAnchor.constraint(equalTo: leadingAnchor),
            field.trailingAnchor.constraint(equalTo: trailingAnchor),
            field.topAnchor.constraint(equalTo: topAnchor),
            field.bottomAnchor.constraint(equalTo: bottomAnchor)
        ])
    }

    public required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    /// Paste 0x10023adf0: initialize and configure the platform field exactly once.
    public func f_10023adf0() -> NSTextField {
        if let storedTextField { return storedTextField }
        let field = NSTextField()
        f_10023b954(field)
        storedTextField = field
        return field
    }

    /// Paste 0x10023b954: these defaults precede the preview title's own appearance.
    public func f_10023b954(_ field: NSTextField) {
        field.delegate = self
        field.isBordered = false
        field.isEditable = false
        field.drawsBackground = false
        field.usesSingleLineMode = true
        field.allowsExpansionToolTips = true
        field.allowsDefaultTighteningForTruncation = true
        field.maximumNumberOfLines = 1
        field.lineBreakMode = .byTruncatingTail
        field.alignment = .natural
        field.focusRingType = .none
    }

    /// PastePlatform 0x1000f6874: NSTextField.text reads stringValue.
    public func f_1000f6874() -> String { f_10023adf0().stringValue }

    /// PastePlatform 0x1000f69b0: a nil text becomes an empty stringValue.
    @discardableResult
    public func f_1000f69b0(_ value: String?) -> Int {
        f_10023adf0().stringValue = value ?? ""
        return 0
    }

    public func f_10023b1a4() -> String? { f_1000f6874() }

    @discardableResult
    public func f_10023b214(_ value: String?) -> Int { f_1000f69b0(value) }

    public func f_10023b3e0() -> Bool { f_10023adf0().isEditable }

    public func f_10023b578() -> String? { f_10023adf0().placeholderAttributedString?.string }

    @discardableResult
    public func f_10023b600(_ value: String?) -> Int {
        let field = f_10023adf0()
        field.placeholderAttributedString = value.map {
            NSAttributedString(string: $0, attributes: [
                .foregroundColor: field.textColor?.withAlphaComponent(0.6) ?? NSColor.textColor,
                .font: field.font ?? NSFont.preferredFont(forTextStyle: .title3, options: [:])
            ])
        }
        return 0
    }

    @discardableResult
    public func f_10023af6c(_ color: NSColor?) -> Int {
        let field = f_10023adf0()
        field.textColor = color
        f_10023b600(f_10023b578())
        return 0
    }

    @discardableResult
    public func f_10023b414(_ value: Bool) -> Int {
        f_10023adf0().isEditable = value
        return 0
    }

    /// Paste 0x10023c01c: reapply current text, then invalidate the wrapper's size.
    public func f_10023c01c() {
        let value = f_1000f6874()
        f_1000f69b0(value)
        invalidateIntrinsicContentSize()
    }

    /// Paste 0x10023bfdc: retain abortEditing's result and refresh intrinsic sizing.
    @discardableResult
    public func f_10023bfdc() -> Bool {
        let result = f_10023adf0().abortEditing()
        f_10023c01c()
        return result
    }

    public func f_10023c56c() { onDidEndEditing?() }

    public func controlTextDidEndEditing(_ obj: Notification) { f_10023c56c() }

    public func controlTextDidChange(_ obj: Notification) { f_10023c01c() }

    public override var acceptsFirstResponder: Bool { f_10023adf0().acceptsFirstResponder }
    public override func resignFirstResponder() -> Bool { f_10023adf0().resignFirstResponder() }

    public override func becomeFirstResponder() -> Bool {
        f_10023c304()
    }

    public func f_10023c304() -> Bool {
        let field = f_10023adf0()
        let result = field.becomeFirstResponder()
        if let editor = field.currentEditor() as? NSTextView {
            // The SDK declares this property nonnull, but the original forwards
            // the nullable NSTextField.textColor without an extra nil branch.
            let selector = NSSelectorFromString("setInsertionPointColor:")
            typealias Setter = @convention(c) (NSTextView, Selector, NSColor?) -> Void
            let setter = unsafeBitCast(editor.method(for: selector)!, to: Setter.self)
            setter(editor, selector, field.textColor)
        }
        return result
    }

    public override var intrinsicContentSize: NSSize {
        let field = f_10023adf0()
        let height = field.intrinsicContentSize.height
        let width = field.sizeThatFits(NSSize(width: CGFloat.infinity, height: height)).width
        return NSSize(width: width.rounded(.toNearestOrAwayFromZero), height: height)
    }
}

/// Paste PreviewHeader.TitleLabel's edit, cancel and commit state machine.
@MainActor
public final class OriginalPreviewTitleLabel: NSView {
    public var onCommitEditing: ((String) -> Void)?
    private var storedTextField: OriginalPreviewTextField?
    private var originalText: String?

    public init() {
        super.init(frame: .zero)
        let field = f_100013084()
        addSubview(field)
        f_100013404(field)
    }

    public required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    public func f_100013084() -> OriginalPreviewTextField {
        if let storedTextField { return storedTextField }
        let field = OriginalPreviewTextField()
        f_1000130fc(field)
        storedTextField = field
        return field
    }

    public func f_1000130fc(_ field: OriginalPreviewTextField) {
        field.onDidEndEditing = { [weak self] in self?.f_100013240() }
        field.f_10023af6c(OriginalSearchAppearance.f_1001fec18())
        field.alphaValue = 0.8
        field.f_10023adf0().font = NSFont.preferredFont(forTextStyle: .headline, options: [:])
    }

    public func f_100013404(_ field: OriginalPreviewTextField) {
        field.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            field.leadingAnchor.constraint(equalTo: leadingAnchor),
            field.trailingAnchor.constraint(equalTo: trailingAnchor),
            field.topAnchor.constraint(equalTo: topAnchor),
            field.bottomAnchor.constraint(equalTo: bottomAnchor)
        ])
    }

    @discardableResult
    public func f_100011c78() -> Int {
        let field = f_100013084()
        originalText = field.f_10023b1a4()
        field.f_10023b414(true)
        field.window?.makeFirstResponder(field)
        return 0
    }

    @discardableResult
    public func f_100011d28() -> Int {
        let field = f_100013084()
        field.f_10023b414(false)
        field.f_10023b214(originalText)
        field.f_10023bfdc()
        field.window?.makeFirstResponder(nil)
        return 0
    }

    public func f_100013240() {
        let field = f_100013084()
        field.f_10023b414(false)
        field.window?.makeFirstResponder(nil)
        if let onCommitEditing { onCommitEditing(field.f_10023b1a4()!) }
    }

    public override func mouseDown(with event: NSEvent) {
        if !f_100013084().f_10023b3e0() { f_100011c78() }
        else { super.mouseDown(with: event) }
    }
}
