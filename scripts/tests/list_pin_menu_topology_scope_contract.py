"""Reverse only phase111 list pin-menu topology, preserving historical evidence."""
from native_group_creation_result_scope_contract import pre_native_group_creation_result
CHANGES = [['replica/Sources/Pasto/UI/PanelViews.swift',
  '                Button(OriginalSearchLocalization.text("pasto.action.create-group") + "…") {\n'
  '                    state.controller?.createPinboard(assignSelection: true, selectionItems: '
  'groupItems)\n'
  '                }\n'
  '            }\n'
  '            if !item.pinboardIDs.isEmpty, let board = state.pinboardID {\n'
  '                Button("从此 Pasto 移除") {\n'
  '                    state.perform { try state.store.unassign(ids: state.selection, from: board) '
  '}\n'
  '                }\n'
  '            }\n'
  '            if state.canUnassignItems(groupItems) {\n'
  '                Button("从所有 Pasto 移除") { state.assignItems(groupItems, to: nil) }\n'
  '            }',
  '                Button(OriginalSearchLocalization.text("pasto.action.create-group") + "…") {\n'
  '                    state.controller?.createPinboard(assignSelection: true, selectionItems: '
  'groupItems)\n'
  '                }\n'
  '                if state.canUnassignItems(groupItems) {\n'
  '                    Button(String(localized: OriginalPreviewLocalization.f_1001c4208())) {\n'
  '                        state.assignItems(groupItems, to: nil)\n'
  '                    }\n'
  '                }\n'
  '            }']]

def pre_list_pin_menu_topology(source):
    source=pre_native_group_creation_result(source)
    for _,old,new in reversed(CHANGES):
        if new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    return source
