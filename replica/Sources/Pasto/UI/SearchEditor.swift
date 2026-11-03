import AppKit
import PastoCore

struct ReplicaSearchFilterChip {
    enum Selection: Hashable {
        case kind(ClipboardKind), source(String), device(String), date(OriginalSearchDateFilter), pinboard(String)
    }
    let selection: Selection
    let title: String
    let image: NSImage?
}

private let searchFilterSelectionKey = NSAttributedString.Key("com.pastereplica.search.filter")

/// Configuration for the native toolbar's retained field/coordinator pair.
/// The toolbar owns activation and focus; this value owns input projection.
@MainActor
struct ReplicaSearchEditor {
    let store: ClipboardStore
    var queryNodes: [OriginalSearchQueryNode]
    var filters: [ReplicaSearchFilterChip]
    var onInputChange: (String, [ReplicaSearchFilterChip.Selection], [OriginalSearchQueryNode]) -> Void
    var onLoadSuggestions: (OriginalSearchInputContext.Context) -> [OriginalSearchQueryNode]
    var onEnter: () -> Void
    var onCancel: () -> Void
    var onShowFilters: (NSButton) -> Void
    var onEditingEnded: (NSView) -> Void = { _ in }
    var onApplySuggestion: ([OriginalSearchQueryNode]) -> Void = { _ in }
    var onDismissSuggestions: () -> Void = {}
    var onSuggestionAnchor: (NSRange) -> NSRect? = { _ in nil }

    func makeField(coordinator: Coordinator) -> SearchField {
        let field = SearchField(frame: .zero)
        let input = field.f_100045c2c()
        let editor = input.f_100041f9c() as! SearchTextView
        field.canAcceptFocus = false
        editor.canAcceptFocus = false
        let scroll = input.f_10004200c()
        editor.frame = NSRect(x: 0, y: 0, width: scroll.contentSize.width, height: 22)
        editor.allowsUndo = true
        editor.autoresizingMask = [.width]
        editor.setAccessibilityLabel("搜索剪贴板")
        editor.setAccessibilityIdentifier("clipboard-search")
        coordinator.attach(field, editor: editor)
        coordinator.updateContents(field, editor: editor)
        field.onClear = { [weak coordinator, weak field, weak editor] _ in
            guard let coordinator, let field, let editor else { return }
            // 041bf0 -> 040c64 ignores the field's flag and selects mode1.
            coordinator.clearInput(preserveHistory: true, field: field, editor: editor)
        }
        field.onShowFilters = { [weak coordinator] button in
            coordinator?.dismissSuggestions()
            coordinator?.parent.onShowFilters(button)
        }
        input.f_100042090().setAccessibilityLabel("清空搜索")
        field.f_100045730().setAccessibilityLabel("筛选")
        return field
    }

    func updateField(_ field: SearchField, coordinator: Coordinator) {
        coordinator.parent = self
        let input = field.f_100045c2c()
        guard let editor = input.f_100041f9c() as? SearchTextView else { return }
        coordinator.updateContents(field, editor: editor)
    }

    static func dismantleField(_ field: SearchField, coordinator: Coordinator) {
        coordinator.dismissSuggestions()
        field.onClear = nil
        field.onShowFilters = nil
    }

    final class SearchField: OriginalSearchField {
        override func makeInputView() -> OriginalSearchInputView { InputView(frame: .zero) }
    }

    final class InputView: OriginalSearchInputView {
        override func makeTextView() -> OriginalSearchTextView {
            SearchTextView(usingTextLayoutManager: true)
        }
    }

    @MainActor final class Coordinator {
        var parent: ReplicaSearchEditor
        private var renderedFilters: [ReplicaSearchFilterChip.Selection] = []
        private var currentNodes: [OriginalSearchQueryNode] = []
        private var knownTokens: [ReplicaSearchFilterChip.Selection: NSAttributedString] = [:]
        private let history = OriginalSearchInputHistory(interval: 0.4)
        private var applyingContents = false
        private var restoringHistory = false
        private var suggestionTask: Task<Void, Never>?
        private var suggestionMenu: ReplicaSearchSuggestionsMenu?
        weak var suggestionOwner: OriginalPanelSearchBar?
        init(_ parent: ReplicaSearchEditor) { self.parent = parent }

        private struct Projection {
            let text: String
            let filters: [ReplicaSearchFilterChip.Selection]
            let nodes: [OriginalSearchQueryNode]
            let rawNodes: [OriginalSearchQueryNode]
            var needsNormalization: Bool { nodes != rawNodes }
        }

        private func contents(_ storage: NSAttributedString, text: String) -> Projection {
            var selections: [ReplicaSearchFilterChip.Selection] = []
            var nodes: [OriginalSearchQueryNode] = []
            var buffer = ""
            let string = text as NSString
            storage.enumerateAttributes(in: NSRange(location: 0, length: storage.length)) { attributes, range, _ in
                let selection = attributes[searchFilterSelectionKey] as? ReplicaSearchFilterChip.Selection
                var location = range.location
                for character in string.substring(with: range) {
                    defer { location += String(character).utf16.count }
                    if character == "\u{FFFC}" {
                        OriginalSearchTextTokens.f_1002f8760(&buffer, into: &nodes)
                        if let selection {
                            selections.append(selection)
                            nodes.append(selection.queryNode)
                            self.knownTokens[selection] = storage.attributedSubstring(
                                from: NSRange(location: location, length: 1))
                        }
                    } else { buffer.append(character) }
                }
            }
            OriginalSearchTextTokens.f_1002f8760(&buffer, into: &nodes)
            let normalized = OriginalSearchQueryNormalization.f_1002da16c(nodes, flag: 0)
            let filters = normalized.compactMap { node -> ReplicaSearchFilterChip.Selection? in
                guard case .filter = node else { return nil }
                return selections.first { $0.queryNode == node }
            }
            let text = normalized.compactMap { node -> String? in
                guard case let .text(text) = node else { return nil }
                return text
            }.joined()
            return Projection(text: text, filters: filters, nodes: normalized, rawNodes: nodes)
        }

        private func chip(for node: OriginalSearchQueryNode) -> ReplicaSearchFilterChip? {
            guard case let .filter(kind, value) = node else { return nil }
            let selection: ReplicaSearchFilterChip.Selection
            switch kind {
            case 0: selection = .source(value)
            case 1:
                let type: ClipboardKind
                switch value.lowercased() {
                case "text": type = .text
                case "link": type = .link
                case "image": type = .image
                case "file": type = .files
                case "color": type = .color
                case "unknown": type = .unknown
                default: return nil
                }
                selection = .kind(type)
            case 3:
                let parts = value.split(separator: " ")
                guard parts.count == 2, let start = Int(parts[0]), let end = Int(parts[1]), start < end else { return nil }
                let range = Date(timeIntervalSince1970: Double(start))..<Date(timeIntervalSince1970: Double(end))
                selection = .date(.init(title: OriginalSearchDateEncoding.f_1002d8e9c(value) ?? value, range: range))
            case 4: selection = .device(value)
            case 5: selection = .pinboard(value)
            default: return nil
            }
            return ReplicaFilterMatching.chip(selection, store: parent.store, rawValue: value)
        }

        func dismissSuggestions() {
            suggestionTask?.cancel()
            suggestionTask = nil
            dismissSuggestionMenu()
        }

        private func dismissSuggestionMenu() {
            suggestionMenu?.dismiss()
            suggestionMenu = nil
        }

        private func updateSuggestions(_ field: SearchField, editor: SearchTextView) {
            suggestionTask?.cancel()
            suggestionTask = nil
            guard !applyingContents, !editor.hasMarkedText(),
                  editor.window?.firstResponder === editor,
                  let context = OriginalSearchInputContext.f_1002f78f8(currentNodes, caret: editor.selectedRange().location) else {
                dismissSuggestions()
                return
            }
            // 040ec4 weak-loads the SearchBar;040f44 releases it after the child request.
            suggestionTask = Task { @MainActor [weak owner = suggestionOwner] in
                guard let owner else { return }
                defer { withExtendedLifetime(owner) {} }
                owner.performSuggestionRequest(context)
            }
        }

        func performSuggestionRequest(_ context: OriginalSearchInputContext.Context,
                                      field: SearchField) {
            let candidates = parent.onLoadSuggestions(context)
            guard !Task.isCancelled, !candidates.isEmpty else {
                dismissSuggestionMenu()
                return
            }
            let entries = candidates.compactMap { node -> (OriginalSearchSuggestions.Suggestion, ReplicaSearchFilterChip)? in
                guard case let .filter(tag, value) = node, let chip = self.chip(for: node) else { return nil }
                return (.filter(tag, value), chip)
            }
            guard !entries.isEmpty else {
                self.dismissSuggestionMenu()
                return
            }
            let menu = self.suggestionMenu ?? ReplicaSearchSuggestionsMenu()
            self.suggestionMenu = menu
            guard let anchorRect = parent.onSuggestionAnchor(context.anchorRange) else { return }
            let applySuggestion = self.parent.onApplySuggestion
            let dismissSuggestions = self.parent.onDismissSuggestions
            menu.show(rows: entries.map { .init(title: $0.1.title, image: $0.1.image, matchQuery: context.text) },
                      anchorRect: anchorRect, in: field,
                      onAccept: { index in
                guard entries.indices.contains(index) else { return }
                Self.accept(entries[index].0, context: context, apply: applySuggestion)
            }, onEscape: dismissSuggestions)
        }

        // 041de0 -> 04160c merges the captured context, then proposes to the weak SearchBar.
        private static func accept(_ suggestion: OriginalSearchSuggestions.Suggestion,
                                   context: OriginalSearchInputContext.Context,
                                   apply: ([OriginalSearchQueryNode]) -> Void) {
            let nodes = OriginalSearchSuggestions.f_1002dcca4(suggestion,
                index: context.nodeIndex, addMode: 0, nodes: context.nodes)
            apply(nodes)
        }

        private func attributedString(_ nodes: [OriginalSearchQueryNode], field: SearchField,
                                      editor: SearchTextView) -> NSAttributedString {
            let result = NSMutableAttributedString(string: "")
            for node in nodes {
                switch node {
                case let .text(text):
                    result.append(NSAttributedString(string: text, attributes: editor.preferredTypingAttributes))
                case .filter:
                    let token: NSMutableAttributedString
                    if let filter = parent.filters.first(where: { $0.selection.queryNode == node }) ?? chip(for: node) {
                        let attachment = OriginalFilterTextAttachment { [weak field] in
                            field?.f_100046914(title: filter.title, image: filter.image) ?? NSView()
                        }
                        token = NSMutableAttributedString(attributedString: NSAttributedString(attachment: attachment))
                        token.addAttribute(searchFilterSelectionKey, value: filter.selection,
                                           range: NSRange(location: 0, length: token.length))
                        knownTokens[filter.selection] = token.copy() as? NSAttributedString
                    } else {
                        // Undo retains the actual token metadata even after the filter leaves the model.
                        guard let tokenValue = knownTokens.first(where: { $0.key.queryNode == node })?.value else {
                            preconditionFailure("Search history lost its filter token")
                        }
                        token = NSMutableAttributedString(attributedString: tokenValue)
                    }
                    token.addAttributes(editor.preferredTypingAttributes,
                                        range: NSRange(location: 0, length: token.length))
                    result.append(token)
                }
            }
            return result
        }

        private func display(_ value: NSAttributedString, selection: NSRange,
                             field: SearchField, editor: SearchTextView) {
            applyingContents = true
            editor.textStorage?.setAttributedString(value)
            field.f_100045c2c().f_1000449e8()
            editor.setSelectedRange(selection)
            editor.scrollRangeToVisible(selection)
            applyingContents = false
        }

        private func publish(_ value: Projection) {
            currentNodes = value.nodes
            renderedFilters = value.filters
            parent.onInputChange(value.text, value.filters, value.nodes)
        }

        func updateContents(_ field: SearchField, editor: SearchTextView) {
            guard !applyingContents, !editor.hasMarkedText(), let storage = editor.textStorage else { return }
            let selections = parent.filters.map(\.selection)
            let previous = contents(storage, text: editor.f_1000f7254())
            let nodes = OriginalSearchQueryNormalization.f_1002da16c(parent.queryNodes, flag: 0)
            guard previous.nodes != nodes || previous.needsNormalization else { return }
            dismissSuggestions()
            let result = attributedString(nodes, field: field, editor: editor)
            let selection = NSRange(location: result.length, length: 0)
            display(result, selection: selection, field: field, editor: editor)
            if currentNodes != nodes {
                history.f_1002f5e18(.init(nodes: nodes, selection: selection), immediate: true)
            }
            currentNodes = nodes
            renderedFilters = selections
        }

        private func filterCount(_ nodes: [OriginalSearchQueryNode]) -> Int {
            nodes.reduce(0) { count, node in
                if case .filter = node { return count + 1 }
                return count
            }
        }

        private func propose(_ proposed: NSAttributedString, selection: NSRange,
                             field: SearchField, editor: SearchTextView) -> Bool {
            guard !editor.hasMarkedText() else { return true }
            let value = contents(proposed, text: proposed.string)
            guard value.nodes != currentNodes else { return true }
            let previousNodes = currentNodes
            currentNodes = value.nodes
            if !restoringHistory {
                history.f_1002f5e18(.init(nodes: value.nodes, selection: selection),
                                    immediate: filterCount(value.nodes) != filterCount(previousNodes))
            }
            guard value.needsNormalization else {
                publish(value)
                return true
            }
            let rendered = attributedString(value.nodes, field: field, editor: editor)
            display(rendered, selection: NSRange(location: rendered.length, length: 0),
                    field: field, editor: editor)
            publish(value)
            dismissSuggestions()
            return false
        }

        private func restore(_ snapshot: OriginalSearchInputHistory.Snapshot?,
                             field: SearchField, editor: SearchTextView) -> Bool {
            guard let snapshot else { return false }
            restoringHistory = true
            defer { restoringHistory = false }
            currentNodes = snapshot.nodes
            let rendered = attributedString(snapshot.nodes, field: field, editor: editor)
            display(rendered, selection: snapshot.selection, field: field, editor: editor)
            let value = contents(rendered, text: rendered.string)
            renderedFilters = value.filters
            parent.onInputChange(value.text, value.filters, snapshot.nodes)
            dismissSuggestions()
            return true
        }

        func clearInput(preserveHistory: Bool, field: SearchField, editor: SearchTextView) {
            // 2f7d60 always runs mode0 query replacement, then optionally
            // clears history. Clear-button mode1 keeps its newly recorded undo.
            applyProgrammaticQuery([], field: field, editor: editor)
            if !preserveHistory { history.f_1002f6550() }
        }

        // 2f7744 mode0: internal query -> builder/history -> editor -> public
        // query -> empty suggestions. The equal-query branch has no callbacks.
        func applyProgrammaticQuery(_ nodes: [OriginalSearchQueryNode], field: SearchField, editor: SearchTextView) {
            replaceQuery(nodes, suggestionsEnabled: false, field: field, editor: editor)
        }

        // SearchBar's filtered nonempty query subscriber selects mode1.
        func synchronizeQuery(_ nodes: [OriginalSearchQueryNode], field: SearchField, editor: SearchTextView) {
            replaceQuery(nodes, suggestionsEnabled: true, field: field, editor: editor)
        }

        private func replaceQuery(_ nodes: [OriginalSearchQueryNode], suggestionsEnabled: Bool,
                                  field: SearchField, editor: SearchTextView) {
            let normalized = OriginalSearchQueryNormalization.f_1002da16c(nodes, flag: 0)
            guard normalized != currentNodes else { return }
            currentNodes = normalized
            let rendered = attributedString(normalized, field: field, editor: editor)
            let selection = NSRange(location: rendered.length, length: 0)
            if !restoringHistory {
                history.f_1002f5e18(.init(nodes: normalized, selection: selection), immediate: true)
            }
            display(rendered, selection: selection, field: field, editor: editor)
            renderedFilters = contents(rendered, text: rendered.string).filters
            publishCurrentQuery()
            if suggestionsEnabled { updateSuggestions(field, editor: editor) }
            else { dismissSuggestions() }
        }

        func publishCurrentQuery() {
            let text = currentNodes.compactMap { node -> String? in
                guard case let .text(value) = node else { return nil }
                return value
            }.joined()
            parent.onInputChange(text, renderedFilters, currentNodes)
        }

        var querySnapshot: [OriginalSearchQueryNode] { currentNodes }
        var isQueryEmpty: Bool { OriginalSearchQuery.f_1002ddcf0(currentNodes) }

        func attach(_ field: SearchField, editor: SearchTextView) {
            let editing = field.editingDelegate!
            editing.onTextShouldChange = { [weak self, weak field, weak editor] proposed, selection in
                guard let self, let field, let editor else { return true }
                return self.propose(proposed, selection: selection, field: field, editor: editor)
            }
            editing.onSelectionChange = { [weak self, weak field, weak editor] _ in
                guard let self, let field, let editor, !self.applyingContents else { return }
                self.updateSuggestions(field, editor: editor)
            }
            editing.onEndEditing = { [weak self, weak field] in
                guard let self, let field else { return }
                self.dismissSuggestions()
                self.parent.onEditingEnded(field)
            }
            editing.onEnter = { [weak self, weak editor] in
                guard let self else { return }
                if let panel = editor?.window as? ReplicaPanel {
                    _ = panel.makeFirstResponder(nil)
                } else {
                    self.parent.onEnter()
                }
            }
            editing.onCancel = { [weak self] in self?.parent.onCancel() }
            editor.delegate = editing
            field.onUndo = { [weak self, weak field, weak editor] in
                guard let self, let field, let editor else { return false }
                return self.restore(self.history.f_1002f61f0(), field: field, editor: editor)
            }
            field.onRedo = { [weak self, weak field, weak editor] in
                guard let self, let field, let editor else { return false }
                return self.restore(self.history.f_1002f63b8(), field: field, editor: editor)
            }
            editor.didChange = { [weak self, weak field, weak editor] in
                guard let self, let field, let editor, !self.applyingContents,
                      !editor.hasMarkedText(), let storage = editor.textStorage else { return }
                let value = self.contents(storage, text: editor.f_1000f7254())
                if value.nodes != self.currentNodes {
                    self.history.f_1002f5e18(.init(nodes: value.nodes, selection: editor.selectedRange()),
                                             immediate: self.filterCount(value.nodes) != self.filterCount(self.currentNodes))
                }
                self.publish(value)
                self.updateSuggestions(field, editor: editor)
            }
        }
    }

    final class SearchTextView: OriginalSearchTextView {
        var didChange: (() -> Void)?

        override func didChangeText() {
            super.didChangeText()
            didChange?()
        }
    }
}
