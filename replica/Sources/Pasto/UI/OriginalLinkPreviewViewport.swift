import AppKit
import PastoCore
import QuartzCore
import SwiftUI

@MainActor
enum OriginalLinkPreviewSurface {
    static let startingColor = NSColor(name: nil) { appearance in
        OriginalSearchAppearance.f_1001ff49c(appearance: appearance,
            dark: .windowBackgroundColor, light: .white)
    }
    static let endingColor = NSColor(name: nil) { appearance in
        OriginalSearchAppearance.f_1001ff49c(appearance: appearance,
            dark: NSColor(red: 28.0 / 255, green: 28.0 / 255, blue: 30.0 / 255, alpha: 1),
            light: NSColor(red: 242.0 / 255, green: 242.0 / 255, blue: 247.0 / 255, alpha: 1))
    }
}

@MainActor
private final class OriginalLinkPreviewGradientView: NSView {
    private let gradientLayer = CAGradientLayer()

    override var isFlipped: Bool { true }

    override init(frame frameRect: NSRect) {
        super.init(frame: frameRect)
        wantsLayer = true
        layer?.addSublayer(gradientLayer)
        clipsToBounds = true
        updateColors()
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    override func layout() {
        super.layout()
        CATransaction.begin()
        CATransaction.setDisableActions(true)
        gradientLayer.frame = bounds
        CATransaction.commit()
    }

    override func viewDidChangeEffectiveAppearance() { updateColors() }

    private func updateColors() {
        effectiveAppearance.performAsCurrentDrawingAppearance {
            CATransaction.begin()
            CATransaction.setDisableActions(true)
            gradientLayer.colors = [OriginalLinkPreviewSurface.startingColor.cgColor,
                                    OriginalLinkPreviewSurface.endingColor.cgColor]
            gradientLayer.transform = CATransform3DMakeRotation(0, 0, 0, 1)
            CATransaction.commit()
        }
    }
}

@MainActor
final class OriginalLinkPreviewViewportView: OriginalLayerBackedView {
    private let fadingView = OriginalLinkPreviewGradientView(frame: .zero)
    private let imageView = OriginalAdaptiveScalingImageView(frame: .zero)
    private let iconView = NSImageView(frame: .zero)
    private lazy var iconCenterY = iconView.centerYAnchor.constraint(equalTo: centerYAnchor)

    override init(frame frameRect: NSRect) {
        super.init(frame: frameRect)
        iconView.imageAlignment = .alignCenter
        iconView.imageScaling = .scaleProportionallyUpOrDown
        if #available(macOS 26, *) {
            OriginalViewLayerFunctions.f_10021d49c(12, curve: .continuous, view: iconView)
        } else {
            OriginalViewLayerFunctions.f_10021d49c(10, curve: .circular, view: iconView)
        }
        for view in [fadingView, imageView, iconView] as [NSView] {
            addSubview(view)
            view.translatesAutoresizingMaskIntoConstraints = false
        }
        var constraints = [iconView.widthAnchor.constraint(equalToConstant: 42),
                           iconView.heightAnchor.constraint(equalToConstant: 42),
                           iconView.centerXAnchor.constraint(equalTo: centerXAnchor),
                           iconCenterY]
        for view in [fadingView, imageView] as [NSView] {
            constraints += [view.leadingAnchor.constraint(equalTo: leadingAnchor),
                            view.trailingAnchor.constraint(equalTo: trailingAnchor),
                            view.topAnchor.constraint(equalTo: topAnchor),
                            view.bottomAnchor.constraint(equalTo: bottomAnchor)]
        }
        NSLayoutConstraint.activate(constraints)
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    func configure(image: NSImage?, icon: NSImage?, sizeClass: UInt8) {
        imageView.image = image
        iconView.image = icon
        imageView.scaleToFillRatio = sizeClass == 3 ? 0 : 0.7
        if sizeClass == 3 {
            if #available(macOS 26, *) { iconCenterY.constant = 5 }
            else { iconCenterY.constant = 7 }
        } else {
            iconCenterY.constant = 0
        }
    }
}

@MainActor
struct OriginalLinkPreviewViewport: NSViewRepresentable {
    let image: NSImage?
    let icon: NSImage?
    let sizeClass: UInt8

    func makeNSView(context: Context) -> OriginalLinkPreviewViewportView {
        let view = OriginalLinkPreviewViewportView(frame: .zero)
        view.configure(image: image, icon: icon, sizeClass: sizeClass)
        return view
    }

    func updateNSView(_ nsView: OriginalLinkPreviewViewportView, context: Context) {
        nsView.configure(image: image, icon: icon, sizeClass: sizeClass)
    }
}
