import CoreData
import Foundation
import os

/// Queue-confined snapshots. Resetting this private context never detaches view/writer objects.
final class ClipboardSnapshotReader {
    let context: NSManagedObjectContext
    let coordinator: NSPersistentStoreCoordinator
    private let lists: ClipboardListPersistence
    private let searchLogger = Logger(subsystem: "com.yingyanzhitong.paste-replica", category: "search-source")

    init(coordinator: NSPersistentStoreCoordinator) {
        let context = NSManagedObjectContext(concurrencyType: .privateQueueConcurrencyType)
        context.persistentStoreCoordinator = coordinator
        context.undoManager = nil
        self.context = context
        self.coordinator = coordinator
        lists = ClipboardListPersistence(context: context)
    }

    func searchIndexIdentifiers(before timestamp: Date?) throws -> [String] {
        try perform {
            let request = NSFetchRequest<NSDictionary>(entityName: "Item")
            request.resultType = .dictionaryResultType
            // The second column preserves Pasto's existing local-ID fallback for old records.
            request.propertiesToFetch = ["nativeIdentifier", "key"]
            request.sortDescriptors = [NSSortDescriptor(key: "timestamp", ascending: false)]
            if let timestamp { request.predicate = NSPredicate(format: "timestamp < %@", timestamp as NSDate) }
            return try context.fetch(request).compactMap { row in
                (row["nativeIdentifier"] as? String) ?? (row["key"] as? String)
            }
        }
    }

    func searchIndexRecords(identifiers: [String]?) throws -> [ClipboardSearchRecord] {
        try perform {
            context.reset()
            // 0x10036dc00 resets after projecting records, including the empty/error result.
            defer { context.reset() }
            if let identifiers, identifiers.isEmpty { return [] }
            let request = PastoItemEntity.defaultFetchRequest()
            if let identifiers {
                request.predicate = NSPredicate(
                    format: "nativeIdentifier IN %@ OR (nativeIdentifier == nil AND key IN %@)", identifiers, identifiers)
            }
            guard let coordinator = context.persistentStoreCoordinator else { throw CocoaError(.fileReadCorruptFile) }
            let objects: [NSManagedObject]
            do { objects = try context.fetch(request) }
            catch {
                guard identifiers != nil else { throw error }
                searchLogger.error("Search item fetch failed: \(error.localizedDescription, privacy: .public)")
                return []
            }
            return try objects.map { object in
                // Local cache identity/date columns remain required; content is deferred native data.
                guard let key = object.value(forKey: "key") as? String, let id = UUID(uuidString: key),
                      let contentVersion = object.value(forKey: "updatedAt") as? Date else {
                    throw CocoaError(.fileReadCorruptFile)
                }
                let rawType = (object.value(forKey: "rawType") as? NSNumber)?.int64Value ?? 0
                let kind = UInt8(exactly: rawType).flatMap { OriginalPasteboardContentKind(rawValue: $0) } ?? .unknown
                let reader = ClipboardSearchRecordReader(coordinator: coordinator, objectID: object.objectID, kind: kind)
                let application = object.value(forKey: "sourceApplication") as? NSManagedObject
                let device = object.value(forKey: "device") as? NSManagedObject
                let list = object.value(forKey: "list") as? NSManagedObject
                let pinboard = (list?.value(forKey: "rawType") as? NSNumber)?.int64Value == 2
                    ? list?.value(forKey: "identifier") as? String : nil
                return ClipboardSearchRecord.make(id: id, originalTitle: object.value(forKey: "title") as? String,
                    nativeIdentifier: object.value(forKey: "nativeIdentifier") as? String,
                    kind: kind, modified: object.value(forKey: "timestamp") as? Date,
                    app: application?.value(forKey: "name") as? String, device: device?.value(forKey: "name") as? String,
                    pinboard: pinboard, contentVersion: contentVersion,
                    content: kind == .image ? nil : { reader.content() },
                    imageData: kind == .image ? { reader.imageData() } : nil)
            }
        }
    }

    func searchItems(identifiers: [String]?) throws -> [ClipboardItem] {
        try perform {
            context.reset()
            defer { context.reset() }
            guard let identifiers else { return try fetch("Item").map(ClipboardPersistence.item) }
            guard !identifiers.isEmpty else { return [] }
            let request = PastoItemEntity.defaultFetchRequest()
            request.predicate = NSPredicate(format: "key IN %@", identifiers)
            return try context.fetch(request).map(ClipboardPersistence.item)
        }
    }

    func searchNativeItems(identifiers: [String]?) throws -> [ClipboardItem] {
        try perform {
            context.reset()
            defer { context.reset() }
            guard let identifiers else { return try fetch("Item").map(ClipboardPersistence.item) }
            guard !identifiers.isEmpty else { return [] }
            let request = PastoItemEntity.defaultFetchRequest()
            request.predicate = NSPredicate(
                format: "nativeIdentifier IN %@ OR (nativeIdentifier == nil AND key IN %@)", identifiers, identifiers)
            return try context.fetch(request).map(ClipboardPersistence.item)
        }
    }

    func revision() throws -> UUID? {
        try perform {
            context.reset()
            let request = NSFetchRequest<NSDictionary>(entityName: "State")
            request.resultType = .dictionaryResultType
            request.propertiesToFetch = ["version", "revision"]
            request.fetchLimit = 2
            let roots = try context.fetch(request)
            guard roots.count <= 1 else { throw CocoaError(.fileReadCorruptFile) }
            guard let root = roots.first else { return nil }
            guard (root["version"] as? NSNumber)?.intValue == 1,
                  let revision = root["revision"] as? UUID else {
                throw ClipboardStoreError.unsupportedArchiveVersion
            }
            return revision
        }
    }

    func read() throws -> StoreState {
        try perform {
            context.reset()
            defer { context.reset() }
            guard let root = try root() else { throw CocoaError(.fileReadCorruptFile) }
            let items = try fetch("Item").map(ClipboardPersistence.item)
            var preferences = try ClipboardPersistence.decode(AppPreferences.self, root, key: "preferences")
            // 0x10035ab5c: a missing/non-clipboard projection displays the default capacity.
            preferences.historyRetentionDays = try lists.historyCapacity() ?? 30
            var journal = try (root.value(forKey: "cloudJournal") as? Data).map {
                try PropertyListDecoder().decode(OriginalCloudKitJournal.self, from: $0)
            }
            if journal != nil {
                journal!.documents = try documents("CloudDocument")
                journal!.localBaseline = try documents("CloudBaseline")
            }
            return try StoreState(items: items,
                pinboards: lists.project(fetch("Pinboard").map { try ClipboardPersistence.decode(Pinboard.self, $0) }),
                preferences: preferences,
                sourceApplications: fetch("Application").map { try ClipboardPersistence.decode(SourceApplicationRecord.self, $0) },
                cloudSyncMetadata: (root.value(forKey: "cloudMetadata") as? Data).map {
                    try PropertyListDecoder().decode(ICloudSyncMetadata.self, from: $0)
                }, cloudKitJournal: journal)
        }
    }

    private func fetch(_ entity: String, keys: [String]? = nil) throws -> [NSManagedObject] {
        if entity == PastoItemEntity.entityName {
            let request = PastoItemEntity.defaultFetchRequest()
            if let keys { request.predicate = NSPredicate(format: "key IN %@", keys) }
            return try context.fetch(request)
        }
        let request = NSFetchRequest<NSManagedObject>(entityName: entity)
        if let keys { request.predicate = NSPredicate(format: "key IN %@", keys) }
        return try context.fetch(request)
    }

    private func root() throws -> NSManagedObject? {
        let values = try fetch("State")
        guard values.count <= 1 else { throw CocoaError(.fileReadCorruptFile) }
        return values.first
    }

    private func perform<T>(_ operation: () throws -> T) throws -> T {
        try context.performAndWait {
            do { return try OriginalObjCExceptionBridge.withResult(operation) }
            catch { context.rollback(); throw error }
        }
    }

    private func documents(_ entity: String) throws -> [String: OriginalCloudDocument] {
        try Dictionary(uniqueKeysWithValues: fetch(entity).map {
            ($0.value(forKey: "key") as! String, try ClipboardPersistence.decode(OriginalCloudDocument.self, $0))
        })
    }

    func transactions(after token: NSPersistentHistoryToken?) throws -> [NSPersistentHistoryTransaction] {
        try context.performAndWait {
            // Snapshot projections and history IDs share this queue; no stale registered Item may escape a batch.
            context.reset()
            let request: NSPersistentHistoryChangeRequest
            if let token { request = .fetchHistory(after: token) }
            else { request = .fetchHistory(after: Date.distantPast) }
            let result = try context.execute(request) as? NSPersistentHistoryResult
            return result?.result as? [NSPersistentHistoryTransaction] ?? []
        }
    }

    func searchIdentifier(for objectID: NSManagedObjectID) -> String? {
        context.performAndWait {
            guard let object = try? context.existingObject(with: objectID) else { return nil }
            if let nativeIdentifier = object.value(forKey: "nativeIdentifier") as? String {
                return nativeIdentifier
            }
            return object.value(forKey: "key") as? String
        }
    }
}
