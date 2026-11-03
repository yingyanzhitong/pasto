import Combine
import Foundation
import CoreSpotlight
import CryptoKit
import PastoCore
import UniformTypeIdentifiers
import os

// The delegate task retains only this weak target; its strong indexer scope ends before SDK acknowledgement.
private final class ReplicaSearchIndexDelegateTarget: @unchecked Sendable {
    weak var indexer: ReplicaSearchIndex?
    init(_ indexer: ReplicaSearchIndex) { self.indexer = indexer }
}

// The UI composition owns the service; a running indexer must not extend its lifetime.
@MainActor
final class ReplicaSpotlightService {
    let domain: String
    let index: CSSearchableIndex

    init(directoryURL: URL) {
        let hash = SHA256.hash(data: Data(directoryURL.standardizedFileURL.path.utf8))
        domain = "PasteReplica." + hash.map { String(format: "%02x", $0) }.joined()
        index = CSSearchableIndex(name: domain)
    }
}

/// Delegates matching to the same system query engine as the reference.
/// Record identifiers cross the SDK unchanged; content is read at SDK serialization.
@MainActor
final class ReplicaSearchIndex: NSObject, CSSearchableIndexDelegate {
    // 0x1002d6274 -> 0x1002e19c8: the production search service caps results at 100.
    private static let maximumResultCount = 100
    // 0x1002ea78c / 0x1002eaea4: indexer batches are separate from the query result cap.
    private static let indexingBatchSize = 100
    // 0x1002e6dc4 / 0x1002e74e4: the delete service independently batches 100 input IDs.
    private static let deletionBatchSize = 100

    private enum IndexingError: Error { case unavailable }

    private struct Entry: Equatable {
        let record: ClipboardSearchRecord
        var id: UUID { record.id }
        var nativeIdentifier: String? { record.nativeIdentifier }
        var searchIdentifier: String { record.searchIdentifier }
        var title: String { record.title }
        var modified: Date? { record.modified }
        var app: String? { record.app }
        var type: String { record.type }
        var device: String? { record.device }
        var pinboard: String? { record.pinboard }
        var content: (() -> String?)? { record.content }
        var imageData: (() -> Data?)? { record.imageData }

        init(_ record: ClipboardSearchRecord) { self.record = record }
        init(_ item: ClipboardItem, app: String?) { record = .snapshot(item, app: app) }
    }

    private struct Request: Equatable {
        let entries: [Entry]
        let nodes: [OriginalSearchQueryNode]
        let sourceIdentifier: String?
    }

    private struct HistoryWork {
        let changes: [OriginalSearchHistoryChange]
        let complete: (Error?) -> Void
    }

    private let domain: String
    private let nativeIdentifierFormatKey: String
    private let index: CSSearchableIndex
    private let resolveWriteIndex: () -> CSSearchableIndex?
    private weak var store: ClipboardStore?
    private var suggestionDataSource: OriginalSearchSuggestions.Provider?
    private let appKey = CSCustomAttributeKey(keyName: "pasteApp", searchable: true, searchableByDefault: true, unique: false, multiValued: false)!
    private let typeKey = CSCustomAttributeKey(keyName: "pasteType", searchable: true, searchableByDefault: true, unique: false, multiValued: false)!
    private let deviceKey = CSCustomAttributeKey(keyName: "pasteDevice", searchable: true, searchableByDefault: true, unique: false, multiValued: false)!
    private let pinboardKey = CSCustomAttributeKey(keyName: "pastePinboard", searchable: true, searchableByDefault: true, unique: false, multiValued: false)!
    private var sourceItems: [ClipboardItem] = []
    private var sourceApplications: [SourceApplicationRecord] = []
    private var entries: [Entry] = []
    private var requested: Request?
    private var pending: Request?
    private var pendingMayInitializeIndex = false
    private var pendingResetsIndex = false
    private var indexed: [UUID: Entry] = [:]
    private let stateStore = OriginalSearchIndexStateStore()
    private var mayRestoreSavedState = true
    private var lastSourceIdentifier: String?
    private var needsReset = true
    // 0x1002f20a0/2f2214: independent of the serial queue's Task handle.
    private var isRunning = false
    private var consecutiveTransientFailures = 0
    private var worker: Task<Void, Never>?
    private var historyTask: Task<Void, Never>?
    private var ocrTask: Task<Void, Never>?
    private var ocrQueue: [String] = []
    private var ocrQueuedIdentifiers: Set<String> = []
    private var pendingHistory: [HistoryWork] = []
    private var queryTask: Task<Void, Never>?
    private var queryNodes: [OriginalSearchQueryNode]?
    private let logger = Logger(subsystem: "com.yingyanzhitong.paste-replica", category: "search")
    // Index-work continuation relays; the SDK acknowledgement runs outside the owner scope.
    private var acknowledgements: [() -> Void] = []
    private var reindexIdentifiers: [String] = []
    private(set) var queryString = ""
    private(set) var identifiers: Set<UUID> = []
    private(set) var orderedIdentifiers: [UUID] = []
    private var resultSource: ClipboardSearchCollection?
    private var resultObservation: AnyCancellable?
    var resultItemReferences: [UUID: ClipboardCollectionItemReference] { resultSource?.value.itemReferences ?? [:] }
    var onCollectionUpdate: ((Set<UUID>) -> Void)?
    private(set) var error: Error?
    var onUpdate: (() -> Void)?

    init(service: ReplicaSpotlightService, store: ClipboardStore? = nil) {
        domain = service.domain
        nativeIdentifierFormatKey = "pasto.search.nativeIdentifiers." + domain
        index = service.index
        resolveWriteIndex = { [weak service] in service?.index }
        self.store = store
        super.init()
        lastSourceIdentifier = stateStore.indexedStoreID
        // Pasto compatibility: rebuild the disposable index once before reusing old prefixed IDs.
        mayRestoreSavedState = UserDefaults.standard.bool(forKey: nativeIdentifierFormatKey)
        index.indexDelegate = self
    }

    // 0x1002e1b54: the installed optional source belongs to the search index.
    func setSuggestionDataSource(_ provider: OriginalSearchSuggestions.Provider?) {
        suggestionDataSource = provider
    }

    // 2dfb18/2dfc64/2dfd4c/2dfe58 read the installed optional source at each group call.
    func suggestions(contextNode: OriginalSearchQueryNode,
                     currentNodes: [OriginalSearchQueryNode]) -> [OriginalSearchQueryNode] {
        let provider = OriginalSearchSuggestions.Provider(
            app: { try self.suggestionDataSource?.app($0) ?? [] },
            type: { try self.suggestionDataSource?.type($0) ?? [] },
            device: { try self.suggestionDataSource?.device($0) ?? [] },
            pinboard: { try self.suggestionDataSource?.pinboard($0) ?? [] })
        return OriginalSearchSuggestions.f_1002df190(
            contextNode: contextNode, currentNodes: currentNodes, provider: provider)
    }

    func availableFilters() -> [UInt8: [OriginalSearchQueryNode]] {
        OriginalSearchSuggestions.f_1002e00a0(provider: { suggestionDataSource })
    }

    deinit { historyTask?.cancel(); queryTask?.cancel() }

    // 0x1003600a0: cancel/replace the query task without waiting for the indexer.
    private func replaceQuery(with nodes: [OriginalSearchQueryNode]) {
        queryTask?.cancel()
        let predicate = OriginalSearchQuery.f_1002f45b0(nodes)
        queryString = predicate
        error = nil
        queryTask = Task { [weak self] in
            guard let self, !Task.isCancelled else { return }
            do {
                let found = try await Self.matchingIdentifiers(predicate: predicate, limit: Self.maximumResultCount)
                try Task.checkCancellation()
                if let store {
                    installResultSource(store.makeSearchCollection(identifiers: found))
                } else {
                    installResultSource(nil)
                    orderedIdentifiers = entries.filter { found.contains($0.searchIdentifier) }.map(\.id)
                    identifiers = Set(orderedIdentifiers)
                }
                error = nil
                onUpdate?()
            } catch is CancellationError {
                // 0x1003602fc preserves the prior result for a cancelled query.
            } catch {
                guard !Task.isCancelled else { return }
                logger.error("Search query failed: \(error.localizedDescription, privacy: .public)")
                self.error = error
                installResultSource(nil)
                onUpdate?()
            }
        }
    }

    private func installResultSource(_ source: ClipboardSearchCollection?) {
        resultObservation = nil
        resultSource = source
        orderedIdentifiers = source?.value.identifiers ?? []
        identifiers = Set(orderedIdentifiers)
        resultObservation = source?.publisher.dropFirst().sink { [weak self] snapshot in
            guard let self else { return }
            self.orderedIdentifiers = snapshot.identifiers
            self.identifiers = Set(snapshot.identifiers)
            self.onCollectionUpdate?(snapshot.updatedIdentifiers)
        }
    }

    // The query and its iterator belong to this task, not to the serial index-write worker.
    nonisolated private static func matchingIdentifiers(predicate: String, limit: Int) async throws -> [String] {
        guard !predicate.isEmpty else { return [] }
        let context = CSSearchQueryContext()
        context.fetchAttributes = []
        let query = CSSearchQuery(queryString: predicate, queryContext: context)
        var found: [String] = []
        var resultCount = 0
        for try await result in query.results {
            resultCount += 1
            found.append(result.item.uniqueIdentifier)
            if resultCount == limit { break }
        }
        try Task.checkCancellation()
        return found
    }

    private func startHistoryObservation() {
        // 0x1002f14cc/2f00dc installs a new observer handle without an active/old-handle gate.
        guard let store else { return }
        historyTask = Task { @MainActor [weak self] in
            await store.observeSearchChanges { [weak self] changes in
                guard let self else { throw CancellationError() }
                try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<Void, Error>) in
                    self.pendingHistory.append(HistoryWork(changes: changes) { error in
                        if let error { continuation.resume(throwing: error) }
                        else { continuation.resume() }
                    })
                    self.startWorker()
                }
            }
        }
    }

    // 0x1002f2d18: stop observation, then cancel and await OCR without clearing pending IDs.
    private func stopIndexing() async {
        isRunning = false
        historyTask?.cancel()
        historyTask = nil
        if let ocrTask {
            ocrTask.cancel()
            await ocrTask.value
        }
        ocrTask = nil
    }

    private func enqueueOCR(_ entries: [Entry]) {
        // Filter against the existing queued set before inserting this batch: same-batch duplicates remain.
        let added = entries.filter { $0.imageData != nil && !ocrQueuedIdentifiers.contains($0.searchIdentifier) }
            .map(\.searchIdentifier)
        ocrQueuedIdentifiers.formUnion(added)
        ocrQueue.append(contentsOf: added)
    }

    // 0x1002ec520: one low-priority consumer while active, also allowing a cancelled task replacement.
    private func startOCRWorker() {
        guard isRunning, !ocrQueue.isEmpty, ocrTask == nil || ocrTask?.isCancelled == true else { return }
        ocrTask = Task(priority: .low) { [self] in
            await drainOCRQueue()
            ocrTask = nil
        }
    }

    private func drainOCRQueue() async {
        while isRunning && !Task.isCancelled && !ocrQueue.isEmpty {
            let identifier = ocrQueue.removeFirst()
            ocrQueuedIdentifiers.remove(identifier)
            do {
                guard let entry = try liveEntries(identifiers: [identifier]).first else { continue }
                try Task.checkCancellation()
                guard let readImage = entry.imageData, let data = readImage() else { continue }
                // The original indexer is an actor; use the existing background recognizer from this MainActor adapter.
                let words = try await ImageTextRecognizer.recognizeWords(imageData: data, maximumDimension: 1024)
                let text = words.map(\.text).joined(separator: " ")
                if !text.isEmpty {
                    let enriched = Entry(entry.record.appendingRecognizedText(text))
                    let item = searchableItem(enriched, isUpdate: true)
                    _ = try await Self.writeSearchableItems([item], index: resolveWriteIndex())
                }
                try await ContinuousClock().sleep(for: .seconds(2))
            } catch is CancellationError {
                return
            } catch {
                logger.error("Search image recognition failed: \(error.localizedDescription, privacy: .public)")
            }
        }
    }

    // 0x1002e39b4: local Spotlight availability/connection failures, not arbitrary NSError codes.
    private static func isTransientIndexError(_ error: Error) -> Bool {
        let error = error as NSError
        return error.domain == CSIndexErrorDomain && (error.code == -1000 || error.code == -1003)
    }

    // 0x1002e7914/2e7a14/2e7e4c: three attempts of the whole operation, with 1s/2s delays.
    private func retryTransientIndexErrors(_ operation: () async throws -> Void) async throws {
        var failureCount = 0
        while true {
            do {
                try await operation()
                consecutiveTransientFailures = 0
                return
            } catch {
                guard Self.isTransientIndexError(error) else { throw error }
                failureCount += 1
                guard failureCount < 3 else {
                    consecutiveTransientFailures += 1
                    throw error
                }
                let delay = Duration.seconds(1 << (failureCount - 1))
                logger.info("Transient search index error \((error as NSError).code); retry \(failureCount)/3 after \(delay.description, privacy: .public)")
                try await ContinuousClock().sleep(for: delay)
            }
        }
    }

    private func liveEntries(identifiers: [String]?) throws -> [Entry] {
        guard let store else {
            guard let identifiers else { return entries }
            return entries.filter { identifiers.contains($0.searchIdentifier) }
        }
        return try store.searchIndexRecords(identifiers: identifiers).map { Entry($0) }
    }

    // 0x1002ea78c / 0x1002eaa10 / 0x1002eaea4: advance by input IDs, not fetched rows.
    private func reindexTargets(_ identifiers: [String]) async throws {
        // 0x1002ea78c filters empty identifiers before forming the 100-ID batches.
        let input = identifiers.filter { !$0.isEmpty }
        guard !input.isEmpty else { return }
        var refreshed: [Entry] = []
        for lowerBound in stride(from: 0, to: input.count, by: Self.indexingBatchSize) {
            guard isRunning, !Task.isCancelled else { break }
            let upperBound = min(lowerBound + Self.indexingBatchSize, input.count)
            let live = try liveEntries(identifiers: Array(input[lowerBound..<upperBound]))
            enqueueOCR(live)
            if !live.isEmpty {
                let replacedIdentifiers = live.compactMap { entry -> String? in
                    guard let previous = indexed[entry.id],
                          previous.searchIdentifier != entry.searchIdentifier else { return nil }
                    return previous.searchIdentifier
                }
                if !replacedIdentifiers.isEmpty { try await deleteIdentifiers(replacedIdentifiers) }
                let changed = live.map { searchableItem($0, isUpdate: true) }
                _ = try await Self.writeSearchableItems(changed, index: resolveWriteIndex())
                refreshed.append(contentsOf: live)
            }
        }
        for entry in refreshed { indexed[entry.id] = entry }
        startOCRWorker()
    }

    private func deleteIdentifiers(_ identifiers: [String]) async throws {
        for lowerBound in stride(from: 0, to: identifiers.count, by: Self.deletionBatchSize) {
            let upperBound = min(lowerBound + Self.deletionBatchSize, identifiers.count)
            let input = identifiers[lowerBound..<upperBound]
            let batch = Array(input)
            try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<Void, Error>) in
                index.deleteSearchableItems(withIdentifiers: batch) { error in
                    if let error { continuation.resume(throwing: error) }
                    else { continuation.resume() }
                }
            }
            // The SDK key is the native String identifier; UUID remains the local cache key.
            let deleted = Set(input)
            indexed = indexed.filter { !deleted.contains($0.value.searchIdentifier) }
        }
    }

    private func applyHistoryChanges(_ changes: [OriginalSearchHistoryChange]) async throws {
        for change in changes {
            try Task.checkCancellation()
            switch change {
            case .inserted(let identifiers), .updated(let identifiers):
                let live = try liveEntries(identifiers: identifiers)
                guard !live.isEmpty else { continue }
                enqueueOCR(live)
                let replacedIdentifiers = live.compactMap { entry -> String? in
                    guard let previous = indexed[entry.id], previous.searchIdentifier != entry.searchIdentifier else { return nil }
                    return previous.searchIdentifier
                }
                if !replacedIdentifiers.isEmpty { try await deleteIdentifiers(replacedIdentifiers) }
                _ = try await Self.writeSearchableItems(live.map { searchableItem($0, isUpdate: false) }, index: resolveWriteIndex())
                for entry in live { indexed[entry.id] = entry }
                startOCRWorker()
            case .deleted(let identifiers):
                try await deleteIdentifiers(identifiers)
            }
        }
    }

    func update(items: [ClipboardItem], nodes: [OriginalSearchQueryNode]) {
        // 0x10035ff00 deduplicates query nodes independently of collection/entity changes.
        if queryNodes != nodes {
            queryNodes = nodes
            replaceQuery(with: nodes)
        }
        let applications = store?.sourceApplications ?? []
        if sourceItems != items || sourceApplications != applications {
            sourceItems = items
            sourceApplications = applications
            let names = store.map { ReplicaSearchSuggestionSource.applicationNames(for: items, store: $0) }
                ?? items.map {
                    if $0.sourceApplicationBundleID == nil, $0.sourceApplicationRelationIsKnown == true { return nil }
                    return $0.sourceName.isEmpty ? nil : $0.sourceName
                }
            entries = zip(items, names).map { item, app in
                return Entry(item, app: app)
            }
        }
        let request = Request(entries: entries, nodes: nodes, sourceIdentifier: store?.searchSourceIdentifier)
        guard requested != request else { return }
        requested = request
        pending = request
        pendingMayInitializeIndex = true
        startWorker()
        onUpdate?()
    }

    func retry() {
        guard let requested else { return }
        pending = requested
        pendingMayInitializeIndex = true
        startWorker()
        replaceQuery(with: requested.nodes)
        onUpdate?()
    }

    private func startWorker() {
        guard worker == nil else { return }
        worker = Task { [weak self] in
            guard let self else { return }
            await drain()
        }
    }

    // 0x1002e20b8: resolve weak service first; retain only the SDK index across its callback.
    // The optional result distinguishes a vanished service from a successful SDK completion.
    private static func writeSearchableItems(_ items: [CSSearchableItem],
                                              index: CSSearchableIndex?) async throws -> Void? {
        guard let index else { return nil }
        try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<Void, Error>) in
            index.indexSearchableItems(items) { error in
                if let error { continuation.resume(throwing: error) }
                else { continuation.resume() }
            }
        }
        return ()
    }

    private func searchableItem(_ entry: Entry, isUpdate: Bool) -> CSSearchableItem {
        let attributes = CSSearchableItemAttributeSet(contentType: .content)
        attributes.title = entry.title
        // 0x1002e3ce8 invokes the optional content callback before limiting its result.
        let content = entry.content?()
        let text = content.map { String($0.prefix(5000)) }
        attributes.textContent = text
        if ProcessInfo.processInfo.isOperatingSystemAtLeast(.init(majorVersion: 26, minorVersion: 4, patchVersion: 0)) {
            attributes.contentDescription = text
        }
        attributes.contentModificationDate = entry.modified
        attributes.setValue(entry.app.map { $0 as NSString }, forCustomKey: appKey)
        attributes.setValue(entry.type as NSString, forCustomKey: typeKey)
        attributes.setValue(entry.device.map { $0 as NSString }, forCustomKey: deviceKey)
        attributes.setValue((entry.pinboard ?? "") as NSString, forCustomKey: pinboardKey)
        let item = CSSearchableItem(uniqueIdentifier: entry.searchIdentifier,
                                    domainIdentifier: domain, attributeSet: attributes)
        item.expirationDate = .distantFuture
        // 0x1002f2ca8 → 0x1002ea770 → 0x1002e1bac → 0x1002e3ce8.
        item.isUpdate = isUpdate
        return item
    }

    private func savedStateForRestore(sourceIdentifier: String?) -> OriginalSearchIndexingState? {
        guard let state = stateStore.savedState,
              state.schemaVersion == OriginalSearchIndexingState.currentSchemaVersion else { return nil }
        if let previous = stateStore.indexedStoreID, let current = sourceIdentifier, previous != current { return nil }
        return state
    }

    // 0x1002f00dc/2f3248/2f32d4: a probe error does not prove that the index is empty.
    private func restoreCompletedStateIfHealthy(_ state: OriginalSearchIndexingState) async -> Bool {
        guard state.indexedItems >= state.totalItems, state.totalItems > 0 else { return false }
        do {
            let found = try await Self.matchingIdentifiers(
                predicate: "contentModificationDate >= $time.iso(1970-01-01T00:00:00Z)",
                limit: Self.maximumResultCount)
            return !found.isEmpty
        } catch {
            logger.error("Search index health probe failed: \(error.localizedDescription, privacy: .public)")
            return true
        }
    }

    private func indexInitialSnapshot(_ fallback: [Entry], resuming saved: OriginalSearchIndexingState?) async throws -> Bool {
        let before = saved?.oldestTimestamp
        let allIDs = try store?.searchIndexIdentifiers(before: before) ?? fallback.filter { entry in
            guard let before else { return true }
            guard let timestamp = entry.modified else { return false }
            return timestamp < before
        }.map(\.searchIdentifier)
        guard !allIDs.isEmpty else { return false }
        defer { startOCRWorker() }
        let input = allIDs.filter { !$0.isEmpty }
        let invalid = allIDs.count - input.count
        let indexedBefore = saved?.indexedItems ?? 0
        var total = saved?.totalItems ?? allIDs.count
        if indexedBefore < 1 { total -= invalid }
        var state = OriginalSearchIndexingState(schemaVersion: OriginalSearchIndexingState.currentSchemaVersion,
            totalItems: total, indexedItems: indexedBefore, oldestTimestamp: nil, invalidItems: invalid)
        for lowerBound in stride(from: 0, to: input.count, by: Self.indexingBatchSize) {
            guard isRunning, !Task.isCancelled else { break }
            let upperBound = min(lowerBound + Self.indexingBatchSize, input.count)
            let live = try liveEntries(identifiers: Array(input[lowerBound..<upperBound]))
            enqueueOCR(live)
            if !live.isEmpty {
                do {
                    // 0x1002e8de0 -> c3e850 -> 2ea1d8: retry this fetched batch, not the snapshot.
                    try await retryTransientIndexErrors {
                        let changed = live.map { searchableItem($0, isUpdate: false) }
                        _ = try await Self.writeSearchableItems(changed, index: resolveWriteIndex())
                    }
                } catch is CancellationError {
                    // 0x1002e9d54: cancellation uses normal finalization's active/task gates.
                    break
                } catch {
                    // Failed batches do not reach progress save, completion, or the initializer's catch.
                    logger.error("Search snapshot indexing failed: \(error.localizedDescription, privacy: .public)")
                    return false
                }
            }
            state.indexedItems += live.count
            state.oldestTimestamp = live.compactMap(\.modified).min()
            try stateStore.save(state)
            for entry in live { indexed[entry.id] = entry }
        }
        // 0x1002ea410 marks a non-cancelled finished pass complete, including missing IDs.
        guard isRunning, !Task.isCancelled else { return true }
        state.indexedItems = state.totalItems
        try stateStore.save(state)
        return true
    }

    private func clearIndex() async throws {
        try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<Void, Error>) in
            index.deleteAllSearchableItems { error in
                if let error { continuation.resume(throwing: error) }
                else { continuation.resume() }
            }
        }
        indexed = [:]
        // Only a successful SDK clear retires the legacy encoding for this local index.
        UserDefaults.standard.set(true, forKey: nativeIdentifierFormatKey)
    }

    // 0x1002f1ca0/2f201c: clear while inactive, then enter the normal initialization path.
    private func resetIndex(_ request: Request) async throws {
        if isRunning { await stopIndexing() }
        try stateStore.save(nil)
        try await clearIndex()
        needsReset = true
        mayRestoreSavedState = false
        try await initializeIndexIfNeeded(request)
    }

    private func initializeIndexIfNeeded(_ request: Request) async throws {
        if let previous = lastSourceIdentifier, let current = request.sourceIdentifier, previous != current {
            needsReset = true
        }
        if needsReset && isRunning { await stopIndexing() }
        guard !isRunning else { return }
        isRunning = true
        do {
            // A new start reloads persisted progress; an explicit reset still disables reuse.
            if !needsReset {
                needsReset = true
                mayRestoreSavedState = true
            }
            // 0x1002efccc: unavailable indexing must not start a snapshot/write/observer.
            if needsReset && !CSSearchableIndex.isIndexingAvailable() { throw IndexingError.unavailable }
            var restoredCompletedState = false
            var resumeState: OriginalSearchIndexingState?
            if needsReset && mayRestoreSavedState,
               let saved = savedStateForRestore(sourceIdentifier: request.sourceIdentifier) {
                if saved.indexedItems < saved.totalItems {
                    // 0x1002f00dc: copy the old cursor and keep indexed/total counters.
                    resumeState = saved
                    needsReset = false
                } else {
                    let healthy = await restoreCompletedStateIfHealthy(saved)
                    // A full delegate reset received during the probe must remain authoritative.
                    restoredCompletedState = healthy && mayRestoreSavedState
                    if restoredCompletedState { needsReset = false }
                }
            }
            mayRestoreSavedState = false
            if let current = request.sourceIdentifier {
                lastSourceIdentifier = current
                stateStore.indexedStoreID = current
            }
            let usesSnapshot = !restoredCompletedState
            let currentEntries = request.entries
            if needsReset {
                try stateStore.save(nil)
                needsReset = false
                try await clearIndex()
            }
            let current = Dictionary(uniqueKeysWithValues: currentEntries.map { ($0.id, $0) })
            let deleted = usesSnapshot && store == nil ? Set(indexed.keys).subtracting(current.keys) : Set<UUID>()
            if !deleted.isEmpty {
                try await deleteIdentifiers(deleted.compactMap { indexed[$0]?.searchIdentifier })
            }
            // 0x1002f00dc/2f14cc installs change observation before requesting snapshot IDs.
            startHistoryObservation()
            if usesSnapshot {
                if try await indexInitialSnapshot(currentEntries, resuming: resumeState) {
                    // 0x1002f1a44/2f1aa4 consumes the pass's Bool without clearing activity.
                    logger.info("Spotlight indexation complete.")
                }
            }
            if usesSnapshot && store == nil { indexed = current }
        } catch {
            isRunning = false
            throw error
        }
    }

    private func drain() async {
        while pending != nil || !pendingHistory.isEmpty {
            if !pendingHistory.isEmpty {
                let work = pendingHistory.removeFirst()
                do { try await applyHistoryChanges(work.changes); work.complete(nil) }
                catch { work.complete(error) }
                continue
            }
            guard let request = pending else { break }
            pending = nil
            let mayInitializeIndex = pendingMayInitializeIndex
            pendingMayInitializeIndex = false
            let resetsIndex = pendingResetsIndex
            pendingResetsIndex = false
            let forcedIdentifiers = reindexIdentifiers
            reindexIdentifiers = []
            var requestAcknowledgements = acknowledgements
            acknowledgements = []
            do {
                if resetsIndex {
                    try await retryTransientIndexErrors {
                        try await resetIndex(request)
                    }
                } else if mayInitializeIndex {
                    try await initializeIndexIfNeeded(request)
                }
                if !forcedIdentifiers.isEmpty {
                    try await retryTransientIndexErrors {
                        try await reindexTargets(forcedIdentifiers)
                    }
                }
                // Reindex acknowledgements cover this index operation, not a following search.
                let completed = requestAcknowledgements
                requestAcknowledgements = []
                completed.forEach { $0() }
            } catch {
                logger.error("Search index operation failed: \(error.localizedDescription, privacy: .public)")
                // 0x1002f2468/2f2a30 logs and returns without requesting another full reset.
            }
            // The original delegate also acknowledges after its indexer catches an operation error.
            requestAcknowledgements.forEach { $0() }
        }
        worker = nil
    }

    nonisolated func searchableIndex(_ searchableIndex: CSSearchableIndex,
                                    reindexAllSearchableItemsWithAcknowledgementHandler acknowledgementHandler: @escaping () -> Void) {
        rebuild(identifiers: nil, acknowledgementHandler)
    }

    nonisolated func searchableIndex(_ searchableIndex: CSSearchableIndex,
                                    reindexSearchableItemsWithIdentifiers identifiers: [String],
                                    acknowledgementHandler: @escaping () -> Void) {
        rebuild(identifiers: identifiers, acknowledgementHandler)
    }

    nonisolated private func rebuild(identifiers: [String]?, _ acknowledge: @escaping () -> Void) {
        let target = ReplicaSearchIndexDelegateTarget(self)
        Task {
            await ReplicaSearchIndex.performDelegateRebuild(target, identifiers: identifiers)
            acknowledge()
        }
    }

    // 0x1002e467c/2e48a0 load the weak indexer; 2e46fc/2e4928 release it before ack.
    private static func performDelegateRebuild(_ target: ReplicaSearchIndexDelegateTarget,
                                               identifiers: [String]?) async {
        guard let indexer = target.indexer else { return }
        await indexer.enqueueDelegateRebuild(identifiers)
    }

    private func enqueueDelegateRebuild(_ identifiers: [String]?) async {
        // System reindexing does not require an earlier UI update.
        let request = requested ?? Request(entries: entries, nodes: queryNodes ?? [],
                                            sourceIdentifier: store?.searchSourceIdentifier)
        if let identifiers {
            reindexIdentifiers.append(contentsOf: identifiers)
        } else {
            needsReset = true
            mayRestoreSavedState = false
            if isRunning { await stopIndexing() }
            pendingMayInitializeIndex = true
            pendingResetsIndex = true
        }
        await withCheckedContinuation { (continuation: CheckedContinuation<Void, Never>) in
            pending = request
            acknowledgements.append { continuation.resume() }
            startWorker()
        }
    }
}
