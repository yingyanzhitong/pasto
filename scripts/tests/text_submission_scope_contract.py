"""Exact native text submission deltas, for frozen earlier source contracts only."""
from pathlib import Path
from item_observation_scope_contract import pre_item_observation

CHANGES = [['replica/Sources/PastoCore/ClipboardStore.swift',
  '    public func updateTextPreviewItem(id: UUID, attributedString: NSAttributedString) throws {\n'
  '        let representation = OriginalTextPreviewSubmission.makeItem(attributedString)\n'
  '        let types = representation.f_10037da6c()\n'
  '        var payloads: [String: Data] = [:]\n'
  '        for type in types {\n'
  '            if let data = representation.f_10037d810(forType: type) { payloads[type] = data }\n'
  '        }\n'
  '        payloads[Self.orderedPasteboardTypesPayloadKey] = try JSONEncoder().encode(types)\n'
  '        let kind: ClipboardKind\n'
  '        switch OriginalPasteboardClassification.f_10032362c([representation]) {\n'
  '        case .unknown: kind = .unknown\n'
  '        case .image: kind = .image\n'
  '        case .color: kind = .color\n'
  '        case .files: kind = .files\n'
  '        case .link: kind = .link\n'
  '        case .text: kind = types.contains(NSPasteboard.PasteboardType.rtf.rawValue) ? .richText '
  ': .text\n'
  '        }\n'
  '        try mutate { state in\n'
  '            guard let i = state.items.firstIndex(where: { $0.id == id }) else { throw '
  'ClipboardStoreError.itemNotFound }\n'
  '            var item = state.items[i]\n'
  '            item.payloads = payloads\n'
  '            item.plainText = attributedString.string\n'
  '            item.kind = kind\n'
  '            item.imagePreviewMetadata = nil\n'
  '            item.rawPreview = nil\n'
  '            item.updatedAt = Date()\n'
  '            Self.refreshNativeChecksum(&item)\n'
  '            state.items[i] = Self.withPreviewMetadata(item, binaryPropertyList: '
  'state.preferences.useBinaryPlist,\n'
  '                preferQuickLookThumbnails: state.preferences.fileQuickLookThumbnailsEnabled, '
  'generateMissingContentPreview: true)\n'
  '        }\n'
  '    }\n'
  '\n',
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
  '\n'],
 ['replica/Sources/PastoCore/OriginalTextPreviewSubmission.swift',
  '            isRich = true\n            stop.pointee = true\n            return\n',
  '            isRich = true\n            stop.pointee = true\n']]

def pre_text_submission(source):
    source = pre_item_observation(source)
    for path, previous, current in reversed(CHANGES):
        if current in source:
            assert source.count(current) == 1, path
            source = source.replace(current, previous, 1)
    return source

def pre_text_submission_bytes(path):
    path=Path(path);raw=path.read_bytes()
    return pre_text_submission(raw.decode()).encode() if path.suffix == '.swift' else raw
