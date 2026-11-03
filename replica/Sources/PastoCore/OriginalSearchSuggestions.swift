import Foundation

public enum OriginalSearchSuggestions {
    public enum Suggestion: Equatable, Sendable, CustomStringConvertible {
        case query([OriginalSearchQueryNode])
        case filter(UInt8, String)

        // 0x1002dcc94: the registered CustomStringConvertible witness.
        public var description: String { OriginalSearchSuggestions.f_1002dc9b8(self) }
    }

    /// Original 0x1002dcca4, before the caller normalizes the resulting query.
    public static func f_1002dcca4(_ suggestion: Suggestion, index: Int, addMode: UInt8,
                                  nodes: [OriginalSearchQueryNode]) -> [OriginalSearchQueryNode] {
        switch suggestion {
        case let .query(query):
            return query
        case let .filter(tag, value):
            let filter = OriginalSearchQueryNode.filter(tag, value)
            guard !nodes.contains(filter) else { return nodes }
            if addMode == 1 {
                // f_1002dcf24(1, nodes) is the generic dropLast operation.
                return Array(nodes.dropLast()) + [filter]
            }
            guard index < nodes.count else { return nodes }
            precondition(index >= 0)
            var result = nodes
            result[index] = filter
            return result
        }
    }

    private static var listNameResolver: ((String) -> String?)?

    public static func setListNameResolver(_ resolver: ((String) -> String?)?) {
        listNameResolver = resolver
    }

    public static func resolveListName(_ identifier: String) -> String? {
        let resolver = listNameResolver
        return resolver?(identifier)
    }

    // 2dc9b8: preserve node order, raw text and empty components when joining.
    public static func f_1002dc9b8(_ suggestion: Suggestion,
                                  listName: (String) -> String? = { resolveListName($0) }) -> String {
        switch suggestion {
        case let .filter(kind, value):
            return f_1002ddc10(kind: kind, value: value, listName: listName)
        case let .query(nodes):
            return nodes.map { node in
                switch node {
                case let .text(text): return text
                case let .filter(kind, value):
                    let prefix: String
                    switch kind {
                    case 0: prefix = "app"
                    case 1: prefix = "type"
                    case 2: prefix = "title"
                    case 3: prefix = "date"
                    case 4: prefix = "device"
                    default: prefix = "pinboard"
                    }
                    return prefix + ":" + f_1002ddc10(kind: kind, value: value, listName: listName)
                }
            }.joined(separator: " ")
        }
    }

    // 2ddc10: only dates and list identifiers have a resolved caption.
    public static func f_1002ddc10(kind: UInt8, value: String,
                                  listName: (String) -> String? = { resolveListName($0) }) -> String {
        switch kind {
        case 5: return listName(value) ?? value
        case 3: return OriginalSearchDateEncoding.f_1002d8e9c(value) ?? value
        default: return value
        }
    }

    public struct Provider {
        public let app: (String) throws -> [String]
        public let type: (String) throws -> [String]
        public let device: (String) throws -> [String]
        public let pinboard: (String) throws -> [(identifier: String, name: String)]

        public init(
            app: @escaping (String) throws -> [String],
            type: @escaping (String) throws -> [String] = OriginalSearchSuggestions.f_10030f3e0,
            device: @escaping (String) throws -> [String],
            pinboard: @escaping (String) throws -> [(identifier: String, name: String)]
        ) {
            self.app = app
            self.type = type
            self.device = device
            self.pinboard = pinboard
        }
    }

    // 0x1002e00a0: optional provider, independently suppressed source errors, dates always.
    public static func f_1002e00a0(provider: () -> Provider?,
                                  dateFilters: [OriginalSearchDateFilter]? = nil) -> [UInt8: [OriginalSearchQueryNode]] {
        var filters: [UInt8: [OriginalSearchQueryNode]] = [:]
        let types = try? (provider()?.type("") ?? [])
        filters[1] = types.map { $0.map { .filter(1, $0) } }
        let apps = try? (provider()?.app("") ?? [])
        filters[0] = apps.map { $0.map { .filter(0, $0) } }
        let devices = try? (provider()?.device("") ?? [])
        filters[4] = devices.map { $0.map { .filter(4, $0) } }
        filters[3] = (dateFilters ?? OriginalSearchDateRanges.f_1002d8ce0()).map { date in
            // The available-filters builder truncates both endpoints toward zero.
            let start = Int(date.range.lowerBound.timeIntervalSince1970)
            let end = Int(date.range.upperBound.timeIntervalSince1970)
            return .filter(3, "\(start) \(end)")
        }
        let pinboards = try? (provider()?.pinboard("") ?? [])
        filters[5] = pinboards.map { $0.map { .filter(5, $0.identifier) } }
        return filters
    }

    public static func f_10030f3e0(_ query: String) -> [String] {
        let values = ["Unknown", "Image", "Color", "File", "Link", "Text"]
        guard !query.isEmpty else { return values }
        let prefix = query.lowercased()
        return values.filter { $0.lowercased().hasPrefix(prefix) }
    }

    public static func f_1002f51d0(
        _ text: String,
        maxSplits: Int = Int.max,
        omittingEmptySubsequences: Bool = true
    ) -> [Substring] {
        text.split(
            maxSplits: maxSplits,
            omittingEmptySubsequences: omittingEmptySubsequences,
            whereSeparator: { $0.isWhitespace }
        )
    }

    public static func f_1002f5588(_ text: String) -> [String] {
        f_1002f51d0(text).map { "\\b" + NSRegularExpression.escapedPattern(for: String($0)) }
    }

    public static func f_1002f5100(_ text: String) -> String {
        ".*" + f_1002f5588(text).joined(separator: ".*") + ".*"
    }

    public static func f_1002f5748(_ query: String, in target: String) -> [Range<String.Index>] {
        var matches: [Range<String.Index>] = []
        var lowerBound = target.startIndex
        for pattern in f_1002f5588(query) {
            guard let match = target.range(
                of: pattern,
                options: [.caseInsensitive, .regularExpression],
                range: lowerBound..<target.endIndex,
                locale: nil
            ) else { return [] }
            matches.append(match)
            lowerBound = match.upperBound
        }
        return matches
    }

    public static func f_1002df190(
        contextNode: OriginalSearchQueryNode,
        currentNodes: [OriginalSearchQueryNode],
        provider: Provider,
        dateFilters: [OriginalSearchDateFilter]? = nil
    ) -> [OriginalSearchQueryNode] {
        guard case let .text(text) = contextNode,
              !text.trimmingCharacters(in: .whitespaces).isEmpty else { return [] }
        let query = text.trimmingCharacters(in: .whitespacesAndNewlines)
        let applied = currentNodes.filter {
            if case .filter = $0 { return true }
            return false
        }
        // Each source is independent: an error suppresses only that group's rows.
        let groups: [(UInt8, (String) throws -> [String])] = [
            (0, provider.app),
            (1, provider.type),
            (4, provider.device),
            (5, { try provider.pinboard($0).map { $0.identifier } })
        ]
        var suggestions: [OriginalSearchQueryNode] = []
        for (kind, source) in groups {
            do {
                let candidates = try source(query)
                suggestions.append(contentsOf: candidates
                    .map { OriginalSearchQueryNode.filter(kind, $0) }
                    .filter { !applied.contains($0) }
                    .prefix(30))
            } catch {
                continue
            }
        }
        for dateFilter in dateFilters ?? OriginalSearchDateRanges.f_1002d8ce0()
            where !f_1002f5748(query, in: dateFilter.title).isEmpty {
            let node = OriginalSearchDateEncoding.f_1002d9d2c(dateFilter.range)
            if !applied.contains(node) { suggestions.append(node) }
        }
        return suggestions
    }
}
