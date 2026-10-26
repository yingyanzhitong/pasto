import AppKit

@MainActor
open class OriginalSearchInputView: NSView, NSTextStorageDelegate {
    public var onClear: (() -> Void)?
    public var focusRingBounds: NSRect = .zero
    public private(set) var isClearButtonVisible = false
    private var storedTextView: OriginalSearchTextView?
    private var storedScroller: OriginalSearchTextScroller?
    private var storedClearButton: NSButton?

    open func makeTextView() -> OriginalSearchTextView {
        OriginalSearchTextView(usingTextLayoutManager: true)
    }

    public func f_100041f9c() -> OriginalSearchTextView {
        if let storedTextView { return storedTextView }
        let textView = makeTextView()
        storedTextView = textView
        return textView
    }

    public func f_10004200c() -> OriginalSearchTextScroller {
        if let storedScroller { return storedScroller }
        let scroll = OriginalSearchTextScroller(textView: f_100041f9c())
        storedScroller = scroll
        return scroll
    }

    public func f_100042090() -> NSButton {
        if let storedClearButton { return storedClearButton }
        let button = NSButton()
        f_10004212c(button)
        storedClearButton = button
        return button
    }

    public func f_10004212c(_ button: NSButton) {
        // Preserve the original availability probe followed by a second load.
        let image: NSImage
        if NSImage(systemSymbolName: "xmark.circle.fill", accessibilityDescription: nil) != nil {
            image = NSImage(systemSymbolName: "xmark.circle.fill", accessibilityDescription: nil)!
        } else {
            image = NSImage(systemSymbolName: "questionmark.square", accessibilityDescription: nil)!
        }
        button.image = image
        button.action = #selector(clear)
        button.target = self
        button.refusesFirstResponder = true
        button.isBordered = false
    }

    public override init(frame frameRect: NSRect) {
        super.init(frame: frameRect)
        for view in [f_10004200c(), f_100042090()] as [NSView] {
            addSubview(view)
            view.translatesAutoresizingMaskIntoConstraints = false
        }
        NSLayoutConstraint.activate(f_1000424e8().flatMap { $0 })
        f_100041f9c().textStorage?.delegate = self
        let button = f_100042090()
        button.isEnabled = false
        button.isHidden = true
        button.alphaValue = 0
        f_1000449e8()
    }

    public required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    public func f_1000424e8() -> [[NSLayoutConstraint]] {
        let scroll = f_10004200c()
        let clear = f_100042090()
        return [
            [scroll.topAnchor.constraint(equalTo: topAnchor)],
            [scroll.leadingAnchor.constraint(equalTo: leadingAnchor)],
            [scroll.bottomAnchor.constraint(equalTo: bottomAnchor)],
            [clear.widthAnchor.constraint(equalToConstant: 16),
             clear.heightAnchor.constraint(equalToConstant: 16)],
            [clear.centerYAnchor.constraint(equalTo: centerYAnchor)],
            [clear.leadingAnchor.constraint(equalTo: scroll.trailingAnchor, constant: 4)],
            [clear.trailingAnchor.constraint(equalTo: trailingAnchor)]
        ]
    }

    public func f_1000429d0() {
        if let window { window.makeFirstResponder(f_100041f9c()) }
        onClear?()
    }

    public func f_100042a68() {
        OriginalSearchTextView.f_100043508(self) { $0.f_1000429d0() }
    }
    @objc public func clear() { f_100042a68() }

    @discardableResult
    public func f_100042d64() -> Int {
        f_100042090().animator().alphaValue = 1
        return 0
    }

    @discardableResult
    public func f_100042db0() -> Int {
        f_100042090().animator().alphaValue = 0
        return 0
    }

    @discardableResult
    public static func f_100042dfc(_ input: OriginalSearchInputView?) -> Int {
        if let input, !input.isClearButtonVisible { input.f_100042090().isHidden = true }
        return 0
    }

    public func f_100042b50() {
        let visible = !f_100041f9c().string.isEmpty
        guard isClearButtonVisible != visible else { return }
        isClearButtonVisible = visible
        f_100042090().isEnabled = visible
        if visible {
            f_100042090().isHidden = false
            OriginalViewAnimation.f_10021cadc(duration: 0.12,
                timingFunction: OriginalViewAnimation.f_10021ccd4(), animated: true) {
                _ = self.f_100042d64()
            }
        } else {
            OriginalViewAnimation.f_10021cadc(duration: 0.12,
                timingFunction: OriginalViewAnimation.f_10021ccd4(), animated: true) {
                _ = self.f_100042db0()
            } completion: { [weak self] in
                _ = Self.f_100042dfc(self)
            }
        }
    }

    public func f_1000449e8() {
        f_100042b50()
        let textView = f_100041f9c()
        textView.f_1000436a0().isHidden = !textView.string.isEmpty
        let hasAttachments = textView.textStorage?.containsAttachments ?? false
        textView.textContainerInset = NSSize(width: 0, height: hasAttachments ? 0 : 2)
    }

    public func f_100042a78() { f_1000449e8() }
    nonisolated public func textStorage(_ textStorage: NSTextStorage, didProcessEditing editedMask: NSTextStorageEditActions,
                            range editedRange: NSRange, changeInLength delta: Int) {
        MainActor.assumeIsolated { f_100042a78() }
    }
}
