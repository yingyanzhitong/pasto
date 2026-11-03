"""Isolate only reviewed153 actual ItemData constructor/model/diagnostic routing deltas."""
CHANGES = [['replica/Sources/PastoCore/ClipboardItemDataPersistence.swift',
  "/// Called on the owning managed context's queue, including during store migration.",
  '// 31b494: the local named wrapper is owned from object construction, including fetched '
  'faults.\n'
  '// ItemData has no Syncable date fields and directly inherits NSManagedObject.\n'
  '@objc(PastoItemDataEntity)\n'
  'final class PastoItemDataEntity: NSManagedObject {\n'
  '    let diagnostics = OriginalNamedDiagnostic.f_1000d4624(name: "ItemDataEntity")\n'
  '}\n'
  '\n'
  "/// Called on the owning managed context's queue, including during store migration.",
  1],
 ['replica/Sources/PastoCore/ClipboardItemDataPersistence.swift',
  '    // Preserve per-object logger ownership without changing the existing managed entity '
  'class/model.\n'
  '    // The original constructs the named wrapper at entity creation; this adapter defers it to '
  'the error path.\n',
  '    // Current models own the wrapper on the actual entity; older plain objects keep their '
  'local adapter.\n',
  1],
 ['replica/Sources/PastoCore/ClipboardItemDataPersistence.swift',
  '    @MainActor private static func diagnostics(for data: NSManagedObject) -> '
  'OriginalNamedDiagnostic {\n',
  '    @MainActor private static func diagnostics(for data: NSManagedObject) -> '
  'OriginalNamedDiagnostic {\n'
  '        if let data = data as? PastoItemDataEntity { return data.diagnostics }\n',
  1],
 ['replica/Sources/PastoCore/ClipboardSearchRecord.swift',
  '                        // This private context/data object is created once for this deferred '
  'read.\n'
  '                        OriginalNamedDiagnostic.f_1000d4624(name: "ItemDataEntity")',
  '                        if let data = data as? PastoItemDataEntity { return data.diagnostics }\n'
  '                        // Older source models can still produce plain managed objects.\n'
  '                        return OriginalNamedDiagnostic.f_1000d4624(name: "ItemDataEntity")',
  1],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
  'includeTypedSources: Bool = true) -> NSManagedObjectModel {',
  'includeTypedSources: Bool = true,\n'
  '                                  includeTypedItemData: Bool = true) -> NSManagedObjectModel {',
  1],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
  '        if includeNativeItemData { ClipboardItemDataPersistence.addEntity(to: model, item: '
  'model.entitiesByName["Item"]!) }\n',
  '        if includeNativeItemData { ClipboardItemDataPersistence.addEntity(to: model, item: '
  'model.entitiesByName["Item"]!) }\n'
  '        if includeNativeItemData && includeTypedItemData {\n'
  '            model.entitiesByName["ItemDataEntity"]!.managedObjectClassName = '
  'NSStringFromClass(PastoItemDataEntity.self)\n'
  '        }\n',
  1],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
  '        let legacyCandidates = [\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeTypedSources: false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeTypedLists: false, includeTypedSources: false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeNativeTitle: false, includeTypedLists: false, includeTypedSources: false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeItemOrder: false, includeNativeTitle: false, includeTypedLists: false, '
  'includeTypedSources: false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeTypedItem: false, includeItemOrder: false, includeNativeTitle: false, includeTypedLists: '
  'false, includeTypedSources: false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeNativeSources: false, includeTypedItem: false, includeItemOrder: false, '
  'includeNativeTitle: false, includeTypedLists: false, includeTypedSources: false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeNativeItemData: false, includeNativeSources: false, includeTypedItem: false, '
  'includeItemOrder: false, includeNativeTitle: false, includeTypedLists: false, '
  'includeTypedSources: false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeLists: true, includeOptionalTimestamp: false, includeNativeItemData: false, '
  'includeNativeSources: false, includeTypedItem: false, includeItemOrder: false, '
  'includeNativeTitle: false, includeTypedLists: false, includeTypedSources: false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeLists: false, includeOptionalTimestamp: false, includeNativeItemData: false, '
  'includeNativeSources: false, includeTypedItem: false, includeItemOrder: false, '
  'includeNativeTitle: false, includeTypedLists: false, includeTypedSources: false),\n'
  '            makeModel(includeNativeIdentity: false, preserveItemKeyInHistory: true, '
  'includeLists: false, includeOptionalTimestamp: false, includeNativeItemData: false, '
  'includeNativeSources: false, includeTypedItem: false, includeItemOrder: false, '
  'includeNativeTitle: false, includeTypedLists: false, includeTypedSources: false),\n'
  '            makeModel(includeNativeIdentity: false, preserveItemKeyInHistory: false, '
  'includeLists: false, includeOptionalTimestamp: false, includeNativeItemData: false, '
  'includeNativeSources: false, includeTypedItem: false, includeItemOrder: false, '
  'includeNativeTitle: false, includeTypedLists: false, includeTypedSources: false)\n'
  '        ]',
  '        let legacyCandidates = [\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeTypedItemData: false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeTypedSources: false, includeTypedItemData: false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeTypedLists: false, includeTypedSources: false, includeTypedItemData: false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeNativeTitle: false, includeTypedLists: false, includeTypedSources: false, '
  'includeTypedItemData: false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeItemOrder: false, includeNativeTitle: false, includeTypedLists: false, '
  'includeTypedSources: false, includeTypedItemData: false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeTypedItem: false, includeItemOrder: false, includeNativeTitle: false, includeTypedLists: '
  'false, includeTypedSources: false, includeTypedItemData: false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeNativeSources: false, includeTypedItem: false, includeItemOrder: false, '
  'includeNativeTitle: false, includeTypedLists: false, includeTypedSources: false, '
  'includeTypedItemData: false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeNativeItemData: false, includeNativeSources: false, includeTypedItem: false, '
  'includeItemOrder: false, includeNativeTitle: false, includeTypedLists: false, '
  'includeTypedSources: false, includeTypedItemData: false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeLists: true, includeOptionalTimestamp: false, includeNativeItemData: false, '
  'includeNativeSources: false, includeTypedItem: false, includeItemOrder: false, '
  'includeNativeTitle: false, includeTypedLists: false, includeTypedSources: false, '
  'includeTypedItemData: false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeLists: false, includeOptionalTimestamp: false, includeNativeItemData: false, '
  'includeNativeSources: false, includeTypedItem: false, includeItemOrder: false, '
  'includeNativeTitle: false, includeTypedLists: false, includeTypedSources: false, '
  'includeTypedItemData: false),\n'
  '            makeModel(includeNativeIdentity: false, preserveItemKeyInHistory: true, '
  'includeLists: false, includeOptionalTimestamp: false, includeNativeItemData: false, '
  'includeNativeSources: false, includeTypedItem: false, includeItemOrder: false, '
  'includeNativeTitle: false, includeTypedLists: false, includeTypedSources: false, '
  'includeTypedItemData: false),\n'
  '            makeModel(includeNativeIdentity: false, preserveItemKeyInHistory: false, '
  'includeLists: false, includeOptionalTimestamp: false, includeNativeItemData: false, '
  'includeNativeSources: false, includeTypedItem: false, includeItemOrder: false, '
  'includeNativeTitle: false, includeTypedLists: false, includeTypedSources: false, '
  'includeTypedItemData: false)\n'
  '        ]',
  1]]

def pre_item_data_constructor(source):
    from item_creation_date_scope_contract import pre_item_creation_date
    source=pre_item_creation_date(source)
    for _,old,new,count in reversed(CHANGES):
        if new in source:
            assert source.count(new)==count
            source=source.replace(new,old)
    return source

def pre_item_data_constructor_bytes(path):
    data=path.read_bytes()
    return pre_item_data_constructor(data.decode()).encode()if path.suffix=='.swift'else data
