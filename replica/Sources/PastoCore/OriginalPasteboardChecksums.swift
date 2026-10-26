import CryptoKit
import Foundation

public enum OriginalPasteboardChecksums {
    public static func f_100323324(_ data: Data, into hasher: inout Insecure.MD5) {
        data.withUnsafeBytes { hasher.update(bufferPointer: $0) }
    }

    public static func f_100322fe4(_ digest: Insecure.MD5.Digest) -> [String] {
        digest.map { String(format: "%02x", $0) }
    }

    private static func checksum(_ data: Data) -> String {
        var hasher = Insecure.MD5()
        f_100323324(data, into: &hasher)
        return f_100322fe4(hasher.finalize()).joined()
    }

    public static func f_100322d94(_ string: String) -> String {
        guard let data = string.data(using: .utf8, allowLossyConversion: false) else { return "" }
        return checksum(data)
    }

    public static func f_100322ae4(_ items: [OriginalPasteboardItem]) -> String {
        let data = (try? NSKeyedArchiver.archivedData(withRootObject: items as NSArray,
                                                    requiringSecureCoding: false)) ?? Data()
        return checksum(data)
    }

    public static func f_1003216bc(_ items: [OriginalPasteboardItem],
                                  kind: OriginalPasteboardContentKind) -> String? {
        switch kind {
        case .unknown:
            return f_100322ae4(items)
        case .image:
            guard let data = items.lazy.compactMap({ $0.f_10037d5c4() }).first else { return nil }
            return checksum(data)
        case .color, .link, .text:
            guard let text = items.first?.f_10037c9a8() else { return nil }
            return f_100322d94(text)
        case .files:
            let paths = items.compactMap { $0.f_10037cc6c()?.path }
            guard !paths.isEmpty else { return f_100322ae4(items) }
            return f_100322d94("FileSnippet:" + paths.joined())
        }
    }
}
