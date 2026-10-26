import AppKit

public enum OriginalPinboardColor: UInt8, CaseIterable, Sendable {
    case red = 0
    case orange
    case yellow
    case green
    case blue
    case purple
    case pink
    case gray

    public init(canonicalColorCode: UInt64) {
        switch canonicalColorCode {
        case 0xfa9214, 0xfffa9214: self = .orange
        case 0xfab700, 0xfffab700: self = .yellow
        case 0x52cc64, 0xff52cc64: self = .green
        case 0x62a9f5, 0xff62a9f5: self = .blue
        case 0xb663e0, 0xffb663e0: self = .purple
        case 0xfa506f, 0xfffa506f: self = .pink
        case 0x8f8f93, 0xff8f8f93: self = .gray
        default: self = .red
        }
    }

    public var canonicalColorCode: UInt64 {
        switch self {
        case .red: return 0xf0554d
        case .orange: return 0xfa9214
        case .yellow: return 0xfab700
        case .green: return 0x52cc64
        case .blue: return 0x62a9f5
        case .purple: return 0xb663e0
        case .pink: return 0xfa506f
        case .gray: return 0x8f8f93
        }
    }

    @MainActor
    public func color() -> NSColor {
        let provider: NSColor
        switch self {
        case .red: provider = Self.redProvider
        case .orange: provider = Self.orangeProvider
        case .yellow: provider = Self.yellowProvider
        case .green: provider = Self.greenProvider
        case .blue: provider = Self.blueProvider
        case .purple: provider = Self.purpleProvider
        case .pink: provider = Self.pinkProvider
        case .gray: provider = Self.grayProvider
        }
        let code = canonicalColorCode
        let fixed = NSColor(red: CGFloat((code >> 16) & 255) / 255,
                            green: CGFloat((code >> 8) & 255) / 255,
                            blue: CGFloat(code & 255) / 255, alpha: 1)
        if #available(macOS 26.0, *) { return provider }
        return fixed
    }

    @MainActor private static let redProvider = NSColor.systemRed
    @MainActor private static let orangeProvider = NSColor.systemOrange
    @MainActor private static let greenProvider = NSColor.systemGreen
    @MainActor private static let blueProvider = NSColor.systemBlue
    @MainActor private static let purpleProvider = NSColor.systemPurple
    @MainActor private static let pinkProvider = NSColor.systemPink
    @MainActor private static let yellowProvider = dynamicColor(light: 0xf2b600, dark: 0xf2b600)
    @MainActor private static let grayProvider = dynamicColor(light: 0x8e8e93, dark: 0x98989d)

    @MainActor
    private static func dynamicColor(light: UInt64, dark: UInt64) -> NSColor {
        let lightColor = NSColor(red: CGFloat((light >> 16) & 255) / 255,
                                 green: CGFloat((light >> 8) & 255) / 255,
                                 blue: CGFloat(light & 255) / 255, alpha: 1)
        let darkColor = NSColor(red: CGFloat((dark >> 16) & 255) / 255,
                                green: CGFloat((dark >> 8) & 255) / 255,
                                blue: CGFloat(dark & 255) / 255, alpha: 1)
        return NSColor(name: nil) { appearance in
            OriginalSearchAppearance.f_1001ff49c(appearance: appearance, dark: darkColor, light: lightColor)
        }
    }
}
