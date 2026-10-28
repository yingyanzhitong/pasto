import AppKit
import PastoCore
import QuartzCore

/// Native child window for search suggestions. The editor supplies real rows and keeps first responder.
@MainActor
final class ReplicaSearchSuggestionsMenu: NSWindow {
    struct Row {
        let title: String
        let subtitle: String?
        let image: NSImage?
        let isEnabled: Bool
        let matchQuery: String?

        init(title: String, subtitle: String? = nil, image: NSImage? = nil, isEnabled: Bool = true, matchQuery: String? = nil) {
            self.title = title
            self.subtitle = subtitle
            self.image = image
            self.isEnabled = isEnabled
            self.matchQuery = matchQuery
        }
    }

    private let scroller = SuggestionsScroller()
    private var rows: [Row] = []
    private var selectedIndex: Int?
    private var mouseSelectionCooldown: DispatchWorkItem?
    private var accept: ((Int) -> Void)?
    private var escape: (() -> Void)?
    private weak var anchorView: NSView?
    private var keyboardMonitor: Any?
    private var mouseMonitor: Any?
    private var lostFocusObserver: NSObjectProtocol?

    override var canBecomeKey: Bool { false }
    override var canBecomeMain: Bool { false }

    init() {
        super.init(contentRect: .zero, styleMask: .borderless, backing: .buffered, defer: false)
        backgroundColor = .clear
        hasShadow = true
        isOpaque = false
        level = .init(rawValue: 101)
        isReleasedWhenClosed = false
        contentView = scroller
        scroller.onHover = { [weak self] index in
            guard let self, self.mouseSelectionCooldown == nil else { return }
            self.select(index, reveal: false)
        }
        scroller.onExit = { [weak self] in
            guard let self, self.mouseSelectionCooldown == nil else { return }
            self.selectedIndex = nil
            self.scroller.select(nil)
        }
        scroller.onAccept = { [weak self] index in self?.acceptRow(index) }
    }

    deinit {
        MainActor.assumeIsolated {
            removeMonitors()
            scroller.dispose()
        }
    }

    func show(rows: [Row], anchorRect: NSRect, in anchorView: NSView,
              onAccept: @escaping (Int) -> Void, onEscape: @escaping () -> Void) {
        guard let parent = anchorView.window else { return }
        self.rows = rows
        self.anchorView = anchorView
        accept = onAccept
        escape = onEscape
        guard !rows.isEmpty else { dismiss(); return }
        scroller.setRows(rows)
        selectedIndex = nil
        scroller.select(selectedIndex)
        let width = max(120, scroller.fittingSize.width)
        setFrame(.init(x: frame.minX, y: frame.minY, width: width, height: frame.height), display: false)
        scroller.layoutSubtreeIfNeeded()
        let contentHeight = scroller.fittingSize.height
        let screenRect = parent.convertToScreen(anchorView.convert(anchorRect, to: nil))
        guard let screen = NSScreen.screens.first(where: { $0.frame.contains(screenRect.origin) }) else { return }
        // Original caps downward height at anchor.y - visibleFrame.minY - 6;
        // it does not add an unrelated right-edge or above-anchor placement policy.
        let height = min(contentHeight, screenRect.minY - screen.visibleFrame.minY - 6)
        setFrame(.init(x: screenRect.minX, y: screenRect.minY - height, width: width, height: height), display: true)
        scroller.layoutSubtreeIfNeeded()
        if let titleRect = scroller.firstTitleRectInWindow {
            setFrameOrigin(.init(x: frame.minX - titleRect.minX - 2, y: frame.minY))
        }
        if self.parent !== parent {
            self.parent?.removeChildWindow(self)
            parent.addChildWindow(self, ordered: .above)
        }
        display()
        orderFront(nil)
        installMonitors(parent: parent)
    }

    func dismiss() {
        removeMonitors()
        self.parent?.removeChildWindow(self)
        orderOut(nil)
        accept = nil
        escape = nil
        anchorView = nil
    }

    /// Original suggestion navigation leaves unsupported keys with the editor.
    @discardableResult
    func handleKeyDown(_ event: NSEvent) -> Bool {
        guard isVisible else { return false }
        switch OriginalNavigationKey.f_100219ddc(event) {
        case .down: moveSelection(by: 1)
        case .up: moveSelection(by: -1)
        case .home: moveSelection(by: -rows.count)
        case .pageUp: moveSelection(by: -5)
        case .end: moveSelection(by: rows.count)
        case .pageDown: moveSelection(by: 5)
        case .enter, .tab, .right:
            guard let selectedIndex else { return false }
            acceptRow(selectedIndex)
        case .escape:
            let forwardToPanel = parent is ReplicaPanel && (event.window ?? NSApp.keyWindow) === parent
            cancel()
            return !forwardToPanel
        default: return false
        }
        return true
    }

    private func moveSelection(by offset: Int) {
        guard !rows.isEmpty else { return }
        mouseSelectionCooldown?.cancel()
        let index = selectedIndex.map { max(0, min(rows.count - 1, $0 + offset)) }
            ?? (offset > 0 ? 0 : rows.count - 1)
        selectedIndex = index
        scroller.select(index)
        scroller.revealSelection()
        let cooldown = DispatchWorkItem { [weak self] in
            MainActor.assumeIsolated { self?.mouseSelectionCooldown = nil }
        }
        mouseSelectionCooldown = cooldown
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1, execute: cooldown)
    }

    private func select(_ index: Int, reveal: Bool) {
        selectedIndex = index
        scroller.select(index)
        if reveal { scroller.revealSelection() }
    }

    private func acceptRow(_ index: Int) {
        guard index < rows.count else { return }
        precondition(index >= 0)
        accept?(index)
    }

    private func cancel() {
        let callback = escape
        dismiss()
        callback?()
    }

    private func installMonitors(parent: NSWindow) {
        removeMonitors()
        keyboardMonitor = NSEvent.addLocalMonitorForEvents(matching: .init(rawValue: 0x400)) { [weak self] event in
            let handled = MainActor.assumeIsolated { self?.handleKeyDown(event) ?? false }
            return handled ? nil : event
        }
        mouseMonitor = NSEvent.addLocalMonitorForEvents(matching: .init(rawValue: 0x200000a)) { [weak self] event in
            MainActor.assumeIsolated {
                guard let self, self.isVisible else { return }
                if event.window === self { return }
                if let anchor = self.anchorView, event.window === anchor.window,
                   anchor.bounds.contains(anchor.convert(event.locationInWindow, from: nil)) { return }
                self.cancel()
            }
            return event
        }
        lostFocusObserver = NotificationCenter.default.addObserver(forName: NSWindow.didResignKeyNotification,
            object: parent, queue: .main) { [weak self] _ in
                MainActor.assumeIsolated { self?.cancel() }
            }
    }

    private func removeMonitors() {
        if let keyboardMonitor { NSEvent.removeMonitor(keyboardMonitor); self.keyboardMonitor = nil }
        if let mouseMonitor { NSEvent.removeMonitor(mouseMonitor); self.mouseMonitor = nil }
        if let lostFocusObserver { NotificationCenter.default.removeObserver(lostFocusObserver); self.lostFocusObserver = nil }
    }
}

@MainActor
private final class SuggestionsScroller: NSView {
    private let background = NSVisualEffectView()
    private var storedScrollView: NSScrollView?
    private var scrollView: NSScrollView { f_1000493ec() }
    private let list = SuggestionsList()
    private let up = SuggestionsScrollIndicator(symbol: "chevron.up")
    private let down = SuggestionsScrollIndicator(symbol: "chevron.down")
    private var boundsObserver: NSObjectProtocol?
    var onHover: ((Int) -> Void)?
    var onAccept: ((Int) -> Void)?
    var onExit: (() -> Void)?

    override init(frame frameRect: NSRect) {
        super.init(frame: frameRect)
        background.material = .menu
        background.blendingMode = .behindWindow
        background.state = .active
        background.wantsLayer = true
        background.layer?.cornerRadius = 6
        background.layer?.masksToBounds = true
        addSubview(background)
        scrollView.documentView = list
        addSubview(scrollView)
        addSubview(up)
        addSubview(down)
        list.onHover = { [weak self] in self?.onHover?($0) }
        list.onAccept = { [weak self] in self?.onAccept?($0) }
        list.onExit = { [weak self] in self?.onExit?() }
        up.canScroll = { [weak self] in
            guard let self else { return false }
            return self.scrollView.documentVisibleRect.minY > 0
        }
        down.canScroll = { [weak self] in
            guard let self else { return false }
            return self.scrollView.documentVisibleRect.maxY < self.list.bounds.height
        }
        up.onScroll = { [weak self] in self?.list.scrollUpOneRow() }
        down.onScroll = { [weak self] in self?.list.scrollDownOneRow() }
        boundsObserver = NotificationCenter.default.addObserver(forName: NSView.boundsDidChangeNotification,
            object: scrollView.contentView, queue: .main) { [weak self] _ in
                MainActor.assumeIsolated { self?.updateIndicators() }
            }
    }

    required init?(coder: NSCoder) { return nil }

    private func f_1000493ec() -> NSScrollView {
        if let storedScrollView { return storedScrollView }
        let view = NSScrollView()
        view.contentView.postsBoundsChangedNotifications = true
        view.usesPredominantAxisScrolling = true
        view.hasHorizontalScroller = false
        view.hasVerticalScroller = false
        view.autohidesScrollers = false
        view.drawsBackground = false
        view.borderType = .noBorder
        view.wantsLayer = true
        storedScrollView = view
        return view
    }

    override var fittingSize: NSSize { list.fittingSize }
    var firstTitleRectInWindow: NSRect? { list.firstTitleRectInWindow }

    func setRows(_ rows: [ReplicaSearchSuggestionsMenu.Row]) { list.setRows(rows); needsLayout = true }
    func select(_ index: Int?) { list.select(index) }
    func revealSelection() { list.revealSelection(); updateIndicators() }

    override func viewDidMoveToWindow() {
        super.viewDidMoveToWindow()
        if window != nil {
            layoutSubtreeIfNeeded()
            updateIndicators()
        }
    }

    override func layout() {
        super.layout()
        background.frame = bounds
        scrollView.frame = bounds
        list.frame = .init(origin: .zero, size: .init(width: bounds.width, height: list.fittingSize.height))
        list.layoutSubtreeIfNeeded()
        up.frame = .init(x: 0, y: bounds.height - 16, width: bounds.width, height: 16)
        down.frame = .init(x: 0, y: 0, width: bounds.width, height: 16)
        updateIndicators()
    }

    private func updateIndicators() {
        let visible = scrollView.documentVisibleRect
        up.isHidden = visible.minY <= 0
        down.isHidden = visible.maxY >= list.bounds.height
        f_10004a994(showLowEdge: visible.maxY < list.bounds.height, showHighEdge: 0 < visible.origin.y)
    }

    private func f_10004a994(showLowEdge: Bool, showHighEdge: Bool) {
        guard let layer = scrollView.layer else { return }
        let rect = scrollView.bounds
        guard showLowEdge || showHighEdge else {
            layer.mask = nil
            return
        }
        let mask = CALayer()
        mask.frame = rect
        let low: CGFloat = showLowEdge ? 18 : 0
        let high: CGFloat = showHighEdge ? 18 : 0
        let body = CALayer()
        body.frame = .init(x: 0, y: low, width: rect.width, height: rect.height - low - high)
        body.backgroundColor = NSColor.white.cgColor
        mask.addSublayer(body)
        if showLowEdge {
            mask.addSublayer(f_10004ad10(y: 0, bounds: rect, height: 18, colors: [.clear, .white]))
        }
        if showHighEdge {
            mask.addSublayer(f_10004ad10(y: rect.height - 18, bounds: rect, height: 18, colors: [.white, .clear]))
        }
        layer.mask = mask
    }

    private func f_10004ad10(y: CGFloat, bounds: NSRect, height: CGFloat,
                            colors: [NSColor]) -> CAGradientLayer {
        let gradient = CAGradientLayer()
        gradient.frame = .init(x: 0, y: y, width: bounds.width, height: height)
        gradient.colors = colors.map { $0.cgColor }
        gradient.startPoint = .init(x: 0.5, y: 0)
        gradient.endPoint = .init(x: 0.5, y: 1)
        return gradient
    }

    func dispose() {
        if let boundsObserver { NotificationCenter.default.removeObserver(boundsObserver); self.boundsObserver = nil }
    }
}

@MainActor
private final class SuggestionsList: NSView {
    private var rows: [SuggestionRowView] = []
    private var selectedIndex: Int?
    var onHover: ((Int) -> Void)?
    var onAccept: ((Int) -> Void)?
    var onExit: (() -> Void)?
    var firstTitleRectInWindow: NSRect? { rows.first?.titleRectInWindow }
    override var isFlipped: Bool { true }

    override var fittingSize: NSSize {
        .init(width: (rows.map { $0.fittingSize.width }.max() ?? 0) + 10,
              height: rows.reduce(10) { $0 + $1.fittingSize.height })
    }

    func setRows(_ items: [ReplicaSearchSuggestionsMenu.Row]) {
        select(nil)
        rows.forEach { $0.removeFromSuperview() }
        rows = items.enumerated().map { index, item in
            let row = SuggestionRowView(item: item)
            row.onHover = { [weak self] in self?.onHover?(index) }
            row.onAccept = { [weak self] in self?.onAccept?(index) }
            row.onExit = { [weak self] in self?.onExit?() }
            addSubview(row)
            return row
        }
        needsLayout = true
    }

    override func layout() {
        super.layout()
        var y: CGFloat = 5
        for row in rows {
            row.frame = .init(x: 5, y: y, width: max(0, bounds.width - 10), height: row.fittingSize.height)
            y += row.fittingSize.height
        }
    }

    func select(_ index: Int?) {
        let previous = selectedIndex
        selectedIndex = index
        selectionDidChange(from: previous)
    }

    private func selectionDidChange(from previous: Int?) {
        if let previous {
            precondition(rows.indices.contains(previous))
            rows[previous].setSelected(false)
        }
        if let selectedIndex {
            precondition(rows.indices.contains(selectedIndex))
            rows[selectedIndex].setSelected(true)
        }
    }
    func revealSelection() {
        guard let selectedIndex, selectedIndex < rows.count else { return }
        precondition(selectedIndex >= 0)
        let row = rows[selectedIndex]
        let padding = rows.first?.bounds.size.height ?? 0
        var rect = row.bounds
        rect.origin.y -= padding
        rect.size.height += padding + padding
        row.scrollToVisible(rect)
    }

    func scrollDownOneRow() {
        guard let scroll = enclosingScrollView, let document = scroll.documentView else { return }
        let origin = scroll.documentVisibleRect.origin.y
        let maximum = document.bounds.size.height - scroll.documentVisibleRect.size.height
        let candidate = origin + (rows.first?.bounds.size.height ?? 0)
        let y = candidate < maximum ? candidate : maximum
        scroll.documentView?.scroll(.init(x: 0, y: y))
        scroll.reflectScrolledClipView(scroll.contentView)
    }

    func scrollUpOneRow() {
        guard let scroll = enclosingScrollView else { return }
        let origin = scroll.documentVisibleRect.origin.y
        let y: CGFloat
        if let first = rows.first {
            let candidate = origin - first.bounds.size.height
            y = 0 <= candidate ? candidate : 0
        } else {
            y = origin < 0 ? 0 : origin
        }
        scroll.documentView?.scroll(.init(x: 0, y: y))
        scroll.reflectScrolledClipView(scroll.contentView)
    }
}

@MainActor
private final class SuggestionRowView: NSView {
    private var storedTitle: NSTextField?
    private var storedImage: NSImageView?
    private var storedStack: NSStackView?
    private var title: NSTextField { f_10000ed50() }
    private var image: NSImageView { f_10000ee38() }
    private var stack: NSStackView { f_10000eedc() }
    private let item: ReplicaSearchSuggestionsMenu.Row
    private var selected = false
    private var hoverArea: NSTrackingArea?
    var onHover: (() -> Void)?
    var onExit: (() -> Void)?
    var onAccept: (() -> Void)?
    var titleRectInWindow: NSRect { title.convert(title.bounds, to: nil) }

    init(item: ReplicaSearchSuggestionsMenu.Row) {
        self.item = item
        super.init(frame: .zero)
        stack.translatesAutoresizingMaskIntoConstraints = false
        image.translatesAutoresizingMaskIntoConstraints = false
        stack.addArrangedSubview(image)
        stack.addArrangedSubview(title)
        addSubview(stack)
        NSLayoutConstraint.activate([
            stack.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 8),
            stack.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -8),
            stack.topAnchor.constraint(equalTo: topAnchor, constant: 3),
            stack.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -3),
            image.widthAnchor.constraint(equalToConstant: 18),
            image.heightAnchor.constraint(equalToConstant: 18)
        ])
        wantsLayer = true
        layer?.cornerRadius = 7
        layer?.cornerCurve = .continuous
        updateSelectionAppearance()
    }

    required init?(coder: NSCoder) { return nil }

    private func f_10000ed50() -> NSTextField {
        if let storedTitle { return storedTitle }
        let field = NSTextField(labelWithString: item.title)
        field.lineBreakMode = .byTruncatingTail
        field.maximumNumberOfLines = 1
        field.font = OriginalSearchAppearance.f_1001ff928()
        storedTitle = field
        return field
    }

    private func f_10000ee38() -> NSImageView {
        if let storedImage { return storedImage }
        let view = NSImageView()
        view.imageScaling = .scaleProportionallyDown
        view.image = item.image
        view.isHidden = item.image == nil
        storedImage = view
        return view
    }

    private func f_10000eedc() -> NSStackView {
        if let storedStack { return storedStack }
        let view = NSStackView()
        view.orientation = .horizontal
        view.alignment = .centerY
        view.spacing = 7
        storedStack = view
        return view
    }

    override func layout() {
        super.layout()
        updateSelectionAppearance()
    }
    override var fittingSize: NSSize {
        let iconWidth: CGFloat = image.isHidden ? 0 : 25
        return .init(width: title.fittingSize.width + iconWidth + 16,
                     height: max(title.fittingSize.height, image.isHidden ? 0 : 18) + 6)
    }
    func setSelected(_ value: Bool) {
        guard selected != value else { return }
        selected = value
        needsLayout = true
    }

    private func updateSelectionAppearance() {
        layer?.backgroundColor = selected ? NSColor.controlAccentColor.cgColor : NSColor.clear.cgColor
        let primary = selected ? NSColor.white : OriginalSearchAppearance.f_1001fec18()!
        let secondary = selected ? NSColor.white.withAlphaComponent(0.6) : NSColor.secondaryLabelColor
        image.contentTintColor = primary
        title.attributedStringValue = OriginalSuggestionAttributedTitle.f_100010984(
            primary: primary, secondary: secondary, title: item.title, query: item.matchQuery)
    }
    override func updateTrackingAreas() {
        super.updateTrackingAreas()
        if let hoverArea { removeTrackingArea(hoverArea) }
        let area: NSTrackingArea? = NSTrackingArea(rect: bounds, options: .init(rawValue: 0x81), owner: self, userInfo: nil)
        hoverArea = area
        if let area { addTrackingArea(area) }
    }
    override func mouseEntered(with event: NSEvent) { onHover?() }
    override func mouseExited(with event: NSEvent) { onExit?() }
    override func mouseDown(with event: NSEvent) { onAccept?() }
}

@MainActor
private final class SuggestionsScrollIndicator: NSView {
    private var storedImage: NSImageView?
    private var image: NSImageView { f_10004afcc() }
    private var hoverArea: NSTrackingArea?
    private var isMouseInside = false
    private var scrollTimer: OriginalSuggestionScrollTimer?
    var canScroll: () -> Bool = { false }
    var onScroll: (() -> Void)?
    init(symbol: String) {
        super.init(frame: .zero)
        let symbolImage: NSImage
        if NSImage(systemSymbolName: symbol, accessibilityDescription: nil) == nil {
            symbolImage = NSImage(systemSymbolName: "questionmark.square", accessibilityDescription: nil)!
        } else {
            symbolImage = NSImage(systemSymbolName: symbol, accessibilityDescription: nil)!
        }
        image.image = symbolImage.withSymbolConfiguration(.init(pointSize: 12, weight: .medium))
        image.contentTintColor = .secondaryLabelColor
        addSubview(image)
        wantsLayer = true
        layer?.backgroundColor = NSColor.windowBackgroundColor.withAlphaComponent(0.95).cgColor
    }
    required init?(coder: NSCoder) { return nil }

    private func f_10004afcc() -> NSImageView {
        if let storedImage { return storedImage }
        let view = NSImageView()
        storedImage = view
        return view
    }

    override func layout() { super.layout(); image.frame = .init(x: (bounds.width - 12) / 2, y: (bounds.height - 12) / 2, width: 12, height: 12) }
    override func updateTrackingAreas() {
        super.updateTrackingAreas()
        if let hoverArea { removeTrackingArea(hoverArea) }
        let area: NSTrackingArea? = NSTrackingArea(rect: bounds, options: .init(rawValue: 0x83), owner: self, userInfo: nil)
        hoverArea = area
        if let area { addTrackingArea(area) }
    }
    override func mouseEntered(with event: NSEvent) { isMouseInside = true }
    override func mouseMoved(with event: NSEvent) {
        guard isMouseInside, canScroll(), scrollTimer == nil else { return }
        scrollTimer = OriginalSuggestionScrollTimer(interval: 0.075, repeats: true) { [weak self] in
            MainActor.assumeIsolated { self?.onScroll?() }
        }
    }
    override func mouseExited(with event: NSEvent) {
        isMouseInside = false
        scrollTimer = nil
    }
}

/// Paste 0x100385984 / 0x100385acc: release of the wrapper invalidates its scheduled timer.
private final class OriginalSuggestionScrollTimer {
    private let timer: Timer

    init(interval: TimeInterval, repeats: Bool, action: @escaping () -> Void) {
        timer = Timer.scheduledTimer(withTimeInterval: interval, repeats: repeats) { _ in action() }
    }

    func invalidate() { timer.invalidate() }

    deinit { invalidate() }
}
