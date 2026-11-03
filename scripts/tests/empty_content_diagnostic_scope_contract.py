"""Reverse only eight reviewed134 detailed empty-content diagnostic hunks."""
CHANGES = [['replica/Sources/PastoCore/ClipboardSearchRecord.swift',
  '    static func nativeText(_ items: [OriginalPasteboardItem], kind: '
  'OriginalPasteboardContentKind,\n'
  '                           preview: Data?) -> String? {',
  '    static func nativeText(_ items: [OriginalPasteboardItem], kind: '
  'OriginalPasteboardContentKind,\n'
  '                           preview: Data?, diagnoseEmpty: ((Int, String?) -> Void)? = nil) -> '
  'String? {'],
 ['replica/Sources/PastoCore/ClipboardSearchRecord.swift',
  '        let fallback: String?\n        if let metadata',
  '        let fallback: String?\n        let previewLength: Int\n        if let metadata'],
 ['replica/Sources/PastoCore/ClipboardSearchRecord.swift',
  '            guard metadata.length != 0 else { return nil }\n            fallback',
  '            guard metadata.length != 0 else { return nil }\n'
  '            previewLength = metadata.length\n'
  '            fallback'],
 ['replica/Sources/PastoCore/ClipboardSearchRecord.swift',
  '            guard !metadata.url.absoluteString.isEmpty else { return nil }\n'
  '            var values',
  '            guard !metadata.url.absoluteString.isEmpty else { return nil }\n'
  '            previewLength = metadata.url.absoluteString.count\n'
  '            var values'],
 ['replica/Sources/PastoCore/ClipboardSearchRecord.swift',
  '                    || OriginalImagePreviewMetadataCodec.decodeColor(preview) != nil {\n'
  '            fallback = nil',
  '                    || OriginalImagePreviewMetadataCodec.decodeColor(preview) != nil {\n'
  '            previewLength = -1\n'
  '            fallback = nil'],
 ['replica/Sources/PastoCore/ClipboardSearchRecord.swift',
  '            guard !metadata.paths.joined().isEmpty else { return nil }\n'
  '            fallback = metadata.paths.joined(separator: " ")\n'
  '        } else { return nil }\n'
  '        guard let fallback',
  '            let joinedPaths = metadata.paths.joined()\n'
  '            guard !joinedPaths.isEmpty else { return nil }\n'
  '            previewLength = joinedPaths.count\n'
  '            fallback = metadata.paths.joined(separator: " ")\n'
  '        } else { return nil }\n'
  '        diagnoseEmpty?(previewLength, fallback)\n'
  '        guard let fallback'],
 ['replica/Sources/PastoCore/ClipboardSearchRecord.swift',
  '            return ClipboardSearchRecordContent.nativeText(items, kind: kind,\n'
  '                preview: object.value(forKey: "rawPreview") as? Data)',
  '            return ClipboardSearchRecordContent.nativeText(items, kind: kind,\n'
  '                preview: object.value(forKey: "rawPreview") as? Data, diagnoseEmpty: { '
  'previewLength, fallback in\n'
  '                    self.diagnoseEmptyContent(for: object, items: items, previewLength: '
  'previewLength, fallback: fallback)\n'
  '                })'],
 ['replica/Sources/PastoCore/ClipboardSearchRecord.swift',
  '    func imageData() -> Data? {\n',
  '    // 374e84: sample five items and ten ordered types per item, including repeated/missing '
  'types.\n'
  '    private func diagnoseEmptyContent(for object: NSManagedObject, items: '
  '[OriginalPasteboardItem],\n'
  '                                      previewLength: Int, fallback: String?) {\n'
  '        guard let identifier = (object.value(forKey: "nativeIdentifier") as? String)\n'
  '                    ?? (object.value(forKey: "key") as? String),\n'
  '              let created = object.value(forKey: "createdAt") as? Date else { return }\n'
  '        let application = object.value(forKey: "sourceApplication") as? NSManagedObject\n'
  '        let app = application?.value(forKey: "name") as? String ?? "nil"\n'
  '        let types = items.prefix(5).enumerated().map { index, item in\n'
  '            let values = item.f_10037da6c().prefix(10).map { type in\n'
  '                "\\(type):\\(item.f_10037d810(forType: type)?.count ?? 0)"\n'
  '            }.joined(separator: ", ")\n'
  '            return "item[\\(index)]={\\(values)}"\n'
  '        }.joined(separator: "; ")\n'
  '        let usedPreviewFallback = fallback.map { !$0.isEmpty } ?? false\n'
  '        let synced = hasObjectMetadata(for: object)\n'
  '        contentDiagnostics.f_1000d468c().f_1000d4df0(\n'
  '            "Item content resolved to empty string (id: \\(identifier), type: \\(kind), app: '
  '\\(app), synced: \\(synced), created: \\(created), previewLength: \\(previewLength), '
  'usedPreviewFallback: \\(usedPreviewFallback), types: \\(types))")\n'
  '    }\n'
  '\n'
  '    // 38efa8 → 328980 is a local fetch. An offline model without this entity has no such '
  'records.\n'
  '    private func hasObjectMetadata(for object: NSManagedObject) -> Bool {\n'
  '        guard let context = object.managedObjectContext,\n'
  '              let entity = '
  'context.persistentStoreCoordinator?.managedObjectModel.entitiesByName["ObjectMetadata"] else {\n'
  '            return false\n'
  '        }\n'
  '        let request = NSFetchRequest<NSManagedObject>()\n'
  '        request.entity = entity\n'
  '        request.predicate = NSPredicate(format: "objectURI == %@", '
  'object.objectID.uriRepresentation().absoluteString)\n'
  '        request.fetchLimit = 1\n'
  '        request.fetchOffset = 0\n'
  '        return (try? context.fetch(request).first) != nil\n'
  '    }\n'
  '\n'
  '    func imageData() -> Data? {\n']]

def pre_empty_content_diagnostic(source):
    from supplied_preview_input_scope_contract import pre_supplied_preview_input
    source=pre_supplied_preview_input(source)
    for _,old,new in reversed(CHANGES):
        if new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    return source
