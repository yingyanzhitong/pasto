import AppKit
import Foundation
import PastoCore
import CryptoKit

@main
struct ICloudDriveControllerHarness {
    struct Failure: Error { let message: String }
    static var checks = 0
    static func check(_ value: @autoclosure () throws -> Bool, _ message: String) throws {
        guard try value() else { throw Failure(message: message) }
        checks += 1
    }
    @MainActor static func idle(_ controller: ICloudDriveSyncController) async throws {
        let deadline = Date().addingTimeInterval(10)
        while controller.isBusy {
            guard Date() < deadline else { throw Failure(message: "Controller did not finish") }
            try await Task.sleep(for: .milliseconds(20))
        }
    }

    @MainActor static func main() async throws {
        _ = NSApplication.shared
        let files = FileManager.default
        let root = files.temporaryDirectory.appendingPathComponent("PastoDriveController-\(UUID())")
        let cloud = root.appendingPathComponent("cloud"), shared = cloud.appendingPathComponent("Pasto")
        try files.createDirectory(at: cloud, withIntermediateDirectories: true)
        defer { try? files.removeItem(at: root) }
        let suite = "local.pasto.drive-controller.\(UUID())"
        let defaults = UserDefaults(suiteName: suite)!
        defer { defaults.removePersistentDomain(forName: suite) }
        let a = try ClipboardStore(directoryURL: root.appendingPathComponent("a"))
        let b = try ClipboardStore(directoryURL: root.appendingPathComponent("b"))
        a.preferences.historyRetentionDays = 0; b.preferences.historyRetentionDays = 0
        let group = try a.createPinboard(name: "合成分组", colorHex: "#12AB89")
        let id = try a.add(ClipboardItem(plainText: "Generated A", pinboardIDs: [group.id], pinboardOwnerID: group.id))
        var first: ICloudDriveSyncController? = ICloudDriveSyncController(store: a, defaults: defaults,
            supportedDataDirectory: a.directoryURL, cloudRoot: cloud)
        try check(first!.canSync && !first!.isEnabled, "Free sync must not require CloudKit signing")
        first!.start()
        try check(!first!.isEnabled && !files.fileExists(atPath: shared.path), "First launch created the cloud folder without opt-in")
        first!.setEnabled(true)
        try await idle(first!)
        try check(first!.isEnabled && first!.lastSyncDate != nil, "Switch did not create the default folder and synchronize")
        weak var retired = first
        first = nil
        await Task.yield()
        try check(retired == nil, "Timer retained the retired controller")
        let resumed = ICloudDriveSyncController(store: a, defaults: defaults,
            supportedDataDirectory: a.directoryURL, cloudRoot: cloud)
        defer { resumed.setEnabled(false) }
        resumed.start()
        try await idle(resumed)
        try check(resumed.isEnabled, "Saved opt-in did not resume")
        try check(resumed.folderURL?.path == shared.path, "Automatic folder was not restored")
        let resumedIdentity = try a.prepareICloudSync().deviceID
        resumed.setEnabled(true)
        try await idle(resumed)
        try check(try a.prepareICloudSync().deviceID == resumedIdentity, "Equivalent directory URLs reset sync identity")
        let second = ICloudDriveSyncController(store: b, defaults: defaults,
            supportedDataDirectory: b.directoryURL, cloudRoot: cloud)
        defer { second.setEnabled(false) }
        second.setEnabled(true)
        try await idle(second)
        try check(b.items.contains { $0.id == id } && b.pinboards.contains(group), "Controller did not merge content and group")
        let bID = try b.add(ClipboardItem(plainText: "Generated B"))
        second.syncNow(); try await idle(second)
        resumed.syncNow(); try await idle(resumed)
        try check(a.items.contains { $0.id == bID }, "Other client's item did not merge")
        try a.permanentlyDelete(ids: [id])
        resumed.syncNow(); try await idle(resumed)
        second.syncNow(); try await idle(second)
        try check(!b.items.contains { $0.id == id }, "Permanent deletion did not propagate")
        resumed.setEnabled(false)
        resumed.setEnabled(true)
        try await idle(resumed)
        try check(try a.prepareICloudSync().deviceID == resumedIdentity, "Toggling the same folder reset sync identity")
        resumed.setEnabled(false)
        try check(files.fileExists(atPath: shared.appendingPathComponent("PastoSync-v1").path)
                  && a.items.contains { $0.id == bID }, "Disabling sync removed local or cloud content")

        func fixture(_ name: String, cloudRoot: URL) throws -> ICloudDriveSyncController {
            let store = try ClipboardStore(directoryURL: root.appendingPathComponent(name))
            _ = try store.add(ClipboardItem(plainText: "Synthetic " + name))
            return ICloudDriveSyncController(store: store, defaults: defaults,
                supportedDataDirectory: store.directoryURL, cloudRoot: cloudRoot)
        }
        func saveLegacyFolder(_ controllerName: String, folder: URL) {
            let storeURL = root.appendingPathComponent(controllerName)
            let digest = SHA256.hash(data: Data(storeURL.standardizedFileURL.path.utf8))
                .map { String(format: "%02x", $0) }.joined()
            defaults.set(folder.path, forKey: "pasto.icloud-drive.\(digest).folder")
        }
        let unavailable = root.appendingPathComponent("unavailable-cloud")
        let missing = try fixture("missing", cloudRoot: unavailable)
        missing.setEnabled(true)
        try check(!missing.isEnabled && !missing.isBusy && missing.statusText.hasPrefix("无法开启"), "Unavailable iCloud was not reported inline")
        try check(!files.fileExists(atPath: unavailable.path), "Created a fake iCloud root")
        let missingReopened = try fixture("missing", cloudRoot: unavailable)
        missingReopened.start()
        try check(!missingReopened.isEnabled, "Failed activation persisted an enabled switch")

        let blockedRoot = root.appendingPathComponent("blocked-cloud")
        try files.createDirectory(at: blockedRoot, withIntermediateDirectories: true)
        let blockedFile = blockedRoot.appendingPathComponent("Pasto")
        let sentinel = Data("Do not replace".utf8)
        try sentinel.write(to: blockedFile)
        let blocked = try fixture("blocked", cloudRoot: blockedRoot)
        blocked.setEnabled(true)
        try check(!blocked.isEnabled, "Accepted a file as the default folder")
        try check(try Data(contentsOf: blockedFile) == sentinel, "Overwrote an existing file")

        let linkedRoot = root.appendingPathComponent("linked-cloud")
        let outside = root.appendingPathComponent("outside")
        try files.createDirectory(at: linkedRoot, withIntermediateDirectories: true)
        try files.createDirectory(at: outside, withIntermediateDirectories: true)
        try files.createSymbolicLink(at: linkedRoot.appendingPathComponent("Pasto"), withDestinationURL: outside)
        let linked = try fixture("linked", cloudRoot: linkedRoot)
        linked.setEnabled(true)
        try check(!linked.isEnabled && !files.fileExists(atPath: outside.appendingPathComponent("PastoSync-v1").path), "Followed a default-folder symlink outside iCloud")

        saveLegacyFolder("invalid-legacy", folder: outside)
        let invalidLegacy = try fixture("invalid-legacy", cloudRoot: cloud)
        invalidLegacy.setEnabled(true)
        try check(!invalidLegacy.isEnabled, "Accepted a saved folder outside iCloud")
        let legacyFolder = cloud.appendingPathComponent("Existing Custom Folder")
        try files.createDirectory(at: legacyFolder, withIntermediateDirectories: true)
        saveLegacyFolder("legacy", folder: legacyFolder)
        let legacy = try fixture("legacy", cloudRoot: cloud)
        legacy.setEnabled(true)
        try await idle(legacy)
        try check(legacy.isEnabled && legacy.folderURL?.path == legacyFolder.path && legacy.lastSyncDate != nil, "Upgrade abandoned the saved custom directory")
        legacy.setEnabled(false)

        let cancelledCloud = root.appendingPathComponent("cancelled-cloud")
        try files.createDirectory(at: cancelledCloud, withIntermediateDirectories: true)
        let cancelled = try fixture("cancelled", cloudRoot: cancelledCloud)
        cancelled.setEnabled(true)
        cancelled.setEnabled(false)
        try await Task.sleep(for: .milliseconds(100))
        try check(!cancelled.isEnabled && !cancelled.isBusy && cancelled.statusText.contains("已关闭"), "Late task replaced disabled state")
        try check(!files.fileExists(atPath: cancelledCloud.appendingPathComponent("Pasto/PastoSync-v1").path), "Cancelled queued task wrote cloud documents")
        let disabled = ICloudDriveSyncController(store: a, defaults: defaults,
            supportedDataDirectory: a.directoryURL, cloudRoot: cloud)
        disabled.start()
        try check(!disabled.isEnabled, "Disabled setting was not persisted")
        print(String(decoding: try JSONSerialization.data(withJSONObject: ["passed": true, "checks": checks,
            "scope": "Temporary stores, defaults and synthetic cloud root; production defaults still require the real data directory and explicit switch opt-in. No folder chooser or confirmation dialog.",
            "real_icloud_accessed": false, "user_history_accessed": false], options: [.sortedKeys]), as: UTF8.self))
    }
}
