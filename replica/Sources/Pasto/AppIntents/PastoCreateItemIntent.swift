import AppIntents
import Foundation
import PastoCore

struct PastoCreateItemIntent: AppIntent {
    static var title: LocalizedStringResource = "Create Pasto Item"

    @Parameter(title: "Content", description: "Text")
    var content: String

    @Parameter(title: "Pasto")
    var destination: PastoPinboardEntity

    @MainActor
    func perform() async throws -> some IntentResult & ReturnsValue<String?> {
        guard !content.isEmpty else { throw OriginalPasteboardItemCreationError.emptyContent }
        let target: ClipboardStore.IntentTextDestination
        if destination.id == PastoPinboardEntity.historyID {
            target = .history
        } else if let id = UUID(uuidString: destination.id) {
            target = .pinboard(id)
        } else {
            throw PastoCreateItemError.destinationNotFound
        }
        let store = try PastoAppIntentStore.requireStore()
        let item = try store.createIntentText(content, destination: target)
        let representations = (try? ClipboardStore.originalPasteboardItems(from: item.payloads)) ?? []
        return .result(value: representations.first?.f_10037c9a8())
    }
}

private enum PastoCreateItemError: LocalizedError {
    case destinationNotFound

    var errorDescription: String? { "Pasto 分组不存在。" }
}
