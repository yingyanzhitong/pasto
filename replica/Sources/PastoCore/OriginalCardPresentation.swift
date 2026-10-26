import AppKit

public struct OriginalCardPresentation: Equatable, Sendable {
    public let isCompactContentFullsize: Bool
    public let preferredCompactHeaderStyle: UInt8

    public init(isCompactContentFullsize: Bool, preferredCompactHeaderStyle: UInt8) {
        self.isCompactContentFullsize = isCompactContentFullsize
        self.preferredCompactHeaderStyle = preferredCompactHeaderStyle
    }

    @MainActor
    public static func resolve(_ item: ClipboardItem, linkPreviewsEnabled: Bool) -> Self? {
        switch item.kind {
        case .image:
            guard item.decodedImagePreviewMetadata != nil else { return nil }
            return Self(isCompactContentFullsize: true, preferredCompactHeaderStyle: 1)
        case .color:
            guard item.decodedColorPreviewMetadata != nil else { return nil }
            return Self(isCompactContentFullsize: true, preferredCompactHeaderStyle: 0)
        case .files:
            guard item.decodedFilePreviewMetadata != nil else { return nil }
            return Self(isCompactContentFullsize: false, preferredCompactHeaderStyle: 2)
        case .text, .richText:
            guard item.decodedTextPreviewMetadata != nil else { return nil }
            return Self(isCompactContentFullsize: false, preferredCompactHeaderStyle: 2)
        case .link:
            guard let metadata = item.decodedLinkPreviewMetadata else { return nil }
            guard linkPreviewsEnabled else {
                return Self(isCompactContentFullsize: false, preferredCompactHeaderStyle: 2)
            }
            let image = metadata.imageData.flatMap(NSImage.init(data:))
            let style: UInt8 = image.map { $0.size.width == $0.size.height ? 0 : 1 } ?? 0
            return Self(isCompactContentFullsize: true, preferredCompactHeaderStyle: style)
        case .unknown:
            return nil
        }
    }

    public struct Geometry: Equatable, Sendable {
        public let bodyTop: CGFloat
        public let headerHeight: CGFloat
        public let lockCenterOffset: CGFloat

        public init(bodyTop: CGFloat, headerHeight: CGFloat, lockCenterOffset: CGFloat) {
            self.bodyTop = bodyTop
            self.headerHeight = headerHeight
            self.lockCenterOffset = lockCenterOffset
        }
    }

    /// The three independent constraint values returned by f_1003d8588.
    public func geometry(sizeClass: UInt8, modernOS: Bool) -> Geometry {
        switch sizeClass {
        case 0: return Geometry(bodyTop: 56, headerHeight: 56, lockCenterOffset: -10)
        case 1: return Geometry(bodyTop: 52, headerHeight: 52, lockCenterOffset: -10)
        case 2: return Geometry(bodyTop: 48, headerHeight: 48, lockCenterOffset: -10)
        default:
            let height: CGFloat = modernOS ? 36 : 34
            return Geometry(bodyTop: isCompactContentFullsize ? 0 : height,
                            headerHeight: height,
                            lockCenterOffset: isCompactContentFullsize ? (modernOS ? 8 : 7) : -10)
        }
    }
}
