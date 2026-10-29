import CryptoKit
import Foundation

public enum ICloudDriveSyncError: LocalizedError {
    case invalidSnapshot, incompatibleVersion, folderUnavailable, downloadPending, clockExhausted

    public var errorDescription: String? {
        switch self {
        case .invalidSnapshot: return "同步数据损坏，已保留本地内容。"
        case .incompatibleVersion: return "同步数据来自较新的 Pasto，请先更新应用。"
        case .folderUnavailable: return "同步文件夹不可用，请检查 iCloud Drive 或重新选择文件夹。"
        case .downloadPending: return "正在从 iCloud Drive 下载同步数据，请稍后重试。"
        case .clockExhausted: return "同步版本记录无效，已停止本次同步。"
        }
    }
}

/// A deterministic, monotonic version for edits made while devices are offline.
public struct ICloudSyncRevision: Codable, Equatable, Comparable, Sendable {
    public var timestamp: Date
    public var sequence: UInt64
    public var deviceID: UUID

    public static func < (lhs: Self, rhs: Self) -> Bool {
        if lhs.timestamp != rhs.timestamp { return lhs.timestamp < rhs.timestamp }
        if lhs.sequence != rhs.sequence { return lhs.sequence < rhs.sequence }
        return lhs.deviceID.uuidString < rhs.deviceID.uuidString
    }
}

public struct ICloudSyncEntity: Codable, Equatable, Sendable {
    public enum Kind: String, Codable, Sendable { case item, pinboard, application }
    public var kind: Kind
    public var id: String
    public var item: ClipboardItem?
    public var pinboard: Pinboard?
    public var application: SourceApplicationRecord?

    public var key: String { "\(kind.rawValue):\(id)" }

    public init(item: ClipboardItem) {
        kind = .item; id = item.id.uuidString; self.item = item
    }
    public init(pinboard: Pinboard) {
        kind = .pinboard; id = pinboard.id.uuidString; self.pinboard = pinboard
    }
    public init(application: SourceApplicationRecord) {
        kind = .application; id = application.bundleIdentifier; self.application = application
    }

    func validate() throws {
        let present = [item != nil, pinboard != nil, application != nil].filter { $0 }.count
        guard present == 1 else { throw ICloudDriveSyncError.invalidSnapshot }
        switch kind {
        case .item:
            guard let item, item.id.uuidString == id else { throw ICloudDriveSyncError.invalidSnapshot }
        case .pinboard:
            guard let pinboard, pinboard.id.uuidString == id else { throw ICloudDriveSyncError.invalidSnapshot }
        case .application:
            guard let application, application.bundleIdentifier == id,
                  application.rawColor.map({ $0 < (UInt64(1) << 63) }) ?? true else {
                throw ICloudDriveSyncError.invalidSnapshot
            }
        }
    }

    func digest() throws -> String {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys]
        // Codable Set order is not stable, even with JSONEncoder.sortedKeys.
        var object = try JSONSerialization.jsonObject(with: encoder.encode(self)) as! [String: Any]
        if var encodedItem = object["item"] as? [String: Any], let item {
            encodedItem["pinboardIDs"] = item.pinboardIDs.map(\.uuidString).sorted()
            object["item"] = encodedItem
        }
        let data = try JSONSerialization.data(withJSONObject: object, options: [.sortedKeys])
        return SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
    }
}

public struct ICloudSyncRecord: Codable, Equatable, Sendable {
    public var key: String
    public var revision: ICloudSyncRevision
    /// nil is an explicit permanent deletion; missing files are never treated as deletions.
    public var entity: ICloudSyncEntity?
}

public struct ICloudSyncSnapshot: Codable, Equatable, Sendable {
    public var format = "pasto-icloud-drive"
    public var version = 1
    public var deviceID: UUID
    public var records: [ICloudSyncRecord]

    public func validate() throws {
        guard format == "pasto-icloud-drive" else { throw ICloudDriveSyncError.invalidSnapshot }
        guard version == 1 else { throw ICloudDriveSyncError.incompatibleVersion }
        guard Set(records.map(\.key)).count == records.count else { throw ICloudDriveSyncError.invalidSnapshot }
        for record in records {
            guard record.revision.timestamp.timeIntervalSince1970.isFinite,
                  record.revision.sequence < UInt64.max else { throw ICloudDriveSyncError.invalidSnapshot }
            let parts = record.key.split(separator: ":", maxSplits: 1).map(String.init)
            guard parts.count == 2, let kind = ICloudSyncEntity.Kind(rawValue: parts[0]), !parts[1].isEmpty,
                  record.revision.deviceID == deviceID else { throw ICloudDriveSyncError.invalidSnapshot }
            if kind != .application, UUID(uuidString: parts[1])?.uuidString != parts[1] {
                throw ICloudDriveSyncError.invalidSnapshot
            }
            if let entity = record.entity {
                try entity.validate()
                guard entity.key == record.key else { throw ICloudDriveSyncError.invalidSnapshot }
            }
        }
    }
}

struct ICloudSyncStamp: Codable, Equatable {
    var revision: ICloudSyncRevision
    var digest: String?
}

/// Stored in the same locked, atomic transaction as the clipboard, never in exported archives.
struct ICloudSyncMetadata: Codable, Equatable {
    var deviceID = UUID()
    var clock: ICloudSyncRevision?
    var stamps: [String: ICloudSyncStamp] = [:]

    mutating func nextRevision(now: Date) throws -> ICloudSyncRevision {
        let sequence = clock?.sequence ?? 0
        guard sequence < UInt64.max - 1 else { throw ICloudDriveSyncError.clockExhausted }
        let revision = ICloudSyncRevision(timestamp: max(now, clock?.timestamp ?? .distantPast),
                                         sequence: sequence + 1, deviceID: deviceID)
        clock = revision
        return revision
    }

    mutating func observe(_ revision: ICloudSyncRevision) {
        if clock == nil || clock! < revision { clock = revision }
    }

    mutating func reconcile(_ entities: [String: ICloudSyncEntity], now: Date) throws {
        let isInitialSnapshot = stamps.isEmpty && clock == nil
        for key in entities.keys.sorted() {
            let digest = try entities[key]!.digest()
            if stamps[key]?.digest != digest {
                if isInitialSnapshot {
                    // Enabling sync on an old archive is not a new edit. Do not let its
                    // enable time overwrite newer changes already tracked by another Mac.
                    let date = entities[key]?.item?.updatedAt ?? Date(timeIntervalSince1970: 0)
                    let revision = ICloudSyncRevision(timestamp: date, sequence: 0, deviceID: deviceID)
                    observe(revision)
                    stamps[key] = ICloudSyncStamp(revision: revision, digest: digest)
                } else {
                    stamps[key] = try ICloudSyncStamp(revision: nextRevision(now: now), digest: digest)
                }
            }
        }
        for key in stamps.keys.sorted() where entities[key] == nil && stamps[key]?.digest != nil {
            stamps[key] = try ICloudSyncStamp(revision: nextRevision(now: now), digest: nil)
        }
    }
}

/// Each device owns one file; devices never race to replace the same iCloud document.
/// Blocking NSFileCoordinator work stays on this actor, away from the app's MainActor.
public actor ICloudDriveSyncTransport {
    public init() {}

    private func dataDirectory(in folder: URL) throws -> URL {
        var isDirectory: ObjCBool = false
        guard FileManager.default.fileExists(atPath: folder.path, isDirectory: &isDirectory), isDirectory.boolValue else {
            throw ICloudDriveSyncError.folderUnavailable
        }
        let directory = folder.appendingPathComponent("PastoSync-v1", isDirectory: true)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true,
                                                attributes: [.posixPermissions: 0o700])
        guard try directory.resourceValues(forKeys: [.isSymbolicLinkKey]).isSymbolicLink != true else {
            throw ICloudDriveSyncError.folderUnavailable
        }
        return directory
    }

    private func coordinate<T>(at url: URL, writing: Bool, _ body: (URL) throws -> T) throws -> T {
        let coordinator = NSFileCoordinator(filePresenter: nil)
        var coordinationError: NSError?
        var result: Result<T, Error>?
        let accessor: (URL) -> Void = { location in result = Result { try body(location) } }
        if writing {
            coordinator.coordinate(writingItemAt: url, options: .forReplacing, error: &coordinationError, byAccessor: accessor)
        } else {
            coordinator.coordinate(readingItemAt: url, options: [], error: &coordinationError, byAccessor: accessor)
        }
        if let coordinationError { throw coordinationError }
        guard let result else { throw ICloudDriveSyncError.folderUnavailable }
        return try result.get()
    }

    public func read(from folder: URL, excluding deviceID: UUID) throws -> [ICloudSyncSnapshot] {
        let directory = try dataDirectory(in: folder)
        let files = try FileManager.default.contentsOfDirectory(at: directory,
            includingPropertiesForKeys: [.isSymbolicLinkKey])
        var snapshots: [ICloudSyncSnapshot] = []
        for file in files.sorted(by: { $0.lastPathComponent < $1.lastPathComponent }) {
            // Finder can represent an evicted document as .<name>.icloud rather than <name>.
            // Request its download instead of silently ignoring all data on a new Mac.
            let name = file.lastPathComponent
            if name.hasPrefix("."), name.hasSuffix(".json.icloud") {
                let documentName = String(name.dropFirst().dropLast(".icloud".count))
                if UUID(uuidString: String(documentName.dropLast(".json".count))) != nil {
                    try FileManager.default.startDownloadingUbiquitousItem(at: directory.appendingPathComponent(documentName))
                    throw ICloudDriveSyncError.downloadPending
                }
            }
            guard file.pathExtension == "json" else { continue }
            guard let id = UUID(uuidString: file.deletingPathExtension().lastPathComponent) else { continue }
            if id == deviceID { continue }
            guard try file.resourceValues(forKeys: [.isSymbolicLinkKey]).isSymbolicLink != true else {
                throw ICloudDriveSyncError.invalidSnapshot
            }
            // Upload/account metadata can be unavailable while an ordinary, already-downloaded
            // iCloud Drive document remains readable (for example offline). Do not reject it.
            let values = try? file.resourceValues(forKeys: [.isUbiquitousItemKey, .ubiquitousItemDownloadingStatusKey])
            if values?.isUbiquitousItem == true,
               values?.ubiquitousItemDownloadingStatus == .notDownloaded {
                try FileManager.default.startDownloadingUbiquitousItem(at: file)
                throw ICloudDriveSyncError.downloadPending
            }
            let snapshot: ICloudSyncSnapshot = try coordinate(at: file, writing: false) {
                try JSONDecoder().decode(ICloudSyncSnapshot.self, from: Data(contentsOf: $0))
            }
            try snapshot.validate()
            guard snapshot.deviceID == id else { throw ICloudDriveSyncError.invalidSnapshot }
            snapshots.append(snapshot)
        }
        return snapshots
    }

    public func write(_ snapshot: ICloudSyncSnapshot, to folder: URL) throws {
        try snapshot.validate()
        let directory = try dataDirectory(in: folder)
        let file = directory.appendingPathComponent(snapshot.deviceID.uuidString + ".json")
        if FileManager.default.fileExists(atPath: file.path),
           try file.resourceValues(forKeys: [.isSymbolicLinkKey]).isSymbolicLink == true {
            throw ICloudDriveSyncError.invalidSnapshot
        }
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys]
        let data = try encoder.encode(snapshot)
        try coordinate(at: file, writing: true) { destination in
            // No-op sync must not rewrite a document and retrigger iCloud uploads.
            if let existing = try? Data(contentsOf: destination),
               let previous = try? JSONDecoder().decode(ICloudSyncSnapshot.self, from: existing), previous == snapshot { return }
            try data.write(to: destination, options: .atomic)
            try FileManager.default.setAttributes([.posixPermissions: 0o600], ofItemAtPath: destination.path)
        }
    }
}
