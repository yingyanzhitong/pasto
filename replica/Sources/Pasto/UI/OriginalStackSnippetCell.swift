import AppKit
import PastoCore
import SwiftUI

@MainActor
struct OriginalStackSnippetCellView: NSViewRepresentable {
    let input: ClipboardRestoreItem
    let imageProvider: (ClipboardRestoreItem) -> NSImage?

    init(input: ClipboardRestoreItem, imageProvider: @escaping (ClipboardRestoreItem) -> NSImage?) {
        self.input = input
        self.imageProvider = imageProvider
    }

    init(item: ClipboardItem, imageProvider: @escaping (ClipboardItem) -> NSImage?) {
        input = ClipboardRestoreItem(item: item)
        self.imageProvider = { imageProvider($0.resolvedItem()) }
    }

    func makeNSView(context: Context) -> OriginalStackSnippetCell {
        OriginalStackSnippetCell(nativeImageProvider: imageProvider)
    }

    func updateNSView(_ view: OriginalStackSnippetCell, context: Context) {
        view.nativeImageProvider = imageProvider
        view.updateNativeSnippet(input)
    }
}

@MainActor
final class OriginalStackSnippetCell: NSTableCellView {
    var nativeImageProvider: (ClipboardRestoreItem) -> NSImage?

    convenience init(imageProvider: @escaping (ClipboardItem) -> NSImage?) {
        self.init(nativeImageProvider: { imageProvider($0.resolvedItem()) })
    }

    init(nativeImageProvider: @escaping (ClipboardRestoreItem) -> NSImage?) {
        self.nativeImageProvider = nativeImageProvider
        super.init(frame: .zero)
        // Retain the replica's existing row dimensions; the original Nib layout is separate.
        let icon = NSImageView(frame: .zero)
        icon.imageScaling = .scaleProportionallyUpOrDown
        let label = NSTextField(labelWithString: "")
        label.font = .systemFont(ofSize: 12)
        label.lineBreakMode = .byTruncatingTail
        label.cell?.wraps = true
        label.cell?.isScrollable = false
        for view in [icon, label] {
            view.translatesAutoresizingMaskIntoConstraints = false
            addSubview(view)
        }
        imageView = icon
        textField = label
        NSLayoutConstraint.activate([
            icon.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 10),
            icon.centerYAnchor.constraint(equalTo: centerYAnchor),
            icon.widthAnchor.constraint(equalToConstant: 24),
            icon.heightAnchor.constraint(equalToConstant: 24),
            label.leadingAnchor.constraint(equalTo: icon.trailingAnchor, constant: 8),
            label.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -10),
            label.centerYAnchor.constraint(equalTo: centerYAnchor),
            label.topAnchor.constraint(greaterThanOrEqualTo: topAnchor),
            label.bottomAnchor.constraint(lessThanOrEqualTo: bottomAnchor)
        ])
    }

    required init?(coder: NSCoder) {
        nativeImageProvider = { input in
            let rawType = input.previewRawType() ?? 0
            return OriginalStackCategoryIcons.image(for:
                OriginalPasteboardContentKind(rawValue: UInt8(rawType)) ?? .unknown)
        }
        super.init(coder: coder)
    }

    /// Paste 0x1000519f8: update only the outlets that exist, in the original order.
    func f_1000519f8(_ item: ClipboardItem) {
        updateNativeSnippet(ClipboardRestoreItem(item: item))
    }

    func updateNativeSnippet(_ input: ClipboardRestoreItem) {
        if let imageView { imageView.image = nativeImageProvider(input) }
        textField?.maximumNumberOfLines = 2
        if let textField { textField.stringValue = OriginalStackSnippetText.text(for: input) }
    }
}
