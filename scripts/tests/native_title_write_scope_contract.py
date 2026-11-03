"""Exact title preflight/native target deltas for prior frozen source checks only."""
from pathlib import Path
from card_title_input_scope_contract import pre_card_title_input
CHANGES = [['replica/Sources/PastoCore/OriginalPreviewTitles.swift',
  '    public static func f_100308f88(_ title: String?, defaultTitle: @autoclosure () -> String) '
  '-> String {\n',
  '    // Compare the displayed title first; re-read the optional field only for an empty trimmed '
  'input.\n'
  '    public static func f_1003bae08(_ title: String, originalTitle: @autoclosure () -> String?,\n'
  '                                  defaultTitle: @autoclosure () -> String,\n'
  '                                  update: (String?) throws -> Void) rethrows {\n'
  '        let displayedTitle = f_100308f88(originalTitle(), defaultTitle: defaultTitle())\n'
  '        guard title != displayedTitle else { return }\n'
  '        let normalized = title.trimmingCharacters(in: .whitespacesAndNewlines)\n'
  '        try update(normalized.isEmpty && originalTitle() != nil ? nil : normalized)\n'
  '    }\n'
  '\n'
  '    public static func f_100308f88(_ title: String?, defaultTitle: @autoclosure () -> String) '
  '-> String {\n'],
 ['replica/Sources/PastoCore/ClipboardStore.swift',
  '    public func updateItem(id: UUID, title: String? = nil, text: String? = nil) throws {\n',
  '    public func updateItem(_ input: ClipboardRestoreItem, title: String) throws {\n'
  '        guard let object = input.nativeObject else {\n'
  '            try updateItem(id: input.id, title: title, text: nil)\n'
  '            return\n'
  '        }\n'
  '        try OriginalPreviewTitles.f_1003bae08(title,\n'
  '            originalTitle: object.value(forKey: "title") as? String,\n'
  '            defaultTitle: OriginalPreviewTitles.f_100309008(\n'
  '                rawType: Int((object.value(forKey: "rawType") as? NSNumber)?.int64Value ?? 0),\n'
  '                fileCount: OriginalImagePreviewMetadataCodec.decodeFiles(object.value(forKey: '
  '"rawPreview") as? Data)?.paths.count)) { replacement in\n'
  '            try mutateInTransaction { state, _ in\n'
  '                var item = input.resolvedItem()\n'
  '                item.title = replacement ?? ""\n'
  '                item.hasExplicitTitle = replacement != nil\n'
  '                ClipboardItemTitlePersistence.update(item, on: object)\n'
  '                if let index = state.items.firstIndex(where: { $0.id == input.id }) {\n'
  '                    state.items[index] = item\n'
  '                } else { state.items.append(item) }\n'
  '            }\n'
  '        }\n'
  '    }\n'
  '\n'
  '    public func updateItem(id: UUID, title: String? = nil, text: String? = nil) throws {\n'],
 ['replica/Sources/PastoCore/ClipboardStore.swift',
  '            if let title {\n'
  '                let previousTitle = state.items[i].originalTitle\n'
  '                let displayedTitle = OriginalPreviewTitles.f_100308f88(previousTitle,\n'
  '                    defaultTitle: OriginalPreviewTitles.f_100309008(\n'
  '                        rawType: Int(originalContentKind(of: state.items[i]).rawValue),\n'
  '                        fileCount: state.items[i].decodedFilePreviewMetadata?.paths.count))\n'
  '                if title != displayedTitle {\n'
  '                    let normalized = title.trimmingCharacters(in: .whitespacesAndNewlines)\n'
  '                    state.items[i].title = normalized\n'
  '                    state.items[i].hasExplicitTitle = !normalized.isEmpty || previousTitle == '
  'nil\n'
  '                }\n'
  '            }\n',
  '            if let title {\n'
  '                let item = state.items[i]\n'
  '                OriginalPreviewTitles.f_1003bae08(title, originalTitle: item.originalTitle,\n'
  '                    defaultTitle: OriginalPreviewTitles.f_100309008(\n'
  '                        rawType: Int(originalContentKind(of: item).rawValue),\n'
  '                        fileCount: item.decodedFilePreviewMetadata?.paths.count)) { replacement '
  'in\n'
  '                    state.items[i].title = replacement ?? ""\n'
  '                    state.items[i].hasExplicitTitle = replacement != nil\n'
  '                }\n'
  '            }\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '    connectReplicaPreviewHeader(header, view: view, state: state, item: item)\n'
  '    editorHeader.onCancel = { [weak view] in view?.f_10007c1fc() }\n'
  '    editorHeader.onSave = { [weak view] in view?.f_10007c080() }\n'
  '    view.setCanCommitEditing = { [weak editorHeader] enabled in '
  'editorHeader?.setCanCommit(enabled) }\n'
  '    if let image = content as? ReplicaImagePreviewContent { '
  'editorHeader.setCanCommit(image.canCommit) }\n',
  '    connectReplicaPreviewHeader(header, view: view, state: state, item: item, input: input)\n'
  '    editorHeader.onCancel = { [weak view] in view?.f_10007c1fc() }\n'
  '    editorHeader.onSave = { [weak view] in view?.f_10007c080() }\n'
  '    view.setCanCommitEditing = { [weak editorHeader] enabled in '
  'editorHeader?.setCanCommit(enabled) }\n'
  '    if let image = content as? ReplicaImagePreviewContent { '
  'editorHeader.setCanCommit(image.canCommit) }\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '    connectReplicaPreviewHeader(header, view: view, state: state, item: item)\n'
  '    editorHeader.onCancel = { [weak view] in view?.f_10007c1fc() }\n'
  '    editorHeader.onSave = { [weak view] in view?.f_10007c080() }\n'
  '    view.setCanCommitEditing = { [weak editorHeader] enabled in '
  'editorHeader?.setCanCommit(enabled) }\n'
  '    content.onCancel = { [weak view] in view?.f_10007c1fc() }\n',
  '    connectReplicaPreviewHeader(header, view: view, state: state, item: item, input: input)\n'
  '    editorHeader.onCancel = { [weak view] in view?.f_10007c1fc() }\n'
  '    editorHeader.onSave = { [weak view] in view?.f_10007c080() }\n'
  '    view.setCanCommitEditing = { [weak editorHeader] enabled in '
  'editorHeader?.setCanCommit(enabled) }\n'
  '    content.onCancel = { [weak view] in view?.f_10007c1fc() }\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '                                         state: ReplicaUIState, item: ClipboardItem) {\n',
  '                                         state: ReplicaUIState, item: ClipboardItem,\n'
  '                                         input: ClipboardRestoreItem?) {\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '            state.perform { try state.store.updateItem(id: item.id, title: title, text: nil) '
  '}\n',
  '            if let input {\n'
  '                state.perform { try state.store.updateItem(input, title: title) }\n'
  '            } else {\n'
  '                state.perform { try state.store.updateItem(id: item.id, title: title, text: '
  'nil) }\n'
  '            }\n']]

def pre_native_title_write(source):
    source = pre_card_title_input(source)
    for path, previous, current in reversed(CHANGES):
        if current in source:
            assert source.count(current) == 1, path
            source = source.replace(current, previous, 1)
    return source

def pre_native_title_write_bytes(path):
    path=Path(path);raw=path.read_bytes()
    return pre_native_title_write(raw.decode()).encode() if path.suffix == '.swift' else raw
