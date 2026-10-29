import CoreData
import Foundation

/// Pasto's model adapter for the original performAndWait / hasChanges / save transaction.
/// Entity identities remain the existing UUIDs; this is not the original vendor's store schema.
@MainActor
final class ClipboardPersistence {
    private let context: NSManagedObjectContext
    private let databaseURL: URL

    init(directoryURL: URL) throws {
        databaseURL = directoryURL.appendingPathComponent("clipboard.sqlite")
        let model = NSManagedObjectModel()
        func attribute(_ name: String, _ type: NSAttributeType, optional: Bool = false) -> NSAttributeDescription {
            let value = NSAttributeDescription()
            value.name = name; value.attributeType = type; value.isOptional = optional
            return value
        }
        func entity(_ name: String, _ attributes: [NSAttributeDescription]) -> NSEntityDescription {
            let value = NSEntityDescription()
            value.name = name; value.managedObjectClassName = "NSManagedObject"
            value.properties = [attribute("key", .stringAttributeType)] + attributes
            value.uniquenessConstraints = [["key"]]
            return value
        }
        func content() -> NSAttributeDescription {
            let value = attribute("content", .binaryDataAttributeType)
            value.allowsExternalBinaryDataStorage = true
            return value
        }
        model.entities = [
            entity("Item", [content(), attribute("timestamp", .dateAttributeType),
                attribute("updatedAt", .dateAttributeType), attribute("inHistory", .booleanAttributeType)]),
            entity("Pinboard", [attribute("content", .binaryDataAttributeType)]),
            entity("Application", [attribute("content", .binaryDataAttributeType)]),
            entity("CloudDocument", [content()]), entity("CloudBaseline", [content()]),
            entity("State", [attribute("revision", .UUIDAttributeType), attribute("version", .integer64AttributeType),
                attribute("preferences", .binaryDataAttributeType),
                attribute("cloudMetadata", .binaryDataAttributeType, optional: true),
                attribute("cloudJournal", .binaryDataAttributeType, optional: true)])
        ]
        let coordinator = NSPersistentStoreCoordinator(managedObjectModel: model)
        try coordinator.addPersistentStore(ofType: NSSQLiteStoreType, configurationName: nil, at: databaseURL,
            options: [NSSQLitePragmasOption: ["journal_mode": "WAL", "synchronous": "FULL"]])
        // The original default local context is the container's viewContext.
        context = NSManagedObjectContext(concurrencyType: .mainQueueConcurrencyType)
        context.persistentStoreCoordinator = coordinator
        context.undoManager = nil
        for suffix in ["", "-wal", "-shm"] {
            let path = databaseURL.path + suffix
            if FileManager.default.fileExists(atPath: path) {
                try FileManager.default.setAttributes([.posixPermissions: 0o600], ofItemAtPath: path)
            }
        }
    }

    private func fetch(_ entity: String, keys: [String]? = nil) throws -> [NSManagedObject] {
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

    private func decode<T: Decodable>(_ type: T.Type, _ object: NSManagedObject, key: String = "content") throws -> T {
        guard let data = object.value(forKey: key) as? Data else { throw CocoaError(.fileReadCorruptFile) }
        return try PropertyListDecoder().decode(type, from: data)
    }

    private func encode<T: Encodable>(_ value: T) throws -> Data {
        let encoder = PropertyListEncoder(); encoder.outputFormat = .binary
        return try encoder.encode(value)
    }

    func read() throws -> StoreState {
        try perform {
            context.reset()
            guard let root = try root() else { throw CocoaError(.fileReadCorruptFile) }
            let items = try fetch("Item").map { object -> ClipboardItem in
                var item = try decode(ClipboardItem.self, object)
                guard let timestamp = object.value(forKey: "timestamp") as? Date,
                      let updatedAt = object.value(forKey: "updatedAt") as? Date,
                      let inHistory = object.value(forKey: "inHistory") as? Bool else {
                    throw CocoaError(.fileReadCorruptFile)
                }
                item.createdAt = timestamp; item.updatedAt = updatedAt; item.isInHistory = inHistory
                return item
            }
            var journal = try (root.value(forKey: "cloudJournal") as? Data).map {
                try PropertyListDecoder().decode(OriginalCloudKitJournal.self, from: $0)
            }
            if journal != nil {
                journal!.documents = try documents("CloudDocument")
                journal!.localBaseline = try documents("CloudBaseline")
            }
            return try StoreState(items: items,
                pinboards: fetch("Pinboard").map { try decode(Pinboard.self, $0) },
                preferences: decode(AppPreferences.self, root, key: "preferences"),
                sourceApplications: fetch("Application").map { try decode(SourceApplicationRecord.self, $0) },
                cloudSyncMetadata: (root.value(forKey: "cloudMetadata") as? Data).map {
                    try PropertyListDecoder().decode(ICloudSyncMetadata.self, from: $0)
                }, cloudKitJournal: journal)
        }
    }

    private struct Document: Equatable {
        let key: String
        let value: OriginalCloudDocument
    }

    private func documents(_ entity: String) throws -> [String: OriginalCloudDocument] {
        try Dictionary(uniqueKeysWithValues: fetch(entity).map {
            ($0.value(forKey: "key") as! String, try decode(OriginalCloudDocument.self, $0))
        })
    }

    private func journalHeader(_ journal: OriginalCloudKitJournal?) -> OriginalCloudKitJournal? {
        guard var value = journal else { return nil }
        value.documents = [:]; value.localBaseline = [:]
        return value
    }

    // Recency lives in managed attributes. Copying a large image must not encode its unchanged bytes.
    private func content(_ item: ClipboardItem) -> ClipboardItem {
        var value = item
        value.createdAt = Date(timeIntervalSinceReferenceDate: 0)
        value.updatedAt = value.createdAt; value.isInHistory = false
        return value
    }

    private func update<T: Equatable>(_ values: [T], previous: [T], entity: String,
                                     key: (T) -> String, apply: (T, T?, NSManagedObject) throws -> Void) throws {
        let before = Dictionary(uniqueKeysWithValues: previous.map { (key($0), $0) })
        let after = Dictionary(uniqueKeysWithValues: values.map { (key($0), $0) })
        let changed = values.filter { before[key($0)] != $0 }
        let removed = Set(before.keys).subtracting(after.keys)
        let keys = changed.map(key) + removed
        guard !keys.isEmpty else { return }
        let objects = Dictionary(uniqueKeysWithValues: try fetch(entity, keys: keys).map {
            ($0.value(forKey: "key") as! String, $0)
        })
        for id in removed { if let object = objects[id] { context.delete(object) } }
        for value in changed {
            let id = key(value)
            let object = objects[id] ?? NSEntityDescription.insertNewObject(forEntityName: entity, into: context)
            object.setValue(id, forKey: "key")
            try apply(value, before[id], object)
        }
    }

    /// Caller holds the process-shared flock across read / merge / transaction / publish.
    /// A thrown callback or save rolls back every entity and the sync checkpoint together.
    func commit(_ state: StoreState, previous: StoreState?) throws {
        try perform {
            context.reset()
            try update(state.items, previous: previous?.items ?? [], entity: "Item", key: { $0.id.uuidString }) { item, old, object in
                if old.map(content) != content(item) {
                    object.setValue(try encode(content(item)), forKey: "content")
                }
                if old?.createdAt != item.createdAt { object.setValue(item.createdAt, forKey: "timestamp") }
                if old?.updatedAt != item.updatedAt { object.setValue(item.updatedAt, forKey: "updatedAt") }
                if old?.isInHistory != item.isInHistory { object.setValue(item.isInHistory, forKey: "inHistory") }
            }
            try update(state.pinboards, previous: previous?.pinboards ?? [], entity: "Pinboard", key: { $0.id.uuidString }) { value, _, object in
                object.setValue(try encode(value), forKey: "content")
            }
            try update(state.sourceApplications, previous: previous?.sourceApplications ?? [], entity: "Application", key: { $0.bundleIdentifier }) { value, _, object in
                object.setValue(try encode(value), forKey: "content")
            }
            for (entity, values, old) in [
                ("CloudDocument", state.cloudKitJournal?.documents ?? [:], previous?.cloudKitJournal?.documents ?? [:]),
                ("CloudBaseline", state.cloudKitJournal?.localBaseline ?? [:], previous?.cloudKitJournal?.localBaseline ?? [:])
            ] {
                try update(values.map { Document(key: $0.key, value: $0.value) },
                    previous: old.map { Document(key: $0.key, value: $0.value) }, entity: entity, key: { $0.key }) { value, _, object in
                    object.setValue(try encode(value.value), forKey: "content")
                }
            }
            let root = try root() ?? NSEntityDescription.insertNewObject(forEntityName: "State", into: context)
            if root.isInserted {
                root.setValue("local", forKey: "key")
                root.setValue(1, forKey: "version")
            }
            if previous?.preferences != state.preferences {
                root.setValue(try encode(state.preferences), forKey: "preferences")
            }
            if previous?.cloudSyncMetadata != state.cloudSyncMetadata {
                root.setValue(try state.cloudSyncMetadata.map(encode), forKey: "cloudMetadata")
            }
            if journalHeader(previous?.cloudKitJournal) != journalHeader(state.cloudKitJournal) {
                root.setValue(try journalHeader(state.cloudKitJournal).map(encode), forKey: "cloudJournal")
            }
            if context.hasChanges {
                root.setValue(UUID(), forKey: "revision")
                try context.save()
            }

        }
    }
}
