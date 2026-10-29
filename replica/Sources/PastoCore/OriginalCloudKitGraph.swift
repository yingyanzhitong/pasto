import CryptoKit
import Foundation

/// Adapter from Pasto's model to the original wire entity/field names.
/// Pasto owns its zone, stable history ID and child suffixes.
public enum OriginalCloudKitGraph {
    public static let historyIdentifier = "E8CB6A03-9E6C-4D3C-924B-02721DC6E60A"

    public static func localID(_ document: OriginalCloudDocument) -> UUID? {
        guard document.type == "ItemEntity" || document.type == "ListEntity" else { return nil }
        if document.scope == .private { return UUID(uuidString: document.id.name) }
        var bytes = Array(SHA256.hash(data: Data(document.id.key.utf8)).prefix(16))
        bytes[6] = (bytes[6] & 15) | 0x50; bytes[8] = (bytes[8] & 63) | 0x80
        return bytes.withUnsafeBufferPointer { NSUUID(uuidBytes: $0.baseAddress!) as UUID }
    }

    public static func capture(items: [ClipboardItem], pinboards: [Pinboard], applications: [SourceApplicationRecord],
                               capacity: Int, journal: OriginalCloudKitJournal, now: Date,
                               previousItems: [ClipboardItem] = []) throws -> [OriginalCloudDocument] {
        let existing = journal.documents.values
        let previousItems = Dictionary(uniqueKeysWithValues: previousItems.map { ($0.id, $0) })
        var result: [OriginalCloudDocument] = []
        func reference(_ id: OriginalCloudRecordID, cascade: Bool = false) -> OriginalCloudField { .reference(id, deleteSelf: cascade) }
        func previous(_ id: OriginalCloudRecordID, scope: OriginalCloudKitScope) -> OriginalCloudDocument? {
            journal.documents[OriginalCloudKitJournal.key(id, scope: scope)]
        }
        func make(_ type: String, _ id: OriginalCloudRecordID, scope: OriginalCloudKitScope = .private,
                  fields: [String: OriginalCloudField], parent: OriginalCloudRecordID? = nil) -> OriginalCloudDocument {
            var value = OriginalCloudDocument(id: id, type: type, scope: scope, fields: fields, parent: parent)
            let old = previous(id, scope: scope)
            if type != "ItemDataEntity" {
                let initial = type == "DeviceEntity" ? now : Date.distantPast
                value.fields["createdAt"] = fields["createdAt"] ?? old?.fields["createdAt"] ?? .date(initial)
                value.fields["updatedAt"] = fields["updatedAt"] ?? old?.fields["updatedAt"] ?? .date(initial)
                if type != "ItemEntity", let old, !value.hasSameContent(as: OriginalCloudDocument(id: old.id, type: old.type, scope: old.scope,
                    fields: old.fields, parent: old.parent)) {
                    value.fields["updatedAt"] = .date(now)
                }
            }
            value.systemFields = old?.systemFields
            return value
        }
        func identity(_ local: UUID, type: String) -> (OriginalCloudRecordID, OriginalCloudKitScope) {
            if let value = existing.first(where: { $0.type == type && localID($0) == local }) { return (value.id, value.scope) }
            return (OriginalCloudRecordID(name: local.uuidString, zone: journal.zoneName), .private)
        }

        let device = OriginalCloudRecordID(name: journal.deviceID, zone: journal.zoneName)
        // Preserve peer devices instead of assigning their items to this Mac.
        result += existing.filter { $0.type == "DeviceEntity" && $0.id != device }
        result.append(make("DeviceEntity", device, fields: ["identifier": .string(device.name),
            "name": .string(journal.deviceName ?? Host.current().localizedName ?? "Mac"), "rawType": .integer(1),
            "appVersion": .string(Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "development")]))
        let history = OriginalCloudRecordID(name: historyIdentifier, zone: journal.zoneName)
        let boards = Dictionary(uniqueKeysWithValues: pinboards.map { ($0.id, identity($0.id, type: "ListEntity")) })
        var grouped: [String: [OriginalCloudField]] = [:]
        for item in items where !item.isDeleted {
            let (id, scope) = identity(item.id, type: "ItemEntity")
            let old = previous(id, scope: scope)
            let list = item.pinboardOwnerID.flatMap { boards[$0] } ?? (history, .private)
            guard list.1 == scope else { throw PastoCloudKitError.invalidRecord }
            let dataID = old?.fields["data"]?.referencedID ?? OriginalCloudRecordID(name: id.name + ".data", zone: id.zone, owner: id.owner)
            let raw: Data, rawType: OriginalCloudField, checksum: OriginalCloudField?
            let local = journal.localBaseline[OriginalCloudKitJournal.key(id, scope: scope)]
            if previousItems[item.id]?.payloads == item.payloads,
               let data = journal.localBaseline[OriginalCloudKitJournal.key(dataID, scope: scope)],
               case .asset(let bytes) = data.fields["rawPasteboardItems"], let type = local?.fields["rawType"] {
                raw = bytes; rawType = type; checksum = local?.fields["checksum"]
            } else {
                let representations = try ClipboardStore.originalPasteboardItems(from: item.payloads)
                raw = item.payloads[originalItemDataPayloadKey]
                    ?? OriginalPasteboardDataCodec.f_10031a8e8(representations, useBinaryPlist: true)
                rawType = .integer(Int64(OriginalPasteboardClassification.f_10032362c(representations).rawValue))
                checksum = try ClipboardStore.knownPasteboardChecksum(from: item.payloads).map(OriginalCloudField.string)
            }
            var fields: [String: OriginalCloudField] = ["identifier": .string(id.name), "createdAt": .date(item.createdAt),
                "updatedAt": .date(item.updatedAt), "timestamp": .date(item.createdAt),
                "rawType": rawType,
                "data": reference(dataID, cascade: true), "list": reference(list.0),
                "device": old?.fields["device"] ?? reference(device)]
            if let title = item.originalTitle { fields["title"] = .string(title) }
            if let preview = item.rawPreview { fields["rawPreview"] = .data(preview) }
            if let order = item.pinboardOrder { fields["displayOrderInPinboard"] = .integer(order) }
            if let checksum { fields["checksum"] = checksum }
            if let bundle = item.sourceApplicationBundleID {
                fields["sourceApplication"] = reference(OriginalCloudRecordID(name: bundle, zone: id.zone, owner: id.owner))
            }
            result.append(make("ItemEntity", id, scope: scope, fields: fields, parent: list.0))
            result.append(make("ItemDataEntity", dataID, scope: scope,
                fields: ["rawPasteboardItems": .asset(raw), "item": reference(id)], parent: id))
            grouped[OriginalCloudKitJournal.key(list.0, scope: scope), default: []].append(reference(id))
        }
        func list(_ id: OriginalCloudRecordID, scope: OriginalCloudKitScope, name: String, type: Int64, attributes: Data, index: Int64) {
            let metadata = previous(id, scope: scope)?.fields["metadata"]?.referencedID
                ?? OriginalCloudRecordID(name: id.name + ".metadata", zone: id.zone, owner: id.owner)
            let refs = (grouped[OriginalCloudKitJournal.key(id, scope: scope)] ?? []).sorted { ($0.referencedID?.key ?? "") < ($1.referencedID?.key ?? "") }
            result.append(make("ListEntity", id, scope: scope, fields: ["identifier": .string(id.name), "name": .string(name),
                "rawType": .integer(type), "rawAttributes": .data(attributes), "items": .array(refs), "metadata": reference(metadata, cascade: true)]))
            result.append(make("ListMetadataEntity", metadata, scope: scope, fields: ["identifier": .string(metadata.name),
                "index": .integer(index), "list": reference(id)], parent: id))
        }
        list(history, scope: .private, name: "剪贴板", type: 1,
             attributes: try JSONSerialization.data(withJSONObject: ["type": "clipboard", "capacity": capacity], options: .sortedKeys), index: -1)
        for board in pinboards {
            let (id, scope) = boards[board.id]!
            list(id, scope: scope, name: board.name, type: Int64(board.rawType ?? 2),
                 attributes: try board.rawAttributes ?? OriginalPinboardAttributes.encoded(colorCode: OriginalPinboardAttributes.parsedColorCode(board.colorHex) ?? 0),
                 index: Int64(board.sortOrder))
        }
        for application in applications {
            let id = OriginalCloudRecordID(name: application.bundleIdentifier, zone: journal.zoneName)
            var fields: [String: OriginalCloudField] = ["bundleIdentifier": .string(application.bundleIdentifier), "name": .string(application.name)]
            if let color = application.rawColor { fields["rawColor"] = .integer(Int64(color)) }
            if let icon = application.rawIcon { fields["rawIcon"] = .data(icon) }
            result.append(make("ApplicationEntity", id, fields: fields))
        }
        // Shared application records belong to their owner's zone; do not republish privately.
        result += existing.filter { $0.type == "ApplicationEntity" && $0.scope == .shared }
        return result
    }

    public struct Projection {
        public var items: [ClipboardItem]
        public var pinboards: [Pinboard]
        public var applications: [SourceApplicationRecord]
        public var capacity: Int?
    }

    /// Two-pass relationship resolution. Incomplete records stay in the journal for a later fetch;
    /// never create a blank local clipboard item while its CKAsset or list is still missing.
    public static func project(_ journal: OriginalCloudKitJournal, preserving items: [ClipboardItem],
                               pinboards: [Pinboard], applications: [SourceApplicationRecord]) throws -> Projection {
        let documents = journal.documents
        func related(_ value: OriginalCloudDocument, _ field: String) -> OriginalCloudDocument? {
            guard let id = value.fields[field]?.referencedID else { return nil }
            return documents[OriginalCloudKitJournal.key(id, scope: value.scope)]
        }
        let managed = Set(journal.localBaseline.values.compactMap(localID))
        var result = Projection(items: items.filter { !managed.contains($0.id) }, pinboards: pinboards.filter { !managed.contains($0.id) }, applications: applications, capacity: nil)
        for value in documents.values where value.type == "ApplicationEntity" && value.scope == .private {
            guard let bundle = value.fields["bundleIdentifier"]?.string else { throw PastoCloudKitError.invalidRecord }
            let app = SourceApplicationRecord(bundleIdentifier: bundle, name: value.fields["name"]?.string ?? "",
                rawIcon: value.fields["rawIcon"]?.bytes, rawColor: value.fields["rawColor"]?.integer.flatMap { $0 >= 0 ? UInt64($0) : nil })
            result.applications.removeAll { $0.bundleIdentifier == bundle }; result.applications.append(app)
        }
        for value in documents.values where value.type == "ListEntity" {
            if value.fields["rawType"]?.integer == 1 {
                if value.scope == .private, let raw = value.fields["rawAttributes"]?.bytes,
                   let attributes = try JSONSerialization.jsonObject(with: raw) as? [String: Any], let capacity = attributes["capacity"] as? Int, capacity >= 0 {
                    result.capacity = capacity
                }
                continue
            }
            guard let id = localID(value) else { throw PastoCloudKitError.invalidRecord }
            guard let metadata = related(value, "metadata") else {
                if let old = pinboards.first(where: { $0.id == id }) { result.pinboards.append(old) }
                continue
            }
            guard let type = Int16(exactly: value.fields["rawType"]?.integer ?? 2) else { throw PastoCloudKitError.invalidRecord }
            let attributes = value.fields["rawAttributes"]?.bytes
            let color = OriginalPinboardAttributes.colorCode(from: attributes) ?? 0xf0554d
            result.pinboards.append(Pinboard(id: id, name: value.fields["name"]?.string ?? "", colorHex: String(format: "#%06llX", color & 0xffffff),
                sortOrder: Int(metadata.fields["index"]?.integer ?? 0), rawType: type, rawAttributes: attributes))
        }
        for value in documents.values where value.type == "ItemEntity" {
            guard let id = localID(value) else { throw PastoCloudKitError.invalidRecord }
            guard let list = related(value, "list"),
                  let data = related(value, "data"), let raw = data.fields["rawPasteboardItems"]?.bytes else {
                if let old = items.first(where: { $0.id == id }) { result.items.append(old) }
                continue
            }
            guard let representations = OriginalPasteboardDataCodec.decodeIfValid(raw), !representations.isEmpty else {
                throw PastoCloudKitError.invalidRecord
            }
            let isHistory = list.fields["rawType"]?.integer == 1
            let owner = isHistory ? nil : localID(list)
            guard isHistory || result.pinboards.contains(where: { $0.id == owner }) else { continue }
            let source = related(value, "sourceApplication")
            if value.fields["sourceApplication"] != nil && source == nil { continue }
            let bundle = source?.fields["bundleIdentifier"]?.string
            if let bundle, !result.applications.contains(where: { $0.bundleIdentifier == bundle }) {
                result.applications.append(SourceApplicationRecord(bundleIdentifier: bundle, name: source?.fields["name"]?.string ?? "",
                    rawIcon: source?.fields["rawIcon"]?.bytes))
            }
            var payloads: [String: Data] = [originalItemDataPayloadKey: raw]
            if let first = representations.first {
                for type in first.f_10037da6c() { payloads[type] = first.f_10037d810(forType: type) }
            }
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
            let text = kind == .files ? representations.compactMap { $0.f_10037cc6c()?.path }.joined(separator: "\n")
                : representations.lazy.compactMap { $0.f_10037c9a8() ?? $0.f_10037d33c()?.string }.first
            let created = value.fields["timestamp"]?.date ?? value.fields["createdAt"]?.date ?? .distantPast
            result.items.append(ClipboardItem(id: id, createdAt: created, updatedAt: value.fields["updatedAt"]?.date ?? created,
                title: value.fields["title"]?.string ?? "", kind: kind, plainText: text, sourceName: source?.fields["name"]?.string ?? "",
                sourceBundleID: bundle, payloads: payloads, pinboardIDs: owner.map { [$0] } ?? [],
                sourceDevice: related(value, "device")?.fields["name"]?.string ?? "Mac", isInHistory: isHistory,
                rawPreview: value.fields["rawPreview"]?.bytes, hasExplicitTitle: value.fields["title"] != nil,
                pinboardOrder: value.fields["displayOrderInPinboard"]?.integer, sourceApplicationBundleID: bundle, pinboardOwnerID: owner))
        }
        return result
    }
}
