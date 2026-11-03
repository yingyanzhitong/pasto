import CoreData
import Foundation
import ObjectiveC

// 31b494: the local named wrapper is owned from object construction, including fetched faults.
// ItemData has no Syncable date fields and directly inherits NSManagedObject.
@objc(PastoItemDataEntity)
final class PastoItemDataEntity: NSManagedObject {
    let diagnostics = OriginalNamedDiagnostic.f_1000d4624(name: "ItemDataEntity")
}

/// Called on the owning managed context's queue, including during store migration.
final class ClipboardItemDataPersistence {
    private let context: NSManagedObjectContext

    init(context: NSManagedObjectContext) { self.context = context }

    static func addEntity(to model: NSManagedObjectModel, item: NSEntityDescription) {
        let data = NSEntityDescription()
        data.name = "ItemDataEntity"; data.managedObjectClassName = "NSManagedObject"
        let raw = NSAttributeDescription()
        raw.name = "rawPasteboardItems"; raw.attributeType = .binaryDataAttributeType
        raw.isOptional = false; raw.allowsExternalBinaryDataStorage = true
        let owner = NSRelationshipDescription()
        owner.name = "item"; owner.destinationEntity = item
        owner.minCount = 0; owner.maxCount = 1; owner.isOptional = true; owner.deleteRule = .denyDeleteRule
        let content = NSRelationshipDescription()
        content.name = "data"; content.destinationEntity = data
        content.minCount = 0; content.maxCount = 1; content.isOptional = false; content.deleteRule = .cascadeDeleteRule
        content.inverseRelationship = owner; owner.inverseRelationship = content
        data.properties = [raw, owner]
        let kind = NSAttributeDescription()
        kind.name = "rawType"; kind.attributeType = .integer64AttributeType; kind.defaultValue = 0
        let preview = NSAttributeDescription()
        preview.name = "rawPreview"; preview.attributeType = .binaryDataAttributeType; preview.isOptional = true
        item.properties += [kind, preview, content]
        model.entities.append(data)
    }

    @MainActor private static var diagnosticsKey: UInt8 = 0

    // Current models own the wrapper on the actual entity; older plain objects keep their local adapter.
    @MainActor private static func diagnostics(for data: NSManagedObject) -> OriginalNamedDiagnostic {
        if let data = data as? PastoItemDataEntity { return data.diagnostics }
        if let existing = objc_getAssociatedObject(data, &diagnosticsKey) as? OriginalNamedDiagnostic {
            return existing
        }
        let diagnostics = OriginalNamedDiagnostic.f_1000d4624(name: "ItemDataEntity")
        objc_setAssociatedObject(data, &diagnosticsKey, diagnostics, .OBJC_ASSOCIATION_RETAIN_NONATOMIC)
        return diagnostics
    }

    // 31b218: raw getter exceptions log locally and yield no representations; invalid local graphs stay optional.
    @MainActor static func readItems(from object: PastoItemEntity) -> [OriginalPasteboardItem]? {
        guard let data = object.value(forKey: "data") as? NSManagedObject else { return nil }
        return readRepresentations(from: data) { diagnostics(for: data) }
    }

    // 31b218 is also called from a search reader's private context. Invoke on its owning queue.
    static func readRepresentations(from data: NSManagedObject,
                                    diagnostics: () -> OriginalNamedDiagnostic) -> [OriginalPasteboardItem]? {
        let raw: Data
        do {
            raw = try OriginalObjCExceptionBridge.f_1002ffc68 {
                let raw = data.value(forKey: "rawPasteboardItems") as? NSData
                return Data._unconditionallyBridgeFromObjectiveC(raw)
            }
        } catch let error as OriginalObjCExceptionError {
            diagnostics().f_1000d468c().f_1000d4e0c("Unreadable pasteboard items blob: \(error)")
            return []
        } catch { return nil }
        return autoreleasepool { OriginalPasteboardDataCodec.f_10031aeec(raw) }
    }

    // 0x100360ff8: type/checksum, delete old data, create/encode replacement,
    // assign the inverse relation, then generate and write the preview.
    func replace(on object: NSManagedObject, items: [OriginalPasteboardItem], kind: OriginalPasteboardContentKind, checksum: String?,
                 useBinaryPlist: Bool, preview: () -> Data?) {
        object.setValue(Int64(kind.rawValue), forKey: "rawType")
        object.setValue(checksum, forKey: "nativeChecksum")
        if let old = object.value(forKey: "data") as? NSManagedObject {
            context.delete(old)
        }
        let data = NSEntityDescription.insertNewObject(forEntityName: "ItemDataEntity", into: context)
        data.setValue(OriginalPasteboardDataCodec.f_10031a8e8(items, useBinaryPlist: useBinaryPlist),
                      forKey: "rawPasteboardItems")
        object.setValue(data, forKey: "data")
        object.setValue(preview(), forKey: "rawPreview")
    }
}

/// Populate required native creation time and content relationships before destination validation.
/// The original store is replaced only after migration succeeds.
@objc(PastoItemDataMigrationPolicy)
final class PastoItemDataMigrationPolicy: NSEntityMigrationPolicy {
    private var binaryPlist: Bool?

    override func createRelationships(forDestination object: NSManagedObject,
                                      in mapping: NSEntityMapping, manager: NSMigrationManager) throws {
        try super.createRelationships(forDestination: object, in: mapping, manager: manager)
        // The old local date records historical recency; preserve it when introducing the native field.
        if manager.sourceModel.entitiesByName["Item"]?.attributesByName["createdAt"] == nil {
            let sources = manager.sourceInstances(forEntityMappingName: mapping.name, destinationInstances: [object])
            guard sources.count == 1, let source = sources.first else { throw CocoaError(.fileReadCorruptFile) }
            let localDate = source.entity.attributesByName["localCreatedAt"] != nil
                ? source.value(forKey: "localCreatedAt") as? Date : nil
            guard let createdAt = localDate ?? source.value(forKey: "timestamp") as? Date else {
                throw CocoaError(.fileReadCorruptFile)
            }
            object.setPrimitiveValue(createdAt, forKey: "createdAt")
        }
        guard object.value(forKey: "data") == nil else { return }
        guard let encoded = object.value(forKey: "content") as? Data else {
            throw CocoaError(.fileReadCorruptFile)
        }
        let value = try PropertyListDecoder().decode(ClipboardItem.self, from: encoded)
        if binaryPlist == nil {
            let request = NSFetchRequest<NSManagedObject>(entityName: "State")
            request.fetchLimit = 2
            let roots = try manager.sourceContext.fetch(request)
            guard roots.count <= 1 else { throw CocoaError(.fileReadCorruptFile) }
            if let root = roots.first {
                guard let bytes = root.value(forKey: "preferences") as? Data else {
                    throw CocoaError(.fileReadCorruptFile)
                }
                binaryPlist = try PropertyListDecoder().decode(AppPreferences.self, from: bytes).useBinaryPlist
            } else { binaryPlist = AppPreferences().useBinaryPlist }
        }
        let items = try ClipboardStore.originalPasteboardItems(from: value.payloads)
        let kind = OriginalPasteboardClassification.f_10032362c(items)
        let preview = value.rawPreview ?? OriginalImagePreviewMetadataCodec.encode(
            value.imagePreviewMetadata, binaryPropertyList: binaryPlist!)
        ClipboardItemDataPersistence(context: manager.destinationContext).replace(on: object, items: items, kind: kind,
            checksum: object.value(forKey: "nativeChecksum") as? String, useBinaryPlist: binaryPlist!) { preview }
        if let raw = value.payloads[originalItemDataPayloadKey],
           let data = object.value(forKey: "data") as? NSManagedObject {
            data.setValue(raw, forKey: "rawPasteboardItems")
        }
    }
}
