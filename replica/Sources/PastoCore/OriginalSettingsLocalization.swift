import Foundation

public enum OriginalSettingsLocalization {
    private static let resourceBundle = OriginalResourceBundle.bundle

    private static func resource(_ key: String) -> LocalizedStringResource {
        LocalizedStringResource(String.LocalizationValue(stringLiteral: key),
                                table: "Localizable", locale: .current,
                                bundle: .atURL(resourceBundle.bundleURL))
    }

    public static func text(_ key: String) -> String { String(localized: resource(key)) }

    public static func f_1001dbfd4() -> LocalizedStringResource { resource("settings.general.title") }
    public static func f_1001e16d4() -> LocalizedStringResource { resource("settings.privacy.title") }
    public static func f_1001e28d4() -> LocalizedStringResource { resource("settings.sound-effects.title") }
}
