"""Reverse only reviewed126 local-device deltas for historical source checks."""
from raw_data_diagnostic_scope_contract import pre_raw_data_diagnostic
CHANGES = [['replica/Sources/PastoCore/ClipboardSourcePersistence.swift',
  '    private func device(named name: String) throws -> NSManagedObject {',
  '    // 312150: current hardware identity is distinct from legacy archive display names.\n'
  '    func currentDevice() -> NSManagedObject {\n'
  '        let identifier = OriginalLocalDevice.f_1000f35e0()\n'
  '        let request = NSFetchRequest<NSManagedObject>(entityName: "DeviceEntity")\n'
  '        request.predicate = NSPredicate(format: "identifier == %@", identifier)\n'
  '        request.fetchBatchSize = 20\n'
  '        request.fetchLimit = 1\n'
  '        request.fetchOffset = 0\n'
  '        if let existing = (try? context.fetch(request))?.first { return existing }\n'
  '        let name = OriginalLocalDevice.f_1000f36ec()\n'
  '        let object = NSEntityDescription.insertNewObject(forEntityName: "DeviceEntity", into: '
  'context)\n'
  '        object.setValue(Int64(2), forKey: "rawType")\n'
  '        object.setValue(identifier, forKey: "identifier")\n'
  '        object.setValue(name, forKey: "name")\n'
  '        // The existing local model requires this creation column.\n'
  '        object.setValue(Date(), forKey: "createdAt")\n'
  '        return object\n'
  '    }\n'
  '\n'
  '    private func device(named name: String) throws -> NSManagedObject {'],
 ['replica/Sources/PastoCore/ClipboardPersistence.swift',
  '        func initializeCapturedDevice(_ target: (id: UUID, object: NSManagedObject), name: '
  'String) throws {\n'
  '            try sources.applyDevice(named: name, to: target.object)\n'
  '        }\n',
  '        func initializeCapturedDevice(_ target: (id: UUID, object: NSManagedObject)) -> String '
  '{\n'
  '            let device = sources.currentDevice()\n'
  '            target.object.setValue(device, forKey: "device")\n'
  '            return device.value(forKey: "name") as? String ?? ""\n'
  '        }\n'],
 ['replica/Sources/PastoCore/ClipboardStore.swift',
  '                    try transaction.repository.initializeCapturedDevice(target!, name: '
  'state.items[result.index].sourceDevice)\n',
  '                    state.items[result.index].sourceDevice = '
  'transaction.repository.initializeCapturedDevice(target!)\n'],
 ['replica/Sources/PastoCore/ClipboardSourcePersistence.swift',
  'import CoreData\nimport Foundation\n',
  'import CoreData\nimport CoreFoundation\nimport Darwin\nimport Foundation\nimport IOKit\n'],
 ['replica/Sources/PastoCore/ClipboardSourcePersistence.swift',
  '    func deviceNames(matching query: String) throws -> [String] {\n'
  '        try names(in: "DeviceEntity", matching: query)\n'
  '    }\n'
  '}\n',
  '    func deviceNames(matching query: String) throws -> [String] {\n'
  '        try names(in: "DeviceEntity", matching: query)\n'
  '    }\n'
  '}\n'
  '\n'
  '/// Local device information used by the original DeviceEntity factory.\n'
  'enum OriginalLocalDevice {\n'
  '    // 0f35e0 reads the registry on each request; failed reads share the original Unknown '
  'identity.\n'
  '    static func f_1000f35e0() -> String {\n'
  '        let service = IOServiceGetMatchingService(kIOMainPortDefault, '
  'IOServiceMatching("IOPlatformExpertDevice"))\n'
  '        defer { _ = IOObjectRelease(service) }\n'
  '        guard service != 0,\n'
  '              let value = IORegistryEntryCreateCFProperty(service, "IOPlatformSerialNumber" as '
  'CFString,\n'
  '                  kCFAllocatorDefault, 0)?.takeRetainedValue() as? String else { return '
  '"Unknown" }\n'
  '        return value\n'
  '    }\n'
  '\n'
  '    static func f_1000f36ec() -> String {\n'
  '        modelName(f_1000f4774("hw.model"))\n'
  '    }\n'
  '\n'
  '    static func modelName(_ model: String) -> String {\n'
  '        let trimmed = model.trimmingCharacters(in: CharacterSet.letters.inverted)\n'
  '        switch trimmed.lowercased() {\n'
  '        case "macbook": return "MacBook"\n'
  '        case "macbookpro": return "MacBook Pro"\n'
  '        case "macbookair": return "MacBook Air"\n'
  '        case "imac": return "iMac"\n'
  '        case "macpro": return "Mac Pro"\n'
  '        default: return trimmed\n'
  '        }\n'
  '    }\n'
  '\n'
  '    // 0f4774 ignores both status codes and decodes the allocated, zero-terminated UTF-8 '
  'prefix.\n'
  '    static func f_1000f4774(_ key: String) -> String {\n'
  '        var size = 0\n'
  '        _ = sysctlbyname(key, nil, &size, nil, 0)\n'
  '        var bytes = [UInt8](repeating: 0, count: size)\n'
  '        bytes.withUnsafeMutableBytes { buffer in\n'
  '            _ = sysctlbyname(key, buffer.baseAddress, &size, nil, 0)\n'
  '        }\n'
  '        return String(bytes: bytes.prefix { $0 != 0 }, encoding: .utf8) ?? ""\n'
  '    }\n'
  '}\n']]

def pre_local_device(source):
    source=pre_raw_data_diagnostic(source)
    for _,old,new in reversed(CHANGES):
        if new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    return source
