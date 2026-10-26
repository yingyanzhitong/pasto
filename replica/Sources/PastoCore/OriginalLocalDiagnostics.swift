import Foundation
import os

public protocol OriginalDiagnosticSink {
    func emit(level: UInt8, message: String)
}

extension OriginalDiagnosticSink {
    public func f_1000d4db8(_ message: String) { emit(level: 0, message: message) }
    public func f_1000d4dd4(_ message: String) { emit(level: 1, message: message) }
    public func f_1000d4df0(_ message: String) { emit(level: 2, message: message) }
    public func f_1000d4e0c(_ message: String) { emit(level: 3, message: message) }
}

extension OriginalDependencyValues {
    public var diagnosticFactory: (String) -> any OriginalDiagnosticSink {
        { OriginalDiagnosticDispatcher.f_1000d4a94(name: $0) }
    }
}

public final class OriginalNamedDiagnostic {
    private static let factoryDependency = OriginalDependency(\OriginalDependencyValues.diagnosticFactory)
    private let lock = OSAllocatedUnfairLock<Void>(uncheckedState: ())
    public let name: String
    private var cached: (any OriginalDiagnosticSink)?

    private init(name: String) {
        self.name = name
        self.cached = nil
    }

    public static func f_1000d4624(name: String) -> OriginalNamedDiagnostic {
        OriginalNamedDiagnostic(name: name)
    }

    public func f_1000d468c() -> any OriginalDiagnosticSink {
        lock.withLockUnchecked { _ in
            if let cached { return cached }
            let sink = Self.factoryDependency.f_1000da768()(name)
            cached = sink
            return sink
        }
    }
}
