import Foundation
import PastoCore

/// Adapts the replica's JSON relationships to the recovered name-based provider interface.
@MainActor
enum ReplicaSearchSuggestionSource {
    private static func matches(_ value: String, query: String) -> Bool {
        guard !query.isEmpty else { return true }
        return NSPredicate(format: "SELF MATCHES[cd] %@", OriginalSearchSuggestions.f_1002f5100(query))
            .evaluate(with: value)
    }

    static func applications(_ query: String, store: ClipboardStore) -> [String] {
        Set(store.items.map(\.sourceName)).filter { !$0.isEmpty && matches($0, query: query) }
            .sorted { $0.compare($1) == .orderedAscending }
    }

    static func devices(_ query: String, store: ClipboardStore) -> [String] {
        Set(store.items.map(\.sourceDevice)).filter { !$0.isEmpty && matches($0, query: query) }
            .sorted { $0.compare($1) == .orderedAscending }
    }

    static func pinboards(_ query: String, store: ClipboardStore) -> [(identifier: String, name: String)] {
        store.pinboards.filter { matches($0.name, query: query) }
            .sorted { $0.name.compare($1.name) == .orderedAscending }.map { (identifier: $0.id.uuidString, name: $0.name) }
    }
}
