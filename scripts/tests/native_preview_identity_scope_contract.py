"""Reverse only seven reviewed136 preview object-URI identity hunks."""
CHANGES = [['replica/Sources/PastoCore/ClipboardRestoreItem.swift',
  '    public var isDeleted: Bool { nativeObject?.isDeleted ?? false }',
  "    // 3541f4 → URIRepresentation: window lookup/registration use the managed object's URL "
  'identity.\n'
  '    public var previewIdentity: AnyHashable {\n'
  '        if let nativeObject { return AnyHashable(nativeObject.objectID.uriRepresentation()) }\n'
  '        return AnyHashable(id)\n'
  '    }\n'
  '\n'
  '    public var isDeleted: Bool { nativeObject?.isDeleted ?? false }'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  'popover.show(itemIdentity: AnyHashable(input.id), itemIdentifier: input.id.uuidString, input: '
  'input,',
  'popover.show(itemIdentity: input.previewIdentity, itemIdentifier: input.id.uuidString, input: '
  'input,'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '        if let existing = previewRegistry.f_10008747c(itemIdentity: AnyHashable(item.id)) {\n'
  '            show(existing)\n'
  '            return\n'
  '        }\n'
  '        let input = input ?? appliedRestoreItems(orderedIDs: [item.id]).first\n'
  '            ?? state.stackRestoreItem(for: item.id) ?? ClipboardRestoreItem(item: item)',
  '        let input = input ?? appliedRestoreItems(orderedIDs: [item.id]).first\n'
  '            ?? state.stackRestoreItem(for: item.id) ?? ClipboardRestoreItem(item: item)\n'
  '        if let existing = previewRegistry.f_10008747c(itemIdentity: input.previewIdentity) {\n'
  '            show(existing)\n'
  '            return\n'
  '        }'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  'popover.show(itemIdentity: AnyHashable(item.id), itemIdentifier: item.id.uuidString, input: '
  'input,\n'
  '                contentView: makePreviewContent(for: input), relativeTo: anchor)\n'
  '            return',
  'popover.show(itemIdentity: input.previewIdentity, itemIdentifier: item.id.uuidString, input: '
  'input,\n'
  '                contentView: makePreviewContent(for: input), relativeTo: anchor)\n'
  '            return'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  'popover.show(itemIdentity: AnyHashable(item.id), itemIdentifier: item.id.uuidString, input: '
  'input,\n'
  '                contentView: makePreviewContent(for: input), relativeTo: anchor)\n'
  '        }',
  'popover.show(itemIdentity: input.previewIdentity, itemIdentifier: item.id.uuidString, input: '
  'input,\n'
  '                contentView: makePreviewContent(for: input), relativeTo: anchor)\n'
  '        }'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  'previewRegistry.f_100086c10(window: window, itemIdentity: AnyHashable(item.id),',
  'previewRegistry.f_100086c10(window: window, itemIdentity: input.previewIdentity,'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  'registry.f_100086c10(window: window, itemIdentity: AnyHashable(input.id),',
  'registry.f_100086c10(window: window, itemIdentity: input.previewIdentity,']]

def pre_native_preview_identity(source):
    from live_preview_identifier_scope_contract import pre_live_preview_identifier
    source=pre_live_preview_identifier(source)
    for _,old,new in reversed(CHANGES):
        if new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    return source
