import AppKit
import PastoCore
import SwiftUI

/// Local stored link values. Original card configuration and outer layout remain separate.
@MainActor
struct ReplicaLinkMetadataContent: View {
    let metadata: OriginalLinkPreviewMetadata
    let compact: Bool
    let linkPreviewsEnabled: Bool
    var cardSizeClass: UInt8? = nil

    var body: some View {
        let image = metadata.imageData.flatMap(NSImage.init(data:))
        VStack(alignment: .leading, spacing: 0) {
            if linkPreviewsEnabled {
                Group {
                    if let cardSizeClass {
                        let hasMainImage = image.map { $0.size.width != $0.size.height } ?? false
                        OriginalLinkPreviewViewport(image: hasMainImage ? image : nil,
                            icon: hasMainImage ? nil : image ?? metadata.iconData.flatMap(NSImage.init(data:)) ?? fallbackIcon(),
                            sizeClass: cardSizeClass)
                    } else if let image, image.size.width != image.size.height {
                        Image(nsImage: image).resizable().scaledToFit()
                    } else if let icon = image ?? metadata.iconData.flatMap(NSImage.init(data:)) ?? fallbackIcon() {
                        Image(nsImage: icon).resizable().scaledToFit()
                            .frame(width: 42, height: 42)
                    }
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
            VStack(alignment: .leading, spacing: 3) {
                if let name = metadata.name {
                    Text(name)
                        .font(Font(NSFont.systemFont(ofSize: OriginalSearchAppearance.f_1001ff928().pointSize,
                                                     weight: .semibold)))
                        .foregroundStyle(Color(nsColor: OriginalSearchAppearance.f_1001fec18() ?? .labelColor))
                        .lineLimit(linkPreviewsEnabled ? 1 : 3)
                }
                Text(linkPreviewsEnabled ? OriginalLinkDisplay.formattedURL(metadata.url) : metadata.url.absoluteString)
                    .font(Font(NSFont.preferredFont(forTextStyle: .callout, options: [:])))
                    .foregroundStyle(Color(nsColor: OriginalToolbarAppearance.secondaryForeground()))
                    .lineLimit(linkPreviewsEnabled ? (metadata.name == nil ? 2 : 1) : nil)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.vertical, 10)
            .padding(.horizontal, 12)
            .background {
                if cardSizeClass != nil { Color(nsColor: OriginalLinkPreviewSurface.startingColor) }
            }
        }
        .help(metadata.url.absoluteString)
    }

    private func fallbackIcon() -> NSImage? {
        let image = NSImage(systemSymbolName: "safari", accessibilityDescription: nil)
            ?? NSImage(systemSymbolName: "questionmark.square", accessibilityDescription: nil)!
        let configuration = NSImage.SymbolConfiguration(pointSize: 42, weight: .regular)
            .applying(NSImage.SymbolConfiguration(paletteColors: [OriginalToolbarAppearance.secondaryForeground()]))
        return image.withSymbolConfiguration(configuration)
    }
}
