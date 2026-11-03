"""Exact phase102 native color/link read deltas, historical contract isolation only."""
from pathlib import Path
from image_preview_read_scope_contract import pre_image_preview_read
CHANGES = [['replica/Sources/PastoCore/ClipboardRestoreItem.swift',
  'import Combine\n'
  'import CoreData\n'
  'import Foundation\n'
  '\n'
  '/// Retains the selected entity for restoration and editing; consumers read its current content.\n',
  'import AppKit\n'
  'import Combine\n'
  'import CoreData\n'
  'import Foundation\n'
  '\n'
  '/// Retains the selected entity for restoration and editing; consumers read its current content.\n'],
 ['replica/Sources/PastoCore/ClipboardRestoreItem.swift',
  '    public func resolvedItem() -> ClipboardItem { resolve() }\n',
  '    // 3bbc20 reads the current native preview; absent/noncolor metadata displays black.\n'
  '    public func previewColor() -> NSColor? {\n'
  '        guard let object = nativeObject else { return nil }\n'
  '        guard let metadata = OriginalImagePreviewMetadataCodec.decodeColor(object.value(forKey: '
  '"rawPreview") as? Data) else {\n'
  '            return .black\n'
  '        }\n'
  '        return OriginalColorPreviewMetadataGenerator.color(metadata.code)\n'
  '    }\n'
  '\n'
  '    // 3bf65c requires canonical link metadata; an invalid native value must not use a stale DTO URL.\n'
  '    public func previewLinkURL() -> URL? {\n'
  '        guard let object = nativeObject else { return nil }\n'
  '        guard let metadata = OriginalImagePreviewMetadataCodec.decodeLink(object.value(forKey: '
  '"rawPreview") as? Data) else {\n'
  '            preconditionFailure("Link preview requires canonical link metadata")\n'
  '        }\n'
  '        return metadata.url\n'
  '    }\n'
  '\n'
  '    public func resolvedItem() -> ClipboardItem { resolve() }\n'],
 ['replica/Sources/Pasto/UI/ReplicaColorPreviewContent.swift',
  '    private let editInput: ClipboardRestoreItem?\n    private let codeLabel',
  '    private var editInput: ClipboardRestoreItem?\n    private let codeLabel'],
 ['replica/Sources/Pasto/UI/ReplicaColorPreviewContent.swift',
  '    init(state: ReplicaUIState, item: ClipboardItem, input: ClipboardRestoreItem? = nil) {\n'
  '        self.state = state\n'
  '        itemID = item.id\n',
  '    init(state: ReplicaUIState, item: ClipboardItem?, input: ClipboardRestoreItem? = nil) {\n'
  '        self.state = state\n'
  '        guard let itemID = input?.id ?? item?.id else { preconditionFailure("Missing color preview '
  'input") }\n'
  '        self.itemID = itemID\n'],
 ['replica/Sources/Pasto/UI/ReplicaColorPreviewContent.swift',
  '        itemObservation = state.store.$items.sink { [weak self] items in\n'
  '            MainActor.assumeIsolated {\n'
  '                guard let self, !self.editing,\n'
  '                      let current = items.first(where: { $0.id == self.itemID }) else { return }\n'
  '                self.display(Self.modelColor(current))\n'
  '            }\n'
  '        }\n',
  '        itemObservation = input?.observeChanges { [weak self] current in\n'
  '            self?.receiveNativeModel(current)\n'
  '        }\n'
  '        if itemObservation != nil, let input {\n'
  '            receiveNativeModel(input)\n'
  '        } else {\n'
  '            itemObservation = state.store.$items.sink { [weak self] items in\n'
  '                MainActor.assumeIsolated {\n'
  '                    guard let self, !self.editing,\n'
  '                          let current = items.first(where: { $0.id == self.itemID }) else { return }\n'
  '                    self.display(Self.modelColor(current))\n'
  '                }\n'
  '            }\n'
  '        }\n'],
 ['replica/Sources/Pasto/UI/ReplicaColorPreviewContent.swift',
  '    private func currentModelColor() -> NSColor {\n'
  '        state?.store.items.first(where: { $0.id == itemID }).map(Self.modelColor) ?? .black\n'
  '    }\n',
  '    private func receiveNativeModel(_ input: ClipboardRestoreItem) {\n'
  '        // The model accepts the new entity even while its editor keeps the current color on screen.\n'
  '        editInput = input\n'
  '        guard !editing else { return }\n'
  '        display(currentModelColor())\n'
  '    }\n'
  '\n'
  '    private func currentModelColor() -> NSColor {\n'
  '        if let color = editInput?.previewColor() { return color }\n'
  '        return state?.store.items.first(where: { $0.id == itemID }).map(Self.modelColor) ?? .black\n'
  '    }\n'],
 ['replica/Sources/Pasto/UI/ReplicaLinkPreviewContent.swift',
  '    private let editInput: ClipboardRestoreItem?\n    private let readOnlyContent',
  '    private var editInput: ClipboardRestoreItem?\n    private let readOnlyContent'],
 ['replica/Sources/Pasto/UI/ReplicaLinkPreviewContent.swift',
  '        itemObservation = state.store.$items.sink { [weak self] items in\n'
  '            MainActor.assumeIsolated {\n'
  '                guard let self, let current = items.first(where: { $0.id == self.itemID }) else { return '
  '}\n'
  '                self.updateMetadata(Self.itemURL(current))\n'
  '            }\n'
  '        }\n',
  '        itemObservation = input?.observeChanges { [weak self] current in\n'
  '            self?.receiveNativeModel(current)\n'
  '        }\n'
  '        if itemObservation != nil, let input {\n'
  '            receiveNativeModel(input)\n'
  '        } else {\n'
  '            itemObservation = state.store.$items.sink { [weak self] items in\n'
  '                MainActor.assumeIsolated {\n'
  '                    guard let self, let current = items.first(where: { $0.id == self.itemID }) else { '
  'return }\n'
  '                    self.updateMetadata(Self.itemURL(current))\n'
  '                }\n'
  '            }\n'
  '        }\n'],
 ['replica/Sources/Pasto/UI/ReplicaLinkPreviewContent.swift',
  '    private func currentURL() -> URL? {\n'
  '        state?.store.items.first(where: { $0.id == itemID }).map(Self.itemURL)\n'
  '    }\n',
  '    private func receiveNativeModel(_ input: ClipboardRestoreItem) {\n'
  '        editInput = input\n'
  '        updateMetadata(currentURL())\n'
  '    }\n'
  '\n'
  '    private func currentURL() -> URL? {\n'
  '        if let url = editInput?.previewLinkURL() { return url }\n'
  '        return state?.store.items.first(where: { $0.id == itemID }).map(Self.itemURL)\n'
  '    }\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '// Native text creation does not require the archived value DTO; other content keeps its adapter.\n'
  '@MainActor\n'
  'func makeOriginalReplicaNativePreview(state: ReplicaUIState, input: ClipboardRestoreItem) -> '
  'OriginalItemPreviewView {\n'
  '    if input.previewRawType() == 5 {\n'
  '        return makeReplicaTextPreview(state: state, item: nil, input: input)\n'
  '    }\n',
  '// Native text/color creation reads its captured entity; other content keeps its adapter.\n'
  '@MainActor\n'
  'func makeOriginalReplicaNativePreview(state: ReplicaUIState, input: ClipboardRestoreItem) -> '
  'OriginalItemPreviewView {\n'
  '    let rawType = input.previewRawType()\n'
  '    if rawType == 5 {\n'
  '        return makeReplicaTextPreview(state: state, item: nil, input: input)\n'
  '    }\n'
  '    if rawType == 2 {\n'
  '        let content = ReplicaColorPreviewContent(state: state, item: nil, input: input)\n'
  '        return makeReplicaContentPreview(state: state, item: nil, input: input, content: content,\n'
  '            contentSize: content.preferredPreviewSize, metadata: content.previewMetadataView)\n'
  '    }\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '    let header = ReplicaInlinePreviewHeader(state: state, item: item, input: input)\n'
  '    let editorHeader = ReplicaInlinePreviewEditorHeader()\n'
  '    let footer = OriginalPreviewFooterView()\n'
  '    if let metadata { footer.f_1003df0b0(metadata) }\n'
  '    else {\n'
  '        let emptyMetadata = NSView()\n'
  '        emptyMetadata.heightAnchor.constraint(equalToConstant: 0).isActive = true\n'
  '        footer.f_1003df0b0(emptyMetadata)\n'
  '    }\n'
  '    let view = ReplicaInlinePreviewContainer(previewHeader: header, editorHeader: editorHeader,\n'
  '                                            contentView: content, footer: footer,\n'
  '                                            contentSize: contentSize)\n'
  '    view.applyContentAppearance()\n'
  '    connectReplicaPreviewHeader(header, view: view, state: state, item: item, input: input)\n'
  '    editorHeader.onCancel = { [weak view] in view?.f_10007c1fc() }\n'
  '    editorHeader.onSave = { [weak view] in view?.f_10007c080() }\n'
  '    view.setCanCommitEditing = { [weak editorHeader] enabled in editorHeader?.setCanCommit(enabled) }\n'
  '    if let image = content as? ReplicaImagePreviewContent { editorHeader.setCanCommit(image.canCommit) }\n'
  '    return view\n'
  '}\n',
  '    return makeReplicaContentPreview(state: state, item: item, input: input, content: content,\n'
  '        contentSize: contentSize, metadata: metadata)\n'
  '}\n'
  '\n'
  '@MainActor\n'
  'private func makeReplicaContentPreview(state: ReplicaUIState, item: ClipboardItem?, input: '
  'ClipboardRestoreItem?,\n'
  '                                       content: NSView, contentSize: NSSize, metadata: NSView?) -> '
  'OriginalItemPreviewView {\n'
  '    let header = ReplicaInlinePreviewHeader(state: state, item: item, input: input)\n'
  '    let editorHeader = ReplicaInlinePreviewEditorHeader()\n'
  '    let footer = OriginalPreviewFooterView()\n'
  '    if let metadata { footer.f_1003df0b0(metadata) }\n'
  '    else {\n'
  '        let emptyMetadata = NSView()\n'
  '        emptyMetadata.heightAnchor.constraint(equalToConstant: 0).isActive = true\n'
  '        footer.f_1003df0b0(emptyMetadata)\n'
  '    }\n'
  '    let view = ReplicaInlinePreviewContainer(previewHeader: header, editorHeader: editorHeader,\n'
  '                                            contentView: content, footer: footer,\n'
  '                                            contentSize: contentSize)\n'
  '    view.applyContentAppearance()\n'
  '    connectReplicaPreviewHeader(header, view: view, state: state, item: item, input: input)\n'
  '    editorHeader.onCancel = { [weak view] in view?.f_10007c1fc() }\n'
  '    editorHeader.onSave = { [weak view] in view?.f_10007c080() }\n'
  '    view.setCanCommitEditing = { [weak editorHeader] enabled in editorHeader?.setCanCommit(enabled) }\n'
  '    if let image = content as? ReplicaImagePreviewContent { editorHeader.setCanCommit(image.canCommit) }\n'
  '    return view\n'
  '}\n']]

def pre_nontext_preview_read(source):
    source=pre_image_preview_read(source)
    for _,old,new in reversed(CHANGES):
        if old.startswith(new) and old in source: continue
        if new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    return source

def pre_nontext_preview_read_bytes(path):
    p=Path(path)
    return pre_nontext_preview_read(p.read_text()).encode() if p.suffix=='.swift' else p.read_bytes()
