import Foundation

/// Recovered value conversion shared by the original local Config wrappers.
/// Storage lookup and the original archive/key-path layout remain separate concerns.
public enum OriginalConfigurationFunctions {
    /// Paste 0x1002cb804: conditionally cast Optional<Any> to the requested value type.
    public static func f_1002cb804<Value>(storedValue: Any?, as type: Value.Type) -> Value? {
        storedValue as? Value
    }

    /// Paste 0x1002cc5a8: the closure entry captures and forwards the configured value type.
    public static func f_1002cc5a8<Value>(storedValue: Any?, as type: Value.Type) -> Value? {
        f_1002cb804(storedValue: storedValue, as: type)
    }

    /// Paste 0x1002ca920: decoding failure alone evaluates the configured default.
    public static func f_1002ca920<Value>(storedValue: Any?,
                                        decode: (Any?) -> Value?,
                                        defaultValue: () -> Value) -> Value {
        if let value = decode(storedValue) { return value }
        return defaultValue()
    }

    /// Paste 0x1002cb458: independently decode the old/new observation values.
    public static func f_1002cb458<Value>(old: Any?, new: Any?,
                                        decode: (Any?) -> Value?,
                                        defaultValue: () -> Value) -> (old: Value, new: Value) {
        let oldValue = f_1002ca920(storedValue: old, decode: decode, defaultValue: defaultValue)
        let newValue = f_1002ca920(storedValue: new, decode: decode, defaultValue: defaultValue)
        return (oldValue, newValue)
    }
}
