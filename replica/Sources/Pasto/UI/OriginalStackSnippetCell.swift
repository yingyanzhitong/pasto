import AppKit
import PastoCore
import SwiftUI

@MainActor
struct OriginalStackSnippetCellView: NSViewRepresentable {
    let item: ClipboardItem
    let imageProvider: (ClipboardItem) -> NSImage?

    func makeNSView(context: Context) -> OriginalStackSnippetCell {
        OriginalStackSnippetCell(imageProvider: imageProvider)
    }

    func updateNSView(_ view: OriginalStackSnippetCell, context: Context) {
        view.imageProvider = imageProvider
        view.f_1000519f8(item)
    }
}

@MainActor
final class OriginalStackSnippetCell: NSTableCellView {
    var imageProvider: (ClipboardItem) -> NSImage?

    init(imageProvider: @escaping (ClipboardItem) -> NSImage?) {
        self.imageProvider = imageProvider
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

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    /// Paste 0x1000519f8: update only the outlets that exist, in the original order.
    func f_1000519f8(_ item: ClipboardItem) {
        if let imageView { imageView.image = imageProvider(item) }
        textField?.maximumNumberOfLines = 2
        if let textField { textField.stringValue = OriginalStackSnippetText.f_100051ec8(item) }
    }
}
