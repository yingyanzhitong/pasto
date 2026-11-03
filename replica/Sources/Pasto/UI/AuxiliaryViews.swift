import AppKit
import ApplicationServices
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
            if state.stackItemIDs.isEmpty {
                Text("Empty").font(.system(size: 12)).foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity).frame(height: 44)
            } else {
                ReplicaStackTable(state: state)
                    .frame(height: CGFloat(min(10, max(1, state.stackItemIDs.count)) * 44))
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
                state.hasStackItem(state.stackIDs[index])
            }
            guard visibleOffsets.indices.contains(row),
                  visibleOffsets.map({ state.stackIDs[$0] }) == expectedIDs else { return false }
            state.stackIDs.remove(at: visibleOffsets[row])
            return true
        }
        controller.makeNativeCell = { [weak controller] input, row in
            let expectedIDs = controller?.snippetIDs ?? []
            return NSHostingView(rootView:
                OriginalStackSnippetCellView(input: input, imageProvider: { current in
                    if let rawType = current.previewRawType() {
                        return OriginalStackCategoryIcons.image(for: OriginalPasteboardContentKind(rawValue: UInt8(rawType)) ?? .unknown)
                    }
                    return OriginalStackCategoryIcons.image(for: state.store.originalContentKind(of: current.resolvedItem()))
                }).frame(maxWidth: .infinity).frame(height: 44)
                .contextMenu {
                    Button("复制") { state.controller?.copy(input: input, plainTextOnly: false) }
                    Button("粘贴") {
                        if state.controller?.pasteStackItem(id: input.id, plainTextOnly: false) == true {
                            controller?.removeRow(at: row, expectedIDs: expectedIDs)
                            if state.stackItemIDs.isEmpty { state.controller?.hideStack() }
                        }
                    }
                    Button("预览") { state.controller?.showPreview(item: input.resolvedItem(), input: input) }
                    Button("移除") { controller?.removeRow(at: row, expectedIDs: expectedIDs) }
                })
        }
        controller.updateNativeSnippets(state.stackSnippetInputs)
    }
}

@MainActor
struct ReplicaSettingsView: View {
    @ObservedObject var state: ReplicaUIState
    @Environment(\.colorScheme) private var colorScheme
    @State private var selectedExclusions: Set<String> = []
    @State private var showingMCPConfiguration = false
    @State private var tab: Int? = 0
    @State private var shortcutError = ""
    @State private var backgroundEnabled = BackgroundService.isEnabled

    var body: some View {
        OriginalSettingsSplitView(sidebar: AnyView(sidebar), detail: AnyView(detail.ignoresSafeArea(.container, edges: .top)))
            .ignoresSafeArea(.container, edges: .top)
            .frame(minWidth: 640)
            .preferredColorScheme(state.preferredScheme)
    }

    private var sidebar: some View {
        VStack(spacing: 0) {
            List(selection: $tab) {
                sidebarRow(String(localized: OriginalSettingsLocalization.f_1001dbfd4()), icon: "gearshape", index: 0)
                sidebarRow(String(localized: OriginalSettingsLocalization.f_1001e16d4()), icon: "hand.raised", index: 1)
                sidebarRow(OriginalSettingsLocalization.text("settings.shortcuts.title"), icon: "keyboard", index: 4)
                sidebarRow(OriginalSettingsLocalization.text("settings.mcp.title"), icon: "point.3.connected.trianglepath.dotted", index: 5)
            }
            .listStyle(.sidebar)
            .padding(.top, sidebarTopInset)
            Link(destination: URL(string: "https://yingyanzhitong.github.io/pasto/#faq")!) {
                Label(OriginalSettingsLocalization.text("general.help-center"), systemImage: "questionmark.circle")
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .contentShape(Rectangle())
            }
            .buttonStyle(.plain)
            .foregroundStyle(.secondary)
            .padding(16)
        }
    }

    private var sidebarTopInset: CGFloat {
        if #available(macOS 26, *) { return -16 }
        return 0
    }

    private var paneTitle: String {
        switch tab ?? 0 {
        case 1: return String(localized: OriginalSettingsLocalization.f_1001e16d4())
        case 4: return OriginalSettingsLocalization.text("settings.shortcuts.title")
        case 5: return OriginalSettingsLocalization.text("settings.mcp.title")
        default: return String(localized: OriginalSettingsLocalization.f_1001dbfd4())
        }
    }

    private var detail: some View {
        VStack(alignment: .leading, spacing: 0) {
            Text(paneTitle)
                .font(.system(size: 13, weight: .semibold))
                .padding(.horizontal, 30)
                .frame(height: 44, alignment: .center)
            Group {
                switch tab ?? 0 {
                case 1: privacy
                case 4: shortcuts
                case 5: mcp
                default: general
                }
            }.frame(maxWidth: .infinity, maxHeight: .infinity)
        }
    }

    private func sidebarRow(_ title: String, icon: String, index: Int) -> some View {
        Label(title, systemImage: icon).font(.system(size: 13))
            .frame(maxWidth: .infinity, alignment: .leading)
            .contentShape(Rectangle())
            .tag(index)
            .accessibilityLabel(title)
    }

    private func pasteDestination(_ title: String, subtitle: String) -> some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(OriginalSettingsLocalization.text(title))
            Text(OriginalSettingsLocalization.text(subtitle))
                .font(.caption).foregroundStyle(.secondary)
                .fixedSize(horizontal: false, vertical: true)
        }
        .padding(.vertical, 4)
        .frame(maxWidth: .infinity, alignment: .leading)
        .contentShape(Rectangle())
    }

    private func settingsToggle(_ title: String, subtitle: String, isOn: Binding<Bool>) -> some View {
        HStack {
            VStack(alignment: .leading, spacing: 3) {
                Text(OriginalSettingsLocalization.text(title))
                Text(ReplicaBrand.replacingOriginalName(in: OriginalSettingsLocalization.text(subtitle)))
                    .font(.caption).foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }
            Spacer()
            Toggle(OriginalSettingsLocalization.text(title), isOn: isOn)
                .labelsHidden().toggleStyle(.switch).controlSize(.mini)
        }
        .frame(minHeight: 42)
    }

    private func settingsSwitch(_ title: String, isOn: Binding<Bool>) -> some View {
        HStack {
            Text(title)
            Spacer()
            Toggle(title, isOn: isOn).labelsHidden().toggleStyle(.switch).controlSize(.mini)
        }.frame(minHeight: 30)
    }

    private func excludedApplication(_ identifier: String) -> some View {
        let url = NSWorkspace.shared.urlForApplication(withBundleIdentifier: identifier)
        return HStack(spacing: 8) {
            Image(nsImage: url.map { NSWorkspace.shared.icon(forFile: $0.path) }
                  ?? NSImage(systemSymbolName: "app", accessibilityDescription: nil)!)
                .resizable().frame(width: 20, height: 20)
            Text(url.map { FileManager.default.displayName(atPath: $0.path) } ?? identifier).lineLimit(1)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .contentShape(Rectangle())
        .help(identifier)
    }

    private func removeExcludedApps() {
        guard !selectedExclusions.isEmpty else { return }
        state.store.preferences.excludedBundleIDs.removeAll { selectedExclusions.contains($0) }
        selectedExclusions.removeAll()
        state.perform { try state.store.save() }
    }

    private var general: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 32) {
                settingsCard {
                    settingsSwitch(OriginalSettingsLocalization.text("settings.open-at-login.title"), isOn: Binding(get: { state.store.preferences.launchAtLogin },
                        set: { value in setLaunchAtLogin(value) }))
                    Divider()
                    settingsSwitch(OriginalSettingsLocalization.text("settings.run-in-background.title"), isOn: Binding(get: { backgroundEnabled }, set: { value in
                        BackgroundService.setEnabled(value)
                    }))
                    .onReceive(BackgroundService.enabledChanges) { backgroundEnabled = $0 }
                    Divider()
                    ICloudSyncGeneralRow(sync: state.originalCloudSync, drive: state.cloudSync)
                        .frame(minHeight: 30)
                    Divider()
                    settingsSwitch(String(localized: OriginalSettingsLocalization.f_1001e28d4()), isOn: preference(\.playSounds))
                }
                VStack(alignment: .leading, spacing: 8) {
                    settingsSectionTitle(OriginalSettingsLocalization.text("settings.paste-items.title"))
                    settingsCard {
                        ZStack(alignment: state.store.preferences.pasteToActiveApp ? .topTrailing : .bottomTrailing) {
                            Picker(OriginalSettingsLocalization.text("settings.paste-items.title"), selection: preference(\.pasteToActiveApp)) {
                                pasteDestination("settings.paste-items.active-app.title", subtitle: "settings.paste-items.active-app.info").tag(true)
                                pasteDestination("settings.paste-items.clipboard.title", subtitle: "settings.paste-items.clipboard.info").tag(false)
                            }
                            .pickerStyle(.radioGroup).labelsHidden()
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .padding(.trailing, 100)
                            if let illustration = OriginalSettingsIllustrations.image(directPaste: state.store.preferences.pasteToActiveApp, dark: colorScheme == .dark) {
                                Image(nsImage: illustration).resizable().scaledToFit()
                                    .frame(width: 96, height: 64)
                                    .clipShape(RoundedRectangle(cornerRadius: 8)).accessibilityHidden(true)
                                    .allowsHitTesting(false)
                            }
                        }
                        Divider().padding(.vertical, 8)
                        Toggle(OriginalSettingsLocalization.text("settings.paste-items.plain-text.title"), isOn: preference(\.alwaysPastePlainText))
                            .toggleStyle(.checkbox)
                        if state.store.preferences.pasteToActiveApp && !AXIsProcessTrusted() {
                            Button(OriginalSettingsLocalization.text("settings.paste-items.accessibility-access-request")) {
                                _ = OriginalEnableAccessibilityModal.run()
                            }.padding(.top, 8)
                        }
                    }
                }
                VStack(alignment: .leading, spacing: 8) {
                    settingsSectionTitle(OriginalSettingsLocalization.text("settings.history.title"))
                    settingsCard {
                        OriginalHistoryCapacitySlider(days: Binding(get: { state.store.preferences.historyRetentionDays }, set: { days in
                            state.store.preferences.historyRetentionDays = days
                            state.perform { try state.store.save() }
                        }))
                        .padding(.vertical, 4)
                        Divider().padding(.vertical, 8)
                        HStack {
                            Spacer()
                            Button(OriginalSettingsLocalization.text("general.action.erase-history") + "…") {
                                state.controller?.clearHistory()
                            }
                        }
                    }
                }
            }
            .padding(.horizontal, 20).padding(.top, 8).padding(.bottom, 20)
        }
    }

    private func settingsSectionTitle(_ title: String) -> some View {
        Text(title).font(.system(size: 13, weight: .semibold)).padding(.leading, 10)
    }

    private func settingsCard<Content: View>(verticalPadding: CGFloat = 10, @ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 0, content: content)
            .padding(.horizontal, 10).padding(.vertical, verticalPadding)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Color.primary.opacity(0.035), in: RoundedRectangle(cornerRadius: 12))
    }

    private var privacy: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                settingsCard {
                    settingsToggle("settings.privacy.screensharing.title", subtitle: "settings.privacy.screensharing.subtitle", isOn: preference(\.showDuringScreenSharing))
                    Divider()
                    settingsToggle("replica.settings.privacy.saved-link-preview.title", subtitle: "replica.settings.privacy.saved-link-preview.subtitle", isOn: preference(\.linkPreviewsEnabled))
                }
                settingsCard {
                    settingsToggle("settings.privacy.confidential-content.title", subtitle: "settings.privacy.confidential-content.subtitle", isOn: preference(\.ignoreConcealedContent))
                    Divider()
                    settingsToggle("settings.privacy.autogenerated-content.title", subtitle: "settings.privacy.autogenerated-content.subtitle", isOn: preference(\.ignoreTransientContent))
                }
                VStack(alignment: .leading, spacing: 8) {
                    VStack(alignment: .leading, spacing: 3) {
                        Text(OriginalSettingsLocalization.text("settings.privacy.applications-history.title")).font(.system(size: 13, weight: .semibold))
                        Text(OriginalSettingsLocalization.text("settings.privacy.applications-history.subtitle"))
                            .font(.callout).foregroundStyle(.secondary)
                    }.padding(.horizontal, 10).padding(.top, 8)
                    VStack(spacing: 0) {
                        List(state.store.preferences.excludedBundleIDs, id: \.self, selection: $selectedExclusions) { identifier in
                            excludedApplication(identifier).tag(identifier)
                                .listRowInsets(EdgeInsets(top: 6, leading: 10, bottom: 6, trailing: 10))
                                .listRowBackground(Color.clear)
                        }
                        .listStyle(.plain).scrollContentBackground(.hidden)
                        .onDeleteCommand(perform: removeExcludedApps)
                        .overlay {
                            if state.store.preferences.excludedBundleIDs.isEmpty {
                                Text(OriginalSettingsLocalization.text("settings.privacy.applications-history.empty"))
                                    .foregroundStyle(.secondary).allowsHitTesting(false)
                            }
                        }
                        .frame(height: min(180, max(40, CGFloat(state.store.preferences.excludedBundleIDs.count) * 40)))
                        Divider()
                        HStack(spacing: 0) {
                            Button(action: chooseExcludedApp) { Image(systemName: "plus").frame(width: 20, height: 24) }
                                .accessibilityLabel("添加应用")
                            Divider().frame(height: 16)
                            Button(action: removeExcludedApps) { Image(systemName: "minus").frame(width: 20, height: 24) }
                                .disabled(selectedExclusions.isEmpty).accessibilityLabel("移除应用")
                            Spacer()
                        }.buttonStyle(.borderless)
                    }
                    .background(Color.primary.opacity(0.035), in: RoundedRectangle(cornerRadius: 12))
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                }
            }
            .padding(.horizontal, 20).padding(.top, 8).padding(.bottom, 20)
        }
    }

    private var shortcuts: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                settingsCard(verticalPadding: 0) {
                    shortcutRecorder(ReplicaBrand.replacingOriginalName(in: OriginalSettingsLocalization.text("settings.shortcuts.activate-paste.title")), path: \.historyShortcut)
                    Divider()
                    shortcutRecorder(ReplicaBrand.replacingOriginalName(in: OriginalSettingsLocalization.text("settings.shortcuts.activate-paste-stack.title")), path: \.stackShortcut)
                }
                .help(state.hotKeyStatusMessage)
                settingsCard(verticalPadding: 0) {
                    shortcutRecorder(OriginalSettingsLocalization.text("pasto.settings.shortcuts.next-group.title"), path: \.nextPinboardShortcut)
                    Divider()
                    shortcutRecorder(OriginalSettingsLocalization.text("pasto.settings.shortcuts.previous-group.title"), path: \.previousPinboardShortcut)
                }
                settingsCard(verticalPadding: 0) {
                    HStack {
                        Text(OriginalSettingsLocalization.text("settings.shortcuts.quick-paste.title"))
                        Spacer()
                        Picker(OriginalSettingsLocalization.text("settings.shortcuts.quick-paste.title"), selection: preference(\.quickPasteModifierRawValue)) {
                            Text("⌘ Command").tag(NSEvent.ModifierFlags.command.rawValue)
                            Text("⌥ Option").tag(NSEvent.ModifierFlags.option.rawValue)
                            Text("⌃ Control").tag(NSEvent.ModifierFlags.control.rawValue)
                            Text("未设置").tag(UInt(0))
                        }.labelsHidden().pickerStyle(.menu).buttonStyle(.borderless)
                            .padding(.vertical, 2).fixedSize()
                        Text("+ 1...9")
                    }.frame(minHeight: 36)
                    Divider()
                    HStack {
                        Text(OriginalSettingsLocalization.text("settings.shortcuts.plain-text.title"))
                        Spacer()
                        Picker(OriginalSettingsLocalization.text("settings.shortcuts.plain-text.title"), selection: preference(\.plainTextModifierRawValue)) {
                            Text("⇧ Shift").tag(NSEvent.ModifierFlags.shift.rawValue)
                            Text("⌥ Option").tag(NSEvent.ModifierFlags.option.rawValue)
                            Text("⌃ Control").tag(NSEvent.ModifierFlags.control.rawValue)
                            Text("未设置").tag(UInt(0))
                        }.labelsHidden().pickerStyle(.menu).buttonStyle(.borderless)
                            .padding(.vertical, 2).fixedSize()
                    }.frame(minHeight: 36)
                }
                if !shortcutError.isEmpty { Text(shortcutError).foregroundStyle(.red).font(.caption) }
                HStack {
                    Spacer()
                    Button(OriginalSettingsLocalization.text("settings.shortcuts.action.reset") + "...") { resetShortcuts() }
                }
            }
            .padding(.horizontal, 20).padding(.top, 8).padding(.bottom, 20)
        }
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
        }.frame(minHeight: 36)
    }

    private func resetShortcuts() {
        let alert = NSAlert()
        alert.messageText = OriginalSettingsLocalization.text("settings.shortcuts.action.reset.confirmation")
        alert.addButton(withTitle: OriginalSettingsLocalization.text("general.action.reset")); alert.addButton(withTitle: OriginalSettingsLocalization.text("general.action.cancel"))
        alert.buttons[0].keyEquivalent = ""
        alert.buttons[1].keyEquivalent = "\r"
        alert.window.defaultButtonCell = alert.buttons[1].cell as? NSButtonCell
        if let window = NSApp.keyWindow {
            alert.beginSheetModal(for: window) { response in
                if response == .alertFirstButtonReturn { applyDefaultShortcuts() }
            }
        } else if alert.runModal() == .alertFirstButtonReturn { applyDefaultShortcuts() }
    }

    private func applyDefaultShortcuts() {
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
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                settingsCard {
                    Label(FileManager.default.isExecutableFile(atPath: mcpExecutable.path) ? "可连接 AI 工具" : "MCP 服务暂不可用",
                          systemImage: FileManager.default.isExecutableFile(atPath: mcpExecutable.path) ? "checkmark.circle" : "exclamationmark.circle")
                        .padding(.bottom, 4)
                    Text("连接 AI 工具，让它们搜索、读取和整理保存在 Pasto 中的内容。连接由你选择的客户端在本机建立。")
                        .font(.callout).foregroundStyle(.secondary)
                        .fixedSize(horizontal: false, vertical: true)
                }
                HStack {
                    Spacer()
                    Button(OriginalSettingsLocalization.text("settings.mcp.connect.action.connect-to")) {
                        showingMCPConfiguration = true
                    }.disabled(!FileManager.default.isExecutableFile(atPath: mcpExecutable.path))
                }
            }
            .padding(.horizontal, 20).padding(.top, 8).padding(.bottom, 20)
        }
        .sheet(isPresented: $showingMCPConfiguration) {
            VStack(alignment: .leading, spacing: 16) {
                Text("连接 AI 工具").font(.headline)
                Text("将以下配置添加到支持 MCP 的客户端。客户端会在本机启动 Pasto 服务。")
                    .font(.callout).foregroundStyle(.secondary)
                ScrollView {
                    Text(mcpConfiguration).font(.system(size: 11, design: .monospaced))
                        .textSelection(.enabled).frame(maxWidth: .infinity, alignment: .leading).padding(12)
                }
                .frame(height: 180)
                .background(Color(nsColor: .textBackgroundColor), in: RoundedRectangle(cornerRadius: 8))
                HStack {
                    Button(OriginalSettingsLocalization.text("settings.mcp.copy")) {
                        let pasteboard = state.controller?.pasteboard ?? .general
                        pasteboard.clearContents()
                        if !pasteboard.setString(mcpConfiguration, forType: .string) {
                            state.controller?.showError(message: "无法复制 MCP 配置。")
                        }
                    }
                    Spacer()
                    Button(OriginalSettingsLocalization.text("settings.mcp.connection-sheet.done")) {
                        showingMCPConfiguration = false
                    }.keyboardShortcut(.defaultAction)
                }
            }
            .padding(24).frame(width: 420)
        }
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
        let complete: (NSApplication.ModalResponse) -> Void = { response in
            guard response == .OK else { return }
            let identifiers = panel.urls.compactMap { Bundle(url: $0)?.bundleIdentifier }
            state.store.preferences.excludedBundleIDs = Array(Set(state.store.preferences.excludedBundleIDs + identifiers)).sorted()
            state.perform { try state.store.save() }
        }
        if let window = NSApp.keyWindow { panel.beginSheetModal(for: window, completionHandler: complete) }
        else { complete(panel.runModal()) }
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
