import AppKit
import PastoCore
import SwiftUI

/// The image card's size label uses the original material overlay, not a bare caption.
@MainActor
struct OriginalImageSizeBadge: NSViewRepresentable {
    let text: String

    func makeNSView(context: Context) -> OriginalImageSizeBadgeView {
        OriginalImageSizeBadgeView(text: text)
    }

    func updateNSView(_ nsView: OriginalImageSizeBadgeView, context: Context) {
        nsView.update(text: text)
    }

    func sizeThatFits(_ proposal: ProposedViewSize, nsView: OriginalImageSizeBadgeView,
                      context: Context) -> CGSize? {
        nsView.intrinsicContentSize
    }
}

@MainActor
final class OriginalImageSizeBadgeView: OriginalLayerBackedView {
    private let label = NSTextField(labelWithString: "")

    init(text: String) {
        super.init(frame: .zero)
        let material = NSVisualEffectView()
        material.blendingMode = .withinWindow
        material.material = .popover
        label.alignment = .center
        label.font = NSFont.preferredFont(forTextStyle: .callout, options: [:])
        label.textColor = OriginalToolbarAppearance.secondaryForeground()
        OriginalViewLayerFunctions.f_10021d49c(4, curve: .circular, view: self)
        for child in [material, label] {
            child.translatesAutoresizingMaskIntoConstraints = false
            addSubview(child)
        }
        NSLayoutConstraint.activate([
            material.topAnchor.constraint(equalTo: topAnchor),
            material.leadingAnchor.constraint(equalTo: leadingAnchor),
            material.bottomAnchor.constraint(equalTo: bottomAnchor),
            material.trailingAnchor.constraint(equalTo: trailingAnchor),
            heightAnchor.constraint(greaterThanOrEqualTo: label.heightAnchor),
            label.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 4),
            label.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -4),
            label.centerYAnchor.constraint(equalTo: centerYAnchor)
        ])
        update(text: text)
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    override var intrinsicContentSize: NSSize {
        NSSize(width: label.intrinsicContentSize.width + 8, height: 19)
    }

    func update(text: String) {
        label.stringValue = text
        invalidateIntrinsicContentSize()
    }
}
