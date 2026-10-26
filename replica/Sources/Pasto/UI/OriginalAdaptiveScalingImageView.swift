import AppKit
import SwiftUI

/// The compact image cell's adaptive drawing; its checkerboard remains a separate view.
@MainActor
final class OriginalAdaptiveScalingImageView: NSView {
    var image: NSImage? {
        didSet { needsDisplay = true }
    }

    var scaleToFillRatio: CGFloat = 0.8 {
        didSet { needsDisplay = true }
    }

    override func setFrameSize(_ newSize: NSSize) {
        super.setFrameSize(newSize)
        needsDisplay = true
    }

    override func draw(_ dirtyRect: NSRect) {
        guard let image else { return }
        let viewAspect = bounds.width / bounds.height
        let imageAspect = image.size.width / image.size.height
        let denominator = viewAspect <= imageAspect ? imageAspect : viewAspect
        let similarity = 1 - abs(imageAspect - viewAspect) / denominator
        let useWidth: Bool
        if scaleToFillRatio <= similarity {
            useWidth = imageAspect < viewAspect
        } else {
            useWidth = !(imageAspect < viewAspect)
        }
        let scale = useWidth ? bounds.width / image.size.width : bounds.height / image.size.height
        let width = image.size.width * scale
        let height = image.size.height * scale
        let target = NSRect(x: (bounds.width - width) / 2,
                            y: (bounds.height - height) / 2,
                            width: width, height: height).integral
        image.draw(in: target, from: NSRect(origin: .zero, size: image.size),
                   operation: .copy, fraction: 1)
    }
}

@MainActor
struct ReplicaAdaptiveScalingImage: NSViewRepresentable {
    let image: NSImage
    var scaleToFillRatio: CGFloat = 0.8

    func makeNSView(context: Context) -> OriginalAdaptiveScalingImageView {
        let view = OriginalAdaptiveScalingImageView(frame: .zero)
        view.image = image
        view.scaleToFillRatio = scaleToFillRatio
        return view
    }

    func updateNSView(_ nsView: OriginalAdaptiveScalingImageView, context: Context) {
        nsView.image = image
        nsView.scaleToFillRatio = scaleToFillRatio
    }
}
