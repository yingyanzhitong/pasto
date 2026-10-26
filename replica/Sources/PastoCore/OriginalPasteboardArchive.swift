import Foundation

public enum OriginalPasteboardArchive {
    public enum ArchiveError: Error { case invalidRoot }

    public static func decodeItems(_ data: Data) throws -> [OriginalPasteboardItem] {
        try OriginalObjCExceptionBridge.withResult {
            if let items = OriginalPasteboardDataCodec.decodeIfValid(data) { return items }
            let decoder = try NSKeyedUnarchiver(forReadingFrom: data)
            decoder.requiresSecureCoding = true
            decoder.decodingFailurePolicy = .setErrorAndReturn
            decoder.setClass(OriginalPasteboardItem.self, forClassName: "PasteCore.PasteboardItem")
            decoder.setClass(OriginalPasteboardItem.self, forClassName: "_TtC9PasteCore14PasteboardItem")
            defer { decoder.finishDecoding() }
            let root = decoder.decodeObject(of: [NSArray.self, OriginalPasteboardItem.self],
                                            forKey: NSKeyedArchiveRootObjectKey)
            if let error = decoder.error { throw error }
            if let items = root as? [OriginalPasteboardItem] { return items }
            if let item = root as? OriginalPasteboardItem { return [item] }
            throw ArchiveError.invalidRoot
        }
    }

    public static func encodeItems(_ items: [OriginalPasteboardItem]) throws -> Data {
        try OriginalObjCExceptionBridge.f_1002ffc68 {
            try NSKeyedArchiver.archivedData(withRootObject: items as NSArray, requiringSecureCoding: true)
        }
    }
}
