import AppKit

@MainActor
public enum OriginalFilePreviewActions {
    public static func f_1003bc874(_ items: [OriginalPasteboardItem]) {
        let urls = items.compactMap { $0.f_10037cc6c() }
        NSWorkspace.shared.activateFileViewerSelecting(urls)
        NSApp.deactivate()
    }
}
