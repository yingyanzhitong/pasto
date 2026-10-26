import AppKit

/// The original animates its entire MainView in an unflipped window coordinate space.
/// Hosting and the top resize handle remain children of that same moving content.
@MainActor
final class ReplicaPanelContentView: NSView {
    override var isFlipped: Bool { false }
}
