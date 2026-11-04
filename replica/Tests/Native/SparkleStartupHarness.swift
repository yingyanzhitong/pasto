import AppKit
import Sparkle

@main
struct SparkleStartupHarness {
    @MainActor static func main() throws {
        _ = NSApplication.shared
        let controller = SPUStandardUpdaterController(
            startingUpdater: false, updaterDelegate: nil, userDriverDelegate: nil)
        try controller.updater.start()
        precondition(controller.updater.canCheckForUpdates)
        precondition(!controller.updater.automaticallyChecksForUpdates)
        precondition(!controller.updater.automaticallyDownloadsUpdates)
        precondition(controller.updater.feedURL?.absoluteString ==
            "https://github.com/yingyanzhitong/pasto/releases/latest/download/appcast.xml")
        // Exercise scheduled work without initiating a check or showing UI.
        RunLoop.current.run(until: Date().addingTimeInterval(0.15))
        precondition(!controller.updater.sessionInProgress)
        print("{\"passed\":true,\"sparkle_startup\":true,\"manual_installation_only\":true}")
    }
}
