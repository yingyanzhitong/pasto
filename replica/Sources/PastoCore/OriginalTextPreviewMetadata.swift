import AppKit
import Foundation

public struct OriginalTextPreviewMetadata: Equatable, Sendable {
    public var length: Int
    public var text: AttributedString

    public init(length: Int, text: AttributedString) {
        self.length = length
        self.text = text
    }
}

public enum OriginalTextPreviewMetadataGenerator {
    @MainActor
    public static func generate(_ items: [OriginalPasteboardItem]) -> OriginalTextPreviewMetadata? {
        guard let source = items.first?.f_10037d33c() else { return nil }
        let length = source.length
        let sample = length > 500
            ? source.attributedSubstring(from: NSRange(location: 0, length: 500)) : source
        return OriginalTextPreviewMetadata(length: length, text: AttributedString(sample))
    }
}
