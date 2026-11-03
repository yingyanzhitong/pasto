"""Reverse only reviewed122 native checksum lookup changes for historical checks."""
from capture_metadata_device_scope_contract import pre_capture_metadata_device
CHANGES = [['replica/Sources/PastoCore/ClipboardPersistence.swift',
  '        func prepareHistoryItems(_ ids: [UUID]) throws -> [(id: UUID, object: NSManagedObject)] '
  '{',
  '        // 3214c8/328bc8: lookup by native checksum; fetch failure is an empty result.\n'
  '        func capturedItem(checksum: String?) throws -> (id: UUID, object: NSManagedObject)? {\n'
  '            guard let checksum else { return nil }\n'
  '            let request = PastoItemEntity.defaultFetchRequest()\n'
  '            request.predicate = NSPredicate(format: "nativeChecksum == %@", checksum)\n'
  '            request.fetchLimit = 1\n'
  '            request.fetchOffset = 0\n'
  '            guard let object = (try? context.fetch(request))?.first else { return nil }\n'
  '            guard let key = object.value(forKey: "key") as? String,\n'
  '                  let id = UUID(uuidString: key) else { throw CocoaError(.fileReadCorruptFile) '
  '}\n'
  '            return (id: id, object: object)\n'
  '        }\n'
  '\n'
  '        func prepareHistoryItems(_ ids: [UUID]) throws -> [(id: UUID, object: NSManagedObject)] '
  '{'],
 ['replica/Sources/PastoCore/ClipboardStore.swift',
  '            let result: (index: Int, isNew: Bool)\n'
  '            if let i = state.items.firstIndex(where: { previous in\n'
  '                if recordCapture {\n'
  '                    guard let checksum else { return false }\n'
  '                    return previous.nativeChecksum == checksum\n'
  '                }\n',
  '            let capturedTarget = recordCapture ? try '
  'transaction.repository.capturedItem(checksum: checksum) : nil\n'
  '            let existingIndex: Int?\n'
  '            if recordCapture {\n'
  '                if let capturedTarget {\n'
  '                    if let index = state.items.firstIndex(where: { $0.id == capturedTarget.id '
  '}) {\n'
  '                        existingIndex = index\n'
  '                    } else {\n'
  '                        state.items.append(try '
  'ClipboardPersistence.item(capturedTarget.object))\n'
  '                        existingIndex = state.items.count - 1\n'
  '                    }\n'
  '                } else { existingIndex = nil }\n'
  '            } else {\n'
  '                existingIndex = state.items.firstIndex(where: { previous in\n'],
 ['replica/Sources/PastoCore/ClipboardStore.swift',
  '                    && Self.hasSamePasteboardRepresentations(previous.payloads, item.payloads)\n'
  '            }) {\n'
  '                let analysis = state.items[i].kind == .image && item.kind == .image\n',
  '                    && Self.hasSamePasteboardRepresentations(previous.payloads, item.payloads)\n'
  '                })\n'
  '            }\n'
  '            let result: (index: Int, isNew: Bool)\n'
  '            if let i = existingIndex {\n'
  '                let analysis = state.items[i].kind == .image && item.kind == .image\n'],
 ['replica/Sources/PastoCore/ClipboardStore.swift',
  '                target = try '
  'transaction.repository.prepareHistoryItems([state.items[result.index].id]).first!\n',
  '                target = try capturedTarget ?? '
  'transaction.repository.prepareHistoryItems([state.items[result.index].id]).first!\n']]

def pre_native_capture_lookup(source):
    source=pre_capture_metadata_device(source)
    for _,old,new in reversed(CHANGES):
        if new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    return source
