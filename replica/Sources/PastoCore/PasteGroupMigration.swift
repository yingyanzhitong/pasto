import AppKit
import CoreData
import CryptoKit
import Foundation

/// Reads Paste's store through its original model, including WAL and external binary data.
/// This coordinator is read-only and never creates a CloudKit container or migrates the source.
public enum PasteGroupMigration {
    public struct Snapshot: Sendable {
        public var pinboards: [Pinboard]
        public var items: [ClipboardItem]
        public var sourceApplications: [SourceApplicationRecord]
        public var unavailableItemCount: Int
    }

    public struct Result: Sendable {
        public var addedGroups: Int
        public var addedItems: Int
        public var existingGroups: Int
        public var existingItems: Int
        public var unavailableItems: Int
    }

    public enum MigrationError: LocalizedError {
        case originalAppNotFound, incompatibleStore, invalidIdentifier

        public var errorDescription: String? {
            switch self {
            case .originalAppNotFound:
                return "未找到 Paste 的数据模型。请保留已安装的 Paste 后重试。"
            case .incompatibleStore:
                return "无法读取这个版本的 Paste 数据库。请使用与数据库对应的 Paste 版本后重试。"
            case .invalidIdentifier:
                return "Paste 数据中的分组或项目标识无效，未写入任何迁移数据。"
            }
        }
    }

    public static var defaultDatabaseURL: URL? {
        let library = FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Library")
        let paths = [
            "Containers/com.wiheads.paste/Data/Library/Application Support/Paste/db.sqlite",
            "Application Support/Paste/db.sqlite",
            "Group Containers/4788TTJ39Y.com.wiheads.paste-group/Library/Application Support/Paste/db.sqlite",
            "Group Containers/group.com.wiheads.paste/Library/Application Support/Paste/db.sqlite"
        ]
        return paths.map { library.appendingPathComponent($0) }
            .first { FileManager.default.fileExists(atPath: $0.path) }
    }

    private static func originalModel(metadata: [String: Any]) throws -> NSManagedObjectModel {
        let applications = [URL(fileURLWithPath: "/Applications"),
                            FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Applications")]
        for applicationsURL in applications {
            let url = applicationsURL.appendingPathComponent(
                "Paste.app/Contents/Resources/PastePackages_PasteCore.bundle")
            if let bundle = Bundle(url: url),
               let model = NSManagedObjectModel.mergedModel(from: [bundle], forStoreMetadata: metadata) {
                return model
            }
        }
        if applications.contains(where: {
            FileManager.default.fileExists(atPath: $0.appendingPathComponent("Paste.app").path)
        }) { throw MigrationError.incompatibleStore }
        throw MigrationError.originalAppNotFound
    }

    public static func read(from databaseURL: URL, model suppliedModel: NSManagedObjectModel? = nil) throws -> Snapshot {
        let options: [AnyHashable: Any] = [
            NSReadOnlyPersistentStoreOption: true,
            NSMigratePersistentStoresAutomaticallyOption: false,
            NSInferMappingModelAutomaticallyOption: false
        ]
        let metadata = try NSPersistentStoreCoordinator.metadataForPersistentStore(
            ofType: NSSQLiteStoreType, at: databaseURL, options: options)
        let original = try suppliedModel ?? originalModel(metadata: metadata)
        guard original.isConfiguration(withName: nil, compatibleWithStoreMetadata: metadata),
              let model = original.copy() as? NSManagedObjectModel else { throw MigrationError.incompatibleStore }
        // Use generic objects: no original app classes or their side effects are loaded.
        for entity in model.entities { entity.managedObjectClassName = NSStringFromClass(NSManagedObject.self) }
        let required: [String: Set<String>] = [
            "ListEntity": ["identifier", "name", "rawType", "rawAttributes", "metadata"],
            "ItemEntity": ["identifier", "title", "createdAt", "updatedAt", "timestamp", "list",
                           "data", "sourceApplication", "device", "rawPreview", "displayOrderInPinboard"],
            "ItemDataEntity": ["rawPasteboardItems"],
            "ListMetadataEntity": ["index"],
            "ApplicationEntity": ["bundleIdentifier", "name", "rawIcon", "rawColor"],
            "DeviceEntity": ["name"]
        ]
        guard required.allSatisfy({ name, properties in
            guard let entity = model.entitiesByName[name] else { return false }
            return properties.isSubset(of: Set(entity.propertiesByName.keys))
        }) else { throw MigrationError.incompatibleStore }
        let coordinator = NSPersistentStoreCoordinator(managedObjectModel: model)
        let store = try coordinator.addPersistentStore(ofType: NSSQLiteStoreType, configurationName: nil,
                                                       at: databaseURL, options: options)
        defer { try? coordinator.remove(store) }
        let context = NSManagedObjectContext(concurrencyType: .privateQueueConcurrencyType)
        context.persistentStoreCoordinator = coordinator
        return try context.performAndWait {
            defer { context.reset() }
            try context.setQueryGenerationFrom(.current)
            return try OriginalObjCExceptionBridge.withResult { try snapshot(in: context) }
        }
    }

    private static func identifier(_ object: NSManagedObject, kind: String) throws -> UUID {
        let value = object.value(forKey: "identifier")
        let source = (value as? UUID)?.uuidString ?? (value as? String)
        guard let source, !source.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            throw MigrationError.invalidIdentifier
        }
        // Stable import namespace avoids colliding with, or overwriting, existing Pasto content.
        let digest = SHA256.hash(data: Data("Pasto/PasteMigration/\(kind)/\(source)".utf8))
        var bytes = Array(digest.prefix(16))
        bytes[6] = (bytes[6] & 0x0f) | 0x50
        bytes[8] = (bytes[8] & 0x3f) | 0x80
        return bytes.withUnsafeBufferPointer { NSUUID(uuidBytes: $0.baseAddress!) as UUID }
    }

    private static func snapshot(in context: NSManagedObjectContext) throws -> Snapshot {
        let request = NSFetchRequest<NSManagedObject>(entityName: "ListEntity")
        request.predicate = NSPredicate(format: "rawType == 2")
        request.sortDescriptors = [NSSortDescriptor(key: "metadata.index", ascending: true),
                                   NSSortDescriptor(key: "identifier", ascending: true)]
        let lists = try context.fetch(request)
        var result = Snapshot(pinboards: [], items: [], sourceApplications: [], unavailableItemCount: 0)
        var applications: [String: SourceApplicationRecord] = [:]
        for (index, list) in lists.enumerated() {
            let boardID = try identifier(list, kind: "group")
            let attributes = list.value(forKey: "rawAttributes") as? Data
            let color = OriginalPinboardAttributes.colorCode(from: attributes) ?? 0xf0554d
            result.pinboards.append(Pinboard(id: boardID, name: list.value(forKey: "name") as? String ?? "",
                colorHex: String(format: "#%06llX", color & 0xffffff), sortOrder: index,
                rawType: 2, rawAttributes: attributes))
            let items = NSFetchRequest<NSManagedObject>(entityName: "ItemEntity")
            items.predicate = NSPredicate(format: "list == %@", list)
            items.sortDescriptors = [NSSortDescriptor(key: "displayOrderInPinboard", ascending: true),
                                      NSSortDescriptor(key: "identifier", ascending: true)]
            for object in try context.fetch(items) {
                let id = try identifier(object, kind: "item")
                guard let dataObject = object.value(forKey: "data") as? NSManagedObject,
                      let raw = dataObject.value(forKey: "rawPasteboardItems") as? Data,
                      let representations = OriginalPasteboardDataCodec.decodeIfValid(raw),
                      !representations.isEmpty else {
                    result.unavailableItemCount += 1
                    continue
                }
                var payloads: [String: Data] = [:]
                if let first = representations.first {
                    for type in first.f_10037da6c() { payloads[type] = first.f_10037d810(forType: type) }
                }
                payloads[originalItemDataPayloadKey] = raw
                let types = Set(representations.flatMap { $0.f_10037da6c() })
                let kind: ClipboardKind
                switch OriginalPasteboardClassification.f_10032362c(representations) {
                case .unknown: kind = .unknown
                case .image: kind = .image
                case .color: kind = .color
                case .files: kind = .files
                case .link: kind = .link
                case .text: kind = types.isDisjoint(with: ["public.rtf", "com.apple.flat-rtfd", "public.html"]) ? .text : .richText
                }
                let filePaths = kind == .files ? representations.compactMap { $0.f_10037cc6c()?.path } : []
                let text = filePaths.isEmpty
                    ? representations.lazy.compactMap { $0.f_10037c9a8() ?? $0.f_10037d33c()?.string }.first
                    : filePaths.joined(separator: "\n")
                let application = object.value(forKey: "sourceApplication") as? NSManagedObject
                let bundleID = application?.value(forKey: "bundleIdentifier") as? String
                let sourceName = application?.value(forKey: "name") as? String ?? ""
                if let bundleID {
                    let rawColor = (application?.value(forKey: "rawColor") as? NSNumber)?.uint64Value
                    applications[bundleID] = SourceApplicationRecord(bundleIdentifier: bundleID, name: sourceName,
                        rawIcon: application?.value(forKey: "rawIcon") as? Data,
                        rawColor: rawColor.flatMap { $0 < (UInt64(1) << 63) ? $0 : nil })
                }
                let device = object.value(forKey: "device") as? NSManagedObject
                let title = object.value(forKey: "title") as? String
                let created = object.value(forKey: "createdAt") as? Date ?? Date(timeIntervalSinceReferenceDate: 0)
                result.items.append(ClipboardItem(id: id, createdAt: created,
                    updatedAt: object.value(forKey: "updatedAt") as? Date ?? created,
                    title: title ?? "", kind: kind, plainText: text, sourceName: sourceName, sourceBundleID: bundleID,
                    payloads: payloads, pinboardIDs: [boardID],
                    sourceDevice: device?.value(forKey: "name") as? String ?? "此Mac", isInHistory: false,
                    rawPreview: object.value(forKey: "rawPreview") as? Data, hasExplicitTitle: title != nil,
                    pinboardOrder: (object.value(forKey: "displayOrderInPinboard") as? NSNumber)?.int64Value,
                    sourceApplicationBundleID: bundleID, pinboardOwnerID: boardID))
            }
        }
        result.sourceApplications = applications.values.sorted { $0.bundleIdentifier < $1.bundleIdentifier }
        return result
    }
}
