"""Reverse only reviewed152 typed source classes/model and four complete source factories."""
CHANGES = [['replica/Sources/PastoCore/OriginalManagedItem.swift',
  'enum OriginalManagedFetchRequest {',
  '// Source entities share the native local save callback and initialize their own creation '
  'date.\n'
  '@objc(PastoApplicationEntity)\n'
  'class PastoApplicationEntity: PastoManagedObject {\n'
  '    override class var entityName: String { "ApplicationEntity" }\n'
  '\n'
  '    override func awakeFromInsert() {\n'
  '        super.awakeFromInsert()\n'
  '        setPrimitiveValue(Date(), forKey: "createdAt")\n'
  '    }\n'
  '}\n'
  '\n'
  '@objc(PastoDeviceEntity)\n'
  'class PastoDeviceEntity: PastoManagedObject {\n'
  '    override class var entityName: String { "DeviceEntity" }\n'
  '\n'
  '    override func awakeFromInsert() {\n'
  '        super.awakeFromInsert()\n'
  '        setPrimitiveValue(Date(), forKey: "createdAt")\n'
  '    }\n'
  '}\n'
  '\n'
  'enum OriginalManagedFetchRequest {',
  1],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
  'includeTypedLists: Bool = true) -> NSManagedObjectModel {',
  'includeTypedLists: Bool = true,\n'
  '                                  includeTypedSources: Bool = true) -> NSManagedObjectModel {',
  1],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
  '        if includeNativeSources { ClipboardSourcePersistence.addEntities(to: model, item: '
  'model.entitiesByName["Item"]!) }\n',
  '        if includeNativeSources { ClipboardSourcePersistence.addEntities(to: model, item: '
  'model.entitiesByName["Item"]!) }\n'
  '        if includeNativeSources && includeTypedSources {\n'
  '            model.entitiesByName["ApplicationEntity"]!.managedObjectClassName = '
  'NSStringFromClass(PastoApplicationEntity.self)\n'
  '            model.entitiesByName["DeviceEntity"]!.managedObjectClassName = '
  'NSStringFromClass(PastoDeviceEntity.self)\n'
  '        }\n',
  1],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
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
  '        ]',
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
  1],
 ['replica/Sources/PastoCore/ClipboardSourcePersistence.swift',
  '    private func first(_ entity: String, key: String, value: String) throws -> NSManagedObject? '
  '{\n'
  '        let request = NSFetchRequest<NSManagedObject>(entityName: entity)\n'
  '        request.predicate = NSPredicate(format: "%K == %@", key, value)\n'
  '        request.fetchLimit = 1\n'
  '        return try context.fetch(request).first\n'
  '    }',
  '    private func first<Entity: PastoManagedObject>(_ entity: Entity.Type, key: String, value: '
  'String) throws -> Entity? {\n'
  '        let request = OriginalManagedFetchRequest.make(for: entity)\n'
  '        request.predicate = NSPredicate(format: "%K == %@", key, value)\n'
  '        request.fetchLimit = 1\n'
  '        request.fetchOffset = 0\n'
  '        return try context.fetch(request).first\n'
  '    }',
  1],
 ['replica/Sources/PastoCore/ClipboardSourcePersistence.swift',
  'try first("ApplicationEntity", key:',
  'try first(PastoApplicationEntity.self, key:',
  1],
 ['replica/Sources/PastoCore/ClipboardSourcePersistence.swift',
  'try first("DeviceEntity", key:',
  'try first(PastoDeviceEntity.self, key:',
  1],
 ['replica/Sources/PastoCore/ClipboardSourcePersistence.swift',
  '            object.setValue(Date(), forKey: "createdAt")\n',
  '',
  1],
 ['replica/Sources/PastoCore/ClipboardSourcePersistence.swift',
  '        let request = NSFetchRequest<NSManagedObject>(entityName: "DeviceEntity")\n',
  '        let request = OriginalManagedFetchRequest.make(for: PastoDeviceEntity.self)\n',
  1],
 ['replica/Sources/PastoCore/ClipboardSourcePersistence.swift',
  '        request.fetchBatchSize = 20\n',
  '',
  1],
 ['replica/Sources/PastoCore/ClipboardSourcePersistence.swift',
  '        // The existing local model requires this creation column.\n'
  '        object.setValue(Date(), forKey: "createdAt")\n',
  '',
  1],
 ['replica/Sources/PastoCore/ClipboardSourcePersistence.swift',
  '        object.setValue(Date(), forKey: "createdAt")\n',
  '',
  1]]
FACTORY_CHANGES = [['    private func first(_ entity: String, key: String, value: String) throws -> NSManagedObject? '
  '{\n'
  '        let request = NSFetchRequest<NSManagedObject>(entityName: entity)\n'
  '        request.predicate = NSPredicate(format: "%K == %@", key, value)\n'
  '        request.fetchLimit = 1\n'
  '        return try context.fetch(request).first\n'
  '    }',
  '    private func first<Entity: PastoManagedObject>(_ entity: Entity.Type, key: String, value: '
  'String) throws -> Entity? {\n'
  '        let request = OriginalManagedFetchRequest.make(for: entity)\n'
  '        request.predicate = NSPredicate(format: "%K == %@", key, value)\n'
  '        request.fetchLimit = 1\n'
  '        request.fetchOffset = 0\n'
  '        return try context.fetch(request).first\n'
  '    }'],
 ['    func application(_ value: SourceApplicationRecord) throws -> NSManagedObject {\n'
  '        let object: NSManagedObject\n'
  '        if let existing = try first("ApplicationEntity", key: "bundleIdentifier", value: '
  'value.bundleIdentifier) {\n'
  '            object = existing\n'
  '        } else {\n'
  '            object = NSEntityDescription.insertNewObject(forEntityName: "ApplicationEntity", '
  'into: context)\n'
  '            object.setValue(value.bundleIdentifier, forKey: "bundleIdentifier")\n'
  '            object.setValue(Date(), forKey: "createdAt")\n'
  '        }\n'
  '        if (object.value(forKey: "name") as? String) != value.name { '
  'object.setValue(value.name, forKey: "name") }\n'
  '        if (object.value(forKey: "rawIcon") as? Data) != value.rawIcon { '
  'object.setValue(value.rawIcon, forKey: "rawIcon") }\n'
  '        let color = Int64(bitPattern: value.rawColor ?? 0)\n'
  '        if (object.value(forKey: "rawColor") as? NSNumber)?.int64Value != color {\n'
  '            object.setValue(color, forKey: "rawColor")\n'
  '        }\n'
  '        return object\n'
  '    }',
  '    func application(_ value: SourceApplicationRecord) throws -> NSManagedObject {\n'
  '        let object: NSManagedObject\n'
  '        if let existing = try first(PastoApplicationEntity.self, key: "bundleIdentifier", '
  'value: value.bundleIdentifier) {\n'
  '            object = existing\n'
  '        } else {\n'
  '            object = NSEntityDescription.insertNewObject(forEntityName: "ApplicationEntity", '
  'into: context)\n'
  '            object.setValue(value.bundleIdentifier, forKey: "bundleIdentifier")\n'
  '        }\n'
  '        if (object.value(forKey: "name") as? String) != value.name { '
  'object.setValue(value.name, forKey: "name") }\n'
  '        if (object.value(forKey: "rawIcon") as? Data) != value.rawIcon { '
  'object.setValue(value.rawIcon, forKey: "rawIcon") }\n'
  '        let color = Int64(bitPattern: value.rawColor ?? 0)\n'
  '        if (object.value(forKey: "rawColor") as? NSNumber)?.int64Value != color {\n'
  '            object.setValue(color, forKey: "rawColor")\n'
  '        }\n'
  '        return object\n'
  '    }'],
 ['    func currentDevice() -> NSManagedObject {\n'
  '        let identifier = OriginalLocalDevice.f_1000f35e0()\n'
  '        let request = NSFetchRequest<NSManagedObject>(entityName: "DeviceEntity")\n'
  '        request.predicate = NSPredicate(format: "identifier == %@", identifier)\n'
  '        request.fetchBatchSize = 20\n'
  '        request.fetchLimit = 1\n'
  '        request.fetchOffset = 0\n'
  '        if let existing = (try? context.fetch(request))?.first { return existing }\n'
  '        let name = OriginalLocalDevice.f_1000f36ec()\n'
  '        let object = NSEntityDescription.insertNewObject(forEntityName: "DeviceEntity", into: '
  'context)\n'
  '        object.setValue(Int64(2), forKey: "rawType")\n'
  '        object.setValue(identifier, forKey: "identifier")\n'
  '        object.setValue(name, forKey: "name")\n'
  '        // The existing local model requires this creation column.\n'
  '        object.setValue(Date(), forKey: "createdAt")\n'
  '        return object\n'
  '    }',
  '    func currentDevice() -> NSManagedObject {\n'
  '        let identifier = OriginalLocalDevice.f_1000f35e0()\n'
  '        let request = OriginalManagedFetchRequest.make(for: PastoDeviceEntity.self)\n'
  '        request.predicate = NSPredicate(format: "identifier == %@", identifier)\n'
  '        request.fetchLimit = 1\n'
  '        request.fetchOffset = 0\n'
  '        if let existing = (try? context.fetch(request))?.first { return existing }\n'
  '        let name = OriginalLocalDevice.f_1000f36ec()\n'
  '        let object = NSEntityDescription.insertNewObject(forEntityName: "DeviceEntity", into: '
  'context)\n'
  '        object.setValue(Int64(2), forKey: "rawType")\n'
  '        object.setValue(identifier, forKey: "identifier")\n'
  '        object.setValue(name, forKey: "name")\n'
  '        return object\n'
  '    }'],
 ['    private func device(named name: String) throws -> NSManagedObject {\n'
  '        if let existing = try first("DeviceEntity", key: "name", value: name) { return existing '
  '}\n'
  '        // Old Pasto records have a device name, but no vendor/device UUID.\n'
  '        let object = NSEntityDescription.insertNewObject(forEntityName: "DeviceEntity", into: '
  'context)\n'
  '        object.setValue(UUID().uuidString, forKey: "identifier")\n'
  '        object.setValue(name, forKey: "name")\n'
  '        object.setValue(Date(), forKey: "createdAt")\n'
  '        return object\n'
  '    }',
  '    private func device(named name: String) throws -> NSManagedObject {\n'
  '        if let existing = try first(PastoDeviceEntity.self, key: "name", value: name) { return '
  'existing }\n'
  '        // Old Pasto records have a device name, but no vendor/device UUID.\n'
  '        let object = NSEntityDescription.insertNewObject(forEntityName: "DeviceEntity", into: '
  'context)\n'
  '        object.setValue(UUID().uuidString, forKey: "identifier")\n'
  '        object.setValue(name, forKey: "name")\n'
  '        return object\n'
  '    }']]

FACTORY_BODY_CHANGES = [['{\n'
  '        let request = NSFetchRequest<NSManagedObject>(entityName: entity)\n'
  '        request.predicate = NSPredicate(format: "%K == %@", key, value)\n'
  '        request.fetchLimit = 1\n'
  '        return try context.fetch(request).first\n'
  '    }',
  '{\n'
  '        let request = OriginalManagedFetchRequest.make(for: entity)\n'
  '        request.predicate = NSPredicate(format: "%K == %@", key, value)\n'
  '        request.fetchLimit = 1\n'
  '        request.fetchOffset = 0\n'
  '        return try context.fetch(request).first\n'
  '    }'],
 ['{\n'
  '        let object: NSManagedObject\n'
  '        if let existing = try first("ApplicationEntity", key: "bundleIdentifier", value: '
  'value.bundleIdentifier) {\n'
  '            object = existing\n'
  '        } else {\n'
  '            object = NSEntityDescription.insertNewObject(forEntityName: "ApplicationEntity", '
  'into: context)\n'
  '            object.setValue(value.bundleIdentifier, forKey: "bundleIdentifier")\n'
  '            object.setValue(Date(), forKey: "createdAt")\n'
  '        }\n'
  '        if (object.value(forKey: "name") as? String) != value.name { '
  'object.setValue(value.name, forKey: "name") }\n'
  '        if (object.value(forKey: "rawIcon") as? Data) != value.rawIcon { '
  'object.setValue(value.rawIcon, forKey: "rawIcon") }\n'
  '        let color = Int64(bitPattern: value.rawColor ?? 0)\n'
  '        if (object.value(forKey: "rawColor") as? NSNumber)?.int64Value != color {\n'
  '            object.setValue(color, forKey: "rawColor")\n'
  '        }\n'
  '        return object\n'
  '    }',
  '{\n'
  '        let object: NSManagedObject\n'
  '        if let existing = try first(PastoApplicationEntity.self, key: "bundleIdentifier", '
  'value: value.bundleIdentifier) {\n'
  '            object = existing\n'
  '        } else {\n'
  '            object = NSEntityDescription.insertNewObject(forEntityName: "ApplicationEntity", '
  'into: context)\n'
  '            object.setValue(value.bundleIdentifier, forKey: "bundleIdentifier")\n'
  '        }\n'
  '        if (object.value(forKey: "name") as? String) != value.name { '
  'object.setValue(value.name, forKey: "name") }\n'
  '        if (object.value(forKey: "rawIcon") as? Data) != value.rawIcon { '
  'object.setValue(value.rawIcon, forKey: "rawIcon") }\n'
  '        let color = Int64(bitPattern: value.rawColor ?? 0)\n'
  '        if (object.value(forKey: "rawColor") as? NSNumber)?.int64Value != color {\n'
  '            object.setValue(color, forKey: "rawColor")\n'
  '        }\n'
  '        return object\n'
  '    }'],
 ['{\n'
  '        let identifier = OriginalLocalDevice.f_1000f35e0()\n'
  '        let request = NSFetchRequest<NSManagedObject>(entityName: "DeviceEntity")\n'
  '        request.predicate = NSPredicate(format: "identifier == %@", identifier)\n'
  '        request.fetchBatchSize = 20\n'
  '        request.fetchLimit = 1\n'
  '        request.fetchOffset = 0\n'
  '        if let existing = (try? context.fetch(request))?.first { return existing }\n'
  '        let name = OriginalLocalDevice.f_1000f36ec()\n'
  '        let object = NSEntityDescription.insertNewObject(forEntityName: "DeviceEntity", into: '
  'context)\n'
  '        object.setValue(Int64(2), forKey: "rawType")\n'
  '        object.setValue(identifier, forKey: "identifier")\n'
  '        object.setValue(name, forKey: "name")\n'
  '        // The existing local model requires this creation column.\n'
  '        object.setValue(Date(), forKey: "createdAt")\n'
  '        return object\n'
  '    }',
  '{\n'
  '        let identifier = OriginalLocalDevice.f_1000f35e0()\n'
  '        let request = OriginalManagedFetchRequest.make(for: PastoDeviceEntity.self)\n'
  '        request.predicate = NSPredicate(format: "identifier == %@", identifier)\n'
  '        request.fetchLimit = 1\n'
  '        request.fetchOffset = 0\n'
  '        if let existing = (try? context.fetch(request))?.first { return existing }\n'
  '        let name = OriginalLocalDevice.f_1000f36ec()\n'
  '        let object = NSEntityDescription.insertNewObject(forEntityName: "DeviceEntity", into: '
  'context)\n'
  '        object.setValue(Int64(2), forKey: "rawType")\n'
  '        object.setValue(identifier, forKey: "identifier")\n'
  '        object.setValue(name, forKey: "name")\n'
  '        return object\n'
  '    }'],
 ['{\n'
  '        if let existing = try first("DeviceEntity", key: "name", value: name) { return existing '
  '}\n'
  '        // Old Pasto records have a device name, but no vendor/device UUID.\n'
  '        let object = NSEntityDescription.insertNewObject(forEntityName: "DeviceEntity", into: '
  'context)\n'
  '        object.setValue(UUID().uuidString, forKey: "identifier")\n'
  '        object.setValue(name, forKey: "name")\n'
  '        object.setValue(Date(), forKey: "createdAt")\n'
  '        return object\n'
  '    }',
  '{\n'
  '        if let existing = try first(PastoDeviceEntity.self, key: "name", value: name) { return '
  'existing }\n'
  '        // Old Pasto records have a device name, but no vendor/device UUID.\n'
  '        let object = NSEntityDescription.insertNewObject(forEntityName: "DeviceEntity", into: '
  'context)\n'
  '        object.setValue(UUID().uuidString, forKey: "identifier")\n'
  '        object.setValue(name, forKey: "name")\n'
  '        return object\n'
  '    }']]
def pre_source_entity_lifecycle(source):
    from item_data_constructor_scope_contract import pre_item_data_constructor
    source=pre_item_data_constructor(source)
    for old,new in reversed(FACTORY_CHANGES):
        if new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    for old,new in reversed(FACTORY_BODY_CHANGES):
        if new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    for path,old,new,count in reversed(CHANGES):
        if path.endswith('ClipboardSourcePersistence.swift'): continue
        if new in source:
            assert source.count(new)==count
            source=source.replace(new,old)
    return source

def pre_source_entity_lifecycle_bytes(path):
    data=path.read_bytes()
    return pre_source_entity_lifecycle(data.decode()).encode()if path.suffix=='.swift'else data
