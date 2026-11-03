import CoreData
import Foundation
import SwiftUI

/// A group menu retains its target entity until the captured action is invoked.
@MainActor
public struct ClipboardPinboardTarget {
    public let id: UUID
    public var listTarget: ClipboardListTarget { ClipboardListTarget(object: nativeObject) }
    public var name: String { nativeObject.value(forKey: "name") as? String ?? "" }
    public var colorCode: UInt64? {
        OriginalPinboardAttributes.colorCode(from: nativeObject.value(forKey: "rawAttributes") as? Data)
    }
    let nativeObject: NSManagedObject

    init(id: UUID, object: NSManagedObject) {
        self.id = id
        nativeObject = object
    }
}

/// A tab retains its List itself; history and groups share the native ordered collection.
@MainActor
public struct ClipboardListTarget {
    let nativeObject: NSManagedObject
    public var objectID: NSManagedObjectID { nativeObject.objectID }
    public var isDeleted: Bool { nativeObject.isDeleted }
    public func hasSameObjectID(as other: ClipboardListTarget) -> Bool {
        nativeObject.objectID.isEqual(other.nativeObject.objectID)
    }
    public var identifier: String {
        String._unconditionallyBridgeFromObjectiveC(nativeObject.value(forKey: "identifier") as? NSString)
    }
    public var name: String {
        String._unconditionallyBridgeFromObjectiveC(nativeObject.value(forKey: "name") as? NSString)
    }
    public var colorCode: UInt64? {
        OriginalPinboardAttributes.colorCode(from: nativeObject.value(forKey: "rawAttributes") as? Data)
    }
    public var rawType: Int64 { (nativeObject.value(forKey: "rawType") as? NSNumber)?.int64Value ?? 0 }
    public var pinboardValue: Pinboard? {
        guard rawType == 2, let id = UUID(uuidString: identifier) else { return nil }
        let attributes = nativeObject.value(forKey: "rawAttributes") as? Data
        let color = OriginalPinboardAttributes.colorCode(from: attributes)
            .map { String(format: "#%06llX", $0) } ?? "#FF9500"
        let metadata = nativeObject.value(forKey: "metadata") as? NSManagedObject
        let index = (metadata?.value(forKey: "index") as? NSNumber)?.intValue ?? 0
        return Pinboard(id: id, name: name, colorHex: color, sortOrder: index, rawType: 2, rawAttributes: attributes)
    }

    init(object: NSManagedObject) { nativeObject = object }
}

/// Access on the supplied context queue. Existing Pasto IDs and legacy memberships stay compatible.
final class ClipboardListPersistence {
    private static let reorderDiagnostics = OriginalNamedDiagnostic.f_1000d4624(name: "NSManagedObjectContext")
    static let historyIdentifier = "sharedPasteboardHistory"
    private let context: NSManagedObjectContext
    var refreshHistoryAfterOperation = false
    private var nativeLists: [String: NSManagedObject] = [:]

    init(context: NSManagedObjectContext) { self.context = context }

    static func addEntities(to model: NSManagedObjectModel, item: NSEntityDescription) {
        func attribute(_ name: String, _ type: NSAttributeType, optional: Bool = false,
                       defaultValue: Any? = nil) -> NSAttributeDescription {
            let value = NSAttributeDescription()
            value.name = name; value.attributeType = type; value.isOptional = optional
            value.defaultValue = defaultValue
            return value
        }
        func entity(_ name: String) -> NSEntityDescription {
            let value = NSEntityDescription()
            value.name = name; value.managedObjectClassName = "NSManagedObject"
            return value
        }
        func relationship(_ name: String, destination: NSEntityDescription,
                          maxCount: Int, optional: Bool, rule: NSDeleteRule) -> NSRelationshipDescription {
            let value = NSRelationshipDescription()
            value.name = name; value.destinationEntity = destination
            value.minCount = 0; value.maxCount = maxCount; value.isOptional = optional
            value.deleteRule = rule
            return value
        }
        let list = entity("ListEntity")
        let metadata = entity("ListMetadataEntity")
        list.properties = [attribute("identifier", .stringAttributeType), attribute("name", .stringAttributeType),
            attribute("rawType", .integer64AttributeType, defaultValue: 0),
            attribute("rawAttributes", .binaryDataAttributeType, optional: true),
            attribute("createdAt", .dateAttributeType), attribute("updatedAt", .dateAttributeType, optional: true)]
        list.uniquenessConstraints = [["identifier"]]
        metadata.properties = [attribute("identifier", .stringAttributeType),
            attribute("index", .integer64AttributeType, defaultValue: 0),
            attribute("createdAt", .dateAttributeType), attribute("updatedAt", .dateAttributeType, optional: true)]
        let listMetadata = relationship("metadata", destination: metadata, maxCount: 1,
                                        optional: false, rule: .cascadeDeleteRule)
        let metadataList = relationship("list", destination: list, maxCount: 1,
                                        optional: true, rule: .denyDeleteRule)
        listMetadata.inverseRelationship = metadataList; metadataList.inverseRelationship = listMetadata
        let items = relationship("items", destination: item, maxCount: 0,
                                 optional: false, rule: .nullifyDeleteRule)
        let owner = relationship("list", destination: list, maxCount: 1,
                                 optional: true, rule: .nullifyDeleteRule)
        items.inverseRelationship = owner; owner.inverseRelationship = items
        list.properties += [listMetadata, items]
        metadata.properties += [metadataList]
        item.properties.append(owner)
        model.entities += [list, metadata]
    }

    // 0x10030e6bc: dictionary projection, native predicate/sort, and fetch-error propagation.
    func searchPinboardNames(matching query: String) throws -> [(identifier: String, name: String)] {
        let request = NSFetchRequest<NSDictionary>(entityName: "ListEntity")
        request.resultType = .dictionaryResultType
        request.propertiesToFetch = ["identifier", "name"]
        if query.isEmpty {
            request.predicate = NSPredicate(format: "rawType == %d", 2)
        } else {
            request.predicate = NSPredicate(format: "rawType == %d AND name MATCHES[cd] %@", 2,
                OriginalSearchSuggestions.f_1002f5100(query))
        }
        request.sortDescriptors = [NSSortDescriptor(key: "name", ascending: true)]
        return try context.fetch(request).compactMap { row in
            guard let identifier = row["identifier"] as? String, let name = row["name"] as? String else { return nil }
            return (identifier: identifier, name: name)
        }
    }

    // 36c094/329764: the menu's live group collection uses the List class defaults.
    func pinboardRequest() -> NSFetchRequest<PastoListEntity> {
        let request = PastoListEntity.listFetchRequest()
        request.predicate = NSPredicate(format: "rawType == %d", 2)
        return request
    }

    // 367f78 does not apply the menu's type2 predicate.
    // 07d740/07d78c: same native List lookup and name bridge, inside its context queue.
    func searchListNameResolver() -> (String) -> String? {
        { identifier in
            self.context.performAndWait {
                guard let list = self.tabList(identifier: identifier) else { return nil }
                return String._unconditionallyBridgeFromObjectiveC(list.value(forKey: "name") as? NSString)
            }
        }
    }

    func tabListRequest() -> NSFetchRequest<PastoListEntity> { PastoListEntity.listFetchRequest() }

    // 368080/32a5b0 fetch the matching native List collection and return its first object.
    func tabList(identifier: String) -> NSManagedObject? {
        let request = PastoListEntity.listFetchRequest()
        request.predicate = NSPredicate(format: "identifier == %@", identifier)
        return (try? context.fetch(request))?.first
    }

    // 0x100328bb4 → 0x100328bc8, specialized to the actual local ListEntity consumers.
    func firstList(predicate: NSPredicate?, sortDescriptors: [NSSortDescriptor]? = nil) throws -> NSManagedObject? {
        let request = NSFetchRequest<NSManagedObject>(entityName: "ListEntity")
        request.predicate = predicate
        request.sortDescriptors = sortDescriptors ?? [NSSortDescriptor(key: "metadata.index", ascending: true)]
        request.fetchLimit = 1
        request.fetchOffset = 0
        request.fetchBatchSize = 20
        return try context.fetch(request).first
    }

    func historyList() throws -> NSManagedObject? {
        try firstList(predicate: NSPredicate(format: "identifier == %@", Self.historyIdentifier))
    }

    func list(identifier: String) throws -> NSManagedObject? {
        try firstList(predicate: NSPredicate(format: "identifier == %@", identifier))
    }

    // 329088: history uses its timestamp; pinboard uses the Item's order, not the List's index.
    func itemRequest(for list: NSManagedObject) -> NSFetchRequest<PastoItemEntity> {
        let request = PastoItemEntity.defaultFetchRequest()
        switch (list.value(forKey: "rawType") as? NSNumber)?.int64Value ?? 0 {
        case 1:
            request.sortDescriptors = [NSSortDescriptor(key: "timestamp", ascending: false)]
            request.predicate = NSPredicate(format: "timestamp != nil")
        case 2:
            request.sortDescriptors = [NSSortDescriptor(key: "displayOrderInPinboard", ascending: true)]
            request.predicate = NSPredicate(format: "list == %@", list)
        default: break
        }
        return request
    }

    // 0x1003620f8: consume the supplied local entities without reducing them to IDs.
    func moveItems(_ items: [PastoItemEntity], to pinboard: NSManagedObject) -> [PastoItemEntity] {
        guard var destination = try? context.fetch(itemRequest(for: pinboard)) else { return [] }
        let moving = items.filter { item in
            guard let owner = item.value(forKey: "list") as? NSManagedObject,
                  (owner.value(forKey: "rawType") as? NSNumber)?.int64Value == 2 else { return true }
            return !owner.isEqual(pinboard)
        }
        for item in moving {
            item.setValue(pinboard, forKey: "list")
            destination.insert(item, at: 0)
        }
        for (index, item) in destination.enumerated() {
            if (item.value(forKey: "displayOrderInPinboard") as? NSNumber)?.int64Value != Int64(index) {
                item.setValue(Int64(index), forKey: "displayOrderInPinboard")
            }
        }
        return destination
    }

    // 0x100325130/329088: count managed history/group members; count errors mean empty.
    func menuState(identifier: String) -> (rawType: Int64?, isEmpty: Bool) {
        guard let list = try? list(identifier: identifier) else { return (nil, true) }
        return menuState(for: list)
    }

    func menuState(for list: NSManagedObject) -> (rawType: Int64?, isEmpty: Bool) {
        let rawType = (list.value(forKey: "rawType") as? NSNumber)?.int64Value ?? 0
        guard let context = list.managedObjectContext else { return (rawType, true) }
        let request = PastoItemEntity.defaultFetchRequest()
        switch rawType {
        case 1: request.predicate = NSPredicate(format: "timestamp != nil")
        case 2: request.predicate = NSPredicate(format: "list == %@", list)
        default: return (rawType, true)
        }
        let count = (try? context.count(for: request)) ?? 0
        return (rawType, count == 0)
    }

    func historyCapacity() throws -> Int? {
        guard let history = try historyList() else { return nil }
        return historyCapacity(of: history)
    }

    func historyCapacity(of history: NSManagedObject) -> Int? {
        return OriginalPinboardAttributes.clipboardCapacity(from: history.value(forKey: "rawAttributes") as? Data)
    }

    func refreshHistoryIfNeeded() throws {
        guard refreshHistoryAfterOperation else { return }
        guard let history = try historyList() else { return }
        context.refresh(history, mergeChanges: true)
    }

    private func set<T: Equatable>(_ value: T?, key: String, on object: NSManagedObject) {
        guard (object.value(forKey: key) as? T) != value else { return }
        object.setValue(value, forKey: key)
    }

    private func allLists() throws -> [String: NSManagedObject] {
        let request = NSFetchRequest<NSManagedObject>(entityName: "ListEntity")
        return try Dictionary(uniqueKeysWithValues: context.fetch(request).map { object in
            guard let identifier = object.value(forKey: "identifier") as? String else {
                throw CocoaError(.fileReadCorruptFile)
            }
            return (identifier, object)
        })
    }

    private func makeList(identifier: String, name: String, rawType: Int64,
                          attributes: Data?, index: Int64) throws -> NSManagedObject {
        let list = NSEntityDescription.insertNewObject(forEntityName: "ListEntity", into: context)
        let metadata = NSEntityDescription.insertNewObject(forEntityName: "ListMetadataEntity", into: context)
        try context.obtainPermanentIDs(for: [list, metadata])
        let now = Date()
        list.setValue(identifier, forKey: "identifier")
        list.setValue(name, forKey: "name")
        list.setValue(rawType, forKey: "rawType")
        list.setValue(attributes, forKey: "rawAttributes")
        list.setValue(now, forKey: "createdAt")
        metadata.setValue(identifier, forKey: "identifier")
        metadata.setValue(index, forKey: "index")
        metadata.setValue(now, forKey: "createdAt")
        list.setValue(metadata, forKey: "metadata")
        return list
    }

    func retainNativeList(_ list: NSManagedObject) {
        let identifier = String._unconditionallyBridgeFromObjectiveC(list.value(forKey: "identifier") as? NSString)
        nativeLists[identifier] = list
    }

    // 368a30: index changes belong to this context; a separate context touches each changed List's metadata.
    func moveList(_ target: NSManagedObject, toOffset offset: Int) -> [PastoListEntity] {
        let request = PastoListEntity.listFetchRequest()
        request.sortDescriptors = [NSSortDescriptor(key: "metadata.index", ascending: true)]
        var ordered: [PastoListEntity] = []
        context.performAndWait { ordered = (try? context.fetch(request)) ?? [] }
        guard let source = ordered.firstIndex(where: { $0.isEqual(target) }) else { return [] }
        ordered.move(fromOffsets: IndexSet(integer: source), toOffset: offset)
        let background = NSManagedObjectContext(concurrencyType: .privateQueueConcurrencyType)
        background.persistentStoreCoordinator = context.persistentStoreCoordinator
        background.mergePolicy = NSMergeByPropertyStoreTrumpMergePolicy
        for (index, object) in ordered.enumerated() {
            retainNativeList(object)
            let current = ((object.value(forKey: "metadata") as? NSManagedObject)?.value(forKey: "index") as? NSNumber)?.int64Value ?? 0
            if current != Int64(index) {
                (object.value(forKey: "metadata") as? NSManagedObject)?.setValue(Int64(index), forKey: "index")
                background.performAndWait {
                    let list = background.object(with: object.objectID)
                    list.willChangeValue(forKey: "metadata")
                    list.didChangeValue(forKey: "metadata")
                }
            }
        }
        let observer = NotificationCenter.default.addObserver(forName: .NSManagedObjectContextDidSave,
            object: background, queue: nil) { [weak self] notification in
                guard let context = self?.context else { return }
                context.performAndWait { [weak self] in
                    self?.context.mergeChanges(fromContextDidSave: notification)
                }
            }
        background.performAndWait {
            guard background.hasChanges else { return }
            do {
                try OriginalObjCExceptionBridge.f_1002ff9c8 { try background.save() }
            } catch {
                background.rollback()
                Self.reorderDiagnostics.f_1000d468c().f_1000d4e0c("Error saving managed object context: \(error)")
            }
        }
        NotificationCenter.default.removeObserver(observer)
        return ordered
    }

    // 368818/363004, local pinboard branch: fetch errors use an empty sequence, then delete the same List.
    func removePinboard(_ list: NSManagedObject) -> [PastoItemEntity] {
        let items: [PastoItemEntity]
        if let context = list.managedObjectContext {
            items = (try? context.fetch(itemRequest(for: list))) ?? []
        } else { items = [] }
        for item in items {
            if (list.value(forKey: "rawType") as? NSNumber)?.int64Value == 2,
               let owner = item.value(forKey: "list") as? NSManagedObject, owner.isEqual(list) {
                item.setValue(nil, forKey: "list")
            }
            if item.value(forKey: "timestamp") == nil, item.value(forKey: "list") == nil {
                item.managedObjectContext?.delete(item)
            }
        }
        list.managedObjectContext?.delete(list)
        return items
    }

    // 36c448: the callback edits the first read; compare against a fresh second read before setting.
    func updateName(on list: NSManagedObject, _ update: (inout String) -> Void) {
        var value = String._unconditionallyBridgeFromObjectiveC(list.value(forKey: "name") as? NSString)
        update(&value)
        let current = String._unconditionallyBridgeFromObjectiveC(list.value(forKey: "name") as? NSString)
        if current != value { list.setValue(value, forKey: "name") }
    }

    // 36c614: only a decoded pinboard case is editable; encode failure still writes nil attributes.
    func updateColor(on list: NSManagedObject, _ update: (inout UInt64) -> Void) {
        guard case let .pinboard(old)? = OriginalPinboardAttributes.decoded(
            from: list.value(forKey: "rawAttributes") as? Data) else { return }
        var value = old
        update(&value)
        guard old != value else { return }
        let attributes = try? OriginalPinboardAttributes.encoded(colorCode: value)
        list.setValue(attributes, forKey: "rawAttributes")
    }

    // 0x100368560: insert/name first, attempt permanent ID, then encode attributes and set type.
    func insertPinboard(identifier: String, name: String,
                        encodeAttributes: () throws -> Data?) throws -> (object: NSManagedObject, attributes: Data?) {
        let list = PastoListEntity(context: context)
        list.setValue(identifier, forKey: "identifier")
        list.setValue(name, forKey: "name")
        nativeLists[identifier] = list
        // ARM 3686b8...3686e8 releases a permanent-ID error and rejoins the encoding path.
        try? context.obtainPermanentIDs(for: [list])
        let attributes = try? encodeAttributes()
        list.setValue(attributes, forKey: "rawAttributes")
        list.setValue(Int64(2), forKey: "rawType")
        return (list, attributes)
    }

    @discardableResult
    func synchronize(pinboards: [Pinboard], preferences: AppPreferences, previous: StoreState?) throws -> NSManagedObject {
        var lists = try allLists()
        let history: NSManagedObject
        if let existing = lists[Self.historyIdentifier] {
            history = existing
            set(preferences.historyTitle, key: "name", on: history)
            // Missing/invalid attributes are meaningful; unrelated saves must not replace them.
            if previous?.preferences.historyRetentionDays != preferences.historyRetentionDays {
                set(try OriginalPinboardAttributes.encodedClipboard(capacity: preferences.historyRetentionDays),
                    key: "rawAttributes", on: history)
            }
        } else {
            history = try makeList(identifier: Self.historyIdentifier,
                name: preferences.historyTitle, rawType: 1,
                attributes: OriginalPinboardAttributes.encodedClipboard(capacity: preferences.historyRetentionDays), index: 0)
            lists[Self.historyIdentifier] = history
        }
        let retained = Set(pinboards.map { $0.id.uuidString })
        for old in previous?.pinboards ?? [] where !retained.contains(old.id.uuidString) {
            if let object = lists.removeValue(forKey: old.id.uuidString) { context.delete(object) }
        }
        for board in pinboards {
            let identifier = board.id.uuidString
            let list: NSManagedObject
            if let existing = lists[identifier] { list = existing }
            else {
                list = try makeList(identifier: identifier, name: board.name,
                    rawType: Int64(board.rawType ?? 2), attributes: board.rawAttributes, index: Int64(board.sortOrder))
                lists[identifier] = list
            }
            // Native operations already changed this exact List; do not replay fields from a value snapshot.
            if nativeLists[identifier] === list { continue }
            set(board.name, key: "name", on: list)
            set(Int64(board.rawType ?? 2), key: "rawType", on: list)
            set(board.rawAttributes, key: "rawAttributes", on: list)
            guard let metadata = list.value(forKey: "metadata") as? NSManagedObject else {
                throw CocoaError(.fileReadCorruptFile)
            }
            set(Int64(board.sortOrder), key: "index", on: metadata)
        }
        return history
    }

    // Saving has already run the List validator. Project native input objects without another fetch/save.
    func projectNativePinboards(_ pinboards: [Pinboard]) -> [Pinboard] {
        guard !nativeLists.isEmpty else { return pinboards }
        return pinboards.map { board in
            guard let list = nativeLists[board.id.uuidString],
                  let metadata = list.value(forKey: "metadata") as? NSManagedObject,
                  let index = metadata.value(forKey: "index") as? NSNumber else { return board }
            var value = board
            value.sortOrder = index.intValue
            return value
        }.sorted { $0.sortOrder == $1.sortOrder ? $0.id.uuidString < $1.id.uuidString : $0.sortOrder < $1.sortOrder }
    }

    func project(_ pinboards: [Pinboard]) throws -> [Pinboard] {
        let lists = try allLists()
        var values = pinboards.map { board in
            guard let list = lists[board.id.uuidString] else { return board }
            var value = board
            value.name = list.value(forKey: "name") as? String ?? board.name
            value.rawAttributes = list.value(forKey: "rawAttributes") as? Data
            // Nil from legacy JSON is normalized when building the graph; readers use its real type.
            let rawType = (list.value(forKey: "rawType") as? NSNumber)?.int64Value ?? 0
            // Do not truncate an unknown 64-bit type into the ordinary-group value 2.
            value.rawType = Int16(exactly: rawType) ?? 0
            if let metadata = list.value(forKey: "metadata") as? NSManagedObject,
               let index = metadata.value(forKey: "index") as? NSNumber { value.sortOrder = index.intValue }
            return value
        }
        // A native List does not require a separate compatibility Pinboard row to exist.
        var represented = Set(values.map(\.id))
        for list in lists.values {
            guard !list.isDeleted,
                  (list.value(forKey: "rawType") as? NSNumber)?.int64Value == 2,
                  let identifier = list.value(forKey: "identifier") as? String,
                  let id = UUID(uuidString: identifier), represented.insert(id).inserted else { continue }
            let attributes = list.value(forKey: "rawAttributes") as? Data
            let colorHex = OriginalPinboardAttributes.colorCode(from: attributes)
                .map { String(format: "#%06llX", $0) } ?? "#FF9500"
            let metadata = list.value(forKey: "metadata") as? NSManagedObject
            let index = (metadata?.value(forKey: "index") as? NSNumber)?.intValue ?? 0
            values.append(Pinboard(id: id, name: list.value(forKey: "name") as? String ?? "",
                colorHex: colorHex, sortOrder: index, rawType: 2, rawAttributes: attributes))
        }
        return values.sorted {
            $0.sortOrder == $1.sortOrder ? $0.id.uuidString < $1.id.uuidString : $0.sortOrder < $1.sortOrder
        }
    }
}
