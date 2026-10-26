import AppKit

/// Recovered preview colors are weighted by UTF-16 coverage, including uncovered text.
@MainActor
public enum OriginalPreviewTextColors {
    private static let backgroundSlot: UnsafeMutablePointer<NSColor?> = {
        let slot = UnsafeMutablePointer<NSColor?>.allocate(capacity: 1)
        slot.initialize(to: nil)
        return slot
    }()
    private static let backgroundInitialized: Void = f_100219a90()

    public static func f_100219a90() {
        let light = NSColor.white
        let dark = NSColor(red: 20.0 / 255, green: 20.0 / 255, blue: 20.0 / 255, alpha: 1)
        backgroundSlot.pointee = NSColor(name: nil) { appearance in
            OriginalSearchAppearance.f_1001ff49c(appearance: appearance, dark: dark, light: light)
        }
    }

    public static func f_100219bc4() -> UnsafeMutablePointer<NSColor?> {
        _ = backgroundInitialized
        return backgroundSlot
    }

    public static func f_100200560(_ value: Any?, range: NSRange, counts: NSCountedSet) {
        guard let value else { return }
        precondition(range.length >= 0)
        for _ in 0..<range.length { counts.add(value) }
    }

    public static func f_1002006b0(_ value: Any?, range: NSRange, counts: NSCountedSet) {
        f_100200560(value, range: range, counts: counts)
    }

    private static func counts(_ source: NSAttributedString, key: NSAttributedString.Key) -> NSCountedSet {
        let result = NSCountedSet()
        source.enumerateAttribute(key, in: NSRange(location: 0, length: source.length), options: []) { value, range, _ in
            f_1002006b0(value, range: range, counts: result)
        }
        return result
    }

    public static func f_1001ffac0(_ source: NSAttributedString) -> Bool {
        counts(source, key: .foregroundColor).count == 0
    }

    public static func f_100200450(_ colors: inout [(color: NSColor, count: Int)]) {
        colors.sort { $0.count > $1.count }
    }

    public static func f_1002067d4(_ color: NSColor) -> Bool {
        guard let rgb = color.usingColorSpace(.deviceRGB) else { return false }
        let red = rgb.redComponent
        let green = rgb.greenComponent
        let blue = rgb.blueComponent
        _ = rgb.alphaComponent
        return 0.55 < (red * 299 + green * 587 + blue * 114) / 1000
    }

    public static func f_1001ffc58(_ source: NSAttributedString) -> NSColor {
        let backgrounds = counts(source, key: .backgroundColor)
        let foregrounds = counts(source, key: .foregroundColor)
        var backgroundColors: [(color: NSColor, count: Int)] = []
        var backgroundCoverage = 0
        for value in backgrounds {
            let count = backgrounds.count(for: value)
            backgroundColors.append((value as! NSColor, count))
            backgroundCoverage += count
        }
        var foregroundColors: [(color: NSColor, count: Int)] = []
        var foregroundCoverage = 0
        for value in foregrounds {
            let count = foregrounds.count(for: value)
            foregroundColors.append((value as! NSColor, count))
            foregroundCoverage += count
        }
        var dominantForeground = OriginalSearchAppearance.f_1001fec18()!
        foregroundColors.append((dominantForeground, source.length - foregroundCoverage))
        f_100200450(&foregroundColors)
        if let first = foregroundColors.first { dominantForeground = first.color }
        let fallback: NSColor
        if f_1002067d4(dominantForeground) {
            fallback = NSColor(red: 30.0 / 255, green: 30.0 / 255, blue: 30.0 / 255, alpha: 1)
        } else { fallback = .white }
        backgroundColors.append((fallback, source.length - backgroundCoverage))
        f_100200450(&backgroundColors)
        return backgroundColors.first?.color ?? fallback
    }

    /// Paste 0x1003eb4a8: background always changes; foreground changes only when absent.
    @discardableResult
    public static func f_1003eb4a8(original: NSAttributedString, editor: NSTextView) -> Int {
        let isPlain = OriginalPreviewAttributedText.f_1003095bc(original)
        let background: NSColor
        let foreground: NSColor?
        if isPlain {
            background = f_100219bc4().pointee!
            foreground = OriginalSearchAppearance.f_1001fec18()
        } else {
            background = f_1001ffc58(original)
            foreground = f_1001ffac0(original) ? OriginalSearchAppearance.f_1001fec18() : nil
        }
        editor.backgroundColor = background
        if let foreground { editor.textColor = foreground }
        if isPlain, !editor.isEditable { editor.font = OriginalPreviewAttributedText.f_1000f3e48() }
        return 0
    }
}
