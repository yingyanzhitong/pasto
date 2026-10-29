import Combine
import CryptoKit
import Foundation
import PastoCore

@MainActor
final class ICloudDriveSyncController: ObservableObject {
    @Published private(set) var isEnabled = false
    @Published private(set) var isBusy = false
    @Published private(set) var folderURL: URL?
    @Published private(set) var lastSyncDate: Date?
    @Published private(set) var statusText = "未开启 iCloud 同步"
    let canSync: Bool
    private let store: ClipboardStore
    private let transport = ICloudDriveSyncTransport()
    private let defaults: UserDefaults
    private let prefix: String
    private let cloudRoot: URL
    private var timer: Timer?
    private var syncTask: Task<Void, Never>?
    private var generation = UUID()

    static var iCloudDriveURL: URL {
        FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent("Library/Mobile Documents/com~apple~CloudDocs", isDirectory: true)
    }

    init(store: ClipboardStore, defaults: UserDefaults = .standard,
         supportedDataDirectory: URL? = nil, cloudRoot: URL? = nil) {
        self.store = store
        self.defaults = defaults
        self.cloudRoot = cloudRoot ?? Self.iCloudDriveURL
        canSync = store.directoryURL.standardizedFileURL.resolvingSymlinksInPath()
            == (supportedDataDirectory ?? ClipboardStore.defaultDirectoryURL).standardizedFileURL.resolvingSymlinksInPath()
        let digest = SHA256.hash(data: Data(store.directoryURL.standardizedFileURL.path.utf8))
            .map { String(format: "%02x", $0) }.joined()
        prefix = "pasto.icloud-drive.\(digest)."
        if let path = defaults.string(forKey: prefix + "folder") { folderURL = URL(fileURLWithPath: path, isDirectory: true) }
    }

    deinit { timer?.invalidate(); syncTask?.cancel() }

    func start() {
        guard canSync, defaults.bool(forKey: prefix + "enabled") else { return }
        setEnabled(true)
    }

    private func isICloudFolder(_ url: URL) -> Bool {
        let root = cloudRoot.resolvingSymlinksInPath().standardizedFileURL.pathComponents
        let candidate = url.resolvingSymlinksInPath().standardizedFileURL.pathComponents
        return candidate.count >= root.count && Array(candidate.prefix(root.count)) == root
    }

    private func prepareFolder() throws -> URL {
        let files = FileManager.default
        guard (try? cloudRoot.resourceValues(forKeys: [.isDirectoryKey]))?.isDirectory == true else {
            throw ICloudDriveSyncError.folderUnavailable
        }
        // Keep an existing explicit location so upgrading never abandons its documents.
        let selected = folderURL ?? cloudRoot.appendingPathComponent("Pasto", isDirectory: true)
        guard isICloudFolder(selected) else { throw ICloudDriveSyncError.folderUnavailable }
        if folderURL == nil && !files.fileExists(atPath: selected.path) {
            try files.createDirectory(at: selected, withIntermediateDirectories: false,
                                      attributes: [.posixPermissions: 0o700])
        }
        guard (try selected.resourceValues(forKeys: [.isDirectoryKey])).isDirectory == true else {
            throw ICloudDriveSyncError.folderUnavailable
        }
        if folderURL == nil {
            try store.resetICloudSyncIdentity()
            lastSyncDate = nil
        }
        return selected
    }

    func setEnabled(_ enabled: Bool) {
        guard enabled else {
            stop()
            defaults.set(false, forKey: prefix + "enabled")
            statusText = "同步已关闭，本地和 iCloud Drive 中的内容均保留。"
            return
        }
        guard canSync, !isEnabled else { return }
        do {
            let selected = try prepareFolder()
            folderURL = selected
            defaults.set(selected.path, forKey: prefix + "folder")
        } catch {
            defaults.set(false, forKey: prefix + "enabled")
            statusText = "无法开启：请确认系统已开启 iCloud Drive，且 Pasto 同步文件夹可访问。"
            return
        }
        isEnabled = true
        defaults.set(true, forKey: prefix + "enabled")
        timer = Timer.scheduledTimer(withTimeInterval: 30, repeats: true) { [weak self] _ in
            Task { @MainActor in self?.syncNow() }
        }
        syncNow()
    }

    private func stop() {
        generation = UUID()
        timer?.invalidate(); timer = nil
        syncTask?.cancel(); syncTask = nil
        isBusy = false
        isEnabled = false
    }

    func syncNow() {
        guard isEnabled, !isBusy, let folderURL else { return }
        let currentGeneration = generation
        isBusy = true
        statusText = "正在合并 iCloud Drive 中的内容…"
        syncTask = Task { [weak self] in
            guard let self else { return }
            defer {
                if generation == currentGeneration { isBusy = false; syncTask = nil }
            }
            do {
                try Task.checkCancellation()
                guard generation == currentGeneration, isEnabled else { return }
                let local = try store.prepareICloudSync()
                let incoming = try await transport.read(from: folderURL, excluding: local.deviceID)
                try Task.checkCancellation()
                guard generation == currentGeneration, isEnabled else { return }
                let outgoing = try store.applyICloudSync(incoming)
                try Task.checkCancellation()
                try await transport.write(outgoing, to: folderURL)
                try Task.checkCancellation()
                guard generation == currentGeneration, isEnabled else { return }
                lastSyncDate = Date()
                statusText = "iCloud Drive 数据已更新，设备间传输由 macOS 完成。"
            } catch is CancellationError {
                // Disabling sync must not replace the user's new state with a late completion.
            } catch {
                guard generation == currentGeneration else { return }
                statusText = "同步未完成：\(error.localizedDescription)"
            }
        }
    }
}
