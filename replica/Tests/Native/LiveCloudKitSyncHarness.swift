import CloudKit
import Foundation
import PastoCore

/// Explicitly signed test process, separate temporary stores and an allowlisted random zone.
/// No system pasteboard, installed application's store, or existing cloud record zone is opened.
@main
struct LiveCloudKitSyncHarness {
    struct Failure: Error { let message: String }
    @MainActor static func main() async {
        guard ProcessInfo.processInfo.environment["PASTO_CLOUDKIT_ALLOW_LIVE_TEST"] == "1" else {
            print("BLOCKED: 必须显式启用合成数据 CloudKit 测试。 "); exit(2)
        }
        do { try await run() }
        catch { print("FAIL: \(error)"); exit(1) }
    }
    @MainActor static func run() async throws {
        let configuration = try PastoCloudKitConfiguration.current()
        guard configuration.environment == "Development" else { throw Failure(message: "真实探针只允许开发环境") }
        let root = FileManager.default.temporaryDirectory.appendingPathComponent("PastoCloudKitLive-\(UUID().uuidString)")
        defer { try? FileManager.default.removeItem(at: root) }
        let zoneName = "Pasto-Verification-\(UUID().uuidString)"
        let database = CKContainer(identifier: configuration.containerIdentifier).privateCloudDatabase
        let a = try ClipboardStore(directoryURL: root.appendingPathComponent("a"))
        let b = try ClipboardStore(directoryURL: root.appendingPathComponent("b"))
        a.preferences.historyRetentionDays = 0; b.preferences.historyRetentionDays = 0
        _ = try a.prepareCloudKit(zoneName: zoneName); _ = try b.prepareCloudKit(zoneName: zoneName)
        _ = try a.cloudKitTransaction { $0.deviceName = "Pasto synthetic client A" }
        _ = try b.cloudKitTransaction { $0.deviceName = "Pasto synthetic client B" }
        let first = OriginalCloudKitSyncEngine(store: a, configuration: configuration, zoneName: zoneName)
        let second = OriginalCloudKitSyncEngine(store: b, configuration: configuration, zoneName: zoneName)
        var testError: Error?
        do {
            let board = try a.createPinboard(name: "Pasto CloudKit 合成分组", colorHex: "#12AB89")
            let bytes = Data((0..<200_000).map { UInt8($0 % 251) })
            let id = try a.add(ClipboardItem(title: "CloudKit 合成内容", plainText: "Pasto cloud verification",
                payloads: ["public.utf8-plain-text": Data("Pasto cloud verification".utf8), "local.pasto.synthetic": bytes],
                pinboardIDs: [board.id], pinboardOwnerID: board.id))
            try await first.start(); try await first.synchronize()
            try await second.start(); try await second.synchronize()
            guard let received = b.items.first(where: { $0.id == id }), b.pinboards.contains(where: { $0.id == board.id }),
                  try ClipboardStore.originalPasteboardItems(from: received.payloads).first?.f_10037d810(forType: "local.pasto.synthetic") == bytes else {
                throw Failure(message: "真实服务端传输或附件回验失败")
            }
            let index = b.items.firstIndex(where: { $0.id == id })!
            b.items[index].title = "CloudKit 更新验证"; b.items[index].updatedAt = Date(); try b.save()
            try await second.synchronize(); try await first.synchronize()
            guard a.items.first(where: { $0.id == id })?.title == "CloudKit 更新验证" else { throw Failure(message: "真实更新回验失败") }
            b.items.removeAll { $0.id == id }; try b.save()
            try await second.synchronize(); try await first.synchronize()
            guard !a.items.contains(where: { $0.id == id }) else { throw Failure(message: "真实删除回验失败") }
        } catch { testError = error }
        await first.stop(); await second.stop()
        do { _ = try await database.deleteRecordZone(withID: CKRecordZone.ID(zoneName: zoneName)) }
        catch let error as CKError where error.code == .zoneNotFound || error.code == .unknownItem { }
        catch { throw Failure(message: "测试区域清理失败：\(zoneName)，\(error.localizedDescription)") }
        do { _ = try await database.deleteSubscription(withID: "\(zoneName).2") }
        catch let error as CKError where error.code == .unknownItem { }
        catch { throw Failure(message: "测试订阅清理失败：\(zoneName).2，\(error.localizedDescription)") }
        if let testError { throw testError }
        print("{\"passed\":true,\"actualCloudKitService\":true,\"clients\":2,\"physicalMacs\":1,\"syntheticOnly\":true,\"zoneCleaned\":true}")
    }
}
