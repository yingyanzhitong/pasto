import AppKit
import PastoCore
import SwiftUI

@MainActor
final class ReplicaRichTextDocument: NSObject, ObservableObject, NSTextViewDelegate {
    enum Format { case bold, italic, underline, strikethrough }
    @Published private(set) var content: NSAttributedString
    @Published private(set) var bold = false
    @Published private(set) var italic = false
    @Published private(set) var underlined = false
    @Published private(set) var struck = false
    weak var textView: NSTextView?
    var usesRecoveredContentEvents = false
    var onRecoveredTraitsChange: ((Set<OriginalPreviewTextTraits.Trait>) -> Void)?

    init(content: NSAttributedString) {
        self.content = NSAttributedString(attributedString: content)
        super.init()
    }

    var characterCount: Int { content.string.count }
    var wordCount: Int { content.string.split(whereSeparator: \.isWhitespace).count }
    var lineCount: Int {
        guard !content.string.isEmpty else { return 0 }
        return content.string.replacingOccurrences(of: "\r\n", with: "\n")
            .replacingOccurrences(of: "\r", with: "\n").components(separatedBy: "\n").count
    }

    func textDidChange(_ notification: Notification) {
        guard !usesRecoveredContentEvents else { return }
        guard let view = notification.object as? NSTextView else { return }
        content = NSAttributedString(attributedString: view.attributedString())
        updateFormatting()
    }

    func textViewDidChangeSelection(_ notification: Notification) {
        if !usesRecoveredContentEvents { updateFormatting() }
    }

    func updateFormatting() {
        guard !usesRecoveredContentEvents else { return }
        guard let view = textView else { return }
        let range = view.selectedRange()
        let attributes: [NSAttributedString.Key: Any]
        if range.length > 0, range.location < view.textStorage?.length ?? 0 {
            attributes = view.textStorage?.attributes(at: range.location, effectiveRange: nil) ?? view.typingAttributes
        } else { attributes = view.typingAttributes }
        let font = attributes[.font] as? NSFont ?? .systemFont(ofSize: 14)
        let traits = NSFontManager.shared.traits(of: font)
        bold = traits.contains(.boldFontMask)
        italic = traits.contains(.italicFontMask)
        underlined = (attributes[.underlineStyle] as? Int ?? 0) != 0
        struck = (attributes[.strikethroughStyle] as? Int ?? 0) != 0
    }

    func applyRecoveredTraits(_ traits: Set<OriginalPreviewTextTraits.Trait>) {
        bold = OriginalPreviewTextTraits.f_100208290(.bold, in: traits)
        italic = OriginalPreviewTextTraits.f_100208290(.italic, in: traits)
        underlined = OriginalPreviewTextTraits.f_100208290(.underline, in: traits)
        struck = OriginalPreviewTextTraits.f_100208290(.strikethrough, in: traits)
        onRecoveredTraitsChange?(traits)
    }

    func receiveRecoveredContent(_ value: NSAttributedString) {
        content = NSAttributedString(attributedString: value)
    }

    func toggle(_ format: Format) {
        guard let view = textView else { return }
        if usesRecoveredContentEvents {
            let trait: OriginalPreviewTextTraits.Trait
            switch format {
            case .bold: trait = .bold
            case .italic: trait = .italic
            case .underline: trait = .underline
            case .strikethrough: trait = .strikethrough
            }
            OriginalPreviewTextTraits.f_1002072a0(trait, editor: view)
            return
        }
        view.window?.makeFirstResponder(view)
        let range = view.selectedRange()
        let enable: Bool
        switch format {
        case .bold: enable = !bold
        case .italic: enable = !italic
        case .underline: enable = !underlined
        case .strikethrough: enable = !struck
        }
        if range.length == 0 {
            var attributes = view.typingAttributes
            change(&attributes, format: format, enable: enable)
            view.typingAttributes = attributes
        } else if let storage = view.textStorage, NSMaxRange(range) <= storage.length {
            let selection = NSMutableAttributedString(attributedString: storage.attributedSubstring(from: range))
            selection.enumerateAttributes(in: NSRange(location: 0, length: selection.length)) { attributes, run, _ in
                var attributes = attributes
                change(&attributes, format: format, enable: enable)
                selection.setAttributes(attributes, range: run)
            }
            // NSTextView's input path retains native undo, validation and delegate notifications.
            view.insertText(selection, replacementRange: range)
            view.setSelectedRange(range)
        }
        if !usesRecoveredContentEvents { content = NSAttributedString(attributedString: view.attributedString()) }
        updateFormatting()
    }

    private func change(_ attributes: inout [NSAttributedString.Key: Any], format: Format, enable: Bool) {
        switch format {
        case .bold, .italic:
            let trait: NSFontTraitMask = format == .bold ? .boldFontMask : .italicFontMask
            let font = attributes[.font] as? NSFont ?? .systemFont(ofSize: 14)
            attributes[.font] = enable ? NSFontManager.shared.convert(font, toHaveTrait: trait)
                : NSFontManager.shared.convert(font, toNotHaveTrait: trait)
        case .underline: attributes[.underlineStyle] = enable ? NSUnderlineStyle.single.rawValue : 0
        case .strikethrough: attributes[.strikethroughStyle] = enable ? NSUnderlineStyle.single.rawValue : 0
        }
    }
}

@MainActor
private final class ReplicaRichTextView: NSTextView {
    weak var document: ReplicaRichTextDocument?
    var saveAction: (() -> Void)?
    override func performKeyEquivalent(with event: NSEvent) -> Bool {
        if event.modifierFlags.contains(.command) {
            switch event.charactersIgnoringModifiers?.lowercased() {
            case "b": document?.toggle(.bold); return true
            case "i": document?.toggle(.italic); return true
            case "u": document?.toggle(.underline); return true
            case "s": saveAction?(); return true
            default: break
            }
        }
        return super.performKeyEquivalent(with: event)
    }
}

@MainActor
struct ReplicaRichTextInput: NSViewRepresentable {
    @ObservedObject var document: ReplicaRichTextDocument
    let save: () -> Void

    func makeNSView(context: Context) -> NSScrollView {
        let scroll = NSScrollView()
        scroll.hasVerticalScroller = true
        scroll.autohidesScrollers = true
        scroll.hasHorizontalScroller = false
        scroll.borderType = .noBorder
        scroll.backgroundColor = .textBackgroundColor
        let text = ReplicaRichTextView(frame: NSRect(x: 0, y: 0, width: 490, height: 284))
        text.isRichText = true
        text.isEditable = true
        text.isSelectable = true
        text.allowsUndo = true
        text.isVerticallyResizable = true
        text.isHorizontallyResizable = false
        text.autoresizingMask = [.width]
        text.minSize = .zero
        text.maxSize = NSSize(width: CGFloat.greatestFiniteMagnitude, height: CGFloat.greatestFiniteMagnitude)
        text.textContainer?.containerSize = NSSize(width: 490, height: CGFloat.greatestFiniteMagnitude)
        text.textContainer?.widthTracksTextView = true
        text.textContainerInset = NSSize(width: 8, height: 8)
        text.font = .systemFont(ofSize: 14)
        text.textColor = .textColor
        text.backgroundColor = .textBackgroundColor
        text.usesAdaptiveColorMappingForDarkAppearance = true
        text.textStorage?.setAttributedString(document.content)
        text.typingAttributes = [.font: NSFont.systemFont(ofSize: 14), .foregroundColor: NSColor.textColor]
        text.document = document
        text.saveAction = save
        text.delegate = document
        text.setAccessibilityLabel("富文本内容")
        document.textView = text
        scroll.documentView = text
        DispatchQueue.main.async { [weak text] in
            guard let text else { return }
            text.window?.makeFirstResponder(text)
        }
        return scroll
    }

    func updateNSView(_ nsView: NSScrollView, context: Context) {
        (nsView.documentView as? ReplicaRichTextView)?.saveAction = save
    }

    static func dismantleNSView(_ nsView: NSScrollView, coordinator: ()) {
        guard let text = nsView.documentView as? ReplicaRichTextView else { return }
        text.delegate = nil
        text.saveAction = nil
    }
}
