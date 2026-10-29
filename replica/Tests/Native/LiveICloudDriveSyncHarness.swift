import Foundation
import PastoCore

/// Explicitly opt-in integration probe: writes only generated test content to iCloud Drive.
@main
struct LiveICloudDriveSyncHarness {
    /// Test-only independent observation. The production app does not invoke this utility.
    static func fileProviderUploadStatus(_ file: URL) -> Bool? {
        guard FileManager.default.isExecutableFile(atPath: "/usr/bin/fileproviderctl") else { return nil }
        let process = Process()
        let pipe = Pipe()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/fileproviderctl")
        process.arguments = ["evaluate", file.path]
        process.standardOutput = pipe; process.standardError = pipe
        do {
            try process.run()
            let output = String(decoding: pipe.fileHandleForReading.readDataToEndOfFile(), as: UTF8.self)
            process.waitUntilExit()
            guard process.terminationStatus == 0 else { return nil }
            let expression = try NSRegularExpression(pattern: #"\bisUploaded\s*=\s*([01]);"#)
            guard let match = expression.firstMatch(in: output, range: NSRange(output.startIndex..., in: output)),
                  let range = Range(match.range(at: 1), in: output) else { return nil }
            return output[range] == "1"
        } catch { return nil }
    }

    @MainActor static func main() async {
        let files = FileManager.default
        let root = files.homeDirectoryForCurrentUser.appendingPathComponent("Library/Mobile Documents/com~apple~CloudDocs")
        let testID = UUID().uuidString
        let cloud = root.appendingPathComponent("Pasto Sync Verification \(testID)", isDirectory: true)
        let local = files.temporaryDirectory.appendingPathComponent("PastoCloudProbe-\(testID)", isDirectory: true)
        var createdCloudFolder = false
        var stage = "create-test-folder"
        defer {
            if createdCloudFolder { try? files.removeItem(at: cloud) }
            try? files.removeItem(at: local)
        }
        do {
            guard files.fileExists(atPath: root.path) else { throw ICloudDriveSyncError.folderUnavailable }
            try files.createDirectory(at: cloud, withIntermediateDirectories: false)
            createdCloudFolder = true
            let source = try ClipboardStore(directoryURL: local.appendingPathComponent("source"))
            let id = try source.add(ClipboardItem(title: "Pasto synthetic sync verification", plainText: "Generated test data \(testID)"))
            let snapshot = try source.prepareICloudSync()
            let transport = ICloudDriveSyncTransport()
            stage = "coordinated-write"
            try await transport.write(snapshot, to: cloud)
            let file = cloud.appendingPathComponent("PastoSync-v1/\(snapshot.deviceID.uuidString).json")
            var uploaded = false
            var ubiquitous = false
            var metadataError: String?
            stage = "query-upload-status"
            for _ in 0..<20 {
                do {
                    let values = try file.resourceValues(forKeys: [.isUbiquitousItemKey, .ubiquitousItemIsUploadedKey, .ubiquitousItemUploadingErrorKey])
                    ubiquitous = values.isUbiquitousItem == true
                    if let error = values.ubiquitousItemUploadingError { throw error }
                    if values.ubiquitousItemIsUploaded == true { uploaded = true; break }
                } catch { metadataError = "\((error as NSError).domain) \((error as NSError).code): \(error.localizedDescription)"; break }
                try await Task.sleep(for: .seconds(2))
            }
            var providerUploaded: Bool?
            if !uploaded {
                stage = "file-provider-upload-status"
                for _ in 0..<20 {
                    providerUploaded = fileProviderUploadStatus(file)
                    if providerUploaded == true { break }
                    try await Task.sleep(for: .seconds(2))
                }
            }
            let target = try ClipboardStore(directoryURL: local.appendingPathComponent("target"))
            let targetSnapshot = try target.prepareICloudSync()
            stage = "coordinated-readback"
            let incoming = try await transport.read(from: cloud, excluding: targetSnapshot.deviceID)
            _ = try target.applyICloudSync(incoming)
            let contentMatches = target.items.first(where: { $0.id == id })?.plainText == source.items.first?.plainText
            guard contentMatches else { throw ICloudDriveSyncError.invalidSnapshot }
            let uploadConfirmed = uploaded || providerUploaded == true
            var report: [String: Any] = ["passed": uploadConfirmed, "iCloud_document_recognized": ubiquitous || providerUploaded != nil,
                "system_reports_uploaded": uploaded, "coordinated_readback_matches": contentMatches,
                "cloud_upload_confirmed": uploadConfirmed,
                "second_physical_mac_tested": false, "user_history_accessed": false,
                "synthetic_cloud_folder_cleanup_scheduled": true]
            if let metadataError { report["upload_status_error"] = metadataError }
            if let providerUploaded { report["fileprovider_reports_uploaded"] = providerUploaded }
            print(String(decoding: try JSONSerialization.data(withJSONObject: report, options: [.sortedKeys]), as: UTF8.self))
            if !uploadConfirmed { exitAfterCleanup(cloud: cloud, local: local) }
        } catch {
            print(String(decoding: try! JSONSerialization.data(withJSONObject: ["passed": false,
                "error": error.localizedDescription, "stage": stage, "domain": (error as NSError).domain,
                "code": (error as NSError).code, "user_history_accessed": false]), as: UTF8.self))
            exitAfterCleanup(cloud: createdCloudFolder ? cloud : nil, local: local)
        }
    }

    static func exitAfterCleanup(cloud: URL?, local: URL) -> Never {
        if let cloud { try? FileManager.default.removeItem(at: cloud) }
        try? FileManager.default.removeItem(at: local)
        exit(1)
    }
}
