import AppKit

/// The explicit-window branch of the recovered WindowTransition.
/// The application's owner retains this adapter for the presented window's lifetime.
@MainActor
public final class OriginalPreviewWindowTransition: NSObject, NSWindowDelegate {
    public let window: NSWindow
    public var onPresented: ((NSWindow) -> Void)?
    public var onDismissed: ((Bool) -> Void)?

    public init(window: NSWindow) {
        self.window = window
        super.init()
        window.isReleasedWhenClosed = false
    }

    /// Paste 0x1001ae4f0: presentation and its callback are synchronous.
    public func present(_ controller: NSViewController) {
        window.delegate = self
        let view = controller.view
        view.setFrameSize(controller.view.fittingSize)
        window.contentViewController = controller
        window.makeKeyAndOrderFront(nil)
        window.orderFrontRegardless()
        onPresented?(window)
    }

    /// Paste 0x1001ae360: release content before reporting a window close.
    public func windowWillClose(_ notification: Notification) {
        window.contentViewController = nil
        onDismissed?(true)
    }
}
