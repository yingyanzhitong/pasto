"""Exact native popover input deltas for historical frozen source contracts only."""
from pathlib import Path
from preview_index_retry_scope_contract import pre_preview_index_retry
CHANGES = [['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    func showPreview(item: ClipboardItem) {',
  '    func showPreview(item: ClipboardItem, input: ClipboardRestoreItem? = nil) {'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '            show(existing)\n            return\n        }\n        let anchor: NSView?\n',
  '            show(existing)\n'
  '            return\n'
  '        }\n'
  '        let input = input ?? appliedRestoreItems(orderedIDs: [item.id]).first\n'
  '            ?? state.stackRestoreItem(for: item.id) ?? ClipboardRestoreItem(item: item)\n'
  '        let anchor: NSView?\n'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '            popover.show(itemIdentity: AnyHashable(item.id), itemIdentifier: item.id.uuidString,\n'
  '                contentView: makePreviewContent(for: item), relativeTo: anchor)\n'
  '            return\n',
  '            popover.show(itemIdentity: AnyHashable(item.id), itemIdentifier: item.id.uuidString, input: '
  'input,\n'
  '                contentView: makePreviewContent(for: input), relativeTo: anchor)\n'
  '            return\n'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '        let content = makePreviewContent(for: item)\n',
  '        let content = makePreviewContent(for: input)\n'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '        guard let items = collection.appliedItems(for: state), items.indices.contains(requestedIndex),\n'
  '              let anchor = collection.visibleSelectionAnchor',
  '        guard let items = collection.appliedItems(for: state), items.indices.contains(requestedIndex),\n'
  '              let input = items[requestedIndex].restoreItem(),\n'
  '              let anchor = collection.visibleSelectionAnchor'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '            popover.show(itemIdentity: AnyHashable(item.id), itemIdentifier: item.id.uuidString,\n'
  '                contentView: makePreviewContent(for: item), relativeTo: anchor)\n'
  '        }\n',
  '            popover.show(itemIdentity: AnyHashable(item.id), itemIdentifier: item.id.uuidString, input: '
  'input,\n'
  '                contentView: makePreviewContent(for: input), relativeTo: anchor)\n'
  '        }\n'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    private func makePreviewContent(for item: ClipboardItem) -> NSView {\n'
  '        makeOriginalReplicaPreview(state: state, item: item)\n'
  '    }\n',
  '    private func makePreviewContent(for input: ClipboardRestoreItem) -> NSView {\n'
  '        makeOriginalReplicaPreview(state: state, item: input.resolvedItem(), input: input)\n'
  '    }\n'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '        popover.makeContentView = { [weak self] _, identifier in\n'
  '            guard let self, let item = self.store.items.first(where: { $0.id.uuidString == identifier }) '
  'else { return nil }\n'
  '            return makeOriginalReplicaPreview(state: self.state, item: item)\n'
  '        }\n',
  '        popover.makeContentView = { [weak self] input in\n'
  '            guard let self else { return nil }\n'
  '            return makeOriginalReplicaPreview(state: self.state, item: input.resolvedItem(), input: '
  'input)\n'
  '        }\n'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '            if let item = appliedSelectionItems().last { showPreview(item: item) }',
  '            if let input = appliedRestoreItems().last { showPreview(item: input.resolvedItem(), input: '
  'input) }'],
 ['replica/Sources/PastoCore/OriginalPreviewPopover.swift',
  '    public var makeContentView: ((_ itemIdentity: AnyHashable,\n'
  '                                  _ itemIdentifier: String) -> OriginalItemPreviewView?)?\n',
  '    public var makeContentView: ((_ input: ClipboardRestoreItem) -> OriginalItemPreviewView?)?\n'
  '    private var item: ClipboardRestoreItem?\n'],
 ['replica/Sources/PastoCore/OriginalPreviewPopover.swift',
  '    public func show(itemIdentity: AnyHashable, itemIdentifier: String,\n'
  '                     contentView: NSView, relativeTo anchor: NSView) {\n'
  '        self.itemIdentity = itemIdentity\n'
  '        self.itemIdentifier = itemIdentifier\n',
  '    public func show(itemIdentity: AnyHashable, itemIdentifier: String, input: ClipboardRestoreItem,\n'
  '                     contentView: NSView, relativeTo anchor: NSView) {\n'
  '        self.itemIdentity = itemIdentity\n'
  '        self.itemIdentifier = itemIdentifier\n'
  '        item = input\n'],
 ['replica/Sources/PastoCore/OriginalPreviewPopover.swift',
  '        guard let itemIdentity, let itemIdentifier else { return nil }\n',
  '        guard let itemIdentity, let itemIdentifier, let item else { return nil }\n'],
 ['replica/Sources/PastoCore/OriginalPreviewPopover.swift',
  '        guard let preview = makeContentView?(itemIdentity, itemIdentifier) else { return nil }\n',
  '        guard let preview = makeContentView?(item) else { return nil }\n'],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  '            Button("预览") { state.controller?.showPreview(item: item) }',
  '            Button("预览") { state.controller?.showPreview(item: item, input: titleInput) }'],
 ['replica/Sources/Pasto/UI/AuxiliaryViews.swift',
  '                    Button("预览") { state.controller?.showPreview(item: item) }',
  '                    Button("预览") { state.controller?.showPreview(item: item, input: '
  'state.stackRestoreItem(for: item.id)) }']]

def pre_popover_entity_input(source):
    source = pre_preview_index_retry(source)
    for path, before, after in reversed(CHANGES):
        if after in source:
            assert source.count(after) == 1, path
            source = source.replace(after, before, 1)
    return source

def pre_popover_entity_input_bytes(path):
    data = Path(path).read_bytes()
    if str(path).endswith(".swift"):
        return pre_popover_entity_input(data.decode()).encode()
    return data
