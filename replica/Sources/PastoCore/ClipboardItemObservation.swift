import Combine
import CoreData
import Foundation

/// Holds the text preview's entity and observes its owning context, not a store-wide value cache.
@MainActor
public final class ClipboardItemObservation {
    private let context: NSManagedObjectContext
    private let objectID: NSManagedObjectID
    private var object: PastoItemEntity
    private var observation: AnyCancellable?
    public var onChange: ((ClipboardItem) -> Void)?
    public var onTextChange: ((NSAttributedString) -> Void)?

    init(object: PastoItemEntity) {
        guard let context = object.managedObjectContext else {
            preconditionFailure("Item observation requires a managed context")
        }
        self.context = context
        self.object = object
        objectID = object.objectID
        observation = NotificationCenter.default
            .publisher(for: .NSManagedObjectContextObjectsDidChange, object: context)
            .sink { [weak self] notification in
                MainActor.assumeIsolated { self?.consume(notification) }
            }
    }

    public var value: ClipboardItem? {
        guard !object.isDeleted else { return nil }
        return try? ClipboardPersistence.item(object)
    }

    // 3c05d4 reads Item.data directly; unrelated archived value metadata is not a text dependency.
    public var attributedText: NSAttributedString? {
        guard !object.isDeleted else { return nil }
        guard let items = ClipboardItemDataPersistence.readItems(from: object) else { return nil }
        return items.first?.f_10037d33c() ?? NSAttributedString(string: "")
    }

    // 356260 selects the event object by ID; 3c04f0 ignores deleted entities.
    private func consume(_ notification: Notification) {
        for key in [NSInsertedObjectsKey, NSUpdatedObjectsKey, NSDeletedObjectsKey, NSRefreshedObjectsKey] {
            let objects = notification.userInfo?[key] as? Set<NSManagedObject> ?? []
            guard let current = objects.first(where: { $0.objectID == objectID }) else { continue }
            let currentItem = current as! PastoItemEntity
            guard !currentItem.isDeleted else { return }
            object = currentItem
            if let attributedText { onTextChange?(attributedText) }
            // Retain the value adapter only for clients that request it.
            if onChange != nil, let value { onChange?(value) }
            return
        }
    }
}
