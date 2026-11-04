import Foundation

/// Uses the same localized-resource / current-locale path as the original generated accessors.
enum OriginalShortcutMessages {
    private static let bundle = OriginalResourceBundle.bundle

    static func value(_ key: String) -> String {
        String(localized: LocalizedStringResource(String.LocalizationValue(key), table: "Localizable",
            locale: .current, bundle: .atURL(bundle.bundleURL)))
    }

    static func menuConflict(_ title: String) -> String {
        String(localized: LocalizedStringResource("shortcut-recorder.error.used-in-menu",
            defaultValue: "\(title)", table: "Localizable", locale: .current,
            bundle: .atURL(bundle.bundleURL)))
    }
}
