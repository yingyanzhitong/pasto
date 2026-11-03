import CoreData
import Foundation
import os

/// 0x100371998: metadata plus deferred content/image readers, copied without evaluating them.
public struct ClipboardSearchRecord: Equatable {
    public let id: UUID
    public let nativeIdentifier: String?
    public let type: String
    public let title: String
    public let app: String?
    public let modified: Date?
    public let device: String?
    public let pinboard: String?
    public let content: (() -> String?)?
    public let imageData: (() -> Data?)?
    // Pasto's value-cache invalidation metadata; not an original SearchableItemEntity field.
    public let contentVersion: Date

    public var searchIdentifier: String { nativeIdentifier ?? id.uuidString }

    // 0x1002ee16c: preserve metadata, append OCR to existing content, drop the image capability.
    public func appendingRecognizedText(_ text: String) -> Self {
        let existing = content?() ?? ""
        let combined = existing.isEmpty ? text : existing + "\n" + text
        return Self(id: id, nativeIdentifier: nativeIdentifier, type: type, title: title,
                    app: app, modified: modified, device: device, pinboard: pinboard,
                    content: { combined }, imageData: nil, contentVersion: contentVersion)
    }

    public static func == (lhs: Self, rhs: Self) -> Bool {
        lhs.id == rhs.id && lhs.nativeIdentifier == rhs.nativeIdentifier && lhs.type == rhs.type
            && lhs.title == rhs.title && lhs.app == rhs.app && lhs.modified == rhs.modified
            && lhs.device == rhs.device && lhs.pinboard == rhs.pinboard && lhs.contentVersion == rhs.contentVersion
    }

    static func make(id: UUID, originalTitle: String?, nativeIdentifier: String?, kind: OriginalPasteboardContentKind,
                     modified: Date?, app: String?, device: String?, pinboard: String?, contentVersion: Date,
                     content: (() -> String?)?, imageData: (() -> Data?)?) -> Self {
        let name: String
        switch kind {
        case .unknown: name = "Unknown"
        case .image: name = "Image"
        case .color: name = "Color"
        case .files: name = "File"
        case .link: name = "Link"
        case .text: name = "Text"
        }
        return Self(id: id, nativeIdentifier: nativeIdentifier, type: name,
                    title: originalTitle ?? name, app: app, modified: modified, device: device,
                    pinboard: pinboard, content: content, imageData: imageData, contentVersion: contentVersion)
    }

    // UI request equality and the explicit store-less adapter do not perform native fetches.
    // Actual SDK writes with a live store always use searchIndexRecords instead.
    public static func snapshot(_ value: ClipboardItem, app: String?) -> Self {
        let kind: OriginalPasteboardContentKind
        switch value.kind {
        case .unknown: kind = .unknown
        case .image: kind = .image
        case .color: kind = .color
        case .files: kind = .files
        case .link: kind = .link
        case .text, .richText: kind = .text
        }
        return make(id: value.id, originalTitle: value.originalTitle, nativeIdentifier: value.nativeIdentifier, kind: kind,
                    modified: value.isInHistory ? value.createdAt : nil, app: app, device: value.sourceDevice,
                    pinboard: value.pinboardOwnerID?.uuidString, contentVersion: value.updatedAt,
                    content: kind == .image ? nil : {
                        let items = (try? ClipboardStore.originalPasteboardItems(from: value.payloads)) ?? []
                        return ClipboardSearchRecordContent.text(items, kind: kind, preview: value.rawPreview) { value.plainText }
                    }, imageData: kind == .image ? { value.imageData } : nil)
    }
}

enum ClipboardSearchRecordContent {
    // 3724f0: native empty content consults typed metadata, never the compatibility value archive.
    static func nativeText(_ items: [OriginalPasteboardItem], kind: OriginalPasteboardContentKind,
                           preview: Data?, diagnoseEmpty: ((Int, String?) -> Void)? = nil) -> String? {
        // Reuse primary extraction; this closure supplies no archived fallback.
        guard let value = text(items, kind: kind, preview: preview, legacyPreviewFallback: { "" }) else { return nil }
        guard value.isEmpty else { return value }
        guard kind != .unknown else { return nil }
        let fallback: String?
        let previewLength: Int
        if let metadata = OriginalImagePreviewMetadataCodec.decodeText(preview) {
            // The stored sample may be truncated. Recover the full first rich/plain representation.
            guard metadata.length != 0 else { return nil }
            previewLength = metadata.length
            fallback = items.first?.f_10037d33c()?.string
        } else if let metadata = OriginalImagePreviewMetadataCodec.decodeLink(preview) {
            guard !metadata.url.absoluteString.isEmpty else { return nil }
            previewLength = metadata.url.absoluteString.count
            var values = [metadata.url.absoluteString]
            if let name = metadata.name { values.append(name) }
            fallback = values.joined(separator: " ")
        } else if OriginalImagePreviewMetadataCodec.decode(preview) != nil
                    || OriginalImagePreviewMetadataCodec.decodeColor(preview) != nil {
            previewLength = -1
            fallback = nil
        } else if let metadata = OriginalImagePreviewMetadataCodec.decodeFiles(preview) {
            let joinedPaths = metadata.paths.joined()
            guard !joinedPaths.isEmpty else { return nil }
            previewLength = joinedPaths.count
            fallback = metadata.paths.joined(separator: " ")
        } else { return nil }
        diagnoseEmpty?(previewLength, fallback)
        guard let fallback, !fallback.isEmpty else { return value }
        return fallback
    }

    // 0x1003724f0: normal unknown/text content uses all nonnil strings, in input order.
    static func text(_ items: [OriginalPasteboardItem], kind: OriginalPasteboardContentKind, preview: Data?,
                     legacyPreviewFallback: () -> String?) -> String? {
        switch kind {
        case .unknown, .text:
            let value = items.compactMap { $0.f_10037c9a8() }.joined(separator: " ")
            if !value.isEmpty || kind == .unknown { return value }
            // The complete original typed-preview fallback remains a separate migration boundary.
            return legacyPreviewFallback() ?? value
        case .image: return nil
        case .color: return items.first?.f_10037c9a8()
        case .files:
            let value = items.compactMap { $0.f_10037cc6c()?.path }.joined(separator: " ")
            return value.isEmpty ? legacyPreviewFallback() : value
        case .link:
            let url = items.first?.f_10037ce0c()
            var values = url.map { [$0.absoluteString] } ?? []
            if let name = OriginalImagePreviewMetadataCodec.decodeLink(preview)?.name { values.append(name) }
            let value = values.joined(separator: " ")
            return value.isEmpty ? legacyPreviewFallback() : value
        }
    }
}

/// 0x1003753f8/375458: retain coordinator + object ID, never a materialized item/context.
final class ClipboardSearchRecordReader {
    private let coordinator: NSPersistentStoreCoordinator
    private let objectID: NSManagedObjectID
    private let kind: OriginalPasteboardContentKind
    private let contentDiagnostics = OriginalNamedDiagnostic.f_1000d4624(name: "init(_:coordinator:)")
    private let logger = Logger(subsystem: "com.yingyanzhitong.paste-replica", category: "search-content")

    init(coordinator: NSPersistentStoreCoordinator, objectID: NSManagedObjectID, kind: OriginalPasteboardContentKind) {
        self.coordinator = coordinator; self.objectID = objectID; self.kind = kind
    }

    // 0x100372440/371f2c: a new private context is created on each evaluation.
    private func read<T>(contentDiagnostics: OriginalNamedDiagnostic? = nil,
                         imageDiagnostics: OriginalNamedDiagnostic? = nil,
                         _ project: (NSManagedObject, [OriginalPasteboardItem]) throws -> T?) -> T? {
        let context = NSManagedObjectContext(concurrencyType: .privateQueueConcurrencyType)
        context.persistentStoreCoordinator = coordinator
        do {
            return try context.performAndWait {
                try OriginalObjCExceptionBridge.withResult {
                    let object: NSManagedObject
                    do { object = try context.existingObject(with: objectID) }
                    catch {
                        guard let contentDiagnostics else {
                            if let imageDiagnostics {
                                imageDiagnostics.f_1000d468c().f_1000d4df0("Failed to load image content: \(error.localizedDescription)")
                                return nil
                            }
                            throw error
                        }
                        contentDiagnostics.f_1000d468c().f_1000d4df0("Failed to load item content: \(error.localizedDescription)")
                        return nil
                    }
                    guard object.entity.name == "Item" else {
                        contentDiagnostics?.f_1000d468c().f_1000d4df0("Failed to load item for content indexing: object not found")
                        return nil
                    }
                    guard !object.isDeleted,
                          let data = object.value(forKey: "data") as? NSManagedObject else { return nil }
                    guard let items = ClipboardItemDataPersistence.readRepresentations(from: data, diagnostics: {
                        if let data = data as? PastoItemDataEntity { return data.diagnostics }
                        // Older source models can still produce plain managed objects.
                        return OriginalNamedDiagnostic.f_1000d4624(name: "ItemDataEntity")
                    }) else { return nil }
                    return try project(object, items)
                }
            }
        } catch {
            logger.error("Search content read failed: \(error.localizedDescription, privacy: .public)")
            return nil
        }
    }

    func content() -> String? {
        read(contentDiagnostics: contentDiagnostics) { object, items in
            if items.isEmpty { diagnoseEmptyRepresentations(for: object) }
            return ClipboardSearchRecordContent.nativeText(items, kind: kind,
                preview: object.value(forKey: "rawPreview") as? Data, diagnoseEmpty: { previewLength, fallback in
                    self.diagnoseEmptyContent(for: object, items: items, previewLength: previewLength, fallback: fallback)
                })
        }
    }

    // 3724f0: this second raw read is diagnostic-only; failure must not stop typed fallback.
    private func diagnoseEmptyRepresentations(for object: NSManagedObject) {
        guard let data = object.value(forKey: "data") as? NSManagedObject else { return }
        let raw = (try? OriginalObjCExceptionBridge.f_1002ffc68 {
            guard let raw = data.value(forKey: "rawPasteboardItems") as? Data else {
                throw CocoaError(.fileReadCorruptFile)
            }
            return raw
        }) ?? Data()
        let prefix = raw.prefix(6).map { String(format: "%02x", $0) }.joined()
        contentDiagnostics.f_1000d468c().f_1000d4df0(
            "Item has no pasteboard data for content indexing (type: \(kind), rawSize: \(raw.count), rawPrefix: \(prefix))")
    }

    // 374e84: sample five items and ten ordered types per item, including repeated/missing types.
    private func diagnoseEmptyContent(for object: NSManagedObject, items: [OriginalPasteboardItem],
                                      previewLength: Int, fallback: String?) {
        guard let identifier = (object.value(forKey: "nativeIdentifier") as? String)
                    ?? (object.value(forKey: "key") as? String),
              let created = object.value(forKey: "createdAt") as? Date else { return }
        let application = object.value(forKey: "sourceApplication") as? NSManagedObject
        let app = application?.value(forKey: "name") as? String ?? "nil"
        let types = items.prefix(5).enumerated().map { index, item in
            let values = item.f_10037da6c().prefix(10).map { type in
                "\(type):\(item.f_10037d810(forType: type)?.count ?? 0)"
            }.joined(separator: ", ")
            return "item[\(index)]={\(values)}"
        }.joined(separator: "; ")
        let usedPreviewFallback = fallback.map { !$0.isEmpty } ?? false
        let synced = hasObjectMetadata(for: object)
        contentDiagnostics.f_1000d468c().f_1000d4df0(
            "Item content resolved to empty string (id: \(identifier), type: \(kind), app: \(app), synced: \(synced), created: \(created), previewLength: \(previewLength), usedPreviewFallback: \(usedPreviewFallback), types: \(types))")
    }

    // 38efa8 → 328980 is a local fetch. An offline model without this entity has no such records.
    private func hasObjectMetadata(for object: NSManagedObject) -> Bool {
        guard let context = object.managedObjectContext,
              let entity = context.persistentStoreCoordinator?.managedObjectModel.entitiesByName["ObjectMetadata"] else {
            return false
        }
        let request = NSFetchRequest<NSManagedObject>()
        request.entity = entity
        request.predicate = NSPredicate(format: "objectURI == %@", object.objectID.uriRepresentation().absoluteString)
        request.fetchLimit = 1
        request.fetchOffset = 0
        return (try? context.fetch(request).first) != nil
    }

    func imageData() -> Data? {
        read(imageDiagnostics: contentDiagnostics) { _, items in items.compactMap { $0.f_10037d5c4() }.first }
    }
}
