import AppKit
import Sparkle

/// Sparkle owns download verification, replacement, and relaunch. The About
/// window's GitHub query only supplies the version summary shown to the user.
@MainActor
final class PastoInAppUpdater {
    private let controller = SPUStandardUpdaterController(
        startingUpdater: false, updaterDelegate: nil, userDriverDelegate: nil)
    private var started = false

    func checkForUpdates() throws {
        if !started {
            try controller.updater.start()
            started = true
        }
        controller.checkForUpdates(nil)
    }
}
