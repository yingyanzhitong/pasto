"""Reverse only phase105 deltas when checking immutable historical source contracts."""
from pathlib import Path
from group_target_scope_contract import pre_group_target
CHANGES = [['replica/Sources/PastoCore/ClipboardListPersistence.swift',
  '    // 0x100325130/329088: count managed history/group members; count errors mean empty.',
  '    // 0x1003620f8: consume the supplied local entities without reducing them to IDs.\n'
  '    func moveItems(_ items: [PastoItemEntity], to pinboard: NSManagedObject) -> '
  '[PastoItemEntity] {\n'
  '        guard var destination = try? context.fetch(itemRequest(for: pinboard)) else { return [] '
  '}\n'
  '        let moving = items.filter { item in\n'
  '            guard let owner = item.value(forKey: "list") as? NSManagedObject,\n'
  '                  (owner.value(forKey: "rawType") as? NSNumber)?.int64Value == 2 else { return '
  'true }\n'
  '            return !owner.isEqual(pinboard)\n'
  '        }\n'
  '        for item in moving {\n'
  '            item.setValue(pinboard, forKey: "list")\n'
  '            destination.insert(item, at: 0)\n'
  '        }\n'
  '        for (index, item) in destination.enumerated() {\n'
  '            if (item.value(forKey: "displayOrderInPinboard") as? NSNumber)?.int64Value != '
  'Int64(index) {\n'
  '                item.setValue(Int64(index), forKey: "displayOrderInPinboard")\n'
  '            }\n'
  '        }\n'
  '        return destination\n'
  '    }\n'
  '\n'
  '    // 0x100325130/329088: count managed history/group members; count errors mean empty.'],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
  '        private(set) var sourcedItemIDs: Set<UUID> = []',
  '        private(set) var sourcedItemIDs: Set<UUID> = []\n'
  '        private(set) var assignedItemIDs: Set<UUID> = []'],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
  '        func restoreHistoryItems(_ targets:',
  '        func assignItems(_ items: [PastoItemEntity], to pinboard: NSManagedObject) throws -> '
  '[ClipboardItem] {\n'
  '            let destination = lists.moveItems(items, to: pinboard)\n'
  '            let values = try destination.map { object in\n'
  '                var item = try ClipboardPersistence.item(object)\n'
  '                if let owner = item.pinboardOwnerID { item.pinboardIDs = [owner] }\n'
  '                else { item.pinboardIDs.removeAll() }\n'
  '                return item\n'
  '            }\n'
  '            assignedItemIDs.formUnion(values.map(\\.id))\n'
  '            return values\n'
  '        }\n'
  '\n'
  '        func restoreHistoryItems(_ targets:'],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
  '                    if object.isInserted || old?.pinboardOwnerID != item.pinboardOwnerID {',
  '                    if !transaction.repository.assignedItemIDs.contains(item.id),\n'
  '                       object.isInserted || old?.pinboardOwnerID != item.pinboardOwnerID {'],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
  '                    ClipboardItemOrderPersistence.update(item, on: object)',
  '                    if !transaction.repository.assignedItemIDs.contains(item.id) {\n'
  '                        ClipboardItemOrderPersistence.update(item, on: object)\n'
  '                    }'],
 ['replica/Sources/PastoCore/ClipboardStore.swift',
  '    public func assign(orderedIDs: [UUID], to pinboardID: UUID?) throws {',
  '    /// The local group menu retains its supplied entities through the repository transaction.\n'
  '    public func assign(items: [ClipboardRestoreItem], to pinboardID: UUID?) throws {\n'
  '        guard let pinboardID, items.allSatisfy({ $0.nativeObject != nil }) else {\n'
  '            try assign(orderedIDs: items.map(\\.id), to: pinboardID)\n'
  '            return\n'
  '        }\n'
  '        guard !items.isEmpty else { return }\n'
  '        try mutateInTransaction { state, transaction in\n'
  '            guard let pinboard = try transaction.repository.lists.list(identifier: '
  'pinboardID.uuidString) else {\n'
  '                throw ClipboardStoreError.pinboardNotFound\n'
  '            }\n'
  '            let destination = try transaction.repository.assignItems(items.map { '
  '$0.nativeObject! }, to: pinboard)\n'
  '            for item in destination {\n'
  '                if let index = state.items.firstIndex(where: { $0.id == item.id }) {\n'
  '                    state.items[index] = item\n'
  '                } else {\n'
  '                    state.items.append(item)\n'
  '                }\n'
  '            }\n'
  '        }\n'
  '    }\n'
  '\n'
  '    public func assign(orderedIDs: [UUID], to pinboardID: UUID?) throws {'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  'try store.assign(orderedIDs: items.map(\\.id), to: id)',
  'try store.assign(items: items, to: id)'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '                try withExtendedLifetime(selectionItems) {\n'
  '                    try store.assign(orderedIDs: ids, to: board.id)\n'
  '                }',
  '                if let selectionItems {\n'
  '                    try store.assign(items: selectionItems, to: board.id)\n'
  '                } else {\n'
  '                    try store.assign(orderedIDs: ids, to: board.id)\n'
  '                }']]

def pre_native_group_write(source):
    source = pre_group_target(source)
    for _,old,new in reversed(CHANGES):
        if old.startswith(new) and old in source: continue
        if new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    return source

def pre_native_group_write_bytes(path):
    p=Path(path)
    return pre_native_group_write(p.read_text()).encode() if p.suffix=='.swift' else p.read_bytes()
