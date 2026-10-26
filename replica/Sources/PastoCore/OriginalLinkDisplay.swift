import Foundation

/// The local URL label value recovered from f_1003189b0.
public enum OriginalLinkDisplay {
    public static func formattedURL(_ url: URL) -> String {
        var result = (url.host ?? "").replacingOccurrences(of: "www.", with: "") + url.path
        if let scheme = url.scheme, !scheme.starts(with: "http") {
            result = scheme + "://" + result
        }
        if let query = url.query, !result.starts(with: "pasteapp.io") {
            result += "?" + query
        }
        return result.trimmingCharacters(in: CharacterSet(charactersIn: "/"))
    }
}
