"""Reverse only reviewed162 native List metadata deferral and success-only value projection."""
CHANGES = [['replica/Sources/PastoCore/ClipboardListPersistence.swift',
  '    var refreshHistoryAfterOperation = false',
  '    var refreshHistoryAfterOperation = false\n'
  '    private var createdPinboards: [String: PastoListEntity] = [:]',
  1],
 ['replica/Sources/PastoCore/ClipboardListPersistence.swift',
  '    func insertPinboard(identifier: String, name: String, index: Int64,\n'
  '                        encodeAttributes: () throws -> Data?) throws -> (object: '
  'NSManagedObject, attributes: Data?) {\n'
  '        let list = NSEntityDescription.insertNewObject(forEntityName: "ListEntity", into: '
  'context)\n'
  '        list.setValue(identifier, forKey: "identifier")\n'
  '        list.setValue(name, forKey: "name")\n'
  "        // Pasto's model requires explicit metadata and creation dates; the original entity "
  'factory is separate.\n'
  '        let now = Date()\n'
  '        list.setValue(now, forKey: "createdAt")\n'
  '        let metadata = NSEntityDescription.insertNewObject(forEntityName: "ListMetadataEntity", '
  'into: context)\n'
  '        metadata.setValue(identifier, forKey: "identifier")\n'
  '        metadata.setValue(index, forKey: "index")\n'
  '        metadata.setValue(now, forKey: "createdAt")\n'
  '        list.setValue(metadata, forKey: "metadata")\n'
  '        // ARM 3686b8...3686e8 releases a permanent-ID error and rejoins the encoding path.\n'
  '        try? context.obtainPermanentIDs(for: [list])\n'
  '        let attributes = try? encodeAttributes()\n'
  '        list.setValue(attributes, forKey: "rawAttributes")\n'
  '        list.setValue(Int64(2), forKey: "rawType")\n'
  '        return (list, attributes)\n'
  '    }',
  '    func insertPinboard(identifier: String, name: String,\n'
  '                        encodeAttributes: () throws -> Data?) throws -> (object: '
  'NSManagedObject, attributes: Data?) {\n'
  '        let list = PastoListEntity(context: context)\n'
  '        list.setValue(identifier, forKey: "identifier")\n'
  '        list.setValue(name, forKey: "name")\n'
  '        createdPinboards[identifier] = list\n'
  '        // ARM 3686b8...3686e8 releases a permanent-ID error and rejoins the encoding path.\n'
  '        try? context.obtainPermanentIDs(for: [list])\n'
  '        let attributes = try? encodeAttributes()\n'
  '        list.setValue(attributes, forKey: "rawAttributes")\n'
  '        list.setValue(Int64(2), forKey: "rawType")\n'
  '        return (list, attributes)\n'
  '    }',
  1],
 ['replica/Sources/PastoCore/ClipboardListPersistence.swift',
  '            guard let metadata = list.value(forKey: "metadata") as? NSManagedObject else {\n'
  '                throw CocoaError(.fileReadCorruptFile)\n'
  '            }\n'
  '            set(Int64(board.sortOrder), key: "index", on: metadata)',
  '            // A newly created native List supplies metadata/index in validateForInsert, not '
  'this value adapter.\n'
  '            if createdPinboards[identifier] === list { continue }\n'
  '            guard let metadata = list.value(forKey: "metadata") as? NSManagedObject else {\n'
  '                throw CocoaError(.fileReadCorruptFile)\n'
  '            }\n'
  '            set(Int64(board.sortOrder), key: "index", on: metadata)',
  1],
 ['replica/Sources/PastoCore/ClipboardListPersistence.swift',
  '    func project(_ pinboards: [Pinboard]) throws -> [Pinboard] {',
  '    // Saving has already run the List validator. Project only its created objects, without '
  'another fetch/save.\n'
  '    func projectCreatedPinboards(_ pinboards: [Pinboard]) -> [Pinboard] {\n'
  '        guard !createdPinboards.isEmpty else { return pinboards }\n'
  '        return pinboards.map { board in\n'
  '            guard let list = createdPinboards[board.id.uuidString],\n'
  '                  let metadata = list.value(forKey: "metadata") as? NSManagedObject,\n'
  '                  let index = metadata.value(forKey: "index") as? NSNumber else { return board '
  '}\n'
  '            var value = board\n'
  '            value.sortOrder = index.intValue\n'
  '            return value\n'
  '        }.sorted { $0.sortOrder == $1.sortOrder ? $0.id.uuidString < $1.id.uuidString : '
  '$0.sortOrder < $1.sortOrder }\n'
  '    }\n'
  '\n'
  '    func project(_ pinboards: [Pinboard]) throws -> [Pinboard] {',
  1],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
  '                let outcome = try operation(transaction)',
  '                var outcome = try operation(transaction)',
  1],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
  '                return outcome',
  '                outcome.state.pinboards = '
  'transaction.repository.lists.projectCreatedPinboards(outcome.state.pinboards)\n'
  '                return outcome',
  1],
 ['replica/Sources/PastoCore/ClipboardStore.swift',
  '{\n'
  '        return try mutateInTransaction { state, transaction in\n'
  '            let code: UInt64?\n'
  '            let value: String\n'
  '            if let colorHex {\n'
  '                value = colorHex\n'
  '                code = OriginalPinboardAttributes.parsedColorCode(colorHex)\n'
  '            } else {\n'
  '                // Keep the original eight-color palette (0x100324a80), but prefer\n'
  '                // unused colors as requested; the original creation path is random.\n'
  '                let used = Set(state.pinboards.compactMap { board -> OriginalPinboardColor? in\n'
  '                    guard let code = OriginalPinboardAttributes.colorCode(from: '
  'board.rawAttributes)\n'
  '                        ?? OriginalPinboardAttributes.parsedColorCode(board.colorHex) else { '
  'return nil }\n'
  '                    return OriginalPinboardColor(canonicalColorCode: code)\n'
  '                })\n'
  '                let unused = OriginalPinboardColor.allCases.filter { !used.contains($0) }\n'
  '                let palette = unused.isEmpty ? OriginalPinboardColor.allCases : unused\n'
  '                let color = palette[Int.random(in: 0..<palette.count)]\n'
  '                code = color.canonicalColorCode\n'
  '                value = String(format: "#%06llX", color.canonicalColorCode)\n'
  '            }\n'
  '            let id = UUID()\n'
  '            let sortOrder = (state.pinboards.map(\\.sortOrder).max() ?? -1) + 1\n'
  '            let created = try transaction.repository.lists.insertPinboard(identifier: '
  'id.uuidString,\n'
  '                name: name, index: Int64(sortOrder)) {\n'
  '                try code.map { try OriginalPinboardAttributes.encoded(colorCode: $0) }\n'
  '            }\n'
  '            let board = Pinboard(id: id, name: name, colorHex: value, sortOrder: sortOrder,\n'
  '                                 rawType: 2, rawAttributes: created.attributes)\n'
  '            state.pinboards.append(board)\n'
  '            return (board, ClipboardPinboardTarget(id: id, object: created.object))\n'
  '        }\n'
  '    }',
  '{\n'
  '        let result: (board: Pinboard, target: ClipboardPinboardTarget) = try '
  'mutateInTransaction { state, transaction in\n'
  '            let code: UInt64?\n'
  '            let value: String\n'
  '            if let colorHex {\n'
  '                value = colorHex\n'
  '                code = OriginalPinboardAttributes.parsedColorCode(colorHex)\n'
  '            } else {\n'
  '                // Keep the original eight-color palette (0x100324a80), but prefer\n'
  '                // unused colors as requested; the original creation path is random.\n'
  '                let used = Set(state.pinboards.compactMap { board -> OriginalPinboardColor? in\n'
  '                    guard let code = OriginalPinboardAttributes.colorCode(from: '
  'board.rawAttributes)\n'
  '                        ?? OriginalPinboardAttributes.parsedColorCode(board.colorHex) else { '
  'return nil }\n'
  '                    return OriginalPinboardColor(canonicalColorCode: code)\n'
  '                })\n'
  '                let unused = OriginalPinboardColor.allCases.filter { !used.contains($0) }\n'
  '                let palette = unused.isEmpty ? OriginalPinboardColor.allCases : unused\n'
  '                let color = palette[Int.random(in: 0..<palette.count)]\n'
  '                code = color.canonicalColorCode\n'
  '                value = String(format: "#%06llX", color.canonicalColorCode)\n'
  '            }\n'
  '            let id = UUID()\n'
  '            let created = try transaction.repository.lists.insertPinboard(identifier: '
  'id.uuidString,\n'
  '                name: name) {\n'
  '                try code.map { try OriginalPinboardAttributes.encoded(colorCode: $0) }\n'
  '            }\n'
  '            let board = Pinboard(id: id, name: name, colorHex: value, sortOrder: 0,\n'
  '                                 rawType: 2, rawAttributes: created.attributes)\n'
  '            state.pinboards.append(board)\n'
  '            return (board, ClipboardPinboardTarget(id: id, object: created.object))\n'
  '        }\n'
  '        var board = result.board\n'
  '        if let metadata = result.target.nativeObject.value(forKey: "metadata") as? '
  'NSManagedObject,\n'
  '           let index = metadata.value(forKey: "index") as? NSNumber { board.sortOrder = '
  'index.intValue }\n'
  '        return (board, result.target)\n'
  '    }',
  1]]

from native_group_read_projection_scope_contract import pre_native_group_read_projection

def pre_native_list_creation_lifecycle(source):
    source=pre_native_group_read_projection(source)
    for _,old,new,count in reversed(CHANGES):
        if new in source:
            assert source.count(new)==count
            source=source.replace(new,old)
    return source

def pre_native_list_creation_lifecycle_bytes(path):
    data=path.read_bytes()
    return pre_native_list_creation_lifecycle(data.decode()).encode()if path.suffix=='.swift'else data
