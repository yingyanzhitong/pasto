import CoreData
import Foundation

/// Source counterpart of the original synchronous Undo/Redo context-save path.
@MainActor
enum OriginalContextUndo {
    private static let diagnostics = OriginalNamedDiagnostic.f_1000d4624(name: "DB")

    // 0x10035ca9c -> 0x10035f228: keep a successful result when there are no changes.
    @discardableResult
    static func f_10035ca9c(_ context: NSManagedObjectContext,
                           prepareForSave: (() throws -> Void)? = nil) -> Bool {
        var succeeded = true
        context.performAndWait { f_10035e4d8(context, succeeded: &succeeded, prepareForSave: prepareForSave) }
        return succeeded
    }

    // 0x10035e4d8: Ghidra drops this failure branch; ARM restores rollback/false/log.
    static func f_10035e4d8(_ context: NSManagedObjectContext, succeeded: inout Bool,
                           prepareForSave: (() throws -> Void)? = nil) {
        guard context.hasChanges else { return }
        do {
            try OriginalObjCExceptionBridge.f_1002ff9c8 {
                try prepareForSave?()
                try context.save()
            }
        } catch {
            context.rollback()
            succeeded = false
            diagnostics.f_1000d468c().f_1000d4e0c("Error saving managed object context: \(error)")
        }
    }
}
