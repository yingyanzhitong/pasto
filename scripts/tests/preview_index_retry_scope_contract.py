"""Exact native preview retry deltas for historical frozen contracts only."""
from pathlib import Path
from entity_lookup_scope_contract import pre_entity_lookup
CHANGES = [['replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift',
  '    func previewAnchor(for itemID: UUID, revealIfNeeded: Bool = true) -> NSView? {',
  '    // 06bb3c/06be48: keep the requested index across scrolling, then read the applier again.\n'
  '    func previewItem(at index: Int, present: @escaping (ClipboardRestoreItem, NSView) -> Void) {\n'
  '        guard let state, state.collectionOwner === self, window != nil else { return }\n'
  '        if items.indices.contains(index), let input = items[index].restoreItem(),\n'
  '           let anchor = visibleSelectionAnchor(at: index, itemID: items[index].id) {\n'
  '            present(input, anchor)\n'
  '            return\n'
  '        }\n'
  '        revealPrimaryCard(at: index, animated: true) { [weak self] success in\n'
  '            guard success else { return }\n'
  '            self?.previewItem(at: index, present: present)\n'
  '        }\n'
  '    }\n'
  '\n'
  '    func previewAnchor(for itemID: UUID, revealIfNeeded: Bool = true) -> NSView? {'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    func showPreview(item: ClipboardItem, input: ClipboardRestoreItem? = nil) {\n',
  '    private func previewSelection() {\n'
  '        guard let id = state.collectionSelectionSnapshot().orderedIDs.last else { return }\n'
  '        _ = showCollectionPreview(itemID: id)\n'
  '    }\n'
  '\n'
  '    @discardableResult\n'
  '    private func showCollectionPreview(itemID: UUID) -> Bool {\n'
  '        guard isPanelOrderedVisible, !isPanelClosing,\n'
  '              let replicaPanel = loadedPanel as? ReplicaPanel,\n'
  '              let collection = replicaPanel.collectionFocusTarget as? ReplicaNativeCollectionHost,\n'
  '              collection.window === replicaPanel,\n'
  '              let items = collection.appliedItems(for: state),\n'
  '              let index = items.firstIndex(where: { $0.id == itemID }) else { return false }\n'
  '        collection.previewItem(at: index) { [weak self] input, anchor in\n'
  '            guard let self else { return }\n'
  '            let popover = self.previewPopover ?? self.makePreviewPopover()\n'
  '            self.previewPopover = popover\n'
  '            if popover.isDisplayed {\n'
  '                popover.close()\n'
  '                return\n'
  '            }\n'
  '            popover.show(itemIdentity: AnyHashable(input.id), itemIdentifier: input.id.uuidString, input: '
  'input,\n'
  '                contentView: self.makePreviewContent(for: input), relativeTo: anchor)\n'
  '        }\n'
  '        return true\n'
  '    }\n'
  '\n'
  '    func showPreview(item: ClipboardItem, input: ClipboardRestoreItem? = nil) {\n'
  '        if showCollectionPreview(itemID: item.id) { return }\n'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '            if let input = appliedRestoreItems().last { showPreview(item: input.resolvedItem(), input: '
  'input) }',
  '            previewSelection()']]

def pre_preview_index_retry(source):
    source = pre_entity_lookup(source)
    for path, before, after in reversed(CHANGES):
        if after in source:
            assert source.count(after) == 1, path
            source = source.replace(after, before, 1)
    return source

def pre_preview_index_retry_bytes(path):
    data = Path(path).read_bytes()
    if str(path).endswith(".swift"):
        return pre_preview_index_retry(data.decode()).encode()
    return data
