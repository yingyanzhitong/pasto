import AppKit
import Foundation

public enum OriginalPasteboardRestore {
    public struct Options: OptionSet {
        public let rawValue: UInt8
        public init(rawValue: UInt8) { self.rawValue = rawValue }
        public static let plainOtherContent = Options(rawValue: 1 << 0)
        public static let plainTextAndLinks = Options(rawValue: 1 << 1)
        public static let plainText: Options = [.plainOtherContent, .plainTextAndLinks]
    }

    public struct Selection {
        public let kind: OriginalPasteboardContentKind
        public let items: [OriginalPasteboardItem]
        public let sourceBundleID: String?

        public init(kind: OriginalPasteboardContentKind, items: [OriginalPasteboardItem], sourceBundleID: String?) {
            self.kind = kind
            self.items = items
            self.sourceBundleID = sourceBundleID
        }
    }

    public static func usesPlainProjection(kind: OriginalPasteboardContentKind, options: Options) -> Bool {
        options.contains(kind == .text || kind == .link ? .plainTextAndLinks : .plainOtherContent)
    }

    /// Value portion of the original entity processor; callers supply decoded/prepared items.
    public static func f_10038222c(_ selections: [Selection], options: Options,
                                  removingTypesContaining ignoredTypes: [String]) -> [[OriginalPasteboardItem]] {
        let multiple = selections.count > 1
        let aggregatesText = selections.contains { $0.kind == .text || $0.kind == .link }
        var groups: [[OriginalPasteboardItem]] = []
        var contents: [NSAttributedString] = []
        for selection in selections {
            let items = usesPlainProjection(kind: selection.kind, options: options)
                ? f_10031bcdc(selection.items) : selection.items
            for item in items {
                item.f_100383574(removingTypesContaining: ignoredTypes)
                item.f_10037c4a8(selection.sourceBundleID ?? "", forType: "org.nspasteboard.source")
                item.f_1003838bc()
            }
            if !multiple { return [items] }
            if aggregatesText {
                contents.append(contentsOf: items.compactMap { $0.f_10037d33c() })
                groups.append([])
            } else {
                groups.append(items)
            }
        }
        let combined = f_100383a0c(separator: "\n", contents: contents)
        if combined.length > 0 {
            let aggregate = OriginalPasteboardItem()
            aggregate.f_1003838bc()
            if !options.contains(.plainTextAndLinks), let data = f_100381fdc(combined) {
                aggregate.f_10037d8c8(data, forType: "public.rtf")
            } else {
                aggregate.f_10037c4a8(combined.string, forType: "public.utf8-plain-text")
            }
            groups.insert([aggregate], at: 0)
        }
        return groups
    }

    /// The original entity getter first decodes ItemData; this is its array projection.
    public static func f_10031bcdc(_ items: [OriginalPasteboardItem]) -> [OriginalPasteboardItem] {
        items.compactMap { $0.f_10037c9a8() }.map(OriginalPasteboardItem.f_10037c6d4)
    }

    public static func f_100383a0c(separator: String, contents: [NSAttributedString]) -> NSMutableAttributedString {
        let result = NSMutableAttributedString(string: "")
        for content in contents {
            if !result.string.isEmpty { result.append(NSAttributedString(string: separator)) }
            result.append(content)
        }
        return result
    }

    public static func f_100381fdc(_ content: NSAttributedString) -> Data? {
        try? content.data(from: NSRange(location: 0, length: content.length), documentAttributes: [
            .documentType: NSAttributedString.DocumentType.rtf,
            .characterEncoding: String.Encoding.utf8
        ])
    }
}
