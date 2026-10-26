import AppKit
import PastoCore
import SwiftUI

@MainActor
final class OriginalCompactTextContentView: NSView {
    private let label = NSTextField(labelWithAttributedString: NSAttributedString(string: ""))

    override init(frame frameRect: NSRect) {
        super.init(frame: frameRect)
        label.maximumNumberOfLines = 0
        label.alignment = .natural
        label.textColor = OriginalSearchAppearance.f_1001fec18()
        label.font = OriginalPreviewAttributedText.f_1000f3e48()
        label.translatesAutoresizingMaskIntoConstraints = false
        addSubview(label)
        NSLayoutConstraint.activate([
            label.leadingAnchor.constraint(equalTo: leadingAnchor),
            label.trailingAnchor.constraint(equalTo: trailingAnchor),
            label.topAnchor.constraint(equalTo: topAnchor),
            label.bottomAnchor.constraint(lessThanOrEqualTo: bottomAnchor, constant: 10)
        ])
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    func update(text: AttributedString) {
        appearance = OriginalCompactTextCardAppearance.appearance(
            for: OriginalCompactTextCardAppearance.background(for: text))
        label.attributedStringValue = NSAttributedString(text)
    }
}

@MainActor
struct OriginalCompactTextContent: NSViewRepresentable {
    let text: AttributedString

    func makeNSView(context: Context) -> OriginalCompactTextContentView {
        let view = OriginalCompactTextContentView(frame: .zero)
        view.update(text: text)
        return view
    }

    func updateNSView(_ nsView: OriginalCompactTextContentView, context: Context) {
        nsView.update(text: text)
    }
}
