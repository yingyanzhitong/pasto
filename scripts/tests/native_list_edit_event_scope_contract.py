"""Reverse only reviewed168 native List editing-event producer/subscriber/consumer changes."""
CHANGES = [['replica/Sources/PastoCore/ClipboardListPersistence.swift',
  'public struct ClipboardPinboardTarget {\n    public let id: UUID',
  'public struct ClipboardPinboardTarget {\n'
  '    public let id: UUID\n'
  '    public var listTarget: ClipboardListTarget { ClipboardListTarget(object: nativeObject) }',
  1],
 ['replica/Sources/PastoCore/ClipboardListPersistence.swift',
  '    public var isDeleted: Bool { nativeObject.isDeleted }',
  '    public var isDeleted: Bool { nativeObject.isDeleted }\n'
  '    public func hasSameObjectID(as other: ClipboardListTarget) -> Bool {\n'
  '        nativeObject.objectID.isEqual(other.nativeObject.objectID)\n'
  '    }',
  1],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    @Published var tabRenameRequest: (key: String, token: UUID)?',
  '    let beginEditingListSubject = PassthroughSubject<ClipboardListTarget, Never>()',
  1],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '            // 0x100039618 → 0x10003b4c0: create first, then request inline editing.\n'
  '            DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) { [weak self] in\n'
  '                guard let self, self.store.pinboards.contains(where: { $0.id == board.id }) '
  'else { return }\n'
  '                self.state.tabRenameRequest = (board.id.uuidString, UUID())\n'
  '            }',
  '            // 039618/03b4c0: retain the created List across the delay; only the owner is '
  'weak.\n'
  '            let target = board.listTarget\n'
  '            DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) { [weak self, target] in\n'
  '                self?.state.beginEditingListSubject.send(target)\n'
  '            }',
  1],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  '            tab.menuProvider = { localListMenu(for: target) }',
  '            tab.target = target\n            tab.menuProvider = { localListMenu(for: target) }',
  1],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  'requestTabRename(target.identifier)',
  'requestTabRename(target)',
  1],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  '    private func requestTabRename(_ identifier: String) {\n'
  '        state.tabRenameRequest = (key: identifier, token: UUID())\n'
  '    }',
  '    private func requestTabRename(_ target: ClipboardListTarget) {\n'
  '        state.beginEditingListSubject.send(target)\n'
  '    }',
  1],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  '    private func boardButton(_ name: String, board: Pinboard?, target: ClipboardListTarget) -> '
  'OriginalPinboardTab {\n'
  '        let key = target.identifier\n'
  '        return OriginalPinboardTab(key: key, title: name, iconColor: board.map { '
  'NSColor(boardColor($0)) },\n'
  '                isSelected: state.selectedListIdentifier == target.identifier && '
  '!state.showDeleted,\n'
  '                beginRequest: state.tabRenameRequest?.key == key ? '
  'state.tabRenameRequest?.token : nil,\n'
  '                onSelect: {\n'
  '                    if target.rawType != 2, searching {\n'
  '                        state.query = ""; state.chooseList(identifier: target.identifier); '
  'state.searchVisible = false\n'
  '                        state.controller?.panel.makeFirstResponder(nil)\n'
  '                    } else { state.chooseList(identifier: target.identifier) }\n'
  '                },\n'
  '                onEnd: { if state.tabRenameRequest?.key == key { state.tabRenameRequest = nil } '
  '},\n'
  '                onCommit: { value in\n'
  '                    try? state.store.renameList(target, rawName: value)\n'
  '                    return target.name\n'
  '                })\n'
  '    }',
  '    private func boardButton(_ name: String, board: Pinboard?, target: ClipboardListTarget) -> '
  'OriginalPinboardTab {\n'
  '        let key = target.identifier\n'
  '        return OriginalPinboardTab(key: key, title: name, iconColor: board.map { '
  'NSColor(boardColor($0)) },\n'
  '                isSelected: state.selectedListIdentifier == target.identifier && '
  '!state.showDeleted,\n'
  '                beginRequest: nil,\n'
  '                onSelect: {\n'
  '                    if target.rawType != 2, searching {\n'
  '                        state.query = ""; state.chooseList(identifier: target.identifier); '
  'state.searchVisible = false\n'
  '                        state.controller?.panel.makeFirstResponder(nil)\n'
  '                    } else { state.chooseList(identifier: target.identifier) }\n'
  '                },\n'
  '                onEnd: {},\n'
  '                onCommit: { value in\n'
  '                    try? state.store.renameList(target, rawName: value)\n'
  '                    return target.name\n'
  '                })\n'
  '    }',
  1],
 ['replica/Sources/Pasto/UI/OriginalPinboardTabTitle.swift',
  '    var onDropString: ((String) -> Bool)?\n\n    func configure(_ view:',
  '    var onDropString: ((String) -> Bool)?\n'
  '    var target: ClipboardListTarget? = nil\n'
  '\n'
  '    func configure(_ view:',
  1],
 ['replica/Sources/Pasto/UI/OriginalPinboardTabTitle.swift',
  '        view.menuProvider = menuProvider',
  '        view.listTarget = target\n        view.menuProvider = menuProvider',
  1],
 ['replica/Sources/Pasto/UI/OriginalPinboardTabTitle.swift',
  '    var onDropString: ((String) -> Bool)?\n    private var isDragging',
  '    var onDropString: ((String) -> Bool)?\n'
  '    var listTarget: ClipboardListTarget?\n'
  '    private var isDragging',
  1],
 ['replica/Sources/Pasto/UI/OriginalPinboardTabTitle.swift',
  '    private func beginEditing() {',
  '    func beginEditingFromListRequest() { beginEditing() }\n\n    private func beginEditing() {',
  1],
 ['replica/Sources/Pasto/UI/OriginalPanelToolbar.swift',
  '        view.searchBar.observeQuery(state.searchInputPublisher, initial: '
  'state.searchQueryNodes)',
  '        view.searchBar.observeQuery(state.searchInputPublisher, initial: '
  'state.searchQueryNodes)\n'
  '        view.observeListEditing(state.beginEditingListSubject.eraseToAnyPublisher())',
  1],
 ['replica/Sources/Pasto/UI/OriginalPanelToolbar.swift',
  '        view.searchBar.dismantleEditor()',
  '        view.stopObservingListEditing()\n        view.searchBar.dismantleEditor()',
  1],
 ['replica/Sources/Pasto/UI/OriginalPanelToolbar.swift',
  '    private let tabBar = OriginalPanelTabBar()',
  '    private let tabBar = OriginalPanelTabBar()\n'
  '    private var listEditingObservation: AnyCancellable?',
  1],
 ['replica/Sources/Pasto/UI/OriginalPanelToolbar.swift',
  '    func applySearchQuery(_ nodes: [OriginalSearchQueryNode]) { '
  'searchBar.applySearchQuery(nodes) }',
  '    func observeListEditing(_ publisher: AnyPublisher<ClipboardListTarget, Never>) {\n'
  '        listEditingObservation = publisher.sink { [weak self] target in\n'
  '            MainActor.assumeIsolated { self?.tabBar.beginEditingList(target) }\n'
  '        }\n'
  '    }\n'
  '\n'
  '    func stopObservingListEditing() {\n'
  '        listEditingObservation?.cancel()\n'
  '        listEditingObservation = nil\n'
  '    }\n'
  '\n'
  '    func applySearchQuery(_ nodes: [OriginalSearchQueryNode]) { '
  'searchBar.applySearchQuery(nodes) }',
  1],
 ['replica/Sources/Pasto/UI/OriginalPanelTabBar.swift',
  '    func setCollapsed(_ collapsed: Bool) {',
  '    // 099838: locate the same native object, scroll its cell, then start editing after the '
  'animation.\n'
  '    func beginEditingList(_ target: ClipboardListTarget) {\n'
  '        guard let cell = keys.compactMap({ cells[$0] }).first(where: {\n'
  '            $0.listTarget?.hasSameObjectID(as: target) == true\n'
  '        }) else { return }\n'
  '        window?.makeFirstResponder(nil)\n'
  '        let rect = cell.frame.insetBy(dx: -17, dy: 0)\n'
  '        OriginalViewAnimation.f_10021cadc(duration: 0.15,\n'
  '            timingFunction: OriginalViewAnimation.f_10021ccd4(), animated: true,\n'
  '            animations: { self.f_10009ac24(rect) },\n'
  '            completion: { cell.titleView.beginEditingFromListRequest() })\n'
  '    }\n'
  '\n'
  '    func setCollapsed(_ collapsed: Bool) {',
  1]]

def pre_native_list_edit_event(source):
    from native_tab_applier_scope_contract import pre_native_tab_applier
    source = pre_native_tab_applier(source)
    from test_offline_p0_contracts import body
    for path,old,new,count in CHANGES:
        if path.endswith("PanelViews.swift") and old.startswith("    private func boardButton("):
            if source == body(new, "private func boardButton("):
                return body(old, "private func boardButton(")
    for _,old,new,count in reversed(CHANGES):
        if new and new in source:
            assert source.count(new)==count
            source=source.replace(new,old)
    return source

def pre_native_list_edit_event_bytes(path):
    data=path.read_bytes()
    return pre_native_list_edit_event(data.decode()).encode() if path.suffix=='.swift' else data
