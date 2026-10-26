import Foundation

public enum OriginalSearchLocalization {
    private static let bundle: Bundle = {
        if let url = Bundle.main.resourceURL?.appendingPathComponent("Pasto_PastoCore.bundle"),
           let bundle = Bundle(url: url) { return bundle }
        return Bundle.module
    }()

    public static func text(_ key: String) -> String {
        String(localized: LocalizedStringResource(String.LocalizationValue(stringLiteral: key),
            table: "Localizable", locale: .current, bundle: .atURL(bundle.bundleURL)))
    }
}
