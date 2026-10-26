import AppKit
import SwiftUI

/// Supplies the collection card's real view coordinates to the native popover.
@MainActor
struct ReplicaItemPreviewAnchor: NSViewRepresentable {
    let itemID: UUID
    weak var controller: ReplicaUIController?

    func makeNSView(context: Context) -> AnchorView { AnchorView() }

    func updateNSView(_ view: AnchorView, context: Context) {
        if let previous = view.itemID, previous != itemID {
            view.controller?.removePreviewAnchor(for: previous, view: view)
        }
        view.itemID = itemID
        view.controller = controller
        controller?.registerPreviewAnchor(for: itemID, view: view)
    }

    static func dismantleNSView(_ view: AnchorView, coordinator: ()) {
        if let itemID = view.itemID { view.controller?.removePreviewAnchor(for: itemID, view: view) }
    }

    final class AnchorView: NSView {
        var itemID: UUID?
        weak var controller: ReplicaUIController?
        override func hitTest(_ point: NSPoint) -> NSView? { nil }
    }
}

@MainActor
final class WeakReplicaPreviewAnchor {
    weak var view: NSView?
    init(_ view: NSView) { self.view = view }
}
