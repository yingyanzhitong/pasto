import AppKit
import Foundation

public enum OriginalSourceApplicationColors {
    private static let overrides: [String: UInt64] = [
        "com.wiheads.paste": 0xf8b92e,
        "com.wiheads.paste-direct": 0xf8b92e,
        "com.wiheads.paste-setapp": 0xf8b92e,
        "com.adobe.Acrobat": 0x9b0a00,
        "com.adobe.AfterEffects": 0x3b3b92,
        "com.adobe.Dreamweaver": 0x285c28,
        "com.adobe.flash": 0x901313,
        "com.adobe.Fonts": 0x34363a,
        "com.adobe.illustrator": 0xe58b00,
        "com.adobe.InDesign": 0xc0264d,
        "com.adobe.Lean": 0x74528f,
        "com.adobe.Photoshop": 0x5c90,
        "com.adobe.RoboHelp": 0xa957c,
        "com.adobe.XD": 0x85156b,
        "com.agilebits.onepassword7": 0x299de6,
        "com.apple.AddressBook": 0xab8248,
        "com.apple.AppStore": 0x62a9f5,
        "com.apple.calculator": 0x5b5f61,
        "com.apple.dt.Xcode": 0x62a9f5,
        "com.apple.finder": 0x62a9f5,
        "com.apple.iCal": 0xf0554d,
        "com.apple.iBooksX": 0xfa9214,
        "com.apple.iWork.Keynote": 0x62a9f5,
        "com.apple.iWork.Numbers": 0x52cc64,
        "com.apple.iWork.Pages": 0xfa9214,
        "com.apple.mail": 0x62a9f5,
        "com.apple.Photos": 0xf0554d,
        "com.apple.reminders": 0xf0554d,
        "com.apple.Safari": 0x62a9f5,
        "com.apple.Terminal": 0x454d4d,
        "com.apple.TextEdit": 0x9c9c9c,
        "com.bohemiancoding.sketch3": 0xff8d00,
        "com.figma.Desktop": 0x18a0fb,
        "com.framer.electron": 0x2983da,
        "com.google.Chrome": 0x4285f4,
        "com.linear": 0xf1011,
        "com.microsoft.Excel": 0x107c41,
        "com.microsoft.onenote.mac": 0x963cba,
        "com.microsoft.Outlook": 0x78d4,
        "com.microsoft.Powerpoint": 0xcf4d2b,
        "com.microsoft.teams": 0x4650c2,
        "com.microsoft.Word": 0x185abd,
        "com.microsoft.VSCode": 0xd76bd,
        "com.tinyspeck.slackmacgap": 0x611f69,
        "notion.id": 0x0,
        "ru.keepcoder.Telegram": 0x50a5df,
        "com.tdesktop.Telegram": 0x50a5df,
    ]

    @MainActor
    public static func rawColor(bundleIdentifier: String, image: NSImage) -> UInt64 {
        let color: NSColor
        if let override = overrides[bundleIdentifier] {
            color = OriginalColorPreviewMetadataGenerator.color(override)
        } else {
            color = OriginalSourceApplicationImageColor.prominentColor(image) ?? .gray
        }
        return encoded(color)
    }

    @MainActor
    public static func encoded(_ color: NSColor) -> UInt64 {
        guard let rgb = color.usingColorSpace(.deviceRGB) else {
            preconditionFailure("Source application color cannot convert to device RGB")
        }
        var red: CGFloat = 0
        var green: CGFloat = 0
        var blue: CGFloat = 0
        var alpha: CGFloat = 0
        rgb.getRed(&red, green: &green, blue: &blue, alpha: &alpha)
        let alphaValue = UInt64(alpha * 255)
        let redValue = UInt64(red * 255)
        let greenValue = UInt64(green * 255)
        let blueValue = UInt64(blue * 255)
        return (alphaValue << 24) | (redValue << 16) | (greenValue << 8) | blueValue
    }
}
