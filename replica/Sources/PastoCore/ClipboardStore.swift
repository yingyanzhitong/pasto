import AppKit
import Combine
import Darwin
import Foundation

private struct StoreState: Codable, Equatable {
    var schemaVersion = 1
    var items: [ClipboardItem] = []
    var pinboards: [Pinboard] = []
    var preferences = AppPreferences()
    var sourceApplications: [SourceApplicationRecord] = []

    init(items: [ClipboardItem] = [], pinboards: [Pinboard] = [], preferences: AppPreferences = AppPreferences(),
         sourceApplications: [SourceApplicationRecord] = []) {
        self.items = items
        self.pinboards = pinboards
        self.preferences = preferences
        self.sourceApplications = sourceApplications
    }

    private enum CodingKeys: String, CodingKey {
        case schemaVersion, items, pinboards, preferences, sourceApplications
    }

    init(from decoder: Decoder) throws {
        let values = try decoder.container(keyedBy: CodingKeys.self)
        schemaVersion = try values.decode(Int.self, forKey: .schemaVersion)
        items = try values.decode([ClipboardItem].self, forKey: .items)
        pinboards = try values.decode([Pinboard].self, forKey: .pinboards)
        preferences = try values.decode(AppPreferences.self, forKey: .preferences)
        sourceApplications = try values.decodeIfPresent([SourceApplicationRecord].self, forKey: .sourceApplications) ?? []
    }
}

private struct DiskRevision: Equatable {
    var inode: UInt64
    var size: UInt64
    var modified: Date
}

@MainActor
public final class ClipboardStore: ObservableObject {
    @Published public var items: [ClipboardItem] = []
    @Published public var pinboards: [Pinboard] = []
    @Published public private(set) var sourceApplications: [SourceApplicationRecord] = []
    public let didRestoreItem = PassthroughSubject<Void, Never>()
    public let preferenceChanges = PassthroughSubject<(old: AppPreferences, new: AppPreferences), Never>()
    @Published public var preferences = AppPreferences() {
        didSet { preferenceChanges.send((oldValue, preferences)) }
    }
    public let directoryURL: URL
    private var baseline = StoreState()
    private var diskRevision: DiskRevision?

    public static var defaultDirectoryURL: URL {
        FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("PasteReplica", isDirectory: true)
    }

    public init(directoryURL: URL) throws {
        self.directoryURL = directoryURL
        try FileManager.default.createDirectory(at: directoryURL, withIntermediateDirectories: true,
                                                attributes: [.posixPermissions: 0o700])
        try FileManager.default.setAttributes([.posixPermissions: 0o700], ofItemAtPath: directoryURL.path)
        try reload()
    }

    private var stateURL: URL { directoryURL.appendingPathComponent("clipboard.json") }
    private var current: StoreState {
        StoreState(items: items, pinboards: pinboards, preferences: preferences, sourceApplications: sourceApplications)
    }

    private func publish(_ state: StoreState, persisted: StoreState? = nil) {
        if items != state.items { items = state.items }
        if pinboards != state.pinboards { pinboards = state.pinboards }
        if sourceApplications != state.sourceApplications { sourceApplications = state.sourceApplications }
        if preferences != state.preferences { preferences = state.preferences }
        baseline = persisted ?? state
    }

    private func withLock<T>(_ operation: () throws -> T) throws -> T {
        let path = directoryURL.appendingPathComponent(".lock").path
        let descriptor = Darwin.open(path, O_CREAT | O_RDWR, 0o600)
        guard descriptor >= 0 else { throw POSIXError(POSIXErrorCode(rawValue: errno) ?? .EIO) }
        defer { Darwin.close(descriptor) }
        guard flock(descriptor, LOCK_EX) == 0 else { throw POSIXError(POSIXErrorCode(rawValue: errno) ?? .EIO) }
        defer { flock(descriptor, LOCK_UN) }
        // Catch inside the flock scope so the converted Swift Error executes both defers.
        return try OriginalObjCExceptionBridge.withResult(operation)
    }

    private func validate(_ state: StoreState) throws {
        guard state.schemaVersion == 1 else { throw ClipboardStoreError.unsupportedArchiveVersion }
        guard Set(state.items.map(\.id)).count == state.items.count,
              Set(state.pinboards.map(\.id)).count == state.pinboards.count else {
            throw ClipboardStoreError.duplicateIdentifiers
        }
        let boardIDs = Set(state.pinboards.map(\.id))
        guard state.items.allSatisfy({ item in
            item.pinboardOwnerID.map { boardIDs.contains($0) && item.pinboardIDs.contains($0) } ?? true
        }) else { throw ClipboardStoreError.pinboardNotFound }
        let applicationIDs = Set(state.sourceApplications.map(\.bundleIdentifier))
        guard applicationIDs.count == state.sourceApplications.count,
              state.sourceApplications.allSatisfy({ $0.rawColor.map { $0 < (UInt64(1) << 63) } ?? true }),
              state.items.allSatisfy({ $0.sourceApplicationBundleID.map(applicationIDs.contains) ?? true }) else {
            throw ClipboardStoreError.invalidSourceApplication
        }
    }

    private func readState() throws -> StoreState {
        guard FileManager.default.fileExists(atPath: stateURL.path) else { return StoreState() }
        let state = try JSONDecoder().decode(StoreState.self, from: Data(contentsOf: stateURL))
        try validate(state)
        return state
    }

    private func revision() throws -> DiskRevision? {
        guard FileManager.default.fileExists(atPath: stateURL.path) else { return nil }
        let attributes = try FileManager.default.attributesOfItem(atPath: stateURL.path)
        return DiskRevision(inode: (attributes[.systemFileNumber] as? NSNumber)?.uint64Value ?? 0,
                            size: (attributes[.size] as? NSNumber)?.uint64Value ?? 0,
                            modified: attributes[.modificationDate] as? Date ?? .distantPast)
    }

    private func latestState() throws -> StoreState {
        if try revision() == diskRevision { return baseline }
        return try readState()
    }

    private func writeAtomically(_ data: Data, to url: URL) throws {
        let temporary = url.deletingLastPathComponent().appendingPathComponent(".pasto-\(UUID().uuidString).tmp")
        guard FileManager.default.createFile(atPath: temporary.path, contents: nil,
                                              attributes: [.posixPermissions: 0o600]) else {
            throw CocoaError(.fileWriteUnknown)
        }
        defer { try? FileManager.default.removeItem(at: temporary) }
        let handle = try FileHandle(forWritingTo: temporary)
        do {
            try handle.write(contentsOf: data)
            try handle.synchronize()
            try handle.close()
        } catch {
            try? handle.close()
            throw error
        }
        guard Darwin.rename(temporary.path, url.path) == 0 else {
            throw POSIXError(POSIXErrorCode(rawValue: errno) ?? .EIO)
        }
        let parent = Darwin.open(url.deletingLastPathComponent().path, O_RDONLY)
        if parent >= 0 { _ = fsync(parent); Darwin.close(parent) }
    }

    private func mergedEntities<T: Identifiable & Equatable>(_ local: [T], _ base: [T], _ remote: [T],
                                                            merge: (T, T, T) -> T) -> [T] where T.ID == UUID {
        let old = Dictionary(uniqueKeysWithValues: base.map { ($0.id, $0) })
        let localByID = Dictionary(uniqueKeysWithValues: local.map { ($0.id, $0) })
        var result = Dictionary(uniqueKeysWithValues: remote.map { ($0.id, $0) })
        for id in old.keys where localByID[id] == nil { result.removeValue(forKey: id) }
        for value in local where old[value.id] != value {
            if let original = old[value.id] {
                // A permanent removal in another process must not be resurrected by a stale edit.
                if let current = result[value.id] { result[value.id] = merge(value, original, current) }
            } else {
                result[value.id] = value
            }
        }
        return Array(result.values)
    }

    private func merge(_ local: StoreState, onto remote: StoreState) -> StoreState {
        var result = remote
        result.items = mergedEntities(local.items, baseline.items, remote.items) { local, base, remote in
            var value = remote
            if local.createdAt != base.createdAt { value.createdAt = local.createdAt }
            if local.updatedAt != base.updatedAt { value.updatedAt = max(local.updatedAt, remote.updatedAt) }
            if local.title != base.title || local.hasExplicitTitle != base.hasExplicitTitle {
                value.title = local.title
                value.hasExplicitTitle = local.hasExplicitTitle
            }
            if local.kind != base.kind { value.kind = local.kind }
            if local.plainText != base.plainText { value.plainText = local.plainText }
            if local.sourceName != base.sourceName { value.sourceName = local.sourceName }
            if local.sourceBundleID != base.sourceBundleID { value.sourceBundleID = local.sourceBundleID }
            if local.sourceApplicationBundleID != base.sourceApplicationBundleID ||
                local.sourceApplicationRelationIsKnown != base.sourceApplicationRelationIsKnown {
                value.sourceApplicationBundleID = local.sourceApplicationBundleID
                value.sourceApplicationRelationIsKnown = local.sourceApplicationRelationIsKnown
            }
            if local.sourceDevice != base.sourceDevice { value.sourceDevice = local.sourceDevice }
            if local.isInHistory != base.isInHistory { value.isInHistory = local.isInHistory }
            if local.payloads != base.payloads {
                value.payloads = local.payloads
                value.imagePreviewMetadata = local.imagePreviewMetadata
                value.rawPreview = local.rawPreview
            } else if (local.imagePreviewMetadata != base.imagePreviewMetadata || local.rawPreview != base.rawPreview),
                      remote.payloads == base.payloads {
                value.imagePreviewMetadata = local.imagePreviewMetadata
                value.rawPreview = local.rawPreview
            }
            // A local ownership change replaces the relation; merging additions can recreate two owners.
            // Unchanged legacy memberships retain the latest persisted value.
            if local.pinboardIDs != base.pinboardIDs {
                value.pinboardIDs = local.pinboardIDs
                value.pinboardOwnerID = local.pinboardOwnerID
                value.pinboardOrder = local.pinboardOrder
            } else if remote.pinboardIDs == base.pinboardIDs, remote.pinboardOwnerID == base.pinboardOwnerID {
                if local.pinboardOwnerID != base.pinboardOwnerID { value.pinboardOwnerID = local.pinboardOwnerID }
                if local.pinboardOrder != base.pinboardOrder { value.pinboardOrder = local.pinboardOrder }
            }
            if local.isDeleted != base.isDeleted { value.isDeleted = local.isDeleted }
            return value
        }
        result.pinboards = mergedEntities(local.pinboards, baseline.pinboards, remote.pinboards) { local, base, remote in
            var value = remote
            if local.name != base.name { value.name = local.name }
            if local.colorHex != base.colorHex || local.rawType != base.rawType || local.rawAttributes != base.rawAttributes {
                value.colorHex = local.colorHex
                value.rawType = local.rawType
                value.rawAttributes = local.rawAttributes
            }
            if local.sortOrder != base.sortOrder { value.sortOrder = local.sortOrder }
            return value
        }
        let oldApplications = Dictionary(uniqueKeysWithValues: baseline.sourceApplications.map { ($0.bundleIdentifier, $0) })
        for application in local.sourceApplications where oldApplications[application.bundleIdentifier] != application {
            var changed = application
            if let old = oldApplications[application.bundleIdentifier],
               let current = result.sourceApplications.first(where: { $0.bundleIdentifier == application.bundleIdentifier }) {
                if application.rawIcon == old.rawIcon, application.rawColor == old.rawColor {
                    changed.rawIcon = current.rawIcon
                    changed.rawColor = current.rawColor
                }
                if application.name == old.name { changed.name = current.name }
            }
            Self.upsertSourceApplication(changed, in: &result)
        }
        let local = local.preferences, base = baseline.preferences
        if local.historyLimit != base.historyLimit { result.preferences.historyLimit = local.historyLimit }
        if local.isMonitoringPaused != base.isMonitoringPaused { result.preferences.isMonitoringPaused = local.isMonitoringPaused }
        if local.pauseUntil != base.pauseUntil { result.preferences.pauseUntil = local.pauseUntil }
        if local.excludedBundleIDs != base.excludedBundleIDs { result.preferences.excludedBundleIDs = local.excludedBundleIDs }
        if local.ignoredPasteboardTypes != base.ignoredPasteboardTypes { result.preferences.ignoredPasteboardTypes = local.ignoredPasteboardTypes }
        if local.ignoreConcealedContent != base.ignoreConcealedContent { result.preferences.ignoreConcealedContent = local.ignoreConcealedContent }
        if local.playSounds != base.playSounds { result.preferences.playSounds = local.playSounds }
        if local.appearance != base.appearance { result.preferences.appearance = local.appearance }
        if local.panelHeight != base.panelHeight { result.preferences.panelHeight = local.panelHeight }
        if local.launchAtLogin != base.launchAtLogin { result.preferences.launchAtLogin = local.launchAtLogin }
        if local.pasteToActiveApp != base.pasteToActiveApp { result.preferences.pasteToActiveApp = local.pasteToActiveApp }
        if local.alwaysPastePlainText != base.alwaysPastePlainText { result.preferences.alwaysPastePlainText = local.alwaysPastePlainText }
        if local.historyRetentionDays != base.historyRetentionDays { result.preferences.historyRetentionDays = local.historyRetentionDays }
        if local.historyShortcut != base.historyShortcut { result.preferences.historyShortcut = local.historyShortcut }
        if local.stackShortcut != base.stackShortcut { result.preferences.stackShortcut = local.stackShortcut }
        if local.previousPinboardShortcut != base.previousPinboardShortcut { result.preferences.previousPinboardShortcut = local.previousPinboardShortcut }
        if local.nextPinboardShortcut != base.nextPinboardShortcut { result.preferences.nextPinboardShortcut = local.nextPinboardShortcut }
        if local.quickPasteModifierRawValue != base.quickPasteModifierRawValue { result.preferences.quickPasteModifierRawValue = local.quickPasteModifierRawValue }
        if local.plainTextModifierRawValue != base.plainTextModifierRawValue { result.preferences.plainTextModifierRawValue = local.plainTextModifierRawValue }
        if local.showDuringScreenSharing != base.showDuringScreenSharing { result.preferences.showDuringScreenSharing = local.showDuringScreenSharing }
        if local.ignoreTransientContent != base.ignoreTransientContent { result.preferences.ignoreTransientContent = local.ignoreTransientContent }
        if local.historyTitle != base.historyTitle { result.preferences.historyTitle = local.historyTitle }
        if local.stackItemIDs != base.stackItemIDs { result.preferences.stackItemIDs = local.stackItemIDs }
        if local.stackReversed != base.stackReversed { result.preferences.stackReversed = local.stackReversed }
        if local.isDiagnosticsEnabled != base.isDiagnosticsEnabled { result.preferences.isDiagnosticsEnabled = local.isDiagnosticsEnabled }
        if local.useBinaryPlist != base.useBinaryPlist { result.preferences.useBinaryPlist = local.useBinaryPlist }
        if local.fileQuickLookThumbnailsEnabled != base.fileQuickLookThumbnailsEnabled { result.preferences.fileQuickLookThumbnailsEnabled = local.fileQuickLookThumbnailsEnabled }
        if local.linkPreviewsEnabled != base.linkPreviewsEnabled { result.preferences.linkPreviewsEnabled = local.linkPreviewsEnabled }
        return result
    }

    private func normalize(_ state: inout StoreState) {
        let boards = Set(state.pinboards.map(\.id))
        for i in state.items.indices {
            state.items[i].pinboardIDs.formIntersection(boards)
            if let owner = state.items[i].pinboardOwnerID, !state.items[i].pinboardIDs.contains(owner) {
                state.items[i].pinboardOwnerID = nil
            }
            if state.items[i].pinboardIDs.isEmpty { state.items[i].pinboardOrder = nil }
        }
        state.items.sort { $0.updatedAt == $1.updatedAt ? $0.id.uuidString < $1.id.uuidString : $0.updatedAt > $1.updatedAt }
        state.pinboards.sort { $0.sortOrder == $1.sortOrder ? $0.id.uuidString < $1.id.uuidString : $0.sortOrder < $1.sortOrder }
        state.sourceApplications.sort { $0.bundleIdentifier < $1.bundleIdentifier }
    }

    private static func upsertSourceApplication(_ application: SourceApplicationRecord, in state: inout StoreState) {
        let incomingIcon = application.rawIcon
        if let index = state.sourceApplications.firstIndex(where: { $0.bundleIdentifier == application.bundleIdentifier }) {
            if state.sourceApplications[index].name.isEmpty { state.sourceApplications[index].name = application.name }
            if OriginalSourceApplication.normalizedIcon(state.sourceApplications[index].rawIcon) != incomingIcon {
                state.sourceApplications[index].rawIcon = incomingIcon
                state.sourceApplications[index].rawColor = application.rawColor
            } else if state.sourceApplications[index].rawColor == nil, let color = application.rawColor {
                // Records saved before source-app colors existed gain one on an explicit later write.
                state.sourceApplications[index].rawColor = color
            }
        } else {
            state.sourceApplications.append(SourceApplicationRecord(bundleIdentifier: application.bundleIdentifier,
                name: application.name, rawIcon: incomingIcon, rawColor: application.rawColor))
        }
    }

    public func sourceApplication(for item: ClipboardItem) -> SourceApplicationRecord? {
        guard let identifier = item.sourceApplicationBundleID else { return nil }
        return sourceApplications.first { $0.bundleIdentifier == identifier }
    }

    public func pinboardOwner(for item: ClipboardItem) -> Pinboard? {
        guard let identifier = item.pinboardOwnerID else { return nil }
        return pinboards.first { $0.id == identifier }
    }

    private func expireHistory(_ state: inout StoreState) {
        guard state.preferences.historyRetentionDays > 0 else { return }
        let cutoff = Date().addingTimeInterval(-Double(state.preferences.historyRetentionDays) * 86_400)
        state.items.removeAll { $0.isInHistory && $0.pinboardIDs.isEmpty && $0.createdAt < cutoff }
    }

    private func mutate<T>(historyAction: Bool = false, _ change: (inout StoreState) throws -> T) throws -> T {
        let local = current
        try validate(local)
        return try withLock {
            let remote = try latestState()
            var state = merge(local, onto: remote)
            let result = try change(&state)
            try validate(state)
            normalize(&state)
            if historyAction || state.preferences.historyRetentionDays != remote.preferences.historyRetentionDays {
                expireHistory(&state)
            }
            if state != remote || !FileManager.default.fileExists(atPath: stateURL.path) {
                let encoder = JSONEncoder()
                encoder.outputFormatting = [.sortedKeys]
                try writeAtomically(encoder.encode(state), to: stateURL)
            }
            diskRevision = try revision()
            publish(state)
            return result
        }
    }

    /// Restore promotes the selected content in reverse order, as the original history repository does.
    func recordRestoredItems(ids: [UUID]) throws {
        try mutate(historyAction: true) { state in
            for id in ids.reversed() {
                guard let index = state.items.firstIndex(where: { $0.id == id && !$0.isDeleted }) else {
                    throw ClipboardStoreError.itemNotFound
                }
                let timestamp = Date()
                state.items[index].createdAt = timestamp
                state.items[index].updatedAt = timestamp
                state.items[index].isInHistory = true
            }
        }
    }

    public func save() throws { try mutate { _ in } }
    public func reload() throws {
        let local = current
        try validate(local)
        try withLock {
            if local == baseline, try revision() == diskRevision { return }
            let remote = try latestState()
            // A timer refresh must not discard edits that have not reached save() yet.
            var merged = merge(local, onto: remote)
            // Entity merging uses dictionaries; restore persisted group/item ordering on reopen.
            normalize(&merged)
            publish(merged, persisted: remote)
            diskRevision = try revision()
        }
    }

    private static func withPreviewMetadata(_ item: ClipboardItem, binaryPropertyList: Bool, preferQuickLookThumbnails: Bool, generateMissingContentPreview: Bool) -> ClipboardItem {
        var item = item
        guard item.kind == .image else {
            item.imagePreviewMetadata = nil
            if generateMissingContentPreview, [.files, .color, .text, .richText, .link].contains(item.kind), item.rawPreview == nil,
               let items = try? originalPasteboardItems(from: item.payloads) {
                if item.kind == .files {
                    let metadata = OriginalFilePreviewMetadataGenerator.generate(items, preferQuickLookThumbnails: preferQuickLookThumbnails)
                    item.rawPreview = OriginalImagePreviewMetadataCodec.encodeFiles(metadata, binaryPropertyList: binaryPropertyList)
                } else if item.kind == .color {
                    item.rawPreview = OriginalImagePreviewMetadataCodec.encodeColor(
                        OriginalColorPreviewMetadataGenerator.generate(items), binaryPropertyList: binaryPropertyList)
                } else if item.kind == .link {
                    item.rawPreview = OriginalImagePreviewMetadataCodec.encodeLink(
                        OriginalLinkPreviewMetadataGenerator.generate(items), binaryPropertyList: binaryPropertyList)
                } else {
                    item.rawPreview = OriginalImagePreviewMetadataCodec.encodeText(
                        OriginalTextPreviewMetadataGenerator.generate(items), binaryPropertyList: binaryPropertyList)
                }
            }
            return item
        }
        if let rawPreview = item.rawPreview {
            item.imagePreviewMetadata = OriginalImagePreviewMetadataCodec.decode(rawPreview)
        } else {
            if item.imagePreviewMetadata == nil {
                item.imagePreviewMetadata = (try? originalPasteboardItems(from: item.payloads))
                    .flatMap(OriginalImagePreviewMetadataGenerator.f_100313548)
            }
            if let metadata = item.imagePreviewMetadata {
                item.rawPreview = OriginalImagePreviewMetadataCodec.encode(metadata, binaryPropertyList: binaryPropertyList)
                if item.rawPreview == nil { item.imagePreviewMetadata = nil }
            }
        }
        return item
    }

    @discardableResult
    public func add(_ item: ClipboardItem, sourceApplication: SourceApplicationRecord? = nil) throws -> UUID {
        try addWithInsertionResult(item, sourceApplication: sourceApplication).id
    }

    func addWithInsertionResult(_ item: ClipboardItem,
                                sourceApplication: SourceApplicationRecord? = nil) throws -> (id: UUID, isNew: Bool) {
        var item = item
        if let sourceApplication {
            item.sourceApplicationBundleID = sourceApplication.bundleIdentifier
            item.sourceApplicationRelationIsKnown = true
        }
        let checksum = try? Self.knownPasteboardChecksum(from: item.payloads)
        return try mutate(historyAction: item.isInHistory) { state in
            item = Self.withPreviewMetadata(item, binaryPropertyList: state.preferences.useBinaryPlist,
                preferQuickLookThumbnails: state.preferences.fileQuickLookThumbnailsEnabled,
                generateMissingContentPreview: true)
            if let sourceApplication { Self.upsertSourceApplication(sourceApplication, in: &state) }
            if let owner = item.pinboardOwnerID,
               !item.pinboardIDs.contains(owner) || !state.pinboards.contains(where: { $0.id == owner }) {
                throw ClipboardStoreError.pinboardNotFound
            }
            if let i = state.items.firstIndex(where: { previous in
                if let checksum, let previousChecksum = try? Self.knownPasteboardChecksum(from: previous.payloads) {
                    return checksum == previousChecksum
                }
                let explicitIdentity = Self.hasValidExplicitPasteboardRepresentations(previous.payloads)
                    && Self.hasValidExplicitPasteboardRepresentations(item.payloads)
                return (explicitIdentity || previous.kind == item.kind && previous.plainText == item.plainText)
                    && Self.hasSamePasteboardRepresentations(previous.payloads, item.payloads)
            }) {
                let analysis = state.items[i].kind == .image && item.kind == .image
                    ? state.items[i].payloads.filter { Self.analysisPayloadKeys.contains($0.key) } : [:]
                state.items[i].kind = item.kind
                state.items[i].plainText = item.plainText
                state.items[i].payloads = item.payloads
                state.items[i].imagePreviewMetadata = item.imagePreviewMetadata
                state.items[i].rawPreview = item.rawPreview
                for (type, data) in analysis where state.items[i].payloads[type] == nil {
                    state.items[i].payloads[type] = data
                }
                state.items[i].updatedAt = max(Date(), item.updatedAt)
                state.items[i].sourceName = item.sourceName
                state.items[i].sourceBundleID = item.sourceBundleID
                state.items[i].sourceApplicationBundleID = item.sourceApplicationBundleID
                state.items[i].sourceApplicationRelationIsKnown = item.sourceApplicationRelationIsKnown
                state.items[i].sourceDevice = item.sourceDevice
                if item.isInHistory { state.items[i].createdAt = item.createdAt }
                state.items[i].isInHistory = state.items[i].isInHistory || item.isInHistory
                state.items[i].isDeleted = false
                if state.items[i].pinboardIDs == item.pinboardIDs, let order = item.pinboardOrder {
                    state.items[i].pinboardOrder = order
                }
                if state.items[i].pinboardOwnerID == nil {
                    if let owner = item.pinboardOwnerID {
                        if state.items[i].pinboardIDs.isEmpty {
                            state.items[i].pinboardIDs = [owner]
                            state.items[i].pinboardOwnerID = owner
                        } else if state.items[i].pinboardIDs.contains(owner) {
                            state.items[i].pinboardOwnerID = owner
                        }
                    } else {
                        state.items[i].pinboardIDs.formUnion(item.pinboardIDs)
                    }
                }
                return (state.items[i].id, false)
            }
            state.items.removeAll { $0.id == item.id }
            state.items.append(item)
            return (item.id, true)
        }
    }

    public enum IntentTextDestination: Sendable {
        case history
        case pinboard(UUID)
    }

    /// CreateItem differs from capture: a checksum hit retains its title and source relationships.
    public func createIntentText(_ content: String, destination: IntentTextDestination) throws -> ClipboardItem {
        guard !content.isEmpty else { throw OriginalPasteboardItemCreationError.emptyContent }
        let representation = OriginalPasteboardItem.f_10037c6d4(content)
        let rawKind = OriginalPasteboardClassification.f_10032362c([representation])
        let kind: ClipboardKind
        switch rawKind {
        case .text: kind = .text
        case .link: kind = .link
        case .color: kind = .color
        case .image: kind = .image
        case .files: kind = .files
        case .unknown: kind = .unknown
        }
        let payloads = [NSPasteboard.PasteboardType.string.rawValue: Data(content.utf8),
                        Self.orderedPasteboardTypesPayloadKey: try JSONEncoder().encode(representation.f_10037da6c())]
        let checksum = try Self.knownPasteboardChecksum(from: payloads)
        let historyAction: Bool
        switch destination {
        case .history: historyAction = true
        case .pinboard: historyAction = false
        }
        return try mutate(historyAction: historyAction) { state in
            let destinationOrder: [UUID]
            if case let .pinboard(id) = destination {
                guard state.pinboards.contains(where: { $0.id == id }) else {
                    throw ClipboardStoreError.pinboardNotFound
                }
                destinationOrder = Self.sortedPinboardItems(state.items.filter { !$0.isDeleted && $0.pinboardIDs.contains(id) }).map(\.id)
            } else {
                destinationOrder = []
            }
            let existing = state.items.firstIndex { previous in
                guard !previous.isDeleted else { return false }
                if let checksum, let previousChecksum = try? Self.knownPasteboardChecksum(from: previous.payloads) {
                    return checksum == previousChecksum
                }
                let explicitIdentity = Self.hasValidExplicitPasteboardRepresentations(previous.payloads)
                    && Self.hasValidExplicitPasteboardRepresentations(payloads)
                return (explicitIdentity || previous.kind == kind && previous.plainText == content)
                    && Self.hasSamePasteboardRepresentations(previous.payloads, payloads)
            }
            let index: Int
            if let existing {
                index = existing
                state.items[index].kind = kind
                state.items[index].plainText = content
                state.items[index].payloads = payloads
                state.items[index].imagePreviewMetadata = nil
                state.items[index].rawPreview = nil
                state.items[index].updatedAt = Date()
            } else {
                index = state.items.count
                state.items.append(ClipboardItem(kind: kind, plainText: content, sourceName: "",
                                                 payloads: payloads, isInHistory: false))
            }
            state.items[index] = Self.withPreviewMetadata(state.items[index],
                binaryPropertyList: state.preferences.useBinaryPlist,
                preferQuickLookThumbnails: state.preferences.fileQuickLookThumbnailsEnabled,
                generateMissingContentPreview: true)
            switch destination {
            case .history:
                let timestamp = Date()
                state.items[index].createdAt = timestamp
                state.items[index].updatedAt = timestamp
                state.items[index].isInHistory = true
            case let .pinboard(id):
                var ordered = destinationOrder
                let itemID = state.items[index].id
                if let owner = state.items[index].pinboardOwnerID, owner != id {
                    ordered.removeAll { $0 == itemID }
                }
                if !ordered.contains(itemID) { ordered.insert(itemID, at: 0) }
                state.items[index].pinboardIDs = [id]
                state.items[index].pinboardOwnerID = id
                Self.writePinboardOrder(ordered, into: &state)
            }
            return state.items[index]
        }
    }

    public func search(query: String, kind: ClipboardKind? = nil, pinboardID: UUID? = nil,
                       includeDeleted: Bool = false) -> [ClipboardItem] {
        func folded(_ string: String) -> String {
            string.folding(options: [.caseInsensitive, .diacriticInsensitive, .widthInsensitive], locale: Locale(identifier: "en_US_POSIX"))
        }
        let terms = folded(query).split(whereSeparator: \.isWhitespace).map(String.init)
        let matches = items.filter { item in
            guard (includeDeleted || !item.isDeleted), kind == nil || item.kind == kind,
                  pinboardID == nil || item.pinboardIDs.contains(pinboardID!),
                  pinboardID != nil || !terms.isEmpty || includeDeleted || item.isInHistory else { return false }
            let haystack = folded([item.title, item.plainText ?? "", item.recognizedText ?? "", item.sourceName, item.sourceBundleID ?? "", item.kind.displayName].joined(separator: "\n"))
            return terms.allSatisfy { haystack.contains($0) }
        }
        if pinboardID != nil, terms.isEmpty { return Self.sortedPinboardItems(matches) }
        if pinboardID == nil, terms.isEmpty, !includeDeleted {
            return matches.sorted { $0.createdAt > $1.createdAt }
        }
        return matches.sorted { $0.updatedAt > $1.updatedAt }
    }

    public func items(in pinboardID: UUID) -> [ClipboardItem] {
        search(query: "", pinboardID: pinboardID)
    }

    private static func sortedPinboardItems(_ items: [ClipboardItem]) -> [ClipboardItem] {
        items.sorted { lhs, rhs in
            switch (lhs.pinboardOrder, rhs.pinboardOrder) {
            case let (left?, right?) where left != right: return left < right
            case (_?, nil): return true
            case (nil, _?): return false
            default:
                if lhs.updatedAt != rhs.updatedAt { return lhs.updatedAt > rhs.updatedAt }
                return lhs.id.uuidString < rhs.id.uuidString
            }
        }
    }

    private static func writePinboardOrder(_ ids: [UUID], into state: inout StoreState) {
        let positions = Dictionary(uniqueKeysWithValues: ids.enumerated().map { ($0.element, Int64($0.offset)) })
        for i in state.items.indices {
            if let position = positions[state.items[i].id] { state.items[i].pinboardOrder = position }
        }
    }

    public func updateItem(id: UUID, title: String? = nil, text: String? = nil) throws {
        try mutate { state in
            guard let i = state.items.firstIndex(where: { $0.id == id }) else { throw ClipboardStoreError.itemNotFound }
            if let title {
                state.items[i].title = title
                state.items[i].hasExplicitTitle = true
            }
            if let text {
                state.items[i].plainText = text
                state.items[i].payloads = [NSPasteboard.PasteboardType.string.rawValue: Data(text.utf8)]
                state.items[i].imagePreviewMetadata = nil
                state.items[i].rawPreview = nil
                state.items[i].kind = Self.isLink(text) ? .link : (Self.isColor(text) ? .color : .text)
                if state.items[i].kind == .color {
                    state.items[i].rawPreview = OriginalImagePreviewMetadataCodec.encodeColor(
                        OriginalColorPreviewMetadataGenerator.generate([OriginalPasteboardItem.f_10037c6d4(text)]),
                        binaryPropertyList: state.preferences.useBinaryPlist)
                } else if state.items[i].kind == .text {
                    state.items[i].rawPreview = OriginalImagePreviewMetadataCodec.encodeText(
                        OriginalTextPreviewMetadataGenerator.generate([OriginalPasteboardItem.f_10037c6d4(text)]),
                        binaryPropertyList: state.preferences.useBinaryPlist)
                }
                if state.items[i].kind == .link,
                   let url = OriginalPasteboardItem.f_10037c6d4(text).f_10037ce0c() {
                    let representation = OriginalPasteboardItem.f_10037c7bc(url, title: state.items[i].title)
                    for type in representation.f_10037da6c() {
                        state.items[i].payloads[type] = representation.f_10037d810(forType: type)
                    }
                    state.items[i].payloads[Self.orderedPasteboardTypesPayloadKey] =
                        try JSONEncoder().encode(representation.f_10037da6c())
                    state.items[i].rawPreview = OriginalImagePreviewMetadataCodec.encodeLink(
                        OriginalLinkPreviewMetadataGenerator.generate([representation]),
                        binaryPropertyList: state.preferences.useBinaryPlist)
                }
            }
            state.items[i].updatedAt = Date()
        }
    }

    public func updateTextPreviewItem(id: UUID, attributedString: NSAttributedString) throws {
        let representation = OriginalTextPreviewSubmission.makeItem(attributedString)
        let types = representation.f_10037da6c()
        var payloads: [String: Data] = [:]
        for type in types {
            if let data = representation.f_10037d810(forType: type) { payloads[type] = data }
        }
        payloads[Self.orderedPasteboardTypesPayloadKey] = try JSONEncoder().encode(types)
        let kind: ClipboardKind
        switch OriginalPasteboardClassification.f_10032362c([representation]) {
        case .unknown: kind = .unknown
        case .image: kind = .image
        case .color: kind = .color
        case .files: kind = .files
        case .link: kind = .link
        case .text: kind = types.contains(NSPasteboard.PasteboardType.rtf.rawValue) ? .richText : .text
        }
        try mutate { state in
            guard let i = state.items.firstIndex(where: { $0.id == id }) else { throw ClipboardStoreError.itemNotFound }
            var item = state.items[i]
            item.payloads = payloads
            item.plainText = attributedString.string
            item.kind = kind
            item.imagePreviewMetadata = nil
            item.rawPreview = nil
            item.updatedAt = Date()
            state.items[i] = Self.withPreviewMetadata(item, binaryPropertyList: state.preferences.useBinaryPlist,
                preferQuickLookThumbnails: state.preferences.fileQuickLookThumbnailsEnabled, generateMissingContentPreview: true)
        }
    }

    public func updateRichTextItem(id: UUID, attributedString: NSAttributedString) throws {
        let rtf = try attributedString.data(from: NSRange(location: 0, length: attributedString.length),
                                            documentAttributes: [.documentType: NSAttributedString.DocumentType.rtf])
        let text = attributedString.string
        try mutate { state in
            guard let i = state.items.firstIndex(where: { $0.id == id }) else { throw ClipboardStoreError.itemNotFound }
            state.items[i].plainText = text
            state.items[i].payloads = [NSPasteboard.PasteboardType.rtf.rawValue: rtf,
                                       NSPasteboard.PasteboardType.string.rawValue: Data(text.utf8)]
            state.items[i].kind = .richText
            state.items[i].imagePreviewMetadata = nil
            state.items[i].rawPreview = OriginalImagePreviewMetadataCodec.encodeText(
                (try? Self.originalPasteboardItems(from: state.items[i].payloads))
                    .flatMap(OriginalTextPreviewMetadataGenerator.generate),
                binaryPropertyList: state.preferences.useBinaryPlist)
            state.items[i].updatedAt = Date()
        }
    }

    public func updateImageItem(id: UUID, payloads: [String: Data]) throws {
        try updateImageItem(id: id, payloads: payloads, allowingEmptyRepresentation: false)
    }

    public func updateImagePreviewItem(id: UUID, payloads: [String: Data]) throws {
        try updateImageItem(id: id, payloads: payloads, allowingEmptyRepresentation: true)
    }

    private func updateImageItem(id: UUID, payloads: [String: Data], allowingEmptyRepresentation: Bool) throws {
        let imageTypes = ["public.png", "public.jpeg", "public.heic", "public.tiff", "com.apple.icns", "com.compuserve.gif"]
        let types = imageTypes.filter { payloads[$0] != nil }
        guard !types.isEmpty || (allowingEmptyRepresentation && payloads.isEmpty) else {
            throw OriginalPasteboardItemCreationError.unsupportedContent
        }
        var replacement = payloads.filter { imageTypes.contains($0.key) }
        replacement[Self.orderedPasteboardTypesPayloadKey] = try JSONEncoder().encode(types)
        let metadata = (try? Self.originalPasteboardItems(from: replacement))
            .flatMap(OriginalImagePreviewMetadataGenerator.f_100313548)
        let rawPreview = metadata.flatMap {
            OriginalImagePreviewMetadataCodec.encode($0, binaryPropertyList: preferences.useBinaryPlist)
        }
        try mutate { state in
            guard let i = state.items.firstIndex(where: { $0.id == id && !$0.isDeleted && $0.kind == .image }) else {
                throw ClipboardStoreError.itemNotFound
            }
            state.items[i].payloads = replacement
            state.items[i].imagePreviewMetadata = rawPreview == nil ? nil : metadata
            state.items[i].rawPreview = rawPreview
            state.items[i].plainText = nil
            state.items[i].kind = types.isEmpty ? .unknown : .image
            state.items[i].updatedAt = Date()
        }
        startBackgroundTextRecognition(id: id)
    }

    public func updateLinkItem(id: UUID, url: URL) throws {
        try mutate { state in
            guard let i = state.items.firstIndex(where: { $0.id == id && !$0.isDeleted && $0.kind == .link }) else {
                throw ClipboardStoreError.itemNotFound
            }
            let name: String?
            if let previous = state.items[i].decodedLinkPreviewMetadata {
                name = previous.name
            } else {
                name = ""
            }
            let representation = OriginalPasteboardItem.f_10037c7bc(url, title: name)
            var payloads: [String: Data] = [:]
            for type in representation.f_10037da6c() { payloads[type] = representation.f_10037d810(forType: type) }
            payloads[Self.orderedPasteboardTypesPayloadKey] = try JSONEncoder().encode(representation.f_10037da6c())
            state.items[i].payloads = payloads
            state.items[i].plainText = url.absoluteString
            state.items[i].kind = .link
            state.items[i].imagePreviewMetadata = nil
            state.items[i].rawPreview = OriginalImagePreviewMetadataCodec.encodeLink(
                OriginalLinkPreviewMetadataGenerator.generate([representation]),
                binaryPropertyList: state.preferences.useBinaryPlist)
            state.items[i].updatedAt = Date()
        }
    }

    public func updateColorItem(id: UUID, text: String) throws {
        try mutate { state in
            guard let i = state.items.firstIndex(where: { $0.id == id && !$0.isDeleted && $0.kind == .color }) else {
                throw ClipboardStoreError.itemNotFound
            }
            state.items[i].payloads = [NSPasteboard.PasteboardType.string.rawValue: Data(text.utf8)]
            state.items[i].plainText = text
            state.items[i].kind = .color
            state.items[i].imagePreviewMetadata = nil
            state.items[i].rawPreview = OriginalImagePreviewMetadataCodec.encodeColor(
                OriginalColorPreviewMetadataGenerator.generate([OriginalPasteboardItem.f_10037c6d4(text)]),
                binaryPropertyList: state.preferences.useBinaryPlist)
            state.items[i].updatedAt = Date()
        }
    }

    public func delete(ids: Set<UUID>) throws { try setDeleted(ids: ids, deleted: true) }
    public func delete(ids: Set<UUID>, contextPinboardID: UUID?) throws {
        try mutate { state in
            for i in state.items.indices where ids.contains(state.items[i].id) {
                if let contextPinboardID {
                    state.items[i].pinboardIDs.remove(contextPinboardID)
                    if state.items[i].pinboardOwnerID == contextPinboardID { state.items[i].pinboardOwnerID = nil }
                }
                else { state.items[i].isInHistory = false }
            }
            state.items.removeAll { ids.contains($0.id) && !$0.isInHistory && $0.pinboardIDs.isEmpty }
        }
    }
    public func restore(ids: Set<UUID>) throws { try setDeleted(ids: ids, deleted: false) }
    private func setDeleted(ids: Set<UUID>, deleted: Bool) throws {
        try mutate { state in
            for i in state.items.indices where ids.contains(state.items[i].id) {
                state.items[i].isDeleted = deleted
                state.items[i].updatedAt = Date()
            }
        }
    }
    public func permanentlyDelete(ids: Set<UUID>) throws {
        try mutate { state in state.items.removeAll { ids.contains($0.id) } }
    }

    @discardableResult
    public func createPinboard(name: String, colorHex: String? = nil) throws -> Pinboard {
        guard !name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { throw ClipboardStoreError.invalidPinboardName }
        return try insertPinboard(name: name, colorHex: colorHex)
    }

    /// The original AppIntent rejects an empty string without trimming the supplied name.
    @discardableResult
    public func createPinboardFromIntent(name: String) throws -> Pinboard {
        guard !name.isEmpty else { throw ClipboardStoreError.invalidPinboardName }
        return try insertPinboard(name: name, colorHex: nil)
    }

    private func insertPinboard(name: String, colorHex: String?) throws -> Pinboard {
        return try mutate { state in
            let code: UInt64?
            let value: String
            if let colorHex {
                value = colorHex
                code = OriginalPinboardAttributes.parsedColorCode(colorHex)
            } else {
                let color = OriginalPinboardColor.allCases[Int.random(in: 0..<OriginalPinboardColor.allCases.count)]
                code = color.canonicalColorCode
                value = String(format: "#%06llX", color.canonicalColorCode)
            }
            let attributes = try code.map { try OriginalPinboardAttributes.encoded(colorCode: $0) }
            let board = Pinboard(name: name, colorHex: value, sortOrder: (state.pinboards.map(\.sortOrder).max() ?? -1) + 1,
                                 rawType: 2, rawAttributes: attributes)
            state.pinboards.append(board)
            return board
        }
    }
    public func renamePinboard(id: UUID, name: String) throws {
        guard !name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { throw ClipboardStoreError.invalidPinboardName }
        try mutate { state in
            guard let i = state.pinboards.firstIndex(where: { $0.id == id }) else { throw ClipboardStoreError.pinboardNotFound }
            state.pinboards[i].name = name
        }
    }
    public func renamePinboardFromTab(id: UUID, rawName: String) throws {
        let name = OriginalPinboardTitle.normalizedRename(rawName)
        try mutate { state in
            guard let i = state.pinboards.firstIndex(where: { $0.id == id }) else { throw ClipboardStoreError.pinboardNotFound }
            state.pinboards[i].name = name
        }
    }
    public func removePinboard(id: UUID) throws {
        try mutate { state in
            let affected = Set(state.items.filter { $0.pinboardIDs.contains(id) }.map(\.id))
            state.pinboards.removeAll { $0.id == id }
            for i in state.items.indices {
                state.items[i].pinboardIDs.remove(id)
                if state.items[i].pinboardOwnerID == id { state.items[i].pinboardOwnerID = nil }
            }
            state.items.removeAll { affected.contains($0.id) && !$0.isInHistory && $0.pinboardIDs.isEmpty }
        }
    }

    @discardableResult
    public func duplicateItem(id: UUID) throws -> UUID {
        try mutate { state in
            guard var item = state.items.first(where: { $0.id == id && !$0.isDeleted }) else { throw ClipboardStoreError.itemNotFound }
            item.id = UUID()
            item.createdAt = Date()
            item.updatedAt = item.createdAt
            state.items.append(item)
            return item.id
        }
    }
    public func assign(ids: Set<UUID>, to pinboardID: UUID?) throws {
        try assign(orderedIDs: items.filter { ids.contains($0.id) }.map(\.id), to: pinboardID)
    }

    public func assign(orderedIDs: [UUID], to pinboardID: UUID?) throws {
        try mutate { state in
            if let pinboardID, !state.pinboards.contains(where: { $0.id == pinboardID }) { throw ClipboardStoreError.pinboardNotFound }
            var destination = pinboardID.map { board in
                Self.sortedPinboardItems(state.items.filter { !$0.isDeleted && $0.pinboardIDs.contains(board) }).map(\.id)
            } ?? []
            var seen = Set<UUID>()
            for id in orderedIDs where seen.insert(id).inserted {
                guard let i = state.items.firstIndex(where: { $0.id == id }) else { continue }
                if let pinboardID {
                    let movingFromOtherOwner = state.items[i].pinboardOwnerID.map { $0 != pinboardID } ?? false
                    if movingFromOtherOwner { destination.removeAll { $0 == id } }
                    if movingFromOtherOwner || !state.items[i].pinboardIDs.contains(pinboardID) { destination.insert(id, at: 0) }
                    state.items[i].pinboardIDs = [pinboardID]
                    state.items[i].pinboardOwnerID = pinboardID
                } else {
                    state.items[i].pinboardIDs.removeAll()
                    state.items[i].pinboardOwnerID = nil
                    state.items[i].pinboardOrder = nil
                }
            }
            if pinboardID != nil { Self.writePinboardOrder(destination, into: &state) }
            state.items.removeAll { seen.contains($0.id) && !$0.isInHistory && $0.pinboardIDs.isEmpty }
        }
    }

    public func reorderItems(ids: [UUID], in pinboardID: UUID, toOffset: Int) throws {
        try mutate { state in
            guard state.pinboards.contains(where: { $0.id == pinboardID }) else { throw ClipboardStoreError.pinboardNotFound }
            let current = Self.sortedPinboardItems(state.items.filter { !$0.isDeleted && $0.pinboardIDs.contains(pinboardID) }).map(\.id)
            guard (0...current.count).contains(toOffset) else { throw ClipboardStoreError.invalidPinboardOrder }
            let selected = Set(ids)
            let offsets = current.indices.filter { selected.contains(current[$0]) }
            let moved = offsets.map { current[$0] }
            let remaining = current.filter { !selected.contains($0) }
            let insertion = toOffset - offsets.filter { $0 < toOffset }.count
            var reordered = remaining
            reordered.insert(contentsOf: moved, at: insertion)
            Self.writePinboardOrder(reordered, into: &state)
        }
    }
    public func unassign(ids: Set<UUID>, from pinboardID: UUID) throws {
        try mutate { state in
            for i in state.items.indices where ids.contains(state.items[i].id) {
                state.items[i].pinboardIDs.remove(pinboardID)
                if state.items[i].pinboardOwnerID == pinboardID { state.items[i].pinboardOwnerID = nil }
            }
            state.items.removeAll { ids.contains($0.id) && !$0.isInHistory && $0.pinboardIDs.isEmpty }
        }
    }

    public func updatePinboard(id: UUID, colorHex: String? = nil, sortOrder: Int? = nil) throws {
        try mutate { state in
            guard let i = state.pinboards.firstIndex(where: { $0.id == id }) else { throw ClipboardStoreError.pinboardNotFound }
            if let colorHex {
                state.pinboards[i].colorHex = colorHex
                state.pinboards[i].rawType = 2
                state.pinboards[i].rawAttributes = try OriginalPinboardAttributes.parsedColorCode(colorHex).map {
                    try OriginalPinboardAttributes.encoded(colorCode: $0)
                }
            }
            if let sortOrder { state.pinboards[i].sortOrder = sortOrder }
        }
    }

    public func reorderPinboards(ids: [UUID]) throws {
        try mutate { state in
            guard Set(ids).count == ids.count, Set(ids) == Set(state.pinboards.map(\.id)) else { throw ClipboardStoreError.pinboardNotFound }
            let positions = Dictionary(uniqueKeysWithValues: ids.enumerated().map { ($0.element, $0.offset) })
            for i in state.pinboards.indices { state.pinboards[i].sortOrder = positions[state.pinboards[i].id]! }
        }
    }

    public func eraseHistory() throws {
        try mutate { state in
            state.items.removeAll { $0.isInHistory && $0.pinboardIDs.isEmpty }
            for i in state.items.indices { state.items[i].isInHistory = false }
        }
    }

    func saveRecognizedDocument(id: UUID, document: RecognizedTextDocument, expectedImageData: Data) throws {
        try mutate { state in
            guard let i = state.items.firstIndex(where: { $0.id == id && !$0.isDeleted }),
                  state.items[i].kind == .image, state.items[i].imageData == expectedImageData else { return }
            state.items[i].payloads[Self.recognizedTextPayloadKey] = Data(document.text.utf8)
            state.items[i].payloads[Self.recognizedDocumentPayloadKey] = try JSONEncoder().encode(document)
        }
    }

    public func exportArchive(to url: URL) throws {
        try OriginalObjCExceptionBridge.f_1002ff9c8 {
            try save()
            let encoder = JSONEncoder()
            encoder.outputFormatting = [.sortedKeys]
            try writeAtomically(encoder.encode(current), to: url)
        }
    }

    /// Additive, atomic import; stable migration IDs keep local edits intact on subsequent runs.
    public func importPasteGroups(_ snapshot: PasteGroupMigration.Snapshot) throws -> PasteGroupMigration.Result {
        let imported = StoreState(items: snapshot.items, pinboards: snapshot.pinboards,
                                  sourceApplications: snapshot.sourceApplications)
        try validate(imported)
        return try mutate { state in
            var groupIDs = Set(state.pinboards.map(\.id))
            var itemIDs = Set(state.items.map(\.id))
            var applicationIDs = Set(state.sourceApplications.map(\.bundleIdentifier))
            var result = PasteGroupMigration.Result(addedGroups: 0, addedItems: 0,
                existingGroups: 0, existingItems: 0, unavailableItems: snapshot.unavailableItemCount)
            var order = state.pinboards.map(\.sortOrder).max() ?? -1
            for var board in snapshot.pinboards {
                guard groupIDs.insert(board.id).inserted else { result.existingGroups += 1; continue }
                order += 1
                board.sortOrder = order
                state.pinboards.append(board)
                result.addedGroups += 1
            }
            for application in snapshot.sourceApplications where applicationIDs.insert(application.bundleIdentifier).inserted {
                state.sourceApplications.append(application)
            }
            for item in snapshot.items {
                guard itemIDs.insert(item.id).inserted else { result.existingItems += 1; continue }
                state.items.append(item)
                result.addedItems += 1
            }
            return result
        }
    }

    public func importArchive(from url: URL) throws {
        let data = try Data(contentsOf: url)
        let archive: StoreState
        do {
            archive = try JSONDecoder().decode(StoreState.self, from: data)
        } catch {
            let textPrefix = data.starts(with: [0xef, 0xbb, 0xbf]) ? data.dropFirst(3) : data[...]
            let trimmedPrefix = textPrefix.drop(while: { [9, 10, 13, 32].contains($0) })
            if data.starts(with: Data("bplist00".utf8)) || trimmedPrefix.starts(with: Data("<?xml".utf8)) ||
                trimmedPrefix.first == UInt8(ascii: "[") || OriginalPasteboardDataCodec.decodeIfValid(data) != nil {
                _ = try importOriginalPasteboardItems(data, sourceName: "导入的剪贴板")
                return
            }
            throw error
        }
        try validate(archive)
        let importedItems = archive.items.map { Self.withPreviewMetadata($0, binaryPropertyList: archive.preferences.useBinaryPlist, preferQuickLookThumbnails: archive.preferences.fileQuickLookThumbnailsEnabled, generateMissingContentPreview: false) }
        try mutate { state in
            for application in archive.sourceApplications { Self.upsertSourceApplication(application, in: &state) }
            var boards = Dictionary(uniqueKeysWithValues: state.pinboards.map { ($0.id, $0) })
            for var board in archive.pinboards {
                if board.rawType == nil, board.rawAttributes == nil,
                   let existing = boards[board.id], existing.colorHex == board.colorHex {
                    board.rawType = existing.rawType
                    board.rawAttributes = existing.rawAttributes
                }
                boards[board.id] = board
            }
            state.pinboards = Array(boards.values)
            var items = Dictionary(uniqueKeysWithValues: state.items.map { ($0.id, $0) })
            for var item in importedItems where items[item.id] == nil || items[item.id]!.updatedAt <= item.updatedAt {
                if let existing = items[item.id], existing.pinboardIDs == item.pinboardIDs {
                    if item.pinboardOrder == nil { item.pinboardOrder = existing.pinboardOrder }
                    if item.pinboardOwnerID == nil { item.pinboardOwnerID = existing.pinboardOwnerID }
                }
                items[item.id] = item
            }
            state.items = Array(items.values)
            state.preferences = archive.preferences
        }
    }

    static func isLink(_ text: String) -> Bool {
        OriginalPasteboardClassification.f_10032362c([OriginalPasteboardItem.f_10037c6d4(text)]) == .link
    }

    static func isColor(_ text: String) -> Bool {
        OriginalPasteboardClassification.f_100321f48(text)
    }
}
