"""Reverse only reviewed164 all-List tab delivery and native selection consumer changes."""
CHANGES = [['replica/Sources/PastoCore/ClipboardListPersistence.swift',
  '/// Access on the supplied context queue. Existing Pasto IDs and legacy memberships stay '
  'compatible.',
  '/// A tab retains its List itself; history and groups share the native ordered collection.\n'
  '@MainActor\n'
  'public struct ClipboardListTarget {\n'
  '    let nativeObject: NSManagedObject\n'
  '    public var identifier: String {\n'
  '        String._unconditionallyBridgeFromObjectiveC(nativeObject.value(forKey: "identifier") '
  'as? NSString)\n'
  '    }\n'
  '    public var name: String {\n'
  '        String._unconditionallyBridgeFromObjectiveC(nativeObject.value(forKey: "name") as? '
  'NSString)\n'
  '    }\n'
  '    public var rawType: Int64 { (nativeObject.value(forKey: "rawType") as? '
  'NSNumber)?.int64Value ?? 0 }\n'
  '    public var pinboardValue: Pinboard? {\n'
  '        guard rawType == 2, let id = UUID(uuidString: identifier) else { return nil }\n'
  '        let attributes = nativeObject.value(forKey: "rawAttributes") as? Data\n'
  '        let color = OriginalPinboardAttributes.colorCode(from: attributes)\n'
  '            .map { String(format: "#%06llX", $0) } ?? "#FF9500"\n'
  '        let metadata = nativeObject.value(forKey: "metadata") as? NSManagedObject\n'
  '        let index = (metadata?.value(forKey: "index") as? NSNumber)?.intValue ?? 0\n'
  '        return Pinboard(id: id, name: name, colorHex: color, sortOrder: index, rawType: 2, '
  'rawAttributes: attributes)\n'
  '    }\n'
  '\n'
  '    init(object: NSManagedObject) { nativeObject = object }\n'
  '}\n'
  '\n'
  '/// Access on the supplied context queue. Existing Pasto IDs and legacy memberships stay '
  'compatible.',
  1],
 ['replica/Sources/PastoCore/ClipboardListPersistence.swift',
  '    // 0x100328bb4 → 0x100328bc8, specialized to the actual local ListEntity consumers.',
  "    // 367f78 does not apply the menu's type2 predicate.\n"
  '    func tabListRequest() -> NSFetchRequest<PastoListEntity> { '
  'PastoListEntity.listFetchRequest() }\n'
  '\n'
  '    // 368080/32a5b0 fetch the matching native List collection and return its first object.\n'
  '    func tabList(identifier: String) -> NSManagedObject? {\n'
  '        let request = PastoListEntity.listFetchRequest()\n'
  '        request.predicate = NSPredicate(format: "identifier == %@", identifier)\n'
  '        return (try? context.fetch(request))?.first\n'
  '    }\n'
  '\n'
  '    // 0x100328bb4 → 0x100328bc8, specialized to the actual local ListEntity consumers.',
  1],
 ['replica/Sources/PastoCore/ClipboardSearchCollection.swift',
  "/// The group menu's lazily owned live ListEntity collection (3b8c94/36c094).",
  '/// Live ListEntity collection: tabs use class defaults (367f78), the menu narrows to type2 '
  '(36c094).',
  1],
 ['replica/Sources/PastoCore/ClipboardSearchCollection.swift',
  "    // 1b85f0 maps the current ordered IDs using the collection's optional native lookup.",
  '    @MainActor public struct ListSnapshot {\n'
  '        private let identifiers: [NSManagedObjectID]\n'
  '        private let context: NSManagedObjectContext\n'
  '        fileprivate init(identifiers: [NSManagedObjectID], context: NSManagedObjectContext) {\n'
  '            self.identifiers = identifiers\n'
  '            self.context = context\n'
  '        }\n'
  '        public var count: Int { identifiers.count }\n'
  '        public var targets: [ClipboardListTarget] { identifiers.indices.compactMap { target(at: '
  '$0) } }\n'
  '        public func index(of target: ClipboardListTarget) -> Int? {\n'
  '            identifiers.firstIndex { $0.isEqual(target.nativeObject.objectID) }\n'
  '        }\n'
  '        public func target(at index: Int) -> ClipboardListTarget? {\n'
  '            guard identifiers.indices.contains(index),\n'
  '                  let object = (try? context.existingObject(with: identifiers[index])) as? '
  'PastoListEntity else { return nil }\n'
  '            return ClipboardListTarget(object: object)\n'
  '        }\n'
  '    }\n'
  '\n'
  '    public var listSnapshot: ListSnapshot { ListSnapshot(identifiers: '
  'subject.value.identifiers, context: context) }\n'
  '    public var listPublisher: AnyPublisher<ListSnapshot, Never> {\n'
  '        subject.map { [self] snapshot in ListSnapshot(identifiers: snapshot.identifiers, '
  'context: context) }\n'
  '            .eraseToAnyPublisher()\n'
  '    }\n'
  '\n'
  "    // 1b85f0 maps the current ordered IDs using the collection's optional native lookup.",
  1],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
  '    func makePinboardCollection() -> ClipboardPinboardCollection {',
  '    func tabListTarget(identifier: String) -> ClipboardListTarget? {\n'
  '        context.performAndWait {\n'
  '            lists.tabList(identifier: identifier).map { ClipboardListTarget(object: $0) }\n'
  '        }\n'
  '    }\n'
  '\n'
  '    func makeTabListCollection() -> ClipboardPinboardCollection {\n'
  '        context.performAndWait {\n'
  '            ClipboardPinboardCollection(context: context, request: lists.tabListRequest())\n'
  '        }\n'
  '    }\n'
  '\n'
  '    func makePinboardCollection() -> ClipboardPinboardCollection {',
  1],
 ['replica/Sources/PastoCore/ClipboardStore.swift',
  '    public func makePinboardCollection() -> ClipboardPinboardCollection {',
  '    public func makeTabListCollection() -> ClipboardPinboardCollection { '
  'persistence.makeTabListCollection() }\n'
  '    public func tabListTarget(identifier: String) -> ClipboardListTarget? { '
  'persistence.tabListTarget(identifier: identifier) }\n'
  '    public func makeListCollection(identifier: String) -> ClipboardSearchCollection? {\n'
  '        persistence.makeListCollection(identifier: identifier)\n'
  '    }\n'
  '    public func makePinboardCollection() -> ClipboardPinboardCollection {',
  1],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    private lazy var pinboardMenuCollection = store.makePinboardCollection()',
  '    private lazy var pinboardMenuCollection = store.makePinboardCollection()\n'
  '    private lazy var tabListCollection = store.makeTabListCollection()\n'
  '    private var tabListObservation: AnyCancellable?\n'
  '    private var tabListSnapshot: ClipboardPinboardCollection.ListSnapshot?\n'
  '    @Published private(set) var tabListTargets: [ClipboardListTarget] = []\n'
  '    private var selectedTabList: ClipboardListTarget?\n'
  '    private var selectedTabIndex: Int?\n'
  '    private var selectedCollectionIdentifier = ClipboardStore.historyListIdentifier\n'
  '    var selectedListIdentifier: String { selectedTabList?.identifier ?? '
  'ClipboardStore.historyListIdentifier }',
  1],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '        installListSelectionDelivery()\n        installSearchQueryDelivery()',
  '        installTabListDelivery()\n'
  '        installListSelectionDelivery()\n'
  '        installSearchQueryDelivery()',
  1],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '        let source = store.makeListCollection(pinboardID: pinboardID)',
  '        let source = store.makeListCollection(identifier: selectedCollectionIdentifier)',
  1],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '        if let pinboardID, !store.pinboards.contains(where: { $0.id == pinboardID }) {\n'
  '            selectListIdentifier(ClipboardStore.historyListIdentifier, force: false)\n'
  '        }\n',
  '        // Native List delivery owns removal and neighboring-list selection.\n',
  1],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    func chooseBoard(_ id: UUID?) {',
  '    private func installTabListDelivery() {\n'
  '        let snapshot = tabListCollection.listSnapshot\n'
  '        tabListSnapshot = snapshot\n'
  '        tabListTargets = snapshot.targets\n'
  '        reconcileTabListSelection()\n'
  '        tabListObservation = tabListCollection.listPublisher.dropFirst().sink { [weak self] '
  'snapshot in\n'
  '            MainActor.assumeIsolated {\n'
  '                guard let self else { return }\n'
  '                self.tabListSnapshot = snapshot\n'
  '                self.tabListTargets = snapshot.targets\n'
  '                self.reconcileTabListSelection()\n'
  '            }\n'
  '        }\n'
  '    }\n'
  '\n'
  '    // 03a538: retain an existing object ID, otherwise clamp the old index into the raw native '
  'order.\n'
  '    private func reconcileTabListSelection() {\n'
  '        guard let selected = selectedTabList, let previousIndex = selectedTabIndex else {\n'
  '            selectListIdentifier(ClipboardStore.historyListIdentifier, force: false)\n'
  '            return\n'
  '        }\n'
  '        guard let snapshot = tabListSnapshot else { return }\n'
  '        if let index = snapshot.index(of: selected) {\n'
  '            selectedTabIndex = index\n'
  '            return\n'
  '        }\n'
  '        let index = min(previousIndex, snapshot.count - 1)\n'
  '        guard let target = snapshot.target(at: index) else { return }\n'
  '        selectListIdentifier(target.identifier, force: false)\n'
  '    }\n'
  '\n'
  '    func chooseList(identifier: String) { selectListIdentifier(identifier, force: true) }\n'
  '\n'
  '    func chooseBoard(_ id: UUID?) {',
  1],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '{\n'
  '        listIdentifierObservation = listIdentifierChanges.sink { [weak self] identifier in\n'
  '            guard let self, let identifier else { return }\n'
  '            let id: UUID?\n'
  '            if identifier == ClipboardStore.historyListIdentifier {\n'
  '                id = nil\n'
  '            } else {\n'
  '                guard let board = self.store.pinboards.first(where: { $0.id.uuidString == '
  'identifier }) else { return }\n'
  '                // Published boards project the managed type; nil is the existing legacy-group '
  'adapter.\n'
  '                let context = OriginalCollectionListContext.f_1003b80f0(identifier: '
  'identifier,\n'
  '                    rawType: Int64(board.rawType ?? 2), historyIdentifier: { '
  'ClipboardStore.historyListIdentifier })\n'
  '                switch context {\n'
  '                case .pinboard: id = board.id\n'
  '                case .history: id = nil\n'
  '                }\n'
  '            }\n'
  '            self.applySelectedList(id)\n'
  '        }\n'
  '    }',
  '{\n'
  '        listIdentifierObservation = listIdentifierChanges.sink { [weak self] identifier in\n'
  '            guard let self, let identifier,\n'
  '                  let target = self.store.tabListTarget(identifier: identifier) else { return '
  '}\n'
  '            let context = OriginalCollectionListContext.f_1003b80f0(identifier: '
  'target.identifier,\n'
  '                rawType: target.rawType, historyIdentifier: { '
  'ClipboardStore.historyListIdentifier })\n'
  '            let id: UUID?\n'
  '            switch context {\n'
  '            case .pinboard(let identifier):\n'
  '                self.selectedCollectionIdentifier = identifier\n'
  '                id = UUID(uuidString: identifier)\n'
  '            case .history(let identifier):\n'
  '                self.selectedCollectionIdentifier = identifier\n'
  '                id = nil\n'
  '            }\n'
  '            self.selectedTabList = target\n'
  '            self.applySelectedList(id)\n'
  '            self.selectedTabIndex = self.tabListSnapshot?.index(of: target)\n'
  '        }\n'
  '    }',
  1],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '{\n'
  '        let ids: [UUID?] = [nil] + store.pinboards.sorted { $0.sortOrder < $1.sortOrder }.map { '
  'Optional($0.id) }\n'
  '        guard let current = ids.firstIndex(where: { $0 == pinboardID }) else { return }\n'
  '        let next: Int\n'
  '        switch offset {\n'
  '        case -1: next = (current - 1 + ids.count) % ids.count\n'
  '        case 1: next = (current + 1) % ids.count\n'
  '        default: return\n'
  '        }\n'
  '        chooseBoard(ids[next])\n'
  '    }',
  '{\n'
  '        guard let snapshot = tabListSnapshot, let selected = selectedTabList,\n'
  '              let current = snapshot.index(of: selected) else { return }\n'
  '        let next: Int\n'
  '        switch offset {\n'
  '        case -1: next = (current - 1 + snapshot.count) % snapshot.count\n'
  '        case 1: next = (current + 1) % snapshot.count\n'
  '        default: return\n'
  '        }\n'
  '        guard let target = snapshot.target(at: next) else { return }\n'
  '        chooseList(identifier: target.identifier)\n'
  '    }',
  1],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  '{\n'
  '        var history = boardButton(state.store.preferences.historyTitle, board: nil)\n'
  '        history.menuProvider = { localListMenu(for: nil) }\n'
  '        var tabs = [history]\n'
  '        for board in state.store.pinboards.sorted(by: { $0.sortOrder < $1.sortOrder }) {\n'
  '            var tab = boardButton(board.name, board: board)\n'
  '            tab.menuProvider = { localListMenu(for: board) }\n'
  '            tab.dragString = "paste-pinboard:" + board.id.uuidString\n'
  '            tab.onDropString = { value in\n'
  '                guard value.hasPrefix("paste-pinboard:"), let id = UUID(uuidString: '
  'String(value.dropFirst(15))) else { return false }\n'
  '                state.movePinboard(id: id, before: board.id)\n'
  '                return true\n'
  '            }\n'
  '            tabs.append(tab)\n'
  '        }\n'
  '        return tabs\n'
  '    }',
  '{\n'
  '        state.tabListTargets.map { target in\n'
  '            let board = target.pinboardValue\n'
  '            var tab = boardButton(target.name, board: board, target: target)\n'
  '            tab.menuProvider = { localListMenu(for: board) }\n'
  '            if let board {\n'
  '                tab.dragString = "paste-pinboard:" + board.id.uuidString\n'
  '                tab.onDropString = { value in\n'
  '                    guard value.hasPrefix("paste-pinboard:"), let id = UUID(uuidString: '
  'String(value.dropFirst(15))) else { return false }\n'
  '                    state.movePinboard(id: id, before: board.id)\n'
  '                    return true\n'
  '                }\n'
  '            }\n'
  '            return tab\n'
  '        }\n'
  '    }',
  1],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  'state.tabRenameRequest = (key: id?.uuidString ?? "history", token: UUID())',
  'state.tabRenameRequest = (key: id?.uuidString ?? ClipboardStore.historyListIdentifier, token: '
  'UUID())',
  1],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  '    private func boardButton(_ name: String, board: Pinboard?) -> OriginalPinboardTab {\n'
  '        let key = board?.id.uuidString ?? "history"\n'
  '        return OriginalPinboardTab(key: key, title: name, iconColor: board.map { '
  'NSColor(boardColor($0)) },\n'
  '                isSelected: state.pinboardID == board?.id && !state.showDeleted,\n'
  '                beginRequest: state.tabRenameRequest?.key == key ? '
  'state.tabRenameRequest?.token : nil,\n'
  '                onSelect: {\n'
  '                    if board?.id == nil, searching {\n'
  '                        state.query = ""; state.chooseBoard(nil); state.searchVisible = false\n'
  '                        state.controller?.panel.makeFirstResponder(nil)\n'
  '                    } else { state.chooseBoard(board?.id) }\n'
  '                },\n'
  '                onEnd: { if state.tabRenameRequest?.key == key { state.tabRenameRequest = nil } '
  '},\n'
  '                onCommit: { value in\n'
  '                    if let board {\n'
  '                        state.perform { try state.store.renamePinboardFromTab(id: board.id, '
  'rawName: value) }\n'
  '                        return state.store.pinboards.first(where: { $0.id == board.id })?.name '
  '?? name\n'
  '                    } else {\n'
  '                        state.store.preferences.historyTitle = '
  'OriginalPinboardTitle.normalizedRename(value)\n'
  '                        state.perform { try state.store.save() }\n'
  '                        return state.store.preferences.historyTitle\n'
  '                    }\n'
  '                })\n'
  '    }',
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
  '                    if let board {\n'
  '                        state.perform { try state.store.renamePinboardFromTab(id: board.id, '
  'rawName: value) }\n'
  '                        return state.store.pinboards.first(where: { $0.id == board.id })?.name '
  '?? name\n'
  '                    } else {\n'
  '                        state.store.preferences.historyTitle = '
  'OriginalPinboardTitle.normalizedRename(value)\n'
  '                        state.perform { try state.store.save() }\n'
  '                        return state.store.preferences.historyTitle\n'
  '                    }\n'
  '                })\n'
  '    }',
  1],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '            if state.pinboardID == id { state.chooseBoard(nil) }',
  '            // The native List snapshot chooses the adjacent surviving list.',
  1]]

def pre_native_tab_list_delivery(source):
    from native_list_name_color_scope_contract import pre_native_list_name_color
    source = pre_native_list_name_color(source)
    for _,old,new,count in reversed(CHANGES):
        if new and new in source:
            assert source.count(new)==count
            source=source.replace(new,old)
    return source

def pre_native_tab_list_delivery_bytes(path):
    data=path.read_bytes()
    return pre_native_tab_list_delivery(data.decode()).encode()if path.suffix=='.swift'else data
