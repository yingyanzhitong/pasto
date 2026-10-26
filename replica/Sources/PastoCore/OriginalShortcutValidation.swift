import AppKit
import Carbon
import Foundation

@MainActor
public enum OriginalShortcutValidation {
    /// The original checks system shortcuts before walking the application's menu.
    public static func f_1001ebce4(shortcut: KeyboardShortcut, menu: NSMenu?) -> String? {
        f_1001ebce4(shortcut: OriginalShortcutValue(keyCode: Int(shortcut.keyCode),
            internalModifiers: shortcut.modifierRawValue), menu: menu)
    }

    public static func f_1001ebce4(shortcut: OriginalShortcutValue, menu: NSMenu?) -> String? {
        var copiedKeys: Unmanaged<CFArray>?
        if CopySymbolicHotKeys(&copiedKeys) == noErr,
           let keys = copiedKeys?.takeRetainedValue() as? [[String: Any]],
           keys.contains(where: { OriginalShortcutFunctions.f_1001ebf04($0, shortcut: shortcut) }) {
            return OriginalShortcutMessages.value("shortcut-recorder.error.used-in-system")
        }
        return f_1001ec200(shortcut: shortcut, menu: menu)
    }

    /// Depth-first submenu traversal, including Shift implicit in uppercase equivalents.
    public static func f_1001ec200(shortcut: KeyboardShortcut, menu: NSMenu?) -> String? {
        f_1001ec200(shortcut: OriginalShortcutValue(keyCode: Int(shortcut.keyCode),
            internalModifiers: shortcut.modifierRawValue), menu: menu)
    }

    public static func f_1001ec200(shortcut: OriginalShortcutValue, menu: NSMenu?) -> String? {
        for item in menu?.items ?? [] {
            if let failure = f_1001ec200(shortcut: shortcut, menu: item.submenu) { return failure }
            let candidate = OriginalShortcutFunctions.f_1001e8098(keyCode: shortcut.keyCode)
            guard item.keyEquivalent.lowercased() == candidate else { continue }
            let rawModifiers = item.keyEquivalentModifierMask.rawValue
            let modifiers = item.keyEquivalent == candidate
                ? rawModifiers & 0x1e0000 : (rawModifiers & 0x1c0000) | 0x20000
            if modifiers == shortcut.internalModifiers {
                return String(format: OriginalShortcutMessages.value("shortcut-recorder.error.used-in-menu"),
                              locale: Locale.current, item.title)
            }
        }
        return nil
    }

    public static func optionCompatibilityWarning(modifierRawValue: UInt,
                                                  version: OperatingSystemVersion) -> String? {
        guard requiresOptionCompatibilityWarning(modifierRawValue: modifierRawValue, version: version)
        else { return nil }
        return OriginalShortcutMessages.value("shortcut-recorder.error.option-key")
    }

    public static func requiresOptionCompatibilityWarning(modifierRawValue: UInt,
                                                          version: OperatingSystemVersion) -> Bool {
        modifierRawValue & 0x80000 != 0 && modifierRawValue & 0x140000 == 0
            && version.majorVersion == 15 && version.minorVersion < 2
    }
}
