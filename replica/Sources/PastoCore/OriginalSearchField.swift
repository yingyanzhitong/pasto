import AppKit
import QuartzCore

@MainActor
open class OriginalSearchField: OriginalLayerBackedView {
    public var onShowFilters: ((NSButton) -> Void)?
    public var onClear: ((Bool) -> Void)?
    public var onUndo: (() -> Bool)?
    public var onRedo: (() -> Bool)?
    public var canAcceptFocus = true
    public private(set) var editingDelegate: OriginalSearchEditing?
    private var storedIcon: NSImageView?
    private var storedInput: OriginalSearchInputView?
    private var storedFiltersButton: NSButton?

    open func makeInputView() -> OriginalSearchInputView { OriginalSearchInputView(frame: .zero) }

    public func f_100045c2c() -> OriginalSearchInputView {
        if let storedInput { return storedInput }
        let input = makeInputView()
        let editing = OriginalSearchEditing(textView: input.f_100041f9c())
        input.f_100041f9c().delegate = editing
        editingDelegate = editing
        input.onClear = { [weak self] in self?.f_100045e54() }
        storedInput = input
        return input
    }

    public func f_100045d40() -> NSImageView {
        if let storedIcon { return storedIcon }
        let style: NSFont.TextStyle
        if #available(macOS 26, *) { style = .body } else { style = .title2 }
        let configuration = NSImage.SymbolConfiguration(textStyle: style)
        let image = Self.systemImage("magnifyingglass")
        let icon = NSImageView(image: image.withSymbolConfiguration(configuration) ?? image)
        storedIcon = icon
        return icon
    }

    private static func systemImage(_ name: String) -> NSImage {
        if NSImage(systemSymbolName: name, accessibilityDescription: nil) != nil {
            return NSImage(systemSymbolName: name, accessibilityDescription: nil)!
        }
        return NSImage(systemSymbolName: "questionmark.square", accessibilityDescription: nil)!
    }

    public func f_100045730() -> NSButton {
        if let storedFiltersButton { return storedFiltersButton }
        let button = NSButton()
        f_100045edc(button)
        storedFiltersButton = button
        return button
    }

    public func f_100045edc(_ button: NSButton) {
        button.image = Self.systemImage("line.3.horizontal.decrease")
        button.action = #selector(didClickFiltersButton)
        button.target = self
        button.refusesFirstResponder = true
        button.isBordered = false
        button.wantsLayer = true
        let shortcut = KeyboardShortcut(keyCode: OriginalShortcutFunctions.f_1001e94d4("f"),
                                       modifierRawValue: NSEvent.ModifierFlags.command.rawValue)
        button.toolTip = Self.filtersTitle() + " (" + shortcut.displayName + ")"
    }

    private static func filtersTitle() -> String {
        let values = ["cs": "Filtry", "da": "Filtre", "de": "Filter", "en": "Filters",
            "es": "Filtros", "fr": "Filtres", "he": "מסננים", "it": "Filtri",
            "ja": "フィルター", "ko": "필터", "nl": "Filters", "pl": "Filtry",
            "pt-BR": "Filtros", "pt-PT": "Filtros", "ru": "Фильтры",
            "zh-Hans": "筛选", "zh-Hant": "篩選"]
        let language = Bundle.preferredLocalizations(from: ["en"] + values.keys.filter { $0 != "en" }.sorted(),
            forPreferences: [Locale.current.identifier]).first ?? "en"
        return values[language] ?? "Filters"
    }

    public override init(frame frameRect: NSRect) {
        super.init(frame: frameRect)
        backgroundColor = OriginalSearchSurfaceAppearance.f_1001ff0d0().pointee
        for view in [f_100045d40(), f_100045c2c(), f_100045730()] as [NSView] {
            addSubview(view)
            view.translatesAutoresizingMaskIntoConstraints = false
        }
        NSLayoutConstraint.activate(f_10004639c().flatMap { $0 })
    }

    public required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    public func f_10004639c() -> [[NSLayoutConstraint]] {
        let icon = f_100045d40()
        let input = f_100045c2c()
        let filters = f_100045730()
        return [
            [icon.centerYAnchor.constraint(equalTo: centerYAnchor)],
            [icon.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 8)],
            [input.centerYAnchor.constraint(equalTo: centerYAnchor)],
            [input.heightAnchor.constraint(equalToConstant: 20)],
            [input.leadingAnchor.constraint(equalTo: icon.trailingAnchor, constant: 4)],
            [filters.topAnchor.constraint(equalTo: topAnchor), filters.bottomAnchor.constraint(equalTo: bottomAnchor)],
            [filters.leadingAnchor.constraint(equalTo: input.trailingAnchor, constant: 4)],
            [filters.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -8)]
        ]
    }

    public func f_100045e54() { onClear?(false) }

    public func f_1000460b8() {
        if let onShowFilters { onShowFilters(f_100045730()) }
    }
    @objc public func didClickFiltersButton() { f_1000460b8() }

    public func f_1000472ac() {
        super.layout()
        let input = f_100045c2c()
        input.focusRingBounds = convert(bounds, to: input)
        input.f_10004200c().focusRingBounds = input.focusRingBounds
        let radius: CGFloat
        if #available(macOS 26, *) { radius = bounds.height * 0.5 } else { radius = 6 }
        OriginalViewLayerFunctions.f_10021d49c(radius, curve: .circular, view: self)
    }

    public func f_1000473b4() { f_1000472ac() }
    open override func layout() { f_1000473b4() }

    public func f_100046b10(_ event: NSEvent) {
        if let window { window.makeFirstResponder(f_100045c2c().f_100041f9c()) }
        let textView = f_100045c2c().f_100041f9c()
        let point = textView.convert(event.locationInWindow, from: nil)
        guard let manager = textView.textLayoutManager,
              let fragment = manager.textLayoutFragment(for: point),
              let line = fragment.textLineFragments.first else { return }
        let inFragment = NSPoint(x: point.x - fragment.layoutFragmentFrame.origin.x,
                                y: point.y - fragment.layoutFragmentFrame.origin.y - line.typographicBounds.origin.y)
        let index = line.characterIndex(for: inFragment)
        let offset = manager.offset(from: manager.documentRange.location, to: fragment.rangeInElement.location)
        textView.setSelectedRange(NSRange(location: offset + index, length: 1))
    }

    public func f_1000471b4(_ event: NSEvent) {
        if let window { window.makeFirstResponder(f_100045c2c().f_100041f9c()) }
    }
    open override func mouseDown(with event: NSEvent) { f_1000471b4(event) }

    public func f_100046914(title: String, image: NSImage?) -> NSStackView {
        let filter = OriginalSearchFilterView(title: title, image: image) { [weak self] event in
            Self.f_100046acc(event, field: self)
        }
        let stack = NSStackView(views: [filter])
        stack.edgeInsets = NSEdgeInsets(top: 0, left: 0, bottom: 0, right: 4)
        return stack
    }

    @discardableResult
    public static func f_100046acc(_ event: NSEvent, field: OriginalSearchField?) -> Int {
        field?.f_100046b10(event)
        return 0
    }

    public func f_100047450(_ event: NSEvent) -> Bool {
        let responder = window?.firstResponder
        let textView = f_100045c2c().f_100041f9c()
        if let responder, responder.isEqual(textView) {
            let shortcut = OriginalShortcutFunctions.f_1001e7d18(event)
            let undoKey = OriginalShortcutFunctions.f_1001e94d4("z")
            if shortcut.keyCode == undoKey, shortcut.modifierRawValue == 0x100000 {
                return onUndo?() ?? false
            }
            let redoKey = OriginalShortcutFunctions.f_1001e94d4("z")
            if shortcut.keyCode == redoKey, shortcut.modifierRawValue == 0x120000 {
                return onRedo?() ?? false
            }
        }
        return super.performKeyEquivalent(with: event)
    }

    public func f_1000475fc(_ event: NSEvent) -> Bool { f_100047450(event) }
    open override func performKeyEquivalent(with event: NSEvent) -> Bool { f_1000475fc(event) }
}
