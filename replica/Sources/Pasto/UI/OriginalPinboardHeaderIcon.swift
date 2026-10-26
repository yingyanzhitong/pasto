import AppKit
import CoreGraphics

@MainActor
enum OriginalPinboardHeaderIcon {
    static func image(height: CGFloat, shared: Bool, color: NSColor) -> NSImage {
        let width = shared ? height * 1.45 : height
        let bounds = CGRect(x: 0, y: 0, width: width, height: height)
        let rectangleHeight = bounds.height
        let fill = color.cgColor
        let stroke = darkened(fill, by: 0.2)
        let image = NSImage(size: NSSize(width: width, height: height))
        image.lockFocusFlipped(false)
        guard let context = NSGraphicsContext.current?.cgContext else {
            image.unlockFocus()
            return image
        }
        let lineWidth = rectangleHeight * 0.05
        let diameter = bounds.height - lineWidth
        let inset = lineWidth * 0.5
        let firstRect = CGRect(x: inset, y: inset, width: diameter, height: diameter)
        let first = CGPath(ellipseIn: firstRect, transform: nil)
        context.setAllowsAntialiasing(true)
        context.setShouldAntialias(true)
        context.saveGState()
        draw(first, in: context, fill: fill, stroke: stroke, lineWidth: lineWidth)
        if diameter < bounds.width {
            let rightRect = CGRect(x: bounds.width - (inset + diameter), y: inset,
                                   width: diameter, height: diameter)
            let right = CGPath(ellipseIn: rightRect, transform: nil)
            let expandedDiameter = firstRect.width * 1.3
            let expanded = CGPath(ellipseIn:
                CGRect(x: firstRect.midX - expandedDiameter * 0.5,
                       y: firstRect.midY - expandedDiameter * 0.5,
                       width: expandedDiameter, height: expandedDiameter), transform: nil)
            let remainder = right.subtracting(expanded, using: .winding)
            draw(remainder, in: context, fill: fill, stroke: stroke, lineWidth: lineWidth)
        }
        context.restoreGState()
        image.unlockFocus()
        return image
    }

    private static func draw(_ path: CGPath, in context: CGContext, fill: CGColor,
                             stroke: CGColor, lineWidth: CGFloat) {
        context.addPath(path)
        context.setFillColor(fill)
        context.fillPath(using: .winding)
        context.addPath(path)
        context.setStrokeColor(stroke)
        context.setLineWidth(lineWidth)
        context.strokePath()
    }

    private static func darkened(_ color: CGColor, by amount: CGFloat) -> CGColor {
        guard amount >= 0, amount <= 1,
              let space = CGColorSpace(name: CGColorSpace.sRGB),
              let converted = color.converted(to: space, intent: .defaultIntent, options: nil),
              let components = converted.components, components.count >= 3 else { return color }
        let scale = 1 - amount
        let alpha = components.count == 3 ? 1 : components[3]
        return CGColor(colorSpace: space, components:
            [components[0] * scale, components[1] * scale, components[2] * scale, alpha]) ?? color
    }
}
