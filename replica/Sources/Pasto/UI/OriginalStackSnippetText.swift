import AppKit
import Foundation
import PastoCore

@MainActor
enum OriginalStackSnippetText {
    /// Paste 0x100051ec8: derive the Stack label from stored preview metadata.
    static func f_100051ec8(_ item: ClipboardItem) -> String {
        if let metadata = OriginalImagePreviewMetadataCodec.decodeText(item.rawPreview) {
            return String(metadata.text.characters)
        }
        if let metadata = OriginalImagePreviewMetadataCodec.decodeLink(item.rawPreview) {
            return metadata.url.absoluteString
        }
        if OriginalImagePreviewMetadataCodec.decode(item.rawPreview) != nil { return "Unknown" }
        if let metadata = OriginalImagePreviewMetadataCodec.decodeColor(item.rawPreview) {
            return OriginalPreviewColorFormatting.f_100206b5c(
                OriginalColorPreviewMetadataGenerator.color(metadata.code))
        }
        if let metadata = OriginalImagePreviewMetadataCodec.decodeFiles(item.rawPreview) {
            if metadata.paths.count > 1 {
                return OriginalPreviewTitles.f_100308f88(item.originalTitle,
                    defaultTitle: defaultTitle(item, fileCount: metadata.paths.count))
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
