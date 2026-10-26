import AppKit
import UniformTypeIdentifiers

@MainActor
public enum OriginalPreviewSharing {
    public struct Content {
        public let items: [OriginalPasteboardItem]
        public let rawType: Int
        public init(items: [OriginalPasteboardItem], rawType: Int) {
            self.items = items
            self.rawType = rawType
        }
    }

    /// Paste 0x1003202f0: keep data-item order and discard missing representations.
    public static func f_1003202f0(items: [OriginalPasteboardItem], rawType: Int) -> [Any] {
        switch rawType {
        case 1: return items.compactMap { $0.f_10037d5c4().flatMap(NSImage.init(data:)) }
        case 2, 5: return items.compactMap { $0.f_10037c9a8() }
        case 3:
            return items.compactMap { item -> URL? in
                guard let data = item.f_10037d810(forType: UTType.fileURL.identifier),
                      let string = String(data: data, encoding: .utf8) else { return nil }
                return URL(string: string)
            }
        case 4: return items.compactMap { $0.f_10037ce0c() }
        default: return []
        }
    }

    /// Paste 0x100320cc0: file sharing additionally requires reachable local URLs.
    public static func f_100320cc0(_ content: Content) -> Bool {
        switch content.rawType {
        case 1, 2, 4, 5:
            return !f_1003202f0(items: content.items, rawType: content.rawType).isEmpty
        case 3:
            let urls = f_1003202f0(items: content.items, rawType: content.rawType).compactMap { $0 as? URL }
            return !urls.isEmpty && urls.allSatisfy {
                $0.isFileURL && (try? $0.checkResourceIsReachable()) == true
            }
        default:
            return false
        }
    }

    /// The picker consumes a flattened sequence, without starting any network work.
    public static func f_1000183e0(_ contents: [Content]) -> NSSharingServicePicker {
        NSSharingServicePicker(items: contents.flatMap { f_1003202f0(items: $0.items, rawType: $0.rawType) })
    }
}
