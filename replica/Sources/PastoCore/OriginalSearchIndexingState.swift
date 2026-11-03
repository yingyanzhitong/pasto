import Foundation

/// 0x100cab74c: the source identity lives in a separate Config slot.
public struct OriginalSearchIndexingState: Codable, Equatable {
    public var schemaVersion: Int
    public var totalItems: Int
    public var indexedItems: Int
    public var oldestTimestamp: Date?
    public var invalidItems: Int

    public init(schemaVersion: Int, totalItems: Int, indexedItems: Int,
                oldestTimestamp: Date?, invalidItems: Int) {
        self.schemaVersion = schemaVersion; self.totalItems = totalItems; self.indexedItems = indexedItems
        self.oldestTimestamp = oldestTimestamp; self.invalidItems = invalidItems
    }

    public static var currentSchemaVersion: Int {
        ProcessInfo.processInfo.isOperatingSystemAtLeast(.init(majorVersion: 26, minorVersion: 4, patchVersion: 0)) ? 6 : 5
    }
}

@MainActor
public final class OriginalSearchIndexStateStore {
    private let defaults: UserDefaults

    public init(defaults: UserDefaults = .standard) { self.defaults = defaults }

    public var savedState: OriginalSearchIndexingState? {
        guard let data = defaults.data(forKey: "indexingState") else { return nil }
        return try? JSONDecoder().decode(OriginalSearchIndexingState.self, from: data)
    }

    public func save(_ state: OriginalSearchIndexingState?) throws {
        defaults.set(try JSONEncoder().encode(state), forKey: "indexingState")
    }

    public var indexedStoreID: String? {
        get { defaults.string(forKey: "indexedStoreID") }
        set { defaults.set(newValue, forKey: "indexedStoreID") }
    }
}
