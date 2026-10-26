import Carbon
import CoreGraphics
import Foundation

/// The original paste sender resolves the character in the active ASCII-capable layout.
public enum OriginalPasteKeyTranslation {
    public static func pasteKeyCode() -> CGKeyCode? {
        for code in UInt16(0)..<UInt16(128) {
            if f_100ae6678(keyCode: code) == "v" { return code }
        }
        return nil
    }

    public static func f_100ae6678(keyCode: UInt16) -> String? {
        guard let source = TISCopyCurrentASCIICapableKeyboardLayoutInputSource()?.takeRetainedValue() else {
            preconditionFailure("ASCII-capable keyboard layout input source is missing")
        }
        // The original does not guard absent layout data; retain a safe adapter boundary here.
        guard let property = TISGetInputSourceProperty(source, kTISPropertyUnicodeKeyLayoutData) else { return nil }
        let data = Unmanaged<CFData>.fromOpaque(property).takeUnretainedValue()
        guard let bytes = CFDataGetBytePtr(data) else { return nil }
        let layout = UnsafeRawPointer(bytes).assumingMemoryBound(to: UCKeyboardLayout.self)
        var deadKeyState: UInt32 = 0
        var length = 0
        var characters = [UniChar](repeating: 0, count: 4)
        let status = characters.withUnsafeMutableBufferPointer { buffer in
            UCKeyTranslate(layout, keyCode, UInt16(kUCKeyActionDisplay), 0,
                           UInt32(LMGetKbdType()), 0, &deadKeyState, buffer.count,
                           &length, buffer.baseAddress!)
        }
        guard status == noErr, length > 0,
              let scalar = UnicodeScalar(UInt32(characters[0])) else { return nil }
        return String(scalar)
    }
}
