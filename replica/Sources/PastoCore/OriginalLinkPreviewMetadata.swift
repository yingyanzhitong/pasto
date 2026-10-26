import Foundation

public struct OriginalLinkPreviewMetadata: Equatable, Sendable {
    public var url: URL
    public var name: String?
    public var iconData: Data?
    public var imageData: Data?

    public init(url: URL, name: String? = nil, iconData: Data? = nil, imageData: Data? = nil) {
        self.url = url
        self.name = name
        self.iconData = iconData
        self.imageData = imageData
    }
}

/// The local initial value from f_100319778, before its optional asynchronous provider branch.
public enum OriginalLinkPreviewMetadataGenerator {
    public static func generate(_ items: [OriginalPasteboardItem]) -> OriginalLinkPreviewMetadata? {
        guard let first = items.first, let url = first.f_10037ce0c() else { return nil }
        let name = first.f_10037e4b8(forType: "public.url-name")?
            .trimmingCharacters(in: .whitespacesAndNewlines)
        return OriginalLinkPreviewMetadata(url: url, name: name)
    }
}
