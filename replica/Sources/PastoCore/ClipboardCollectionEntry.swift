import Foundation

/// Collection membership is an identity/reference snapshot; payload is read only by a consumer.
public struct ClipboardCollectionEntry: Identifiable, Equatable {
    public let id: UUID
    private let reference: ClipboardCollectionItemReference?
    private let legacyItem: ClipboardItem?

    public init(id: UUID, reference: ClipboardCollectionItemReference) {
        self.id = id
        self.reference = reference
        legacyItem = nil
    }

    public init(item: ClipboardItem) {
        id = item.id
        reference = nil
        legacyItem = item
    }

    @MainActor public func item() -> ClipboardItem? {
        if let reference { return reference.restoreItem(id: id)?.resolvedItem() }
        return legacyItem
    }

    @MainActor public func restoreItem() -> ClipboardRestoreItem? {
        if let reference { return reference.restoreItem(id: id) }
        guard let legacyItem else { return nil }
        return ClipboardRestoreItem(item: legacyItem)
    }

    @MainActor public func requiredItem() -> ClipboardItem {
        if let reference { return reference.requiredRestoreItem(id: id).resolvedItem() }
        guard let legacyItem else { fatalError("Missing collection entry") }
        return legacyItem
    }

    @MainActor public func requiredRestoreItem() -> ClipboardRestoreItem {
        if let reference { return reference.requiredRestoreItem(id: id) }
        guard let legacyItem else { fatalError("Missing collection entry") }
        return ClipboardRestoreItem(item: legacyItem)
    }
}
