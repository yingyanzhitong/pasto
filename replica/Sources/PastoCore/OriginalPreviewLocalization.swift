import Foundation

/// Recovered Localizable keys use the platform locale and bundle fallback behavior.
public enum OriginalPreviewLocalization {
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

    public static func f_1001c6aa4() -> LocalizedStringResource { resource("general.untitled") }

    public static func f_1001c5b38() -> LocalizedStringResource { resource("general.paused") }
    public static func f_1001c2888() -> LocalizedStringResource { resource("general.action.pause-paste") }

    public static func f_1001c5838() -> LocalizedStringResource { resource("general.paste-paused") }
    public static func f_1001c59b8() -> LocalizedStringResource { resource("general.paste-resumed") }

    public static func f_1001e6c18(_ time: String) -> LocalizedStringResource {
        LocalizedStringResource("general.until", defaultValue: "\(time)", table: "Localizable",
                                locale: .current, bundle: .atURL(resourceBundle.bundleURL))
    }

    public static func f_1001c482c() -> LocalizedStringResource {
        resource("general.copied")
    }

    public static func f_1001c4b50() -> LocalizedStringResource {
        resource("general.enable-direct-paste")
    }

    public static func f_1001bf288() -> LocalizedStringResource {
        resource("edit-item.toolbar.text.bold")
    }

    public static func f_1001bf408() -> LocalizedStringResource {
        resource("edit-item.toolbar.text.italic")
    }

    public static func f_1001bf588() -> LocalizedStringResource {
        resource("edit-item.toolbar.text.strikethrough")
    }

    public static func f_1001bf708() -> LocalizedStringResource {
        resource("edit-item.toolbar.text.underline")
    }

    public static func f_1001bf108() -> LocalizedStringResource {
        resource("edit-item.toolbar.save-changes")
    }

    public static func f_1001c3908() -> LocalizedStringResource {
        resource("general.action.save")
    }

    public static func f_1001c0788() -> LocalizedStringResource {
        resource("general.action.cancel")
    }

    public static func f_1001be988() -> LocalizedStringResource {
        resource("edit-item.toolbar.discard-changes")
    }

    public static func f_1001c1688() -> LocalizedStringResource {
        resource("general.action.edit")
    }

    public static func f_1001c3188() -> LocalizedStringResource {
        resource("general.action.restart-paste")
    }

    public static func f_1001bdd88() -> LocalizedStringResource {
        resource("diagnostics.start.title")
    }

    public static func f_1001bdc08() -> LocalizedStringResource {
        resource("diagnostics.start.message")
    }

    public static func f_1001be088() -> LocalizedStringResource {
        resource("diagnostics.stop.title")
    }

    public static func f_1001bdf08() -> LocalizedStringResource {
        resource("diagnostics.stop.message")
    }

    public static func f_1001bda88() -> LocalizedStringResource {
        resource("diagnostics.action.stop-and-copy-logs")
    }

    public static func f_1001c2a08() -> LocalizedStringResource {
        resource("general.action.pin")
    }

    public static func f_1001c3f08() -> LocalizedStringResource {
        resource("general.action.share")
    }

    public static func f_1001c0f08() -> LocalizedStringResource {
        resource("general.action.create-pinboard")
    }

    public static func f_1001c4208() -> LocalizedStringResource {
        resource("general.action.unpin")
    }

    public static func f_1001bee08() -> LocalizedStringResource {
        resource("edit-item.toolbar.image.rotate-left")
    }

    public static func f_1001bef88() -> LocalizedStringResource {
        resource("edit-item.toolbar.image.rotate-right")
    }

    public static func f_1001c4388() -> LocalizedStringResource {
        resource("general.browser")
    }

    public static func f_1001c6fb0() -> LocalizedStringResource {
        resource("item-type.multiple-files")
    }

    public static func f_1001c6f44() -> LocalizedStringResource { resource("item-type.color") }
    public static func f_1001c6f68() -> LocalizedStringResource { resource("item-type.image") }
    public static func f_1001c6f8c() -> LocalizedStringResource { resource("item-type.link") }
    public static func f_1001c7130() -> LocalizedStringResource { resource("item-type.text") }
    public static func f_1001c7154() -> LocalizedStringResource { resource("item-type.unknown") }

    public static func f_1001e6c38(_ count: Int32) -> LocalizedStringResource {
        countResource(count, key: "item-type.file-count")
    }

    public static func f_1001dac54() -> LocalizedStringResource {
        resource("preview.reveal-in-finder.title")
    }

    public static func f_1001e6b98(_ applicationName: String) -> LocalizedStringResource {
        LocalizedStringResource("general.action.open-in", defaultValue: "\(applicationName)",
                                table: "Localizable", locale: .current,
                                bundle: .atURL(resourceBundle.bundleURL))
    }

    private static func countResource(_ count: Int32, key: StaticString) -> LocalizedStringResource {
        LocalizedStringResource(key, defaultValue: "\(count)", table: "Localizable",
                                locale: .current, bundle: .atURL(resourceBundle.bundleURL))
    }

    public static func f_1001e6b38(_ count: Int32) -> LocalizedStringResource {
        countResource(count, key: "editor.character-count")
    }

    public static func f_1001e6b78(_ count: Int32) -> LocalizedStringResource {
        countResource(count, key: "editor.word-count")
    }

    public static func f_1001e6b58(_ count: Int32) -> LocalizedStringResource {
        countResource(count, key: "editor.line-count")
    }

}
