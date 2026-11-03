"""Reverse only reviewed124 capture init/retry deltas for earlier source checks."""
from mixed_restore_scope_contract import pre_mixed_restore
CHANGES = [['replica/Sources/PastoCore/ClipboardSourcePersistence.swift',
  '        guard !preserveDevice else { return }\n'
  '        let device = try device(named: item.sourceDevice)\n',
  '        guard !preserveDevice else { return }\n'
  '        try applyDevice(named: item.sourceDevice, to: object)\n'
  '    }\n'
  '\n'
  '    func applyDevice(named name: String, to object: NSManagedObject) throws {\n'
  '        let device = try device(named: name)\n'],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
  '        let metadata = try Self.decode(CapturedItemCompatibilityMetadata.self, object)\n'
  '        var item = replacement\n'
  '        item.id = id\n'
  '        item.title = metadata.title\n'
  '        item.hasExplicitTitle = metadata.hasExplicitTitle\n'
  '        item.sourceIdentifier = metadata.sourceIdentifier\n'
  '        item.sourceDevice = metadata.sourceDevice\n'
  '        item.pinboardIDs = metadata.pinboardIDs\n',
  '        let metadata: CapturedItemCompatibilityMetadata?\n'
  '        if object.isInserted, object.value(forKey: "content") == nil {\n'
  '            // A failed new capture may have native content before its compatibility value is '
  'saved.\n'
  '            metadata = nil\n'
  '        } else {\n'
  '            metadata = try Self.decode(CapturedItemCompatibilityMetadata.self, object)\n'
  '        }\n'
  '        var item = replacement\n'
  '        item.id = id\n'
  '        if let metadata {\n'
  '            item.title = metadata.title\n'
  '            item.hasExplicitTitle = metadata.hasExplicitTitle\n'
  '            item.sourceIdentifier = metadata.sourceIdentifier\n'
  '            item.sourceDevice = metadata.sourceDevice\n'
  '            item.pinboardIDs = metadata.pinboardIDs\n'
  '        } else {\n'
  '            item.title = ""\n'
  '            item.hasExplicitTitle = false\n'
  '            item.sourceIdentifier = nil\n'
  '            item.sourceDevice = (object.value(forKey: "device") as? '
  'NSManagedObject)?.value(forKey: "name") as? String\n'
  '                ?? replacement.sourceDevice\n'
  '            item.pinboardIDs = []\n'
  '        }\n'],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
  '        func applyCapturedSources(_ target: (id: UUID, object: NSManagedObject), item: '
  'ClipboardItem,\n',
  '        func initializeCapturedDevice(_ target: (id: UUID, object: NSManagedObject), name: '
  'String) throws {\n'
  '            try sources.applyDevice(named: name, to: target.object)\n'
  '        }\n'
  '\n'
  '        func applyCapturedSources(_ target: (id: UUID, object: NSManagedObject), item: '
  'ClipboardItem,\n'],
 ['replica/Sources/PastoCore/ClipboardStore.swift',
  '                let items = try Self.originalPasteboardItems(from: '
  'state.items[result.index].payloads)\n',
  '                if capturedTarget == nil {\n'
  '                    try transaction.repository.initializeCapturedDevice(target!, name: '
  'state.items[result.index].sourceDevice)\n'
  '                }\n'
  '                let items = try Self.originalPasteboardItems(from: '
  'state.items[result.index].payloads)\n'],
 ['replica/Sources/PastoCore/ClipboardStore.swift',
  '                    applications: state.sourceApplications, preserveDevice: capturedTarget != '
  'nil)\n',
  '                    applications: state.sourceApplications, preserveDevice: true)\n']]

def pre_new_capture_recovery(source):
    source=pre_mixed_restore(source)
    for _,old,new in reversed(CHANGES):
        if new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    return source
