import AppKit
import Combine
import PastoCore
import QuickLookUI
import UniformTypeIdentifiers

/// File content, Quick Look, and local Finder action share the existing native preview chrome.
@MainActor
final class ReplicaFilePreviewContent: NSView {
    var previewMetadataView: NSView? { metadata }
    var preferredPreviewSize: NSSize {
        // Both original PreferredSizeProviding witnesses use f_1003e3eec: half screen or zero.
        guard let size = NSScreen.main?.frame.size else { return .zero }
        return .init(width: size.width * 0.5, height: size.height * 0.5)
    }

    private weak var state: ReplicaUIState?
    private let itemID: UUID
    private let quickLookView = ReplicaFileQuickLookView(frame: .zero, style: .normal)!
    private let multipleFilesView = NSImageView()
    private let metadata = NSStackView()
    private let metadataLabel = NSTextField()
    private var itemObservation: AnyCancellable?
    private var displayedURLs: [URL] = []

    init(state: ReplicaUIState, item: ClipboardItem) {
        self.state = state
        itemID = item.id
        super.init(frame: .zero)
        multipleFilesView.imageAlignment = .alignCenter
        multipleFilesView.imageScaling = .scaleProportionallyDown
        let image = NSImage(named: NSImage.multipleDocumentsName)?.copy() as? NSImage
        image?.size = .init(width: 160, height: 160)
        multipleFilesView.image = image
        for view in [multipleFilesView, quickLookView] {
            view.translatesAutoresizingMaskIntoConstraints = false
            addSubview(view)
        }
        NSLayoutConstraint.activate([
            multipleFilesView.centerXAnchor.constraint(equalTo: centerXAnchor),
            multipleFilesView.centerYAnchor.constraint(equalTo: centerYAnchor),
            multipleFilesView.widthAnchor.constraint(equalToConstant: 160),
            multipleFilesView.heightAnchor.constraint(equalToConstant: 160),
            quickLookView.topAnchor.constraint(equalTo: topAnchor),
            quickLookView.leadingAnchor.constraint(equalTo: leadingAnchor),
            quickLookView.bottomAnchor.constraint(equalTo: bottomAnchor),
            quickLookView.trailingAnchor.constraint(equalTo: trailingAnchor)
        ])
        metadataLabel.maximumNumberOfLines = 0
        metadataLabel.textColor = OriginalToolbarAppearance.secondaryForeground()
        metadataLabel.font = OriginalSearchAppearance.f_1001ff928()
        metadataLabel.isEditable = false
        metadataLabel.isSelectable = false
        metadataLabel.isBordered = false
        metadataLabel.drawsBackground = false
        metadataLabel.setContentCompressionResistancePriority(.defaultLow, for: .horizontal)
        let spacer = NSView()
        spacer.setContentHuggingPriority(.defaultLow, for: .horizontal)
        spacer.setContentCompressionResistancePriority(.defaultLow, for: .horizontal)
        let reveal = OriginalToolbarButton(title: String(localized: OriginalPreviewLocalization.f_1001dac54())) { [weak self] _ in
            self?.revealInFinder()
        }
        metadata.orientation = .horizontal
        metadata.alignment = .centerY
        metadata.spacing = 8
        for view in [metadataLabel, spacer, reveal] { metadata.addArrangedSubview(view) }
        itemObservation = state.store.$items.sink { [weak self] items in
            MainActor.assumeIsolated {
                guard let self, let current = items.first(where: { $0.id == self.itemID }) else { return }
                self.update(current)
            }
        }
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    private func update(_ item: ClipboardItem) {
        let fileMetadata = item.decodedFilePreviewMetadata
        let paths = fileMetadata?.paths ?? []
        let urls = paths.map { URL(fileURLWithPath: $0) }
        let changed = urls != displayedURLs
        displayedURLs = urls
        multipleFilesView.isHidden = paths.count == 1
        quickLookView.isHidden = paths.count != 1
        let description = paths.count == 1
            ? paths[0] : String(localized: OriginalPreviewLocalization.f_1001c6fb0())
        var fields = [description]
        if let size = fileMetadata?.totalSize, size > 0 {
            fields.append(size.formatted(.byteCount(style: .file, allowedUnits: .all,
                                                   spellsOutZero: false, includesActualByteCount: false)))
        }
        metadataLabel.stringValue = fields.joined(separator: "  ·  ")
        if changed { quickLookView.previewItem = nil }
        installPreviewItemIfNeeded()
    }

    override func viewDidMoveToWindow() {
        super.viewDidMoveToWindow()
        installPreviewItemIfNeeded()
    }

    private func installPreviewItemIfNeeded() {
        guard window != nil, quickLookView.previewItem == nil,
              let url = displayedURLs.first else { return }
        let title = state?.store.items.first(where: { $0.id == itemID })?.originalTitle
        quickLookView.previewItem = ReplicaFilePreviewItem(path: url.path, title: title)
    }

    private func revealInFinder() {
        guard let item = state?.store.items.first(where: { $0.id == itemID }) else { return }
        let items = (try? ClipboardStore.originalPasteboardItems(from: item.payloads)) ?? []
        let urls = items.compactMap { item -> URL? in
            guard let data = item.f_10037d810(forType: UTType.fileURL.identifier),
                  let string = String(data: data, encoding: .utf8) else { return nil }
            return URL(string: string)
        }
        NSWorkspace.shared.activateFileViewerSelecting(urls)
        NSApp.deactivate()
        window?.performClose(nil)
    }
}

@MainActor
private final class ReplicaFileQuickLookView: QLPreviewView {
    override var acceptsFirstResponder: Bool { false }
}

private final class ReplicaFilePreviewItem: NSObject, QLPreviewItem {
    let previewItemURL: URL?
    let previewItemTitle: String?

    init(path: String, title: String?) {
        previewItemURL = URL(fileURLWithPath: path)
        previewItemTitle = title
        super.init()
    }
}
