import Carbon
import CoreGraphics
import Foundation
import OSLog
import PastoObjC

/// The original paste sender resolves the character in the active ASCII-capable layout.
public enum OriginalPasteKeyTranslation {
    public static func pasteKeyCode() -> CGKeyCode? {
        keyCode(for: "v")
    }

    private static func keyCode(for character: Character) -> CGKeyCode? {
        for code in UInt16(0)..<UInt16(128) {
            if f_100ae6678(keyCode: code) == String(character) { return code }
        }
        return nil
    }

    public static func f_100ae6428(_ character: Character) {
        guard let keyCode = keyCode(for: character) else {
            Logger(subsystem: "Pasto", category: "paste").error(
                "Cannot find a keyboard key for character \(String(character), privacy: .public)")
            return
        }
        // The original permits a nil source and handles each event separately.
        let source = CGEventSource(stateID: .combinedSessionState)
        let down = CGEvent(keyboardEventSource: source, virtualKey: keyCode, keyDown: true)
        down?.flags = .maskCommand
        let up = CGEvent(keyboardEventSource: source, virtualKey: keyCode, keyDown: false)
        down?.post(tap: .cgAnnotatedSessionEventTap)
        up?.post(tap: .cgAnnotatedSessionEventTap)
    }

    public static func f_100ae641c() {
        f_100ae6428("v")
    }

    public static func f_100ae6678(keyCode: UInt16) -> String? {
        guard let source = TISCopyCurrentASCIICapableKeyboardLayoutInputSource()?.takeRetainedValue() else {
            preconditionFailure("ASCII-capable keyboard layout input source is missing")
        }
        let property = TISGetInputSourceProperty(source, kTISPropertyUnicodeKeyLayoutData)
        var length: UInt64 = 0
        var characters = [UniChar](repeating: 0, count: 4)
        let status = withExtendedLifetime(source) {
            characters.withUnsafeMutableBufferPointer { buffer in
                PastoTranslateASCIIKeyLayoutData(property, keyCode, buffer.baseAddress!, UInt64(buffer.count), &length)
            }
        }
        guard status == noErr, length > 0,
              let scalar = UnicodeScalar(UInt32(characters[0])) else { return nil }
        return String(scalar)
    }
}
