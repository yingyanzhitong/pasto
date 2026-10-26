import AppKit
import Foundation

public struct OriginalColorPreviewMetadata: Equatable, Sendable {
    public var code: UInt64

    public init(code: UInt64) { self.code = code }
}

public enum OriginalColorPreviewMetadataGenerator {
    public static func generate(_ items: [OriginalPasteboardItem]) -> OriginalColorPreviewMetadata? {
        guard let text = items.first?.f_10037c9a8() else { return nil }
        let scanner = Scanner(string: text.replacingOccurrences(of: "#", with: ""))
        var code: UInt64 = 0
        guard scanner.scanHexInt64(&code) else { return nil }
        return OriginalColorPreviewMetadata(code: code)
    }

    @MainActor
    public static func color(_ code: UInt64) -> NSColor {
        let alpha = code >> 24 == 0 ? 1 : CGFloat((code >> 24) & 255) / 255
        return NSColor(red: CGFloat((code >> 16) & 255) / 255,
                       green: CGFloat((code >> 8) & 255) / 255,
                       blue: CGFloat(code & 255) / 255, alpha: alpha)
    }
}
