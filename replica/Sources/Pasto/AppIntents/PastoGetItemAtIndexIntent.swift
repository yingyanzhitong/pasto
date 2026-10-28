import AppIntents
import Foundation
import PastoCore

/// Reads the first original representation; it does not restore the clipboard or synthesize OCR text.
struct PastoGetItemAtIndexIntent: AppIntent {
    static var title: LocalizedStringResource = "Get Pasto Item at Index"

    @Parameter(title: "Index", description: "Item Index", controlStyle: .stepper)
    var index: Int

    @Parameter(title: "Pasto")
    var pinboard: PastoPinboardEntity

    @MainActor
    func perform() async throws -> some IntentResult & ReturnsValue<String?> {
        let store = try PastoAppIntentStore.refreshedStore()
        guard let items = pinboard.items(in: store) else {
            throw PastoIndexedItemError.pinboardNotFound
        }
        // Use the actual local collection order, without claiming the original repository order.
        guard items.indices.contains(index) else { throw PastoIndexedItemError.itemNotFound }
        let representations = (try? ClipboardStore.originalPasteboardItems(from: items[index].payloads)) ?? []
        return .result(value: representations.first?.f_10037c9a8())
    }
}

private enum PastoIndexedItemError: LocalizedError {
    case pinboardNotFound
    case itemNotFound

    var errorDescription: String? {
        switch self {
        case .pinboardNotFound: return "Pasto 分组不存在。"
        case .itemNotFound: return "Pasto 项目不存在。"
        }
    }
}
