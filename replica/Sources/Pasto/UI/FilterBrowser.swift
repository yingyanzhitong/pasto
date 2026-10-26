import AppKit
import SwiftUI
import PastoCore

extension ReplicaSearchFilterChip.Selection {
    var queryNode: OriginalSearchQueryNode {
        let value: String
        switch self {
        case let .kind(kind):
            switch kind {
            case .text, .richText: value = "Text"
            case .link: value = "Link"
            case .image: value = "Image"
            case .files: value = "File"
            case .color: value = "Color"
            case .unknown: value = "Unknown"
            }
        case let .source(source): value = source
        case let .device(device): value = device
        case let .date(filter): return OriginalSearchDateEncoding.f_1002d9d2c(filter.range)
        case let .pinboard(id): value = id.uuidString
        }
        return .filter(group, value)
    }

    var group: UInt8 {
        switch self {
        case .source: return 0
        case .kind: return 1
        case .date: return 3
        case .device: return 4
        case .pinboard: return 5
        }
    }
}

@MainActor
enum ReplicaFilterMatching {
    static func chip(_ selection: ReplicaSearchFilterChip.Selection, store: ClipboardStore) -> ReplicaSearchFilterChip {
        let title: String
        var image: NSImage?
        var value = ""
        switch selection {
        case let .kind(kind):
            title = kind.displayName
            value = kind == .files ? "file" : kind == .richText ? "text" : kind.rawValue
        case let .source(source):
            let item = store.items.first { $0.sourceName == source }
            title = item?.sourceName ?? source
            image = item?.sourceBundleID.flatMap { NSWorkspace.shared.urlForApplication(withBundleIdentifier: $0) }
                .map { NSWorkspace.shared.icon(forFile: $0.path) }
        case let .device(device): title = device
        case let .date(filter): title = OriginalSearchDateEncoding.title(for: filter.range)
        case let .pinboard(id): title = store.pinboards.first { $0.id == id }?.name ?? "Pinboard"
        }
        if image == nil {
            image = OriginalSearchFilterSymbols.f_100054b2c(kind: selection.group, value: value)
                .flatMap { OriginalSystemImageFunctions.f_1000f653c($0) }
        }
        return ReplicaSearchFilterChip(selection: selection, title: title, image: image)
    }
}

@MainActor
private struct ReplicaFilterBrowser: View {
    struct Section: Identifiable {
        let id: UInt8
        let title: String
        let choices: [ReplicaSearchFilterChip.Selection]
    }
    struct Entry: Identifiable {
        let id: String
        let selection: ReplicaSearchFilterChip.Selection?
        let section: UInt8
    }
    @ObservedObject var state: ReplicaUIState
    let sections: [Section]
    let hideApplied: Bool
    let close: () -> Void
    @State private var expanded: Set<UInt8> = []
    @State private var selectedIndex: Int?
    @FocusState private var focused: Bool
    private let columns = Array(repeating: GridItem(.flexible(minimum: 10)), count: 3)

    private var visibleSections: [(section: Section, entries: [Entry])] {
        sections.compactMap { section in
            let choices = section.choices.filter { !hideApplied || !state.searchFilters.contains($0) }
            guard !choices.isEmpty else { return nil }
            var entries = (choices.count >= 11 && !expanded.contains(section.id) ? Array(choices.prefix(8)) : choices)
                .map { Entry(id: String(describing: $0), selection: $0, section: section.id) }
            if choices.count >= 11 { entries.append(Entry(id: "more-\(section.id)", selection: nil, section: section.id)) }
            return (section, entries)
        }
    }

    private var allEntries: [Entry] { visibleSections.flatMap(\.entries) }

    var body: some View {
        ScrollViewReader { reader in
            ScrollView(.vertical) {
                VStack(alignment: .leading, spacing: 0) {
                    ForEach(visibleSections, id: \.section.id) { group in
                        Text(group.section.title).font(.callout.bold()).foregroundStyle(.secondary)
                            .padding(.vertical, 10)
                        LazyVGrid(columns: columns, alignment: .center, spacing: 8) {
                            ForEach(group.entries) { entry in
                                entryView(entry).id(entry.id)
                            }
                        }.padding(.bottom, 8)
                    }
                }.padding(.horizontal, 10)
            }
            .contentMargins(.vertical, 10, for: .scrollIndicators)
            .onChange(of: selectedIndex) { _, index in
                if let index, allEntries.indices.contains(index) { reader.scrollTo(allEntries[index].id) }
            }
        }
        .frame(width: 440).frame(minHeight: 230, maxHeight: 330)
        .focusable().focusEffectDisabled().focused($focused)
        .onAppear { focused = true }
        .onMoveCommand { move($0) }
        .onExitCommand { close() }
        .onKeyPress(.return) {
            if let index = selectedIndex, allEntries.indices.contains(index) { activate(allEntries[index]) }
            return .handled
        }
        .onKeyPress(.tab) {
            move(NSEvent.modifierFlags.intersection([.shift, .option]).isEmpty ? .right : .left)
            return .handled
        }
        .onKeyPress("f", phases: .down) { press in
            guard press.modifiers == .command else { return .ignored }
            close()
            return .handled
        }
    }

    @ViewBuilder private func entryView(_ entry: Entry) -> some View {
        let highlighted = selectedIndex.flatMap { allEntries.indices.contains($0) ? allEntries[$0].id : nil } == entry.id
        Group {
            if let selection = entry.selection {
                let chip = ReplicaFilterMatching.chip(selection, store: state.store)
                FilterView(chip: chip, applied: state.searchFilters.contains(selection)) { activate(entry) }
            } else {
                Button { activate(entry) } label: {
                    HStack(spacing: 8) {
                        Image(systemName: expanded.contains(entry.section) ? "chevron.up" : "chevron.down")
                            .resizable().scaledToFit().frame(width: 12, height: 12)
                        Text(OriginalSearchLocalization.text(expanded.contains(entry.section) ? "general.less" : "general.more"))
                            .font(.body).lineLimit(1)
                    }.padding(.horizontal, 10).padding(.vertical, 6)
                        .frame(maxWidth: .infinity, alignment: .leading).frame(height: 28)
                }.buttonStyle(.plain)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading).frame(height: 28)
        .overlay {
            if highlighted {
                Capsule(style: .continuous).strokeBorder(Color.accentColor, lineWidth: 2).padding(-4)
            }
        }
    }

    private func activate(_ entry: Entry) {
        guard let selection = entry.selection else {
            if expanded.contains(entry.section) { expanded.remove(entry.section) }
            else { expanded.insert(entry.section) }
            selectedIndex = nil
            return
        }
        if let index = state.searchFilters.firstIndex(of: selection) { state.searchFilters.remove(at: index) }
        else { state.searchFilters.append(selection) }
        state.normalizeSelection()
        if !NSEvent.modifierFlags.contains(.command) { close() }
    }

    private func move(_ direction: MoveCommandDirection) {
        let counts = visibleSections.map { $0.entries.count }
        let total = counts.reduce(0, +)
        guard total > 0 else { selectedIndex = nil; return }
        guard let selectedIndex else { self.selectedIndex = 0; return }
        let current = min(selectedIndex, total - 1)
        switch direction {
        case .left: self.selectedIndex = (current - 1 + total) % total
        case .right: self.selectedIndex = (current + 1) % total
        case .up, .down:
            var offset = 0
            for (section, count) in counts.enumerated() {
                defer { offset += count }
                guard current < offset + count else { continue }
                let local = current - offset
                let column = local % 3
                if direction == .up {
                    if local >= 3 { self.selectedIndex = current - 3 }
                    else if section == 0 { self.selectedIndex = total - 1 }
                    else {
                        let previousCount = counts[section - 1]
                        self.selectedIndex = offset - previousCount + ((previousCount - 1) / 3) * 3
                            + min(column, (previousCount - 1) % 3)
                    }
                } else if local / 3 < (count - 1) / 3 {
                    self.selectedIndex = min(current + 3, offset + count - 1)
                } else if section + 1 < counts.count {
                    self.selectedIndex = offset + count + min(column, counts[section + 1] - 1)
                } else { self.selectedIndex = 0 }
                return
            }
        @unknown default: break
        }
    }

    private struct FilterView: View {
        let chip: ReplicaSearchFilterChip
        let applied: Bool
        let action: () -> Void
        var body: some View {
            Button(action: action) {
                HStack(spacing: 4) {
                    if let image = chip.image {
                        if chip.selection.group == 5 {
                            Image(nsImage: image).frame(width: 16, height: 16)
                        } else {
                            Image(nsImage: image).resizable().scaledToFit().frame(width: 16, height: 16)
                        }
                    }
                    Text(chip.title).font(.body).lineLimit(1)
                    Spacer(minLength: 0)
                }
                .padding(.horizontal, 10).padding(.vertical, 6)
                .frame(height: 28, alignment: .leading)
            }.buttonStyle(FilterButtonStyle(applied: applied))
        }
    }

    private struct FilterButtonStyle: ButtonStyle {
        let applied: Bool
        func makeBody(configuration: Configuration) -> some View {
            configuration.label
                .foregroundStyle(applied ? Color.white : Color(nsColor: .labelColor))
                .background(Capsule(style: .continuous).fill(applied ? Color.accentColor
                    : Color(nsColor: OriginalToolbarAppearance.borderAndHover())))
                .overlay(Capsule(style: .continuous).fill(Color.black.opacity(configuration.isPressed ? 0.1 : 0)))
        }
    }
}

extension ReplicaUIController {
    func handleSearchCommand() {
        func findField(_ view: NSView) -> OriginalSearchField? {
            if let field = view as? OriginalSearchField { return field }
            return view.subviews.lazy.compactMap { findField($0) }.first
        }
        guard state.searchVisible, let content = panel.contentView, let field = findField(content) else {
            focusSearch()
            return
        }
        let editor = field.f_100045c2c().f_100041f9c()
        if panel.firstResponder === editor { showFilterBrowser(relativeTo: field.f_100045730()) }
        else { panel.makeFirstResponder(editor) }
    }

    func showFilterBrowser(relativeTo button: NSButton) {
        if let filterBrowserPopover, filterBrowserPopover.isDisplayed { filterBrowserPopover.close(); return }
        let popover = OriginalFilterBrowserPopover()
        let field = button.superview as? OriginalSearchField
        popover.onWillClose = { [weak self, weak field] in
            self?.filterBrowserPopover = nil
            if self?.state.searchVisible == true, let field {
                field.window?.makeFirstResponder(field.f_100045c2c().f_100041f9c())
            }
            field?.f_1000457cc()
        }
        let sources = Set(store.items.map(\.sourceName)).filter { !$0.isEmpty }
            .sorted { $0.compare($1) == .orderedAscending }
        let devices = Set(store.items.map(\.sourceDevice)).sorted()
        let sections: [ReplicaFilterBrowser.Section] = [
            .init(id: 1, title: OriginalSearchLocalization.text("search.filters.section.type"),
                  choices: [ClipboardKind.text, .link, .image, .files, .color, .unknown].map { .kind($0) }),
            .init(id: 0, title: OriginalSearchLocalization.text("search.filters.section.app"), choices: sources.map { .source($0) }),
            .init(id: 5, title: OriginalSearchLocalization.text("search.filters.section.pinboard"),
                  choices: store.pinboards.sorted { $0.sortOrder < $1.sortOrder }.map { .pinboard($0.id) }),
            .init(id: 3, title: OriginalSearchLocalization.text("search.filters.section.date"), choices: OriginalSearchDateRanges.f_1002d8ce0().map { .date($0) }),
            .init(id: 4, title: OriginalSearchLocalization.text("search.filters.section.device"), choices: devices.map { .device($0) })
        ]
        let content = ReplicaFilterBrowser(state: state, sections: sections,
            hideApplied: NSEvent.modifierFlags.contains(.option), close: { [weak popover] in popover?.close() })
        let controller = NSHostingController(rootView: content)
        controller.sizingOptions = [.preferredContentSize]
        filterBrowserPopover = popover
        popover.present(controller, relativeTo: button)
        field?.f_1000457cc()
    }
}
