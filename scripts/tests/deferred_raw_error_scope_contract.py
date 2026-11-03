"""Reverse only reviewed131 shared raw getter/search continuation deltas."""
CHANGES = [['replica/Sources/PastoCore/ClipboardItemDataPersistence.swift',
  '    @MainActor static func readItems(from object: PastoItemEntity) -> [OriginalPasteboardItem]? '
  '{\n'
  '        guard let data = object.value(forKey: "data") as? NSManagedObject else { return nil }\n'
  '        let raw: Data',
  '    @MainActor static func readItems(from object: PastoItemEntity) -> [OriginalPasteboardItem]? '
  '{\n'
  '        guard let data = object.value(forKey: "data") as? NSManagedObject else { return nil }\n'
  '        return readRepresentations(from: data) { diagnostics(for: data) }\n'
  '    }\n'
  '\n'
  "    // 31b218 is also called from a search reader's private context. Invoke on its owning "
  'queue.\n'
  '    static func readRepresentations(from data: NSManagedObject,\n'
  '                                    diagnostics: () -> OriginalNamedDiagnostic) -> '
  '[OriginalPasteboardItem]? {\n'
  '        let raw: Data'],
 ['replica/Sources/PastoCore/ClipboardItemDataPersistence.swift',
  '            diagnostics(for: data).f_1000d468c().f_1000d4e0c("Unreadable pasteboard items blob: '
  '\\(error)")',
  '            diagnostics().f_1000d468c().f_1000d4e0c("Unreadable pasteboard items blob: '
  '\\(error)")'],
 ['replica/Sources/PastoCore/ClipboardSearchRecord.swift',
  '                    guard object.entity.name == "Item", !object.isDeleted,\n'
  '                          let data = object.value(forKey: "data") as? NSManagedObject,\n'
  '                          let raw = data.value(forKey: "rawPasteboardItems") as? Data else { '
  'return nil }\n'
  '                    return try project(object, OriginalPasteboardDataCodec.f_10031aeec(raw))',
  '                    guard object.entity.name == "Item", !object.isDeleted,\n'
  '                          let data = object.value(forKey: "data") as? NSManagedObject else { '
  'return nil }\n'
  '                    guard let items = ClipboardItemDataPersistence.readRepresentations(from: '
  'data, diagnostics: {\n'
  '                        // This private context/data object is created once for this deferred '
  'read.\n'
  '                        OriginalNamedDiagnostic.f_1000d4624(name: "ItemDataEntity")\n'
  '                    }) else { return nil }\n'
  '                    return try project(object, items)']]

def pre_deferred_raw_error(source):
    from content_load_diagnostic_scope_contract import pre_content_load_diagnostic
    source=pre_content_load_diagnostic(source)
    for _,old,new in reversed(CHANGES):
        if new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    return source
