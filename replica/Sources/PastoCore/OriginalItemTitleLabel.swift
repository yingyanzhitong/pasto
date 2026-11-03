import AppKit

/// ItemCell.HeaderView.TitleLabel has its own queued-focus editing contract.
@MainActor
public final class OriginalItemTitleLabel: NSView, NSTextFieldDelegate {
    public var isEditable = false
    public var onCommitEditing: ((String) -> Void)?
    private var storedTextField: OriginalPreviewTextField?
    private var originalText: String?

    public init() {
        super.init(frame: .zero)
        let field = f_1003d1cc0()
        field.translatesAutoresizingMaskIntoConstraints = false
        addSubview(field)
        NSLayoutConstraint.activate([
            field.leadingAnchor.constraint(equalTo: leadingAnchor),
            field.trailingAnchor.constraint(equalTo: trailingAnchor),
            field.topAnchor.constraint(equalTo: topAnchor),
            field.bottomAnchor.constraint(equalTo: bottomAnchor)
        ])
    }

    public required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    public func f_1003d1cc0() -> OriginalPreviewTextField {
        if let storedTextField { return storedTextField }
        let field = OriginalPreviewTextField()
        storedTextField = field
        field.onDidEndEditing = { [weak self] in self?.f_1003d1dbc() }
        // Forward the shared field's sizing/end callbacks while owning cancelOperation.
        field.f_10023adf0().delegate = self
        return field
    }

    public var isEditing: Bool { f_1003d1cc0().f_10023b3e0() }

    public func f_1003d2488() {
        let field = f_1003d1cc0()
        originalText = field.f_10023b1a4()
        field.f_10023b414(true)
        DispatchQueue.main.async { [weak self] in
            guard let self else { return }
            let field = self.f_1003d1cc0()
            field.window?.makeFirstResponder(field)
        }
    }

    public func f_1003d2838() {
        let field = f_1003d1cc0()
        field.f_10023b414(false)
        field.f_10023b214(originalText)
        field.f_10023bfdc()
        enqueueFocusClear()
    }

    public func f_1003d1dbc() {
        let field = f_1003d1cc0()
        field.f_10023b414(false)
        enqueueFocusClear()
        if let onCommitEditing { onCommitEditing(field.f_10023b1a4() ?? "") }
    }

    private func enqueueFocusClear() {
        DispatchQueue.main.async { [weak self] in
            self?.f_1003d1cc0().window?.makeFirstResponder(nil)
        }
    }

    public override func cancelOperation(_ sender: Any?) { f_1003d2838() }

    public override func mouseDown(with event: NSEvent) {
        if isEditable, !isEditing { f_1003d2488() }
        else { super.mouseDown(with: event) }
    }

    public func controlTextDidEndEditing(_ obj: Notification) {
        f_1003d1cc0().controlTextDidEndEditing(obj)
    }

    public func controlTextDidChange(_ obj: Notification) {
        f_1003d1cc0().controlTextDidChange(obj)
        invalidateIntrinsicContentSize()
    }

    public func control(_ control: NSControl, textView: NSTextView, doCommandBy commandSelector: Selector) -> Bool {
        guard commandSelector == #selector(NSResponder.cancelOperation(_:)) else { return false }
        cancelOperation(nil)
        return true
    }

    public override var intrinsicContentSize: NSSize { f_1003d1cc0().intrinsicContentSize }
}
