import AppKit
import SwiftUI
import UniformTypeIdentifiers
import PastoCore

@MainActor
struct ReplicaPanelView: View {
    @ObservedObject var state: ReplicaUIState

    var body: some View {
        GeometryReader { geometry in
            let collectionHeight = max(0, geometry.size.height - 60 - backgroundInset)
            let cardSide = max(0, collectionHeight - 32)
            VStack(spacing: 0) {
                header.frame(height: 60)
                ZStack {
                    ReplicaNativeCollection(state: state, cardSide: cardSide)
                        .frame(height: collectionHeight)
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
                    }
                    if state.hasPendingDeletion {
                        Color.black.opacity(0.08)
                            .contentShape(Rectangle())
                            .onTapGesture { state.controller?.cancelPendingDeletion() }
                        if let request = state.pendingItemDeletion {
                            itemDeletionConfirmation(request)
                                .frame(width: min(360, max(0, geometry.size.width - 32)))
                        } else if let target = state.pendingPinboardDeletion {
                            pinboardDeletionConfirmation(target)
                                .frame(width: min(360, max(0, geometry.size.width - 32)))
                        }
                    }
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
        .accessibilityIdentifier("clipboard-panel")
    }

    private var backgroundInset: CGFloat {
        if #available(macOS 26, *) { return 8 }
        return 0
    }

    private func pinboardDeletionConfirmation(_ target: ClipboardListTarget) -> some View {
        deletionConfirmation(title: "删除“\(target.name)”？",
            message: "保留历史和其他分组中的内容，仅属于此分组的内容将被删除。",
            error: state.pinboardDeletionError, confirmTitle: "删除分组", kind: "group",
            cancel: { state.controller?.cancelPinboardRemoval() },
            confirm: { state.controller?.confirmPinboardRemoval() })
    }

    private func itemDeletionConfirmation(_ request: ReplicaUIState.ItemDeletionRequest) -> some View {
        let message: String
        if request.permanently { message = "将从剪贴板历史和所有分组中删除这 \(request.ids.count) 个项目。" }
        else if request.contextPinboardID != nil { message = "仅移出当前分组，保留历史和其他分组中的内容。" }
        else { message = "从剪贴板历史中删除，保留分组中的内容。" }
        return deletionConfirmation(title: "删除选中的项目？", message: message,
            error: state.itemDeletionError, confirmTitle: "删除", kind: "item",
            cancel: { state.cancelItemDeletion() }, confirm: { state.confirmItemDeletion() })
    }

    private func deletionConfirmation(title: String, message: String, error: String?,
                                      confirmTitle: String, kind: String,
                                      cancel: @escaping () -> Void, confirm: @escaping () -> Void) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(title)
                .font(.system(size: 16, weight: .semibold))
                .lineLimit(2)
            Text(error ?? message)
                .font(.system(size: 13))
                .foregroundStyle(error == nil ? Color.secondary : Color.red)
                .fixedSize(horizontal: false, vertical: true)
            HStack {
                Spacer()
                Button("取消", action: cancel)
                    .buttonStyle(.bordered)
                    .accessibilityIdentifier("cancel-\(kind)-deletion")
                Button(confirmTitle, role: .destructive, action: confirm)
                    .buttonStyle(.borderedProminent)
                    .tint(.red)
                    .accessibilityIdentifier("confirm-\(kind)-deletion")
            }
        }
        .padding(16)
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 16))
        .overlay(RoundedRectangle(cornerRadius: 16).strokeBorder(.primary.opacity(0.1)))
        .shadow(color: .black.opacity(0.12), radius: 12, y: 4)
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("\(kind)-deletion-confirmation")
    }

    private var backgroundRadius: CGFloat {
        if #available(macOS 26, *) { return 26 }
        return 0
    }

    private var searching: Bool { state.searchVisible || !state.isSearchQueryEmpty }

    private var header: some View {
        OriginalPanelToolbar(state: state, isSearching: searching,
            searchButton: AnyView(OriginalPanelToolbarButton(symbol: "magnifyingglass", label: "搜索剪贴板") {
                state.searchVisible = true
            }), searchField: searchField, tabConfiguration: boardTab,
            createButton: AnyView(createPinboardButton),
            menuButton: AnyView(trailingControls), onDismiss: {
                state.searchVisible = false
            })
    }

    private var searchField: ReplicaSearchEditor {
        ReplicaSearchEditor(store: state.store,
            queryNodes: state.searchQueryNodes,
            filters: searchFilterChips,
            onInputChange: { text, filters, nodes in state.publishSearchInputFromEditor(nodes: nodes, text: text, filters: filters) },
            onLoadSuggestions: { state.searchSuggestions(for: $0) },
            onEnter: { state.controller?.pasteSelection(plainTextOnly: false) },
            onCancel: { state.controller?.cancelSearchOrPanel() },
            onShowFilters: { button in state.controller?.showFilterBrowser(relativeTo: button) },
            onEditingEnded: { field in
                guard let controller = state.controller, field.window === controller.panel else { return }
                if state.searchVisible, state.isSearchQueryEmpty, controller.filterBrowserPopover?.isDisplayed != true {
                    state.searchVisible = false
                }
            })
    }

    private var searchFilterChips: [ReplicaSearchFilterChip] {
        state.searchFilters.map { ReplicaFilterMatching.chip($0, store: state.store) }
    }

    private func boardTab(_ target: ClipboardListTarget) -> OriginalPinboardTab {
        let board = target.pinboardValue
        var tab = boardButton(target.name, board: board, target: target)
        tab.menuProvider = { localListMenu(for: target) }
        tab.dragString = "paste-pinboard:" + target.identifier
        // 328f38's nil-share branch is writable for Pasto's local Lists, including history.
        tab.canDropItems = { true }
        tab.onDropItemIdentifiers = { [weak state = state] identifiers in
            state?.dropItems(identifiers: identifiers, to: target)
        }
        tab.onDropString = { value in
            guard value.hasPrefix("paste-pinboard:") else { return false }
            return state.moveList(identifier: String(value.dropFirst(15)), to: target)
        }
        return tab
    }

    // 0x100021f00: offline rename, typed deletion, then color choices.
    private func localListMenu(for target: ClipboardListTarget) -> NSMenu {
        let menu = NSMenu()
        menu.autoenablesItems = false
        menu.addItem(OriginalPanelTabMenuItem(title: "重命名") { requestTabRename(target) })
        // Resolve and count only when the native context menu is requested.
        let list = state.store.localListMenuState(target)
        if list.rawType == 1 {
            if !list.isEmpty {
                menu.addItem(OriginalPanelTabMenuItem(title: "删除历史…") { state.controller?.clearHistory() })
            }
        } else if list.rawType == 2 {
            menu.addItem(OriginalPanelTabMenuItem(title: list.isEmpty ? "删除" : "删除…") {
                state.controller?.removePinboard(target)
            })
            menu.addItem(.separator())
            // Keep the requested named color rows and colored dots as the local presentation adapter.
            let colors = NSMenu()
            colors.autoenablesItems = false
            let selectedColor = target.colorCode.map { OriginalPinboardColor(canonicalColorCode: $0) }
            for color in OriginalPinboardColor.allCases {
                let item = OriginalPanelTabMenuItem(title: colorName(color)) { [weak menu] in
                    try? state.store.updateListColor(target, colorCode: color.canonicalColorCode)
                    menu?.cancelTracking()
                }
                item.image = colorMenuImage(color)
                item.state = selectedColor == color ? .on : .off
                colors.addItem(item)
            }
            let colorMenu = NSMenuItem(title: "颜色", action: nil, keyEquivalent: "")
            colorMenu.submenu = colors
            menu.addItem(colorMenu)
        }
        return menu
    }

    private var createPinboardButton: some View {
        OriginalPanelToolbarButton(symbol: "plus", label: OriginalSearchLocalization.text("pasto.action.create-group"),
            help: OriginalSearchLocalization.text("pasto.action.create-group") + " (⇧⌘N)") {
            state.controller?.createPinboard()
        }
    }

    private func colorMenuImage(_ color: OriginalPinboardColor) -> NSImage {
        let fill = color.color()
        let image = NSImage(size: NSSize(width: 12, height: 12), flipped: false) { bounds in
            fill.setFill()
            NSBezierPath(ovalIn: bounds).fill()
            return true
        }
        image.isTemplate = false
        return image
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

    private func requestTabRename(_ target: ClipboardListTarget) {
        state.beginEditingListSubject.send(target)
    }

    private func boardButton(_ name: String, board: Pinboard?, target: ClipboardListTarget) -> OriginalPinboardTab {
        return OriginalPinboardTab(title: name, iconColor: board.map { NSColor(boardColor($0)) },
                isSelected: state.selectedTabList?.hasSameObjectID(as: target) == true && !state.showDeleted,
                beginRequest: nil,
                onSelect: {
                    if target.rawType != 2, searching {
                        state.query = ""; state.chooseList(identifier: target.identifier); state.searchVisible = false
                        state.controller?.panel.makeFirstResponder(nil)
                    } else { state.chooseList(identifier: target.identifier) }
                },
                onEnd: {},
                onCommit: { value in
                    try? state.store.renameList(target, rawName: value)
                    return target.name
                })
    }

    private var trailingControls: some View {
        OriginalPanelMoreMenu(state: state)
            .frame(width: 44, height: 44)
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
    var titleInput: ClipboardRestoreItem? = nil
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
            state.selectForContextMenu(item)
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
        guard let boardID = state.pinboardID, state.isCollectionSearchQueryEmpty, !state.showDeleted else { return provider }
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
        guard let boardID = state.pinboardID, state.isCollectionSearchQueryEmpty, !state.showDeleted,
              let provider = providers.first(where: { $0.hasItemConformingToTypeIdentifier(ReplicaLocalItemDrag.typeIdentifier) }) else { return false }
        provider.loadDataRepresentation(forTypeIdentifier: ReplicaLocalItemDrag.typeIdentifier) { data, _ in
            guard let data, let marker = try? JSONDecoder().decode(ReplicaLocalItemDrag.self, from: data) else { return }
            Task { @MainActor in
                guard marker.sessionID == state.itemDragSessionID, marker.boardID == boardID,
                      state.pinboardID == boardID, state.isCollectionSearchQueryEmpty, !state.showDeleted,
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
              case let .pinboard(code)? = state.listAttributes(for: owner) else { return nil }
        return OriginalPinboardColor(canonicalColorCode: code).color()
    }

    private var headerTrailingInset: CGFloat {
        if sizeClass == 3 { return 30 }
        return headerOwner == nil ? sourceIconSide - 14 : 12
    }

    private var headerLabels: some View {
        Group {
            if nativeInteractions {
                ReplicaCardTitle(state: state, itemID: item.id, input: titleInput, title: cardTitle,
                    font: headerTitleFont, textColor: NSColor(headerPrimaryColor))
                    .fixedSize(horizontal: false, vertical: true)
            } else {
                Text(cardTitle)
                    .font(Font(headerTitleFont))
                    .lineLimit(1)
                    .foregroundStyle(headerPrimaryColor)
            }
            ReplicaCardDateLabel(date: item.isInHistory ? item.createdAt : nil, isCompact: sizeClass == 3)
                .font(Font(NSFont.preferredFont(forTextStyle: sizeClass == 3 ? .body : .callout, options: [:])))
                .foregroundStyle(headerSecondaryColor)
        }
    }

    private var headerTitleFont: NSFont {
        NSFont.systemFont(ofSize: NSFont.preferredFont(forTextStyle: sizeClass == 3 ? .headline : .title3, options: [:]).pointSize,
                          weight: sizeClass == 3 ? .semibold : .medium)
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
        return OriginalPreviewTitles.f_100308f88(item.originalTitle,
            defaultTitle: OriginalPreviewTitles.f_100309008(rawType: rawType,
                fileCount: item.kind == .files ? item.decodedFilePreviewMetadata?.paths.count : nil))
    }

    private var canRestoreSelectionAsPlainText: Bool {
        let items = state.selectedItems
        guard !items.isEmpty else { return false }
        do {
            let selections = try items.map { item -> OriginalPasteboardRestore.Selection in
                let kind: OriginalPasteboardContentKind
                switch item.kind {
                case .text, .richText: kind = .text
                case .link: kind = .link
                case .image: kind = .image
                case .files: kind = .files
                case .color: kind = .color
                case .unknown: kind = .unknown
                }
                let representations = try ClipboardStore.ordinaryRestoreRepresentations(for: item, plainTextProjection: true)
                return .init(kind: kind, items: representations, sourceBundleID: nil)
            }
            return OriginalPasteboardRestore.f_10038222c(selections, options: .plainText,
                removingTypesContaining: ["com.microsoft.ole.source"])
                .contains { !$0.isEmpty }
        } catch {
            return false
        }
    }

    // 09e8a8 snapshots off/on/mixed; the single writable source keeps each click one batch action.
    private func pinboardMenuBindings(for target: ClipboardPinboardTarget,
                                      items: [ClipboardRestoreItem]) -> [Binding<Bool>] {
        let matched = items.filter { input in
            input.isAssigned(to: target)
                ?? (state.store.pinboardOwner(for: input.resolvedItem())?.id == target.id)
        }.count
        let assignment = Binding<Bool>(get: { matched == items.count },
            set: { _ in state.assignItems(items, to: target) })
        if matched > 0, matched < items.count { return [assignment, .constant(true)] }
        return [assignment]
    }

    @ViewBuilder private var contextMenu: some View {
        if item.isDeleted {
            Button("恢复") { state.perform { try state.store.restore(ids: state.selection) } }
        } else {
            let groupItems = state.controller?.contextMenuRestoreItems() ?? []
            Button("拷贝") { state.controller?.copySelection(plainTextOnly: false) }
            Button("复制为纯文本") { state.controller?.copySelection(plainTextOnly: true) }
                .disabled(!canRestoreSelectionAsPlainText)
            Button("粘贴") { state.controller?.pasteSelection(plainTextOnly: false) }
            Button("以纯文本粘贴") { state.controller?.pasteSelection(plainTextOnly: true) }
                .disabled(!canRestoreSelectionAsPlainText)
            Divider()
            Button("预览") { state.controller?.showPreview(item: item, input: titleInput) }
            if item.plainText != nil { Button("编辑…") { state.controller?.showEditor(item: item) } }
            Button("重命名…") { state.controller?.renameItem(item) }
            Button("副本") { state.perform { _ = try state.store.duplicateItem(id: item.id) } }
            if item.kind == .image {
                Button("复制图中文字") {
                    Task {
                        do {
                            _ = try await state.store.recognizeImageText(id: item.id)
                            state.controller?.copyRecognizedImageText(item: item)
                        } catch { state.controller?.presentError(error) }
                    }
                }
            }
            if item.kind == .files {
                Button("打开") { for url in itemFileURLs(item) { NSWorkspace.shared.open(url) } }
                Button("在 Finder 中显示") { NSWorkspace.shared.activateFileViewerSelecting(itemFileURLs(item)) }
            }
            Menu("添加到 Pasto") {
                ForEach(state.pinboardMenuTargets(), id: \.id) { target in
                    Toggle(sources: pinboardMenuBindings(for: target, items: groupItems), isOn: \.self) {
                        Label {
                            Text(target.name)
                        } icon: {
                            let color = target.colorCode.map { OriginalPinboardColor(canonicalColorCode: $0).color() } ?? .clear
                            Image(nsImage: OriginalPinboardHeaderIcon.image(height: 12, shared: false, color: color))
                        }
                    }
                }
                Divider()
                Button(OriginalSearchLocalization.text("pasto.action.create-group") + "…") {
                    state.controller?.createPinboard(assignSelection: true, selectionItems: groupItems)
                }
                if state.canUnassignItems(groupItems) {
                    Button(String(localized: OriginalPreviewLocalization.f_1001c4208())) {
                        state.assignItems(groupItems, to: nil)
                    }
                }
            }
            Button("添加到 Pasto Stack") {
                state.controller?.addSelectionToStack()
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

@MainActor
func relativeTime(_ date: Date, isCompact: Bool = false) -> String {
    let reference = Date()
    return OriginalDateDisplay.f_100309e0c(date, format: isCompact
        ? .abbreviated(relativeTo: reference) : .named(relativeTo: reference))
}

@MainActor
private struct ReplicaCardDateLabel: View {
    let date: Date?
    let isCompact: Bool
    @StateObject private var presentation = ReplicaCardDatePresentation()

    var body: some View {
        Text(presentation.text ?? relativeTime(date ?? Date(), isCompact: isCompact))
            .help(presentation.tooltip)
            .onAppear { presentation.configure(date: date, isCompact: isCompact) }
            .onChange(of: date) { _, _ in presentation.configure(date: date, isCompact: isCompact) }
            .onChange(of: isCompact) { _, _ in presentation.configure(date: date, isCompact: isCompact) }
            .onDisappear { presentation.stop() }
    }
}

@MainActor
private final class ReplicaCardDatePresentation: ObservableObject {
    @Published private(set) var text: String?
    private(set) var tooltip = ""
    private var inputDate: Date?
    private var resolvedDate: Date?
    private var timer: Timer?

    deinit { timer?.invalidate() }

    func configure(date: Date?, isCompact: Bool) {
        if resolvedDate == nil || inputDate != date {
            inputDate = date
            resolvedDate = date ?? Date()
        }
        refresh(date: resolvedDate!, isCompact: isCompact)
    }

    private func refresh(date: Date, isCompact: Bool) {
        tooltip = OriginalDateDisplay.f_100309e0c(date, format: .absolute)
        text = relativeTime(date, isCompact: isCompact)
        let replacement = Timer.scheduledTimer(withTimeInterval: 30, repeats: false) { [weak self] _ in
            MainActor.assumeIsolated {
                self?.refresh(date: date, isCompact: isCompact)
            }
        }
        let previous = timer
        timer = replacement
        previous?.invalidate()
    }

    func stop() {
        timer?.invalidate()
        timer = nil
    }
}

@MainActor
private struct OriginalPanelToolbarButton: NSViewRepresentable {
    let symbol: String
    let label: String
    var help: String? = nil
    var iconColor: NSColor? = nil
    var isSelected = false
    let action: () -> Void
    func makeNSView(context: Context) -> OriginalToolbarButton {
        OriginalToolbarButton(symbol: symbol, size: .large, action: { _ in action() })
    }
    func updateNSView(_ view: OriginalToolbarButton, context: Context) {
        view.buttonAction = { _ in action() }
        view.toolTip = help ?? label
        view.setAccessibilityLabel(label)
        view.isSelected = isSelected
        if let iconColor {
            view.contentTintColor = iconColor
            view.f_10023cc80().image = NSImage(systemSymbolName: symbol, accessibilityDescription: nil)?
                .withSymbolConfiguration(.init(pointSize: 12, weight: .regular))
        }
    }
    func sizeThatFits(_ proposal: ProposedViewSize, nsView: OriginalToolbarButton, context: Context) -> CGSize? {
        CGSize(width: 32, height: 32)
    }
}

@MainActor
private struct OriginalPanelMoreMenu: NSViewRepresentable {
    @ObservedObject var state: ReplicaUIState

    func makeCoordinator() -> Coordinator { Coordinator() }

    func makeNSView(context: Context) -> OriginalToolbarButton {
        let button = OriginalToolbarButton(symbol: "ellipsis", size: .large, action: { _ in })
        // Keep the recovered native hover/press behavior; only enlarge this control.
        for constraint in button.constraints where constraint.firstItem === button
            && (constraint.firstAttribute == .width || constraint.firstAttribute == .height)
            && constraint.secondItem == nil && constraint.constant == 32 {
            constraint.constant = 44
        }
        button.setAccessibilityIdentifier("panel-more-actions")
        button.setAccessibilityLabel("更多操作")
        button.toolTip = "更多操作"
        return button
    }

    func updateNSView(_ button: OriginalToolbarButton, context: Context) {
        button.buttonAction = { [state, coordinator = context.coordinator] button in
            let menu = coordinator.makeMenu(state: state)
            menu.popUp(positioning: nil, at: .init(x: button.bounds.maxX - menu.size.width, y: 0), in: button)
        }
    }

    func sizeThatFits(_ proposal: ProposedViewSize, nsView: OriginalToolbarButton, context: Context) -> CGSize? {
        CGSize(width: 44, height: 44)
    }

    @MainActor final class Coordinator: NSObject {
        private var actions: [() -> Void] = []

        @discardableResult private func add(_ title: String, symbol: String? = nil, key: String = "",
                         to menu: NSMenu, action: @escaping () -> Void) -> NSMenuItem {
            let item = NSMenuItem(title: title, action: #selector(invoke(_:)), keyEquivalent: key)
            item.target = self
            item.tag = actions.count
            actions.append(action)
            if let symbol { item.image = NSImage(systemSymbolName: symbol, accessibilityDescription: nil) }
            menu.addItem(item)
            return item
        }

        @objc private func invoke(_ item: NSMenuItem) { actions[item.tag]() }

        func makeMenu(state: ReplicaUIState) -> NSMenu {
            actions.removeAll()
            let menu = NSMenu()
            menu.autoenablesItems = false
            add("关于 Pasto", symbol: "info.circle", to: menu) {
                NSApp.sendAction(NSSelectorFromString("about:"), to: NSApp.delegate, from: nil)
            }
            menu.addItem(.separator())
            add("新文本项", symbol: "square.and.pencil", key: "n", to: menu) { state.controller?.newTextItem() }
            add("设置…", symbol: "gear", key: ",", to: menu) { state.controller?.showSettings() }
            menu.addItem(.separator())
            add("从 Paste 迁移分组…", symbol: "square.and.arrow.down", to: menu) {
                state.controller?.migratePasteGroups()
            }.isEnabled = !state.isMigratingPasteGroups
            menu.addItem(.separator())
            let pause = NSMenuItem(title: "暂停 Pasto", action: nil, keyEquivalent: "")
            pause.image = NSImage(systemSymbolName: "pause.circle", accessibilityDescription: nil)
            let submenu = NSMenu()
            submenu.autoenablesItems = false
            if state.store.preferences.isMonitoringPaused {
                add("继续 Pasto", to: submenu) { state.resumeMonitoring() }
            } else {
                add("暂停", to: submenu) { state.pauseMonitoring() }
                for minutes in [15, 30, 60, 180, 480] {
                    add(minutes < 60 ? "暂停 \(minutes)分钟" : "暂停 \(minutes / 60)小时", to: submenu) {
                        state.pauseMonitoring(minutes: minutes)
                    }
                }
            }
            pause.submenu = submenu
            menu.addItem(pause)
            add("退出 Pasto", symbol: "xmark.square", key: "q", to: menu) { NSApp.terminate(nil) }
            return menu
        }
    }
}
