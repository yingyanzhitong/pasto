"""Reverse only round150 two bound List/Metadata willSave methods."""
CHANGES = [['replica/Sources/PastoCore/OriginalManagedItem.swift',
  '    override func awakeFromInsert() {\n',
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
  2]]

def pre_list_will_save(source):
    from item_shared_will_save_scope_contract import pre_item_shared_will_save
    source=pre_item_shared_will_save(source)
    for _,old,new,count in reversed(CHANGES):
        if new in source:
            assert source.count(new)==count
            source=source.replace(new,old)
    return source

def pre_list_will_save_bytes(path):
    data=path.read_bytes()
    return pre_list_will_save(data.decode()).encode()if path.suffix=='.swift'else data
