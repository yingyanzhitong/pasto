"""Reverse only reviewed166 native pinboard deletion deltas for historical shape contracts."""
CHANGES = [['replica/Sources/PastoCore/ClipboardListPersistence.swift',
  'public struct ClipboardListTarget {\n    let nativeObject: NSManagedObject',
  'public struct ClipboardListTarget {\n'
  '    let nativeObject: NSManagedObject\n'
  '    public var isDeleted: Bool { nativeObject.isDeleted }',
  1],
 ['replica/Sources/PastoCore/ClipboardListPersistence.swift',
  '    // 36c448: the callback edits the first read; compare against a fresh second read before '
  'setting.',
  '    // 368818/363004, local pinboard branch: fetch errors use an empty sequence, then delete '
  'the same List.\n'
  '    func removePinboard(_ list: NSManagedObject) -> [PastoItemEntity] {\n'
  '        let items: [PastoItemEntity]\n'
  '        if let context = list.managedObjectContext {\n'
  '            items = (try? context.fetch(itemRequest(for: list))) ?? []\n'
  '        } else { items = [] }\n'
  '        for item in items {\n'
  '            if (list.value(forKey: "rawType") as? NSNumber)?.int64Value == 2,\n'
  '               let owner = item.value(forKey: "list") as? NSManagedObject, owner.isEqual(list) '
  '{\n'
  '                item.setValue(nil, forKey: "list")\n'
  '            }\n'
  '            if item.value(forKey: "timestamp") == nil, item.value(forKey: "list") == nil {\n'
  '                item.managedObjectContext?.delete(item)\n'
  '            }\n'
  '        }\n'
  '        list.managedObjectContext?.delete(list)\n'
  '        return items\n'
  '    }\n'
  '\n'
  '    // 36c448: the callback edits the first read; compare against a fresh second read before '
  'setting.',
  1],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
  '        // 363a3c/36299c: retain sequence order; a non-pinboard owner is a no-op.',
  '        func removePinboard(_ list: NSManagedObject) -> [PastoItemEntity] {\n'
  '            let affected = lists.removePinboard(list)\n'
  '            // Compatibility identifiers are read only after all native mutations, never as an '
  'input gate.\n'
  '            for object in affected {\n'
  '                guard let key = object.value(forKey: "key") as? String, let id = '
  'UUID(uuidString: key) else { continue }\n'
  '                assignedItemIDs.insert(id)\n'
  '                unassignedItemIDs.insert(id)\n'
  '                if object.isDeleted { alreadyDeletedItemIDs.insert(id) }\n'
  '            }\n'
  '            return affected\n'
  '        }\n'
  '\n'
  '        // 363a3c/36299c: retain sequence order; a non-pinboard owner is a no-op.',
  1],
 ['replica/Sources/PastoCore/ClipboardStore.swift',
  '    public func removePinboard(id: UUID) throws {',
  '    public func removeList(_ target: ClipboardListTarget) throws {\n'
  '        try mutateInTransaction { state, transaction in\n'
  '            let identifier = target.identifier\n'
  '            let affected = transaction.repository.removePinboard(target.nativeObject)\n'
  '            if let id = UUID(uuidString: identifier) {\n'
  '                state.pinboards.removeAll { $0.id == id }\n'
  '                for index in state.items.indices {\n'
  '                    state.items[index].pinboardIDs.remove(id)\n'
  '                    if state.items[index].pinboardOwnerID == id { '
  'state.items[index].pinboardOwnerID = nil }\n'
  '                }\n'
  '            }\n'
  '            for object in affected {\n'
  '                guard let key = object.value(forKey: "key") as? String, let id = '
  'UUID(uuidString: key) else { continue }\n'
  '                if object.isDeleted {\n'
  '                    state.items.removeAll { $0.id == id }\n'
  '                    continue\n'
  '                }\n'
  '                let index = state.items.firstIndex { $0.id == id }\n'
  '                var item: ClipboardItem\n'
  '                if let index { item = state.items[index] }\n'
  '                else { item = try ClipboardPersistence.item(object) }\n'
  '                item.isInHistory = object.value(forKey: "timestamp") != nil\n'
  '                if let owner = object.value(forKey: "list") as? NSManagedObject,\n'
  '                   (owner.value(forKey: "rawType") as? NSNumber)?.int64Value == 2,\n'
  '                   let ownerIdentifier = owner.value(forKey: "identifier") as? String,\n'
  '                   let ownerID = UUID(uuidString: ownerIdentifier) {\n'
  '                    item.pinboardOwnerID = ownerID\n'
  '                    item.pinboardIDs = [ownerID]\n'
  '                } else {\n'
  '                    item.pinboardOwnerID = nil\n'
  '                    item.pinboardIDs.removeAll()\n'
  '                }\n'
  '                try ClipboardItemOrderPersistence.project(&item, from: object)\n'
  '                if let index { state.items[index] = item }\n'
  '                else { state.items.append(item) }\n'
  '            }\n'
  '        }\n'
  '    }\n'
  '\n'
  '    public func removePinboard(id: UUID) throws {',
  1],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '@Published var pendingPinboardDeletionID: UUID?',
  '@Published var pendingPinboardDeletion: ClipboardListTarget?',
  1],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  'var hasPendingDeletion: Bool { pendingPinboardDeletionID != nil || pendingItemDeletion != nil }',
  'var hasPendingDeletion: Bool { pendingPinboardDeletion != nil || pendingItemDeletion != nil }',
  1],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '        if let id = pendingPinboardDeletionID, !store.pinboards.contains(where: { $0.id == id '
  '}) {\n'
  '            pendingPinboardDeletionID = nil',
  '        if pendingPinboardDeletion?.isDeleted == true {\n'
  '            pendingPinboardDeletion = nil',
  1],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    func removePinboard(_ board: Pinboard) {\n'
  '        guard store.pinboards.contains(where: { $0.id == board.id }) else { return }\n'
  '        state.cancelItemDeletion()\n'
  '        state.pinboardDeletionError = nil\n'
  '        state.pendingPinboardDeletionID = board.id',
  '    func removePinboard(_ target: ClipboardListTarget) {\n'
  '        state.cancelItemDeletion()\n'
  '        state.pinboardDeletionError = nil\n'
  '        state.pendingPinboardDeletion = target',
  1],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  'if store.localListMenuState(pinboardID: board.id).isEmpty {',
  'if store.localListMenuState(target).isEmpty {',
  1],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  'state.pendingPinboardDeletionID = nil',
  'state.pendingPinboardDeletion = nil',
  1],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '        guard let id = state.pendingPinboardDeletionID else { return }\n'
  '        guard store.pinboards.contains(where: { $0.id == id }) else {\n'
  '            cancelPinboardRemoval()\n'
  '            return\n'
  '        }\n'
  '        do {\n'
  '            try store.removePinboard(id: id)',
  '        guard let target = state.pendingPinboardDeletion else { return }\n'
  '        do {\n'
  '            try store.removeList(target)',
  1],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  '                        } else if let board = state.store.pinboards.first(where: { $0.id == '
  'state.pendingPinboardDeletionID }) {\n'
  '                            pinboardDeletionConfirmation(board)',
  '                        } else if let target = state.pendingPinboardDeletion {\n'
  '                            pinboardDeletionConfirmation(target)',
  1],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  'private func pinboardDeletionConfirmation(_ board: Pinboard) -> some View {\n'
  '        deletionConfirmation(title: "删除“\\(board.name)”？",',
  'private func pinboardDeletionConfirmation(_ target: ClipboardListTarget) -> some View {\n'
  '        deletionConfirmation(title: "删除“\\(target.name)”？",',
  1],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  '            if let board {\n'
  '                menu.addItem(OriginalPanelTabMenuItem(title: list.isEmpty ? "删除" : "删除…") {\n'
  '                    state.controller?.removePinboard(board)\n'
  '                })\n'
  '            }',
  '            menu.addItem(OriginalPanelTabMenuItem(title: list.isEmpty ? "删除" : "删除…") {\n'
  '                state.controller?.removePinboard(target)\n'
  '            })',
  1],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  'tab.menuProvider = { localListMenu(for: board, target: target) }',
  'tab.menuProvider = { localListMenu(for: target) }',
  1],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  'private func localListMenu(for board: Pinboard?, target: ClipboardListTarget) -> NSMenu',
  'private func localListMenu(for target: ClipboardListTarget) -> NSMenu',
  1]]

def pre_native_list_deletion(source):
    from native_list_reorder_scope_contract import pre_native_list_reorder
    source = pre_native_list_reorder(source)
    for _,old,new,count in reversed(CHANGES):
        if new and new in source:
            assert source.count(new)==count
            source=source.replace(new,old)
    return source

def pre_native_list_deletion_bytes(path):
    data=path.read_bytes()
    return pre_native_list_deletion(data.decode()).encode() if path.suffix=='.swift' else data
