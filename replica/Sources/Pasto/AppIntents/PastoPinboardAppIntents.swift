import AppIntents
import AppKit
import Foundation
import PastoCore
import _AppIntents_AppKit

/// The app supplies its live store so intent actions use the same directory and transaction path.
@MainActor
enum PastoAppIntentStore {
    private static weak var store: ClipboardStore?

    static func configure(store: ClipboardStore) {
        self.store = store
    }

    static func requireStore() throws -> ClipboardStore {
        guard let store else { throw PastoAppIntentAccessError.storeUnavailable }
        return store
    }

    static func refreshedStore() throws -> ClipboardStore {
        let store = try requireStore()
        try store.reload()
        return store
    }
}

private enum PastoAppIntentAccessError: LocalizedError {
    case storeUnavailable

    var errorDescription: String? { "Pasto 本地资料尚未就绪。" }
}

struct PastoPinboardEntity: AppEntity {
    static var typeDisplayRepresentation: TypeDisplayRepresentation = "Pasto"
    static var defaultQuery = PastoPinboardQuery()
    static let historyID = "sharedPasteboardHistory"

    static func history(name: String) -> Self {
        Self(id: historyID, name: name, symbolName: "clock.arrow.circlepath")
    }

    let id: String
    let name: String
    private let symbolName: String
    private let tintColor: NSColor?

    @MainActor
    init(_ pinboard: Pinboard) {
        id = pinboard.id.uuidString
        name = pinboard.name
        // The local model has no shared-list entity; the original shared symbol remains separate.
        symbolName = pinboard.rawType == 1 ? "clock.arrow.circlepath" : "circle.fill"
        // f_1000cef84 projects only the decoded pinboard attributes into the
        // original palette; absent/other attributes retain an uncolored image.
        tintColor = OriginalPinboardAttributes.colorCode(from: pinboard.rawAttributes).map {
            OriginalPinboardColor(canonicalColorCode: $0).color()
        }
    }

    private init(id: String, name: String, symbolName: String) {
        self.id = id
        self.name = name
        self.symbolName = symbolName
        tintColor = nil
    }

    @MainActor
    func items(in store: ClipboardStore) -> [ClipboardItem]? {
        if id == Self.historyID { return store.search(query: "") }
        guard let pinboard = store.pinboards.first(where: { $0.id.uuidString == id }) else { return nil }
        return store.items(in: pinboard.id)
    }

    var displayRepresentation: DisplayRepresentation {
        // Paste f_1000ce644/f_1000ce5bc use the AppKit image initializer and body symbol style.
        // Preserve its optional result, without substituting another image if construction fails.
        DisplayRepresentation(title: "\(name)", image: .init(systemName: symbolName,
            tintColor: tintColor, symbolConfiguration: NSImage.SymbolConfiguration(textStyle: .body)))
    }
}

struct PastoPinboardQuery: EntityQuery {
    @MainActor
    func entities(for identifiers: [String]) async throws -> [PastoPinboardEntity] {
        let store = try PastoAppIntentStore.refreshedStore()
        let pinboards = store.pinboards
        return identifiers.compactMap { identifier in
            if identifier == PastoPinboardEntity.historyID {
                return .history(name: store.preferences.historyTitle)
            }
            return pinboards.first(where: { $0.id.uuidString == identifier }).map(PastoPinboardEntity.init)
        }
    }

    @MainActor
    func suggestedEntities() async throws -> [PastoPinboardEntity] {
        let store = try PastoAppIntentStore.refreshedStore()
        let pinboards = store.pinboards
        // This local presentation puts History first; the original metadata.index ordering is unresolved.
        return [.history(name: store.preferences.historyTitle)] + pinboards.map(PastoPinboardEntity.init)
    }
}

struct PastoCreatePinboardIntent: AppIntent {
    static var title: LocalizedStringResource = "Create Pasto"

    @Parameter(title: "Name", description: "Text")
    var name: String

    @MainActor
    func perform() async throws -> some IntentResult & ReturnsValue<PastoPinboardEntity> {
        let store = try PastoAppIntentStore.requireStore()
        let pinboard = try store.createPinboardFromIntent(name: name)
        return .result(value: PastoPinboardEntity(pinboard))
    }
}
