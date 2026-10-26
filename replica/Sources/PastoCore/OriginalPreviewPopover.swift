import AppKit
import Combine
import Foundation

/// Native popover lifecycle recovered from ItemCollectionView.PreviewPopover.
/// Content rendering and inline editing are supplied by the replica's item-view adapter.
@MainActor
public final class OriginalPreviewPopover: NSPopover, NSPopoverDelegate {
    public static let mainWindowWillCloseNotification = Notification.Name("mainWindowWillClose")
    public private(set) var isDisplayed = false
    public private(set) var itemIdentity: AnyHashable?
    public private(set) var itemIdentifier: String?
    public var onWillClose: (() -> Void)?
    public var makeContentView: ((_ itemIdentity: AnyHashable,
                                  _ itemIdentifier: String) -> OriginalItemPreviewView?)?
    private let registry: OriginalPreviewWindowRegistry
    private let isScreenSharingContentVisible: () -> Bool
    private var visibilityObservation: AnyCancellable?

    public init(registry: OriginalPreviewWindowRegistry,
                isScreenSharingContentVisible: @escaping () -> Bool,
                visibilityChanges: AnyPublisher<Bool, Never>) {
        self.registry = registry
        self.isScreenSharingContentVisible = isScreenSharingContentVisible
        super.init()
        behavior = .transient
        animates = true
        delegate = self
        NotificationCenter.default.addObserver(self, selector: #selector(close),
                                              name: Self.mainWindowWillCloseNotification, object: nil)
        visibilityObservation = visibilityChanges.prepend(isScreenSharingContentVisible())
            .sink { [weak self] _ in
                MainActor.assumeIsolated { self?.f_100029f60() }
            }
    }

    public required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    /// The recovered display mechanics in 0x10002964c, after the item-view factory returns.
    public func show(itemIdentity: AnyHashable, itemIdentifier: String,
                     contentView: NSView, relativeTo anchor: NSView) {
        self.itemIdentity = itemIdentity
        self.itemIdentifier = itemIdentifier
        registry.f_10008747c(itemIdentity: itemIdentity)?.close()
        if let preview = contentView as? OriginalItemPreviewView {
            preview.onBeginEditing = { [weak self] in
                self?.f_1000298b0(itemIdentity: itemIdentity)
            }
        }
        let controller = NSViewController()
        controller.preferredContentSize = contentView.frame.size
        controller.view = contentView
        contentViewController = controller
        show(relativeTo: anchor.bounds, of: anchor, preferredEdge: .maxY)
        animates = false
        anchor.window?.makeFirstResponder(nil)
    }

    /// Paste 0x100029f60: only the content controller's actual window is affected.
    public func f_100029f60() {
        guard let window = contentViewController?.view.window else { return }
        window.sharingType = isScreenSharingContentVisible() ? .readOnly : .none
    }

    /// Paste 0x100029e6c: mark displayed, apply sharing policy, publish changed item identity.
    @discardableResult
    public func f_100029e6c() -> Int {
        isDisplayed = true
        f_100029f60()
        if let itemIdentifier, registry.popoverItemIdentifier != itemIdentifier {
            registry.popoverItemIdentifier = itemIdentifier
            registry.f_100087864()
        }
        return 0
    }

    /// Paste 0x100029da8: restore animation, notify owner, then clear the tracked popover.
    @discardableResult
    public func f_100029da8() -> Int {
        animates = true
        isDisplayed = false
        onWillClose?()
        if registry.popoverItemIdentifier != nil {
            registry.popoverItemIdentifier = nil
            registry.f_100087864()
        }
        return 0
    }

    public func popoverWillShow(_ notification: Notification) { f_100029e6c() }
    public func popoverWillClose(_ notification: Notification) { f_100029da8() }

    /// Paste 0x10002a1e8: AppKit may detach this popover.
    public func popoverShouldDetach(_ popover: NSPopover) -> Bool { true }

    /// Paste 0x10002a26c: detaching requests a nonediting window kept open after editing.
    public func detachableWindow(for popover: NSPopover) -> NSWindow? {
        f_100029a80(beginEditing: false, keepOpenAfterEditing: true)
    }

    /// Paste 0x1000298b0: an existing detached preview prevents a second edit transition.
    public func f_1000298b0(itemIdentity: AnyHashable) {
        guard registry.f_10008747c(itemIdentity: itemIdentity) == nil else { return }
        detachForEditing()
    }

    /// Paste 0x100029a80 after the local item-view adapter resolves the content dependency.
    public func f_100029a80(beginEditing: Bool, keepOpenAfterEditing: Bool) -> OriginalPreviewWindow? {
        guard let itemIdentity, let itemIdentifier else { return nil }
        let window = OriginalPreviewWindow()
        guard let preview = makeContentView?(itemIdentity, itemIdentifier) else { return nil }
        preview.onEndEditing = {
            if !keepOpenAfterEditing { window.close() }
        }
        let manager = registry
        preview.onEditingStateChanged = { editing in
            manager.f_10008727c(isEditing: editing, itemIdentifier: itemIdentifier)
        }
        if beginEditing { preview.f_10007be8c() }
        let controller = NSViewController()
        controller.view = preview
        window.contentViewController = controller
        manager.f_100086c10(window: window, itemIdentity: itemIdentity,
                           itemIdentifier: itemIdentifier, isEditing: beginEditing)
        return window
    }

    /// The screen-geometry transition recovered from 0x100029958.
    public func detachForEditing() {
        guard let view = contentViewController?.view, let oldWindow = view.window else { return }
        let screenFrame = oldWindow.convertToScreen(view.frame)
        oldWindow.alphaValue = 0
        close()
        guard let window = f_100029a80(beginEditing: true, keepOpenAfterEditing: false) else { return }
        window.setFrame(screenFrame, display: false)
        window.makeKeyAndOrderFront(nil)
    }

    deinit { NotificationCenter.default.removeObserver(self) }
}
