"""Reverse only the reviewed135 supplied-preview-input route guard."""
CHANGES = [['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '        if showCollectionPreview(itemID: item.id) { return }',
  '        if case nil = input, showCollectionPreview(itemID: item.id) { return }']]

def pre_supplied_preview_input(source):
    from native_preview_identity_scope_contract import pre_native_preview_identity
    source=pre_native_preview_identity(source)
    for _,old,new in reversed(CHANGES):
        if new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    return source
