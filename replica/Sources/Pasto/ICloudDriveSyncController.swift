import AppKit
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
    private var timer: Timer?
    private var syncTask: Task<Void, Never>?
    private var generation = UUID()

    static var iCloudDriveURL: URL {
        FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent("Library/Mobile Documents/com~apple~CloudDocs", isDirectory: true)
    }

    init(store: ClipboardStore, defaults: UserDefaults = .standard) {
        self.store = store
        self.defaults = defaults
        canSync = store.directoryURL.standardizedFileURL.resolvingSymlinksInPath()
            == ClipboardStore.defaultDirectoryURL.standardizedFileURL.resolvingSymlinksInPath()
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
        let root = Self.iCloudDriveURL.resolvingSymlinksInPath().standardizedFileURL.pathComponents
        let candidate = url.resolvingSymlinksInPath().standardizedFileURL.pathComponents
        return candidate.count >= root.count && Array(candidate.prefix(root.count)) == root
    }

    func chooseFolder() {
        guard canSync else { return }
        guard FileManager.default.fileExists(atPath: Self.iCloudDriveURL.path) else {
            statusText = "请先在系统设置中登录 Apple ID 并开启 iCloud Drive。"
            return
        }
        let panel = NSOpenPanel()
        panel.title = "选择 iCloud Drive 同步文件夹"
        panel.message = "请在 iCloud Drive 中新建或选择一个 Pasto 文件夹；其他 Mac 选择相同文件夹。"
        panel.prompt = "选择同步文件夹"
        panel.canChooseDirectories = true; panel.canChooseFiles = false
        panel.canCreateDirectories = true; panel.allowsMultipleSelection = false
        panel.directoryURL = folderURL ?? Self.iCloudDriveURL
        guard panel.runModal() == .OK, let selected = panel.url else { return }
        guard isICloudFolder(selected) else {
            statusText = "请选择 iCloud Drive 中的文件夹，普通本地文件夹无法跨设备同步。"
            return
        }
        let alert = NSAlert()
        alert.messageText = "开启 iCloud 同步？"
        alert.informativeText = "将本机剪贴板历史、图片和收藏分组写入选中的 iCloud Drive 文件夹，并与其他 Mac 合并。删除也会同步。\n\n仅限使用同一文件夹的 Pasto；不会连接原版 Paste 的云数据。"
        alert.addButton(withTitle: "开启并同步"); alert.addButton(withTitle: "取消")
        guard alert.runModal() == .alertFirstButtonReturn else { return }
        do {
            stop()
            defaults.set(false, forKey: prefix + "enabled")
            if folderURL?.standardizedFileURL != selected.standardizedFileURL {
                try store.resetICloudSyncIdentity()
            }
            folderURL = selected
            defaults.set(selected.path, forKey: prefix + "folder")
            setEnabled(true)
        } catch { statusText = error.localizedDescription }
    }

    func setEnabled(_ enabled: Bool) {
        guard enabled else {
            stop()
            defaults.set(false, forKey: prefix + "enabled")
            statusText = "同步已关闭，本地和 iCloud Drive 中的内容均保留。"
            return
        }
        guard canSync else { return }
        guard let folderURL else { chooseFolder(); return }
        guard isICloudFolder(folderURL), FileManager.default.fileExists(atPath: folderURL.path) else {
            statusText = "同步文件夹不可用，请重新选择 iCloud Drive 文件夹。"
            return
        }
        stop()
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
