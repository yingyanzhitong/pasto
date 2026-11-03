import AppKit
import Combine

/// The text model owns its input and derived values independently of the preview view.
@MainActor
public final class OriginalTextPreviewModel {
    public var onChange: (() -> Void)?
    public private(set) var originalText = NSAttributedString(string: "")
    public private(set) var editingText = NSAttributedString(string: "")
    private var input: ClipboardRestoreItem
    private var observation: AnyCancellable?
    public var item: ClipboardRestoreItem { input }

    public init?(input: ClipboardRestoreItem) {
        guard input.hasNativeEntity else { return nil }
        self.input = input
        observation = input.observeChanges { [weak self] current in
            Self.receive(current, from: { [weak self] in self })
        }
        reload()
    }

    // 3c05d4: read the held entity's first representation, then replace both model values.
    public func reload() {
        guard let object = input.nativeObject else { preconditionFailure("Text model requires a native item") }
        let items = ClipboardItemDataPersistence.readItems(from: object) ?? []
        originalText = items.first?.f_10037d33c() ?? NSAttributedString(string: "")
        editingText = OriginalPreviewAttributedText.normalizedEditingText(originalText)
    }

    // 3c04f0: each phase has its own strong-owner scope; retain the callback, not the owner.
    private static func receive(_ current: ClipboardRestoreItem,
                                from loadOwner: () -> OriginalTextPreviewModel?) {
        guard !current.isDeleted else { return }
        replaceInputAndReleasePrevious(current, from: loadOwner)
        reload(from: loadOwner)
        let callback = changeCallback(from: loadOwner)
        callback?()
    }

    @inline(never)
    private static func replaceInputAndReleasePrevious(_ current: ClipboardRestoreItem,
                                                       from loadOwner: () -> OriginalTextPreviewModel?) {
        withExtendedLifetime(replaceInput(current, from: loadOwner)) {}
    }

    @inline(never)
    private static func replaceInput(_ current: ClipboardRestoreItem,
                                     from loadOwner: () -> OriginalTextPreviewModel?) -> ClipboardRestoreItem? {
        guard let owner = loadOwner() else { return nil }
        let previous = owner.input
        owner.input = current
        return previous
    }

    @inline(never)
    private static func reload(from loadOwner: () -> OriginalTextPreviewModel?) {
        guard let owner = loadOwner() else { return }
        owner.reload()
    }

    @inline(never)
    private static func changeCallback(from loadOwner: () -> OriginalTextPreviewModel?) -> (() -> Void)? {
        guard let owner = loadOwner() else { return nil }
        return owner.onChange
    }
}
