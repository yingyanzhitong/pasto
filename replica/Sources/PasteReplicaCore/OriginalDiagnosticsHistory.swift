import AppKit
import UniformTypeIdentifiers

extension OriginalDiagnosticsManager {
    /// The replica's repository creates the file item before history restores it.
    public func f_1002fef28(store: ClipboardStore, pasteboard: NSPasteboard) throws -> UUID? {
        guard let file = f_1002feb60() else { return nil }
        let item = OriginalPasteboardItem()
        item.f_10037c4a8(file.absoluteString, forType: UTType.fileURL.identifier)
        guard let id = try store.capture(pasteboard: pasteboard, sourceName: "Pasto",
                                         sourceBundleID: Bundle.main.bundleIdentifier,
                                         snapshot: [item], respectMonitoringPolicy: false) else {
            throw OriginalPasteboardItemCreationError.emptyContent
        }
        try store.writeToPasteboard(ids: [id], pasteboard: pasteboard)
        return id
    }
}
