"""Reverse only phase112 native group creation-result deltas for historical checks."""
from pathlib import Path
from native_owner_type_scope_contract import pre_native_owner_type
CHANGES = [['replica/Sources/PastoCore/ClipboardStore.swift',
  '        return try insertPinboard(name: name, colorHex: colorHex)',
  '        return try insertPinboard(name: name, colorHex: colorHex).board'],
 ['replica/Sources/PastoCore/ClipboardStore.swift',
  '        return try insertPinboard(name: name, colorHex: nil)',
  '        return try insertPinboard(name: name, colorHex: nil).board'],
 ['replica/Sources/PastoCore/ClipboardStore.swift',
  '    private func insertPinboard(name: String, colorHex: String?) throws -> Pinboard {',
  '    // 367c5c/368560: preserve the created List entity for subsequent group assignment.\n'
  '    public func createPinboardTarget(name: String) throws -> ClipboardPinboardTarget {\n'
  '        guard !name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { throw '
  'ClipboardStoreError.invalidPinboardName }\n'
  '        return try insertPinboard(name: name, colorHex: nil).target\n'
  '    }\n'
  '\n'
  '    private func insertPinboard(name: String, colorHex: String?) throws -> (board: Pinboard, '
  'target: ClipboardPinboardTarget) {'],
 ['replica/Sources/PastoCore/ClipboardStore.swift',
  '            let attributes = try transaction.repository.lists.insertPinboard(identifier: '
  'id.uuidString,',
  '            let created = try transaction.repository.lists.insertPinboard(identifier: '
  'id.uuidString,'],
 ['replica/Sources/PastoCore/ClipboardStore.swift',
  '            let board = Pinboard(id: id, name: name, colorHex: value, sortOrder: sortOrder,\n'
  '                                 rawType: 2, rawAttributes: attributes)\n'
  '            state.pinboards.append(board)\n'
  '            return board',
  '            let board = Pinboard(id: id, name: name, colorHex: value, sortOrder: sortOrder,\n'
  '                                 rawType: 2, rawAttributes: created.attributes)\n'
  '            state.pinboards.append(board)\n'
  '            return (board, ClipboardPinboardTarget(id: id, object: created.object))'],
 ['replica/Sources/PastoCore/ClipboardListPersistence.swift',
  '                        encodeAttributes: () throws -> Data?) throws -> Data? {',
  '                        encodeAttributes: () throws -> Data?) throws -> (object: '
  'NSManagedObject, attributes: Data?) {'],
 ['replica/Sources/PastoCore/ClipboardListPersistence.swift',
  '        list.setValue(Int64(2), forKey: "rawType")\n        return attributes\n    }',
  '        list.setValue(Int64(2), forKey: "rawType")\n        return (list, attributes)\n    }'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '            let board = try store.createPinboard(name: name)\n'
  '            if assignSelection {\n'
  '                if let selectionItems {\n'
  '                    try store.assign(items: selectionItems, to: board.id)',
  '            let board = try store.createPinboardTarget(name: name)\n'
  '            if assignSelection {\n'
  '                if let selectionItems {\n'
  '                    try store.assign(items: selectionItems, to: board)'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '                let board = try state.store.createPinboard(name: String(localized: '
  'OriginalPreviewLocalization.f_1001c6aa4()))\n'
  '                guard let current = self.input else { return }\n'
  '                try state.store.assign(items: [current], to: board.id)',
  '                let board = try state.store.createPinboardTarget(name: String(localized: '
  'OriginalPreviewLocalization.f_1001c6aa4()))\n'
  '                guard let current = self.input else { return }\n'
  '                try state.store.assign(items: [current], to: board)'],
 ['replica/Sources/PastoCore/ClipboardListPersistence.swift',
  '        let attributes = try encodeAttributes()',
  '        let attributes = try? encodeAttributes()']]

def pre_native_group_creation_result(source):
    source=pre_native_owner_type(source)
    if not any(marker in source for marker in ["createPinboardTarget(name:", "return (list, attributes)"]): return source
    for _,old,new in reversed(CHANGES):
        if new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    return source
