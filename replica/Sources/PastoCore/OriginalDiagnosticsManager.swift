import Foundation

/// Local diagnostics controls, using the same shared outputs as named loggers.
/// The caller owns preference persistence and restores the saved flag at launch.
@MainActor
public final class OriginalDiagnosticsManager {
    public static let preferenceKey = "isDiagnosticsEnabled"
    public private(set) var enabled = false
    public let logDirectory: URL
    private let configuration: OriginalConsoleLogConfiguration
    private let fileOutput: OriginalFileLogOutput
    private let persist: (Bool) -> Void

    public init(logDirectory: URL, configuration: OriginalConsoleLogConfiguration,
                fileOutput: OriginalFileLogOutput, persist: @escaping (Bool) -> Void) {
        self.logDirectory = logDirectory
        self.configuration = configuration
        self.fileOutput = fileOutput
        self.persist = persist
    }

    public static func makeLocal(logDirectory: URL, persist: @escaping (Bool) -> Void) -> OriginalDiagnosticsManager {
        OriginalDiagnosticsManager(logDirectory: logDirectory,
                                   configuration: OriginalDiagnosticDispatcher.f_1000d48fc(),
                                   fileOutput: OriginalDiagnosticDispatcher.f_1000d4994(), persist: persist)
    }

    public func f_1002fe514() {
        try? FileManager.default.createDirectory(at: logDirectory, withIntermediateDirectories: true, attributes: nil)
        fileOutput.f_1000d682c()
        fileOutput.f_1000d56f8(logDirectory)
        fileOutput.enabled = true
        configuration.f_1000d55fc(0)
    }

    public func f_1002fe72c(_ enabled: Bool) {
        let previous = self.enabled
        self.enabled = enabled
        guard previous != enabled else { return }
        persist(enabled)
        if self.enabled {
            f_1002fe514()
        } else {
            fileOutput.enabled = false
            fileOutput.f_1000d682c()
            configuration.f_1000d55fc(1)
        }
    }

    public func f_1002feb60() -> URL? { fileOutput.fileURL }

    public func f_1002febd4() -> [URL] {
        let contents = (try? FileManager.default.contentsOfDirectory(at: logDirectory,
                                                                    includingPropertiesForKeys: nil,
                                                                    options: [])) ?? []
        return contents.filter { $0.pathExtension == "log" && $0.lastPathComponent.hasPrefix("paste-diagnostics-") }
            .sorted { $0.lastPathComponent < $1.lastPathComponent }
    }
}
