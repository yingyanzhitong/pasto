"""Reverse only reviewed130 native search metadata/content deltas for historical evidence."""
from deferred_raw_error_scope_contract import pre_deferred_raw_error
CHANGES = [['replica/Sources/PastoCore/ClipboardSearchRecord.swift',
  '    static func make(_ value: ClipboardItem, nativeIdentifier: String?, kind: '
  'OriginalPasteboardContentKind,',
  '    static func make(id: UUID, originalTitle: String?, nativeIdentifier: String?, kind: '
  'OriginalPasteboardContentKind,'],
 ['replica/Sources/PastoCore/ClipboardSearchRecord.swift',
  '        return Self(id: value.id, nativeIdentifier: nativeIdentifier, type: name,\n'
  '                    title: value.originalTitle ?? name,',
  '        return Self(id: id, nativeIdentifier: nativeIdentifier, type: name,\n'
  '                    title: originalTitle ?? name,'],
 ['replica/Sources/PastoCore/ClipboardSearchRecord.swift',
  '        return make(value, nativeIdentifier: value.nativeIdentifier, kind: kind,',
  '        return make(id: value.id, originalTitle: value.originalTitle, nativeIdentifier: '
  'value.nativeIdentifier, kind: kind,'],
 ['replica/Sources/PastoCore/ClipboardSearchRecord.swift',
  '    // 0x1003724f0: normal unknown/text content uses all nonnil strings, in input order.',
  '    // 3724f0: native empty content consults typed metadata, never the compatibility value '
  'archive.\n'
  '    static func nativeText(_ items: [OriginalPasteboardItem], kind: '
  'OriginalPasteboardContentKind,\n'
  '                           preview: Data?) -> String? {\n'
  '        // Reuse primary extraction; this closure supplies no archived fallback.\n'
  '        guard let value = text(items, kind: kind, preview: preview, legacyPreviewFallback: { "" '
  '}) else { return nil }\n'
  '        guard value.isEmpty else { return value }\n'
  '        guard kind != .unknown else { return nil }\n'
  '        let fallback: String?\n'
  '        if let metadata = OriginalImagePreviewMetadataCodec.decodeText(preview) {\n'
  '            // The stored sample may be truncated. Recover the full first rich/plain '
  'representation.\n'
  '            guard metadata.length != 0 else { return nil }\n'
  '            fallback = items.first?.f_10037d33c()?.string\n'
  '        } else if let metadata = OriginalImagePreviewMetadataCodec.decodeLink(preview) {\n'
  '            guard !metadata.url.absoluteString.isEmpty else { return nil }\n'
  '            var values = [metadata.url.absoluteString]\n'
  '            if let name = metadata.name { values.append(name) }\n'
  '            fallback = values.joined(separator: " ")\n'
  '        } else if OriginalImagePreviewMetadataCodec.decode(preview) != nil\n'
  '                    || OriginalImagePreviewMetadataCodec.decodeColor(preview) != nil {\n'
  '            fallback = nil\n'
  '        } else if let metadata = OriginalImagePreviewMetadataCodec.decodeFiles(preview) {\n'
  '            guard !metadata.paths.joined().isEmpty else { return nil }\n'
  '            fallback = metadata.paths.joined(separator: " ")\n'
  '        } else { return nil }\n'
  '        guard let fallback, !fallback.isEmpty else { return value }\n'
  '        return fallback\n'
  '    }\n'
  '\n'
  '    // 0x1003724f0: normal unknown/text content uses all nonnil strings, in input order.'],
 ['replica/Sources/PastoCore/ClipboardSearchRecord.swift',
  '            ClipboardSearchRecordContent.text(items, kind: kind, preview: object.value(forKey: '
  '"rawPreview") as? Data) {\n'
  '                guard let raw = object.value(forKey: "content") as? Data else { return nil }\n'
  '                return (try? PropertyListDecoder().decode(ClipboardItem.self, from: '
  'raw))?.plainText\n'
  '            }',
  '            ClipboardSearchRecordContent.nativeText(items, kind: kind,\n'
  '                preview: object.value(forKey: "rawPreview") as? Data)'],
 ['replica/Sources/PastoCore/ClipboardSnapshotReader.swift',
  '                var value = try ClipboardPersistence.decode(ClipboardItem.self, object)\n'
  '                ClipboardItemTitlePersistence.project(&value, from: object)\n'
  '                let rawType',
  '                // Local cache identity/date columns remain required; content is deferred '
  'native data.\n'
  '                guard let key = object.value(forKey: "key") as? String, let id = '
  'UUID(uuidString: key),\n'
  '                      let contentVersion = object.value(forKey: "updatedAt") as? Date else {\n'
  '                    throw CocoaError(.fileReadCorruptFile)\n'
  '                }\n'
  '                let rawType'],
 ['replica/Sources/PastoCore/ClipboardSnapshotReader.swift',
  '                return ClipboardSearchRecord.make(value, nativeIdentifier: object.value(forKey: '
  '"nativeIdentifier") as? String,',
  '                return ClipboardSearchRecord.make(id: id, originalTitle: object.value(forKey: '
  '"title") as? String,\n'
  '                    nativeIdentifier: object.value(forKey: "nativeIdentifier") as? String,'],
 ['replica/Sources/PastoCore/ClipboardSnapshotReader.swift',
  '                    pinboard: pinboard, contentVersion: object.value(forKey: "updatedAt") as? '
  'Date ?? value.updatedAt,',
  '                    pinboard: pinboard, contentVersion: contentVersion,']]

def pre_native_search_content(source):
    source=pre_deferred_raw_error(source)
    for _,old,new in reversed(CHANGES):
        if new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    return source

def pre_native_search_content_bytes(path):
    data=path.read_bytes()
    return pre_native_search_content(data.decode()).encode() if path.suffix==".swift" else data
