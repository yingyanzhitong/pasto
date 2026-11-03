"""Reverse only reviewed165 native same-object name/color writes and compatibility projection."""
CHANGES = [['replica/Sources/PastoCore/ClipboardListPersistence.swift',
  'private var createdPinboards: [String: PastoListEntity] = [:]',
  'private var nativeLists: [String: NSManagedObject] = [:]',
  1],
 ['replica/Sources/PastoCore/ClipboardListPersistence.swift',
  'createdPinboards[identifier] = list',
  'nativeLists[identifier] = list',
  1],
 ['replica/Sources/PastoCore/ClipboardListPersistence.swift',
  '            set(board.name, key: "name", on: list)\n'
  '            set(Int64(board.rawType ?? 2), key: "rawType", on: list)\n'
  '            set(board.rawAttributes, key: "rawAttributes", on: list)\n'
  '            // A newly created native List supplies metadata/index in validateForInsert, not '
  'this value adapter.\n'
  '            if createdPinboards[identifier] === list { continue }',
  '            // Native operations already changed this exact List; do not replay fields from a '
  'value snapshot.\n'
  '            if nativeLists[identifier] === list { continue }\n'
  '            set(board.name, key: "name", on: list)\n'
  '            set(Int64(board.rawType ?? 2), key: "rawType", on: list)\n'
  '            set(board.rawAttributes, key: "rawAttributes", on: list)',
  1],
 ['replica/Sources/PastoCore/ClipboardListPersistence.swift',
  'projectCreatedPinboards',
  'projectNativePinboards',
  1],
 ['replica/Sources/PastoCore/ClipboardListPersistence.swift',
  'createdPinboards.isEmpty',
  'nativeLists.isEmpty',
  1],
 ['replica/Sources/PastoCore/ClipboardListPersistence.swift',
  'createdPinboards[board.id.uuidString]',
  'nativeLists[board.id.uuidString]',
  1],
 ['replica/Sources/PastoCore/ClipboardListPersistence.swift',
  '// Saving has already run the List validator. Project only its created objects, without another '
  'fetch/save.',
  '// Saving has already run the List validator. Project native input objects without another '
  'fetch/save.',
  1],
 ['replica/Sources/PastoCore/ClipboardListPersistence.swift',
  '    // 0x100368560: insert/name first, attempt permanent ID, then encode attributes and set '
  'type.',
  '    func retainNativeList(_ list: NSManagedObject) {\n'
  '        let identifier = String._unconditionallyBridgeFromObjectiveC(list.value(forKey: '
  '"identifier") as? NSString)\n'
  '        nativeLists[identifier] = list\n'
  '    }\n'
  '\n'
  '    // 36c448: the callback edits the first read; compare against a fresh second read before '
  'setting.\n'
  '    func updateName(on list: NSManagedObject, _ update: (inout String) -> Void) {\n'
  '        var value = String._unconditionallyBridgeFromObjectiveC(list.value(forKey: "name") as? '
  'NSString)\n'
  '        update(&value)\n'
  '        let current = String._unconditionallyBridgeFromObjectiveC(list.value(forKey: "name") '
  'as? NSString)\n'
  '        if current != value { list.setValue(value, forKey: "name") }\n'
  '    }\n'
  '\n'
  '    // 36c614: only a decoded pinboard case is editable; encode failure still writes nil '
  'attributes.\n'
  '    func updateColor(on list: NSManagedObject, _ update: (inout UInt64) -> Void) {\n'
  '        guard case let .pinboard(old)? = OriginalPinboardAttributes.decoded(\n'
  '            from: list.value(forKey: "rawAttributes") as? Data) else { return }\n'
  '        var value = old\n'
  '        update(&value)\n'
  '        guard old != value else { return }\n'
  '        let attributes = try? OriginalPinboardAttributes.encoded(colorCode: value)\n'
  '        list.setValue(attributes, forKey: "rawAttributes")\n'
  '    }\n'
  '\n'
  '    // 0x100368560: insert/name first, attempt permanent ID, then encode attributes and set '
  'type.',
  1],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
  'transaction.repository.lists.projectCreatedPinboards',
  'transaction.repository.lists.projectNativePinboards',
  1],
 ['replica/Sources/PastoCore/ClipboardStore.swift',
  '    public func renamePinboard(id: UUID, name: String) throws {',
  '    public func renameList(_ target: ClipboardListTarget, rawName: String) throws {\n'
  '        try mutateInTransaction { state, transaction in\n'
  '            let lists = transaction.repository.lists\n'
  '            lists.retainNativeList(target.nativeObject)\n'
  '            lists.updateName(on: target.nativeObject) { $0 = '
  'OriginalPinboardTitle.normalizedRename(rawName) }\n'
  '            projectNativeList(target, into: &state)\n'
  '        }\n'
  '    }\n'
  '\n'
  '    public func updateListColor(_ target: ClipboardListTarget, colorCode: UInt64) throws {\n'
  '        try mutateInTransaction { state, transaction in\n'
  '            let lists = transaction.repository.lists\n'
  '            lists.retainNativeList(target.nativeObject)\n'
  '            lists.updateColor(on: target.nativeObject) { $0 = colorCode }\n'
  '            projectNativeList(target, into: &state)\n'
  '        }\n'
  '    }\n'
  '\n'
  '    private func projectNativeList(_ target: ClipboardListTarget, into state: inout StoreState) '
  '{\n'
  '        if target.identifier == Self.historyListIdentifier {\n'
  '            state.preferences.historyTitle = target.name\n'
  '            return\n'
  '        }\n'
  '        guard let id = UUID(uuidString: target.identifier) else { return }\n'
  '        guard let index = state.pinboards.firstIndex(where: { $0.id == id }) else {\n'
  '            if let board = target.pinboardValue { state.pinboards.append(board) }\n'
  '            return\n'
  '        }\n'
  '        state.pinboards[index].name = target.name\n'
  '        state.pinboards[index].rawType = Int16(exactly: target.rawType) ?? 0\n'
  '        let attributes = target.nativeObject.value(forKey: "rawAttributes") as? Data\n'
  '        if state.pinboards[index].rawAttributes != attributes {\n'
  '            state.pinboards[index].rawAttributes = attributes\n'
  '            if let color = OriginalPinboardAttributes.colorCode(from: attributes) {\n'
  '                state.pinboards[index].colorHex = String(format: "#%06llX", color)\n'
  '            }\n'
  '        }\n'
  '        if let metadata = target.nativeObject.value(forKey: "metadata") as? NSManagedObject,\n'
  '           let order = metadata.value(forKey: "index") as? NSNumber { '
  'state.pinboards[index].sortOrder = order.intValue }\n'
  '    }\n'
  '\n'
  '    public func renamePinboard(id: UUID, name: String) throws {',
  1],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  'tab.menuProvider = { localListMenu(for: board) }',
  'tab.menuProvider = { localListMenu(for: board, target: target) }',
  1],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  'private func localListMenu(for board: Pinboard?) -> NSMenu',
  'private func localListMenu(for board: Pinboard?, target: ClipboardListTarget) -> NSMenu',
  1],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  '                let item = OriginalPanelTabMenuItem(title: colorName(color)) {\n'
  '                    state.perform {\n'
  '                        try state.store.updatePinboard(id: board.id,\n'
  '                            colorHex: String(format: "%06llX", color.canonicalColorCode))\n'
  '                    }\n'
  '                }',
  '                let item = OriginalPanelTabMenuItem(title: colorName(color)) { [weak menu] in\n'
  '                    try? state.store.updateListColor(target, colorCode: '
  'color.canonicalColorCode)\n'
  '                    menu?.cancelTracking()\n'
  '                }',
  1],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  '{ value in\n'
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
  '                }',
  '{\n'
  '                    try? state.store.renameList(target, rawName: value)\n'
  '                    return target.name\n'
  '                }',
  1],
 ['replica/Sources/PastoCore/ClipboardListPersistence.swift',
  '{\n'
  '        guard let list = try? list(identifier: identifier) else { return (nil, true) }\n'
  '        let rawType = (list.value(forKey: "rawType") as? NSNumber)?.int64Value ?? 0\n'
  '        guard let context = list.managedObjectContext else { return (rawType, true) }\n'
  '        let request = PastoItemEntity.defaultFetchRequest()\n'
  '        switch rawType {\n'
  '        case 1: request.predicate = NSPredicate(format: "timestamp != nil")\n'
  '        case 2: request.predicate = NSPredicate(format: "list == %@", list)\n'
  '        default: return (rawType, true)\n'
  '        }\n'
  '        let count = (try? context.count(for: request)) ?? 0\n'
  '        return (rawType, count == 0)\n'
  '    }',
  '{\n'
  '        guard let list = try? list(identifier: identifier) else { return (nil, true) }\n'
  '        return menuState(for: list)\n'
  '    }\n'
  '\n'
  '    func menuState(for list: NSManagedObject) -> (rawType: Int64?, isEmpty: Bool) {\n'
  '        let rawType = (list.value(forKey: "rawType") as? NSNumber)?.int64Value ?? 0\n'
  '        guard let context = list.managedObjectContext else { return (rawType, true) }\n'
  '        let request = PastoItemEntity.defaultFetchRequest()\n'
  '        switch rawType {\n'
  '        case 1: request.predicate = NSPredicate(format: "timestamp != nil")\n'
  '        case 2: request.predicate = NSPredicate(format: "list == %@", list)\n'
  '        default: return (rawType, true)\n'
  '        }\n'
  '        let count = (try? context.count(for: request)) ?? 0\n'
  '        return (rawType, count == 0)\n'
  '    }',
  1],
 ['replica/Sources/PastoCore/ClipboardListPersistence.swift',
  '    public var rawType: Int64 { (nativeObject.value(forKey: "rawType") as? '
  'NSNumber)?.int64Value ?? 0 }',
  '    public var colorCode: UInt64? {\n'
  '        OriginalPinboardAttributes.colorCode(from: nativeObject.value(forKey: "rawAttributes") '
  'as? Data)\n'
  '    }\n'
  '    public var rawType: Int64 { (nativeObject.value(forKey: "rawType") as? '
  'NSNumber)?.int64Value ?? 0 }',
  1],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
  '    func localListMenuState(identifier: String) -> (rawType: Int64?, isEmpty: Bool) {',
  '    func localListMenuState(_ target: ClipboardListTarget) -> (rawType: Int64?, isEmpty: Bool) '
  '{\n'
  '        context.performAndWait { lists.menuState(for: target.nativeObject) }\n'
  '    }\n'
  '\n'
  '    func localListMenuState(identifier: String) -> (rawType: Int64?, isEmpty: Bool) {',
  1],
 ['replica/Sources/PastoCore/ClipboardStore.swift',
  '    public func makeTabListCollection() -> ClipboardPinboardCollection {',
  '    public func localListMenuState(_ target: ClipboardListTarget) -> (rawType: Int64?, isEmpty: '
  'Bool) {\n'
  '        persistence.localListMenuState(target)\n'
  '    }\n'
  '    public func makeTabListCollection() -> ClipboardPinboardCollection {',
  1],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  'menu.addItem(OriginalPanelTabMenuItem(title: "重命名") { requestTabRename(board?.id) })',
  'menu.addItem(OriginalPanelTabMenuItem(title: "重命名") { requestTabRename(target.identifier) })',
  1],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  'let list = state.store.localListMenuState(pinboardID: board?.id)',
  'let list = state.store.localListMenuState(target)',
  1],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  '        } else if list.rawType == 2, let board {\n'
  '            menu.addItem(OriginalPanelTabMenuItem(title: list.isEmpty ? "删除" : "删除…") {\n'
  '                state.controller?.removePinboard(board)\n'
  '            })',
  '        } else if list.rawType == 2 {\n'
  '            if let board {\n'
  '                menu.addItem(OriginalPanelTabMenuItem(title: list.isEmpty ? "删除" : "删除…") {\n'
  '                    state.controller?.removePinboard(board)\n'
  '                })\n'
  '            }',
  1],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  '            let selectedColor = OriginalPinboardAttributes.colorCode(from: '
  'board.rawAttributes)\n'
  '                .map { OriginalPinboardColor(canonicalColorCode: $0) }',
  '            let selectedColor = target.colorCode.map { '
  'OriginalPinboardColor(canonicalColorCode: $0) }',
  1],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  '    private func requestTabRename(_ id: UUID?) {\n'
  '        state.tabRenameRequest = (key: id?.uuidString ?? ClipboardStore.historyListIdentifier, '
  'token: UUID())\n'
  '    }',
  '    private func requestTabRename(_ identifier: String) {\n'
  '        state.tabRenameRequest = (key: identifier, token: UUID())\n'
  '    }',
  1],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  'onCommit: {\n                    try? state.store.renameList(target, rawName: value)',
  'onCommit: { value in\n                    try? state.store.renameList(target, rawName: value)',
  1]]

def pre_native_list_name_color(source):
    from native_list_deletion_scope_contract import pre_native_list_deletion
    source = pre_native_list_deletion(source)
    for _,old,new,count in reversed(CHANGES):
        if new in source:
            assert source.count(new)==count
            source=source.replace(new,old)
    return source

def pre_native_list_name_color_bytes(path):
    data=path.read_bytes()
    return pre_native_list_name_color(data.decode()).encode()if path.suffix=='.swift'else data
