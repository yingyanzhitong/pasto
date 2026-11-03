"""Exact phase103 native image read deltas for historical contracts only."""
from pathlib import Path
from native_group_write_scope_contract import pre_native_group_write
CHANGES = [['replica/Sources/PastoCore/ClipboardRestoreItem.swift',
  '    public var isDeleted: Bool { nativeObject?.isDeleted ?? false }\n',
  '    public var isDeleted: Bool { nativeObject?.isDeleted ?? false }\n'
  '    public var hasNativeEntity: Bool { nativeObject != nil }\n'],
 ['replica/Sources/PastoCore/ClipboardRestoreItem.swift',
  '    public func resolvedItem() -> ClipboardItem { resolve() }\n',
  '    // 3bd9cc: first decodable image in native representation order; no value DTO or metadata '
  'dependency.\n'
  '    public func previewImage() -> NSImage? {\n'
  '        guard let object = nativeObject,\n'
  '              let items = ClipboardItemDataPersistence.readItems(from: object) else { return nil }\n'
  '        for item in items {\n'
  '            guard let data = item.f_10037d5c4(), NSImage(data: data) != nil else { continue }\n'
  '            return item.f_10037d5c4().flatMap(NSImage.init(data:))\n'
  '        }\n'
  '        return nil\n'
  '    }\n'
  '\n'
  '    // 3bd740/3bd784: missing or nonimage metadata supplies zero size.\n'
  '    public func previewImageSize() -> NSSize? {\n'
  '        guard let object = nativeObject else { return nil }\n'
  '        return OriginalImagePreviewMetadataCodec.decode(object.value(forKey: "rawPreview") as? '
  'Data)?.size ?? .zero\n'
  '    }\n'
  '\n'
  '    public func resolvedItem() -> ClipboardItem { resolve() }\n'],
 ['replica/Sources/Pasto/UI/ReplicaImagePreviewContent.swift',
  '    init(state: ReplicaUIState, item: ClipboardItem, input: ClipboardRestoreItem? = nil) {\n'
  '        self.state = state\n'
  '        itemID = item.id\n',
  '    init(state: ReplicaUIState, item: ClipboardItem?, input: ClipboardRestoreItem? = nil) {\n'
  '        self.state = state\n'
  '        guard let itemID = input?.id ?? item?.id else { preconditionFailure("Missing image preview '
  'input") }\n'
  '        self.itemID = itemID\n'],
 ['replica/Sources/Pasto/UI/ReplicaImagePreviewContent.swift',
  '        replaceDisplayedItem(item)\n'
  '        itemObservation = state.store.$items.sink { [weak self] items in\n'
  '            MainActor.assumeIsolated {\n'
  '                guard let self else { return }\n'
  '                guard let current = items.first(where: { $0.id == self.itemID }),\n'
  '                      !current.isDeleted, current.kind == .image else {\n'
  '                    self.window?.performClose(nil)\n'
  '                    return\n'
  '                }\n'
  '                if !self.isEditing { self.replaceDisplayedItem(current) }\n'
  '            }\n'
  '        }',
  '        if input?.hasNativeEntity == true {\n'
  '            zoomView.f_100240a64(input?.previewImage())\n'
  '            zoomView.f_100240be8(false)\n'
  '            updateMetadataAndCommitState()\n'
  '        } else if let item = item ?? input?.resolvedItem() {\n'
  '            replaceDisplayedItem(item)\n'
  '            itemObservation = state.store.$items.sink { [weak self] items in\n'
  '                MainActor.assumeIsolated {\n'
  '                    guard let self else { return }\n'
  '                    guard let current = items.first(where: { $0.id == self.itemID }),\n'
  '                          !current.isDeleted, current.kind == .image else {\n'
  '                        self.window?.performClose(nil)\n'
  '                        return\n'
  '                    }\n'
  '                    if !self.isEditing { self.replaceDisplayedItem(current) }\n'
  '                }\n'
  '            }\n'
  '        } else { preconditionFailure("Missing image preview content") }'],
 ['replica/Sources/Pasto/UI/ReplicaImagePreviewContent.swift',
  '        let imageSize = imageMetadataSize\n',
  '        let imageSize = editInput?.previewImageSize() ?? imageMetadataSize\n'],
 ['replica/Sources/Pasto/UI/ReplicaImagePreviewContent.swift',
  '    func cancelPreviewEditing() {\n        finishEditing()\n    }\n',
  '    func cancelPreviewEditing() {\n        finishEditing(reloadNativeImage: true)\n    }\n'],
 ['replica/Sources/Pasto/UI/ReplicaImagePreviewContent.swift',
  '        finishEditing()\n    }\n\n    private func finishEditing() {\n        isEditing = false\n',
  '        finishEditing(reloadNativeImage: false)\n'
  '    }\n'
  '\n'
  '    private func finishEditing(reloadNativeImage: Bool) {\n'
  '        isEditing = false\n'
  '        if editInput?.hasNativeEntity == true {\n'
  '            if reloadNativeImage { zoomView.f_100240a64(editInput?.previewImage()) }\n'
  '            zoomView.f_100240be8(false)\n'
  '            quarterTurns = 0\n'
  '            editingUndoManager.removeAllActions()\n'
  '            updateMetadataAndCommitState()\n'
  '            return\n'
  '        }\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '// Native text/color creation reads its captured entity; other content keeps its adapter.\n',
  '// Native text/color/image creation reads its captured entity; other content keeps its adapter.\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '    return makeOriginalReplicaPreview(state: state, item: input.resolvedItem(), input: input)\n}\n',
  '    if rawType == 1 {\n'
  '        let content = ReplicaImagePreviewContent(state: state, item: nil, input: input)\n'
  '        return makeReplicaContentPreview(state: state, item: nil, input: input, content: content,\n'
  '            contentSize: content.preferredPreviewSize, metadata: content.previewMetadataView)\n'
  '    }\n'
  '    return makeOriginalReplicaPreview(state: state, item: input.resolvedItem(), input: input)\n'
  '}\n']]

def pre_image_preview_read(source):
    source = pre_native_group_write(source)
    for _,old,new in reversed(CHANGES):
        if old.startswith(new) and old in source: continue
        if new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    return source

def pre_image_preview_read_bytes(path):
    p=Path(path)
    return pre_image_preview_read(p.read_text()).encode() if p.suffix=='.swift' else p.read_bytes()
