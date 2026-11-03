"""Reverse only reviewed160 save-failure diagnostics/rollback for historical snapshots."""
CHANGES = [['replica/Sources/PastoCore/ClipboardPersistence.swift',
  'final class ClipboardPersistence {',
  'final class ClipboardPersistence {\n'
  '    private static let transactionDiagnostics = OriginalNamedDiagnostic.f_1000d4624(name: "DB")',
  1],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
  '    /// The native transaction propagates callback/save errors without resetting or rolling '
  'back.',
  '    /// Callback errors propagate directly; save errors diagnose and roll back this context.',
  1],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
  '                    try OriginalObjCExceptionBridge.f_1002ff9c8 { try context.save() }\n'
  '                    // Store callers',
  '                    do {\n'
  '                        try OriginalObjCExceptionBridge.f_1002ff9c8 { try context.save() }\n'
  '                    } catch {\n'
  '                        // 0x100302b78: snapshot before validation, then roll back and rethrow '
  'the save error.\n'
  '                        let inserted = context.insertedObjects\n'
  '                        let updated = context.updatedObjects\n'
  '                        let deleted = context.deletedObjects\n'
  '                        Self.transactionDiagnostics.f_1000d468c().f_1000d4e0c(\n'
  '                            "Error saving managed object context (inserted: \\(inserted.count), '
  'updated: \\(updated.count), deleted: \\(deleted.count)): \\(error)")\n'
  '                        for object in inserted {\n'
  '                            do { try object.validateForInsert() }\n'
  '                            catch {\n'
  '                                Self.transactionDiagnostics.f_1000d468c().f_1000d4e0c(\n'
  '                                    "  Invalid inserted: \\(object.entity.name ?? "?") '
  '\\(object.objectID) — \\(error)")\n'
  '                            }\n'
  '                        }\n'
  '                        for object in updated {\n'
  '                            do { try object.validateForUpdate() }\n'
  '                            catch {\n'
  '                                Self.transactionDiagnostics.f_1000d468c().f_1000d4e0c(\n'
  '                                    "  Invalid updated: \\(object.entity.name ?? "?") '
  '\\(object.objectID) — \\(error)")\n'
  '                            }\n'
  '                        }\n'
  '                        context.rollback()\n'
  '                        throw error\n'
  '                    }\n'
  '                    // Store callers',
  1]]

from text_setter_return_scope_contract import pre_text_setter_return

def pre_save_failure_rollback(source):
    source=pre_text_setter_return(source)
    for _,old,new,count in reversed(CHANGES):
        if new in source:
            assert source.count(new)==count
            source=source.replace(new,old)
    return source

def pre_save_failure_rollback_bytes(path):
    data=path.read_bytes()
    return pre_save_failure_rollback(data.decode()).encode()if path.suffix=='.swift'else data
