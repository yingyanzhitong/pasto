import AppKit

@MainActor
public final class OriginalSearchTextScroller: NSScrollView {
    public var focusRingBounds: NSRect = .zero

    /// REA 0x100042edc: dedicated document-view initializer.
    public init(textView: OriginalSearchTextView) {
        super.init(frame: .zero)
        hasHorizontalScroller = false
        hasVerticalScroller = false
        drawsBackground = false
        focusRingType = .none
        borderType = .noBorder
        documentView = textView
        textView.f_100042fc8()
    }

    public required init?(coder: NSCoder) {
        fatalError("init(coder:) is unavailable for OriginalSearchTextScroller")
    }

    public override init(frame frameRect: NSRect) {
        fatalError("init(frame:) is unavailable for OriginalSearchTextScroller")
    }

    public func f_100043344() -> NSRect { focusRingBounds }
    public override var focusRingMaskBounds: NSRect { f_100043344() }

    public func f_100043418() {
        let radius: CGFloat
        if #available(macOS 26, *) { radius = focusRingBounds.height * 0.5 }
        else { radius = 6 }
        let path = NSBezierPath(roundedRect: focusRingBounds, xRadius: radius, yRadius: radius)
        NSColor.black.set()
        path.fill()
    }

    public func f_1000434f8() {
        OriginalSearchTextView.f_100043508(self) { $0.f_100043418() }
    }
    public override func drawFocusRingMask() { f_1000434f8() }
}
