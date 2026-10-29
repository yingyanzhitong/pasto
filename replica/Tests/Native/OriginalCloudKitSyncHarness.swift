import CloudKit
import Foundation
import PastoCore

@main
struct OriginalCloudKitSyncHarness {
    struct Failure: Error { let message: String }
    static var checks: [String] = []
    static func check(_ condition: @autoclosure () throws -> Bool, _ name: String) throws {
        guard try condition() else { throw Failure(message: name) }
        checks.append(name)
    }
    static func rejects(_ name: String, _ operation: () throws -> Void) throws {
        do { try operation() } catch { checks.append(name); return }
        throw Failure(message: name)
    }
    static func sqlite(_ directory: URL, _ sql: String) throws {
        let process = Process(), output = Pipe()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/sqlite3")
        process.arguments = [directory.appendingPathComponent("clipboard.sqlite").path, sql]
        process.standardOutput = output; process.standardError = output
        try process.run()
        let data = output.fileHandleForReading.readDataToEndOfFile()
        process.waitUntilExit()
        guard process.terminationStatus == 0 else { throw Failure(message: String(decoding: data, as: UTF8.self)) }
    }
    @MainActor static func main() async {
        do { try await run() }
        catch { print("FAIL \(error)"); exit(1) }
    }
    @MainActor static func run() async throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent("PastoCloudKitTests-\(UUID().uuidString)")
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: root) }
        let assets = root.appendingPathComponent("assets")
        let id = OriginalCloudRecordID(name: UUID().uuidString)
        let parent = OriginalCloudRecordID(name: UUID().uuidString)
        let older = Date(timeIntervalSince1970: 1_000), newer = Date(timeIntervalSince1970: 2_000)
        var sample = OriginalCloudDocument(id: id, type: "ItemEntity", fields: ["identifier": .string(id.name),
            "updatedAt": .date(older), "timestamp": .date(older), "title": .string("旧内容"), "rawType": .integer(5),
            "rawPreview": .data(Data([1, 2, 3])), "list": .reference(parent, deleteSelf: false),
            "data": .reference(OriginalCloudRecordID(name: id.name + ".data"), deleteSelf: true)], parent: parent)
        let encoded = try OriginalCloudKitRecordCodec.encode(sample, assetDirectory: assets)
        let decoded = try OriginalCloudKitRecordCodec.decode(encoded, scope: .private)
        try check(decoded.hasSameContent(as: sample), "真实 CKRecord 字段往返")
        try check(encoded.parent?.recordID == parent.ckID, "父记录映射")
        try check((encoded["data"] as? CKRecord.Reference)?.action == .deleteSelf, "级联删除引用")
        try check((encoded["list"] as? CKRecord.Reference)?.action == CKRecord.ReferenceAction.none, "非级联引用")
        let system = OriginalCloudKitRecordCodec.systemFields(of: encoded)
        let restored = try OriginalCloudKitRecordCodec.restoreSystemFields(system)
        try check(restored.recordID == encoded.recordID && restored.recordType == encoded.recordType, "真实 CKRecord 系统字段归档")
        sample.systemFields = system
        try check(try OriginalCloudKitRecordCodec.encode(sample, assetDirectory: assets).recordID == encoded.recordID, "从系统字段重建发送记录")
        var cleared = decoded; cleared.fields.removeValue(forKey: "title")
        let clearedRecord = try OriginalCloudKitRecordCodec.encode(cleared, assetDirectory: assets)
        try check(clearedRecord["title"] == nil && clearedRecord.changedKeys().contains("title"), "清空可选字段显式标记服务器删除")
        let bytes = Data((0..<1_000_000).map { UInt8($0 % 251) })
        let assetDoc = OriginalCloudDocument(id: OriginalCloudRecordID(name: id.name + ".data"), type: "ItemDataEntity",
            fields: ["rawPasteboardItems": .asset(bytes), "item": .reference(id, deleteSelf: false)], parent: id)
        let assetRecord = try OriginalCloudKitRecordCodec.encode(assetDoc, assetDirectory: assets)
        try check(assetRecord["rawPasteboardItems"] is CKAsset, "外置二进制字段使用 CKAsset")
        try check(try OriginalCloudKitRecordCodec.decode(assetRecord, scope: .private).fields["rawPasteboardItems"]?.bytes == bytes, "百万字节 CKAsset 往返")
        let heldURL = (assetRecord["rawPasteboardItems"] as! CKAsset).fileURL!
        _ = try OriginalCloudKitRecordCodec.encode(assetDoc, assetDirectory: assets)
        try check(try Data(contentsOf: heldURL) == bytes, "重试期间附件文件保持有效")
        var invalid = sample; invalid.fields["identifier"] = .string("  ")
        try rejects("空白标识拒绝") { _ = try OriginalCloudKitRecordCodec.encode(invalid, assetDirectory: assets) }
        invalid = sample; invalid.type = "UnexpectedEntity"
        try rejects("未知记录类型拒绝") { _ = try OriginalCloudKitRecordCodec.encode(invalid, assetDirectory: assets) }
        invalid = sample; invalid.fields["updatedAt"] = .string("wrong type")
        try rejects("错误字段类型拒绝") { _ = try OriginalCloudKitRecordCodec.encode(invalid, assetDirectory: assets) }
        invalid = sample; invalid.fields["list"] = .reference(OriginalCloudRecordID(name: "bad", zone: "other"), deleteSelf: false)
        try rejects("跨区域错误引用拒绝") { _ = try OriginalCloudKitRecordCodec.encode(invalid, assetDirectory: assets) }
        try rejects("损坏系统字段拒绝") { _ = try OriginalCloudKitRecordCodec.restoreSystemFields(Data("corrupt".utf8)) }
        var client = sample; client.fields["updatedAt"] = .date(newer); client.fields["title"] = .string("新内容")
        let merged = try OriginalCloudKitConflictResolver.resolve(client: client, server: decoded)
        try check(merged.fields["title"]?.string == "新内容", "严格较新客户端字段胜出")
        try check(merged.systemFields == decoded.systemFields, "冲突保留服务器系统字段")
        var moved = client; moved.parent = OriginalCloudRecordID(name: "moved-list")
        moved.fields["list"] = .reference(moved.parent!, deleteSelf: false)
        try check(try OriginalCloudKitConflictResolver.resolve(client: moved, server: decoded).parent == moved.parent, "冲突后父关系与较新分组字段一致")
        client.fields["updatedAt"] = .date(older)
        try check(try OriginalCloudKitConflictResolver.resolve(client: client, server: decoded).fields["title"]?.string == "旧内容", "同时间服务器胜出")
        client.fields["updatedAt"] = .date(newer); client.fields["identifier"] = .string("不能替换")
        try check(try OriginalCloudKitConflictResolver.resolve(client: client, server: decoded).fields["identifier"] == decoded.fields["identifier"], "业务标识不被冲突覆盖")
        var changedAsset = assetDoc; changedAsset.fields["rawPasteboardItems"] = .asset(Data([9, 9]))
        try rejects("未闭合的附件冲突暂停而不丢弃本机编辑") { _ = try OriginalCloudKitConflictResolver.resolve(client: changedAsset, server: assetDoc) }
        var imageClient = sample; imageClient.fields["rawType"] = .integer(1); imageClient.fields["updatedAt"] = .date(newer)
        var imageServer = sample; imageServer.fields["rawType"] = .integer(1)
        try rejects("未闭合的图片冲突暂停而不套用 clipboard 分支") { _ = try OriginalCloudKitConflictResolver.resolve(client: imageClient, server: imageServer) }
        func clipboard(_ capacity: Int) throws -> OriginalCloudDocument {
            OriginalCloudDocument(id: parent, type: "ListEntity", fields: ["identifier": .string(parent.name), "rawType": .integer(1),
                "updatedAt": .date(newer), "rawAttributes": .data(try JSONSerialization.data(withJSONObject: ["type": "clipboard", "capacity": capacity]))])
        }
        let limited = try clipboard(7), unlimited = try clipboard(0), larger = try clipboard(30)
        try check(try OriginalCloudKitConflictResolver.resolve(client: limited, server: unlimited).fields["rawAttributes"] == limited.fields["rawAttributes"], "正数容量优先于无限容量")
        try check(try OriginalCloudKitConflictResolver.resolve(client: unlimited, server: limited).fields["rawAttributes"] == limited.fields["rawAttributes"], "无限容量不覆盖已有上限")
        try check(try OriginalCloudKitConflictResolver.resolve(client: larger, server: limited).fields["rawAttributes"] == limited.fields["rawAttributes"], "容量选择较小正数")

        var journal = OriginalCloudKitJournal()
        try journal.capture([sample, try clipboard(30)])
        try check(journal.eligible(scope: .private).isEmpty, "首次拉取前禁止发送本地记录")
        try check(!journal.deletedZone(parent.ckID.zoneID, scope: .private), "首次拉取忽略历史区域删除")
        journal.finishedInitialFetch(scope: .private)
        try check(journal.eligible(scope: .private).count == 1, "未确认父记录的子项保持待发送")
        let parentPending = journal.pending[OriginalCloudKitJournal.key(parent, scope: .private)]!
        let parentServer = try OriginalCloudKitRecordCodec.decode(OriginalCloudKitRecordCodec.encode(clipboard(30), assetDirectory: assets), scope: .private)
        try journal.acknowledged(parentServer, generation: parentPending.generation)
        try check(journal.eligible(scope: .private).count == 1 && journal.eligible(scope: .private).first?.id == id, "父记录确认后释放子项")
        let sent = journal.pending[OriginalCloudKitJournal.key(id, scope: .private)]!
        var edited = sample; edited.fields["title"] = .string("发送中再次修改"); edited.fields["updatedAt"] = .date(newer)
        try journal.capture([edited, parentServer])
        try journal.acknowledged(decoded, generation: sent.generation)
        try check(journal.pending[OriginalCloudKitJournal.key(id, scope: .private)] != nil && journal.documents[OriginalCloudKitJournal.key(id, scope: .private)]?.fields["title"]?.string == "发送中再次修改", "旧发送回执不吞掉新编辑")
        try journal.capture([parentServer])
        try journal.received([decoded], deleted: [], scope: .private)
        try check(journal.documents[OriginalCloudKitJournal.key(id, scope: .private)] == nil, "旧拉取不复活待删除记录")
        try check(journal.eligible(scope: .shared).isEmpty, "私有和共享作用域隔离")
        journal.resetAccount()
        try check(journal.serializations.isEmpty && journal.confirmed.isEmpty && journal.accountConfirmationRequired, "账户变更清理令牌并要求重新确认")
        try check(journal.eligible(scope: .private).isEmpty && !journal.documents.isEmpty, "账户退出保留内容并停止发送")
        try check(try JSONDecoder().decode(OriginalCloudKitJournal.self, from: JSONEncoder().encode(journal)) == journal, "同步日志可持久化恢复")
        for code in [CKError.Code.networkFailure, .requestRateLimited, .zoneBusy, .notAuthenticated] {
            try check(OriginalCloudKitRetryPolicy.action(for: code, isPrivate: true) == .retry, "可重试错误 \(code.rawValue)")
        }
        try check(OriginalCloudKitRetryPolicy.action(for: .serverRecordChanged, isPrivate: true) == .mergeServer, "服务器冲突进入合并路径")
        try check(OriginalCloudKitRetryPolicy.action(for: .zoneNotFound, isPrivate: true) == .recreateZone, "私有区域丢失进入重建路径")
        try check(OriginalCloudKitRetryPolicy.action(for: .unknownItem, isPrivate: true) == .recreateRecord, "服务器记录丢失清除旧版本")
        try rejects("无有效签名时不初始化容器") { _ = try PastoCloudKitConfiguration.current() }
        let bundle = "local.pasto.cloudkit-tests", container = "iCloud.local.pasto.tests"
        var entitlements: [String: Any] = ["com.apple.developer.icloud-container-identifiers": [container], "com.apple.developer.icloud-services": ["CloudKit"],
            "com.apple.developer.team-identifier": "TESTTEAM01", "com.apple.application-identifier": "TESTTEAM01.\(bundle)", "com.apple.developer.icloud-container-environment": "Development"]
        try check(try PastoCloudKitConfiguration.validate(container: container, bundleIdentifier: bundle, entitlements: entitlements).containerIdentifier == container, "合法自有配置校验")
        entitlements["com.apple.developer.icloud-container-identifiers"] = ["iCloud.com.wiheads.paste"]
        try rejects("原版厂商容器不可复用") { _ = try PastoCloudKitConfiguration.validate(container: "iCloud.com.wiheads.paste", bundleIdentifier: bundle, entitlements: entitlements) }

        let a = try ClipboardStore(directoryURL: root.appendingPathComponent("a"))
        let b = try ClipboardStore(directoryURL: root.appendingPathComponent("b"))
        a.preferences.historyRetentionDays = 0; b.preferences.historyRetentionDays = 0
        b.preferences.excludedBundleIDs = ["local.b.only"]
        let board = try a.createPinboard(name: "云端分组 👋", colorHex: "#12AB89")
        let empty = try a.createPinboard(name: "空分组")
        let application = SourceApplicationRecord(bundleIdentifier: "local.source", name: "测试来源", rawIcon: nil, rawColor: 123)
        let itemID = try a.add(ClipboardItem(title: "云端内容", plainText: "中文 é", sourceBundleID: application.bundleIdentifier,
            payloads: ["public.utf8-plain-text": Data("中文 é".utf8), "local.binary": bytes], pinboardIDs: [board.id],
            pinboardOrder: 7, pinboardOwnerID: board.id), sourceApplication: application)
        var server: [String: OriginalCloudDocument] = [:]
        func push(_ store: ClipboardStore) throws {
            _ = try store.cloudKitTransaction { $0.finishedInitialFetch(scope: .private) }
            for _ in 0..<10 {
                let changes = try store.prepareCloudKit().eligible(scope: .private)
                if changes.isEmpty { return }
                for change in changes {
                    let key = OriginalCloudKitJournal.key(change.id, scope: change.scope)
                    if change.deletion {
                        server.removeValue(forKey: key)
                        _ = try store.cloudKitTransaction { $0.acknowledgedDeletion(change) }
                    } else {
                        let document = try store.prepareCloudKit().documents[key]!
                        let value = try OriginalCloudKitRecordCodec.decode(OriginalCloudKitRecordCodec.encode(document, assetDirectory: assets), scope: .private)
                        server[key] = value
                        _ = try store.cloudKitTransaction { try $0.acknowledged(value, generation: change.generation) }
                    }
                }
            }
            throw Failure(message: "父子发送队列未收敛")
        }
        try push(a)
        try check(try a.prepareCloudKit().pending.isEmpty, "六类实体经真实 SDK 编解码后发送队列收敛")
        try check(Set(server.values.map(\.type)) == OriginalCloudKitSchema.recordTypes, "原版六类业务实体完整覆盖")
        _ = try b.cloudKitTransaction(project: true) { try $0.received(Array(server.values), deleted: [], scope: .private); $0.finishedInitialFetch(scope: .private) }
        try check(b.pinboards.contains(where: { $0.id == empty.id }), "远端空分组投影")
        try check(b.pinboards.first(where: { $0.id == board.id })?.colorHex == "#12AB89", "远端分组颜色投影")
        try check(b.items.first(where: { $0.id == itemID })?.plainText == "中文 é", "远端中文文本投影")
        if let item = b.items.first(where: { $0.id == itemID }) {
            let values = try ClipboardStore.originalPasteboardItems(from: item.payloads)
            try check(values.first?.f_10037d810(forType: "local.binary") == bytes, "内容附件字节完整")
        } else { throw Failure(message: "远端内容缺失") }
        try check(b.items.first(where: { $0.id == itemID })?.pinboardOrder == 7, "远端分组内顺序投影")
        try check(b.sourceApplications.contains(application), "来源应用实体投影")
        try check(b.preferences.excludedBundleIDs == ["local.b.only"], "本机隐私偏好不被同步覆盖")
        let stable = try b.prepareCloudKit(), again = try b.prepareCloudKit()
        try check(stable == again, "无变更不制造新发送记录")
        let bState = b.directoryURL.appendingPathComponent("clipboard.sqlite-wal")
        let beforeFailure = try Data(contentsOf: bState)
        let unusable = OriginalCloudDocument(id: OriginalCloudRecordID(name: "invalid"), type: "NoSuchEntity", fields: [:])
        try rejects("错误远端事务不保存令牌或部分内容") {
            _ = try b.cloudKitTransaction(project: true) {
                $0.serializations["2"] = Data("must not be committed".utf8)
                try $0.received([unusable], deleted: [], scope: .private)
            }
        }
        try check(try Data(contentsOf: bState) == beforeFailure, "失败事务保留磁盘原字节")
        try sqlite(b.directoryURL, "CREATE TRIGGER reject_checkpoint BEFORE UPDATE ON ZSTATE BEGIN SELECT RAISE(ABORT,'synthetic checkpoint failure'); END;")
        let beforeSaveFailure = try Data(contentsOf: bState)
        do {
            try rejects("磁盘不可写时拒绝推进引擎检查点") {
                _ = try b.cloudKitTransaction { $0.serializations["2"] = Data("not persisted".utf8) }
            }
        } catch {
            try sqlite(b.directoryURL, "DROP TRIGGER reject_checkpoint;")
            throw error
        }
        try check(try Data(contentsOf: bState) == beforeSaveFailure && b.prepareCloudKit().serializations == again.serializations, "磁盘失败不发布内存检查点")
        try sqlite(b.directoryURL, "DROP TRIGGER reject_checkpoint;")
        let reopened = try ClipboardStore(directoryURL: b.directoryURL)
        try check(try reopened.prepareCloudKit() == again, "重启恢复记录与待发送状态")
        let archive = root.appendingPathComponent("export.json")
        try b.exportArchive(to: archive)
        let archiveObject = try JSONSerialization.jsonObject(with: Data(contentsOf: archive)) as! [String: Any]
        try check(archiveObject["cloudKitJournal"] == nil, "导出不携带账户和同步令牌")
        let deletedID = OriginalCloudRecordID(name: itemID.uuidString)
        _ = try b.cloudKitTransaction(project: true) { try $0.received([], deleted: [deletedID], scope: .private) }
        try check(!b.items.contains(where: { $0.id == itemID }), "远端删除投影到本地")
        let orphan = try ClipboardStore(directoryURL: root.appendingPathComponent("orphan"))
        _ = try orphan.cloudKitTransaction(project: true) { try $0.received([decoded], deleted: [], scope: .private) }
        try check(orphan.items.isEmpty && (try orphan.prepareCloudKit().documents.values.contains(where: { $0.id == decoded.id })), "引用未到齐暂存而不创建空内容")
        let outOfOrder = try ClipboardStore(directoryURL: root.appendingPathComponent("out-of-order"))
        let originalItem = server.values.first { $0.type == "ItemEntity" }!
        _ = try outOfOrder.cloudKitTransaction(project: true) { try $0.received([originalItem], deleted: [], scope: .private) }
        try check(outOfOrder.items.isEmpty, "乱序到达先暂存内容引用")
        _ = try outOfOrder.cloudKitTransaction(project: true) { try $0.received(Array(server.values), deleted: [], scope: .private) }
        try check(outOfOrder.items.contains(where: { $0.id == itemID }), "附件和关系到齐后恢复内容")
        let updateIndex = a.items.firstIndex(where: { $0.id == itemID })!
        a.items[updateIndex].title = "发送后的新标题"; a.items[updateIndex].updatedAt = Date().addingTimeInterval(5)
        try a.save(); try push(a)
        _ = try outOfOrder.cloudKitTransaction(project: true) { try $0.received(Array(server.values), deleted: [], scope: .private) }
        try check(outOfOrder.items.first(where: { $0.id == itemID })?.title == "发送后的新标题", "后续编辑经原版记录字段传播")
        _ = try a.cloudKitTransaction { $0.resetAccount() }
        try check(a.items.contains(where: { $0.id == itemID }) && a.pinboards.contains(where: { $0.id == board.id }), "账户退出不删除本机历史分组")
        let data = try JSONSerialization.data(withJSONObject: ["passed": true, "checks": checks.count, "cases": checks,
            "transport": "real CKRecord/CKAsset with isolated in-memory server; no CKContainer/network", "liveCloudKitTested": false], options: [.prettyPrinted, .sortedKeys])
        print(String(decoding: data, as: UTF8.self))
    }
}
