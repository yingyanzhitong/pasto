"""Reverse only phase109 native group unassign deltas for historical source checks."""
from pathlib import Path
from list_remove_menu_scope_contract import pre_list_remove_menu
CHANGES = [['replica/Sources/PastoCore/ClipboardPersistence.swift',
  '        private(set) var assignedItemIDs: Set<UUID> = []',
  '        private(set) var assignedItemIDs: Set<UUID> = []\n'
  '        private(set) var unassignedItemIDs: Set<UUID> = []\n'
  '        private(set) var alreadyDeletedItemIDs: Set<UUID> = []'],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
  '        func restoreHistoryItems(_ targets:',
  '        // 363a3c/36299c: retain sequence order; a non-pinboard owner is a no-op.\n'
  '        func unassignItems(_ targets: [(id: UUID, object: NSManagedObject)]) -> [(id: UUID, '
  'object: NSManagedObject)] {\n'
  '            var affected: [(id: UUID, object: NSManagedObject)] = []\n'
  '            for target in targets {\n'
  '                let object = target.object\n'
  '                guard let owner = object.value(forKey: "list") as? NSManagedObject,\n'
  '                      (owner.value(forKey: "rawType") as? NSNumber)?.int64Value == 2 else { '
  'continue }\n'
  '                if let currentOwner = object.value(forKey: "list") as? NSManagedObject,\n'
  '                   currentOwner.isEqual(owner) {\n'
  '                    object.setValue(nil, forKey: "list")\n'
  '                }\n'
  '                if object.value(forKey: "timestamp") == nil, object.value(forKey: "list") == '
  'nil {\n'
  "                    // 3646ec uses the item's own context, including a nil-context no-op.\n"
  '                    object.managedObjectContext?.delete(object)\n'
  '                    if object.isDeleted { alreadyDeletedItemIDs.insert(target.id) }\n'
  '                }\n'
  '                // These sets suppress only compatibility writes, never the supplied sequence.\n'
  '                assignedItemIDs.insert(target.id)\n'
  '                unassignedItemIDs.insert(target.id)\n'
  '                affected.append(target)\n'
  '            }\n'
  '            return affected\n'
  '        }\n'
  '\n'
  '        func restoreHistoryItems(_ targets:'],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
  '                                         updatingKeys: [String] = [],\n'
  '                                         apply:',
  '                                         updatingKeys: [String] = [], alreadyDeletedKeys: '
  'Set<String> = [],\n'
  '                                         apply:'],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
  '            orderedRemoved += previous.map(key).filter { removed.contains($0) && '
  '!scheduled.contains($0) }\n'
  '            let keys = changed.map(key) + orderedRemoved',
  '            orderedRemoved += previous.map(key).filter { removed.contains($0) && '
  '!scheduled.contains($0) }\n'
  '            orderedRemoved.removeAll { alreadyDeletedKeys.contains($0) }\n'
  '            let keys = changed.map(key) + orderedRemoved'],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
  '                           updatingKeys: replacements.map(\\.uuidString)) { item, old, object '
  'in',
  '                           updatingKeys: replacements.map(\\.uuidString),\n'
  '                           alreadyDeletedKeys: '
  'Set(transaction.repository.alreadyDeletedItemIDs.map(\\.uuidString))) { item, old, object in'],
 ['replica/Sources/PastoCore/ClipboardStore.swift',
  '    private func assign(items: [ClipboardRestoreItem], pinboardID: UUID?, nativePinboard: '
  'NSManagedObject?) throws {\n'
  '        guard let pinboardID,',
  '    private func assign(items: [ClipboardRestoreItem], pinboardID: UUID?, nativePinboard: '
  'NSManagedObject?) throws {\n'
  '        if pinboardID == nil, items.allSatisfy({ $0.nativeObject != nil }) {\n'
  '            try unassignNative(items: items)\n'
  '            return\n'
  '        }\n'
  '        guard let pinboardID,'],
 ['replica/Sources/PastoCore/ClipboardStore.swift',
  '    public func assign(orderedIDs: [UUID], to pinboardID: UUID?) throws {',
  '    private func unassignNative(items: [ClipboardRestoreItem]) throws {\n'
  '        try mutateInTransaction { state, transaction in\n'
  '            let affected = transaction.repository.unassignItems(items.map { (id: $0.id, object: '
  '$0.nativeObject!) })\n'
  '            // Native sequence mutations finish before compatibility projection can fail.\n'
  '            for target in affected {\n'
  '                if target.object.isDeleted {\n'
  '                    state.items.removeAll { $0.id == target.id }\n'
  '                    continue\n'
  '                }\n'
  '                let index = state.items.firstIndex { $0.id == target.id }\n'
  '                var item: ClipboardItem\n'
  '                if let index { item = state.items[index] }\n'
  '                else { item = try ClipboardPersistence.item(target.object) }\n'
  '                if let owner = target.object.value(forKey: "list") as? NSManagedObject,\n'
  '                   (owner.value(forKey: "rawType") as? NSNumber)?.int64Value == 2,\n'
  '                   let identifier = owner.value(forKey: "identifier") as? String,\n'
  '                   let ownerID = UUID(uuidString: identifier) {\n'
  '                    item.pinboardOwnerID = ownerID\n'
  '                    item.pinboardIDs = [ownerID]\n'
  '                } else {\n'
  '                    item.pinboardOwnerID = nil\n'
  '                    item.pinboardIDs.removeAll()\n'
  '                }\n'
  '                try ClipboardItemOrderPersistence.project(&item, from: target.object)\n'
  '                if let index { state.items[index] = item }\n'
  '                else { state.items.append(item) }\n'
  '            }\n'
  '        }\n'
  '    }\n'
  '\n'
  '    public func assign(orderedIDs: [UUID], to pinboardID: UUID?) throws {'],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
  '                           alreadyDeletedKeys: '
  'Set(transaction.repository.alreadyDeletedItemIDs.map(\\.uuidString))) { item, old, object in\n'
  '                    if !sourced.contains(item.id), object.isInserted',
  '                           alreadyDeletedKeys: '
  'Set(transaction.repository.alreadyDeletedItemIDs.map(\\.uuidString))) { item, old, object in\n'
  '                    if transaction.repository.unassignedItemIDs.contains(item.id) {\n'
  '                        if old.map(contentForComparison) != contentForComparison(item) {\n'
  '                            object.setValue(try encode(content(item)), forKey: "content")\n'
  '                        }\n'
  '                        return\n'
  '                    }\n'
  '                    if !sourced.contains(item.id), object.isInserted']]

def pre_native_unassign(source):
    source=pre_list_remove_menu(source)
    for _,old,new in reversed(CHANGES):
        if old.startswith(new) and old in source: continue
        if new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    return source

def pre_native_unassign_bytes(path):
    p=Path(path)
    return pre_native_unassign(p.read_text()).encode() if p.suffix=='.swift' else p.read_bytes()
