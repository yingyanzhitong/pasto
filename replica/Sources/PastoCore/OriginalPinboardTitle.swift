import Foundation

/// The shared tab-name value mapping from Paste 0x1003c4b2c.
public enum OriginalPinboardTitle {
    public static func normalizedRename(_ value: String) -> String {
        value.isEmpty ? String(localized: OriginalPreviewLocalization.f_1001c6aa4()) : value
    }
}
