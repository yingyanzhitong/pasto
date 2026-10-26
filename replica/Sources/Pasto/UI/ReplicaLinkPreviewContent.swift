import AppKit
import Combine
import PastoCore

/// URL editing and footer are local. No WKWebView or network-preview request is created.
@MainActor
final class ReplicaLinkPreviewContent: NSView, OriginalPreviewEditableContent, NSTextViewDelegate {
    var onCanCommitEditing: ((Bool) -> Void)?
    var previewEditingToolbar: NSView? { nil }
    var previewMetadataView: NSView? { metadata }
    var preferredPreviewSize: NSSize {
        // Both original PreferredSizeProviding witnesses use f_1003e3eec: half screen or zero.
        guard let size = NSScreen.main?.frame.size else { return .zero }
        return .init(width: size.width * 0.5, height: size.height * 0.5)
    }

    private weak var state: ReplicaUIState?
    private let itemID: UUID
    private let readOnlyContent: NSView
    private let textView = NSTextView()
    private let metadata = NSStackView()
    private let urlLabel = NSTextField(labelWithString: "")
    private var openButton: OriginalToolbarButton?
    private var itemObservation: AnyCancellable?

    init(state: ReplicaUIState, item: ClipboardItem) {
        self.state = state
        itemID = item.id
        readOnlyContent = makeReplicaReadOnlyPreviewContent(store: state.store, item: item)
        super.init(frame: .zero)
        textView.isSelectable = true
        textView.isEditable = true
        textView.font = OriginalSearchAppearance.f_1001ff928()
        textView.textColor = OriginalSearchAppearance.f_1001fec18()
        textView.textContainerInset = .init(width: 12, height: 12)
        textView.autoresizingMask = .width
        textView.delegate = self
        urlLabel.font = OriginalSearchAppearance.f_1001ff928()
        urlLabel.textColor = OriginalToolbarAppearance.secondaryForeground()
        urlLabel.isEditable = false
        urlLabel.isSelectable = false
        urlLabel.isBordered = false
        urlLabel.drawsBackground = false
        urlLabel.setContentCompressionResistancePriority(.defaultLow, for: .horizontal)
        let spacer = NSView()
        spacer.setContentHuggingPriority(.defaultLow, for: .horizontal)
        spacer.setContentCompressionResistancePriority(.defaultLow, for: .horizontal)
        let open = OriginalToolbarButton(title: "") { [weak self] _ in
            guard let url = self?.currentURL() else { return }
            NSWorkspace.shared.open(url)
        }
        openButton = open
        metadata.orientation = .horizontal
        metadata.alignment = .centerY
        metadata.spacing = 8
        for view in [urlLabel, spacer, open] { metadata.addArrangedSubview(view) }
        showContent(readOnlyContent)
        itemObservation = state.store.$items.sink { [weak self] items in
            MainActor.assumeIsolated {
                guard let self, let current = items.first(where: { $0.id == self.itemID }) else { return }
                self.updateMetadata(Self.itemURL(current))
            }
        }
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    func beginPreviewEditing() {
        textView.string = currentURL()?.absoluteString ?? ""
        showContent(textView)
        updateCanCommit()
        window?.makeFirstResponder(textView)
    }

    func cancelPreviewEditing() {
        showContent(readOnlyContent)
        updateMetadata(currentURL())
    }

    func commitPreviewEditing() {
        guard let state, let url = Self.normalizedURL(textView.string) else { return }
        do {
            try state.store.updateLinkItem(id: itemID, url: url)
            state.normalizeSelection()
        } catch { state.controller?.presentError(error) }
        showContent(readOnlyContent)
        updateMetadata(currentURL())
    }

    nonisolated func textDidChange(_ notification: Notification) {
        MainActor.assumeIsolated { updateCanCommit() }
    }

    /// The reference validates URL initialization; it does not require a host or compare to the old URL.
    static func normalizedURL(_ string: String) -> URL? {
        guard let url = URL(string: string) else { return nil }
        return url.scheme == nil ? URL(string: "https://" + url.absoluteString) : url
    }

    private func updateCanCommit() { onCanCommitEditing?(Self.normalizedURL(textView.string) != nil) }

    private func currentURL() -> URL? {
        state?.store.items.first(where: { $0.id == itemID }).flatMap(Self.itemURL)
    }

    private static func itemURL(_ item: ClipboardItem) -> URL? {
        // The original VM requires canonical link metadata and traps if it is absent.
        // This optional UI adapter leaves missing metadata empty rather than rebuilding it from payloads.
        item.decodedLinkPreviewMetadata?.url
    }

    private func updateMetadata(_ url: URL?) {
        urlLabel.stringValue = url?.absoluteString ?? ""
        let applicationName: String
        if let url, let application = NSWorkspace.shared.urlForApplication(toOpen: url),
           let name = Bundle(url: application)?.object(forInfoDictionaryKey: "CFBundleName") as? String {
            applicationName = name
        } else { applicationName = String(localized: OriginalPreviewLocalization.f_1001c4388()) }
        openButton?.title = String(localized: OriginalPreviewLocalization.f_1001e6b98(applicationName))
        openButton?.isEnabled = url != nil
    }

    private func showContent(_ view: NSView) {
        for previous in subviews { previous.removeFromSuperview() }
        view.translatesAutoresizingMaskIntoConstraints = false
        addSubview(view)
        NSLayoutConstraint.activate([
            view.leadingAnchor.constraint(equalTo: leadingAnchor),
            view.trailingAnchor.constraint(equalTo: trailingAnchor),
            view.topAnchor.constraint(equalTo: topAnchor),
            view.bottomAnchor.constraint(equalTo: bottomAnchor)
        ])
    }
}
