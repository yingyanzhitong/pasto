import AppKit
import CoreData
import Combine
import Foundation
import os

private struct CapturedItemCompatibilityMetadata: Decodable {
    let title: String
    let hasExplicitTitle: Bool?
    let sourceIdentifier: String?
    let sourceDevice: String
    let pinboardIDs: Set<UUID>
}

/// Pasto's model adapter for the original performAndWait / hasChanges / save transaction.
/// Entity identities remain the existing UUIDs; this is not the original vendor's store schema.
@MainActor
final class ClipboardPersistence {
    private static let transactionDiagnostics = OriginalNamedDiagnostic.f_1000d4624(name: "DB")
    private enum StoreModelError: Error {
        case unknownSchema
    }

    private let context: NSManagedObjectContext
    private let databaseURL: URL
    private let snapshotReader: ClipboardSnapshotReader
    private var viewHistoryToken: NSPersistentHistoryToken?
    private var viewRevision: UUID?
    private let searchHistory: OriginalSearchHistory
    private let lists: ClipboardListPersistence
    private let sources: ClipboardSourcePersistence
    private let itemUpdatesSubject = PassthroughSubject<Set<UUID>, Never>()
    private var contextChangesObservation: AnyCancellable?
    private let contentUndoManager = OriginalDependency(\OriginalDependencyValues.pasteboardUndoManager)
    private var undoChangesObservation: AnyCancellable?

    init(directoryURL: URL) throws {
        databaseURL = directoryURL.appendingPathComponent("clipboard.sqlite")
        let model = Self.makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true)
        try Self.migrateLegacyStoreIfNeeded(at: databaseURL, destinationModel: model)
        let coordinator = NSPersistentStoreCoordinator(managedObjectModel: model)
        try coordinator.addPersistentStore(ofType: NSSQLiteStoreType, configurationName: nil, at: databaseURL,
            options: Self.storeOptions)
        // The original default local context is the container's viewContext.
        let managedContext = NSManagedObjectContext(concurrencyType: .mainQueueConcurrencyType)
        managedContext.persistentStoreCoordinator = coordinator
        managedContext.undoManager = nil
        managedContext.automaticallyMergesChangesFromParent = true
        managedContext.mergePolicy = NSMergeByPropertyStoreTrumpMergePolicy
        context = managedContext
        snapshotReader = ClipboardSnapshotReader(coordinator: coordinator)
        searchHistory = OriginalSearchHistory(reader: snapshotReader)
        lists = ClipboardListPersistence(context: managedContext)
        sources = ClipboardSourcePersistence(context: managedContext)
        try bootstrapListsIfNeeded()
        viewHistoryToken = coordinator.currentPersistentHistoryToken(fromStores: nil)
        viewRevision = try context.performAndWait { try root()?.value(forKey: "revision") as? UUID }
        for suffix in ["", "-wal", "-shm"] {
            let path = databaseURL.path + suffix
            if FileManager.default.fileExists(atPath: path) {
                try FileManager.default.setAttributes([.posixPermissions: 0o600], ofItemAtPath: path)
            }
        }
        contextChangesObservation = NotificationCenter.default
            .publisher(for: .NSManagedObjectContextObjectsDidChange, object: managedContext)
            .sink { [weak self] notification in
                MainActor.assumeIsolated {
                    self?.publishChangedItemIDs(from: notification)
                }
            }
    }

    var collectionItemUpdates: AnyPublisher<Set<UUID>, Never> {
        itemUpdatesSubject.eraseToAnyPublisher()
    }

    // 0x10035cc80: extensions skip the main-context manager and its two publishers.
    // Pasto's compatibility-root migration finishes before enabling user Undo.
    func configureUndoRegistration() {
        guard !Bundle.main.bundlePath.hasSuffix(".appex") else { return }
        context.undoManager = contentUndoManager.f_1000da768()
        undoChangesObservation = NotificationCenter.default.publisher(
            for: .NSUndoManagerDidUndoChange, object: contentUndoManager.f_1000da768())
            .merge(with: NotificationCenter.default.publisher(
                for: .NSUndoManagerDidRedoChange, object: contentUndoManager.f_1000da768()))
            .sink { [weak self] _ in
                MainActor.assumeIsolated {
                    guard let context = Self.undoContext(from: { self }) else { return }
                    OriginalContextUndo.f_10035ca9c(context) {
                        try Self.updateRevisionAfterUndo(in: context)
                    }
                }
            }
    }

    // 0x10035f32c -> 0x10035dd04 releases the weak owner before saving its context.
    @inline(never)
    private static func undoContext(from loadOwner: () -> ClipboardPersistence?) -> NSManagedObjectContext? {
        loadOwner()?.context
    }

    // State is Pasto's compatibility metadata, not an original undoable model entity.
    // Flush native edits while registration is enabled, then flush metadata while disabled.
    private static func withoutMetadataUndo(in context: NSManagedObjectContext,
                                             _ operation: () throws -> Void) rethrows {
        context.processPendingChanges()
        let manager = context.undoManager
        manager?.disableUndoRegistration()
        defer {
            context.processPendingChanges()
            manager?.enableUndoRegistration()
        }
        try operation()
    }

    private static func updateRevisionAfterUndo(in context: NSManagedObjectContext) throws {
        let request = NSFetchRequest<NSManagedObject>(entityName: "State")
        request.predicate = NSPredicate(format: "key == %@", "local")
        request.fetchLimit = 2
        let roots = try context.fetch(request)
        guard roots.count == 1 else { throw CocoaError(.fileReadCorruptFile) }
        withoutMetadataUndo(in: context) { roots[0].setValue(UUID(), forKey: "revision") }
    }

    private func publishChangedItemIDs(from notification: Notification) {
        let updated = notification.userInfo?[NSUpdatedObjectsKey] as? Set<NSManagedObject> ?? []
        let refreshed = notification.userInfo?[NSRefreshedObjectsKey] as? Set<NSManagedObject> ?? []
        let identifiers = Set(updated.union(refreshed).compactMap { object -> UUID? in
            guard object.entity.name == "Item",
                  let key = object.value(forKey: "key") as? String else { return nil }
            return UUID(uuidString: key)
        })
        guard !identifiers.isEmpty else { return }
        itemUpdatesSubject.send(identifiers)
    }

    private static let storeOptions: [AnyHashable: Any] = [
        NSSQLitePragmasOption: ["journal_mode": "WAL", "synchronous": "FULL"],
        NSPersistentHistoryTrackingKey: true,
        NSPersistentStoreRemoteChangeNotificationPostOptionKey: true,
        NSMigratePersistentStoresAutomaticallyOption: true,
        NSInferMappingModelAutomaticallyOption: true
    ]

    private static func makeModel(includeNativeIdentity: Bool,
                                  preserveItemKeyInHistory: Bool,
                                  includeLists: Bool = true,
                                  includeOptionalTimestamp: Bool = true,
                                  includeNativeItemData: Bool = true,
                                  includeNativeSources: Bool = true,
                                  includeTypedItem: Bool = true,
                                  includeItemOrder: Bool = true,
                                  includeNativeTitle: Bool = true,
                                  includeTypedLists: Bool = true,
                                  includeTypedSources: Bool = true,
                                  includeTypedItemData: Bool = true,
                                  includeNativeCreationDate: Bool = true) -> NSManagedObjectModel {
        let model = NSManagedObjectModel()
        func attribute(_ name: String, _ type: NSAttributeType, optional: Bool = false) -> NSAttributeDescription {
            let value = NSAttributeDescription()
            value.name = name; value.attributeType = type; value.isOptional = optional
            return value
        }
        func entity(_ name: String, _ attributes: [NSAttributeDescription]) -> NSEntityDescription {
            let value = NSEntityDescription()
            value.name = name; value.managedObjectClassName = "NSManagedObject"
            let key = attribute("key", .stringAttributeType)
            if name == "Item", preserveItemKeyInHistory {
                key.preservesValueInHistoryOnDeletion = true
            }
            if name == "Item", includeNativeIdentity {
                attributes.first(where: { $0.name == "nativeIdentifier" })?.preservesValueInHistoryOnDeletion = true
            }
            value.properties = [key] + attributes
            value.uniquenessConstraints = [["key"]]
            return value
        }
        func content() -> NSAttributeDescription {
            let value = attribute("content", .binaryDataAttributeType)
            value.allowsExternalBinaryDataStorage = true
            return value
        }
        var itemAttributes = [content(), attribute("timestamp", .dateAttributeType, optional: includeOptionalTimestamp)]
        if includeOptionalTimestamp {
            // Preserve Pasto's display date when the original history timestamp becomes nil.
            itemAttributes.append(attribute("localCreatedAt", .dateAttributeType, optional: true))
        }
        if includeNativeIdentity {
            itemAttributes.append(attribute("nativeIdentifier", .stringAttributeType, optional: true))
            itemAttributes.append(attribute("nativeChecksum", .stringAttributeType, optional: true))
        }
        if includeNativeCreationDate { itemAttributes.append(attribute("createdAt", .dateAttributeType)) }
        itemAttributes.append(contentsOf: [attribute("updatedAt", .dateAttributeType), attribute("inHistory", .booleanAttributeType)])
        model.entities = [
            entity("Item", itemAttributes),
            entity("Pinboard", [attribute("content", .binaryDataAttributeType)]),
            entity("Application", [attribute("content", .binaryDataAttributeType)]),
            entity("CloudDocument", [content()]), entity("CloudBaseline", [content()]),
            entity("State", [attribute("revision", .UUIDAttributeType), attribute("version", .integer64AttributeType),
                attribute("preferences", .binaryDataAttributeType),
                attribute("cloudMetadata", .binaryDataAttributeType, optional: true),
                attribute("cloudJournal", .binaryDataAttributeType, optional: true)])
        ]
        if includeTypedItem {
            model.entitiesByName["Item"]!.managedObjectClassName = NSStringFromClass(PastoItemEntity.self)
        }
        if includeItemOrder { ClipboardItemOrderPersistence.addField(to: model) }
        if includeNativeTitle { ClipboardItemTitlePersistence.addField(to: model) }
        if includeLists { ClipboardListPersistence.addEntities(to: model, item: model.entitiesByName["Item"]!) }
        if includeLists && includeTypedLists {
            model.entitiesByName["ListEntity"]!.managedObjectClassName = NSStringFromClass(PastoListEntity.self)
            model.entitiesByName["ListMetadataEntity"]!.managedObjectClassName = NSStringFromClass(PastoListMetadataEntity.self)
        }
        if includeNativeItemData { ClipboardItemDataPersistence.addEntity(to: model, item: model.entitiesByName["Item"]!) }
        if includeNativeItemData && includeTypedItemData {
            model.entitiesByName["ItemDataEntity"]!.managedObjectClassName = NSStringFromClass(PastoItemDataEntity.self)
        }
        if includeNativeSources { ClipboardSourcePersistence.addEntities(to: model, item: model.entitiesByName["Item"]!) }
        if includeNativeSources && includeTypedSources {
            model.entitiesByName["ApplicationEntity"]!.managedObjectClassName = NSStringFromClass(PastoApplicationEntity.self)
            model.entitiesByName["DeviceEntity"]!.managedObjectClassName = NSStringFromClass(PastoDeviceEntity.self)
        }
        return model
    }

    private static func migrateLegacyStoreIfNeeded(at storeURL: URL,
                                                    destinationModel: NSManagedObjectModel) throws {
        guard FileManager.default.fileExists(atPath: storeURL.path) else { return }
        let metadata = try NSPersistentStoreCoordinator.metadataForPersistentStore(
            type: .sqlite, at: storeURL, options: storeOptions)
        guard !destinationModel.isConfiguration(withName: nil, compatibleWithStoreMetadata: metadata) else { return }

        let legacyCandidates = [
            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, includeNativeCreationDate: false),
            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, includeTypedItemData: false, includeNativeCreationDate: false),
            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, includeTypedSources: false, includeTypedItemData: false, includeNativeCreationDate: false),
            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, includeTypedLists: false, includeTypedSources: false, includeTypedItemData: false, includeNativeCreationDate: false),
            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, includeNativeTitle: false, includeTypedLists: false, includeTypedSources: false, includeTypedItemData: false, includeNativeCreationDate: false),
            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, includeItemOrder: false, includeNativeTitle: false, includeTypedLists: false, includeTypedSources: false, includeTypedItemData: false, includeNativeCreationDate: false),
            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, includeTypedItem: false, includeItemOrder: false, includeNativeTitle: false, includeTypedLists: false, includeTypedSources: false, includeTypedItemData: false, includeNativeCreationDate: false),
            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, includeNativeSources: false, includeTypedItem: false, includeItemOrder: false, includeNativeTitle: false, includeTypedLists: false, includeTypedSources: false, includeTypedItemData: false, includeNativeCreationDate: false),
            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, includeNativeItemData: false, includeNativeSources: false, includeTypedItem: false, includeItemOrder: false, includeNativeTitle: false, includeTypedLists: false, includeTypedSources: false, includeTypedItemData: false, includeNativeCreationDate: false),
            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, includeLists: true, includeOptionalTimestamp: false, includeNativeItemData: false, includeNativeSources: false, includeTypedItem: false, includeItemOrder: false, includeNativeTitle: false, includeTypedLists: false, includeTypedSources: false, includeTypedItemData: false, includeNativeCreationDate: false),
            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, includeLists: false, includeOptionalTimestamp: false, includeNativeItemData: false, includeNativeSources: false, includeTypedItem: false, includeItemOrder: false, includeNativeTitle: false, includeTypedLists: false, includeTypedSources: false, includeTypedItemData: false, includeNativeCreationDate: false),
            makeModel(includeNativeIdentity: false, preserveItemKeyInHistory: true, includeLists: false, includeOptionalTimestamp: false, includeNativeItemData: false, includeNativeSources: false, includeTypedItem: false, includeItemOrder: false, includeNativeTitle: false, includeTypedLists: false, includeTypedSources: false, includeTypedItemData: false, includeNativeCreationDate: false),
            makeModel(includeNativeIdentity: false, preserveItemKeyInHistory: false, includeLists: false, includeOptionalTimestamp: false, includeNativeItemData: false, includeNativeSources: false, includeTypedItem: false, includeItemOrder: false, includeNativeTitle: false, includeTypedLists: false, includeTypedSources: false, includeTypedItemData: false, includeNativeCreationDate: false)
        ]
        // The older history-retention variants can share a version hash.
        let sourceModel = legacyCandidates.first {
            $0.isConfiguration(withName: nil, compatibleWithStoreMetadata: metadata)
        }
        guard let sourceModel else {
            throw StoreModelError.unknownSchema
        }
        let mapping = try NSMappingModel.inferredMappingModel(
            forSourceModel: sourceModel, destinationModel: destinationModel)
        let requiresItemBackfill = sourceModel.entitiesByName["ItemDataEntity"] == nil
            || sourceModel.entitiesByName["Item"]?.attributesByName["createdAt"] == nil
        if requiresItemBackfill {
            for entity in mapping.entityMappings where entity.destinationEntityName == "Item" {
                entity.entityMigrationPolicyClassName = NSStringFromClass(PastoItemDataMigrationPolicy.self)
            }
        }

        let temporaryDirectory = storeURL.deletingLastPathComponent()
            .appendingPathComponent(".pasto-store-migration-\(UUID().uuidString)", isDirectory: true)
        defer { try? FileManager.default.removeItem(at: temporaryDirectory) }
        try FileManager.default.createDirectory(at: temporaryDirectory, withIntermediateDirectories: false)
        let migratedURL = temporaryDirectory.appendingPathComponent("clipboard.sqlite")
        let manager = NSMigrationManager(sourceModel: sourceModel, destinationModel: destinationModel)
        // SQLite's fast migration skips policy callbacks needed for required item fields.
        if requiresItemBackfill { manager.usesStoreSpecificMigrationManager = false }
        try manager.migrateStore(from: storeURL, type: .sqlite, options: nil,
            mapping: mapping, to: migratedURL, type: .sqlite, options: storeOptions)

        let coordinator = NSPersistentStoreCoordinator(managedObjectModel: destinationModel)
        try coordinator.replacePersistentStore(at: storeURL, destinationOptions: storeOptions,
            withPersistentStoreFrom: migratedURL, sourceOptions: storeOptions, type: .sqlite)
    }

    // 0x10036e3c4: source identity is the first persistent store's identifier, not a save revision.
    var searchSourceIdentifier: String? {
        context.persistentStoreCoordinator?.persistentStores.first?.identifier
    }

    func observeSearchChanges(_ consume: @escaping ([OriginalSearchHistoryChange]) async throws -> Void) async {
        await searchHistory.observe(consume)
    }

    nonisolated static func item(_ object: NSManagedObject) throws -> ClipboardItem {
        var item = try Self.decode(ClipboardItem.self, object)
        ClipboardItemTitlePersistence.project(&item, from: object)
        let timestamp = object.value(forKey: "timestamp") as? Date
        guard let createdAt = timestamp ?? object.value(forKey: "localCreatedAt") as? Date,
              let updatedAt = object.value(forKey: "updatedAt") as? Date else {
            throw CocoaError(.fileReadCorruptFile)
        }
        item.createdAt = createdAt; item.updatedAt = updatedAt; item.isInHistory = timestamp != nil
        item.nativeIdentifier = object.value(forKey: "nativeIdentifier") as? String
        item.nativeChecksum = object.value(forKey: "nativeChecksum") as? String
        guard let data = object.value(forKey: "data") as? NSManagedObject,
              let raw = data.value(forKey: "rawPasteboardItems") as? Data else {
            throw CocoaError(.fileReadCorruptFile)
        }
        item.payloads = try ClipboardStore.projectNativePasteboardItems(raw, onto: item.payloads)
        item.rawPreview = object.value(forKey: "rawPreview") as? Data
        item.imagePreviewMetadata = OriginalImagePreviewMetadataCodec.decode(item.rawPreview)
        if let list = object.value(forKey: "list") as? NSManagedObject,
           (list.value(forKey: "rawType") as? NSNumber)?.int64Value == 2,
           let identifier = list.value(forKey: "identifier") as? String,
           let owner = UUID(uuidString: identifier) {
            item.pinboardOwnerID = owner
            item.pinboardIDs.insert(owner)
        } else { item.pinboardOwnerID = nil }
        try ClipboardItemOrderPersistence.project(&item, from: object)
        try ClipboardSourcePersistence.projectApplication(&item, from: object)
        return item
    }

    // Capture replaces content, preview, source application and history time; only retain metadata.
    nonisolated static func capturedItemValue(_ object: NSManagedObject, id: UUID,
                                             replacingContentWith replacement: ClipboardItem) throws -> ClipboardItem {
        let metadata: CapturedItemCompatibilityMetadata?
        if object.isInserted, object.value(forKey: "content") == nil {
            // A failed new capture may have native content before its compatibility value is saved.
            metadata = nil
        } else {
            metadata = try Self.decode(CapturedItemCompatibilityMetadata.self, object)
        }
        var item = replacement
        item.id = id
        if let metadata {
            item.title = metadata.title
            item.hasExplicitTitle = metadata.hasExplicitTitle
            item.sourceIdentifier = metadata.sourceIdentifier
            item.sourceDevice = metadata.sourceDevice
            item.pinboardIDs = metadata.pinboardIDs
        } else {
            item.title = ""
            item.hasExplicitTitle = false
            item.sourceIdentifier = nil
            item.sourceDevice = (object.value(forKey: "device") as? NSManagedObject)?.value(forKey: "name") as? String
                ?? replacement.sourceDevice
            item.pinboardIDs = []
        }
        item.pinboardOwnerID = nil
        item.nativeIdentifier = object.value(forKey: "nativeIdentifier") as? String
        ClipboardItemTitlePersistence.project(&item, from: object)
        if let list = object.value(forKey: "list") as? NSManagedObject,
           (list.value(forKey: "rawType") as? NSNumber)?.int64Value == 2,
           let identifier = list.value(forKey: "identifier") as? String,
           let owner = UUID(uuidString: identifier) {
            item.pinboardOwnerID = owner
            item.pinboardIDs.insert(owner)
        }
        try ClipboardItemOrderPersistence.project(&item, from: object)
        // Preserve valid local OCR annotations without making old payload decoding a capture gate.
        if replacement.kind == .image, let data = object.value(forKey: "content") as? Data,
           let dictionary = (try? PropertyListSerialization.propertyList(from: data, options: [], format: nil)) as? [String: Any],
           dictionary["kind"] as? String == ClipboardKind.image.rawValue,
           let payloads = dictionary["payloads"] as? [String: Data] {
            for (type, data) in payloads where ClipboardStore.analysisPayloadKeys.contains(type) && item.payloads[type] == nil {
                item.payloads[type] = data
            }
        }
        return item
    }

    func searchPinboardNames(matching query: String) throws -> [(identifier: String, name: String)] {
        try context.performAndWait { try lists.searchPinboardNames(matching: query) }
    }

    func searchApplicationNames(matching query: String) throws -> [String] {
        try context.performAndWait { try sources.applicationNames(matching: query) }
    }

    func searchDeviceNames(matching query: String) throws -> [String] {
        try context.performAndWait { try sources.deviceNames(matching: query) }
    }

    func makeSearchListNameResolver() -> (String) -> String? {
        lists.searchListNameResolver()
    }

    func searchApplicationImage(named name: String) -> NSImage? {
        context.performAndWait { sources.applicationImage(named: name) }
    }

    func searchDeviceType(named name: String) -> UInt8? {
        context.performAndWait { sources.deviceType(named: name) }
    }

    // 0x10036d140: fetch IDs only, newest history timestamp first, no request limit.
    func searchIndexIdentifiers(before timestamp: Date?) throws -> [String] {
        try snapshotReader.searchIndexIdentifiers(before: timestamp)
    }

    func searchIndexRecords(identifiers: [String]?) throws -> [ClipboardSearchRecord] {
        try snapshotReader.searchIndexRecords(identifiers: identifiers)
    }

    func searchItems(identifiers: [String]?) throws -> [ClipboardItem] {
        try snapshotReader.searchItems(identifiers: identifiers)
    }

    func makeListCollection(identifier: String) -> ClipboardSearchCollection? {
        context.performAndWait {
            guard let list = try? lists.list(identifier: identifier) else { return nil }
            return ClipboardSearchCollection(context: context, request: lists.itemRequest(for: list))
        }
    }

    func makeSearchCollection(identifiers: [String]) -> ClipboardSearchCollection? {
        guard !identifiers.isEmpty else { return nil }
        return ClipboardSearchCollection(context: context, identifiers: identifiers)
    }

    func searchNativeItems(identifiers: [String]?) throws -> [ClipboardItem] {
        try snapshotReader.searchNativeItems(identifiers: identifiers)
    }

    func localListMenuState(_ target: ClipboardListTarget) -> (rawType: Int64?, isEmpty: Bool) {
        context.performAndWait { lists.menuState(for: target.nativeObject) }
    }

    func localListMenuState(identifier: String) -> (rawType: Int64?, isEmpty: Bool) {
        context.performAndWait { lists.menuState(identifier: identifier) }
    }

    func tabListTarget(identifier: String) -> ClipboardListTarget? {
        context.performAndWait {
            lists.tabList(identifier: identifier).map { ClipboardListTarget(object: $0) }
        }
    }

    func makeTabListCollection() -> ClipboardPinboardCollection {
        context.performAndWait {
            ClipboardPinboardCollection(context: context, request: lists.tabListRequest())
        }
    }

    func makePinboardCollection() -> ClipboardPinboardCollection {
        context.performAndWait {
            ClipboardPinboardCollection(context: context, request: lists.pinboardRequest())
        }
    }

    func observeListAttributes(identifier: String) -> ClipboardListAttributesObservation? {
        context.performAndWait {
            guard let list = try? lists.list(identifier: identifier) else { return nil }
            return ClipboardListAttributesObservation(list: list)
        }
    }

    func observeItem(identifier: String) -> ClipboardItemObservation? {
        context.performAndWait {
            let request = PastoItemEntity.defaultFetchRequest()
            request.predicate = NSPredicate(format: "key == %@", identifier)
            request.fetchLimit = 1
            guard let object = (try? context.fetch(request))?.first else { return nil }
            return ClipboardItemObservation(object: object)
        }
    }

    func itemContentKind(identifier: String) -> OriginalPasteboardContentKind {
        context.performAndWait {
            let request = PastoItemEntity.defaultFetchRequest()
            request.predicate = NSPredicate(format: "key == %@", identifier)
            request.fetchLimit = 1
            guard let object = (try? context.fetch(request))?.first else { return .unknown }
            let raw = (object.value(forKey: "rawType") as? NSNumber)?.int64Value ?? 0
            guard let value = UInt8(exactly: raw) else { return .unknown }
            return OriginalPasteboardContentKind(rawValue: value) ?? .unknown
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

    /// Backfill only the new graph; legacy encoded content and memberships remain intact.
    private func bootstrapListsIfNeeded() throws {
        try perform {
            guard let root = try root() else { return }
            if try lists.historyList() == nil {
                let preferences = try Self.decode(AppPreferences.self, root, key: "preferences")
                let pinboards = try fetch("Pinboard").map { try Self.decode(Pinboard.self, $0) }
                try lists.synchronize(pinboards: pinboards, preferences: preferences, previous: nil)
                for object in try fetch("Item") {
                    let value = try Self.decode(ClipboardItem.self, object)
                    if let ownerID = value.pinboardOwnerID {
                        guard let owner = try lists.list(identifier: ownerID.uuidString) else {
                            throw CocoaError(.fileReadCorruptFile)
                        }
                        object.setValue(owner, forKey: "list")
                    }
                }
            }
            try bootstrapHistoryTimestamps()
            try bootstrapSourcesIfNeeded(root)
            try ClipboardItemOrderPersistence.bootstrap(in: context, root: root)
            try ClipboardItemTitlePersistence.bootstrap(in: context, root: root)
            if context.hasChanges {
                root.setValue(UUID(), forKey: "revision")
                try context.save()
            }
        }
    }

    private func bootstrapHistoryTimestamps() throws {
        let request = NSFetchRequest<NSManagedObject>(entityName: "Item")
        request.predicate = NSPredicate(format: "localCreatedAt == nil")
        for object in try context.fetch(request) {
            guard let timestamp = object.value(forKey: "timestamp") as? Date,
                  let inHistory = object.value(forKey: "inHistory") as? Bool else {
                throw CocoaError(.fileReadCorruptFile)
            }
            object.setValue(timestamp, forKey: "localCreatedAt")
            if !inHistory { object.setValue(nil, forKey: "timestamp") }
        }
    }

    private func bootstrapSourcesIfNeeded(_ root: NSManagedObject) throws {
        guard (root.value(forKey: ClipboardSourcePersistence.versionKey) as? NSNumber)?.intValue != 1 else { return }
        let applications = try fetch("Application").map { try Self.decode(SourceApplicationRecord.self, $0) }
        for application in applications { try sources.application(application) }
        for object in try fetch("Item") {
            let value = try Self.decode(ClipboardItem.self, object)
            try sources.apply(value, applications: applications, to: object)
        }
        root.setValue(1, forKey: ClipboardSourcePersistence.versionKey)
    }

    func revision() throws -> UUID? {
        let revision = try snapshotReader.revision()
        if revision != viewRevision {
            try mergeViewChanges()
            viewRevision = revision
        }
        return revision
    }

    // Preserve the shared view context while incorporating committed local-process changes.
    // The in-memory cursor is separate from the indexer's persisted history token.
    private func mergeViewChanges() throws {
        let transactions = try snapshotReader.transactions(after: viewHistoryToken)
        context.performAndWait {
            for transaction in transactions {
                let before = context.insertedObjects.count + context.updatedObjects.count + context.deletedObjects.count
                // 0x100396df4: incoming context merges must not become user Undo actions.
                context.undoManager?.disableUndoRegistration()
                context.mergeChanges(fromContextDidSave: transaction.objectIDNotification())
                context.undoManager?.enableUndoRegistration()
                let after = context.insertedObjects.count + context.updatedObjects.count + context.deletedObjects.count
                if before < after {
                    Self.transactionDiagnostics.f_1000d468c().f_1000d4db8(
                        "[SYNC:MERGE] viewContext dirty objects: \(before) → \(after) (inserted: \(context.insertedObjects.count), updated: \(context.updatedObjects.count), deleted: \(context.deletedObjects.count))")
                }
            }
        }
        if let token = transactions.last?.token { viewHistoryToken = token }
    }

    nonisolated static func decode<T: Decodable>(_ type: T.Type, _ object: NSManagedObject, key: String = "content") throws -> T {
        guard let data = object.value(forKey: key) as? Data else { throw CocoaError(.fileReadCorruptFile) }
        return try PropertyListDecoder().decode(type, from: data)
    }

    private func encode<T: Encodable>(_ value: T) throws -> Data {
        let encoder = PropertyListEncoder(); encoder.outputFormat = .binary
        return try encoder.encode(value)
    }

    func read() throws -> StoreState {
        try snapshotReader.read()
    }

    private struct Document: Equatable {
        let key: String
        let value: OriginalCloudDocument
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
        value.pinboardOrder = nil
        value.sourceApplicationSnapshot = nil
        value.hasSourceApplicationSnapshot = false
        return value
    }

    private func contentForComparison(_ item: ClipboardItem) -> ClipboardItem {
        var value = content(item)
        value.title = ""
        value.hasExplicitTitle = false
        return value
    }

    @MainActor
    final class ManagedRepository {
        private let context: NSManagedObjectContext
        let lists: ClipboardListPersistence
        let itemData: ClipboardItemDataPersistence
        let sources: ClipboardSourcePersistence
        private(set) var replacedItemDataIDs: Set<UUID> = []
        private(set) var sourcedItemIDs: Set<UUID> = []
        private(set) var assignedItemIDs: Set<UUID> = []
        private(set) var unassignedItemIDs: Set<UUID> = []
        private(set) var alreadyDeletedItemIDs: Set<UUID> = []

        init(context: NSManagedObjectContext) {
            self.context = context
            lists = ClipboardListPersistence(context: context)
            itemData = ClipboardItemDataPersistence(context: context)
            sources = ClipboardSourcePersistence(context: context)
        }

        private func fetchObjects(_ entity: String, keys: [String]) throws -> [NSManagedObject] {
            let request = NSFetchRequest<NSManagedObject>(entityName: entity)
            request.predicate = NSPredicate(format: "key IN %@", keys)
            return try context.fetch(request)
        }

        // 3214c8/328bc8: lookup by native checksum; fetch failure is an empty result.
        func capturedItem(checksum: String?) throws -> (id: UUID, object: NSManagedObject)? {
            guard let checksum else { return nil }
            let request = PastoItemEntity.defaultFetchRequest()
            request.predicate = NSPredicate(format: "nativeChecksum == %@", checksum)
            request.fetchLimit = 1
            request.fetchOffset = 0
            guard let object = (try? context.fetch(request))?.first else { return nil }
            guard let key = object.value(forKey: "key") as? String,
                  let id = UUID(uuidString: key) else { throw CocoaError(.fileReadCorruptFile) }
            return (id: id, object: object)
        }

        func prepareHistoryItems(_ ids: [UUID]) throws -> [(id: UUID, object: NSManagedObject)] {
            var objects = Dictionary(uniqueKeysWithValues: try fetchObjects("Item", keys: ids.map(\.uuidString)).map {
                ($0.value(forKey: "key") as! String, $0)
            })
            return try ids.map { id in
                if let object = objects[id.uuidString] { return (id: id, object: object) }
                // Preserve value-only, not-yet-saved items accepted by the existing store facade.
                let object = NSEntityDescription.insertNewObject(forEntityName: "Item", into: context)
                try context.obtainPermanentIDs(for: [object])
                object.setValue(id.uuidString, forKey: "key")
                objects[id.uuidString] = object
                return (id: id, object: object)
            }
        }

        // 03b634 → ItemsReading witness+20: resolve each String independently and retain duplicates/order.
        func droppedItem(identifier: String) -> PastoItemEntity? {
            let request = PastoItemEntity.defaultFetchRequest()
            request.predicate = NSPredicate(
                format: "nativeIdentifier == %@ OR (nativeIdentifier == nil AND key == %@)", identifier, identifier)
            request.fetchLimit = 1
            request.fetchOffset = 0
            return (try? context.fetch(request))?.first
        }

        // 364014/3614c0: local nil-share path; cloud clone/permission flows are outside this adapter.
        func dropItems(identifiers: [String], to list: NSManagedObject) throws -> [ClipboardItem] {
            let items = identifiers.compactMap { droppedItem(identifier: $0) }
            guard !items.isEmpty else { return [] }
            switch (list.value(forKey: "rawType") as? NSNumber)?.int64Value ?? 0 {
            case 2:
                return try assignItems(items, to: list)
            case 1:
                // 361ec0/364108 reverse the input before generating one Date per occurrence.
                for item in items.reversed() { item.setValue(Date(), forKey: "timestamp") }
                if let capacity = lists.historyCapacity(of: list), capacity > 0 {
                    let interval = -capacity * 24 * 60 * 60
                    let request = PastoItemEntity.defaultFetchRequest()
                    request.predicate = NSPredicate(format: "list == nil && timestamp < %@",
                        Date(timeIntervalSinceNow: Double(interval)) as NSDate)
                    let expired = (try? context.fetch(request)) ?? []
                    for item in expired { context.delete(item) }
                    // Compatibility bookkeeping follows native deletion, never filters its input.
                    for item in expired {
                        if let key = item.value(forKey: "key") as? String, let id = UUID(uuidString: key) {
                            alreadyDeletedItemIDs.insert(id)
                        }
                    }
                }
                // Original static predicate is identifier == sharedPasteboardHistory, then refresh(merge:true).
                if let history = try? lists.historyList() { context.refresh(history, mergeChanges: true) }
                return try items.map { try ClipboardPersistence.item($0) }
            default:
                return []
            }
        }

        func assignItems(_ items: [PastoItemEntity], to pinboard: NSManagedObject) throws -> [ClipboardItem] {
            let destination = lists.moveItems(items, to: pinboard)
            let values = try destination.map { object in
                var item = try ClipboardPersistence.item(object)
                if let owner = item.pinboardOwnerID { item.pinboardIDs = [owner] }
                else { item.pinboardIDs.removeAll() }
                return item
            }
            assignedItemIDs.formUnion(values.map(\.id))
            return values
        }

        func removePinboard(_ list: NSManagedObject) -> [PastoItemEntity] {
            let affected = lists.removePinboard(list)
            // Compatibility identifiers are read only after all native mutations, never as an input gate.
            for object in affected {
                guard let key = object.value(forKey: "key") as? String, let id = UUID(uuidString: key) else { continue }
                assignedItemIDs.insert(id)
                unassignedItemIDs.insert(id)
                if object.isDeleted { alreadyDeletedItemIDs.insert(id) }
            }
            return affected
        }

        // 363a3c/36299c: retain sequence order; a non-pinboard owner is a no-op.
        func unassignItems(_ targets: [(id: UUID, object: NSManagedObject)]) -> [(id: UUID, object: NSManagedObject)] {
            var affected: [(id: UUID, object: NSManagedObject)] = []
            for target in targets {
                let object = target.object
                guard let owner = object.value(forKey: "list") as? NSManagedObject,
                      (owner.value(forKey: "rawType") as? NSNumber)?.int64Value == 2 else { continue }
                if let currentOwner = object.value(forKey: "list") as? NSManagedObject,
                   currentOwner.isEqual(owner) {
                    object.setValue(nil, forKey: "list")
                }
                if object.value(forKey: "timestamp") == nil, object.value(forKey: "list") == nil {
                    // 3646ec uses the item's own context, including a nil-context no-op.
                    object.managedObjectContext?.delete(object)
                    if object.isDeleted { alreadyDeletedItemIDs.insert(target.id) }
                }
                // These sets suppress only compatibility writes, never the supplied sequence.
                assignedItemIDs.insert(target.id)
                unassignedItemIDs.insert(target.id)
                affected.append(target)
            }
            return affected
        }

        func restoreHistoryItems(_ targets: [(id: UUID, object: NSManagedObject)]) -> [(id: UUID, timestamp: Date)] {
            var updates: [(id: UUID, timestamp: Date)] = []
            for (id, object) in targets.reversed() {
                let timestamp = Date()
                object.setValue(timestamp, forKey: "timestamp")
                updates.append((id: id, timestamp: timestamp))
            }
            return updates
        }

        func replaceCapturedItemData(_ target: (id: UUID, object: NSManagedObject), items: [OriginalPasteboardItem],
                                     kind: OriginalPasteboardContentKind, checksum: String, useBinaryPlist: Bool,
                                     preview: () -> Data?) {
            itemData.replace(on: target.object, items: items, kind: kind, checksum: checksum,
                             useBinaryPlist: useBinaryPlist, preview: preview)
            replacedItemDataIDs.insert(target.id)
        }

        func initializeCapturedDevice(_ target: (id: UUID, object: NSManagedObject)) -> String {
            let device = sources.currentDevice()
            target.object.setValue(device, forKey: "device")
            return device.value(forKey: "name") as? String ?? ""
        }

        func applyCapturedSources(_ target: (id: UUID, object: NSManagedObject), item: ClipboardItem,
                                  applications: [SourceApplicationRecord], preserveDevice: Bool = false) throws {
            try sources.apply(item, applications: applications, to: target.object, preserveDevice: preserveDevice)
            sourcedItemIDs.insert(target.id)
        }

        func update<T: Equatable>(_ values: [T], previous: [T], entity: String,
                                         key: (T) -> String, deletingKeys: [String] = [],
                                         updatingKeys: [String] = [], alreadyDeletedKeys: Set<String> = [],
                                         apply: (T, T?, NSManagedObject) throws -> Void) throws {
            let before = Dictionary(uniqueKeysWithValues: previous.map { (key($0), $0) })
            let after = Dictionary(uniqueKeysWithValues: values.map { (key($0), $0) })
            let forced = Set(updatingKeys)
            let changed = values.filter { before[key($0)] != $0 || forced.contains(key($0)) }
            let removed = Set(before.keys).subtracting(after.keys)
            // 0x1003646ec consumes the supplied object array in order, including repeated entries.
            var orderedRemoved = deletingKeys.filter { removed.contains($0) }
            let scheduled = Set(orderedRemoved)
            orderedRemoved += previous.map(key).filter { removed.contains($0) && !scheduled.contains($0) }
            orderedRemoved.removeAll { alreadyDeletedKeys.contains($0) }
            let keys = changed.map(key) + orderedRemoved
            guard !keys.isEmpty else { return }
            let objects = Dictionary(uniqueKeysWithValues: try fetchObjects(entity, keys: keys).map {
                ($0.value(forKey: "key") as! String, $0)
            })
            for id in orderedRemoved {
                if let object = objects[id] { object.managedObjectContext?.delete(object) }
            }
            for value in changed {
                let id = key(value)
                let object: NSManagedObject
                if let existing = objects[id] {
                    object = existing
                } else {
                    object = NSEntityDescription.insertNewObject(forEntityName: entity, into: context)
                    // 0x100360d9c obtains the new Item's permanent object ID before writing its fields.
                    if entity == "Item" { try context.obtainPermanentIDs(for: [object]) }
                }
                if (object.value(forKey: "key") as? String) != id { object.setValue(id, forKey: "key") }
                try apply(value, before[id], object)
            }
        }
    }

    @MainActor
    final class Transaction {
        let context: NSManagedObjectContext
        let nativeHistoryRestoreTargets: [(id: UUID, object: NSManagedObject)]
        private var cachedRepository: ManagedRepository?

        init(context: NSManagedObjectContext, nativeHistoryRestoreTargets: [(id: UUID, object: NSManagedObject)] = []) {
            self.context = context
            self.nativeHistoryRestoreTargets = nativeHistoryRestoreTargets
        }

        // 0x100357cf0 -> 0x1003594e4: cache belongs to this transaction instance.
        var repository: ManagedRepository {
            if let cachedRepository { return cachedRepository }
            let repository = ManagedRepository(context: context)
            cachedRepository = repository
            return repository
        }
    }

    struct HistoryRestoreSelection {
        let transaction: Transaction
        let targets: [(id: UUID, object: NSManagedObject)]
    }

    func prepareHistoryRestore(targets: [(id: UUID, object: NSManagedObject)]) throws -> HistoryRestoreSelection {
        let transaction = Transaction(context: context, nativeHistoryRestoreTargets: targets)
        return try context.performAndWait {
            try OriginalObjCExceptionBridge.withResult {
                HistoryRestoreSelection(transaction: transaction, targets: targets)
            }
        }
    }

    func prepareHistoryRestore(inputs: [ClipboardRestoreItem]) throws -> HistoryRestoreSelection {
        let nativeTargets: [(id: UUID, object: NSManagedObject)] = inputs.compactMap { input in
            guard let object = input.nativeObject else { return nil }
            return (id: input.id, object: object)
        }
        if nativeTargets.count == inputs.count {
            return try prepareHistoryRestore(targets: nativeTargets)
        }
        let transaction = Transaction(context: context, nativeHistoryRestoreTargets: nativeTargets)
        return try context.performAndWait {
            try OriginalObjCExceptionBridge.withResult {
                let legacyIDs = inputs.filter { $0.nativeObject == nil }.map(\.id)
                let legacyTargets: [(id: UUID, object: NSManagedObject)]
                if legacyIDs.isEmpty { legacyTargets = [] }
                else { legacyTargets = try transaction.repository.prepareHistoryItems(legacyIDs) }
                var legacyIndex = 0
                let targets: [(id: UUID, object: NSManagedObject)] = inputs.map { input in
                    if let object = input.nativeObject { return (id: input.id, object: object) }
                    defer { legacyIndex += 1 }
                    return legacyTargets[legacyIndex]
                }
                return HistoryRestoreSelection(transaction: transaction, targets: targets)
            }
        }
    }

    func prepareHistoryRestore(ids: [UUID]) throws -> HistoryRestoreSelection {
        let transaction = Transaction(context: context)
        return try context.performAndWait {
            try OriginalObjCExceptionBridge.withResult {
                HistoryRestoreSelection(transaction: transaction,
                    targets: try transaction.repository.prepareHistoryItems(ids))
            }
        }
    }

    /// Caller holds the process-shared flock across read / merge / transaction / publish.
    /// Callback errors propagate directly; save errors diagnose and roll back this context.
    func commit(_ state: StoreState, previous: StoreState?, deletingItemIDs: [UUID] = []) throws {
        _ = try commit(previous: previous, deletingItemIDs: deletingItemIDs) { transaction in
            try transaction.repository.lists.synchronize(pinboards: state.pinboards,
                preferences: state.preferences, previous: previous)
            return (state: state, result: ())
        }
    }

    // 0x1002ff310 -> 0x100302b78: run the business operation inside performAndWait,
    // then apply its mutations and save only after the operation has returned successfully.
    func commit<T>(previous: StoreState?, deletingItemIDs: [UUID] = [], preparedTransaction: Transaction? = nil,
                   operation: (Transaction) throws -> (state: StoreState, result: T)) throws -> (state: StoreState, result: T) {
        let transaction = preparedTransaction ?? Transaction(context: context)
        return try withExtendedLifetime(transaction) {
            try context.performAndWait {
                var outcome = try operation(transaction)
                let state = outcome.state
                let replacements = transaction.repository.replacedItemDataIDs
                let sourced = transaction.repository.sourcedItemIDs
                let previousItems = previous?.items ?? []
                var restoredMetadataOnly: Set<UUID> = []
                var nativeRestoreWithoutValue: Set<UUID> = []
                if !transaction.nativeHistoryRestoreTargets.isEmpty {
                    let targets = Dictionary(transaction.nativeHistoryRestoreTargets.map { ($0.id, $0.object) },
                                             uniquingKeysWith: { _, last in last })
                    nativeRestoreWithoutValue = Set(targets.keys).subtracting(state.items.map(\.id))
                    let before = Dictionary(uniqueKeysWithValues: previousItems.map { ($0.id, $0) })
                    for item in state.items {
                        guard let object = targets[item.id], let old = before[item.id] else { continue }
                        var restored = old
                        restored.createdAt = item.createdAt
                        restored.updatedAt = item.updatedAt
                        restored.isInHistory = item.isInHistory
                        guard restored == item else { continue }
                        // The native restore already wrote timestamp. Keep Pasto's local metadata,
                        // without replaying unchanged value payload/preview/order onto this entity.
                        if old.createdAt != item.createdAt { object.setValue(item.createdAt, forKey: "localCreatedAt") }
                        if old.updatedAt != item.updatedAt { object.setValue(item.updatedAt, forKey: "updatedAt") }
                        if old.isInHistory != item.isInHistory { object.setValue(item.isInHistory, forKey: "inHistory") }
                        restoredMetadataOnly.insert(item.id)
                    }
                }
                let itemValues = restoredMetadataOnly.isEmpty ? state.items : state.items.filter { !restoredMetadataOnly.contains($0.id) }
                let itemPrevious = restoredMetadataOnly.isEmpty && nativeRestoreWithoutValue.isEmpty ? previousItems
                    : previousItems.filter { !restoredMetadataOnly.contains($0.id) && !nativeRestoreWithoutValue.contains($0.id) }
                try transaction.repository.update(itemValues, previous: itemPrevious, entity: "Item", key: { $0.id.uuidString },
                           deletingKeys: deletingItemIDs.map(\.uuidString),
                           updatingKeys: replacements.map(\.uuidString),
                           alreadyDeletedKeys: Set(transaction.repository.alreadyDeletedItemIDs.map(\.uuidString))) { item, old, object in
                    if transaction.repository.unassignedItemIDs.contains(item.id) {
                        if old.map(contentForComparison) != contentForComparison(item) {
                            object.setValue(try encode(content(item)), forKey: "content")
                        }
                        return
                    }
                    if !sourced.contains(item.id), object.isInserted
                        || old?.sourceApplicationBundleID != item.sourceApplicationBundleID
                        || old?.sourceDevice != item.sourceDevice {
                        try transaction.repository.sources.apply(item, applications: state.sourceApplications, to: object)
                    }
                    if !replacements.contains(item.id) && (old?.payloads != item.payloads || object.value(forKey: "data") == nil) {
                        let items = try ClipboardStore.originalPasteboardItems(from: item.payloads)
                        let kind = OriginalPasteboardClassification.f_10032362c(items)
                        if let checksum = OriginalPasteboardChecksums.f_1003216bc(items, kind: kind) {
                            transaction.repository.itemData.replace(on: object, items: items, kind: kind, checksum: checksum,
                                useBinaryPlist: state.preferences.useBinaryPlist) { item.rawPreview }
                        }
                    }
                    if (object.value(forKey: "rawPreview") as? Data) != item.rawPreview {
                        object.setValue(item.rawPreview, forKey: "rawPreview")
                    }
                    if object.isInserted || old?.originalTitle != item.originalTitle {
                        ClipboardItemTitlePersistence.update(item, on: object)
                    }
                    if old.map(contentForComparison) != contentForComparison(item) {
                        object.setValue(try encode(content(item)), forKey: "content")
                    }
                    let timestamp = item.isInHistory ? item.createdAt : nil
                    if old.flatMap({ $0.isInHistory ? $0.createdAt : nil }) != timestamp,
                       (object.value(forKey: "timestamp") as? Date) != timestamp {
                        object.setValue(timestamp, forKey: "timestamp")
                    }
                    if old?.createdAt != item.createdAt { object.setValue(item.createdAt, forKey: "localCreatedAt") }
                    if old?.updatedAt != item.updatedAt { object.setValue(item.updatedAt, forKey: "updatedAt") }
                    if old?.isInHistory != item.isInHistory { object.setValue(item.isInHistory, forKey: "inHistory") }
                    if old?.nativeIdentifier != item.nativeIdentifier,
                       (object.value(forKey: "nativeIdentifier") as? String) != item.nativeIdentifier {
                        object.setValue(item.nativeIdentifier, forKey: "nativeIdentifier")
                    }
                    if old?.nativeChecksum != item.nativeChecksum,
                       (object.value(forKey: "nativeChecksum") as? String) != item.nativeChecksum {
                        object.setValue(item.nativeChecksum, forKey: "nativeChecksum")
                    }
                    if !transaction.repository.assignedItemIDs.contains(item.id),
                       object.isInserted || old?.pinboardOwnerID != item.pinboardOwnerID {
                        if let ownerID = item.pinboardOwnerID {
                            guard let owner = try transaction.repository.lists.list(identifier: ownerID.uuidString) else {
                                throw CocoaError(.fileReadCorruptFile)
                            }
                            object.setValue(owner, forKey: "list")
                        } else { object.setValue(nil, forKey: "list") }
                    }
                    if !transaction.repository.assignedItemIDs.contains(item.id) {
                        ClipboardItemOrderPersistence.update(item, on: object)
                    }
                }
                try transaction.repository.update(state.pinboards, previous: previous?.pinboards ?? [], entity: "Pinboard", key: { $0.id.uuidString }) { value, _, object in
                    object.setValue(try encode(value), forKey: "content")
                }
                try transaction.repository.update(state.sourceApplications, previous: previous?.sourceApplications ?? [], entity: "Application", key: { $0.bundleIdentifier }) { value, _, object in
                    object.setValue(try encode(value), forKey: "content")
                    try transaction.repository.sources.application(value)
                }
                for (entity, values, old) in [
                    ("CloudDocument", state.cloudKitJournal?.documents ?? [:], previous?.cloudKitJournal?.documents ?? [:]),
                    ("CloudBaseline", state.cloudKitJournal?.localBaseline ?? [:], previous?.cloudKitJournal?.localBaseline ?? [:])
                ] {
                    try transaction.repository.update(values.map { Document(key: $0.key, value: $0.value) },
                        previous: old.map { Document(key: $0.key, value: $0.value) }, entity: entity, key: { $0.key }) { value, _, object in
                        object.setValue(try encode(value.value), forKey: "content")
                    }
                }
                try transaction.repository.lists.refreshHistoryIfNeeded()
                let root = try root() ?? NSEntityDescription.insertNewObject(forEntityName: "State", into: context)
                try Self.withoutMetadataUndo(in: context) {
                    if root.isInserted {
                        root.setValue("local", forKey: "key")
                        root.setValue(1, forKey: "version")
                        root.setValue(Int64(1), forKey: ClipboardItemOrderPersistence.versionKey)
                        root.setValue(Int64(1), forKey: ClipboardItemTitlePersistence.versionKey)
                    }
                    if (root.value(forKey: ClipboardSourcePersistence.versionKey) as? NSNumber)?.intValue != 1 {
                        root.setValue(1, forKey: ClipboardSourcePersistence.versionKey)
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
                }
                if context.hasChanges {
                    Self.withoutMetadataUndo(in: context) { root.setValue(UUID(), forKey: "revision") }
                    do {
                        try OriginalObjCExceptionBridge.f_1002ff9c8 { try context.save() }
                    } catch {
                        // 0x100302b78: snapshot before validation, then roll back and rethrow the save error.
                        let inserted = context.insertedObjects
                        let updated = context.updatedObjects
                        let deleted = context.deletedObjects
                        Self.transactionDiagnostics.f_1000d468c().f_1000d4e0c(
                            "Error saving managed object context (inserted: \(inserted.count), updated: \(updated.count), deleted: \(deleted.count)): \(error)")
                        for object in inserted {
                            do { try object.validateForInsert() }
                            catch {
                                Self.transactionDiagnostics.f_1000d468c().f_1000d4e0c(
                                    "  Invalid inserted: \(object.entity.name ?? "?") \(object.objectID) — \(error)")
                            }
                        }
                        for object in updated {
                            do { try object.validateForUpdate() }
                            catch {
                                Self.transactionDiagnostics.f_1000d468c().f_1000d4e0c(
                                    "  Invalid updated: \(object.entity.name ?? "?") \(object.objectID) — \(error)")
                            }
                        }
                        context.rollback()
                        throw error
                    }
                    // Store callers hold their existing cross-process lock through this save/cursor update.
                    viewHistoryToken = context.persistentStoreCoordinator?.currentPersistentHistoryToken(fromStores: nil)
                    viewRevision = root.value(forKey: "revision") as? UUID
                }
                outcome.state.pinboards = transaction.repository.lists.projectNativePinboards(outcome.state.pinboards)
                return outcome
            }
        }
    }
}
