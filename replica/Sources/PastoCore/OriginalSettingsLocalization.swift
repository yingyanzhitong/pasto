import Foundation

public enum OriginalSettingsLocalization {
    private static let resourceBundle: Bundle = {
        if let url = Bundle.main.resourceURL?.appendingPathComponent("Pasto_PastoCore.bundle"),
           let bundle = Bundle(url: url) { return bundle }
        return Bundle.module
    }()

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
