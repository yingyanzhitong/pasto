import AppKit
import Combine
import CoreData
import Darwin
import Foundation

struct StoreState: Codable, Equatable {
    var schemaVersion = 1
    var items: [ClipboardItem] = []
    var pinboards: [Pinboard] = []
    var preferences = AppPreferences()
    var sourceApplications: [SourceApplicationRecord] = []
    var cloudSyncMetadata: ICloudSyncMetadata?
    var cloudKitJournal: OriginalCloudKitJournal?

    init(items: [ClipboardItem] = [], pinboards: [Pinboard] = [], preferences: AppPreferences = AppPreferences(),
         sourceApplications: [SourceApplicationRecord] = [], cloudSyncMetadata: ICloudSyncMetadata? = nil,
         cloudKitJournal: OriginalCloudKitJournal? = nil) {
        self.items = items
        self.pinboards = pinboards
        self.preferences = preferences
        self.sourceApplications = sourceApplications
        self.cloudSyncMetadata = cloudSyncMetadata
        self.cloudKitJournal = cloudKitJournal
    }

    private enum CodingKeys: String, CodingKey {
        case schemaVersion, items, pinboards, preferences, sourceApplications, cloudSyncMetadata, cloudKitJournal
    }

    init(from decoder: Decoder) throws {
        let values = try decoder.container(keyedBy: CodingKeys.self)
        schemaVersion = try values.decode(Int.self, forKey: .schemaVersion)
        items = try values.decode([ClipboardItem].self, forKey: .items)
        pinboards = try values.decode([Pinboard].self, forKey: .pinboards)
        preferences = try values.decode(AppPreferences.self, forKey: .preferences)
        sourceApplications = try values.decodeIfPresent([SourceApplicationRecord].self, forKey: .sourceApplications) ?? []
        cloudSyncMetadata = try values.decodeIfPresent(ICloudSyncMetadata.self, forKey: .cloudSyncMetadata)
        cloudKitJournal = try values.decodeIfPresent(OriginalCloudKitJournal.self, forKey: .cloudKitJournal)
    }
}

@MainActor
public final class ClipboardStore: ObservableObject {
    @Published public var items: [ClipboardItem] = []
    @Published public var pinboards: [Pinboard] = []
    @Published public private(set) var sourceApplications: [SourceApplicationRecord] = []
    public let didRestoreItem = PassthroughSubject<Void, Never>()
    public static let didRestoreItemNotification = Notification.Name("pasteboardHistoryManagerDidRestoreItem")
    public let preferenceChanges = PassthroughSubject<(old: AppPreferences, new: AppPreferences), Never>()
    @Published public var preferences = AppPreferences() {
        didSet { preferenceChanges.send((oldValue, preferences)) }
    }
    public let directoryURL: URL
    public var searchSourceIdentifier: String? { persistence.searchSourceIdentifier }
    public var collectionItemUpdates: AnyPublisher<Set<UUID>, Never> { persistence.collectionItemUpdates }
    public func localListMenuState(_ target: ClipboardListTarget) -> (rawType: Int64?, isEmpty: Bool) {
        persistence.localListMenuState(target)
    }
    public func makeTabListCollection() -> ClipboardPinboardCollection { persistence.makeTabListCollection() }
    public func tabListTarget(identifier: String) -> ClipboardListTarget? { persistence.tabListTarget(identifier: identifier) }
    public func makeListCollection(identifier: String) -> ClipboardSearchCollection? {
        persistence.makeListCollection(identifier: identifier)
    }
    public func makePinboardCollection() -> ClipboardPinboardCollection {
        persistence.makePinboardCollection()
    }
    public func observeListAttributes(pinboardID: UUID?) -> ClipboardListAttributesObservation? {
        persistence.observeListAttributes(identifier: pinboardID?.uuidString ?? Self.historyListIdentifier)
    }
    public func observeItem(id: UUID) -> ClipboardItemObservation? {
        persistence.observeItem(identifier: id.uuidString)
    }
    public func originalContentKind(of item: ClipboardItem) -> OriginalPasteboardContentKind {
        persistence.itemContentKind(identifier: item.id.uuidString)
    }
    public func observeSearchChanges(_ consume: @escaping ([OriginalSearchHistoryChange]) async throws -> Void) async {
        await persistence.observeSearchChanges(consume)
    }
    // Local equivalent of the startup viewContext-backed suggestion-source registration.
    public func makeSearchListNameResolver() -> (String) -> String? {
        persistence.makeSearchListNameResolver()
    }

    public func makeSearchSuggestionProvider() -> OriginalSearchSuggestions.Provider {
        let persistence = self.persistence
        return OriginalSearchSuggestions.Provider(
            app: { try persistence.searchApplicationNames(matching: $0) },
            device: { try persistence.searchDeviceNames(matching: $0) },
            pinboard: { try persistence.searchPinboardNames(matching: $0) })
    }

    public func searchPinboardNames(matching query: String) throws -> [(identifier: String, name: String)] {
        try persistence.searchPinboardNames(matching: query)
    }

    public func searchApplicationNames(matching query: String) throws -> [String] {
        try persistence.searchApplicationNames(matching: query)
    }

    public func searchDeviceNames(matching query: String) throws -> [String] {
        try persistence.searchDeviceNames(matching: query)
    }

    public func searchApplicationImage(named name: String) -> NSImage? {
        persistence.searchApplicationImage(named: name)
    }

    public func searchDeviceType(named name: String) -> UInt8? {
        persistence.searchDeviceType(named: name)
    }

    public func searchItems(identifiers: [String]?) throws -> [ClipboardItem] {
        try persistence.searchItems(identifiers: identifiers)
    }
    public func makeListCollection(pinboardID: UUID?) -> ClipboardSearchCollection? {
        persistence.makeListCollection(identifier: pinboardID?.uuidString ?? Self.historyListIdentifier)
    }
    public func makeSearchCollection(identifiers: [String]) -> ClipboardSearchCollection? {
        persistence.makeSearchCollection(identifiers: identifiers)
    }
    public func searchNativeItems(identifiers: [String]?) throws -> [ClipboardItem] {
        try persistence.searchNativeItems(identifiers: identifiers)
    }

    public func searchIndexRecords(identifiers: [String]?) throws -> [ClipboardSearchRecord] {
        try persistence.searchIndexRecords(identifiers: identifiers)
    }

    public func searchIndexIdentifiers(before timestamp: Date?) throws -> [String] {
        try persistence.searchIndexIdentifiers(before: timestamp)
    }

    public static let historyListIdentifier = ClipboardListPersistence.historyIdentifier

    public func localListMenuState(pinboardID: UUID?) -> (rawType: Int64?, isEmpty: Bool) {
        persistence.localListMenuState(identifier: pinboardID?.uuidString ?? ClipboardListPersistence.historyIdentifier)
    }
    private var baseline = StoreState()
    private var diskRevision: UUID?
    private let persistence: ClipboardPersistence
    private var iCloudDigestCache: [String: (entity: ICloudSyncEntity, digest: String)] = [:]

    public static var defaultDirectoryURL: URL {
        FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("PasteReplica", isDirectory: true)
    }

    public init(directoryURL: URL) throws {
        self.directoryURL = directoryURL
        try FileManager.default.createDirectory(at: directoryURL, withIntermediateDirectories: true,
                                                attributes: [.posixPermissions: 0o700])
        try FileManager.default.setAttributes([.posixPermissions: 0o700], ofItemAtPath: directoryURL.path)
        persistence = try Self.withLock(directoryURL: directoryURL) { try ClipboardPersistence(directoryURL: directoryURL) }
        try withLock {
            if try persistence.revision() == nil {
                // First successful Core Data save is the migration marker. Keep the JSON intact as a backup.
                let state = try readLegacyState()
                try persistence.commit(state, previous: nil)
            }
        }
        try reload()
        persistence.configureUndoRegistration()
    }

    private var stateURL: URL { directoryURL.appendingPathComponent("clipboard.json") }
    private var current: StoreState {
        StoreState(items: items, pinboards: pinboards, preferences: preferences, sourceApplications: sourceApplications,
                   cloudSyncMetadata: baseline.cloudSyncMetadata, cloudKitJournal: baseline.cloudKitJournal)
    }

    private func publish(_ state: StoreState, persisted: StoreState? = nil) {
        if items != state.items { items = state.items }
        if pinboards != state.pinboards { pinboards = state.pinboards }
        if sourceApplications != state.sourceApplications { sourceApplications = state.sourceApplications }
        if preferences != state.preferences { preferences = state.preferences }
        baseline = persisted ?? state
    }

    private func withLock<T>(_ operation: () throws -> T) throws -> T {
        try Self.withLock(directoryURL: directoryURL, operation)
    }

    private static func withLock<T>(directoryURL: URL, _ operation: () throws -> T) throws -> T {
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
        let effectiveItemIdentifiers = state.items.map { $0.nativeIdentifier ?? $0.id.uuidString }
        guard Set(effectiveItemIdentifiers).count == effectiveItemIdentifiers.count else {
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

    private func readLegacyState() throws -> StoreState {
        guard FileManager.default.fileExists(atPath: stateURL.path) else { return StoreState() }
        let state = try JSONDecoder().decode(StoreState.self, from: Data(contentsOf: stateURL))
        try validate(state)
        return state
    }

    private func revision() throws -> UUID? { try persistence.revision() }

    private func latestState() throws -> StoreState {
        if try revision() == diskRevision { return baseline }
        let state = try persistence.read()
        try validate(state)
        return state
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
            if local.nativeIdentifier != base.nativeIdentifier { value.nativeIdentifier = local.nativeIdentifier }
            if local.nativeChecksum != base.nativeChecksum { value.nativeChecksum = local.nativeChecksum }
            if local.sourceIdentifier != base.sourceIdentifier { value.sourceIdentifier = local.sourceIdentifier }
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
        // Legacy value-only groups use type 2 in the managed graph; canonicalize before publishing too.
        for i in state.pinboards.indices where state.pinboards[i].rawType == nil {
            state.pinboards[i].rawType = 2
        }
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
        if item.hasSourceApplicationSnapshot { return item.sourceApplicationSnapshot }
        guard let identifier = item.sourceApplicationBundleID else { return nil }
        return sourceApplications.first { $0.bundleIdentifier == identifier }
    }

    public func pinboardOwner(for item: ClipboardItem) -> Pinboard? {
        guard let identifier = item.pinboardOwnerID else { return nil }
        // 0x10031bc94/3250f0: a related list is an owning group only when rawType is exactly 2.
        return pinboards.first { $0.id == identifier && $0.rawType == 2 }
    }

    private func expireHistory(_ state: inout StoreState, capacity: Int) {
        guard capacity > 0 else { return }
        let interval = -capacity * 24 * 60 * 60
        let cutoff = Date(timeIntervalSinceNow: Double(interval))
        state.items.removeAll { $0.isInHistory && $0.pinboardIDs.isEmpty && $0.createdAt < cutoff }
    }

    struct HistoryRestoreOperation {
        let local: StoreState
        let previous: StoreState
        let native: ClipboardPersistence.HistoryRestoreSelection
    }

    func prepareHistoryRestore(_ selected: [ClipboardItem]) throws -> HistoryRestoreOperation {
        let local = current
        try validate(local)
        return try withLock {
            var state = local
            var previous = baseline
            // Keep the selected native input while adapting a newer persisted state for restoration metadata.
            if try revision() != diskRevision {
                previous = try latestState()
                state = merge(local, onto: previous)
                try validate(state)
            }
            let available = Set(state.items.filter { !$0.isDeleted }.map(\.id))
            guard selected.allSatisfy({ available.contains($0.id) }) else { throw ClipboardStoreError.itemNotFound }
            return HistoryRestoreOperation(local: state, previous: previous,
                native: try persistence.prepareHistoryRestore(ids: selected.map(\.id)))
        }
    }

    func prepareHistoryRestore(_ selected: [ClipboardRestoreItem]) throws -> HistoryRestoreOperation {
        let local = current
        try validate(local)
        return try withLock {
            var state = local
            var previous = baseline
            // Keep the selected native input while adapting a newer persisted state for restoration metadata.
            if try revision() != diskRevision {
                previous = try latestState()
                state = merge(local, onto: previous)
                try validate(state)
            }
            let legacy = selected.filter { $0.nativeObject == nil }
            if !legacy.isEmpty {
                let available = Set(state.items.filter { !$0.isDeleted }.map(\.id))
                guard legacy.allSatisfy({ available.contains($0.id) }) else { throw ClipboardStoreError.itemNotFound }
            }
            return HistoryRestoreOperation(local: state, previous: previous,
                native: try persistence.prepareHistoryRestore(inputs: selected))
        }
    }

    private func mutate<T>(historyAction: Bool = false, deletingItemIDs: [UUID] = [], restoringItemIDs: [UUID] = [],
                           refreshHistoryAfterChange: (() -> Bool)? = nil,
                           _ change: (inout StoreState) throws -> T) throws -> T {
        try mutateInTransaction(historyAction: historyAction, deletingItemIDs: deletingItemIDs,
                                restoringItemIDs: restoringItemIDs, refreshHistoryAfterChange: refreshHistoryAfterChange) { state, _ in
            try change(&state)
        }
    }

    private func mutateInTransaction<T>(historyAction: Bool = false, deletingItemIDs: [UUID] = [], restoringItemIDs: [UUID] = [],
                                        refreshHistoryAfterChange: (() -> Bool)? = nil,
                                        preparedRestore: HistoryRestoreOperation? = nil,
                                        _ change: (inout StoreState, ClipboardPersistence.Transaction) throws -> T) throws -> T {
        let local = preparedRestore?.local ?? current
        try validate(local)
        return try withLock {
            let remote = try preparedRestore?.previous ?? latestState()
            let (state, result) = try persistence.commit(previous: remote, deletingItemIDs: deletingItemIDs,
                                                       preparedTransaction: preparedRestore?.native.transaction) { transaction in
                // A prepared restore keeps its native selection and value snapshot across the pasteboard write.
                var state = preparedRestore?.local ?? merge(local, onto: remote)
                let result = try change(&state, transaction)
                if preparedRestore == nil, !restoringItemIDs.isEmpty {
                    let available = Set(state.items.filter { !$0.isDeleted }.map(\.id))
                    guard restoringItemIDs.allSatisfy({ available.contains($0) }) else {
                        throw ClipboardStoreError.itemNotFound
                    }
                }
                try validate(state)
                normalize(&state)
                let lists = transaction.repository.lists
                let history = try lists.synchronize(pinboards: state.pinboards, preferences: state.preferences, previous: remote)
                if !restoringItemIDs.isEmpty {
                    let positions = Dictionary(uniqueKeysWithValues: state.items.enumerated().map { ($0.element.id, $0.offset) })
                    let targets = try preparedRestore?.native.targets ?? transaction.repository.prepareHistoryItems(restoringItemIDs)
                    for update in transaction.repository.restoreHistoryItems(targets) {
                        guard let index = positions[update.id] else { continue }
                        state.items[index].createdAt = update.timestamp
                        state.items[index].updatedAt = update.timestamp
                        state.items[index].isInHistory = true
                    }
                    normalize(&state)
                }
                if historyAction || state.preferences.historyRetentionDays != remote.preferences.historyRetentionDays {
                    if let capacity = lists.historyCapacity(of: history) { expireHistory(&state, capacity: capacity) }
                }
                lists.refreshHistoryAfterOperation = historyAction || (refreshHistoryAfterChange?() ?? false)
                if state.cloudKitJournal != nil { try Self.captureCloudKit(&state, previous: remote) }
                return (state: state, result: result)
            }
            diskRevision = try revision()
            publish(state)
            return result
        }
    }

    /// Restore promotes the selected content in reverse order, as the original history repository does.
    func recordRestoredItems(_ ids: [UUID]) throws {
        guard !ids.isEmpty else { return }
        try mutate(historyAction: true, restoringItemIDs: ids) { _ in }
    }

    func recordRestoredSelection(_ operation: HistoryRestoreOperation) throws {
        guard !operation.native.targets.isEmpty else { return }
        try mutateInTransaction(historyAction: true, restoringItemIDs: operation.native.targets.map(\.id),
                                preparedRestore: operation) { _, _ in }
    }

    public func save() throws { try mutate { _ in } }

    private static func cloudKitGraph(_ state: StoreState, journal: OriginalCloudKitJournal,
                                     previousItems: [ClipboardItem] = []) throws -> [OriginalCloudDocument] {
        try OriginalCloudKitGraph.capture(items: state.items, pinboards: state.pinboards,
            applications: state.sourceApplications, capacity: state.preferences.historyRetentionDays,
            journal: journal, now: Date(), previousItems: previousItems)
    }

    private static func captureCloudKit(_ state: inout StoreState, previous: StoreState? = nil) throws {
        var journal = state.cloudKitJournal ?? OriginalCloudKitJournal()
        try journal.capture(cloudKitGraph(state, journal: journal, previousItems: previous?.items ?? []))
        state.cloudKitJournal = journal
    }

    /// Called only after an explicit CloudKit opt-in. Existing archives decode without a journal.
    public func prepareCloudKit(zoneName: String? = nil) throws -> OriginalCloudKitJournal {
        try mutate { state in
            if let zoneName {
                guard !zoneName.isEmpty else { throw PastoCloudKitError.invalidRecord }
                if let journal = state.cloudKitJournal {
                    guard journal.zoneName == zoneName else { throw PastoCloudKitError.invalidRecord }
                } else {
                    var journal = OriginalCloudKitJournal(); journal.zoneName = zoneName; state.cloudKitJournal = journal
                }
            }
            try Self.captureCloudKit(&state)
            return state.cloudKitJournal!
        }
    }

    /// Content, pending mappings, server metadata and engine checkpoints share one disk commit.
    /// On failure no advanced token is published; the delegate stops rather than losing changes.
    public func cloudKitTransaction(project: Bool = false,
        _ operation: (inout OriginalCloudKitJournal) throws -> Void) throws -> OriginalCloudKitJournal {
        try mutate { state in
            try Self.captureCloudKit(&state)
            var journal = state.cloudKitJournal!
            try operation(&journal)
            if project {
                let value = try OriginalCloudKitGraph.project(journal, preserving: state.items,
                    pinboards: state.pinboards, applications: state.sourceApplications)
                state.items = value.items; state.pinboards = value.pinboards; state.sourceApplications = value.applications
                if let capacity = value.capacity { state.preferences.historyRetentionDays = capacity }
                normalize(&state)
                let graph = try Self.cloudKitGraph(state, journal: journal)
                journal.localBaseline = Dictionary(uniqueKeysWithValues: graph.map { (OriginalCloudKitJournal.key($0.id, scope: $0.scope), $0) })
            }
            state.cloudKitJournal = journal
            return journal
        }
    }

    private static func cloudEntities(_ state: StoreState) -> [String: ICloudSyncEntity] {
        let values = state.items.map(ICloudSyncEntity.init(item:))
            + state.pinboards.map(ICloudSyncEntity.init(pinboard:))
            + state.sourceApplications.map(ICloudSyncEntity.init(application:))
        return Dictionary(uniqueKeysWithValues: values.map { ($0.key, $0) })
    }

    private static func cloudSnapshot(_ state: StoreState, metadata: ICloudSyncMetadata) -> ICloudSyncSnapshot {
        let entities = cloudEntities(state)
        let records = metadata.stamps.keys.sorted().compactMap { key -> ICloudSyncRecord? in
            guard let stamp = metadata.stamps[key], stamp.revision.deviceID == metadata.deviceID else { return nil }
            return ICloudSyncRecord(key: key, revision: stamp.revision, entity: stamp.digest == nil ? nil : entities[key])
        }
        return ICloudSyncSnapshot(deviceID: metadata.deviceID, records: records)
    }

    private func reconcileICloud(_ metadata: inout ICloudSyncMetadata, state: StoreState, now: Date) throws {
        let entities = Self.cloudEntities(state)
        iCloudDigestCache = iCloudDigestCache.filter { entities[$0.key] != nil }
        try metadata.reconcile(entities, now: now) { key, entity in
            if let cached = iCloudDigestCache[key], cached.entity == entity { return cached.digest }
            let digest = try entity.digest()
            iCloudDigestCache[key] = (entity, digest)
            return digest
        }
    }

    /// Capture edits and explicit deletions under the same lock as normal application/MCP writes.
    public func prepareICloudSync(now: Date = Date()) throws -> ICloudSyncSnapshot {
        try mutate { state in
            var metadata = state.cloudSyncMetadata ?? ICloudSyncMetadata()
            try reconcileICloud(&metadata, state: state, now: now)
            state.cloudSyncMetadata = metadata
            return Self.cloudSnapshot(state, metadata: metadata)
        }
    }

    public func resetICloudSyncIdentity() throws {
        try mutate { state in state.cloudSyncMetadata = nil }
    }

    /// Validate all incoming data before committing. Local preferences never leave this Mac.
    public func applyICloudSync(_ snapshots: [ICloudSyncSnapshot], now: Date = Date()) throws -> ICloudSyncSnapshot {
        for snapshot in snapshots { try snapshot.validate() }
        return try mutate { state in
            var metadata = state.cloudSyncMetadata ?? ICloudSyncMetadata()
            try reconcileICloud(&metadata, state: state, now: now)
            var entities = Self.cloudEntities(state)
            for snapshot in snapshots {
                for record in snapshot.records {
                    metadata.observe(record.revision)
                    if let stamp = metadata.stamps[record.key], !(stamp.revision < record.revision) { continue }
                    entities[record.key] = record.entity
                    metadata.stamps[record.key] = try ICloudSyncStamp(revision: record.revision, digest: record.entity?.digest())
                }
            }
            state.items = entities.values.compactMap(\.item)
            state.pinboards = entities.values.compactMap(\.pinboard)
            state.sourceApplications = entities.values.compactMap(\.application)
            // A group removal on another Mac must not leave dangling ownership here.
            normalize(&state)
            try reconcileICloud(&metadata, state: state, now: now)
            state.cloudSyncMetadata = metadata
            return Self.cloudSnapshot(state, metadata: metadata)
        }
    }

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

    private static func refreshNativeChecksum(_ item: inout ClipboardItem) {
        item.nativeChecksum = try? knownPasteboardChecksum(from: item.payloads)
    }

    @discardableResult
    public func add(_ item: ClipboardItem, sourceApplication: SourceApplicationRecord? = nil) throws -> UUID {
        try addWithInsertionResult(item, sourceApplication: sourceApplication).id
    }

    func addWithInsertionResult(_ item: ClipboardItem,
                                sourceApplication: SourceApplicationRecord? = nil,
                                recordCapture: Bool = false,
                                sourceProvider: (() -> (name: String, bundleID: String?, application: SourceApplicationRecord?))? = nil) throws -> (id: UUID, isNew: Bool) {
        var item = item
        if let sourceApplication {
            item.sourceApplicationBundleID = sourceApplication.bundleIdentifier
            item.sourceApplicationRelationIsKnown = true
        }
        var checksum: String? = nil
        if !recordCapture {
            checksum = try? Self.knownPasteboardChecksum(from: item.payloads)
            if item.nativeIdentifier == nil { item.nativeIdentifier = item.id.uuidString }
            item.nativeChecksum = checksum
        }
        return try mutateInTransaction(historyAction: recordCapture || item.isInHistory) { state, transaction in
            if recordCapture {
                checksum = try Self.knownPasteboardChecksum(from: item.payloads)
                guard item.nativeIdentifier != nil || checksum != nil else {
                    throw OriginalPasteboardItemCreationError.unsupportedContent
                }
                if item.nativeIdentifier == nil { item.nativeIdentifier = checksum }
                item.nativeChecksum = checksum
                item.rawPreview = nil
                item.imagePreviewMetadata = nil
            } else {
                item = Self.withPreviewMetadata(item, binaryPropertyList: state.preferences.useBinaryPlist,
                    preferQuickLookThumbnails: state.preferences.fileQuickLookThumbnailsEnabled,
                    generateMissingContentPreview: true)
            }
            if let sourceApplication { Self.upsertSourceApplication(sourceApplication, in: &state) }
            if let owner = item.pinboardOwnerID,
               !item.pinboardIDs.contains(owner) || !state.pinboards.contains(where: { $0.id == owner }) {
                throw ClipboardStoreError.pinboardNotFound
            }
            let capturedTarget = recordCapture ? try transaction.repository.capturedItem(checksum: checksum) : nil
            let existingIndex: Int?
            if recordCapture {
                if let capturedTarget {
                    if let index = state.items.firstIndex(where: { $0.id == capturedTarget.id }) {
                        existingIndex = index
                    } else {
                        state.items.append(try ClipboardPersistence.capturedItemValue(capturedTarget.object,
                            id: capturedTarget.id, replacingContentWith: item))
                        existingIndex = state.items.count - 1
                    }
                } else { existingIndex = nil }
            } else {
                existingIndex = state.items.firstIndex(where: { previous in
                if let checksum {
                    let previousChecksum = try? Self.knownPasteboardChecksum(from: previous.payloads)
                    if let previousChecksum { return checksum == previousChecksum }
                }
                let explicitIdentity = Self.hasValidExplicitPasteboardRepresentations(previous.payloads)
                    && Self.hasValidExplicitPasteboardRepresentations(item.payloads)
                return (explicitIdentity || previous.kind == item.kind && previous.plainText == item.plainText)
                    && Self.hasSamePasteboardRepresentations(previous.payloads, item.payloads)
                })
            }
            let result: (index: Int, isNew: Bool)
            if let i = existingIndex {
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
                if !recordCapture { state.items[i].updatedAt = max(Date(), item.updatedAt) }
                state.items[i].sourceName = item.sourceName
                state.items[i].sourceBundleID = item.sourceBundleID
                state.items[i].sourceApplicationBundleID = item.sourceApplicationBundleID
                state.items[i].sourceApplicationRelationIsKnown = item.sourceApplicationRelationIsKnown
                state.items[i].nativeChecksum = checksum
                if state.items[i].nativeIdentifier == nil { state.items[i].nativeIdentifier = state.items[i].id.uuidString }
                // 0x100360ff8 updates the existing content, not its creation device.
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
                result = (i, false)
            } else {
                state.items.removeAll { $0.id == item.id }
                state.items.append(item)
                result = (state.items.count - 1, true)
            }
            let target: (id: UUID, object: NSManagedObject)?
            if recordCapture {
                target = try capturedTarget ?? transaction.repository.prepareHistoryItems([state.items[result.index].id]).first!
                if target!.object.value(forKey: "nativeIdentifier") == nil {
                    target!.object.setValue(state.items[result.index].nativeIdentifier, forKey: "nativeIdentifier")
                }
                if capturedTarget == nil {
                    state.items[result.index].sourceDevice = transaction.repository.initializeCapturedDevice(target!)
                }
                let items = try Self.originalPasteboardItems(from: state.items[result.index].payloads)
                let kind = OriginalPasteboardClassification.f_10032362c(items)
                if let checksum = OriginalPasteboardChecksums.f_1003216bc(items, kind: kind) {
                    var value = state.items[result.index]
                    let preferences = state.preferences
                    transaction.repository.replaceCapturedItemData(target!, items: items, kind: kind, checksum: checksum,
                        useBinaryPlist: preferences.useBinaryPlist) {
                            value = Self.withPreviewMetadata(value, binaryPropertyList: preferences.useBinaryPlist,
                                preferQuickLookThumbnails: preferences.fileQuickLookThumbnailsEnabled,
                                generateMissingContentPreview: true)
                            return value.rawPreview
                        }
                    state.items[result.index] = value
                }
            } else { target = nil }
            if let sourceProvider {
                let source = sourceProvider()
                state.items[result.index].sourceName = source.name
                state.items[result.index].sourceBundleID = source.bundleID
                state.items[result.index].sourceApplicationBundleID = source.application?.bundleIdentifier
                state.items[result.index].sourceApplicationRelationIsKnown = true
                if let application = source.application {
                    Self.upsertSourceApplication(application, in: &state)
                }
            }
            if recordCapture {
                // 0x10037b034 → 0x100361ec0: stamp history after content/source
                // updates, not before preview generation or checksum lookup.
                try transaction.repository.applyCapturedSources(target!, item: state.items[result.index],
                    applications: state.sourceApplications, preserveDevice: true)
                let timestamp = transaction.repository.restoreHistoryItems([target!])[0].timestamp
                state.items[result.index].createdAt = timestamp
                state.items[result.index].updatedAt = timestamp
                state.items[result.index].isInHistory = true
            }
            return (state.items[result.index].id, result.isNew)
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
        guard let checksum = try Self.knownPasteboardChecksum(from: payloads) else {
            throw OriginalPasteboardItemCreationError.unsupportedContent
        }
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
                if let previousChecksum = try? Self.knownPasteboardChecksum(from: previous.payloads) {
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
                state.items[index].nativeChecksum = checksum
                if state.items[index].nativeIdentifier == nil { state.items[index].nativeIdentifier = state.items[index].id.uuidString }
                state.items[index].imagePreviewMetadata = nil
                state.items[index].rawPreview = nil
                state.items[index].updatedAt = Date()
            } else {
                index = state.items.count
                state.items.append(ClipboardItem(nativeIdentifier: checksum, nativeChecksum: checksum,
                                                 kind: kind, plainText: content, sourceName: "",
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
            if terms.isEmpty { return true }
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

    public func updateItem(_ input: ClipboardRestoreItem, title: String) throws {
        guard let object = input.nativeObject else {
            try updateItem(id: input.id, title: title, text: nil)
            return
        }
        try OriginalPreviewTitles.f_1003bae08(title,
            originalTitle: object.value(forKey: "title") as? String,
            defaultTitle: OriginalPreviewTitles.f_100309008(
                rawType: Int((object.value(forKey: "rawType") as? NSNumber)?.int64Value ?? 0),
                fileCount: OriginalImagePreviewMetadataCodec.decodeFiles(object.value(forKey: "rawPreview") as? Data)?.paths.count)) { replacement in
            try mutateInTransaction { state, _ in
                var item = input.resolvedItem()
                item.title = replacement ?? ""
                item.hasExplicitTitle = replacement != nil
                ClipboardItemTitlePersistence.update(item, on: object)
                if let index = state.items.firstIndex(where: { $0.id == input.id }) {
                    state.items[index] = item
                } else { state.items.append(item) }
            }
        }
    }

    public func updateItem(id: UUID, title: String? = nil, text: String? = nil) throws {
        try mutate { state in
            guard let i = state.items.firstIndex(where: { $0.id == id }) else { throw ClipboardStoreError.itemNotFound }
            if let title {
                let item = state.items[i]
                OriginalPreviewTitles.f_1003bae08(title, originalTitle: item.originalTitle,
                    defaultTitle: OriginalPreviewTitles.f_100309008(
                        rawType: Int(originalContentKind(of: item).rawValue),
                        fileCount: item.decodedFilePreviewMetadata?.paths.count)) { replacement in
                    state.items[i].title = replacement ?? ""
                    state.items[i].hasExplicitTitle = replacement != nil
                }
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
                Self.refreshNativeChecksum(&state.items[i])
                state.items[i].updatedAt = Date()
            }
        }
    }

    public func updateTextPreviewItem(id: UUID, attributedString: NSAttributedString) throws {
        try updateTextPreviewItem(id: id, input: nil, attributedString: attributedString)
    }

    public func updateTextPreviewItem(_ input: ClipboardRestoreItem, attributedString: NSAttributedString) throws {
        try updateTextPreviewItem(id: input.id, input: input, attributedString: attributedString)
    }

    private func updateTextPreviewItem(id: UUID, input: ClipboardRestoreItem?, attributedString: NSAttributedString) throws {
        try replacePreviewContent(id: id, input: input, plainText: attributedString.string) {
            OriginalTextPreviewSubmission.makeItem(attributedString)
        }
    }

    // All local content writers submit the captured entity through Writing +0x18 / 360ff8.
    private func replacePreviewContent(id: UUID, input: ClipboardRestoreItem?, plainText: @autoclosure () -> String?,
                                       makeRepresentation: () -> OriginalPasteboardItem) throws {
        try mutateInTransaction { state, transaction in
            let nativeObject = input?.nativeObject
            var index = state.items.firstIndex(where: { $0.id == id })
            guard nativeObject != nil || index != nil else { throw ClipboardStoreError.itemNotFound }
            let representation = makeRepresentation()
            let items = [representation]
            let nativeKind = OriginalPasteboardClassification.f_10032362c(items)
            guard let checksum = OriginalPasteboardChecksums.f_1003216bc(items, kind: nativeKind) else { return }
            let types = representation.f_10037da6c()
            var payloads: [String: Data] = [:]
            for type in types {
                if let data = representation.f_10037d810(forType: type) { payloads[type] = data }
            }
            payloads[Self.orderedPasteboardTypesPayloadKey] = try JSONEncoder().encode(types)
            let kind: ClipboardKind
            switch nativeKind {
            case .unknown: kind = .unknown
            case .image: kind = .image
            case .color: kind = .color
            case .files: kind = .files
            case .link: kind = .link
            case .text: kind = types.contains(NSPasteboard.PasteboardType.rtf.rawValue) ? .richText : .text
            }
            let target: (id: UUID, object: NSManagedObject)
            var item: ClipboardItem
            if let nativeObject, let input {
                target = (id: id, object: nativeObject)
                item = input.resolvedItem()
                if index == nil {
                    index = state.items.count
                    state.items.append(item)
                }
            } else {
                target = try transaction.repository.prepareHistoryItems([id]).first!
                item = state.items[index!]
            }
            let i = index!
            item.payloads = payloads
            item.plainText = plainText()
            item.kind = kind
            item.imagePreviewMetadata = nil
            item.rawPreview = nil
            // Native content replacement preserves recency; retain the old value-only adapter's clock.
            if nativeObject == nil { item.updatedAt = Date() }
            item.nativeChecksum = checksum
            let preferences = state.preferences
            // Editing shares 0x100360ff8 with capture: replace data before producing its preview.
            transaction.repository.replaceCapturedItemData(target, items: items, kind: nativeKind, checksum: checksum,
                useBinaryPlist: preferences.useBinaryPlist) {
                    item = Self.withPreviewMetadata(item, binaryPropertyList: preferences.useBinaryPlist,
                        preferQuickLookThumbnails: preferences.fileQuickLookThumbnailsEnabled,
                        generateMissingContentPreview: true)
                    return item.rawPreview
                }
            state.items[i] = item
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
            Self.refreshNativeChecksum(&state.items[i])
        }
    }

    public func updateImageItem(id: UUID, payloads: [String: Data]) throws {
        try updateImageItem(id: id, payloads: payloads, allowingEmptyRepresentation: false)
    }

    public func updateImagePreviewItem(_ input: ClipboardRestoreItem, payloads: [String: Data]) throws {
        guard input.nativeObject != nil else {
            try updateImagePreviewItem(id: input.id, payloads: payloads)
            return
        }
        let imageTypes = ["public.png", "public.jpeg", "public.heic", "public.tiff", "com.apple.icns", "com.compuserve.gif"]
        let types = imageTypes.filter { payloads[$0] != nil }
        guard !types.isEmpty || payloads.isEmpty else {
            throw OriginalPasteboardItemCreationError.unsupportedContent
        }
        try replacePreviewContent(id: input.id, input: input, plainText: nil) {
            OriginalPasteboardItem(types: types, dataByType: payloads)
        }
        startBackgroundTextRecognition(id: input.id)
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
            Self.refreshNativeChecksum(&state.items[i])
        }
        startBackgroundTextRecognition(id: id)
    }

    public func updateLinkItem(_ input: ClipboardRestoreItem, url: URL) throws {
        guard let object = input.nativeObject else {
            try updateLinkItem(id: input.id, url: url)
            return
        }
        let name: String?
        if let previous = OriginalImagePreviewMetadataCodec.decodeLink(object.value(forKey: "rawPreview") as? Data) {
            name = previous.name
        } else { name = "" }
        try replacePreviewContent(id: input.id, input: input, plainText: url.absoluteString) {
            OriginalPasteboardItem.f_10037c7bc(url, title: name)
        }
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
            Self.refreshNativeChecksum(&state.items[i])
        }
    }

    public func updateColorItem(_ input: ClipboardRestoreItem, text: String) throws {
        guard input.nativeObject != nil else {
            try updateColorItem(id: input.id, text: text)
            return
        }
        try replacePreviewContent(id: input.id, input: input, plainText: text) {
            OriginalPasteboardItem.f_10037c6d4(text)
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
            Self.refreshNativeChecksum(&state.items[i])
        }
    }

    public func delete(ids: Set<UUID>) throws { try setDeleted(ids: ids, deleted: true) }
    public func delete(ids: Set<UUID>, contextPinboardID: UUID?) throws {
        try delete(orderedIDs: ids.sorted { $0.uuidString < $1.uuidString }, contextPinboardID: contextPinboardID)
    }
    public func delete(orderedIDs: [UUID], contextPinboardID: UUID?) throws {
        try delete(orderedIDs: orderedIDs, currentPinboardID: { contextPinboardID })
    }
    public func delete(orderedIDs: [UUID], currentPinboardID: () -> UUID?) throws {
        let ids = Set(orderedIDs)
        var refreshHistory = false
        try mutate(deletingItemIDs: orderedIDs, refreshHistoryAfterChange: { refreshHistory }) { state in
            let contextPinboardID = currentPinboardID()
            refreshHistory = contextPinboardID == nil
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
        try permanentlyDelete(orderedIDs: ids.sorted { $0.uuidString < $1.uuidString })
    }
    public func permanentlyDelete(orderedIDs: [UUID]) throws {
        let ids = Set(orderedIDs)
        try mutate(deletingItemIDs: orderedIDs) { state in state.items.removeAll { ids.contains($0.id) } }
    }

    @discardableResult
    public func createPinboard(name: String, colorHex: String? = nil) throws -> Pinboard {
        guard !name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { throw ClipboardStoreError.invalidPinboardName }
        return try insertPinboard(name: name, colorHex: colorHex).board
    }

    /// The original AppIntent rejects an empty string without trimming the supplied name.
    @discardableResult
    public func createPinboardFromIntent(name: String) throws -> Pinboard {
        guard !name.isEmpty else { throw ClipboardStoreError.invalidPinboardName }
        return try insertPinboard(name: name, colorHex: nil).board
    }

    // 367c5c/368560: preserve the created List entity for subsequent group assignment.
    public func createPinboardTarget(name: String) throws -> ClipboardPinboardTarget {
        guard !name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { throw ClipboardStoreError.invalidPinboardName }
        return try insertPinboard(name: name, colorHex: nil).target
    }

    private func insertPinboard(name: String, colorHex: String?) throws -> (board: Pinboard, target: ClipboardPinboardTarget) {
        let result: (board: Pinboard, target: ClipboardPinboardTarget) = try mutateInTransaction { state, transaction in
            let code: UInt64?
            let value: String
            if let colorHex {
                value = colorHex
                code = OriginalPinboardAttributes.parsedColorCode(colorHex)
            } else {
                // Keep the original eight-color palette (0x100324a80), but prefer
                // unused colors as requested; the original creation path is random.
                let used = Set(state.pinboards.compactMap { board -> OriginalPinboardColor? in
                    guard let code = OriginalPinboardAttributes.colorCode(from: board.rawAttributes)
                        ?? OriginalPinboardAttributes.parsedColorCode(board.colorHex) else { return nil }
                    return OriginalPinboardColor(canonicalColorCode: code)
                })
                let unused = OriginalPinboardColor.allCases.filter { !used.contains($0) }
                let palette = unused.isEmpty ? OriginalPinboardColor.allCases : unused
                let color = palette[Int.random(in: 0..<palette.count)]
                code = color.canonicalColorCode
                value = String(format: "#%06llX", color.canonicalColorCode)
            }
            let id = UUID()
            let created = try transaction.repository.lists.insertPinboard(identifier: id.uuidString,
                name: name) {
                try code.map { try OriginalPinboardAttributes.encoded(colorCode: $0) }
            }
            let board = Pinboard(id: id, name: name, colorHex: value, sortOrder: 0,
                                 rawType: 2, rawAttributes: created.attributes)
            state.pinboards.append(board)
            return (board, ClipboardPinboardTarget(id: id, object: created.object))
        }
        var board = result.board
        if let metadata = result.target.nativeObject.value(forKey: "metadata") as? NSManagedObject,
           let index = metadata.value(forKey: "index") as? NSNumber { board.sortOrder = index.intValue }
        return (board, result.target)
    }
    public func renameList(_ target: ClipboardListTarget, rawName: String) throws {
        try mutateInTransaction { state, transaction in
            let lists = transaction.repository.lists
            lists.retainNativeList(target.nativeObject)
            lists.updateName(on: target.nativeObject) { $0 = OriginalPinboardTitle.normalizedRename(rawName) }
            projectNativeList(target, into: &state)
        }
    }

    public func updateListColor(_ target: ClipboardListTarget, colorCode: UInt64) throws {
        try mutateInTransaction { state, transaction in
            let lists = transaction.repository.lists
            lists.retainNativeList(target.nativeObject)
            lists.updateColor(on: target.nativeObject) { $0 = colorCode }
            projectNativeList(target, into: &state)
        }
    }

    private func projectNativeList(_ target: ClipboardListTarget, into state: inout StoreState) {
        if target.identifier == Self.historyListIdentifier {
            state.preferences.historyTitle = target.name
            return
        }
        guard let id = UUID(uuidString: target.identifier) else { return }
        guard let index = state.pinboards.firstIndex(where: { $0.id == id }) else {
            if let board = target.pinboardValue { state.pinboards.append(board) }
            return
        }
        state.pinboards[index].name = target.name
        state.pinboards[index].rawType = Int16(exactly: target.rawType) ?? 0
        let attributes = target.nativeObject.value(forKey: "rawAttributes") as? Data
        if state.pinboards[index].rawAttributes != attributes {
            state.pinboards[index].rawAttributes = attributes
            if let color = OriginalPinboardAttributes.colorCode(from: attributes) {
                state.pinboards[index].colorHex = String(format: "#%06llX", color)
            }
        }
        if let metadata = target.nativeObject.value(forKey: "metadata") as? NSManagedObject,
           let order = metadata.value(forKey: "index") as? NSNumber { state.pinboards[index].sortOrder = order.intValue }
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
    public func removeList(_ target: ClipboardListTarget) throws {
        try mutateInTransaction { state, transaction in
            let identifier = target.identifier
            let affected = transaction.repository.removePinboard(target.nativeObject)
            if let id = UUID(uuidString: identifier) {
                state.pinboards.removeAll { $0.id == id }
                for index in state.items.indices {
                    state.items[index].pinboardIDs.remove(id)
                    if state.items[index].pinboardOwnerID == id { state.items[index].pinboardOwnerID = nil }
                }
            }
            for object in affected {
                guard let key = object.value(forKey: "key") as? String, let id = UUID(uuidString: key) else { continue }
                if object.isDeleted {
                    state.items.removeAll { $0.id == id }
                    continue
                }
                let index = state.items.firstIndex { $0.id == id }
                var item: ClipboardItem
                if let index { item = state.items[index] }
                else { item = try ClipboardPersistence.item(object) }
                item.isInHistory = object.value(forKey: "timestamp") != nil
                if let owner = object.value(forKey: "list") as? NSManagedObject,
                   (owner.value(forKey: "rawType") as? NSNumber)?.int64Value == 2,
                   let ownerIdentifier = owner.value(forKey: "identifier") as? String,
                   let ownerID = UUID(uuidString: ownerIdentifier) {
                    item.pinboardOwnerID = ownerID
                    item.pinboardIDs = [ownerID]
                } else {
                    item.pinboardOwnerID = nil
                    item.pinboardIDs.removeAll()
                }
                try ClipboardItemOrderPersistence.project(&item, from: object)
                if let index { state.items[index] = item }
                else { state.items.append(item) }
            }
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
            item.nativeIdentifier = item.id.uuidString
            Self.refreshNativeChecksum(&item)
            item.createdAt = Date()
            item.updatedAt = item.createdAt
            state.items.append(item)
            return item.id
        }
    }
    public func assign(ids: Set<UUID>, to pinboardID: UUID?) throws {
        var ordered = items.filter { ids.contains($0.id) }.map(\.id)
        let cached = Set(ordered)
        // A UUID absent from the cached value array must still reach the transaction's current state.
        ordered += ids.subtracting(cached).sorted { $0.uuidString < $1.uuidString }
        try assign(orderedIDs: ordered, to: pinboardID)
    }

    /// Native tab item-drop keeps the supplied List through String lookup and local repository dispatch.
    public func dropItems(identifiers: [String], to target: ClipboardListTarget) throws {
        try mutateInTransaction { state, transaction in
            let values = try transaction.repository.dropItems(identifiers: identifiers, to: target.nativeObject)
            state.items.removeAll { transaction.repository.alreadyDeletedItemIDs.contains($0.id) }
            for item in values {
                if let index = state.items.firstIndex(where: { $0.id == item.id }) {
                    state.items[index] = item
                } else {
                    state.items.append(item)
                }
            }
        }
    }

    /// The local group menu retains its supplied entities through the repository transaction.
    public func assign(items: [ClipboardRestoreItem], to pinboardID: UUID?) throws {
        try assign(items: items, pinboardID: pinboardID, nativePinboard: nil)
    }

    public func assign(items: [ClipboardRestoreItem], to target: ClipboardPinboardTarget) throws {
        try assign(items: items, pinboardID: target.id, nativePinboard: target.nativeObject)
    }

    private func assign(items: [ClipboardRestoreItem], pinboardID: UUID?, nativePinboard: NSManagedObject?) throws {
        if pinboardID == nil, items.allSatisfy({ $0.nativeObject != nil }) {
            try unassignNative(items: items)
            return
        }
        guard let pinboardID, items.allSatisfy({ $0.nativeObject != nil }) else {
            try assign(orderedIDs: items.map(\.id), to: pinboardID)
            return
        }
        guard !items.isEmpty else { return }
        try mutateInTransaction { state, transaction in
            let pinboard: NSManagedObject
            if let nativePinboard {
                pinboard = nativePinboard
            } else {
                guard let current = try transaction.repository.lists.list(identifier: pinboardID.uuidString) else {
                    throw ClipboardStoreError.pinboardNotFound
                }
                pinboard = current
            }
            let destination = try transaction.repository.assignItems(items.map { $0.nativeObject! }, to: pinboard)
            for item in destination {
                if let index = state.items.firstIndex(where: { $0.id == item.id }) {
                    state.items[index] = item
                } else {
                    state.items.append(item)
                }
            }
        }
    }

    private func unassignNative(items: [ClipboardRestoreItem]) throws {
        try mutateInTransaction { state, transaction in
            let affected = transaction.repository.unassignItems(items.map { (id: $0.id, object: $0.nativeObject!) })
            // Native sequence mutations finish before compatibility projection can fail.
            for target in affected {
                if target.object.isDeleted {
                    state.items.removeAll { $0.id == target.id }
                    continue
                }
                let index = state.items.firstIndex { $0.id == target.id }
                var item: ClipboardItem
                if let index { item = state.items[index] }
                else { item = try ClipboardPersistence.item(target.object) }
                if let owner = target.object.value(forKey: "list") as? NSManagedObject,
                   (owner.value(forKey: "rawType") as? NSNumber)?.int64Value == 2,
                   let identifier = owner.value(forKey: "identifier") as? String,
                   let ownerID = UUID(uuidString: identifier) {
                    item.pinboardOwnerID = ownerID
                    item.pinboardIDs = [ownerID]
                } else {
                    item.pinboardOwnerID = nil
                    item.pinboardIDs.removeAll()
                }
                try ClipboardItemOrderPersistence.project(&item, from: target.object)
                if let index { state.items[index] = item }
                else { state.items.append(item) }
            }
        }
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

    public func moveList(_ target: ClipboardListTarget, toOffset offset: Int) throws {
        try mutateInTransaction { state, transaction in
            let ordered = transaction.repository.lists.moveList(target.nativeObject, toOffset: offset)
            for object in ordered {
                projectNativeList(ClipboardListTarget(object: object), into: &state)
            }
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
            var archive = current
            archive.cloudSyncMetadata = nil
            archive.cloudKitJournal = nil
            try writeAtomically(encoder.encode(archive), to: url)
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
                if let existing = items[item.id] {
                    if item.nativeIdentifier == nil { item.nativeIdentifier = existing.nativeIdentifier }
                    if item.nativeChecksum == nil { item.nativeChecksum = existing.nativeChecksum }
                    if item.sourceIdentifier == nil { item.sourceIdentifier = existing.sourceIdentifier }
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
