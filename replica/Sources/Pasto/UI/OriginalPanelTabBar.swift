import AppKit
import Combine
import CoreData
import PastoCore

/// Native List snapshots drive the original full/incremental tab renderer.
@MainActor
final class OriginalPanelTabBar: NSView {
    private let scrollView = NSScrollView()
    private let documentContainer = NSView()
    private let stack = NSStackView()
    private var keys: [NSManagedObjectID] = []
    private var isCollapsed = false
    private var collectionSnapshot: ClipboardPinboardCollection.ListSnapshot?
    private var pendingSnapshot: (value: ClipboardPinboardCollection.ListSnapshot, updated: Set<NSManagedObjectID>)?
    private var listObservation: AnyCancellable?
    private var selectionObservation: AnyCancellable?
    private var configuration: ((ClipboardListTarget) -> OriginalPinboardTab)?
    private var currentSelection: (() -> ClipboardListTarget?)?
    private var hasAppliedSnapshot = false
    private var snapshotDrainScheduled = false
    private var isApplyingSnapshots = false
    private var isPerformingLocalMutation = false

    override init(frame frameRect: NSRect) {
        super.init(frame: frameRect)
        stack.orientation = .horizontal
        stack.spacing = 8
        stack.alignment = .centerY
        stack.distribution = .fill
        stack.detachesHiddenViews = false
        scrollView.drawsBackground = false
        scrollView.hasHorizontalScroller = false
        scrollView.hasVerticalScroller = false
        scrollView.horizontalScrollElasticity = .allowed
        scrollView.verticalScrollElasticity = .none
        scrollView.contentView.drawsBackground = false
        scrollView.documentView = documentContainer
        documentContainer.addSubview(stack)
        addSubview(scrollView)
        setContentCompressionResistancePriority(NSLayoutConstraint.Priority(250), for: .horizontal)
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    override var intrinsicContentSize: NSSize {
        // TabBarScrollView's recovered content inset is (6,7,6,7), height 40.
        // Its shadow-overlay drawing is still a separate incomplete contract.
        NSSize(width: stack.fittingSize.width + 14, height: 40)
    }

    func observeLists(_ publisher: AnyPublisher<ClipboardPinboardCollection.ListSnapshot, Never>,
                      configuration: @escaping (ClipboardListTarget) -> OriginalPinboardTab,
                      selection: AnyPublisher<ClipboardListTarget, Never>,
                      currentSelection: @escaping () -> ClipboardListTarget?) {
        self.configuration = configuration
        self.currentSelection = currentSelection
        listObservation = publisher.sink { [weak self] snapshot in
            MainActor.assumeIsolated { self?.receive(snapshot) }
        }
        // 096430 subscribes, forces the initial applier flush, then subscribes to selected List.
        drainSnapshots()
        selectionObservation = selection.sink { [weak self] target in
            MainActor.assumeIsolated { self?.selectList(target) }
        }
    }

    func updateConfiguration(_ configuration: @escaping (ClipboardListTarget) -> OriginalPinboardTab) {
        self.configuration = configuration
    }

    func stopObservingLists() {
        listObservation?.cancel()
        selectionObservation?.cancel()
        listObservation = nil
        selectionObservation = nil
        pendingSnapshot = nil
        collectionSnapshot = nil
        configuration = nil
        currentSelection = nil
    }

    private func receive(_ snapshot: ClipboardPinboardCollection.ListSnapshot) {
        collectionSnapshot = snapshot
        // 1b912c/1b59e4 replace IDs and union pending changed IDs before scheduling.
        pendingSnapshot = (snapshot, (pendingSnapshot?.updated ?? []).union(snapshot.updatedIdentifiers))
        scheduleSnapshotDrain()
    }

    private func scheduleSnapshotDrain() {
        // 1b9214: applying, scheduled and local-mutation flags gate one main-queue delivery.
        guard !isApplyingSnapshots, !snapshotDrainScheduled, !isPerformingLocalMutation else { return }
        snapshotDrainScheduled = true
        DispatchQueue.main.async { [weak self] in
            MainActor.assumeIsolated { self?.drainSnapshots() }
        }
    }

    private func drainSnapshots() {
        // 1b95bc clears the pending slot before the renderer, then rechecks for reentry.
        snapshotDrainScheduled = false
        guard !isPerformingLocalMutation, !isApplyingSnapshots else { return }
        isApplyingSnapshots = true
        while !isPerformingLocalMutation, let pending = pendingSnapshot {
            pendingSnapshot = nil
            applySnapshot(pending.value, updated: pending.updated)
        }
        isApplyingSnapshots = false
    }

    private func applySnapshot(_ snapshot: ClipboardPinboardCollection.ListSnapshot,
                               updated: Set<NSManagedObjectID>) {
        let newKeys = snapshot.identifiers
        let difference = newKeys.difference(from: keys).inferringMoves()
        var removals: Set<Int> = []
        var insertions: Set<Int> = []
        var moveSources: Set<Int> = []
        for change in difference {
            switch change {
            case let .remove(offset, _, associatedWith):
                if associatedWith == nil { removals.insert(offset) }
                else { moveSources.insert(offset) }
            case let .insert(offset, _, associatedWith):
                if associatedWith == nil { insertions.insert(offset) }
            }
        }
        // 1b5a8c enumerates OLD IDs; deletions and moved source offsets exclude updates.
        let updates = keys.indices.filter {
            updated.contains(keys[$0]) && !removals.contains($0) && !moveSources.contains($0)
        }
        let initial = !hasAppliedSnapshot
        if !initial, removals.isEmpty, insertions.isEmpty, moveSources.isEmpty, updates.isEmpty { return }
        hasAppliedSnapshot = true
        let fullReload = initial || removals.count + insertions.count + moveSources.count > OriginalCollectionSnapshot.fullReloadThreshold
        // 097eb0 invokes the applier setter before either rendering branch.
        keys = newKeys
        if fullReload || !moveSources.isEmpty {
            rebuildCells()
            layoutSubtreeIfNeeded()
            return
        }
        // 097eb0 deletes descending, inserts ascending, then reconfigures every current cell.
        for index in removals.sorted(by: >) {
            if let removed = cell(at: index) {
                removed.removeFromSuperview()
                if removed.isSelected, let selected = currentSelection?() { selectList(selected) }
            }
        }
        for index in insertions.sorted() {
            let inserted = OriginalPinboardTabView()
            stack.insertArrangedSubview(inserted, at: index)
            inserted.layoutSubtreeIfNeeded()
            configureCell(at: index)
        }
        for index in keys.indices { configureCell(at: index) }
        invalidateIntrinsicContentSize()
        needsLayout = true
        OriginalViewAnimation.f_10021cadc(duration: nil,
            timingFunction: OriginalViewAnimation.f_10021ccd4(), animated: true,
            animations: { self.superview?.layoutSubtreeIfNeeded() })
    }

    private func cell(at index: Int) -> OriginalPinboardTabView? {
        let views = stack.arrangedSubviews
        guard views.indices.contains(index) else { return nil }
        return views[index] as? OriginalPinboardTabView
    }

    private func configureCell(at index: Int) {
        guard keys.indices.contains(index),
              let target = collectionSnapshot?.target(for: keys[index]),
              let view = cell(at: index), let configuration else { return }
        configuration(target).configure(view)
        view.setCollapsed(isCollapsed)
    }

    private func rebuildCells() {
        for view in stack.arrangedSubviews { view.removeFromSuperview() }
        for index in keys.indices {
            let view = OriginalPinboardTabView()
            stack.insertArrangedSubview(view, at: index)
            view.layoutSubtreeIfNeeded()
            configureCell(at: index)
        }
        invalidateIntrinsicContentSize()
        needsLayout = true
    }

    private func selectList(_ target: ClipboardListTarget) {
        // 099218 clears all cells before resolving the same native object ID in the applier.
        for view in stack.arrangedSubviews.compactMap({ $0 as? OriginalPinboardTabView }) {
            view.setSelected(false)
        }
        guard let index = keys.firstIndex(of: target.objectID), let view = cell(at: index) else { return }
        view.setSelected(true)
        f_100095ae8(view)
    }

    func moveList(_ source: ClipboardListTarget, to target: ClipboardListTarget,
                  persist: (Int) -> Void) -> Bool {
        // 0973d8/097828 use the displayed applier positions, not a newer model snapshot.
        guard let sourceIndex = keys.firstIndex(of: source.objectID),
              let destinationIndex = keys.firstIndex(of: target.objectID) else { return false }
        // 1b91e4 defers incoming snapshots throughout persistence and the local array move.
        isPerformingLocalMutation = true
        persist(sourceIndex < destinationIndex ? destinationIndex + 1 : destinationIndex)
        // 1b9460: remove first, then insert at min(destination, post-removal count).
        let key = keys.remove(at: sourceIndex)
        keys.insert(key, at: min(destinationIndex, keys.count))
        isPerformingLocalMutation = false
        scheduleSnapshotDrain()
        // 0973d8 recreates cells from the moved applier and reads current model selection in configuration.
        rebuildCells()
        layoutSubtreeIfNeeded()
        if let cell = cell(at: destinationIndex), cell.isSelected {
            f_100095ae8(cell)
        }
        return true
    }

    // 099838: locate the same native object, scroll its cell, then start editing after the animation.
    func beginEditingList(_ target: ClipboardListTarget) {
        guard let index = keys.firstIndex(of: target.objectID), let cell = cell(at: index) else { return }
        window?.makeFirstResponder(nil)
        let rect = cell.frame.insetBy(dx: -17, dy: 0)
        OriginalViewAnimation.f_10021cadc(duration: 0.15,
            timingFunction: OriginalViewAnimation.f_10021ccd4(), animated: true,
            animations: { self.f_10009ac24(rect) },
            completion: { cell.titleView.beginEditingFromListRequest() })
    }

    func setCollapsed(_ collapsed: Bool) {
        isCollapsed = collapsed
        f_100095228()
    }

    private func f_100095228() {
        let tabs = stack.arrangedSubviews.compactMap { $0 as? OriginalPinboardTabView }
        for tab in tabs { tab.setCollapsed(isCollapsed) }
        invalidateIntrinsicContentSize()
        needsLayout = true
        if isCollapsed {
            _ = scrollToVisible(.zero)
            return
        }
        guard let selected = tabs.first(where: { $0.isSelected }) else { return }
        // 095228 retains the selected cell but captures the TabBar owner weakly.
        // Do not add a new generation/collapsed-state cancellation gate here.
        DispatchQueue.main.async { [weak self, selected] in
            MainActor.assumeIsolated { self?.f_100095ae8(selected) }
        }
    }

    private func f_100095ae8(_ cell: OriginalPinboardTabView) {
        // ARM 095ba0/095ba4: CGRectInset(frame, -17, 0).
        let rect = cell.frame.insetBy(dx: -17, dy: 0)
        OriginalViewAnimation.f_10021cadc(duration: 0.15,
            timingFunction: OriginalViewAnimation.f_10021ccd4(), animated: true,
            animations: { self.f_10009ac24(rect) })
    }

    private func f_10009ac24(_ rect: NSRect) { _ = scrollToVisible(rect) }

    override func scrollToVisible(_ rect: NSRect) -> Bool {
        // 051068 forwards to the underlying scroll view's contentView.
        scrollView.contentView.scrollToVisible(rect)
    }

    override func layout() {
        super.layout()
        scrollView.frame = bounds
        let size = stack.fittingSize
        documentContainer.frame = NSRect(origin: .zero,
            size: NSSize(width: size.width + 14, height: max(scrollView.contentSize.height, size.height + 12)))
        stack.frame = NSRect(x: 7, y: 6, width: size.width, height: size.height)
    }
}

@MainActor
final class OriginalPanelTabMenuItem: NSMenuItem {
    private let invoke: () -> Void
    init(title: String, invoke: @escaping () -> Void) {
        self.invoke = invoke
        super.init(title: title, action: #selector(performMenuAction), keyEquivalent: "")
        target = self
    }
    required init(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }
    @objc private func performMenuAction() { invoke() }
}
