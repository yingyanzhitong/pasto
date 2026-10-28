import AppKit
import UniformTypeIdentifiers

@MainActor
public enum OriginalTextPreviewSubmission {
    /// Paste 0x1003c14d0: only emphasis traits and the two style keys require RTF.
    public static func f_1003c14d0(attributes: [NSAttributedString.Key: Any],
                                  isRich: inout Bool, stop: UnsafeMutablePointer<ObjCBool>) {
        for (key, value) in attributes {
            if key == .font, let font = value as? NSFont {
                if font.fontDescriptor.symbolicTraits.rawValue & 3 == 0 { continue }
            } else if key != .underlineStyle && key != .strikethroughStyle {
                continue
            }
            isRich = true
            stop.pointee = true
            return
        }
    }

    /// The value preparation in Paste 0x1003c0e50, including the optional RTF result.
    public static func makeItem(_ content: NSAttributedString) -> OriginalPasteboardItem {
        var isRich = false
        content.enumerateAttributes(in: NSRange(location: 0, length: content.length), options: []) { attributes, _, stop in
            f_1003c14d0(attributes: attributes, isRich: &isRich, stop: stop)
        }
        guard isRich else { return OriginalPasteboardItem.f_10037c6d4(content.string) }
        let item = OriginalPasteboardItem()
        item.f_10037d8c8(OriginalPasteboardRestore.f_100381fdc(content), forType: UTType.rtf.identifier)
        item.f_10037c4a8(content.string, forType: UTType.utf8PlainText.identifier)
        return item
    }
}
