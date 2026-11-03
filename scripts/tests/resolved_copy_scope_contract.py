"""The explicit resolved-copy input delta, for earlier frozen writer/UI contracts."""
from pathlib import Path
from modal_restore_scope_contract import pre_modal_restore
from test_offline_p0_contracts import body


def pre_resolved_copy(source):
    source = pre_modal_restore(source)
    declaration = '    public func writeToPasteboard(selectedItems:'
    if declaration in source:
        start = source.index(declaration);value = body(source, 'public func writeToPasteboard(selectedItems:')
        end = source.index(value, start) + len(value) + 2
        source = source[:start] + source[end:]
        new = 'options: OriginalPasteboardRestore.Options, recognizedImageData: Data?,\n                                   resolvedSelection: [ClipboardItem]? = nil) throws'
        assert source.count(new) == 1
        source = source.replace(new, 'options: OriginalPasteboardRestore.Options, recognizedImageData: Data?) throws', 1)
        start = source.index('        let selected: [ClipboardItem]\n')
        end = source.index('        let selections = try selected.map', start)
        actual = source[start:end]
        assert 'if let resolvedSelection' in actual and 'selected = try ids.map' in actual
        old = '''        // Refresh selection inputs without an extra pre-writer save; the restore transaction saves once below.
        try reload()
        let selected = try ids.map { id -> ClipboardItem in
            guard let item = items.first(where: { $0.id == id && !$0.isDeleted }) else { throw ClipboardStoreError.itemNotFound }
            return item
        }
'''
        source = source[:start] + old + source[end:]
    if 'store.writeToPasteboard(selectedItems: items,' in source:
        value = body(source, 'func copySelection(plainTextOnly:')
        assert 'guard !items.isEmpty else { NSSound.beep(); return }' in value and 'performCopy {' in value
        old = '''{
        let items = appliedSelectionItems()
        guard !items.isEmpty else { NSSound.beep(); return }
        copy(ids: items.map(\\.id), plainTextOnly: plainTextOnly)
    }'''
        source = source.replace(value, old, 1)
    return source


def pre_resolved_copy_bytes(path):
    path = Path(path);value = path.read_bytes()
    return pre_resolved_copy(value.decode()).encode() if path.suffix == '.swift' else value
