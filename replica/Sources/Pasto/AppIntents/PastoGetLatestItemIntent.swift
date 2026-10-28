import AppIntents
import Foundation
import PastoCore

enum PastoLatestItemType: String, AppEnum {
    case text
    case link

    static var typeDisplayRepresentation: TypeDisplayRepresentation = "Pasto Item Type"
    static var caseDisplayRepresentations: [Self: DisplayRepresentation] = [
        .text: "Text",
        .link: "Link"
    ]
}

struct PastoGetLatestItemIntent: AppIntent {
    static var title: LocalizedStringResource = "Get Latest Pasto Item"

    @Parameter(title: "Type", description: "Text or Link")
    var type: PastoLatestItemType

    @Parameter(title: "Pasto")
    var pinboard: PastoPinboardEntity

    @MainActor
    func perform() async throws -> some IntentResult & ReturnsValue<String?> {
        let store = try PastoAppIntentStore.refreshedStore()
        guard let items = pinboard.items(in: store) else {
            throw PastoLatestItemError.pinboardNotFound
        }
        // The recovered body accepts raw types 4/5; dependence on its Type parameter is unproven.
        // Keep the real local collection order, including the existing History order.
        let item = items.first {
            $0.kind == .link || $0.kind == .text || $0.kind == .richText
        }
        let text: String?
        if let item {
            let representations = (try? ClipboardStore.originalPasteboardItems(from: item.payloads)) ?? []
            text = OriginalPasteboardRestore.f_10031bcdc(representations).first?.f_10037c9a8()
        } else {
            text = nil
        }
        return .result(value: text)
    }
}

private enum PastoLatestItemError: LocalizedError {
    case pinboardNotFound

    var errorDescription: String? { "Pasto 分组不存在。" }
}
