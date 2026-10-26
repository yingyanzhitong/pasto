import AppKit

/// The original PastePlatform NSView category's UIKit-compatible layout method.
@MainActor
public enum OriginalPreviewPlatformView {
    public static func f_1000f74b8(_ view: NSView) {
        view.layoutSubtreeIfNeeded()
    }
}

@MainActor
public final class OriginalPreviewTextMetaView: NSView {
    public init(text: String) {
        super.init(frame: .zero)
        let characters = Int32(exactly: text.count)!
        let words = Int32(exactly: text.isEmpty ? 0 : text.components(separatedBy: .whitespaces).filter { !$0.isEmpty }.count)!
        let lines = Int32(exactly: text.isEmpty ? 0 : text.components(separatedBy: .newlines).count)!
        let titles = [
            String(localized: OriginalPreviewLocalization.f_1001e6b38(characters)),
            String(localized: OriginalPreviewLocalization.f_1001e6b78(words)),
            String(localized: OriginalPreviewLocalization.f_1001e6b58(lines))
        ]
        var views: [NSView] = []
        for title in titles {
            if !views.isEmpty { views.append(Self.f_1002127a4()) }
            let label = NSTextField(labelWithString: title)
            label.textColor = OriginalToolbarAppearance.secondaryForeground()
            label.font = .monospacedDigitSystemFont(
                ofSize: NSFont.preferredFont(forTextStyle: .body, options: [:]).pointSize, weight: .regular)
            views.append(label)
        }
        let stack = NSStackView(views: views)
        stack.spacing = 8
        stack.translatesAutoresizingMaskIntoConstraints = false
        addSubview(stack)
        NSLayoutConstraint.activate(f_100212840(stack))
    }

    public required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    private static let separatorColor: NSColor = {
        let light = NSColor.black.withAlphaComponent(0.26)
        let dark = NSColor.white.withAlphaComponent(0.26)
        return NSColor(name: nil) { OriginalSearchAppearance.f_1001ff49c(appearance: $0, dark: dark, light: light) }
    }()

    public static func f_1002127a4() -> NSTextField {
        let label = NSTextField(labelWithString: "·")
        label.textColor = separatorColor
        return label
    }

    public func f_100212840(_ stack: NSView) -> [NSLayoutConstraint] {
        Self.f_100212bac(0, parent: self, child: stack) + [
            stack.leadingAnchor.constraint(equalTo: leadingAnchor),
            stack.trailingAnchor.constraint(lessThanOrEqualTo: trailingAnchor)
        ]
    }

    public static func f_100212bac(_ inset: CGFloat, parent: NSView, child: NSView) -> [NSLayoutConstraint] {
        [child.topAnchor.constraint(equalTo: parent.topAnchor, constant: inset),
         child.bottomAnchor.constraint(equalTo: parent.bottomAnchor, constant: -inset)]
    }
}

/// Replaces the content within the original 11/12-point footer insets.
@MainActor
open class OriginalPreviewFooterView: NSView {
    private let containerView = NSView()

    public init() {
        super.init(frame: .zero)
        containerView.translatesAutoresizingMaskIntoConstraints = false
        addSubview(containerView)
        NSLayoutConstraint.activate([
            containerView.topAnchor.constraint(equalTo: topAnchor, constant: 11),
            containerView.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 12),
            containerView.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -11),
            containerView.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -12)
        ])
    }

    public required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    public func f_1003df0b0(_ view: NSView) {
        for oldView in containerView.subviews { oldView.removeFromSuperview() }
        view.translatesAutoresizingMaskIntoConstraints = false
        containerView.addSubview(view)
        NSLayoutConstraint.activate(f_1003df260(view))
        OriginalPreviewPlatformView.f_1000f74b8(containerView)
    }

    public func f_1003df260(_ view: NSView) -> [NSLayoutConstraint] {
        [view.leadingAnchor.constraint(equalTo: containerView.leadingAnchor),
         view.trailingAnchor.constraint(equalTo: containerView.trailingAnchor),
         view.topAnchor.constraint(equalTo: containerView.topAnchor),
         view.bottomAnchor.constraint(equalTo: containerView.bottomAnchor)]
    }
}
