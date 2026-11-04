import AppKit
import Foundation
import PastoCore

private final class UpdateProtocol: URLProtocol {
    private static let lock = NSLock()
    private static var payload = Data()
    private static var status = 200
    private static var failure: Error?
    private static var requests: [URLRequest] = []

    static func reply(_ data: Data, status: Int = 200, failure: Error? = nil) {
        lock.withLock {
            payload = data
            self.status = status
            self.failure = failure
            requests = []
        }
    }

    static var capturedRequests: [URLRequest] { lock.withLock { requests } }

    override class func canInit(with request: URLRequest) -> Bool { true }
    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }
    override func stopLoading() { }

    override func startLoading() {
        let (data, status, failure) = Self.lock.withLock {
            Self.requests.append(request)
            return (Self.payload, Self.status, Self.failure)
        }
        DispatchQueue.global().asyncAfter(deadline: .now() + 0.02) { [self] in
            if let failure {
                client?.urlProtocol(self, didFailWithError: failure)
                return
            }
            let response = HTTPURLResponse(url: request.url!, statusCode: status,
                httpVersion: "HTTP/1.1", headerFields: ["Content-Type": "application/json"])!
            client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
            client?.urlProtocol(self, didLoad: data)
            client?.urlProtocolDidFinishLoading(self)
        }
    }
}

@main
struct AppUpdateHarness {
    struct Failure: Error { let message: String }
    static func check(_ value: @autoclosure () -> Bool, _ message: String) throws {
        if !value() { throw Failure(message: message) }
    }

    static func release(_ version: String = "1.0.6") -> [String: Any] {
        let name = "Pasto-\(version)-macos-universal.dmg"
        return ["tag_name": "v\(version)", "draft": false, "prerelease": false,
            "published_at": "2026-11-04T00:00:00Z", "assets": [["name": name,
            "state": "uploaded", "size": 1024,
            "browser_download_url": "https://github.com/yingyanzhitong/pasto/releases/download/v\(version)/\(name)"]]]
    }

    static func reply(_ release: [String: Any], status: Int = 200) throws {
        UpdateProtocol.reply(try JSONSerialization.data(withJSONObject: release), status: status)
    }

    @MainActor static func main() async {
        do {
            let app = NSApplication.shared
            app.setActivationPolicy(.accessory)
            app.finishLaunching()
            let icon = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
                .deletingLastPathComponent().deletingLastPathComponent().appendingPathComponent("Assets/PastoIcon.png")
            if let image = NSImage(contentsOf: icon) { app.applicationIconImage = image }
            let configuration = URLSessionConfiguration.ephemeral
            configuration.protocolClasses = [UpdateProtocol.self]
            let session = URLSession(configuration: configuration)
            defer { session.invalidateAndCancel() }
            if CommandLine.arguments.contains("--preview") {
                try reply(release())
                let checker = PastoUpdateChecker(currentVersion: "1.0.5", session: session)
                let controller = PastoAboutWindowController(checker: checker, installUpdate: {})
                controller.showWindow(nil)
                Timer.scheduledTimer(withTimeInterval: 120, repeats: false) { _ in NSApp.terminate(nil) }
                print("PREVIEW_READY")
                fflush(stdout)
                app.run()
                withExtendedLifetime(controller) { }
                return
            }
            try await run(session: session)
            if CommandLine.arguments.contains("--live") {
                let live = PastoUpdateChecker(currentVersion: "0.0.0", session: URLSession(configuration: .ephemeral))
                await live.check(force: true)
                guard case let .available(update) = live.state else {
                    throw Failure(message: "Live GitHub release check failed: \(live.state)")
                }
                print("{\"live_github\":true,\"version\":\"\(update.version)\",\"download\":\"\(update.downloadURL.absoluteString)\"}")
            }
            print("{\"passed\":true,\"version_comparison\":true,\"release_validation\":true,\"throttle_and_retry\":true,\"concurrent_checks\":true,\"about_controls\":true}")
        } catch {
            let result: [String: Any] = ["passed": false, "error": String(describing: error)]
            print(String(data: try! JSONSerialization.data(withJSONObject: result), encoding: .utf8)!)
            exit(1)
        }
    }

    @MainActor static func run(session: URLSession) async throws {
        try check(PastoUpdateChecker(session: session).currentVersion == "1.0.5-dev.2",
                  "Source version did not take precedence over the short bundle version")
        for (older, newer) in [("1.0.9", "1.0.10"), ("1.99.99", "2.0.0"),
            ("1.0.5-dev.2", "1.0.5-dev.10"), ("1.0.5-dev.10", "1.0.5"), ("1.0.5", "1.0.6-dev.1")] {
            try check(PastoReleaseVersion(older)! < PastoReleaseVersion(newer)!, "Incorrect version order")
        }
        try check(PastoReleaseVersion("v1.0.5") == PastoReleaseVersion("1.0.5"), "Tag prefix changed comparison")
        for value in ["", "1.0", "1.0.5\n", "1.-1.5", "1.0.5-beta", "1.0.5-dev.", "999999999999999999999.0.0"] {
            try check(PastoReleaseVersion(value) == nil, "Invalid version accepted: \(value)")
        }
        try reply(release())
        let checker = PastoUpdateChecker(currentVersion: "1.0.5", session: session)
        await checker.check(force: true)
        guard case let .available(update) = checker.state else { throw Failure(message: "Missing newer release") }
        try check(update.version == "1.0.6" && update.downloadURL.lastPathComponent == "Pasto-1.0.6-macos-universal.dmg",
                  "Wrong installer selected")
        let request = UpdateProtocol.capturedRequests[0]
        try check(request.url?.absoluteString == "https://api.github.com/repos/yingyanzhitong/pasto/releases/latest"
            && request.httpMethod == "GET" && request.httpBody == nil
            && request.value(forHTTPHeaderField: "Authorization") == nil
            && request.value(forHTTPHeaderField: "X-GitHub-Api-Version") == "2026-03-10", "Unexpected update request")

        var installations = 0
        let controller = PastoAboutWindowController(checker: checker, installUpdate: { installations += 1 })
        controller.window?.contentView?.layoutSubtreeIfNeeded()
        try check(controller.window?.contentView?.bounds.size == NSSize(width: 360, height: 320), "About layout changed")
        try check(!controller.downloadButton.isHidden && controller.downloadButton.isEnabled
            && controller.statusLabel.stringValue.contains("1.0.6"), "About omitted the newer version")
        controller.downloadButton.performClick(nil)
        try check(installations == 1, "Download did not start the in-app updater")
        var canInstall = false
        let retryDownload = PastoAboutWindowController(checker: checker, installUpdate: {
            if !canInstall { throw Failure(message: "Cannot start updater") }
        })
        retryDownload.download()
        try check(retryDownload.statusLabel.textColor == .systemRed, "Download failure was hidden")
        canInstall = true
        retryDownload.download()
        try check(retryDownload.statusLabel.stringValue.contains("1.0.6"), "Successful download retry kept stale error")

        try reply(release("1.0.5"))
        await checker.check(force: true)
        try check(checker.state == .upToDate && controller.downloadButton.isHidden, "Current version offered an update")
        controller.download()
        try check(installations == 1, "Stale download action started an installation")
        try reply(release("1.0.4"))
        await checker.check(force: true)
        try check(checker.state == .upToDate, "Older release offered a downgrade")

        for key in ["draft", "prerelease"] {
            var invalid = release()
            invalid[key] = true
            try await expectFailure(invalid, checker: checker)
        }
        for published: Any in [NSNull(), ""] {
            var invalid = release()
            invalid["published_at"] = published
            try await expectFailure(invalid, checker: checker)
        }
        for version in ["unknown", "1.0.6-dev.1"] {
            var invalid = release()
            invalid["tag_name"] = version
            try await expectFailure(invalid, checker: checker)
        }
        var invalid = release()
        invalid["assets"] = []
        try await expectFailure(invalid, checker: checker)
        invalid = release()
        let asset = (invalid["assets"] as! [[String: Any]])[0]
        invalid["assets"] = [asset, asset]
        try await expectFailure(invalid, checker: checker)
        for change in [["state": "new"], ["size": 0], ["browser_download_url": "https://example.com/Pasto.dmg"],
                       ["browser_download_url": "http://github.com/yingyanzhitong/pasto/file.dmg"],
                       ["name": "Pasto-1.0.6-macos-arm64.dmg"]] as [[String: Any]] {
            var invalid = release()
            var asset = (invalid["assets"] as! [[String: Any]])[0]
            asset.merge(change) { _, new in new }
            invalid["assets"] = [asset]
            try await expectFailure(invalid, checker: checker)
        }
        for status in [403, 404, 429, 500] {
            try reply(release(), status: status)
            await checker.check(force: true)
            guard case .failed = checker.state else { throw Failure(message: "HTTP failure reported as success") }
        }
        UpdateProtocol.reply(Data("invalid JSON".utf8))
        await checker.check(force: true)
        guard case .failed = checker.state else { throw Failure(message: "Malformed JSON accepted") }
        try check(controller.downloadButton.isHidden && controller.checkButton.isEnabled, "Failure prevents retry")
        UpdateProtocol.reply(Data(), failure: URLError(.notConnectedToInternet))
        await checker.check(force: true)
        guard case .failed = checker.state else { throw Failure(message: "Offline check reported as success") }
        try reply(release())
        controller.checkButton.performClick(nil)
        try await Task.sleep(for: .milliseconds(100))
        guard case .available = checker.state else { throw Failure(message: "Check button did not retry") }

        try reply(release())
        let throttled = PastoUpdateChecker(currentVersion: "1.0.5", session: session)
        let date = Date(timeIntervalSince1970: 1000)
        await throttled.check(now: date)
        await throttled.check(now: date.addingTimeInterval(1))
        try check(UpdateProtocol.capturedRequests.count == 1, "Automatic checks were not throttled")
        await throttled.check(now: date.addingTimeInterval(6 * 60 * 60))
        try check(UpdateProtocol.capturedRequests.count == 2, "Throttle never expires")
        await throttled.check(force: true, now: date.addingTimeInterval(6 * 60 * 60 + 1))
        try check(UpdateProtocol.capturedRequests.count == 3, "Manual check did not bypass throttle")

        try reply(release())
        let concurrent = PastoUpdateChecker(currentVersion: "1.0.5", session: session)
        async let first: Void = concurrent.check(force: true)
        async let second: Void = concurrent.check(force: true)
        _ = await (first, second)
        try check(UpdateProtocol.capturedRequests.count == 1, "Concurrent requests were duplicated")
        try reply(release())
        let unknown = PastoUpdateChecker(currentVersion: "unknown", session: session)
        await unknown.check(force: true)
        try check(UpdateProtocol.capturedRequests.isEmpty, "Invalid installed version reached network")
    }

    @MainActor static func expectFailure(_ release: [String: Any], checker: PastoUpdateChecker) async throws {
        try reply(release)
        await checker.check(force: true)
        guard case .failed = checker.state else { throw Failure(message: "Invalid release accepted") }
    }
}
