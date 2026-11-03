"""Reverse only reviewed151 shared callback move and Item inheritance hookup."""
CHANGES = [['replica/Sources/PastoCore/OriginalManagedItem.swift',
  '    // 3b4984: local edits advance updatedAt; inserted/syncApply/unchanged objects do not.\n'
  '    override func willSave() {\n'
  '        let isSyncApply = managedObjectContext?.transactionAuthor == "syncApply"\n'
  '        if !isInserted && !isSyncApply && !changedValues().isEmpty {\n'
  '            setPrimitiveValue(Date(), forKey: "updatedAt")\n'
  '        }\n'
  '        super.willSave()\n'
  '    }\n'
  '\n'
  '    override func awakeFromInsert() {\n',
  '    override func awakeFromInsert() {\n',
  2],
 ['replica/Sources/PastoCore/OriginalManagedItem.swift',
  '    @objc class var defaultPredicate: NSPredicate? { nil }\n',
  '    @objc class var defaultPredicate: NSPredicate? { nil }\n'
  '\n'
  '    // 3b4984: local edits advance updatedAt; inserted/syncApply/unchanged objects do not.\n'
  '    override func willSave() {\n'
  '        let isSyncApply = managedObjectContext?.transactionAuthor == "syncApply"\n'
  '        if !isInserted && !isSyncApply && !changedValues().isEmpty {\n'
  '            setPrimitiveValue(Date(), forKey: "updatedAt")\n'
  '        }\n'
  '        super.willSave()\n'
  '    }\n'
  '\n',
  1]]

def pre_item_shared_will_save(source):
    from source_entity_lifecycle_scope_contract import pre_source_entity_lifecycle
    source=pre_source_entity_lifecycle(source)
    if CHANGES[1][2] not in source: return source
    for _,old,new,count in reversed(CHANGES):
        if new in source:
            assert source.count(new)==count
            source=source.replace(new,old)
    return source

def pre_item_shared_will_save_bytes(path):
    data=path.read_bytes()
    return pre_item_shared_will_save(data.decode()).encode()if path.suffix=='.swift'else data
