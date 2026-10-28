import AppKit
import ServiceManagement
import SwiftUI
import UniformTypeIdentifiers
import PastoCore
import QuickLookUI

@MainActor
struct ReplicaPreviewView: View {
    @ObservedObject var state: ReplicaUIState
    let itemID: UUID
    @State private var selectedFile = 0
    private var item: ClipboardItem? { state.store.items.first { $0.id == itemID } }

    var body: some View {
        Group {
            if let item {
                VStack(alignment: .leading, spacing: 16) {
                    HStack(spacing: 10) {
                        SourceAppIcon(item: item, store: state.store).frame(width: 32, height: 32)
                        VStack(alignment: .leading, spacing: 3) {
                            Text(item.title.isEmpty ? item.kind.displayName : item.title).font(.headline).lineLimit(2)
                            Text("\(item.sourceName) · \(item.kind.displayName) · \(itemSummary(item))")
                                .font(.caption).foregroundStyle(.secondary)
                        }
                        Spacer()
                        if item.isDeleted { Text("已删除").foregroundStyle(.secondary) }
                    }
                    Divider()
                    if item.kind == .files, !itemFileURLs(item).isEmpty {
                        filePreview(urls: itemFileURLs(item))
                    } else if item.kind == .image, let image = itemImage(item) {
                        OriginalImageTextSelection(item: item, image: image)
                            .frame(maxWidth: .infinity, maxHeight: .infinity)
                    } else {
                        ScrollView {
                            ReplicaItemContent(item: item, compact: false,
                                               linkPreviewsEnabled: state.store.preferences.linkPreviewsEnabled)
                                .textSelection(.enabled)
                                .frame(maxWidth: .infinity, alignment: .topLeading)
                                .padding(8)
                        }
                    }
                    HStack {
                        Text(item.createdAt, format: .dateTime.year().month().day().hour().minute())
                            .font(.caption).foregroundStyle(.secondary)
                        Spacer()
                        if item.plainText != nil {
                            Button("编辑…") { state.controller?.showEditor(item: item) }
                        }
                        Button("拷贝") {
                            state.controller?.copy(item: item, plainTextOnly: false)
                        }.disabled(item.isDeleted)
                    }
                }
                .padding(22)
            } else {
                ContentUnavailableView("项目不存在", systemImage: "doc.questionmark", description: Text("这个项目已被移除。"))
            }
        }
        .frame(minWidth: 360, minHeight: 280)
        .preferredColorScheme(state.preferredScheme)
    }

    private func filePreview(urls: [URL]) -> some View {
        let index = min(selectedFile, urls.count - 1)
        let url = urls[index]
        return VStack(spacing: 8) {
            if urls.count > 1 {
                Picker("文件", selection: $selectedFile) {
                    ForEach(Array(urls.enumerated()), id: \.offset) { index, file in
                        Text(file.lastPathComponent).tag(index)
                    }
                }
            }
            if FileManager.default.fileExists(atPath: url.path) {
                NativeFilePreview(url: url).frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                ContentUnavailableView("文件不可用", systemImage: "doc.questionmark",
                                       description: Text("文件可能已移动或删除。\n\(url.lastPathComponent)"))
            }
        }
    }
}

@MainActor
struct NativeFilePreview: NSViewRepresentable {
    let url: URL
    func makeNSView(context: Context) -> QLPreviewView {
        let view = QLPreviewView(frame: .zero, style: .normal)!
        view.shouldCloseWithWindow = false
        view.autostarts = false
        view.previewItem = url as NSURL
        return view
    }
    func updateNSView(_ nsView: QLPreviewView, context: Context) {
        if nsView.previewItem?.previewItemURL != url { nsView.previewItem = url as NSURL }
    }
    static func dismantleNSView(_ nsView: QLPreviewView, coordinator: ()) { nsView.close() }
}

@MainActor
struct ReplicaEditorView: View {
    @ObservedObject var state: ReplicaUIState
    let item: ClipboardItem?
    let close: () -> Void
    @StateObject private var document: ReplicaRichTextDocument
    @Environment(\.colorScheme) private var colorScheme

    init(state: ReplicaUIState, item: ClipboardItem?, close: @escaping () -> Void) {
        self.state = state
        self.item = item
        self.close = close
        let initial: NSAttributedString
        if let data = item?.payloads["public.rtf"], let rich = NSAttributedString(rtf: data, documentAttributes: nil) {
            initial = rich
        } else {
            initial = NSAttributedString(string: item?.plainText ?? "", attributes: [
                .font: NSFont.systemFont(ofSize: 14), .foregroundColor: NSColor.textColor
            ])
        }
        _document = StateObject(wrappedValue: ReplicaRichTextDocument(content: initial))
    }

    var body: some View {
        VStack(spacing: 0) {
            ZStack {
                HStack {
                    Button("取消", action: close)
                        .buttonStyle(.plain).padding(.horizontal, 10).frame(height: 22)
                        .overlay(Capsule().stroke(.gray.opacity(0.16)))
                        .keyboardShortcut(.cancelAction)
                    Spacer()
                    Button(item == nil ? "创建" : "保存", action: save)
                        .buttonStyle(.plain).foregroundStyle(.white)
                        .font(.system(size: 14, weight: .semibold))
                        .padding(.horizontal, 10).frame(height: 22)
                        .background(document.content.length == 0 ? Color.gray.opacity(0.30) : .blue, in: Capsule())
                        .disabled(document.content.length == 0)
                        .keyboardShortcut("s", modifiers: .command)
                        .accessibilityIdentifier("editor-save")
                }
                HStack(spacing: 24) {
                    formatButton("B", format: .bold, active: document.bold)
                        .fontWeight(.bold).keyboardShortcut("b", modifiers: .command)
                    formatButton("I", format: .italic, active: document.italic)
                        .italic().keyboardShortcut("i", modifiers: .command)
                    formatButton("U", format: .underline, active: document.underlined)
                        .underline().keyboardShortcut("u", modifiers: .command)
                    formatButton("S", format: .strikethrough, active: document.struck).strikethrough()
                }
            }
            .padding(.horizontal, 8).frame(height: 38)
            ReplicaRichTextInput(document: document, save: save)
                .clipShape(RoundedRectangle(cornerRadius: 5))
                .padding(.horizontal, 5)
            HStack {
                Text("\(document.characterCount) 个字符  ·  \(document.wordCount) 单词  ·  \(document.lineCount) 行")
                    .font(.system(size: 14)).foregroundStyle(.secondary)
                Spacer()
            }.padding(.horizontal, 12).frame(height: 38)
        }
        .frame(width: 500, height: 360)
        .background(colorScheme == .dark ? Color(red: 0.18, green: 0.18, blue: 0.19)
                    : Color(red: 0.87, green: 0.85, blue: 0.83))
        .clipShape(RoundedRectangle(cornerRadius: 16))
        .preferredColorScheme(state.preferredScheme)
    }

    private func formatButton(_ label: String, format: ReplicaRichTextDocument.Format, active: Bool) -> some View {
        Button { document.toggle(format) } label: {
            Text(label).font(.system(size: 14)).frame(width: 16, height: 24)
                .background(active ? Color.primary.opacity(0.10) : .clear, in: RoundedRectangle(cornerRadius: 4))
        }
        .buttonStyle(.plain)
        .accessibilityLabel(format == .bold ? "粗体" : format == .italic ? "斜体" : format == .underline ? "下划线" : "删除线")
    }

    private func save() {
        guard document.content.length > 0 else { return }
        do {
            if let item {
                try state.store.updateRichTextItem(id: item.id, attributedString: document.content)
            } else {
                let rtf = try document.content.data(from: NSRange(location: 0, length: document.content.length),
                                                     documentAttributes: [.documentType: NSAttributedString.DocumentType.rtf])
                let new = ClipboardItem(title: String(document.content.string.prefix(80)),
                                        kind: .richText, plainText: document.content.string, sourceName: "Pasto",
                                        sourceBundleID: Bundle.main.bundleIdentifier,
                                        payloads: ["public.rtf": rtf, NSPasteboard.PasteboardType.string.rawValue: Data(document.content.string.utf8)])
                let id = try state.store.add(new)
                if let board = state.pinboardID { try state.store.assign(ids: [id], to: board) }
            }
            state.normalizeSelection()
            close()
        } catch { state.controller?.presentError(error) }
    }
}

@MainActor
struct ReplicaStackView: View {
    @ObservedObject var state: ReplicaUIState
    var body: some View {
        VStack(spacing: 0) {
            ZStack {
                Text("Pasto Stack").font(.system(size: 12, weight: .medium))
                HStack {
                    Button { state.controller?.hideStack() } label: { Image(systemName: "xmark.circle.fill") }
                        .accessibilityLabel("关闭 Pasto Stack")
                    Spacer()
                    Button { state.reverseStack() } label: { Image(systemName: "arrow.up.arrow.down") }
                        .accessibilityLabel("反转 Stack 顺序")
                }.buttonStyle(.plain).padding(.horizontal, 8)
            }.frame(height: 32)
            if state.stackItems.isEmpty {
                Text("Empty").font(.system(size: 12)).foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity).frame(height: 44)
            } else {
                ReplicaStackTable(state: state)
                    .frame(height: CGFloat(min(10, max(1, state.stackItems.count)) * 44))
            }
        }
        .frame(width: 264)
        .background(.regularMaterial).clipShape(RoundedRectangle(cornerRadius: 10))
        .preferredColorScheme(state.preferredScheme)
    }
}

@MainActor
struct ReplicaStackTable: NSViewRepresentable {
    @ObservedObject var state: ReplicaUIState

    func makeCoordinator() -> OriginalStackTableController { OriginalStackTableController() }
    func makeNSView(context: Context) -> NSScrollView {
        state.controller?.stackTableController = context.coordinator
        return context.coordinator.scrollView
    }
    func updateNSView(_ view: NSScrollView, context: Context) {
        let controller = context.coordinator
        controller.removeActionTitle = OriginalShortcutRecorder.removeTitle
        controller.removeSnippet = { expectedIDs, row in
            let visibleOffsets = state.stackIDs.indices.filter { index in
                state.store.items.contains { $0.id == state.stackIDs[index] && !$0.isDeleted }
            }
            guard visibleOffsets.indices.contains(row),
                  visibleOffsets.map({ state.stackIDs[$0] }) == expectedIDs else { return false }
            state.stackIDs.remove(at: visibleOffsets[row])
            return true
        }
        controller.makeCell = { item in
            NSHostingView(rootView:
                OriginalStackSnippetCellView(item: item, imageProvider: { item in
                    if let application = state.store.sourceApplication(for: item) {
                        return application.rawIcon.flatMap(NSImage.init(data:)) ?? NSImage()
                    }
                    return NSImage(systemSymbolName: "doc.on.clipboard.fill", accessibilityDescription: nil)
                }).frame(maxWidth: .infinity).frame(height: 44)
                .contextMenu {
                    Button("复制") { state.controller?.copy(item: item, plainTextOnly: false) }
                    Button("粘贴") {
                        if state.controller?.paste(item: item, plainTextOnly: false) == true {
                            state.stackIDs.removeAll { $0 == item.id }
                            if state.stackItems.isEmpty { state.controller?.hideStack() }
                        }
                    }
                    Button("预览") { state.controller?.showPreview(item: item) }
                    Button("移除") { state.stackIDs.removeAll { $0 == item.id } }
                })
        }
        controller.updateSnippets(state.stackItems)
    }
}

@MainActor
struct ReplicaSettingsView: View {
    @ObservedObject var state: ReplicaUIState
    @State private var exclusions = ""
    @State private var tab = 0
    @State private var shortcutError = ""
    @State private var backgroundEnabled = BackgroundService.isEnabled

    var body: some View {
        HStack(spacing: 0) {
            VStack(spacing: 4) {
                sidebarButton(String(localized: OriginalSettingsLocalization.f_1001dbfd4()), icon: "gearshape", index: 0)
                sidebarButton(String(localized: OriginalSettingsLocalization.f_1001e16d4()), icon: "hand.raised", index: 1)
                sidebarButton(OriginalSettingsLocalization.text("settings.shortcuts.title"), icon: "keyboard", index: 4)
                sidebarButton("MCP 与 AI 工具", icon: "point.3.connected.trianglepath.dotted", index: 5)
                Spacer()
            }
            .padding(12).padding(.top, 12)
            .frame(width: 208)
            .background(Color(nsColor: .controlBackgroundColor))
            Divider()
            Group {
                switch tab {
                case 1: privacy
                case 4: shortcuts
                case 5: mcp
                default: general
                }
            }.frame(maxWidth: .infinity, maxHeight: .infinity)
        }
        .frame(minWidth: 640, minHeight: 560)
        .preferredColorScheme(state.preferredScheme)
        .onAppear { exclusions = state.store.preferences.excludedBundleIDs.joined(separator: "\n") }
    }

    private func sidebarButton(_ title: String, icon: String, index: Int) -> some View {
        Button { tab = index } label: {
            Label(title, systemImage: icon).font(.system(size: 13))
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.horizontal, 10).padding(.vertical, 9)
                .background(tab == index ? Color.accentColor.opacity(0.16) : .clear,
                            in: RoundedRectangle(cornerRadius: 7))
        }.buttonStyle(.plain).accessibilityLabel(title)
    }

    private var general: some View {
        Form {
            Section {
                Toggle(OriginalSettingsLocalization.text("settings.open-at-login.title"), isOn: Binding(get: { state.store.preferences.launchAtLogin },
                                              set: { value in setLaunchAtLogin(value) }))
                Toggle(OriginalSettingsLocalization.text("settings.run-in-background.title"), isOn: Binding(get: { backgroundEnabled }, set: { value in
                    BackgroundService.setEnabled(value)
                }))
                .onReceive(BackgroundService.enabledChanges) { backgroundEnabled = $0 }
                Toggle(String(localized: OriginalSettingsLocalization.f_1001e28d4()), isOn: preference(\.playSounds))
            }
            Section(OriginalSettingsLocalization.text("settings.paste-items.title")) {
                Picker(OriginalSettingsLocalization.text("settings.paste-items.title"), selection: preference(\.pasteToActiveApp)) {
                    Text(OriginalSettingsLocalization.text("settings.paste-items.active-app.title")).tag(true)
                    Text(OriginalSettingsLocalization.text("settings.paste-items.clipboard.title")).tag(false)
                }
                .pickerStyle(.radioGroup)
                .labelsHidden()
                Toggle(OriginalSettingsLocalization.text("settings.paste-items.plain-text.title"), isOn: preference(\.alwaysPastePlainText))
            }
            Section(OriginalSettingsLocalization.text("settings.history.title")) {
                Slider(value: Binding(get: {
                    Double([1, 7, 30, 365, 0].firstIndex(of: state.store.preferences.historyRetentionDays) ?? 4)
                }, set: { value in
                    let index = max(0, min(4, Int(value.rounded())))
                    state.store.preferences.historyRetentionDays = [1, 7, 30, 365, 0][index]
                    state.perform { try state.store.save() }
                }), in: 0...4, step: 1)
                .accessibilityLabel(OriginalSettingsLocalization.text("settings.history.title"))
                HStack {
                    ForEach(["天", "周", "个月", "年", OriginalSettingsLocalization.text("settings.history.forever")], id: \.self) { title in
                        Text(title).frame(maxWidth: .infinity)
                    }
                }.font(.caption).foregroundStyle(.secondary)
                Button(OriginalSettingsLocalization.text("general.action.erase-history")) { state.controller?.clearHistory() }
            }
        }
        .formStyle(.grouped)
    }

    private var privacy: some View {
        Form {
            Section("内容与窗口") {
                Toggle(OriginalSettingsLocalization.text("settings.privacy.screensharing.title"), isOn: preference(\.showDuringScreenSharing))
                Toggle(OriginalSettingsLocalization.text("settings.privacy.confidential-content.title"), isOn: preference(\.ignoreConcealedContent))
                Toggle(OriginalSettingsLocalization.text("settings.privacy.autogenerated-content.title"), isOn: preference(\.ignoreTransientContent))
                Toggle(OriginalSettingsLocalization.text("replica.settings.privacy.saved-link-preview.title"), isOn: preference(\.linkPreviewsEnabled))
                    .controlSize(.mini)
                Text(OriginalSettingsLocalization.text("replica.settings.privacy.saved-link-preview.subtitle"))
                    .font(.caption).foregroundStyle(.secondary)
            }
            Section(OriginalSettingsLocalization.text("settings.privacy.applications-history.title")) {
                Text("每行输入一个应用 Bundle ID，例如 com.apple.Safari。列表中的应用不会被采集。")
                    .font(.caption).foregroundStyle(.secondary)
                TextEditor(text: $exclusions).font(.system(.body, design: .monospaced))
                    .frame(height: 125).accessibilityLabel("排除来源 Bundle ID 列表")
                HStack {
                    Button("添加应用…", action: chooseExcludedApp)
                    Spacer()
                    Button("保存排除列表") {
                        state.store.preferences.excludedBundleIDs = Array(Set(exclusions
                            .components(separatedBy: .newlines)
                            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
                            .filter { !$0.isEmpty })).sorted()
                        exclusions = state.store.preferences.excludedBundleIDs.joined(separator: "\n")
                        state.perform { try state.store.save() }
                    }
                }
            }
            Section("系统权限") {
                Text("直接粘贴需要辅助功能权限。你可以在系统设置中授权或撤销。")
                    .font(.caption).foregroundStyle(.secondary)
                Button(OriginalSettingsLocalization.text("settings.paste-items.accessibility-access-request")) {
                    _ = OriginalEnableAccessibilityModal.run()
                }
            }
        }
        .formStyle(.grouped)
    }

    private var shortcuts: some View {
        Form {
            Section(OriginalSettingsLocalization.text("settings.shortcuts.title")) {
                shortcutRecorder(ReplicaBrand.replacingOriginalName(in: OriginalSettingsLocalization.text("settings.shortcuts.activate-paste.title")), path: \.historyShortcut)
                shortcutRecorder(ReplicaBrand.replacingOriginalName(in: OriginalSettingsLocalization.text("settings.shortcuts.activate-paste-stack.title")), path: \.stackShortcut)
                shortcutRecorder(OriginalSettingsLocalization.text("pasto.settings.shortcuts.next-group.title"), path: \.nextPinboardShortcut)
                shortcutRecorder(OriginalSettingsLocalization.text("pasto.settings.shortcuts.previous-group.title"), path: \.previousPinboardShortcut)
                Picker(OriginalSettingsLocalization.text("settings.shortcuts.quick-paste.title"), selection: preference(\.quickPasteModifierRawValue)) {
                    Text("⌘ Command + 1…9").tag(NSEvent.ModifierFlags.command.rawValue)
                    Text("⌥ Option + 1…9").tag(NSEvent.ModifierFlags.option.rawValue)
                    Text("⌃ Control + 1…9").tag(NSEvent.ModifierFlags.control.rawValue)
                    Text("未设置").tag(UInt(0))
                }
                Picker(OriginalSettingsLocalization.text("settings.shortcuts.plain-text.title"), selection: preference(\.plainTextModifierRawValue)) {
                    Text("⇧ Shift").tag(NSEvent.ModifierFlags.shift.rawValue)
                    Text("⌥ Option").tag(NSEvent.ModifierFlags.option.rawValue)
                    Text("⌃ Control").tag(NSEvent.ModifierFlags.control.rawValue)
                    Text("未设置").tag(UInt(0))
                }
                Button(OriginalSettingsLocalization.text("settings.shortcuts.action.reset")) { resetShortcuts() }
                if !shortcutError.isEmpty { Text(shortcutError).foregroundStyle(.red).font(.caption) }
                if !state.hotKeyStatusMessage.isEmpty {
                    Text(state.hotKeyStatusMessage).font(.caption).foregroundStyle(.secondary)
                }
            }
            Section("项目") {
                shortcut("切换选择", "←  →")
                shortcut("扩展选择", "⇧←  ⇧→")
                shortcut("预览", "Space")
                shortcut("粘贴", "Return")
                shortcut(OriginalSettingsLocalization.text("settings.shortcuts.quick-paste.title"), "⌘1…9")
                shortcut("纯文本粘贴", "⇧Return / ⌘Return")
                shortcut("拷贝", "⌘C")
                shortcut("删除", "Delete")
            }
        }
        .formStyle(.grouped)
    }

    private func shortcutRecorder(_ title: String, path: WritableKeyPath<AppPreferences, PastoCore.KeyboardShortcut?>) -> some View {
        HStack {
            Text(title)
            Spacer()
            ReplicaShortcutRecorder(shortcut: Binding(get: { state.store.preferences[keyPath: path] }, set: { value in
                let paths: [WritableKeyPath<AppPreferences, PastoCore.KeyboardShortcut?>] = [
                    \.historyShortcut, \.stackShortcut, \.nextPinboardShortcut, \.previousPinboardShortcut]
                if let value, paths.contains(where: { $0 != path && state.store.preferences[keyPath: $0] == value }) {
                    shortcutError = "此快捷键已用于其他 Pasto 命令。"
                    return
                }
                shortcutError = ""
                state.store.preferences[keyPath: path] = value
                state.perform { try state.store.save() }
                state.controller?.hotKeyConfigurationChanged?()
            }), label: title, error: { shortcutError = $0 }, recordingChanged: {
                state.controller?.hotKeyRecordingChanged?($0)
            }).frame(width: 120, height: 24)
        }
    }

    private func resetShortcuts() {
        let alert = NSAlert()
        alert.messageText = OriginalSettingsLocalization.text("settings.shortcuts.action.reset.confirmation")
        alert.addButton(withTitle: OriginalSettingsLocalization.text("general.action.reset")); alert.addButton(withTitle: OriginalSettingsLocalization.text("general.action.cancel"))
        guard alert.runModal() == .alertFirstButtonReturn else { return }
        state.store.preferences.historyShortcut = .historyDefault
        state.store.preferences.stackShortcut = .stackDefault
        state.store.preferences.nextPinboardShortcut = .nextPinboardDefault
        state.store.preferences.previousPinboardShortcut = .previousPinboardDefault
        state.store.preferences.quickPasteModifierRawValue = NSEvent.ModifierFlags.command.rawValue
        state.store.preferences.plainTextModifierRawValue = NSEvent.ModifierFlags.shift.rawValue
        state.perform { try state.store.save() }
        state.controller?.hotKeyConfigurationChanged?()
        shortcutError = ""
    }

    private var mcpExecutable: URL {
        (Bundle.main.executableURL?.deletingLastPathComponent() ?? URL(fileURLWithPath: CommandLine.arguments[0]).deletingLastPathComponent())
            .appendingPathComponent("pasto-mcp")
    }

    private var mcpConfiguration: String {
        let object: [String: Any] = ["mcpServers": ["pasto": [
            "command": mcpExecutable.path, "args": ["--data-dir", state.store.directoryURL.path]
        ]]]
        guard let data = try? JSONSerialization.data(withJSONObject: object, options: [.prettyPrinted, .sortedKeys]),
              let value = String(data: data, encoding: .utf8) else { return "" }
        return value
    }

    private var mcp: some View {
        Form {
            Section("MCP 服务") {
                Label(FileManager.default.isExecutableFile(atPath: mcpExecutable.path) ? "可执行文件已就绪" : "未找到 MCP 可执行文件",
                      systemImage: FileManager.default.isExecutableFile(atPath: mcpExecutable.path) ? "checkmark.circle" : "exclamationmark.circle")
                Text("连接 MCP 客户端后，可以搜索和读取内容、创建项目及管理 Pasto。服务由客户端通过标准输入输出启动。")
                    .font(.caption).foregroundStyle(.secondary)
            }
            Section("客户端配置") {
                Text(mcpConfiguration).font(.system(size: 11, design: .monospaced)).textSelection(.enabled)
                    .padding(8).frame(maxWidth: .infinity, alignment: .leading)
                Button("复制配置") {
                    let pasteboard = state.controller?.pasteboard ?? .general
                    pasteboard.clearContents()
                    if !pasteboard.setString(mcpConfiguration, forType: .string) {
                        state.controller?.showError(message: "无法复制 MCP 配置。")
                    }
                }.disabled(!FileManager.default.isExecutableFile(atPath: mcpExecutable.path))
            }
        }
        .formStyle(.grouped)
    }

    private func shortcut(_ title: String, _ keys: String) -> some View {
        HStack { Text(title); Spacer(); Text(keys).font(.system(.body, design: .monospaced)).foregroundStyle(.secondary) }
    }

    private func preference<Value>(_ keyPath: WritableKeyPath<AppPreferences, Value>) -> Binding<Value> {
        Binding(get: { state.store.preferences[keyPath: keyPath] }, set: { value in
            state.store.preferences[keyPath: keyPath] = value
            if (keyPath as AnyKeyPath) == (\AppPreferences.isMonitoringPaused as AnyKeyPath) {
                state.store.preferences.pauseUntil = nil
            }
            state.perform { try state.store.save() }
        })
    }

    private func chooseExcludedApp() {
        let panel = NSOpenPanel()
        panel.title = "选择不采集的应用"
        panel.allowedContentTypes = [.application]
        panel.directoryURL = URL(fileURLWithPath: "/Applications")
        panel.allowsMultipleSelection = true
        if panel.runModal() == .OK {
            let ids = panel.urls.compactMap { Bundle(url: $0)?.bundleIdentifier }
            let current = exclusions.components(separatedBy: .newlines).filter { !$0.isEmpty }
            exclusions = Array(Set(current + ids)).sorted().joined(separator: "\n")
        }
    }

    private func setLaunchAtLogin(_ enabled: Bool) {
        do {
            if enabled { try SMAppService.mainApp.register() }
            else { try SMAppService.mainApp.unregister() }
            state.store.preferences.launchAtLogin = enabled
            try state.store.save()
        } catch { state.controller?.presentError(error) }
    }


}
