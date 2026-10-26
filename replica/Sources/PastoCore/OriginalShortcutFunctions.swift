import AppKit
import Carbon
import Foundation

/// Shortcut value/label operations recovered from the original address chain.
/// These helpers preserve logical values, rather than the original Swift object layout.
public enum OriginalShortcutFunctions {
    public static let eventModifierMask: UInt = 0xff5f0000

    /// Original NSEvent shortcut initializer: omit numeric-pad/function/device flags.
    public static func f_1001e7d18(_ event: NSEvent) -> KeyboardShortcut {
        KeyboardShortcut(keyCode: UInt32(event.keyCode),
                         modifierRawValue: event.modifierFlags.rawValue & eventModifierMask)
    }

    /// Four entries in the original constant dictionary at 0x100fb4fc0.
    public static func f_1001e7d58(modifierRawValue: UInt) -> UInt32 {
        var result: UInt32 = 0
        let mappings: [(UInt, UInt32)] = [
            (0x100000, 0x100), (0x80000, 0x800),
            (0x40000, 0x1000), (0x20000, 0x200)
        ]
        for (appKit, carbon) in mappings where modifierRawValue & appKit == appKit {
            result |= carbon
        }
        return result
    }

    /// Function keys need no modifiers; other keys require Command, Control or Option.
    public static func f_1001ebc2c(keyCode: UInt32, modifierRawValue: UInt) -> Bool {
        f_1001ebc2c(keyCode: Int(keyCode), modifierRawValue: modifierRawValue)
    }

    public static func f_1001ebc2c(keyCode: Int, modifierRawValue: UInt) -> Bool {
        (UInt32(exactly: keyCode).map(functionKeyCodes.contains) ?? false)
            || keyCode == 90 || modifierRawValue & 0x1c0000 != 0
    }

    /// The verbose variant intentionally uses the original English modifier names.
    public static func f_1001e9774(verbose: Bool, modifierRawValue: UInt) -> String {
        var text = ""
        let labels: [(UInt, String, String)] = [
            (0x40000, "⌃", "⌃ Control"), (0x80000, "⌥", "⌥ Option"),
            (0x20000, "⇧", "⇧ Shift"), (0x100000, "⌘", "⌘ Command")
        ]
        for (mask, symbol, name) in labels where modifierRawValue & mask != 0 {
            text += verbose ? name : symbol
        }
        return text
    }

    /// Compare one Carbon symbolic-shortcut dictionary, including its enabled flag.
    public static func f_1001ebf04(_ entry: [String: Any], shortcut: KeyboardShortcut) -> Bool {
        f_1001ebf04(entry, shortcut: OriginalShortcutValue(keyCode: Int(shortcut.keyCode),
            internalModifiers: shortcut.modifierRawValue))
    }

    public static func f_1001ebf04(_ entry: [String: Any], shortcut: OriginalShortcutValue) -> Bool {
        guard let code = entry["kHISymbolicHotKeyCode"] as? NSNumber,
              code.intValue == shortcut.keyCode,
              let modifiers = entry["kHISymbolicHotKeyModifiers"] as? NSNumber,
              modifiers.uintValue == UInt(f_1001e7d58(modifierRawValue: shortcut.internalModifiers)),
              let enabled = entry["kHISymbolicHotKeyEnabled"] as? NSNumber else { return false }
        return enabled.boolValue
    }

    private static let displayLabels = f_1001e822c()
    private static let menuLabels = f_1001e8a98()
    private static let keyCodes = f_1001e9654()

    /// The original literal-key initializer uses a fixed ANSI map, independently
    /// of the current keyboard layout used to display an already chosen key.
    public static func f_1001e9654() -> [String: UInt32] {
        ["a": 0, "b": 11, "c": 8, "d": 2, "e": 14, "f": 3, "g": 5,
         "h": 4, "i": 34, "j": 38, "k": 40, "l": 37, "m": 46, "n": 45,
         "o": 31, "p": 35, "q": 12, "r": 15, "s": 1, "t": 17, "u": 32,
         "v": 9, "w": 13, "x": 7, "y": 16, "z": 6, "0": 29, "1": 18,
         "2": 19, "3": 20, "4": 21, "5": 23, "6": 22, "7": 26, "8": 28,
         "9": 25, "=": 24, "-": 27, "]": 30, "[": 33, "\"": 39,
         ";": 41, "\\": 42, ",": 43, "/": 44, ".": 47]
    }

    public static func f_1001e94d4(_ key: String) -> UInt32 {
        guard let keyCode = keyCodes[key.lowercased()] else {
            preconditionFailure("Unsupported shortcut key: \(key)")
        }
        return keyCode
    }

    // These original accessors consist solely of returning the fixed key code.
    public static func f_1001e95fc() -> Int { 53 }
    public static func f_1001e9610() -> Int { 51 }
    public static func f_1001e9624() -> Int { 117 }
    public static func f_1001e9638() -> Int { 123 }
    public static func f_1001e964c() -> Int { 124 }

    /// The original 52-entry display table; F20 deliberately uses layout translation.
    public static func f_1001e822c() -> [UInt32: String] {
        var labels: [UInt32: String] = [
            49: spaceLabel, 53: "⎋", 51: "⌫", 117: "⌦",
            123: "←", 124: "→", 126: "↑", 125: "↓", 114: "?",
            116: "⇞", 121: "⇟", 48: "⇥", 36: "↩",
            82: "0", 83: "1", 84: "2", 85: "3", 86: "4", 87: "5",
            88: "6", 89: "7", 91: "8", 92: "9", 65: ".", 67: "*",
            69: "+", 71: "⌧", 75: "/", 76: "⌅", 78: "-", 81: "=",
            119: "↘", 115: "↖"
        ]
        for (index, code) in functionKeyCodes.enumerated() { labels[code] = "F\(index + 1)" }
        return labels
    }

    /// Resolve special labels first, then translate the current ASCII-capable layout.
    public static func f_1001e7e50(keyCode: UInt32) -> String {
        f_1001e7e50(keyCode: Int(keyCode))
    }

    public static func f_1001e7e50(keyCode: Int) -> String {
        if let code = UInt32(exactly: keyCode), let label = displayLabels[code] { return label }
        guard let source = TISCopyCurrentASCIICapableKeyboardLayoutInputSource()?.takeRetainedValue(),
              let property = TISGetInputSourceProperty(source, kTISPropertyUnicodeKeyLayoutData) else { return "" }
        let data = Unmanaged<CFData>.fromOpaque(property).takeUnretainedValue()
        guard let bytes = CFDataGetBytePtr(data) else { return "" }
        precondition(keyCode >= 0 && keyCode <= Int(UInt16.max))
        let layout = UnsafeRawPointer(bytes).assumingMemoryBound(to: UCKeyboardLayout.self)
        var deadKeyState: UInt32 = 0
        var length = 0
        var characters = [UniChar](repeating: 0, count: 256)
        let status = characters.withUnsafeMutableBufferPointer { buffer in
            UCKeyTranslate(layout, UInt16(keyCode), UInt16(kUCKeyActionDisplay), 0,
                           UInt32(LMGetKbdType()), 0, &deadKeyState, buffer.count,
                           &length, buffer.baseAddress!)
        }
        guard status == noErr else { return "" }
        return String(utf16CodeUnits: characters, count: length).uppercased()
    }

    /// The original 20-entry menu-equivalent table (F1...F19 and Space).
    public static func f_1001e8a98() -> [UInt32: String] {
        var labels: [UInt32: String] = [49: " "]
        for (index, code) in functionKeyCodes.enumerated() {
            labels[code] = String(UnicodeScalar(0xf704 + index)!)
        }
        return labels
    }

    public static func f_1001e8098(keyCode: UInt32) -> String {
        f_1001e8098(keyCode: Int(keyCode))
    }

    public static func f_1001e8098(keyCode: Int) -> String {
        let label = f_1001e7e50(keyCode: keyCode)
        if label == "↩" { return "\r" }
        if label.count < 2 { return label.lowercased() }
        return UInt32(exactly: keyCode).flatMap { menuLabels[$0] } ?? ""
    }

    private static let functionKeyCodes: [UInt32] = [
        122, 120, 99, 118, 96, 97, 98, 100, 101, 109, 103, 111, 105, 107, 113, 106, 64, 79, 80
    ]

    // The sole localized item in the display table is the standard Space key label.
    private static var spaceLabel: String {
        let labels = [
            "cs": "Mezerník", "da": "Mellemrum", "de": "Leertaste", "en": "Space",
            "es": "Espacio", "fr": "Espace", "he": "רווח", "it": "Spazio",
            "ja": "スペース", "ko": "공간", "nl": "Spatie", "pl": "Spacja",
            "pt-BR": "Espaço", "pt-PT": "Espaço", "ru": "Пробел",
            "zh-Hans": "空格键", "zh-Hant": "空間"
        ]
        let language = Bundle.preferredLocalizations(from: Array(labels.keys),
                                                    forPreferences: Locale.preferredLanguages).first ?? "en"
        return labels[language] ?? "Space"
    }
}
