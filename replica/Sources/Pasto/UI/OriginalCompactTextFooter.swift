import AppKit
import PastoCore
import QuartzCore
import SwiftUI

@MainActor
enum OriginalCompactTextCardAppearance {
    static func background(for text: AttributedString) -> NSColor {
        let source = NSAttributedString(text)
        if OriginalPreviewAttributedText.f_1003095bc(source) {
            return OriginalPreviewTextColors.f_100219bc4().pointee!
        }
        let color = OriginalPreviewTextColors.f_1001ffc58(source)
        return color.alphaComponent < 1 ? OriginalLinkPreviewSurface.startingColor : color
    }

    static func appearance(for color: NSColor) -> NSAppearance {
        NSAppearance(named: OriginalPreviewTextColors.f_1002067d4(color) ? .aqua : .darkAqua)
            ?? NSAppearance.currentDrawing()
    }
}

@MainActor
private final class OriginalCompactTextFadeView: NSView {
    private let gradient = CAGradientLayer()
    private var fadingColor: NSColor?
    override var isFlipped: Bool { true }

    override init(frame frameRect: NSRect) {
        super.init(frame: frameRect)
        wantsLayer = true
        layer?.addSublayer(gradient)
        clipsToBounds = true
        updateColors()
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    func configure(color: NSColor) {
        fadingColor = color
        updateColors()
    }

    override func layout() {
        super.layout()
        CATransaction.begin()
        CATransaction.setDisableActions(true)
        gradient.frame = bounds
        CATransaction.commit()
    }

    override func viewDidChangeEffectiveAppearance() { updateColors() }

    private func updateColors() {
        effectiveAppearance.performAsCurrentDrawingAppearance {
            CATransaction.begin()
            CATransaction.setDisableActions(true)
            gradient.colors = [(fadingColor?.withAlphaComponent(0) ?? .clear).cgColor,
                               (fadingColor ?? .clear).cgColor]
            gradient.transform = CATransform3DMakeRotation(0, 0, 0, 1)
            CATransaction.commit()
        }
    }
}

@MainActor
final class OriginalCompactTextFooterView: NSView {
    private let opaqueView = OriginalLayerBackedView(frame: .zero)
    private let fadingView = OriginalCompactTextFadeView(frame: .zero)
    private let textLabel = NSTextField(labelWithString: "")
    private lazy var opaqueHeight = opaqueView.heightAnchor.constraint(equalToConstant: 18)

    override init(frame frameRect: NSRect) {
        super.init(frame: frameRect)
        textLabel.textColor = OriginalToolbarAppearance.secondaryForeground()
        textLabel.alignment = .center
        textLabel.font = NSFont.preferredFont(forTextStyle: .callout, options: [:])
        for view in [opaqueView, fadingView, textLabel] as [NSView] {
            addSubview(view)
            view.translatesAutoresizingMaskIntoConstraints = false
        }
        NSLayoutConstraint.activate([
            fadingView.leadingAnchor.constraint(equalTo: leadingAnchor),
            fadingView.trailingAnchor.constraint(equalTo: trailingAnchor),
            fadingView.topAnchor.constraint(equalTo: topAnchor),
            fadingView.heightAnchor.constraint(equalToConstant: 32),
            fadingView.bottomAnchor.constraint(equalTo: opaqueView.topAnchor),
            opaqueView.leadingAnchor.constraint(equalTo: leadingAnchor),
            opaqueView.trailingAnchor.constraint(equalTo: trailingAnchor),
            opaqueView.bottomAnchor.constraint(equalTo: bottomAnchor),
            opaqueHeight,
            textLabel.leadingAnchor.constraint(equalTo: leadingAnchor),
            textLabel.trailingAnchor.constraint(equalTo: trailingAnchor),
            textLabel.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -10)
        ])
        setContentHuggingPriority(.init(750), for: .vertical)
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    override var intrinsicContentSize: NSSize {
        NSSize(width: NSView.noIntrinsicMetric, height: 32 + opaqueHeight.constant)
    }

    func configure(length: Int, sizeClass: UInt8, fadingColor: NSColor) {
        appearance = OriginalCompactTextCardAppearance.appearance(for: fadingColor)
        textLabel.stringValue = String(localized: OriginalPreviewLocalization.f_1001e6b38(Int32(length)))
        let compact = sizeClass == 3
        textLabel.alphaValue = compact ? 0 : 1
        textLabel.isHidden = compact
        opaqueHeight.constant = compact ? 0 : 18
        opaqueView.backgroundColor = fadingColor
        fadingView.configure(color: fadingColor)
        invalidateIntrinsicContentSize()
    }
}

@MainActor
struct OriginalCompactTextFooter: NSViewRepresentable {
    let length: Int
    let sizeClass: UInt8
    let fadingColor: NSColor

    func makeNSView(context: Context) -> OriginalCompactTextFooterView {
        let view = OriginalCompactTextFooterView(frame: .zero)
        view.configure(length: length, sizeClass: sizeClass, fadingColor: fadingColor)
        return view
    }

    func updateNSView(_ nsView: OriginalCompactTextFooterView, context: Context) {
        nsView.configure(length: length, sizeClass: sizeClass, fadingColor: fadingColor)
    }

    func sizeThatFits(_ proposal: ProposedViewSize, nsView: OriginalCompactTextFooterView,
                     context: Context) -> CGSize? {
        guard let width = proposal.width else { return nil }
        return CGSize(width: width, height: sizeClass == 3 ? 32 : 50)
    }
}
