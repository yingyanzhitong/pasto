import AppKit
import PastoCore
import SwiftUI

/// The unsupported-content tree belongs to the full preview, not the compact card.
@MainActor
final class OriginalUnavailablePreviewContentView: NSView {
    override init(frame frameRect: NSRect) {
        super.init(frame: frameRect)

        let imageView = NSImageView(frame: .zero)
        if NSImage(systemSymbolName: "exclamationmark.triangle", accessibilityDescription: nil) == nil {
            imageView.image = NSImage(systemSymbolName: "questionmark.square", accessibilityDescription: nil)!
        } else {
            imageView.image = NSImage(systemSymbolName: "exclamationmark.triangle", accessibilityDescription: nil)!
        }
        imageView.contentTintColor = OriginalToolbarAppearance.secondaryLabelForeground()
        imageView.imageScaling = .scaleProportionallyUpOrDown

        let title = NSTextField(frame: .zero)
        title.stringValue = String(localized: OriginalUnavailablePreviewLocalization.f_1001daf54())
        let titleFont = OriginalSearchAppearance.f_1001ff964(style: .title2)
        title.font = NSFont.systemFont(ofSize: titleFont.pointSize, weight: .medium)
        title.alignment = .center
        title.isEditable = false
        title.isSelectable = false
        title.isBordered = false
        title.drawsBackground = false

        let subtitle = NSTextField(frame: .zero)
        subtitle.stringValue = String(localized: OriginalUnavailablePreviewLocalization.f_1001dadd4())
        subtitle.textColor = OriginalToolbarAppearance.secondaryForeground()
        subtitle.maximumNumberOfLines = 0
        subtitle.alignment = .center
        subtitle.font = OriginalSearchAppearance.f_1001ff928()
        subtitle.isEditable = false
        subtitle.isSelectable = false
        subtitle.isBordered = false
        subtitle.drawsBackground = false
        subtitle.setContentCompressionResistancePriority(.init(250), for: .horizontal)

        let information = NSStackView(views: [title, subtitle])
        information.orientation = .vertical
        information.spacing = 4
        let stack = NSStackView(views: [imageView, information])
        stack.orientation = .vertical
        stack.spacing = 16
        addSubview(stack)
        stack.translatesAutoresizingMaskIntoConstraints = false
        imageView.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            stack.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 48),
            stack.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -48),
            stack.centerYAnchor.constraint(equalTo: centerYAnchor),
            imageView.widthAnchor.constraint(equalToConstant: 60),
            imageView.heightAnchor.constraint(equalToConstant: 60)
        ])
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }
}

@MainActor
struct OriginalUnavailablePreviewContent: NSViewRepresentable {
    func makeNSView(context: Context) -> OriginalUnavailablePreviewContentView {
        OriginalUnavailablePreviewContentView(frame: .zero)
    }

    func updateNSView(_ nsView: OriginalUnavailablePreviewContentView, context: Context) {}
}
