import AppKit
import PastoCore
import SwiftUI

/// Restores the original explicit suffix truncation; the AppKit label host is an adaptation.
@MainActor
final class OriginalHeadTruncatedLabel: NSTextField {
    private var storedAttributedText: NSAttributedString?

    func setStoredAttributedText(_ value: NSAttributedString) {
        guard storedAttributedText?.isEqual(to: value) != true else { return }
        storedAttributedText = value
        refreshTruncation()
    }

    override func layout() {
        super.layout()
        refreshTruncation()
    }

    private func refreshTruncation() {
        guard let storedAttributedText else { return }
        let fullString = storedAttributedText.string
        guard !fullString.isEmpty else {
            if !attributedStringValue.isEqual(to: storedAttributedText) { attributedStringValue = storedAttributedText }
            if toolTip != nil { toolTip = nil }
            return
        }
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
            if !attributedStringValue.isEqual(to: result) { attributedStringValue = result }
            if toolTip != fullString { toolTip = fullString }
        } else {
            if !attributedStringValue.isEqual(to: storedAttributedText) { attributedStringValue = storedAttributedText }
            if toolTip != nil { toolTip = nil }
        }
    }
}

@MainActor
final class OriginalHeadTruncatedPathView: NSView {
    let label = OriginalHeadTruncatedLabel(labelWithAttributedString: NSAttributedString(string: ""))

    override init(frame frameRect: NSRect) {
        super.init(frame: frameRect)
        addSubview(label)
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    override func layout() {
        super.layout()
        if label.frame != bounds { label.frame = bounds }
    }
}

@MainActor
struct ReplicaHeadTruncatedPath: NSViewRepresentable {
    let path: String

    func makeNSView(context: Context) -> OriginalHeadTruncatedPathView {
        let host = OriginalHeadTruncatedPathView(frame: .zero)
        let view = host.label
        view.maximumNumberOfLines = 2
        view.lineBreakMode = .byCharWrapping
        view.alignment = .center
        view.font = NSFont.preferredFont(forTextStyle: .callout, options: [:])
        view.textColor = OriginalToolbarAppearance.secondaryForeground()
        view.cell?.wraps = true
        view.cell?.usesSingleLineMode = false
        return host
    }

    func updateNSView(_ nsView: OriginalHeadTruncatedPathView, context: Context) {
        nsView.label.setStoredAttributedText(NSAttributedString(string: path, attributes: [
            .font: nsView.label.font ?? NSFont.preferredFont(forTextStyle: .callout, options: [:]),
            .foregroundColor: OriginalToolbarAppearance.secondaryForeground()
        ]))
    }

    func sizeThatFits(_ proposal: ProposedViewSize, nsView: OriginalHeadTruncatedPathView,
                      context: Context) -> CGSize? {
        // Keep NSTextField's width-dependent intrinsic constraints out of the
        // SwiftUI host. Measurement never mutates a live view or forces layout.
        let width = proposal.width.flatMap { $0.isFinite ? max(0, $0) : nil } ?? 0
        let font = nsView.label.font ?? NSFont.preferredFont(forTextStyle: .callout, options: [:])
        let lineHeight = NSLayoutManager().defaultLineHeight(for: font)
        let measured = (path as NSString).boundingRect(with: NSSize(width: width, height: .greatestFiniteMagnitude),
            options: [.usesLineFragmentOrigin, .usesFontLeading], attributes: [.font: font])
        return CGSize(width: width, height: ceil(min(lineHeight * 2, measured.height)))
    }
}
