"""Reverse only reviewed phase116 native-restore fast-path increments."""
from postwrite_restore_scope_contract import pre_postwrite_restore
CHANGES = [['replica/Sources/PastoCore/ClipboardPersistence.swift',
  '        let context: NSManagedObjectContext\n'
  '        private var cachedRepository: ManagedRepository?\n'
  '\n'
  '        init(context: NSManagedObjectContext) { self.context = context }\n',
  '        let context: NSManagedObjectContext\n'
  '        let nativeHistoryRestoreTargets: [(id: UUID, object: NSManagedObject)]\n'
  '        private var cachedRepository: ManagedRepository?\n'
  '\n'
  '        init(context: NSManagedObjectContext, nativeHistoryRestoreTargets: [(id: UUID, object: '
  'NSManagedObject)] = []) {\n'
  '            self.context = context\n'
  '            self.nativeHistoryRestoreTargets = nativeHistoryRestoreTargets\n'
  '        }\n'],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
  '    func prepareHistoryRestore(targets: [(id: UUID, object: NSManagedObject)]) throws -> '
  'HistoryRestoreSelection {\n'
  '        let transaction = Transaction(context: context)\n',
  '    func prepareHistoryRestore(targets: [(id: UUID, object: NSManagedObject)]) throws -> '
  'HistoryRestoreSelection {\n'
  '        let transaction = Transaction(context: context, nativeHistoryRestoreTargets: targets)\n'],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
  '                let replacements = transaction.repository.replacedItemDataIDs\n'
  '                let sourced = transaction.repository.sourcedItemIDs\n'
  '                try transaction.repository.update(state.items, previous: previous?.items ?? [], entity: '
  '"Item", key: { $0.id.uuidString },\n',
  '                let replacements = transaction.repository.replacedItemDataIDs\n'
  '                let sourced = transaction.repository.sourcedItemIDs\n'
  '                let previousItems = previous?.items ?? []\n'
  '                var restoredMetadataOnly: Set<UUID> = []\n'
  '                var nativeRestoreWithoutValue: Set<UUID> = []\n'
  '                if !transaction.nativeHistoryRestoreTargets.isEmpty {\n'
  '                    let targets = Dictionary(transaction.nativeHistoryRestoreTargets.map { ($0.id, '
  '$0.object) },\n'
  '                                             uniquingKeysWith: { _, last in last })\n'
  '                    nativeRestoreWithoutValue = Set(targets.keys).subtracting(state.items.map(\\.id))\n'
  '                    let before = Dictionary(uniqueKeysWithValues: previousItems.map { ($0.id, $0) })\n'
  '                    for item in state.items {\n'
  '                        guard let object = targets[item.id], let old = before[item.id] else { continue }\n'
  '                        var restored = old\n'
  '                        restored.createdAt = item.createdAt\n'
  '                        restored.updatedAt = item.updatedAt\n'
  '                        restored.isInHistory = item.isInHistory\n'
  '                        guard restored == item else { continue }\n'
  "                        // The native restore already wrote timestamp. Keep Pasto's local metadata,\n"
  '                        // without replaying unchanged value payload/preview/order onto this entity.\n'
  '                        if old.createdAt != item.createdAt { object.setValue(item.createdAt, forKey: '
  '"localCreatedAt") }\n'
  '                        if old.updatedAt != item.updatedAt { object.setValue(item.updatedAt, forKey: '
  '"updatedAt") }\n'
  '                        if old.isInHistory != item.isInHistory { object.setValue(item.isInHistory, '
  'forKey: "inHistory") }\n'
  '                        restoredMetadataOnly.insert(item.id)\n'
  '                    }\n'
  '                }\n'
  '                let itemValues = restoredMetadataOnly.isEmpty ? state.items : state.items.filter { '
  '!restoredMetadataOnly.contains($0.id) }\n'
  '                let itemPrevious = restoredMetadataOnly.isEmpty && nativeRestoreWithoutValue.isEmpty ? '
  'previousItems\n'
  '                    : previousItems.filter { !restoredMetadataOnly.contains($0.id) && '
  '!nativeRestoreWithoutValue.contains($0.id) }\n'
  '                try transaction.repository.update(itemValues, previous: itemPrevious, entity: "Item", '
  'key: { $0.id.uuidString },\n']]

def pre_native_restore_only(source):
    source=pre_postwrite_restore(source)
    for _,old,new in reversed(CHANGES):
        if new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    return source
