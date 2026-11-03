"""Reverse only reviewed123 capture metadata/device deltas for older source contracts."""
from new_capture_recovery_scope_contract import pre_new_capture_recovery
CHANGES = [['replica/Sources/PastoCore/ClipboardPersistence.swift',
  "/// Pasto's model adapter for the original performAndWait / hasChanges / save transaction.",
  'private struct CapturedItemCompatibilityMetadata: Decodable {\n'
  '    let title: String\n'
  '    let hasExplicitTitle: Bool?\n'
  '    let sourceIdentifier: String?\n'
  '    let sourceDevice: String\n'
  '    let pinboardIDs: Set<UUID>\n'
  '}\n'
  '\n'
  "/// Pasto's model adapter for the original performAndWait / hasChanges / save transaction."],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
  '    func searchPinboardNames(matching query: String) throws -> [(identifier: String, name: '
  'String)] {',
  '    // Capture replaces content, preview, source application and history time; only retain '
  'metadata.\n'
  '    nonisolated static func capturedItemValue(_ object: NSManagedObject, id: UUID,\n'
  '                                             replacingContentWith replacement: ClipboardItem) '
  'throws -> ClipboardItem {\n'
  '        let metadata = try Self.decode(CapturedItemCompatibilityMetadata.self, object)\n'
  '        var item = replacement\n'
  '        item.id = id\n'
  '        item.title = metadata.title\n'
  '        item.hasExplicitTitle = metadata.hasExplicitTitle\n'
  '        item.sourceIdentifier = metadata.sourceIdentifier\n'
  '        item.sourceDevice = metadata.sourceDevice\n'
  '        item.pinboardIDs = metadata.pinboardIDs\n'
  '        item.pinboardOwnerID = nil\n'
  '        item.nativeIdentifier = object.value(forKey: "nativeIdentifier") as? String\n'
  '        ClipboardItemTitlePersistence.project(&item, from: object)\n'
  '        if let list = object.value(forKey: "list") as? NSManagedObject,\n'
  '           (list.value(forKey: "rawType") as? NSNumber)?.int64Value == 2,\n'
  '           let identifier = list.value(forKey: "identifier") as? String,\n'
  '           let owner = UUID(uuidString: identifier) {\n'
  '            item.pinboardOwnerID = owner\n'
  '            item.pinboardIDs.insert(owner)\n'
  '        }\n'
  '        try ClipboardItemOrderPersistence.project(&item, from: object)\n'
  '        // Preserve valid local OCR annotations without making old payload decoding a capture '
  'gate.\n'
  '        if replacement.kind == .image, let data = object.value(forKey: "content") as? Data,\n'
  '           let dictionary = (try? PropertyListSerialization.propertyList(from: data, options: '
  '[], format: nil)) as? [String: Any],\n'
  '           dictionary["kind"] as? String == ClipboardKind.image.rawValue,\n'
  '           let payloads = dictionary["payloads"] as? [String: Data] {\n'
  '            for (type, data) in payloads where '
  'ClipboardStore.analysisPayloadKeys.contains(type) && item.payloads[type] == nil {\n'
  '                item.payloads[type] = data\n'
  '            }\n'
  '        }\n'
  '        return item\n'
  '    }\n'
  '\n'
  '    func searchPinboardNames(matching query: String) throws -> [(identifier: String, name: '
  'String)] {'],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
  '        func applyCapturedSources(_ target: (id: UUID, object: NSManagedObject), item: '
  'ClipboardItem,\n'
  '                                  applications: [SourceApplicationRecord]) throws {\n'
  '            try sources.apply(item, applications: applications, to: target.object)\n',
  '        func applyCapturedSources(_ target: (id: UUID, object: NSManagedObject), item: '
  'ClipboardItem,\n'
  '                                  applications: [SourceApplicationRecord], preserveDevice: Bool '
  '= false) throws {\n'
  '            try sources.apply(item, applications: applications, to: target.object, '
  'preserveDevice: preserveDevice)\n'],
 ['replica/Sources/PastoCore/ClipboardStore.swift',
  '                        state.items.append(try '
  'ClipboardPersistence.item(capturedTarget.object))\n',
  '                        state.items.append(try '
  'ClipboardPersistence.capturedItemValue(capturedTarget.object,\n'
  '                            id: capturedTarget.id, replacingContentWith: item))\n'],
 ['replica/Sources/PastoCore/ClipboardStore.swift',
  '                try transaction.repository.applyCapturedSources(target!, item: '
  'state.items[result.index],\n'
  '                                                                applications: '
  'state.sourceApplications)\n',
  '                try transaction.repository.applyCapturedSources(target!, item: '
  'state.items[result.index],\n'
  '                    applications: state.sourceApplications, preserveDevice: capturedTarget != '
  'nil)\n'],
 ['replica/Sources/PastoCore/ClipboardSourcePersistence.swift',
  '    func apply(_ item: ClipboardItem, applications: [SourceApplicationRecord], to object: '
  'NSManagedObject) throws {',
  '    func apply(_ item: ClipboardItem, applications: [SourceApplicationRecord], to object: '
  'NSManagedObject,\n'
  '               preserveDevice: Bool = false) throws {'],
 ['replica/Sources/PastoCore/ClipboardSourcePersistence.swift',
  '        let device = try device(named: item.sourceDevice)\n',
  '        guard !preserveDevice else { return }\n'
  '        let device = try device(named: item.sourceDevice)\n']]

def pre_capture_metadata_device(source):
    source=pre_new_capture_recovery(source)
    for _,old,new in reversed(CHANGES):
        if new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    return source
