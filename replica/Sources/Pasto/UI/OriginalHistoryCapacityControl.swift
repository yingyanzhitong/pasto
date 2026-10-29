import AppKit
import SwiftUI
import PastoCore

/// HistoryCapacitySlider uses an NSSlider, with completion after native mouse tracking.
@MainActor
struct OriginalHistoryCapacitySlider: NSViewRepresentable {
    @Binding var days: Int

    func makeNSView(context: Context) -> OriginalHistoryCapacityControl {
        OriginalHistoryCapacityControl()
    }

    func updateNSView(_ view: OriginalHistoryCapacityControl, context: Context) {
        view.onCommit = { days = $0 }
        if !view.slider.isTrackingMouse { view.setDays(days) }
    }

    func sizeThatFits(_ proposal: ProposedViewSize, nsView: OriginalHistoryCapacityControl, context: Context) -> CGSize? {
        CGSize(width: proposal.width ?? 400, height: 54)
    }
}

@MainActor
final class OriginalHistoryCapacityControl: NSView {
    let slider = OriginalHistoryCapacityNSSlider()
    var onCommit: ((Int) -> Void)?
    private let labels: [NSTextField]
    private var pendingDays: Int?

    override init(frame frameRect: NSRect) {
        labels = ["天", "周", "个月", "年", OriginalSettingsLocalization.text("settings.history.forever")].map {
            let label = NSTextField(labelWithString: $0)
            label.font = .preferredFont(forTextStyle: .body)
            label.textColor = .labelColor
            label.alignment = .center
            return label
        }
        super.init(frame: frameRect)
        slider.minValue = 1
        slider.maxValue = 5
        slider.numberOfTickMarks = 5
        slider.allowsTickMarkValuesOnly = false
        slider.tickMarkPosition = .below
        slider.controlSize = .regular
        slider.isContinuous = true
        slider.target = self
        slider.action = #selector(valueChanged)
        slider.onTrackingBegan = { [weak self] in self?.pendingDays = nil }
        slider.onTrackingEnded = { [weak self] in self?.commit() }
        slider.setAccessibilityLabel(OriginalSettingsLocalization.text("settings.history.title"))
        addSubview(slider)
        for label in labels { addSubview(label) }
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    override func layout() {
        super.layout()
        slider.frame = NSRect(x: 0, y: 24, width: bounds.width, height: 28)
        for (index, label) in labels.enumerated() {
            let size = label.intrinsicContentSize
            let tick = (slider.cell as! NSSliderCell).rectOfTickMark(at: index)
            let center = slider.convert(NSPoint(x: tick.midX, y: tick.midY), to: self).x
            label.frame = NSRect(x: max(0, min(bounds.width - size.width, center - size.width / 2)),
                                 y: 0, width: size.width, height: 20)
        }
    }

    func setDays(_ days: Int) {
        pendingDays = nil
        slider.doubleValue = OriginalHistoryCapacity.position(for: days)
    }

    @objc private func valueChanged() {
        guard let days = OriginalHistoryCapacity.days(for: slider.doubleValue) else { return }
        pendingDays = days
        slider.doubleValue = OriginalHistoryCapacity.position(for: days)
        slider.setAccessibilityValueDescription(days == 0 ? "永久" : "保留 \(days) 天")
        if !slider.isTrackingMouse { onCommit?(days) }
    }

    private func commit() {
        if let days = pendingDays ?? OriginalHistoryCapacity.days(for: slider.doubleValue) { onCommit?(days) }
    }
}

@MainActor
final class OriginalHistoryCapacityNSSlider: NSSlider {
    private(set) var isTrackingMouse = false
    var onTrackingBegan: (() -> Void)?
    var onTrackingEnded: (() -> Void)?

    override func mouseDown(with event: NSEvent) {
        isTrackingMouse = true
        onTrackingBegan?()
        super.mouseDown(with: event)
        isTrackingMouse = false
        onTrackingEnded?()
    }
}
