import AppKit
import CoreGraphics
import ImageIO
import UniformTypeIdentifiers

// Compose the generated foreground on the standard legacy macOS icon grid.
let replica = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent()
let assets = replica.appendingPathComponent("Assets")
let input = assets.appendingPathComponent("PastoIconForeground.png")
guard let source = CGImageSourceCreateWithURL(input as CFURL, nil),
      let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else { fatalError("Invalid foreground") }
let width = image.width, height = image.height, count = width * height
let space = CGColorSpace(name: CGColorSpace.sRGB)!
let flags = CGImageAlphaInfo.premultipliedLast.rawValue | CGBitmapInfo.byteOrder32Big.rawValue
var pixels = [UInt8](repeating: 0, count: count * 4)
pixels.withUnsafeMutableBytes { buffer in
    let bytes = buffer.bindMemory(to: UInt8.self)
    let foreground = CGContext(data: buffer.baseAddress, width: width, height: height,
                              bitsPerComponent: 8, bytesPerRow: width * 4, space: space, bitmapInfo: flags)!
    foreground.draw(image, in: CGRect(x: 0, y: 0, width: width, height: height))
    // Ignore disconnected alpha specks; the p and rear card form one silhouette.
    var seen = [Bool](repeating: false, count: count), largest = [Int]()
    for start in 0..<count where !seen[start] && bytes[start * 4 + 3] >= 16 {
        var component = [start], cursor = 0
        seen[start] = true
        while cursor < component.count {
            let index = component[cursor], x = index % width, y = index / width
            cursor += 1
            let neighbors = [(x > 0, index - 1), (x + 1 < width, index + 1),
                             (y > 0, index - width), (y + 1 < height, index + width)]
            for (valid, next) in neighbors where valid && !seen[next] && bytes[next * 4 + 3] >= 16 {
                seen[next] = true
                component.append(next)
            }
        }
        if component.count > largest.count { largest = component }
    }
    guard !largest.isEmpty else { fatalError("Empty foreground") }
    var keep = [Bool](repeating: false, count: count)
    var minX = width, minY = height, maxX = 0, maxY = 0
    for index in largest {
        keep[index] = true
        minX = min(minX, index % width); maxX = max(maxX, index % width)
        minY = min(minY, index / width); maxY = max(maxY, index / width)
    }
    for index in 0..<count where !keep[index] {
        for channel in 0..<4 { bytes[index * 4 + channel] = 0 }
    }
    let crop = foreground.makeImage()!.cropping(to: CGRect(x: minX, y: minY,
                                                          width: maxX - minX + 1, height: maxY - minY + 1))!
    let canvas = CGContext(data: nil, width: 1024, height: 1024, bitsPerComponent: 8,
                           bytesPerRow: 0, space: space, bitmapInfo: flags)!
    let tile = CGRect(x: 100, y: 100, width: 824, height: 824)
    let shape = CGPath(roundedRect: tile, cornerWidth: 184, cornerHeight: 184, transform: nil)
    canvas.saveGState()
    canvas.addPath(shape); canvas.clip()
    let colors = [CGColor(srgbRed: 0.13, green: 0.74, blue: 0.76, alpha: 1),
                  CGColor(srgbRed: 0.02, green: 0.28, blue: 0.36, alpha: 1)] as CFArray
    let gradient = CGGradient(colorsSpace: space, colors: colors, locations: [0, 1])!
    canvas.drawLinearGradient(gradient, start: CGPoint(x: 100, y: 924),
                              end: CGPoint(x: 924, y: 100), options: [.drawsBeforeStartLocation, .drawsAfterEndLocation])
    let scale = min(782 / CGFloat(crop.height), 760 / CGFloat(crop.width))
    let size = CGSize(width: CGFloat(crop.width) * scale, height: CGFloat(crop.height) * scale)
    canvas.interpolationQuality = .high
    canvas.draw(crop, in: CGRect(x: 512 - size.width / 2, y: 512 - size.height / 2,
                                width: size.width, height: size.height))
    canvas.restoreGState()
    let output = assets.appendingPathComponent("PastoIcon.png")
    let destination = CGImageDestinationCreateWithURL(output as CFURL, UTType.png.identifier as CFString, 1, nil)!
    CGImageDestinationAddImage(destination, canvas.makeImage()!, nil)
    guard CGImageDestinationFinalize(destination) else { fatalError("PNG encoding failed") }
}

let temporary = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
try FileManager.default.createDirectory(at: temporary, withIntermediateDirectories: true)
defer { try? FileManager.default.removeItem(at: temporary) }
let iconset = temporary.appendingPathComponent("Pasto.iconset")
try FileManager.default.createDirectory(at: iconset, withIntermediateDirectories: true)
func run(_ command: String, _ arguments: [String]) throws {
    let process = Process(); process.executableURL = URL(fileURLWithPath: command); process.arguments = arguments
    try process.run(); process.waitUntilExit()
    guard process.terminationStatus == 0 else { fatalError("Icon preparation failed") }
}
for size in [16, 32, 128, 256, 512] {
    for scale in [1, 2] {
        let suffix = scale == 2 ? "@2x" : ""
        let output = iconset.appendingPathComponent("icon_\(size)x\(size)\(suffix).png")
        try run("/usr/bin/sips", ["-z", "\(size * scale)", "\(size * scale)",
                                  assets.appendingPathComponent("PastoIcon.png").path, "--out", output.path])
    }
}
try run("/usr/bin/iconutil", ["-c", "icns", iconset.path, "-o", assets.appendingPathComponent("PastoAppIcon.icns").path])
