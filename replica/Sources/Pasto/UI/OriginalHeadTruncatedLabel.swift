import AppKit
import PastoCore
import SwiftUI

/// Restores the original explicit suffix truncation; the AppKit label host is an adaptation.
@MainActor
final class OriginalHeadTruncatedLabel: NSTextField {
    private var storedAttributedText: NSAttributedString?

    func setStoredAttributedText(_ value: NSAttributedString) {
        attributedStringValue = value
        storedAttributedText = value
        refreshTruncation()
    }

    override func layout() {
        super.layout()
        refreshTruncation()
    }

    private func refreshTruncation() {
        lineBreakMode = .byCharWrapping
        guard let storedAttributedText else { return }
        let fullString = storedAttributedText.string
        guard !fullString.isEmpty else { return }
        let measureFont = font ?? NSFont.preferredFont(forTextStyle: .body, options: [:])
        let slashWidth = ("/" as NSString).size(withAttributes: [.font: measureFont]).width
        let capacity = Int(floor(bounds.width / slashWidth)) * maximumNumberOfLines
        let characterCount = fullString.count
        if capacity < characterCount {
            let result = NSMutableAttributedString(string: "…",
                attributes: storedAttributedText.attributes(at: 0, effectiveRange: nil))
            // The original mixes Character.count offsets with an attributed UTF-16 range.
            result.append(storedAttributedText.attributedSubstring(from:
                NSRange(location: characterCount - capacity, length: capacity)))
            attributedStringValue = result
            toolTip = fullString
        } else {
            attributedStringValue = storedAttributedText
            toolTip = nil
        }
    }
}

@MainActor
struct ReplicaHeadTruncatedPath: NSViewRepresentable {
    let path: String

    func makeNSView(context: Context) -> OriginalHeadTruncatedLabel {
        let view = OriginalHeadTruncatedLabel(labelWithAttributedString: NSAttributedString(string: ""))
        view.maximumNumberOfLines = 2
        view.alignment = .center
        view.font = NSFont.preferredFont(forTextStyle: .callout, options: [:])
        view.textColor = OriginalToolbarAppearance.secondaryForeground()
        view.cell?.wraps = true
        view.cell?.usesSingleLineMode = false
        view.setContentCompressionResistancePriority(.required, for: .vertical)
        view.setContentHuggingPriority(.required, for: .vertical)
        return view
    }

    func updateNSView(_ nsView: OriginalHeadTruncatedLabel, context: Context) {
        nsView.setStoredAttributedText(NSAttributedString(string: path, attributes: [
            .font: nsView.font ?? NSFont.preferredFont(forTextStyle: .callout, options: [:]),
            .foregroundColor: OriginalToolbarAppearance.secondaryForeground()
        ]))
    }

    func sizeThatFits(_ proposal: ProposedViewSize, nsView: OriginalHeadTruncatedLabel,
                      context: Context) -> CGSize? {
        guard let width = proposal.width else { return nil }
        nsView.setFrameSize(NSSize(width: width, height: nsView.frame.height))
        nsView.needsLayout = true
        nsView.layoutSubtreeIfNeeded()
        nsView.preferredMaxLayoutWidth = width
        return nsView.sizeThatFits(NSSize(width: width, height: .greatestFiniteMagnitude))
    }
}
