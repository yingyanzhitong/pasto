import AppKit

// Export the original 20-point template images at both supported scales. Plain
// PNG resources avoid depending on the source catalog's CoreUI storage version.
guard CommandLine.arguments.count == 3,
      let source = Bundle(path: CommandLine.arguments[1]) else {
    fatalError("Usage: swift extract_stack_icon_pngs.swift Paste.app destination")
}
let destination = URL(fileURLWithPath: CommandLine.arguments[2], isDirectory: true)
try FileManager.default.createDirectory(at: destination, withIntermediateDirectories: true)
for name in ["icon.file", "icon.link", "icon.text", "icon.unknown"] {
    guard let image = source.image(forResource: NSImage.Name(name)) else {
        fatalError("Missing original image \(name)")
    }
    for scale in [1, 2] {
        guard let bitmap = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: 20 * scale,
            pixelsHigh: 20 * scale, bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true,
            isPlanar: false, colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0),
              let context = NSGraphicsContext(bitmapImageRep: bitmap) else {
            fatalError("Cannot create bitmap for \(name)")
        }
        bitmap.size = NSSize(width: 20, height: 20)
        NSGraphicsContext.saveGraphicsState()
        NSGraphicsContext.current = context
        context.cgContext.scaleBy(x: CGFloat(scale), y: CGFloat(scale))
        image.draw(in: NSRect(x: 0, y: 0, width: 20, height: 20), from: .zero,
                   operation: .copy, fraction: 1)
        NSGraphicsContext.restoreGraphicsState()
        guard let png = bitmap.representation(using: .png, properties: [:]) else {
            fatalError("Cannot encode \(name)")
        }
        let suffix = scale == 2 ? "@2x" : ""
        try png.write(to: destination.appendingPathComponent(name + suffix + ".png"), options: .atomic)
    }
}
