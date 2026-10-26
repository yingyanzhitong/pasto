import AppKit

/// SearchField.swift delegate contracts recovered from REA. Swift object and
/// closure storage replaces the original optimized x20 context and bridge calls.
@MainActor public final class OriginalSearchEditing: NSObject, NSTextViewDelegate {
    public var onTextShouldChange: ((NSAttributedString, NSRange) -> Bool)?
    public var onSelectionChange: ((NSRange) -> Void)?
    public var onEndEditing: (() -> Void)?
    public var onEnter: (() -> Void)?
    public var onCancel: (() -> Void)?
    private let inputTextView: NSTextView

    public init(textView: NSTextView) {
        inputTextView = textView
        super.init()
    }

    /// The original helper reads the first scalar of a Character's StringGuts.
    /// Returning an Optional preserves its empty-string discriminator without
    /// exposing the original packed Swift ABI representation.
    public static func f_1000482c8(_ value: String) -> Unicode.Scalar? {
        value.unicodeScalars.first
    }

    public func f_10004795c(textView: NSTextView, range: NSRange, replacementString: String?) -> Bool {
        guard let storage = textView.textStorage else { return false }
        var replacement = replacementString ?? ""
        let containsNewline = replacement.contains { character in
            guard let scalar = Self.f_1000482c8(String(character)) else { preconditionFailure() }
            let value = scalar.value
            return (10...13).contains(value) || (0x2028...0x2029).contains(value) || value == 0x85
        }
        if containsNewline {
            // REA explicitly replaces LF and CR only. The other newline scalars
            // trigger this branch but remain unchanged in the proposed string.
            replacement = replacement.replacingOccurrences(of: "\n", with: " ")
                .replacingOccurrences(of: "\r", with: " ")
        }
        if replacement.isEmpty, range.length == 1,
           storage.attribute(.attachment, at: range.location, effectiveRange: nil) != nil,
           textView.selectedRange() != range {
            textView.setSelectedRange(range)
            return false
        }
        let proposed = NSMutableAttributedString(attributedString: storage)
        proposed.replaceCharacters(in: range, with: replacement)
        let selection = NSRange(location: range.location + (replacement as NSString).length, length: 0)
        // The callback receives a proposal; this function does not mutate storage.
        // Its absence allows the original edit, even if the proposal was normalized.
        return onTextShouldChange?(proposed, selection) ?? true
    }

    public func f_100047d8c(textView: NSTextView, range: NSRange, replacementString: String?) -> Bool {
        f_10004795c(textView: textView, range: range, replacementString: replacementString)
    }

    public func f_100047ea4(_ notification: Notification) {
        onSelectionChange?(inputTextView.selectedRange())
    }

    public func f_100048058(selector: Selector) -> Bool {
        OriginalSearchCommands.f_10004867c(selector: selector, onEnter: onEnter, onCancel: onCancel)
    }

    public func f_100048128(_ notification: Notification) {
        onEndEditing?()
    }

    public func textView(_ textView: NSTextView, shouldChangeTextIn affectedCharRange: NSRange,
                         replacementString: String?) -> Bool {
        f_100047d8c(textView: textView, range: affectedCharRange, replacementString: replacementString)
    }

    public func textViewDidChangeSelection(_ notification: Notification) {
        f_100047ea4(notification)
    }

    public func textView(_ textView: NSTextView, doCommandBy commandSelector: Selector) -> Bool {
        f_100048058(selector: commandSelector)
    }

    public func textDidEndEditing(_ notification: Notification) {
        f_100048128(notification)
    }
}
