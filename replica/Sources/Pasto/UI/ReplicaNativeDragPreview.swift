import AppKit

@MainActor
protocol ReplicaNativeDragPreviewCell: AnyObject {
    var snapshotView: NSView { get }
    var isSelected: Bool { get set }
    func flushPreviewRendering()
}

@MainActor
enum ReplicaNativeDragPreview {
    static func image(for cell: any ReplicaNativeDragPreviewCell,
                      singleWriter: Bool) -> NSImage {
        let view = cell.snapshotView
        let wasSelected = cell.isSelected
        let previousOpacity = view.layer?.opacity ?? 1
        defer {
            cell.isSelected = wasSelected
            view.layer?.opacity = previousOpacity
            cell.flushPreviewRendering()
        }
        cell.isSelected = false
        view.layer?.opacity = singleWriter ? 0.8 : 1
        cell.flushPreviewRendering()
        let representation = view.bitmapImageRepForCachingDisplay(in: view.bounds)!
        view.cacheDisplay(in: view.bounds, to: representation)
        let image = NSImage(size: view.bounds.size)
        image.addRepresentation(representation)
        return image
    }

    static func makeItem(writer: any NSPasteboardWriting,
                         draggingFrame: NSRect,
                         visibleCell: (any ReplicaNativeDragPreviewCell)?,
                         singleWriter: Bool) -> NSDraggingItem {
        let item = NSDraggingItem(pasteboardWriter: writer)
        let contents: NSImage?
        if let visibleCell {
            contents = image(for: visibleCell, singleWriter: singleWriter)
        } else {
            contents = nil
        }
        item.setDraggingFrame(draggingFrame, contents: contents)
        return item
    }
}
