"""Exact phase100 native text creation deltas for historical contracts only."""
from pathlib import Path
from nontext_edit_write_scope_contract import pre_nontext_edit_write
CHANGES = [['replica/Sources/PastoCore/ClipboardRestoreItem.swift',
  '    // 309008/308f88 read title/type/preview, independently of archived value content.\n',
  '    // 31eba8/31c2ec inspect native type before content creation or editing eligibility.\n'
  '    public func previewRawType() -> Int? {\n'
  '        guard let object = nativeObject else { return nil }\n'
  '        let rawType = (object.value(forKey: "rawType") as? NSNumber)?.intValue ?? 0\n'
  '        return (0...5).contains(rawType) ? rawType : 0\n'
  '    }\n'
  '\n'
  '    // 309008/308f88 read title/type/preview, independently of archived value content.\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '/// Shares preview chrome and editing transitions; per-kind content retains its own contract.\n',
  '// Native text creation does not require the archived value DTO; other content keeps its adapter.\n'
  '@MainActor\n'
  'func makeOriginalReplicaNativePreview(state: ReplicaUIState, input: ClipboardRestoreItem) -> '
  'OriginalItemPreviewView {\n'
  '    if input.previewRawType() == 5 {\n'
  '        return makeReplicaTextPreview(state: state, item: nil, input: input)\n'
  '    }\n'
  '    return makeOriginalReplicaPreview(state: state, item: input.resolvedItem(), input: input)\n'
  '}\n'
  '\n'
  '/// Shares preview chrome and editing transitions; per-kind content retains its own contract.\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '    guard item.kind == .text || item.kind == .richText else { return nil }\n'
  '    let content = ReplicaInlineTextPreviewContent(state: state, item: item, input: input)\n',
  '    let isText: Bool\n'
  '    if let rawType = input?.previewRawType() { isText = rawType == 5 }\n'
  '    else { isText = item.kind == .text || item.kind == .richText }\n'
  '    guard isText else { return nil }\n'
  '    return makeReplicaTextPreview(state: state, item: item, input: input)\n'
  '}\n'
  '\n'
  '@MainActor\n'
  'private func makeReplicaTextPreview(state: ReplicaUIState, item: ClipboardItem?,\n'
  '                                    input: ClipboardRestoreItem?) -> OriginalItemPreviewView {\n'
  '    let content = ReplicaInlineTextPreviewContent(state: state, item: item, input: input)\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '                                         state: ReplicaUIState, item: ClipboardItem,\n',
  '                                         state: ReplicaUIState, item: ClipboardItem?,\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '            } else {\n'
  '                state.perform { try state.store.updateItem(id: item.id, title: title, text: nil) }\n',
  '            } else if let item {\n'
  '                state.perform { try state.store.updateItem(id: item.id, title: title, text: nil) }\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '    init(state: ReplicaUIState, item: ClipboardItem, input: ClipboardRestoreItem?) {\n'
  '        self.state = state\n'
  '        itemID = item.id\n'
  '        editInput = input\n',
  '    init(state: ReplicaUIState, item: ClipboardItem?, input: ClipboardRestoreItem?) {\n'
  '        self.state = state\n'
  '        guard let itemID = input?.id ?? item?.id else { preconditionFailure("Missing preview input") }\n'
  '        self.itemID = itemID\n'
  '        editInput = input\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '        else { nativeSource = state.store.observeItem(id: item.id) }\n',
  '        else { nativeSource = state.store.observeItem(id: itemID) }\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '        } else { initial = Self.attributedContent(item) }\n',
  '        } else if let item = item ?? input?.resolvedItem() {\n'
  '            initial = Self.attributedContent(item)\n'
  '        } else { preconditionFailure("Missing preview content") }\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '    init(state: ReplicaUIState, item: ClipboardItem, input: ClipboardRestoreItem?) {\n'
  '        self.state = state\n'
  '        itemID = item.id\n'
  '        self.input = input\n',
  '    init(state: ReplicaUIState, item: ClipboardItem?, input: ClipboardRestoreItem?) {\n'
  '        self.state = state\n'
  '        guard let itemID = input?.id ?? item?.id else { preconditionFailure("Missing preview input") }\n'
  '        self.itemID = itemID\n'
  '        self.input = input\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '                    guard let current = items.first(where: { $0.id == item.id }) else { return }\n',
  '                    guard let current = items.first(where: { $0.id == itemID }) else { return }\n'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '        let editable = items.filter { Self.allowsContentEditing($0.resolvedItem()) }\n',
  '        let editable = items.filter { Self.allowsEditingInput($0) }\n'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    // 0x10031c2ec: offline lists have no CKShare permission branch.\n',
  '    private static func allowsEditingInput(_ input: ClipboardRestoreItem) -> Bool {\n'
  '        if let rawType = input.previewRawType() {\n'
  '            return [1, 2, 4, 5].contains(rawType)\n'
  '        }\n'
  '        return allowsContentEditing(input.resolvedItem())\n'
  '    }\n'
  '\n'
  '    // 0x10031c2ec: offline lists have no CKShare permission branch.\n'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '        let items = appliedRestoreItems().filter {\n'
  '            let item = $0.resolvedItem()\n'
  '            return Self.allowsContentEditing(item) && (item.kind == .text || item.kind == .richText)\n'
  '        }\n',
  '        let items = appliedRestoreItems().filter {\n'
  '            guard Self.allowsEditingInput($0) else { return false }\n'
  '            if let rawType = $0.previewRawType() { return rawType == 5 }\n'
  '            let item = $0.resolvedItem()\n'
  '            return item.kind == .text || item.kind == .richText\n'
  '        }\n'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    private func presentEditingPreview(input: ClipboardRestoreItem) {\n'
  '        let item = input.resolvedItem()\n',
  '    private func presentEditingPreview(input: ClipboardRestoreItem) {\n'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '        let itemIdentifier = item.id.uuidString\n'
  '        registry.f_100086c10(window: window, itemIdentity: AnyHashable(item.id),\n',
  '        let itemIdentifier = input.id.uuidString\n'
  '        registry.f_100086c10(window: window, itemIdentity: AnyHashable(input.id),\n'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '        let preview = makeOriginalReplicaPreview(state: state, item: item, input: input)\n',
  '        let preview = makeOriginalReplicaNativePreview(state: state, input: input)\n'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '        makeOriginalReplicaPreview(state: state, item: input.resolvedItem(), input: input)\n',
  '        makeOriginalReplicaNativePreview(state: state, input: input)\n'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '            return makeOriginalReplicaPreview(state: self.state, item: input.resolvedItem(), input: '
  'input)\n',
  '            return makeOriginalReplicaNativePreview(state: self.state, input: input)\n']]

def pre_text_preview_creation(source):
    source=pre_nontext_edit_write(source)
    for _,old,new in reversed(CHANGES):
        if old.startswith(new) and old in source: continue
        if new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    return source

def pre_text_preview_creation_bytes(path):
    p=Path(path)
    return pre_text_preview_creation(p.read_text()).encode() if p.suffix=='.swift' else p.read_bytes()
