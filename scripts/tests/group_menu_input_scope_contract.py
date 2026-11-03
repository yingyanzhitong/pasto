"""Six reviewed captured-group-menu deltas for earlier frozen source contracts."""
from pathlib import Path
from optional_selection_scope_contract import pre_optional_selection

CHANGES = [['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    func addToStack(_ item: ClipboardItem, restoreItem: ClipboardRestoreItem? = nil) {\n',
  '    // 09ee9c forwards the array captured when the group menu was built.\n'
  '    func assignItems(_ items: [ClipboardRestoreItem], to id: UUID?) {\n'
  '        perform {\n'
  '            try withExtendedLifetime(items) {\n'
  '                try store.assign(orderedIDs: items.map(\\.id), to: id)\n'
  '            }\n'
  '        }\n'
  '    }\n'
  '\n'
  '    func addToStack(_ item: ClipboardItem, restoreItem: ClipboardRestoreItem? = nil) {\n'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    func addSelectionToStack() {\n',
  '    func contextMenuRestoreItems() -> [ClipboardRestoreItem] {\n'
  '        appliedRestoreItems()\n'
  '    }\n'
  '\n'
  '    func addSelectionToStack() {\n'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    func createPinboard(assignSelection: Bool = false) {\n',
  '    func createPinboard(assignSelection: Bool = false, selectionItems: [ClipboardRestoreItem]? '
  '= nil) {\n'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '        let ids = state.visibleItems.filter { state.selection.contains($0.id) }.map(\\.id)\n',
  '        let ids = selectionItems?.map(\\.id) ?? state.visibleItems.filter { '
  'state.selection.contains($0.id) }.map(\\.id)\n'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '            if assignSelection { try store.assign(orderedIDs: ids, to: board.id) }\n',
  '            if assignSelection {\n'
  '                try withExtendedLifetime(selectionItems) {\n'
  '                    try store.assign(orderedIDs: ids, to: board.id)\n'
  '                }\n'
  '            }\n'],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  '            Menu("添加到 Pasto") {\n'
  '                ForEach(state.store.pinboards) { board in\n'
  '                    Button(board.name) { state.assignSelection(to: board.id) }\n'
  '                }\n'
  '                Divider()\n'
  '                Button(OriginalSearchLocalization.text("pasto.action.create-group") + "…") { '
  'state.controller?.createPinboard(assignSelection: true) }\n'
  '            }\n',
  '            Menu("添加到 Pasto") {\n'
  '                let groupItems = state.controller?.contextMenuRestoreItems() ?? []\n'
  '                ForEach(state.store.pinboards) { board in\n'
  '                    Button(board.name) { state.assignItems(groupItems, to: board.id) }\n'
  '                }\n'
  '                Divider()\n'
  '                Button(OriginalSearchLocalization.text("pasto.action.create-group") + "…") {\n'
  '                    state.controller?.createPinboard(assignSelection: true, selectionItems: '
  'groupItems)\n'
  '                }\n'
  '            }\n']]

def pre_group_menu_input(source):
    source = pre_optional_selection(source)
    for path, previous, current in reversed(CHANGES):
        if current in source:
            assert source.count(current) == 1, path
            source = source.replace(current, previous, 1)
    return source

def pre_group_menu_input_bytes(path):
    path=Path(path)
    raw=path.read_bytes()
    return pre_group_menu_input(raw.decode()).encode() if path.suffix == '.swift' else raw
