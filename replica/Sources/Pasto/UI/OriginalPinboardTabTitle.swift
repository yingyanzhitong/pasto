import AppKit
import PastoCore

/// Stable tab configuration consumed by the native stack; actions stay in the
/// panel's existing state/store layer.
@MainActor
struct OriginalPinboardTab {
    let title: String
    let iconColor: NSColor?
    var isSelected = false
    let beginRequest: UUID?
    let onSelect: () -> Void
    let onEnd: () -> Void
    let onCommit: (String) -> String
    var menuProvider: (() -> NSMenu)?
    var dragString: String?
    var onDropString: ((String) -> Bool)?
    var onDropItemIdentifiers: (([String]) -> Void)?
    var canDropItems: (() -> Bool)?

    func configure(_ view: OriginalPinboardTabView) {
        view.configure(title: title, iconColor: iconColor, isSelected: isSelected, beginRequest: beginRequest,
                       onSelect: onSelect, onEnd: onEnd, onCommit: onCommit)
        view.menuProvider = menuProvider
        view.dragString = dragString
        view.onDropString = onDropString
        view.onDropItemIdentifiers = onDropItemIdentifiers
        view.canDropItems = canDropItems
        view.setAccessibilityElement(true)
        view.setAccessibilityRole(.button)
        view.setAccessibilityLabel(title)
        view.setAccessibilityValue(isSelected)
    }
}

@MainActor
final class OriginalPinboardTabView: NSView, NSDraggingSource {
    let titleView = OriginalPinboardTabTitleView()
    private let historyIconView = NSImageView()
    private var iconColor: NSColor?
    private(set) var isSelected = false
    private(set) var isCollapsed = false
    private var isHovered = false
    private var isPressed = false
    private var hoverArea: NSTrackingArea?
    private var onSelect: (() -> Void)?
    var menuProvider: (() -> NSMenu)?
    var dragString: String?
    var onDropString: ((String) -> Bool)?
    var onDropItemIdentifiers: (([String]) -> Void)?
    var canDropItems: (() -> Bool)?
    private var isDragging = false
    private var isDragDestination = false
    private lazy var labelTrailingConstraint = titleView.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -8)
    private lazy var compactWidthConstraint = widthAnchor.constraint(equalTo: heightAnchor, multiplier: 1)
    private lazy var iconWidthConstraint = historyIconView.widthAnchor.constraint(equalToConstant: iconSize)
    private lazy var iconHeightConstraint = historyIconView.heightAnchor.constraint(equalToConstant: iconSize)
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
        historyIconView.translatesAutoresizingMaskIntoConstraints = false
        titleView.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            historyIconView.centerYAnchor.constraint(equalTo: centerYAnchor),
            historyIconView.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 8),
            historyIconView.trailingAnchor.constraint(lessThanOrEqualTo: trailingAnchor, constant: -8),
            iconWidthConstraint, iconHeightConstraint,
            titleView.topAnchor.constraint(equalTo: topAnchor, constant: 6),
            titleView.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -6),
            titleView.widthAnchor.constraint(lessThanOrEqualToConstant: 200),
            titleView.leadingAnchor.constraint(equalTo: historyIconView.trailingAnchor, constant: 4),
            labelTrailingConstraint
        ])
        // Native item IDs are distinct from the retained local group-reorder adapter.
        registerForDraggedTypes([OriginalNativeDragPasteboardWriter.itemIdentifierType, .string])
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    func setSelected(_ selected: Bool) {
        isSelected = selected
        setAccessibilityValue(selected)
        needsDisplay = true
    }

    private var iconSize: CGFloat { iconColor == nil ? 15 : 12 }
    var measuredSize: NSSize {
        let height = ceil(max(titleView.measuredSize.height, iconSize) + 12)
        if isCollapsed {
            if #available(macOS 26, *) { return NSSize(width: height, height: height) }
            return NSSize(width: iconSize + 16, height: height)
        }
        return NSSize(width: ceil(min(titleView.measuredSize.width, 200) + iconSize + 20), height: height)
    }

    override var intrinsicContentSize: NSSize { measuredSize }

    func configure(title: String, iconColor: NSColor?, isSelected: Bool = false, beginRequest: UUID?, onSelect: @escaping () -> Void,
                   onEnd: @escaping () -> Void, onCommit: @escaping (String) -> String) {
        let previousSize = measuredSize
        self.iconColor = iconColor
        self.isSelected = isSelected
        if let iconColor {
            let image = NSImage(size: NSSize(width: 12, height: 12), flipped: false) { bounds in
                iconColor.setFill()
                NSBezierPath(ovalIn: bounds).fill()
                return true
            }
            image.isTemplate = false
            historyIconView.image = image
            historyIconView.contentTintColor = nil
        } else {
            historyIconView.image = historyIcon
            historyIconView.contentTintColor = .labelColor
        }
        iconWidthConstraint.constant = iconSize
        iconHeightConstraint.constant = iconSize
        self.onSelect = onSelect
        titleView.configure(title: title, beginRequest: beginRequest, onSelect: { [weak self] in
            self?.isPressed = false; self?.needsDisplay = true; onSelect()
        },
                            onEnd: onEnd, onCommit: onCommit)
        if measuredSize != previousSize { invalidateIntrinsicContentSize() }
        needsLayout = true
        needsDisplay = true
    }

    // 0785e0 / inlined 095228: keep the same cell and label while collapsing.
    func setCollapsed(_ collapsed: Bool) {
        isCollapsed = collapsed
        if #available(macOS 26, *) { compactWidthConstraint.isActive = collapsed }
        else { compactWidthConstraint.isActive = false }
        labelTrailingConstraint.isActive = !collapsed
        titleView.alphaValue = collapsed ? 0 : 1
        invalidateIntrinsicContentSize()
        needsLayout = true
        needsDisplay = true
    }

    override func draw(_ dirtyRect: NSRect) {
        super.draw(dirtyRect)
        // TabBarCell 0x10007a078: editing, pressed, selected, hover, then clear.
        let background: NSColor?
        if titleView.isEditing { background = OriginalToolbarAppearance.borderAndHover() }
        else if isPressed { background = OriginalSearchSurfaceAppearance.f_1001ff0d0().pointee?.withAlphaComponent(0.15) }
        else if (isSelected && !isCollapsed) || isDragDestination { background = OriginalSearchSurfaceAppearance.f_1001ff0d0().pointee }
        else { background = isHovered ? OriginalToolbarAppearance.borderAndHover() : nil }
        background?.setFill()
        if background != nil {
            let radius: CGFloat
            if #available(macOS 26, *) { radius = bounds.height / 2 } else { radius = 6 }
            NSBezierPath(roundedRect: bounds, xRadius: radius, yRadius: radius).fill()
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
        isDragging = false
        needsDisplay = true
    }

    // Paste 0x100079e98: select on release inside the whole cell, not on mouse-down.
    override func mouseUp(with event: NSEvent) {
        guard !titleView.isEditing else { return }
        isPressed = false
        needsDisplay = true
        if bounds.contains(convert(event.locationInWindow, from: nil)) { onSelect?() }
        else { super.mouseUp(with: event) }
    }

    override func menu(for event: NSEvent) -> NSMenu? { menuProvider?() ?? super.menu(for: event) }

    override func accessibilityPerformPress() -> Bool { onSelect?(); return true }

    override func mouseDragged(with event: NSEvent) {
        guard !titleView.isEditing, !isDragging, let dragString else { return }
        let writer = NSPasteboardItem()
        writer.setString(dragString, forType: .string)
        let item = NSDraggingItem(pasteboardWriter: writer)
        let image = NSImage(size: bounds.size)
        if let bitmap = bitmapImageRepForCachingDisplay(in: bounds) {
            cacheDisplay(in: bounds, to: bitmap)
            image.addRepresentation(bitmap)
        }
        item.setDraggingFrame(bounds, contents: image)
        isDragging = true
        isPressed = false
        needsDisplay = true
        beginDraggingSession(with: [item], event: event, source: self)
    }

    func draggingSession(_ session: NSDraggingSession, sourceOperationMaskFor context: NSDraggingContext) -> NSDragOperation { .move }
    func draggingSession(_ session: NSDraggingSession, endedAt screenPoint: NSPoint, operation: NSDragOperation) {
        isDragging = false
        isPressed = false
        needsDisplay = true
    }

    private func draggedGroup(_ sender: NSDraggingInfo) -> String? {
        guard onDropString != nil, let value = sender.draggingPasteboard.string(forType: .string),
              value.hasPrefix("paste-pinboard:") else { return nil }
        return value
    }

    private func isItemDrag(_ sender: NSDraggingInfo) -> Bool {
        sender.draggingPasteboard.types?.contains(OriginalNativeDragPasteboardWriter.itemIdentifierType) == true
    }

    override func draggingEntered(_ sender: NSDraggingInfo) -> NSDragOperation {
        if isItemDrag(sender) {
            // 0792a8/07a4f8 returns the predicate's Bool as operation raw value 0/1 (copy).
            isDragDestination = canDropItems?() ?? false
            needsDisplay = true
            return isDragDestination ? .copy : []
        }
        isDragDestination = draggedGroup(sender) != nil
        needsDisplay = true
        return isDragDestination ? .move : []
    }
    override func draggingUpdated(_ sender: NSDraggingInfo) -> NSDragOperation { draggingEntered(sender) }
    override func prepareForDragOperation(_ sender: NSDraggingInfo) -> Bool {
        if isItemDrag(sender) { return true }
        return draggedGroup(sender) != nil
    }
    override func draggingExited(_ sender: NSDraggingInfo?) { isDragDestination = false; needsDisplay = true }
    override func draggingEnded(_ sender: NSDraggingInfo) { isDragDestination = false; needsDisplay = true }
    override func performDragOperation(_ sender: NSDraggingInfo) -> Bool {
        if performItemDrop(sender) { return true }
        if isItemDrag(sender) { return false }
        isDragDestination = false
        needsDisplay = true
        guard let value = draggedGroup(sender) else { return false }
        return onDropString?(value) ?? false
    }

    // 079430: preserve item order/duplicates, skip nil strings, report acceptance independently of the write.
    private func performItemDrop(_ sender: NSDraggingInfo) -> Bool {
        guard let onDropItemIdentifiers else { return false }
        let identifiers = (sender.draggingPasteboard.pasteboardItems ?? []).compactMap {
            $0.string(forType: OriginalNativeDragPasteboardWriter.itemIdentifierType)
        }
        guard !identifiers.isEmpty else { return false }
        onDropItemIdentifiers(identifiers)
        return true
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

    func beginEditingFromListRequest() { beginEditing() }

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
        guard alphaValue > 0, let hit = super.hitTest(point) else { return nil }
        return field.isEditable ? hit : self
    }

    override func menu(for event: NSEvent) -> NSMenu? {
        field.isEditable ? super.menu(for: event) : superview?.menu(for: event)
    }

    override func mouseDragged(with event: NSEvent) {
        if field.isEditable { super.mouseDragged(with: event) }
        else { superview?.mouseDragged(with: event) }
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
        NSColor.black.setFill()
        NSBezierPath(roundedRect: rect, xRadius: radius, yRadius: radius).fill()
    }
}
