import Foundation

public enum OriginalSearchTextTokens {
    public static func f_1002f8760(_ buffer: inout String, into nodes: inout [OriginalSearchQueryNode]) {
        guard !buffer.isEmpty else { return }
        let text = buffer.replacingOccurrences(of: "\u{FFFC}", with: " ")
        var run = ""
        var previousWhitespace: Bool?
        for character in text {
            let whitespace = character.isWhitespace
            if let previousWhitespace, previousWhitespace != whitespace {
                nodes.append(.text(run))
                run = ""
            }
            run.append(character)
            previousWhitespace = whitespace
        }
        if !run.isEmpty { nodes.append(.text(run)) }
        buffer.removeAll(keepingCapacity: true)
    }
}
