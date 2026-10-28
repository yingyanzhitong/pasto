import Foundation

public enum ClipboardKind: String, Codable, CaseIterable, Sendable {
    case text, link, image, files, richText, color, unknown

    public var displayName: String {
        switch self {
        case .text: return "文本"
        case .link: return "链接"
        case .image: return "图片"
        case .files: return "文件"
        case .richText: return "富文本"
        case .color: return "颜色"
        case .unknown: return "其他"
        }
    }
}

public struct ClipboardItem: Identifiable, Codable, Equatable, Sendable {
    public var id: UUID
    public var createdAt: Date
    public var updatedAt: Date
    public var title: String
    public var hasExplicitTitle: Bool?
    public var kind: ClipboardKind
    public var plainText: String?
    public var sourceName: String
    public var sourceBundleID: String?
    public var sourceApplicationBundleID: String?
    public var sourceApplicationRelationIsKnown: Bool?
    public var sourceDevice: String
    public var isInHistory: Bool
    public var payloads: [String: Data]
    public var imagePreviewMetadata: OriginalImagePreviewMetadata?
    public var rawPreview: Data?

    public var originalTitle: String? {
        if hasExplicitTitle == false || (hasExplicitTitle == nil && title.isEmpty) { return nil }
        return title
    }

    public var decodedImagePreviewMetadata: OriginalImagePreviewMetadata? {
        if let rawPreview { return OriginalImagePreviewMetadataCodec.decode(rawPreview) }
        return imagePreviewMetadata
    }
    public var decodedTextPreviewMetadata: OriginalTextPreviewMetadata? {
        OriginalImagePreviewMetadataCodec.decodeText(rawPreview)
    }
    public var decodedLinkPreviewMetadata: OriginalLinkPreviewMetadata? {
        OriginalImagePreviewMetadataCodec.decodeLink(rawPreview)
    }
    public var decodedColorPreviewMetadata: OriginalColorPreviewMetadata? {
        OriginalImagePreviewMetadataCodec.decodeColor(rawPreview)
    }
    public var decodedFilePreviewMetadata: OriginalFilePreviewMetadata? {
        OriginalImagePreviewMetadataCodec.decodeFiles(rawPreview)
    }
    public var pinboardIDs: Set<UUID>
    public var pinboardOwnerID: UUID?
    public var pinboardOrder: Int64?
    public var isDeleted: Bool

    public init(id: UUID = UUID(), createdAt: Date = Date(), updatedAt: Date? = nil,
                title: String = "", kind: ClipboardKind = .text, plainText: String? = nil,
                sourceName: String = "Pasto", sourceBundleID: String? = nil,
                payloads: [String: Data] = [:], pinboardIDs: Set<UUID> = [], isDeleted: Bool = false,
                sourceDevice: String = "此Mac", isInHistory: Bool = true,
                imagePreviewMetadata: OriginalImagePreviewMetadata? = nil,
                rawPreview: Data? = nil, hasExplicitTitle: Bool? = nil, pinboardOrder: Int64? = nil,
                sourceApplicationBundleID: String? = nil, pinboardOwnerID: UUID? = nil,
                sourceApplicationRelationIsKnown: Bool? = true) {
        self.id = id
        self.createdAt = createdAt
        self.updatedAt = updatedAt ?? createdAt
        self.title = title
        self.hasExplicitTitle = hasExplicitTitle ?? !title.isEmpty
        self.kind = kind
        self.plainText = plainText
        self.sourceName = sourceName
        self.sourceBundleID = sourceBundleID
        self.sourceApplicationBundleID = sourceApplicationBundleID
        self.sourceApplicationRelationIsKnown = sourceApplicationRelationIsKnown
        self.payloads = payloads
        self.imagePreviewMetadata = imagePreviewMetadata
        self.rawPreview = rawPreview
        self.pinboardIDs = pinboardIDs
        self.pinboardOwnerID = pinboardOwnerID
        self.pinboardOrder = pinboardOrder
        self.isDeleted = isDeleted
        self.sourceDevice = sourceDevice
        self.isInHistory = isInHistory
    }
}

public struct Pinboard: Identifiable, Codable, Equatable, Sendable {
    public var id: UUID
    public var name: String
    public var colorHex: String
    public var sortOrder: Int
    public var rawType: Int16?
    public var rawAttributes: Data?

    public init(id: UUID = UUID(), name: String = "新建 Pasto", colorHex: String = "#FF9500", sortOrder: Int = 0,
                rawType: Int16? = nil, rawAttributes: Data? = nil) {
        self.id = id
        self.name = name
        self.colorHex = colorHex
        self.sortOrder = sortOrder
        self.rawType = rawType
        self.rawAttributes = rawAttributes
    }
}

public struct AppPreferences: Codable, Equatable, Sendable {
    public var historyLimit: Int
    public var isMonitoringPaused: Bool
    public var pauseUntil: Date?
    public var excludedBundleIDs: [String]
    public var ignoredPasteboardTypes: [String]
    public var ignoreConcealedContent: Bool
    public var playSounds: Bool
    public var appearance: String
    public var panelHeight: Double
    public var launchAtLogin: Bool
    public var pasteToActiveApp: Bool
    public var alwaysPastePlainText: Bool
    public var historyRetentionDays: Int
    public var historyShortcut: KeyboardShortcut?
    public var stackShortcut: KeyboardShortcut?
    public var previousPinboardShortcut: KeyboardShortcut?
    public var nextPinboardShortcut: KeyboardShortcut?
    public var quickPasteModifierRawValue: UInt
    public var plainTextModifierRawValue: UInt
    public var showDuringScreenSharing: Bool
    public var ignoreTransientContent: Bool
    public var historyTitle: String
    public var stackItemIDs: [UUID]
    public var stackReversed: Bool
    public var isDiagnosticsEnabled: Bool
    public var useBinaryPlist: Bool
    public var fileQuickLookThumbnailsEnabled: Bool
    public var linkPreviewsEnabled: Bool

    public init(historyLimit: Int = 1000, isMonitoringPaused: Bool = false, pauseUntil: Date? = nil,
                excludedBundleIDs: [String] = [], ignoredPasteboardTypes: [String] = [], ignoreConcealedContent: Bool = true,
                playSounds: Bool = true, appearance: String = "system", panelHeight: Double = 332,
                launchAtLogin: Bool = false, pasteToActiveApp: Bool = true, alwaysPastePlainText: Bool = false,
                historyRetentionDays: Int = 30,
                historyShortcut: KeyboardShortcut? = KeyboardShortcut.historyDefault,
                stackShortcut: KeyboardShortcut? = KeyboardShortcut.stackDefault,
                previousPinboardShortcut: KeyboardShortcut? = KeyboardShortcut.previousPinboardDefault,
                nextPinboardShortcut: KeyboardShortcut? = KeyboardShortcut.nextPinboardDefault,
                quickPasteModifierRawValue: UInt = 1 << 20, plainTextModifierRawValue: UInt = 1 << 17,
                showDuringScreenSharing: Bool = true, ignoreTransientContent: Bool = true,
                historyTitle: String = "剪贴板", stackItemIDs: [UUID] = [], stackReversed: Bool = false,
                isDiagnosticsEnabled: Bool = false, useBinaryPlist: Bool = false,
                fileQuickLookThumbnailsEnabled: Bool = true, linkPreviewsEnabled: Bool = true) {
        self.historyLimit = historyLimit
        self.isMonitoringPaused = isMonitoringPaused
        self.pauseUntil = pauseUntil
        self.excludedBundleIDs = excludedBundleIDs
        self.ignoredPasteboardTypes = ignoredPasteboardTypes
        self.ignoreConcealedContent = ignoreConcealedContent
        self.playSounds = playSounds
        self.appearance = appearance
        self.panelHeight = panelHeight
        self.launchAtLogin = launchAtLogin
        self.pasteToActiveApp = pasteToActiveApp
        self.alwaysPastePlainText = alwaysPastePlainText
        self.historyRetentionDays = historyRetentionDays
        self.historyShortcut = historyShortcut
        self.stackShortcut = stackShortcut
        self.previousPinboardShortcut = previousPinboardShortcut
        self.nextPinboardShortcut = nextPinboardShortcut
        self.quickPasteModifierRawValue = quickPasteModifierRawValue
        self.plainTextModifierRawValue = plainTextModifierRawValue
        self.showDuringScreenSharing = showDuringScreenSharing
        self.ignoreTransientContent = ignoreTransientContent
        self.historyTitle = historyTitle
        self.stackItemIDs = stackItemIDs
        self.stackReversed = stackReversed
        self.isDiagnosticsEnabled = isDiagnosticsEnabled
        self.useBinaryPlist = useBinaryPlist
        self.fileQuickLookThumbnailsEnabled = fileQuickLookThumbnailsEnabled
        self.linkPreviewsEnabled = linkPreviewsEnabled
    }

    private enum CodingKeys: String, CodingKey {
        case historyLimit, isMonitoringPaused, pauseUntil, excludedBundleIDs, ignoredPasteboardTypes, ignoreConcealedContent
        case playSounds, appearance, panelHeight, launchAtLogin, pasteToActiveApp, alwaysPastePlainText, historyRetentionDays
        case historyShortcut, stackShortcut, previousPinboardShortcut, nextPinboardShortcut
        case quickPasteModifierRawValue, plainTextModifierRawValue, showDuringScreenSharing, ignoreTransientContent
        case historyTitle, stackItemIDs, stackReversed, isDiagnosticsEnabled, useBinaryPlist, fileQuickLookThumbnailsEnabled, linkPreviewsEnabled
    }

    public init(from decoder: Decoder) throws {
        let values = try decoder.container(keyedBy: CodingKeys.self)
        self.init(historyLimit: try values.decodeIfPresent(Int.self, forKey: .historyLimit) ?? 1000,
                  isMonitoringPaused: try values.decodeIfPresent(Bool.self, forKey: .isMonitoringPaused) ?? false,
                  pauseUntil: try values.decodeIfPresent(Date.self, forKey: .pauseUntil),
                  excludedBundleIDs: try values.decodeIfPresent([String].self, forKey: .excludedBundleIDs) ?? [],
                  ignoredPasteboardTypes: try values.decodeIfPresent([String].self, forKey: .ignoredPasteboardTypes) ?? [],
                  ignoreConcealedContent: try values.decodeIfPresent(Bool.self, forKey: .ignoreConcealedContent) ?? true,
                  playSounds: try values.decodeIfPresent(Bool.self, forKey: .playSounds) ?? true,
                  appearance: try values.decodeIfPresent(String.self, forKey: .appearance) ?? "system",
                  panelHeight: try values.decodeIfPresent(Double.self, forKey: .panelHeight) ?? 332,
                  launchAtLogin: try values.decodeIfPresent(Bool.self, forKey: .launchAtLogin) ?? false,
                  pasteToActiveApp: try values.decodeIfPresent(Bool.self, forKey: .pasteToActiveApp) ?? true,
                  alwaysPastePlainText: try values.decodeIfPresent(Bool.self, forKey: .alwaysPastePlainText) ?? false,
                  historyRetentionDays: try values.decodeIfPresent(Int.self, forKey: .historyRetentionDays) ?? 30,
                  historyShortcut: values.contains(.historyShortcut) ? try values.decodeIfPresent(KeyboardShortcut.self, forKey: .historyShortcut) : KeyboardShortcut.historyDefault,
                  stackShortcut: values.contains(.stackShortcut) ? try values.decodeIfPresent(KeyboardShortcut.self, forKey: .stackShortcut) : KeyboardShortcut.stackDefault,
                  previousPinboardShortcut: values.contains(.previousPinboardShortcut) ? try values.decodeIfPresent(KeyboardShortcut.self, forKey: .previousPinboardShortcut) : KeyboardShortcut.previousPinboardDefault,
                  nextPinboardShortcut: values.contains(.nextPinboardShortcut) ? try values.decodeIfPresent(KeyboardShortcut.self, forKey: .nextPinboardShortcut) : KeyboardShortcut.nextPinboardDefault,
                  quickPasteModifierRawValue: try values.decodeIfPresent(UInt.self, forKey: .quickPasteModifierRawValue) ?? (1 << 20),
                  plainTextModifierRawValue: try values.decodeIfPresent(UInt.self, forKey: .plainTextModifierRawValue) ?? (1 << 17),
                  showDuringScreenSharing: try values.decodeIfPresent(Bool.self, forKey: .showDuringScreenSharing) ?? true,
                  ignoreTransientContent: try values.decodeIfPresent(Bool.self, forKey: .ignoreTransientContent) ?? true,
                  historyTitle: try values.decodeIfPresent(String.self, forKey: .historyTitle) ?? "剪贴板",
                  stackItemIDs: try values.decodeIfPresent([UUID].self, forKey: .stackItemIDs) ?? [],
                  stackReversed: try values.decodeIfPresent(Bool.self, forKey: .stackReversed) ?? false,
                  isDiagnosticsEnabled: try values.decodeIfPresent(Bool.self, forKey: .isDiagnosticsEnabled) ?? false,
                  useBinaryPlist: try values.decodeIfPresent(Bool.self, forKey: .useBinaryPlist) ?? false,
                  fileQuickLookThumbnailsEnabled: try values.decodeIfPresent(Bool.self, forKey: .fileQuickLookThumbnailsEnabled) ?? true,
                  linkPreviewsEnabled: try values.decodeIfPresent(Bool.self, forKey: .linkPreviewsEnabled) ?? true)
    }

    public func encode(to encoder: Encoder) throws {
        var values = encoder.container(keyedBy: CodingKeys.self)
        try values.encode(historyLimit, forKey: .historyLimit)
        try values.encode(isMonitoringPaused, forKey: .isMonitoringPaused)
        try values.encodeIfPresent(pauseUntil, forKey: .pauseUntil)
        try values.encode(excludedBundleIDs, forKey: .excludedBundleIDs)
        try values.encode(ignoredPasteboardTypes, forKey: .ignoredPasteboardTypes)
        try values.encode(ignoreConcealedContent, forKey: .ignoreConcealedContent)
        try values.encode(playSounds, forKey: .playSounds)
        try values.encode(appearance, forKey: .appearance)
        try values.encode(panelHeight, forKey: .panelHeight)
        try values.encode(launchAtLogin, forKey: .launchAtLogin)
        try values.encode(pasteToActiveApp, forKey: .pasteToActiveApp)
        try values.encode(alwaysPastePlainText, forKey: .alwaysPastePlainText)
        try values.encode(historyRetentionDays, forKey: .historyRetentionDays)
        // nil 必须编码为 null，不能省略，否则重载会恢复默认快捷键。
        try values.encode(historyShortcut, forKey: .historyShortcut)
        try values.encode(stackShortcut, forKey: .stackShortcut)
        try values.encode(previousPinboardShortcut, forKey: .previousPinboardShortcut)
        try values.encode(nextPinboardShortcut, forKey: .nextPinboardShortcut)
        try values.encode(quickPasteModifierRawValue, forKey: .quickPasteModifierRawValue)
        try values.encode(plainTextModifierRawValue, forKey: .plainTextModifierRawValue)
        try values.encode(showDuringScreenSharing, forKey: .showDuringScreenSharing)
        try values.encode(ignoreTransientContent, forKey: .ignoreTransientContent)
        try values.encode(historyTitle, forKey: .historyTitle)
        try values.encode(stackItemIDs, forKey: .stackItemIDs)
        try values.encode(stackReversed, forKey: .stackReversed)
        try values.encode(isDiagnosticsEnabled, forKey: .isDiagnosticsEnabled)
        try values.encode(useBinaryPlist, forKey: .useBinaryPlist)
        try values.encode(fileQuickLookThumbnailsEnabled, forKey: .fileQuickLookThumbnailsEnabled)
        try values.encode(linkPreviewsEnabled, forKey: .linkPreviewsEnabled)
    }
}

public enum ClipboardStoreError: LocalizedError {
    case itemNotFound, pinboardNotFound, missingPlainText, pasteboardWriteFailed
    case invalidPinboardName, invalidPinboardOrder, unsupportedArchiveVersion, duplicateIdentifiers, invalidSourceApplication

    public var errorDescription: String? {
        switch self {
        case .itemNotFound: return "未找到剪贴板项目。"
        case .pinboardNotFound: return "未找到 Pasto。"
        case .missingPlainText: return "此项目没有可用的纯文本。"
        case .pasteboardWriteFailed: return "写入剪贴板失败。"
        case .invalidPinboardName: return "Pasto 名称不能为空。"
        case .invalidPinboardOrder: return "Pasto 项目移动位置无效。"
        case .invalidSourceApplication: return "来源应用记录缺失或关联无效。"
        case .unsupportedArchiveVersion: return "不支持此存档版本。"
        case .duplicateIdentifiers: return "存档中包含重复标识符。"
        }
    }
}
