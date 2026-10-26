import AppKit
import PastoCore
import QuartzCore

@MainActor
final class OriginalImageCheckerboardView: OriginalLayerBackedView {
    override func layout() { f_1001fdae8() }

    private func f_1001fdae8() {
        super.layout()
        let tile = Self.f_1001fe000(width: 8, height: 8,
                                  color: OriginalToolbarAppearance.borderAndHover())
        backgroundColor = NSColor(patternImage: tile)
        layer?.contentsGravity = .resizeAspectFill
    }

    private static func f_1001fe000(width: CGFloat, height: CGFloat, color: NSColor) -> NSImage {
        let image = NSImage(size: NSSize(width: width + width, height: height + height))
        image.lockFocus()
        color.setFill()
        NSBezierPath(rect: NSRect(x: 0, y: 0, width: width, height: height)).fill()
        NSBezierPath(rect: NSRect(x: width, y: height, width: width, height: height)).fill()
        image.unlockFocus()
        return image
    }
}
