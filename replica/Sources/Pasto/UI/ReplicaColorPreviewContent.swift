import AppKit
import Combine
import PastoCore

/// Native local color editing. Core Data ownership and the original ColorView remain adapters.
@MainActor
final class ReplicaColorPreviewContent: OriginalLayerBackedView, OriginalPreviewEditableContent {
    var onCanCommitEditing: ((Bool) -> Void)?
    var previewEditingToolbar: NSView? { nil }
    var previewMetadataView: NSView? { metadata }
    var preferredPreviewSize: NSSize {
        // Without a PreferredSize provider, f_10007c994 uses a quarter screen or zero.
        guard let size = NSScreen.main?.frame.size else { return .zero }
        return .init(width: size.width * 0.25, height: size.height * 0.25)
    }

    private weak var state: ReplicaUIState?
    private let itemID: UUID
    private let codeLabel = NSTextField(labelWithString: "")
    private let metadata = NSStackView()
    private var itemObservation: AnyCancellable?
    private var editing = false
    private var displayedColor: NSColor = .black
    private var storedPanel: NSColorPanel?
    private static let metadataNameColor = NSColor(name: nil) { appearance in
        OriginalSearchAppearance.f_1001ff49c(appearance: appearance,
            dark: NSColor.white.withAlphaComponent(0.26), light: NSColor.black.withAlphaComponent(0.26))
    }

    init(state: ReplicaUIState, item: ClipboardItem) {
        self.state = state
        itemID = item.id
        super.init(frame: .zero)
        codeLabel.font = NSFont.userFixedPitchFont(ofSize: 22)
        codeLabel.alignment = .center
        codeLabel.translatesAutoresizingMaskIntoConstraints = false
        addSubview(codeLabel)
        NSLayoutConstraint.activate([
            codeLabel.centerXAnchor.constraint(equalTo: centerXAnchor),
            codeLabel.centerYAnchor.constraint(equalTo: centerYAnchor)
        ])
        metadata.orientation = .horizontal
        metadata.alignment = .centerY
        metadata.spacing = 8
        NotificationCenter.default.addObserver(self, selector: #selector(colorChanged),
            name: NSColorPanel.colorDidChangeNotification, object: colorPanel)
        itemObservation = state.store.$items.sink { [weak self] items in
            MainActor.assumeIsolated {
                guard let self, !self.editing,
                      let current = items.first(where: { $0.id == self.itemID }) else { return }
                self.display(Self.modelColor(current))
            }
        }
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    private var colorPanel: NSColorPanel {
        if let storedPanel { return storedPanel }
        let panel = NSColorPanel.shared
        panel.standardWindowButton(.zoomButton)?.isEnabled = false
        panel.standardWindowButton(.closeButton)?.isEnabled = false
        panel.showsAlpha = false
        panel.hidesOnDeactivate = false
        panel.level = .init(rawValue: (window?.level.rawValue ?? 3) + 1)
        panel.animationBehavior = .none
        storedPanel = panel
        return panel
    }

    func beginPreviewEditing() {
        editing = true
        let panel = colorPanel
        onCanCommitEditing?(false)
        panel.color = currentModelColor()
        panel.makeKeyAndOrderFront(nil)
        if let window, let screen = NSScreen.main {
            let frame = window.frame
            let panelFrame = panel.frame
            let x = screen.frame.maxX - frame.maxX >= panelFrame.width + 40
                ? frame.maxX + 20 : frame.minX - 20 - panelFrame.width
            panel.setFrameOrigin(.init(x: x, y: frame.minY + (frame.height - panelFrame.height) * 0.5))
        }
    }

    func cancelPreviewEditing() {
        editing = false
        colorPanel.orderOut(nil)
        display(currentModelColor())
    }

    func commitPreviewEditing() {
        editing = false
        colorPanel.orderOut(nil)
        guard let state else { return }
        do {
            try state.store.updateColorItem(id: itemID, text: Self.hexString(displayedColor))
            state.normalizeSelection()
        } catch { state.controller?.presentError(error) }
    }

    @objc private func colorChanged() {
        let color = colorPanel.color
        display(color)
        onCanCommitEditing?(!color.isEqual(currentModelColor()))
    }

    private func currentModelColor() -> NSColor {
        state?.store.items.first(where: { $0.id == itemID }).map(Self.modelColor) ?? .black
    }

    private static func modelColor(_ item: ClipboardItem) -> NSColor {
        guard let metadata = item.decodedColorPreviewMetadata else { return .black }
        return OriginalColorPreviewMetadataGenerator.color(metadata.code)
    }

    private static func hexString(_ color: NSColor) -> String {
        guard let rgb = color.usingColorSpace(.deviceRGB) else { return "#000000" }
        return String(format: "#%02X%02X%02X", Int(rgb.redComponent * 255),
                      Int(rgb.greenComponent * 255), Int(rgb.blueComponent * 255))
    }

    private func display(_ color: NSColor) {
        displayedColor = color
        backgroundColor = color
        codeLabel.stringValue = Self.hexString(color)
        codeLabel.textColor = OriginalPreviewTextColors.f_1002067d4(color) ? .black : .white
        for view in metadata.arrangedSubviews {
            metadata.removeArrangedSubview(view)
            view.removeFromSuperview()
        }
        let rgb = color.usingColorSpace(.deviceRGB)
        let red = rgb?.redComponent ?? 0
        let green = rgb?.greenComponent ?? 0
        let blue = rgb?.blueComponent ?? 0
        let hue = rgb?.hueComponent ?? 0
        let saturation = rgb?.saturationComponent ?? 0
        let brightness = rgb?.brightnessComponent ?? 0
        // Preserve the reference's 256 RGB scaling and its HSV-saturation HSL tuple.
        let rounded: (CGFloat) -> Int = { Int($0.rounded(.toNearestOrAwayFromZero)) }
        let values = [
            ("RGB", "\(rounded(red * 256)), \(rounded(green * 256)), \(rounded(blue * 256))"),
            ("HSL", "\(rounded(hue * 360)), \(rounded(saturation * 100)), \(rounded((2 - saturation) * brightness * 50))"),
            ("HSB", "\(rounded(hue * 360)), \(rounded(saturation * 100)), \(rounded(brightness * 100))")
        ]
        for (index, pair) in values.enumerated() {
            if index > 0 {
                let separator = NSTextField(labelWithString: "·")
                separator.textColor = Self.metadataNameColor
                metadata.addArrangedSubview(separator)
            }
            let name = NSTextField(labelWithString: pair.0)
            name.font = OriginalSearchAppearance.f_1001ff928()
            name.textColor = Self.metadataNameColor
            let value = NSTextField(labelWithString: pair.1)
            value.font = .monospacedDigitSystemFont(ofSize: OriginalSearchAppearance.f_1001ff928().pointSize,
                                                   weight: .regular)
            value.textColor = OriginalToolbarAppearance.secondaryForeground()
            let row = NSStackView(views: [name, value])
            row.orientation = .horizontal
            row.alignment = .centerY
            row.spacing = 4
            metadata.addArrangedSubview(row)
        }
    }

    deinit { NotificationCenter.default.removeObserver(self) }
}
