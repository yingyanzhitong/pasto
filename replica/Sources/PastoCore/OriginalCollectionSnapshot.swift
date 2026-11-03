import Foundation

/// Snapshot-change threshold used by the original collection applier.
public enum OriginalCollectionSnapshot {
    public static let fullReloadThreshold = 300

    /// Counts removals, insertions, and inferred moves once each; equal IDs with
    /// changed payloads do not inflate the structural-change threshold.
    public static func structuralChangeCount(from previousIDs: [UUID], to currentIDs: [UUID]) -> Int {
        guard previousIDs != currentIDs else { return 0 }
        let difference = currentIDs.difference(from: previousIDs).inferringMoves()
        var removals = 0
        var insertions = 0
        var moves = 0
        for change in difference {
            switch change {
            case let .remove(_, _, associatedWith):
                if associatedWith == nil { removals += 1 }
                else { moves += 1 }
            case let .insert(_, _, associatedWith):
                if associatedWith == nil { insertions += 1 }
            }
        }
        return removals + insertions + moves
    }

    public static func requiresFullReload(from previousIDs: [UUID], to currentIDs: [UUID]) -> Bool {
        structuralChangeCount(from: previousIDs, to: currentIDs) > fullReloadThreshold
    }
}
