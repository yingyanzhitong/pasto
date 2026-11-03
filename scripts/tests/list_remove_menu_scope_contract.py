"""Reverse only phase110 list remove-menu deltas in historical source checks."""
from pathlib import Path
from list_pin_menu_topology_scope_contract import pre_list_pin_menu_topology
CHANGES = [['replica/Sources/PastoCore/ClipboardRestoreItem.swift',
  '    public func previewSharingContent() -> OriginalPreviewSharing.Content? {',
  '    // 3ba390/3250f0: removal eligibility needs only the current native owner type.\n'
  '    public func hasNativePinboardOwner() -> Bool? {\n'
  '        guard let object = nativeObject else { return nil }\n'
  '        guard let owner = object.value(forKey: "list") as? NSManagedObject else { return false '
  '}\n'
  '        return (owner.value(forKey: "rawType") as? NSNumber)?.int64Value == 2\n'
  '    }\n'
  '\n'
  '    public func previewSharingContent() -> OriginalPreviewSharing.Content? {'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    // 09ee9c forwards the array captured when the group menu was built.',
  '    // 3ba2bc: history context, nonempty input, and at least one current type2 owner.\n'
  "    // Pasto's local unshared groups satisfy the original writable-owner predicate.\n"
  '    func canUnassignItems(_ items: [ClipboardRestoreItem]) -> Bool {\n'
  '        let hasPinboardOwner = items.contains { $0.hasNativePinboardOwner() ?? '
  '!$0.resolvedItem().pinboardIDs.isEmpty }\n'
  '        return pinboardID == nil && !showDeleted && !items.isEmpty && hasPinboardOwner\n'
  '    }\n'
  '\n'
  '    // 09ee9c forwards the array captured when the group menu was built.'],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  '        } else {\n            Button("拷贝")',
  '        } else {\n'
  '            let groupItems = state.controller?.contextMenuRestoreItems() ?? []\n'
  '            Button("拷贝")'],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  '            Menu("添加到 Pasto") {\n'
  '                let groupItems = state.controller?.contextMenuRestoreItems() ?? []',
  '            Menu("添加到 Pasto") {'],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  '            if !item.pinboardIDs.isEmpty {\n'
  '                if let board = state.pinboardID {\n'
  '                    Button("从此 Pasto 移除") {\n'
  '                        state.perform { try state.store.unassign(ids: state.selection, from: '
  'board) }\n'
  '                    }\n'
  '                }\n'
  '                Button("从所有 Pasto 移除") { state.assignSelection(to: nil) }\n'
  '            }',
  '            if !item.pinboardIDs.isEmpty, let board = state.pinboardID {\n'
  '                Button("从此 Pasto 移除") {\n'
  '                    state.perform { try state.store.unassign(ids: state.selection, from: board) '
  '}\n'
  '                }\n'
  '            }\n'
  '            if state.canUnassignItems(groupItems) {\n'
  '                Button("从所有 Pasto 移除") { state.assignItems(groupItems, to: nil) }\n'
  '            }']]

def pre_list_remove_menu(source):
    source=pre_list_pin_menu_topology(source)
    if not any(marker in source for marker in ["public func hasNativePinboardOwner()", "func canUnassignItems(", "if state.canUnassignItems(groupItems)"]): return source
    for _,old,new in reversed(CHANGES):
        if old.startswith(new) and old in source: continue
        if new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    return source
