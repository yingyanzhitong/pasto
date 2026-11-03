import AppKit
import CoreData
import CoreFoundation
import Darwin
import Foundation
import IOKit

/// Native source relationships used by the recovered suggestion queries.
/// Legacy value records remain available for archives and local display compatibility.
@MainActor
final class ClipboardSourcePersistence {
    static let versionKey = "sourceGraphVersion"
    private let context: NSManagedObjectContext

    init(context: NSManagedObjectContext) { self.context = context }

    static func addEntities(to model: NSManagedObjectModel, item: NSEntityDescription) {
        func attribute(_ name: String, _ type: NSAttributeType, optional: Bool = false,
                       defaultValue: Any? = nil) -> NSAttributeDescription {
            let value = NSAttributeDescription()
            value.name = name; value.attributeType = type; value.isOptional = optional
            value.defaultValue = defaultValue
            return value
        }
        func entity(_ name: String, key: String, properties: [NSAttributeDescription]) -> NSEntityDescription {
            let value = NSEntityDescription()
            value.name = name; value.managedObjectClassName = "NSManagedObject"
            properties.first(where: { $0.name == key })?.isIndexed = true
            value.properties = properties; value.uniquenessConstraints = [[key]]
            return value
        }
        func connect(_ name: String, source: NSEntityDescription) {
            let owner = NSRelationshipDescription()
            owner.name = name; owner.destinationEntity = source
            owner.minCount = 0; owner.maxCount = 1; owner.isOptional = true
            owner.deleteRule = .nullifyDeleteRule
            let items = NSRelationshipDescription()
            items.name = "items"; items.destinationEntity = item
            items.minCount = 0; items.maxCount = 0; items.isOptional = true
            items.deleteRule = .nullifyDeleteRule
            owner.inverseRelationship = items; items.inverseRelationship = owner
            item.properties.append(owner); source.properties.append(items)
        }
        let application = entity("ApplicationEntity", key: "bundleIdentifier", properties: [
            attribute("bundleIdentifier", .stringAttributeType), attribute("name", .stringAttributeType),
            attribute("rawColor", .integer64AttributeType, defaultValue: 0),
            attribute("rawIcon", .binaryDataAttributeType, optional: true),
            attribute("createdAt", .dateAttributeType), attribute("updatedAt", .dateAttributeType, optional: true)
        ])
        let device = entity("DeviceEntity", key: "identifier", properties: [
            attribute("identifier", .stringAttributeType), attribute("name", .stringAttributeType),
            attribute("rawType", .integer64AttributeType, defaultValue: 0),
            attribute("appVersion", .stringAttributeType, defaultValue: ""),
            attribute("createdAt", .dateAttributeType), attribute("updatedAt", .dateAttributeType, optional: true)
        ])
        connect("sourceApplication", source: application)
        connect("device", source: device)
        model.entities += [application, device]
        model.entitiesByName["State"]!.properties.append(attribute(versionKey, .integer64AttributeType, defaultValue: 0))
    }

    private func first<Entity: PastoManagedObject>(_ entity: Entity.Type, key: String, value: String) throws -> Entity? {
        let request = OriginalManagedFetchRequest.make(for: entity)
        request.predicate = NSPredicate(format: "%K == %@", key, value)
        request.fetchLimit = 1
        request.fetchOffset = 0
        return try context.fetch(request).first
    }

    @discardableResult
    func application(_ value: SourceApplicationRecord) throws -> NSManagedObject {
        let object: NSManagedObject
        if let existing = try first(PastoApplicationEntity.self, key: "bundleIdentifier", value: value.bundleIdentifier) {
            object = existing
        } else {
            object = NSEntityDescription.insertNewObject(forEntityName: "ApplicationEntity", into: context)
            object.setValue(value.bundleIdentifier, forKey: "bundleIdentifier")
        }
        if (object.value(forKey: "name") as? String) != value.name { object.setValue(value.name, forKey: "name") }
        if (object.value(forKey: "rawIcon") as? Data) != value.rawIcon { object.setValue(value.rawIcon, forKey: "rawIcon") }
        let color = Int64(bitPattern: value.rawColor ?? 0)
        if (object.value(forKey: "rawColor") as? NSNumber)?.int64Value != color {
            object.setValue(color, forKey: "rawColor")
        }
        return object
    }

    // 312150: current hardware identity is distinct from legacy archive display names.
    func currentDevice() -> NSManagedObject {
        let identifier = OriginalLocalDevice.f_1000f35e0()
        let request = OriginalManagedFetchRequest.make(for: PastoDeviceEntity.self)
        request.predicate = NSPredicate(format: "identifier == %@", identifier)
        request.fetchLimit = 1
        request.fetchOffset = 0
        if let existing = (try? context.fetch(request))?.first { return existing }
        let name = OriginalLocalDevice.f_1000f36ec()
        let object = NSEntityDescription.insertNewObject(forEntityName: "DeviceEntity", into: context)
        object.setValue(Int64(2), forKey: "rawType")
        object.setValue(identifier, forKey: "identifier")
        object.setValue(name, forKey: "name")
        return object
    }

    private func device(named name: String) throws -> NSManagedObject {
        if let existing = try first(PastoDeviceEntity.self, key: "name", value: name) { return existing }
        // Old Pasto records have a device name, but no vendor/device UUID.
        let object = NSEntityDescription.insertNewObject(forEntityName: "DeviceEntity", into: context)
        object.setValue(UUID().uuidString, forKey: "identifier")
        object.setValue(name, forKey: "name")
        return object
    }

    func apply(_ item: ClipboardItem, applications: [SourceApplicationRecord], to object: NSManagedObject,
               preserveDevice: Bool = false) throws {
        let source: NSManagedObject?
        if let identifier = item.sourceApplicationBundleID {
            guard let value = applications.first(where: { $0.bundleIdentifier == identifier }) else {
                throw ClipboardStoreError.invalidSourceApplication
            }
            source = try application(value)
        } else { source = nil }
        if (object.value(forKey: "sourceApplication") as? NSManagedObject) !== source {
            object.setValue(source, forKey: "sourceApplication")
        }
        guard !preserveDevice else { return }
        try applyDevice(named: item.sourceDevice, to: object)
    }

    func applyDevice(named name: String, to object: NSManagedObject) throws {
        let device = try device(named: name)
        if (object.value(forKey: "device") as? NSManagedObject) !== device {
            object.setValue(device, forKey: "device")
        }
    }

    // 38222c / 383df4 consume the selected entity's current sourceApplication relation.
    nonisolated static func projectApplication(_ item: inout ClipboardItem, from object: NSManagedObject) throws {
        item.hasSourceApplicationSnapshot = true
        item.sourceApplicationRelationIsKnown = true
        guard let application = object.value(forKey: "sourceApplication") as? NSManagedObject else {
            item.sourceApplicationSnapshot = nil
            item.sourceApplicationBundleID = nil
            return
        }
        guard let identifier = application.value(forKey: "bundleIdentifier") as? String,
              let name = application.value(forKey: "name") as? String,
              let color = application.value(forKey: "rawColor") as? NSNumber else {
            throw CocoaError(.fileReadCorruptFile)
        }
        item.sourceApplicationBundleID = identifier
        item.sourceApplicationSnapshot = SourceApplicationRecord(bundleIdentifier: identifier, name: name,
            rawIcon: application.value(forKey: "rawIcon") as? Data,
            rawColor: UInt64(bitPattern: color.int64Value))
    }

    // 35fa18/35fe08: the icon readers use exact case-insensitive names, not the suggestion regex.
    private func firstNamed<Entity: PastoManagedObject>(_ entity: Entity.Type, name: String) -> Entity? {
        let request = OriginalManagedFetchRequest.make(for: entity)
        request.predicate = NSPredicate(format: "name ==[c] %@", name)
        request.fetchLimit = 1
        request.fetchOffset = 0
        return (try? context.fetch(request))?.first
    }

    func applicationImage(named name: String) -> NSImage? {
        guard let application = firstNamed(PastoApplicationEntity.self, name: name) else { return nil }
        return (application.value(forKey: "rawIcon") as? Data).flatMap(NSImage.init(data:)) ?? NSImage()
    }

    func deviceType(named name: String) -> UInt8? {
        guard let device = firstNamed(PastoDeviceEntity.self, name: name) else { return nil }
        let rawType = (device.value(forKey: "rawType") as? NSNumber)?.int64Value ?? 0
        precondition(rawType >= 0 && rawType < 3)
        return UInt8(rawType)
    }

    // 0x10030e070 / 0x10030ed6c share this dictionary/name query shape.
    private func names(in entity: String, matching query: String) throws -> [String] {
        let request = NSFetchRequest<NSDictionary>(entityName: entity)
        request.resultType = .dictionaryResultType
        request.returnsDistinctResults = true
        request.propertiesToFetch = ["name"]
        if query.isEmpty {
            request.predicate = NSPredicate(format: "items.@count > 0")
        } else {
            request.predicate = NSPredicate(format: "name MATCHES[cd] %@ AND items.@count > 0",
                OriginalSearchSuggestions.f_1002f5100(query))
        }
        request.sortDescriptors = [NSSortDescriptor(key: "name", ascending: true)]
        return try context.fetch(request).compactMap { $0["name"] as? String }.filter { !$0.isEmpty }
    }

    func applicationNames(matching query: String) throws -> [String] {
        try names(in: "ApplicationEntity", matching: query)
    }

    func deviceNames(matching query: String) throws -> [String] {
        try names(in: "DeviceEntity", matching: query)
    }
}

/// Local device information used by the original DeviceEntity factory.
enum OriginalLocalDevice {
    // 0f35e0 reads the registry on each request; failed reads share the original Unknown identity.
    static func f_1000f35e0() -> String {
        let service = IOServiceGetMatchingService(kIOMainPortDefault, IOServiceMatching("IOPlatformExpertDevice"))
        defer { _ = IOObjectRelease(service) }
        guard service != 0,
              let value = IORegistryEntryCreateCFProperty(service, "IOPlatformSerialNumber" as CFString,
                  kCFAllocatorDefault, 0)?.takeRetainedValue() as? String else { return "Unknown" }
        return value
    }

    static func f_1000f36ec() -> String {
        modelName(f_1000f4774("hw.model"))
    }

    static func modelName(_ model: String) -> String {
        let trimmed = model.trimmingCharacters(in: CharacterSet.letters.inverted)
        switch trimmed.lowercased() {
        case "macbook": return "MacBook"
        case "macbookpro": return "MacBook Pro"
        case "macbookair": return "MacBook Air"
        case "imac": return "iMac"
        case "macpro": return "Mac Pro"
        default: return trimmed
        }
    }

    // 0f4774 ignores both status codes and decodes the allocated, zero-terminated UTF-8 prefix.
    static func f_1000f4774(_ key: String) -> String {
        var size = 0
        _ = sysctlbyname(key, nil, &size, nil, 0)
        var bytes = [UInt8](repeating: 0, count: size)
        bytes.withUnsafeMutableBytes { buffer in
            _ = sysctlbyname(key, buffer.baseAddress, &size, nil, 0)
        }
        return String(bytes: bytes.prefix { $0 != 0 }, encoding: .utf8) ?? ""
    }
}
