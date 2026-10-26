import AppKit

@MainActor
public enum OriginalSelectionAppearance {
    public static func f_100218b08(_ color: NSColor) -> NSColor {
        let converted = color.usingColorSpace(.sRGB) ?? color
        guard converted.colorSpace.colorSpaceModel == .rgb else { return color }
        return converted.usingColorSpace(.genericGray) ?? color
    }
}
