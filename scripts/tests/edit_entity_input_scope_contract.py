"""Exact editor entity-input deltas, solely for earlier frozen source contracts."""
from pathlib import Path
from native_edit_write_scope_contract import pre_native_edit_write
CHANGES = [['replica/Sources/PastoCore/ClipboardRestoreItem.swift',
  '/// Retains the selected entity across a permission modal; content is read at restoration time.',
  '/// Retains the selected entity for restoration and editing; consumers read its current '
  'content.'],
 ['replica/Sources/PastoCore/ClipboardRestoreItem.swift',
  '    private let resolve: () -> ClipboardItem\n',
  '    private let resolve: () -> ClipboardItem\n'
  '    private let makeObservation: () -> ClipboardItemObservation?\n'],
 ['replica/Sources/PastoCore/ClipboardRestoreItem.swift',
  '            return item\n        }\n    }\n',
  '            return item\n'
  '        }\n'
  '        makeObservation = { ClipboardItemObservation(object: object) }\n'
  '    }\n'],
 ['replica/Sources/PastoCore/ClipboardRestoreItem.swift',
  '        resolve = { item }\n',
  '        resolve = { item }\n        makeObservation = { nil }\n'],
 ['replica/Sources/PastoCore/ClipboardRestoreItem.swift',
  '    public func resolvedItem() -> ClipboardItem { resolve() }\n',
  '    public func resolvedItem() -> ClipboardItem { resolve() }\n'
  '    public func observeItem() -> ClipboardItemObservation? { makeObservation() }\n'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    private func editItems(_ items: [ClipboardItem]) {\n'
  '        let editable = items.filter(Self.allowsContentEditing)\n'
  '        guard !editable.isEmpty else { NSSound.beep(); return }\n'
  '        for item in editable { presentEditingPreview(item: item) }\n'
  '    }\n',
  '    private func editItems(_ items: [ClipboardRestoreItem]) {\n'
  '        let editable = items.filter { Self.allowsContentEditing($0.resolvedItem()) }\n'
  '        guard !editable.isEmpty else { NSSound.beep(); return }\n'
  '        for input in editable { presentEditingPreview(input: input) }\n'
  '    }\n'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '        let items = appliedSelectionItems().filter {\n'
  '            Self.allowsContentEditing($0) && ($0.kind == .text || $0.kind == .richText)\n'
  '        }\n',
  '        let items = appliedRestoreItems().filter {\n'
  '            let item = $0.resolvedItem()\n'
  '            return Self.allowsContentEditing(item) && (item.kind == .text || item.kind == '
  '.richText)\n'
  '        }\n'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    private func presentEditingPreview(item: ClipboardItem) {\n',
  '    private func presentEditingPreview(input: ClipboardRestoreItem) {\n'
  '        let item = input.resolvedItem()\n'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    private func presentEditingPreview(input: ClipboardRestoreItem) {\n'
  '        let item = input.resolvedItem()\n'
  '        let window = OriginalPreviewWindow()\n'
  '        window.animationBehavior = .documentWindow\n'
  '        sharingPolicy.apply(to: window)\n'
  '        let registry = previewRegistry\n'
  '        let itemIdentifier = item.id.uuidString\n'
  '        registry.f_100086c10(window: window, itemIdentity: AnyHashable(item.id),\n'
  '                           itemIdentifier: itemIdentifier, isEditing: true)\n'
  '        let transition = OriginalPreviewWindowTransition(window: window)\n'
  '        let windowIdentity = ObjectIdentifier(window)\n'
  '        editorWindowTransitions[windowIdentity] = transition\n'
  '        transition.onPresented = { [weak self] window in self?.positionEditingPreview(window) '
  '}\n'
  '        transition.onDismissed = { [weak self] _ in\n'
  '            _ = self?.editorWindowTransitions.removeValue(forKey: windowIdentity)\n'
  '        }\n'
  '        let preview = makeOriginalReplicaPreview(state: state, item: item)\n'
  '        preview.onEndEditing = { window.close() }\n'
  '        preview.onEditingStateChanged = { editing in\n'
  '            registry.f_10008727c(isEditing: editing, itemIdentifier: itemIdentifier)\n'
  '        }\n'
  '        preview.f_10007be8c()\n'
  '        let controller = NSViewController()\n'
  '        controller.view = preview\n'
  '        transition.present(controller)\n'
  '        (preview.itemContentView as? OriginalPreviewEditableContent)?.focusPreviewEditing()\n'
  '    }\n'
  '\n',
  '    private func presentEditingPreview(input: ClipboardRestoreItem) {\n'
  '        let item = input.resolvedItem()\n'
  '        let window = OriginalPreviewWindow()\n'
  '        window.animationBehavior = .documentWindow\n'
  '        sharingPolicy.apply(to: window)\n'
  '        let registry = previewRegistry\n'
  '        let itemIdentifier = item.id.uuidString\n'
  '        registry.f_100086c10(window: window, itemIdentity: AnyHashable(item.id),\n'
  '                           itemIdentifier: itemIdentifier, isEditing: true)\n'
  '        let transition = OriginalPreviewWindowTransition(window: window)\n'
  '        let windowIdentity = ObjectIdentifier(window)\n'
  '        editorWindowTransitions[windowIdentity] = transition\n'
  '        transition.onPresented = { [weak self] window in self?.positionEditingPreview(window) '
  '}\n'
  '        transition.onDismissed = { [weak self] _ in\n'
  '            _ = self?.editorWindowTransitions.removeValue(forKey: windowIdentity)\n'
  '        }\n'
  '        let preview = makeOriginalReplicaPreview(state: state, item: item, input: input)\n'
  '        preview.onEndEditing = { window.close() }\n'
  '        preview.onEditingStateChanged = { editing in\n'
  '            registry.f_10008727c(isEditing: editing, itemIdentifier: itemIdentifier)\n'
  '        }\n'
  '        preview.f_10007be8c()\n'
  '        let controller = NSViewController()\n'
  '        controller.view = preview\n'
  '        transition.present(controller)\n'
  '        (preview.itemContentView as? OriginalPreviewEditableContent)?.focusPreviewEditing()\n'
  '    }\n'
  '\n'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '            editItems(appliedSelectionItems())\n',
  '            editItems(appliedRestoreItems())\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  'func makeOriginalReplicaPreview(state: ReplicaUIState, item: ClipboardItem) -> '
  'OriginalItemPreviewView {\n'
  '    if let textPreview = makeOriginalReplicaTextPreview(state: state, item: item) { return '
  'textPreview }\n',
  'func makeOriginalReplicaPreview(state: ReplicaUIState, item: ClipboardItem,\n'
  '                                input: ClipboardRestoreItem? = nil) -> OriginalItemPreviewView '
  '{\n'
  '    if let textPreview = makeOriginalReplicaTextPreview(state: state, item: item, input: input) '
  '{ return textPreview }\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  'func makeOriginalReplicaTextPreview(state: ReplicaUIState, item: ClipboardItem) -> '
  'OriginalItemPreviewView? {\n',
  'func makeOriginalReplicaTextPreview(state: ReplicaUIState, item: ClipboardItem,\n'
  '                                    input: ClipboardRestoreItem? = nil) -> '
  'OriginalItemPreviewView? {\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '    let content = ReplicaInlineTextPreviewContent(state: state, item: item)\n',
  '    let content = ReplicaInlineTextPreviewContent(state: state, item: item, input: input)\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '    init(state: ReplicaUIState, item: ClipboardItem) {\n'
  '        self.state = state\n'
  '        itemID = item.id\n'
  '        let nativeSource = state.store.observeItem(id: item.id)\n',
  '    init(state: ReplicaUIState, item: ClipboardItem, input: ClipboardRestoreItem?) {\n'
  '        self.state = state\n'
  '        itemID = item.id\n'
  '        let nativeSource: ClipboardItemObservation?\n'
  '        if let input { nativeSource = input.observeItem() }\n'
  '        else { nativeSource = state.store.observeItem(id: item.id) }\n']]

def pre_edit_entity_input(source):
    source = pre_native_edit_write(source)
    for path, previous, current in reversed(CHANGES):
        if current in source:
            assert source.count(current) == 1, path
            source = source.replace(current, previous, 1)
    return source

def pre_edit_entity_input_bytes(path):
    path=Path(path);raw=path.read_bytes()
    return pre_edit_entity_input(raw.decode()).encode() if path.suffix == '.swift' else raw
