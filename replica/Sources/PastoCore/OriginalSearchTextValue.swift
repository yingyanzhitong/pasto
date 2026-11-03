import AppKit

public extension NSTextView {
    @MainActor func f_1000f7254() -> String { string }

    /// Pasto's independent plain-text setter, matching the observed String → setString: effect.
    /// The original Swift declaration and caller binding remain unconfirmed.
    @MainActor func f_1000f733c(_ value: String) {
        string = value
    }
}
