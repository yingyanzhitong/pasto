import Foundation

public enum OriginalPinboardAttributes {
    private struct Attributes: Codable {
        var type: String?
        var capacity: Int?
        var colorCode: UInt64?
    }

    public enum Value: Equatable {
        case clipboard(capacity: Int)
        case pinboard(colorCode: UInt64)
    }

    public static func decoded(from data: Data?) -> Value? {
        guard let data, let attributes = try? JSONDecoder().decode(Attributes.self, from: data) else { return nil }
        return f_1003245fc(attributes)
    }

    private static func f_1003245fc(_ attributes: Attributes) -> Value {
        if attributes.type == "pinboard" {
            return .pinboard(colorCode: attributes.colorCode ?? 0)
        }
        return .clipboard(capacity: attributes.capacity ?? 30)
    }

    public static func colorCode(from data: Data?) -> UInt64? {
        guard let data, let attributes = try? JSONDecoder().decode(Attributes.self, from: data) else { return nil }
        guard case let .pinboard(colorCode) = f_1003245fc(attributes) else { return nil }
        return colorCode
    }

    /// 0x1003293c4: absent/corrupt attributes remain nil, unlike a decoded missing capacity.
    public static func clipboardCapacity(from data: Data?) -> Int? {
        guard let data, let attributes = try? JSONDecoder().decode(Attributes.self, from: data) else { return nil }
        guard case let .clipboard(capacity) = f_1003245fc(attributes) else { return nil }
        return capacity
    }

    static func encodedClipboard(capacity: Int) throws -> Data {
        try JSONEncoder().encode(Attributes(type: "clipboard", capacity: capacity, colorCode: nil))
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
