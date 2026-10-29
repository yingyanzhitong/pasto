import AppKit
import SwiftUI
import PastoCore

/// One native cell owns the icon, label and padding hit area, as Paste's TabBarCell does.
@MainActor
struct OriginalPinboardTab: NSViewRepresentable {
    let title: String
    let iconColor: NSColor?
    var isSelected = false
    let beginRequest: UUID?
    let onSelect: () -> Void
    let onEnd: () -> Void
    let onCommit: (String) -> String

    func makeNSView(context: Context) -> OriginalPinboardTabView {
        let view = OriginalPinboardTabView()
        updateNSView(view, context: context)
        return view
    }

    func updateNSView(_ view: OriginalPinboardTabView, context: Context) {
        view.configure(title: title, iconColor: iconColor, isSelected: isSelected, beginRequest: beginRequest,
                       onSelect: onSelect, onEnd: onEnd, onCommit: onCommit)
    }

    func sizeThatFits(_ proposal: ProposedViewSize, nsView: OriginalPinboardTabView, context: Context) -> CGSize? {
        nsView.measuredSize
    }
}

@MainActor
final class OriginalPinboardTabView: NSView {
    let titleView = OriginalPinboardTabTitleView()
    private let historyIconView = NSImageView()
    private var iconColor: NSColor?
    private var isSelected = false
    private var isHovered = false
    private var isPressed = false
    private var hoverArea: NSTrackingArea?
    private var onSelect: (() -> Void)?
    private let historyIcon = NSImage(systemSymbolName: "clock.arrow.circlepath", accessibilityDescription: nil)?
        .withSymbolConfiguration(.init(pointSize: 15, weight: .regular))

    override init(frame frameRect: NSRect) {
        super.init(frame: frameRect)
        wantsLayer = true
        titleView.onEditingChanged = { [weak self] in self?.isPressed = false; self?.needsDisplay = true }
        historyIconView.image = historyIcon
        historyIconView.contentTintColor = .labelColor
        historyIconView.imageScaling = .scaleProportionallyUpOrDown
        addSubview(historyIconView)
        addSubview(titleView)
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    private var iconSize: CGFloat { iconColor == nil ? 15 : 12 }
    var measuredSize: NSSize {
        NSSize(width: ceil(min(titleView.measuredSize.width, 200) + iconSize + 6 + 20),
               height: ceil(max(titleView.measuredSize.height, iconSize) + 12))
    }

    override var intrinsicContentSize: NSSize { measuredSize }

    func configure(title: String, iconColor: NSColor?, isSelected: Bool = false, beginRequest: UUID?, onSelect: @escaping () -> Void,
                   onEnd: @escaping () -> Void, onCommit: @escaping (String) -> String) {
        let previousSize = measuredSize
        self.iconColor = iconColor
        self.isSelected = isSelected
        historyIconView.isHidden = iconColor != nil
        self.onSelect = onSelect
        titleView.configure(title: title, beginRequest: beginRequest, onSelect: { [weak self] in
            self?.isPressed = false; self?.needsDisplay = true; onSelect()
        },
                            onEnd: onEnd, onCommit: onCommit)
        if measuredSize != previousSize { invalidateIntrinsicContentSize() }
        needsLayout = true
        needsDisplay = true
    }

    override func layout() {
        super.layout()
        historyIconView.frame = NSRect(x: 10, y: (bounds.height - iconSize) / 2,
                                       width: iconSize, height: iconSize)
        let x = 10 + iconSize + 6
        titleView.frame = NSRect(x: x, y: 6, width: max(0, bounds.width - x - 10),
                                 height: max(0, bounds.height - 12))
    }

    override func draw(_ dirtyRect: NSRect) {
        super.draw(dirtyRect)
        // TabBarCell 0x10007a078: editing, pressed, selected, hover, then clear.
        let background: NSColor?
        if titleView.isEditing { background = OriginalToolbarAppearance.borderAndHover() }
        else if isPressed { background = OriginalSearchSurfaceAppearance.f_1001ff0d0().pointee?.withAlphaComponent(0.15) }
        else if isSelected { background = OriginalSearchSurfaceAppearance.f_1001ff0d0().pointee }
        else { background = isHovered ? OriginalToolbarAppearance.borderAndHover() : nil }
        background?.setFill()
        if background != nil {
            let radius: CGFloat
            if #available(macOS 26, *) { radius = bounds.height / 2 } else { radius = 6 }
            NSBezierPath(roundedRect: bounds, xRadius: radius, yRadius: radius).fill()
        }
        let iconFrame = NSRect(x: 10, y: (bounds.height - iconSize) / 2, width: iconSize, height: iconSize)
        if let iconColor {
            iconColor.setFill()
            NSBezierPath(ovalIn: iconFrame).fill()
        }
    }

    override func updateTrackingAreas() {
        super.updateTrackingAreas()
        if let hoverArea { removeTrackingArea(hoverArea) }
        let area = NSTrackingArea(rect: bounds, options: [.mouseEnteredAndExited, .activeInKeyWindow], owner: self, userInfo: nil)
        hoverArea = area
        addTrackingArea(area)
        isHovered = NSEvent.pressedMouseButtons == 0 && window.map {
            bounds.contains(convert($0.mouseLocationOutsideOfEventStream, from: nil))
        } == true
        isPressed = false
        needsDisplay = true
    }

    override func mouseEntered(with event: NSEvent) { isHovered = true; needsDisplay = true }
    override func mouseExited(with event: NSEvent) { isHovered = false; isPressed = false; needsDisplay = true }
    override func viewDidChangeEffectiveAppearance() { super.viewDidChangeEffectiveAppearance(); needsDisplay = true }

    override func hitTest(_ point: NSPoint) -> NSView? {
        guard bounds.contains(convert(point, from: superview)) else { return nil }
        let hit = super.hitTest(point)
        return hit == nil || hit === historyIconView ? self : hit
    }

    override func mouseDown(with event: NSEvent) {
        guard !titleView.isEditing else { return }
        // Keep the press in the tab instead of starting the panel's background-window drag.
        if event.modifierFlags.contains(.control) { super.rightMouseDown(with: event); return }
        isPressed = true
        needsDisplay = true
    }

    // Paste 0x100079e98: select on release inside the whole cell, not on mouse-down.
    override func mouseUp(with event: NSEvent) {
        guard !titleView.isEditing, !event.modifierFlags.contains(.control) else { return }
        isPressed = false
        needsDisplay = true
        if bounds.contains(convert(event.locationInWindow, from: nil)) { onSelect?() }
        else { super.mouseUp(with: event) }
    }
}

@MainActor
final class OriginalPinboardTabTitleView: NSView, NSTextFieldDelegate {
    var onEditingChanged: (() -> Void)?
    private let field = OriginalTabTitleTextField()
    private var originalString = ""
    private var lastRequest: UUID?
    private var pendingBegin = false
    private weak var editingPanel: ReplicaPanel?
    private var onSelect: (() -> Void)?
    private var onEnd: (() -> Void)?
    private var onCommit: ((String) -> String)?

    override init(frame frameRect: NSRect) {
        super.init(frame: frameRect)
        field.isBordered = false
        field.drawsBackground = false
        field.isEditable = false
        field.usesSingleLineMode = true
        field.maximumNumberOfLines = 1
        field.lineBreakMode = .byTruncatingTail
        field.alignment = .natural
        field.font = NSFont.preferredFont(forTextStyle: .body)
        field.delegate = self
        field.focusRingType = .exterior
        addSubview(field)
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    var measuredSize: NSSize {
        field.sizeThatFits(NSSize(width: CGFloat.greatestFiniteMagnitude, height: CGFloat.greatestFiniteMagnitude))
    }

    override var intrinsicContentSize: NSSize { measuredSize }
    var isEditing: Bool { field.isEditable }

    override func layout() {
        super.layout()
        field.frame = bounds
        field.focusRingContainer = superview
        field.noteFocusRingMaskChanged()
    }

    func configure(title: String, beginRequest: UUID?, onSelect: @escaping () -> Void, onEnd: @escaping () -> Void,
                   onCommit: @escaping (String) -> String) {
        self.onSelect = onSelect
        self.onEnd = onEnd
        self.onCommit = onCommit
        // f08c2c0: incoming model text replaces the cancel baseline during editing.
        if field.isEditable {
            originalString = title
        } else if field.stringValue != title {
            field.stringValue = title
            invalidateIntrinsicContentSize()
        }
        if let beginRequest, beginRequest != lastRequest {
            lastRequest = beginRequest
            pendingBegin = true
        }
        if pendingBegin, window != nil {
            pendingBegin = false
            beginEditing()
        }
    }

    override func viewDidMoveToWindow() {
        super.viewDidMoveToWindow()
        if editingPanel !== window { clearOwner() }
        if pendingBegin, window != nil {
            pendingBegin = false
            beginEditing()
        }
    }

    func ownsEditor(in panel: ReplicaPanel) -> Bool {
        window === panel && field.isEditable && field.currentEditor() != nil
            && field.currentEditor() === panel.firstResponder
    }

    private func clearOwner() {
        if editingPanel?.tabTitleEditingOwner === self { editingPanel?.tabTitleEditingOwner = nil }
        editingPanel = nil
    }

    private func beginEditing() {
        guard !field.isEditable else { return }
        originalString = field.stringValue
        field.isEditable = true
        editingPanel = window as? ReplicaPanel
        editingPanel?.tabTitleEditingOwner = self
        window?.makeFirstResponder(field)
        if let editor = field.currentEditor() as? NSTextView {
            editor.setSelectedRange(NSRange(location: 0, length: (field.stringValue as NSString).length))
        }
        onEditingChanged?()
    }

    private func restoreInitialResponder() {
        clearOwner()
        if let window { window.makeFirstResponder(window.initialFirstResponder) }
        onEditingChanged?()
        onEnd?()
    }

    private func cancelEditing() {
        guard field.isEditable else { return }
        field.isEditable = false
        if field.stringValue != originalString {
            field.stringValue = originalString
            invalidateIntrinsicContentSize()
        }
        field.abortEditing()
        restoreInitialResponder()
    }

    private func commitEditing() {
        guard field.isEditable else { return }
        field.isEditable = false
        if let displayed = onCommit?(field.stringValue), field.stringValue != displayed {
            field.stringValue = displayed
            invalidateIntrinsicContentSize()
        }
        restoreInitialResponder()
    }

    override func hitTest(_ point: NSPoint) -> NSView? {
        guard let hit = super.hitTest(point) else { return nil }
        return field.isEditable ? hit : self
    }

    override func mouseDown(with event: NSEvent) {
        if event.clickCount == 2, !field.isEditable { beginEditing() }
        else { super.mouseDown(with: event) }
    }

    override func mouseUp(with event: NSEvent) {
        guard !field.isEditable else { return }
        if bounds.contains(convert(event.locationInWindow, from: nil)) { onSelect?() }
        else { super.mouseUp(with: event) }
    }

    override func cancelOperation(_ sender: Any?) { cancelEditing() }

    func controlTextDidEndEditing(_ obj: Notification) { commitEditing() }

    func controlTextDidChange(_ obj: Notification) { invalidateIntrinsicContentSize() }

    func control(_ control: NSControl, textView: NSTextView, doCommandBy commandSelector: Selector) -> Bool {
        switch commandSelector {
        case #selector(NSResponder.cancelOperation(_:)): cancelEditing(); return true
        case #selector(NSResponder.insertNewline(_:)): commitEditing(); return true
        default: return false
        }
    }
}

/// The original label maps its focus ring to the whole enclosing tab (0x1000791a0).
@MainActor
private final class OriginalTabTitleTextField: NSTextField {
    weak var focusRingContainer: NSView?
    override var focusRingMaskBounds: NSRect {
        focusRingContainer.map { $0.convert($0.bounds, to: self) } ?? bounds
    }
    override func drawFocusRingMask() {
        let rect = focusRingMaskBounds
        let radius: CGFloat
        if #available(macOS 26, *) { radius = rect.height / 2 } else { radius = 6 }
        NSBezierPath(roundedRect: rect, xRadius: radius, yRadius: radius).fill()
    }
}
