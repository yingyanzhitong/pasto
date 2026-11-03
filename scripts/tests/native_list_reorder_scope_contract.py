"""Reverse only reviewed167 native all-List reorder and drag-input deltas for historical contracts."""
CHANGES = [['replica/Sources/PastoCore/ClipboardListPersistence.swift',
  'import Foundation\n',
  'import Foundation\nimport SwiftUI\n',
  1],
 ['replica/Sources/PastoCore/ClipboardListPersistence.swift',
  '    static let historyIdentifier = "sharedPasteboardHistory"',
  '    private static let reorderDiagnostics = OriginalNamedDiagnostic.f_1000d4624(name: '
  '"NSManagedObjectContext")\n'
  '    static let historyIdentifier = "sharedPasteboardHistory"',
  1],
 ['replica/Sources/PastoCore/ClipboardListPersistence.swift',
  '    // 368818/363004, local pinboard branch: fetch errors use an empty sequence, then delete '
  'the same List.',
  '    // 368a30: index changes belong to this context; a separate context touches each changed '
  "List's metadata.\n"
  '    func moveList(_ target: NSManagedObject, toOffset offset: Int) -> [PastoListEntity] {\n'
  '        let request = PastoListEntity.listFetchRequest()\n'
  '        request.sortDescriptors = [NSSortDescriptor(key: "metadata.index", ascending: true)]\n'
  '        var ordered: [PastoListEntity] = []\n'
  '        context.performAndWait { ordered = (try? context.fetch(request)) ?? [] }\n'
  '        guard let source = ordered.firstIndex(where: { $0.isEqual(target) }) else { return [] '
  '}\n'
  '        ordered.move(fromOffsets: IndexSet(integer: source), toOffset: offset)\n'
  '        let background = NSManagedObjectContext(concurrencyType: .privateQueueConcurrencyType)\n'
  '        background.persistentStoreCoordinator = context.persistentStoreCoordinator\n'
  '        background.mergePolicy = NSMergeByPropertyStoreTrumpMergePolicy\n'
  '        for (index, object) in ordered.enumerated() {\n'
  '            retainNativeList(object)\n'
  '            let current = ((object.value(forKey: "metadata") as? '
  'NSManagedObject)?.value(forKey: "index") as? NSNumber)?.int64Value ?? 0\n'
  '            if current != Int64(index) {\n'
  '                (object.value(forKey: "metadata") as? NSManagedObject)?.setValue(Int64(index), '
  'forKey: "index")\n'
  '                background.performAndWait {\n'
  '                    let list = background.object(with: object.objectID)\n'
  '                    list.willChangeValue(forKey: "metadata")\n'
  '                    list.didChangeValue(forKey: "metadata")\n'
  '                }\n'
  '            }\n'
  '        }\n'
  '        let observer = NotificationCenter.default.addObserver(forName: '
  '.NSManagedObjectContextDidSave,\n'
  '            object: background, queue: nil) { [weak self] notification in\n'
  '                guard let context = self?.context else { return }\n'
  '                context.performAndWait { [weak self] in\n'
  '                    self?.context.mergeChanges(fromContextDidSave: notification)\n'
  '                }\n'
  '            }\n'
  '        background.performAndWait {\n'
  '            guard background.hasChanges else { return }\n'
  '            do {\n'
  '                try OriginalObjCExceptionBridge.f_1002ff9c8 { try background.save() }\n'
  '            } catch {\n'
  '                background.rollback()\n'
  '                Self.reorderDiagnostics.f_1000d468c().f_1000d4e0c("Error saving managed object '
  'context: \\(error)")\n'
  '            }\n'
  '        }\n'
  '        NotificationCenter.default.removeObserver(observer)\n'
  '        return ordered\n'
  '    }\n'
  '\n'
  '    // 368818/363004, local pinboard branch: fetch errors use an empty sequence, then delete '
  'the same List.',
  1],
 ['replica/Sources/PastoCore/ClipboardStore.swift',
  '    public func reorderPinboards(ids: [UUID]) throws {',
  '    public func moveList(_ target: ClipboardListTarget, toOffset offset: Int) throws {\n'
  '        try mutateInTransaction { state, transaction in\n'
  '            let ordered = transaction.repository.lists.moveList(target.nativeObject, toOffset: '
  'offset)\n'
  '            for object in ordered {\n'
  '                projectNativeList(ClipboardListTarget(object: object), into: &state)\n'
  '            }\n'
  '        }\n'
  '    }\n'
  '\n'
  '    public func reorderPinboards(ids: [UUID]) throws {',
  1],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    func movePinboard(id: UUID, before target: UUID) {',
  "    // 097828 converts the final destination index to SwiftUI's pre-removal offset.\n"
  '    func moveList(identifier: String, to target: ClipboardListTarget) -> Bool {\n'
  '        guard let source = store.tabListTarget(identifier: identifier), let snapshot = '
  'tabListSnapshot,\n'
  '              let sourceIndex = snapshot.index(of: source), let destinationIndex = '
  'snapshot.index(of: target) else { return false }\n'
  '        let offset = sourceIndex < destinationIndex ? destinationIndex + 1 : destinationIndex\n'
  '        try? store.moveList(source, toOffset: offset)\n'
  '        return true\n'
  '    }\n'
  '\n'
  '    func movePinboard(id: UUID, before target: UUID) {',
  1],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  '            if let board {\n'
  '                tab.dragString = "paste-pinboard:" + board.id.uuidString\n'
  '                tab.onDropString = { value in\n'
  '                    guard value.hasPrefix("paste-pinboard:"), let id = UUID(uuidString: '
  'String(value.dropFirst(15))) else { return false }\n'
  '                    state.movePinboard(id: id, before: board.id)\n'
  '                    return true\n'
  '                }\n'
  '            }',
  '            tab.dragString = "paste-pinboard:" + target.identifier\n'
  '            tab.onDropString = { value in\n'
  '                guard value.hasPrefix("paste-pinboard:") else { return false }\n'
  '                return state.moveList(identifier: String(value.dropFirst(15)), to: target)\n'
  '            }',
  1],
 ['replica/Sources/Pasto/UI/OriginalPinboardTabTitle.swift',
  'value.hasPrefix("paste-pinboard:"), UUID(uuidString: String(value.dropFirst(15))) != nil else { '
  'return nil }',
  'value.hasPrefix("paste-pinboard:") else { return nil }',
  1],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    func movePinboard(id: UUID, before target: UUID) {\n'
  '        guard id != target else { return }\n'
  '        var ids = store.pinboards.sorted { $0.sortOrder < $1.sortOrder }.map(\\.id)\n'
  '        guard ids.contains(id), ids.contains(target) else { return }\n'
  '        ids.removeAll { $0 == id }\n'
  '        ids.insert(id, at: ids.firstIndex(of: target)!)\n'
  '        perform { try store.reorderPinboards(ids: ids) }\n'
  '    }\n'
  '}\n'
  '\n'
  '@MainActor\n'
  'final class ReplicaPanel:',
  '}\n\n@MainActor\nfinal class ReplicaPanel:',
  1]]

def pre_native_list_reorder(source):
    from native_list_edit_event_scope_contract import pre_native_list_edit_event
    source = pre_native_list_edit_event(source)
    for _,old,new,count in reversed(CHANGES):
        if old == "import Foundation\n" and "final class ClipboardListPersistence" not in source:
            continue
        if old.startswith("    func movePinboard(id:") and "func moveList(identifier: String, to target:" not in source:
            continue
        if new and new in source:
            assert source.count(new)==count
            source=source.replace(new,old)
    return source

def pre_native_list_reorder_bytes(path):
    data=path.read_bytes()
    return pre_native_list_reorder(data.decode()).encode() if path.suffix=='.swift' else data
