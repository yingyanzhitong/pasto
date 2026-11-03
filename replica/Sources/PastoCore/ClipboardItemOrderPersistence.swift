import CoreData
import Foundation

/// Queue-confined adapter for ItemEntity.displayOrderInPinboard, distinct from ListMetadataEntity.index.
final class ClipboardItemOrderPersistence {
    static let versionKey = "nativeItemOrderVersion"

    static func addField(to model: NSManagedObjectModel) {
        let order = NSAttributeDescription()
        order.name = "displayOrderInPinboard"; order.attributeType = .integer64AttributeType
        order.isOptional = false; order.defaultValue = 0
        model.entitiesByName["Item"]!.properties.append(order)
        let version = NSAttributeDescription()
        version.name = versionKey; version.attributeType = .integer64AttributeType; version.isOptional = true
        model.entitiesByName["State"]!.properties.append(version)
    }

    // Only the old local blob is a migration input. Normal readers use the managed column.
    static func bootstrap(in context: NSManagedObjectContext, root: NSManagedObject) throws {
        guard (root.value(forKey: versionKey) as? NSNumber)?.int64Value != 1 else { return }
        for object in try context.fetch(PastoItemEntity.defaultFetchRequest()) {
            let item = try ClipboardPersistence.decode(ClipboardItem.self, object)
            object.setValue(item.pinboardOrder ?? 0, forKey: "displayOrderInPinboard")
        }
        root.setValue(Int64(1), forKey: versionKey)
    }

    static func project(_ item: inout ClipboardItem, from object: NSManagedObject) throws {
        guard !item.pinboardIDs.isEmpty else { item.pinboardOrder = nil; return }
        guard let order = (object.value(forKey: "displayOrderInPinboard") as? NSNumber)?.int64Value else {
            throw CocoaError(.fileReadCorruptFile)
        }
        item.pinboardOrder = order
    }

    static func update(_ item: ClipboardItem, on object: NSManagedObject) {
        let order = item.pinboardOrder ?? 0
        if (object.value(forKey: "displayOrderInPinboard") as? NSNumber)?.int64Value != order {
            object.setValue(order, forKey: "displayOrderInPinboard")
        }
    }
}
