"""Exact native preview header metadata deltas for historical contracts only."""
from pathlib import Path
from text_preview_creation_scope_contract import pre_text_preview_creation
CHANGES = [['replica/Sources/PastoCore/ClipboardItemDataPersistence.swift',
  '    // 0x100360ff8: type/checksum, delete old data, create/encode replacement,\n',
  '    // 31b218: raw getter exceptions yield no representations; invalid local graphs stay optional.\n'
  '    @MainActor static func readItems(from object: PastoItemEntity) -> [OriginalPasteboardItem]? {\n'
  '        guard let data = object.value(forKey: "data") as? NSManagedObject else { return nil }\n'
  '        let raw: Data\n'
  '        do {\n'
  '            raw = try OriginalObjCExceptionBridge.f_1002ffc68 {\n'
  '                guard let raw = data.value(forKey: "rawPasteboardItems") as? Data else {\n'
  '                    throw CocoaError(.fileReadCorruptFile)\n'
  '                }\n'
  '                return raw\n'
  '            }\n'
  '        } catch is OriginalObjCExceptionError {\n'
  '            return []\n'
  '        } catch { return nil }\n'
  '        return autoreleasepool { OriginalPasteboardDataCodec.f_10031aeec(raw) }\n'
  '    }\n'
  '\n'
  '    // 0x100360ff8: type/checksum, delete old data, create/encode replacement,\n'],
 ['replica/Sources/PastoCore/ClipboardItemObservation.swift',
  '        guard let data = object.value(forKey: "data") as? NSManagedObject else { return nil }\n'
  '        let raw: Data\n'
  '        do {\n'
  '            raw = try OriginalObjCExceptionBridge.f_1002ffc68 {\n'
  '                guard let raw = data.value(forKey: "rawPasteboardItems") as? Data else {\n'
  '                    throw CocoaError(.fileReadCorruptFile)\n'
  '                }\n'
  '                return raw\n'
  '            }\n'
  '        } catch is OriginalObjCExceptionError {\n'
  '            return NSAttributedString(string: "")\n'
  '        } catch { return nil }\n'
  '        let items = autoreleasepool { OriginalPasteboardDataCodec.f_10031aeec(raw) }\n',
  '        guard let items = ClipboardItemDataPersistence.readItems(from: object) else { return nil }\n'],
 ['replica/Sources/PastoCore/ClipboardRestoreItem.swift',
  '    public func resolvedItem() -> ClipboardItem { resolve() }\n',
  '    // 309008/308f88 read title/type/preview, independently of archived value content.\n'
  '    public func previewTitle() -> (defaultTitle: String, title: String)? {\n'
  '        guard let object = nativeObject else { return nil }\n'
  '        let rawType = (object.value(forKey: "rawType") as? NSNumber)?.intValue ?? 0\n'
  '        let count = rawType == 3\n'
  '            ? OriginalImagePreviewMetadataCodec.decodeFiles(object.value(forKey: "rawPreview") as? '
  'Data)?.paths.count : nil\n'
  '        let defaultTitle = OriginalPreviewTitles.f_100309008(rawType: rawType, fileCount: count)\n'
  '        return (defaultTitle, OriginalPreviewTitles.f_100308f88(object.value(forKey: "title") as? '
  'String,\n'
  '                                                             defaultTitle: defaultTitle))\n'
  '    }\n'
  '\n'
  '    // 31bc94/3250f0 filter the native owner by rawType before reading its attributes.\n'
  '    public func previewPinboard() -> (isPinned: Bool, colorCode: UInt64?)? {\n'
  '        guard let object = nativeObject else { return nil }\n'
  '        guard let list = object.value(forKey: "list") as? NSManagedObject,\n'
  '              (list.value(forKey: "rawType") as? NSNumber)?.int64Value == 2 else { return (false, nil) }\n'
  '        return (true, OriginalPinboardAttributes.colorCode(from: list.value(forKey: "rawAttributes") as? '
  'Data))\n'
  '    }\n'
  '\n'
  '    public func previewSharingContent() -> OriginalPreviewSharing.Content? {\n'
  '        guard let object = nativeObject else { return nil }\n'
  '        let rawType = (object.value(forKey: "rawType") as? NSNumber)?.intValue ?? 0\n'
  '        return .init(items: ClipboardItemDataPersistence.readItems(from: object) ?? [], rawType: '
  'rawType)\n'
  '    }\n'
  '\n'
  '    public func resolvedItem() -> ClipboardItem { resolve() }\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '    private var sharingPicker: NSSharingServicePicker?\n',
  '    private var sharingPicker: NSSharingServicePicker?\n    private let input: ClipboardRestoreItem?\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '    init(state: ReplicaUIState, item: ClipboardItem, input: ClipboardRestoreItem?) {\n'
  '        self.state = state\n'
  '        itemID = item.id\n'
  '        super.init(frame: .zero)\n',
  '    init(state: ReplicaUIState, item: ClipboardItem, input: ClipboardRestoreItem?) {\n'
  '        self.state = state\n'
  '        itemID = item.id\n'
  '        self.input = input\n'
  '        super.init(frame: .zero)\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '        let receive: (ClipboardRestoreItem) -> Void = { [weak self] current in\n',
  '        let receive: (ClipboardRestoreItem) -> Void = { [weak self, weak share] current in\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '            update(current.resolvedItem())\n'
  '        }\n'
  '        itemObservation = input?.observeChanges(receive)\n',
  '            if let title = current.previewTitle() {\n'
  '                let field = self.titleLabel.f_100013084()\n'
  '                field.f_10023b600(title.defaultTitle)\n'
  '                field.f_10023b214(title.title)\n'
  '                if let pin = current.previewPinboard() {\n'
  '                    self.refreshNativePinAppearance(isPinned: pin.isPinned, colorCode: pin.colorCode)\n'
  '                }\n'
  '                share?.isEnabled = '
  'current.previewSharingContent().map(OriginalPreviewSharing.f_100320cc0) ?? false\n'
  '            } else {\n'
  '                update(current.resolvedItem())\n'
  '            }\n'
  '        }\n'
  '        itemObservation = input?.observeChanges(receive)\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '                guard let self, let item = self.state?.store.items.first(where: { $0.id == self.itemID }) '
  'else { return }\n'
  '                self.refreshPinAppearance(item, boards: boards)\n',
  '                guard let self, self.input?.isDeleted != true else { return }\n'
  '                if let pin = self.input?.previewPinboard() {\n'
  '                    self.refreshNativePinAppearance(isPinned: pin.isPinned, colorCode: pin.colorCode)\n'
  '                } else if let item = self.state?.store.items.first(where: { $0.id == self.itemID }) {\n'
  '                    self.refreshPinAppearance(item, boards: boards)\n'
  '                }\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '    private func refreshPinAppearance(_ item: ClipboardItem, boards: [Pinboard]? = nil) {\n',
  '    private func refreshNativePinAppearance(isPinned: Bool, colorCode: UInt64?) {\n'
  '        pinButton?.symbol = isPinned ? "circle.fill" : "circle.dashed"\n'
  '        pinButton?.contentTintColor = colorCode.map { OriginalPinboardColor(canonicalColorCode: '
  '$0).color() }\n'
  '    }\n'
  '\n'
  '    private func refreshPinAppearance(_ item: ClipboardItem, boards: [Pinboard]? = nil) {\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '    private func showSharingPicker(from button: NSButton) {\n'
  '        guard let state, let item = state.store.items.first(where: { $0.id == itemID }) else { return }\n',
  '    private func showSharingPicker(from button: NSButton) {\n'
  '        if let content = input?.previewSharingContent() {\n'
  '            let picker = OriginalPreviewSharing.f_1000183e0([content])\n'
  '            sharingPicker = picker\n'
  '            picker.show(relativeTo: .zero, of: button, preferredEdge: .minY)\n'
  '            return\n'
  '        }\n'
  '        guard let state, let item = state.store.items.first(where: { $0.id == itemID }) else { return '
  '}\n']]

def pre_native_preview_header(source):
    source=pre_text_preview_creation(source)
    for path, before, after in reversed(CHANGES):
        if after in source:
            assert source.count(after) == 1, path
            source = source.replace(after, before, 1)
    return source

def pre_native_preview_header_bytes(path):
    data = Path(path).read_bytes()
    if str(path).endswith(".swift"):
        return pre_native_preview_header(data.decode()).encode()
    return data
