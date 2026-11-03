"""Exact native item-observation deltas for previous frozen source contracts."""
from pathlib import Path
from edit_entity_input_scope_contract import pre_edit_entity_input
NEW_PATH = 'replica/Sources/PastoCore/ClipboardItemObservation.swift'
CHANGES = [['replica/Sources/PastoCore/ClipboardPersistence.swift',
  '    func itemContentKind(identifier: String) -> OriginalPasteboardContentKind {\n',
  '    func observeItem(identifier: String) -> ClipboardItemObservation? {\n'
  '        context.performAndWait {\n'
  '            let request = PastoItemEntity.defaultFetchRequest()\n'
  '            request.predicate = NSPredicate(format: "key == %@", identifier)\n'
  '            request.fetchLimit = 1\n'
  '            guard let object = (try? context.fetch(request))?.first else { return nil }\n'
  '            return ClipboardItemObservation(object: object)\n'
  '        }\n'
  '    }\n'
  '\n'
  '    func itemContentKind(identifier: String) -> OriginalPasteboardContentKind {\n'],
 ['replica/Sources/PastoCore/ClipboardStore.swift',
  '    public func originalContentKind(of item: ClipboardItem) -> OriginalPasteboardContentKind '
  '{\n',
  '    public func observeItem(id: UUID) -> ClipboardItemObservation? {\n'
  '        persistence.observeItem(identifier: id.uuidString)\n'
  '    }\n'
  '    public func originalContentKind(of item: ClipboardItem) -> OriginalPasteboardContentKind '
  '{\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '    private let itemID: UUID\n    private var itemObservation: AnyCancellable?\n',
  '    private let itemID: UUID\n'
  '    private var nativeItemObservation: ClipboardItemObservation?\n'
  '    private var itemObservation: AnyCancellable?\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '        itemID = item.id\n        let initial = Self.attributedContent(item)\n',
  '        itemID = item.id\n'
  '        let nativeSource = state.store.observeItem(id: item.id)\n'
  '        nativeItemObservation = nativeSource\n'
  '        let initial: NSAttributedString\n'
  '        if let nativeSource {\n'
  '            initial = nativeSource.value.map(Self.attributedContent) ?? '
  'NSAttributedString(string: "")\n'
  '        } else { initial = Self.attributedContent(item) }\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '        itemObservation = state.store.$items.sink { [weak self] items in\n'
  '            MainActor.assumeIsolated {\n'
  '                guard let self else { return }\n'
  '                guard let current = items.first(where: { $0.id == self.itemID }), '
  '!current.isDeleted else {\n'
  '                    self.window?.performClose(nil)\n'
  '                    return\n'
  '                }\n'
  '                self.replaceStoredModel(current)\n'
  '                if !self.text.isEditable { self.displayStoredModel() }\n'
  '            }\n'
  '        }\n',
  '        if let nativeSource {\n'
  '            nativeSource.onChange = { [weak self] current in\n'
  '                self?.receiveStoredModel(current)\n'
  '            }\n'
  '        } else {\n'
  '            // No native source is available; retain the existing store adapter.\n'
  '            itemObservation = state.store.$items.sink { [weak self] items in\n'
  '                MainActor.assumeIsolated {\n'
  '                    guard let self,\n'
  '                          let current = items.first(where: { $0.id == self.itemID }), '
  '!current.isDeleted else { return }\n'
  '                    self.receiveStoredModel(current)\n'
  '                }\n'
  '            }\n'
  '        }\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '    private func reloadStoredContent() {\n'
  '        guard let item = state?.store.items.first(where: { $0.id == itemID }) else { return }\n'
  '        replaceStoredModel(item)\n'
  '        displayStoredModel()\n'
  '    }\n'
  '\n',
  '    private func reloadStoredContent() {\n'
  '        let item: ClipboardItem?\n'
  '        if let nativeItemObservation { item = nativeItemObservation.value }\n'
  '        else { item = state?.store.items.first(where: { $0.id == itemID }) }\n'
  '        guard let item else { return }\n'
  '        replaceStoredModel(item)\n'
  '        displayStoredModel()\n'
  '    }\n'
  '\n'
  '    private func receiveStoredModel(_ item: ClipboardItem) {\n'
  '        replaceStoredModel(item)\n'
  '        if !text.isEditable { displayStoredModel() }\n'
  '    }\n'
  '\n']]

def pre_item_observation(source):
    source = pre_edit_entity_input(source)
    for path, previous, current in reversed(CHANGES):
        if current in source:
            assert source.count(current) == 1, path
            source = source.replace(current, previous, 1)
    return source

def pre_item_observation_bytes(path):
    path=Path(path);raw=path.read_bytes()
    return pre_item_observation(raw.decode()).encode() if path.suffix == '.swift' else raw
