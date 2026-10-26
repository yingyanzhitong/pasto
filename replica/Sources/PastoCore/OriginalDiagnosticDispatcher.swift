import Dispatch
import Foundation
import OSLog

public final class OriginalConsoleLogConfiguration {
    public var level: UInt8

    private init(level: UInt8) { self.level = level }

    public static func f_1000d4958() -> OriginalConsoleLogConfiguration {
        OriginalConsoleLogConfiguration(level: 1)
    }

    public func f_1000d55cc() -> UInt8 { level }

    public func f_1000d55fc(_ level: UInt8) { self.level = level }
}

public protocol OriginalDiagnosticOutput: AnyObject {
    func emit(level: UInt8, name: String, message: String)
}

/// All outputs share the original serial queue; their mutable caches are used
/// only inside the dispatcher's synchronous output pass.
public final class OriginalDiagnosticDispatcher: OriginalDiagnosticSink {
    private static let queue = f_1000d4e28()
    public let name: String
    public let configuration: OriginalConsoleLogConfiguration
    private let outputs: [any OriginalDiagnosticOutput]

    private init(name: String, configuration: OriginalConsoleLogConfiguration,
                 outputs: [any OriginalDiagnosticOutput]) {
        self.name = name
        self.configuration = configuration
        self.outputs = outputs
    }

    public static func f_1000d48fc() -> OriginalConsoleLogConfiguration {
        OriginalDependencies.f_1000d80e0(file: "PasteLogging/DI+PasteLogging.swift", line: 37, column: 19,
                                         factory: OriginalConsoleLogConfiguration.f_1000d4958)
    }

    public static func f_1000d4994() -> OriginalFileLogOutput {
        OriginalDependencies.f_1000d80e0(file: "PasteLogging/DI+PasteLogging.swift", line: 43, column: 19,
                                         factory: OriginalFileLogOutput.f_1000d49e8)
    }

    public static func f_1000d4a94(name: String) -> any OriginalDiagnosticSink {
        let configuration = f_1000d48fc()
        let system = OriginalDependencies.f_1000d80e0(
            file: "PasteLogging/DI+PasteLogging.swift", line: 56, column: 31,
            factory: OriginalSystemLogOutput.f_1000d4c18)
        let file = f_1000d4994()
        return OriginalDiagnosticDispatcher(name: name, configuration: configuration, outputs: [system, file])
    }

    private static func f_1000d4e28() -> DispatchQueue {
        DispatchQueue(label: "com.wiheads.paste.logger", qos: .utility,
                      attributes: [], autoreleaseFrequency: .inherit)
    }

    public func emit(level: UInt8, message: String) { f_1000d4fc0(level: level, message: message) }

    public func f_1000d4fc0(level: UInt8, message: String) {
        guard configuration.f_1000d55cc() <= level else { return }
        Self.queue.sync { f_1000d5160(level: level, message: message) }
    }

    private func f_1000d5160(level: UInt8, message: String) {
        for output in outputs { output.emit(level: level, name: name, message: message) }
    }
}

public final class OriginalSystemLogOutput: OriginalDiagnosticOutput {
    private var loggers: [String: Logger] = [:]

    private init() {}

    public static func f_1000d4c18() -> OriginalSystemLogOutput { OriginalSystemLogOutput() }

    public func emit(level: UInt8, name: String, message: String) {
        f_1000d6ad0(level: level, name: name, message: message)
    }

    public func f_1000d6ad0(level: UInt8, name: String, message: String) {
        let logger = f_1000d6c8c(name: name)
        let type: OSLogType
        switch level {
        case 0: type = .debug
        case 1: type = .info
        case 2: type = .error
        default: type = .fault
        }
        logger.log(level: type, "\(message, privacy: .public)")
    }

    private func f_1000d6c8c(name: String) -> Logger {
        if let logger = loggers[name] { return logger }
        let logger = Logger(subsystem: name, category: name)
        f_1000d6e90(logger, name: name)
        return logger
    }

    private func f_1000d6e90(_ logger: Logger?, name: String) { loggers[name] = logger }
}

public final class OriginalFileLogOutput: OriginalDiagnosticOutput {
    public var enabled: Bool
    public var directoryURL: URL?
    public private(set) var fileURL: URL?
    private var fileHandle: FileHandle?
    private static let timestampFormat = f_1000d5840()

    private init() {
        enabled = false
        directoryURL = nil
        fileURL = nil
        fileHandle = nil
    }

    public static func f_1000d49e8() -> OriginalFileLogOutput { OriginalFileLogOutput() }

    public func f_1000d56f8(_ url: URL?) { directoryURL = url }

    private static func f_1000d5840() -> Date.ISO8601FormatStyle {
        Date.ISO8601FormatStyle(dateSeparator: .dash, dateTimeSeparator: .standard,
                               timeSeparator: .colon, timeZoneSeparator: .omitted,
                               includingFractionalSeconds: true, timeZone: TimeZone(secondsFromGMT: 0)!)
    }

    public func emit(level: UInt8, name: String, message: String) {
        f_1000d5aec(level: level, name: name, message: message)
    }

    public func f_1000d5aec(level: UInt8, name: String, message: String) {
        guard enabled, let directoryURL else { return }
        let timestamp = Date.now.formatted(Self.timestampFormat)
        let tag: String
        switch level {
        case 0: tag = "DEBUG"
        case 1: tag = "INFO"
        case 2: tag = "WARN"
        default: tag = "ERROR"
        }
        guard let data = "[\(timestamp)] [\(tag)] [\(name)] \(message)\n".data(using: .utf8, allowLossyConversion: false) else { return }
        if fileHandle == nil {
            if let fileURL, FileManager.default.fileExists(atPath: fileURL.path) {
                fileHandle = try? FileHandle(forWritingTo: fileURL)
                fileHandle?.seekToEndOfFile()
            } else {
                let formatter = DateFormatter()
                formatter.dateFormat = "yyyy-MM-dd-HHmmss"
                let filename = "paste-diagnostics-" + formatter.string(from: Date()) + "-"
                    + ProcessInfo.processInfo.processIdentifier.description + ".log"
                let url = directoryURL.appendingPathComponent(filename)
                _ = FileManager.default.createFile(atPath: url.path, contents: nil, attributes: nil)
                fileHandle = try? FileHandle(forWritingTo: url)
                fileURL = url
            }
        }
        fileHandle?.write(data)
        fileHandle?.synchronizeFile()
    }

    public func f_1000d682c() {
        try? fileHandle?.close()
        fileHandle = nil
    }
}
