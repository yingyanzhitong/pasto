import AppKit

/// The recovered PasteUI.Editable requirements used by ItemPreviewView.
/// Names of cancel/commit are established by the original EditorHeader callbacks.
@MainActor
public protocol OriginalPreviewEditableContent: AnyObject {
    var onCanCommitEditing: ((Bool) -> Void)? { get set }
    var previewEditingToolbar: NSView? { get }
    func beginPreviewEditing()
    func cancelPreviewEditing()
    func commitPreviewEditing()
}

/// Recovered preview mode transitions. Concrete headers and item renderers are adapters.
@MainActor
open class OriginalItemPreviewView: NSView {
    public let previewHeader: NSView
    public let editorHeader: NSView
    public let itemContentView: NSView
    public let footer: NSView
    public var onBeginEditing: (() -> Void)?
    public var onEndEditing: (() -> Void)?
    public var onEditingStateChanged: ((Bool) -> Void)?
    public var configureWritingTools: ((Bool) -> Void)?
    public var supportsWritingTools: () -> Bool = { false }
    public var setCanCommitEditing: ((Bool) -> Void)?

    public init(previewHeader: NSView, editorHeader: NSView, contentView: NSView,
                footer: NSView, contentSize: NSSize) {
        self.previewHeader = previewHeader
        self.editorHeader = editorHeader
        self.itemContentView = contentView
        self.footer = footer
        super.init(frame: NSRect(origin: .zero,
                                 size: .init(width: contentSize.width + 10,
                                             height: contentSize.height + 76)))
        for view in [previewHeader, editorHeader, contentView, footer] {
            view.translatesAutoresizingMaskIntoConstraints = false
            addSubview(view)
        }
        NSLayoutConstraint.activate([
            previewHeader.leadingAnchor.constraint(equalTo: leadingAnchor),
            previewHeader.trailingAnchor.constraint(equalTo: trailingAnchor),
            previewHeader.heightAnchor.constraint(equalToConstant: 38),
            previewHeader.topAnchor.constraint(equalTo: topAnchor),
            editorHeader.leadingAnchor.constraint(equalTo: leadingAnchor),
            editorHeader.trailingAnchor.constraint(equalTo: trailingAnchor),
            editorHeader.heightAnchor.constraint(equalToConstant: 38),
            editorHeader.topAnchor.constraint(equalTo: topAnchor),
            contentView.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 5),
            contentView.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -5),
            contentView.topAnchor.constraint(equalTo: previewHeader.bottomAnchor),
            contentView.bottomAnchor.constraint(equalTo: footer.topAnchor),
            contentView.widthAnchor.constraint(greaterThanOrEqualToConstant: 380),
            contentView.heightAnchor.constraint(greaterThanOrEqualToConstant: 240),
            footer.leadingAnchor.constraint(equalTo: leadingAnchor),
            footer.trailingAnchor.constraint(equalTo: trailingAnchor),
            footer.bottomAnchor.constraint(equalTo: bottomAnchor)
        ])
        if let toolbar = (contentView as? OriginalPreviewEditableContent)?.previewEditingToolbar {
            toolbar.translatesAutoresizingMaskIntoConstraints = false
            editorHeader.addSubview(toolbar)
            NSLayoutConstraint.activate([
                toolbar.centerXAnchor.constraint(equalTo: editorHeader.centerXAnchor),
                toolbar.centerYAnchor.constraint(equalTo: editorHeader.centerYAnchor)
            ])
        }
        (contentView as? OriginalPreviewEditableContent)?.onCanCommitEditing = { [weak self] canCommit in
            self?.setCanCommitEditing?(canCommit)
        }
        editorHeader.isHidden = true
    }

    public required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    /// Paste 0x10007be8c: noneditable content leaves the entire preview unchanged.
    public func f_10007be8c() {
        guard let editable = itemContentView as? OriginalPreviewEditableContent else { return }
        configureWritingTools?(supportsWritingTools())
        editable.beginPreviewEditing()
        previewHeader.isHidden = true
        editorHeader.isHidden = false
        onBeginEditing?()
        onEditingStateChanged?(true)
    }

    /// Paste 0x10007c080: content commit precedes headers, state callback, end callback.
    public func f_10007c080() {
        guard let editable = itemContentView as? OriginalPreviewEditableContent else { return }
        editable.commitPreviewEditing()
        previewHeader.isHidden = false
        editorHeader.isHidden = true
        onEditingStateChanged?(false)
        onEndEditing?()
    }

    /// Paste 0x10007c1fc: content cancellation has the same outer callback ordering.
    public func f_10007c1fc() {
        guard let editable = itemContentView as? OriginalPreviewEditableContent else { return }
        editable.cancelPreviewEditing()
        previewHeader.isHidden = false
        editorHeader.isHidden = true
        onEditingStateChanged?(false)
        onEndEditing?()
    }
}
