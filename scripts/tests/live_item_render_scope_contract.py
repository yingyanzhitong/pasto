"""Compare earlier contracts outside phase74's explicit reference/render additions."""
from test_offline_p0_contracts import body
from pathlib import Path

REFERENCE_PATH = 'replica/Sources/PastoCore/ClipboardCollectionItemReference.swift'


def pre_live_render_bytes(path):
    path = Path(path)
    value = path.read_bytes()
    return pre_live_render(value.decode()).encode() if path.suffix == '.swift' else value


def remove_declaration(source, declaration, signature):
    start = source.index(declaration)
    value = body(source, signature)
    end = source.index(value, start) + len(value) + 2
    return source[:start] + source[end:]


def pre_live_render(source):
    from live_item_selection_scope_contract import pre_live_selection
    source = pre_live_selection(source)
    if 'public let itemReferences: [UUID: ClipboardCollectionItemReference]' in source:
        snapshot = body(source, 'public struct Snapshot: Equatable')
        prefix, sep, _ = snapshot.partition('        public let itemReferences:')
        assert sep and prefix == '{\n        public let identifiers: [UUID]\n        public let updatedIdentifiers: Set<UUID>\n'
        source = source.replace(snapshot, prefix + '    }', 1)
        start = source.index('        var references: [UUID: ClipboardCollectionItemReference] = [:]\n')
        end = source.index('        subject.send(', start)
        source = source[:start] + source[end:]
        new = '                              updatedIdentifiers: Set(value.updated.compactMap { keys[$0] }),\n                              itemReferences: references))'
        assert source.count(new) == 1
        source = source.replace(new, '                              updatedIdentifiers: Set(value.updated.compactMap { keys[$0] })))', 1)
    line = '    var resultItemReferences: [UUID: ClipboardCollectionItemReference] { resultSource?.value.itemReferences ?? [:] }\n'
    if line in source:
        source = source.replace(line, '', 1)
    if '    var collectionItemReferences:' in source:
        source = remove_declaration(source, '    var collectionItemReferences:', 'var collectionItemReferences:')
    if '    private func renderedItem(at index:' in source:
        source = remove_declaration(source, '    private func renderedItem(at index:', 'private func renderedItem(at index:')
        for line, count in [
            ('    private var itemReferences: [UUID: ClipboardCollectionItemReference] = [:]\n', 1),
            ('        let itemReferences: [UUID: ClipboardCollectionItemReference]\n', 1),
            ('            itemReferences = [:]\n', 1),
            ('        itemReferences = [:]\n', 2),
            ('            itemReferences = pending.itemReferences\n', 1)]:
            assert source.count(line) == count, (line, source.count(line))
            source = source.replace(line, '')
        source = source.replace('        let incomingItemReferences = state.collectionItemReferences\n', '', 1)
        source = source.replace('        if pendingSnapshot?.items != incomingItems || !changedIDs.isEmpty\n            || pendingSnapshot?.itemReferences != incomingItemReferences {',
                                '        if pendingSnapshot?.items != incomingItems || !changedIDs.isEmpty {', 1)
        new = '                changedIDs: (pendingSnapshot?.changedIDs ?? []).union(changedIDs),\n                itemReferences: incomingItemReferences)'
        assert source.count(new) == 1
        source = source.replace(new, '                changedIDs: (pendingSnapshot?.changedIDs ?? []).union(changedIDs))', 1)
        assert source.count('            let item = renderedItem(at: index)\n') == 1
        source = source.replace('            let item = renderedItem(at: index)\n', '            let item = items[index]\n', 1)
        source = source.replace('cell.update(state: state, item: renderedItem(at: index), side:',
                                'cell.update(state: state, item: items[index], side:', 1)
    return source
