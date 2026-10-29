import CloudKit
import CryptoKit
import Foundation

public enum PastoCloudKitError: LocalizedError {
    case invalidRecord, unsupportedField(String), unavailableAsset, unconfigured, persistenceFailed, unresolvedConflict
    public var errorDescription: String? {
        switch self {
        case .invalidRecord: return "CloudKit 记录或引用无效，已保留本地数据。"
        case .unsupportedField(let field): return "无法解码 CloudKit 字段：\(field)。"
        case .unavailableAsset: return "CloudKit 附件尚不可用，本次变更未应用。"
        case .unconfigured: return "尚未配置 Pasto 自有的 CloudKit 容器与开发者签名。"
        case .persistenceFailed: return "同步数据保存失败，已停止推进云端同步状态。"
        case .unresolvedConflict: return "遇到尚未完成对照的同步冲突，已保留本机变更并暂停同步。"
        }
    }
}

/// Original SyncEngine distinguishes its private/shared engines with raw scopes 2/3.
public enum OriginalCloudKitScope: Int, Codable, Sendable, CaseIterable { case `private` = 2, shared = 3 }

public struct OriginalCloudRecordID: Codable, Hashable, Sendable {
    public var name: String
    public var zone: String
    public var owner: String
    public init(_ id: CKRecord.ID) { name = id.recordName; zone = id.zoneID.zoneName; owner = id.zoneID.ownerName }
    public init(name: String, zone: String = "Pasto", owner: String = CKCurrentUserDefaultName) {
        self.name = name; self.zone = zone; self.owner = owner
    }
    public var ckID: CKRecord.ID { CKRecord.ID(recordName: name, zoneID: CKRecordZone.ID(zoneName: zone, ownerName: owner)) }
    public var key: String { [owner, zone, name].map { Data($0.utf8).base64EncodedString() }.joined(separator: ".") }
}

public indirect enum OriginalCloudField: Codable, Equatable, Sendable {
    case string(String), integer(Int64), double(Double), date(Date), data(Data), asset(Data)
    case reference(OriginalCloudRecordID, deleteSelf: Bool), array([OriginalCloudField])
    public var string: String? { if case .string(let value) = self { return value }; return nil }
    public var integer: Int64? { if case .integer(let value) = self { return value }; return nil }
    public var date: Date? { if case .date(let value) = self { return value }; return nil }
    public var bytes: Data? {
        switch self { case .data(let value), .asset(let value): return value; default: return nil }
    }
    public var referencedID: OriginalCloudRecordID? {
        if case .reference(let value, _) = self { return value }; return nil
    }
}

public struct OriginalCloudDocument: Codable, Equatable, Sendable {
    public var id: OriginalCloudRecordID
    public var type: String
    public var scope: OriginalCloudKitScope
    public var fields: [String: OriginalCloudField]
    public var parent: OriginalCloudRecordID?
    public var systemFields: Data?
    public init(id: OriginalCloudRecordID, type: String, scope: OriginalCloudKitScope = .private,
                fields: [String: OriginalCloudField], parent: OriginalCloudRecordID? = nil, systemFields: Data? = nil) {
        self.id = id; self.type = type; self.scope = scope; self.fields = fields
        self.parent = parent; self.systemFields = systemFields
    }
    public func hasSameContent(as other: Self) -> Bool {
        id == other.id && type == other.type && fields == other.fields && parent == other.parent && scope == other.scope
    }
}

/// Field names/types come from Paste 6.6.6 v10.mom; ObjectMetadata/PendingMapping remain local.
public enum OriginalCloudKitSchema {
    public static let recordTypes: Set<String> = ["ApplicationEntity", "DeviceEntity", "ItemEntity", "ItemDataEntity", "ListEntity", "ListMetadataEntity"]
    public static let fields: [String: Set<String>] = [
        "ApplicationEntity": ["bundleIdentifier", "createdAt", "name", "rawColor", "rawIcon", "updatedAt", "items"],
        "DeviceEntity": ["appVersion", "createdAt", "identifier", "name", "rawType", "updatedAt", "items"],
        "ItemEntity": ["checksum", "createdAt", "displayOrderInPinboard", "identifier", "rawPreview", "rawType", "timestamp", "title", "updatedAt", "data", "device", "list", "sourceApplication"],
        "ItemDataEntity": ["rawPasteboardItems", "item"],
        "ListEntity": ["createdAt", "identifier", "name", "rawAttributes", "rawShareRecord", "rawType", "updatedAt", "items", "metadata"],
        "ListMetadataEntity": ["createdAt", "identifier", "index", "updatedAt", "list"]
    ]
    public static let identifierFields = ["ApplicationEntity": "bundleIdentifier", "DeviceEntity": "identifier", "ItemEntity": "identifier", "ListEntity": "identifier", "ListMetadataEntity": "identifier"]
    public static let externalDataFields: Set<String> = ["rawPasteboardItems"]
    public static func validate(_ document: OriginalCloudDocument) throws {
        guard !document.id.name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty,
              !document.id.zone.isEmpty, !document.id.owner.isEmpty, recordTypes.contains(document.type) else {
            throw PastoCloudKitError.invalidRecord
        }
        if let key = identifierFields[document.type] {
            guard let value = document.fields[key]?.string, !value.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
                throw PastoCloudKitError.invalidRecord
            }
        }
        let strings: Set<String> = ["identifier", "bundleIdentifier", "name", "appVersion", "title", "checksum"]
        let integers: Set<String> = ["rawType", "rawColor", "displayOrderInPinboard", "index"]
        let dates: Set<String> = ["createdAt", "updatedAt", "timestamp"]
        let binary: Set<String> = ["rawIcon", "rawPreview", "rawShareRecord", "rawAttributes", "rawPasteboardItems"]
        let relationships: Set<String> = ["data", "device", "list", "sourceApplication", "metadata", "item"]
        for (key, value) in document.fields {
            guard fields[document.type, default: []].contains(key) else { throw PastoCloudKitError.unsupportedField(key) }
            if strings.contains(key), value.string == nil { throw PastoCloudKitError.invalidRecord }
            if integers.contains(key), value.integer == nil { throw PastoCloudKitError.invalidRecord }
            if dates.contains(key), value.date == nil { throw PastoCloudKitError.invalidRecord }
            if binary.contains(key), value.bytes == nil { throw PastoCloudKitError.invalidRecord }
            if relationships.contains(key) {
                guard let id = value.referencedID, id.zone == document.id.zone, id.owner == document.id.owner,
                      !id.name.isEmpty else { throw PastoCloudKitError.invalidRecord }
            }
            if key == "items" {
                guard case .array(let references) = value, references.allSatisfy({
                    guard let id = $0.referencedID else { return false }
                    return id.zone == document.id.zone && id.owner == document.id.owner && !id.name.isEmpty
                }) else { throw PastoCloudKitError.invalidRecord }
            }
        }
        if let parent = document.parent {
            guard parent.zone == document.id.zone, parent.owner == document.id.owner else { throw PastoCloudKitError.invalidRecord }
        }
    }
}

public enum OriginalCloudKitRecordCodec {
    /// 0x10038f904 / 0x10038eecc: retain server system fields when recreating a record.
    public static func restoreSystemFields(_ data: Data) throws -> CKRecord {
        try OriginalObjCExceptionBridge.withResult {
            let decoder = try NSKeyedUnarchiver(forReadingFrom: data)
            decoder.requiresSecureCoding = true
            decoder.decodingFailurePolicy = .setErrorAndReturn
            defer { decoder.finishDecoding() }
            guard let record = CKRecord(coder: decoder), decoder.error == nil else { throw PastoCloudKitError.invalidRecord }
            return record
        }
    }

    public static func systemFields(of record: CKRecord) -> Data {
        let encoder = NSKeyedArchiver(requiringSecureCoding: true)
        record.encodeSystemFields(with: encoder)
        encoder.finishEncoding()
        return encoder.encodedData
    }

    public static func decode(_ record: CKRecord, scope: OriginalCloudKitScope) throws -> OriginalCloudDocument {
        var fields: [String: OriginalCloudField] = [:]
        for key in record.allKeys() { fields[key] = try decodeField(record[key], key: key) }
        let result = OriginalCloudDocument(id: OriginalCloudRecordID(record.recordID), type: record.recordType,
            scope: scope, fields: fields, parent: record.parent.map { OriginalCloudRecordID($0.recordID) }, systemFields: systemFields(of: record))
        try OriginalCloudKitSchema.validate(result)
        return result
    }

    private static func decodeField(_ value: CKRecordValue?, key: String) throws -> OriginalCloudField {
        if let value = value as? CKAsset {
            guard let url = value.fileURL else { throw PastoCloudKitError.unavailableAsset }
            return .asset(try Data(contentsOf: url))
        }
        if let value = value as? CKRecord.Reference { return .reference(OriginalCloudRecordID(value.recordID), deleteSelf: value.action == .deleteSelf) }
        if let value = value as? Date { return .date(value) }
        if let value = value as? Data { return .data(value) }
        if let value = value as? String { return .string(value) }
        if let value = value as? NSNumber {
            let type = String(cString: value.objCType)
            return ["d", "f"].contains(type) ? .double(value.doubleValue) : .integer(value.int64Value)
        }
        if let values = value as? [CKRecordValue] { return .array(try values.map { try decodeField($0, key: key) }) }
        throw PastoCloudKitError.unsupportedField(key)
    }

    public static func encode(_ document: OriginalCloudDocument, assetDirectory: URL) throws -> CKRecord {
        try OriginalCloudKitSchema.validate(document)
        let record: CKRecord
        if let data = document.systemFields {
            record = try restoreSystemFields(data)
            guard record.recordID == document.id.ckID, record.recordType == document.type else { throw PastoCloudKitError.invalidRecord }
        } else { record = CKRecord(recordType: document.type, recordID: document.id.ckID) }
        // Restored system fields do not include old values. Explicit nil writes are required
        // to mark cleared optional fields dirty; omission would leave the server's old title.
        for key in OriginalCloudKitSchema.fields[document.type, default: []] {
            if let value = document.fields[key] { record[key] = try encodeField(value, directory: assetDirectory) }
            else { record[key] = nil }
        }
        record.parent = document.parent.map { CKRecord.Reference(recordID: $0.ckID, action: .none) }
        return record
    }

    private static func encodeField(_ value: OriginalCloudField, directory: URL) throws -> CKRecordValue {
        switch value {
        case .string(let value): return value as NSString
        case .integer(let value): return NSNumber(value: value)
        case .double(let value): return NSNumber(value: value)
        case .date(let value): return value as NSDate
        case .data(let value): return value as NSData
        case .reference(let id, let deleteSelf): return CKRecord.Reference(recordID: id.ckID, action: deleteSelf ? .deleteSelf : .none)
        case .array(let values): return try values.map { try encodeField($0, directory: directory) } as NSArray
        case .asset(let value):
            // 0x10038e594 writes a stable temporary file before constructing CKAsset. Keep files
            // for pending/retried batches; never remove them while CloudKit may still read them.
            try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true,
                                                    attributes: [.posixPermissions: 0o700])
            let name = SHA256.hash(data: value).map { String(format: "%02x", $0) }.joined()
            let url = directory.appendingPathComponent(name)
            if !FileManager.default.fileExists(atPath: url.path) {
                try value.write(to: url, options: .atomic)
                try FileManager.default.setAttributes([.posixPermissions: 0o600], ofItemAtPath: url.path)
            }
            return CKAsset(fileURL: url)
        }
    }
}

public enum OriginalCloudKitConflictResolver {
    /// 0x100394f08: patch the server record, preserving its change tag, using strictly newer
    /// client fields. The identifier is never replaced. Clipboard capacity has its own merge.
    public static func resolve(client: OriginalCloudDocument, server: OriginalCloudDocument) throws -> OriginalCloudDocument {
        guard client.id == server.id, client.type == server.type else { throw PastoCloudKitError.invalidRecord }
        if !client.hasSameContent(as: server),
           client.type == "ItemDataEntity" || client.fields["updatedAt"]?.date == nil || server.fields["updatedAt"]?.date == nil {
            // The original no-date/ItemData branch is not fully recovered. Never acknowledge a
            // guessed server-wins result that would erase an unsent local attachment edit.
            throw PastoCloudKitError.unresolvedConflict
        }
        var result = server
        let newer = (client.fields["updatedAt"]?.date ?? .distantPast) > (server.fields["updatedAt"]?.date ?? .distantPast)
        let identifierKey = OriginalCloudKitSchema.identifierFields[client.type]
        if newer {
            if client.type != "ListEntity", client.fields["rawType"]?.integer == 1, !client.hasSameContent(as: server) {
                throw PastoCloudKitError.unresolvedConflict
            }
            for key in OriginalCloudKitSchema.fields[client.type, default: []] where key != identifierKey && key != "rawAttributes" {
                if client.fields["rawType"]?.integer == 1 { continue }
                result.fields[key] = client.fields[key]
            }
            if !(client.type == "ListEntity" && client.fields["rawType"]?.integer == 1) { result.parent = client.parent }
        }
        if client.type == "ListEntity", client.fields["rawType"]?.integer == 1,
           let a = capacity(client.fields["rawAttributes"]?.bytes), let b = capacity(server.fields["rawAttributes"]?.bytes) {
            if a > 0 && (b == 0 || a < b) { result.fields["rawAttributes"] = client.fields["rawAttributes"] }
        } else if newer, let attributes = client.fields["rawAttributes"] {
            result.fields["rawAttributes"] = attributes
        }
        return result
    }

    private static func capacity(_ data: Data?) -> Int? {
        guard let data, let object = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              object["type"] as? String != "pinboard" else { return nil }
        return object["capacity"] as? Int ?? 30
    }
}

public enum OriginalCloudKitRetryPolicy {
    public enum Action: Equatable { case mergeServer, recreateZone, recreateRecord, removePending, retry, stop }
    /// Bounded recovery branches from 0x10039e1a8; unknown cases stay visible instead of succeeding.
    public static func action(for code: CKError.Code, isPrivate: Bool) -> Action {
        switch code {
        case .serverRecordChanged: return .mergeServer
        case .zoneNotFound, .userDeletedZone: return isPrivate ? .recreateZone : .removePending
        case .unknownItem: return .recreateRecord
        case .permissionFailure: return isPrivate ? .stop : .removePending
        case .networkUnavailable, .networkFailure, .serviceUnavailable, .requestRateLimited, .zoneBusy, .operationCancelled, .notAuthenticated: return .retry
        case .constraintViolation, .invalidArguments: return .removePending
        default: return .stop
        }
    }
}
