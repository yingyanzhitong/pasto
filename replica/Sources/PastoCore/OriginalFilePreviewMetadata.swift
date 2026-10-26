import AppKit
import Foundation
import QuickLook

public struct OriginalFilePreviewMetadata: Equatable, Sendable {
    public var paths: [String]
    public var totalSize: Int
    public var previewData: Data?

    public init(paths: [String], totalSize: Int, previewData: Data? = nil) {
        self.paths = paths
        self.totalSize = totalSize
        self.previewData = previewData
    }
}

public enum OriginalFilePreviewMetadataGenerator {
    @MainActor
    public static func generate(_ items: [OriginalPasteboardItem],
                                preferQuickLookThumbnails: Bool) -> OriginalFilePreviewMetadata {
        let urls = items.compactMap { $0.f_10037cc6c() }
        let size: Int
        let preview: Data?
        if let first = urls.first {
            size = (try? first.resourceValues(forKeys: [.totalFileSizeKey]))?.totalFileSize ?? 0
            preview = f_100312874(first, preferQuickLookThumbnails: preferQuickLookThumbnails)
        } else {
            size = 0
            preview = nil
        }
        return OriginalFilePreviewMetadata(paths: urls.map(\.path), totalSize: size, previewData: preview)
    }

    @MainActor
    private static func f_100312874(_ url: URL, preferQuickLookThumbnails: Bool) -> Data? {
        if preferQuickLookThumbnails,
           let thumbnail = QLThumbnailImageCreate(kCFAllocatorDefault, url as CFURL,
                                                   CGSize(width: 128, height: 128),
                                                   [kQLThumbnailOptionIconModeKey! as String: true] as CFDictionary) {
            let image = NSImage(cgImage: thumbnail.takeRetainedValue(), size: .zero)
            return OriginalPasteboardImageEncoding.f_1003c89c8(image)
        }
        let image = NSWorkspace.shared.icon(forFile: url.path)
        image.size = NSSize(width: 128, height: 128)
        return OriginalPasteboardImageEncoding.f_1003c89c8(image)
    }
}
