"""Exact captured-entity text-write deltas for earlier frozen source contracts only."""
from pathlib import Path
from native_title_write_scope_contract import pre_native_title_write
CHANGES = [['replica/Sources/PastoCore/ClipboardRestoreItem.swift',
  '    public let id: UUID\n',
  '    public let id: UUID\n    let nativeObject: PastoItemEntity?\n'],
 ['replica/Sources/PastoCore/ClipboardRestoreItem.swift',
  '        self.id = id\n',
  '        self.id = id\n        nativeObject = object\n'],
 ['replica/Sources/PastoCore/ClipboardRestoreItem.swift',
  '        id = item.id\n',
  '        id = item.id\n        nativeObject = nil\n'],
 ['replica/Sources/PastoCore/ClipboardStore.swift',
  '    public func updateTextPreviewItem(id: UUID, attributedString: NSAttributedString) throws {\n'
  '        try mutateInTransaction { state, transaction in\n'
  '            guard let i = state.items.firstIndex(where: { $0.id == id }) else { throw '
  'ClipboardStoreError.itemNotFound }\n'
  '            let representation = OriginalTextPreviewSubmission.makeItem(attributedString)\n'
  '            let items = [representation]\n'
  '            let nativeKind = OriginalPasteboardClassification.f_10032362c(items)\n'
  '            guard let checksum = OriginalPasteboardChecksums.f_1003216bc(items, kind: '
  'nativeKind) else { return }\n'
  '            let types = representation.f_10037da6c()\n'
  '            var payloads: [String: Data] = [:]\n'
  '            for type in types {\n'
  '                if let data = representation.f_10037d810(forType: type) { payloads[type] = data '
  '}\n'
  '            }\n'
  '            payloads[Self.orderedPasteboardTypesPayloadKey] = try JSONEncoder().encode(types)\n'
  '            let kind: ClipboardKind\n'
  '            switch nativeKind {\n'
  '            case .unknown: kind = .unknown\n'
  '            case .image: kind = .image\n'
  '            case .color: kind = .color\n'
  '            case .files: kind = .files\n'
  '            case .link: kind = .link\n'
  '            case .text: kind = types.contains(NSPasteboard.PasteboardType.rtf.rawValue) ? '
  '.richText : .text\n'
  '            }\n'
  '            let target = try transaction.repository.prepareHistoryItems([id]).first!\n'
  '            var item = state.items[i]\n'
  '            item.payloads = payloads\n'
  '            item.plainText = attributedString.string\n'
  '            item.kind = kind\n'
  '            item.imagePreviewMetadata = nil\n'
  '            item.rawPreview = nil\n'
  '            // Keep the local conflict clock; the native history timestamp is unchanged.\n'
  '            item.updatedAt = Date()\n'
  '            item.nativeChecksum = checksum\n'
  '            let preferences = state.preferences\n'
  '            // Editing shares 0x100360ff8 with capture: replace data before producing its '
  'preview.\n'
  '            transaction.repository.replaceCapturedItemData(target, items: items, kind: '
  'nativeKind, checksum: checksum,\n'
  '                useBinaryPlist: preferences.useBinaryPlist) {\n'
  '                    item = Self.withPreviewMetadata(item, binaryPropertyList: '
  'preferences.useBinaryPlist,\n'
  '                        preferQuickLookThumbnails: preferences.fileQuickLookThumbnailsEnabled,\n'
  '                        generateMissingContentPreview: true)\n'
  '                    return item.rawPreview\n'
  '                }\n'
  '            state.items[i] = item\n'
  '        }\n'
  '    }\n'
  '\n',
  '    public func updateTextPreviewItem(id: UUID, attributedString: NSAttributedString) throws {\n'
  '        try updateTextPreviewItem(id: id, input: nil, attributedString: attributedString)\n'
  '    }\n'
  '\n'
  '    public func updateTextPreviewItem(_ input: ClipboardRestoreItem, attributedString: '
  'NSAttributedString) throws {\n'
  '        try updateTextPreviewItem(id: input.id, input: input, attributedString: '
  'attributedString)\n'
  '    }\n'
  '\n'
  '    private func updateTextPreviewItem(id: UUID, input: ClipboardRestoreItem?, '
  'attributedString: NSAttributedString) throws {\n'
  '        try mutateInTransaction { state, transaction in\n'
  '            let nativeObject = input?.nativeObject\n'
  '            var index = state.items.firstIndex(where: { $0.id == id })\n'
  '            guard nativeObject != nil || index != nil else { throw '
  'ClipboardStoreError.itemNotFound }\n'
  '            let representation = OriginalTextPreviewSubmission.makeItem(attributedString)\n'
  '            let items = [representation]\n'
  '            let nativeKind = OriginalPasteboardClassification.f_10032362c(items)\n'
  '            guard let checksum = OriginalPasteboardChecksums.f_1003216bc(items, kind: '
  'nativeKind) else { return }\n'
  '            let types = representation.f_10037da6c()\n'
  '            var payloads: [String: Data] = [:]\n'
  '            for type in types {\n'
  '                if let data = representation.f_10037d810(forType: type) { payloads[type] = data '
  '}\n'
  '            }\n'
  '            payloads[Self.orderedPasteboardTypesPayloadKey] = try JSONEncoder().encode(types)\n'
  '            let kind: ClipboardKind\n'
  '            switch nativeKind {\n'
  '            case .unknown: kind = .unknown\n'
  '            case .image: kind = .image\n'
  '            case .color: kind = .color\n'
  '            case .files: kind = .files\n'
  '            case .link: kind = .link\n'
  '            case .text: kind = types.contains(NSPasteboard.PasteboardType.rtf.rawValue) ? '
  '.richText : .text\n'
  '            }\n'
  '            let target: (id: UUID, object: NSManagedObject)\n'
  '            var item: ClipboardItem\n'
  '            if let nativeObject, let input {\n'
  '                target = (id: id, object: nativeObject)\n'
  '                item = input.resolvedItem()\n'
  '                if index == nil {\n'
  '                    index = state.items.count\n'
  '                    state.items.append(item)\n'
  '                }\n'
  '            } else {\n'
  '                target = try transaction.repository.prepareHistoryItems([id]).first!\n'
  '                item = state.items[index!]\n'
  '            }\n'
  '            let i = index!\n'
  '            item.payloads = payloads\n'
  '            item.plainText = attributedString.string\n'
  '            item.kind = kind\n'
  '            item.imagePreviewMetadata = nil\n'
  '            item.rawPreview = nil\n'
  '            // Keep the local conflict clock; the native history timestamp is unchanged.\n'
  '            item.updatedAt = Date()\n'
  '            item.nativeChecksum = checksum\n'
  '            let preferences = state.preferences\n'
  '            // Editing shares 0x100360ff8 with capture: replace data before producing its '
  'preview.\n'
  '            transaction.repository.replaceCapturedItemData(target, items: items, kind: '
  'nativeKind, checksum: checksum,\n'
  '                useBinaryPlist: preferences.useBinaryPlist) {\n'
  '                    item = Self.withPreviewMetadata(item, binaryPropertyList: '
  'preferences.useBinaryPlist,\n'
  '                        preferQuickLookThumbnails: preferences.fileQuickLookThumbnailsEnabled,\n'
  '                        generateMissingContentPreview: true)\n'
  '                    return item.rawPreview\n'
  '                }\n'
  '            state.items[i] = item\n'
  '        }\n'
  '    }\n'
  '\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '    private let itemID: UUID\n'
  '    private var nativeItemObservation: ClipboardItemObservation?\n',
  '    private let itemID: UUID\n'
  '    private let editInput: ClipboardRestoreItem?\n'
  '    private var nativeItemObservation: ClipboardItemObservation?\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '        itemID = item.id\n        let nativeSource: ClipboardItemObservation?\n',
  '        itemID = item.id\n'
  '        editInput = input\n'
  '        let nativeSource: ClipboardItemObservation?\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '    func commitPreviewEditing() {\n'
  '        text.isEditable = false\n'
  '        guard let state else { return }\n'
  '        do {\n'
  '            try state.store.updateTextPreviewItem(id: itemID,\n'
  '                attributedString: OriginalPreviewAttributedText.f_100212ccc(editor: text))\n'
  '            state.normalizeSelection()\n'
  '        } catch { state.controller?.presentError(error) }\n'
  '        reloadStoredContent()\n'
  '    }\n',
  '    func commitPreviewEditing() {\n'
  '        text.isEditable = false\n'
  '        guard let state else { return }\n'
  '        do {\n'
  '            let content = OriginalPreviewAttributedText.f_100212ccc(editor: text)\n'
  '            if let editInput {\n'
  '                try state.store.updateTextPreviewItem(editInput, attributedString: content)\n'
  '            } else {\n'
  '                try state.store.updateTextPreviewItem(id: itemID, attributedString: content)\n'
  '            }\n'
  '            state.normalizeSelection()\n'
  '        } catch { state.controller?.presentError(error) }\n'
  '        reloadStoredContent()\n'
  '    }\n'],
 ('replica/Sources/PastoCore/ClipboardStore.swift',
  '            // Keep the local conflict clock; the native history timestamp is unchanged.\n'
  '            item.updatedAt = Date()\n',
  '            // Native content replacement preserves recency; retain the old value-only '
  "adapter's clock.\n"
  '            if nativeObject == nil { item.updatedAt = Date() }\n')]

def pre_native_edit_write(source):
    source = pre_native_title_write(source)
    for path, previous, current in reversed(CHANGES):
        if current in source:
            assert source.count(current) == 1, path
            source = source.replace(current, previous, 1)
    return source

def pre_native_edit_write_bytes(path):
    path=Path(path);raw=path.read_bytes()
    return pre_native_edit_write(raw.decode()).encode() if path.suffix == '.swift' else raw
