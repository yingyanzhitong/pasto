import AppKit

public enum OriginalSearchFilterSymbols {
    private static func slot(_ value: String) -> UnsafePointer<String> {
        let pointer = UnsafeMutablePointer<String>.allocate(capacity: 1)
        pointer.initialize(to: value)
        return UnsafePointer(pointer)
    }

    private static let application = slot("app.dashed")
    private static let calendar = slot("calendar")
    private static let board = slot("circle.fill")
    private static let file = slot("doc")
    private static let unrecognizedType = slot("exclamationmark.triangle.fill")
    private static let link = slot("link")
    private static let devices = slot("macbook.and.iphone")
    private static let color = slot("paintpalette")
    private static let image = slot("photo")
    private static let unknown = slot("questionmark.app")
    private static let text = slot("text.alignleft")

    public static func f_10020c714() -> UnsafePointer<String> { application }
    public static func f_10020c934() -> UnsafePointer<String> { calendar }
    public static func f_10020cc48() -> UnsafePointer<String> { board }
    public static func f_10020cdd0() -> UnsafePointer<String> { file }
    public static func f_10020cf40() -> UnsafePointer<String> { unrecognizedType }
    public static func f_10020d3b0() -> UnsafePointer<String> { link }
    public static func f_10020d434() -> UnsafePointer<String> { devices }
    public static func f_10020d4f4() -> UnsafePointer<String> { color }
    public static func f_10020d6a4() -> UnsafePointer<String> { image }
    public static func f_10020d798() -> UnsafePointer<String> { unknown }
    public static func f_10020d9c8() -> UnsafePointer<String> { text }

    public static func f_100054b2c(kind: UInt8, value: String) -> String? {
        let symbol: UnsafePointer<String>
        switch kind {
        case 0: symbol = f_10020c714()
        case 1:
            switch value.lowercased() {
            case "link": symbol = f_10020d3b0()
            case "image": symbol = f_10020d6a4()
            case "color": symbol = f_10020d4f4()
            case "text": symbol = f_10020d9c8()
            case "file": symbol = f_10020cdd0()
            case "unknown": symbol = f_10020d798()
            default: symbol = f_10020cf40()
            }
        case 2: return nil
        case 3: symbol = f_10020c934()
        case 4: symbol = f_10020d434()
        default: symbol = f_10020cc48()
        }
        return symbol.pointee
    }
}

@MainActor
public enum OriginalSystemImageFunctions {
    public static func f_1000f653c(_ name: String, imageType: NSImage.Type = NSImage.self) -> NSImage? {
        imageType.init(systemSymbolName: name, accessibilityDescription: nil)
    }
}
