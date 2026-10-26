import AppKit
import Foundation

public enum OriginalPasteboardImageEncoding {
    public static func f_1003c89c8(_ image: NSImage) -> Data? {
        guard let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else { return nil }
        let bitmap = NSBitmapImageRep(cgImage: cgImage)
        let scale = bitmap.size.width / image.size.width
        bitmap.size = NSSize(width: bitmap.size.width / scale, height: bitmap.size.height / scale)
        return bitmap.representation(using: .png, properties: [:])
    }
}
