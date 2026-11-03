"""Exact phase107 native group collection deltas, for historical source proofs only."""
from pathlib import Path
from preview_group_menu_scope_contract import pre_preview_group_menu
CHANGES = [['replica/Sources/PastoCore/ClipboardListPersistence.swift',
  '    public let id: UUID\n    let nativeObject: NSManagedObject',
  '    public let id: UUID\n'
  '    public var name: String { nativeObject.value(forKey: "name") as? String ?? "" }\n'
  '    let nativeObject: NSManagedObject'],
 ['replica/Sources/PastoCore/ClipboardListPersistence.swift',
  '    // 0x100328bb4 → 0x100328bc8, specialized to the actual local ListEntity consumers.',
  "    // 36c094/329764: the menu's live group collection uses the List class defaults.\n"
  '    func pinboardRequest() -> NSFetchRequest<NSManagedObject> {\n'
  '        let request = NSFetchRequest<NSManagedObject>(entityName: "ListEntity")\n'
  '        request.sortDescriptors = [NSSortDescriptor(key: "metadata.index", ascending: true)]\n'
  '        request.predicate = NSPredicate(format: "rawType == %d", 2)\n'
  '        request.fetchBatchSize = 20\n'
  '        return request\n'
  '    }\n'
  '\n'
  '    // 0x100328bb4 → 0x100328bc8, specialized to the actual local ListEntity consumers.'],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
  '    func pinboardAssignmentTarget(id: UUID) -> ClipboardPinboardTarget? {\n'
  '        context.performAndWait {\n'
  '            guard let list = try? lists.list(identifier: id.uuidString) else { return nil }\n'
  '            return ClipboardPinboardTarget(id: id, object: list)\n'
  '        }\n'
  '    }',
  '    func makePinboardCollection() -> ClipboardPinboardCollection {\n'
  '        context.performAndWait {\n'
  '            ClipboardPinboardCollection(context: context, request: lists.pinboardRequest())\n'
  '        }\n'
  '    }'],
 ['replica/Sources/PastoCore/ClipboardStore.swift',
  '    public func pinboardAssignmentTarget(id: UUID) -> ClipboardPinboardTarget? {\n'
  '        persistence.pinboardAssignmentTarget(id: id)\n'
  '    }',
  '    public func makePinboardCollection() -> ClipboardPinboardCollection {\n'
  '        persistence.makePinboardCollection()\n'
  '    }'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    private var listCollection: ClipboardSearchCollection?',
  '    private var listCollection: ClipboardSearchCollection?\n'
  '    private lazy var pinboardMenuCollection = store.makePinboardCollection()'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    func assignItems(_ items: [ClipboardRestoreItem], to target: ClipboardPinboardTarget) {',
  '    // 076318/09e510: read the cached native list collection when the menu is constructed.\n'
  '    func pinboardMenuTargets() -> [ClipboardPinboardTarget] {\n'
  '        pinboardMenuCollection.value\n'
  '    }\n'
  '\n'
  '    func assignItems(_ items: [ClipboardRestoreItem], to target: ClipboardPinboardTarget) {'],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  '                ForEach(state.store.pinboards) { board in\n'
  '                    let target = state.store.pinboardAssignmentTarget(id: board.id)\n'
  '                    Button(board.name) {\n'
  '                        if let target { state.assignItems(groupItems, to: target) }\n'
  '                        else { state.assignItems(groupItems, to: board.id) }\n'
  '                    }\n'
  '                }',
  '                ForEach(state.pinboardMenuTargets(), id: \\.id) { target in\n'
  '                    Button(target.name) { state.assignItems(groupItems, to: target) }\n'
  '                }'],
 ['replica/Sources/PastoCore/ClipboardSearchCollection.swift',
  '/// 354800/354f90: use the difference selector, not the diffable-snapshot or legacy per-object '
  'selectors.',
  "/// The group menu's lazily owned live ListEntity collection (3b8c94/36c094).\n"
  '@MainActor\n'
  'public final class ClipboardPinboardCollection {\n'
  '    private struct Snapshot {\n'
  '        let identifiers: [NSManagedObjectID]\n'
  '        let updatedIdentifiers: Set<NSManagedObjectID>\n'
  '    }\n'
  '\n'
  '    private let context: NSManagedObjectContext\n'
  '    private let controller: NSFetchedResultsController<NSManagedObject>\n'
  '    private let subject = CurrentValueSubject<Snapshot, Never>(Snapshot(identifiers: [], '
  'updatedIdentifiers: []))\n'
  '    private var differenceDelegate: ClipboardSearchDifferenceDelegate?\n'
  '    private var objectsObservation: AnyCancellable?\n'
  '    private var objectIDs: [NSManagedObjectID] = []\n'
  '    private var pending: (ids: [NSManagedObjectID], updated: Set<NSManagedObjectID>)?\n'
  '\n'
  '    init(context: NSManagedObjectContext, request: NSFetchRequest<NSManagedObject>) {\n'
  '        self.context = context\n'
  '        controller = NSFetchedResultsController(fetchRequest: request, managedObjectContext: '
  'context,\n'
  '                                                sectionNameKeyPath: nil, cacheName: nil)\n'
  '        // 365e18: initial fetch failure is fatal; index-record fetch36dc00 has a different '
  'error contract.\n'
  '        do { try controller.performFetch() }\n'
  '        catch { fatalError("Fetched results fetch failed: \\(error)") }\n'
  '        let initial = initialObjectIDs()\n'
  '        let delegate = ClipboardSearchDifferenceDelegate(ids: initial) { [weak self] ids in\n'
  '            self?.receive(ids: ids, updated: [])\n'
  '        }\n'
  '        differenceDelegate = delegate\n'
  '        controller.delegate = delegate\n'
  '        pending = (initial, [])\n'
  '        flushPending()\n'
  '        // 365e18 installs same-context object observation only after publishing the initial '
  'IDs.\n'
  '        objectsObservation = NotificationCenter.default\n'
  '            .publisher(for: .NSManagedObjectContextObjectsDidChange, object: context)\n'
  '            .sink { [weak self] notification in\n'
  '                MainActor.assumeIsolated { self?.objectsDidChange(notification) }\n'
  '            }\n'
  '    }\n'
  '\n'
  "    // 1b85f0 maps the current ordered IDs using the collection's optional native lookup.\n"
  '    public var value: [ClipboardPinboardTarget] {\n'
  '        subject.value.identifiers.compactMap { objectID in\n'
  '            guard let object = try? context.existingObject(with: objectID),\n'
  '                  object.entity.name == "ListEntity",\n'
  '                  let identifier = object.value(forKey: "identifier") as? String,\n'
  '                  let id = UUID(uuidString: identifier) else { return nil }\n'
  '            return ClipboardPinboardTarget(id: id, object: object)\n'
  '        }\n'
  '    }\n'
  '\n'
  '    // 366344: a clean context can use an ID-only fetch after checking FRC count and '
  'endpoints.\n'
  '    private func initialObjectIDs() -> [NSManagedObjectID] {\n'
  '        guard !context.hasChanges else { return (controller.fetchedObjects ?? '
  '[]).map(\\.objectID) }\n'
  '        let ids = fetchInitialObjectIDs()\n'
  '        guard let count = controller.sections?.first?.numberOfObjects, ids.count == count,\n'
  '              ids.first == fetchedObjectID(at: 0), ids.last == fetchedObjectID(at: ids.count - '
  '1) else {\n'
  '            return (controller.fetchedObjects ?? []).map(\\.objectID)\n'
  '        }\n'
  '        return ids\n'
  '    }\n'
  '\n'
  '    // 367014: copy only entity/predicate/sort; an ID-query error yields an empty candidate '
  'array.\n'
  '    private func fetchInitialObjectIDs() -> [NSManagedObjectID] {\n'
  '        guard let entityName = controller.fetchRequest.entityName else { fatalError("Missing '
  'fetch entity name") }\n'
  '        let request = NSFetchRequest<NSManagedObjectID>(entityName: entityName)\n'
  '        request.predicate = controller.fetchRequest.predicate\n'
  '        request.sortDescriptors = controller.fetchRequest.sortDescriptors\n'
  '        request.resultType = .managedObjectIDResultType\n'
  '        return (try? context.fetch(request)) ?? []\n'
  '    }\n'
  '\n'
  '    // 367184: negative/out-of-section positions have no object ID.\n'
  '    private func fetchedObjectID(at index: Int) -> NSManagedObjectID? {\n'
  '        guard index >= 0, let count = controller.sections?.first?.numberOfObjects, index < '
  'count else { return nil }\n'
  '        return controller.object(at: IndexPath(indexes: [0, index])).objectID\n'
  '    }\n'
  '\n'
  '    // 3669fc: replace pending order, union changed IDs and schedule only the first pending '
  'delivery.\n'
  '    private func receive(ids: [NSManagedObjectID], updated: Set<NSManagedObjectID>) {\n'
  '        let schedulesDelivery = pending == nil\n'
  '        pending = (ids, (pending?.updated ?? []).union(updated))\n'
  '        if schedulesDelivery {\n'
  '            context.perform { [weak self] in\n'
  '                MainActor.assumeIsolated { self?.flushPending() }\n'
  '            }\n'
  '        }\n'
  '    }\n'
  '\n'
  '    // 366b38: update the ID snapshot before publishing, allowing subscriber reentry.\n'
  '    private func flushPending() {\n'
  '        guard let value = pending else { return }\n'
  '        pending = nil\n'
  '        objectIDs = value.ids\n'
  '        subject.send(Snapshot(identifiers: value.ids, updatedIdentifiers: value.updated))\n'
  '    }\n'
  '\n'
  '    private func objectsDidChange(_ notification: Notification) {\n'
  '        let ids = pending?.ids ?? objectIDs\n'
  '        let membership = Set(ids)\n'
  '        let updated = notification.userInfo?[NSUpdatedObjectsKey] as? Set<NSManagedObject> ?? '
  '[]\n'
  '        let refreshed = notification.userInfo?[NSRefreshedObjectsKey] as? Set<NSManagedObject> '
  '?? []\n'
  '        let changed = Set(updated.union(refreshed).map(\\.objectID)).intersection(membership)\n'
  '        if !changed.isEmpty { receive(ids: ids, updated: changed) }\n'
  '    }\n'
  '}\n'
  '\n'
  '/// 354800/354f90: use the difference selector, not the diffable-snapshot or legacy per-object '
  'selectors.']]

def pre_pinboard_collection(source):
    source = pre_preview_group_menu(source)
    for _,old,new in reversed(CHANGES):
        if old.startswith(new) and old in source: continue
        if new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    return source

def pre_pinboard_collection_bytes(path):
    p=Path(path)
    return pre_pinboard_collection(p.read_text()).encode() if p.suffix=='.swift' else p.read_bytes()
