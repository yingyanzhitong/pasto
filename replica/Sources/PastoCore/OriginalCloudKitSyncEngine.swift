import CloudKit
import Foundation

/// Production CloudKit transport reconstructed from the original private/shared CKSyncEngine
/// call chain. It sends individual typed CKRecords and CKAssets, never an opaque archive blob.
@MainActor
public final class OriginalCloudKitSyncEngine: CKSyncEngineDelegate {
    public private(set) var isRunning = false
    public private(set) var lastError: String?
    public var statusChanged: (@MainActor (String) -> Void)?
    private let store: ClipboardStore
    private let configuration: PastoCloudKitConfiguration
    private let zoneName: String
    private var verificationOnly: Bool { zoneName.hasPrefix("Pasto-Verification-") }
    private var scopes: [OriginalCloudKitScope] { verificationOnly ? [.private] : OriginalCloudKitScope.allCases }
    private var engines: [OriginalCloudKitScope: CKSyncEngine] = [:]
    private var inFlight: [String: OriginalCloudKitJournal.Pending] = [:]
    private var generation = UUID()
    private var fetchingFailures: Set<OriginalCloudKitScope> = []

    public init(store: ClipboardStore, configuration: PastoCloudKitConfiguration, zoneName: String = "Pasto") {
        self.store = store; self.configuration = configuration; self.zoneName = zoneName
    }

    public func start() async throws {
        guard !isRunning else { return }
        // Configuration can only be obtained by validating this process's signing entitlements.
        let signed = try PastoCloudKitConfiguration.current()
        guard signed.containerIdentifier == configuration.containerIdentifier,
              signed.teamIdentifier == configuration.teamIdentifier,
              signed.environment == configuration.environment else { throw PastoCloudKitError.unconfigured }
        guard zoneName == "Pasto" || verificationOnly else { throw PastoCloudKitError.invalidRecord }
        _ = try store.prepareCloudKit(zoneName: zoneName)
        var journal = try store.cloudKitTransaction { $0.resumeAccount() }
        let container = CKContainer(identifier: configuration.containerIdentifier)
        generation = UUID(); isRunning = true; lastError = nil
        for scope in scopes {
            let serialized = journal.serializations[String(scope.rawValue)]
            let restored = serialized.flatMap { try? JSONDecoder().decode(CKSyncEngine.State.Serialization.self, from: $0) }
            if serialized != nil && restored == nil {
                journal = try store.cloudKitTransaction {
                    $0.serializations.removeValue(forKey: String(scope.rawValue))
                    $0.fetchedScopes.remove(String(scope.rawValue))
                }
            }
            var config = CKSyncEngine.Configuration(database: scope == .private ? container.privateCloudDatabase : container.sharedCloudDatabase,
                stateSerialization: restored, delegate: self)
            // First fetch must finish before local-only records are seeded. After bootstrap the
            // engine is recreated with automatic sync, matching original app vs extension policy.
            config.automaticallySync = !verificationOnly && journal.fetchedScopes.contains(String(scope.rawValue)) && !Bundle.main.bundlePath.hasSuffix(".appex")
            config.subscriptionID = "\(zoneName).\(scope.rawValue)"
            let engine = CKSyncEngine(config); engines[scope] = engine
            if scope == .private, restored == nil {
                engine.state.add(pendingDatabaseChanges: [.saveZone(CKRecordZone(zoneName: zoneName))])
            }
            enqueue(journal, engine: engine, scope: scope)
        }
        statusChanged?("CloudKit 已启动，正在拉取云端变更。")
    }

    public func stop() async {
        isRunning = false; generation = UUID()
        let previous = Array(engines.values); engines.removeAll(); inFlight.removeAll()
        for engine in previous { await engine.cancelOperations() }
    }

    public func synchronize() async throws {
        guard isRunning else { throw PastoCloudKitError.unconfigured }
        lastError = nil
        let token = generation
        for scope in scopes {
            guard let engine = engines[scope] else { continue }
            let initial = try !store.prepareCloudKit().fetchedScopes.contains(String(scope.rawValue))
            fetchingFailures.remove(scope)
            if initial && scope == .private { try await engine.sendChanges() }
            try await engine.fetchChanges(fetchOptions(scope: scope))
            guard token == generation, isRunning else { throw CancellationError() }
            guard !fetchingFailures.contains(scope) else { throw PastoCloudKitError.persistenceFailed }
            let journal = try store.cloudKitTransaction { $0.finishedInitialFetch(scope: scope) }
            enqueue(journal, engine: engine, scope: scope)
            // Parent acknowledgements unblock children in later batches. Repeated sendChanges
            // advances those batches without treating a deferred child as a successful send.
            while !journal.accountConfirmationRequired {
                let next = try store.prepareCloudKit()
                guard !next.eligible(scope: scope).isEmpty else { break }
                enqueue(next, engine: engine, scope: scope)
                let before = next.pending
                try await engine.sendChanges()
                guard token == generation, isRunning else { throw CancellationError() }
                if try store.prepareCloudKit().pending == before { break }
            }
            if initial, isRunning, !verificationOnly {
                // Reuse serialized progress and requeue the durable journal on automatic engine.
                await engine.cancelOperations()
                guard token == generation, isRunning else { throw CancellationError() }
                let latest = try store.prepareCloudKit()
                let serialized = latest.serializations[String(scope.rawValue)].flatMap { try? JSONDecoder().decode(CKSyncEngine.State.Serialization.self, from: $0) }
                var config = CKSyncEngine.Configuration(database: engine.database, stateSerialization: serialized, delegate: self)
                config.automaticallySync = !Bundle.main.bundlePath.hasSuffix(".appex")
                config.subscriptionID = "Pasto.\(scope.rawValue)"
                let automatic = CKSyncEngine(config); engines[scope] = automatic
                enqueue(latest, engine: automatic, scope: scope)
            }
        }
        guard token == generation else { throw CancellationError() }
        if let lastError { throw NSError(domain: "Pasto.CloudKit", code: 1, userInfo: [NSLocalizedDescriptionKey: lastError]) }
        let pendingCount = try store.prepareCloudKit().pending.count
        statusChanged?(pendingCount == 0 ? "本轮 CloudKit 拉取与发送完成。" : "本轮拉取完成，仍有 \(pendingCount) 条变更等待系统继续发送。")
    }

    private func enqueue(_ journal: OriginalCloudKitJournal, engine: CKSyncEngine, scope: OriginalCloudKitScope) {
        guard !journal.accountConfirmationRequired else { return }
        let changes = journal.pending.values.filter { $0.scope == scope }.map { change -> CKSyncEngine.PendingRecordZoneChange in
            change.deletion ? .deleteRecord(change.id.ckID) : .saveRecord(change.id.ckID)
        }
        if !changes.isEmpty { engine.state.add(pendingRecordZoneChanges: changes) }
    }

    private func fetchOptions(scope: OriginalCloudKitScope) -> CKSyncEngine.FetchChangesOptions {
        if scope == .private { return .init(scope: .zoneIDs([CKRecordZone.ID(zoneName: zoneName)])) }
        return .init()
    }

    nonisolated public func nextFetchChangesOptions(_ context: CKSyncEngine.FetchChangesContext, syncEngine: CKSyncEngine) async -> CKSyncEngine.FetchChangesOptions {
        await fetchOptionsForEngine(syncEngine)
    }

    private func fetchOptionsForEngine(_ engine: CKSyncEngine) -> CKSyncEngine.FetchChangesOptions {
        fetchOptions(scope: scope(of: engine) ?? .private)
    }

    private func scope(of engine: CKSyncEngine) -> OriginalCloudKitScope? {
        engines.first { $0.value === engine }?.key
    }

    nonisolated public func handleEvent(_ event: CKSyncEngine.Event, syncEngine: CKSyncEngine) async {
        await process(event, engine: syncEngine)
    }

    private func process(_ event: CKSyncEngine.Event, engine: CKSyncEngine) {
        guard isRunning, let scope = scope(of: engine) else { return }
        do {
            switch event {
            case .stateUpdate(let event):
                let data = try JSONEncoder().encode(event.stateSerialization)
                _ = try store.cloudKitTransaction { $0.serializations[String(scope.rawValue)] = data }
            case .accountChange(let event):
                switch event.changeType {
                case .signIn:
                    engine.state.add(pendingDatabaseChanges: scope == .private ? [.saveZone(CKRecordZone(zoneName: zoneName))] : [])
                case .signOut, .switchAccounts:
                    _ = try store.cloudKitTransaction { $0.resetAccount() }
                    fail("iCloud 账户已退出或切换，已暂停同步并保留本地内容。请确认账户后重新开启。")
                @unknown default: fail("无法识别 iCloud 账户变更，已暂停同步。")
                }
            case .fetchedDatabaseChanges(let event):
                _ = try store.cloudKitTransaction(project: true) { journal in
                    for deletion in event.deletions { _ = journal.deletedZone(deletion.zoneID, scope: scope) }
                }
            case .fetchedRecordZoneChanges(let event):
                let values = try event.modifications.map { try OriginalCloudKitRecordCodec.decode($0.record, scope: scope) }
                _ = try store.cloudKitTransaction(project: true) {
                    try $0.received(values, deleted: event.deletions.map { OriginalCloudRecordID($0.recordID) }, scope: scope)
                }
            case .sentRecordZoneChanges(let event):
                var retry: [CKSyncEngine.PendingRecordZoneChange] = []
                var recreateZone = false
                let journal = try store.cloudKitTransaction { journal in
                    for record in event.savedRecords {
                        let id = OriginalCloudRecordID(record.recordID), key = OriginalCloudKitJournal.key(id, scope: scope)
                        guard let sent = inFlight.removeValue(forKey: key) else { continue }
                        try journal.acknowledged(OriginalCloudKitRecordCodec.decode(record, scope: scope), generation: sent.generation)
                    }
                    for id in event.deletedRecordIDs {
                        let key = OriginalCloudKitJournal.key(OriginalCloudRecordID(id), scope: scope)
                        if let sent = inFlight.removeValue(forKey: key) { journal.acknowledgedDeletion(sent) }
                    }
                    for failure in event.failedRecordSaves {
                        let id = OriginalCloudRecordID(failure.record.recordID), key = OriginalCloudKitJournal.key(id, scope: scope)
                        inFlight.removeValue(forKey: key)
                        switch OriginalCloudKitRetryPolicy.action(for: failure.error.code, isPrivate: scope == .private) {
                        case .mergeServer:
                            guard let server = failure.error.serverRecord else { throw failure.error }
                            try journal.received([OriginalCloudKitRecordCodec.decode(server, scope: scope)], deleted: [], scope: scope)
                        case .recreateRecord: journal.recoverRecord(id, scope: scope)
                        case .recreateZone: journal.recoverPrivateZone(); recreateZone = true
                        case .retry: break // CloudKit owns backoff and retryAfterSeconds.
                        case .removePending, .stop:
                            // Preserve the unsent edit on unverified/destructive failure branches.
                            throw failure.error
                        }
                        if journal.pending[key] != nil { retry.append(.saveRecord(id.ckID)) }
                    }
                    for (id, error) in event.failedRecordDeletes {
                        let key = OriginalCloudKitJournal.key(OriginalCloudRecordID(id), scope: scope)
                        if error.code == .unknownItem, let sent = inFlight.removeValue(forKey: key) { journal.acknowledgedDeletion(sent) }
                        else if OriginalCloudKitRetryPolicy.action(for: error.code, isPrivate: scope == .private) == .retry { retry.append(.deleteRecord(id)) }
                        else { throw error }
                    }
                }
                if recreateZone { engine.state.add(pendingDatabaseChanges: [.saveZone(CKRecordZone(zoneName: zoneName))]) }
                engine.state.add(pendingRecordZoneChanges: retry)
                enqueue(journal, engine: engine, scope: scope)
            case .sentDatabaseChanges(let event):
                if let failure = event.failedZoneSaves.first { lastError = failure.error.localizedDescription; statusChanged?(lastError!) }
                if let failure = event.failedZoneDeletes.values.first { throw failure }
            case .didFetchRecordZoneChanges(let event):
                if let error = event.error { fetchingFailures.insert(scope); lastError = error.localizedDescription; statusChanged?(lastError!) }
            case .didFetchChanges:
                break // Checkpoint/seed only follows a successful explicit fetch during bootstrap.
            case .willFetchChanges, .willFetchRecordZoneChanges, .willSendChanges, .didSendChanges:
                break
            @unknown default: break
            }
        } catch { fail(error.localizedDescription) }
    }

    private func fail(_ message: String) {
        lastError = message; isRunning = false; generation = UUID(); statusChanged?(message)
        let previous = Array(engines.values); engines.removeAll(); inFlight.removeAll()
        Task { for engine in previous { await engine.cancelOperations() } }
    }

    nonisolated public func nextRecordZoneChangeBatch(_ context: CKSyncEngine.SendChangesContext, syncEngine: CKSyncEngine) async -> CKSyncEngine.RecordZoneChangeBatch? {
        await batch(context, engine: syncEngine)
    }

    private func batch(_ context: CKSyncEngine.SendChangesContext, engine: CKSyncEngine) -> CKSyncEngine.RecordZoneChangeBatch? {
        guard isRunning, let scope = scope(of: engine) else { return nil }
        do {
            let journal = try store.prepareCloudKit()
            let pending = Set(engine.state.pendingRecordZoneChanges)
            let eligible = journal.eligible(scope: scope).filter { change in
                let value: CKSyncEngine.PendingRecordZoneChange = change.deletion ? .deleteRecord(change.id.ckID) : .saveRecord(change.id.ckID)
                return pending.contains(value) && context.options.scope.contains(value)
            }
            guard !eligible.isEmpty else { return nil }
            var saves: [CKRecord] = [], deletes: [CKRecord.ID] = []
            for change in eligible.prefix(100) {
                let key = OriginalCloudKitJournal.key(change.id, scope: scope)
                if change.deletion { deletes.append(change.id.ckID) }
                else if let document = journal.documents[key] {
                    saves.append(try OriginalCloudKitRecordCodec.encode(document, assetDirectory: store.directoryURL.appendingPathComponent("CloudKitAssets", isDirectory: true)))
                } else { continue }
                inFlight[key] = change
            }
            return CKSyncEngine.RecordZoneChangeBatch(recordsToSave: saves, recordIDsToDelete: deletes)
        } catch { fail(error.localizedDescription); return nil }
    }
}
