"""Five reviewed optional-selected-input deltas for earlier frozen contracts."""
from pathlib import Path
from single_item_restore_scope_contract import pre_single_item_restore

CHANGES = [['replica/Sources/PastoCore/ClipboardCollectionItemReference.swift',
  '    @MainActor public func requiredRestoreItem(id: UUID) -> ClipboardRestoreItem {\n',
  '    // 06e1f8 -> 1b9698 uses the optional ID lookup, unlike required indexed access.\n'
  '    @MainActor public func restoreItem(id: UUID) -> ClipboardRestoreItem? {\n'
  '        guard let object = (try? context.existingObject(with: objectID)) as? PastoItemEntity '
  'else { return nil }\n'
  '        return ClipboardRestoreItem(id: id, object: object)\n'
  '    }\n'
  '\n'
  '    @MainActor public func requiredRestoreItem(id: UUID) -> ClipboardRestoreItem {\n'],
 ['replica/Sources/PastoCore/ClipboardCollectionEntry.swift',
  '    @MainActor public func requiredItem() -> ClipboardItem {\n',
  '    @MainActor public func item() -> ClipboardItem? {\n'
  '        if let reference { return reference.item() }\n'
  '        return legacyItem\n'
  '    }\n'
  '\n'
  '    @MainActor public func restoreItem() -> ClipboardRestoreItem? {\n'
  '        if let reference { return reference.restoreItem(id: id) }\n'
  '        guard let legacyItem else { return nil }\n'
  '        return ClipboardRestoreItem(item: legacyItem)\n'
  '    }\n'
  '\n'
  '    @MainActor public func requiredItem() -> ClipboardItem {\n'],
 ['replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift',
  '    func appliedSelectedItems(for state: ReplicaUIState, orderedIDs: [UUID]) -> '
  '[ClipboardItem]? {\n'
  '        guard self.state === state, state.collectionOwner === self else { return nil }\n'
  '        let positions = Dictionary(uniqueKeysWithValues: items.enumerated().map { '
  '($0.element.id, $0.offset) })\n'
  '        return orderedIDs.compactMap { identifier in\n'
  '            guard let index = positions[identifier] else { return nil }\n'
  '            return renderedItem(at: index)\n'
  '        }\n'
  '    }\n',
  '    func appliedSelectedItems(for state: ReplicaUIState, orderedIDs: [UUID]) -> '
  '[ClipboardItem]? {\n'
  '        guard self.state === state, state.collectionOwner === self else { return nil }\n'
  '        let positions = Dictionary(uniqueKeysWithValues: items.enumerated().map { '
  '($0.element.id, $0.offset) })\n'
  '        return orderedIDs.compactMap { identifier in\n'
  '            guard let index = positions[identifier] else { return nil }\n'
  '            return items[index].item()\n'
  '        }\n'
  '    }\n'],
 ['replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift',
  '            return items[index].requiredRestoreItem()\n',
  '            return items[index].restoreItem()\n'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '        return ids.compactMap { byID[$0]?.requiredItem() }\n',
  '        return ids.compactMap { byID[$0]?.item() }\n']]

def pre_optional_selection(source):
    source = pre_single_item_restore(source)
    for path, previous, current in reversed(CHANGES):
        if current in source:
            assert source.count(current) == 1, path
            source = source.replace(current, previous, 1)
    return source

def pre_optional_selection_bytes(path):
    path=Path(path)
    raw=path.read_bytes()
    return pre_optional_selection(raw.decode()).encode() if path.suffix == '.swift' else raw
