import Foundation

/// The reference value stores an Int key code. Carbon's UInt32 constraint is
/// applied when registering it, rather than when decoding preferences.
public struct OriginalShortcutValue: Codable, Equatable, Hashable, CustomStringConvertible, Sendable {
    public var keyCode: Int
    public var internalModifiers: UInt

    public init(keyCode: Int, internalModifiers: UInt) {
        self.keyCode = keyCode
        self.internalModifiers = internalModifiers
    }

    public init(from decoder: Decoder) throws { self = try Self.f_1001e9d68(from: decoder) }

    public static func f_1001e9d68(from decoder: Decoder) throws -> Self {
        let values = try decoder.container(keyedBy: OriginalShortcutCodingKey.self)
        let keyCode = try values.decode(Int.self, forKey: .keyCode)
        let modifiers = try values.decode(UInt.self, forKey: .internalModifiers)
        return Self(keyCode: keyCode, internalModifiers: modifiers)
    }

    public func f_1001e9b00(to encoder: Encoder) throws {
        var values = encoder.container(keyedBy: OriginalShortcutCodingKey.self)
        try values.encode(keyCode, forKey: .keyCode)
        try values.encode(internalModifiers, forKey: .internalModifiers)
    }

    public func encode(to encoder: Encoder) throws { try f_1001e9b00(to: encoder) }

    public static func f_1001e9cc8(keyCode: Int, internalModifiers: UInt) -> String {
        OriginalShortcutFunctions.f_1001e9774(verbose: false, modifierRawValue: internalModifiers)
            + OriginalShortcutFunctions.f_1001e7e50(keyCode: keyCode)
    }

    public var description: String {
        Self.f_1001e9cc8(keyCode: keyCode, internalModifiers: internalModifiers)
    }

    public var displayName: String { description }
}

public enum OriginalShortcutCodingKey: CodingKey, Sendable {
    case keyCode
    case internalModifiers

    public func f_1001e9990() -> String {
        switch self {
        case .keyCode: return "keyCode"
        case .internalModifiers: return "internalModifiers"
        }
    }

    public static func f_1001e99d0(_ string: String) -> Self? {
        switch string {
        case "keyCode": return .keyCode
        case "internalModifiers": return .internalModifiers
        default: return nil
        }
    }

    public var stringValue: String { f_1001e9990() }
    public init?(stringValue: String) {
        guard let key = Self.f_1001e99d0(stringValue) else { return nil }
        self = key
    }
    public var intValue: Int? { nil }
    public init?(intValue: Int) { return nil }
}
