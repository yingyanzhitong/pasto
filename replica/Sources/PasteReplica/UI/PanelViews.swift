import AppKit
import SwiftUI
import UniformTypeIdentifiers
import PasteReplicaCore

@MainActor
struct ReplicaPanelView: View {
    @ObservedObject var state: ReplicaUIState
    @State private var searchFocused = false

    var body: some View {
        GeometryReader { geometry in
            let collectionHeight = max(0, geometry.size.height - 60 - backgroundInset)
            let cardSide = max(0, collectionHeight - 32)
            VStack(spacing: 0) {
                header.frame(height: 60)
                if state.visibleItems.isEmpty {
                    VStack {
                        Spacer()
                        Text(state.searchFailed ? "本地搜索暂不可用" : "无结果")
                            .font(.system(size: 26, weight: .medium))
                            .foregroundStyle(Color(red: 185 / 255, green: 185 / 255, blue: 185 / 255))
                        if state.searchFailed { Button("重试") { state.retrySearch() } }
                        Spacer()
                    }
                    .frame(maxWidth: .infinity, minHeight: collectionHeight, maxHeight: collectionHeight)
                    .accessibilityLabel(state.searchFailed ? "本地搜索暂不可用" : "无结果")
                } else {
                    ReplicaNativeCollection(state: state, cardSide: cardSide)
                    .frame(height: collectionHeight)
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(ReplicaPanelGlassBackground(cornerRadius: backgroundRadius))
            .clipShape(RoundedRectangle(cornerRadius: backgroundRadius, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: backgroundRadius).strokeBorder(.white.opacity(0.22), lineWidth: 1))
            .padding(.horizontal, backgroundInset).padding(.bottom, backgroundInset)
        }
        .preferredColorScheme(state.preferredScheme)
        .onChange(of: state.query) { _, _ in state.normalizeSelection() }
        .onChange(of: state.searchFilters) { _, _ in state.normalizeSelection() }
        .onChange(of: state.searchFocus) { _, _ in searchFocused = true }
        .onChange(of: state.searchVisible) { _, visible in if !visible { searchFocused = false } }
        .accessibilityIdentifier("clipboard-panel")
    }

    private var backgroundInset: CGFloat {
        if #available(macOS 26, *) { return 8 }
        return 0
    }

    private var backgroundRadius: CGFloat {
        if #available(macOS 26, *) { return 26 }
        return 0
    }

    private var searching: Bool { searchFocused || state.searchVisible || !state.isSearchQueryEmpty }

    private var header: some View {
        ZStack {
            HStack { Spacer(); trailingControls }
            if searching {
                searchField
                historyControls.offset(x: 246)
            } else {
                HStack(spacing: 20) {
                    Button { state.searchVisible = true; searchFocused = true } label: {
                        Image(systemName: "magnifyingglass").font(.system(size: 19))
                    }.buttonStyle(.plain).accessibilityLabel("搜索剪贴板")
                    boardTabs
                }.fixedSize(horizontal: true, vertical: false)
            }
        }.padding(.horizontal, 24)
    }

    private var searchField: some View {
        ReplicaSearchEditor(text: $state.query, focused: $searchFocused, store: state.store,
            filters: searchFilterChips,
            onInputChange: { text, filters, nodes in state.applySearchInput(nodes: nodes, text: text, filters: filters) },
            onEnter: { state.controller?.pasteSelection(plainTextOnly: false) },
            onCancel: { state.controller?.cancelSearchOrPanel() },
            onShowFilters: { button in state.controller?.showFilterBrowser(relativeTo: button) })
            .frame(width: 400, height: 32)
    }

    private var searchFilterChips: [ReplicaSearchFilterChip] {
        state.searchFilters.map { ReplicaFilterMatching.chip($0, store: state.store) }
    }

    private var boardTabs: some View {
        HStack(spacing: 7) {
            boardButton(state.store.preferences.historyTitle, board: nil)
                .contextMenu {
                    Button("重命名") { state.controller?.renameHistory() }
                    Button("删除历史…") { state.controller?.clearHistory() }
                }
            ForEach(state.store.pinboards.sorted { $0.sortOrder < $1.sortOrder }) { board in
                boardButton(board.name, board: board)
                    .contextMenu {
                        Button("重命名") { state.controller?.renamePinboard(board) }
                        Menu("颜色") {
                            ForEach(OriginalPinboardColor.allCases, id: \.rawValue) { color in
                                Button(colorName(color)) {
                                    state.perform {
                                        try state.store.updatePinboard(id: board.id,
                                            colorHex: String(format: "%06llX", color.canonicalColorCode))
                                    }
                                }
                            }
                        }
                        Button("向左移动") { state.movePinboard(board, by: -1) }
                        Button("向右移动") { state.movePinboard(board, by: 1) }
                        Button("删除…", role: .destructive) { state.controller?.removePinboard(board) }
                    }
                    .onDrag { NSItemProvider(object: ("paste-pinboard:" + board.id.uuidString) as NSString) }
                    .onDrop(of: [UTType.text], isTargeted: nil) { providers in
                        guard let provider = providers.first else { return false }
                        _ = provider.loadObject(ofClass: String.self) { value, _ in
                            guard let value, value.hasPrefix("paste-pinboard:"), let id = UUID(uuidString: String(value.dropFirst(15))) else { return }
                            Task { @MainActor in state.movePinboard(id: id, before: board.id) }
                        }
                        return true
                    }
            }
            Button { state.controller?.createPinboard() } label: { Image(systemName: "plus").font(.system(size: 21)).frame(width: 30, height: 28) }
                .buttonStyle(.plain).accessibilityLabel("创建 Pinboard").help("创建 Pinboard (⇧⌘N)")
        }.fixedSize()
    }

    private func colorName(_ color: OriginalPinboardColor) -> String {
        switch color {
        case .red: return "红色"
        case .orange: return "橙色"
        case .yellow: return "黄色"
        case .green: return "绿色"
        case .blue: return "蓝色"
        case .purple: return "紫色"
        case .pink: return "粉色"
        case .gray: return "灰色"
        }
    }

    private func boardColor(_ board: Pinboard) -> Color {
        if let code = OriginalPinboardAttributes.colorCode(from: board.rawAttributes) {
            return Color(nsColor: OriginalPinboardColor(canonicalColorCode: code).color())
        }
        return parseColor(board.colorHex) ?? .red
    }

    private func boardButton(_ name: String, board: Pinboard?) -> some View {
        Button { state.chooseBoard(board?.id) } label: {
            HStack(spacing: 6) {
                if let board { Circle().fill(boardColor(board)).frame(width: 12, height: 12) }
                else { Image(systemName: "clock.arrow.circlepath").font(.system(size: 15)) }
                Text(name).font(.system(size: 13, weight: .medium))
            }
            .lineLimit(1).padding(.horizontal, 10).padding(.vertical, 6)
            .background(state.pinboardID == board?.id && !state.showDeleted ? Color.primary.opacity(0.10) : .clear, in: Capsule())
        }.buttonStyle(.plain).accessibilityLabel(name)
        .accessibilityAddTraits(state.pinboardID == board?.id ? .isSelected : [])
    }

    private var trailingControls: some View {
        HStack(spacing: 14) {
            Menu {
                Button {
                    NSApp.sendAction(NSSelectorFromString("about:"), to: NSApp.delegate, from: nil)
                } label: { Label("关于 Pasto", systemImage: "info.circle") }
                Divider()
                Button { state.controller?.newTextItem() } label: {
                    Label("新文本项", systemImage: "square.and.pencil")
                }
                .keyboardShortcut("n", modifiers: .command)
                Button { state.controller?.showSettings() } label: {
                    Label("设置…", systemImage: "gear")
                }
                .keyboardShortcut(",", modifiers: .command)
                Divider()
                Menu {
                    Button {
                        if let url = URL(string: "https://pasteapp.io/help") { NSWorkspace.shared.open(url) }
                    } label: { Text("帮助中心") }
                } label: { Label("帮助", systemImage: "questionmark.circle") }
                Button {
                    var components = URLComponents(string: "https://twitter.com/intent/tweet")
                    components?.queryItems = [URLQueryItem(name: "text", value: "Pasto")]
                    if let url = components?.url { NSWorkspace.shared.open(url) }
                } label: { Label("在 Twitter 上粘贴", systemImage: "at") }
                Divider()
                Menu {
                    if state.store.preferences.isMonitoringPaused {
                        Button("继续 Pasto", action: state.resumeMonitoring)
                    } else {
                        Button("暂停") { state.pauseMonitoring() }
                        ForEach([15, 30, 60, 180, 480], id: \.self) { minutes in
                            Button(minutes < 60 ? "暂停 \(minutes)分钟" : "暂停 \(minutes / 60)小时") {
                                state.pauseMonitoring(minutes: minutes)
                            }
                        }
                    }
                } label: { Label("暂停 Pasto", systemImage: "pause.circle") }
                Button { NSApp.terminate(nil) } label: {
                    Label("退出 Pasto", systemImage: "xmark.square")
                }
                .keyboardShortcut("q", modifiers: .command)
            } label: { Image(systemName: "ellipsis").frame(width: 16) }
            .menuStyle(.borderlessButton).menuIndicator(.hidden).fixedSize()
            .accessibilityLabel("更多操作")
        }
        .buttonStyle(.plain)
        .font(.system(size: 18, weight: .semibold))
        .foregroundStyle(.secondary)
        .fixedSize()
    }

    private var historyControls: some View {
        HStack(spacing: 22) {
            Button {
                state.query = ""; state.chooseBoard(nil); state.searchVisible = false; searchFocused = false
                state.controller?.panel.makeFirstResponder(nil)
            } label: { Image(systemName: "clock.arrow.circlepath").font(.system(size: 17)).frame(width: 18, height: 32) }
            .buttonStyle(.plain).accessibilityLabel("返回剪贴板历史")
            ForEach(state.store.pinboards) { board in
                Button { state.chooseBoard(board.id) } label: {
                    Circle().fill(boardColor(board)).frame(width: 12, height: 12).frame(height: 32)
                }.buttonStyle(.plain).accessibilityLabel(board.name)
            }
        }.foregroundStyle(Color(nsColor: .labelColor)).fixedSize()
    }

}

@MainActor
struct ReplicaClipboardCard: View {
    @ObservedObject var state: ReplicaUIState
    let item: ClipboardItem
    let sideLength: CGFloat
    var selectionOverride: Bool? = nil
    var dimmingOverride: Bool? = nil
    var nativeInteractions = false
    private var selected: Bool { state.selection.contains(item.id) }
    private var renderedSelected: Bool { selectionOverride ?? selected }
    @Environment(\.controlActiveState) private var activeState

    var body: some View {
        ZStack(alignment: .topLeading) {
            VStack(alignment: .leading, spacing: 0) {
                cardContent
                    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
                    .clipped()
            }
            .overlay(alignment: .bottom) {
                if let metadata = compactTextMetadata, let background = compactTextBackground {
                    OriginalCompactTextFooter(length: metadata.length, sizeClass: UInt8(sizeClass),
                                              fadingColor: background)
                        .frame(height: sizeClass == 3 ? 32 : 50)
                }
            }
            .padding(.top, cardGeometry?.bodyTop ?? headerHeight)
            cardHeader
        }
        .frame(width: sideLength, height: sideLength)
        .background(ReplicaItemPreviewAnchor(itemID: item.id, controller: state.controller))
        .background(cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: cardCornerRadius, style: cardCornerStyle))
        .background {
            if renderedSelected {
                RoundedRectangle(cornerRadius: selectionCornerRadius, style: cardCornerStyle)
                    .fill(Color(nsColor: selectionBackground))
                    .padding(-4)
            }
        }
        .shadow(color: .black.opacity(0.10), radius: 3, y: 2)
        .contentShape(RoundedRectangle(cornerRadius: cardCornerRadius, style: cardCornerStyle))
        .modifier(ReplicaCardTapHandlers(enabled: !nativeInteractions,
            single: { state.select(item, modifiers: NSEvent.modifierFlags) },
            double: {
                state.select(item)
                let plainModifiers = NSEvent.ModifierFlags(rawValue: state.store.preferences.plainTextModifierRawValue)
                state.controller?.paste(item: item, plainTextOnly: NSEvent.modifierFlags.isSuperset(of: plainModifiers))
            }))
        .background(ReplicaCardContextSelection(onContextMenu: {
            if !selected { state.select(item) }
        }))
        .contextMenu { contextMenu }
        .modifier(ReplicaCardDragHandlers(enabled: !nativeInteractions,
            provider: cardDragProvider,
            drop: { providers, location in
                receiveItemDrop(providers, after: location.x >= sideLength / 2)
            }))
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("\(item.kind.displayName)，\(item.sourceName)，\(item.title)，\(item.plainText.map { String($0.prefix(160)) } ?? "")")
        .accessibilityAddTraits(selected ? [.isSelected, .isButton] : .isButton)
        .accessibilityAction { state.select(item) }
        .accessibilityIdentifier("clipboard-card-\(item.id.uuidString)")
    }

    private func cardDragProvider() -> NSItemProvider {
        guard !item.isDeleted else { return NSItemProvider() }
        let provider = itemDragProvider(item)
        guard let boardID = state.pinboardID, state.isSearchQueryEmpty, !state.showDeleted else { return provider }
        prepareSelection()
        let marker = ReplicaLocalItemDrag(sessionID: state.itemDragSessionID, boardID: boardID,
                                          ids: state.selectedItems.map(\.id))
        if let data = try? JSONEncoder().encode(marker) {
            provider.registerDataRepresentation(forTypeIdentifier: ReplicaLocalItemDrag.typeIdentifier,
                                                visibility: .ownProcess) { completion in
                completion(data, nil)
                return nil
            }
        }
        return provider
    }

    private func receiveItemDrop(_ providers: [NSItemProvider], after: Bool) -> Bool {
        guard let boardID = state.pinboardID, state.isSearchQueryEmpty, !state.showDeleted,
              let provider = providers.first(where: { $0.hasItemConformingToTypeIdentifier(ReplicaLocalItemDrag.typeIdentifier) }) else { return false }
        provider.loadDataRepresentation(forTypeIdentifier: ReplicaLocalItemDrag.typeIdentifier) { data, _ in
            guard let data, let marker = try? JSONDecoder().decode(ReplicaLocalItemDrag.self, from: data) else { return }
            Task { @MainActor in
                guard marker.sessionID == state.itemDragSessionID, marker.boardID == boardID,
                      state.pinboardID == boardID, state.isSearchQueryEmpty, !state.showDeleted,
                      let index = state.store.items(in: boardID).firstIndex(where: { $0.id == item.id }) else { return }
                state.perform { try state.store.reorderItems(ids: marker.ids, in: boardID, toOffset: index + (after ? 1 : 0)) }
            }
        }
        return true
    }

    private var presentation: OriginalCardPresentation? {
        OriginalCardPresentation.resolve(item, linkPreviewsEnabled: state.store.preferences.linkPreviewsEnabled)
    }

    private var cardGeometry: OriginalCardPresentation.Geometry? {
        presentation?.geometry(sizeClass: UInt8(sizeClass), modernOS: modernCardOS)
    }

    private var modernCardOS: Bool {
        if #available(macOS 26, *) { return true }
        return false
    }

    private var cardBackground: Color {
        if item.kind == .color, let metadata = item.decodedColorPreviewMetadata {
            return Color(nsColor: OriginalColorPreviewMetadataGenerator.color(metadata.code))
        }
        if let background = compactTextBackground { return Color(nsColor: background) }
        return Color(nsColor: .textBackgroundColor)
    }

    private var selectionBackground: NSColor {
        let color = NSColor.controlAccentColor
        return (dimmingOverride ?? (activeState != .key))
            ? OriginalSelectionAppearance.f_100218b08(color) : color
    }

    private var compactTextMetadata: OriginalTextPreviewMetadata? {
        guard item.kind == .text || item.kind == .richText else { return nil }
        return item.decodedTextPreviewMetadata
    }

    private var compactTextBackground: NSColor? {
        compactTextMetadata.map { OriginalCompactTextCardAppearance.background(for: $0.text) }
    }

    @ViewBuilder private var cardContent: some View {
        switch item.kind {
        case .image, .color, .files:
            ReplicaCanonicalCardContent(item: item, sizeClass: UInt8(sizeClass))
        case .unknown:
            OriginalUnavailableCompactContent(sizeClass: UInt8(sizeClass))
        default:
            ReplicaItemContent(item: item, compact: true, linkPreviewsEnabled: state.store.preferences.linkPreviewsEnabled,
                               cardSizeClass: UInt8(sizeClass))
                .padding(.horizontal, item.kind == .link ? 0 : 12).padding(.top, contentTopInset)
        }
    }

    private var contentTopInset: CGFloat {
        switch item.kind {
        case .link: return 0
        case .text, .richText: return sizeClass == 3 ? 0 : 10
        default: return 11
        }
    }

    private var cardCornerRadius: CGFloat {
        if #available(macOS 26, *) { return 16 }
        return 10
    }

    private var selectionCornerRadius: CGFloat {
        if #available(macOS 26, *) { return 20 }
        return 14
    }

    private var cardCornerStyle: RoundedCornerStyle {
        if #available(macOS 26, *) { return .continuous }
        return .circular
    }

    private var sizeClass: Int {
        if sideLength < 200 { return 3 }
        if sideLength < 240 { return 2 }
        if sideLength < 280 { return 1 }
        return 0
    }

    private var headerHeight: CGFloat {
        if let cardGeometry { return cardGeometry.headerHeight }
        switch sizeClass {
        case 0: return 56
        case 1: return 52
        case 2: return 48
        default:
            if #available(macOS 26, *) { return 36 }
            return 34
        }
    }

    private var sourceIconSide: CGFloat {
        sizeClass == 3 ? 20 : headerHeight + 28
    }

    private var headerOwner: Pinboard? {
        guard let owner = state.store.pinboardOwner(for: item), owner.rawType == 2 else { return nil }
        return owner
    }

    private var pinboardHeaderColor: NSColor? {
        guard let owner = headerOwner,
              let code = OriginalPinboardAttributes.colorCode(from: owner.rawAttributes) else { return nil }
        return OriginalPinboardColor(canonicalColorCode: code).color()
    }

    private var headerTrailingInset: CGFloat {
        if sizeClass == 3 { return 30 }
        return headerOwner == nil ? sourceIconSide - 14 : 12
    }

    private var headerLabels: some View {
        Group {
            Text(cardTitle)
                .font(Font(NSFont.systemFont(ofSize: NSFont.preferredFont(forTextStyle: sizeClass == 3 ? .headline : .title3, options: [:]).pointSize,
                                            weight: sizeClass == 3 ? .semibold : .medium)))
                .lineLimit(1)
                .foregroundStyle(headerPrimaryColor)
            Text(relativeTime(item.createdAt))
                .font(Font(NSFont.preferredFont(forTextStyle: sizeClass == 3 ? .body : .callout, options: [:])))
                .foregroundStyle(headerSecondaryColor)
        }
    }

    private var compactHeaderStyle: UInt8 { presentation?.preferredCompactHeaderStyle == 1 ? 1 : 0 }

    private var headerPrimaryColor: Color {
        guard sizeClass == 3 else { return .white }
        return compactHeaderStyle == 1 ? .white.opacity(0.85)
            : Color(nsColor: resolvedCardHeaderColor(OriginalSearchAppearance.f_1001fec18() ?? .labelColor))
    }

    private var headerSecondaryColor: Color {
        guard sizeClass == 3 else { return .white.opacity(0.8) }
        return compactHeaderStyle == 1 ? .white.opacity(0.55)
            : Color(nsColor: resolvedCardHeaderColor(OriginalToolbarAppearance.secondaryForeground()))
    }

    private func resolvedCardHeaderColor(_ color: NSColor) -> NSColor {
        let appearance: NSAppearance
        if item.kind == .color, let metadata = item.decodedColorPreviewMetadata {
            let background = OriginalColorPreviewMetadataGenerator.color(metadata.code)
            let name: NSAppearance.Name = OriginalPreviewTextColors.f_1002067d4(background) ? .aqua : .darkAqua
            guard let resolved = NSAppearance(named: name) else { return color }
            appearance = resolved
        } else if let background = compactTextBackground {
            appearance = OriginalCompactTextCardAppearance.appearance(for: background)
        } else {
            return color
        }
        var resolved = color
        appearance.performAsCurrentDrawingAppearance {
            resolved = color.usingColorSpace(.deviceRGB) ?? color
        }
        return resolved
    }

    private var cardHeader: some View {
        ZStack(alignment: .trailing) {
            Group {
                if sizeClass == 3 {
                    HStack(spacing: 0) { headerLabels }
                } else {
                    VStack(alignment: .leading, spacing: -1) { headerLabels }
                }
            }
            .foregroundStyle(sizeClass == 3 ? Color(nsColor: .labelColor) : .white)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.leading, 12)
            .padding(.trailing, headerTrailingInset)
            if headerOwner != nil {
                if let color = pinboardHeaderColor {
                    Image(nsImage: OriginalPinboardHeaderIcon.image(height: 12, shared: false, color: color))
                        .offset(x: sizeClass == 3 ? -12 : 8)
                }
            } else {
                SourceAppIcon(item: item, store: state.store,
                              rasterSize: NSSize(width: sourceIconSide, height: sourceIconSide))
                    .frame(width: sourceIconSide, height: sourceIconSide)
                    .opacity(sizeClass == 3 ? 0.9 : 1)
                    .offset(x: sizeClass == 3 ? -8 : 14)
            }
        }
        .frame(height: headerHeight)
        .background(sizeClass == 3 ? Color.clear
            : pinboardHeaderColor.map { Color(nsColor: $0) } ?? sourceColor(item, store: state.store))
        .clipped()
    }

    private var cardTitle: String {
        let rawType: Int
        switch item.kind {
        case .unknown: rawType = 0
        case .image: rawType = 1
        case .color: rawType = 2
        case .files: rawType = 3
        case .link: rawType = 4
        case .text, .richText: rawType = 5
        }
        let defaultTitle = OriginalPreviewTitles.f_100309008(rawType: rawType,
            fileCount: item.kind == .files ? item.decodedFilePreviewMetadata?.paths.count : nil)
        return OriginalPreviewTitles.f_100308f88(item.originalTitle, defaultTitle: defaultTitle)
    }

    @ViewBuilder private var contextMenu: some View {
        if item.isDeleted {
            Button("恢复") { state.perform { try state.store.restore(ids: state.selection) } }
        } else {
            Button("拷贝") { state.controller?.copySelection(plainTextOnly: false) }
            Button("复制为纯文本") { state.controller?.copySelection(plainTextOnly: true) }
                .disabled(item.plainText == nil && item.recognizedText == nil)
            Button("粘贴") { state.controller?.pasteSelection(plainTextOnly: false) }
            Button("以纯文本粘贴") { state.controller?.pasteSelection(plainTextOnly: true) }
                .disabled(item.plainText == nil && item.recognizedText == nil)
            Divider()
            Button("预览") { state.controller?.showPreview(item: item) }
            if item.plainText != nil { Button("编辑…") { state.controller?.showEditor(item: item) } }
            Button("重命名…") { state.controller?.renameItem(item) }
            Button("副本") { state.perform { _ = try state.store.duplicateItem(id: item.id) } }
            if item.kind == .image {
                Button("复制图中文字") {
                    Task {
                        do {
                            _ = try await state.store.recognizeImageText(id: item.id)
                            state.controller?.copy(item: item, plainTextOnly: true)
                        } catch { state.controller?.presentError(error) }
                    }
                }
            }
            if item.kind == .files {
                Button("打开") { for url in itemFileURLs(item) { NSWorkspace.shared.open(url) } }
                Button("在 Finder 中显示") { NSWorkspace.shared.activateFileViewerSelecting(itemFileURLs(item)) }
            }
            Menu("添加到 Pinboard") {
                ForEach(state.store.pinboards) { board in
                    Button(board.name) { state.assignSelection(to: board.id) }
                }
                Divider()
                Button("新建 Pinboard…") { state.controller?.createPinboard(assignSelection: true) }
            }
            if !item.pinboardIDs.isEmpty {
                if let board = state.pinboardID {
                    Button("从此 Pinboard 移除") {
                        state.perform { try state.store.unassign(ids: state.selection, from: board) }
                    }
                }
                Button("从所有 Pinboard 移除") { state.assignSelection(to: nil) }
            }
            Button("添加到 Pasto Stack") {
                for selected in state.selectedItems { state.addToStack(selected) }
                state.controller?.showStack()
            }
            Button("全选") { state.selectAll() }
            Button("取消全选") { state.deselectAll() }
            Divider()
            Button("删除", role: .destructive) { state.deleteSelection() }
        }
    }

    private func prepareSelection() {
        if !selected { state.select(item) }
        state.primaryID = item.id
    }
}

@MainActor
private struct ReplicaCardTapHandlers: ViewModifier {
    let enabled: Bool
    let single: () -> Void
    let double: () -> Void

    @ViewBuilder func body(content: Content) -> some View {
        if enabled {
            content.onTapGesture(count: 2, perform: double).onTapGesture(perform: single)
        } else {
            content
        }
    }
}

@MainActor
private struct ReplicaCardDragHandlers: ViewModifier {
    let enabled: Bool
    let provider: () -> NSItemProvider
    let drop: ([NSItemProvider], CGPoint) -> Bool

    @ViewBuilder func body(content: Content) -> some View {
        if enabled {
            content.onDrag(provider).onDrop(of: [ReplicaLocalItemDrag.typeIdentifier],
                                           isTargeted: nil, perform: drop)
        } else {
            content
        }
    }
}

@MainActor
struct SourceAppIcon: View {
    let item: ClipboardItem
    @ObservedObject var store: ClipboardStore
    var rasterSize: NSSize? = nil

    var body: some View {
        if let application = store.sourceApplication(for: item) {
            let image = application.rawIcon.flatMap(NSImage.init(data:)) ?? NSImage()
            if let rasterSize {
                if let raster = OriginalImagePreviewMetadataGenerator.f_1003ca024(
                    image, width: rasterSize.width, height: rasterSize.height) {
                    Image(nsImage: raster).resizable().scaledToFit()
                }
            } else {
                Image(nsImage: image).resizable().scaledToFit()
            }
        } else {
            // Independent unknown-application placeholder; the original private asset is not copied.
            Image(systemName: "doc.on.clipboard.fill")
                .resizable().scaledToFit().padding(4).foregroundStyle(.gray)
        }
    }
}

@MainActor
struct ReplicaItemContent: View {
    let item: ClipboardItem
    let compact: Bool
    var linkPreviewsEnabled = true
    var cardSizeClass: UInt8? = nil
    var body: some View {
        Group {
            if item.kind == .unknown, !compact {
                OriginalUnavailablePreviewContent()
            } else if item.kind == .image, let image = itemImage(item) {
                Image(nsImage: image).resizable().scaledToFit()
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if item.kind == .color, let color = parseColor(item.plainText ?? item.title) {
                VStack(alignment: .leading, spacing: 9) {
                    RoundedRectangle(cornerRadius: 6).fill(color).frame(height: compact ? 70 : 150)
                    Text(item.plainText ?? item.title).font(.system(size: 14, design: .monospaced))
                }
            } else if item.kind == .files {
                VStack(alignment: .leading, spacing: 10) {
                    Image(systemName: "doc.fill").font(.system(size: compact ? 30 : 58)).foregroundStyle(.blue)
                    Text(item.plainText ?? item.title).font(.system(size: 14)).lineLimit(compact ? 4 : nil)
                }
            } else if item.kind == .link {
                if let metadata = item.decodedLinkPreviewMetadata {
                    ReplicaLinkMetadataContent(metadata: metadata, compact: compact, linkPreviewsEnabled: linkPreviewsEnabled,
                                               cardSizeClass: cardSizeClass)
                }
            } else if compact, item.kind == .text || item.kind == .richText {
                if let metadata = item.decodedTextPreviewMetadata {
                    OriginalCompactTextContent(text: metadata.text)
                }
            } else if item.kind == .richText, let data = item.payloads["public.rtf"],
                      let attributed = NSAttributedString(rtf: data, documentAttributes: nil) {
                Text(AttributedString(compact ? attributed.attributedSubstring(from: .init(location: 0, length: min(attributed.length, 2000))) : attributed))
                    .lineLimit(compact ? 7 : nil)
                    .frame(maxWidth: .infinity, alignment: .topLeading)
            } else {
                Text(compact ? String((item.plainText?.isEmpty == false ? item.plainText! : item.title).prefix(2000))
                     : (item.plainText?.isEmpty == false ? item.plainText! : item.title))
                    .font(.system(size: 14))
                    .foregroundStyle(Color(nsColor: .labelColor))
                    .lineSpacing(3)
                    .lineLimit(compact ? 7 : nil)
                    .frame(maxWidth: .infinity, alignment: .topLeading)
            }
        }
    }
}

func itemImage(_ item: ClipboardItem) -> NSImage? {
    ClipboardStore.pasteboardImage(from: item.payloads)
}

func itemFileURLs(_ item: ClipboardItem) -> [URL] {
    let representations = ClipboardStore.normalizedPasteboardPayloads(item.payloads)
    var urls: [URL] = []
    for representation in representations {
        if let data = representation[NSPasteboard.PasteboardType.fileURL.rawValue],
           let value = String(data: data, encoding: .utf8),
           let url = URL(string: value), url.isFileURL { urls.append(url) }
        if let data = representation["NSFilenamesPboardType"],
           let paths = try? PropertyListSerialization.propertyList(from: data, format: nil) as? [String] {
            urls.append(contentsOf: paths.map { URL(fileURLWithPath: $0) })
        }
    }
    if urls.isEmpty, item.kind == .files, let text = item.plainText {
        urls = text.components(separatedBy: .newlines).filter { $0.hasPrefix("/") }.map { URL(fileURLWithPath: $0) }
    }
    var unique = Set<URL>()
    return urls.filter { unique.insert($0).inserted }
}

struct ReplicaLocalItemDrag: Codable {
    static let typeIdentifier = "com.pastereplica.internal.pinboard-item-drag"
    let sessionID: UUID
    let boardID: UUID
    let ids: [UUID]
}

func itemDragProvider(_ item: ClipboardItem) -> NSItemProvider {
    let files = itemFileURLs(item)
    let provider = files.first.flatMap { NSItemProvider(contentsOf: $0) } ?? NSItemProvider()
    provider.suggestedName = files.first?.lastPathComponent ?? item.title
    for (type, data) in item.payloads where !type.hasPrefix("com.pastereplica.internal.")
        && type != "org.nspasteboard.AutoGeneratedType" {
        provider.registerDataRepresentation(forTypeIdentifier: type, visibility: .all) { completion in
            completion(data, nil)
            return nil
        }
    }
    if let text = item.plainText,
       !provider.hasItemConformingToTypeIdentifier(UTType.utf8PlainText.identifier) {
        provider.registerDataRepresentation(forTypeIdentifier: UTType.utf8PlainText.identifier, visibility: .all) { completion in
            completion(Data(text.utf8), nil)
            return nil
        }
    }
    if item.kind == .link, let text = item.plainText, let url = URL(string: text),
       !provider.hasItemConformingToTypeIdentifier(UTType.url.identifier) {
        provider.registerObject(url as NSURL, visibility: .all)
    }
    if files.count > 1,
       let data = try? PropertyListSerialization.data(fromPropertyList: files.map(\.path), format: .binary, options: 0) {
        provider.registerDataRepresentation(forTypeIdentifier: "NSFilenamesPboardType", visibility: .all) { completion in
            completion(data, nil)
            return nil
        }
    }
    return provider
}

func parseColor(_ text: String) -> Color? {
    let value = text.trimmingCharacters(in: .whitespacesAndNewlines).replacingOccurrences(of: "#", with: "")
    guard value.count == 6 || value.count == 8, let number = UInt64(value, radix: 16) else { return nil }
    let rgb = value.count == 8 ? number >> 8 : number
    return Color(red: Double((rgb >> 16) & 255) / 255,
                 green: Double((rgb >> 8) & 255) / 255,
                 blue: Double(rgb & 255) / 255)
}

@MainActor
func sourceColor(_ item: ClipboardItem, store: ClipboardStore) -> Color {
    Color(nsColor: SourceAppColor.color(application: store.sourceApplication(for: item)))
}

func itemSummary(_ item: ClipboardItem) -> String {
    if item.kind == .link, let value = item.plainText, let url = URL(string: value), let host = url.host { return host }
    if item.kind == .image, let image = itemImage(item) { return "\(Int(image.size.width)) × \(Int(image.size.height))" }
    if let text = item.plainText { return "\(text.count) 个字符" }
    let bytes = item.payloads.values.reduce(0) { $0 + $1.count }
    return ByteCountFormatter.string(fromByteCount: Int64(bytes), countStyle: .file)
}

func relativeTime(_ date: Date) -> String {
    let interval = max(0, Date().timeIntervalSince(date))
    if interval < 60 { return "刚刚" }
    if interval < 3600 { return "\(Int(interval / 60)) 分钟前" }
    if interval < 86400 { return "\(Int(interval / 3600)) 小时前" }
    return "\(Int(interval / 86400)) 天前"
}
