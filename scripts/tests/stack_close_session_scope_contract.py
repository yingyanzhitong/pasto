"""Reverse only round147 reviewed Stack session source changes."""
CHANGES = [['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '            guard oldValue != stackIDs, store.preferences.stackItemIDs != stackIDs else { '
  'return }\n'
  '            store.preferences.stackItemIDs = stackIDs\n'
  '            perform { try store.save() }\n',
  '            guard oldValue != stackIDs else { return }\n'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '        stackIDs = store.preferences.stackItemIDs\n',
  ''],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    func hideStack() { stackWindowController?.close(); stackDidChange?() }',
  '    func hideStack() {\n'
  '        guard let closingController = stackWindowController else { return }\n'
  '        let closingWindow = stackWindow\n'
  '        closingController.close()\n'
  '        // 0a86c0/2182a4: release the coordinator owner, then the presented content.\n'
  '        stackWindowController = nil\n'
  '        closingController.contentViewController = nil\n'
  '        closingWindow?.contentView = nil\n'
  '        stackWindow = nil\n'
  '        stackTableController = nil\n'
  '        if let stackCaptureObserver { '
  'NotificationCenter.default.removeObserver(stackCaptureObserver) }\n'
  '        stackCaptureObserver = nil\n'
  '        // 084f14/083d18: each new Stack controller owns a fresh, transient queue.\n'
  '        if state.stackIDs.isEmpty { stackDidChange?() }\n'
  '        else { state.stackIDs.removeAll() }\n'
  '    }']]

def pre_stack_close_session(source):
    from list_insert_validation_scope_contract import pre_list_insert_validation
    source=pre_list_insert_validation(source)
    for _,old,new in reversed(CHANGES):
        if not new:
            anchor='        searchIndex.setSuggestionDataSource(store.makeSearchSuggestionProvider())\n'
            if anchor+old not in source and anchor in source:
                source=source.replace(anchor,anchor+old,1)
        elif new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    return source

def pre_stack_close_session_bytes(path):
    data=path.read_bytes()
    return pre_stack_close_session(data.decode()).encode()if path.suffix=='.swift'else data
