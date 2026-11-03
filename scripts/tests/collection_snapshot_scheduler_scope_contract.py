"""Reverse only the two reviewed144 default snapshot delivery sites."""
CHANGES = [['replica/Sources/PastoCore/ClipboardSearchCollection.swift',
  '        if schedulesDelivery {\n'
  '            context.perform { [weak self] in\n'
  '                MainActor.assumeIsolated { self?.flushPending() }\n'
  '            }\n'
  '        }\n',
  '        if schedulesDelivery {\n'
  "            // 3669fc's default ImmediateSnapshotScheduler executes its work inline.\n"
  '            flushPending()\n'
  '        }\n',
  2]]

def pre_collection_snapshot_scheduler(source):
    from stack_cell_coder_scope_contract import pre_stack_cell_coder
    source=pre_stack_cell_coder(source)
    for _,old,new,count in reversed(CHANGES):
        if new in source:
            assert source.count(new)==count
            source=source.replace(new,old)
    return source

def pre_collection_snapshot_scheduler_bytes(path):
    data=path.read_bytes()
    return pre_collection_snapshot_scheduler(data.decode()).encode()if path.suffix==".swift"else data
