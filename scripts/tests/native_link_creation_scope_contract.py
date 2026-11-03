"""Reverse only four reviewed139 native link-editor constructor hunks."""
CHANGES = [['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '// Native text/color/image creation reads its captured entity; other content keeps its adapter.',
  '// Native text/color/image/link creation reads its captured entity; other content keeps its '
  'adapter.'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '    return makeOriginalReplicaPreview(state: state, item: input.resolvedItem(), input: input)\n'
  '}',
  '    if rawType == 4 {\n'
  '        let content = ReplicaLinkPreviewContent(state: state, item: nil, input: input)\n'
  '        return makeReplicaContentPreview(state: state, item: nil, input: input, content: '
  'content,\n'
  '            contentSize: content.preferredPreviewSize, metadata: content.previewMetadataView)\n'
  '    }\n'
  '    return makeOriginalReplicaPreview(state: state, item: input.resolvedItem(), input: input)\n'
  '}'],
 ['replica/Sources/Pasto/UI/ReplicaLinkPreviewContent.swift',
  '    init(state: ReplicaUIState, item: ClipboardItem, input: ClipboardRestoreItem? = nil) {\n'
  '        self.state = state\n'
  '        itemID = item.id\n'
  '        editInput = input\n'
  '        readOnlyContent = makeReplicaReadOnlyPreviewContent(store: state.store, item: item)',
  '    init(state: ReplicaUIState, item: ClipboardItem?, input: ClipboardRestoreItem? = nil) {\n'
  '        self.state = state\n'
  '        guard let itemID = input?.id ?? item?.id else { preconditionFailure("Link preview '
  'requires an item") }\n'
  '        self.itemID = itemID\n'
  '        editInput = input\n'
  '        readOnlyContent = makeReplicaReadOnlyPreviewContent(store: state.store, itemID: '
  'itemID)'],
 ['replica/Sources/Pasto/UI/ReplicaReadOnlyPreviewContent.swift',
  'func makeReplicaReadOnlyPreviewContent(store: ClipboardStore, item: ClipboardItem) -> NSView {\n'
  '    NSHostingView(rootView: ReplicaReadOnlyPreviewContent(store: store, itemID: item.id))\n'
  '}',
  'func makeReplicaReadOnlyPreviewContent(store: ClipboardStore, item: ClipboardItem) -> NSView {\n'
  '    makeReplicaReadOnlyPreviewContent(store: store, itemID: item.id)\n'
  '}\n'
  '\n'
  '@MainActor\n'
  'func makeReplicaReadOnlyPreviewContent(store: ClipboardStore, itemID: UUID) -> NSView {\n'
  '    NSHostingView(rootView: ReplicaReadOnlyPreviewContent(store: store, itemID: itemID))\n'
  '}']]

def pre_native_link_creation(source):
    from native_list_navigation_scope_contract import pre_native_list_navigation
    source=pre_native_list_navigation(source)
    for _,old,new in reversed(CHANGES):
        if new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    return source

def pre_native_link_creation_bytes(path):
    data=path.read_bytes()
    return pre_native_link_creation(data.decode()).encode()if path.suffix==".swift"else data
