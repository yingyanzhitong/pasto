import CoreData
import Foundation
import os

public enum OriginalSearchHistoryChange {
    case inserted([String])
    case updated([String])
    case deleted([String])
}

/// Local Core Data history adapter. The independent Item/key model is not the vendor schema.
@MainActor
final class OriginalSearchHistory {
    private let reader: ClipboardSnapshotReader
    private let logger = Logger(subsystem: "com.yingyanzhitong.paste-replica", category: "search-history")

    init(reader: ClipboardSnapshotReader) { self.reader = reader }

    // 0x1003703b0: nil token means history after distantPast; execution errors propagate.
    private func transactions(after token: NSPersistentHistoryToken?) throws -> [NSPersistentHistoryTransaction] {
        try reader.transactions(after: token)
    }

    // 0x10036fa2c: flatten transactions, filter Item, then reduce in original change order.
    private func changes(in transactions: [NSPersistentHistoryTransaction]) -> [OriginalSearchHistoryChange] {
        var inserted: Set<String> = []
        var updated: Set<String> = []
        var deleted: Set<String> = []
        for change in transactions.flatMap({ $0.changes ?? [] }) where change.changedObjectID.entity.name == "Item" {
            let identifier: String?
            switch change.changeType {
            case .insert, .update:
                // 0x10037063c: resolve on the private reader's queue, return only the identifier.
                identifier = reader.searchIdentifier(for: change.changedObjectID)
            case .delete:
                if let nativeIdentifier = change.tombstone?["nativeIdentifier"] as? String {
                    identifier = nativeIdentifier
                } else {
                    identifier = change.tombstone?["key"] as? String
                }
            @unknown default:
                continue
            }
            guard let identifier else { continue }
            switch change.changeType {
            case .insert:
                inserted.insert(identifier)
                updated.remove(identifier)
                deleted.remove(identifier)
            case .update:
                if !inserted.contains(identifier) { updated.insert(identifier) }
                deleted.remove(identifier)
            case .delete:
                deleted.insert(identifier)
                inserted.remove(identifier)
                updated.remove(identifier)
            @unknown default:
                break
            }
        }
        var result: [OriginalSearchHistoryChange] = []
        if !inserted.isEmpty { result.append(.inserted(Array(inserted))) }
        if !updated.isEmpty { result.append(.updated(Array(updated))) }
        if !deleted.isEmpty { result.append(.deleted(Array(deleted))) }
        return result
    }

    // 0x10036f7b8 / 0x10036f9e8: unbounded local notifications, scoped to this coordinator.
    private func notifications() -> AsyncStream<Void> {
        let coordinator = reader.coordinator
        return AsyncStream(bufferingPolicy: .unbounded) { continuation in
            let observer = NotificationCenter.default.addObserver(
                forName: .NSPersistentStoreRemoteChange, object: coordinator, queue: nil
            ) { _ in continuation.yield(()) }
            continuation.onTermination = { _ in NotificationCenter.default.removeObserver(observer) }
        }
    }

    func observe(_ consume: @escaping ([OriginalSearchHistoryChange]) async throws -> Void) async {
        // 0x1003707a8/371394: one app-wide Config slot, independent of store identity.
        let key = "indexHistoryTokenData"
        var token: NSPersistentHistoryToken?
        if let data = UserDefaults.standard.data(forKey: key) {
            token = try? NSKeyedUnarchiver.unarchivedObject(ofClass: NSPersistentHistoryToken.self, from: data)
        }
        func persistToken() {
            let data = token.flatMap { try? NSKeyedArchiver.archivedData(withRootObject: $0, requiringSecureCoding: true) }
            UserDefaults.standard.set(data, forKey: key)
        }
        // 0x10036e5cc normalizes a decoded token before the first catch-up read.
        persistToken()
        func process() async {
            do {
                let batch = try transactions(after: token)
                guard !batch.isEmpty else { return }
                try await consume(changes(in: batch))
                // 0x10036f040: advance only after the consumer succeeds, including an empty change list.
                if let next = batch.last?.token {
                    token = next
                    persistToken()
                }
            } catch is CancellationError {
                // Original cancellation is silent and keeps the previous token.
            } catch {
                logger.error("Local search history consumption failed: \(error.localizedDescription, privacy: .public)")
            }
        }
        // 0x10036e5cc -> 0x10036e854: initial catch-up precedes installing the notification iterator.
        await process()
        for await _ in notifications() {
            guard !Task.isCancelled else { break }
            await process()
        }
    }
}
