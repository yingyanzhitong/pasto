import AppKit
import Combine
import Foundation

@MainActor
public enum OriginalWindowVisualEffects {
    /// Paste 0x10021d7a4: collect direct NSVisualEffectView siblings and return the first.
    public static func f_10021d7a4(window: NSWindow) -> NSVisualEffectView? {
        guard let parent = window.contentView?.superview else { return nil }
        return parent.subviews.compactMap { $0 as? NSVisualEffectView }.first
    }
}

@MainActor
public final class OriginalPreviewWindow: NSPanel {
    /// Paste 0x1000af8a0. The recovered original calls NSPanel's designated initializer.
    public init(recovered: Void = ()) {
        super.init(contentRect: .zero, styleMask: .init(rawValue: 0x801b),
                   backing: .buffered, defer: true)
        animationBehavior = .none
        OriginalWindowVisualEffects.f_10021d7a4(window: self)?.blendingMode = .behindWindow
        OriginalWindowVisualEffects.f_10021d7a4(window: self)?.material = .popover
        standardWindowButton(.miniaturizeButton)?.isHidden = true
        standardWindowButton(.closeButton)?.isHidden = true
        standardWindowButton(.zoomButton)?.isHidden = true
        titlebarAppearsTransparent = true
        isMovableByWindowBackground = true
        hidesOnDeactivate = false
        level = .init(rawValue: 3)
    }

    /// Paste 0x1000afaa8: activation precedes the superclass key-window transition.
    public override func becomeKey() {
        NSApp.activate(ignoringOtherApps: true)
        super.becomeKey()
    }
}

public struct OriginalTopmostPreview: Equatable {
    public var itemIdentifier: String
    public var isEditing: Bool

    public init(itemIdentifier: String, isEditing: Bool) {
        self.itemIdentifier = itemIdentifier
        self.isEditing = isEditing
    }

    /// Paste 0x10008764c: compare the string before the editing flag.
    public static func f_10008764c(_ lhs: Self, _ rhs: Self) -> Bool {
        guard lhs.itemIdentifier == rhs.itemIdentifier else { return false }
        return lhs.isEditing == rhs.isEditing
    }

    public static func == (lhs: Self, rhs: Self) -> Bool { f_10008764c(lhs, rhs) }
}

/// Original entries use Core Data object-ID URLs as AnyHashable identities.
/// The independent replica supplies its stable local item identity at the boundary.
@MainActor
public final class OriginalPreviewWindowRegistry: NSObject, ObservableObject {
    private struct Entry {
        var itemIdentity: AnyHashable
        var itemIdentifier: String
        var window: OriginalPreviewWindow
        var isEditing: Bool
    }

    private var entries: [Entry] = []
    /// Replica appearance propagation; this adapter does not represent an original function.
    public var windows: [OriginalPreviewWindow] { entries.map(\.window) }
    public var popoverItemIdentifier: String?
    @Published public private(set) var topmost: OriginalTopmostPreview?
    public var onAllPreviewsClosed: (() -> Void)?

    /// Paste 0x100087ef0 / 0x100087ffc: the empty registry and published nil state.
    public override init() { super.init() }

    /// Paste 0x10008747c: return the first window with an equal stable item identity.
    public func f_10008747c(itemIdentity: AnyHashable) -> OriginalPreviewWindow? {
        entries.first { $0.itemIdentity == itemIdentity }?.window
    }

    /// Paste 0x100086c10: replace the item's window, append, observe closing, publish topmost.
    public func f_100086c10(window: OriginalPreviewWindow, itemIdentity: AnyHashable,
                          itemIdentifier: String, isEditing: Bool) {
        f_10008747c(itemIdentity: itemIdentity)?.close()
        entries.removeAll { $0.itemIdentity == itemIdentity }
        entries.append(Entry(itemIdentity: itemIdentity, itemIdentifier: itemIdentifier,
                             window: window, isEditing: isEditing))
        NotificationCenter.default.addObserver(self, selector: #selector(handleWindowWillClose(_:)),
                                              name: NSWindow.willCloseNotification, object: window)
        f_100087864()
    }

    /// Paste 0x10008727c: update the last matching identifier; publish only if it is topmost.
    public func f_10008727c(isEditing: Bool, itemIdentifier: String) {
        guard let index = entries.lastIndex(where: { $0.itemIdentifier == itemIdentifier }) else { return }
        entries[index].isEditing = isEditing
        if index == entries.count - 1 { f_100087864() }
    }

    /// Paste 0x100087864: detached windows take precedence over a nonediting popover.
    public func f_100087864() {
        if let last = entries.last {
            topmost = OriginalTopmostPreview(itemIdentifier: last.itemIdentifier, isEditing: last.isEditing)
        } else if let popoverItemIdentifier {
            topmost = OriginalTopmostPreview(itemIdentifier: popoverItemIdentifier, isEditing: false)
        } else { topmost = nil }
    }

    /// Paste 0x1000879dc: remove all equal windows, then notify the nonempty-to-empty transition.
    public func f_1000879dc(window: OriginalPreviewWindow) {
        let previousCount = entries.count
        entries.removeAll { $0.window.isEqual(window) }
        f_100087864()
        if previousCount > 0, entries.isEmpty { onAllPreviewsClosed?() }
    }

    /// Paste 0x100087d3c: unrelated or absent notification objects have no effect.
    @objc private func handleWindowWillClose(_ notification: Notification) {
        guard let window = notification.object as? OriginalPreviewWindow else { return }
        f_1000879dc(window: window)
    }

    /// Paste 0x10008771c: unregister the selector observations before object destruction.
    deinit { NotificationCenter.default.removeObserver(self) }
}
