import AppKit
import ApplicationServices
import Combine
import os
import PastoCore

@main
enum PastoMain {
    @MainActor static func main() {
        let application = NSApplication.shared
        let delegate = ReplicaAppDelegate()
        application.delegate = delegate
        application.setActivationPolicy(.accessory)
        application.run()
        withExtendedLifetime(delegate) {}
    }
}

@MainActor
final class ReplicaAppDelegate: NSObject, NSApplicationDelegate, NSMenuItemValidation {
    private var store: ClipboardStore!
    private var ui: ReplicaUIController!
    private var monitor: ClipboardMonitor?
    private var soundEffects: OriginalSoundEffects?
    private var diagnostics: OriginalDiagnosticsManager?
    private var diagnosticsObservation: AnyCancellable?
    private let accessibilityService = OriginalAccessibilityService()
    private var accessibilityObservation: AnyCancellable?
    private let hotKey = GlobalHotKey()
    private let stackHotKey = GlobalHotKey()
    private let stackPasteHotKey = GlobalHotKey()
    private var stackPasteRegistered = false
    private var statusItem: NSStatusItem!
    private var targetApplication: NSRunningApplication?
    private let pasteLogger = Logger(subsystem: "com.yingyanzhitong.paste-replica", category: "direct-paste")
    private var activationObserver: NSObjectProtocol?
    private var refreshTimer: Timer?
    private var pausePreferencesObservation: AnyCancellable?
    private var pauseResumeTimer: Timer?
    private var scheduledResumeDate: Date?
    private var lastPauseFlag: Bool?
    private var hotKeyStatus: OSStatus = noErr
    private var stackHotKeyStatus: OSStatus = noErr
    private var hotKeyObservation: AnyCancellable?
    private var lastHotKeyConfiguration: [KeyboardShortcut?]?
    private var isRecordingHotKey = false
    private var pasteGeneration = UUID()
    private let arguments = ProcessInfo.processInfo.arguments
    private var pasteboard: NSPasteboard = .general

    private func argument(_ name: String) -> String? {
        guard let index = arguments.firstIndex(of: name), index + 1 < arguments.count else { return nil }
        return arguments[index + 1]
    }

    func applicationDidFinishLaunching(_ notification: Notification) {
        do {
            for flag in ["--data-dir", "--pasteboard-name"] where arguments.contains(flag) {
                guard let value = argument(flag), !value.isEmpty, !value.hasPrefix("--") else {
                    throw NSError(domain: "PastoArguments", code: 1,
                                  userInfo: [NSLocalizedDescriptionKey: "\(flag) 必须提供有效的值。"])
                }
            }
            if arguments.contains("--fixture"), argument("--data-dir") == nil {
                throw NSError(domain: "PastoArguments", code: 2,
                              userInfo: [NSLocalizedDescriptionKey: "--fixture 必须搭配独立的 --data-dir。"])
            }
            if let name = argument("--pasteboard-name") {
                guard name != "general", name != NSPasteboard.Name.general.rawValue else {
                    throw NSError(domain: "PastoArguments", code: 3,
                                  userInfo: [NSLocalizedDescriptionKey: "--pasteboard-name 只支持具名私有剪贴板。"])
                }
                pasteboard = NSPasteboard(name: .init(name))
            } else if arguments.contains("--fixture") {
                pasteboard = NSPasteboard(name: .init("pasto-fixture-\(UUID().uuidString)"))
            }
            let directory = argument("--data-dir").map { URL(fileURLWithPath: $0, isDirectory: true) }
                ?? ClipboardStore.defaultDirectoryURL
            store = try ClipboardStore(directoryURL: directory)
            PastoAppIntentStore.configure(store: store)
            diagnostics = OriginalDiagnosticsManager.makeLocal(
                logDirectory: directory.appendingPathComponent("Diagnostics", isDirectory: true)
            ) { [weak self] enabled in
                guard let self, self.store.preferences.isDiagnosticsEnabled != enabled else { return }
                self.store.preferences.isDiagnosticsEnabled = enabled
                do { try self.store.save() }
                catch { self.ui?.presentError(error) }
            }
            diagnostics?.f_1002fe72c(store.preferences.isDiagnosticsEnabled)
            diagnosticsObservation = store.$preferences.map(\.isDiagnosticsEnabled).removeDuplicates().sink { [weak self] _ in
                // @Published emits before storage changes; resolve the committed preference next turn.
                DispatchQueue.main.async {
                    guard let self else { return }
                    self.diagnostics?.f_1002fe72c(self.store.preferences.isDiagnosticsEnabled)
                }
            }
            try store.save()
            if arguments.contains("--fixture"), store.items.isEmpty { try seedFixture() }
            ui = ReplicaUIController(store: store)
            ui.pasteboard = pasteboard
            ui.pasteHandler = { [weak self] id, plain in self?.paste(id: id, plain: plain) ?? false }
            ui.pasteItemsHandler = { [weak self] ids, plain in self?.paste(ids: ids, plain: plain) ?? false }
            ui.copiedItemsHandler = {
                ReplicaCopiedOSD.showCopied()
                NSApp.deactivate()
            }
            ui.hotKeyConfigurationChanged = { [weak self] in self?.configureGlobalHotKeys() }
            ui.stackDidChange = { [weak self] in self?.configureStackPasteShortcut() }
            ui.hotKeyRecordingChanged = { [weak self] recording in
                guard let self else { return }
                self.isRecordingHotKey = recording
                if recording { self.hotKey.unregister(); self.stackHotKey.unregister(); self.updateStatus() }
                else { self.configureGlobalHotKeys(force: true) }
                self.configureStackPasteShortcut()
            }
            setupMenus()
            targetApplication = NSWorkspace.shared.frontmostApplication
            activationObserver = NSWorkspace.shared.notificationCenter.addObserver(
                forName: NSWorkspace.didActivateApplicationNotification, object: nil, queue: .main
            ) { [weak self] notification in
                guard let app = notification.userInfo?[NSWorkspace.applicationUserInfoKey] as? NSRunningApplication,
                      app.processIdentifier != ProcessInfo.processInfo.processIdentifier else { return }
                MainActor.assumeIsolated { self?.targetApplication = app }
            }
            if !arguments.contains("--no-monitor") {
                monitor = ClipboardMonitor(store: store, pasteboard: pasteboard)
                monitor?.onCapture = { [weak self] id in self?.ui.captureIntoStack(id: id) }
            }
            soundEffects = OriginalSoundEffects(store: store, monitor: monitor)
            ReplicaCopiedOSD.pauseStatus = { [weak self] in
                guard let self, self.monitor != nil,
                      let capture = OriginalPasteboardCaptureState.current(for: self.pasteboard) else { return nil }
                return capture.pollTimer == nil
            }
            ui.state.monitoringPauseChanged = { [weak self] in self?.configurePauseMonitoring() }
            configurePauseMonitoring()
            pausePreferencesObservation = store.$preferences.sink { [weak self] _ in
                // @Published fires before the two pause fields finish changing.
                DispatchQueue.main.async { self?.configurePauseMonitoring() }
            }
            hotKey.action = { [weak self] in self?.togglePanel(nil) }
            stackHotKey.action = { [weak self] in
                guard let self else { return }
                if NSApp.isActive, self.ui.panel.isKeyWindow, self.store.preferences.stackShortcut == .stackDefault {
                    self.ui.copySelection(plainTextOnly: true)
                } else { self.ui.showStack() }
            }
            hotKeyObservation = store.$preferences.sink { [weak self] _ in
                // @Published 在赋值前通知，下一轮读取完整的新偏好。
                DispatchQueue.main.async { self?.configureGlobalHotKeys() }
            }
            stackPasteHotKey.action = { [weak self] in
                guard let self else { return }
                if NSApp.isActive {
                    NSApp.sendAction(#selector(NSText.paste(_:)), to: nil, from: nil)
                    return
                }
                guard let first = self.ui.state.stackItems.first else { return }
                self.targetApplication = NSWorkspace.shared.frontmostApplication
                self.ui.consumeStackHead()
                _ = self.paste(ids: [first.id], plain: false, forceDirect: true)
                if self.ui.state.stackItems.isEmpty { self.ui.hideStack() }
            }
            configureGlobalHotKeys(force: true)
            accessibilityObservation = accessibilityService.f_100ae5e90().sink { [weak self] _ in
                MainActor.assumeIsolated { self?.configureStackPasteShortcut() }
            }
            refreshTimer = Timer.scheduledTimer(withTimeInterval: 1, repeats: true) { [weak self] _ in
                Task { @MainActor in
                    guard let self else { return }
                    do { try self.store.reload() }
                    catch { self.statusItem.button?.toolTip = "无法刷新历史：\(error.localizedDescription)" }
                }
            }
            updateStatus()
            if argument("--data-dir") == nil { BackgroundService.markRunning(true) }
            if arguments.contains("--show-panel") { ui.showPanel() }
            if arguments.contains("--show-settings") { ui.showSettings() }
        } catch {
            NSAlert(error: error).runModal()
            NSApp.terminate(nil)
        }
    }

    private func menuItem(_ title: String, _ action: Selector, key: String = "",
                          modifiers: NSEvent.ModifierFlags = [.command]) -> NSMenuItem {
        let item = NSMenuItem(title: title, action: action, keyEquivalent: key)
        item.target = self
        item.keyEquivalentModifierMask = modifiers
        return item
    }

    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows flag: Bool) -> Bool {
        ui?.showPanel()
        return true
    }

    private func setupMenus() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength)
        statusItem.button?.image = NSImage(systemSymbolName: "clipboard", accessibilityDescription: "Pasto")
        statusItem.button?.target = self
        statusItem.button?.action = #selector(statusClicked(_:))
        statusItem.button?.sendAction(on: [.leftMouseUp, .rightMouseUp])
        let main = NSMenu()
        let appMenu = NSMenu(title: "Pasto")
        appMenu.addItem(menuItem("关于 Pasto", #selector(about(_:))))
        appMenu.addItem(menuItem("设置…", #selector(settings(_:)), key: ","))
        appMenu.addItem(menuItem(diagnosticsMenuTitle, #selector(toggleDiagnostics(_:))))
        appMenu.addItem(.separator())
        appMenu.addItem(menuItem("退出 Pasto", #selector(quit(_:)), key: "q"))
        let app = NSMenuItem(); app.submenu = appMenu; main.addItem(app)
        let file = NSMenu(title: "文件")
        file.addItem(menuItem("新建文本…", #selector(newText(_:)), key: "n"))
        file.addItem(menuItem(OriginalSearchLocalization.text("pasto.action.create-group") + "…", #selector(newBoard(_:)), key: "n", modifiers: [.command, .shift]))
        file.addItem(.separator())
        file.addItem(menuItem("导入…", #selector(importArchive(_:))))
        file.addItem(menuItem("从 Paste 迁移分组…", #selector(migratePasteGroups(_:))))
        file.addItem(menuItem("导出…", #selector(exportArchive(_:))))
        let fileItem = NSMenuItem(title: "文件", action: nil, keyEquivalent: ""); fileItem.submenu = file; main.addItem(fileItem)
        let edit = NSMenu(title: "编辑")
        for (title, selector, key) in [("撤销", "undo:", "z"), ("剪切", "cut:", "x"),
                                        ("拷贝", "copy:", "c"), ("粘贴", "paste:", "v"), ("全选", "selectAll:", "a")] {
            edit.addItem(NSMenuItem(title: title, action: Selector(selector), keyEquivalent: key))
        }
        let editItem = NSMenuItem(title: "编辑", action: nil, keyEquivalent: ""); editItem.submenu = edit; main.addItem(editItem)
        let view = NSMenu(title: "显示")
        view.addItem(menuItem("剪贴板历史", #selector(togglePanel(_:))))
        view.addItem(menuItem("搜索", #selector(search(_:)), key: "f"))
        view.addItem(menuItem("Pasto Stack", #selector(stack(_:))))
        let viewItem = NSMenuItem(title: "显示", action: nil, keyEquivalent: ""); viewItem.submenu = view; main.addItem(viewItem)
        NSApp.mainMenu = main
    }

    private func updateStatus() {
        if arguments.contains("--no-global-hotkey") {
            ui.hotKeyStatusMessage = "本次运行已停用全局快捷键。"
        } else if isRecordingHotKey {
            ui.hotKeyStatusMessage = "正在录制快捷键，全局快捷键暂时停用。"
        } else {
            func message(_ title: String, _ shortcut: KeyboardShortcut?, _ status: OSStatus) -> String {
                guard let shortcut else { return "\(title)：未设置" }
                return status == noErr ? "\(title)：\(shortcut.displayName)" : "\(title)：\(shortcut.displayName) 无法注册（可能已被占用，错误 \(status)）"
            }
            ui.hotKeyStatusMessage = [message("历史", store.preferences.historyShortcut, hotKeyStatus),
                                      message("Pasto Stack", store.preferences.stackShortcut, stackHotKeyStatus)].joined(separator: "；")
        }
        statusItem.button?.toolTip = "Pasto · \(ui.hotKeyStatusMessage)"
    }

    private func configureGlobalHotKeys(force: Bool = false) {
        guard !isRecordingHotKey else { updateStatus(); return }
        let configuration = [store.preferences.historyShortcut, store.preferences.stackShortcut]
        guard force || configuration != lastHotKeyConfiguration else { return }
        lastHotKeyConfiguration = configuration
        hotKey.unregister(); stackHotKey.unregister()
        func register(_ shortcut: KeyboardShortcut?, with hotKey: GlobalHotKey, identifier: UInt32) -> OSStatus {
            guard let shortcut else { return noErr }
            guard shortcut.isValidGlobal else { return OSStatus(-50) }
            return hotKey.register(keyCode: shortcut.keyCode, modifiers: shortcut.modifiers, identifier: identifier)
        }
        if !arguments.contains("--no-global-hotkey") {
            hotKeyStatus = register(configuration[0], with: hotKey, identifier: 1)
            stackHotKeyStatus = register(configuration[1], with: stackHotKey, identifier: 2)
        } else { hotKeyStatus = noErr; stackHotKeyStatus = noErr }
        updateStatus()
    }

    private func configureStackPasteShortcut() {
        let enabled = ui.isStackVisible && !ui.state.stackItems.isEmpty && !isRecordingHotKey
            && !arguments.contains("--no-global-hotkey") && pasteboard.name == NSPasteboard.general.name
            && accessibilityService.f_100ae5e74()
        guard enabled != stackPasteRegistered else { return }
        stackPasteHotKey.unregister()
        stackPasteRegistered = false
        if enabled {
            stackPasteRegistered = stackPasteHotKey.register(keyCode: 9, modifiers: .command, identifier: 3) == noErr
            if !stackPasteRegistered { ui.hotKeyStatusMessage = "Pasto Stack 的 ⌘V 无法注册，请使用项目菜单粘贴。" }
        }
    }

    @objc private func statusClicked(_ sender: Any?) {
        if NSApp.currentEvent?.type == .rightMouseUp {
            let menu = NSMenu()
            menu.addItem(menuItem("打开剪贴板", #selector(togglePanel(_:))))
            menu.addItem(menuItem("新建文本…", #selector(newText(_:))))
            menu.addItem(menuItem("设置…", #selector(settings(_:))))
            menu.addItem(menuItem(diagnosticsMenuTitle, #selector(toggleDiagnostics(_:))))
            menu.addItem(menuItem(store.preferences.isMonitoringPaused ? "继续采集" : "暂停采集", #selector(pause(_:))))
            if hotKeyStatus != noErr {
                let notice = NSMenuItem(title: "历史快捷键无法注册", action: nil, keyEquivalent: "")
                menu.addItem(notice)
            }
            if stackHotKeyStatus != noErr {
                menu.addItem(NSMenuItem(title: "Pasto Stack 快捷键无法注册", action: nil, keyEquivalent: ""))
            }
            menu.addItem(.separator())
            menu.addItem(menuItem("退出", #selector(quit(_:))))
            statusItem.menu = menu
            statusItem.button?.performClick(nil)
            statusItem.menu = nil
        } else { togglePanel(sender) }
    }

    private var diagnosticsMenuTitle: String {
        String(localized: diagnostics?.enabled == true
            ? OriginalPreviewLocalization.f_1001be088() : OriginalPreviewLocalization.f_1001bdd88())
    }

    func validateMenuItem(_ menuItem: NSMenuItem) -> Bool {
        if menuItem.action == #selector(toggleDiagnostics(_:)) {
            menuItem.title = diagnosticsMenuTitle
            return diagnostics != nil
        }
        return true
    }

    @objc private func toggleDiagnostics(_ sender: Any?) { f_10004e064() }

    private func f_10004e064() {
        guard let diagnostics else { return }
        let wasEnabled = diagnostics.enabled
        let alert = NSAlert()
        alert.messageText = String(localized: wasEnabled
            ? OriginalPreviewLocalization.f_1001be088() : OriginalPreviewLocalization.f_1001bdd88())
        alert.informativeText = ReplicaBrand.replacingOriginalName(in: String(localized: wasEnabled
            ? OriginalPreviewLocalization.f_1001bdf08() : OriginalPreviewLocalization.f_1001bdc08()))
        alert.addButton(withTitle: ReplicaBrand.replacingOriginalName(in: String(localized: wasEnabled
            ? OriginalPreviewLocalization.f_1001bda88() : OriginalPreviewLocalization.f_1001c3188())))
        alert.addButton(withTitle: String(localized: OriginalPreviewLocalization.f_1001c0788()))
        NSApp.activate(ignoringOtherApps: true)
        guard alert.runModal() == .alertFirstButtonReturn else { return }
        if wasEnabled {
            diagnostics.f_1002fe72c(false)
            do {
                if try diagnostics.f_1002fef28(store: store, pasteboard: pasteboard) != nil {
                    ReplicaCopiedOSD.showCopied()
                }
            }
            catch { ui.presentError(error) }
        } else {
            diagnostics.f_1002fe72c(true)
            OriginalDiagnosticsAppActions.f_10004e8ec()
        }
    }

    @objc private func togglePanel(_ sender: Any?) {
        rememberPasteTargetBeforeOpeningPanel()
        ui.togglePanel()
    }
    private func rememberPasteTargetBeforeOpeningPanel() {
        guard !ui.panel.isVisible else { return }
        pasteGeneration = UUID()
        let app = NSWorkspace.shared.frontmostApplication
        if app?.processIdentifier != ProcessInfo.processInfo.processIdentifier { targetApplication = app }
    }
    @objc private func settings(_ sender: Any?) { ui.showSettings() }
    @objc private func newText(_ sender: Any?) { ui.newTextItem() }
    @objc private func newBoard(_ sender: Any?) { ui.createPinboard() }
    @objc private func search(_ sender: Any?) { rememberPasteTargetBeforeOpeningPanel(); ui.focusSearch() }
    @objc private func stack(_ sender: Any?) { ui.showStack() }
    @objc private func importArchive(_ sender: Any?) { ui.importArchive() }
    @objc private func migratePasteGroups(_ sender: Any?) { ui.migratePasteGroups() }
    @objc private func exportArchive(_ sender: Any?) { ui.exportArchive() }
    @objc private func quit(_ sender: Any?) { NSApp.terminate(nil) }
    @objc private func about(_ sender: Any?) {
        NSApp.orderFrontStandardAboutPanel(options: [.applicationName: "Pasto",
                                                     .applicationVersion: Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "开发版本",
                                                     .credits: NSAttributedString(string: "原生剪贴板历史与 Pasto 工具")])
    }
    private func configurePauseMonitoring() {
        let paused = store.preferences.isMonitoringPaused
        let date = store.preferences.pauseUntil
        guard lastPauseFlag != paused || scheduledResumeDate != date else { return }
        pauseResumeTimer?.invalidate()
        pauseResumeTimer = nil
        lastPauseFlag = paused
        scheduledResumeDate = date
        guard paused || date != nil else {
            monitor?.start()
            return
        }
        monitor?.stop()
        if let date {
            // Original f_100004b40 schedules one NSTimer for resumeDate - Date().
            pauseResumeTimer = Timer.scheduledTimer(withTimeInterval: date.timeIntervalSinceNow,
                                                   repeats: false) { [weak self] _ in
                MainActor.assumeIsolated { self?.resumeTimedPause(expectedDate: date) }
            }
        }
    }

    private func resumeTimedPause(expectedDate: Date) {
        guard store.preferences.pauseUntil == expectedDate else {
            configurePauseMonitoring()
            return
        }
        pauseResumeTimer?.invalidate()
        pauseResumeTimer = nil
        store.preferences.pauseUntil = nil
        store.preferences.isMonitoringPaused = false
        do {
            try store.save()
            ReplicaCopiedOSD.showResumed()
        } catch { ui.presentError(error) }
        configurePauseMonitoring()
    }

    @objc private func pause(_ sender: Any?) {
        if store.preferences.isMonitoringPaused { ui.state.resumeMonitoring() }
        else { ui.state.pauseMonitoring() }
    }

    private func paste(id: UUID, plain: Bool) -> Bool {
        paste(ids: [id], plain: plain)
    }

    @discardableResult
    private func paste(ids: [UUID], plain: Bool, forceDirect: Bool = false) -> Bool {
        let generation = UUID()
        pasteGeneration = generation
        let requestedTarget = targetApplication
        let hasAccessibilityAccess = accessibilityService.f_100ae5e74()
        pasteLogger.notice("request ax=\(hasAccessibilityAccess, privacy: .public) post=\(CGPreflightPostEventAccess(), privacy: .public) target=\(requestedTarget?.processIdentifier ?? -1, privacy: .public) front=\(NSWorkspace.shared.frontmostApplication?.processIdentifier ?? -1, privacy: .public)")
        var copyInsteadOfPaste = !(forceDirect || store.preferences.pasteToActiveApp)
        if pasteboard.name == NSPasteboard.general.name, !copyInsteadOfPaste,
           !hasAccessibilityAccess {
            NSApp.activate(ignoringOtherApps: true)
            let result = OriginalPasteToOtherAppsModal.run()
            pasteLogger.notice("permission_result=\(result, privacy: .public)")
            if result == 2 {
                NSApp.deactivate()
                _ = OriginalEnableAccessibilityModal.run(requestOnShow: true)
                return false
            }
            if result & 1 != 0 {
                do {
                    store.preferences.pasteToActiveApp = false
                    try store.save()
                } catch { ui.presentError(error); return false }
            }
            copyInsteadOfPaste = true
        }
        var restoreOptions: OriginalPasteboardRestore.Options = plain ? .plainText : []
        if store.preferences.alwaysPastePlainText { restoreOptions.insert(.plainTextAndLinks) }
        do { try store.writeToPasteboard(ids: ids, pasteboard: pasteboard, options: restoreOptions) }
        catch {
            pasteLogger.error("restore_failed code=\((error as NSError).code, privacy: .public)")
            ui.presentError(error)
            return false
        }
        pasteLogger.notice("restored copy_only=\(copyInsteadOfPaste, privacy: .public)")
        // Named pasteboards support isolated acceptance runs and never generate system keystrokes.
        guard pasteboard.name == NSPasteboard.general.name else {
            ui.hidePanel()
            return true
        }
        guard !copyInsteadOfPaste else {
            ReplicaCopiedOSD.showCopied(enableDirectPaste: { [weak self] in
                guard let self else { return }
                self.ui.state.perform {
                    self.store.preferences.pasteToActiveApp = true
                    try self.store.save()
                }
            })
            NSApp.deactivate()
            ui.hidePanel()
            return true
        }
        ui.hidePanel()
        guard let target = requestedTarget, !target.isTerminated,
              target.processIdentifier != ProcessInfo.processInfo.processIdentifier else {
            pasteLogger.error("target_unavailable")
            return false
        }
        let changeCount = pasteboard.changeCount
        NSApp.yieldActivation(to: target)
        NSApp.deactivate()
        let activationRequested = target.activate(from: .current, options: [])
        pasteLogger.notice("activate target=\(target.processIdentifier, privacy: .public) accepted=\(activationRequested, privacy: .public)")
        let deadline = Date().addingTimeInterval(1)
        waitForTarget(target, deadline: deadline, generation: generation, changeCount: changeCount)
        return true
    }

    private func waitForTarget(_ target: NSRunningApplication, deadline: Date, generation: UUID, changeCount: Int) {
        guard generation == pasteGeneration else { pasteLogger.notice("cancelled newer_request"); return }
        guard !target.isTerminated else { pasteLogger.notice("cancelled target_terminated"); return }
        guard pasteboard.changeCount == changeCount else { pasteLogger.notice("cancelled clipboard_changed"); return }
        if NSWorkspace.shared.frontmostApplication?.processIdentifier == target.processIdentifier {
            guard let keyCode = OriginalPasteKeyTranslation.pasteKeyCode(),
                  let source = CGEventSource(stateID: .combinedSessionState),
                  let down = CGEvent(keyboardEventSource: source, virtualKey: keyCode, keyDown: true),
                  let up = CGEvent(keyboardEventSource: source, virtualKey: keyCode, keyDown: false) else {
                pasteLogger.error("event_creation_failed")
                return
            }
            down.flags = .maskCommand
            down.post(tap: .cgAnnotatedSessionEventTap)
            up.post(tap: .cgAnnotatedSessionEventTap)
            pasteLogger.notice("posted target=\(target.processIdentifier, privacy: .public) key=\(keyCode, privacy: .public)")
        } else if Date() < deadline {
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.05) { [weak self] in
                self?.waitForTarget(target, deadline: deadline, generation: generation, changeCount: changeCount)
            }
        } else {
            pasteLogger.error("activation_timeout target=\(target.processIdentifier, privacy: .public) front=\(NSWorkspace.shared.frontmostApplication?.processIdentifier ?? -1, privacy: .public)")
        }
    }

    private func seedFixture() throws {
        let board = try store.createPinboard(name: "实用链接", colorHex: "5575D9")
        _ = try store.add(ClipboardItem(title: "欢迎使用 Pasto", plainText: "拷贝内容，随时找回。\n搜索、预览、编辑，整理到 Pasto。", sourceName: "文本编辑", sourceBundleID: "com.apple.TextEdit"))
        _ = try store.add(ClipboardItem(title: "REA", kind: .link, plainText: "https://github.com/morluto/rea", sourceName: "Safari", sourceBundleID: "com.apple.Safari", pinboardIDs: [board.id]))
        _ = try store.add(ClipboardItem(title: "品牌颜色", kind: .color, plainText: "#5575D9", sourceName: "设计工具"))
        _ = try store.add(ClipboardItem(title: "会议记录", plainText: "今天的计划\n1. 整理灵感\n2. 完成设计\n3. 分享成果", sourceName: "备忘录", sourceBundleID: "com.apple.Notes"))
    }

    func applicationShouldTerminate(_ sender: NSApplication) -> NSApplication.TerminateReply {
        guard store != nil, ui != nil else { return .terminateNow }
        do { try store?.save(); return .terminateNow }
        catch { ui?.presentError(error); return .terminateCancel }
    }

    func applicationWillTerminate(_ notification: Notification) {
        if argument("--data-dir") == nil { BackgroundService.markRunning(false) }
        pasteGeneration = UUID()
        hotKeyObservation?.cancel()
        diagnosticsObservation?.cancel()
        accessibilityObservation?.cancel()
        soundEffects?.stop()
        soundEffects = nil
        pausePreferencesObservation?.cancel()
        pauseResumeTimer?.invalidate()
        pauseResumeTimer = nil
        ReplicaCopiedOSD.pauseStatus = nil
        monitor?.stop(); hotKey.unregister(); stackHotKey.unregister(); stackPasteHotKey.unregister(); refreshTimer?.invalidate()
        if let activationObserver { NSWorkspace.shared.notificationCenter.removeObserver(activationObserver) }
    }
}
