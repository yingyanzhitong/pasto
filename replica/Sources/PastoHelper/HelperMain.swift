import AppKit
import Combine
import Foundation
import os

@main
enum HelperMain {
    @MainActor static func main() {
        let app = NSApplication.shared
        let delegate = HelperDelegate()
        app.delegate = delegate
        app.setActivationPolicy(.prohibited)
        app.run()
        withExtendedLifetime(delegate) {}
    }
}

@MainActor
final class HelperDelegate: NSObject, NSApplicationDelegate {
    private var defaults: UserDefaults? {
        UserDefaults(suiteName: "com.yingyanzhitong.paste-replica.session")
    }
    private let mainID = "com.yingyanzhitong.paste-replica"
    private let logger = Logger(subsystem: "com.yingyanzhitong.paste-replica.helper", category: "general")
    private var cancellables: Set<AnyCancellable> = []
    private var isLaunching = false
    private var retryCount = 0

    func applicationDidFinishLaunching(_ notification: Notification) {
        startMonitoring()
    }

    /// Paste Helper 0x100001488, with this independent app's bundle and defaults identities.
    private func startMonitoring() {
        logger.info("Paste Helper started at \(Bundle.main.bundleURL)")
        let url = applicationURL()
        let markedRunning = defaults?.bool(forKey: "pasteIsRunning") ?? false
        let running = isMainApplicationRunning()
        logger.info("Paste located at: \(url)")
        logger.info("Paste is marked as running: \(markedRunning)")
        logger.info("Paste is running: \(running)")
        observeRunningApplications()
    }

    /// Paste Helper 0x1000019f4: enclosing app, Launch Services, then the Applications fallback.
    private func applicationURL() -> URL {
        var enclosing = Bundle.main.bundleURL
        for _ in 0..<4 { enclosing.deleteLastPathComponent() }
        if enclosing.lastPathComponent == "Pasto.app" { return enclosing }
        if let registered = NSWorkspace.shared.urlForApplication(withBundleIdentifier: mainID) {
            return registered
        }
        // Static import resolution identifies URL.init(fileURLWithPath:), not URL(string:).
        return URL(fileURLWithPath: "/Applications/Pasto.app")
    }

    /// Paste Helper 0x100001db0; the KVO publisher includes its initial value.
    private func observeRunningApplications() {
        logger.info("Starting to monitor running applications")
        NSWorkspace.shared.publisher(for: \.runningApplications, options: [.initial, .new])
            .sink { [weak self] _ in
                // 0x10000239c / 0x1000025a0 enqueue a MainActor task for each publication.
                MainActor.assumeIsolated {
                    _ = Task { @MainActor [weak self] in self?.checkRunning() }
                }
            }
            .store(in: &cancellables)
    }

    /// Paste Helper 0x100004c34: ignore missing identifiers; stop at the first matching app.
    private func isMainApplicationRunning() -> Bool {
        NSWorkspace.shared.runningApplications.contains { $0.bundleIdentifier == mainID }
    }

    /// Paste Helper 0x100002614: the launch guard covers an attempt, not the retry cooldown.
    private func checkRunning() {
        logger.info("Checking if Paste needs to be launched...")
        guard !isLaunching else {
            logger.info("Launch already in progress")
            return
        }
        guard defaults?.bool(forKey: "pasteIsRunning") == true else {
            logger.info("Paste is not marked as running")
            return
        }
        guard !isMainApplicationRunning() else {
            logger.info("Paste is already running")
            return
        }
        logger.info("Paste not running \n will launch in 3 seconds...")
        isLaunching = true
        Task { @MainActor [weak self] in
            // 0x10000307c / 0x100003100: cancellation also proceeds to the post-delay check.
            try? await ContinuousClock().sleep(for: .seconds(3))
            await self?.launchAfterDelay()
        }
    }

    /// Paste Helper 0x100003170 / 0x100003314: recheck the process, without rereading isRunning.
    private func launchAfterDelay() async {
        guard !isMainApplicationRunning() else {
            // The recovered branch returns without clearing isLaunching.
            logger.info("Paste is already running")
            return
        }
        completeLaunchAttempt(succeeded: await launchApplication())
    }

    /// Paste Helper 0x10000385c / 0x100003c20 / 0x100003d58.
    private func launchApplication() async -> Bool {
        defaults?.set(true, forKey: "pasteLaunchedByHelper")
        let url = applicationURL()
        let configuration = NSWorkspace.OpenConfiguration()
        configuration.activates = false
        logger.info("Launching Paste at \(url.path)")
        do {
            _ = try await openApplication(at: url, configuration: configuration)
            logger.info("Paste launched successfully.")
            return true
        } catch {
            logger.error("Failed to launch Paste: \(error.localizedDescription)")
            return false
        }
    }

    /// Paste Helper 0x100004230: error takes precedence; a successful callback must carry an app.
    private func openApplication(at url: URL, configuration: NSWorkspace.OpenConfiguration) async throws -> NSRunningApplication {
        try await withCheckedThrowingContinuation { continuation in
            NSWorkspace.shared.openApplication(at: url, configuration: configuration) { application, error in
                if let error { continuation.resume(throwing: error) }
                else {
                    guard let application else {
                        preconditionFailure("NSWorkspace returned neither an application nor an error")
                    }
                    continuation.resume(returning: application)
                }
            }
        }
    }

    /// Paste Helper 0x100003514: success resets the persistent retry counter; failure schedules retry.
    private func completeLaunchAttempt(succeeded: Bool) {
        if succeeded { retryCount = 0 }
        else {
            retryCount += 1
            let retryDelay = retryCount * 10
            logger.info("Retry in \(retryDelay) seconds...")
            Task { @MainActor [weak self] in
                // 0x100004020 / 0x10000413c / 0x1000041a8 recheck even if sleep throws.
                try? await ContinuousClock().sleep(for: .seconds(retryDelay))
                self?.checkRunning()
            }
        }
        isLaunching = false
    }
}
