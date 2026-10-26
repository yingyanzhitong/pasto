import AppKit
import QuartzCore

@MainActor
public enum OriginalViewLayerFunctions {
    public static func f_10021d024(_ view: NSView) -> NSColor? {
        guard let color = view.layer?.borderColor else { return nil }
        return NSColor(cgColor: color)
    }

    @discardableResult
    public static func f_10021d1cc(_ color: NSColor?, view: NSView) -> Int {
        view.wantsLayer = true
        view.layer?.borderColor = color?.cgColor
        return 0
    }

    @discardableResult
    public static func f_10021d49c(_ radius: CGFloat, curve: CALayerCornerCurve, view: NSView) -> Int {
        view.wantsLayer = true
        view.clipsToBounds = true
        view.layer?.cornerRadius = radius
        view.layer?.cornerCurve = curve
        return 0
    }
}

@MainActor
open class OriginalLayerBackedView: NSView {
    private var storedBackgroundColor: NSColor?

    open var backgroundColor: NSColor? {
        get { f_10023565c() }
        set { f_1002356a8(newValue) }
    }

    public var replicaBorderColor: NSColor? {
        get { OriginalViewLayerFunctions.f_10021d024(self) }
        set { OriginalViewLayerFunctions.f_10021d1cc(newValue, view: self) }
    }

    public override init(frame frameRect: NSRect) {
        super.init(frame: frameRect)
        wantsLayer = true
    }

    public required init?(coder: NSCoder) {
        super.init(coder: coder)
        wantsLayer = true
    }

    public func f_10023565c() -> NSColor? { storedBackgroundColor }

    public func f_1002356a8(_ color: NSColor?) {
        storedBackgroundColor = color
        f_1002359f4()
    }

    public func f_1002359f4() {
        effectiveAppearance.performAsCurrentDrawingAppearance {
            Self.f_1001fe108(self)
        }
    }

    public static func f_1001fe108(_ view: OriginalLayerBackedView) { view.f_100236188() }

    public func f_100236188() {
        if let layer { layer.backgroundColor = backgroundColor?.cgColor }
        if let layer { layer.borderColor = replicaBorderColor?.cgColor }
    }

    public func f_100235f6c() {
        super.viewDidChangeEffectiveAppearance()
        f_1002359f4()
    }

    public func f_1002360c0() { f_100235f6c() }
    open override func viewDidChangeEffectiveAppearance() { f_1002360c0() }
}

@MainActor
public enum OriginalSearchSurfaceAppearance {
    private static let colorSlot: UnsafeMutablePointer<NSColor?> = {
        let slot = UnsafeMutablePointer<NSColor?>.allocate(capacity: 1)
        slot.initialize(to: nil)
        return slot
    }()
    private static let initialized: Void = f_1001fef6c()

    public static func f_1001fef6c() {
        let dark = NSColor.white.withAlphaComponent(0.1)
        let light = NSColor.black.withAlphaComponent(0.1)
        colorSlot.pointee = NSColor(name: nil) { appearance in
            OriginalSearchAppearance.f_1001ff49c(appearance: appearance, dark: dark, light: light)
        }
    }

    public static func f_1001ff0d0() -> UnsafeMutablePointer<NSColor?> {
        _ = initialized
        return colorSlot
    }
}
