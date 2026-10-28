import AppKit

@MainActor
public enum OriginalSourceApplicationImageColor {
    public static func prominentColor(_ image: NSImage) -> NSColor? {
        guard let bitmap = f_1003c7c4c(image, width: 128, height: 128) else { return nil }
        let colors = NSCountedSet(capacity: bitmap.pixelsWide * bitmap.pixelsHigh)
        for x in 0..<bitmap.pixelsWide {
            for y in 0..<bitmap.pixelsHigh {
                guard let color = bitmap.colorAt(x: x, y: y),
                      color.alphaComponent == 1, color.saturationComponent > 0.25 else { continue }
                colors.add(color)
            }
        }
        var counted: [(color: NSColor, count: Int)] = []
        for object in colors {
            if let color = object as? NSColor {
                counted.append((color, colors.count(for: object)))
            }
        }
        // Equal counts retain the counted set's enumeration order.
        counted.sort { $0.count > $1.count }
        guard let winner = counted.first?.color else { return .gray }
        return f_1003c7f84(winner)
    }

    public static func f_1003c7f84(_ color: NSColor) -> NSColor {
        let originalSaturation = color.saturationComponent
        let firstBrightness = color.brightnessComponent
        let secondBrightness = color.brightnessComponent
        let upperBrightness = secondBrightness > 0.96 ? 0.96 : secondBrightness
        let lowerBrightness = upperBrightness <= 0.75 ? 0.75 : upperBrightness
        let brightness = firstBrightness > 0.4 ? lowerBrightness : secondBrightness
        let saturation = originalSaturation <= 0.85 ? 0.85 : originalSaturation
        let hue = color.hueComponent
        let alpha = color.alphaComponent
        return NSColor(calibratedHue: hue, saturation: saturation,
                       brightness: brightness, alpha: alpha)
    }

    public static func f_1003c7c4c(_ image: NSImage, width targetWidth: CGFloat,
                                 height targetHeight: CGFloat) -> NSBitmapImageRep? {
        let rect = NSRect(x: 0, y: 0, width: targetWidth, height: targetHeight)
        guard let representation = image.bestRepresentation(for: rect, context: nil, hints: nil) else { return nil }
        let representationWidth = representation.size.width
        let width = Int(targetWidth < representationWidth ? targetWidth : representationWidth)
        let representationHeight = representation.size.height
        let height = Int(targetHeight < representationHeight ? targetHeight : representationHeight)
        guard let bitmap = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: width, pixelsHigh: height,
                                            bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true,
                                            isPlanar: false, colorSpaceName: .deviceRGB,
                                            bytesPerRow: width * 4, bitsPerPixel: 32),
              let context = NSGraphicsContext(bitmapImageRep: bitmap) else { return nil }
        NSGraphicsContext.saveGraphicsState()
        defer { NSGraphicsContext.restoreGraphicsState() }
        NSGraphicsContext.current = context
        representation.draw(in: rect)
        context.flushGraphics()
        return bitmap
    }
}
