import Foundation

public enum OriginalSearchLocalization {
    private static let bundle = OriginalResourceBundle.bundle

    public static func text(_ key: String) -> String {
        String(localized: LocalizedStringResource(String.LocalizationValue(stringLiteral: key),
            table: "Localizable", locale: .current, bundle: .atURL(bundle.bundleURL)))
    }
}
