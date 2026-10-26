import Foundation

public enum OriginalSearchQueryNormalization {
    public static func f_1002da16c(_ nodes: [OriginalSearchQueryNode], flag: UInt8) -> [OriginalSearchQueryNode] {
        var filters: [OriginalSearchQueryNode] = []
        var seen: [UInt8: Set<String>] = [:]
        for node in nodes {
            guard case let .filter(tag, value) = node,
                  !value.trimmingCharacters(in: .whitespaces).isEmpty else { continue }
            if seen[tag, default: []].insert(value).inserted { filters.append(node) }
        }

        // The split uses the original input, including discarded filters.
        let lastFilter = nodes.lastIndex { node in
            if case .filter = node { return true }
            return false
        }
        var before: [OriginalSearchQueryNode] = []
        var after: [OriginalSearchQueryNode] = []
        for (index, node) in nodes.enumerated() {
            guard case let .text(value) = node else { continue }
            if flag & 1 != 0, value.trimmingCharacters(in: .whitespaces).isEmpty { continue }
            if let lastFilter, index > lastFilter { after.append(node) }
            else { before.append(node) }
        }
        // Original appends the post-filter text first, then the preceding text.
        filters.append(contentsOf: after)
        filters.append(contentsOf: before)
        return filters
    }
}
