import AppKit
import PastoCore
import SwiftUI

/// Compact card values only. The independent full preview keeps its own content chain.
@MainActor
struct ReplicaCanonicalCardContent: View {
    let item: ClipboardItem
    let sizeClass: UInt8

    var body: some View {
        Group {
            switch item.kind {
            case .image:
                if let metadata = item.decodedImagePreviewMetadata {
                    ZStack(alignment: .bottom) {
                        ReplicaCardCheckerboard()
                        if let image = NSImage(data: metadata.previewData) {
                            ReplicaAdaptiveScalingImage(image: image)
                        }
                        if sizeClass != 3 {
                            Text(String(format: "%d × %d", Int(metadata.width), Int(metadata.height)))
                                .font(Font(NSFont.preferredFont(forTextStyle: .callout, options: [:])))
                                .foregroundStyle(Color(nsColor: OriginalToolbarAppearance.secondaryForeground()))
                                .padding(.bottom, 8)
                        }
                    }
                }
            case .color:
                if let metadata = item.decodedColorPreviewMetadata {
                    let color = OriginalColorPreviewMetadataGenerator.color(metadata.code)
                    Color(nsColor: color)
                        .overlay {
                            Text(hexString(color))
                                .font(Font(NSFont.userFixedPitchFont(ofSize: 18) ?? NSFont.monospacedSystemFont(ofSize: 18, weight: .regular)))
                                .foregroundStyle(Color(nsColor: (OriginalPreviewTextColors.f_1002067d4(color)
                                    ? NSColor.black : NSColor.white).withAlphaComponent(0.85)))
                        }
                }
            case .files:
                if let metadata = item.decodedFilePreviewMetadata {
                    VStack(spacing: 12) {
                        if metadata.paths.count == 1 {
                            ReplicaFileCardImage(image: metadata.previewData.flatMap(NSImage.init(data:)))
                                .frame(maxWidth: .infinity, maxHeight: .infinity)
                            ReplicaHeadTruncatedPath(path: metadata.paths[0])
                        } else {
                            ReplicaFileCardImage(image: ReplicaFileCardImage.multipleDocumentsImage())
                                .frame(maxWidth: .infinity, maxHeight: .infinity)
                            Text(String(localized: OriginalPreviewLocalization.f_1001c6fb0()))
                        }
                    }
                    .font(Font(NSFont.preferredFont(forTextStyle: .callout, options: [:])))
                    .padding(.horizontal, 12)
                    .padding(.top, 10)
                    .padding(.bottom, 10)
                }
            default:
                EmptyView()
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private func hexString(_ color: NSColor) -> String {
        guard let rgb = color.usingColorSpace(.deviceRGB) else { return "#000000" }
        return String(format: "#%02X%02X%02X", Int(rgb.redComponent * 255),
                      Int(rgb.greenComponent * 255), Int(rgb.blueComponent * 255))
    }
}

@MainActor
private struct ReplicaCardCheckerboard: NSViewRepresentable {
    func makeNSView(context: Context) -> OriginalImageCheckerboardView {
        OriginalImageCheckerboardView(frame: .zero)
    }

    func updateNSView(_ nsView: OriginalImageCheckerboardView, context: Context) {}
}
