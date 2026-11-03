import AppKit

/// The light/dark destination illustrations used by Paste's settings picker.
public enum OriginalSettingsIllustrations {
    @MainActor private static let images: [String: NSImage] = {
        var result: [String: NSImage] = [:]
        for name in ["OriginalSettingsCopyToAppLight", "OriginalSettingsCopyToAppDark",
                     "OriginalSettingsCopyToClipboardLight", "OriginalSettingsCopyToClipboardDark"] {
            if let url = Bundle.module.url(forResource: name + "@2x", withExtension: "png"),
               let image = NSImage(contentsOf: url) {
                result[name] = image
            }
        }
        return result
    }()

    @MainActor public static func image(directPaste: Bool, dark: Bool) -> NSImage? {
        images["OriginalSettingsCopyTo" + (directPaste ? "App" : "Clipboard") + (dark ? "Dark" : "Light")]
    }
}
