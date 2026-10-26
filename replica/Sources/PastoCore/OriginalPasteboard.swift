import AppKit
import Foundation
import UniformTypeIdentifiers

/// The original item stores an ordered type list separately from its data map.
/// In particular, repeated writes append a type even when replacing its data.
public final class OriginalPasteboardItem: NSObject, Codable, NSSecureCoding {
    private var orderedTypes: [String] = []
    private var dataByType: [String: Data] = [:]

    public override init() { super.init() }

    public static var supportsSecureCoding: Bool { f_10037f314() }
    public static func f_10037f314() -> Bool { true }

    public required init?(coder: NSCoder) {
        super.init()
        guard let types = coder.decodeArrayOfObjects(ofClass: NSString.self, forKey: "types") as? [String],
              let values = coder.decodeDictionary(withKeyClass: NSString.self, objectClass: NSData.self,
                                                 forKey: "dataByType") as? [String: Data] else { return nil }
        orderedTypes = types
        dataByType = values
    }

    public func f_10037f520(with coder: NSCoder) {
        coder.encode(orderedTypes as NSArray, forKey: "types")
        coder.encode(dataByType as NSDictionary, forKey: "dataByType")
    }

    public func encode(with coder: NSCoder) {
        f_10037f520(with: coder)
    }

    private enum CodingKeys: String, CodingKey { case types, dataByType }

    public required init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        orderedTypes = try container.decode([String].self, forKey: .types)
        dataByType = try container.decode([String: Data].self, forKey: .dataByType)
        super.init()
    }

    public func f_10037df78(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(orderedTypes, forKey: .types)
        try container.encode(dataByType, forKey: .dataByType)
    }

    public func encode(to encoder: Encoder) throws {
        try f_10037df78(to: encoder)
    }

    public static func f_10037c6d4(_ string: String) -> OriginalPasteboardItem {
        let item = OriginalPasteboardItem()
        item.f_10037c4a8(string, forType: UTType.utf8PlainText.identifier)
        return item
    }

    public static func f_10037c7bc(_ url: URL, title: String?) -> OriginalPasteboardItem {
        let item = OriginalPasteboardItem()
        item.f_10037c4a8(url.absoluteString, forType: UTType.utf8PlainText.identifier)
        item.f_10037c4a8(url.absoluteString, forType: UTType.url.identifier)
        if let title { item.f_10037c4a8(title, forType: "public.url-name") }
        return item
    }

    public func f_10037c4a8(_ string: String, forType type: String) {
        f_10037d8c8(string.data(using: .utf8, allowLossyConversion: false), forType: type)
    }

    public func f_10037d810(forType type: String) -> Data? {
        dataByType[type]
    }

    public func f_10037d8c8(_ data: Data?, forType type: String) {
        orderedTypes.append(type)
        dataByType[type] = data
    }

    public func f_10037e6b0(_ value: Any, forType type: String) {
        if let data = value as? Data {
            f_10037d8c8(data, forType: type)
        } else if let string = value as? String {
            f_10037c4a8(string, forType: type)
        } else if let string = value as? NSAttributedString {
            f_10037c4a8(string.string, forType: type)
        } else if let url = value as? URL {
            f_10037c4a8(url.absoluteString, forType: type)
        } else if let image = value as? NSImage {
            f_10037d8c8(OriginalPasteboardImageEncoding.f_1003c89c8(image), forType: type)
        }
    }

    public func f_10037da6c() -> [String] { orderedTypes }

    public func f_10037dab0(_ type: String) {
        orderedTypes.removeAll { $0 == type }
        dataByType.removeValue(forKey: type)
    }

    public func f_100383574(removingTypesContaining patterns: [String]) {
        for type in orderedTypes where patterns.contains(where: { type.contains($0) }) {
            f_10037dab0(type)
        }
    }

    public func f_1003838bc() {
        f_10037d8c8(Data(), forType: "com.wiheads.paste")
    }

    public func f_10037e4b8(forType type: String) -> String? {
        guard let data = f_10037d810(forType: type) else { return nil }
        return String(data: data, encoding: .utf8)
    }

    public func f_10037e5e0(forType type: String) -> NSData? {
        f_10037d810(forType: type).map { $0 as NSData }
    }

    public func f_10037c9a8() -> String? {
        for type in [UTType.plainText, .utf8PlainText, .text, .url] {
            if let string = f_10037e4b8(forType: type.identifier) { return string }
        }
        return nil
    }

    public func f_10037cc6c() -> URL? {
        guard let string = f_10037e4b8(forType: UTType.fileURL.identifier) else { return nil }
        return URL(string: string)
    }

    public func f_10037ce0c() -> URL? {
        if let string = f_10037e4b8(forType: UTType.url.identifier), let url = URL(string: string) {
            return url
        }
        var allowed = CharacterSet(charactersIn: "#")
        allowed.formUnion(.urlQueryAllowed)
        allowed.formUnion(.urlFragmentAllowed)
        guard let string = f_10037c9a8(), let encoded = string.addingPercentEncoding(withAllowedCharacters: allowed),
              let url = URL(string: encoded), url.scheme != nil, url.host != nil else { return nil }
        return url
    }

    public func f_10037d210() -> String? {
        f_10037e4b8(forType: "public.url-name")
    }

    public func f_10037cd68() -> NSImage? {
        f_10037d5c4().flatMap(NSImage.init(data:))
    }

    public func f_10037d5c4() -> Data? {
        for type in [UTType.png, .jpeg, .heic, .tiff, .icns] {
            if let data = f_10037d810(forType: type.identifier) { return data }
        }
        return nil
    }

    public func f_10037ebdc(_ types: [UTType]) -> NSAttributedString? {
        for type in types {
            guard let data = f_10037d810(forType: type.identifier) else { continue }
            if let string = NSAttributedString(rtfd: data, documentAttributes: nil) { return string }
            if let string = NSAttributedString(rtf: data, documentAttributes: nil) { return string }
            if let string = try? NSAttributedString(data: data, options: [:], documentAttributes: nil) {
                return string
            }
        }
        return nil
    }

    public func f_10037d33c() -> NSAttributedString? {
        guard let rich = f_10037ebdc([.flatRTFD, .rtfd, .rtf]) else {
            return f_10037c9a8().map { NSAttributedString(string: $0) }
        }
        let result = NSMutableAttributedString(attributedString: rich)
        result.enumerateAttributes(in: NSRange(location: 0, length: result.length)) { attributes, range, _ in
            Self.f_100309924(attributes: attributes, range: range, string: result)
        }
        return result
    }

    public static func f_100309924(attributes: [NSAttributedString.Key: Any], range: NSRange,
                                    string: NSMutableAttributedString) {
        guard let paragraph = attributes[.paragraphStyle] as? NSParagraphStyle,
              let mutable = paragraph.mutableCopy() as? NSMutableParagraphStyle else { return }
        mutable.textBlocks = []
        string.addAttribute(.paragraphStyle, value: mutable, range: range)
    }
}

/// Source function 0x10037875c has no filtering, empty-input guard, generated
/// marker, or write-failure branch. Those policies belong to its callers.
@MainActor
public final class OriginalPasteboardWriter {
    public let pasteboard: NSPasteboard
    public private(set) var lastChangeCount: Int
    public private(set) var lastWriteSucceeded = false

    public init(pasteboard: NSPasteboard) {
        self.pasteboard = pasteboard
        self.lastChangeCount = pasteboard.changeCount
    }

    public func f_10037875c(_ items: [OriginalPasteboardItem]) {
        let objects = items.map { item -> NSPasteboardItem in
            let object = NSPasteboardItem()
            for type in item.f_10037da6c() {
                if let data = item.f_10037e5e0(forType: type) {
                    object.setData(data as Data, forType: NSPasteboard.PasteboardType(type))
                }
            }
            return object
        }
        pasteboard.clearContents()
        lastWriteSucceeded = pasteboard.writeObjects(objects)
        lastChangeCount = pasteboard.changeCount
        OriginalPasteboardCaptureState.current(for: pasteboard)?.lastChangeCount = lastChangeCount
    }
}
