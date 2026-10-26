import Foundation

public enum OriginalSearchSuggestions {
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
