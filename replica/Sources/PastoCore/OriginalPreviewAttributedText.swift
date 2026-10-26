import AppKit

/// Recovered local attributed-text operations used by the preview content model.
@MainActor
public enum OriginalPreviewAttributedText {
    /// Paste 0x1000f3e48: the platform body font with an empty options dictionary.
    public static func f_1000f3e48() -> NSFont {
        NSFont.preferredFont(forTextStyle: .body, options: [:])
    }

    /// Paste 0x1000f3ef4: the original's fixed editing font, with its nil trap.
    public static func f_1000f3ef4() -> NSFont {
        NSFont(name: "HelveticaNeue", size: 13)!
    }

    /// Paste 0x1000f3f6c: clear traits, apply the requested traits, preserve both fallbacks.
    public static func f_1000f3f6c(font: NSFont,
                                 traits: NSFontDescriptor.SymbolicTraits) -> NSFont {
        let descriptor = font.fontDescriptor
        let cleared = descriptorWithTraits(descriptor, traits: [])
        let requested = cleared.flatMap { descriptorWithTraits($0, traits: traits) }
        return NSFont(descriptor: requested ?? descriptor, size: font.pointSize) ?? font
    }

    // The older build SDK imports this selector as nonnull. The recovered binary
    // explicitly checks both returned descriptors for nil, so retain that ObjC ABI.
    static func descriptorWithTraits(_ descriptor: NSFontDescriptor,
                                             traits: NSFontDescriptor.SymbolicTraits) -> NSFontDescriptor? {
        let selector = NSSelectorFromString("fontDescriptorWithSymbolicTraits:")
        typealias Getter = @convention(c) (NSFontDescriptor, Selector, UInt32) -> Unmanaged<NSFontDescriptor>?
        let getter = unsafeBitCast(descriptor.method(for: selector)!, to: Getter.self)
        return getter(descriptor, selector, traits.rawValue)?.takeUnretainedValue()
    }

    /// Paste 0x100309700: Foundation ranges use the attributed string's UTF-16 length.
    public static func f_100309700(_ source: NSAttributedString) -> NSRange {
        NSRange(location: 0, length: source.length)
    }

    /// Paste 0x100309720: the first nonempty run clears the flag and stops enumeration.
    public static func f_100309720(attributes: [NSAttributedString.Key: Any],
                                  isUnattributed: inout Bool,
                                  stop: UnsafeMutablePointer<ObjCBool>) {
        if !attributes.isEmpty {
            isUnattributed = false
            stop.pointee = true
        }
    }

    /// Paste 0x1003095bc: empty text or text with no attributes is considered plain.
    public static func f_1003095bc(_ source: NSAttributedString) -> Bool {
        var isUnattributed = true
        source.enumerateAttributes(in: f_100309700(source), options: []) { attributes, _, stop in
            f_100309720(attributes: attributes, isUnattributed: &isUnattributed, stop: stop)
        }
        return isUnattributed
    }

    /// Paste 0x100309924: clear text blocks only when a run has a paragraph style.
    public static func f_100309924(attributes: [NSAttributedString.Key: Any], range: NSRange,
                                  destination: NSMutableAttributedString) {
        guard !attributes.isEmpty,
              let paragraph = attributes[.paragraphStyle] as? NSParagraphStyle,
              let mutable = paragraph.mutableCopy() as? NSMutableParagraphStyle else { return }
        mutable.textBlocks = []
        destination.addAttribute(.paragraphStyle, value: mutable, range: range)
    }

    /// Paste 0x1003097c0: return a mutable copy with paragraph table blocks removed.
    public static func f_1003097c0(_ source: NSAttributedString) -> NSMutableAttributedString {
        let result = NSMutableAttributedString(attributedString: source)
        result.enumerateAttributes(in: f_100309700(result), options: []) { attributes, range, _ in
            f_100309924(attributes: attributes, range: range, destination: result)
        }
        return result
    }

    /// Paste 0x1003c1860: retain only the original bold/italic traits and underline/strike.
    public static func f_1003c1860(attributes: [NSAttributedString.Key: Any], range: NSRange,
                                  destination: NSMutableAttributedString) {
        for (key, value) in attributes {
            if key == .font, let font = value as? NSFont {
                let traits = NSFontDescriptor.SymbolicTraits(rawValue: font.fontDescriptor.symbolicTraits.rawValue & 3)
                destination.addAttribute(.font, value: f_1000f3f6c(font: f_1000f3ef4(), traits: traits), range: range)
            } else if key == .underlineStyle || key == .strikethroughStyle {
                destination.addAttribute(key, value: value, range: range)
            }
        }
    }

    /// The editing-text half of 0x1003c05d4, after local source data has been decoded.
    public static func normalizedEditingText(_ source: NSAttributedString) -> NSAttributedString {
        let result = NSMutableAttributedString(string: source.string, attributes: [.font: f_1000f3ef4()])
        result.beginEditing()
        source.enumerateAttributes(in: f_100309700(source), options: []) { attributes, range, _ in
            f_1003c1860(attributes: attributes, range: range, destination: result)
        }
        result.endEditing()
        return result
    }

    /// Paste 0x1003c0be0: nonempty changed text, with the original plain/rich baseline choice.
    public static func f_1003c0be0(candidate: NSAttributedString, original: NSAttributedString,
                                  editing: NSAttributedString) -> Bool {
        guard !candidate.string.isEmpty else { return false }
        return (f_1003095bc(original) ? editing : original) != candidate
    }

    /// PastePlatform's NSTextView.attributedText Objective-C getter, 0x1000f6ef8.
    public static func f_1000f6ef8(editor: NSTextView) -> NSAttributedString {
        f_1000f6fec(editor: editor)
    }

    /// Paste 0x1000f6fec: preserve the actual storage identity; only nil creates empty storage.
    public static func f_1000f6fec(editor: NSTextView) -> NSAttributedString {
        editor.textStorage ?? NSTextStorage(string: "")
    }

    /// PastePlatform's NSTextView.attributedText Objective-C setter, 0x1000f7054.
    @discardableResult
    public static func f_1000f7054(_ value: NSAttributedString, editor: NSTextView) -> Int {
        f_1000f7138(value, editor: editor)
    }

    /// Paste 0x1000f7138: a nil textStorage causes no mutation.
    @discardableResult
    public static func f_1000f7138(_ value: NSAttributedString, editor: NSTextView) -> Int {
        editor.textStorage?.setAttributedString(value)
        return 0
    }

    /// Paste 0x100212ccc: the content getter forwards through the platform category.
    public static func f_100212ccc(editor: NSTextView) -> NSAttributedString {
        f_1000f6ef8(editor: editor)
    }

    /// Paste 0x100215cac: last-character attributes become typingAttributes before content.
    public static func f_100215cac(_ value: NSAttributedString, editor: NSTextView) {
        editor.typingAttributes = value.length < 1 ? [:]
            : value.attributes(at: value.length - 1, effectiveRange: nil)
        f_1000f7054(value, editor: editor)
    }

    /// Paste 0x100212e78: the public TextEditor attributed-text setter returns zero.
    @discardableResult
    public static func f_100212e78(_ value: NSAttributedString, editor: NSTextView) -> Int {
        f_100215cac(value, editor: editor)
        return 0
    }

    /// Paste 0x1003eb330: the two actual isEditable reads select content and plain styling.
    @discardableResult
    public static func f_1003eb330(original: NSAttributedString, editing: NSAttributedString,
                                  editor: NSTextView) -> Int {
        var displayed = editor.isEditable ? editing : original
        if !editor.isEditable, f_1003095bc(original) {
            let plain = NSMutableAttributedString(attributedString: displayed)
            let range = f_100309700(plain)
            plain.removeAttribute(.foregroundColor, range: range)
            plain.removeAttribute(.backgroundColor, range: range)
            displayed = plain
        }
        f_100212e78(displayed, editor: editor)
        return 0
    }
}
