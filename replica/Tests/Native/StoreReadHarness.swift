import Foundation
import PastoCore

/// Test-only observer: read through the same model and lock as the app, not SQLite's private blob format.
@main
struct StoreReadHarness {
    @MainActor static func main() throws {
        let store = try ClipboardStore(directoryURL: URL(fileURLWithPath: CommandLine.arguments[1]))
        FileHandle.standardOutput.write(try JSONEncoder().encode(store.items))
    }
}
