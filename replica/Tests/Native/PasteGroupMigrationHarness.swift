import AppKit
import CoreData
import CryptoKit
import Foundation
import PastoCore

@main
struct PasteGroupMigrationHarness {
    struct Failure: Error { var message: String }

    static func check(_ value: @autoclosure () throws -> Bool, _ message: String) throws {
        if try !value() { throw Failure(message: message) }
    }

    static func model() -> NSManagedObjectModel {
        func attribute(_ name: String, _ type: NSAttributeType, external: Bool = false) -> NSAttributeDescription {
            let property = NSAttributeDescription()
            property.name = name; property.attributeType = type; property.isOptional = true
            property.allowsExternalBinaryDataStorage = external
            return property
        }
        func entity(_ name: String, _ properties: [NSPropertyDescription]) -> NSEntityDescription {
            let entity = NSEntityDescription()
            entity.name = name; entity.managedObjectClassName = NSStringFromClass(NSManagedObject.self)
            entity.properties = properties
            return entity
        }
        func relation(_ from: NSEntityDescription, _ name: String, _ to: NSEntityDescription) {
            let relation = NSRelationshipDescription()
            relation.name = name; relation.destinationEntity = to; relation.minCount = 0; relation.maxCount = 1
            relation.isOptional = true; relation.deleteRule = .nullifyDeleteRule
            from.properties.append(relation)
        }
        let list = entity("ListEntity", [attribute("identifier", .stringAttributeType), attribute("name", .stringAttributeType),
            attribute("rawType", .integer16AttributeType), attribute("rawAttributes", .binaryDataAttributeType)])
        let metadata = entity("ListMetadataEntity", [attribute("index", .integer64AttributeType)])
        let data = entity("ItemDataEntity", [attribute("rawPasteboardItems", .binaryDataAttributeType, external: true)])
        let application = entity("ApplicationEntity", [attribute("bundleIdentifier", .stringAttributeType),
            attribute("name", .stringAttributeType), attribute("rawColor", .integer64AttributeType), attribute("rawIcon", .binaryDataAttributeType)])
        let device = entity("DeviceEntity", [attribute("name", .stringAttributeType)])
        let item = entity("ItemEntity", [attribute("identifier", .stringAttributeType), attribute("title", .stringAttributeType),
            attribute("createdAt", .dateAttributeType), attribute("timestamp", .dateAttributeType),
            attribute("updatedAt", .dateAttributeType), attribute("rawPreview", .binaryDataAttributeType),
            attribute("displayOrderInPinboard", .integer64AttributeType)])
        relation(list, "metadata", metadata)
        relation(item, "list", list); relation(item, "data", data)
        relation(item, "sourceApplication", application); relation(item, "device", device)
        let result = NSManagedObjectModel()
        result.entities = [list, metadata, item, data, application, device]
        return result
    }

    @MainActor static func main() {
        do {
            // Read-only, count-only verification against a caller-selected original store.
            if CommandLine.arguments.count == 3, CommandLine.arguments[1] == "--inspect-paste" {
                let snapshot = try PasteGroupMigration.read(from: URL(fileURLWithPath: CommandLine.arguments[2]))
                print("{\"passed\":true,\"groups\":\(snapshot.pinboards.count),\"items\":\(snapshot.items.count),\"unavailable\":\(snapshot.unavailableItemCount),\"source_read_only\":true}")
                return
            }
            try run()
        } catch {
            print(String(data: try! JSONSerialization.data(withJSONObject: ["passed": false, "error": String(describing: error)]), encoding: .utf8)!)
            exit(1)
        }
    }

    @MainActor static func run() throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent("PastoMigrationTests-\(UUID().uuidString)")
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: root) }
        let model = model()
        let coordinator = NSPersistentStoreCoordinator(managedObjectModel: model)
        let source = root.appendingPathComponent("db.sqlite")
        let persistentStore = try coordinator.addPersistentStore(ofType: NSSQLiteStoreType, configurationName: nil, at: source)
        defer { try? coordinator.remove(persistentStore) }
        let writer = NSManagedObjectContext(concurrencyType: .mainQueueConcurrencyType)
        writer.persistentStoreCoordinator = coordinator
        func object(_ entity: String, _ values: [String: Any]) -> NSManagedObject {
            let object = NSEntityDescription.insertNewObject(forEntityName: entity, into: writer)
            for (key, value) in values { object.setValue(value, forKey: key) }
            return object
        }
        let attributes = Data("{\"type\":\"pinboard\",\"colorCode\":4293940557}".utf8)
        let empty = object("ListEntity", ["identifier": UUID().uuidString, "name": "空分组", "rawType": 2,
            "metadata": object("ListMetadataEntity", ["index": 9]), "rawAttributes": attributes])
        let group = object("ListEntity", ["identifier": "legacy-Paste-list-key", "name": "工作 📋", "rawType": 2,
            "metadata": object("ListMetadataEntity", ["index": 3]), "rawAttributes": attributes])
        let history = object("ListEntity", ["identifier": UUID().uuidString, "name": "历史", "rawType": 1,
            "metadata": object("ListMetadataEntity", ["index": 0])])
        let application = object("ApplicationEntity", ["bundleIdentifier": "local.fixture.editor", "name": "合成来源", "rawColor": 0x62a9f5])
        let device = object("DeviceEntity", ["name": "合成设备"])
        let text = OriginalPasteboardItem.f_10037c6d4("中文 😀\nsecond line")
        text.f_10037d8c8(Data("<b>中文 😀</b>".utf8), forType: "public.html")
        let rawText = OriginalPasteboardDataCodec.f_10031a8e8([text], useBinaryPlist: false)
        var seed: UInt64 = 0x123456789abcdef
        let binary = Data((0..<(2 * 1024 * 1024)).map { _ -> UInt8 in
            seed ^= seed << 13; seed ^= seed >> 7; seed ^= seed << 17
            return UInt8(truncatingIfNeeded: seed)
        })
        let opaque = OriginalPasteboardItem()
        opaque.f_10037d8c8(binary, forType: "local.fixture.binary")
        let rawBinary = OriginalPasteboardDataCodec.f_10031a8e8([opaque, OriginalPasteboardItem.f_10037c6d4("附件")], useBinaryPlist: true)
        func item(_ list: NSManagedObject, _ raw: Data?, _ title: String, _ order: Int) -> NSManagedObject {
            let data = object("ItemDataEntity", [:])
            data.setValue(raw, forKey: "rawPasteboardItems")
            return object("ItemEntity", ["identifier": UUID().uuidString, "title": title, "list": list, "data": data,
                "createdAt": Date(timeIntervalSince1970: 1000), "updatedAt": Date(timeIntervalSince1970: 2000),
                "timestamp": Date(timeIntervalSince1970: 3000), "displayOrderInPinboard": order,
                "sourceApplication": application, "device": device])
        }
        let textItem = item(group, rawText, "文字", 20)
        textItem.setValue("legacy-Paste-item-key", forKey: "identifier")
        _ = item(group, rawBinary, "多表示附件", 10)
        _ = item(group, nil, "尚未下载", 30)
        _ = item(history, rawText, "不得迁移历史", 0)
        try writer.save()
        try check(empty.value(forKey: "name") as? String == "空分组", "Fixture missing empty group")
        func hashes() throws -> [String: String] {
            var result: [String: String] = [:]
            for case let file as URL in FileManager.default.enumerator(at: root, includingPropertiesForKeys: nil)! {
                if file.lastPathComponent == "db.sqlite" || file.lastPathComponent == "db.sqlite-wal" || file.path.contains("_EXTERNAL_DATA/") {
                    let bytes = try Data(contentsOf: file)
                    result[file.path] = SHA256.hash(data: bytes).map { String(format: "%02x", $0) }.joined()
                }
            }
            return result
        }
        let before = try hashes()
        try check(before.keys.contains { $0.contains("_EXTERNAL_DATA/") }, "Fixture did not exercise Core Data external binary storage")
        try check(before.keys.contains { $0.hasSuffix("-wal") }, "Fixture did not exercise a live WAL store")
        let snapshot = try PasteGroupMigration.read(from: source, model: model)
        try check(try hashes() == before, "Reader modified source database, WAL or external data")
        try check(snapshot.pinboards.map(\.name) == ["工作 📋", "空分组"], "Group order or empty group lost")
        try check(snapshot.pinboards.first?.rawAttributes == attributes && snapshot.pinboards.first?.colorHex == "#F0554D", "Group color changed")
        try check(snapshot.items.map(\.title) == ["多表示附件", "文字"] && snapshot.unavailableItemCount == 1, "Item order or missing-data accounting incorrect")
        let encoder = JSONEncoder()
        encoder.outputFormatting = .sortedKeys
        try check(try encoder.encode(ClipboardStore.originalPasteboardItems(from: snapshot.items[0].payloads)) == encoder.encode([opaque, OriginalPasteboardItem.f_10037c6d4("附件")]), "Ordered multi-item payload changed")
        try check(snapshot.items[1].plainText == "中文 😀\nsecond line" && snapshot.items[1].kind == .richText, "Unicode or rich-text kind changed")
        let destination = root.appendingPathComponent("destination")
        let store = try ClipboardStore(directoryURL: destination)
        let existing = try store.createPinboard(name: "工作 📋", colorHex: "#00FF00")
        store.preferences.pasteToActiveApp = false
        store.preferences.historyShortcut = nil
        try store.save()
        let stale = try ClipboardStore(directoryURL: destination)
        let historyID = try stale.add(ClipboardItem(plainText: "existing history"))
        let preferences = store.preferences
        let result = try store.importPasteGroups(snapshot)
        try check(result.addedGroups == 2 && result.addedItems == 2 && result.unavailableItems == 1, "Import totals incorrect")
        try check(store.pinboards.contains(existing) && store.items.contains { $0.id == historyID }, "Existing/concurrent user data overwritten")
        try check(store.preferences == preferences, "Migration changed preferences")
        try check(store.items(in: snapshot.pinboards[0].id).map(\.title) == ["多表示附件", "文字"], "Pasto group order differs")
        try check(store.items(in: snapshot.pinboards[1].id).isEmpty, "Empty group was lost")
        let board = NSPasteboard(name: .init("PastoMigrationTests-\(UUID().uuidString)"))
        defer { board.releaseGlobally() }
        try store.writeToPasteboard(id: snapshot.items[0].id, pasteboard: board)
        try check(board.pasteboardItems?.first?.data(forType: .init("local.fixture.binary")) == binary, "Imported external binary cannot be restored")
        try store.renamePinboard(id: snapshot.pinboards[0].id, name: "本地改名")
        try store.updateItem(id: snapshot.items[1].id, title: "本地编辑", text: "保留我的改动")
        let repeated = try store.importPasteGroups(snapshot)
        try check(repeated.addedGroups == 0 && repeated.addedItems == 0 && repeated.existingGroups == 2 && repeated.existingItems == 2, "Repeated migration duplicated data")
        try check(store.pinboards.contains { $0.name == "本地改名" } && store.items.contains { $0.plainText == "保留我的改动" }, "Repeated migration overwrote edits")
        let stateURL = destination.appendingPathComponent("clipboard.json")
        let stateBefore = try Data(contentsOf: stateURL)
        var corrupt = snapshot
        corrupt.items.append(snapshot.items[0])
        do { _ = try store.importPasteGroups(corrupt); throw Failure(message: "Invalid duplicate accepted") }
        catch is ClipboardStoreError { }
        try check(try Data(contentsOf: stateURL) == stateBefore, "Failed migration partially wrote destination")
        let reopened = try ClipboardStore(directoryURL: destination)
        try check(reopened.pinboards == store.pinboards, "Groups did not survive reopen")
        try check(reopened.preferences == preferences, "Preferences changed after reopen")
        if reopened.items != store.items {
            for item in store.items {
                guard let restored = reopened.items.first(where: { $0.id == item.id }) else {
                    throw Failure(message: "Migrated item missing after reopen")
                }
                let a = try JSONSerialization.jsonObject(with: JSONEncoder().encode(item)) as! NSDictionary
                let b = try JSONSerialization.jsonObject(with: JSONEncoder().encode(restored)) as! NSDictionary
                let fields = a.allKeys.compactMap { $0 as? String }.filter { !(a[$0] as AnyObject).isEqual(b[$0]) }
                if !fields.isEmpty { throw Failure(message: "Reopened item fields differ: \(fields)") }
            }
            throw Failure(message: "Reopened item order differs")
        }
        print("{\"passed\":true,\"checks\":[\"read-only live WAL and external blobs\",\"group name/color/order and empty groups\",\"ordered Unicode/rich-text/binary payload restore\",\"unavailable items reported\",\"existing/concurrent data and preferences preserved\",\"repeat import preserves local edits\",\"atomic rejection and reopen\"]}")
    }
}
