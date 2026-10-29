import AppKit
import Foundation
import PastoCore

@main
struct ICloudDriveSyncHarness {
    struct Failure: Error { var message: String }
    static var checks = 0
    static func check(_ value: @autoclosure () throws -> Bool, _ message: String) throws {
        if try !value() { throw Failure(message: message) }
        checks += 1
    }

    @MainActor static func main() async {
        do { try await run() }
        catch {
            let data = try! JSONSerialization.data(withJSONObject: ["passed": false, "error": String(describing: error)])
            print(String(decoding: data, as: UTF8.self)); exit(1)
        }
    }

    @MainActor static func run() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent("PastoSyncTests-\(UUID().uuidString)")
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: root) }
        let folder = root.appendingPathComponent("shared", isDirectory: true)
        try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
        let a = try ClipboardStore(directoryURL: root.appendingPathComponent("a"))
        let b = try ClipboardStore(directoryURL: root.appendingPathComponent("b"))
        a.preferences.historyRetentionDays = 0; b.preferences.historyRetentionDays = 0
        a.preferences.excludedBundleIDs = ["local.a"]; b.preferences.excludedBundleIDs = ["local.b"]
        let board = try a.createPinboard(name: "工作 🧩", colorHex: "#12AB89")
        let empty = try a.createPinboard(name: "空分组")
        let application = SourceApplicationRecord(bundleIdentifier: "local.test.source", name: "测试来源", rawIcon: nil, rawColor: 123)
        let bytes = Data((0..<500_000).map { UInt8($0 % 251) })
        let id = try a.add(ClipboardItem(title: "原文 👋", plainText: "中文 é", sourceBundleID: application.bundleIdentifier,
            payloads: ["public.utf8-plain-text": Data("中文 é".utf8), "local.test.binary": bytes],
            pinboardIDs: [board.id], pinboardOrder: 7, pinboardOwnerID: board.id), sourceApplication: application)
        let bID = try b.add(ClipboardItem(title: "B 的内容", plainText: "来自 B"))
        let transport = ICloudDriveSyncTransport()
        let start = Date()
        func instant(_ seconds: TimeInterval) -> Date { start.addingTimeInterval(seconds) }
        func round(_ store: ClipboardStore, at time: Date) async throws -> ICloudSyncSnapshot {
            let local = try store.prepareICloudSync(now: time)
            let incoming = try await transport.read(from: folder, excluding: local.deviceID)
            let result = try store.applyICloudSync(incoming, now: time)
            try await transport.write(result, to: folder)
            return result
        }
        let aFirst = try await round(a, at: instant(1))
        let bFirst = try await round(b, at: instant(2))
        try check(aFirst.deviceID != bFirst.deviceID, "Devices share an identity")
        try check(Set(b.items.map(\.id)) == [id, bID], "Initial merge lost history")
        try check(b.items.first(where: { $0.id == id })?.payloads["local.test.binary"] == bytes, "Raw bytes changed")
        try check(b.pinboards.contains(where: { $0.id == empty.id }), "Empty group missing")
        try check(b.pinboards.first(where: { $0.id == board.id })?.colorHex == "#12AB89", "Color changed")
        try check(b.pinboards.map(\.id) == a.pinboards.map(\.id), "Group ordering changed")
        try check(b.items.first(where: { $0.id == id })?.pinboardOrder == 7, "Member ordering changed")
        try check(b.sourceApplications.contains(application), "Source application missing")
        try check(b.preferences.excludedBundleIDs == ["local.b"], "Overwrote local privacy settings")
        let encoded = String(decoding: try JSONEncoder().encode(aFirst), as: UTF8.self)
        try check(!encoded.contains("excludedBundleIDs") && !encoded.contains("historyShortcut"), "Preferences leaked")
        _ = try await round(a, at: instant(3))
        try check(a.items.contains(where: { $0.id == bID }), "B item missing on A")
        let stable = try a.prepareICloudSync(now: instant(4))
        let again = try a.prepareICloudSync(now: instant(5))
        try check(stable == again, "No-op generated new revisions")
        let ownFile = folder.appendingPathComponent("PastoSync-v1/\(stable.deviceID.uuidString).json")
        let modification = try ownFile.resourceValues(forKeys: [.contentModificationDateKey]).contentModificationDate
        try await transport.write(again, to: folder)
        try check(try ownFile.resourceValues(forKeys: [.contentModificationDateKey]).contentModificationDate == modification, "No-op rewrote cloud file")
        let oldArchive = root.appendingPathComponent("old-archive.json")
        try a.exportArchive(to: oldArchive)
        let delayed = try ClipboardStore(directoryURL: root.appendingPathComponent("delayed-device"))
        try delayed.importArchive(from: oldArchive)

        a.items[a.items.firstIndex(where: { $0.id == id })!].title = "A 的修改"
        b.items[b.items.firstIndex(where: { $0.id == bID })!].title = "B 的修改"
        try a.save(); try b.save()
        try a.renamePinboard(id: board.id, name: "最新分组")
        let editA = try a.prepareICloudSync(now: instant(10))
        let editB = try b.prepareICloudSync(now: instant(10))
        _ = try a.applyICloudSync([editB], now: instant(11))
        _ = try b.applyICloudSync([editA], now: instant(11))
        try check(a.items.first(where: { $0.id == bID })?.title == "B 的修改", "Lost independent B edit")
        try check(b.items.first(where: { $0.id == id })?.title == "A 的修改", "Lost independent A edit")
        _ = try a.applyICloudSync([delayed.prepareICloudSync(now: instant(100))], now: instant(12))
        try check(a.items.first(where: { $0.id == id })?.title == "A 的修改", "Late enable overwrote a newer item")
        try check(a.pinboards.first(where: { $0.id == board.id })?.name == "最新分组", "Late enable overwrote a renamed group")
        a.items[a.items.firstIndex(where: { $0.id == id })!].title = "版本 A"
        b.items[b.items.firstIndex(where: { $0.id == id })!].title = "版本 B"
        try a.save(); try b.save()
        let conflictA = try a.prepareICloudSync(now: instant(20))
        let conflictB = try b.prepareICloudSync(now: instant(20))
        _ = try a.applyICloudSync([conflictB, conflictA], now: instant(21))
        _ = try b.applyICloudSync([conflictA, conflictB], now: instant(21))
        try check(a.items.first(where: { $0.id == id }) == b.items.first(where: { $0.id == id }), "Conflict did not converge")
        try a.permanentlyDelete(ids: [id])
        let deletion = try a.prepareICloudSync(now: instant(30))
        _ = try b.applyICloudSync([deletion, conflictA, conflictB], now: instant(31))
        try check(!b.items.contains(where: { $0.id == id }), "Stale file resurrected a deletion")
        let reopened = try ClipboardStore(directoryURL: b.directoryURL)
        _ = try reopened.applyICloudSync([aFirst, conflictA], now: instant(32))
        try check(!reopened.items.contains(where: { $0.id == id }), "Restart lost deletion tombstone")

        let member = try b.add(ClipboardItem(title: "保留成员", plainText: "成员", pinboardIDs: [board.id], pinboardOwnerID: board.id))
        _ = try a.applyICloudSync([b.prepareICloudSync(now: instant(35))], now: instant(36))
        try a.removePinboard(id: board.id)
        _ = try b.applyICloudSync([a.prepareICloudSync(now: instant(40))], now: instant(41))
        try check(!b.pinboards.contains(where: { $0.id == board.id }), "Group deletion missing")
        try check(b.items.first(where: { $0.id == member })?.pinboardIDs.isEmpty == true, "Dangling membership")
        let otherProcess = try ClipboardStore(directoryURL: b.directoryURL)
        let concurrentID = try otherProcess.add(ClipboardItem(title: "进程写入", plainText: "不丢失"))
        _ = try b.applyICloudSync([], now: instant(42))
        try check(b.items.contains(where: { $0.id == concurrentID }), "Lost concurrent process write")
        let before = b.items
        var invalid = deletion; invalid.records += invalid.records
        do { _ = try b.applyICloudSync([invalid]); throw Failure(message: "Accepted duplicate records") }
        catch is ICloudDriveSyncError { checks += 1 }
        try check(b.items == before, "Invalid input partially modified data")
        var future = deletion; future.version = 999
        do { _ = try b.applyICloudSync([future]); throw Failure(message: "Accepted future schema") }
        catch is ICloudDriveSyncError { checks += 1 }
        let corrupt = folder.appendingPathComponent("PastoSync-v1/\(UUID().uuidString).json")
        try Data("{broken".utf8).write(to: corrupt)
        do { _ = try await transport.read(from: folder, excluding: bFirst.deviceID); throw Failure(message: "Accepted corrupt file") }
        catch is DecodingError { checks += 1 }
        try check(b.items == before, "Corrupt document erased local data")
        let archive = root.appendingPathComponent("archive.json")
        try b.exportArchive(to: archive)
        let object = try JSONSerialization.jsonObject(with: Data(contentsOf: archive)) as! [String: Any]
        try check(object["cloudSyncMetadata"] == nil, "Identity leaked into archive")
        let imported = try ClipboardStore(directoryURL: root.appendingPathComponent("imported"))
        try imported.importArchive(from: archive)
        let importedSnapshot = try imported.prepareICloudSync()
        try check(importedSnapshot.deviceID != bFirst.deviceID, "Archive cloned device identity")
        try imported.resetICloudSyncIdentity()
        let reset = try imported.prepareICloudSync()
        try check(reset.deviceID != importedSnapshot.deviceID && !reset.records.isEmpty, "Folder change failed to republish")
        do { try await transport.write(reset, to: root.appendingPathComponent("unavailable")); throw Failure(message: "Recreated missing folder") }
        catch is ICloudDriveSyncError { checks += 1 }
        let linked = root.appendingPathComponent("linked", isDirectory: true)
        try FileManager.default.createDirectory(at: linked, withIntermediateDirectories: true)
        try FileManager.default.createSymbolicLink(at: linked.appendingPathComponent("PastoSync-v1"),
            withDestinationURL: folder.appendingPathComponent("PastoSync-v1"))
        do { try await transport.write(reset, to: linked); throw Failure(message: "Accepted a linked data directory") }
        catch is ICloudDriveSyncError { checks += 1 }
        let cachedStore = try ClipboardStore(directoryURL: root.appendingPathComponent("digest-cache"))
        let cachedID = try cachedStore.add(ClipboardItem(plainText: "cache", payloads: ["local.binary": bytes]))
        let originalDigest = try cachedStore.prepareICloudSync()
        try check(try cachedStore.prepareICloudSync() == originalDigest, "Warm digest cache changed the snapshot")
        cachedStore.items[cachedStore.items.firstIndex { $0.id == cachedID }!].payloads["local.binary"] = Data([9, 8, 7])
        try cachedStore.save()
        let changedDigest = try cachedStore.prepareICloudSync()
        try check(changedDigest != originalDigest, "Payload change did not invalidate digest cache")
        let uncached = try ClipboardStore(directoryURL: cachedStore.directoryURL)
        try check(try uncached.prepareICloudSync() == changedDigest, "Cached digest differs from cold encoding after reopen")
        let cancelFolder = root.appendingPathComponent("cancelled-transport")
        try FileManager.default.createDirectory(at: cancelFolder, withIntermediateDirectories: true)
        let cancelled = Task { try await transport.write(changedDigest, to: cancelFolder) }
        cancelled.cancel()
        do { try await cancelled.value; throw Failure(message: "Cancelled write continued") }
        catch is CancellationError { checks += 1 }
        try check(!FileManager.default.fileExists(atPath: cancelFolder.appendingPathComponent("PastoSync-v1").path), "Cancelled write created a data directory")
        print("{\"passed\":true,\"checks\":\(checks),\"isolated_devices\":2,\"real_icloud_accessed\":false,\"general_pasteboard_accessed\":false}")
    }
}
