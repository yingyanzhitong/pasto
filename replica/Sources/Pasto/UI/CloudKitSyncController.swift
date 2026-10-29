import AppKit
import Combine
import CryptoKit
import PastoCore
import SwiftUI

@MainActor
final class CloudKitSyncController: ObservableObject {
    @Published private(set) var isEnabled = false
    @Published private(set) var isBusy = false
    @Published private(set) var statusText: String
    @Published private(set) var lastSyncDate: Date?
    let canSync: Bool
    let containerIdentifier: String?
    private let configuration: PastoCloudKitConfiguration?
    private let store: ClipboardStore
    private let drive: ICloudDriveSyncController
    private let defaults: UserDefaults
    private let key: String
    private var engine: OriginalCloudKitSyncEngine?
    private var timer: Timer?
    private var task: Task<Void, Never>?
    private var generation = UUID()

    init(store: ClipboardStore, drive: ICloudDriveSyncController, defaults: UserDefaults = .standard) {
        self.store = store; self.drive = drive; self.defaults = defaults
        configuration = try? PastoCloudKitConfiguration.current()
        containerIdentifier = configuration?.containerIdentifier
        canSync = configuration != nil && store.directoryURL.standardizedFileURL.resolvingSymlinksInPath()
            == ClipboardStore.defaultDirectoryURL.standardizedFileURL.resolvingSymlinksInPath()
        let digest = SHA256.hash(data: Data(store.directoryURL.path.utf8)).map { String(format: "%02x", $0) }.joined()
        key = "pasto.cloudkit.\(digest).enabled"
        statusText = configuration == nil ? "此构建未配置 Pasto 自有 CloudKit 容器和开发者签名，暂不能连接 iCloud。" : "尚未开启 CloudKit 同步。"
    }

    deinit { timer?.invalidate(); task?.cancel() }

    func start() {
        guard canSync, defaults.bool(forKey: key), !drive.isEnabled else { return }
        enable()
    }

    func setEnabled(_ enabled: Bool) {
        guard enabled else { disable(); return }
        guard canSync else { return }
        let alert = NSAlert()
        alert.messageText = "开启 iCloud 同步？"
        alert.informativeText = "将本机历史和收藏分组同步到 Pasto 自有的 iCloud 容器，并合并其他 Mac 的内容与删除。不会访问原版 Paste 的云数据。开启后将关闭独立的 iCloud Drive 文件同步。"
        alert.addButton(withTitle: "开启并同步"); alert.addButton(withTitle: "取消")
        guard alert.runModal() == .alertFirstButtonReturn else { return }
        drive.setEnabled(false)
        enable()
    }

    private func enable() {
        guard canSync, let configuration, !isEnabled else { return }
        generation = UUID(); let token = generation
        let engine = OriginalCloudKitSyncEngine(store: store, configuration: configuration)
        self.engine = engine
        engine.statusChanged = { [weak self, weak engine] message in
            guard let self, generation == token else { return }
            statusText = message
            if engine?.isRunning == false {
                isEnabled = false; defaults.set(false, forKey: key); timer?.invalidate(); timer = nil
            }
        }
        isEnabled = true; isBusy = true
        defaults.set(true, forKey: key)
        timer = Timer.scheduledTimer(withTimeInterval: 30, repeats: true) { [weak self] _ in
            Task { @MainActor in self?.syncNow() }
        }
        task = Task { [weak self] in
            guard let self else { return }
            do {
                try await engine.start()
                NSApplication.shared.registerForRemoteNotifications()
                guard generation == token, !Task.isCancelled else { await engine.stop(); return }
                try await engine.synchronize()
                if generation == token { lastSyncDate = Date() }
            } catch {
                if generation == token {
                    statusText = error.localizedDescription
                    if !engine.isRunning { isEnabled = false; defaults.set(false, forKey: key); timer?.invalidate(); timer = nil }
                }
            }
            if generation == token { isBusy = false; task = nil }
        }
    }

    private func disable() {
        generation = UUID(); timer?.invalidate(); timer = nil; task?.cancel(); task = nil
        isEnabled = false; isBusy = false; defaults.set(false, forKey: key)
        if let engine { Task { await engine.stop() } }
        engine = nil; statusText = "同步已关闭，本地内容与 iCloud 数据均保留。"
    }

    func syncNow() {
        guard isEnabled, !isBusy, let engine else { return }
        if drive.isEnabled { disable(); statusText = "已开启独立 iCloud Drive 同步，CloudKit 同步已暂停。"; return }
        let token = generation; isBusy = true
        task = Task { [weak self] in
            guard let self else { return }
            do { try await engine.synchronize(); if token == generation { lastSyncDate = Date() } }
            catch { if token == generation { statusText = error.localizedDescription } }
            if token == generation { isBusy = false; task = nil }
        }
    }
}

@MainActor
struct ICloudSyncGeneralRow: View {
    @ObservedObject var sync: CloudKitSyncController
    @ObservedObject var drive: ICloudDriveSyncController

    private var enabled: Bool { drive.isEnabled || sync.isEnabled }
    private var summary: String {
        if drive.isBusy || sync.isBusy { return "正在同步…" }
        guard enabled else { return drive.statusText.hasPrefix("无法开启") ? "无法开启" : "未开启" }
        if let date = drive.isEnabled ? drive.lastSyncDate : sync.lastSyncDate {
            return (drive.isEnabled ? "本地合并 " : "最近更新 ") + date.formatted(date: .omitted, time: .shortened)
        }
        return "等待同步"
    }

    var body: some View {
        HStack {
            Text("iCloud 同步")
            Spacer()
            Text(summary).font(.caption).foregroundStyle(.secondary)
            Toggle("iCloud 同步", isOn: Binding(get: { enabled }, set: { value in
                if value { drive.setEnabled(true) }
                else {
                    if drive.isEnabled { drive.setEnabled(false) }
                    if sync.isEnabled { sync.setEnabled(false) }
                }
            })).labelsHidden().toggleStyle(.switch)
                .disabled(!drive.canSync && !sync.canSync)
        }
        .help(drive.isEnabled || !sync.isEnabled ? drive.statusText : sync.statusText)
    }
}
