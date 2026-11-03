import Combine
import CoreData
import Foundation

/// The selected managed list's post-change attributes, independent of store-wide UI invalidation.
@MainActor
public final class ClipboardListAttributesObservation {
    public let identifier: String
    private let context: NSManagedObjectContext
    private let objectID: NSManagedObjectID
    private let subject: CurrentValueSubject<OriginalPinboardAttributes.Value?, Never>
    private var observation: AnyCancellable?

    init(list: NSManagedObject) {
        guard let context = list.managedObjectContext else {
            preconditionFailure("List observation requires a managed context")
        }
        self.context = context
        identifier = list.value(forKey: "identifier") as! String
        subject = CurrentValueSubject(OriginalPinboardAttributes.decoded(from: list.value(forKey: "rawAttributes") as? Data))
        let objectID = list.objectID
        self.objectID = objectID
        observation = NotificationCenter.default
            .publisher(for: .NSManagedObjectContextObjectsDidChange, object: context)
            .sink { [weak self] notification in
                MainActor.assumeIsolated {
                    let subject = self?.subject
                    Self.consume(notification, objectID: objectID, subject: subject)
                }
            }
    }

    // Pasto's snapshot reads can reset the view context. Resolve the current object
    // for rendering instead of retaining a detached list or a stale decoded value.
    public var value: OriginalPinboardAttributes.Value? {
        context.performAndWait {
            guard let list = try? context.existingObject(with: objectID), !list.isDeleted else { return nil }
            return OriginalPinboardAttributes.decoded(from: list.value(forKey: "rawAttributes") as? Data)
        }
    }

    public var publisher: AnyPublisher<OriginalPinboardAttributes.Value?, Never> {
        subject.removeDuplicates().eraseToAnyPublisher()
    }

    // 356260 dispatches insert(0), update(2), delete(1), refresh(3) in this order.
    // 3bb73c ignores delete; the object in the notification supplies the current value.
    private static func consume(_ notification: Notification, objectID: NSManagedObjectID,
                                subject: CurrentValueSubject<OriginalPinboardAttributes.Value?, Never>?) {
        guard let subject else { return }
        for key in [NSInsertedObjectsKey, NSUpdatedObjectsKey, NSDeletedObjectsKey, NSRefreshedObjectsKey] {
            let objects = notification.userInfo?[key] as? Set<NSManagedObject> ?? []
            guard let list = objects.first(where: { $0.objectID == objectID }) else { continue }
            if key != NSDeletedObjectsKey {
                subject.send(OriginalPinboardAttributes.decoded(from: list.value(forKey: "rawAttributes") as? Data))
            }
            return
        }
    }
}
