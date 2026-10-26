import AppKit

@MainActor
final class ReplicaPanelResizeHandle: NSView {
    var onLiveResize: ((NSSize) -> Void)?
    var onEndResize: (() -> Void)?
    var onResetSize: (() -> Void)?
    var onGestureFinished: (() -> Void)?
    private var initialLocation: NSPoint?
    private var initialWindowSize: NSSize?

    override func mouseDown(with event: NSEvent) {
        super.mouseDown(with: event)
        initialLocation = event.locationInWindow
        initialWindowSize = window?.frame.size
        if event.clickCount == 2 { onResetSize?() }
    }

    override func mouseDragged(with event: NSEvent) {
        super.mouseDragged(with: event)
        guard let initialLocation, let initialWindowSize else { return }
        onLiveResize?(NSSize(width: initialWindowSize.width,
                             height: initialWindowSize.height + event.locationInWindow.y - initialLocation.y))
    }

    override func mouseUp(with event: NSEvent) {
        super.mouseUp(with: event)
        initialLocation = nil
        initialWindowSize = nil
        onGestureFinished?()
        if event.clickCount < 2 { onEndResize?() }
    }

    override func resetCursorRects() {
        super.resetCursorRects()
        addCursorRect(bounds, cursor: .resizeUpDown)
    }
}
