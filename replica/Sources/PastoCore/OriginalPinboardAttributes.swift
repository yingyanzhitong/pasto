import Foundation

public enum OriginalPinboardAttributes {
    private struct Attributes: Codable {
        var type: String?
        var capacity: Int?
        var colorCode: UInt64?
    }

    public static func colorCode(from data: Data?) -> UInt64? {
        guard let data, let attributes = try? JSONDecoder().decode(Attributes.self, from: data),
              attributes.type == "pinboard" else { return nil }
        return attributes.colorCode ?? 0
    }

    static func encoded(colorCode: UInt64) throws -> Data {
        try JSONEncoder().encode(Attributes(type: "pinboard", capacity: nil, colorCode: colorCode))
    }

    static func parsedColorCode(_ colorHex: String) -> UInt64? {
        var value = colorHex.trimmingCharacters(in: .whitespacesAndNewlines)
        if value.hasPrefix("#") { value.removeFirst() }
        return UInt64(value, radix: 16)
    }
}
