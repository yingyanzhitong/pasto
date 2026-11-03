import AppKit

enum OriginalCollectionNavigation: UInt8 {
    case forward = 0, backward = 1, first = 2, last = 3, unhandled = 4

    /// 0x1002348a8: Control letters and the collection's supported arrow aliases.
    @MainActor
    static func f_1002348a8(_ event: NSEvent) -> Self {
        let commandModifiers = event.modifierFlags
        let modifiers = event.modifierFlags
        let key = event.charactersIgnoringModifiers?.lowercased()
        let specialKey = event.specialKey
        if (modifiers.contains(.control) && key == "f") || specialKey == .rightArrow { return .forward }
        if (modifiers.contains(.control) && key == "b") || specialKey == .leftArrow { return .backward }
        if (modifiers.contains(.control) && key == "e") ||
            (commandModifiers.contains(.command) && specialKey == .downArrow) { return .last }
        if (modifiers.contains(.control) && key == "a") ||
            (commandModifiers.contains(.command) && specialKey == .upArrow) { return .first }
        return .unhandled
    }
}
