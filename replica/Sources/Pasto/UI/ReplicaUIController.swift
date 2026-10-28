import AppKit
import Combine
import CryptoKit
import QuartzCore
import SwiftUI
import UniformTypeIdentifiers
import PastoCore

@MainActor
final class ReplicaUIState: ObservableObject {
    let store: ClipboardStore
    weak var controller: ReplicaUIController?
    var monitoringPauseChanged: (() -> Void)?
    @Published var query = "" { didSet {
        if !isApplyingSearchInput { searchInputProjection = nil; refreshSearch() }
    } }
    @Published var searchFilters: [ReplicaSearchFilterChip.Selection] = [] { didSet {
        if !isApplyingSearchInput { searchInputProjection = nil; refreshSearch() }
    } }
    @Published var pinboardID: UUID?
    @Published var showDeleted = false
    @Published var isMigratingPasteGroups = false
    @Published var selection: Set<UUID> = [] {
        didSet { if !isApplyingSelection { reconcileExternalSelection() } }
    }
    @Published var primaryID: UUID?
    @Published var searchFocus = UUID()
    @Published var searchVisible = false
    @Published var stackIDs: [UUID] = [] {
        didSet {
            guard oldValue != stackIDs, store.preferences.stackItemIDs != stackIDs else { return }
            store.preferences.stackItemIDs = stackIDs
            perform { try store.save() }
            controller?.stackContentsChanged()
        }
    }
    @Published var hotKeyStatusMessage = ""
    @Published var allowsEmptySelection = false
    private var observation: AnyCancellable?
    private let searchIndex: ReplicaSearchIndex
    let itemDragSessionID = UUID()
    private var searchInputProjection: [OriginalSearchQueryNode]?
    private var isApplyingSearchInput = false
    private var orderedSelectionIDs: [UUID] = []
    private var rangeAnchorID: UUID?
    private var isApplyingSelection = false

    init(store: ClipboardStore) {
        self.store = store
        searchIndex = ReplicaSearchIndex(directoryURL: store.directoryURL, store: store)
        stackIDs = store.preferences.stackItemIDs
        searchIndex.onUpdate = { [weak self] in
            self?.objectWillChange.send()
            self?.normalizeSelection()
        }
        refreshSearch()
        observation = store.objectWillChange.sink { [weak self] _ in
            self?.objectWillChange.send()
            DispatchQueue.main.async { [weak self] in
                self?.refreshSearch()
                self?.normalizeSelection()
            }
        }
    }

    private var searchQueryNodes: [OriginalSearchQueryNode] {
        if let searchInputProjection { return searchInputProjection }
        var buffer = query
        var nodes: [OriginalSearchQueryNode] = []
        OriginalSearchTextTokens.f_1002f8760(&buffer, into: &nodes)
        nodes += searchFilters.map(\.queryNode)
        return OriginalSearchQueryNormalization.f_1002da16c(nodes, flag: 0)
    }

    func applySearchInput(nodes: [OriginalSearchQueryNode], text: String,
                          filters: [ReplicaSearchFilterChip.Selection]) {
        isApplyingSearchInput = true
        query = text
        searchFilters = filters
        searchInputProjection = nodes
        isApplyingSearchInput = false
        refreshSearch()
    }

    var isSearchQueryEmpty: Bool { OriginalSearchQuery.f_1002ddcf0(searchQueryNodes) }

    private func refreshSearch() {
        searchIndex.update(items: store.items, nodes: searchQueryNodes)
    }

    var searchFailed: Bool { !searchIndex.queryString.isEmpty && searchIndex.error != nil }
    func retrySearch() { searchIndex.retry() }

    var visibleItems: [ClipboardItem] {
        if isSearchQueryEmpty {
            if let pinboardID, !showDeleted { return store.items(in: pinboardID) }
            return store.search(query: "", pinboardID: pinboardID, includeDeleted: showDeleted)
                .filter { !showDeleted || $0.isDeleted }
        }
        return store.items.filter { item in
            (showDeleted ? item.isDeleted : !item.isDeleted)
                && searchIndex.identifiers.contains(item.id)
        }.sorted { $0.updatedAt > $1.updatedAt }
    }
    var selectedItems: [ClipboardItem] {
        let byID = Dictionary(uniqueKeysWithValues: visibleItems.map { ($0.id, $0) })
        return orderedSelectionIDs.compactMap { selection.contains($0) ? byID[$0] : nil }
    }
    var primaryItem: ClipboardItem? {
        visibleItems.first { $0.id == primaryID } ?? selectedItems.first ?? visibleItems.first
    }
    var stackItems: [ClipboardItem] {
        stackIDs.compactMap { id in store.items.first { $0.id == id && !$0.isDeleted } }
    }
    var preferredScheme: ColorScheme? {
        switch store.preferences.appearance {
        case "light": return .light
        case "dark": return .dark
        default: return nil
        }
    }

    private func applyOrderedSelection(_ ids: [UUID], anchor: UUID?, primary: UUID?) {
        isApplyingSelection = true
        orderedSelectionIDs = ids
        rangeAnchorID = anchor
        selection = Set(ids)
        primaryID = primary
        isApplyingSelection = false
    }

    private func reconcileExternalSelection() {
        let visibleIDs = visibleItems.map(\.id)
        let visible = Set(visibleIDs)
        orderedSelectionIDs = orderedSelectionIDs.filter { selection.contains($0) && visible.contains($0) }
        let retained = Set(orderedSelectionIDs)
        orderedSelectionIDs += visibleIDs.filter { selection.contains($0) && !retained.contains($0) }
        if rangeAnchorID.map({ !selection.contains($0) || !visible.contains($0) }) ?? true {
            rangeAnchorID = orderedSelectionIDs.last
        }
        if primaryID.map({ !selection.contains($0) || !visible.contains($0) }) ?? true {
            isApplyingSelection = true
            primaryID = orderedSelectionIDs.last
            isApplyingSelection = false
        }
    }

    func normalizeSelection() {
        let items = visibleItems
        let visible = Set(items.map(\.id))
        var ids = orderedSelectionIDs.filter { selection.contains($0) && visible.contains($0) }
        let retained = Set(ids)
        ids += items.map(\.id).filter { selection.contains($0) && !retained.contains($0) }
        if ids.isEmpty, !allowsEmptySelection, let first = items.first { ids = [first.id] }
        let anchor = rangeAnchorID.flatMap { visible.contains($0) ? $0 : nil } ?? ids.last
        let primary = primaryID.flatMap { ids.contains($0) ? $0 : nil } ?? ids.last
        applyOrderedSelection(ids, anchor: anchor, primary: primary)
        if let pinboardID, !store.pinboards.contains(where: { $0.id == pinboardID }) {
            self.pinboardID = nil
        }
    }

    private func selectIndex(_ index: Int, mode: UInt8, items: [ClipboardItem], animated: Bool = true) {
        if items.indices.contains(index), orderedSelectionIDs == [items[index].id] { return }
        let positions = Dictionary(uniqueKeysWithValues: items.enumerated().map { ($0.element.id, $0.offset) })
        var value = OriginalOrderedSelection(selectedIndexes: orderedSelectionIDs.compactMap { positions[$0] },
            itemCount: items.count, anchor: rangeAnchorID.flatMap { positions[$0] })
        value.select(index, mode: mode)
        let ids = value.selectedIndexes.map { items[$0].id }
        if !ids.isEmpty { allowsEmptySelection = false }
        applyOrderedSelection(ids, anchor: value.anchor.map { items[$0].id }, primary: ids.last)
        if let endpointID = ids.last {
            controller?.revealSelection(endpointID: endpointID, requestedIndex: index, animated: animated)
        }
    }

    // f228a50's double-click path sets the singleton directly, without a reveal/delegate callback.
    func selectForDoubleClick(at index: Int) {
        let items = visibleItems
        guard items.indices.contains(index) else { return }
        let id = items[index].id
        allowsEmptySelection = false
        applyOrderedSelection([id], anchor: id, primary: id)
    }

    func select(_ item: ClipboardItem, modifiers: NSEvent.ModifierFlags = []) {
        controller?.panel.makeFirstResponder(nil)
        let items = visibleItems
        guard let index = items.firstIndex(where: { $0.id == item.id }) else { return }
        selectIndex(index, mode: OriginalOrderedSelection.mode(modifierFlags: modifiers.rawValue), items: items)
    }

    // f2287ec keeps the captured numeric index and does not move first responder.
    func selectAfterPressDelay(at index: Int) {
        selectIndex(index, mode: 0, items: visibleItems)
    }

    // f228128 preserves an existing multi-selection and does not change first responder.
    func selectForContextMenu(_ item: ClipboardItem) {
        let items = visibleItems
        guard let index = items.firstIndex(where: { $0.id == item.id }),
              !selection.contains(item.id) else { return }
        selectIndex(index, mode: 0, items: items)
    }

    func moveSelection(_ offset: Int, extending: Bool = false) {
        let items = visibleItems
        guard !items.isEmpty else { return }
        guard let endpoint = orderedSelectionIDs.last,
              let current = items.firstIndex(where: { $0.id == endpoint }) else { return }
        let next = current + offset
        selectIndex(next, mode: extending ? 2 : 0, items: items)
    }

    func moveSelectionToBoundary(last: Bool, extending: Bool = false) {
        let items = visibleItems
        guard !items.isEmpty else { return }
        selectIndex(last ? items.count - 1 : 0, mode: extending ? 2 : 0, items: items, animated: false)
    }

    func chooseBoard(_ id: UUID?) {
        allowsEmptySelection = false
        pinboardID = id
        showDeleted = false
        selection = []
        primaryID = nil
        normalizeSelection()
    }

    func switchBoard(_ offset: Int) {
        let ids: [UUID?] = [nil] + store.pinboards.sorted { $0.sortOrder < $1.sortOrder }.map { Optional($0.id) }
        guard let current = ids.firstIndex(where: { $0 == pinboardID }) else { return }
        let next: Int
        switch offset {
        case -1: next = (current - 1 + ids.count) % ids.count
        case 1: next = (current + 1) % ids.count
        default: return
        }
        chooseBoard(ids[next])
    }

    func perform(_ action: () throws -> Void) {
        do { try action() }
        catch { controller?.presentError(error) }
    }

    func deleteSelection() {
        let before = visibleItems
        let ids = selection.isEmpty ? Set(primaryItem.map { [$0.id] } ?? []) : selection
        let indexes = before.indices.filter { ids.contains(before[$0].id) }
        var neighborID: UUID?
        if let first = indexes.min(), let last = indexes.max() {
            neighborID = [last + 1, first - 1].first {
                before.indices.contains($0) && !ids.contains(before[$0].id)
            }.map { before[$0].id }
        }
        do {
            if showDeleted || !isSearchQueryEmpty { try store.permanentlyDelete(ids: ids) }
            else { try store.delete(ids: ids, contextPinboardID: pinboardID) }
        } catch {
            controller?.presentError(error)
            return
        }
        let items = visibleItems
        guard items.map(\.id) != before.map(\.id) else { return }
        let visible = Set(items.map(\.id))
        let remaining = orderedSelectionIDs.filter { selection.contains($0) && visible.contains($0) }
        if remaining.isEmpty { allowsEmptySelection = true }
        applyOrderedSelection(remaining,
            anchor: rangeAnchorID.flatMap { visible.contains($0) ? $0 : nil },
            primary: primaryID.flatMap { remaining.contains($0) ? $0 : nil })
        if let neighborID, let index = items.firstIndex(where: { $0.id == neighborID }) {
            selectIndex(index, mode: 0, items: items)
        }
    }

    func assignSelection(to id: UUID?) {
        let ids = selection.isEmpty ? primaryItem.map { [$0.id] } ?? []
            : visibleItems.filter { selection.contains($0.id) }.map(\.id)
        perform { try store.assign(orderedIDs: ids, to: id) }
    }

    func addToStack(_ item: ClipboardItem) {
        guard !stackIDs.contains(item.id) else { return }
        let previousIDs = stackItems.map(\.id)
        let append = store.preferences.stackReversed
        let insertionIndex = append ? previousIDs.count : 0
        stackIDs.insert(item.id, at: append ? stackIDs.count : 0)
        controller?.stackTableController?.didInsertSnippet(previousIDs: previousIDs,
            updated: stackItems, at: insertionIndex)
    }

    func reverseStack() {
        OriginalStackFunctions.f_10008468c(&stackIDs)
        store.preferences.stackReversed.toggle()
        perform { try store.save() }
        controller?.stackTableController?.updateSnippets(stackItems)
    }

    func selectAll() {
        allowsEmptySelection = false
        let ids = visibleItems.map(\.id)
        applyOrderedSelection(ids, anchor: ids.last, primary: primaryID)
    }
    func deselectAll() {
        allowsEmptySelection = true
        applyOrderedSelection([], anchor: nil, primary: nil)
    }

    func pauseMonitoring(minutes: Int? = nil) {
        store.preferences.isMonitoringPaused = true
        store.preferences.pauseUntil = minutes.map { Date().addingTimeInterval(Double($0) * 60) }
        perform {
            try store.save()
            ReplicaCopiedOSD.showPaused(resumeDate: store.preferences.pauseUntil)
            monitoringPauseChanged?()
        }
    }

    func resumeMonitoring() {
        store.preferences.isMonitoringPaused = false
        store.preferences.pauseUntil = nil
        perform {
            try store.save()
            ReplicaCopiedOSD.showResumed()
            monitoringPauseChanged?()
        }
    }

    func movePinboard(_ board: Pinboard, by offset: Int) {
        var ids = store.pinboards.sorted { $0.sortOrder < $1.sortOrder }.map(\.id)
        guard let index = ids.firstIndex(of: board.id), ids.indices.contains(index + offset) else { return }
        ids.swapAt(index, index + offset)
        perform { try store.reorderPinboards(ids: ids) }
    }

    func movePinboard(id: UUID, before target: UUID) {
        guard id != target else { return }
        var ids = store.pinboards.sorted { $0.sortOrder < $1.sortOrder }.map(\.id)
        guard ids.contains(id), ids.contains(target) else { return }
        ids.removeAll { $0 == id }
        ids.insert(id, at: ids.firstIndex(of: target)!)
        perform { try store.reorderPinboards(ids: ids) }
    }
}

@MainActor
final class ReplicaPanel: NSPanel, NSWindowDelegate {
    weak var collectionFocusTarget: NSView?
    weak var tabTitleEditingOwner: OriginalPinboardTabTitleView?
    var keyHandler: ((NSEvent) -> Bool)?
    var didResignKey: (() -> Void)?
    var didChangeScreen: (() -> Void)?
    var closeRequested: (() -> Void)?
    var copyRequested: (() -> Void)?
    func windowDidResignKey(_ notification: Notification) { didResignKey?() }
    func windowDidChangeScreen(_ notification: Notification) { didChangeScreen?() }
    override func performClose(_ sender: Any?) { closeRequested?() }
    override func validateMenuItem(_ menuItem: NSMenuItem) -> Bool {
        if menuItem.action == #selector(NSWindow.performClose(_:)) { return true }
        return super.validateMenuItem(menuItem)
    }
    @objc func copy(_ sender: Any?) { copyRequested?() }
    override var canBecomeKey: Bool { true }
    override var canBecomeMain: Bool { true }
    override func layoutIfNeeded() {
        super.layoutIfNeeded()
        minSize = frame.size
        maxSize = frame.size
    }
    override func makeFirstResponder(_ responder: NSResponder?) -> Bool {
        if let responder { return super.makeFirstResponder(responder) }
        return super.makeFirstResponder(initialFirstResponder ?? contentView)
    }
    override func sendEvent(_ event: NSEvent) {
        if event.type == .keyDown, tabTitleEditingOwner?.ownsEditor(in: self) == true {
            super.sendEvent(event)
            return
        }
        if event.type == .keyDown, keyHandler?(event) == true { return }
        if event.type == .keyDown, let collection = collectionFocusTarget,
           collection.window === self, firstResponder === collection,
           let content = contentView as? ReplicaPanelContentView,
           content.tryInterpretSearchKeyEvent(event) { return }
        super.sendEvent(event)
    }
}

@MainActor
private final class ReplicaEditorWindow: NSWindow {
    override var canBecomeKey: Bool { true }
    override var canBecomeMain: Bool { true }
}

@MainActor
private final class ReplicaStackPanel: NSPanel {
    override var canBecomeKey: Bool { OriginalStackFunctions.f_1000114f4() }
    override var canBecomeMain: Bool { OriginalStackFunctions.f_1000114ec() }
}

@MainActor
final class ReplicaUIController {
    let store: ClipboardStore
    let state: ReplicaUIState
    let panel: NSPanel
    var pasteHandler: ((UUID, Bool) -> Bool)?
    var pasteItemsHandler: (([UUID], Bool) -> Bool)?
    var copiedItemsHandler: (() -> Void)?
    var pasteboard: NSPasteboard = .general
    var hotKeyConfigurationChanged: (() -> Void)?
    var hotKeyRecordingChanged: ((Bool) -> Void)?
    var stackDidChange: (() -> Void)?
    weak var stackTableController: OriginalStackTableController?
    var isStackVisible: Bool { stackWindow?.isVisible == true }
    var hotKeyStatusMessage: String {
        get { state.hotKeyStatusMessage }
        set { state.hotKeyStatusMessage = newValue }
    }
    private let sharingPolicy: WindowSharingPolicy
    private let panelFrameAutosaveName: String
    private var isPanelResizing = false
    private var panelTransitionGeneration = 0
    private var isPanelClosing = false
    private var panelMouseMonitor: Any?
    private var panelEscapeMonitor: Any?
    private var outsideMouseMonitor: Any?
    private var panelDismissObservers: [NSObjectProtocol] = []
    private var menuTrackingDepth = 0
    private weak var originalPanelScreen: NSScreen?
    private var settingsWindow: NSWindow?
    private var closedSearchTimer: Timer?
    private var closedCreateObserver: NSObjectProtocol?
    private var closedRestoreObservation: AnyCancellable?
    private var stackWindow: NSWindow?
    private var stackWindowController: OriginalStackWindowController?
    private var itemWindows: [UUID: NSWindow] = [:]
    private let previewRegistry = OriginalPreviewWindowRegistry()
    private var previewAnchors: [UUID: WeakReplicaPreviewAnchor] = [:]
    private var previewPopover: OriginalPreviewPopover?
    var filterBrowserPopover: OriginalFilterBrowserPopover?
    private var preferenceObservation: AnyCancellable?

    init(store: ClipboardStore) {
        self.store = store
        let storePath = store.directoryURL.standardizedFileURL.resolvingSymlinksInPath().path
        let namespace = SHA256.hash(data: Data(storePath.utf8)).map { String(format: "%02x", $0) }.joined()
        panelFrameAutosaveName = "PasteReplicaMainWindow_NSWindowFrameAutosaveName.\(namespace)"
        sharingPolicy = WindowSharingPolicy(store: store)
        state = ReplicaUIState(store: store)
        let panel = ReplicaPanel(contentRect: .init(x: 0, y: 0, width: 1512, height: 332),
                                 styleMask: [.borderless, .nonactivatingPanel],
                                 backing: .buffered, defer: false)
        self.panel = panel
        panel.identifier = NSUserInterfaceItemIdentifier("paste-replica-panel")
        panel.title = "Pasto"
        panel.isOpaque = false
        panel.backgroundColor = .clear
        panel.hasShadow = false
        panel.isMovable = false
        panel.isFloatingPanel = true
        panel.level = .mainMenu
        panel.hidesOnDeactivate = false
        panel.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
        panel.isReleasedWhenClosed = false
        sharingPolicy.apply(to: panel)
        let content = ReplicaPanelContentView(frame: NSRect(origin: .zero, size: panel.frame.size))
        content.canInterpretSearchInput = { [weak self, weak content] in
            guard let self, let content, self.panel.isKeyWindow,
                  let responder = self.panel.firstResponder else { return false }
            return responder === (self.panel as? ReplicaPanel)?.collectionFocusTarget || responder === content || responder === self.panel
        }
        content.onSearchText = { [weak self] text in
            guard let self else { return }
            let words = text.split(separator: " ").map(String.init)
            self.state.applySearchInput(nodes: words.map(OriginalSearchQueryNode.text),
                text: words.joined(separator: " "), filters: [])
            if !words.isEmpty {
                self.state.searchVisible = true
                self.state.searchFocus = UUID()
            }
        }
        let hosting = NSHostingView(rootView: ReplicaPanelView(state: state))
        hosting.frame = content.bounds
        hosting.autoresizingMask = [.width, .height]
        content.addSubview(hosting)
        panel.contentView = content
        panel.delegate = panel
        panel.didResignKey = { [weak self] in self?.panelDidResignKey() }
        panel.didChangeScreen = { [weak self] in self?.panelDidChangeScreen() }
        panel.closeRequested = { [weak self] in self?.hidePanel() }
        panel.copyRequested = { [weak self] in self?.copySelection(plainTextOnly: false) }
        restorePanelFrame()
        panel.layoutIfNeeded()
        installPanelResizeHandle()
        state.controller = self
        panel.keyHandler = { [weak self] event in self?.handleKey(event) ?? false }
        preferenceObservation = store.$preferences.sink { [weak self] _ in
            DispatchQueue.main.async { [weak self] in self?.applyAppearance() }
        }
        applyAppearance()
    }

    deinit {
        MainActor.assumeIsolated {
            removePanelDismissMonitors()
            cancelClosedState()
        }
    }

    func showPanel() {
        guard NSApp.modalWindow == nil else {
            NSApp.activate(ignoringOtherApps: true)
            return
        }
        guard let screen = NSScreen.main, let content = panel.contentView else { return }
        panelTransitionGeneration += 1
        let generation = panelTransitionGeneration
        isPanelClosing = false
        panel.backgroundColor = .clear
        positionPanel()
        panel.makeFirstResponder(nil)
        cancelClosedState()
        state.normalizeSelection()
        installPanelDismissMonitors()
        panel.makeKeyAndOrderFront(nil)
        originalPanelScreen = screen
        content.superview?.clipsToBounds = true
        content.frame = NSRect(origin: NSPoint(x: 0, y: -panel.frame.height), size: panel.frame.size)
        NSApp.activate(ignoringOtherApps: true)
        NSAnimationContext.runAnimationGroup { context in
            context.duration = 0.15
            context.timingFunction = CAMediaTimingFunction(controlPoints: 0.2, 0.8, 0.2, 1)
            context.allowsImplicitAnimation = true
            content.animator().frame = NSRect(origin: .zero, size: content.frame.size)
        } completionHandler: { [weak self, weak content] in
            MainActor.assumeIsolated {
                guard let self, let content, generation == self.panelTransitionGeneration else { return }
                if #available(macOS 26, *) {} else { self.panel.backgroundColor = .windowBackgroundColor }
                content.superview?.clipsToBounds = true
                if self.state.searchVisible, self.filterBrowserPopover?.isDisplayed != true {
                    self.state.searchFocus = UUID()
                }
            }
        }
    }

    private func panelDidChangeScreen() {
        guard let content = panel.contentView, let screen = panel.screen,
              let originalScreen = originalPanelScreen, !screen.isEqual(originalScreen) else { return }
        let frame = screen.frame
        panel.setFrame(.init(x: frame.minX, y: frame.minY,
                             width: frame.width, height: content.frame.height), display: true)
        originalPanelScreen = screen
    }

    private func panelDidResignKey() {
        // AppKit may be transferring key status to an attached popover or sheet.
        DispatchQueue.main.async { [weak self] in
            guard let self, self.canDismissPanelForInteraction,
                  !self.panel.isKeyWindow,
                  !self.isPanelInteractionWindow(NSApp.keyWindow) else { return }
            self.hidePanel()
        }
    }

    private var canDismissPanelForInteraction: Bool {
        panel.isVisible && !isPanelClosing && menuTrackingDepth == 0
            && panel.sheets.isEmpty && NSApp.modalWindow == nil
    }

    private func isPanelInteractionWindow(_ window: NSWindow?) -> Bool {
        guard let window else { return false }
        if window === previewPopover?.contentViewController?.viewIfLoaded?.window
            || window === filterBrowserPopover?.contentViewController?.viewIfLoaded?.window { return true }
        var ancestor: NSWindow? = window
        while let current = ancestor {
            if current === panel { return true }
            ancestor = current.parent
        }
        return false
    }

    private func installPanelDismissMonitors() {
        removePanelDismissMonitors()
        panelEscapeMonitor = NSEvent.addLocalMonitorForEvents(matching: .keyDown) { [weak self] event in
            let handled = MainActor.assumeIsolated { () -> Bool in
                guard let self, event.keyCode == 53, self.canDismissPanelForInteraction,
                      let window = event.window ?? NSApp.keyWindow else { return false }
                let filterWindow = self.filterBrowserPopover?.contentViewController?.viewIfLoaded?.window
                let previewWindow = self.previewPopover?.contentViewController?.viewIfLoaded?.window
                guard window === filterWindow || window === previewWindow else { return false }
                self.cancelSearchOrPanel()
                return true
            }
            return handled ? nil : event
        }
        let mouseDown: NSEvent.EventTypeMask = [.leftMouseDown, .rightMouseDown, .otherMouseDown]
        panelMouseMonitor = NSEvent.addLocalMonitorForEvents(matching: mouseDown) { [weak self] event in
            MainActor.assumeIsolated {
                guard let self, self.canDismissPanelForInteraction,
                      !self.isPanelInteractionWindow(event.window) else { return }
                if event.window == nil && self.panel.frame.contains(NSEvent.mouseLocation) { return }
                self.hidePanel()
            }
            return event
        }
        outsideMouseMonitor = NSEvent.addGlobalMonitorForEvents(matching: mouseDown) { [weak self] _ in
            DispatchQueue.main.async { [weak self] in
                guard let self, self.canDismissPanelForInteraction,
                      !self.panel.frame.contains(NSEvent.mouseLocation) else { return }
                self.hidePanel()
            }
        }
        let center = NotificationCenter.default
        panelDismissObservers.append(center.addObserver(forName: NSMenu.didBeginTrackingNotification,
            object: nil, queue: .main) { [weak self] _ in
                MainActor.assumeIsolated { self?.menuTrackingDepth += 1 }
            })
        panelDismissObservers.append(center.addObserver(forName: NSMenu.didEndTrackingNotification,
            object: nil, queue: .main) { [weak self] _ in
                MainActor.assumeIsolated {
                    guard let self else { return }
                    self.menuTrackingDepth = max(0, self.menuTrackingDepth - 1)
                    guard self.menuTrackingDepth == 0 else { return }
                    DispatchQueue.main.async { [weak self] in
                        guard let self, self.canDismissPanelForInteraction,
                              !self.panel.frame.contains(NSEvent.mouseLocation) else { return }
                        if !NSApp.isActive || (!self.panel.isKeyWindow
                            && !self.isPanelInteractionWindow(NSApp.keyWindow)) { self.hidePanel() }
                    }
                }
            })
        panelDismissObservers.append(center.addObserver(forName: NSApplication.didResignActiveNotification,
            object: NSApp, queue: .main) { [weak self] _ in
                MainActor.assumeIsolated {
                    guard let self, self.canDismissPanelForInteraction else { return }
                    self.hidePanel()
                }
            })
    }

    private func removePanelDismissMonitors() {
        if let panelMouseMonitor { NSEvent.removeMonitor(panelMouseMonitor) }
        if let panelEscapeMonitor { NSEvent.removeMonitor(panelEscapeMonitor) }
        if let outsideMouseMonitor { NSEvent.removeMonitor(outsideMouseMonitor) }
        panelMouseMonitor = nil
        panelEscapeMonitor = nil
        outsideMouseMonitor = nil
        for observer in panelDismissObservers { NotificationCenter.default.removeObserver(observer) }
        panelDismissObservers.removeAll()
        menuTrackingDepth = 0
    }

    func hidePanel() {
        guard panel.isVisible, !isPanelClosing, let content = panel.contentView else { return }
        removePanelDismissMonitors()
        panelTransitionGeneration += 1
        let generation = panelTransitionGeneration
        if #available(macOS 26, *) {} else { panel.backgroundColor = .clear }
        panel.makeFirstResponder(nil)
        beginClosedState()
        isPanelClosing = true
        NotificationCenter.default.post(name: OriginalPreviewPopover.mainWindowWillCloseNotification, object: nil)
        content.superview?.clipsToBounds = false
        NSAnimationContext.runAnimationGroup { context in
            context.duration = 0.2
            context.timingFunction = CAMediaTimingFunction(name: .easeInEaseOut)
            context.allowsImplicitAnimation = true
            content.animator().frame = NSRect(origin: NSPoint(x: 0, y: -content.frame.height), size: content.frame.size)
        } completionHandler: { [weak self, weak content] in
            MainActor.assumeIsolated {
                guard let self, let content, generation == self.panelTransitionGeneration else { return }
                self.panel.close()
                self.originalPanelScreen = nil
                self.isPanelClosing = false
                content.superview?.clipsToBounds = true
            }
        }
    }

    private func beginClosedState() {
        cancelClosedState()
        closedCreateObserver = NotificationCenter.default.addObserver(
            forName: ClipboardMonitor.didCreateItemNotification, object: nil, queue: .main) { [weak self] _ in
                MainActor.assumeIsolated {
                    guard let self else { return }
                    self.state.chooseBoard(nil)
                    self.closedSearchTimer?.invalidate()
                    self.closedSearchTimer = nil
                }
            }
        closedRestoreObservation = store.didRestoreItem.sink { [weak self] in
            guard let self, self.state.isSearchQueryEmpty, self.state.pinboardID == nil else { return }
            self.state.chooseBoard(nil)
            self.closedSearchTimer?.invalidate()
            self.closedSearchTimer = nil
        }
        closedSearchTimer = Timer.scheduledTimer(withTimeInterval: 10, repeats: false) { [weak self] _ in
            MainActor.assumeIsolated {
                guard let self, !self.state.isSearchQueryEmpty else { return }
                self.state.applySearchInput(nodes: [], text: "", filters: [])
                self.state.searchVisible = false
            }
        }
    }

    private func cancelClosedState() {
        closedSearchTimer?.invalidate()
        closedSearchTimer = nil
        if let closedCreateObserver { NotificationCenter.default.removeObserver(closedCreateObserver) }
        closedCreateObserver = nil
        closedRestoreObservation?.cancel()
        closedRestoreObservation = nil
    }
    func togglePanel() { panel.isVisible && !isPanelClosing ? hidePanel() : showPanel() }
    func focusSearch() {
        if !panel.isVisible || !panel.isKeyWindow || isPanelClosing { showPanel() }
        state.searchVisible = true
        state.searchFocus = UUID()
    }
    func showError(message: String) {
        presentError(NSError(domain: "Pasto", code: 1,
                             userInfo: [NSLocalizedDescriptionKey: message]))
    }

    func showSettings() {
        if settingsWindow == nil {
            settingsWindow = makeWindow(title: "设置", size: .init(width: 640, height: 564),
                                        view: ReplicaSettingsView(state: state))
        }
        show(settingsWindow!)
    }

    func showStack() {
        if stackWindow == nil {
            let window = ReplicaStackPanel(contentRect: .init(x: 0, y: 0, width: 264, height: 76),
                                           styleMask: [.borderless, .nonactivatingPanel], backing: .buffered, defer: false)
            window.title = "Pasto Stack"
            window.isReleasedWhenClosed = false
            window.isOpaque = false; window.backgroundColor = .clear; window.hasShadow = true
            window.contentView = NSHostingView(rootView: ReplicaStackView(state: state))
            sharingPolicy.apply(to: window)
            if !window.setFrameUsingName(OriginalStackWindowController.stackFrameAutosaveName),
               !window.setFrameUsingName("PasteReplicaStack") {
                let frame = NSScreen.main?.visibleFrame ?? .init(x: 0, y: 0, width: 1200, height: 800)
                window.setFrameOrigin(.init(x: frame.maxX - 284, y: frame.maxY - 96))
            }
            let controller = OriginalStackWindowController(window: window)
            controller.f_100011138()
            stackWindowController = controller
            stackWindow = window
        }
        hidePanel()
        stackWindow!.orderFrontRegardless()
        stackContentsChanged()
    }

    func hideStack() { stackWindowController?.close(); stackDidChange?() }

    func stackContentsChanged() {
        if let window = stackWindow {
            let height = CGFloat(32 + min(10, max(1, state.stackItems.count)) * 44)
            let top = window.frame.maxY
            window.setFrame(.init(x: window.frame.minX, y: top - height, width: 264, height: height), display: true)
        }
        stackDidChange?()
    }

    func captureIntoStack(id: UUID) {
        guard isStackVisible, let item = store.items.first(where: { $0.id == id && !$0.isDeleted }) else { return }
        state.addToStack(item)
    }

    func consumeStackHead() {
        let previousIDs = state.stackItems.map(\.id)
        guard let first = previousIDs.first else { return }
        guard let index = state.stackIDs.firstIndex(of: first) else { return }
        state.stackIDs.remove(at: index)
        stackTableController?.didConsumeHead(previousIDs: previousIDs, remaining: state.stackItems)
    }

    func newTextItem() { showEditor(item: nil) }

    func renameHistory() {
        guard let name = prompt(title: "重命名", message: "", initial: store.preferences.historyTitle) else { return }
        store.preferences.historyTitle = name
        state.perform { try store.save() }
    }

    func renameItem(_ item: ClipboardItem) {
        guard let title = prompt(title: "重命名", message: "", initial: item.title) else { return }
        state.perform { try store.updateItem(id: item.id, title: title, text: nil) }
    }

    func clearHistory() {
        guard store.items.contains(where: { $0.isInHistory && !$0.isDeleted }) else {
            state.perform { try store.eraseHistory() }
            return
        }
        let alert = NSAlert()
        sharingPolicy.apply(to: alert.window)
        alert.messageText = "您确定要删除剪贴板历史记录吗？"
        alert.informativeText = "已固定的项目和 Pasto 不会被删除。此操作无法撤销。"
        alert.addButton(withTitle: "删除历史"); alert.addButton(withTitle: "取消")
        if alert.runModal() == .alertFirstButtonReturn { state.perform { try store.eraseHistory() } }
    }

    func copySelection(plainTextOnly: Bool) {
        let items = state.selectedItems
        guard !items.isEmpty else { return }
        copy(ids: items.map(\.id), plainTextOnly: plainTextOnly)
    }

    func copy(item: ClipboardItem, plainTextOnly: Bool) {
        copy(ids: [item.id], plainTextOnly: plainTextOnly)
    }

    func copy(ids: [UUID], plainTextOnly: Bool) {
        guard !ids.isEmpty else { return }
        performCopy {
            try store.writeToPasteboard(ids: ids, pasteboard: pasteboard, plainTextOnly: plainTextOnly)
        }
    }

    func copyRecognizedImageText(item: ClipboardItem) {
        performCopy {
            try store.writeRecognizedImageTextToPasteboard(item: item, pasteboard: pasteboard)
        }
    }

    private func performCopy(_ write: () throws -> Void) {
        state.perform {
            try write()
            copiedItemsHandler?()
            // Deactivation may not emit a new notification for a nonactivating panel.
            hidePanel()
        }
    }

    func pasteSelection(plainTextOnly: Bool) {
        let items = state.selectedItems
        guard !items.isEmpty else { return }
        paste(ids: items.map(\.id), plainTextOnly: plainTextOnly)
    }

    @discardableResult
    func paste(item: ClipboardItem, plainTextOnly: Bool) -> Bool {
        paste(ids: [item.id], plainTextOnly: plainTextOnly)
    }

    @discardableResult
    func paste(ids: [UUID], plainTextOnly: Bool) -> Bool {
        guard !ids.isEmpty else { return false }
        if let pasteItemsHandler {
            return pasteItemsHandler(ids, plainTextOnly)
        }
        guard ids.count == 1, let id = ids.first, let pasteHandler else {
            presentError(NSError(domain: "Pasto", code: 1,
                                 userInfo: [NSLocalizedDescriptionKey: "粘贴服务尚未就绪，请使用“拷贝”后粘贴。 "]))
            return false
        }
        return pasteHandler(id, plainTextOnly)
    }

    func showPreview(item: ClipboardItem) {
        if let existing = previewRegistry.f_10008747c(itemIdentity: AnyHashable(item.id)) {
            show(existing)
            return
        }
        let anchor: NSView?
        if panel.isVisible, !isPanelClosing, state.visibleItems.contains(where: { $0.id == item.id }),
           let replicaPanel = panel as? ReplicaPanel,
           let collection = replicaPanel.collectionFocusTarget as? ReplicaNativeCollectionHost,
           collection.window === panel {
            guard let cell = collection.previewAnchor(for: item.id) else { return }
            anchor = cell
        } else {
            anchor = previewAnchors[item.id]?.view
        }
        if let anchor, anchor.window != nil {
            let popover = previewPopover ?? makePreviewPopover()
            previewPopover = popover
            if popover.isDisplayed {
                popover.close()
                return
            }
            popover.show(itemIdentity: AnyHashable(item.id), itemIdentifier: item.id.uuidString,
                contentView: makePreviewContent(for: item), relativeTo: anchor)
            return
        }
        let window = OriginalPreviewWindow()
        window.title = item.title.isEmpty ? item.kind.displayName : item.title
        let content = makePreviewContent(for: item)
        if let preview = content as? OriginalItemPreviewView {
            preview.onEditingStateChanged = { [weak self] editing in
                self?.previewRegistry.f_10008727c(isEditing: editing, itemIdentifier: item.id.uuidString)
            }
        }
        window.contentView = content
        window.setContentSize(content.frame.size)
        sharingPolicy.apply(to: window)
        window.center()
        previewRegistry.f_100086c10(window: window, itemIdentity: AnyHashable(item.id),
            itemIdentifier: item.id.uuidString, isEditing: false)
        show(window)
    }

    // f228c78 -> f229130 / f228e1c: only a successful reveal calls the live delegate.
    fileprivate func revealSelection(endpointID: UUID, requestedIndex: Int, animated: Bool) {
        guard let replicaPanel = panel as? ReplicaPanel,
              let collection = replicaPanel.collectionFocusTarget as? ReplicaNativeCollectionHost,
              collection.window === panel else { return }
        collection.revealSelection(state: state, itemID: endpointID, animated: animated) { [weak self, weak collection] success in
            guard success, let self, let collection else { return }
            self.selectionDidReveal(requestedIndex: requestedIndex, collection: collection)
        }
    }

    // f075e3c resolves the requested index after completion, not the revealed endpoint.
    private func selectionDidReveal(requestedIndex: Int, collection: ReplicaNativeCollectionHost) {
        let items = state.visibleItems
        guard items.indices.contains(requestedIndex),
              let anchor = collection.visibleSelectionAnchor(at: requestedIndex,
                  itemID: items[requestedIndex].id) else {
            NSSound.beep()
            return
        }
        let item = items[requestedIndex]
        if let popover = previewPopover, popover.isDisplayed {
            popover.show(itemIdentity: AnyHashable(item.id), itemIdentifier: item.id.uuidString,
                contentView: makePreviewContent(for: item), relativeTo: anchor)
        }
    }

    func registerPreviewAnchor(for itemID: UUID, view: NSView) {
        previewAnchors[itemID] = WeakReplicaPreviewAnchor(view)
    }

    func removePreviewAnchor(for itemID: UUID, view: NSView) {
        if previewAnchors[itemID]?.view === view { previewAnchors.removeValue(forKey: itemID) }
    }

    private func makePreviewContent(for item: ClipboardItem) -> NSView {
        makeOriginalReplicaPreview(state: state, item: item)
    }

    private func makePreviewPopover() -> OriginalPreviewPopover {
        let preferenceStore = store
        let changes = preferenceStore.preferenceChanges
            .filter { $0.old.showDuringScreenSharing != $0.new.showDuringScreenSharing }
            .map { $0.new.showDuringScreenSharing }.eraseToAnyPublisher()
        let popover = OriginalPreviewPopover(registry: previewRegistry,
            isScreenSharingContentVisible: { preferenceStore.preferences.showDuringScreenSharing },
            visibilityChanges: changes)
        popover.makeContentView = { [weak self] _, identifier in
            guard let self, let item = self.store.items.first(where: { $0.id.uuidString == identifier }) else { return nil }
            return makeOriginalReplicaPreview(state: self.state, item: item)
        }
        return popover
    }

    func showEditor(item: ClipboardItem?) {
        let windowID = UUID()
        let window = ReplicaEditorWindow(contentRect: NSRect(x: 0, y: 0, width: 500, height: 360),
                                         styleMask: [.borderless], backing: .buffered, defer: false)
        window.title = item == nil ? "新建文本" : "编辑文本"
        window.isReleasedWhenClosed = false
        window.isMovableByWindowBackground = true
        window.isOpaque = false
        window.backgroundColor = .clear
        window.hasShadow = true
        window.level = .floating
        sharingPolicy.apply(to: window)
        window.contentView = NSHostingView(rootView: ReplicaEditorView(state: state, item: item, close: { [weak self] in
            self?.itemWindows[windowID]?.close()
            self?.itemWindows.removeValue(forKey: windowID)
        }))
        window.center()
        itemWindows[windowID] = window
        show(window)
    }

    func createPinboard(assignSelection: Bool = false) {
        guard let name = prompt(title: OriginalSearchLocalization.text("pasto.action.create-group"), message: "为这个分组输入名称。", initial: "") else { return }
        let ids = state.visibleItems.filter { state.selection.contains($0.id) }.map(\.id)
        state.perform {
            let board = try store.createPinboard(name: name)
            if assignSelection { try store.assign(orderedIDs: ids, to: board.id) }
            state.chooseBoard(board.id)
        }
    }

    func renamePinboard(_ board: Pinboard) {
        guard let name = prompt(title: "重命名 Pasto", message: "输入新的分组名称。", initial: board.name) else { return }
        state.perform { try store.renamePinboard(id: board.id, name: name) }
    }

    func removePinboard(_ board: Pinboard) {
        let alert = NSAlert()
        alert.messageText = "删除“\(board.name)”？"
        alert.informativeText = "分组中的项目仍保留在剪贴板历史中。"
        alert.addButton(withTitle: "删除分组")
        alert.addButton(withTitle: "取消")
        if alert.runModal() == .alertFirstButtonReturn {
            state.perform { try store.removePinboard(id: board.id) }
            if state.pinboardID == board.id { state.chooseBoard(nil) }
        }
    }

    func exportArchive() {
        let chooser = NSSavePanel()
        sharingPolicy.apply(to: chooser)
        chooser.title = "导出剪贴板归档"
        chooser.nameFieldStringValue = "Pasto-archive.json"
        chooser.allowedContentTypes = [.json]
        if chooser.runModal() == .OK, let url = chooser.url {
            state.perform { try store.exportArchive(to: url) }
        }
    }

    func importArchive() {
        let chooser = NSOpenPanel()
        sharingPolicy.apply(to: chooser)
        chooser.title = "导入剪贴板归档"
        chooser.allowedContentTypes = [.json]
        chooser.allowsMultipleSelection = false
        if chooser.runModal() == .OK, let url = chooser.url {
            state.perform { try store.importArchive(from: url) }
            state.normalizeSelection()
        }
    }

    func migratePasteGroups() {
        guard !state.isMigratingPasteGroups else { return }
        hidePanel()
        NSApp.activate(ignoringOtherApps: true)
        let source: URL
        if let detected = PasteGroupMigration.defaultDatabaseURL {
            source = detected
        } else {
            let chooser = NSOpenPanel()
            sharingPolicy.apply(to: chooser)
            chooser.title = "选择 Paste 数据库"
            chooser.message = "未找到本机 Paste 数据。请选择 Paste 的 db.sqlite 文件；已安装的 Paste 将用于识别数据格式。"
            chooser.canChooseDirectories = false
            chooser.allowsMultipleSelection = false
            guard chooser.runModal() == .OK, let url = chooser.url else { return }
            source = url
        }
        state.isMigratingPasteGroups = true
        Task { @MainActor [weak self] in
            guard let self else { return }
            defer { self.state.isMigratingPasteGroups = false }
            do {
                let snapshot = try await Task.detached(priority: .userInitiated) {
                    try PasteGroupMigration.read(from: source)
                }.value
                let confirmation = NSAlert()
                self.sharingPolicy.apply(to: confirmation.window)
                confirmation.messageText = "从 Paste 迁移分组"
                guard !snapshot.pinboards.isEmpty else {
                    confirmation.informativeText = "未找到可迁移的本地分组。"
                    confirmation.addButton(withTitle: "好")
                    confirmation.runModal()
                    return
                }
                confirmation.informativeText = "发现 \(snapshot.pinboards.count) 个分组、\(snapshot.items.count) 个项目。\n将保留分组名称、颜色、排列顺序和项目内容。重复迁移不会重复添加，也不会覆盖 Pasto 已有的内容和设置。"
                if snapshot.unavailableItemCount > 0 {
                    confirmation.informativeText += "\n另有 \(snapshot.unavailableItemCount) 个项目的本地内容不可用，将跳过这些项目。"
                }
                confirmation.addButton(withTitle: "迁移")
                confirmation.addButton(withTitle: "取消")
                guard confirmation.runModal() == .alertFirstButtonReturn else { return }
                let result = try self.store.importPasteGroups(snapshot)
                self.state.normalizeSelection()
                let finished = NSAlert()
                self.sharingPolicy.apply(to: finished.window)
                finished.messageText = result.unavailableItems == 0 ? "迁移完成" : "迁移完成，部分项目已跳过"
                finished.informativeText = "已新增 \(result.addedGroups) 个分组、\(result.addedItems) 个项目。\n已存在：\(result.existingGroups) 个分组、\(result.existingItems) 个项目。"
                if result.unavailableItems > 0 {
                    finished.informativeText += "\n有 \(result.unavailableItems) 个项目未取得本地内容；在 Paste 中恢复内容后可重新迁移。"
                }
                finished.addButton(withTitle: "好")
                finished.runModal()
            } catch {
                self.presentError(error)
            }
        }
    }

    func presentError(_ error: Error) {
        let alert = NSAlert(error: error)
        sharingPolicy.apply(to: alert.window)
        alert.messageText = "操作未完成"
        alert.runModal()
    }

    private func prompt(title: String, message: String, initial: String) -> String? {
        let alert = NSAlert()
        sharingPolicy.apply(to: alert.window)
        alert.messageText = title
        alert.informativeText = message
        let input = NSTextField(string: initial)
        input.frame = .init(x: 0, y: 0, width: 300, height: 24)
        alert.accessoryView = input
        alert.addButton(withTitle: "确定")
        alert.addButton(withTitle: "取消")
        alert.window.initialFirstResponder = input
        guard alert.runModal() == .alertFirstButtonReturn else { return nil }
        let name = input.stringValue.trimmingCharacters(in: .whitespacesAndNewlines)
        return name.isEmpty ? nil : name
    }

    private func restorePanelFrame() {
        if !panel.setFrameUsingName(panelFrameAutosaveName) {
            let storedHeight = store.preferences.panelHeight
            let height = storedHeight.isFinite && storedHeight > 0 ? storedHeight : 332
            if panel.frame.height != height {
                var frame = panel.frame
                frame.size.height = height
                panel.setFrame(frame, display: true, animate: false)
                panel.saveFrame(usingName: panelFrameAutosaveName)
            }
        }
        store.preferences.panelHeight = panel.frame.height
    }

    private func installPanelResizeHandle() {
        guard let content = panel.contentView else { return }
        let handle = ReplicaPanelResizeHandle()
        handle.translatesAutoresizingMaskIntoConstraints = false
        content.addSubview(handle)
        NSLayoutConstraint.activate([
            handle.topAnchor.constraint(equalTo: content.topAnchor),
            handle.leadingAnchor.constraint(equalTo: content.leadingAnchor),
            handle.trailingAnchor.constraint(equalTo: content.trailingAnchor),
            handle.heightAnchor.constraint(equalToConstant: 10)
        ])
        handle.onLiveResize = { [weak self] size in self?.resizePanel(size: size) }
        handle.onEndResize = { [weak self] in self?.finishPanelResize() }
        handle.onResetSize = { [weak self] in self?.resetPanelSize() }
        handle.onGestureFinished = { [weak self] in self?.isPanelResizing = false }
    }

    private func resizePanel(size: NSSize) {
        isPanelResizing = true
        let height: CGFloat
        if size.height < 252 {
            height = 252 - (252 - size.height).squareRoot().rounded(.toNearestOrAwayFromZero)
        } else if size.height > 412 {
            height = 412 + (size.height - 412).squareRoot().rounded(.toNearestOrAwayFromZero)
        } else {
            height = size.height
        }
        panel.setFrame(NSRect(origin: panel.frame.origin,
                              size: NSSize(width: size.width, height: height)), display: false)
    }

    private func finishPanelResize() {
        var frame = panel.frame
        frame.size.height = min(max(frame.height, 252), 412)
        panel.setFrame(frame, display: true, animate: true)
        isPanelResizing = false
        savePanelFrame()
    }

    private func resetPanelSize() {
        guard panel.frame.height != 332 else { return }
        var frame = panel.frame
        frame.size.height = 332
        panel.setFrame(frame, display: true, animate: true)
        isPanelResizing = false
        savePanelFrame()
    }

    private func savePanelFrame() {
        panel.saveFrame(usingName: panelFrameAutosaveName)
        store.preferences.panelHeight = panel.frame.height
        state.perform { try store.save() }
    }

    private func positionPanel() {
        guard !isPanelResizing, let screen = NSScreen.main else { return }
        let frame = screen.frame
        let storedHeight = store.preferences.panelHeight
        let height = storedHeight.isFinite && storedHeight > 0 ? storedHeight : 332
        panel.setFrame(.init(x: frame.minX, y: frame.minY,
                             width: frame.width, height: height), display: true)
    }

    private func applyAppearance() {
        let appearance: NSAppearance?
        switch store.preferences.appearance {
        case "light": appearance = NSAppearance(named: .aqua)
        case "dark": appearance = NSAppearance(named: .darkAqua)
        default: appearance = nil
        }
        NSApp.appearance = appearance
        panel.appearance = appearance
        settingsWindow?.appearance = appearance
        stackWindow?.appearance = appearance
        itemWindows.values.forEach { $0.appearance = appearance }
        previewRegistry.windows.forEach { $0.appearance = appearance }
        if panel.isVisible { positionPanel() }
    }

    private func makeWindow<V: View>(title: String, size: NSSize, view: V) -> NSWindow {
        let window = NSWindow(contentRect: .init(origin: .zero, size: size),
                              styleMask: [.titled, .closable, .miniaturizable, .resizable],
                              backing: .buffered, defer: false)
        window.title = title
        window.isReleasedWhenClosed = false
        window.contentView = NSHostingView(rootView: view)
        sharingPolicy.apply(to: window)
        window.center()
        return window
    }

    private func show(_ window: NSWindow) {
        hidePanel()
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }

    private func handleKey(_ event: NSEvent) -> Bool {
        if event.keyCode == 53 {
            guard canDismissPanelForInteraction else { return false }
            cancelSearchOrPanel()
            return true
        }
        let modifiers = event.modifierFlags.intersection(.deviceIndependentFlagsMask)
        let command = modifiers.contains(.command)
        let shift = modifiers.contains(.shift)
        let isEditing = panel.firstResponder is NSTextView
        let key = event.charactersIgnoringModifiers?.lowercased() ?? ""
        if !state.searchVisible {
            if store.preferences.previousPinboardShortcut?.matches(event) == true { state.switchBoard(-1); return true }
            if store.preferences.nextPinboardShortcut?.matches(event) == true { state.switchBoard(1); return true }
        }
        let plainModifiers = NSEvent.ModifierFlags(rawValue: store.preferences.plainTextModifierRawValue)
        let plain = event.modifierFlags.isSuperset(of: plainModifiers)
        let signature = OriginalShortcutFunctions.f_1001e7d18(event)
        if !isEditing, let action = OriginalCollectionShortcutActions.quickPasteAction(for: signature,
            quickPasteModifierRawValue: store.preferences.quickPasteModifierRawValue,
            plainTextModifierRawValue: store.preferences.plainTextModifierRawValue) {
            let items = state.visibleItems
            if items.indices.contains(action.index) {
                paste(item: items[action.index], plainTextOnly: action.options.contains(.plainTextAndLinks))
            }
            if let first = state.visibleItems.first { state.select(first) }
            return true
        }
        if !isEditing, let options = OriginalCollectionShortcutActions.copyOptions(for: signature,
            plainTextModifierRawValue: store.preferences.plainTextModifierRawValue) {
            copySelection(plainTextOnly: options.contains(.plainTextAndLinks))
            return true
        }
        if signature.keyCode == OriginalShortcutFunctions.f_1001e94d4("f"),
           signature.modifierRawValue == NSEvent.ModifierFlags.command.rawValue {
            if state.searchVisible, filterBrowserPopover?.isDisplayed == true {
                filterBrowserPopover?.close()
            } else {
                handleSearchCommand()
            }
            return true
        }
        if command {
            switch key {
            case "n": shift ? createPinboard() : newTextItem(); return true
            case ",": showSettings(); return true
            case "a" where !isEditing: shift ? state.deselectAll() : state.selectAll(); return true
            default: break
            }
        }
        if event.keyCode == 49, !isEditing {
            if let item = state.selectedItems.last { showPreview(item: item) }
            return true
        }
        if !isEditing, let specialKey = event.specialKey {
            switch specialKey {
            case .backspace, .delete, .deleteForward:
                state.deleteSelection()
                return true
            case .carriageReturn, .enter:
                return OriginalSearchCommands.f_10004867c(selector: NSSelectorFromString("insertNewline:"),
                    onEnter: { [self] in pasteSelection(plainTextOnly: plain) }, onCancel: nil)
            default: break
            }
        }
        guard !isEditing else { return false }
        let control = modifiers.contains(.control)
        let specialKey = event.specialKey
        let navigation: Int
        if (control && key == "f") || specialKey == .rightArrow { navigation = 0 }
        else if (control && key == "b") || specialKey == .leftArrow { navigation = 1 }
        else if (control && key == "e") || (command && specialKey == .downArrow) { navigation = 3 }
        else if (control && key == "a") || (command && specialKey == .upArrow) { navigation = 2 }
        else { return false }
        if navigation == 0 || navigation == 1 {
            guard !command || shift else { return false }
            state.moveSelection(navigation == 0 ? 1 : -1, extending: shift)
        } else {
            state.moveSelectionToBoundary(last: navigation == 3, extending: shift)
        }
        return true
    }

    func cancelSearchOrPanel() {
        guard canDismissPanelForInteraction else { return }
        if filterBrowserPopover?.isShown == true { filterBrowserPopover?.close() }
        if previewPopover?.isShown == true { previewPopover?.close() }
        hidePanel()
    }
}
