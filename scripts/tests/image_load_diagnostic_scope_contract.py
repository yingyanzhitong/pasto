"""Isolate only reviewed156 image existing-object failure local warning and actual image caller."""
CHANGES = [['replica/Sources/PastoCore/ClipboardSearchRecord.swift',
  '    private func read<T>(contentDiagnostics: OriginalNamedDiagnostic? = nil,\n'
  '                         _ project:',
  '    private func read<T>(contentDiagnostics: OriginalNamedDiagnostic? = nil,\n'
  '                         imageDiagnostics: OriginalNamedDiagnostic? = nil,\n'
  '                         _ project:',
  1],
 ['replica/Sources/PastoCore/ClipboardSearchRecord.swift',
  '                        guard let contentDiagnostics else { throw error }\n',
  '                        guard let contentDiagnostics else {\n'
  '                            if let imageDiagnostics {\n'
  '                                imageDiagnostics.f_1000d468c().f_1000d4df0("Failed to load '
  'image content: \\(error.localizedDescription)")\n'
  '                                return nil\n'
  '                            }\n'
  '                            throw error\n'
  '                        }\n',
  1],
 ['replica/Sources/PastoCore/ClipboardSearchRecord.swift',
  '        read { _, items in items.compactMap { $0.f_10037d5c4() }.first }',
  '        read(imageDiagnostics: contentDiagnostics) { _, items in items.compactMap { '
  '$0.f_10037d5c4() }.first }',
  1]]

def pre_image_load_diagnostic(source):
    from preview_commit_error_scope_contract import pre_preview_commit_error
    source=pre_preview_commit_error(source)
    for _,old,new,count in reversed(CHANGES):
        if new in source:
            assert source.count(new)==count
            source=source.replace(new,old)
    return source

def pre_image_load_diagnostic_bytes(path):
    data=path.read_bytes()
    return pre_image_load_diagnostic(data.decode()).encode()if path.suffix=='.swift'else data
