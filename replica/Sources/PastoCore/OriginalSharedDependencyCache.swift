import Foundation

/// Separate from a dependency wrapper's first-use cache: the original shares
/// services by their declaration site, scoped to the active dependency context.
public final class OriginalSharedDependencyCache: @unchecked Sendable {
    private let lock = NSRecursiveLock()
    private var values: [String: Any] = [:]

    public init() {}

    public func f_1000daac0<Value>(key: String, factory: () -> Value) -> Value {
        lock.lock()
        defer { lock.unlock() }
        if let stored = values[key] { return stored as! Value }
        let value = factory()
        f_1000dad10(value as Any, for: key)
        return value
    }

    /// nil removes the erased entry; a boxed Optional.none is a stored value.
    private func f_1000dad10(_ value: Any?, for key: String) {
        values[key] = value
    }
}

extension OriginalDependencies {
    private static let globalSharedCache = OriginalSharedDependencyCache()

    public static func f_1000d80e0<Value>(file: StaticString, line: UInt, column: UInt,
                                          factory: () -> Value) -> Value {
        let key = file.description + "-" + line.description + "-" + column.description
        if let overrides { return overrides.f_1000d8388(key: key, factory: factory) }
        return globalSharedCache.f_1000daac0(key: key, factory: factory)
    }

    /// A fresh scope has both a fresh override dictionary and a fresh shared
    /// service cache. Nesting never mutates the enclosing task's context.
    public static func f_1000d86bc<Result>(operation: () throws -> Result) rethrows -> Result {
        try withOverrides(OriginalDependencyOverrides(), operation: operation)
    }

    public static func f_1000d8d80<Value>(_ keyPath: KeyPath<OriginalDependencyValues, Value>,
                                         factory: @escaping () -> Value) {
        guard let overrides else { preconditionFailure("A dependency override requires an active scope") }
        overrides.f_1000d83a8(keyPath, factory: factory)
    }

    public static func f_1000d8e10(_ keyPath: AnyKeyPath) {
        guard let overrides else { preconditionFailure("A dependency override requires an active scope") }
        overrides.f_1000d8600(keyPath)
    }

    public static func f_1000d8e88() {
        guard let overrides else { preconditionFailure("Clearing overrides requires an active scope") }
        overrides.removeAllFactories()
    }
}
