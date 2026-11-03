"""Reverse only four reviewed132 content-load diagnostic hunks for historical contracts."""
CHANGES = [['replica/Sources/PastoCore/ClipboardSearchRecord.swift',
  '    private let logger = Logger(',
  '    private let contentDiagnostics = OriginalNamedDiagnostic.f_1000d4624(name: '
  '"init(_:coordinator:)")\n'
  '    private let logger = Logger('],
 ['replica/Sources/PastoCore/ClipboardSearchRecord.swift',
  '    private func read<T>(_ project: (NSManagedObject, [OriginalPasteboardItem]) throws -> T?) '
  '-> T? {',
  '    private func read<T>(contentDiagnostics: OriginalNamedDiagnostic? = nil,\n'
  '                         _ project: (NSManagedObject, [OriginalPasteboardItem]) throws -> T?) '
  '-> T? {'],
 ['replica/Sources/PastoCore/ClipboardSearchRecord.swift',
  '                    let object = try context.existingObject(with: objectID)\n'
  '                    guard object.entity.name == "Item", !object.isDeleted,\n'
  '                          let data = object.value(forKey: "data") as? NSManagedObject else { '
  'return nil }',
  '                    let object: NSManagedObject\n'
  '                    do { object = try context.existingObject(with: objectID) }\n'
  '                    catch {\n'
  '                        guard let contentDiagnostics else { throw error }\n'
  '                        contentDiagnostics.f_1000d468c().f_1000d4df0("Failed to load item '
  'content: \\(error.localizedDescription)")\n'
  '                        return nil\n'
  '                    }\n'
  '                    guard object.entity.name == "Item" else {\n'
  '                        contentDiagnostics?.f_1000d468c().f_1000d4df0("Failed to load item for '
  'content indexing: object not found")\n'
  '                        return nil\n'
  '                    }\n'
  '                    guard !object.isDeleted,\n'
  '                          let data = object.value(forKey: "data") as? NSManagedObject else { '
  'return nil }'],
 ['replica/Sources/PastoCore/ClipboardSearchRecord.swift',
  '    func content() -> String? {\n        read { object, items in',
  '    func content() -> String? {\n'
  '        read(contentDiagnostics: contentDiagnostics) { object, items in']]

def pre_content_load_diagnostic(source):
    from empty_data_diagnostic_scope_contract import pre_empty_data_diagnostic
    source=pre_empty_data_diagnostic(source)
    for _,old,new in reversed(CHANGES):
        if new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    return source
