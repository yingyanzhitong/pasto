import AppKit
import QuartzCore

@MainActor
public final class OriginalSearchFilterView: NSView {
    public let stackView = NSStackView()
    public let iconView = NSImageView()
    public let label = NSTextField()
    public var onClick: ((NSEvent) -> Void)?

    /// The original constructor's filter title and image providers are resolved
    /// by the caller. The filter enum and service lookup are tracked separately.
    public init(title: String, image: NSImage?, onClick: ((NSEvent) -> Void)?) {
        self.onClick = onClick
        super.init(frame: .zero)
        wantsLayer = true
        iconView.image = image
        iconView.contentTintColor = .labelColor
        label.isEditable = false
        label.isSelectable = false
        label.isBordered = false
        label.drawsBackground = false
        label.font = OriginalSearchAppearance.f_1001ff928()
        label.textColor = .labelColor
        label.stringValue = title
        stackView.orientation = .horizontal
        stackView.alignment = .centerY
        stackView.spacing = 2
        stackView.addArrangedSubview(iconView)
        stackView.addArrangedSubview(label)
        addSubview(stackView)
        stackView.translatesAutoresizingMaskIntoConstraints = false
        iconView.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate(f_1000450a8().flatMap { $0 })
    }

    public override init(frame frameRect: NSRect) {
        fatalError("init(frame:) is unavailable for OriginalSearchFilterView")
    }

    public required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    public func f_1000450a8() -> [[NSLayoutConstraint]] {
        [
            [stackView.topAnchor.constraint(equalTo: topAnchor, constant: 2),
             stackView.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 6),
             stackView.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -2),
             stackView.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -6)],
            [iconView.widthAnchor.constraint(equalToConstant: 12),
             iconView.heightAnchor.constraint(equalToConstant: 12)]
        ]
    }

    @discardableResult
    public func f_100045338() -> Int {
        super.layout()
        OriginalViewLayerFunctions.f_10021d49c(bounds.height * 0.5, curve: .continuous, view: self)
        layer?.backgroundColor = OriginalSearchSurfaceAppearance.f_1001ff0d0().pointee?.cgColor
        return 0
    }

    public func f_1000453e8() { f_100045338() }
    public override func layout() { f_1000453e8() }

    public func f_100045484(_ event: NSEvent) { onClick?(event) }
    public override func mouseDown(with event: NSEvent) { f_100045484(event) }
}

@MainActor
public final class OriginalFilterTextAttachment: NSTextAttachment {
    public let makeView: () -> NSView

    public init(makeView: @escaping () -> NSView) {
        self.makeView = makeView
        super.init(data: nil, ofType: nil)
    }

    public required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    public override init(data contentData: Data?, ofType uti: String?) {
        fatalError("init(data:ofType:) is unavailable for OriginalFilterTextAttachment")
    }

    public func f_1002f5a50(for parentView: NSView?, location: any NSTextLocation,
                           textContainer: NSTextContainer?) -> NSTextAttachmentViewProvider {
        OriginalFilterTextAttachmentViewProvider(textAttachment: self, parentView: parentView,
            textLayoutManager: textContainer?.textLayoutManager, location: location)
    }

    public override func viewProvider(for parentView: NSView?, location: any NSTextLocation,
                                       textContainer: NSTextContainer?) -> NSTextAttachmentViewProvider? {
        f_1002f5a50(for: parentView, location: location, textContainer: textContainer)
    }
}

@MainActor
public final class OriginalFilterTextAttachmentViewProvider: NSTextAttachmentViewProvider {
    public override init(textAttachment: NSTextAttachment, parentView: NSView?,
                         textLayoutManager: NSTextLayoutManager?, location: any NSTextLocation) {
        super.init(textAttachment: textAttachment, parentView: parentView,
                   textLayoutManager: textLayoutManager, location: location)
        tracksTextAttachmentViewBounds = true
    }

    @discardableResult
    public func f_1002f5c94() -> Int {
        if let attachment = textAttachment as? OriginalFilterTextAttachment {
            view = attachment.makeView()
            view?.translatesAutoresizingMaskIntoConstraints = false
        }
        return 0
    }

    public func f_1002f5d4c() { f_1002f5c94() }
    public override func loadView() { f_1002f5d4c() }

    public func f_1002f5d74() -> CGRect {
        guard let view else { return .zero }
        let size = view.fittingSize
        return CGRect(x: 0, y: size.height * -0.25, width: size.width, height: size.height)
    }

    public override func attachmentBounds(for attributes: [NSAttributedString.Key: Any],
                                          location: any NSTextLocation, textContainer: NSTextContainer?,
                                          proposedLineFragment: CGRect, position: CGPoint) -> CGRect {
        f_1002f5d74()
    }
}
