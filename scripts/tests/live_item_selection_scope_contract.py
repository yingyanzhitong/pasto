"""Explicit phase75 selected-value delta for frozen earlier contracts."""
from pathlib import Path
from test_offline_p0_contracts import body


def pre_live_selection(source):
    from resolved_copy_scope_contract import pre_resolved_copy
    source = pre_resolved_copy(source)
    declaration = '    func appliedSelectedItems(for state: ReplicaUIState, orderedIDs: [UUID])'
    if declaration in source:
        start = source.index(declaration)
        method = body(source, 'func appliedSelectedItems(for state:')
        end = source.index(method, start) + len(method) + 2
        source = source[:start] + source[end:]
        assert source.count('let selected = indexes.map { renderedItem(at: $0) }') == 1
        source = source.replace('let selected = indexes.map { renderedItem(at: $0) }',
                                'let selected = indexes.map { applied[$0] }', 1)
    if 'let ids = orderedSelectionIDs.filter { selection.contains($0) }' in source:
        selected = body(source, 'var selectedItems:')
        assert 'collectionOwner.appliedSelectedItems(for: self, orderedIDs: ids) ?? []' in selected
        assert 'references[identifier]?.requiredItem() ?? item' in selected
        old = '''{
        let byID = Dictionary(uniqueKeysWithValues: visibleItems.map { ($0.id, $0) })
        return orderedSelectionIDs.compactMap { selection.contains($0) ? byID[$0] : nil }
    }'''
        source = source.replace(selected, old, 1)
        applied = body(source, 'private func appliedSelectionItems()')
        assert 'collection.window === panel else { return [] }' in applied
        assert 'collection.appliedSelectedItems(for: state,' in applied
        old = '''{
        let byID = Dictionary(uniqueKeysWithValues: (appliedCollectionItems() ?? []).map { ($0.id, $0) })
        return state.collectionSelectionSnapshot().orderedIDs.compactMap { byID[$0] }
    }'''
        source = source.replace(applied, old, 1)
    return source


def pre_live_selection_bytes(path):
    path = Path(path)
    value = path.read_bytes()
    return pre_live_selection(value.decode()).encode() if path.suffix == '.swift' else value
