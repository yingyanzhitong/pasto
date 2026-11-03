import CoreData
import Foundation

/// ItemEntity.title is optional metadata, independent of archived pasteboard content.
final class ClipboardItemTitlePersistence {
    static let versionKey = "nativeItemTitleVersion"

    static func addField(to model: NSManagedObjectModel) {
        let title = NSAttributeDescription()
        title.name = "title"; title.attributeType = .stringAttributeType
        title.isOptional = true
        title.isIndexedBySpotlight = true
        model.entitiesByName["Item"]!.properties.append(title)
        let version = NSAttributeDescription()
        version.name = versionKey; version.attributeType = .integer64AttributeType
        version.isOptional = true
        model.entitiesByName["State"]!.properties.append(version)
    }

    // Bootstrap once from the legacy value, then the managed field is authoritative, including nil.
    static func bootstrap(in context: NSManagedObjectContext, root: NSManagedObject) throws {
        guard (root.value(forKey: versionKey) as? NSNumber)?.int64Value != 1 else { return }
        for object in try context.fetch(PastoItemEntity.defaultFetchRequest()) {
            let item = try ClipboardPersistence.decode(ClipboardItem.self, object)
            update(item, on: object)
        }
        root.setValue(Int64(1), forKey: versionKey)
    }

    static func project(_ item: inout ClipboardItem, from object: NSManagedObject) {
        if let title = object.value(forKey: "title") as? String {
            item.title = title
            item.hasExplicitTitle = true
        } else {
            // Clear an old explicit title without discarding a legacy generated display label.
            if item.originalTitle != nil { item.title = "" }
            item.hasExplicitTitle = false
        }
    }

    // 364ab4 compares the optional title before invoking the native setter.
    static func update(_ item: ClipboardItem, on object: NSManagedObject) {
        let title = item.originalTitle
        if (object.value(forKey: "title") as? String) != title {
            object.setValue(title, forKey: "title")
        }
    }
}
