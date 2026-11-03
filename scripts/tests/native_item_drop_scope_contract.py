"""Reverse exactly phase172 native item-drop/integration hunks for historical contracts."""
CHANGES = [['replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift',
  'context == .outsideApplication ? .copy : .move',
  'context == .outsideApplication ? .copy : [.copy, .move]',
  1],
 ['replica/Sources/Pasto/UI/OriginalPinboardTabTitle.swift',
  '    var onDropString: ((String) -> Bool)?',
  '    var onDropString: ((String) -> Bool)?\n'
  '    var onDropItemIdentifiers: (([String]) -> Void)?\n'
  '    var canDropItems: (() -> Bool)?',
  2],
 ['replica/Sources/Pasto/UI/OriginalPinboardTabTitle.swift',
  '        view.onDropString = onDropString',
  '        view.onDropString = onDropString\n'
  '        view.onDropItemIdentifiers = onDropItemIdentifiers\n'
  '        view.canDropItems = canDropItems',
  1],
 ['replica/Sources/Pasto/UI/OriginalPinboardTabTitle.swift',
  '        registerForDraggedTypes([.string])',
  '        // Native item IDs are distinct from the retained local group-reorder adapter.\n'
  '        registerForDraggedTypes([OriginalNativeDragPasteboardWriter.itemIdentifierType, .string])',
  1],
 ['replica/Sources/Pasto/UI/OriginalPinboardTabTitle.swift',
  '    override func draggingEntered(_ sender: NSDraggingInfo) -> NSDragOperation {\n'
  '        isDragDestination = draggedGroup(sender) != nil\n'
  '        needsDisplay = true\n'
  '        return isDragDestination ? .move : []\n'
  '    }',
  '    private func isItemDrag(_ sender: NSDraggingInfo) -> Bool {\n'
  '        sender.draggingPasteboard.types?.contains(OriginalNativeDragPasteboardWriter.itemIdentifierType) '
  '== true\n'
  '    }\n'
  '\n'
  '    override func draggingEntered(_ sender: NSDraggingInfo) -> NSDragOperation {\n'
  '        if isItemDrag(sender) {\n'
  "            // 0792a8/07a4f8 returns the predicate's Bool as operation raw value 0/1 (copy).\n"
  '            isDragDestination = canDropItems?() ?? false\n'
  '            needsDisplay = true\n'
  '            return isDragDestination ? .copy : []\n'
  '        }\n'
  '        isDragDestination = draggedGroup(sender) != nil\n'
  '        needsDisplay = true\n'
  '        return isDragDestination ? .move : []\n'
  '    }',
  1],
 ['replica/Sources/Pasto/UI/OriginalPinboardTabTitle.swift',
  '    override func prepareForDragOperation(_ sender: NSDraggingInfo) -> Bool { draggedGroup(sender) != nil '
  '}',
  '    override func prepareForDragOperation(_ sender: NSDraggingInfo) -> Bool {\n'
  '        if isItemDrag(sender) { return true }\n'
  '        return draggedGroup(sender) != nil\n'
  '    }',
  1],
 ['replica/Sources/Pasto/UI/OriginalPinboardTabTitle.swift',
  '    override func performDragOperation(_ sender: NSDraggingInfo) -> Bool {\n'
  '        isDragDestination = false\n'
  '        needsDisplay = true\n'
  '        guard let value = draggedGroup(sender) else { return false }\n'
  '        return onDropString?(value) ?? false\n'
  '    }\n'
  '}',
  '    override func performDragOperation(_ sender: NSDraggingInfo) -> Bool {\n'
  '        if performItemDrop(sender) { return true }\n'
  '        if isItemDrag(sender) { return false }\n'
  '        isDragDestination = false\n'
  '        needsDisplay = true\n'
  '        guard let value = draggedGroup(sender) else { return false }\n'
  '        return onDropString?(value) ?? false\n'
  '    }\n'
  '\n'
  '    // 079430: preserve item order/duplicates, skip nil strings, report acceptance independently of the '
  'write.\n'
  '    private func performItemDrop(_ sender: NSDraggingInfo) -> Bool {\n'
  '        guard let onDropItemIdentifiers else { return false }\n'
  '        let identifiers = (sender.draggingPasteboard.pasteboardItems ?? []).compactMap {\n'
  '            $0.string(forType: OriginalNativeDragPasteboardWriter.itemIdentifierType)\n'
  '        }\n'
  '        guard !identifiers.isEmpty else { return false }\n'
  '        onDropItemIdentifiers(identifiers)\n'
  '        return true\n'
  '    }\n'
  '}',
  1],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  '        tab.dragString = "paste-pinboard:" + target.identifier',
  '        tab.dragString = "paste-pinboard:" + target.identifier\n'
  "        // 328f38's nil-share branch is writable for Pasto's local Lists, including history.\n"
  '        tab.canDropItems = { true }\n'
  '        tab.onDropItemIdentifiers = { [weak state = state] identifiers in\n'
  '            state?.dropItems(identifiers: identifiers, to: target)\n'
  '        }',
  1],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    func assignItems(_ items: [ClipboardRestoreItem], to target: ClipboardPinboardTarget) {',
  '    func dropItems(identifiers: [String], to target: ClipboardListTarget) {\n'
  "        // 03c3b0's local write error branch only consumes the error; no additional system alert.\n"
  '        try? store.dropItems(identifiers: identifiers, to: target)\n'
  '    }\n'
  '\n'
  '    func assignItems(_ items: [ClipboardRestoreItem], to target: ClipboardPinboardTarget) {',
  1],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
  '        func assignItems(_ items: [PastoItemEntity], to pinboard: NSManagedObject) throws -> '
  '[ClipboardItem] {',
  '        // 03b634 → ItemsReading witness+20: resolve each String independently and retain '
  'duplicates/order.\n'
  '        func droppedItem(identifier: String) -> PastoItemEntity? {\n'
  '            let request = PastoItemEntity.defaultFetchRequest()\n'
  '            request.predicate = NSPredicate(\n'
  '                format: "nativeIdentifier == %@ OR (nativeIdentifier == nil AND key == %@)", identifier, '
  'identifier)\n'
  '            request.fetchLimit = 1\n'
  '            request.fetchOffset = 0\n'
  '            return (try? context.fetch(request))?.first\n'
  '        }\n'
  '\n'
  '        // 364014/3614c0: local nil-share path; cloud clone/permission flows are outside this adapter.\n'
  '        func dropItems(identifiers: [String], to list: NSManagedObject) throws -> [ClipboardItem] {\n'
  '            let items = identifiers.compactMap { droppedItem(identifier: $0) }\n'
  '            guard !items.isEmpty else { return [] }\n'
  '            switch (list.value(forKey: "rawType") as? NSNumber)?.int64Value ?? 0 {\n'
  '            case 2:\n'
  '                return try assignItems(items, to: list)\n'
  '            case 1:\n'
  '                // 361ec0/364108 reverse the input before generating one Date per occurrence.\n'
  '                for item in items.reversed() { item.setValue(Date(), forKey: "timestamp") }\n'
  '                if let capacity = lists.historyCapacity(of: list), capacity > 0 {\n'
  '                    let interval = -capacity * 24 * 60 * 60\n'
  '                    let request = PastoItemEntity.defaultFetchRequest()\n'
  '                    request.predicate = NSPredicate(format: "list == nil && timestamp < %@",\n'
  '                        Date(timeIntervalSinceNow: Double(interval)) as NSDate)\n'
  '                    let expired = (try? context.fetch(request)) ?? []\n'
  '                    for item in expired { context.delete(item) }\n'
  '                    // Compatibility bookkeeping follows native deletion, never filters its input.\n'
  '                    for item in expired {\n'
  '                        if let key = item.value(forKey: "key") as? String, let id = UUID(uuidString: key) '
  '{\n'
  '                            alreadyDeletedItemIDs.insert(id)\n'
  '                        }\n'
  '                    }\n'
  '                }\n'
  '                // Original static predicate is identifier == sharedPasteboardHistory, then '
  'refresh(merge:true).\n'
  '                if let history = try? lists.historyList() { context.refresh(history, mergeChanges: true) '
  '}\n'
  '                return try items.map { try ClipboardPersistence.item($0) }\n'
  '            default:\n'
  '                return []\n'
  '            }\n'
  '        }\n'
  '\n'
  '        func assignItems(_ items: [PastoItemEntity], to pinboard: NSManagedObject) throws -> '
  '[ClipboardItem] {',
  1],
 ['replica/Sources/PastoCore/ClipboardStore.swift',
  '    /// The local group menu retains its supplied entities through the repository transaction.',
  '    /// Native tab item-drop keeps the supplied List through String lookup and local repository '
  'dispatch.\n'
  '    public func dropItems(identifiers: [String], to target: ClipboardListTarget) throws {\n'
  '        try mutateInTransaction { state, transaction in\n'
  '            let values = try transaction.repository.dropItems(identifiers: identifiers, to: '
  'target.nativeObject)\n'
  '            state.items.removeAll { transaction.repository.alreadyDeletedItemIDs.contains($0.id) }\n'
  '            for item in values {\n'
  '                if let index = state.items.firstIndex(where: { $0.id == item.id }) {\n'
  '                    state.items[index] = item\n'
  '                } else {\n'
  '                    state.items.append(item)\n'
  '                }\n'
  '            }\n'
  '        }\n'
  '    }\n'
  '\n'
  '    /// The local group menu retains its supplied entities through the repository transaction.',
  1]]

def pre_native_item_drop(source):
    from text_storage_owner_scope_contract import pre_text_storage_owner
    source = pre_text_storage_owner(source)
    import re
    def pattern(text):
        return re.compile((r"(?m)^" if text[:1] in (" ", "\t") else "") + re.escape(text))
    for _,old,new,count in reversed(CHANGES):
        if new in old and pattern(old).search(source):
            continue
        matches=list(pattern(new).finditer(source)) if new else []
        if matches:
            assert len(matches)==count, (new[:80],len(matches),count)
            source=pattern(new).sub(lambda _:old,source)
    return source

def pre_native_item_drop_bytes(path):
    data=path.read_bytes()
    return pre_native_item_drop(data.decode()).encode() if path.suffix=='.swift' else data
