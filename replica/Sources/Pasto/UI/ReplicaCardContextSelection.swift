import AppKit
import SwiftUI

/// Selects the card before AppKit dispatches the event that opens its context menu.
/// The view remains passive so existing clicks, editing and dragging keep their targets.
@MainActor
struct ReplicaCardContextSelection: NSViewRepresentable {
    let onContextMenu: () -> Void

    func makeNSView(context: Context) -> EventView {
        let view = EventView()
        view.onContextMenu = onContextMenu
        view.installMonitor()
        return view
    }

    func updateNSView(_ view: EventView, context: Context) {
        view.onContextMenu = onContextMenu
    }

    static func dismantleNSView(_ view: EventView, coordinator: ()) {
        view.removeMonitor()
        view.onContextMenu = nil
    }

    final class EventView: NSView {
        var onContextMenu: (() -> Void)?
        private var monitor: Any?

        override func hitTest(_ point: NSPoint) -> NSView? { nil }

        func installMonitor() {
            guard monitor == nil else { return }
            monitor = NSEvent.addLocalMonitorForEvents(matching: [.rightMouseDown, .leftMouseDown]) { [weak self] event in
                MainActor.assumeIsolated {
                    guard let self, !self.isHiddenOrHasHiddenAncestor,
                          let window = self.window, event.window === window,
                          event.type == .rightMouseDown || event.modifierFlags.contains(.control),
                          self.visibleRect.contains(self.convert(event.locationInWindow, from: nil)) else { return event }
                    self.onContextMenu?()
                    return event
                }
            }
        }

        func removeMonitor() {
            if let monitor { NSEvent.removeMonitor(monitor) }
            monitor = nil
        }

        deinit { MainActor.assumeIsolated { removeMonitor() } }
    }
}
