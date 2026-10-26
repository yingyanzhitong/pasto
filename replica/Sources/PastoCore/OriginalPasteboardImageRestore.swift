import Foundation
import UniformTypeIdentifiers

/// The replica supplies a separate temporary root so original Paste files are never touched.
public final class OriginalPasteboardImageRestore: @unchecked Sendable {
    private let temporaryRoot: URL
    private let diagnostics = OriginalNamedDiagnostic.f_1000d4624(name: "PasteboardItemProcessor")

    public init(temporaryRoot: URL) {
        self.temporaryRoot = temporaryRoot
    }

    public func prepare(_ items: [OriginalPasteboardItem], sourceName: String?, timestamp: Date?) -> [OriginalPasteboardItem] {
        // Product isolation adapter; the original algorithm starts at its supplied temporary root.
        do {
            try FileManager.default.createDirectory(at: temporaryRoot, withIntermediateDirectories: true)
        } catch {
            diagnostics.f_1000d468c().f_1000d4e0c("Error while creating temporary images directory: \(error.localizedDescription)")
        }
        return f_100383df4(items, sourceName: sourceName, timestamp: timestamp)
    }

    public func f_100384824() -> URL? {
        // Original 0x1003848f4 calls the one-String URL append, then hasDirectoryPath,
        // not fileExists and not the isDirectory: overload. Preserve that distinction.
        let directory = temporaryRoot.appendingPathComponent("images")
        if !directory.hasDirectoryPath {
            do {
                try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: false)
            } catch {
                diagnostics.f_1000d468c().f_1000d4e0c("Error while creating temporary images directory: \(error.localizedDescription)")
            }
        }
        return directory
    }

    /// Value projection of the original entity-based image preparation branch.
    public func f_100383df4(_ items: [OriginalPasteboardItem], sourceName: String?, timestamp: Date?) -> [OriginalPasteboardItem] {
        guard let directory = f_100384824() else { return items }
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd HH.mm.ss"
        let name = (sourceName ?? "Paste") + " " + formatter.string(from: timestamp ?? Date.now)
        // Original uses one shared base name: equal-format items can target the same file.
        for item in items {
            for type in [UTType.png, .jpeg, .heic, .tiff] {
                guard let data = item.f_10037d810(forType: type.identifier) else { continue }
                let file = directory.appendingPathComponent(name, conformingTo: type)
                do {
                    try data.write(to: file, options: [])
                    item.f_10037c4a8(file.absoluteString, forType: UTType.fileURL.identifier)
                } catch {
                    diagnostics.f_1000d468c().f_1000d4e0c("Error while writing temporary image copy to file: \(error.localizedDescription)")
                }
                // Failure exits this item's type search as well; the next item is still processed.
                break
            }
        }
        f_100384aac()
        return items
    }

    public func f_100384aac() {
        guard let directory = f_100384824() else { return }
        DispatchQueue.global(qos: .background).async { [weak self] in
            Self.f_100384e6c(directory: directory) { self?.diagnostics }
        }
    }

    public static func f_100384e6c(directory: URL, diagnostics: () -> OriginalNamedDiagnostic?) {
        let cutoff = Date().addingTimeInterval(-86400)
        do {
            let files = try FileManager.default.contentsOfDirectory(at: directory, includingPropertiesForKeys: nil, options: [])
            for file in files {
                let values = try file.resourceValues(forKeys: [.creationDateKey])
                if let created = values.creationDate, created < cutoff {
                    try FileManager.default.removeItem(at: file)
                }
            }
        } catch {
            diagnostics()?.f_1000d468c().f_1000d4e0c("Error while remove old temporary image file: \(error.localizedDescription)")
        }
    }
}
