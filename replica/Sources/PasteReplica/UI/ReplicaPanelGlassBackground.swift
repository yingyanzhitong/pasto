import AppKit
import SwiftUI
import PasteReplicaObjC

/// One native glass surface behind the toolbar and card collection.
struct ReplicaPanelGlassBackground: NSViewRepresentable {
    let cornerRadius: CGFloat

    func makeNSView(context: Context) -> PRPanelGlassBackground {
        let view = PRPanelGlassBackground(frame: .zero)
        view.cornerRadius = cornerRadius
        return view
    }

    func updateNSView(_ view: PRPanelGlassBackground, context: Context) {
        view.cornerRadius = cornerRadius
    }
}
