import AppKit
import SwiftUI

/// Both file-card branches use the same flexible AppKit image frame.
@MainActor
struct ReplicaFileCardImage: NSViewRepresentable {
    let image: NSImage?

    func makeNSView(context: Context) -> NSImageView {
        let view = NSImageView(frame: .zero)
        view.imageAlignment = .alignBottom
        view.imageScaling = .scaleProportionallyUpOrDown
        view.image = image
        return view
    }

    func updateNSView(_ nsView: NSImageView, context: Context) {
        nsView.image = image
    }

    func sizeThatFits(_ proposal: ProposedViewSize, nsView: NSImageView,
                      context: Context) -> CGSize? {
        guard let width = proposal.width, let height = proposal.height else { return nil }
        return CGSize(width: width, height: height)
    }

    static func multipleDocumentsImage() -> NSImage? {
        guard let image = NSImage(named: NSImage.multipleDocumentsName) else { return nil }
        image.size = NSSize(width: 128, height: 128)
        return image
    }
}
