"""Reverse only reviewed149 native List model/validator/factory hunks."""
CHANGES = [['replica/Sources/PastoCore/OriginalManagedItem.swift',
  'enum OriginalManagedFetchRequest {',
  "// 32b0c8/329624: the model's actual List class supplies its own fetch defaults.\n"
  '@objc(PastoListEntity)\n'
  'class PastoListEntity: PastoManagedObject {\n'
  '    override class var entityName: String { "ListEntity" }\n'
  '    override class var defaultSortDescriptors: [NSSortDescriptor]? {\n'
  '        [NSSortDescriptor(key: "metadata.index", ascending: true)]\n'
  '    }\n'
  '\n'
  '    override func awakeFromInsert() {\n'
  '        super.awakeFromInsert()\n'
  '        setPrimitiveValue(Date(), forKey: "createdAt")\n'
  '    }\n'
  '\n'
  '    static func listFetchRequest() -> NSFetchRequest<PastoListEntity> {\n'
  '        OriginalManagedFetchRequest.make(for: PastoListEntity.self)\n'
  '    }\n'
  '\n'
  '    // 329980/329ec0: repair a missing relationship, then propagate the superclass error.\n'
  '    override func validateForInsert() throws {\n'
  '        if !isDeleted, value(forKey: "metadata") == nil, let context = managedObjectContext {\n'
  '            let identifier = "list:" + String._unconditionallyBridgeFromObjectiveC(\n'
  '                value(forKey: "identifier") as? NSString)\n'
  '            let request = PastoListMetadataEntity.metadataFetchRequest()\n'
  '            request.predicate = NSPredicate(format: "identifier == %@", identifier)\n'
  '            request.fetchLimit = 1\n'
  '            request.fetchOffset = 0\n'
  '            var existing: PastoListMetadataEntity?\n'
  '            context.performAndWait { existing = (try? context.fetch(request))?.first }\n'
  '            if let existing {\n'
  '                setValue(existing, forKey: "metadata")\n'
  '            } else {\n'
  '                let all = PastoListMetadataEntity.metadataFetchRequest()\n'
  '                all.fetchOffset = 0\n'
  '                var values: [PastoListMetadataEntity] = []\n'
  '                context.performAndWait { values = (try? context.fetch(all)) ?? [] }\n'
  '                let lastIndex: Int64\n'
  '                if let last = values.last {\n'
  '                    lastIndex = (last.value(forKey: "index") as? NSNumber)?.int64Value ?? 0\n'
  '                } else {\n'
  '                    lastIndex = -1\n'
  '                }\n'
  '                let nextIndex = lastIndex + 1\n'
  '                let metadata = PastoListMetadataEntity(context: context)\n'
  '                metadata.setValue(identifier, forKey: "identifier")\n'
  '                metadata.setValue(self, forKey: "list")\n'
  '                metadata.setValue(nextIndex, forKey: "index")\n'
  '                setValue(metadata, forKey: "metadata")\n'
  '            }\n'
  '        }\n'
  '        try super.validateForInsert()\n'
  '    }\n'
  '}\n'
  '\n'
  '// 32b6a8/32b4b4: metadata has a separate class and index ordering.\n'
  '@objc(PastoListMetadataEntity)\n'
  'class PastoListMetadataEntity: PastoManagedObject {\n'
  '    override class var entityName: String { "ListMetadataEntity" }\n'
  '    override class var defaultSortDescriptors: [NSSortDescriptor]? {\n'
  '        [NSSortDescriptor(key: "index", ascending: true)]\n'
  '    }\n'
  '\n'
  '    override func awakeFromInsert() {\n'
  '        super.awakeFromInsert()\n'
  '        setPrimitiveValue(Date(), forKey: "createdAt")\n'
  '    }\n'
  '\n'
  '    static func metadataFetchRequest() -> NSFetchRequest<PastoListMetadataEntity> {\n'
  '        OriginalManagedFetchRequest.make(for: PastoListMetadataEntity.self)\n'
  '    }\n'
  '}\n'
  '\n'
  'enum OriginalManagedFetchRequest {'],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
  'includeNativeTitle: Bool = true) -> NSManagedObjectModel {',
  'includeNativeTitle: Bool = true,\n'
  '                                  includeTypedLists: Bool = true) -> NSManagedObjectModel {'],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
  '        if includeLists { ClipboardListPersistence.addEntities(to: model, item: '
  'model.entitiesByName["Item"]!) }\n',
  '        if includeLists { ClipboardListPersistence.addEntities(to: model, item: '
  'model.entitiesByName["Item"]!) }\n'
  '        if includeLists && includeTypedLists {\n'
  '            model.entitiesByName["ListEntity"]!.managedObjectClassName = '
  'NSStringFromClass(PastoListEntity.self)\n'
  '            model.entitiesByName["ListMetadataEntity"]!.managedObjectClassName = '
  'NSStringFromClass(PastoListMetadataEntity.self)\n'
  '        }\n'],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
  '        let legacyCandidates = [\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeNativeTitle: false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeItemOrder: false, includeNativeTitle: false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeTypedItem: false, includeItemOrder: false, includeNativeTitle: false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeNativeSources: false, includeTypedItem: false, includeItemOrder: false, '
  'includeNativeTitle: false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeNativeItemData: false, includeNativeSources: false, includeTypedItem: false, '
  'includeItemOrder: false, includeNativeTitle: false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeLists: true, includeOptionalTimestamp: false, includeNativeItemData: false, '
  'includeNativeSources: false, includeTypedItem: false, includeItemOrder: false, '
  'includeNativeTitle: false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeLists: false, includeOptionalTimestamp: false, includeNativeItemData: false, '
  'includeNativeSources: false, includeTypedItem: false, includeItemOrder: false, '
  'includeNativeTitle: false),\n'
  '            makeModel(includeNativeIdentity: false, preserveItemKeyInHistory: true, '
  'includeLists: false, includeOptionalTimestamp: false, includeNativeItemData: false, '
  'includeNativeSources: false, includeTypedItem: false, includeItemOrder: false, '
  'includeNativeTitle: false),\n'
  '            makeModel(includeNativeIdentity: false, preserveItemKeyInHistory: false, '
  'includeLists: false, includeOptionalTimestamp: false, includeNativeItemData: false, '
  'includeNativeSources: false, includeTypedItem: false, includeItemOrder: false, '
  'includeNativeTitle: false)\n'
  '        ]',
  '        let legacyCandidates = [\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeTypedLists: false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeNativeTitle: false, includeTypedLists: false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeItemOrder: false, includeNativeTitle: false, includeTypedLists: false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeTypedItem: false, includeItemOrder: false, includeNativeTitle: false, includeTypedLists: '
  'false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeNativeSources: false, includeTypedItem: false, includeItemOrder: false, '
  'includeNativeTitle: false, includeTypedLists: false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeNativeItemData: false, includeNativeSources: false, includeTypedItem: false, '
  'includeItemOrder: false, includeNativeTitle: false, includeTypedLists: false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeLists: true, includeOptionalTimestamp: false, includeNativeItemData: false, '
  'includeNativeSources: false, includeTypedItem: false, includeItemOrder: false, '
  'includeNativeTitle: false, includeTypedLists: false),\n'
  '            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, '
  'includeLists: false, includeOptionalTimestamp: false, includeNativeItemData: false, '
  'includeNativeSources: false, includeTypedItem: false, includeItemOrder: false, '
  'includeNativeTitle: false, includeTypedLists: false),\n'
  '            makeModel(includeNativeIdentity: false, preserveItemKeyInHistory: true, '
  'includeLists: false, includeOptionalTimestamp: false, includeNativeItemData: false, '
  'includeNativeSources: false, includeTypedItem: false, includeItemOrder: false, '
  'includeNativeTitle: false, includeTypedLists: false),\n'
  '            makeModel(includeNativeIdentity: false, preserveItemKeyInHistory: false, '
  'includeLists: false, includeOptionalTimestamp: false, includeNativeItemData: false, '
  'includeNativeSources: false, includeTypedItem: false, includeItemOrder: false, '
  'includeNativeTitle: false, includeTypedLists: false)\n'
  '        ]'],
 ['replica/Sources/PastoCore/ClipboardListPersistence.swift',
  '    func pinboardRequest() -> NSFetchRequest<NSManagedObject> {\n'
  '        let request = NSFetchRequest<NSManagedObject>(entityName: "ListEntity")\n'
  '        request.sortDescriptors = [NSSortDescriptor(key: "metadata.index", ascending: true)]\n'
  '        request.predicate = NSPredicate(format: "rawType == %d", 2)\n'
  '        request.fetchBatchSize = 20\n'
  '        return request\n'
  '    }',
  '    func pinboardRequest() -> NSFetchRequest<PastoListEntity> {\n'
  '        let request = PastoListEntity.listFetchRequest()\n'
  '        request.predicate = NSPredicate(format: "rawType == %d", 2)\n'
  '        return request\n'
  '    }'],
 ['replica/Sources/PastoCore/ClipboardSearchCollection.swift',
  '    private let controller: NSFetchedResultsController<NSManagedObject>',
  '    private let controller: NSFetchedResultsController<PastoListEntity>'],
 ['replica/Sources/PastoCore/ClipboardSearchCollection.swift',
  '    init(context: NSManagedObjectContext, request: NSFetchRequest<NSManagedObject>)',
  '    init(context: NSManagedObjectContext, request: NSFetchRequest<PastoListEntity>)'],
 ['replica/Sources/PastoCore/ClipboardSearchCollection.swift',
  '            guard let object = try? context.existingObject(with: objectID),\n'
  '                  object.entity.name == "ListEntity",',
  '            guard let object = (try? context.existingObject(with: objectID)) as? '
  'PastoListEntity,']]

def pre_list_insert_validation(source):
    from list_will_save_scope_contract import pre_list_will_save
    source=pre_list_will_save(source)
    for _,old,new in reversed(CHANGES):
        if new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    return source

def pre_list_insert_validation_bytes(path):
    data=path.read_bytes()
    return pre_list_insert_validation(data.decode()).encode()if path.suffix=='.swift'else data
