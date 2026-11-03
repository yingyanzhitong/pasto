"""One reviewed native/legacy single-item method pair, for earlier frozen source checks."""
from pathlib import Path
from native_title_scope_contract import pre_native_title

CHANGES = [['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    @discardableResult\n'
  '    func paste(item: ClipboardItem, plainTextOnly: Bool) -> Bool {\n'
  '        paste(itemID: item.id, plainTextOnly: plainTextOnly)\n'
  '    }\n'
  '\n'
  '    @discardableResult\n'
  '    func paste(itemID: UUID, plainTextOnly: Bool) -> Bool {\n'
  '        if let input = appliedRestoreItems(orderedIDs: [itemID]).first {\n'
  '            return paste(restoreItems: [input], plainTextOnly: plainTextOnly)\n'
  '        }\n'
  '        return paste(ids: [itemID], plainTextOnly: plainTextOnly)\n'
  '    }\n',
  '    @discardableResult\n'
  '    func paste(item: ClipboardItem, plainTextOnly: Bool) -> Bool {\n'
  '        // Value-based legacy views retain their ID writer compatibility path.\n'
  '        if let input = appliedRestoreItems(orderedIDs: [item.id]).first {\n'
  '            return paste(restoreItems: [input], plainTextOnly: plainTextOnly)\n'
  '        }\n'
  '        return paste(ids: [item.id], plainTextOnly: plainTextOnly)\n'
  '    }\n'
  '\n'
  '    @discardableResult\n'
  '    func paste(itemID: UUID, plainTextOnly: Bool) -> Bool {\n'
  '        // 075a6c/06c60c use only the optional applied-item lookup.\n'
  '        guard let input = appliedRestoreItems(orderedIDs: [itemID]).first else { return false '
  '}\n'
  '        return paste(restoreItems: [input], plainTextOnly: plainTextOnly)\n'
  '    }\n']]

def pre_single_item_restore(source):
    source = pre_native_title(source)
    for path, previous, current in reversed(CHANGES):
        if current in source:
            assert source.count(current) == 1, path
            source=source.replace(current,previous,1)
    return source

def pre_single_item_restore_bytes(path):
    path=Path(path)
    raw=path.read_bytes()
    return pre_single_item_restore(raw.decode()).encode() if path.suffix == '.swift' else raw
