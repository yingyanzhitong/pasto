"""Reverse three reviewed143 patterns at both native collection sites (six hunks)."""
CHANGES = [['replica/Sources/PastoCore/ClipboardSearchCollection.swift',
  '    private var objectIDs: [NSManagedObjectID] = []\n',
  '    private var objectIDs: [NSManagedObjectID] = []\n'
  '    private var objectIDMembership: Set<NSManagedObjectID> = []\n',
  2],
 ['replica/Sources/PastoCore/ClipboardSearchCollection.swift',
  '        objectIDs = value.ids\n',
  '        if objectIDs != value.ids {\n'
  '            objectIDs = value.ids\n'
  '            objectIDMembership = Set(value.ids)\n'
  '        }\n',
  2],
 ['replica/Sources/PastoCore/ClipboardSearchCollection.swift',
  '        let membership = Set(ids)\n',
  '        let membership = pending.map { Set($0.ids) } ?? objectIDMembership\n',
  2]]

def pre_collection_membership_cache(source):
    from collection_snapshot_scheduler_scope_contract import pre_collection_snapshot_scheduler
    source=pre_collection_snapshot_scheduler(source)
    for _,old,new,count in reversed(CHANGES):
        if new in source:
            assert source.count(new)==count
            source=source.replace(new,old)
    return source

def pre_collection_membership_cache_bytes(path):
    data=path.read_bytes()
    return pre_collection_membership_cache(data.decode()).encode()if path.suffix==".swift"else data
