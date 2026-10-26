import Foundation
import CoreSpotlight
import CryptoKit
import PastoCore
import UniformTypeIdentifiers

/// Delegates matching to the same system query engine as the reference.
/// The store namespace and multi-board projection adapt the replica's JSON model.
@MainActor
final class ReplicaSearchIndex: NSObject, CSSearchableIndexDelegate {
    private struct Entry: Equatable {
        let id: UUID
        let title: String
        let text: String
        let modified: Date
        let app: String
        let type: String
        let device: String
        let pinboards: [String]

        init(_ item: ClipboardItem) {
            id = item.id
            let defaultTitle: String
            switch item.kind {
            case .image: defaultTitle = "Image"
            case .color: defaultTitle = "Color"
            case .files: defaultTitle = "File"
            case .link: defaultTitle = "Link"
            case .text, .richText: defaultTitle = "Text"
            case .unknown: defaultTitle = "Unknown"
            }
            title = item.originalTitle ?? defaultTitle
            text = String([item.plainText, item.recognizedText].compactMap { $0 }.joined(separator: "\n").prefix(5000))
            modified = item.updatedAt
            app = item.sourceName
            type = item.kind == .files ? "file" : item.kind == .richText ? "text" : item.kind.rawValue
            device = item.sourceDevice
            pinboards = item.pinboardIDs.map(\.uuidString).sorted()
        }
    }

    private struct Request: Equatable {
        let entries: [Entry]
        let nodes: [OriginalSearchQueryNode]
    }

    private let domain: String
    private let index: CSSearchableIndex
    private let appKey = CSCustomAttributeKey(keyName: "pasteApp", searchable: true, searchableByDefault: true, unique: false, multiValued: false)!
    private let typeKey = CSCustomAttributeKey(keyName: "pasteType", searchable: true, searchableByDefault: true, unique: false, multiValued: false)!
    private let deviceKey = CSCustomAttributeKey(keyName: "pasteDevice", searchable: true, searchableByDefault: true, unique: false, multiValued: false)!
    private let pinboardKey = CSCustomAttributeKey(keyName: "pastePinboard", searchable: true, searchableByDefault: true, unique: false, multiValued: true)!
    private let storeKey = CSCustomAttributeKey(keyName: "pasteReplicaStore", searchable: true, searchableByDefault: false, unique: false, multiValued: false)!
    private var sourceItems: [ClipboardItem] = []
    private var entries: [Entry] = []
    private var requested: Request?
    private var pending: Request?
    private var indexed: [UUID: Entry] = [:]
    private var needsReset = true
    private var worker: Task<Void, Never>?
    private var activeQuery: CSSearchQuery?
    private var acknowledgements: [() -> Void] = []
    private(set) var queryString = ""
    private(set) var identifiers: Set<UUID> = []
    private(set) var error: Error?
    var onUpdate: (() -> Void)?

    init(directoryURL: URL) {
        let hash = SHA256.hash(data: Data(directoryURL.standardizedFileURL.path.utf8))
        domain = "PasteReplica." + hash.map { String(format: "%02x", $0) }.joined()
        index = CSSearchableIndex(name: domain)
        super.init()
        index.indexDelegate = self
    }

    func update(items: [ClipboardItem], nodes: [OriginalSearchQueryNode]) {
        if sourceItems != items {
            sourceItems = items
            entries = items.map(Entry.init)
        }
        let request = Request(entries: entries, nodes: nodes)
        guard requested != request else { return }
        requested = request
        pending = request
        queryString = OriginalSearchQuery.f_1002f45b0(nodes)
        activeQuery?.cancel()
        identifiers = []
        error = nil
        startWorker()
        onUpdate?()
    }

    func retry() {
        guard let requested else { return }
        pending = requested
        error = nil
        startWorker()
        onUpdate?()
    }

    private func startWorker() {
        guard worker == nil else { return }
        worker = Task { [weak self] in
            guard let self else { return }
            await drain()
        }
    }

    private func searchableItem(_ entry: Entry) -> CSSearchableItem {
        let attributes = CSSearchableItemAttributeSet(contentType: .content)
        attributes.title = entry.title
        attributes.textContent = entry.text
        if ProcessInfo.processInfo.isOperatingSystemAtLeast(.init(majorVersion: 26, minorVersion: 4, patchVersion: 0)) {
            attributes.contentDescription = entry.text
        }
        attributes.contentModificationDate = entry.modified
        attributes.setValue(entry.app as NSString, forCustomKey: appKey)
        attributes.setValue(entry.type as NSString, forCustomKey: typeKey)
        attributes.setValue(entry.device as NSString, forCustomKey: deviceKey)
        attributes.setValue(entry.pinboards as NSArray, forCustomKey: pinboardKey)
        attributes.setValue(domain as NSString, forCustomKey: storeKey)
        let item = CSSearchableItem(uniqueIdentifier: domain + ":" + entry.id.uuidString,
                                    domainIdentifier: domain, attributeSet: attributes)
        item.expirationDate = .distantFuture
        return item
    }

    private func drain() async {
        while let request = pending {
            pending = nil
            var journalCompleted = false
            do {
                if needsReset {
                    needsReset = false
                    try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<Void, Error>) in
                        index.deleteSearchableItems(withDomainIdentifiers: [domain]) { error in
                            if let error { continuation.resume(throwing: error) }
                            else { continuation.resume() }
                        }
                    }
                    indexed = [:]
                }
                let current = Dictionary(uniqueKeysWithValues: request.entries.map { ($0.id, $0) })
                let deleted = Set(indexed.keys).subtracting(current.keys)
                if !deleted.isEmpty {
                    try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<Void, Error>) in
                        index.deleteSearchableItems(withIdentifiers: deleted.map { domain + ":" + $0.uuidString }) { error in
                            if let error { continuation.resume(throwing: error) }
                            else { continuation.resume() }
                        }
                    }
                }
                let changed = request.entries.filter { indexed[$0.id] != $0 }.map(searchableItem)
                if !changed.isEmpty {
                    try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<Void, Error>) in
                        index.indexSearchableItems(changed) { error in
                            if let error { continuation.resume(throwing: error) }
                            else { continuation.resume() }
                        }
                    }
                }
                indexed = current
                journalCompleted = true
                guard pending == nil else { continue }
                let predicate = queryString
                var found: Set<UUID> = []
                if !predicate.isEmpty {
                    let context = CSSearchQueryContext()
                    context.fetchAttributes = []
                    context.filterQueries = ["pasteReplicaStore == \"\(domain)\""]
                    let query = CSSearchQuery(queryString: predicate, queryContext: context)
                    activeQuery = query
                    for try await result in query.results {
                        let identifier = result.item.uniqueIdentifier
                        if identifier.hasPrefix(domain + ":"),
                           let id = UUID(uuidString: String(identifier.dropFirst(domain.count + 1))) { found.insert(id) }
                    }
                    activeQuery = nil
                }
                guard pending == nil, requested == request else { continue }
                identifiers = found
                error = nil
                onUpdate?()
            } catch {
                activeQuery = nil
                if pending == nil {
                    self.error = error
                    identifiers = []
                    onUpdate?()
                }
                // A failed journal must not be treated as an up-to-date index.
                if !journalCompleted { needsReset = true }
            }
        }
        worker = nil
        let callbacks = acknowledgements
        acknowledgements = []
        callbacks.forEach { $0() }
    }

    nonisolated func searchableIndex(_ searchableIndex: CSSearchableIndex,
                                    reindexAllSearchableItemsWithAcknowledgementHandler acknowledgementHandler: @escaping () -> Void) {
        rebuild(acknowledgementHandler)
    }

    nonisolated func searchableIndex(_ searchableIndex: CSSearchableIndex,
                                    reindexSearchableItemsWithIdentifiers identifiers: [String],
                                    acknowledgementHandler: @escaping () -> Void) {
        rebuild(acknowledgementHandler)
    }

    nonisolated private func rebuild(_ acknowledge: @escaping () -> Void) {
        Task { @MainActor [weak self] in
            guard let self else { acknowledge(); return }
            needsReset = true
            pending = requested
            activeQuery?.cancel()
            acknowledgements.append(acknowledge)
            startWorker()
        }
    }
}
