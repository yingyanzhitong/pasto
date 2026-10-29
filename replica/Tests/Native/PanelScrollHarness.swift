import AppKit
import Foundation
import PastoCore

@main
struct PanelScrollHarness {
    @MainActor static func main() async throws {
        _ = NSApplication.shared
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent("PastoScroll-\(UUID())")
        defer { try? FileManager.default.removeItem(at: directory) }
        let store = try ClipboardStore(directoryURL: directory)
        store.preferences.historyRetentionDays = 0
        let bitmap = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: 512, pixelsHigh: 512,
            bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false,
            colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
        memset(bitmap.bitmapData!, 128, bitmap.bytesPerRow * bitmap.pixelsHigh)
        let png = bitmap.representation(using: .png, properties: [:])!
        let original = OriginalPasteboardItem()
        original.f_10037d8c8(png, forType: "public.png")
        let metadata = OriginalImagePreviewMetadataGenerator.f_100313548([original])!
        store.items = (0..<120).map {
            ClipboardItem(title: "Generated \($0)", kind: .image, payloads: ["public.png": png], imagePreviewMetadata: metadata)
        }
        precondition(store.items.allSatisfy { $0.decodedImagePreviewMetadata != nil })
        try store.save()
        let ui = ReplicaUIController(store: store)
        defer { ui.panel.orderOut(nil) }
        ui.showPanel()
        if let screen = NSScreen.main { ui.panel.setFrameOrigin(.init(x: screen.frame.maxX + 200, y: screen.frame.maxY + 200)) }
        try await Task.sleep(for: .milliseconds(250))
        func collection(in view: NSView) -> ReplicaNativeCollectionHost? {
            if let view = view as? ReplicaNativeCollectionHost { return view }
            return view.subviews.lazy.compactMap { collection(in: $0) }.first
        }
        let host = collection(in: ui.panel.contentView!)!
        let scroll = host.subviews.first as! NSScrollView
        var samples: [Double] = []
        for cycle in 0..<3 {
            let start = ProcessInfo.processInfo.systemUptime
            for i in 0..<600 {
                let x = CGFloat(i % 200) * 0.25
                scroll.contentView.setBoundsOrigin(.init(x: x, y: 0))
                NotificationCenter.default.post(name: NSView.boundsDidChangeNotification, object: scroll.contentView)
                if i % 30 == 0 { host.layoutSubtreeIfNeeded() }
            }
            let ms = (ProcessInfo.processInfo.systemUptime - start) * 1000
            if cycle > 0 { samples.append(ms) }
        }
        let maxX = scroll.documentView!.frame.width - scroll.contentView.bounds.width
        for i in 0..<40 {
            scroll.contentView.setBoundsOrigin(.init(x: min(maxX, CGFloat(i) * 100), y: 0))
            host.layoutSubtreeIfNeeded()
        }
        precondition(scroll.contentView.bounds.origin.x > 0 && !scroll.documentView!.subviews.isEmpty)
        let visible = ui.state.visibleItems
        for cell in scroll.documentView!.subviews where cell.frame.intersects(scroll.contentView.bounds) {
            let index = Int(((cell.frame.minX - 24) / (cell.frame.width + 24)).rounded())
            precondition(visible.indices.contains(index))
            precondition(host.previewAnchor(for: visible[index].id, revealIfNeeded: false) === cell)
        }
        precondition(host.previewAnchor(for: visible[0].id, revealIfNeeded: false) == nil)
        print(String(decoding: try JSONSerialization.data(withJSONObject: ["passed": true,
            "stationary_viewport_600_changes_ms": samples, "synthetic_image_items":120,
            "scope":"Temporary store, generated images, offscreen native panel; programmatic clip bounds, not physical trackpad or original runtime benchmark."], options:[.sortedKeys]), as:UTF8.self))
    }
}
