import AppKit
import Combine
import PastoCore

/// The editable image renderer shares the already recovered zoom/Live Text view.
@MainActor
final class ReplicaImagePreviewContent: NSView, OriginalPreviewEditableContent, NSUserInterfaceValidations {
    private weak var state: ReplicaUIState?
    private let itemID: UUID
    private let checkerboardView = OriginalImageCheckerboardView(frame: .zero)
    private let zoomView = OriginalZoomableImageView()
    private let metadataHost = NSView()
    private let editingUndoManager = UndoManager()
    private var itemObservation: AnyCancellable?
    private var sourcePayloads: [String: Data] = [:]
    private var imageMetadataSize: NSSize = .zero
    private var quarterTurns = 0
    private var isEditing = false
    private(set) var canCommit = false
    var onCanCommitEditing: ((Bool) -> Void)?
    var previewMetadataView: NSView? { metadataHost }

    private lazy var toolbar: NSStackView = {
        let left = OriginalToolbarButton(symbol: "rotate.left",
            shortcut: .init(keyCode: Int(OriginalShortcutFunctions.f_1001e94d4("l")),
                            internalModifiers: NSEvent.ModifierFlags.command.rawValue),
            toolTip: String(localized: OriginalPreviewLocalization.f_1001bee08())) { [weak self] _ in
                self?.rotateLeft()
            }
        let right = OriginalToolbarButton(symbol: "rotate.right",
            shortcut: .init(keyCode: Int(OriginalShortcutFunctions.f_1001e94d4("r")),
                            internalModifiers: NSEvent.ModifierFlags.command.rawValue),
            toolTip: String(localized: OriginalPreviewLocalization.f_1001bef88())) { [weak self] _ in
                self?.rotateRight()
            }
        return NSStackView(views: [left, right])
    }()

    var previewEditingToolbar: NSView? { toolbar }

    init(state: ReplicaUIState, item: ClipboardItem) {
        self.state = state
        itemID = item.id
        super.init(frame: .zero)
        addSubview(checkerboardView)
        checkerboardView.translatesAutoresizingMaskIntoConstraints = false
        addSubview(zoomView)
        zoomView.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate(f_1003e57b8())
        replaceDisplayedItem(item)
        itemObservation = state.store.$items.sink { [weak self] items in
            MainActor.assumeIsolated {
                guard let self else { return }
                guard let current = items.first(where: { $0.id == self.itemID }),
                      !current.isDeleted, current.kind == .image else {
                    self.window?.performClose(nil)
                    return
                }
                if !self.isEditing { self.replaceDisplayedItem(current) }
            }
        }
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    private func f_1003e57b8() -> [NSLayoutConstraint] {
        [
            checkerboardView.topAnchor.constraint(equalTo: topAnchor),
            checkerboardView.leadingAnchor.constraint(equalTo: leadingAnchor),
            checkerboardView.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -CGFloat.zero),
            checkerboardView.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -CGFloat.zero),
            zoomView.topAnchor.constraint(equalTo: topAnchor),
            zoomView.leadingAnchor.constraint(equalTo: leadingAnchor),
            zoomView.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -CGFloat.zero),
            zoomView.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -CGFloat.zero)
        ]
    }

    override var acceptsFirstResponder: Bool { true }
    override var undoManager: UndoManager? { editingUndoManager }

    var preferredPreviewSize: NSSize {
        let imageSize = imageMetadataSize
        let screen = NSScreen.main!.frame.size
        let halfWidth = screen.width * 0.5
        let halfHeight = screen.height * 0.5
        // Original 0x1003e6afc returns the source dimensions when both comparisons
        // are nonnegative or unordered; it does not impose a minimum canvas size.
        if !(halfWidth < imageSize.width), !(halfHeight < imageSize.height) { return imageSize }
        let widthScale = halfWidth / imageSize.width
        let heightScale = halfHeight / imageSize.height
        let scale = heightScale < widthScale ? heightScale : widthScale
        return NSSize(width: imageSize.width * scale, height: imageSize.height * scale)
    }

    func beginPreviewEditing() {
        isEditing = true
        quarterTurns = 0
        editingUndoManager.removeAllActions()
        zoomView.f_100240be8(true)
        updateMetadataAndCommitState()
        window?.makeFirstResponder(self)
    }

    func cancelPreviewEditing() {
        finishEditing()
    }

    func commitPreviewEditing() {
        if canCommit, let image = zoomView.f_100240a18(), let state {
            do {
                try state.store.updateImageItem(id: itemID, payloads: Self.encodedPayloads(image))
                state.normalizeSelection()
            } catch { state.controller?.presentError(error) }
        }
        finishEditing()
    }

    private func finishEditing() {
        isEditing = false
        quarterTurns = 0
        editingUndoManager.removeAllActions()
        if let current = state?.store.items.first(where: { $0.id == itemID }) {
            replaceDisplayedItem(current, force: true)
        }
    }

    private func replaceDisplayedItem(_ item: ClipboardItem, force: Bool = false) {
        imageMetadataSize = item.decodedImagePreviewMetadata?.size ?? .zero
        let payloads = item.payloads.filter { !$0.key.hasPrefix("com.pastereplica.internal.recognized-") }
        guard force || payloads != sourcePayloads else { return }
        sourcePayloads = payloads
        zoomView.f_100240a64(itemImage(item))
        zoomView.f_100240be8(false)
        updateMetadataAndCommitState()
    }

    private func rotateRight() {
        guard isEditing else { return }
        let next = quarterTurns + 1
        quarterTurns = next > 3 ? 0 : next
        rotateDisplayedImage(degrees: -90)
        editingUndoManager.registerUndo(withTarget: self) { target in
            MainActor.assumeIsolated { target.rotateLeft() }
        }
    }

    private func rotateLeft() {
        guard isEditing else { return }
        let next = quarterTurns - 1
        quarterTurns = next < 0 ? 3 : next
        rotateDisplayedImage(degrees: 90)
        editingUndoManager.registerUndo(withTarget: self) { target in
            MainActor.assumeIsolated { target.rotateRight() }
        }
    }

    private func rotateDisplayedImage(degrees: Double) {
        let rotated = zoomView.f_100240a18().map { Self.f_100207054($0, degrees: degrees) }
        zoomView.f_100240a64(rotated)
        updateMetadataAndCommitState()
    }

    private func updateMetadataAndCommitState() {
        guard let image = zoomView.f_100240a18() else { return }
        let metadata = ReplicaImageDimensionsView(image: image)
        metadataHost.subviews = []
        metadata.translatesAutoresizingMaskIntoConstraints = false
        metadataHost.addSubview(metadata)
        NSLayoutConstraint.activate([
            metadata.topAnchor.constraint(equalTo: metadataHost.topAnchor),
            metadata.leadingAnchor.constraint(equalTo: metadataHost.leadingAnchor),
            metadata.bottomAnchor.constraint(equalTo: metadataHost.bottomAnchor),
            metadata.trailingAnchor.constraint(equalTo: metadataHost.trailingAnchor)
        ])
        canCommit = quarterTurns != 0
        onCanCommitEditing?(canCommit)
    }

    @objc private func undo(_ sender: Any?) { editingUndoManager.undo() }
    @objc private func redo(_ sender: Any?) { editingUndoManager.redo() }

    func validateUserInterfaceItem(_ item: NSValidatedUserInterfaceItem) -> Bool {
        if item.action == #selector(undo(_:)) { return isEditing && editingUndoManager.canUndo }
        if item.action == #selector(redo(_:)) { return isEditing && editingUndoManager.canRedo }
        return true
    }

    override func performKeyEquivalent(with event: NSEvent) -> Bool {
        if isEditing, event.charactersIgnoringModifiers?.lowercased() == "z" {
            let flags = event.modifierFlags.intersection(.deviceIndependentFlagsMask)
            if flags == .command { editingUndoManager.undo(); return true }
            if flags == [.command, .shift] { editingUndoManager.redo(); return true }
        }
        return super.performKeyEquivalent(with: event)
    }

    /// Paste 0x100207054 always swaps the canvas dimensions, including for
    /// angles other than the two quarter-turns used by the image toolbar.
    static func f_100207054(_ image: NSImage, degrees: Double) -> NSImage {
        let originalSize = image.size
        let size = NSSize(width: image.size.height, height: image.size.width)
        let rotated = NSImage(size: size)
        rotated.lockFocus()
        NSGraphicsContext.current?.imageInterpolation = .high
        let transform = CGAffineTransform.identity.translatedBy(x: size.width * 0.5, y: size.height * 0.5)
            .rotated(by: degrees * .pi / 180)
            .translatedBy(x: image.size.width * -0.5, y: image.size.height * -0.5)
        NSGraphicsContext.current?.cgContext.concatenate(transform)
        image.draw(at: .zero, from: NSRect(origin: .zero, size: originalSize), operation: .copy, fraction: 1)
        rotated.unlockFocus()
        return rotated
    }

    private static func encodedPayloads(_ image: NSImage) throws -> [String: Data] {
        if let data = OriginalPasteboardImageEncoding.f_1003c89c8(image) {
            return [NSPasteboard.PasteboardType.png.rawValue: data]
        }
        if let data = OriginalImagePreviewMetadataGenerator.f_1003c8b58(image, compression: 0.5) {
            return ["public.jpeg": data]
        }
        throw OriginalPasteboardItemCreationError.unsupportedContent
    }

}

@MainActor
private final class ReplicaImageDimensionsView: NSStackView {
    init(image: NSImage) {
        super.init(frame: .zero)
        let size = image.size
        let label = NSTextField(labelWithString: "\(Int(size.width)) × \(Int(size.height))")
        label.font = OriginalSearchAppearance.f_1001ff928()
        label.textColor = OriginalToolbarAppearance.secondaryForeground()
        label.isEditable = false
        label.isSelectable = false
        label.isBordered = false
        label.drawsBackground = false
        let spacer = NSView()
        spacer.setContentHuggingPriority(.init(250), for: .horizontal)
        spacer.setContentCompressionResistancePriority(.init(250), for: .horizontal)
        addArrangedSubview(label)
        addArrangedSubview(spacer)
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }
}
