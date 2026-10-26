import Foundation

public enum OriginalSearchQueryNode: Equatable, Sendable {
    case text(String)
    case filter(UInt8, String)
}

public enum OriginalSearchQuery {
    public static func f_1002ddcf0(_ nodes: [OriginalSearchQueryNode]) -> Bool {
        nodes.allSatisfy { node in
            let value: String
            switch node {
            case let .text(text): value = text
            case let .filter(_, filter): value = filter
            }
            return value.trimmingCharacters(in: .whitespaces).isEmpty
        }
    }

    private static func escaped(_ value: String) -> String {
        value.replacingOccurrences(of: "\\", with: "\\\\")
            .replacingOccurrences(of: "\"", with: "\\\"")
            .replacingOccurrences(of: "*", with: "\\*")
            .replacingOccurrences(of: "?", with: "\\?")
    }

    public static func f_1002f3d94(tag: UInt8, value: String) -> String? {
        let value = value.trimmingCharacters(in: .whitespaces)
        guard !value.isEmpty else { return nil }
        if tag == 3 {
            let parts = value.split(separator: " ")
            guard parts.count == 2, let start = Double(parts[0]), let end = Double(parts[1]) else { return nil }
            let formatter = ISO8601DateFormatter()
            return "(contentModificationDate >= $time.iso(\(formatter.string(from: Date(timeIntervalSince1970: start)))) && contentModificationDate < $time.iso(\(formatter.string(from: Date(timeIntervalSince1970: end)))))"
        }
        let field: String
        switch tag {
        case 0: field = "pasteApp"
        case 1: field = "pasteType"
        case 2: field = "title"
        case 4: field = "pasteDevice"
        default: field = "pastePinboard"
        }
        let escapedValue = escaped(value)
        return tag == 2 || tag == 4 ? "\(field) == \"*\(escapedValue)*\"cd" : "\(field) == \"\(escapedValue)\"cd"
    }

    public static func f_1002f45b0(_ nodes: [OriginalSearchQueryNode]) -> String {
        var predicates: [String] = []
        let text = nodes.compactMap { node -> String? in
            guard case let .text(rawValue) = node else { return nil }
            let value = rawValue.trimmingCharacters(in: .whitespaces)
            return value.isEmpty ? nil : value
        }
        if !text.isEmpty {
            let value = escaped(text.joined(separator: " "))
            var fields = ["title", "textContent"]
            if ProcessInfo.processInfo.isOperatingSystemAtLeast(.init(majorVersion: 26, minorVersion: 4, patchVersion: 0)) {
                fields.append("contentDescription")
            }
            predicates.append("(" + fields.map { "\($0) = \"\(value)*\"cwdt" }.joined(separator: " || ") + ")")
        }
        var groups: [UInt8: [String]] = [:]
        for node in nodes {
            guard case let .filter(tag, value) = node, let predicate = f_1002f3d94(tag: tag, value: value) else { continue }
            groups[tag, default: []].append(predicate)
        }
        for group in groups.values {
            predicates.append(group.count == 1 ? group[0] : "(" + group.joined(separator: " || ") + ")")
        }
        return predicates.joined(separator: " && ")
    }
}
