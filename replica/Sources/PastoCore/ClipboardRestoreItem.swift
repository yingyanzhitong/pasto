import AppKit
import Combine
import CoreData
import Foundation

/// Retains the selected entity for restoration and editing; consumers read its current content.
@MainActor
public struct ClipboardRestoreItem {
    public let id: UUID
    let nativeObject: PastoItemEntity?
    private let resolve: () -> ClipboardItem
    private let makeObservation: () -> ClipboardItemObservation?

    init(id: UUID, object: PastoItemEntity) {
        self.id = id
        nativeObject = object
        resolve = {
            guard let item = try? ClipboardPersistence.item(object) else { fatalError("Missing restore item content") }
            return item
        }
        makeObservation = { ClipboardItemObservation(object: object) }
    }

    public init(item: ClipboardItem) {
        id = item.id
        nativeObject = nil
        resolve = { item }
        makeObservation = { nil }
    }

    public func hasSameEntity(as other: ClipboardRestoreItem) -> Bool {
        if let nativeObject { return nativeObject === other.nativeObject }
        return other.nativeObject == nil && id == other.id
    }

    // 3541f4 → URIRepresentation: window lookup/registration use the managed object's URL identity.
    public var previewIdentity: AnyHashable {
        if let nativeObject { return AnyHashable(nativeObject.objectID.uriRepresentation()) }
        return AnyHashable(id)
    }

    // Registration/publication callbacks read the current native identifier, independent of URI identity.
    public var previewIdentifier: String {
        if let nativeObject, let identifier = nativeObject.value(forKey: "nativeIdentifier") as? String {
            return identifier
        }
        return id.uuidString
    }

    public var isDeleted: Bool { nativeObject?.isDeleted ?? false }
    public var hasNativeEntity: Bool { nativeObject != nil }

    public func makeDragIdentifierSource() -> any OriginalDragItemIdentifierSource {
        ClipboardDragIdentifierSource(object: nativeObject, fallback: id.uuidString)
    }

    // 3c2780 publishes entity changes including deletion; the preview consumer decides how to react.
    public func observeChanges(_ consume: @escaping (ClipboardRestoreItem) -> Void) -> AnyCancellable? {
        guard let object = nativeObject else { return nil }
        guard let context = object.managedObjectContext else {
            preconditionFailure("Item observation requires a managed context")
        }
        let objectID = object.objectID
        let id = self.id
        return NotificationCenter.default
            .publisher(for: .NSManagedObjectContextObjectsDidChange, object: context)
            .sink { [object, context] notification in
                MainActor.assumeIsolated {
                    withExtendedLifetime((object, context)) {
                        for key in [NSInsertedObjectsKey, NSUpdatedObjectsKey, NSDeletedObjectsKey, NSRefreshedObjectsKey] {
                            let objects = notification.userInfo?[key] as? Set<NSManagedObject> ?? []
                            guard let current = objects.first(where: { $0.objectID == objectID }) else { continue }
                            let item = current as! PastoItemEntity
                            consume(ClipboardRestoreItem(id: id, object: item))
                            return
                        }
                    }
                }
            }
    }

    // 31eba8/31c2ec inspect native type before content creation or editing eligibility.
    public func previewRawType() -> Int? {
        guard let object = nativeObject else { return nil }
        let rawType = (object.value(forKey: "rawType") as? NSNumber)?.intValue ?? 0
        return (0...5).contains(rawType) ? rawType : 0
    }

    // 309008/308f88 read title/type/preview, independently of archived value content.
    public func previewTitle() -> (defaultTitle: String, title: String)? {
        guard let object = nativeObject else { return nil }
        let rawType = (object.value(forKey: "rawType") as? NSNumber)?.intValue ?? 0
        let count = rawType == 3
            ? OriginalImagePreviewMetadataCodec.decodeFiles(object.value(forKey: "rawPreview") as? Data)?.paths.count : nil
        let defaultTitle = OriginalPreviewTitles.f_100309008(rawType: rawType, fileCount: count)
        return (defaultTitle, OriginalPreviewTitles.f_100308f88(object.value(forKey: "title") as? String,
                                                             defaultTitle: defaultTitle))
    }

    // 31bc94/3250f0 filter the native owner by rawType before reading its attributes.
    public func previewPinboard() -> (isPinned: Bool, colorCode: UInt64?)? {
        guard let object = nativeObject else { return nil }
        guard let list = object.value(forKey: "list") as? NSManagedObject,
              (list.value(forKey: "rawType") as? NSNumber)?.int64Value == 2 else { return (false, nil) }
        return (true, OriginalPinboardAttributes.colorCode(from: list.value(forKey: "rawAttributes") as? Data))
    }

    // 31bc94/09e8a8: the checkmark uses the current native type2 owner, not legacy memberships.
    public func isAssigned(to target: ClipboardPinboardTarget) -> Bool? {
        guard let object = nativeObject else { return nil }
        guard let owner = object.value(forKey: "list") as? NSManagedObject,
              (owner.value(forKey: "rawType") as? NSNumber)?.int64Value == 2 else { return false }
        return owner.isEqual(target.nativeObject)
    }

    // 3ba390/3250f0: removal eligibility needs only the current native owner type.
    public func hasNativePinboardOwner() -> Bool? {
        guard let object = nativeObject else { return nil }
        guard let owner = object.value(forKey: "list") as? NSManagedObject else { return false }
        return (owner.value(forKey: "rawType") as? NSNumber)?.int64Value == 2
    }

    // 3b83c4 reads current timestamp and type2 owner without decoding the content archive.
    public func listNavigationMembership() -> (isInHistory: Bool, pinboardID: UUID?)? {
        guard let object = nativeObject else { return nil }
        let isInHistory = object.value(forKey: "timestamp") != nil
        guard let owner = object.value(forKey: "list") as? NSManagedObject,
              (owner.value(forKey: "rawType") as? NSNumber)?.int64Value == 2 else {
            return (isInHistory, nil)
        }
        let identifier = owner.value(forKey: "identifier") as? String
        return (isInHistory, identifier.flatMap { UUID(uuidString: $0) })
    }

    // 31ebc8: Stack cells read the current entity preview on row demand.
    public func previewMetadataData() -> Data? {
        nativeObject?.value(forKey: "rawPreview") as? Data
    }

    public func previewSharingContent() -> OriginalPreviewSharing.Content? {
        guard let object = nativeObject else { return nil }
        let rawType = (object.value(forKey: "rawType") as? NSNumber)?.intValue ?? 0
        return .init(items: ClipboardItemDataPersistence.readItems(from: object) ?? [], rawType: rawType)
    }

    // 3bbc20 reads the current native preview; absent/noncolor metadata displays black.
    public func previewColor() -> NSColor? {
        guard let object = nativeObject else { return nil }
        guard let metadata = OriginalImagePreviewMetadataCodec.decodeColor(object.value(forKey: "rawPreview") as? Data) else {
            return .black
        }
        return OriginalColorPreviewMetadataGenerator.color(metadata.code)
    }

    // 3bf65c requires canonical link metadata; an invalid native value must not use a stale DTO URL.
    public func previewLinkURL() -> URL? {
        guard let object = nativeObject else { return nil }
        guard let metadata = OriginalImagePreviewMetadataCodec.decodeLink(object.value(forKey: "rawPreview") as? Data) else {
            preconditionFailure("Link preview requires canonical link metadata")
        }
        return metadata.url
    }

    // 3bd9cc: first decodable image in native representation order; no value DTO or metadata dependency.
    public func previewImage() -> NSImage? {
        guard let object = nativeObject,
              let items = ClipboardItemDataPersistence.readItems(from: object) else { return nil }
        for item in items {
            guard let data = item.f_10037d5c4(), NSImage(data: data) != nil else { continue }
            return item.f_10037d5c4().flatMap(NSImage.init(data:))
        }
        return nil
    }

    // 3bd740/3bd784: missing or nonimage metadata supplies zero size.
    public func previewImageSize() -> NSSize? {
        guard let object = nativeObject else { return nil }
        return OriginalImagePreviewMetadataCodec.decode(object.value(forKey: "rawPreview") as? Data)?.size ?? .zero
    }

    public func resolvedItem() -> ClipboardItem { resolve() }
    public func observeItem() -> ClipboardItemObservation? { makeObservation() }
}

private final class ClipboardDragIdentifierSource: OriginalDragItemIdentifierSource {
    private let object: PastoItemEntity?
    private let context: NSManagedObjectContext?
    private let fallback: String

    init(object: PastoItemEntity?, fallback: String) {
        self.object = object
        context = object?.managedObjectContext
        self.fallback = fallback
    }

    var pasteboardIdentifier: String {
        guard let object else { return fallback }
        let fallback = self.fallback
        let read = { (object.value(forKey: "nativeIdentifier") as? String) ?? fallback }
        if let context { return context.performAndWait(read) }
        return read()
    }
}
