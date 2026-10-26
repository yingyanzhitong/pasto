import Foundation
import os

/// Dependency keys are computed properties on a value with no stored state.
/// Providers remain separate from the task-local override and lazy cache.
public struct OriginalDependencyValues {
    public init() {}
}

public final class OriginalDependencyOverrides: @unchecked Sendable {
    private let lock = NSLock()
    private var factories: [AnyKeyPath: () -> Any] = [:]
    private let sharedCache = OriginalSharedDependencyCache()

    public init() {}

    /// The typed factory is erased only after it produces its result.
    public func f_1000d83a8<Root, Value>(_ keyPath: KeyPath<Root, Value>, factory: @escaping () -> Value) {
        lock.lock()
        factories[keyPath] = { factory() as Any }
        lock.unlock()
    }

    public func f_1000d8600(_ keyPath: AnyKeyPath) {
        lock.lock()
        _ = factories.removeValue(forKey: keyPath)
        lock.unlock()
    }

    func f_1000d8388<Value>(key: String, factory: () -> Value) -> Value {
        sharedCache.f_1000daac0(key: key, factory: factory)
    }

    func removeAllFactories() {
        lock.lock()
        factories.removeAll()
        lock.unlock()
    }

    /// The original casts Optional<Any>, including its nil case. Keeping that
    /// source type also preserves a successful cast to an optional dependency.
    public func f_1000d84ac<Root, Value>(_ keyPath: KeyPath<Root, Value>) -> Value? {
        lock.lock()
        let factory = factories[keyPath]
        lock.unlock()
        let value: Any? = factory?()
        return value as? Value
    }
}

public enum OriginalDependencies {
    @TaskLocal public static var overrides: OriginalDependencyOverrides?

    public static func f_1000da458<Root, Value>(root: Root, keyPath: KeyPath<Root, Value>) -> Value {
        if let overrides, case let .some(value) = overrides.f_1000d84ac(keyPath) {
            return value
        }
        return root[keyPath: keyPath]
    }

    /// This is the recovered task-local scope. The original container's
    /// separate recursive shared-service cache is tracked independently.
    public static func withOverrides<Result>(_ overrides: OriginalDependencyOverrides,
                                              operation: () throws -> Result) rethrows -> Result {
        try $overrides.withValue(overrides, operation: operation)
    }
}

/// 0x1000da6e0/0x1000da760/0x1000da768: resolve once while holding an unfair
/// lock. Optional.some(nil) is cached when Value itself is an optional type.
public final class OriginalDependency<Value>: @unchecked Sendable {
    private let lock: OSAllocatedUnfairLock<Void>
    private let resolve: () -> Value
    private var cached: Value?

    public init(_ keyPath: KeyPath<OriginalDependencyValues, Value>) {
        lock = OSAllocatedUnfairLock()
        cached = nil
        resolve = { Self.f_1000da760(keyPath) }
    }

    public static func f_1000da760(_ keyPath: KeyPath<OriginalDependencyValues, Value>) -> Value {
        OriginalDependencies.f_1000da458(root: OriginalDependencyValues(), keyPath: keyPath)
    }

    public func f_1000da768() -> Value {
        lock.withLockUnchecked {
            if case let .some(value) = cached { return value }
            let value = resolve()
            cached = .some(value)
            return value
        }
    }
}
