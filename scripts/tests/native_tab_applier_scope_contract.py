"""Reverse only phase169 reviewed TabBar snapshot/mutation hunks for historical contracts."""
CHANGES = [['replica/Sources/Pasto/UI/OriginalPanelTabBar.swift',
  '    private var isCollapsed = false',
  '    private var isCollapsed = false\n'
  '    private var pendingTabs: [OriginalPinboardTab]?\n'
  '    private var hasAppliedSnapshot = false\n'
  '    private var snapshotDrainScheduled = false\n'
  '    private var isApplyingSnapshots = false\n'
  '    private var isPerformingLocalMutation = false',
  1],
 ['replica/Sources/Pasto/UI/OriginalPanelTabBar.swift',
  '    func configure(_ tabs: [OriginalPinboardTab]) {\n        let newKeys',
  '    func configure(_ tabs: [OriginalPinboardTab]) {\n'
  '        // 1b912c keeps the latest snapshot; each tab here carries its full configuration.\n'
  '        pendingTabs = tabs\n'
  '        scheduleSnapshotDrain()\n'
  '        // 096430 forces the initial applier delivery after installing its subscription.\n'
  '        if !hasAppliedSnapshot { drainSnapshots() }\n'
  '    }\n'
  '\n'
  '    private func scheduleSnapshotDrain() {\n'
  '        // 1b9214: applying, scheduled and local-mutation flags gate one main-queue delivery.\n'
  '        guard !isApplyingSnapshots, !snapshotDrainScheduled, !isPerformingLocalMutation else { return }\n'
  '        snapshotDrainScheduled = true\n'
  '        DispatchQueue.main.async { [weak self] in\n'
  '            MainActor.assumeIsolated { self?.drainSnapshots() }\n'
  '        }\n'
  '    }\n'
  '\n'
  '    private func drainSnapshots() {\n'
  '        // 1b95bc clears the pending slot before the renderer, then rechecks for reentry.\n'
  '        snapshotDrainScheduled = false\n'
  '        guard !isPerformingLocalMutation, !isApplyingSnapshots else { return }\n'
  '        isApplyingSnapshots = true\n'
  '        while !isPerformingLocalMutation, let tabs = pendingTabs {\n'
  '            pendingTabs = nil\n'
  '            hasAppliedSnapshot = true\n'
  '            applyTabs(tabs)\n'
  '        }\n'
  '        isApplyingSnapshots = false\n'
  '    }\n'
  '\n'
  '    private func applyTabs(_ tabs: [OriginalPinboardTab]) {\n'
  '        let newKeys',
  1],
 ['replica/Sources/Pasto/UI/OriginalPanelTabBar.swift',
  '    // 099838: locate the same native object, scroll its cell, then start editing after the animation.',
  '    func moveList(_ source: ClipboardListTarget, to target: ClipboardListTarget,\n'
  '                  persist: (Int) -> Void) -> Bool {\n'
  '        // 0973d8/097828 use the displayed applier positions, not a newer model snapshot.\n'
  '        guard let sourceIndex = keys.firstIndex(where: { cells[$0]?.listTarget?.hasSameObjectID(as: '
  'source) == true }),\n'
  '              let destinationIndex = keys.firstIndex(where: { cells[$0]?.listTarget?.hasSameObjectID(as: '
  'target) == true }) else { return false }\n'
  '        // 1b91e4 defers incoming snapshots throughout persistence and the local array move.\n'
  '        isPerformingLocalMutation = true\n'
  '        persist(sourceIndex < destinationIndex ? destinationIndex + 1 : destinationIndex)\n'
  '        // 1b9460: remove first, then insert at min(destination, post-removal count).\n'
  '        let key = keys.remove(at: sourceIndex)\n'
  '        keys.insert(key, at: min(destinationIndex, keys.count))\n'
  '        // Existing NSStackView renderer adapter; 0973d8 rebuilds cells after its applier move.\n'
  '        stack.setViews(keys.compactMap { cells[$0] }, in: .leading)\n'
  '        invalidateIntrinsicContentSize()\n'
  '        needsLayout = true\n'
  '        isPerformingLocalMutation = false\n'
  '        scheduleSnapshotDrain()\n'
  '        return true\n'
  '    }\n'
  '\n'
  '    // 099838: locate the same native object, scroll its cell, then start editing after the animation.',
  1],
 ['replica/Sources/Pasto/UI/OriginalPanelToolbar.swift',
  '    func applySearchQuery(_ nodes: [OriginalSearchQueryNode]) { searchBar.applySearchQuery(nodes) }',
  '    func moveList(_ source: ClipboardListTarget, to target: ClipboardListTarget,\n'
  '                  persist: (Int) -> Void) -> Bool {\n'
  '        tabBar.moveList(source, to: target, persist: persist)\n'
  '    }\n'
  '\n'
  '    func applySearchQuery(_ nodes: [OriginalSearchQueryNode]) { searchBar.applySearchQuery(nodes) }',
  1],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  "    // 097828 converts the final destination index to SwiftUI's pre-removal offset.\n"
  '    func moveList(identifier: String, to target: ClipboardListTarget) -> Bool {\n'
  '        guard let source = store.tabListTarget(identifier: identifier), let snapshot = tabListSnapshot,\n'
  '              let sourceIndex = snapshot.index(of: source), let destinationIndex = snapshot.index(of: '
  'target) else { return false }\n'
  '        let offset = sourceIndex < destinationIndex ? destinationIndex + 1 : destinationIndex\n'
  '        try? store.moveList(source, toOffset: offset)\n'
  '        return true\n'
  '    }',
  '    func moveList(identifier: String, to target: ClipboardListTarget) -> Bool {\n'
  '        guard let source = store.tabListTarget(identifier: identifier) else { return false }\n'
  '        return toolbarOwner?.moveList(source, to: target, persist: { offset in\n'
  '            // 3c4cdc consumes transaction errors; 097828 still performs its applier move.\n'
  '            try? self.store.moveList(source, toOffset: offset)\n'
  '        }) ?? false\n'
  '    }',
  1]]

def pre_native_tab_applier(source):
    from native_tab_renderer_delivery_scope_contract import pre_native_tab_renderer_delivery
    source = pre_native_tab_renderer_delivery(source)
    for _,old,new,count in reversed(CHANGES):
        if new in source:
            assert source.count(new)==count
            source=source.replace(new,old)
    return source
