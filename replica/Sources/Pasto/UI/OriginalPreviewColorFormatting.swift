import AppKit
import Foundation

@MainActor
enum OriginalPreviewColorFormatting {
    /// Paste 0x100206b5c returns lowercase RGB; its display callers uppercase the result.
    static func f_100206b5c(_ color: NSColor) -> String {
        var red: CGFloat = 0
        var green: CGFloat = 0
        var blue: CGFloat = 0
        if let rgb = color.usingColorSpace(.deviceRGB) {
            red = rgb.redComponent
            green = rgb.greenComponent
            blue = rgb.blueComponent
            _ = rgb.alphaComponent
        }
        // Int preserves truncation and the original nonfinite/out-of-range traps.
        // The reference neither clamps components nor appends the alpha channel.
        let redText = String(format: "%02x", Int(red * 255))
        let greenText = String(format: "%02x", Int(green * 255))
        let blueText = String(format: "%02x", Int(blue * 255))
        return "#" + redText + greenText + blueText
    }
}
