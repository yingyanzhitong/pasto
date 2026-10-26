import Foundation

enum ReplicaBrand {
    /// Only apply to recovered UI copy that explicitly names the original app.
    /// User content, app names from other processes, and paste commands are not brand copy.
    static func replacingOriginalName(in text: String) -> String {
        text.replacingOccurrences(of: "Paste Replica", with: "Pasto")
            .replacingOccurrences(of: "Paste", with: "Pasto")
    }
}
