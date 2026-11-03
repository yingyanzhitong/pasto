"""Reverse only three reviewed141 native list-navigation hunks."""
CHANGES = [['replica/Sources/PastoCore/ClipboardRestoreItem.swift',
  '    // 31ebc8: Stack cells read the current entity preview on row demand.\n',
  '    // 3b83c4 reads current timestamp and type2 owner without decoding the content archive.\n'
  '    public func listNavigationMembership() -> (isInHistory: Bool, pinboardID: UUID?)? {\n'
  '        guard let object = nativeObject else { return nil }\n'
  '        let isInHistory = object.value(forKey: "timestamp") != nil\n'
  '        guard let owner = object.value(forKey: "list") as? NSManagedObject,\n'
  '              (owner.value(forKey: "rawType") as? NSNumber)?.int64Value == 2 else {\n'
  '            return (isInHistory, nil)\n'
  '        }\n'
  '        let identifier = owner.value(forKey: "identifier") as? String\n'
  '        return (isInHistory, identifier.flatMap { UUID(uuidString: $0) })\n'
  '    }\n'
  '\n'
  '    // 31ebc8: Stack cells read the current entity preview on row demand.\n'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    func selectedItemTargetLists() -> [UUID?] {\n'
  '        let items = selectedItems\n'
  '        guard items.count == 1 else { return [] }\n'
  '        let item = items[0]\n'
  '        let isSearching = !isCollectionSearchQueryEmpty\n'
  '        var lists: [UUID?] = []\n',
  '    func selectedItemTargetLists() -> [UUID?] {\n'
  '        let ids = orderedSelectionIDs.filter { selection.contains($0) }\n'
  '        let inputs: [ClipboardRestoreItem]\n'
  '        if let collectionOwner {\n'
  '            inputs = collectionOwner.appliedRestoreItems(for: self, orderedIDs: ids) ?? []\n'
  '        } else {\n'
  '            let byID = Dictionary(uniqueKeysWithValues: visibleItems.map { ($0.id, $0) })\n'
  '            inputs = ids.compactMap { byID[$0]?.restoreItem() }\n'
  '        }\n'
  '        guard inputs.count == 1 else { return [] }\n'
  '        let input = inputs[0]\n'
  '        let isSearching = !isCollectionSearchQueryEmpty\n'
  '        var lists: [UUID?] = []\n'
  '        if let membership = input.listNavigationMembership() {\n'
  '            if membership.isInHistory, isSearching || pinboardID != nil { lists.append(nil) }\n'
  '            if let ownerID = membership.pinboardID, isSearching || ownerID != pinboardID {\n'
  '                lists.append(ownerID)\n'
  '            }\n'
  '            return lists\n'
  '        }\n'
  '        let item = input.resolvedItem()\n'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '        guard !lists.isEmpty, let item = state.selectedItems.first else { return false }\n'
  '        let collection = (panel as? ReplicaPanel)?.collectionFocusTarget as? '
  'ReplicaNativeCollectionHost\n'
  '        let offset = collection?.horizontalOffsetForVisibleItem(item.id)\n'
  '        state.pendingListFocus = ReplicaUIState.PendingListFocus(itemID: item.id,\n',
  '        guard !lists.isEmpty, let input = appliedRestoreItems().first else { return false }\n'
  '        let collection = (panel as? ReplicaPanel)?.collectionFocusTarget as? '
  'ReplicaNativeCollectionHost\n'
  '        let offset = collection?.horizontalOffsetForVisibleItem(input.id)\n'
  '        state.pendingListFocus = ReplicaUIState.PendingListFocus(itemID: input.id,\n']]

def pre_native_list_navigation(source):
    from group_menu_state_scope_contract import pre_group_menu_state
    source=pre_group_menu_state(source)
    for _,old,new in reversed(CHANGES):
        if new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    return source

def pre_native_list_navigation_bytes(path):
    data=path.read_bytes()
    return pre_native_list_navigation(data.decode()).encode()if path.suffix==".swift"else data
