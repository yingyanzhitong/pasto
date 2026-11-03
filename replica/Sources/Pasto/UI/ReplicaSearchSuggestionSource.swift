import PastoCore

/// Adapts the local backing store to the recovered name-based provider interface.
@MainActor
enum ReplicaSearchSuggestionSource {
    /// Only records predating explicit relation tracking use the captured-name fallback.
    static func applicationNames(for items: [ClipboardItem], store: ClipboardStore) -> [String?] {
        let names = Dictionary(uniqueKeysWithValues: store.sourceApplications.map { ($0.bundleIdentifier, $0.name) })
        return items.map { item in
            if let identifier = item.sourceApplicationBundleID { return names[identifier] }
            if item.sourceApplicationRelationIsKnown == true { return nil }
            return item.sourceName.isEmpty ? nil : item.sourceName
        }
    }

    static func applications(_ query: String, store: ClipboardStore) throws -> [String] {
        try store.searchApplicationNames(matching: query)
    }

    static func devices(_ query: String, store: ClipboardStore) throws -> [String] {
        try store.searchDeviceNames(matching: query)
    }

    static func pinboards(_ query: String, store: ClipboardStore) throws -> [(identifier: String, name: String)] {
        try store.searchPinboardNames(matching: query)
    }
}
