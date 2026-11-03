import AppKit
import Foundation
import PastoCore

@MainActor
enum OriginalStackSnippetText {
    /// Paste 0x100051ec8: derive the Stack label from stored preview metadata.
    static func f_100051ec8(_ item: ClipboardItem) -> String {
        label(rawPreview: item.rawPreview) { count in
            OriginalPreviewTitles.f_100308f88(item.originalTitle,
                defaultTitle: defaultTitle(item, fileCount: count))
        }
    }

    static func text(for input: ClipboardRestoreItem) -> String {
        guard input.hasNativeEntity else { return f_100051ec8(input.resolvedItem()) }
        return label(rawPreview: input.previewMetadataData()) { _ in input.previewTitle()!.title }
    }

    private static func label(rawPreview: Data?, filesTitle: (Int) -> String) -> String {
        if let metadata = OriginalImagePreviewMetadataCodec.decodeText(rawPreview) {
            return String(metadata.text.characters)
        }
        if let metadata = OriginalImagePreviewMetadataCodec.decodeLink(rawPreview) {
            return metadata.url.absoluteString
        }
        if OriginalImagePreviewMetadataCodec.decode(rawPreview) != nil { return "Unknown" }
        if let metadata = OriginalImagePreviewMetadataCodec.decodeColor(rawPreview) {
            return OriginalPreviewColorFormatting.f_100206b5c(
                OriginalColorPreviewMetadataGenerator.color(metadata.code))
        }
        if let metadata = OriginalImagePreviewMetadataCodec.decodeFiles(rawPreview) {
            if metadata.paths.count > 1 {
                return filesTitle(metadata.paths.count)
            }
            if let path = metadata.paths.first {
                return URL(fileURLWithPath: path).lastPathComponent
            }
        }
        return "Unknown"
    }

    private static func defaultTitle(_ item: ClipboardItem, fileCount: Int) -> String {
        let rawType: Int
        switch item.kind {
        case .text, .richText: rawType = 5
        case .image: rawType = 1
        case .files: rawType = 3
        case .link: rawType = 4
        case .color: rawType = 2
        case .unknown: rawType = 0
        }
        return OriginalPreviewTitles.f_100309008(rawType: rawType, fileCount: fileCount)
    }
}
