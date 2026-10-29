import AppKit
import Foundation
import PastoCore

@main
struct CopyRestoreHarness {
    struct Failure: Error { let message: String }
    @MainActor static func main() async throws {
        _ = NSApplication.shared
        guard let screen = NSScreen.main else { throw Failure(message: "No screen") }
        var fixtures: [[String: Any]] = []
        for (count, sync) in [(0, false), (54, false), (54, true)] {
            let directory = FileManager.default.temporaryDirectory.appendingPathComponent("PastoCopyRestore-\(UUID())")
            defer { try? FileManager.default.removeItem(at: directory) }
            let store = try ClipboardStore(directoryURL: directory)
            store.preferences.historyRetentionDays = 0
            let text = ClipboardItem(createdAt: Date(timeIntervalSince1970: 1_700_000_000), plainText: "synthetic copy fixture")
            store.items = [text] + (0..<count).map { i in
                ClipboardItem(title: "binary fixture \(i)", kind: .unknown,
                    payloads: ["local.pasto.synthetic": Data(repeating: UInt8(i), count: 1_048_576)])
            }
            try store.save()
            let archive = directory.appendingPathComponent("fixture-archive.json")
            try store.exportArchive(to: archive)
            let archiveBytes = try FileManager.default.attributesOfItem(atPath: archive.path)[.size] as! NSNumber
            if sync { _ = try store.prepareCloudKit() }
            let ui = ReplicaUIController(store: store)
            let board = NSPasteboard(name: .init("PastoCopyRestore-\(UUID())"))
            defer { board.releaseGlobally(); ui.panel.orderOut(nil) }
            ui.pasteboard = board
            var samples: [[String: Double]] = []
            for _ in 0..<3 {
                ui.showPanel()
                ui.panel.setFrameOrigin(.init(x: screen.frame.maxX + 200, y: screen.frame.maxY + 200))
                try await Task.sleep(nanoseconds: 300_000_000)
                ui.state.select(store.items.first { $0.id == text.id }!)
                var notified: TimeInterval?, feedback: TimeInterval?, closed: TimeInterval?
                let restore = store.didRestoreItem.sink { notified = ProcessInfo.processInfo.systemUptime }
                ui.copiedItemsHandler = { feedback = ProcessInfo.processInfo.systemUptime }
                let observer = NotificationCenter.default.addObserver(forName: NSWindow.willCloseNotification,
                    object: ui.panel, queue: .main) { _ in closed = ProcessInfo.processInfo.systemUptime }
                let prior = store.items.first { $0.id == text.id }!.updatedAt
                let start = ProcessInfo.processInfo.systemUptime
                ui.copySelection(plainTextOnly: false)
                let returned = ProcessInfo.processInfo.systemUptime
                guard let notification = notified, let copied = feedback,
                      notification <= copied, copied <= returned,
                      store.items.first(where: { $0.id == text.id })!.updatedAt > prior,
                      board.string(forType: .string) == text.plainText else {
                    throw Failure(message: "Save/DidRestore/feedback/copy order mismatch")
                }
                while ui.panel.isVisible {
                    guard ProcessInfo.processInfo.systemUptime - start < 10 else { throw Failure(message: "Close timeout") }
                    try await Task.sleep(nanoseconds: 5_000_000)
                }
                NotificationCenter.default.removeObserver(observer)
                restore.cancel()
                guard let closed, notification < closed else { throw Failure(message: "Restore occurred after close") }
                samples.append(["copy_return_ms": (returned-start)*1000,
                    "history_notification_ms": (notification-start)*1000, "panel_closed_ms": (closed-start)*1000])
            }
            let reopened = try ClipboardStore(directoryURL: directory)
            guard reopened.items == store.items else { throw Failure(message: "Durable state mismatch") }
            fixtures.append(["archive_bytes": archiveBytes.intValue, "cloud_journal_enabled": sync, "samples": samples])
        }
        print(String(data: try JSONSerialization.data(withJSONObject: ["passed": true, "fixtures": fixtures,
            "scope": "Release build; synthetic temporary data, private pasteboards and offscreen windows. No original runtime benchmark or network sync."], options: [.sortedKeys]), encoding: .utf8)!)
    }
}
