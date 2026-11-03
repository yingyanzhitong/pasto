"""Exact captured card-title input deltas for earlier frozen source contracts only."""
from pathlib import Path
from preview_entity_changes_scope_contract import pre_preview_entity_changes
CHANGES = [['replica/Sources/PastoCore/ClipboardRestoreItem.swift',
  '    public func resolvedItem() -> ClipboardItem { resolve() }\n',
  '    public func hasSameEntity(as other: ClipboardRestoreItem) -> Bool {\n'
  '        if let nativeObject { return nativeObject === other.nativeObject }\n'
  '        return other.nativeObject == nil && id == other.id\n'
  '    }\n'
  '\n'
  '    public func resolvedItem() -> ClipboardItem { resolve() }\n'],
 ['replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift',
  '        for index in desired.sorted() {\n            let item = renderedItem(at: index)\n',
  '        for index in desired.sorted() {\n'
  '            let input = items[index].requiredRestoreItem()\n'
  '            let item = input.resolvedItem()\n'],
 ['replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift',
  'ReplicaNativeCardCell(owner: self, state: state, item: item, side: cardSide, index: index)',
  'ReplicaNativeCardCell(owner: self, state: state, item: item, input: input, side: cardSide, '
  'index: index)'],
 ['replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift',
  '            cell.update(state: state, item: item, side: cardSide, index: index)\n',
  '            cell.update(state: state, item: item, input: input, side: cardSide, index: '
  'index)\n'],
 ['replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift',
  '            cell.update(state: state, item: renderedItem(at: index), side: cardSide, index: '
  'index)\n',
  '            let input = items[index].requiredRestoreItem()\n'
  '            cell.update(state: state, item: input.resolvedItem(), input: input, side: cardSide, '
  'index: index)\n'],
 ['replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift',
  '    private var item: ClipboardItem\n    private var side: CGFloat\n',
  '    private var item: ClipboardItem\n'
  '    private var titleInput: ClipboardRestoreItem\n'
  '    private var side: CGFloat\n'],
 ['replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift',
  '    init(owner: ReplicaNativeCollectionHost, state: ReplicaUIState, item: ClipboardItem, side: '
  'CGFloat, index: Int) {\n'
  '        self.owner = owner\n'
  '        self.state = state\n'
  '        self.item = item\n',
  '    init(owner: ReplicaNativeCollectionHost, state: ReplicaUIState, item: ClipboardItem, input: '
  'ClipboardRestoreItem, side: CGFloat, index: Int) {\n'
  '        self.owner = owner\n'
  '        self.state = state\n'
  '        self.item = item\n'
  '        titleInput = input\n'],
 ['replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift',
  '    func update(state: ReplicaUIState, item: ClipboardItem, side: CGFloat, index: Int) {\n'
  '        if self.state !== state { renderingSignature = nil }\n'
  '        self.state = state\n'
  '        self.item = item\n',
  '    func update(state: ReplicaUIState, item: ClipboardItem, input: ClipboardRestoreItem, side: '
  'CGFloat, index: Int) {\n'
  '        if self.state !== state || !titleInput.hasSameEntity(as: input) { renderingSignature = '
  'nil }\n'
  '        self.state = state\n'
  '        self.item = item\n'
  '        titleInput = input\n'],
 ['replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift',
  '            selectionOverride: renderedSelection, dimmingOverride: owner?.isDimmed ?? true, '
  'nativeInteractions: true)\n',
  '            selectionOverride: renderedSelection, dimmingOverride: owner?.isDimmed ?? true, '
  'nativeInteractions: true, titleInput: titleInput)\n'],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  '    var nativeInteractions = false\n',
  '    var nativeInteractions = false\n    var titleInput: ClipboardRestoreItem? = nil\n'],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  '                ReplicaCardTitle(state: state, itemID: item.id, title: cardTitle,\n',
  '                ReplicaCardTitle(state: state, itemID: item.id, input: titleInput, title: '
  'cardTitle,\n'],
 ['replica/Sources/Pasto/UI/ReplicaCardTitle.swift',
  '    let itemID: UUID\n',
  '    let itemID: UUID\n    var input: ClipboardRestoreItem? = nil\n'],
 ['replica/Sources/Pasto/UI/ReplicaCardTitle.swift',
  '        view.configure(state: state, itemID: itemID, title: title, font: font, textColor: '
  'textColor)\n',
  '        view.configure(state: state, itemID: itemID, input: input, title: title, font: font, '
  'textColor: textColor)\n'],
 ['replica/Sources/Pasto/UI/ReplicaCardTitle.swift',
  '    func configure(state: ReplicaUIState, itemID: UUID, title: String, font: NSFont, textColor: '
  'NSColor) {\n',
  '    func configure(state: ReplicaUIState, itemID: UUID, input: ClipboardRestoreItem? = nil, '
  'title: String, font: NSFont, textColor: NSColor) {\n'],
 ['replica/Sources/Pasto/UI/ReplicaCardTitle.swift',
  '            state.perform { try state.store.updateItem(id: itemID, title: title, text: nil) }\n',
  '            if let input {\n'
  '                state.perform { try state.store.updateItem(input, title: title) }\n'
  '            } else {\n'
  '                state.perform { try state.store.updateItem(id: itemID, title: title, text: nil) '
  '}\n'
  '            }\n']]

def pre_card_title_input(source):
    source = pre_preview_entity_changes(source)
    for path, previous, current in reversed(CHANGES):
        if current in source:
            assert source.count(current) == 1, path
            source = source.replace(current, previous, 1)
    return source

def pre_card_title_input_bytes(path):
    path=Path(path);raw=path.read_bytes()
    return pre_card_title_input(raw.decode()).encode() if path.suffix == '.swift' else raw
