import AppKit
import Foundation

public struct KeyboardShortcut: Codable, Equatable, Hashable, Sendable {
    public var keyCode: UInt32
    public var modifierRawValue: UInt

    public init(keyCode: UInt32, modifierRawValue: UInt) {
        self.keyCode = keyCode
        self.modifierRawValue = modifierRawValue
    }

    public var originalValue: OriginalShortcutValue {
        OriginalShortcutValue(keyCode: Int(keyCode), internalModifiers: modifierRawValue)
    }

    public init?(originalValue: OriginalShortcutValue) {
        guard let keyCode = UInt32(exactly: originalValue.keyCode) else { return nil }
        self.init(keyCode: keyCode, modifierRawValue: originalValue.internalModifiers)
    }

    private enum CompatibilityCodingKey: String, CodingKey {
        case keyCode, internalModifiers, modifierRawValue
    }

    public init(from decoder: Decoder) throws {
        let values = try decoder.container(keyedBy: CompatibilityCodingKey.self)
        // Preserve preferences written by earlier replica versions. New values
        // use the reference's key names and integer encoding types.
        if !values.contains(.internalModifiers), values.contains(.modifierRawValue) {
            self.init(keyCode: try values.decode(UInt32.self, forKey: .keyCode),
                      modifierRawValue: try values.decode(UInt.self, forKey: .modifierRawValue))
            return
        }
        let original = try OriginalShortcutValue(from: decoder)
        guard let keyCode = UInt32(exactly: original.keyCode) else {
            throw DecodingError.dataCorruptedError(forKey: .keyCode, in: values,
                debugDescription: "The replica shortcut requires a Carbon UInt32 key code")
        }
        self.init(keyCode: keyCode, modifierRawValue: original.internalModifiers)
    }

    public func encode(to encoder: Encoder) throws {
        try OriginalShortcutValue(keyCode: Int(keyCode), internalModifiers: modifierRawValue)
            .f_1001e9b00(to: encoder)
    }

    public static let modifierMask: NSEvent.ModifierFlags = [.command, .shift, .option, .control]
    public static let historyDefault = KeyboardShortcut(keyCode: 9, modifierRawValue: [.command, .shift])
    public static let stackDefault = KeyboardShortcut(keyCode: 8, modifierRawValue: [.command, .shift])
    public static let previousPinboardDefault = KeyboardShortcut(keyCode: UInt32(OriginalShortcutFunctions.f_1001e9638()), modifierRawValue: NSEvent.ModifierFlags.command.rawValue)
    public static let nextPinboardDefault = KeyboardShortcut(keyCode: UInt32(OriginalShortcutFunctions.f_1001e964c()), modifierRawValue: NSEvent.ModifierFlags.command.rawValue)

    private init(keyCode: UInt32, modifierRawValue flags: NSEvent.ModifierFlags) {
        self.init(keyCode: keyCode, modifierRawValue: flags.rawValue)
    }

    public var modifiers: NSEvent.ModifierFlags { NSEvent.ModifierFlags(rawValue: modifierRawValue) }

    public var isValidGlobal: Bool {
        OriginalShortcutFunctions.f_1001ebc2c(keyCode: keyCode, modifierRawValue: modifierRawValue)
    }

    public func matches(_ event: NSEvent) -> Bool {
        OriginalShortcutFunctions.f_1001e7d18(event) == self
    }

    public var displayName: String {
        OriginalShortcutValue(keyCode: Int(keyCode), internalModifiers: modifierRawValue).displayName
    }
}
