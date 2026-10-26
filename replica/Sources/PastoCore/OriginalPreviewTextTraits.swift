import AppKit

/// TextEditor uses a union of all selected runs, not the first run's attributes.
@MainActor
public enum OriginalPreviewTextTraits {
    public enum Trait: UInt8, Hashable, Sendable { case bold = 0, italic = 1, underline = 2, strikethrough = 3 }

    public static func f_100207db8(_ attributes: [NSAttributedString.Key: Any]) -> Set<Trait> {
        var result: Set<Trait> = []
        if let font = attributes[.font] as? NSFont {
            let traits = font.fontDescriptor.symbolicTraits
            if traits.contains(.bold) { result.insert(.bold) }
            if traits.contains(.italic) { result.insert(.italic) }
        }
        if let underline = attributes[.underlineStyle] as? Int, underline == 1 { result.insert(.underline) }
        if let strike = attributes[.strikethroughStyle] as? Int, strike == 1 { result.insert(.strikethrough) }
        return result
    }

    public static func f_100208290(_ trait: Trait, in traits: Set<Trait>) -> Bool {
        traits.contains(trait)
    }

    public static func f_1002080e0(_ traits: Set<Trait>, accumulating result: inout Set<Trait>) {
        result.formUnion(traits)
    }

    public static func f_100208024(_ attributes: [NSAttributedString.Key: Any],
                                  accumulating result: inout Set<Trait>) {
        f_1002080e0(f_100207db8(attributes), accumulating: &result)
    }

    public static func f_1002085e0(_ attributes: [NSAttributedString.Key: Any],
                                  accumulating result: inout Set<Trait>) {
        f_100208024(attributes, accumulating: &result)
    }

    public static func f_100207b54(editor: NSTextView) -> Set<Trait> {
        let range = editor.selectedRange()
        let content = OriginalPreviewAttributedText.f_1000f6ef8(editor: editor)
        if range.location <= content.length {
            let end = range.location + range.length
            if end <= content.length, editor.selectedRange().length != 0 {
                var traits: Set<Trait> = []
                let selectedContent = OriginalPreviewAttributedText.f_1000f6ef8(editor: editor)
                selectedContent.enumerateAttributes(in: editor.selectedRange(), options: []) { attributes, _, _ in
                    f_1002085e0(attributes, accumulating: &traits)
                }
                return traits
            }
        }
        return f_100207db8(editor.typingAttributes)
    }

    /// The second flag forces removal; false toggles according to this run's attributes.
    public static func f_100207648(_ trait: Trait, forceRemove: Bool,
                                   attributes: [NSAttributedString.Key: Any]) -> [NSAttributedString.Key: Any] {
        let remove = forceRemove || f_100208290(trait, in: f_100207db8(attributes))
        var result = attributes
        switch trait {
        case .underline, .strikethrough:
            let key: NSAttributedString.Key = trait == .underline ? .underlineStyle : .strikethroughStyle
            if remove { result.removeValue(forKey: key) }
            else { result[key] = 1 }
        case .bold, .italic:
            guard let font = attributes[.font] as? NSFont else { return result }
            let descriptor = font.fontDescriptor
            let mask: NSFontDescriptor.SymbolicTraits = trait == .bold ? .bold : .italic
            let traits = remove ? descriptor.symbolicTraits.subtracting(mask) : descriptor.symbolicTraits.union(mask)
            let cleared = OriginalPreviewAttributedText.descriptorWithTraits(descriptor, traits: [])
            let changed = cleared.flatMap { OriginalPreviewAttributedText.descriptorWithTraits($0, traits: traits) }
            if let changedFont = NSFont(descriptor: changed ?? descriptor, size: font.pointSize) {
                result[.font] = changedFont
            } else { result.removeValue(forKey: .font) }
        }
        return result
    }

    @discardableResult
    public static func f_1002083e4(_ attributes: [NSAttributedString.Key: Any], range: NSRange,
                                   storage: NSTextStorage, trait: Trait, forceRemove: Bool) -> Int {
        for key in attributes.keys { storage.removeAttribute(key, range: range) }
        storage.addAttributes(f_100207648(trait, forceRemove: forceRemove, attributes: attributes), range: range)
        return 0
    }

    public static func f_1002072a0(_ trait: Trait, editor: NSTextView, range requestedRange: NSRange? = nil) {
        let range = requestedRange ?? editor.selectedRange()
        if range.length < 1 {
            editor.typingAttributes = f_100207648(trait, forceRemove: false, attributes: editor.typingAttributes)
        } else if let storage = editor.textStorage {
            let first = storage.attributes(at: range.location, effectiveRange: nil)
            let forceRemove = f_100208290(trait, in: f_100207db8(first))
            storage.beginEditing()
            storage.enumerateAttributes(in: range, options: []) { attributes, run, _ in
                f_1002083e4(attributes, range: run, storage: storage, trait: trait, forceRemove: forceRemove)
            }
            storage.endEditing()
        }
        editor.undoManager?.registerUndo(withTarget: editor) { [weak editor] _ in
            MainActor.assumeIsolated {
                guard let editor else { return }
                f_1002072a0(trait, editor: editor, range: range)
            }
        }
    }
}

/// Bridges the two original asynchronous paths without synthesizing text-change
/// notifications for typing-attribute changes.
@MainActor
public final class OriginalPreviewTextStorageBridge: NSObject, NSTextStorageDelegate {
    public var onTraitsChange: ((Set<OriginalPreviewTextTraits.Trait>) -> Void)?
    public var onAttributedTextChange: ((NSAttributedString) -> Void)?
    private weak var editor: NSTextView?
    private var typingAttributesObserver: NSKeyValueObservation?

    public init(editor: NSTextView) {
        self.editor = editor
        super.init()
        f_100213780(editor: editor)
        // Original 0x100213cb0 passes options=1 (.new), without .initial.
        typingAttributesObserver = editor.observe(\.typingAttributes, options: [.new]) { [weak self] _, _ in
            Task { @MainActor [weak self] in self?.f_100213fe8() }
        }
    }

    @discardableResult
    public func f_100213780(editor: NSTextView) -> Int {
        editor.isEditable = false
        editor.font = OriginalPreviewAttributedText.f_1000f3ef4()
        editor.textContainerInset = NSSize(width: 8, height: 10)
        editor.isSelectable = true
        editor.allowsUndo = true
        editor.linkTextAttributes = [.cursor: NSCursor.pointingHand]
        editor.autoresizingMask = [.width]
        editor.textStorage?.delegate = self
        return 0
    }

    @discardableResult
    public func f_100213fe8() -> Bool {
        guard let editor else { return true }
        onTraitsChange?(OriginalPreviewTextTraits.f_100207b54(editor: editor))
        return false
    }

    public func f_100214704() {
        if let editor { onTraitsChange?(OriginalPreviewTextTraits.f_100207b54(editor: editor)) }
        // The original reloads its weak owner before invoking the content callback.
        if let editor { onAttributedTextChange?(OriginalPreviewAttributedText.f_1000f6ef8(editor: editor)) }
    }

    public func f_10021453c() {
        Task { @MainActor [weak self] in self?.f_100214704() }
    }

    nonisolated public func textStorage(_ textStorage: NSTextStorage, didProcessEditing editedMask: NSTextStorageEditActions,
                            range editedRange: NSRange, changeInLength delta: Int) {
        MainActor.assumeIsolated { f_10021453c() }
    }
}
