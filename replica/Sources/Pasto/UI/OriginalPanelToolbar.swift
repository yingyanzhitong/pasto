import AppKit
import SwiftUI
import Combine
import PastoCore

/// Native constraint/animation owner for the recovered Toolbar search transition.
/// The native tab stack retains its cells across search transitions. This does
/// not claim the complete original toolbar's data source and coordinator chain.
@MainActor
struct OriginalPanelToolbar: NSViewRepresentable {
    let state: ReplicaUIState
    let isSearching: Bool
    let searchButton: AnyView
    let searchField: ReplicaSearchEditor
    let tabConfiguration: (ClipboardListTarget) -> OriginalPinboardTab
    let createButton: AnyView
    let menuButton: AnyView
    let onDismiss: () -> Void

    final class Coordinator {
        weak var state: ReplicaUIState?
        init(_ state: ReplicaUIState) { self.state = state }
    }

    func makeCoordinator() -> Coordinator { Coordinator(state) }

    func makeNSView(context: Context) -> OriginalPanelToolbarView {
        let view = OriginalPanelToolbarView()
        state.toolbarOwner = view
        view.observeLists(state.tabListPublisher, configuration: tabConfiguration,
            selection: state.$selectedTabList.compactMap { $0 }.eraseToAnyPublisher(),
            currentSelection: { [weak state = state] in state?.selectedTabList })
        updateNSView(view, context: context)
        view.searchBar.observeQuery(state.searchInputPublisher, initial: state.searchQueryNodes)
        view.observeListEditing(state.beginEditingListSubject.eraseToAnyPublisher())
        return view
    }

    func updateNSView(_ view: OriginalPanelToolbarView, context: Context) {
        view.onDismiss = onDismiss
        view.searchBar.isFilterPopoverDisplayed = { [weak state = state] in
            state?.controller?.filterBrowserPopover?.isDisplayed == true
        }
        view.updateTabConfiguration(tabConfiguration)
        view.configure(searchButton: searchButton, searchField: searchField,
                       createButton: createButton, menuButton: menuButton, active: isSearching,
                       focusRequest: state.searchFocus)
    }

    static func dismantleNSView(_ view: OriginalPanelToolbarView, coordinator: Coordinator) {
        if coordinator.state?.toolbarOwner === view { coordinator.state?.toolbarOwner = nil }
        view.stopObservingListEditing()
        view.stopObservingLists()
        view.searchBar.dismantleEditor()
        view.onDismiss = nil
    }
}

@MainActor
final class OriginalPanelToolbarView: NSView {
    let searchBar = OriginalPanelSearchBar()
    private let tabBar = OriginalPanelTabBar()
    private var listEditingObservation: AnyCancellable?
    private let createButton = NSHostingView(rootView: AnyView(EmptyView()))
    private let menuButton = NSHostingView(rootView: AnyView(EmptyView()))
    private var activeSearchConstraints: [NSLayoutConstraint] = []
    private var configured = false
    private var focusRequest: UUID?
    var onDismiss: (() -> Void)?

    override init(frame frameRect: NSRect) {
        super.init(frame: frameRect)
        for view in [searchBar, tabBar, createButton, menuButton] as [NSView] {
            view.translatesAutoresizingMaskIntoConstraints = false
            addSubview(view)
        }
        searchBar.onActivate = { [weak self] in self?.f_10000df98() }
        searchBar.onDismiss = { [weak self] in self?.f_10000e0ec() }
        // 00d884: centering is low priority, create-leading is 750. There is
        // no recovered "tabs width >= 250" constraint (250 is the priority).
        let centeredTabs = tabBar.centerXAnchor.constraint(equalTo: centerXAnchor)
        centeredTabs.priority = NSLayoutConstraint.Priority(250)
        let createLeading = createButton.leadingAnchor.constraint(equalTo: tabBar.trailingAnchor, constant: 8)
        createLeading.priority = NSLayoutConstraint.Priority(750)
        let menuGap: CGFloat
        if #available(macOS 26, *) { menuGap = 8 } else { menuGap = 16 }
        NSLayoutConstraint.activate([
            // The local offline toolbar has no notification bar: its empty
            // leading slot contributes the original 16 + 8 point boundary.
            searchBar.leadingAnchor.constraint(greaterThanOrEqualTo: leadingAnchor, constant: 24),
            searchBar.centerYAnchor.constraint(equalTo: centerYAnchor),
            tabBar.leadingAnchor.constraint(equalTo: searchBar.trailingAnchor, constant: 8),
            tabBar.centerYAnchor.constraint(equalTo: centerYAnchor),
            tabBar.heightAnchor.constraint(equalToConstant: 40), centeredTabs,
            createButton.centerYAnchor.constraint(equalTo: centerYAnchor), createLeading,
            createButton.trailingAnchor.constraint(lessThanOrEqualTo: menuButton.leadingAnchor, constant: -menuGap),
            menuButton.centerYAnchor.constraint(equalTo: centerYAnchor),
            menuButton.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -16),
            menuButton.widthAnchor.constraint(equalToConstant: 44),
            menuButton.heightAnchor.constraint(equalToConstant: 44)
        ])
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    func configure(searchButton: AnyView, searchField: ReplicaSearchEditor,
                   createButton: AnyView, menuButton: AnyView, active: Bool, focusRequest: UUID) {
        let focusChanged = self.focusRequest != focusRequest
        self.focusRequest = focusRequest
        searchBar.configure(button: searchButton, field: searchField)
        self.createButton.rootView = createButton
        self.menuButton.rootView = menuButton
        if !configured {
            configured = true
            if active { activeSearchConstraints = f_10000e4c8(); NSLayoutConstraint.activate(activeSearchConstraints) }
            OriginalViewAnimation.f_10021cadc(duration: nil,
                timingFunction: OriginalViewAnimation.f_10021ccd4(), animated: false,
                animations: { self.f_10000e74c(active) })
        } else if searchBar.isActive != active {
            if active { f_10000df98() } else { transitionToInactive() }
        } else if active, focusChanged {
            searchBar.requestFocus()
        }
    }

    func observeLists(_ publisher: AnyPublisher<ClipboardPinboardCollection.ListSnapshot, Never>,
                      configuration: @escaping (ClipboardListTarget) -> OriginalPinboardTab,
                      selection: AnyPublisher<ClipboardListTarget, Never>,
                      currentSelection: @escaping () -> ClipboardListTarget?) {
        tabBar.observeLists(publisher, configuration: configuration,
                            selection: selection, currentSelection: currentSelection)
    }

    func updateTabConfiguration(_ configuration: @escaping (ClipboardListTarget) -> OriginalPinboardTab) {
        tabBar.updateConfiguration(configuration)
    }

    func stopObservingLists() { tabBar.stopObservingLists() }

    func observeListEditing(_ publisher: AnyPublisher<ClipboardListTarget, Never>) {
        listEditingObservation = publisher.sink { [weak self] target in
            MainActor.assumeIsolated { self?.tabBar.beginEditingList(target) }
        }
    }

    func stopObservingListEditing() {
        listEditingObservation?.cancel()
        listEditingObservation = nil
    }

    func moveList(_ source: ClipboardListTarget, to target: ClipboardListTarget,
                  persist: (Int) -> Void) -> Bool {
        tabBar.moveList(source, to: target, persist: persist)
    }

    func applySearchQuery(_ nodes: [OriginalSearchQueryNode]) { searchBar.applySearchQuery(nodes) }

    private func f_10000e4c8() -> [NSLayoutConstraint] {
        [searchBar.centerXAnchor.constraint(equalTo: centerXAnchor),
         searchBar.widthAnchor.constraint(greaterThanOrEqualToConstant: 400),
         searchBar.widthAnchor.constraint(greaterThanOrEqualTo: widthAnchor, multiplier: 0.25),
         createButton.trailingAnchor.constraint(equalTo: tabBar.trailingAnchor)]
    }

    private func f_10000df98() {
        NSLayoutConstraint.deactivate(activeSearchConstraints)
        activeSearchConstraints = f_10000e4c8()
        NSLayoutConstraint.activate(activeSearchConstraints)
        OriginalViewAnimation.f_10021cadc(duration: nil,
            timingFunction: OriginalViewAnimation.f_10021ccd4(), animated: true,
            animations: { self.f_10000e74c(true) })
    }

    // 00e0ec: these are action-block effects, not an animation completion.
    func f_10000e0ec() {
        transitionToInactive()
        onDismiss?()
    }

    private func transitionToInactive() {
        NSLayoutConstraint.deactivate(activeSearchConstraints)
        OriginalViewAnimation.f_10021cadc(duration: nil,
            timingFunction: OriginalViewAnimation.f_10021ccd4(), animated: true,
            animations: { self.f_10000e74c(false) })
    }

    private func f_10000e74c(_ active: Bool) {
        searchBar.setActive(active)
        tabBar.setCollapsed(active)
        createButton.isHidden = active
        layoutSubtreeIfNeeded()
    }
}

@MainActor
final class OriginalPanelSearchBar: NSView {
    private let button = NSHostingView(rootView: AnyView(EmptyView()))
    private let fieldHost = NSView()
    private var field: ReplicaSearchEditor.SearchField?
    private var coordinator: ReplicaSearchEditor.Coordinator?
    private var queryObservation: AnyCancellable?
    private(set) var isActive = false
    var isFilterPopoverDisplayed: (() -> Bool)?
    var onActivate: (() -> Void)?
    var onDismiss: (() -> Void)?

    override init(frame frameRect: NSRect) {
        super.init(frame: frameRect)
        for view in [button, fieldHost] as [NSView] { view.translatesAutoresizingMaskIntoConstraints = false; addSubview(view) }
        NSLayoutConstraint.activate([
            heightAnchor.constraint(equalTo: button.heightAnchor),
            button.centerXAnchor.constraint(equalTo: centerXAnchor),
            button.centerYAnchor.constraint(equalTo: centerYAnchor),
            fieldHost.leadingAnchor.constraint(equalTo: leadingAnchor), fieldHost.trailingAnchor.constraint(equalTo: trailingAnchor),
            fieldHost.centerYAnchor.constraint(equalTo: centerYAnchor), fieldHost.heightAnchor.constraint(equalToConstant: 32)
        ])
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }
    // 03ed28 forwards the search button's intrinsic size even while active;
    // only the active-search constraints expand its width.
    override var intrinsicContentSize: NSSize { button.fittingSize }

    override func hitTest(_ point: NSPoint) -> NSView? {
        guard super.hitTest(point) != nil else { return nil }
        // Alpha-zero AppKit views still receive hits during the search transition.
        let target = isActive ? fieldHost : button
        return target.hitTest(convert(point, from: superview))
    }

    func configure(button: AnyView, field specification: ReplicaSearchEditor) {
        var specification = specification
        specification.onApplySuggestion = { [weak self] nodes in self?.applySearchQuery(nodes) }
        specification.onDismissSuggestions = { [weak self] in self?.coordinator?.dismissSuggestions() }
        specification.onSuggestionAnchor = { [weak self] range in self?.suggestionAnchor(for: range) }
        self.button.rootView = button
        if let field, let coordinator {
            coordinator.suggestionOwner = self
            specification.updateField(field, coordinator: coordinator)
        } else {
            let coordinator = ReplicaSearchEditor.Coordinator(specification)
            coordinator.suggestionOwner = self
            let field = specification.makeField(coordinator: coordinator)
            self.coordinator = coordinator
            self.field = field
            field.translatesAutoresizingMaskIntoConstraints = false
            fieldHost.addSubview(field)
            NSLayoutConstraint.activate([
                field.leadingAnchor.constraint(equalTo: fieldHost.leadingAnchor),
                field.trailingAnchor.constraint(equalTo: fieldHost.trailingAnchor),
                field.topAnchor.constraint(equalTo: fieldHost.topAnchor),
                field.bottomAnchor.constraint(equalTo: fieldHost.bottomAnchor)
            ])
        }
        invalidateIntrinsicContentSize()
    }

    func setActive(_ active: Bool) {
        isActive = active
        f_10003e350()
    }

    private func f_10003e350() {
        button.alphaValue = isActive ? 0 : 1
        fieldHost.alphaValue = isActive ? 1 : 0
        let (field, _) = inputPair()
        field.canAcceptFocus = isActive
        field.f_100045c2c().f_100041f9c().canAcceptFocus = field.canAcceptFocus
        OriginalViewAnimation.f_10021cadc(duration: nil,
            timingFunction: OriginalViewAnimation.f_10021ccd4(), animated: true,
            animations: { self.f_100040054() })
    }

    private func inputPair() -> (ReplicaSearchEditor.SearchField, ReplicaSearchEditor.Coordinator) {
        guard let field, let coordinator else { preconditionFailure("Search input coordinator is not installed") }
        return (field, coordinator)
    }

    private func f_100040054() {
        let (field, coordinator) = inputPair()
        let editor = field.f_100045c2c().f_100041f9c() as! ReplicaSearchEditor.SearchTextView
        if isActive {
            guard isFilterPopoverDisplayed?() != true else { return }
            if let window { window.makeFirstResponder(editor) }
        } else {
            coordinator.clearInput(preserveHistory: false, field: field, editor: editor)
            // 040054 publishes the current query again even if reset did not
            // change it; do not replace this with an equal-query early return.
            coordinator.publishCurrentQuery()
            window?.makeFirstResponder(nil)
        }
    }

    func requestFocus() { if isActive { f_100040054() } }

    override func viewDidMoveToWindow() {
        super.viewDidMoveToWindow()
        // The SwiftUI toolbar can be attached after its first native action.
        // This mounting retry replaces the old editor requestedFocus bridge.
        if window != nil, isActive { requestFocus() }
    }

    var filterQuerySnapshot: [OriginalSearchQueryNode] {
        guard let coordinator else { preconditionFailure("Search input coordinator is not installed") }
        return coordinator.querySnapshot
    }

    // 0407f8: nil owner/manager is no anchor; a zero helper rectangle remains valid.
    func suggestionAnchor(for range: NSRange) -> NSRect? {
        let (field, _) = inputPair()
        let editor = field.f_100045c2c().f_100041f9c() as! ReplicaSearchEditor.SearchTextView
        guard let manager = editor.textLayoutManager else { return nil }
        manager.textViewportLayoutController.layoutViewport()
        let rect = OriginalSearchSuggestionAnchor.f_100046e28(manager, range: range)
        return editor.convert(rect, to: field)
    }

    func performSuggestionRequest(_ context: OriginalSearchInputContext.Context) {
        let (field, coordinator) = inputPair()
        coordinator.performSuggestionRequest(context, field: field)
    }

    func applySearchQuery(_ nodes: [OriginalSearchQueryNode]) {
        let (field, coordinator) = inputPair()
        let editor = field.f_100045c2c().f_100041f9c() as! ReplicaSearchEditor.SearchTextView
        coordinator.applyProgrammaticQuery(nodes, field: field, editor: editor)
    }

    func observeQuery(_ publisher: AnyPublisher<[OriginalSearchQueryNode], Never>, initial: [OriginalSearchQueryNode]) {
        // 03e9bc -> filter(03fe8c) -> 041b80/03ff40: empty model values
        // are excluded. A timer's [] is cleared by onDismiss, not this sink.
        queryObservation = publisher.prepend(initial)
            .filter { !OriginalSearchQuery.f_1002ddcf0($0) }
            .sink { [weak self] nodes in
                guard let self else { return }
                self.f_10003e658()
                let (field, coordinator) = self.inputPair()
                let editor = field.f_100045c2c().f_100041f9c() as! ReplicaSearchEditor.SearchTextView
                coordinator.synchronizeQuery(nodes, field: field, editor: editor)
            }
    }

    // 041b98 -> 03e61c: the native button action enters this dispatcher directly.
    func f_10003e658() {
        guard isActive else { onActivate?(); return }
        let (_, coordinator) = inputPair()
        if coordinator.isQueryEmpty { onDismiss?() }
        else { requestFocus() }
    }

    func dismantleEditor() {
        queryObservation?.cancel()
        queryObservation = nil
        if let field, let coordinator { ReplicaSearchEditor.dismantleField(field, coordinator: coordinator) }
        isFilterPopoverDisplayed = nil
        onActivate = nil
        onDismiss = nil
    }
}

