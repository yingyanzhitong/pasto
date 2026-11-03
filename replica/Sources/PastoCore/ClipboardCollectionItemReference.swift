import CoreData
import Foundation

/// A published object identity can outlive the source snapshot that supplied it.
public struct ClipboardCollectionItemReference: Equatable {
    private let context: NSManagedObjectContext
    private let objectID: NSManagedObjectID

    init(context: NSManagedObjectContext, objectID: NSManagedObjectID) {
        self.context = context
        self.objectID = objectID
    }

    public static func == (lhs: Self, rhs: Self) -> Bool {
        lhs.context === rhs.context && lhs.objectID == rhs.objectID
    }

    // 3544dc: lookup/class errors are optional; content projection is a later consumer operation.
    @MainActor public func restoreItem(id: UUID) -> ClipboardRestoreItem? {
        guard let object = (try? context.existingObject(with: objectID)) as? PastoItemEntity else { return nil }
        return ClipboardRestoreItem(id: id, object: object)
    }

    @MainActor public func requiredRestoreItem(id: UUID) -> ClipboardRestoreItem {
        // 35440c uses the same optional entity getter, then requires a result.
        guard let input = restoreItem(id: id) else { fatalError("Missing restore item") }
        return input
    }
}
