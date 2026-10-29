import CloudKit
import Foundation

/// Durable counterpart of the original ObjectMetadata / ObjectPendingMapping repositories.
/// This lives in the same local transaction as content, not in a second sync snapshot file.
public struct OriginalCloudKitJournal: Codable, Equatable, Sendable {
    public struct Pending: Codable, Equatable, Sendable {
        public var id: OriginalCloudRecordID
        public var scope: OriginalCloudKitScope
        public var deletion: Bool
        public var generation: UInt64
    }
    public var deviceID = UUID().uuidString
    public var zoneName = "Pasto"
    public var deviceName: String?
    public var documents: [String: OriginalCloudDocument] = [:]
    public var localBaseline: [String: OriginalCloudDocument] = [:]
    public var pending: [String: Pending] = [:]
    public var confirmed: Set<String> = []
    public var serializations: [String: Data] = [:]
    public var fetchedScopes: Set<String> = []
    public var accountConfirmationRequired = false
    private var generation: UInt64 = 0

    public init() {}
    public static func key(_ id: OriginalCloudRecordID, scope: OriginalCloudKitScope) -> String { "\(scope.rawValue).\(id.key)" }

    private mutating func enqueue(_ id: OriginalCloudRecordID, scope: OriginalCloudKitScope, deletion: Bool) {
        generation &+= 1
        pending[Self.key(id, scope: scope)] = Pending(id: id, scope: scope, deletion: deletion, generation: generation)
    }

    /// Capture differences against the last local projection, including permanent deletions.
    public mutating func capture(_ values: [OriginalCloudDocument]) throws {
        var next: [String: OriginalCloudDocument] = [:]
        for var value in values {
            try OriginalCloudKitSchema.validate(value)
            let key = Self.key(value.id, scope: value.scope)
            guard next[key] == nil else { throw PastoCloudKitError.invalidRecord }
            if let old = documents[key] { value.systemFields = old.systemFields }
            next[key] = value
            guard localBaseline[key]?.hasSameContent(as: value) != true else { continue }
            documents[key] = value
            enqueue(value.id, scope: value.scope, deletion: false)
        }
        for (key, value) in localBaseline where next[key] == nil {
            documents.removeValue(forKey: key)
            enqueue(value.id, scope: value.scope, deletion: true)
        }
        localBaseline = next
    }

    public mutating func received(_ values: [OriginalCloudDocument], deleted: [OriginalCloudRecordID], scope: OriginalCloudKitScope) throws {
        for value in values {
            try OriginalCloudKitSchema.validate(value)
            guard value.scope == scope else { throw PastoCloudKitError.invalidRecord }
        }
        for value in values {
            let key = Self.key(value.id, scope: scope)
            // A pending explicit local deletion must not be resurrected by an older fetch.
            if pending[key]?.deletion == true { continue }
            let merged: OriginalCloudDocument
            if pending[key] != nil, let client = documents[key] {
                merged = try OriginalCloudKitConflictResolver.resolve(client: client, server: value)
            } else { merged = value }
            documents[key] = merged
            confirmed.insert(key)
            if merged.hasSameContent(as: value) { pending.removeValue(forKey: key) }
            else { enqueue(merged.id, scope: scope, deletion: false) }
        }
        for id in deleted {
            let key = Self.key(id, scope: scope)
            documents.removeValue(forKey: key)
            pending.removeValue(forKey: key)
            confirmed.remove(key)
        }
    }

    /// 0x10039c*: retain, rather than discard, saves whose parent has not reached the server.
    public func eligible(scope: OriginalCloudKitScope) -> [Pending] {
        guard fetchedScopes.contains(String(scope.rawValue)), !accountConfirmationRequired else { return [] }
        return pending.keys.sorted().compactMap { key in
            guard let change = pending[key], change.scope == scope else { return nil }
            if !change.deletion {
                guard let document = documents[key] else { return nil }
                if let parent = document.parent, !confirmed.contains(Self.key(parent, scope: scope)) { return nil }
            }
            return change
        }
    }

    public mutating func acknowledged(_ server: OriginalCloudDocument, generation sent: UInt64) throws {
        try OriginalCloudKitSchema.validate(server)
        let key = Self.key(server.id, scope: server.scope)
        confirmed.insert(key)
        if pending[key]?.generation == sent, pending[key]?.deletion == false {
            documents[key] = server
            pending.removeValue(forKey: key)
        } else if documents[key] != nil {
            documents[key]?.systemFields = server.systemFields
        }
        localBaseline[key]?.systemFields = server.systemFields
    }

    public mutating func acknowledgedDeletion(_ change: Pending) {
        let key = Self.key(change.id, scope: change.scope)
        if pending[key]?.generation == change.generation { pending.removeValue(forKey: key) }
        confirmed.remove(key)
        // A local recreation while deletion was in flight must not carry the deleted change tag.
        documents[key]?.systemFields = nil
    }

    public mutating func finishedInitialFetch(scope: OriginalCloudKitScope) {
        fetchedScopes.insert(String(scope.rawValue))
        // Original first-fetch recovery seeds local records without server metadata.
        for (key, document) in documents where document.scope == scope && !confirmed.contains(key) && pending[key] == nil {
            enqueue(document.id, scope: scope, deletion: false)
        }
    }

    public mutating func deletedZone(_ zone: CKRecordZone.ID, scope: OriginalCloudKitScope) -> Bool {
        // 0x100398d9c ignores historical zone deletions during the first sync.
        guard fetchedScopes.contains(String(scope.rawValue)) else { return false }
        for (key, value) in documents where value.scope == scope && value.id.zone == zone.zoneName && value.id.owner == zone.ownerName {
            documents.removeValue(forKey: key); pending.removeValue(forKey: key); confirmed.remove(key)
        }
        return true
    }

    public mutating func resetAccount() {
        serializations.removeAll(); confirmed.removeAll(); fetchedScopes.removeAll(); pending.removeAll()
        for key in documents.keys { documents[key]?.systemFields = nil }
        accountConfirmationRequired = true
    }

    public mutating func resumeAccount() {
        accountConfirmationRequired = false
    }

    public mutating func recoverRecord(_ id: OriginalCloudRecordID, scope: OriginalCloudKitScope) {
        let key = Self.key(id, scope: scope)
        confirmed.remove(key)
        documents[key]?.systemFields = nil
        if documents[key] != nil { enqueue(id, scope: scope, deletion: false) }
    }

    public mutating func recoverPrivateZone() {
        for value in documents.values where value.scope == .private { recoverRecord(value.id, scope: .private) }
    }
}
