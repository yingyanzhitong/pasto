import AppKit
import Foundation

public enum OriginalStackCategoryIcons {
    // 0x100051d2c: these are category images, independent of the source application.
    public static func name(for kind: OriginalPasteboardContentKind) -> String {
        switch kind {
        case .files: return "icon.file"
        case .color, .text: return "icon.text"
        case .link: return "icon.link"
        case .unknown, .image: return "icon.unknown"
        }
    }

    @MainActor private static let resources: Bundle = {
        guard let url = OriginalResourceBundle.bundle.url(forResource: "OriginalStackIcons", withExtension: "bundle"),
              let bundle = Bundle(url: url) else { preconditionFailure("Missing Stack icon resource bundle") }
        return bundle
    }()

    @MainActor public static func image(for kind: OriginalPasteboardContentKind) -> NSImage {
        let assetName = name(for: kind)
        guard let image = resources.image(forResource: NSImage.Name(assetName)) else {
            preconditionFailure("Missing Stack category image: \(assetName)")
        }
        image.isTemplate = true
        return image
    }
}
