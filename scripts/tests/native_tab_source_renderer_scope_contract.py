"""Reverse only reviewed phase171 native source/diff renderer/selection hunks."""
CHANGES = [['replica/Sources/PastoCore/ClipboardListPersistence.swift',
  'public struct ClipboardListTarget {\n    let nativeObject: NSManagedObject',
  'public struct ClipboardListTarget {\n'
  '    let nativeObject: NSManagedObject\n'
  '    public var objectID: NSManagedObjectID { nativeObject.objectID }',
  1],
 ['replica/Sources/PastoCore/ClipboardSearchCollection.swift',
  '    @MainActor public struct ListSnapshot {\n'
  '        private let identifiers: [NSManagedObjectID]\n'
  '        private let context: NSManagedObjectContext\n'
  '        fileprivate init(identifiers: [NSManagedObjectID], context: NSManagedObjectContext) {\n'
  '            self.identifiers = identifiers\n'
  '            self.context = context\n'
  '        }',
  '    @MainActor public struct ListSnapshot {\n'
  '        public let identifiers: [NSManagedObjectID]\n'
  '        public let updatedIdentifiers: Set<NSManagedObjectID>\n'
  '        private let context: NSManagedObjectContext\n'
  '        fileprivate init(identifiers: [NSManagedObjectID], updatedIdentifiers: Set<NSManagedObjectID>,\n'
  '                         context: NSManagedObjectContext) {\n'
  '            self.identifiers = identifiers\n'
  '            self.updatedIdentifiers = updatedIdentifiers\n'
  '            self.context = context\n'
  '        }',
  1],
 ['replica/Sources/PastoCore/ClipboardSearchCollection.swift',
  '        public func target(at index: Int) -> ClipboardListTarget? {\n'
  '            guard identifiers.indices.contains(index),\n'
  '                  let object = (try? context.existingObject(with: identifiers[index])) as? '
  'PastoListEntity else { return nil }\n'
  '            return ClipboardListTarget(object: object)\n'
  '        }',
  '        public func target(at index: Int) -> ClipboardListTarget? {\n'
  '            guard identifiers.indices.contains(index) else { return nil }\n'
  '            return target(for: identifiers[index])\n'
  '        }\n'
  '        public func target(for objectID: NSManagedObjectID) -> ClipboardListTarget? {\n'
  '            guard let object = (try? context.existingObject(with: objectID)) as? PastoListEntity else { '
  'return nil }\n'
  '            return ClipboardListTarget(object: object)\n'
  '        }',
  1],
 ['replica/Sources/PastoCore/ClipboardSearchCollection.swift',
  'ListSnapshot(identifiers: subject.value.identifiers, context: context)',
  'ListSnapshot(identifiers: subject.value.identifiers, updatedIdentifiers: '
  'subject.value.updatedIdentifiers, context: context)',
  1],
 ['replica/Sources/PastoCore/ClipboardSearchCollection.swift',
  'ListSnapshot(identifiers: snapshot.identifiers, context: context)',
  'ListSnapshot(identifiers: snapshot.identifiers, updatedIdentifiers: snapshot.updatedIdentifiers, context: '
  'context)',
  1],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    private var selectedTabList: ClipboardListTarget?',
  '    @Published private(set) var selectedTabList: ClipboardListTarget?\n'
  '    var tabListPublisher: AnyPublisher<ClipboardPinboardCollection.ListSnapshot, Never> { '
  'tabListCollection.listPublisher }',
  1],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  '}), searchField: searchField, tabs: boardTabs,',
  '}), searchField: searchField, tabConfiguration: boardTab,',
  1],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  '    private var boardTabs: [OriginalPinboardTab] {\n'
  '        state.tabListTargets.map { target in\n'
  '            let board = target.pinboardValue\n'
  '            var tab = boardButton(target.name, board: board, target: target)\n'
  '            tab.target = target\n'
  '            tab.menuProvider = { localListMenu(for: target) }\n'
  '            tab.dragString = "paste-pinboard:" + target.identifier\n'
  '            tab.onDropString = { value in\n'
  '                guard value.hasPrefix("paste-pinboard:") else { return false }\n'
  '                return state.moveList(identifier: String(value.dropFirst(15)), to: target)\n'
  '            }\n'
  '            return tab\n'
  '        }\n'
  '    }',
  '    private func boardTab(_ target: ClipboardListTarget) -> OriginalPinboardTab {\n'
  '        let board = target.pinboardValue\n'
  '        var tab = boardButton(target.name, board: board, target: target)\n'
  '        tab.target = target\n'
  '        tab.menuProvider = { localListMenu(for: target) }\n'
  '        tab.dragString = "paste-pinboard:" + target.identifier\n'
  '        tab.onDropString = { value in\n'
  '            guard value.hasPrefix("paste-pinboard:") else { return false }\n'
  '            return state.moveList(identifier: String(value.dropFirst(15)), to: target)\n'
  '        }\n'
  '        return tab\n'
  '    }',
  1],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  'isSelected: state.selectedListIdentifier == target.identifier && !state.showDeleted,',
  'isSelected: state.selectedTabList?.hasSameObjectID(as: target) == true && !state.showDeleted,',
  1],
 ['replica/Sources/Pasto/UI/OriginalPanelToolbar.swift',
  '    let tabs: [OriginalPinboardTab]',
  '    let tabConfiguration: (ClipboardListTarget) -> OriginalPinboardTab',
  1],
 ['replica/Sources/Pasto/UI/OriginalPanelToolbar.swift',
  '        state.toolbarOwner = view\n        updateNSView(view, context: context)',
  '        state.toolbarOwner = view\n'
  '        view.observeLists(state.tabListPublisher, configuration: tabConfiguration,\n'
  '            selection: state.$selectedTabList.compactMap { $0 }.eraseToAnyPublisher(),\n'
  '            currentSelection: { [weak state = state] in state?.selectedTabList })\n'
  '        updateNSView(view, context: context)',
  1],
 ['replica/Sources/Pasto/UI/OriginalPanelToolbar.swift',
  '        view.configure(searchButton: searchButton, searchField: searchField,\n'
  '                       tabs: tabs,',
  '        view.updateTabConfiguration(tabConfiguration)\n'
  '        view.configure(searchButton: searchButton, searchField: searchField,',
  1],
 ['replica/Sources/Pasto/UI/OriginalPanelToolbar.swift',
  '        view.stopObservingListEditing()',
  '        view.stopObservingListEditing()\n        view.stopObservingLists()',
  1],
 ['replica/Sources/Pasto/UI/OriginalPanelToolbar.swift',
  'func configure(searchButton: AnyView, searchField: ReplicaSearchEditor, tabs: [OriginalPinboardTab],',
  'func configure(searchButton: AnyView, searchField: ReplicaSearchEditor,',
  1],
 ['replica/Sources/Pasto/UI/OriginalPanelToolbar.swift',
  '        searchBar.configure(button: searchButton, field: searchField)\n        tabBar.configure(tabs)\n',
  '        searchBar.configure(button: searchButton, field: searchField)\n',
  1],
 ['replica/Sources/Pasto/UI/OriginalPanelToolbar.swift',
  '    func observeListEditing(_ publisher: AnyPublisher<ClipboardListTarget, Never>) {',
  '    func observeLists(_ publisher: AnyPublisher<ClipboardPinboardCollection.ListSnapshot, Never>,\n'
  '                      configuration: @escaping (ClipboardListTarget) -> OriginalPinboardTab,\n'
  '                      selection: AnyPublisher<ClipboardListTarget, Never>,\n'
  '                      currentSelection: @escaping () -> ClipboardListTarget?) {\n'
  '        tabBar.observeLists(publisher, configuration: configuration,\n'
  '                            selection: selection, currentSelection: currentSelection)\n'
  '    }\n'
  '\n'
  '    func updateTabConfiguration(_ configuration: @escaping (ClipboardListTarget) -> OriginalPinboardTab) '
  '{\n'
  '        tabBar.updateConfiguration(configuration)\n'
  '    }\n'
  '\n'
  '    func stopObservingLists() { tabBar.stopObservingLists() }\n'
  '\n'
  '    func observeListEditing(_ publisher: AnyPublisher<ClipboardListTarget, Never>) {',
  1],
 ['replica/Sources/Pasto/UI/OriginalPinboardTabTitle.swift',
  '    private var iconSize: CGFloat { iconColor == nil ? 15 : 12 }',
  '    func setSelected(_ selected: Bool) {\n'
  '        isSelected = selected\n'
  '        setAccessibilityValue(selected)\n'
  '        needsDisplay = true\n'
  '    }\n'
  '\n'
  '    private var iconSize: CGFloat { iconColor == nil ? 15 : 12 }',
  1],
 ['replica/Sources/Pasto/UI/OriginalPanelTabBar.swift',
  'import AppKit\nimport PastoCore',
  'import AppKit\nimport Combine\nimport CoreData\nimport PastoCore',
  1],
 ['replica/Sources/Pasto/UI/OriginalPanelTabBar.swift',
  '/// The same native cells remain in the stack for expanded and collapsed states.',
  '/// Native List snapshots drive the original full/incremental tab renderer.',
  1],
 ['replica/Sources/Pasto/UI/OriginalPanelTabBar.swift',
  '    private var cells: [String: OriginalPinboardTabView] = [:]\n'
  '    private var keys: [String] = []\n'
  '    private var isCollapsed = false\n'
  '    private var pendingTabs: [OriginalPinboardTab]?',
  '    private var keys: [NSManagedObjectID] = []\n'
  '    private var isCollapsed = false\n'
  '    private var collectionSnapshot: ClipboardPinboardCollection.ListSnapshot?\n'
  '    private var pendingSnapshot: (value: ClipboardPinboardCollection.ListSnapshot, updated: '
  'Set<NSManagedObjectID>)?\n'
  '    private var listObservation: AnyCancellable?\n'
  '    private var selectionObservation: AnyCancellable?\n'
  '    private var configuration: ((ClipboardListTarget) -> OriginalPinboardTab)?\n'
  '    private var currentSelection: (() -> ClipboardListTarget?)?',
  1],
 ['replica/Sources/Pasto/UI/OriginalPanelTabBar.swift',
  '    func configure(_ tabs: [OriginalPinboardTab]) {\n'
  '        // 1b912c keeps the latest snapshot; each tab here carries its full configuration.\n'
  '        pendingTabs = tabs\n'
  '        scheduleSnapshotDrain()\n'
  '        // 096430 forces the initial applier delivery after installing its subscription.\n'
  '        if !hasAppliedSnapshot { drainSnapshots() }\n'
  '    }',
  '    func observeLists(_ publisher: AnyPublisher<ClipboardPinboardCollection.ListSnapshot, Never>,\n'
  '                      configuration: @escaping (ClipboardListTarget) -> OriginalPinboardTab,\n'
  '                      selection: AnyPublisher<ClipboardListTarget, Never>,\n'
  '                      currentSelection: @escaping () -> ClipboardListTarget?) {\n'
  '        self.configuration = configuration\n'
  '        self.currentSelection = currentSelection\n'
  '        listObservation = publisher.sink { [weak self] snapshot in\n'
  '            MainActor.assumeIsolated { self?.receive(snapshot) }\n'
  '        }\n'
  '        // 096430 subscribes, forces the initial applier flush, then subscribes to selected List.\n'
  '        drainSnapshots()\n'
  '        selectionObservation = selection.sink { [weak self] target in\n'
  '            MainActor.assumeIsolated { self?.selectList(target) }\n'
  '        }\n'
  '    }\n'
  '\n'
  '    func updateConfiguration(_ configuration: @escaping (ClipboardListTarget) -> OriginalPinboardTab) {\n'
  '        self.configuration = configuration\n'
  '    }\n'
  '\n'
  '    func stopObservingLists() {\n'
  '        listObservation?.cancel()\n'
  '        selectionObservation?.cancel()\n'
  '        listObservation = nil\n'
  '        selectionObservation = nil\n'
  '        pendingSnapshot = nil\n'
  '        collectionSnapshot = nil\n'
  '        configuration = nil\n'
  '        currentSelection = nil\n'
  '    }\n'
  '\n'
  '    private func receive(_ snapshot: ClipboardPinboardCollection.ListSnapshot) {\n'
  '        collectionSnapshot = snapshot\n'
  '        // 1b912c/1b59e4 replace IDs and union pending changed IDs before scheduling.\n'
  '        pendingSnapshot = (snapshot, (pendingSnapshot?.updated ?? '
  '[]).union(snapshot.updatedIdentifiers))\n'
  '        scheduleSnapshotDrain()\n'
  '    }',
  1],
 ['replica/Sources/Pasto/UI/OriginalPanelTabBar.swift',
  '        while !isPerformingLocalMutation, let tabs = pendingTabs {\n'
  '            pendingTabs = nil\n'
  '            hasAppliedSnapshot = true\n'
  '            applyTabs(tabs)\n'
  '        }',
  '        while !isPerformingLocalMutation, let pending = pendingSnapshot {\n'
  '            pendingSnapshot = nil\n'
  '            applySnapshot(pending.value, updated: pending.updated)\n'
  '        }',
  1],
 ['replica/Sources/Pasto/UI/OriginalPanelTabBar.swift',
  '    private func applyTabs(_ tabs: [OriginalPinboardTab]) {\n'
  '        let newKeys = tabs.map(\\.key)\n'
  '        let previousKeys = keys\n'
  '        // 097eb0 invokes the applier array setter before configuring any native cell.\n'
  '        keys = newKeys\n'
  '        let retainedKeys = Set(newKeys)\n'
  '        for key in previousKeys where !retainedKeys.contains(key) {\n'
  '            cells[key]?.removeFromSuperview()\n'
  '            cells.removeValue(forKey: key)\n'
  '        }\n'
  '        for tab in tabs {\n'
  '            let cell = cells[tab.key] ?? OriginalPinboardTabView()\n'
  '            cells[tab.key] = cell\n'
  '            tab.configure(cell)\n'
  '            cell.setCollapsed(isCollapsed)\n'
  '        }\n'
  '        if previousKeys != newKeys {\n'
  '            stack.setViews(newKeys.compactMap { cells[$0] }, in: .leading)\n'
  '        }\n'
  '        invalidateIntrinsicContentSize()\n'
  '        needsLayout = true\n'
  '    }\n'
  '\n',
  '    private func applySnapshot(_ snapshot: ClipboardPinboardCollection.ListSnapshot,\n'
  '                               updated: Set<NSManagedObjectID>) {\n'
  '        let newKeys = snapshot.identifiers\n'
  '        let difference = newKeys.difference(from: keys).inferringMoves()\n'
  '        var removals: Set<Int> = []\n'
  '        var insertions: Set<Int> = []\n'
  '        var moveSources: Set<Int> = []\n'
  '        for change in difference {\n'
  '            switch change {\n'
  '            case let .remove(offset, _, associatedWith):\n'
  '                if associatedWith == nil { removals.insert(offset) }\n'
  '                else { moveSources.insert(offset) }\n'
  '            case let .insert(offset, _, associatedWith):\n'
  '                if associatedWith == nil { insertions.insert(offset) }\n'
  '            }\n'
  '        }\n'
  '        // 1b5a8c enumerates OLD IDs; deletions and moved source offsets exclude updates.\n'
  '        let updates = keys.indices.filter {\n'
  '            updated.contains(keys[$0]) && !removals.contains($0) && !moveSources.contains($0)\n'
  '        }\n'
  '        let initial = !hasAppliedSnapshot\n'
  '        if !initial, removals.isEmpty, insertions.isEmpty, moveSources.isEmpty, updates.isEmpty { return '
  '}\n'
  '        hasAppliedSnapshot = true\n'
  '        let fullReload = initial || removals.count + insertions.count + moveSources.count > '
  'OriginalCollectionSnapshot.fullReloadThreshold\n'
  '        // 097eb0 invokes the applier setter before either rendering branch.\n'
  '        keys = newKeys\n'
  '        if fullReload || !moveSources.isEmpty {\n'
  '            rebuildCells()\n'
  '            layoutSubtreeIfNeeded()\n'
  '            return\n'
  '        }\n'
  '        // 097eb0 deletes descending, inserts ascending, then reconfigures every current cell.\n'
  '        for index in removals.sorted(by: >) {\n'
  '            if let removed = cell(at: index) {\n'
  '                removed.removeFromSuperview()\n'
  '                if removed.isSelected, let selected = currentSelection?() { selectList(selected) }\n'
  '            }\n'
  '        }\n'
  '        for index in insertions.sorted() {\n'
  '            let inserted = OriginalPinboardTabView()\n'
  '            stack.insertArrangedSubview(inserted, at: index)\n'
  '            inserted.layoutSubtreeIfNeeded()\n'
  '            configureCell(at: index)\n'
  '        }\n'
  '        for index in keys.indices { configureCell(at: index) }\n'
  '        invalidateIntrinsicContentSize()\n'
  '        needsLayout = true\n'
  '        OriginalViewAnimation.f_10021cadc(duration: nil,\n'
  '            timingFunction: OriginalViewAnimation.f_10021ccd4(), animated: true,\n'
  '            animations: { self.superview?.layoutSubtreeIfNeeded() })\n'
  '    }\n'
  '\n'
  '    private func cell(at index: Int) -> OriginalPinboardTabView? {\n'
  '        let views = stack.arrangedSubviews\n'
  '        guard views.indices.contains(index) else { return nil }\n'
  '        return views[index] as? OriginalPinboardTabView\n'
  '    }\n'
  '\n'
  '    private func configureCell(at index: Int) {\n'
  '        guard keys.indices.contains(index),\n'
  '              let target = collectionSnapshot?.target(for: keys[index]),\n'
  '              let view = cell(at: index), let configuration else { return }\n'
  '        configuration(target).configure(view)\n'
  '        view.setCollapsed(isCollapsed)\n'
  '    }\n'
  '\n'
  '    private func rebuildCells() {\n'
  '        for view in stack.arrangedSubviews { view.removeFromSuperview() }\n'
  '        for index in keys.indices {\n'
  '            let view = OriginalPinboardTabView()\n'
  '            stack.insertArrangedSubview(view, at: index)\n'
  '            view.layoutSubtreeIfNeeded()\n'
  '            configureCell(at: index)\n'
  '        }\n'
  '        invalidateIntrinsicContentSize()\n'
  '        needsLayout = true\n'
  '    }\n'
  '\n'
  '    private func selectList(_ target: ClipboardListTarget) {\n'
  '        // 099218 clears all cells before resolving the same native object ID in the applier.\n'
  '        for view in stack.arrangedSubviews.compactMap({ $0 as? OriginalPinboardTabView }) {\n'
  '            view.setSelected(false)\n'
  '        }\n'
  '        guard let index = keys.firstIndex(of: target.objectID), let view = cell(at: index) else { return '
  '}\n'
  '        view.setSelected(true)\n'
  '        f_100095ae8(view)\n'
  '    }\n'
  '\n',
  1],
 ['replica/Sources/Pasto/UI/OriginalPanelTabBar.swift',
  '        guard let sourceIndex = keys.firstIndex(where: { cells[$0]?.listTarget?.hasSameObjectID(as: '
  'source) == true }),\n'
  '              let destinationIndex = keys.firstIndex(where: { cells[$0]?.listTarget?.hasSameObjectID(as: '
  'target) == true }) else { return false }',
  '        guard let sourceIndex = keys.firstIndex(of: source.objectID),\n'
  '              let destinationIndex = keys.firstIndex(of: target.objectID) else { return false }',
  1],
 ['replica/Sources/Pasto/UI/OriginalPanelTabBar.swift',
  '        // 0973d8 rebuilds/layouts after 1b91e4 unlocks; retain the existing stack renderer adapter.\n'
  '        stack.setViews(keys.compactMap { cells[$0] }, in: .leading)\n'
  '        invalidateIntrinsicContentSize()\n'
  '        needsLayout = true\n'
  '        layoutSubtreeIfNeeded()\n'
  '        if let cell = cells[keys[destinationIndex]], cell.isSelected {',
  '        // 0973d8 recreates cells from the moved applier and reads current model selection in '
  'configuration.\n'
  '        rebuildCells()\n'
  '        layoutSubtreeIfNeeded()\n'
  '        if let cell = cell(at: destinationIndex), cell.isSelected {',
  1],
 ['replica/Sources/Pasto/UI/OriginalPanelTabBar.swift',
  '        guard let cell = keys.compactMap({ cells[$0] }).first(where: {\n'
  '            $0.listTarget?.hasSameObjectID(as: target) == true\n'
  '        }) else { return }',
  '        guard let index = keys.firstIndex(of: target.objectID), let cell = cell(at: index) else { return '
  '}',
  1],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    private var tabListSnapshot: ClipboardPinboardCollection.ListSnapshot?\n'
  '    @Published private(set) var tabListTargets: [ClipboardListTarget] = []',
  '    private var tabListSnapshot: ClipboardPinboardCollection.ListSnapshot?',
  1],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '        tabListSnapshot = snapshot\n        tabListTargets = snapshot.targets',
  '        tabListSnapshot = snapshot',
  1],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '                self.tabListSnapshot = snapshot\n                self.tabListTargets = snapshot.targets',
  '                self.tabListSnapshot = snapshot',
  1],
 ['replica/Sources/Pasto/UI/OriginalPinboardTabTitle.swift',
  'struct OriginalPinboardTab {\n    let key: String',
  'struct OriginalPinboardTab {',
  1],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  '        let key = target.identifier\n        return OriginalPinboardTab(key: key, title: name,',
  '        return OriginalPinboardTab(title: name,',
  1],
 ['replica/Sources/Pasto/UI/OriginalPinboardTabTitle.swift',
  '    var onDropString: ((String) -> Bool)?\n'
  '    var target: ClipboardListTarget? = nil\n'
  '\n'
  '    func configure(_ view: OriginalPinboardTabView) {',
  '    var onDropString: ((String) -> Bool)?\n\n    func configure(_ view: OriginalPinboardTabView) {',
  1],
 ['replica/Sources/Pasto/UI/OriginalPinboardTabTitle.swift',
  '        view.listTarget = target\n        view.menuProvider = menuProvider',
  '        view.menuProvider = menuProvider',
  1],
 ['replica/Sources/Pasto/UI/OriginalPinboardTabTitle.swift',
  '    var listTarget: ClipboardListTarget?\n    private var isDragging = false',
  '    private var isDragging = false',
  1],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  '        tab.target = target\n        tab.menuProvider = { localListMenu(for: target) }',
  '        tab.menuProvider = { localListMenu(for: target) }',
  1]]

def pre_native_tab_source_renderer(source):
    from native_item_drop_scope_contract import pre_native_item_drop
    source = pre_native_item_drop(source)
    import re
    def pattern(text):
        return re.compile((r"(?m)^" if text[:1] in (" ", "\t") else "") + re.escape(text))
    for _,old,new,count in reversed(CHANGES):
        if new in old and pattern(old).search(source):
            continue
        matches = list(pattern(new).finditer(source)) if new else []
        if matches:
            assert len(matches)==count
            source=pattern(new).sub(lambda _: old,source)
    return source


def pre_native_tab_source_renderer_bytes(path):
    data=path.read_bytes()
    return pre_native_tab_source_renderer(data.decode()).encode() if path.suffix=='.swift' else data
