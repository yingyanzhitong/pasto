import AppKit
import Combine
import PastoCore

/// Shares preview chrome and editing transitions; per-kind content retains its own contract.
@MainActor
func makeOriginalReplicaPreview(state: ReplicaUIState, item: ClipboardItem) -> OriginalItemPreviewView {
    if let textPreview = makeOriginalReplicaTextPreview(state: state, item: item) { return textPreview }
    let content: NSView
    let contentSize: NSSize
    let metadata: NSView?
    let screenSize = NSScreen.main?.frame.size ?? .zero
    switch item.kind {
    case .image:
        let image = ReplicaImagePreviewContent(state: state, item: item)
        content = image
        contentSize = image.preferredPreviewSize
        metadata = image.previewMetadataView
    case .color:
        let color = ReplicaColorPreviewContent(state: state, item: item)
        content = color
        contentSize = color.preferredPreviewSize
        metadata = color.previewMetadataView
    case .link:
        let link = ReplicaLinkPreviewContent(state: state, item: item)
        content = link
        contentSize = link.preferredPreviewSize
        metadata = link.previewMetadataView
    case .files:
        let files = ReplicaFilePreviewContent(state: state, item: item)
        content = files
        contentSize = files.preferredPreviewSize
        metadata = files.previewMetadataView
    case .unknown:
        content = OriginalUnavailablePreviewContentView(frame: .zero)
        contentSize = .init(width: screenSize.width * 0.25,
                            height: screenSize.height * 0.25)
        metadata = nil
    default:
        content = makeReplicaReadOnlyPreviewContent(store: state.store, item: item)
        contentSize = .init(width: screenSize.width * 0.25,
                            height: screenSize.height * 0.25)
        metadata = nil
    }
    let header = ReplicaInlinePreviewHeader(state: state, item: item)
    let editorHeader = ReplicaInlinePreviewEditorHeader()
    let footer = OriginalPreviewFooterView()
    if let metadata { footer.f_1003df0b0(metadata) }
    else {
        let emptyMetadata = NSView()
        emptyMetadata.heightAnchor.constraint(equalToConstant: 0).isActive = true
        footer.f_1003df0b0(emptyMetadata)
    }
    let view = ReplicaInlinePreviewContainer(previewHeader: header, editorHeader: editorHeader,
                                            contentView: content, footer: footer,
                                            contentSize: contentSize)
    view.applyContentAppearance()
    connectReplicaPreviewHeader(header, view: view, state: state, item: item)
    editorHeader.onCancel = { [weak view] in view?.f_10007c1fc() }
    editorHeader.onSave = { [weak view] in view?.f_10007c080() }
    view.setCanCommitEditing = { [weak editorHeader] enabled in editorHeader?.setCanCommit(enabled) }
    if let image = content as? ReplicaImagePreviewContent { editorHeader.setCanCommit(image.canCommit) }
    return view
}

/// Connects recovered preview mode transitions to the replica's local text model.
/// Other kinds use their own content adapters in the shared factory above.
@MainActor
func makeOriginalReplicaTextPreview(state: ReplicaUIState, item: ClipboardItem) -> OriginalItemPreviewView? {
    guard item.kind == .text || item.kind == .richText else { return nil }
    let content = ReplicaInlineTextPreviewContent(state: state, item: item)
    let header = ReplicaInlinePreviewHeader(state: state, item: item)
    let editorHeader = ReplicaInlinePreviewEditorHeader(document: content.document)
    let footer = ReplicaInlinePreviewFooter(document: content.document)
    let view = ReplicaInlinePreviewContainer(previewHeader: header, editorHeader: editorHeader,
                                            contentView: content, footer: footer,
                                            contentSize: content.preferredPreviewSize)
    view.applyContentAppearance()
    connectReplicaPreviewHeader(header, view: view, state: state, item: item)
    editorHeader.onCancel = { [weak view] in view?.f_10007c1fc() }
    editorHeader.onSave = { [weak view] in view?.f_10007c080() }
    view.setCanCommitEditing = { [weak editorHeader] enabled in editorHeader?.setCanCommit(enabled) }
    content.onCancel = { [weak view] in view?.f_10007c1fc() }
    content.onSave = { [weak view, weak content] in
        guard content?.canCommit == true else { return }
        view?.f_10007c080()
    }
    return view
}

@MainActor
private func connectReplicaPreviewHeader(_ header: ReplicaInlinePreviewHeader,
                                         view: OriginalItemPreviewView,
                                         state: ReplicaUIState, item: ClipboardItem) {
    header.onEdit = { [weak view] in view?.f_10007be8c() }
    header.onClose = { [weak header, weak view] in
        header?.titleLabel.f_100011d28()
        view?.window?.performClose(nil)
    }
    header.titleLabel.onCommitEditing = { [weak state] title in
        guard let state else { return }
        state.perform { try state.store.updateItem(id: item.id, title: title, text: nil) }
    }
}

@MainActor
private final class ReplicaInlinePreviewContainer: OriginalItemPreviewView {
    /// f_10007acd8 decorates the actual content; text keeps the reference's zero border.
    func applyContentAppearance() {
        itemContentView.effectiveAppearance.performAsCurrentDrawingAppearance {
            OriginalViewLayerFunctions.f_10021d1cc(
                OriginalSearchSurfaceAppearance.f_1001ff0d0().pointee, view: itemContentView)
            itemContentView.layer?.borderWidth = itemContentView is ReplicaInlineTextPreviewContent ? 0 : 0.5
            OriginalViewLayerFunctions.f_10021d49c(5, curve: .circular, view: itemContentView)
        }
    }

    override func viewDidChangeEffectiveAppearance() {
        super.viewDidChangeEffectiveAppearance()
        applyContentAppearance()
    }

    override func performKeyEquivalent(with event: NSEvent) -> Bool {
        let modifiers = event.modifierFlags.intersection(.deviceIndependentFlagsMask)
        if modifiers == .command, event.charactersIgnoringModifiers == "e", editorHeader.isHidden {
            guard itemContentView is OriginalPreviewEditableContent else { return super.performKeyEquivalent(with: event) }
            f_10007be8c()
            return true
        }
        if modifiers.isEmpty, event.keyCode == 53 {
            if !editorHeader.isHidden { f_10007c1fc() }
            else { window?.performClose(nil) }
            return true
        }
        return super.performKeyEquivalent(with: event)
    }
}

@MainActor
private final class ReplicaInlinePreviewTextView: NSTextView {
    weak var document: ReplicaRichTextDocument?
    var onSave: (() -> Void)?
    var onCancel: (() -> Void)?

    override func validateUserInterfaceItem(_ item: NSValidatedUserInterfaceItem) -> Bool {
        if item.action == NSSelectorFromString("changeLayoutOrientation:") { return false }
        return super.validateUserInterfaceItem(item)
    }

    override func menu(for event: NSEvent) -> NSMenu? {
        let menu = super.menu(for: event)
        if let menu { OriginalSearchMenu.f_10021ad80(menu) }
        return menu
    }

    override func performKeyEquivalent(with event: NSEvent) -> Bool {
        if isEditable, event.modifierFlags.intersection(.deviceIndependentFlagsMask) == .command {
            switch event.charactersIgnoringModifiers {
            case "s": onSave?(); return true
            case "b": document?.toggle(.bold); return true
            case "i": document?.toggle(.italic); return true
            case "u": document?.toggle(.underline); return true
            default: break
            }
        }
        return super.performKeyEquivalent(with: event)
    }

    override func cancelOperation(_ sender: Any?) {
        if isEditable { onCancel?() }
        else { super.cancelOperation(sender) }
    }
}

@MainActor
private final class ReplicaInlineTextPreviewContent: NSScrollView, OriginalPreviewEditableContent {
    let document: ReplicaRichTextDocument
    private let text: ReplicaInlinePreviewTextView
    private weak var state: ReplicaUIState?
    private let itemID: UUID
    private var itemObservation: AnyCancellable?
    private var contentObservation: AnyCancellable?
    private var storageBridge: OriginalPreviewTextStorageBridge?
    private var originalText: NSAttributedString
    private var editingText: NSAttributedString
    private(set) var canCommit = false
    var onCanCommitEditing: ((Bool) -> Void)?
    var onCancel: (() -> Void)?
    var onSave: (() -> Void)?
    var previewEditingToolbar: NSView? { nil }

    init(state: ReplicaUIState, item: ClipboardItem) {
        self.state = state
        itemID = item.id
        let initial = Self.attributedContent(item)
        originalText = initial
        editingText = OriginalPreviewAttributedText.normalizedEditingText(initial)
        document = ReplicaRichTextDocument(content: initial)
        text = ReplicaInlinePreviewTextView(frame: .zero)
        super.init(frame: .zero)
        hasVerticalScroller = true
        autohidesScrollers = true
        hasHorizontalScroller = false
        borderType = .noBorder
        drawsBackground = false
        text.isEditable = false
        text.isSelectable = true
        text.isRichText = true
        text.allowsUndo = true
        text.isVerticallyResizable = true
        text.isHorizontallyResizable = false
        text.autoresizingMask = [.width]
        text.maxSize = .init(width: CGFloat.greatestFiniteMagnitude, height: CGFloat.greatestFiniteMagnitude)
        text.textContainer?.widthTracksTextView = true
        text.textContainer?.containerSize = .init(width: 500, height: CGFloat.greatestFiniteMagnitude)
        text.usesAdaptiveColorMappingForDarkAppearance = true
        let bridge = OriginalPreviewTextStorageBridge(editor: text)
        OriginalPreviewAttributedText.f_100212e78(initial, editor: text)
        OriginalPreviewTextColors.f_1003eb4a8(original: initial, editor: text)
        text.delegate = document
        text.document = document
        text.onSave = { [weak self] in self?.onSave?() }
        text.onCancel = { [weak self] in self?.onCancel?() }
        document.textView = text
        document.usesRecoveredContentEvents = true
        bridge.onTraitsChange = { [weak document] traits in document?.applyRecoveredTraits(traits) }
        bridge.onAttributedTextChange = { [weak document] value in document?.receiveRecoveredContent(value) }
        storageBridge = bridge
        documentView = text
        contentObservation = document.$content.sink { [weak self] content in
            MainActor.assumeIsolated {
                guard let self else { return }
                self.canCommit = OriginalPreviewAttributedText.f_1003c0be0(
                    candidate: content, original: self.originalText, editing: self.editingText)
                self.onCanCommitEditing?(self.canCommit)
            }
        }
        itemObservation = state.store.$items.sink { [weak self] items in
            MainActor.assumeIsolated {
                guard let self else { return }
                guard let current = items.first(where: { $0.id == self.itemID }), !current.isDeleted else {
                    self.window?.performClose(nil)
                    return
                }
                if !self.text.isEditable {
                    self.replaceModelAndDisplay(current)
                }
            }
        }
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    override func viewDidChangeEffectiveAppearance() {
        super.viewDidChangeEffectiveAppearance()
        effectiveAppearance.performAsCurrentDrawingAppearance { self.f_1003ebcd4() }
    }

    private func f_1003ebcd4() {
        OriginalPreviewTextColors.f_1003eb4a8(original: originalText, editor: text)
    }

    var preferredPreviewSize: NSSize {
        let screenSize = NSScreen.main?.frame.size
        let maximum = NSSize(width: (screenSize?.width ?? 2000) * 0.5,
                             height: (screenSize?.height ?? 2000) * 0.5)
        let attributed = document.content
        let sample = attributed.length > 2000
            ? attributed.attributedSubstring(from: NSRange(location: 0, length: 2000)) : attributed
        let bounds = sample.boundingRect(with: maximum, options: [.usesLineFragmentOrigin, .usesFontLeading])
        return .init(width: max(380, bounds.width), height: max(240, bounds.height))
    }

    func beginPreviewEditing() {
        text.isEditable = true
        reloadStoredContent()
        window?.makeFirstResponder(text)
    }

    func cancelPreviewEditing() {
        text.isEditable = false
        reloadStoredContent()
    }

    func commitPreviewEditing() {
        text.isEditable = false
        guard let state else { return }
        do {
            try state.store.updateRichTextItem(id: itemID,
                attributedString: OriginalPreviewAttributedText.f_100212ccc(editor: text))
            state.normalizeSelection()
        } catch { state.controller?.presentError(error) }
        reloadStoredContent()
    }

    private func reloadStoredContent() {
        guard let item = state?.store.items.first(where: { $0.id == itemID }) else { return }
        replaceModelAndDisplay(item)
    }

    private func replaceModelAndDisplay(_ item: ClipboardItem) {
        originalText = Self.attributedContent(item)
        editingText = OriginalPreviewAttributedText.normalizedEditingText(originalText)
        OriginalPreviewAttributedText.f_1003eb330(original: originalText, editing: editingText, editor: text)
        OriginalPreviewTextColors.f_1003eb4a8(original: originalText, editor: text)
    }

    private static func attributedContent(_ item: ClipboardItem) -> NSAttributedString {
        for type in ["com.apple.flat-rtfd", "com.apple.rtfd"] {
            if let data = item.payloads[type],
               let content = NSAttributedString(rtfd: data, documentAttributes: nil) {
                return OriginalPreviewAttributedText.f_1003097c0(content)
            }
        }
        if let data = item.payloads["public.rtf"],
           let content = NSAttributedString(rtf: data, documentAttributes: nil) {
            return OriginalPreviewAttributedText.f_1003097c0(content)
        }
        return NSAttributedString(string: item.plainText ?? "")
    }
}

@MainActor
private final class ReplicaPreviewActionMenuItem: NSMenuItem {
    private let invoke: () -> Void
    init(title: String, invoke: @escaping () -> Void) {
        self.invoke = invoke
        super.init(title: title, action: #selector(performMenuAction), keyEquivalent: "")
        target = self
    }
    required init(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }
    @objc private func performMenuAction() { invoke() }
}

@MainActor
private final class ReplicaInlinePreviewHeader: NSView {
    var onEdit: (() -> Void)?
    var onClose: (() -> Void)?
    let titleLabel = OriginalPreviewTitleLabel()
    private var itemObservation: AnyCancellable?
    private var pinboardObservation: AnyCancellable?
    private weak var state: ReplicaUIState?
    private let itemID: UUID
    private var pinButton: OriginalToolbarButton?
    private var sharingPicker: NSSharingServicePicker?

    init(state: ReplicaUIState, item: ClipboardItem) {
        self.state = state
        itemID = item.id
        super.init(frame: .zero)
        let close = NSButton()
        f_1000123d4(close)
        let edit = OriginalToolbarButton(title: String(localized: OriginalPreviewLocalization.f_1001c1688())) { [weak self] _ in self?.onEdit?() }
        let pin = OriginalToolbarButton(symbol: "circle.dashed", toolTip: String(localized: OriginalPreviewLocalization.f_1001c2a08())) { [weak self] button in
            self?.showPinMenu(from: button)
        }
        pin.hasPullDownArrow = true
        pinButton = pin
        let share = OriginalToolbarButton(symbol: "square.and.arrow.up", toolTip: String(localized: OriginalPreviewLocalization.f_1001c3f08())) { [weak self] button in
            self?.showSharingPicker(from: button)
        }
        let row = NSStackView(views: [pin, share, edit])
        row.spacing = 8
        row.alignment = .centerY
        for child in [close, titleLabel, row] {
            child.translatesAutoresizingMaskIntoConstraints = false
            addSubview(child)
        }
        NSLayoutConstraint.activate([
            close.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 10),
            close.centerYAnchor.constraint(equalTo: centerYAnchor),
            titleLabel.leadingAnchor.constraint(equalTo: close.trailingAnchor, constant: 8),
            titleLabel.trailingAnchor.constraint(lessThanOrEqualTo: row.leadingAnchor, constant: -8),
            titleLabel.centerYAnchor.constraint(equalTo: centerYAnchor),
            row.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -8),
            row.centerYAnchor.constraint(equalTo: centerYAnchor)
        ])
        itemObservation = state.store.$items.sink { [weak self, weak share] items in
            MainActor.assumeIsolated {
                guard let self, let current = items.first(where: { $0.id == item.id }) else { return }
                let field = self.titleLabel.f_100013084()
                let rawType: Int
                switch current.kind {
                case .unknown: rawType = 0
                case .image: rawType = 1
                case .color: rawType = 2
                case .files: rawType = 3
                case .link: rawType = 4
                case .text, .richText: rawType = 5
                }
                let defaultTitle = OriginalPreviewTitles.f_100309008(rawType: rawType,
                    fileCount: current.kind == .files ? current.decodedFilePreviewMetadata?.paths.count : nil)
                field.f_10023b600(defaultTitle)
                field.f_10023b214(OriginalPreviewTitles.f_100308f88(current.title, defaultTitle: defaultTitle))
                share?.isEnabled = (try? Self.sharingContent(current))
                    .map { OriginalPreviewSharing.f_100320cc0($0) } ?? false
                self.refreshPinAppearance(current)
            }
        }
        pinboardObservation = state.store.$pinboards.sink { [weak self] boards in
            MainActor.assumeIsolated {
                guard let self, let item = self.state?.store.items.first(where: { $0.id == self.itemID }) else { return }
                self.refreshPinAppearance(item, boards: boards)
            }
        }
    }
    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    private func refreshPinAppearance(_ item: ClipboardItem, boards: [Pinboard]? = nil) {
        let pinboard = (boards ?? state?.store.pinboards ?? []).first { item.pinboardIDs.contains($0.id) }
        pinButton?.symbol = item.pinboardIDs.isEmpty ? "circle.dashed" : "circle.fill"
        pinButton?.contentTintColor = pinboard.flatMap { Self.pinColor($0.colorHex) }
    }

    private static func pinColor(_ hex: String) -> NSColor? {
        let value = hex.hasPrefix("#") ? String(hex.dropFirst()) : hex
        guard value.count == 6, let rgb = UInt32(value, radix: 16) else { return nil }
        return NSColor(srgbRed: CGFloat((rgb >> 16) & 255) / 255,
                       green: CGFloat((rgb >> 8) & 255) / 255,
                       blue: CGFloat(rgb & 255) / 255, alpha: 1)
    }

    private func showPinMenu(from button: NSButton) {
        guard let state, let item = state.store.items.first(where: { $0.id == itemID }) else { return }
        let menu = NSMenu()
        for board in state.store.pinboards {
            let entry = ReplicaPreviewActionMenuItem(title: board.name) { [weak self] in
                guard let self, let state = self.state else { return }
                state.perform { try state.store.assign(ids: [self.itemID], to: board.id) }
            }
            entry.state = item.pinboardIDs.contains(board.id) ? .on : .off
            let color = Self.pinColor(board.colorHex) ?? .clear
            let image = NSImage(size: NSSize(width: 12, height: 12), flipped: false) { bounds in
                color.setFill()
                NSBezierPath(ovalIn: bounds).fill()
                return true
            }
            entry.image = image
            menu.addItem(entry)
        }
        menu.addItem(.separator())
        menu.addItem(ReplicaPreviewActionMenuItem(title: String(localized: OriginalPreviewLocalization.f_1001c0f08()) + "...") { [weak self] in
            self?.createPinboardForCurrentItem()
        })
        if !item.pinboardIDs.isEmpty {
            menu.addItem(ReplicaPreviewActionMenuItem(title: String(localized: OriginalPreviewLocalization.f_1001c4208())) { [weak self] in
                guard let self, let state = self.state else { return }
                state.perform { try state.store.assign(ids: [self.itemID], to: nil) }
            })
        }
        menu.popUp(positioning: nil, at: NSPoint(x: -10, y: 0), in: button)
    }

    private func createPinboardForCurrentItem() {
        guard let state else { return }
        let alert = NSAlert()
        alert.messageText = String(localized: OriginalPreviewLocalization.f_1001c0f08())
        let input = NSTextField(frame: NSRect(x: 0, y: 0, width: 260, height: 24))
        alert.accessoryView = input
        alert.addButton(withTitle: String(localized: OriginalPreviewLocalization.f_1001c3908()))
        alert.addButton(withTitle: String(localized: OriginalPreviewLocalization.f_1001c0788()))
        alert.window.initialFirstResponder = input
        guard alert.runModal() == .alertFirstButtonReturn else { return }
        let name = input.stringValue.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !name.isEmpty else { return }
        state.perform {
            let board = try state.store.createPinboard(name: name)
            try state.store.assign(ids: [itemID], to: board.id)
        }
    }

    private static func sharingContent(_ item: ClipboardItem) throws -> OriginalPreviewSharing.Content {
        let content = try ClipboardStore.originalPasteboardItems(from: item.payloads)
        let kind: OriginalPasteboardContentKind
        switch item.kind {
        case .image: kind = .image
        case .files: kind = .files
        case .link: kind = .link
        case .color: kind = .color
        case .text, .richText: kind = .text
        case .unknown: kind = .unknown
        }
        return .init(items: content, rawType: Int(kind.rawValue))
    }

    private func showSharingPicker(from button: NSButton) {
        guard let state, let item = state.store.items.first(where: { $0.id == itemID }) else { return }
        do {
            let picker = OriginalPreviewSharing.f_1000183e0([try Self.sharingContent(item)])
            sharingPicker = picker
            picker.show(relativeTo: .zero, of: button, preferredEdge: .minY)
        } catch { state.controller?.presentError(error) }
    }

    private func f_1000123d4(_ button: NSButton) {
        if NSImage(systemSymbolName: "xmark.circle.fill", accessibilityDescription: nil) == nil {
            button.image = NSImage(systemSymbolName: "questionmark.square", accessibilityDescription: nil)!
        } else {
            button.image = NSImage(systemSymbolName: "xmark.circle.fill", accessibilityDescription: nil)!
        }
        button.imagePosition = .imageOnly
        button.contentTintColor = OriginalSearchAppearance.f_1001fec18()
        button.isBordered = false
        button.alphaValue = 0.6
        button.action = #selector(closeAction)
        button.target = self
    }

    @objc private func editAction() { onEdit?() }
    @objc private func closeAction() { onClose?() }
    override func cancelOperation(_ sender: Any?) { titleLabel.f_100011d28() }
}

@MainActor
private final class ReplicaInlinePreviewEditorHeader: NSView {
    var onCancel: (() -> Void)?
    var onSave: (() -> Void)?
    private var saveButton: NSButton?
    init(document: ReplicaRichTextDocument? = nil) {
        super.init(frame: .zero)
        let cancel = OriginalToolbarButton(title: String(localized: OriginalPreviewLocalization.f_1001c0788()), shortcut: .init(keyCode: OriginalShortcutFunctions.f_1001e95fc(), internalModifiers: 0), toolTip: String(localized: OriginalPreviewLocalization.f_1001be988())) { [weak self] _ in self?.onCancel?() }
        let save = OriginalToolbarButton(title: String(localized: OriginalPreviewLocalization.f_1001c3908()), shortcut: .init(keyCode: Int(OriginalShortcutFunctions.f_1001e94d4("s")), internalModifiers: NSEvent.ModifierFlags.command.rawValue), toolTip: String(localized: OriginalPreviewLocalization.f_1001bf108())) { [weak self] _ in self?.onSave?() }
        save.isPrimary = true
        save.isEnabled = false
        saveButton = save
        for view in [cancel, save] { view.translatesAutoresizingMaskIntoConstraints = false; addSubview(view) }
        NSLayoutConstraint.activate([
            cancel.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 8),
            cancel.centerYAnchor.constraint(equalTo: centerYAnchor),
            save.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -8),
            save.centerYAnchor.constraint(equalTo: centerYAnchor)
        ])
        if let document {
            let toolbar = ReplicaInlinePreviewFormatting(document: document)
            toolbar.translatesAutoresizingMaskIntoConstraints = false
            addSubview(toolbar)
            NSLayoutConstraint.activate([
                toolbar.centerXAnchor.constraint(equalTo: centerXAnchor),
                toolbar.centerYAnchor.constraint(equalTo: centerYAnchor)
            ])
        }
    }
    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }
    func setCanCommit(_ enabled: Bool) { saveButton?.isEnabled = enabled }
    @objc private func cancelAction() { onCancel?() }
    @objc private func saveAction() { onSave?() }
}

@MainActor
private final class ReplicaInlinePreviewFormatting: NSView {
    private let buttons: [OriginalToolbarButton]

    init(document: ReplicaRichTextDocument) {
        buttons = [
            OriginalToolbarButton(symbol: "bold", shortcut: .init(keyCode: Int(OriginalShortcutFunctions.f_1001e94d4("b")), internalModifiers: NSEvent.ModifierFlags.command.rawValue), toolTip: String(localized: OriginalPreviewLocalization.f_1001bf288())) { [weak document] _ in document?.toggle(.bold) },
            OriginalToolbarButton(symbol: "italic", shortcut: .init(keyCode: Int(OriginalShortcutFunctions.f_1001e94d4("i")), internalModifiers: NSEvent.ModifierFlags.command.rawValue), toolTip: String(localized: OriginalPreviewLocalization.f_1001bf408())) { [weak document] _ in document?.toggle(.italic) },
            OriginalToolbarButton(symbol: "underline", shortcut: .init(keyCode: Int(OriginalShortcutFunctions.f_1001e94d4("u")), internalModifiers: NSEvent.ModifierFlags.command.rawValue), toolTip: String(localized: OriginalPreviewLocalization.f_1001bf708())) { [weak document] _ in document?.toggle(.underline) },
            OriginalToolbarButton(symbol: "strikethrough", toolTip: String(localized: OriginalPreviewLocalization.f_1001bf588())) { [weak document] _ in document?.toggle(.strikethrough) }
        ]
        super.init(frame: .zero)
        let row = NSStackView(views: buttons)
        row.translatesAutoresizingMaskIntoConstraints = false
        addSubview(row)
        NSLayoutConstraint.activate([
            row.leadingAnchor.constraint(equalTo: leadingAnchor),
            row.trailingAnchor.constraint(equalTo: trailingAnchor),
            row.topAnchor.constraint(equalTo: topAnchor),
            row.bottomAnchor.constraint(equalTo: bottomAnchor)
        ])
        document.onRecoveredTraitsChange = { [weak self] traits in _ = self?.f_1002106d0(traits) }
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    @discardableResult
    private func f_1002106d0(_ traits: Set<OriginalPreviewTextTraits.Trait>) -> Int {
        for (index, trait) in [OriginalPreviewTextTraits.Trait.bold, .italic, .underline, .strikethrough].enumerated() {
            buttons[index].isSelected = OriginalPreviewTextTraits.f_100208290(trait, in: traits)
        }
        return 0
    }
}

@MainActor
private final class ReplicaInlinePreviewFooter: OriginalPreviewFooterView {
    private var contentObservation: AnyCancellable?
    init(document: ReplicaRichTextDocument) {
        super.init()
        contentObservation = document.$content.sink { [weak self] content in
            MainActor.assumeIsolated {
                self?.f_1003df0b0(OriginalPreviewTextMetaView(text: content.string))
            }
        }
    }
    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }
}
