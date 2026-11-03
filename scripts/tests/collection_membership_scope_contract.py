"""The explicit phase79 identity/reference membership delta for earlier frozen contracts.

Actual current membership, item/restore consumers and ID-only selection paths are
checked from raw production in test_p1_repair_reference_membership. Historical
contracts remove only these reviewed literal bodies/signatures/call-site changes.
"""
from pathlib import Path
from supplied_input_scope_contract import pre_supplied_input_adapters

ENTRY_PATH = 'replica/Sources/PastoCore/ClipboardCollectionEntry.swift'

CHANGES = [('replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '',
  '    private func collectionEntries(identifiers: [UUID], references: [UUID: '
  'ClipboardCollectionItemReference]) -> [ClipboardCollectionEntry] {\n'
  '        // Imported legacy trash is a local compatibility case; cached payload availability is not '
  'membership.\n'
  '        let deleted = Set(store.items.filter(\\.isDeleted).map(\\.id))\n'
  '        return identifiers.filter { !deleted.contains($0) }.map { identifier in\n'
  '            guard let reference = references[identifier] else { fatalError("Missing collection item '
  'reference") }\n'
  '            return ClipboardCollectionEntry(id: identifier, reference: reference)\n'
  '        }\n'
  '    }\n'
  '\n'),
 ('replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '',
  '    @discardableResult\n'
  '    func paste(itemID: UUID, plainTextOnly: Bool) -> Bool {\n'
  '        if let input = appliedRestoreItems(orderedIDs: [itemID]).first {\n'
  '            return paste(restoreItems: [input], plainTextOnly: plainTextOnly)\n'
  '        }\n'
  '        return paste(ids: [itemID], plainTextOnly: plainTextOnly)\n'
  '    }\n'
  '\n'),
 ('replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '{\n'
  '        if isCollectionSearchQueryEmpty {\n'
  '            if showDeleted {\n'
  '                return store.search(query: "", pinboardID: pinboardID, includeDeleted: '
  'true).filter(\\.isDeleted)\n'
  '            }\n'
  '            let items = Dictionary(uniqueKeysWithValues: store.items.map { ($0.id, $0) })\n'
  '            let identifiers = listCollection?.value.identifiers ?? []\n'
  '            let native = identifiers.compactMap { items[$0] }.filter { !$0.isDeleted }\n'
  '            if let pinboardID {\n'
  '                // Older local archives can retain secondary memberships beyond the native single owner.\n'
  '                let legacy = store.items(in: pinboardID).filter { $0.pinboardOwnerID != pinboardID }\n'
  '                if !legacy.isEmpty {\n'
  '                    let retained = Set(identifiers).union(legacy.map(\\.id))\n'
  '                    return store.items(in: pinboardID).filter { retained.contains($0.id) }\n'
  '                }\n'
  '            }\n'
  '            return native\n'
  '        }\n'
  '        let items = Dictionary(uniqueKeysWithValues: store.items.map { ($0.id, $0) })\n'
  '        return searchIndex.orderedIdentifiers.compactMap { identifier in\n'
  '            guard let item = items[identifier], showDeleted ? item.isDeleted : !item.isDeleted else { '
  'return nil }\n'
  '            return item\n'
  '        }\n'
  '    }',
  '{\n'
  '        if isCollectionSearchQueryEmpty {\n'
  '            if showDeleted {\n'
  '                return store.search(query: "", pinboardID: pinboardID, includeDeleted: true)\n'
  '                    .filter(\\.isDeleted).map { ClipboardCollectionEntry(item: $0) }\n'
  '            }\n'
  '            let snapshot = listCollection?.value\n'
  '            let native = collectionEntries(identifiers: snapshot?.identifiers ?? [],\n'
  '                references: snapshot?.itemReferences ?? [:])\n'
  '            if let pinboardID {\n'
  '                // Preserve old local archives with secondary memberships outside the native single '
  'owner.\n'
  '                let archived = store.items(in: pinboardID)\n'
  '                let legacy = archived.filter { $0.pinboardOwnerID != pinboardID }\n'
  '                if !legacy.isEmpty {\n'
  '                    let byID = Dictionary(uniqueKeysWithValues: native.map { ($0.id, $0) })\n'
  '                    let retained = Set(native.map(\\.id)).union(legacy.map(\\.id))\n'
  '                    let merged = archived.filter { retained.contains($0.id) }.map {\n'
  '                        byID[$0.id] ?? ClipboardCollectionEntry(item: $0)\n'
  '                    }\n'
  '                    let included = Set(merged.map(\\.id))\n'
  '                    return merged + native.filter { !included.contains($0.id) }\n'
  '                }\n'
  '            }\n'
  '            return native\n'
  '        }\n'
  '        if showDeleted {\n'
  '            let archived = Dictionary(uniqueKeysWithValues: store.items.map { ($0.id, $0) })\n'
  '            return searchIndex.orderedIdentifiers.compactMap { identifier in\n'
  '                guard let item = archived[identifier], item.isDeleted else { return nil }\n'
  '                return ClipboardCollectionEntry(item: item)\n'
  '            }\n'
  '        }\n'
  '        return collectionEntries(identifiers: searchIndex.orderedIdentifiers,\n'
  '            references: searchIndex.resultItemReferences)\n'
  '    }'),
 ('replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '{\n'
  '        let ids = orderedSelectionIDs.filter { selection.contains($0) }\n'
  '        if let collectionOwner { return collectionOwner.appliedSelectedItems(for: self, orderedIDs: ids) '
  '?? [] }\n'
  '        let byID = Dictionary(uniqueKeysWithValues: visibleItems.map { ($0.id, $0) })\n'
  '        let references = collectionItemReferences\n'
  '        return ids.compactMap { identifier in\n'
  '            guard let item = byID[identifier] else { return nil }\n'
  '            return references[identifier]?.requiredItem() ?? item\n'
  '        }\n'
  '    }',
  '{\n'
  '        let ids = orderedSelectionIDs.filter { selection.contains($0) }\n'
  '        if let collectionOwner { return collectionOwner.appliedSelectedItems(for: self, orderedIDs: ids) '
  '?? [] }\n'
  '        let byID = Dictionary(uniqueKeysWithValues: visibleItems.map { ($0.id, $0) })\n'
  '        return ids.compactMap { byID[$0]?.requiredItem() }\n'
  '    }'),
 ('replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '{\n        visibleItems.first { $0.id == primaryID } ?? selectedItems.first ?? visibleItems.first\n    }',
  '{\n'
  '        let items = pointerSelectionItems\n'
  '        return items.first { $0.id == primaryID }?.requiredItem()\n'
  '            ?? selectedItems.first ?? items.first?.requiredItem()\n'
  '    }'),
 ('replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '{\n'
  '        if let input = appliedRestoreItems(orderedIDs: [item.id]).first {\n'
  '            return paste(restoreItems: [input], plainTextOnly: plainTextOnly)\n'
  '        }\n'
  '        return paste(ids: [item.id], plainTextOnly: plainTextOnly)\n'
  '    }',
  '{\n        paste(itemID: item.id, plainTextOnly: plainTextOnly)\n    }'),
 ('replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    var visibleItems: [ClipboardItem] {\n',
  '    var visibleItems: [ClipboardCollectionEntry] {\n'),
 ('replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    func selectFirstAppliedItem(items: [ClipboardItem]) {\n',
  '    func selectFirstAppliedItem(items: [ClipboardCollectionEntry]) {\n'),
 ('replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    func selectAppliedItem(at index: Int, items: [ClipboardItem]) {\n',
  '    func selectAppliedItem(at index: Int, items: [ClipboardCollectionEntry]) {\n'),
 ('replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    func applyFullCollectionReload(items: [ClipboardItem]) {\n',
  '    func applyFullCollectionReload(items: [ClipboardCollectionEntry]) {\n'),
 ('replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    func applyIncrementalCollectionSnapshot(items: [ClipboardItem]) {\n',
  '    func applyIncrementalCollectionSnapshot(items: [ClipboardCollectionEntry]) {\n'),
 ('replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    private func selectIndex(_ index: Int, mode: UInt8, items: [ClipboardItem], animated: Bool = true) '
  '{\n',
  '    private func selectIndex(_ index: Int, mode: UInt8, items: [ClipboardCollectionEntry], animated: Bool '
  '= true) {\n'),
 ('replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    private var pointerSelectionItems: [ClipboardItem] {\n',
  '    private var pointerSelectionItems: [ClipboardCollectionEntry] {\n'),
 ('replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    func consumePendingNeighborSelection(token: UUID, items: [ClipboardItem]) {\n',
  '    func consumePendingNeighborSelection(token: UUID, items: [ClipboardCollectionEntry]) {\n'),
 ('replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    private func appliedCollectionItems() -> [ClipboardItem]? {\n',
  '    private func appliedCollectionItems() -> [ClipboardCollectionEntry]? {\n'),
 ('replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '                paste(item: items[action.index], plainTextOnly: '
  'action.options.contains(.plainTextAndLinks))\n',
  '                paste(itemID: items[action.index].id, plainTextOnly: '
  'action.options.contains(.plainTextAndLinks))\n'),
 ('replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift',
  '{\n'
  '        guard self.state === state, state.collectionOwner === self else { return nil }\n'
  '        let positions = Dictionary(uniqueKeysWithValues: items.enumerated().map { ($0.element.id, '
  '$0.offset) })\n'
  '        return orderedIDs.compactMap { identifier in\n'
  '            guard let index = positions[identifier] else { return nil }\n'
  '            let item = items[index]\n'
  '            return itemReferences[identifier]?.requiredRestoreItem(id: identifier) ?? '
  'ClipboardRestoreItem(item: item)\n'
  '        }\n'
  '    }',
  '{\n'
  '        guard self.state === state, state.collectionOwner === self else { return nil }\n'
  '        let positions = Dictionary(uniqueKeysWithValues: items.enumerated().map { ($0.element.id, '
  '$0.offset) })\n'
  '        return orderedIDs.compactMap { identifier in\n'
  '            guard let index = positions[identifier] else { return nil }\n'
  '            return items[index].requiredRestoreItem()\n'
  '        }\n'
  '    }'),
 ('replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift',
  '{\n        let item = items[index]\n        return itemReferences[item.id]?.requiredItem() ?? item\n    }',
  '{\n        items[index].requiredItem()\n    }'),
 ('replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift',
  '    private var items: [ClipboardItem] = []\n',
  '    private var items: [ClipboardCollectionEntry] = []\n'),
 ('replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift',
  '        let items: [ClipboardItem]\n',
  '        let items: [ClipboardCollectionEntry]\n'),
 ('replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift',
  '    func appliedItems(for state: ReplicaUIState) -> [ClipboardItem]? {\n',
  '    func appliedItems(for state: ReplicaUIState) -> [ClipboardCollectionEntry]? {\n'),
 ('replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift',
  '        state.select(current[index], modifiers: modifiers)\n',
  '        state.select(renderedItem(at: index), modifiers: modifiers)\n'),
 ('replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift',
  '                state.controller?.paste(item: current[index], plainTextOnly: '
  'event.modifierFlags.isSuperset(of: plain))\n',
  '                state.controller?.paste(itemID: current[index].id, plainTextOnly: '
  'event.modifierFlags.isSuperset(of: plain))\n')]

def pre_collection_membership(source):
    source = pre_supplied_input_adapters(source)
    for path, previous, current in CHANGES:
        if current in source:
            assert source.count(current) == 1, path
            source = source.replace(current, previous, 1)
    return source


def pre_collection_membership_bytes(path):
    path = Path(path)
    value = path.read_bytes()
    return pre_collection_membership(value.decode()).encode() if path.suffix == '.swift' else value
