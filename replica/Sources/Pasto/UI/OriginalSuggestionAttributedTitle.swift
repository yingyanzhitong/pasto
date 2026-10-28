import AppKit
import PastoCore

@MainActor
enum OriginalSuggestionAttributedTitle {
    /// Paste 0x100010984: only matching titles are assembled as mutable segments.
    static func f_100010984(primary: NSColor, secondary: NSColor,
                            title: String, query: String?) -> NSAttributedString {
        if let query, !query.isEmpty {
            let matches = OriginalSearchSuggestions.f_1002f5748(query, in: title)
            if !matches.isEmpty {
                let result = NSMutableAttributedString(string: "")
                var cursor = title.startIndex
                for match in matches {
                    if cursor < match.lowerBound {
                        result.append(NSAttributedString(string: String(title[cursor..<match.lowerBound]),
                            attributes: [.foregroundColor: secondary]))
                    }
                    result.append(NSAttributedString(string: String(title[match]),
                        attributes: [.foregroundColor: primary]))
                    cursor = match.upperBound
                }
                if cursor < title.endIndex {
                    result.append(NSAttributedString(string: String(title[cursor...]),
                        attributes: [.foregroundColor: secondary]))
                }
                return result
            }
        }
        return NSAttributedString(string: title, attributes: [.foregroundColor: primary])
    }
}
