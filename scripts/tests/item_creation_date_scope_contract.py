"""Isolate only reviewed155 required native Item creation field, callback and legacy backfill."""
CHANGES = [['replica/Sources/PastoCore/OriginalManagedItem.swift',
  '    // 0x100329754: Item-specific wrapper around the same generic request factory.\n',
  '    // 3b4888: creation time is independent of the history timestamp and later recency '
  'changes.\n'
  '    override func awakeFromInsert() {\n'
  '        super.awakeFromInsert()\n'
  '        setPrimitiveValue(Date(), forKey: "createdAt")\n'
  '    }\n'
  '\n'
  '    // 0x100329754: Item-specific wrapper around the same generic request factory.\n',
  1],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
  'includeTypedItemData: Bool = true) -> NSManagedObjectModel {',
  'includeTypedItemData: Bool = true,\n'
  '                                  includeNativeCreationDate: Bool = true) -> '
  'NSManagedObjectModel {',
  1],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
  '        itemAttributes.append(contentsOf: [attribute("updatedAt", .dateAttributeType), '
  'attribute("inHistory", .booleanAttributeType)])\n',
  '        if includeNativeCreationDate { itemAttributes.append(attribute("createdAt", '
  '.dateAttributeType)) }\n'
  '        itemAttributes.append(contentsOf: [attribute("updatedAt", .dateAttributeType), '
  'attribute("inHistory", .booleanAttributeType)])\n',
  1],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
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
  '        let legacyCandidates = [\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeNativeCreationDate: false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeTypedItemData: false, includeNativeCreationDate: false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeTypedSources: false, includeTypedItemData: false, includeNativeCreationDate: false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeTypedLists: false, includeTypedSources: false, includeTypedItemData: false, '
  'includeNativeCreationDate: false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeNativeTitle: false, includeTypedLists: false, includeTypedSources: false, '
  'includeTypedItemData: false, includeNativeCreationDate: false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeItemOrder: false, includeNativeTitle: false, includeTypedLists: false, '
  'includeTypedSources: false, includeTypedItemData: false, includeNativeCreationDate: false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeTypedItem: false, includeItemOrder: false, includeNativeTitle: false, includeTypedLists: '
  'false, includeTypedSources: false, includeTypedItemData: false, includeNativeCreationDate: '
  'false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeNativeSources: false, includeTypedItem: false, includeItemOrder: false, '
  'includeNativeTitle: false, includeTypedLists: false, includeTypedSources: false, '
  'includeTypedItemData: false, includeNativeCreationDate: false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeNativeItemData: false, includeNativeSources: false, includeTypedItem: false, '
  'includeItemOrder: false, includeNativeTitle: false, includeTypedLists: false, '
  'includeTypedSources: false, includeTypedItemData: false, includeNativeCreationDate: false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeLists: true, includeOptionalTimestamp: false, includeNativeItemData: false, '
  'includeNativeSources: false, includeTypedItem: false, includeItemOrder: false, '
  'includeNativeTitle: false, includeTypedLists: false, includeTypedSources: false, '
  'includeTypedItemData: false, includeNativeCreationDate: false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeLists: false, includeOptionalTimestamp: false, includeNativeItemData: false, '
  'includeNativeSources: false, includeTypedItem: false, includeItemOrder: false, '
  'includeNativeTitle: false, includeTypedLists: false, includeTypedSources: false, '
  'includeTypedItemData: false, includeNativeCreationDate: false),\n'
  '            makeModel(includeNativeIdentity: false, preserveItemKeyInHistory: true, '
  'includeLists: false, includeOptionalTimestamp: false, includeNativeItemData: false, '
  'includeNativeSources: false, includeTypedItem: false, includeItemOrder: false, '
  'includeNativeTitle: false, includeTypedLists: false, includeTypedSources: false, '
  'includeTypedItemData: false, includeNativeCreationDate: false),\n'
  '            makeModel(includeNativeIdentity: false, preserveItemKeyInHistory: false, '
  'includeLists: false, includeOptionalTimestamp: false, includeNativeItemData: false, '
  'includeNativeSources: false, includeTypedItem: false, includeItemOrder: false, '
  'includeNativeTitle: false, includeTypedLists: false, includeTypedSources: false, '
  'includeTypedItemData: false, includeNativeCreationDate: false)\n'
  '        ]',
  1],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
  '        if sourceModel.entitiesByName["ItemDataEntity"] == nil {\n',
  '        if sourceModel.entitiesByName["ItemDataEntity"] == nil\n'
  '            || sourceModel.entitiesByName["Item"]?.attributesByName["createdAt"] == nil {\n',
  1],
 ['replica/Sources/PastoCore/ClipboardItemDataPersistence.swift',
  '/// Populate the required relationship before NSMigrationManager validates/saves\n'
  '/// its destination. The original store is replaced only after migration succeeds.\n',
  '/// Populate required native creation time and content relationships before destination '
  'validation.\n'
  '/// The original store is replaced only after migration succeeds.\n',
  1],
 ['replica/Sources/PastoCore/ClipboardItemDataPersistence.swift',
  '        try super.createRelationships(forDestination: object, in: mapping, manager: manager)\n'
  '        guard object.value(forKey: "data") == nil else { return }\n',
  '        try super.createRelationships(forDestination: object, in: mapping, manager: manager)\n'
  '        // The old local date records historical recency; preserve it when introducing the '
  'native field.\n'
  '        if manager.sourceModel.entitiesByName["Item"]?.attributesByName["createdAt"] == nil {\n'
  '            let sources = manager.sourceInstances(forEntityMappingName: mapping.name, '
  'destinationInstances: [object])\n'
  '            guard sources.count == 1, let source = sources.first else { throw '
  'CocoaError(.fileReadCorruptFile) }\n'
  '            let localDate = source.entity.attributesByName["localCreatedAt"] != nil\n'
  '                ? source.value(forKey: "localCreatedAt") as? Date : nil\n'
  '            guard let createdAt = localDate ?? source.value(forKey: "timestamp") as? Date else '
  '{\n'
  '                throw CocoaError(.fileReadCorruptFile)\n'
  '            }\n'
  '            object.setPrimitiveValue(createdAt, forKey: "createdAt")\n'
  '        }\n'
  '        guard object.value(forKey: "data") == nil else { return }\n',
  1]]

def pre_item_creation_date(source):
    from image_load_diagnostic_scope_contract import pre_image_load_diagnostic
    source=pre_image_load_diagnostic(source)
    for _,old,new,count in reversed(CHANGES):
        if new in source:
            assert source.count(new)==count
            source=source.replace(new,old)
    return source

def pre_item_creation_date_bytes(path):
    data=path.read_bytes()
    return pre_item_creation_date(data.decode()).encode()if path.suffix=='.swift'else data
