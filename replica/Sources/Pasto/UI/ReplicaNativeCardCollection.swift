import AppKit
import Combine
import SwiftUI
import PastoCore

/// The viewport owns input and the dragging session; the document only supplies layout.
@MainActor
struct ReplicaNativeCollection: NSViewRepresentable {
    @ObservedObject var state: ReplicaUIState
    let cardSide: CGFloat

    func makeNSView(context: Context) -> ReplicaNativeCollectionHost {
        let view = ReplicaNativeCollectionHost(frame: .zero)
        view.update(state: state, cardSide: cardSide)
        return view
    }

    func updateNSView(_ nsView: ReplicaNativeCollectionHost, context: Context) {
        nsView.update(state: state, cardSide: cardSide)
    }

    static func dismantleNSView(_ nsView: ReplicaNativeCollectionHost, coordinator: ()) {
        nsView.detachObservers()
    }
}

@MainActor
final class ReplicaNativeCollectionHost: NSView, NSDraggingSource {
    private let scrollView = ReplicaNativeHorizontalScrollView(frame: .zero)
    private let document = ReplicaNativeCardDocument(frame: .zero)
    private let scrollAnimator = OriginalCollectionScrollAnimator()
    private weak var state: ReplicaUIState?
    private var listAttributesSource: ClipboardListAttributesObservation?
    private var listAttributesSubscription: AnyCancellable?
    private weak var focusPanel: ReplicaPanel?
    private var collectionIsFirstResponder = false
    private var dimmingMode: UInt8 = 0
    fileprivate var isDimmed: Bool {
        switch dimmingMode {
        case 0: return !collectionIsFirstResponder
        case 1: return false
        default: return true
        }
    }
    private var items: [ClipboardCollectionEntry] = []
    private var itemReferences: [UUID: ClipboardCollectionItemReference] = [:]
    private var hasReceivedCollectionSnapshot = false
    private var collectionOwnerGeneration: UInt64 = 0
    private struct PendingSnapshot {
        let items: [ClipboardCollectionEntry]
        let changedIDs: Set<UUID>
        let itemReferences: [UUID: ClipboardCollectionItemReference]
    }
    private var pendingSnapshot: PendingSnapshot?
    private var snapshotDrainScheduled = false
    private var isDrainingSnapshots = false
    private var cardSide: CGFloat = 0
    private var cells: [Int: ReplicaNativeCardCell] = [:]
    private var recycledCells: [ReplicaNativeCardCell] = []
    private var lastPrimaryID: UUID?
    private var needsPrimaryReveal = false
    private var boundsObserver: NSObjectProtocol?
    private var windowObservers: [NSObjectProtocol] = []
    private var initialDragLocation: NSPoint?
    private var dragWaitTimer: Timer?
    private weak var draggingSession: NSDraggingSession?
    private var draggingWriters: [any NSPasteboardWriting] = []
    private var localMarker: ReplicaLocalItemDrag?
    private static let markerType = NSPasteboard.PasteboardType(ReplicaLocalItemDrag.typeIdentifier)

    override init(frame frameRect: NSRect) {
        super.init(frame: frameRect)
        document.owner = self
        scrollView.borderType = .noBorder
        scrollView.drawsBackground = false
        scrollView.contentView.drawsBackground = false
        scrollView.hasHorizontalScroller = false
        scrollView.hasVerticalScroller = false
        scrollView.verticalScrollElasticity = .none
        scrollView.horizontalScrollElasticity = .allowed
        scrollView.documentView = document
        addSubview(scrollView)
        scrollView.contentView.postsBoundsChangedNotifications = true
        boundsObserver = NotificationCenter.default.addObserver(
            forName: NSView.boundsDidChangeNotification, object: scrollView.contentView, queue: .main
        ) { [weak self] _ in MainActor.assumeIsolated { self?.tileCells() } }
        registerForDraggedTypes([Self.markerType])
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    func update(state: ReplicaUIState, cardSide: CGFloat) {
        let replacesState = self.state !== state
        if replacesState {
            if let previousState = self.state {
                previousState.cancelPendingNeighborSelection()
                if previousState.collectionOwner === self { previousState.collectionOwner = nil }
            }
            hasReceivedCollectionSnapshot = false
            collectionOwnerGeneration &+= 1
            pendingSnapshot = nil
            snapshotDrainScheduled = false
            items = []
            itemReferences = [:]
        }
        self.state = state
        state.collectionOwner = self
        self.cardSide = cardSide
        if replacesState { installListAttributesObservation(state: state) }
        let incomingItems = state.visibleItems
        let incomingItemReferences = state.collectionItemReferences
        let changedIDs = state.takeCollectionChangedIDs(owner: self)
        // f1b912c replaces the pending items; f1b9214 schedules at most one drain.
        // Selection-only redraws do not change the pending data or its changed IDs.
        if pendingSnapshot?.items != incomingItems || !changedIDs.isEmpty
            || pendingSnapshot?.itemReferences != incomingItemReferences {
            pendingSnapshot = PendingSnapshot(items: incomingItems,
                changedIDs: (pendingSnapshot?.changedIDs ?? []).union(changedIDs),
                itemReferences: incomingItemReferences)
        }
        scheduleSnapshotDrain()
    }

    // 0x100036ee0 -> 0x100067c84 installs a fresh applier even when the
    // published search model is the same object. Data-only updates use update.
    func replaceCollectionModel(state: ReplicaUIState) {
        guard self.state === state, state.collectionOwner === self else { return }
        collectionOwnerGeneration &+= 1
        pendingSnapshot = nil
        snapshotDrainScheduled = false
        hasReceivedCollectionSnapshot = false
        items = []
        itemReferences = [:]
        installListAttributesObservation(state: state)
        update(state: state, cardSide: cardSide)
    }

    private func installListAttributesObservation(state: ReplicaUIState) {
        listAttributesSubscription = nil
        listAttributesSource = nil
        state.listAttributesSource = nil
        // 3b9264: search collections do not create a list-attributes subject.
        guard state.isCollectionSearchQueryEmpty, !state.showDeleted,
              let source = state.store.observeListAttributes(pinboardID: state.pinboardID) else { return }
        listAttributesSource = source
        state.listAttributesSource = source
        // 067c84 -> 07660c -> 0687d4 -> 22c22c: skip initial value, force visible-cell reload.
        listAttributesSubscription = source.publisher.dropFirst().sink { [weak self] _ in
            self?.reloadCellsForListAttributes()
        }
    }

    private func reloadCellsForListAttributes() {
        for cell in cells.values {
            cell.removeFromSuperview()
            cell.invalidateRendering()
            recycledCells.append(cell)
        }
        cells.removeAll()
        tileCells()
    }

    func appliedItems(for state: ReplicaUIState) -> [ClipboardCollectionEntry]? {
        guard self.state === state, state.collectionOwner === self else { return nil }
        return items
    }

    func appliedSelectedItems(for state: ReplicaUIState, orderedIDs: [UUID]) -> [ClipboardItem]? {
        guard self.state === state, state.collectionOwner === self else { return nil }
        let positions = Dictionary(uniqueKeysWithValues: items.enumerated().map { ($0.element.id, $0.offset) })
        return orderedIDs.compactMap { identifier in
            guard let index = positions[identifier] else { return nil }
            return items[index].item()
        }
    }

    func appliedRestoreItems(for state: ReplicaUIState, orderedIDs: [UUID]) -> [ClipboardRestoreItem]? {
        guard self.state === state, state.collectionOwner === self else { return nil }
        let positions = Dictionary(uniqueKeysWithValues: items.enumerated().map { ($0.element.id, $0.offset) })
        return orderedIDs.compactMap { identifier in
            guard let index = positions[identifier] else { return nil }
            return items[index].restoreItem()
        }
    }

    // 0x100228ee8 -> 0x100228f6c: deliver selection to visible cells synchronously.
    func applySelection(state: ReplicaUIState) {
        guard self.state === state, state.collectionOwner === self else { return }
        for (index, cell) in cells where items.indices.contains(index) && cell.itemID == items[index].id {
            cell.isSelected = state.selection.contains(items[index].id)
        }
    }

    // 0x100069778: only the last selected visible cell is a rename target.
    func renameSelection(state: ReplicaUIState) -> Bool {
        guard self.state === state, state.collectionOwner === self else { return false }
        guard let id = state.collectionSelectionSnapshot().orderedIDs.last else { return false }
        guard let index = items.firstIndex(where: { $0.id == id }),
              let cell = cells[index], cell.itemID == id else { return true }
        state.selectAppliedItem(at: index, items: items)
        cell.beginTitleEditing()
        return true
    }

    private func scheduleSnapshotDrain() {
        guard !snapshotDrainScheduled, !isDrainingSnapshots, pendingSnapshot != nil else { return }
        snapshotDrainScheduled = true
        let ownerGeneration = collectionOwnerGeneration
        DispatchQueue.main.async { [weak self] in
            guard let self, self.collectionOwnerGeneration == ownerGeneration else { return }
            self.snapshotDrainScheduled = false
            self.drainCollectionSnapshots()
        }
    }

    private func drainCollectionSnapshots() {
        guard !isDrainingSnapshots, let state, state.collectionOwner === self else { return }
        isDrainingSnapshots = true
        let ownerGeneration = collectionOwnerGeneration
        defer {
            isDrainingSnapshots = false
            scheduleSnapshotDrain()
        }
        // f1b95bc clears the pair before applying and rereads it after the callback.
        while collectionOwnerGeneration == ownerGeneration, self.state === state,
              state.collectionOwner === self, let pending = pendingSnapshot {
            pendingSnapshot = nil
            let incomingIDs = pending.items.map(\.id)
            guard incomingIDs == state.visibleItems.map(\.id) else { continue }
            let previousIDs = items.map(\.id)
            let isInitialSnapshot = !hasReceivedCollectionSnapshot
            let selectionRelevantSnapshotChanged = previousIDs != incomingIDs
            let hasRelevantChanges = !pending.changedIDs.isDisjoint(with: Set(incomingIDs))
            let requiresReload = isInitialSnapshot || (selectionRelevantSnapshotChanged
                && OriginalCollectionSnapshot.requiresFullReload(from: previousIDs, to: incomingIDs))
            hasReceivedCollectionSnapshot = true
            // Apply data and selection within the same drain, in original mutation-before-reload order.
            items = pending.items
            itemReferences = pending.itemReferences
            let primary = state.primaryID
            if primary != lastPrimaryID { needsPrimaryReveal = primary != nil }
            if let request = state.pendingListFocus, state.isCollectionSearchQueryEmpty,
               !state.showDeleted, state.pinboardID == request.pinboardID {
                needsPrimaryReveal = false
            }
            lastPrimaryID = primary
            layoutCollection()
            guard collectionOwnerGeneration == ownerGeneration, self.state === state,
                  state.collectionOwner === self else { continue }
            if !isInitialSnapshot && !selectionRelevantSnapshotChanged && !hasRelevantChanges {
                // Selection/layout-only redraws still deliver an explicit focus request.
                // They do not represent the original applier's data onUpdate callback.
                if state.pendingListFocus != nil { restorePendingListFocus(state: state) }
                continue
            }
            if requiresReload {
                state.applyFullCollectionReload(items: items)
                guard collectionOwnerGeneration == ownerGeneration, self.state === state,
                      state.collectionOwner === self else { continue }
                scrollView.contentView.bounds.origin = .zero
                lastPrimaryID = state.primaryID
                needsPrimaryReveal = false
                tileCells()
            } else {
                state.applyIncrementalCollectionSnapshot(items: items)
            }
            // f1b9b78 calls onUpdate only after its mutation/collection callback returns.
            guard collectionOwnerGeneration == ownerGeneration, self.state === state,
                  state.collectionOwner === self else { continue }
            if let neighbor = state.pendingNeighborSelection, incomingIDs != neighbor.beforeIDs {
                state.consumePendingNeighborSelection(token: neighbor.token, items: items)
            }
            if state.pendingListFocus != nil { restorePendingListFocus(state: state) }
        }
    }

    private func restorePendingListFocus(state: ReplicaUIState) {
        guard self.state === state, state.collectionOwner === self else { return }
        let itemIDs = items.map(\.id)
        guard itemIDs == state.visibleItems.map(\.id),
              let pendingFocus = state.consumePendingListFocus(itemIDs: itemIDs) else { return }
        lastPrimaryID = state.primaryID
        needsPrimaryReveal = false
        if let offset = pendingFocus.horizontalOffset {
            // f22cce0 sets clip bounds directly, without animation or clamping.
            scrollView.contentView.bounds.origin = CGPoint(
                x: cardFrame(pendingFocus.index).minX - offset, y: 0)
        } else {
            revealPrimaryCard(at: pendingFocus.index, animated: false)
        }
        tileCells()
    }

    override func layout() {
        super.layout()
        layoutCollection()
    }

    override var acceptsFirstResponder: Bool { true }
    override var canBecomeKeyView: Bool { true }

    override func keyDown(with event: NSEvent) {
        if let specialKey = event.specialKey {
            switch specialKey {
            case .backspace, .delete, .deleteForward:
                state?.deleteSelection()
                return
            default:
                break
            }
        }
        super.keyDown(with: event)
    }

    override func selectAll(_ sender: Any?) {
        state?.selectAll()
    }

    override func becomeFirstResponder() -> Bool {
        let success = super.becomeFirstResponder()
        collectionIsFirstResponder = success
        refreshCellRoots()
        return success
    }

    override func resignFirstResponder() -> Bool {
        let success = super.resignFirstResponder()
        collectionIsFirstResponder = !success
        refreshCellRoots()
        return success
    }

    private func clearFocusTarget() {
        guard let panel = focusPanel else { return }
        if panel.collectionFocusTarget === self { panel.collectionFocusTarget = nil }
        if panel.initialFirstResponder === self { panel.initialFirstResponder = nil }
        if panel.firstResponder === self { panel.makeFirstResponder(nil) }
        focusPanel = nil
    }

    override func viewDidMoveToWindow() {
        super.viewDidMoveToWindow()
        if focusPanel !== window { clearFocusTarget() }
        if let panel = window as? ReplicaPanel {
            focusPanel = panel
            panel.collectionFocusTarget = self
            panel.initialFirstResponder = self
            if panel.firstResponder === panel || panel.firstResponder === panel.contentView {
                panel.makeFirstResponder(self)
            }
        }
        for observer in windowObservers { NotificationCenter.default.removeObserver(observer) }
        windowObservers.removeAll()
        if let window {
            for name in [NSWindow.didBecomeKeyNotification, NSWindow.didResignKeyNotification] {
                windowObservers.append(NotificationCenter.default.addObserver(
                    forName: name, object: window, queue: .main
                ) { [weak self] _ in MainActor.assumeIsolated { self?.refreshCellRoots() } })
            }
            for name in [NSApplication.didBecomeActiveNotification, NSApplication.didResignActiveNotification] {
                windowObservers.append(NotificationCenter.default.addObserver(
                    forName: name, object: NSApp, queue: .main
                ) { [weak self] _ in MainActor.assumeIsolated { self?.refreshCellRoots() } })
            }
        }
        refreshCellRoots()
    }

    func detachObservers() {
        listAttributesSubscription = nil
        listAttributesSource = nil
        collectionOwnerGeneration &+= 1
        pendingSnapshot = nil
        snapshotDrainScheduled = false
        itemReferences = [:]
        if let state, state.collectionOwner === self {
            state.listAttributesSource = nil
            state.cancelPendingNeighborSelection()
            state.collectionOwner = nil
        }
        clearFocusTarget()
        if let boundsObserver { NotificationCenter.default.removeObserver(boundsObserver) }
        boundsObserver = nil
        for observer in windowObservers { NotificationCenter.default.removeObserver(observer) }
        windowObservers.removeAll()
        // Original timer destruction releases its reference; it does not invalidate on detach.
    }

    private func layoutCollection() {
        scrollView.frame = bounds
        let contentWidth = items.isEmpty ? bounds.width
            : 48 + CGFloat(items.count) * cardSide + CGFloat(items.count - 1) * 24
        document.frame = NSRect(x: 0, y: 0, width: max(bounds.width, contentWidth), height: bounds.height)
        tileCells()
        if needsPrimaryReveal, !bounds.isEmpty,
           let index = items.firstIndex(where: { $0.id == lastPrimaryID }) {
            needsPrimaryReveal = false
            revealPrimaryCard(at: index)
            tileCells()
        }
    }

    // 06bb3c/06be48: keep the requested index across scrolling, then read the applier again.
    func previewItem(at index: Int, present: @escaping (ClipboardRestoreItem, NSView) -> Void) {
        guard let state, state.collectionOwner === self, window != nil else { return }
        if items.indices.contains(index), let input = items[index].restoreItem(),
           let anchor = visibleSelectionAnchor(at: index, itemID: items[index].id) {
            present(input, anchor)
            return
        }
        revealPrimaryCard(at: index, animated: true) { [weak self] success in
            guard success else { return }
            self?.previewItem(at: index, present: present)
        }
    }

    func previewAnchor(for itemID: UUID, revealIfNeeded: Bool = true) -> NSView? {
        guard let state, let hostWindow = window, !bounds.isEmpty, cardSide > 0 else { return nil }
        update(state: state, cardSide: cardSide)
        // Explicit preview/reveal commands run outside the representable update transaction.
        drainCollectionSnapshots()
        guard let index = items.firstIndex(where: { $0.id == itemID }) else { return nil }
        if cells[index]?.itemID != itemID {
            guard revealIfNeeded else { return nil }
            revealPrimaryCard(at: index, animated: false)
            tileCells()
        }
        guard let cell = cells[index], cell.itemID == itemID,
              cell.superview === document, cell.window === hostWindow else { return nil }
        return cell
    }

    func revealSelection(state: ReplicaUIState, itemID: UUID, animated: Bool,
        completion: @escaping (Bool) -> Void) {
        guard self.state === state, state.collectionOwner === self,
              let index = items.firstIndex(where: { $0.id == itemID }) else { return }
        // This input selection owns its reveal. Do not also enqueue the primary-ID observer's reveal.
        lastPrimaryID = state.primaryID
        needsPrimaryReveal = false
        revealPrimaryCard(at: index, animated: animated, completion: completion)
    }

    func visibleSelectionAnchor(at index: Int, itemID: UUID) -> NSView? {
        guard items.indices.contains(index), items[index].id == itemID,
              let cell = cells[index], cell.itemID == itemID,
              cell.superview === document, let window, cell.window === window else { return nil }
        return cell
    }

    func horizontalOffsetForVisibleItem(_ itemID: UUID) -> CGFloat? {
        guard let index = items.firstIndex(where: { $0.id == itemID }),
              let cell = visibleSelectionAnchor(at: index, itemID: itemID) else { return nil }
        return cell.frame.minX - scrollView.contentView.bounds.minX
    }

    /// f22c9c4: intersecting cards report immediately; offscreen cards use the animator result.
    private func revealPrimaryCard(at index: Int, animated: Bool = true,
        completion: ((Bool) -> Void)? = nil) {
        let clip = scrollView.contentView
        var viewport = clip.bounds
        let card = cardFrame(index)
        let gap: CGFloat = 24
        if card.maxX > viewport.maxX {
            viewport.origin.x = card.minX - ((scrollView.frame.width - (gap + card.width)) - gap * 1.5)
        } else if card.minX < viewport.minX {
            viewport.origin.x = card.minX - (gap * 1.5 + gap)
        }
        // This document is horizontal only; preserve its existing vertical clip origin.
        if card.intersects(clip.bounds) {
            scrollAnimator.setContentOffset(viewport.origin, in: clip, animated: animated)
            completion?(true)
        } else {
            scrollAnimator.setContentOffset(viewport.origin, in: clip, animated: animated,
                completion: completion)
        }
    }

    private func cardFrame(_ index: Int) -> NSRect {
        NSRect(x: 24 + CGFloat(index) * (cardSide + 24), y: 24, width: cardSide, height: cardSide)
    }

    /// f233494 floors both endpoints and clamps an inclusive index interval.
    private func visibleIndexes() -> ClosedRange<Int>? {
        let viewport = scrollView.contentView.bounds
        guard !items.isEmpty, !viewport.isEmpty else { return nil }
        let step = cardSide + 24
        let first = Int(floor((viewport.minX - 24) / step))
        let last = Int(floor((viewport.maxX - 24) / step))
        precondition(last >= first)
        return max(0, min(items.count - 1, first))...max(0, min(items.count - 1, last))
    }

    private func renderedItem(at index: Int) -> ClipboardItem {
        items[index].requiredItem()
    }

    private func tileCells() {
        guard let state else { return }
        let desired = visibleIndexes().map { Set($0) } ?? []
        for index in Array(cells.keys) where !desired.contains(index) {
            if let cell = cells.removeValue(forKey: index) {
                cell.removeFromSuperview()
                recycledCells.append(cell)
            }
        }
        for index in desired.sorted() {
            let input = items[index].requiredRestoreItem()
            let item = input.resolvedItem()
            let cell: ReplicaNativeCardCell
            let needsInsertion: Bool
            if let existing = cells[index], existing.itemID == item.id {
                cell = existing
                needsInsertion = false
            } else {
                if let replaced = cells.removeValue(forKey: index) {
                    replaced.removeFromSuperview()
                    recycledCells.append(replaced)
                }
                cell = recycledCells.popLast()
                    ?? ReplicaNativeCardCell(owner: self, state: state, item: item, input: input, side: cardSide, index: index)
                cells[index] = cell
                needsInsertion = true
            }
            cell.frame = cardFrame(index)
            cell.update(state: state, item: item, input: input, side: cardSide, index: index)
            if needsInsertion { document.addSubview(cell) }
        }
    }

    private func refreshCellRoots() {
        guard let state else { return }
        for (index, cell) in cells where items.indices.contains(index) && cell.itemID == items[index].id {
            let input = items[index].requiredRestoreItem()
            cell.update(state: state, item: input.resolvedItem(), input: input, side: cardSide, index: index)
        }
    }

    private func index(at point: NSPoint) -> Int? {
        let position = document.convert(point, from: self)
        // f228568 resolves the actual visible cell frames, rather than a layout-derived slot.
        for (index, cell) in cells where items.indices.contains(index) && cell.itemID == items[index].id {
            if cell.frame.contains(position) { return index }
        }
        return nil
    }

    private func select(_ index: Int, modifiers: NSEvent.ModifierFlags = []) {
        guard let state, let current = appliedItems(for: state) else { return }
        guard current.indices.contains(index) else { return }
        state.select(renderedItem(at: index), modifiers: modifiers)
    }

    override func mouseDown(with event: NSEvent) {
        guard let state else { super.mouseDown(with: event); return }
        let point = convert(event.locationInWindow, from: nil)
        guard let index = index(at: point), event.clickCount <= 2 else {
            super.mouseDown(with: event)
            return
        }
        // f227cd4 only redirects Control-click after a visible-cell hit and click-count gate.
        if event.modifierFlags.contains(.control) {
            rightMouseDown(with: event)
            return
        }
        window?.makeFirstResponder(self)
        if event.clickCount == 2 {
            dragWaitTimer?.invalidate()
            state.selectForDoubleClick(at: index)
            lastPrimaryID = state.primaryID
            needsPrimaryReveal = false
            refreshCellRoots()
            let current = appliedItems(for: state) ?? []
            if current.indices.contains(index) {
                let plain = NSEvent.ModifierFlags(rawValue: state.store.preferences.plainTextModifierRawValue)
                state.controller?.paste(itemID: current[index].id, plainTextOnly: event.modifierFlags.isSuperset(of: plain))
            }
            return
        }
        initialDragLocation = point
        let mode = OriginalOrderedSelection.mode(modifierFlags: event.modifierFlags.rawValue)
        if !state.selection.contains(items[index].id) || mode != 0 {
            select(index, modifiers: event.modifierFlags)
        } else {
            // A new press replaces the stored reference, without inventing an old-timer debounce.
            dragWaitTimer = Timer.scheduledTimer(withTimeInterval: 0.45, repeats: false) { [weak self] _ in
                MainActor.assumeIsolated { self?.state?.selectAfterPressDelay(at: index) }
            }
        }
    }

    override func mouseDragged(with event: NSEvent) {
        guard let initialDragLocation else { return }
        dragWaitTimer?.invalidate()
        let point = convert(event.locationInWindow, from: nil)
        guard hypot(point.x - initialDragLocation.x, point.y - initialDragLocation.y) > 3,
              let state, !state.orderedSelectionIDs.isEmpty else { return }
        beginNativeDrag(event, state: state)
        self.initialDragLocation = nil
    }

    private func beginNativeDrag(_ event: NSEvent, state: ReplicaUIState) {
        guard let applied = appliedItems(for: state) else { return }
        let positions = Dictionary(uniqueKeysWithValues: applied.enumerated().map { ($0.element.id, $0.offset) })
        let requestedIndexes = state.orderedSelectionIDs.filter { state.selection.contains($0) }.compactMap { positions[$0] }
        var indexes: [Int] = []
        let selected = requestedIndexes.compactMap { index -> ClipboardRestoreItem? in
            guard let input = applied[index].restoreItem() else { return nil }
            indexes.append(index)
            return input
        }
        let plain = NSEvent.ModifierFlags(rawValue: state.store.preferences.plainTextModifierRawValue)
        let options: OriginalPasteboardRestore.Options = NSEvent.modifierFlags.isSuperset(of: plain) ? .plainText : []
        do {
            let groups = try state.store.dragPasteboardGroups(restoreItems: selected, options: options)
            let sources: [any OriginalDragItemIdentifierSource] = selected.map { $0.makeDragIdentifierSource() }
            let writers = OriginalNativeDragPasteboardWriter.writers(sources: sources, groups: groups)
            localMarker = nil
            var markerData: Data?
            if let boardID = state.pinboardID, state.isCollectionSearchQueryEmpty, !state.showDeleted {
                let marker = ReplicaLocalItemDrag(sessionID: state.itemDragSessionID, boardID: boardID,
                                                  ids: selected.map(\.id))
                markerData = try JSONEncoder().encode(marker)
                localMarker = marker
            }
            draggingWriters = writers.map { writer -> any NSPasteboardWriting in
                if let markerData { return ReplicaNativeLocalDragWriter(writer: writer, marker: markerData) }
                return writer
            }
            let dragItems = zip(indexes, draggingWriters).map { index, writer in
                let frame = convert(cardFrame(index), from: document)
                let cell = cells[index].flatMap { $0.itemID == items[index].id ? $0 : nil }
                return ReplicaNativeDragPreview.makeItem(writer: writer, draggingFrame: frame,
                    visibleCell: cell, singleWriter: writers.count == 1)
            }
            let session = beginDraggingSession(with: dragItems, event: event, source: self)
            session.draggingFormation = event.modifierFlags.contains(.control) ? .stack : .pile
            draggingSession = session
        } catch {
            localMarker = nil
            draggingWriters.removeAll()
            state.controller?.presentError(error)
        }
    }

    func draggingSession(_ session: NSDraggingSession,
                         sourceOperationMaskFor context: NSDraggingContext) -> NSDragOperation {
        context == .outsideApplication ? .copy : [.copy, .move]
    }

    func draggingSession(_ session: NSDraggingSession, willBeginAt screenPoint: NSPoint) {
        draggingSession = session
    }

    func draggingSession(_ session: NSDraggingSession, movedTo screenPoint: NSPoint) {
        guard let window, !window.frame.contains(screenPoint) else { return }
        draggingSession?.animatesToStartingPositionsOnCancelOrFail = false
        NSApp.deactivate()
    }

    func draggingSession(_ session: NSDraggingSession, endedAt screenPoint: NSPoint,
                         operation: NSDragOperation) {
        // Original concrete business delegate is the separately excluded Paywall route.
        if let window, window.frame.contains(screenPoint) {
            DispatchQueue.main.asyncAfter(deadline: .now() + 1) {
                NSApp.activate(ignoringOtherApps: true)
            }
        }
        draggingSession = nil
        draggingWriters.removeAll()
        localMarker = nil
    }

    private func validatedDrag(_ sender: NSDraggingInfo) -> ReplicaLocalItemDrag? {
        guard let state, let marker = localMarker, let session = draggingSession,
              (sender.draggingSource as? ReplicaNativeCollectionHost) === self,
              sender.draggingSequenceNumber == session.draggingSequenceNumber,
              state.pinboardID == marker.boardID, state.isCollectionSearchQueryEmpty, !state.showDeleted,
              let data = sender.draggingPasteboard.data(forType: Self.markerType),
              let decoded = try? JSONDecoder().decode(ReplicaLocalItemDrag.self, from: data),
              decoded.sessionID == marker.sessionID, decoded.boardID == marker.boardID,
              decoded.ids == marker.ids else { return nil }
        return marker
    }

    private func validatedDrop(_ sender: NSDraggingInfo) -> (ReplicaLocalItemDrag, Int)? {
        guard let state, let marker = validatedDrag(sender) else { return nil }
        let point = document.convert(sender.draggingLocation, from: nil)
        for (index, cell) in cells where items.indices.contains(index) && cell.itemID == items[index].id {
            let frame = cell.frame
            guard frame.insetBy(dx: -24, dy: 0).contains(point) else { continue }
            guard let current = state.store.items(in: marker.boardID).firstIndex(where: { $0.id == items[index].id }) else { return nil }
            return (marker, current + (point.x >= frame.midX ? 1 : 0))
        }
        return nil
    }

    /// f226764 receives the original window-space draggingLocation, without a conversion.
    private func dragEdgeDelta(windowX x: CGFloat) -> CGFloat {
        let leftThreshold = bounds.minX + 30
        let secondBounds = bounds
        let distance: CGFloat
        let sign: CGFloat
        if x <= leftThreshold {
            distance = x - secondBounds.minX
            sign = -1
        } else {
            // Original B.HI after FCMP(rightThreshold, x) also returns zero when unordered.
            guard secondBounds.maxX + -30 <= x else { return 0 }
            distance = bounds.maxX - x
            sign = 1
        }
        return sign * (((30 - distance) / 30) * 15)
    }

    override func draggingEntered(_ sender: NSDraggingInfo) -> NSDragOperation {
        validatedDrag(sender) == nil ? [] : .move
    }

    override func draggingUpdated(_ sender: NSDraggingInfo) -> NSDragOperation {
        guard validatedDrag(sender) != nil else { return [] }
        let clip = scrollView.contentView
        var nextBounds = clip.bounds
        nextBounds.origin.x += dragEdgeDelta(windowX: sender.draggingLocation.x)
        if nextBounds != clip.bounds { clip.bounds = nextBounds }
        return .move
    }

    override func prepareForDragOperation(_ sender: NSDraggingInfo) -> Bool {
        validatedDrop(sender) != nil
    }

    override func performDragOperation(_ sender: NSDraggingInfo) -> Bool {
        guard let state, let (marker, offset) = validatedDrop(sender) else { return false }
        do {
            try state.store.reorderItems(ids: marker.ids, in: marker.boardID, toOffset: offset)
            return true
        } catch {
            state.controller?.presentError(error)
            return false
        }
    }

    deinit {
        if let boundsObserver { NotificationCenter.default.removeObserver(boundsObserver) }
        for observer in windowObservers { NotificationCenter.default.removeObserver(observer) }
    }
}

@MainActor
private final class ReplicaNativeCardDocument: NSView {
    weak var owner: ReplicaNativeCollectionHost?

    override func hitTest(_ point: NSPoint) -> NSView? {
        let result = super.hitTest(point)
        if result === self, let event = NSApp.currentEvent,
           event.type == .leftMouseDown, !event.modifierFlags.contains(.control) {
            if let owner { return owner }
            return result
        }
        return result
    }
}

@MainActor
private final class ReplicaNativeCardCell: NSView, ReplicaNativeDragPreviewCell {
    weak var owner: ReplicaNativeCollectionHost?
    private weak var state: ReplicaUIState?
    private var item: ClipboardItem
    private var titleInput: ClipboardRestoreItem
    private var side: CGFloat
    private var absoluteIndex: Int
    private let shortcutIndicator = OriginalCardShortcutIndicatorView(frame: .zero)
    private let hosting = NSHostingView<AnyView>(rootView: AnyView(EmptyView()))
    private var renderedSelection: Bool
    private struct RenderingSignature: Equatable {
        let item: ClipboardItem
        let side: CGFloat
        let index: Int
        let selected: Bool
        let dimmed: Bool
        let scheme: ColorScheme?
        let active: ControlActiveState
    }
    private var renderingSignature: RenderingSignature?
    var itemID: UUID { item.id }
    var snapshotView: NSView { self }
    var isSelected: Bool {
        get { renderedSelection }
        set { renderedSelection = newValue; updateRoot() }
    }

    init(owner: ReplicaNativeCollectionHost, state: ReplicaUIState, item: ClipboardItem, input: ClipboardRestoreItem, side: CGFloat, index: Int) {
        self.owner = owner
        self.state = state
        self.item = item
        titleInput = input
        self.side = side
        absoluteIndex = index
        renderedSelection = state.selection.contains(item.id)
        super.init(frame: .zero)
        wantsLayer = true
        addSubview(hosting)
        addSubview(shortcutIndicator)
        shortcutIndicator.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            shortcutIndicator.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -8),
            shortcutIndicator.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -8)
        ])
        updateRoot()
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    func update(state: ReplicaUIState, item: ClipboardItem, input: ClipboardRestoreItem, side: CGFloat, index: Int) {
        if self.state !== state || !titleInput.hasSameEntity(as: input) { renderingSignature = nil }
        self.state = state
        self.item = item
        titleInput = input
        self.side = side
        absoluteIndex = index
        renderedSelection = state.selection.contains(item.id)
        hosting.frame = bounds
        updateRoot()
    }

    func invalidateRendering() { renderingSignature = nil }

    private func updateRoot() {
        guard let state else { return }
        let active: ControlActiveState = !NSApp.isActive ? .inactive : (window?.isKeyWindow == true ? .key : .active)
        let signature = RenderingSignature(item: item, side: side, index: absoluteIndex,
            selected: renderedSelection, dimmed: owner?.isDimmed ?? true, scheme: state.preferredScheme, active: active)
        guard renderingSignature != signature else { return }
        renderingSignature = signature
        hosting.rootView = AnyView(ReplicaClipboardCard(state: state, item: item, sideLength: side,
            selectionOverride: renderedSelection, dimmingOverride: owner?.isDimmed ?? true, nativeInteractions: true, titleInput: titleInput)
            .id(item.id)
            .preferredColorScheme(state.preferredScheme)
            .environment(\.controlActiveState, active))
        if item.kind == .color, let metadata = item.decodedColorPreviewMetadata {
            let color = OriginalColorPreviewMetadataGenerator.color(metadata.code)
            shortcutIndicator.appearance = NSAppearance(named:
                OriginalPreviewTextColors.f_1002067d4(color) ? .aqua : .darkAqua)
        } else if (item.kind == .text || item.kind == .richText),
                  let metadata = item.decodedTextPreviewMetadata {
            shortcutIndicator.appearance = OriginalCompactTextCardAppearance.appearance(
                for: OriginalCompactTextCardAppearance.background(for: metadata.text))
        } else {
            shortcutIndicator.appearance = nil
        }
        let store = state.store
        shortcutIndicator.configure(index: absoluteIndex < 9 ? absoluteIndex + 1 : nil,
            isEnabled: !(owner?.isDimmed ?? true),
            provider: { (plain: store.preferences.plainTextModifierRawValue,
                         quick: store.preferences.quickPasteModifierRawValue) },
            textColor: OriginalToolbarAppearance.secondaryForeground())
    }

    override func layout() {
        super.layout()
        hosting.frame = bounds
    }

    override func viewDidMoveToWindow() {
        super.viewDidMoveToWindow()
        if window != nil { updateRoot() }
    }

    func flushPreviewRendering() {
        layoutSubtreeIfNeeded()
        hosting.layoutSubtreeIfNeeded()
        hosting.displayIfNeeded()
        displayIfNeeded()
    }

    func beginTitleEditing() {
        var views = hosting.subviews
        while let view = views.popLast() {
            if let title = view as? ReplicaCardTitleView, title.itemID == item.id {
                title.beginEditing()
                return
            }
            views.append(contentsOf: view.subviews)
        }
    }

    override func hitTest(_ point: NSPoint) -> NSView? {
        guard let result = super.hitTest(point) else { return nil }
        guard let event = NSApp.currentEvent, event.type == .leftMouseDown,
              !event.modifierFlags.contains(.control) else { return result }
        var responder: NSView? = result
        while let view = responder, view !== self {
            if view is ReplicaCardTitleView { return result }
            if let text = view as? NSTextView, text.isEditable { return result }
            if let field = view as? NSTextField, field.isEditable { return result }
            if view is NSButton { return result }
            responder = view.superview
        }
        if let owner { return owner }
        return result
    }
}

/// Only the replica's local reorder marker is added; original grouped payload stays intact.
private final class ReplicaNativeLocalDragWriter: NSObject, NSPasteboardWriting {
    private let writer: OriginalNativeDragPasteboardWriter
    private let marker: Data
    private static let markerType = NSPasteboard.PasteboardType(ReplicaLocalItemDrag.typeIdentifier)

    init(writer: OriginalNativeDragPasteboardWriter, marker: Data) {
        self.writer = writer
        self.marker = marker
        super.init()
    }

    func writableTypes(for pasteboard: NSPasteboard) -> [NSPasteboard.PasteboardType] {
        writer.writableTypes(for: pasteboard) + [Self.markerType]
    }

    func pasteboardPropertyList(forType type: NSPasteboard.PasteboardType) -> Any? {
        if type == Self.markerType { return marker }
        return writer.pasteboardPropertyList(forType: type)
    }
}

/// Original NoShiftHorizontalScrollView remaps only the integer wheel axes.
@MainActor
private final class ReplicaNativeHorizontalScrollView: NSScrollView {
    override class var isCompatibleWithResponsiveScrolling: Bool { true }

    // f236910 preserves the original event if reconstruction returns nil.
    override func scrollWheel(with event: NSEvent) {
        super.scrollWheel(with: remappedWheelEvent(event) ?? event)
    }

    // f236978 returns the original event on passthrough, and the optional reconstruction on remap.
    private func remappedWheelEvent(_ event: NSEvent) -> NSEvent? {
        guard event.scrollingDeltaX == 0, event.scrollingDeltaY != 0,
              let cgEvent = event.cgEvent else { return event }
        cgEvent.setIntegerValueField(.scrollWheelEventDeltaAxis2, value: Int64(event.scrollingDeltaY))
        cgEvent.setIntegerValueField(.scrollWheelEventDeltaAxis1, value: 0)
        return NSEvent(cgEvent: cgEvent)
    }
}
