import AppKit

/// REA 0x10004867c: dispatch the two SearchField command selectors to optional
/// callbacks. Callback storage is supplied explicitly instead of the original x20 self.
@MainActor public enum OriginalSearchCommands {
    public static func f_10004867c(selector: Selector, onEnter: (() -> Void)?, onCancel: (() -> Void)?) -> Bool {
        if selector == NSSelectorFromString("insertNewline:") {
            onEnter?()
            return true
        }
        if selector == NSSelectorFromString("cancelOperation:") {
            onCancel?()
            return true
        }
        return false
    }
}
