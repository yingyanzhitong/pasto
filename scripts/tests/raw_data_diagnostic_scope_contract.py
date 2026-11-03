"""Reverse only reviewed127 local diagnostic delta for historical contracts."""
from native_search_content_scope_contract import pre_native_search_content
CHANGES = [['replica/Sources/PastoCore/ClipboardItemDataPersistence.swift',
  'import CoreData\nimport Foundation\n',
  'import CoreData\nimport Foundation\nimport ObjectiveC\n'],
 ['replica/Sources/PastoCore/ClipboardItemDataPersistence.swift',
  '    // 31b218: raw getter exceptions yield no representations; invalid local graphs stay '
  'optional.',
  '    @MainActor private static var diagnosticsKey: UInt8 = 0\n'
  '\n'
  '    // Preserve per-object logger ownership without changing the existing managed entity '
  'class/model.\n'
  '    // The original constructs the named wrapper at entity creation; this adapter defers it to '
  'the error path.\n'
  '    @MainActor private static func diagnostics(for data: NSManagedObject) -> '
  'OriginalNamedDiagnostic {\n'
  '        if let existing = objc_getAssociatedObject(data, &diagnosticsKey) as? '
  'OriginalNamedDiagnostic {\n'
  '            return existing\n'
  '        }\n'
  '        let diagnostics = OriginalNamedDiagnostic.f_1000d4624(name: "ItemDataEntity")\n'
  '        objc_setAssociatedObject(data, &diagnosticsKey, diagnostics, '
  '.OBJC_ASSOCIATION_RETAIN_NONATOMIC)\n'
  '        return diagnostics\n'
  '    }\n'
  '\n'
  '    // 31b218: raw getter exceptions log locally and yield no representations; invalid local '
  'graphs stay optional.'],
 ['replica/Sources/PastoCore/ClipboardItemDataPersistence.swift',
  '        } catch is OriginalObjCExceptionError {\n            return []\n',
  '        } catch let error as OriginalObjCExceptionError {\n'
  '            diagnostics(for: data).f_1000d468c().f_1000d4e0c("Unreadable pasteboard items blob: '
  '\\(error)")\n'
  '            return []\n']]

def pre_raw_data_diagnostic(source):
    source=pre_native_search_content(source)
    for _,old,new in reversed(CHANGES):
        if new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    return source
