"""Reverse only two reviewed133 empty raw-data diagnostic hunks."""
CHANGES = [['replica/Sources/PastoCore/ClipboardSearchRecord.swift',
  '        read(contentDiagnostics: contentDiagnostics) { object, items in\n'
  '            ClipboardSearchRecordContent.nativeText(items, kind: kind,',
  '        read(contentDiagnostics: contentDiagnostics) { object, items in\n'
  '            if items.isEmpty { diagnoseEmptyRepresentations(for: object) }\n'
  '            return ClipboardSearchRecordContent.nativeText(items, kind: kind,'],
 ['replica/Sources/PastoCore/ClipboardSearchRecord.swift',
  '    func imageData() -> Data? {\n',
  '    // 3724f0: this second raw read is diagnostic-only; failure must not stop typed fallback.\n'
  '    private func diagnoseEmptyRepresentations(for object: NSManagedObject) {\n'
  '        guard let data = object.value(forKey: "data") as? NSManagedObject else { return }\n'
  '        let raw = (try? OriginalObjCExceptionBridge.f_1002ffc68 {\n'
  '            guard let raw = data.value(forKey: "rawPasteboardItems") as? Data else {\n'
  '                throw CocoaError(.fileReadCorruptFile)\n'
  '            }\n'
  '            return raw\n'
  '        }) ?? Data()\n'
  '        let prefix = raw.prefix(6).map { String(format: "%02x", $0) }.joined()\n'
  '        contentDiagnostics.f_1000d468c().f_1000d4df0(\n'
  '            "Item has no pasteboard data for content indexing (type: \\(kind), rawSize: '
  '\\(raw.count), rawPrefix: \\(prefix))")\n'
  '    }\n'
  '\n'
  '    func imageData() -> Data? {\n']]

def pre_empty_data_diagnostic(source):
    from empty_content_diagnostic_scope_contract import pre_empty_content_diagnostic
    source=pre_empty_content_diagnostic(source)
    for _,old,new in reversed(CHANGES):
        if new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    return source
