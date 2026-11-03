"""Reverse only the reviewed145 Stack cell coder initializer."""
CHANGES = [['replica/Sources/Pasto/UI/OriginalStackSnippetCell.swift',
  '    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }\n',
  '    required init?(coder: NSCoder) {\n'
  '        nativeImageProvider = { input in\n'
  '            let rawType = input.previewRawType() ?? 0\n'
  '            return OriginalStackCategoryIcons.image(for:\n'
  '                OriginalPasteboardContentKind(rawValue: UInt8(rawType)) ?? .unknown)\n'
  '        }\n'
  '        super.init(coder: coder)\n'
  '    }\n']]

def pre_stack_cell_coder(source):
    from stack_table_drag_scope_contract import pre_stack_table_drag
    source=pre_stack_table_drag(source)
    for _,old,new in reversed(CHANGES):
        if new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    return source

def pre_stack_cell_coder_bytes(path):
    data=path.read_bytes()
    return pre_stack_cell_coder(data.decode()).encode()if path.suffix==".swift"else data
