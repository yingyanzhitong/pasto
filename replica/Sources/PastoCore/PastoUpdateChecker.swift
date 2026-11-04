import Combine
import Foundation

/// Matches the stable and -dev.N version forms accepted by the release scripts.
public struct PastoReleaseVersion: Comparable, Sendable {
    public let text: String
    private let numbers: [Int]
    let development: Int?

    public init?(_ value: String) {
        guard value.range(of: #"\Av?[0-9]+\.[0-9]+\.[0-9]+(?:-dev\.[0-9]+)?\z"#,
                          options: .regularExpression) != nil else { return nil }
        text = value.hasPrefix("v") ? String(value.dropFirst()) : value
        let parts = text.components(separatedBy: "-dev.")
        numbers = parts[0].split(separator: ".").compactMap { Int($0) }
        guard numbers.count == 3 else { return nil }
        development = parts.count == 2 ? Int(parts[1]) : nil
        if parts.count == 2 && development == nil { return nil }
    }

    public static func == (lhs: Self, rhs: Self) -> Bool {
        lhs.numbers == rhs.numbers && lhs.development == rhs.development
    }

    public static func < (lhs: Self, rhs: Self) -> Bool {
        if lhs.numbers != rhs.numbers { return lhs.numbers.lexicographicallyPrecedes(rhs.numbers) }
        switch (lhs.development, rhs.development) {
        case let (left?, right?): return left < right
        case (nil, _): return false
        case (_, nil): return true
        }
    }
}

public struct PastoAvailableUpdate: Equatable, Sendable {
    public let version: String
    public let downloadURL: URL
}

@MainActor
public final class PastoUpdateChecker: ObservableObject {
    public enum State: Equatable {
        case idle, checking, upToDate
        case available(PastoAvailableUpdate)
        case failed(String)
    }

    @Published public private(set) var state: State = .idle
    public let currentVersion: String
    private let session: URLSession
    private var lastAttempt: Date?

    public init(currentVersion: String? = nil, session: URLSession = .shared) {
        self.currentVersion = currentVersion
            ?? Bundle.main.object(forInfoDictionaryKey: "PastoSourceVersion") as? String
            ?? Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String
            ?? "unknown"
        self.session = session
    }

    /// Called when About Pasto opens. Manual checks bypass the six-hour throttle.
    public func check(force: Bool = false, now: Date = Date()) async {
        guard state != .checking else { return }
        if !force, let lastAttempt, now.timeIntervalSince(lastAttempt) < 6 * 60 * 60 { return }
        lastAttempt = now
        state = .checking
        do {
            guard let current = PastoReleaseVersion(currentVersion) else {
                throw UpdateError.invalidCurrentVersion
            }
            var request = URLRequest(url: URL(string: "https://api.github.com/repos/yingyanzhitong/pasto/releases/latest")!)
            request.timeoutInterval = 15
            request.cachePolicy = .reloadIgnoringLocalCacheData
            request.setValue("application/vnd.github+json", forHTTPHeaderField: "Accept")
            request.setValue("2026-03-10", forHTTPHeaderField: "X-GitHub-Api-Version")
            request.setValue("Pasto", forHTTPHeaderField: "User-Agent")
            let (data, response) = try await session.data(for: request)
            guard let response = response as? HTTPURLResponse else { throw UpdateError.invalidRelease }
            guard response.statusCode == 200 else { throw UpdateError.http(response.statusCode) }
            let release = try JSONDecoder().decode(Release.self, from: data)
            guard !release.draft, !release.prerelease, release.published_at?.isEmpty == false,
                  let latest = PastoReleaseVersion(release.tag_name), latest.development == nil else {
                throw UpdateError.invalidRelease
            }
            if latest <= current {
                state = .upToDate
                return
            }
            let name = "Pasto-\(latest.text)-macos-universal.dmg"
            let assets = release.assets.filter { $0.name == name }
            let expectedURL = "https://github.com/yingyanzhitong/pasto/releases/download/\(release.tag_name)/\(name)"
            guard assets.count == 1, let asset = assets.first,
                  asset.state == "uploaded", asset.size > 0,
                  asset.browser_download_url == expectedURL, let url = URL(string: expectedURL) else {
                throw UpdateError.missingInstaller
            }
            state = .available(PastoAvailableUpdate(version: latest.text, downloadURL: url))
        } catch {
            state = .failed(error.localizedDescription)
        }
    }

    private struct Release: Decodable {
        let tag_name: String
        let draft: Bool
        let prerelease: Bool
        let published_at: String?
        let assets: [Asset]
    }

    private struct Asset: Decodable {
        let name: String
        let state: String
        let size: Int
        let browser_download_url: String
    }

    private enum UpdateError: LocalizedError {
        case invalidCurrentVersion, invalidRelease, missingInstaller, http(Int)

        var errorDescription: String? {
            switch self {
            case .invalidCurrentVersion: return OriginalSettingsLocalization.text("updates.invalid-version")
            case .invalidRelease: return OriginalSettingsLocalization.text("updates.invalid-release")
            case .missingInstaller: return OriginalSettingsLocalization.text("updates.missing-installer")
            case let .http(code):
                return OriginalSettingsLocalization.text("updates.http-error") + " (HTTP \(code))"
            }
        }
    }
}
