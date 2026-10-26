import AppKit

/// The writer owns the identifier source and reads it for each item-ID request.
/// A replica UUID snapshot adapter does not claim original CoreData identity.
public protocol OriginalDragItemIdentifierSource: AnyObject {
    var pasteboardIdentifier: String { get }
}

public final class OriginalNativeDragPasteboardWriter: NSObject, NSPasteboardWriting {
    public static let itemIdentifierType = NSPasteboard.PasteboardType("com.wiheads.paste.item-id")

    private let source: any OriginalDragItemIdentifierSource
    private let pasteboardItems: [OriginalPasteboardItem]

    public init(source: any OriginalDragItemIdentifierSource, pasteboardItems: [OriginalPasteboardItem]) {
        self.source = source
        self.pasteboardItems = pasteboardItems
        super.init()
    }

    @MainActor
    public static func writers(sources: [any OriginalDragItemIdentifierSource],
                               groups: [[OriginalPasteboardItem]]) -> [OriginalNativeDragPasteboardWriter] {
        zip(sources, groups).map { source, items in
            OriginalNativeDragPasteboardWriter(source: source, pasteboardItems: items)
        }
    }

    public func writableTypes(for pasteboard: NSPasteboard) -> [NSPasteboard.PasteboardType] {
        var types = pasteboardItems.flatMap { item in
            item.f_10037da6c().map { NSPasteboard.PasteboardType($0) }
        }
        types.append(Self.itemIdentifierType)
        return types
    }

    public func pasteboardPropertyList(forType type: NSPasteboard.PasteboardType) -> Any? {
        if type == Self.itemIdentifierType { return source.pasteboardIdentifier }
        for item in pasteboardItems {
            if let data = item.f_10037d810(forType: type.rawValue) { return data }
        }
        return nil
    }
}
