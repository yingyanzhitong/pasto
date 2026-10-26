import AppKit

@MainActor
public final class OriginalFilterBrowserPopover: NSPopover, NSPopoverDelegate {
    public private(set) var isDisplayed = false
    public var onWillClose: (() -> Void)?

    public override init() {
        super.init()
        behavior = .transient
        animates = true
        delegate = self
        NotificationCenter.default.addObserver(self, selector: #selector(close),
            name: OriginalPreviewPopover.mainWindowWillCloseNotification, object: nil)
    }

    public required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    public func present(_ controller: NSViewController, relativeTo anchor: NSView) {
        if isDisplayed { close(); return }
        controller.view.wantsLayer = true
        controller.view.layer?.backgroundColor = CGColor.clear
        contentViewController = controller
        show(relativeTo: anchor.bounds, of: anchor, preferredEdge: .minY)
        animates = false
    }

    public func f_100008bc0() {
        animates = true
        isDisplayed = false
        contentViewController = nil
        onWillClose?()
    }

    public func popoverWillClose(_ notification: Notification) { f_100008bc0() }
    public func popoverWillShow(_ notification: Notification) { isDisplayed = true }

    deinit { NotificationCenter.default.removeObserver(self) }
}
