"""Reverse only two reviewed146 Stack table subclass/producer hunks."""
CHANGES = [['replica/Sources/PastoCore/OriginalStackTableController.swift',
  'import AppKit\n\n',
  'import AppKit\n'
  '\n'
  '@MainActor\n'
  'private final class OriginalStackTableView: NSTableView {\n'
  '    // 0a0b2c: the Stack table permits window dragging independently of row selection.\n'
  '    override var mouseDownCanMoveWindow: Bool { true }\n'
  '}\n'
  '\n'],
 ['replica/Sources/PastoCore/OriginalStackTableController.swift',
  '        tableView = NSTableView(frame: .init(x: 0, y: 0, width: 264, height: 44))',
  '        tableView = OriginalStackTableView(frame: .init(x: 0, y: 0, width: 264, height: 44))']]

def pre_stack_table_drag(source):
    from stack_close_session_scope_contract import pre_stack_close_session
    source=pre_stack_close_session(source)
    for _,old,new in reversed(CHANGES):
        if new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    return source

def pre_stack_table_drag_bytes(path):
    data=path.read_bytes()
    return pre_stack_table_drag(data.decode()).encode()if path.suffix==".swift"else data
