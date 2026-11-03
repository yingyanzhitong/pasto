"""Reverse only thirteen reviewed137 live preview identifier/late URI hunks."""
CHANGES = [['replica/Sources/PastoCore/ClipboardRestoreItem.swift',
  '    public var isDeleted: Bool { nativeObject?.isDeleted ?? false }',
  '    // Registration/publication callbacks read the current native identifier, independent of '
  'URI identity.\n'
  '    public var previewIdentifier: String {\n'
  '        if let nativeObject, let identifier = nativeObject.value(forKey: "nativeIdentifier") '
  'as? String {\n'
  '            return identifier\n'
  '        }\n'
  '        return id.uuidString\n'
  '    }\n'
  '\n'
  '    public var isDeleted: Bool { nativeObject?.isDeleted ?? false }'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  'popover.show(itemIdentity: input.previewIdentity, itemIdentifier: input.id.uuidString, input: '
  'input,',
  'popover.show(itemIdentity: input.previewIdentity, itemIdentifier: input.previewIdentifier, '
  'input: input,'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  'popover.show(itemIdentity: input.previewIdentity, itemIdentifier: item.id.uuidString, input: '
  'input,\n'
  '                contentView: makePreviewContent(for: input), relativeTo: anchor)\n'
  '            return',
  'popover.show(itemIdentity: input.previewIdentity, itemIdentifier: input.previewIdentifier, '
  'input: input,\n'
  '                contentView: makePreviewContent(for: input), relativeTo: anchor)\n'
  '            return'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  'self?.previewRegistry.f_10008727c(isEditing: editing, itemIdentifier: item.id.uuidString)',
  'self?.previewRegistry.f_10008727c(isEditing: editing, itemIdentifier: input.previewIdentifier)'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '            itemIdentifier: item.id.uuidString, isEditing: false)',
  '            itemIdentifier: input.previewIdentifier, isEditing: false)'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '        let itemIdentifier = input.id.uuidString',
  '        let itemIdentifier = input.previewIdentifier'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  'registry.f_10008727c(isEditing: editing, itemIdentifier: itemIdentifier)',
  'registry.f_10008727c(isEditing: editing, itemIdentifier: input.previewIdentifier)'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  'popover.show(itemIdentity: input.previewIdentity, itemIdentifier: item.id.uuidString, input: '
  'input,\n'
  '                contentView: makePreviewContent(for: input), relativeTo: anchor)\n'
  '        }',
  'popover.show(itemIdentity: input.previewIdentity, itemIdentifier: input.previewIdentifier, '
  'input: input,\n'
  '                contentView: makePreviewContent(for: input), relativeTo: anchor)\n'
  '        }'],
 ['replica/Sources/PastoCore/OriginalPreviewPopover.swift',
  'self?.f_1000298b0(itemIdentity: itemIdentity)',
  'self?.f_1000298b0(itemIdentity: input.previewIdentity)'],
 ['replica/Sources/PastoCore/OriginalPreviewPopover.swift',
  '        if let itemIdentifier, registry.popoverItemIdentifier != itemIdentifier {\n'
  '            registry.popoverItemIdentifier = itemIdentifier\n'
  '            registry.f_100087864()\n'
  '        }',
  '        if let item {\n'
  '            let itemIdentifier = item.previewIdentifier\n'
  '            self.itemIdentifier = itemIdentifier\n'
  '            if registry.popoverItemIdentifier != itemIdentifier {\n'
  '                registry.popoverItemIdentifier = itemIdentifier\n'
  '                registry.f_100087864()\n'
  '            }\n'
  '        }'],
 ['replica/Sources/PastoCore/OriginalPreviewPopover.swift',
  'guard let itemIdentity, let itemIdentifier, let item else { return nil }',
  'guard let item else { return nil }'],
 ['replica/Sources/PastoCore/OriginalPreviewPopover.swift',
  'manager.f_10008727c(isEditing: editing, itemIdentifier: itemIdentifier)',
  'manager.f_10008727c(isEditing: editing, itemIdentifier: item.previewIdentifier)'],
 ['replica/Sources/PastoCore/OriginalPreviewPopover.swift',
  '        manager.f_100086c10(window: window, itemIdentity: itemIdentity,\n'
  '                           itemIdentifier: itemIdentifier, isEditing: beginEditing)',
  '        manager.f_100086c10(window: window, itemIdentity: item.previewIdentity,\n'
  '                           itemIdentifier: item.previewIdentifier, isEditing: beginEditing)']]

def pre_live_preview_identifier(source):
    from native_link_creation_scope_contract import pre_native_link_creation
    source=pre_native_link_creation(source)
    for _,old,new in reversed(CHANGES):
        if new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    return source
