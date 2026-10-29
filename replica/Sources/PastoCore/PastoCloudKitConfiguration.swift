import Foundation
import PastoObjC
import Security

public struct PastoCloudKitConfiguration: Sendable {
    public let containerIdentifier: String
    public let teamIdentifier: String
    public let environment: String

    /// Read actual code-signing entitlements, never a fabricated plist or an original vendor ID.
    /// CKContainer must not be initialized at all in an unentitled/ad-hoc build (it can abort).
    public static func current(bundle: Bundle = .main) throws -> Self {
        try validate(container: bundle.object(forInfoDictionaryKey: "PastoCloudKitContainerIdentifier") as? String,
            bundleIdentifier: bundle.bundleIdentifier, entitlements: PRCloudKitEntitlements.currentProcess())
    }

    public static func validate(container: String?, bundleIdentifier: String?, entitlements: [String: Any]) throws -> Self {
        guard let container, container.hasPrefix("iCloud."),
              !container.lowercased().contains("wiheads"),
              let containers = entitlements["com.apple.developer.icloud-container-identifiers"] as? [String], containers.contains(container),
              let services = entitlements["com.apple.developer.icloud-services"] as? [String], services.contains("CloudKit"),
              let team = entitlements["com.apple.developer.team-identifier"] as? String, !team.isEmpty, team != "4788TTJ39Y",
              let bundleIdentifier, entitlements["com.apple.application-identifier"] as? String == "\(team).\(bundleIdentifier)",
              let environment = entitlements["com.apple.developer.icloud-container-environment"] as? String,
              ["Development", "Production"].contains(environment) else { throw PastoCloudKitError.unconfigured }
        return Self(containerIdentifier: container, teamIdentifier: team, environment: environment)
    }
}
