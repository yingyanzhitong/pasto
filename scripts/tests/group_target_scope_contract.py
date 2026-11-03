"""Exact phase106 captured-target deltas for immutable historical source checks."""
from pathlib import Path
from pinboard_collection_scope_contract import pre_pinboard_collection
CHANGES = [['replica/Sources/PastoCore/ClipboardListPersistence.swift',
  '/// Access on the supplied context queue. Existing Pasto IDs and legacy memberships stay '
  'compatible.',
  '/// A group menu retains its target entity until the captured action is invoked.\n'
  '@MainActor\n'
  'public struct ClipboardPinboardTarget {\n'
  '    public let id: UUID\n'
  '    let nativeObject: NSManagedObject\n'
  '\n'
  '    init(id: UUID, object: NSManagedObject) {\n'
  '        self.id = id\n'
  '        nativeObject = object\n'
  '    }\n'
  '}\n'
  '\n'
  '/// Access on the supplied context queue. Existing Pasto IDs and legacy memberships stay '
  'compatible.'],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
  '    func observeListAttributes(identifier: String) -> ClipboardListAttributesObservation? {',
  '    func pinboardAssignmentTarget(id: UUID) -> ClipboardPinboardTarget? {\n'
  '        context.performAndWait {\n'
  '            guard let list = try? lists.list(identifier: id.uuidString) else { return nil }\n'
  '            return ClipboardPinboardTarget(id: id, object: list)\n'
  '        }\n'
  '    }\n'
  '\n'
  '    func observeListAttributes(identifier: String) -> ClipboardListAttributesObservation? {'],
 ['replica/Sources/PastoCore/ClipboardStore.swift',
  '    public func observeListAttributes(pinboardID: UUID?) -> ClipboardListAttributesObservation? '
  '{',
  '    public func pinboardAssignmentTarget(id: UUID) -> ClipboardPinboardTarget? {\n'
  '        persistence.pinboardAssignmentTarget(id: id)\n'
  '    }\n'
  '    public func observeListAttributes(pinboardID: UUID?) -> ClipboardListAttributesObservation? '
  '{'],
 ['replica/Sources/PastoCore/ClipboardStore.swift',
  '    public func assign(items: [ClipboardRestoreItem], to pinboardID: UUID?) throws {\n'
  '        guard let pinboardID, items.allSatisfy({ $0.nativeObject != nil }) else {',
  '    public func assign(items: [ClipboardRestoreItem], to pinboardID: UUID?) throws {\n'
  '        try assign(items: items, pinboardID: pinboardID, nativePinboard: nil)\n'
  '    }\n'
  '\n'
  '    public func assign(items: [ClipboardRestoreItem], to target: ClipboardPinboardTarget) '
  'throws {\n'
  '        try assign(items: items, pinboardID: target.id, nativePinboard: target.nativeObject)\n'
  '    }\n'
  '\n'
  '    private func assign(items: [ClipboardRestoreItem], pinboardID: UUID?, nativePinboard: '
  'NSManagedObject?) throws {\n'
  '        guard let pinboardID, items.allSatisfy({ $0.nativeObject != nil }) else {'],
 ['replica/Sources/PastoCore/ClipboardStore.swift',
  '        try mutateInTransaction { state, transaction in\n'
  '            guard let pinboard = try transaction.repository.lists.list(identifier: '
  'pinboardID.uuidString) else {\n'
  '                throw ClipboardStoreError.pinboardNotFound\n'
  '            }\n'
  '            let destination = try transaction.repository.assignItems(items.map { '
  '$0.nativeObject! }, to: pinboard)',
  '        try mutateInTransaction { state, transaction in\n'
  '            let pinboard: NSManagedObject\n'
  '            if let nativePinboard {\n'
  '                pinboard = nativePinboard\n'
  '            } else {\n'
  '                guard let current = try transaction.repository.lists.list(identifier: '
  'pinboardID.uuidString) else {\n'
  '                    throw ClipboardStoreError.pinboardNotFound\n'
  '                }\n'
  '                pinboard = current\n'
  '            }\n'
  '            let destination = try transaction.repository.assignItems(items.map { '
  '$0.nativeObject! }, to: pinboard)'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    // 09ee9c forwards the array captured when the group menu was built.',
  '    func assignItems(_ items: [ClipboardRestoreItem], to target: ClipboardPinboardTarget) {\n'
  '        perform { try store.assign(items: items, to: target) }\n'
  '    }\n'
  '\n'
  '    // 09ee9c forwards the array captured when the group menu was built.'],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  '                ForEach(state.store.pinboards) { board in\n'
  '                    Button(board.name) { state.assignItems(groupItems, to: board.id) }\n'
  '                }',
  '                ForEach(state.store.pinboards) { board in\n'
  '                    let target = state.store.pinboardAssignmentTarget(id: board.id)\n'
  '                    Button(board.name) {\n'
  '                        if let target { state.assignItems(groupItems, to: target) }\n'
  '                        else { state.assignItems(groupItems, to: board.id) }\n'
  '                    }\n'
  '                }']]

def pre_group_target(source):
    source = pre_pinboard_collection(source)
    for _,old,new in reversed(CHANGES):
        if old.startswith(new) and old in source: continue
        if new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    return source

def pre_group_target_bytes(path):
    p=Path(path)
    return pre_group_target(p.read_text()).encode() if p.suffix=='.swift' else p.read_bytes()
