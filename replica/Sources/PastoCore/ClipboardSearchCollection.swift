import Combine
import CoreData
import Foundation
import os

/// Each search or ordinary list owns a live FRC on the stable view context. IDs are adapted to Pasto's local keys.
@MainActor
public final class ClipboardSearchCollection {
    public struct Snapshot: Equatable {
        public let identifiers: [UUID]
        public let updatedIdentifiers: Set<UUID>
        public let itemReferences: [UUID: ClipboardCollectionItemReference]

        init(identifiers: [UUID], updatedIdentifiers: Set<UUID>,
             itemReferences: [UUID: ClipboardCollectionItemReference] = [:]) {
            self.identifiers = identifiers
            self.updatedIdentifiers = updatedIdentifiers
            self.itemReferences = itemReferences
        }

        @MainActor public func item(at index: Int) -> ClipboardItem {
            let identifier = identifiers[index]
            guard let reference = itemReferences[identifier] else { fatalError("Missing collection item reference") }
            return reference.requiredRestoreItem(id: identifier).resolvedItem()
        }
    }

    private let context: NSManagedObjectContext
    private let controller: NSFetchedResultsController<PastoItemEntity>
    private let subject = CurrentValueSubject<Snapshot, Never>(Snapshot(identifiers: [], updatedIdentifiers: []))
    private var differenceDelegate: ClipboardSearchDifferenceDelegate?
    private var objectsObservation: AnyCancellable?
    private var objectIDs: [NSManagedObjectID] = []
    private var objectIDMembership: Set<NSManagedObjectID> = []
    private var pending: (ids: [NSManagedObjectID], updated: Set<NSManagedObjectID>)?
    private let logger = Logger(subsystem: "com.yingyanzhitong.paste-replica", category: "search-collection")

    convenience init(context: NSManagedObjectContext, identifiers: [String]) {
        let request = PastoItemEntity.defaultFetchRequest()
        // The second clause preserves existing local records without a native identifier.
        request.predicate = NSPredicate(
            format: "nativeIdentifier IN %@ OR (nativeIdentifier == nil AND key IN %@)", identifiers, identifiers)
        self.init(context: context, request: request)
        if objectIDs.count != identifiers.count {
            logger.error("Search found \(identifiers.count) identifiers but fetched \(self.objectIDs.count) objects")
        }
    }

    init(context: NSManagedObjectContext, request: NSFetchRequest<PastoItemEntity>) {
        self.context = context
        controller = NSFetchedResultsController(fetchRequest: request, managedObjectContext: context,
                                                sectionNameKeyPath: nil, cacheName: nil)
        // 365e18: initial fetch failure is fatal; index-record fetch36dc00 has a different error contract.
        do { try controller.performFetch() }
        catch { fatalError("Fetched results fetch failed: \(error)") }
        let initial = initialObjectIDs()
        let delegate = ClipboardSearchDifferenceDelegate(ids: initial) { [weak self] ids in
            self?.receive(ids: ids, updated: [])
        }
        differenceDelegate = delegate
        controller.delegate = delegate
        pending = (initial, [])
        flushPending()
        // 365e18 installs same-context object observation only after publishing the initial IDs.
        objectsObservation = NotificationCenter.default
            .publisher(for: .NSManagedObjectContextObjectsDidChange, object: context)
            .sink { [weak self] notification in
                MainActor.assumeIsolated { self?.objectsDidChange(notification) }
            }
    }

    public var value: Snapshot { subject.value }
    public var publisher: AnyPublisher<Snapshot, Never> { subject.eraseToAnyPublisher() }

    // 366344: a clean context can use an ID-only fetch after checking FRC count and endpoints.
    private func initialObjectIDs() -> [NSManagedObjectID] {
        guard !context.hasChanges else { return (controller.fetchedObjects ?? []).map(\.objectID) }
        let ids = fetchInitialObjectIDs()
        guard let count = controller.sections?.first?.numberOfObjects, ids.count == count,
              ids.first == fetchedObjectID(at: 0), ids.last == fetchedObjectID(at: ids.count - 1) else {
            return (controller.fetchedObjects ?? []).map(\.objectID)
        }
        return ids
    }

    // 367014: copy only entity/predicate/sort; an ID-query error yields an empty candidate array.
    private func fetchInitialObjectIDs() -> [NSManagedObjectID] {
        guard let entityName = controller.fetchRequest.entityName else { fatalError("Missing fetch entity name") }
        let request = NSFetchRequest<NSManagedObjectID>(entityName: entityName)
        request.predicate = controller.fetchRequest.predicate
        request.sortDescriptors = controller.fetchRequest.sortDescriptors
        request.resultType = .managedObjectIDResultType
        return (try? context.fetch(request)) ?? []
    }

    // 367184: negative/out-of-section positions have no object ID.
    private func fetchedObjectID(at index: Int) -> NSManagedObjectID? {
        guard index >= 0, let count = controller.sections?.first?.numberOfObjects, index < count else { return nil }
        return controller.object(at: IndexPath(indexes: [0, index])).objectID
    }

    // 3669fc: replace pending order, union changed IDs and schedule only the first pending delivery.
    private func receive(ids: [NSManagedObjectID], updated: Set<NSManagedObjectID>) {
        let schedulesDelivery = pending == nil
        pending = (ids, (pending?.updated ?? []).union(updated))
        if schedulesDelivery {
            // 3669fc's default ImmediateSnapshotScheduler executes its work inline.
            flushPending()
        }
    }

    // 366b38: clear before sending so subscriber reentry starts a new pending batch.
    private func flushPending() {
        guard let value = pending else { return }
        pending = nil
        if objectIDs != value.ids {
            objectIDs = value.ids
            objectIDMembership = Set(value.ids)
        }
        let keys = Dictionary(uniqueKeysWithValues: value.ids.compactMap { objectID -> (NSManagedObjectID, UUID)? in
            guard let object = try? context.existingObject(with: objectID),
                  let key = object.value(forKey: "key") as? String,
                  let identifier = UUID(uuidString: key) else { return nil }
            return (objectID, identifier)
        })
        var references: [UUID: ClipboardCollectionItemReference] = [:]
        for objectID in value.ids {
            guard let identifier = keys[objectID] else { continue }
            references[identifier] = ClipboardCollectionItemReference(context: context, objectID: objectID)
        }
        subject.send(Snapshot(identifiers: value.ids.compactMap { keys[$0] },
                              updatedIdentifiers: Set(value.updated.compactMap { keys[$0] }),
                              itemReferences: references))
    }

    private func objectsDidChange(_ notification: Notification) {
        let ids = pending?.ids ?? objectIDs
        let membership = pending.map { Set($0.ids) } ?? objectIDMembership
        let updated = notification.userInfo?[NSUpdatedObjectsKey] as? Set<NSManagedObject> ?? []
        let refreshed = notification.userInfo?[NSRefreshedObjectsKey] as? Set<NSManagedObject> ?? []
        let changed = Set(updated.union(refreshed).map(\.objectID)).intersection(membership)
        if !changed.isEmpty { receive(ids: ids, updated: changed) }
    }
}

/// Live ListEntity collection: tabs use class defaults (367f78), the menu narrows to type2 (36c094).
@MainActor
public final class ClipboardPinboardCollection {
    private struct Snapshot {
        let identifiers: [NSManagedObjectID]
        let updatedIdentifiers: Set<NSManagedObjectID>
    }

    private let context: NSManagedObjectContext
    private let controller: NSFetchedResultsController<PastoListEntity>
    private let subject = CurrentValueSubject<Snapshot, Never>(Snapshot(identifiers: [], updatedIdentifiers: []))
    private var differenceDelegate: ClipboardSearchDifferenceDelegate?
    private var objectsObservation: AnyCancellable?
    private var objectIDs: [NSManagedObjectID] = []
    private var objectIDMembership: Set<NSManagedObjectID> = []
    private var pending: (ids: [NSManagedObjectID], updated: Set<NSManagedObjectID>)?

    init(context: NSManagedObjectContext, request: NSFetchRequest<PastoListEntity>) {
        self.context = context
        controller = NSFetchedResultsController(fetchRequest: request, managedObjectContext: context,
                                                sectionNameKeyPath: nil, cacheName: nil)
        // 365e18: initial fetch failure is fatal; index-record fetch36dc00 has a different error contract.
        do { try controller.performFetch() }
        catch { fatalError("Fetched results fetch failed: \(error)") }
        let initial = initialObjectIDs()
        let delegate = ClipboardSearchDifferenceDelegate(ids: initial) { [weak self] ids in
            self?.receive(ids: ids, updated: [])
        }
        differenceDelegate = delegate
        controller.delegate = delegate
        pending = (initial, [])
        flushPending()
        // 365e18 installs same-context object observation only after publishing the initial IDs.
        objectsObservation = NotificationCenter.default
            .publisher(for: .NSManagedObjectContextObjectsDidChange, object: context)
            .sink { [weak self] notification in
                MainActor.assumeIsolated { self?.objectsDidChange(notification) }
            }
    }

    @MainActor public struct ListSnapshot {
        public let identifiers: [NSManagedObjectID]
        public let updatedIdentifiers: Set<NSManagedObjectID>
        private let context: NSManagedObjectContext
        fileprivate init(identifiers: [NSManagedObjectID], updatedIdentifiers: Set<NSManagedObjectID>,
                         context: NSManagedObjectContext) {
            self.identifiers = identifiers
            self.updatedIdentifiers = updatedIdentifiers
            self.context = context
        }
        public var count: Int { identifiers.count }
        public var targets: [ClipboardListTarget] { identifiers.indices.compactMap { target(at: $0) } }
        public func index(of target: ClipboardListTarget) -> Int? {
            identifiers.firstIndex { $0.isEqual(target.nativeObject.objectID) }
        }
        public func target(at index: Int) -> ClipboardListTarget? {
            guard identifiers.indices.contains(index) else { return nil }
            return target(for: identifiers[index])
        }
        public func target(for objectID: NSManagedObjectID) -> ClipboardListTarget? {
            guard let object = (try? context.existingObject(with: objectID)) as? PastoListEntity else { return nil }
            return ClipboardListTarget(object: object)
        }
    }

    public var listSnapshot: ListSnapshot { ListSnapshot(identifiers: subject.value.identifiers, updatedIdentifiers: subject.value.updatedIdentifiers, context: context) }
    public var listPublisher: AnyPublisher<ListSnapshot, Never> {
        subject.map { [self] snapshot in ListSnapshot(identifiers: snapshot.identifiers, updatedIdentifiers: snapshot.updatedIdentifiers, context: context) }
            .eraseToAnyPublisher()
    }

    // 1b85f0 maps the current ordered IDs using the collection's optional native lookup.
    public var value: [ClipboardPinboardTarget] {
        subject.value.identifiers.compactMap { objectID in
            guard let object = (try? context.existingObject(with: objectID)) as? PastoListEntity,
                  let identifier = object.value(forKey: "identifier") as? String,
                  let id = UUID(uuidString: identifier) else { return nil }
            return ClipboardPinboardTarget(id: id, object: object)
        }
    }

    // 366344: a clean context can use an ID-only fetch after checking FRC count and endpoints.
    private func initialObjectIDs() -> [NSManagedObjectID] {
        guard !context.hasChanges else { return (controller.fetchedObjects ?? []).map(\.objectID) }
        let ids = fetchInitialObjectIDs()
        guard let count = controller.sections?.first?.numberOfObjects, ids.count == count,
              ids.first == fetchedObjectID(at: 0), ids.last == fetchedObjectID(at: ids.count - 1) else {
            return (controller.fetchedObjects ?? []).map(\.objectID)
        }
        return ids
    }

    // 367014: copy only entity/predicate/sort; an ID-query error yields an empty candidate array.
    private func fetchInitialObjectIDs() -> [NSManagedObjectID] {
        guard let entityName = controller.fetchRequest.entityName else { fatalError("Missing fetch entity name") }
        let request = NSFetchRequest<NSManagedObjectID>(entityName: entityName)
        request.predicate = controller.fetchRequest.predicate
        request.sortDescriptors = controller.fetchRequest.sortDescriptors
        request.resultType = .managedObjectIDResultType
        return (try? context.fetch(request)) ?? []
    }

    // 367184: negative/out-of-section positions have no object ID.
    private func fetchedObjectID(at index: Int) -> NSManagedObjectID? {
        guard index >= 0, let count = controller.sections?.first?.numberOfObjects, index < count else { return nil }
        return controller.object(at: IndexPath(indexes: [0, index])).objectID
    }

    // 3669fc: replace pending order, union changed IDs and schedule only the first pending delivery.
    private func receive(ids: [NSManagedObjectID], updated: Set<NSManagedObjectID>) {
        let schedulesDelivery = pending == nil
        pending = (ids, (pending?.updated ?? []).union(updated))
        if schedulesDelivery {
            // 3669fc's default ImmediateSnapshotScheduler executes its work inline.
            flushPending()
        }
    }

    // 366b38: update the ID snapshot before publishing, allowing subscriber reentry.
    private func flushPending() {
        guard let value = pending else { return }
        pending = nil
        if objectIDs != value.ids {
            objectIDs = value.ids
            objectIDMembership = Set(value.ids)
        }
        subject.send(Snapshot(identifiers: value.ids, updatedIdentifiers: value.updated))
    }

    private func objectsDidChange(_ notification: Notification) {
        let ids = pending?.ids ?? objectIDs
        let membership = pending.map { Set($0.ids) } ?? objectIDMembership
        let updated = notification.userInfo?[NSUpdatedObjectsKey] as? Set<NSManagedObject> ?? []
        let refreshed = notification.userInfo?[NSRefreshedObjectsKey] as? Set<NSManagedObject> ?? []
        let changed = Set(updated.union(refreshed).map(\.objectID)).intersection(membership)
        if !changed.isEmpty { receive(ids: ids, updated: changed) }
    }
}

/// 354800/354f90: use the difference selector, not the diffable-snapshot or legacy per-object selectors.
@MainActor
private final class ClipboardSearchDifferenceDelegate: NSObject, NSFetchedResultsControllerDelegate {
    private var ids: [NSManagedObjectID]
    private let handler: ([NSManagedObjectID]) -> Void

    init(ids: [NSManagedObjectID], handler: @escaping ([NSManagedObjectID]) -> Void) {
        self.ids = ids
        self.handler = handler
        super.init()
    }

    nonisolated func controller(_ controller: NSFetchedResultsController<NSFetchRequestResult>,
                                didChangeContentWith diff: CollectionDifference<NSManagedObjectID>) {
        MainActor.assumeIsolated {
            guard !diff.isEmpty else { return }
            let expectedCount = controller.sections?.first?.numberOfObjects
            if let next = ids.applying(diff), expectedCount == nil || next.count == expectedCount {
                ids = next
            } else {
                ids = (controller.fetchedObjects as? [NSManagedObject] ?? []).map(\.objectID)
            }
            handler(ids)
        }
    }
}
