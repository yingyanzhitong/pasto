"""Isolate the phase78 native application projection for earlier frozen source contracts.

New raw-source/encoding-key/consumer checks live in test_p1_repair_live_application_projection.
Only these five reviewed insertions are removed; immutable earlier evidence remains unchanged.
"""
from pathlib import Path
from collection_membership_scope_contract import pre_collection_membership

INSERTIONS = [('replica/Sources/PastoCore/ClipboardPersistence.swift',
  '        try ClipboardSourcePersistence.projectApplication(&item, from: object)\n'),
 ('replica/Sources/PastoCore/ClipboardPersistence.swift',
  '        value.sourceApplicationSnapshot = nil\n        value.hasSourceApplicationSnapshot = false\n'),
 ('replica/Sources/PastoCore/ClipboardStore.swift',
  '        if item.hasSourceApplicationSnapshot { return item.sourceApplicationSnapshot }\n'),
 ('replica/Sources/PastoCore/ClipboardSourcePersistence.swift',
  "    // 38222c / 383df4 consume the selected entity's current sourceApplication relation.\n"
  '    nonisolated static func projectApplication(_ item: inout ClipboardItem, from object: NSManagedObject) '
  'throws {\n'
  '        item.hasSourceApplicationSnapshot = true\n'
  '        item.sourceApplicationRelationIsKnown = true\n'
  '        guard let application = object.value(forKey: "sourceApplication") as? NSManagedObject else {\n'
  '            item.sourceApplicationSnapshot = nil\n'
  '            item.sourceApplicationBundleID = nil\n'
  '            return\n'
  '        }\n'
  '        guard let identifier = application.value(forKey: "bundleIdentifier") as? String,\n'
  '              let name = application.value(forKey: "name") as? String,\n'
  '              let color = application.value(forKey: "rawColor") as? NSNumber else {\n'
  '            throw CocoaError(.fileReadCorruptFile)\n'
  '        }\n'
  '        item.sourceApplicationBundleID = identifier\n'
  '        item.sourceApplicationSnapshot = SourceApplicationRecord(bundleIdentifier: identifier, name: '
  'name,\n'
  '            rawIcon: application.value(forKey: "rawIcon") as? Data,\n'
  '            rawColor: UInt64(bitPattern: color.int64Value))\n'
  '    }\n'
  '\n'),
 ('replica/Sources/PastoCore/Models.swift',
  '\n'
  '    // This is a read-time projection of the native relation, never archived as item content.\n'
  '    public var sourceApplicationSnapshot: SourceApplicationRecord? = nil\n'
  '    public var hasSourceApplicationSnapshot = false\n'
  '\n'
  '    private enum CodingKeys: String, CodingKey {\n'
  '        case id, nativeIdentifier, nativeChecksum, sourceIdentifier, createdAt\n'
  '        case updatedAt, title, hasExplicitTitle, kind, plainText\n'
  '        case sourceName, sourceBundleID, sourceApplicationBundleID, sourceApplicationRelationIsKnown, '
  'sourceDevice\n'
  '        case isInHistory, payloads, imagePreviewMetadata, rawPreview, pinboardIDs\n'
  '        case pinboardOwnerID, pinboardOrder, isDeleted\n'
  '    }\n')]

def pre_native_application(source):
    source = pre_collection_membership(source)
    for path, addition in INSERTIONS:
        if addition in source:
            assert source.count(addition) == 1, path
            source = source.replace(addition, '', 1)
    return source


def pre_native_application_bytes(path):
    path = Path(path)
    value = path.read_bytes()
    return pre_native_application(value.decode()).encode() if path.suffix == '.swift' else value
