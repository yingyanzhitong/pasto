"""Exact header entity-observation deltas for historical frozen contracts only."""
from pathlib import Path
from popover_entity_input_scope_contract import pre_popover_entity_input
CHANGES = [['replica/Sources/PastoCore/ClipboardRestoreItem.swift',
  'import CoreData\n'
  'import Foundation\n'
  '\n'
  '/// Retains the selected entity for restoration and editing; consumers read its current content.\n',
  'import Combine\n'
  'import CoreData\n'
  'import Foundation\n'
  '\n'
  '/// Retains the selected entity for restoration and editing; consumers read its current content.\n'],
 ['replica/Sources/PastoCore/ClipboardRestoreItem.swift',
  '    public func resolvedItem() -> ClipboardItem { resolve() }\n',
  '    public var isDeleted: Bool { nativeObject?.isDeleted ?? false }\n'
  '\n'
  '    // 3c2780 publishes entity changes including deletion; the preview consumer decides how to react.\n'
  '    public func observeChanges(_ consume: @escaping (ClipboardRestoreItem) -> Void) -> AnyCancellable? {\n'
  '        guard let object = nativeObject else { return nil }\n'
  '        guard let context = object.managedObjectContext else {\n'
  '            preconditionFailure("Item observation requires a managed context")\n'
  '        }\n'
  '        let objectID = object.objectID\n'
  '        let id = self.id\n'
  '        return NotificationCenter.default\n'
  '            .publisher(for: .NSManagedObjectContextObjectsDidChange, object: context)\n'
  '            .sink { [object, context] notification in\n'
  '                MainActor.assumeIsolated {\n'
  '                    withExtendedLifetime((object, context)) {\n'
  '                        for key in [NSInsertedObjectsKey, NSUpdatedObjectsKey, NSDeletedObjectsKey, '
  'NSRefreshedObjectsKey] {\n'
  '                            let objects = notification.userInfo?[key] as? Set<NSManagedObject> ?? []\n'
  '                            guard let current = objects.first(where: { $0.objectID == objectID }) else { '
  'continue }\n'
  '                            let item = current as! PastoItemEntity\n'
  '                            consume(ClipboardRestoreItem(id: id, object: item))\n'
  '                            return\n'
  '                        }\n'
  '                    }\n'
  '                }\n'
  '            }\n'
  '    }\n'
  '\n'
  '    public func resolvedItem() -> ClipboardItem { resolve() }\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '    let header = ReplicaInlinePreviewHeader(state: state, item: item)\n'
  '    let editorHeader = ReplicaInlinePreviewEditorHeader()',
  '    let header = ReplicaInlinePreviewHeader(state: state, item: item, input: input)\n'
  '    let editorHeader = ReplicaInlinePreviewEditorHeader()'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '    let header = ReplicaInlinePreviewHeader(state: state, item: item)\n'
  '    let editorHeader = ReplicaInlinePreviewEditorHeader(document: content.document)',
  '    let header = ReplicaInlinePreviewHeader(state: state, item: item, input: input)\n'
  '    let editorHeader = ReplicaInlinePreviewEditorHeader(document: content.document)'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  'private final class ReplicaInlinePreviewHeader: NSView {\n'
  '    var onEdit: (() -> Void)?\n'
  '    var onClose: (() -> Void)?\n'
  '    let titleLabel = OriginalPreviewTitleLabel()\n'
  '    private var itemObservation: AnyCancellable?\n'
  '    private var pinboardObservation: AnyCancellable?\n'
  '    private weak var state: ReplicaUIState?\n'
  '    private let itemID: UUID\n'
  '    private var pinButton: OriginalToolbarButton?\n'
  '    private var sharingPicker: NSSharingServicePicker?\n'
  '\n'
  '    init(state: ReplicaUIState, item: ClipboardItem) {',
  'private final class ReplicaInlinePreviewHeader: NSView {\n'
  '    var onEdit: (() -> Void)?\n'
  '    var onClose: (() -> Void)?\n'
  '    let titleLabel = OriginalPreviewTitleLabel()\n'
  '    private var itemObservation: AnyCancellable?\n'
  '    private var pinboardObservation: AnyCancellable?\n'
  '    private weak var state: ReplicaUIState?\n'
  '    private let itemID: UUID\n'
  '    private var pinButton: OriginalToolbarButton?\n'
  '    private var sharingPicker: NSSharingServicePicker?\n'
  '\n'
  '    init(state: ReplicaUIState, item: ClipboardItem, input: ClipboardRestoreItem?) {'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '        itemObservation = state.store.$items.sink { [weak self, weak share] items in\n'
  '            MainActor.assumeIsolated {\n'
  '                guard let self, let current = items.first(where: { $0.id == item.id }) else { return }\n'
  '                let field = self.titleLabel.f_100013084()\n'
  '                let rawType: Int\n'
  '                switch current.kind {\n'
  '                case .unknown: rawType = 0\n'
  '                case .image: rawType = 1\n'
  '                case .color: rawType = 2\n'
  '                case .files: rawType = 3\n'
  '                case .link: rawType = 4\n'
  '                case .text, .richText: rawType = 5\n'
  '                }\n'
  '                let defaultTitle = OriginalPreviewTitles.f_100309008(rawType: rawType,\n'
  '                    fileCount: current.kind == .files ? current.decodedFilePreviewMetadata?.paths.count : '
  'nil)\n'
  '                field.f_10023b600(defaultTitle)\n'
  '                field.f_10023b214(OriginalPreviewTitles.f_100308f88(current.originalTitle, defaultTitle: '
  'defaultTitle))\n'
  '                share?.isEnabled = (try? Self.sharingContent(current))\n'
  '                    .map { OriginalPreviewSharing.f_100320cc0($0) } ?? false\n'
  '                self.refreshPinAppearance(current)\n'
  '            }\n'
  '        }\n',
  '        let update: (ClipboardItem) -> Void = { [weak self, weak share] current in\n'
  '            guard let self else { return }\n'
  '            let field = self.titleLabel.f_100013084()\n'
  '            let rawType: Int\n'
  '            switch current.kind {\n'
  '            case .unknown: rawType = 0\n'
  '            case .image: rawType = 1\n'
  '            case .color: rawType = 2\n'
  '            case .files: rawType = 3\n'
  '            case .link: rawType = 4\n'
  '            case .text, .richText: rawType = 5\n'
  '            }\n'
  '            let defaultTitle = OriginalPreviewTitles.f_100309008(rawType: rawType,\n'
  '                fileCount: current.kind == .files ? current.decodedFilePreviewMetadata?.paths.count : '
  'nil)\n'
  '            field.f_10023b600(defaultTitle)\n'
  '            field.f_10023b214(OriginalPreviewTitles.f_100308f88(current.originalTitle, defaultTitle: '
  'defaultTitle))\n'
  '            share?.isEnabled = (try? Self.sharingContent(current))\n'
  '                .map { OriginalPreviewSharing.f_100320cc0($0) } ?? false\n'
  '            self.refreshPinAppearance(current)\n'
  '        }\n'
  '        let receive: (ClipboardRestoreItem) -> Void = { [weak self] current in\n'
  '            guard let self else { return }\n'
  '            if current.isDeleted {\n'
  '                self.titleLabel.f_100011d28()\n'
  '                self.window?.performClose(nil)\n'
  '                return\n'
  '            }\n'
  '            update(current.resolvedItem())\n'
  '        }\n'
  '        itemObservation = input?.observeChanges(receive)\n'
  '        if itemObservation != nil, let input {\n'
  '            receive(input)\n'
  '        } else {\n'
  '            itemObservation = state.store.$items.sink { items in\n'
  '                MainActor.assumeIsolated {\n'
  '                    guard let current = items.first(where: { $0.id == item.id }) else { return }\n'
  '                    update(current)\n'
  '                }\n'
  '            }\n'
  '        }\n']]

def pre_preview_entity_changes(source):
    source = pre_popover_entity_input(source)
    for path, before, after in reversed(CHANGES):
        if after in source:
            assert source.count(after) == 1, path
            source = source.replace(after, before, 1)
    return source

def pre_preview_entity_changes_bytes(path):
    data = Path(path).read_bytes()
    if str(path).endswith(".swift"):
        return pre_preview_entity_changes(data.decode()).encode()
    return data
