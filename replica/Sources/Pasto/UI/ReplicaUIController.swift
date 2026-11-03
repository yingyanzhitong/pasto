import AppKit
import Combine
import CryptoKit
import QuartzCore
import SwiftUI
import UniformTypeIdentifiers
import PastoCore

@MainActor
final class ReplicaUIState: ObservableObject {
    struct PendingListFocus {
        let itemID: UUID
        let pinboardID: UUID?
        let horizontalOffset: CGFloat?
    }

    var pendingListFocus: PendingListFocus?

    struct ItemDeletionRequest {
        let ids: Set<UUID>
        let orderedIDs: [UUID]
        let contextPinboardID: UUID?
        let permanently: Bool
        let beforeIDs: [UUID]
        let neighborID: UUID?
    }

    struct PendingNeighborSelection {
        let token: UUID
        let id: UUID
        let beforeIDs: [UUID]
    }

    struct CollectionSelectionSnapshot: Equatable {
        let orderedIDs: [UUID]
        let anchorID: UUID?
        let primaryID: UUID?
        let allowsEmptySelection: Bool
    }

    let store: ClipboardStore
    let cloudSync: ICloudDriveSyncController
    let originalCloudSync: CloudKitSyncController
    weak var controller: ReplicaUIController?
    weak var collectionOwner: ReplicaNativeCollectionHost?
    weak var toolbarOwner: OriginalPanelToolbarView?
    weak var listAttributesSource: ClipboardListAttributesObservation?
    var monitoringPauseChanged: (() -> Void)?
    @Published var query = "" { didSet {
        if oldValue != query { cancelItemDeletion() }
        if !isApplyingSearchInput { searchInputProjection = nil; searchInputChanged() }
    } }
    @Published var searchFilters: [ReplicaSearchFilterChip.Selection] = [] { didSet {
        if oldValue != searchFilters { cancelItemDeletion() }
        if !isApplyingSearchInput { searchInputProjection = nil; searchInputChanged() }
    } }
    @Published var pinboardID: UUID? { didSet {
        if oldValue != pinboardID { cancelItemDeletion() }
    } }
    @Published var pendingPinboardDeletion: ClipboardListTarget?
    @Published var pinboardDeletionError: String?
    @Published var pendingItemDeletion: ItemDeletionRequest?
    @Published var pendingNeighborSelection: PendingNeighborSelection?
    @Published var itemDeletionError: String?
    let beginEditingListSubject = PassthroughSubject<ClipboardListTarget, Never>()
    @Published var showDeleted = false { didSet {
        if oldValue != showDeleted { cancelItemDeletion() }
    } }
    @Published var isMigratingPasteGroups = false
    @Published var selection: Set<UUID> = [] {
        didSet { if !isApplyingSelection { reconcileExternalSelection() } }
    }
    @Published var primaryID: UUID?
    @Published var searchFocus = UUID()
    @Published var searchVisible = false
    private var stackRestoreInputs: [UUID: ClipboardRestoreItem] = [:]
    @Published var stackIDs: [UUID] = [] {
        didSet {
            let retainedIDs = Set(stackIDs)
            stackRestoreInputs = stackRestoreInputs.filter { retainedIDs.contains($0.key) }
            guard oldValue != stackIDs else { return }
            controller?.stackContentsChanged()
        }
    }
    @Published var hotKeyStatusMessage = ""
    @Published var allowsEmptySelection = false
    private var observation: AnyCancellable?
    private let searchService: ReplicaSpotlightService
    private let searchIndex: ReplicaSearchIndex
    private let searchQueryChanges = CurrentValueSubject<[OriginalSearchQueryNode], Never>([])
    private var searchQueryObservation: AnyCancellable?
    private let listIdentifierChanges = CurrentValueSubject<String?, Never>(ClipboardStore.historyListIdentifier)
    private var listIdentifierObservation: AnyCancellable?
    private var collectionQueryObservation: AnyCancellable?
    private var collectionItemObservation: AnyCancellable?
    private var collectionSourceObservation: AnyCancellable?
    private var listCollection: ClipboardSearchCollection?
    private lazy var pinboardMenuCollection = store.makePinboardCollection()
    private lazy var tabListCollection = store.makeTabListCollection()
    private var tabListObservation: AnyCancellable?
    private var tabListSnapshot: ClipboardPinboardCollection.ListSnapshot?
    @Published private(set) var selectedTabList: ClipboardListTarget?
    var tabListPublisher: AnyPublisher<ClipboardPinboardCollection.ListSnapshot, Never> { tabListCollection.listPublisher }
    private var selectedTabIndex: Int?
    private var selectedCollectionIdentifier = ClipboardStore.historyListIdentifier
    var selectedListIdentifier: String { selectedTabList?.identifier ?? ClipboardStore.historyListIdentifier }
    private var listCollectionObservation: AnyCancellable?
    private var pendingCollectionChangedIDs: Set<UUID> = []
    private var indexedSearchQueryNodes: [OriginalSearchQueryNode] = []
    private var collectionSearchQueryNodes: [OriginalSearchQueryNode] = []
    let itemDragSessionID = UUID()
    private var searchInputProjection: [OriginalSearchQueryNode]?
    private var isApplyingSearchInput = false
    private(set) var orderedSelectionIDs: [UUID] = []
    private var rangeAnchorID: UUID?
    private var isApplyingSelection = false

    init(store: ClipboardStore) {
        self.store = store
        cloudSync = ICloudDriveSyncController(store: store)
        originalCloudSync = CloudKitSyncController(store: store, drive: cloudSync)
        let service = ReplicaSpotlightService(directoryURL: store.directoryURL)
        searchService = service
        searchIndex = ReplicaSearchIndex(service: service, store: store)
        searchIndex.setSuggestionDataSource(store.makeSearchSuggestionProvider())
        OriginalSearchSuggestions.setListNameResolver(store.makeSearchListNameResolver())
        searchIndex.onUpdate = { [weak self] in
            self?.objectWillChange.send()
            self?.normalizeSelection()
        }
        searchIndex.onCollectionUpdate = { [weak self] identifiers in
            guard let self, !self.isCollectionSearchQueryEmpty else { return }
            self.pendingCollectionChangedIDs.formUnion(identifiers)
            self.objectWillChange.send()
        }
        installTabListDelivery()
        installListSelectionDelivery()
        installSearchQueryDelivery()
        refreshSearch()
        collectionItemObservation = store.collectionItemUpdates.sink { [weak self] identifiers in
            guard let self, self.collectionOwner != nil else { return }
            self.pendingCollectionChangedIDs.formUnion(identifiers)
            self.objectWillChange.send()
        }
        observation = store.objectWillChange.sink { [weak self] _ in
            self?.objectWillChange.send()
        }
        // Legacy value/registry adapters still refresh payload snapshots and selection.
        // Managed list membership/order now arrives through its retained FRC source.
        collectionSourceObservation = store.$items
            .combineLatest(store.$sourceApplications, store.$pinboards.map { Set($0.map(\.id)) })
            .removeDuplicates { lhs, rhs in lhs.0 == rhs.0 && lhs.1 == rhs.1 && lhs.2 == rhs.2 }
            .dropFirst()
            .sink { [weak self] _ in
                DispatchQueue.main.async { [weak self] in
                    self?.refreshSearch()
                    self?.normalizeSelection()
                }
            }
    }

    func listAttributes(for pinboard: Pinboard) -> OriginalPinboardAttributes.Value? {
        if let source = listAttributesSource, source.identifier == pinboard.id.uuidString { return source.value }
        return OriginalPinboardAttributes.decoded(from: pinboard.rawAttributes)
    }

    var searchQueryNodes: [OriginalSearchQueryNode] {
        if let searchInputProjection { return searchInputProjection }
        var buffer = query
        var nodes: [OriginalSearchQueryNode] = []
        OriginalSearchTextTokens.f_1002f8760(&buffer, into: &nodes)
        nodes += searchFilters.map(\.queryNode)
        return OriginalSearchQueryNormalization.f_1002da16c(nodes, flag: 0)
    }

    func applySearchInput(nodes: [OriginalSearchQueryNode], text: String,
                          filters: [ReplicaSearchFilterChip.Selection]) {
        cancelItemDeletion()
        isApplyingSearchInput = true
        query = text
        searchFilters = filters
        searchInputProjection = nodes
        isApplyingSearchInput = false
        searchInputChanged()
    }

    // The original query Published emits even when reset publishes [] twice.
    // Keep both deliveries on the actual query subject without writing equal
    // SwiftUI fields again during native toolbar configuration.
    func publishSearchInputFromEditor(nodes: [OriginalSearchQueryNode], text: String,
                                      filters: [ReplicaSearchFilterChip.Selection]) {
        if query == text, searchFilters == filters, searchQueryNodes == nodes {
            searchInputChanged()
        } else {
            applySearchInput(nodes: nodes, text: text, filters: filters)
        }
    }

    var isSearchQueryEmpty: Bool { OriginalSearchQuery.f_1002ddcf0(searchQueryNodes) }
    var searchInputPublisher: AnyPublisher<[OriginalSearchQueryNode], Never> { searchQueryChanges.eraseToAnyPublisher() }
    var isCollectionSearchQueryEmpty: Bool { OriginalSearchQuery.f_1002ddcf0(collectionSearchQueryNodes) }
    var hasPendingDeletion: Bool { pendingPinboardDeletion != nil || pendingItemDeletion != nil }

    private func searchInputChanged() {
        searchQueryChanges.send(searchQueryNodes)
    }

    private func installSearchQueryDelivery() {
        // 0x10007e194: query delivery and collection routing have separate subscriptions.
        searchQueryObservation = searchQueryChanges
            .debounce(for: .milliseconds(120), scheduler: RunLoop.main)
            .removeDuplicates()
            .sink { [weak self] nodes in
                guard let self else { return }
                self.indexedSearchQueryNodes = nodes
                self.refreshSearch()
            }
        // 0x10007daa8: only the collection route prepends an immediate empty query.
        collectionQueryObservation = searchQueryChanges
            .debounce(for: .milliseconds(120), scheduler: RunLoop.main)
            .prepend([OriginalSearchQueryNode]())
            .removeDuplicates()
            .sink { [weak self] nodes in
                guard let self else { return }
                self.controller?.cancelPendingDeletion()
                self.objectWillChange.send()
                self.collectionSearchQueryNodes = nodes
                self.installListCollectionSource()
                self.normalizeSelection()
                self.collectionOwner?.replaceCollectionModel(state: self)
            }
    }

    private func installListCollectionSource() {
        listCollectionObservation = nil
        listCollection = nil
        guard isCollectionSearchQueryEmpty else { return }
        let source = store.makeListCollection(identifier: selectedCollectionIdentifier)
        listCollection = source
        listCollectionObservation = source?.publisher.dropFirst().sink { [weak self] snapshot in
            guard let self, self.isCollectionSearchQueryEmpty, !self.showDeleted else { return }
            self.pendingCollectionChangedIDs.formUnion(snapshot.updatedIdentifiers)
            self.objectWillChange.send()
        }
    }

    private func refreshSearch() {
        searchIndex.update(items: store.items, nodes: indexedSearchQueryNodes)
    }

    func searchSuggestions(for context: OriginalSearchInputContext.Context) -> [OriginalSearchQueryNode] {
        searchIndex.suggestions(contextNode: context.nodes[context.nodeIndex], currentNodes: context.nodes)
    }

    func availableSearchFilters() -> [UInt8: [OriginalSearchQueryNode]] {
        searchIndex.availableFilters()
    }

    var searchFailed: Bool { !isCollectionSearchQueryEmpty && searchIndex.error != nil }
    func retrySearch() { searchIndex.retry() }

    var collectionItemReferences: [UUID: ClipboardCollectionItemReference] {
        guard !showDeleted else { return [:] }
        return isCollectionSearchQueryEmpty ? (listCollection?.value.itemReferences ?? [:]) : searchIndex.resultItemReferences
    }

    var visibleItems: [ClipboardCollectionEntry] {
        if isCollectionSearchQueryEmpty {
            if showDeleted {
                return store.search(query: "", pinboardID: pinboardID, includeDeleted: true)
                    .filter(\.isDeleted).map { ClipboardCollectionEntry(item: $0) }
            }
            let snapshot = listCollection?.value
            let native = collectionEntries(identifiers: snapshot?.identifiers ?? [],
                references: snapshot?.itemReferences ?? [:])
            if let pinboardID {
                // Preserve old local archives with secondary memberships outside the native single owner.
                let archived = store.items(in: pinboardID)
                let legacy = archived.filter { $0.pinboardOwnerID != pinboardID }
                if !legacy.isEmpty {
                    let byID = Dictionary(uniqueKeysWithValues: native.map { ($0.id, $0) })
                    let retained = Set(native.map(\.id)).union(legacy.map(\.id))
                    let merged = archived.filter { retained.contains($0.id) }.map {
                        byID[$0.id] ?? ClipboardCollectionEntry(item: $0)
                    }
                    let included = Set(merged.map(\.id))
                    return merged + native.filter { !included.contains($0.id) }
                }
            }
            return native
        }
        if showDeleted {
            let archived = Dictionary(uniqueKeysWithValues: store.items.map { ($0.id, $0) })
            return searchIndex.orderedIdentifiers.compactMap { identifier in
                guard let item = archived[identifier], item.isDeleted else { return nil }
                return ClipboardCollectionEntry(item: item)
            }
        }
        return collectionEntries(identifiers: searchIndex.orderedIdentifiers,
            references: searchIndex.resultItemReferences)
    }
    private func collectionEntries(identifiers: [UUID], references: [UUID: ClipboardCollectionItemReference]) -> [ClipboardCollectionEntry] {
        // Imported legacy trash is a local compatibility case; cached payload availability is not membership.
        let deleted = Set(store.items.filter(\.isDeleted).map(\.id))
        return identifiers.filter { !deleted.contains($0) }.map { identifier in
            guard let reference = references[identifier] else { fatalError("Missing collection item reference") }
            return ClipboardCollectionEntry(id: identifier, reference: reference)
        }
    }

    var selectedItems: [ClipboardItem] {
        let ids = orderedSelectionIDs.filter { selection.contains($0) }
        if let collectionOwner { return collectionOwner.appliedSelectedItems(for: self, orderedIDs: ids) ?? [] }
        let byID = Dictionary(uniqueKeysWithValues: visibleItems.map { ($0.id, $0) })
        return ids.compactMap { byID[$0]?.item() }
    }
    var primaryItem: ClipboardItem? {
        let items = pointerSelectionItems
        return items.first { $0.id == primaryID }?.requiredItem()
            ?? selectedItems.first ?? items.first?.requiredItem()
    }
    var stackItemIDs: [UUID] { stackIDs.filter { hasStackItem($0) } }

    var stackItems: [ClipboardItem] {
        stackIDs.compactMap { stackItem(for: $0) }
    }

    var stackSnippetInputs: [ClipboardRestoreItem] {
        stackIDs.compactMap { id in
            if let input = stackRestoreInputs[id] { return input }
            return store.items.first { $0.id == id && !$0.isDeleted }
                .map { ClipboardRestoreItem(item: $0) }
        }
    }

    func hasStackItem(_ id: UUID) -> Bool {
        stackRestoreInputs[id] != nil || store.items.contains { $0.id == id && !$0.isDeleted }
    }

    func stackItem(for id: UUID) -> ClipboardItem? {
        if let input = stackRestoreInputs[id] { return input.resolvedItem() }
        // UUID queues saved by older versions retain their existing value adapter.
        return store.items.first { $0.id == id && !$0.isDeleted }
    }

    func stackRestoreItem(for id: UUID) -> ClipboardRestoreItem? {
        stackRestoreInputs[id]
    }
    var preferredScheme: ColorScheme? {
        switch store.preferences.appearance {
        case "light": return .light
        case "dark": return .dark
        default: return nil
        }
    }

    private func applyOrderedSelection(_ ids: [UUID], anchor: UUID?, primary: UUID?) {
        isApplyingSelection = true
        orderedSelectionIDs = ids
        rangeAnchorID = anchor
        selection = Set(ids)
        primaryID = primary
        isApplyingSelection = false
        collectionOwner?.applySelection(state: self)
    }

    func takeCollectionChangedIDs(owner: ReplicaNativeCollectionHost) -> Set<UUID> {
        guard collectionOwner === owner else { return [] }
        let identifiers = pendingCollectionChangedIDs
        pendingCollectionChangedIDs.removeAll()
        return identifiers
    }

    // 0x100228c78 receives an index in the applied collection, without moving first responder.
    func selectFirstAppliedItem(items: [ClipboardCollectionEntry]) {
        selectIndex(0, mode: 0, items: items)
    }

    func selectAppliedItem(at index: Int, items: [ClipboardCollectionEntry]) {
        selectIndex(index, mode: 0, items: items)
    }

    func collectionSelectionSnapshot() -> CollectionSelectionSnapshot {
        CollectionSelectionSnapshot(orderedIDs: orderedSelectionIDs, anchorID: rangeAnchorID,
                                    primaryID: primaryID, allowsEmptySelection: allowsEmptySelection)
    }

    func applyFullCollectionReload(items: [ClipboardCollectionEntry]) {
        let firstID = items.first?.id
        allowsEmptySelection = false
        applyOrderedSelection(firstID.map { [$0] } ?? [], anchor: firstID, primary: firstID)
    }

    // 0x1002234e0: preserve the surviving selection order, including an empty
    // selection, and use its last endpoint after the new collection is applied.
    func applyIncrementalCollectionSnapshot(items: [ClipboardCollectionEntry]) {
        let visible = Set(items.map(\.id))
        let ids = orderedSelectionIDs.filter { selection.contains($0) && visible.contains($0) }
        allowsEmptySelection = ids.isEmpty
        applyOrderedSelection(ids, anchor: ids.last, primary: ids.last)
    }

    private func reconcileExternalSelection() {
        let visibleIDs = visibleItems.map(\.id)
        let visible = Set(visibleIDs)
        orderedSelectionIDs = orderedSelectionIDs.filter { selection.contains($0) && visible.contains($0) }
        let retained = Set(orderedSelectionIDs)
        orderedSelectionIDs += visibleIDs.filter { selection.contains($0) && !retained.contains($0) }
        if rangeAnchorID.map({ !selection.contains($0) || !visible.contains($0) }) ?? true {
            rangeAnchorID = orderedSelectionIDs.last
        }
        if primaryID.map({ !selection.contains($0) || !visible.contains($0) }) ?? true {
            isApplyingSelection = true
            primaryID = orderedSelectionIDs.last
            isApplyingSelection = false
        }
        collectionOwner?.applySelection(state: self)
    }

    func normalizeSelection() {
        if pendingPinboardDeletion?.isDeleted == true {
            pendingPinboardDeletion = nil
            pinboardDeletionError = nil
        }
        // Native List delivery owns removal and neighboring-list selection.
        if let request = pendingItemDeletion,
           !request.ids.isSubset(of: Set(visibleItems.map(\.id))) {
            cancelItemDeletion()
        }
        // A live collection updates selection with its applied snapshot. Search
        // and store projections may already describe a later, queued snapshot.
        guard collectionOwner == nil else { return }
        normalizeProjectedSelection()
    }

    private func normalizeProjectedSelection() {
        let items = visibleItems
        let visible = Set(items.map(\.id))
        let hadSelectionBeforeSnapshot = !orderedSelectionIDs.isEmpty
        var ids = orderedSelectionIDs.filter { selection.contains($0) && visible.contains($0) }
        let retained = Set(ids)
        ids += items.map(\.id).filter { selection.contains($0) && !retained.contains($0) }
        if ids.isEmpty, hadSelectionBeforeSnapshot { allowsEmptySelection = true }
        if ids.isEmpty, !allowsEmptySelection, let first = items.first { ids = [first.id] }
        let anchor = rangeAnchorID.flatMap { visible.contains($0) ? $0 : nil } ?? ids.last
        let primary = primaryID.flatMap { ids.contains($0) ? $0 : nil } ?? ids.last
        applyOrderedSelection(ids, anchor: anchor, primary: primary)
    }

    private func selectIndex(_ index: Int, mode: UInt8, items: [ClipboardCollectionEntry], animated: Bool = true) {
        cancelPendingNeighborSelection()
        if items.indices.contains(index), orderedSelectionIDs == [items[index].id] { return }
        let positions = Dictionary(uniqueKeysWithValues: items.enumerated().map { ($0.element.id, $0.offset) })
        var value = OriginalOrderedSelection(selectedIndexes: orderedSelectionIDs.compactMap { positions[$0] },
            itemCount: items.count, anchor: rangeAnchorID.flatMap { positions[$0] })
        value.select(index, mode: mode)
        let ids = value.selectedIndexes.map { items[$0].id }
        if !ids.isEmpty { allowsEmptySelection = false }
        applyOrderedSelection(ids, anchor: value.anchor.map { items[$0].id }, primary: ids.last)
        if let endpointID = ids.last {
            controller?.revealSelection(endpointID: endpointID, requestedIndex: index, animated: animated)
        }
    }

    private var pointerSelectionItems: [ClipboardCollectionEntry] {
        guard let collectionOwner else { return visibleItems }
        return collectionOwner.appliedItems(for: self) ?? []
    }

    // f228a50's double-click path sets the singleton directly, without a reveal/delegate callback.
    func selectForDoubleClick(at index: Int) {
        cancelPendingNeighborSelection()
        let items = pointerSelectionItems
        guard items.indices.contains(index) else { return }
        let id = items[index].id
        allowsEmptySelection = false
        applyOrderedSelection([id], anchor: id, primary: id)
    }

    func select(_ item: ClipboardItem, modifiers: NSEvent.ModifierFlags = []) {
        cancelPendingNeighborSelection()
        controller?.clearPanelFirstResponder()
        let items = pointerSelectionItems
        guard let index = items.firstIndex(where: { $0.id == item.id }) else { return }
        selectIndex(index, mode: OriginalOrderedSelection.mode(modifierFlags: modifiers.rawValue), items: items)
    }

    // f2287ec keeps the captured numeric index and does not move first responder.
    func selectAfterPressDelay(at index: Int) {
        selectIndex(index, mode: 0, items: pointerSelectionItems)
    }

    // f228128 preserves an existing multi-selection and does not change first responder.
    func selectForContextMenu(_ item: ClipboardItem) {
        cancelPendingNeighborSelection()
        let items = pointerSelectionItems
        guard let index = items.firstIndex(where: { $0.id == item.id }),
              !selection.contains(item.id) else { return }
        selectIndex(index, mode: 0, items: items)
    }

    func moveSelection(_ offset: Int, extending: Bool = false) {
        guard let items = collectionOwner?.appliedItems(for: self) else { return }
        guard !items.isEmpty else { return }
        guard let endpoint = orderedSelectionIDs.last,
              let current = items.firstIndex(where: { $0.id == endpoint }) else { return }
        let next = current + offset
        selectIndex(next, mode: extending ? 2 : 0, items: items)
    }

    func moveSelectionToBoundary(last: Bool, extending: Bool = false) {
        guard let items = collectionOwner?.appliedItems(for: self) else { return }
        guard !items.isEmpty else { return }
        selectIndex(last ? items.count - 1 : 0, mode: extending ? 2 : 0, items: items, animated: false)
    }

    private func installTabListDelivery() {
        let snapshot = tabListCollection.listSnapshot
        tabListSnapshot = snapshot
        reconcileTabListSelection()
        tabListObservation = tabListCollection.listPublisher.dropFirst().sink { [weak self] snapshot in
            MainActor.assumeIsolated {
                guard let self else { return }
                self.tabListSnapshot = snapshot
                self.reconcileTabListSelection()
            }
        }
    }

    // 03a538: retain an existing object ID, otherwise clamp the old index into the raw native order.
    private func reconcileTabListSelection() {
        guard let selected = selectedTabList, let previousIndex = selectedTabIndex else {
            selectListIdentifier(ClipboardStore.historyListIdentifier, force: false)
            return
        }
        guard let snapshot = tabListSnapshot else { return }
        if let index = snapshot.index(of: selected) {
            selectedTabIndex = index
            return
        }
        let index = min(previousIndex, snapshot.count - 1)
        guard let target = snapshot.target(at: index) else { return }
        selectListIdentifier(target.identifier, force: false)
    }

    func chooseList(identifier: String) { selectListIdentifier(identifier, force: true) }

    func chooseBoard(_ id: UUID?) {
        selectListIdentifier(id?.uuidString ?? ClipboardStore.historyListIdentifier, force: true)
    }

    // 0x100039c50: same nonnil identifier + force emits nil, then always the target.
    // Nil is an identifier event, not the history list (whose identifier is nonnil).
    private func selectListIdentifier(_ identifier: String, force: Bool) {
        if let current = listIdentifierChanges.value, current == identifier, force {
            listIdentifierChanges.send(nil)
        }
        listIdentifierChanges.send(identifier)
    }

    // 03a900/03a9fc ignore nil or unresolved identifiers before publishing a list.
    // A successful resolution still publishes the same list; no removeDuplicates.
    private func installListSelectionDelivery() {
        listIdentifierObservation = listIdentifierChanges.sink { [weak self] identifier in
            guard let self, let identifier,
                  let target = self.store.tabListTarget(identifier: identifier) else { return }
            let context = OriginalCollectionListContext.f_1003b80f0(identifier: target.identifier,
                rawType: target.rawType, historyIdentifier: { ClipboardStore.historyListIdentifier })
            let id: UUID?
            switch context {
            case .pinboard(let identifier):
                self.selectedCollectionIdentifier = identifier
                id = UUID(uuidString: identifier)
            case .history(let identifier):
                self.selectedCollectionIdentifier = identifier
                id = nil
            }
            self.selectedTabList = target
            self.applySelectedList(id)
            self.selectedTabIndex = self.tabListSnapshot?.index(of: target)
        }
    }

    private func applySelectedList(_ id: UUID?) {
        controller?.cancelPendingDeletion()
        cancelItemDeletion()
        allowsEmptySelection = false
        pinboardID = id
        showDeleted = false
        selection = []
        primaryID = nil
        installListCollectionSource()
        normalizeProjectedSelection()
        collectionOwner?.replaceCollectionModel(state: self)
    }

    // f3b83c4: one resolved item, history first, then its owning pinboard; omit the current list.
    func selectedItemTargetLists() -> [UUID?] {
        let ids = orderedSelectionIDs.filter { selection.contains($0) }
        let inputs: [ClipboardRestoreItem]
        if let collectionOwner {
            inputs = collectionOwner.appliedRestoreItems(for: self, orderedIDs: ids) ?? []
        } else {
            let byID = Dictionary(uniqueKeysWithValues: visibleItems.map { ($0.id, $0) })
            inputs = ids.compactMap { byID[$0]?.restoreItem() }
        }
        guard inputs.count == 1 else { return [] }
        let input = inputs[0]
        let isSearching = !isCollectionSearchQueryEmpty
        var lists: [UUID?] = []
        if let membership = input.listNavigationMembership() {
            if membership.isInHistory, isSearching || pinboardID != nil { lists.append(nil) }
            if let ownerID = membership.pinboardID, isSearching || ownerID != pinboardID {
                lists.append(ownerID)
            }
            return lists
        }
        let item = input.resolvedItem()
        if item.isInHistory, isSearching || pinboardID != nil { lists.append(nil) }
        if let owner = store.pinboardOwner(for: item), owner.rawType == 2,
           isSearching || owner.id != pinboardID {
            lists.append(owner.id)
        }
        return lists
    }

    // f07d9c8: the item locator clears the query; ordinary tab selection does not.
    func chooseListForItemReveal(_ id: UUID?) {
        applySearchInput(nodes: [], text: "", filters: [])
        chooseBoard(id)
    }

    // f068b0c: wait for the target context, clear before resolving against its new item provider.
    func consumePendingListFocus(itemIDs: [UUID]) -> (index: Int, horizontalOffset: CGFloat?)? {
        guard let request = pendingListFocus, isCollectionSearchQueryEmpty,
              !showDeleted, pinboardID == request.pinboardID else { return nil }
        pendingListFocus = nil
        guard let index = itemIDs.firstIndex(of: request.itemID) else { return nil }
        allowsEmptySelection = false
        applyOrderedSelection([request.itemID], anchor: request.itemID, primary: request.itemID)
        return (index, request.horizontalOffset)
    }

    func switchBoard(_ offset: Int) {
        guard let snapshot = tabListSnapshot, let selected = selectedTabList,
              let current = snapshot.index(of: selected) else { return }
        let next: Int
        switch offset {
        case -1: next = (current - 1 + snapshot.count) % snapshot.count
        case 1: next = (current + 1) % snapshot.count
        default: return
        }
        guard let target = snapshot.target(at: next) else { return }
        chooseList(identifier: target.identifier)
    }

    func perform(_ action: () throws -> Void) {
        do { try action() }
        catch { controller?.presentError(error) }
    }

    func deleteSelection() {
        guard let before = collectionOwner?.appliedItems(for: self) else { return }
        guard !hasPendingDeletion else { return }
        cancelPendingNeighborSelection()
        // 0x100068db8 resolves selected indexes and their neighbor in the applied
        // collection, before a queued query result replaces that snapshot.
        let visibleIDs = Set(before.map(\.id))
        let orderedIDs = orderedSelectionIDs.filter { selection.contains($0) && visibleIDs.contains($0) }
        let ids = Set(orderedIDs)
        guard !orderedIDs.isEmpty else { return }
        let indexes = before.indices.filter { ids.contains(before[$0].id) }
        var neighborID: UUID?
        if let first = indexes.min(), let last = indexes.max() {
            neighborID = [last + 1, first - 1].first {
                before.indices.contains($0) && !ids.contains(before[$0].id)
            }.map { before[$0].id }
        }
        pendingItemDeletion = ItemDeletionRequest(ids: ids, orderedIDs: orderedIDs, contextPinboardID: pinboardID,
            permanently: showDeleted || !isCollectionSearchQueryEmpty,
            beforeIDs: before.map(\.id), neighborID: neighborID)
        itemDeletionError = nil
        // 0x1003ba5c4: ordinary local single-item deletion skips confirmation;
        // multiple items require it. Shared/network predicates are out of scope.
        if ids.count < 2 { confirmItemDeletion() }
        else { controller?.clearPanelFirstResponder() }
    }

    func cancelItemDeletion() {
        cancelPendingNeighborSelection()
        guard pendingItemDeletion != nil || itemDeletionError != nil else { return }
        pendingItemDeletion = nil
        itemDeletionError = nil
    }

    func cancelPendingNeighborSelection(token: UUID? = nil) {
        guard let request = pendingNeighborSelection,
              token == nil || request.token == token else { return }
        pendingNeighborSelection = nil
    }

    func consumePendingNeighborSelection(token: UUID, items: [ClipboardCollectionEntry]) {
        guard let request = pendingNeighborSelection, request.token == token else { return }
        pendingNeighborSelection = nil
        guard items.map(\.id) != request.beforeIDs,
              let index = items.firstIndex(where: { $0.id == request.id }) else { return }
        selectIndex(index, mode: 0, items: items)
    }

    func confirmItemDeletion() {
        guard let request = pendingItemDeletion else { return }
        executeItemDeletion(request) { [weak self, weak owner = collectionOwner] in
            guard let self, let owner, self.collectionOwner === owner else { return }
            self.completeItemDeletion(request)
        }
    }

    private func executeItemDeletion(_ request: ItemDeletionRequest, completion: (() -> Void)?) {
        itemDeletionError = nil
        do {
            if request.permanently { try store.permanentlyDelete(orderedIDs: request.orderedIDs) }
            else { try store.delete(orderedIDs: request.orderedIDs, currentPinboardID: { [self] in pinboardID }) }
        } catch {
            itemDeletionError = error.localizedDescription
        }
        // 0x1003baac8 releases a transaction error, then invokes the optional completion.
        completion?()
    }

    private func completeItemDeletion(_ request: ItemDeletionRequest) {
        if itemDeletionError == nil {
            cancelItemDeletion()
            let items = visibleItems
            if items.map(\.id) != request.beforeIDs {
                let visible = Set(items.map(\.id))
                let remaining = orderedSelectionIDs.filter { selection.contains($0) && visible.contains($0) }
                if remaining.isEmpty { allowsEmptySelection = true }
                applyOrderedSelection(remaining,
                    anchor: rangeAnchorID.flatMap { visible.contains($0) ? $0 : nil },
                    primary: primaryID.flatMap { remaining.contains($0) ? $0 : nil })
            }
        }
        if let neighborID = request.neighborID {
            pendingNeighborSelection = PendingNeighborSelection(
                token: UUID(), id: neighborID, beforeIDs: request.beforeIDs)
        } else {
            cancelPendingNeighborSelection()
        }
    }

    func assignSelection(to id: UUID?) {
        let ids = selection.isEmpty ? primaryItem.map { [$0.id] } ?? []
            : visibleItems.filter { selection.contains($0.id) }.map(\.id)
        perform { try store.assign(orderedIDs: ids, to: id) }
    }

    // 076318/09e510: read the cached native list collection when the menu is constructed.
    func pinboardMenuTargets() -> [ClipboardPinboardTarget] {
        pinboardMenuCollection.value
    }

    func dropItems(identifiers: [String], to target: ClipboardListTarget) {
        // 03c3b0's local write error branch only consumes the error; no additional system alert.
        try? store.dropItems(identifiers: identifiers, to: target)
    }

    func assignItems(_ items: [ClipboardRestoreItem], to target: ClipboardPinboardTarget) {
        perform { try store.assign(items: items, to: target) }
    }

    // 3ba2bc: history context, nonempty input, and at least one current type2 owner.
    // Pasto's local unshared groups satisfy the original writable-owner predicate.
    func canUnassignItems(_ items: [ClipboardRestoreItem]) -> Bool {
        let hasPinboardOwner = items.contains { $0.hasNativePinboardOwner() ?? !$0.resolvedItem().pinboardIDs.isEmpty }
        return pinboardID == nil && !showDeleted && !items.isEmpty && hasPinboardOwner
    }

    // 09ee9c forwards the array captured when the group menu was built.
    func assignItems(_ items: [ClipboardRestoreItem], to id: UUID?) {
        perform {
            try withExtendedLifetime(items) {
                try store.assign(items: items, to: id)
            }
        }
    }

    func addToStack(_ item: ClipboardItem, restoreItem: ClipboardRestoreItem? = nil) {
        insertStackItem(id: item.id, input: restoreItem)
    }

    func addToStack(_ input: ClipboardRestoreItem) {
        insertStackItem(id: input.id, input: input)
    }

    private func insertStackItem(id: UUID, input: ClipboardRestoreItem?) {
        let previousIDs = stackItemIDs
        if let input { stackRestoreInputs[id] = input }
        let append = store.preferences.stackReversed
        let insertionIndex = append ? previousIDs.count : 0
        stackIDs.insert(id, at: append ? stackIDs.count : 0)
        controller?.stackTableController?.didInsertNativeSnippet(previousIDs: previousIDs,
            updated: stackSnippetInputs, at: insertionIndex)
    }

    func reverseStack() {
        OriginalStackFunctions.f_10008468c(&stackIDs)
        store.preferences.stackReversed.toggle()
        perform { try store.save() }
        controller?.stackTableController?.updateNativeSnippets(stackSnippetInputs)
    }

    func selectAll() {
        guard let items = collectionOwner?.appliedItems(for: self) else { return }
        cancelPendingNeighborSelection()
        allowsEmptySelection = false
        let ids = items.map(\.id)
        applyOrderedSelection(ids, anchor: ids.last, primary: ids.last)
    }
    func deselectAll() {
        cancelPendingNeighborSelection()
        allowsEmptySelection = true
        applyOrderedSelection([], anchor: nil, primary: nil)
    }

    func pauseMonitoring(minutes: Int? = nil) {
        store.preferences.isMonitoringPaused = true
        store.preferences.pauseUntil = minutes.map { Date().addingTimeInterval(Double($0) * 60) }
        perform {
            try store.save()
            ReplicaCopiedOSD.showPaused(resumeDate: store.preferences.pauseUntil)
            monitoringPauseChanged?()
        }
    }

    func resumeMonitoring() {
        store.preferences.isMonitoringPaused = false
        store.preferences.pauseUntil = nil
        perform {
            try store.save()
            ReplicaCopiedOSD.showResumed()
            monitoringPauseChanged?()
        }
    }

    func moveList(identifier: String, to target: ClipboardListTarget) -> Bool {
        guard let source = store.tabListTarget(identifier: identifier) else { return false }
        return toolbarOwner?.moveList(source, to: target, persist: { offset in
            // 3c4cdc consumes transaction errors; 097828 still performs its applier move.
            try? self.store.moveList(source, toOffset: offset)
        }) ?? false
    }

}

@MainActor
final class ReplicaPanel: NSPanel, NSWindowDelegate {
    weak var collectionFocusTarget: NSView?
    weak var tabTitleEditingOwner: OriginalPinboardTabTitleView?
    weak var cardTitleEditingOwner: ReplicaCardTitleView?
    var keyHandler: ((NSEvent) -> Bool)?
    var didResignKey: (() -> Void)?
    var didChangeScreen: (() -> Void)?
    var closeRequested: (() -> Void)?
    var copyRequested: (() -> Void)?
    var undoManagerRequested: (() -> UndoManager?)?
    func windowDidResignKey(_ notification: Notification) { didResignKey?() }
    func windowDidChangeScreen(_ notification: Notification) { didChangeScreen?() }
    // Paste 0x100077fe0: nil without a provider; otherwise return its current value.
    func windowWillReturnUndoManager(_ window: NSWindow) -> UndoManager? { undoManagerRequested?() }
    override func performClose(_ sender: Any?) { closeRequested?() }
    override func validateMenuItem(_ menuItem: NSMenuItem) -> Bool {
        if menuItem.action == #selector(NSWindow.performClose(_:)) { return true }
        return super.validateMenuItem(menuItem)
    }
    @objc func copy(_ sender: Any?) { copyRequested?() }
    override var canBecomeKey: Bool { true }
    override var canBecomeMain: Bool { true }
    override func layoutIfNeeded() {
        super.layoutIfNeeded()
        minSize = frame.size
        maxSize = frame.size
    }
    override func makeFirstResponder(_ responder: NSResponder?) -> Bool {
        if let responder { return super.makeFirstResponder(responder) }
        return super.makeFirstResponder(initialFirstResponder ?? contentView)
    }
    override func sendEvent(_ event: NSEvent) {
        if event.type == .keyDown, tabTitleEditingOwner?.ownsEditor(in: self) == true {
            super.sendEvent(event)
            return
        }
        if event.type == .keyDown, event.keyCode == 53,
           cardTitleEditingOwner?.ownsEditor(in: self) == true {
            super.sendEvent(event)
            return
        }
        if event.type == .keyDown, keyHandler?(event) == true { return }
        if event.type == .keyDown, let collection = collectionFocusTarget,
           collection.window === self, firstResponder === collection,
           let content = contentView as? ReplicaPanelContentView,
           content.tryInterpretSearchKeyEvent(event) { return }
        super.sendEvent(event)
    }
}

@MainActor
private final class ReplicaMainWindowController: NSWindowController {
    private let contentUndoManager = OriginalDependency(\OriginalDependencyValues.pasteboardUndoManager)

    // Paste 0x100018680: use the shared dependency instead of a window-local manager.
    override var undoManager: UndoManager? { contentUndoManager.f_1000da768() }
}

@MainActor
private final class ReplicaEditorWindow: NSWindow {
    override var canBecomeKey: Bool { true }
    override var canBecomeMain: Bool { true }
}

@MainActor
private final class ReplicaStackPanel: NSPanel {
    override var canBecomeKey: Bool { OriginalStackFunctions.f_1000114f4() }
    override var canBecomeMain: Bool { OriginalStackFunctions.f_1000114ec() }
}

@MainActor
final class ReplicaUIController {
    let store: ClipboardStore
    let state: ReplicaUIState
    var panel: NSPanel { loadPanel() }
    var isPanelOrderedVisible: Bool { loadedPanel?.isVisible == true }
    var isPanelKeyWindow: Bool { loadedPanel?.isKeyWindow == true }
    var pasteHandler: ((UUID, Bool) -> Bool)?
    var pasteItemsHandler: (([UUID], Bool) -> Bool)?
    var directPasteItemsHandler: (([UUID], Bool) -> Bool)?
    var pasteRestoreItemsHandler: (([ClipboardRestoreItem], Bool, Bool) -> Bool)?
    var copiedItemsHandler: (() -> Void)?
    var panelDidShow: (() -> Void)?
    var panelWillClose: ((_ restorePreviousApplication: Bool) -> Void)?
    var panelDidLoad: (() -> Void)?
    @Published private(set) var isPanelVisible = false
    var pasteboard: NSPasteboard = .general
    var hotKeyConfigurationChanged: (() -> Void)?
    var hotKeyRecordingChanged: ((Bool) -> Void)?
    var stackDidChange: (() -> Void)?
    weak var stackTableController: OriginalStackTableController?
    var isStackVisible: Bool { stackWindow?.isVisible == true }
    var hotKeyStatusMessage: String {
        get { state.hotKeyStatusMessage }
        set { state.hotKeyStatusMessage = newValue }
    }
    private let sharingPolicy: WindowSharingPolicy
    private let panelFrameAutosaveName: String
    private var loadedPanel: NSPanel?
    private var mainWindowController: NSWindowController?
    private var isPanelResizing = false
    private var panelTransitionGeneration = 0
    private var isPanelClosing = false
    private var panelMouseMonitor: Any?
    private var panelEscapeMonitor: Any?
    private var outsideMouseMonitor: Any?
    private var panelDismissObservers: [NSObjectProtocol] = []
    private var menuTrackingDepth = 0
    private weak var originalPanelScreen: NSScreen?
    private var settingsWindow: NSWindow?
    private var closedSearchTimer: Timer?
    private var closedCreateObservation: AnyCancellable?
    private var closedRestoreObservation: AnyCancellable?
    private var stackWindow: NSWindow?
    private var stackWindowController: OriginalStackWindowController?
    private var stackCaptureObserver: NSObjectProtocol?
    private var itemWindows: [UUID: NSWindow] = [:]
    private let previewRegistry = OriginalPreviewWindowRegistry()
    private var editorWindowTransitions: [ObjectIdentifier: OriginalPreviewWindowTransition] = [:]
    private var previewAnchors: [UUID: WeakReplicaPreviewAnchor] = [:]
    private var previewPopover: OriginalPreviewPopover?
    var filterBrowserPopover: OriginalFilterBrowserPopover?
    private var preferenceObservation: AnyCancellable?

    init(store: ClipboardStore) {
        self.store = store
        let storePath = store.directoryURL.standardizedFileURL.resolvingSymlinksInPath().path
        let namespace = SHA256.hash(data: Data(storePath.utf8)).map { String(format: "%02x", $0) }.joined()
        panelFrameAutosaveName = "PasteReplicaMainWindow_NSWindowFrameAutosaveName.\(namespace)"
        sharingPolicy = WindowSharingPolicy(store: store)
        state = ReplicaUIState(store: store)
        state.controller = self
        preferenceObservation = store.$preferences.sink { [weak self] _ in
            DispatchQueue.main.async { [weak self] in self?.applyAppearance() }
        }
        applyAppearance()
    }

    private func loadPanel() -> NSPanel {
        if let loadedPanel { return loadedPanel }
        let panel = ReplicaPanel(contentRect: .init(x: 0, y: 0, width: 1512, height: 332),
                                 styleMask: [.borderless, .nonactivatingPanel],
                                 backing: .buffered, defer: false)
        loadedPanel = panel
        let controller = ReplicaMainWindowController(window: panel)
        mainWindowController = controller
        // Paste 0x1000187d0 installs 0x10001a78c -> 0x100018f70 with a weak controller.
        panel.undoManagerRequested = { [weak controller] in controller?.undoManager }
        panel.identifier = NSUserInterfaceItemIdentifier("paste-replica-panel")
        panel.title = "Pasto"
        panel.isOpaque = false
        panel.backgroundColor = .clear
        panel.hasShadow = false
        panel.isMovable = false
        panel.isFloatingPanel = true
        panel.level = .mainMenu
        panel.hidesOnDeactivate = false
        panel.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
        panel.isReleasedWhenClosed = false
        sharingPolicy.apply(to: panel)
        let content = ReplicaPanelContentView(frame: NSRect(origin: .zero, size: panel.frame.size))
        content.canInterpretSearchInput = { [weak self, weak content] in
            guard let self, let content, self.panel.isKeyWindow,
                  let responder = self.panel.firstResponder else { return false }
            return responder === (self.panel as? ReplicaPanel)?.collectionFocusTarget || responder === content || responder === self.panel
        }
        content.onSearchText = { [weak self] text in
            guard let self else { return }
            let words = text.split(separator: " ").map(String.init)
            self.state.applySearchInput(nodes: words.map(OriginalSearchQueryNode.text),
                text: words.joined(separator: " "), filters: [])
            if !words.isEmpty {
                self.state.searchVisible = true
                self.state.searchFocus = UUID()
            }
        }
        let hosting = NSHostingView(rootView: ReplicaPanelView(state: state))
        hosting.frame = content.bounds
        hosting.autoresizingMask = [.width, .height]
        content.addSubview(hosting)
        panel.contentView = content
        panel.delegate = panel
        panel.didResignKey = { [weak self] in self?.panelDidResignKey() }
        panel.didChangeScreen = { [weak self] in self?.panelDidChangeScreen() }
        panel.closeRequested = { [weak self] in self?.hidePanel() }
        panel.copyRequested = { [weak self] in
            guard let self, !self.state.hasPendingDeletion else { return }
            self.copySelection(plainTextOnly: false)
        }
        restorePanelFrame()
        panel.layoutIfNeeded()
        installPanelResizeHandle()
        panel.keyHandler = { [weak self] event in self?.handleKey(event) ?? false }
        applyAppearance()
        panelDidLoad?()
        return panel
    }

    deinit {
        MainActor.assumeIsolated {
            removePanelDismissMonitors()
            cancelClosedState()
            if let stackCaptureObserver { NotificationCenter.default.removeObserver(stackCaptureObserver) }
        }
    }

    func showPanel() {
        guard NSApp.modalWindow == nil else {
            NSApp.activate(ignoringOtherApps: true)
            return
        }
        let panel = self.panel
        guard let screen = NSScreen.main, let content = panel.contentView else { return }
        panelTransitionGeneration += 1
        let generation = panelTransitionGeneration
        isPanelClosing = false
        panel.backgroundColor = .clear
        let screenFrame = screen.frame
        panel.setFrame(.init(x: screenFrame.minX, y: screenFrame.minY,
                             width: screenFrame.width, height: content.frame.height), display: false)
        panel.makeFirstResponder(nil)
        cancelClosedState()
        state.normalizeSelection()
        installPanelDismissMonitors()
        mainWindowController?.showWindow(nil)
        originalPanelScreen = screen
        content.superview?.clipsToBounds = true
        content.frame = panel.frame
        content.frame.origin = NSPoint(x: 0, y: -content.frame.height)
        OriginalViewAnimation.f_10021cadc(duration: 0.15,
            timingFunction: CAMediaTimingFunction(controlPoints: 0.2, 0.8, 0.2, 1),
            animated: true, animations: {
            content.animator().frame = NSRect(origin: .zero, size: content.frame.size)
        }, completion: { [self, panel] in
            MainActor.assumeIsolated {
                guard generation == self.panelTransitionGeneration else { return }
                if #available(macOS 26, *) {} else { panel.backgroundColor = .windowBackgroundColor }
                self.isPanelVisible = true
                if self.state.searchVisible, self.filterBrowserPopover?.isDisplayed != true {
                    self.state.searchFocus = UUID()
                }
                self.panelDidShow?()
            }
        })
    }

    private func panelDidChangeScreen() {
        guard let content = panel.contentView, let screen = panel.screen,
              let originalScreen = originalPanelScreen, !screen.isEqual(originalScreen) else { return }
        let frame = screen.frame
        panel.setFrame(.init(x: frame.minX, y: frame.minY,
                             width: frame.width, height: content.frame.height), display: true)
        originalPanelScreen = screen
    }

    private func panelDidResignKey() {
        // 0x100018c84 checks these guards in the window notification callback.
        // Its one-shot suppression setter belongs to the excluded Handoff path.
        guard panel.sheets.isEmpty, NSApp.modalWindow == nil else { return }
        hidePanel()
    }

    private var canDismissPanelForInteraction: Bool {
        isPanelOrderedVisible && !isPanelClosing && menuTrackingDepth == 0
            && panel.sheets.isEmpty && NSApp.modalWindow == nil
    }

    private func isPanelInteractionWindow(_ window: NSWindow?) -> Bool {
        guard let window else { return false }
        if window === previewPopover?.contentViewController?.viewIfLoaded?.window
            || window === filterBrowserPopover?.contentViewController?.viewIfLoaded?.window { return true }
        var ancestor: NSWindow? = window
        while let current = ancestor {
            if current === panel { return true }
            ancestor = current.parent
        }
        return false
    }

    private func installPanelDismissMonitors() {
        removePanelDismissMonitors()
        panelEscapeMonitor = NSEvent.addLocalMonitorForEvents(matching: .keyDown) { [weak self] event in
            let handled = MainActor.assumeIsolated { () -> Bool in
                guard let self, event.keyCode == 53, self.canDismissPanelForInteraction,
                      let window = event.window ?? NSApp.keyWindow else { return false }
                let filterWindow = self.filterBrowserPopover?.contentViewController?.viewIfLoaded?.window
                let previewWindow = self.previewPopover?.contentViewController?.viewIfLoaded?.window
                guard window === filterWindow || window === previewWindow else { return false }
                self.cancelSearchOrPanel()
                return true
            }
            return handled ? nil : event
        }
        let mouseDown: NSEvent.EventTypeMask = [.leftMouseDown, .rightMouseDown, .otherMouseDown]
        panelMouseMonitor = NSEvent.addLocalMonitorForEvents(matching: mouseDown) { [weak self] event in
            MainActor.assumeIsolated {
                guard let self, self.canDismissPanelForInteraction,
                      !self.isPanelInteractionWindow(event.window) else { return }
                if event.window == nil && self.panel.frame.contains(NSEvent.mouseLocation) { return }
                self.hidePanel()
            }
            return event
        }
        outsideMouseMonitor = NSEvent.addGlobalMonitorForEvents(matching: mouseDown) { [weak self] _ in
            DispatchQueue.main.async { [weak self] in
                guard let self, self.canDismissPanelForInteraction,
                      !self.panel.frame.contains(NSEvent.mouseLocation) else { return }
                self.hidePanel()
            }
        }
        let center = NotificationCenter.default
        panelDismissObservers.append(center.addObserver(forName: NSMenu.didBeginTrackingNotification,
            object: nil, queue: .main) { [weak self] _ in
                MainActor.assumeIsolated { self?.menuTrackingDepth += 1 }
            })
        panelDismissObservers.append(center.addObserver(forName: NSMenu.didEndTrackingNotification,
            object: nil, queue: .main) { [weak self] _ in
                MainActor.assumeIsolated {
                    guard let self else { return }
                    self.menuTrackingDepth = max(0, self.menuTrackingDepth - 1)
                    guard self.menuTrackingDepth == 0 else { return }
                    DispatchQueue.main.async { [weak self] in
                        guard let self, self.canDismissPanelForInteraction,
                              !self.panel.frame.contains(NSEvent.mouseLocation) else { return }
                        if !NSApp.isActive || (!self.panel.isKeyWindow
                            && !self.isPanelInteractionWindow(NSApp.keyWindow)) { self.hidePanel() }
                    }
                }
            })
        panelDismissObservers.append(center.addObserver(forName: NSApplication.didResignActiveNotification,
            object: NSApp, queue: .main) { [weak self] _ in
                MainActor.assumeIsolated {
                    guard let self, self.canDismissPanelForInteraction else { return }
                    self.hidePanel()
                }
            })
    }

    private func removePanelDismissMonitors() {
        if let panelMouseMonitor { NSEvent.removeMonitor(panelMouseMonitor) }
        if let panelEscapeMonitor { NSEvent.removeMonitor(panelEscapeMonitor) }
        if let outsideMouseMonitor { NSEvent.removeMonitor(outsideMouseMonitor) }
        panelMouseMonitor = nil
        panelEscapeMonitor = nil
        outsideMouseMonitor = nil
        for observer in panelDismissObservers { NotificationCenter.default.removeObserver(observer) }
        panelDismissObservers.removeAll()
        menuTrackingDepth = 0
    }

    func hidePanel() {
        guard let panel = loadedPanel else { return }
        guard panel.isVisible, let content = panel.contentView else { return }
        guard !isPanelClosing else { return }
        cancelPendingDeletion()
        removePanelDismissMonitors()
        panelTransitionGeneration += 1
        let generation = panelTransitionGeneration
        if #available(macOS 26, *) {} else { panel.backgroundColor = .clear }
        panel.makeFirstResponder(nil)
        beginClosedState()
        isPanelClosing = true
        NotificationCenter.default.post(name: OriginalPreviewPopover.mainWindowWillCloseNotification, object: nil)
        // 0x100019a84 → onWillClose → 0x1000b11ac: return activation
        // before the close animation, unless detached previews still own it.
        panelWillClose?(previewRegistry.windows.isEmpty)
        content.superview?.clipsToBounds = false
        OriginalViewAnimation.f_10021cadc(duration: 0.2,
            timingFunction: OriginalViewAnimation.f_10021cf38(), animated: true, animations: {
            content.animator().frame = NSRect(origin: NSPoint(x: 0, y: -content.frame.height), size: content.frame.size)
        }, completion: { [self, content] in
            MainActor.assumeIsolated {
                guard generation == self.panelTransitionGeneration else { return }
                self.mainWindowController?.close()
                self.originalPanelScreen = nil
                self.isPanelClosing = false
                self.isPanelVisible = false
                content.superview?.clipsToBounds = true
            }
        })
    }

    private func beginClosedState() {
        cancelClosedState()
        closedCreateObservation = NotificationCenter.default.publisher(
            for: ClipboardMonitor.didCreateItemNotification, object: nil).sink { [weak self] _ in
                MainActor.assumeIsolated {
                    guard let self else { return }
                    self.state.chooseBoard(nil)
                    self.closedSearchTimer?.invalidate()
                    self.closedSearchTimer = nil
                }
            }
        closedRestoreObservation = NotificationCenter.default.publisher(
            for: ClipboardStore.didRestoreItemNotification, object: nil).sink { [weak self] _ in
            MainActor.assumeIsolated {
                guard let self, self.state.isCollectionSearchQueryEmpty, self.state.pinboardID == nil else { return }
                self.state.chooseBoard(nil)
                self.closedSearchTimer?.invalidate()
                self.closedSearchTimer = nil
            }
        }
        closedSearchTimer = Timer.scheduledTimer(withTimeInterval: 10, repeats: false) { [weak self] _ in
            MainActor.assumeIsolated {
                guard let self, !self.state.isCollectionSearchQueryEmpty else { return }
                self.state.applySearchInput(nodes: [], text: "", filters: [])
                self.state.toolbarOwner?.f_10000e0ec()
                self.state.searchVisible = false
            }
        }
    }

    private func cancelClosedState() {
        closedSearchTimer?.invalidate()
        closedSearchTimer = nil
        closedCreateObservation?.cancel()
        closedCreateObservation = nil
        closedRestoreObservation?.cancel()
        closedRestoreObservation = nil
    }
    func togglePanel() { isPanelOrderedVisible && !isPanelClosing ? hidePanel() : showPanel() }
    func focusSearch() {
        if !isPanelOrderedVisible || !isPanelKeyWindow || isPanelClosing { showPanel() }
        state.searchVisible = true
        state.searchFocus = UUID()
    }
    func showError(message: String) {
        presentError(NSError(domain: "Pasto", code: 1,
                             userInfo: [NSLocalizedDescriptionKey: message]))
    }

    func showSettings() {
        if settingsWindow == nil {
            settingsWindow = makeWindow(title: "设置", size: .init(width: 648, height: 600),
                                        view: ReplicaSettingsView(state: state))
            settingsWindow?.styleMask.remove(.resizable)
            settingsWindow?.styleMask.insert(.fullSizeContentView)
            settingsWindow?.titleVisibility = .hidden
            settingsWindow?.titlebarAppearsTransparent = true
            settingsWindow?.toolbar = NSToolbar(identifier: "PastoSettings")
            settingsWindow?.toolbar?.showsBaselineSeparator = false
            settingsWindow?.toolbarStyle = .unified
            if let settingsWindow {
                settingsWindow.setFrame(NSRect(origin: settingsWindow.frame.origin, size: NSSize(width: 648, height: 600)), display: false)
            }
        }
        show(settingsWindow!)
    }

    func showStack() {
        if stackWindow == nil {
            let window = ReplicaStackPanel(contentRect: .init(x: 0, y: 0, width: 264, height: 76),
                                           styleMask: [.borderless, .nonactivatingPanel], backing: .buffered, defer: false)
            window.title = "Pasto Stack"
            window.isReleasedWhenClosed = false
            window.isOpaque = false; window.backgroundColor = .clear; window.hasShadow = true
            window.contentView = NSHostingView(rootView: ReplicaStackView(state: state))
            sharingPolicy.apply(to: window)
            if !window.setFrameUsingName(OriginalStackWindowController.stackFrameAutosaveName),
               !window.setFrameUsingName("PasteReplicaStack") {
                let frame = NSScreen.main?.visibleFrame ?? .init(x: 0, y: 0, width: 1200, height: 800)
                window.setFrameOrigin(.init(x: frame.maxX - 284, y: frame.maxY - 96))
            }
            let controller = OriginalStackWindowController(window: window)
            controller.f_100011138()
            stackWindowController = controller
            stackWindow = window
            // 0x100082f5c → 0x10037a75c: consume the successful capture
            // notification after the history transaction and shared Undo cleanup.
            stackCaptureObserver = NotificationCenter.default.addObserver(
                forName: ClipboardMonitor.didCaptureItemNotification, object: nil, queue: nil) { [weak self] _ in
                    MainActor.assumeIsolated { self?.captureLatestItemIntoStack() }
                }
        }
        hidePanel()
        stackWindow!.orderFrontRegardless()
        stackContentsChanged()
    }

    func hideStack() {
        guard let closingController = stackWindowController else { return }
        let closingWindow = stackWindow
        closingController.close()
        // 0a86c0/2182a4: release the coordinator owner, then the presented content.
        stackWindowController = nil
        closingController.contentViewController = nil
        closingWindow?.contentView = nil
        stackWindow = nil
        stackTableController = nil
        if let stackCaptureObserver { NotificationCenter.default.removeObserver(stackCaptureObserver) }
        stackCaptureObserver = nil
        // 084f14/083d18: each new Stack controller owns a fresh, transient queue.
        if state.stackIDs.isEmpty { stackDidChange?() }
        else { state.stackIDs.removeAll() }
    }

    func stackContentsChanged() {
        if let window = stackWindow {
            let height = CGFloat(32 + min(10, max(1, state.stackItemIDs.count)) * 44)
            let top = window.frame.maxY
            window.setFrame(.init(x: window.frame.minX, y: top - height, width: 264, height: height), display: true)
        }
        stackDidChange?()
    }

    func captureIntoStack(id: UUID) {
        guard isStackVisible, let item = store.items.first(where: { $0.id == id && !$0.isDeleted }) else { return }
        state.addToStack(item)
    }

    private func captureLatestItemIntoStack() {
        // 083758 -> 363d58 creates the history collection; 1b8054 reads its first entity.
        guard isStackVisible, let collection = store.makeListCollection(pinboardID: nil) else { return }
        let snapshot = collection.value
        guard let identifier = snapshot.identifiers.first else { return }
        guard let reference = snapshot.itemReferences[identifier] else { fatalError("Missing Stack item reference") }
        let input = reference.requiredRestoreItem(id: identifier)
        state.addToStack(input)
    }

    func contextMenuRestoreItems() -> [ClipboardRestoreItem] {
        appliedRestoreItems()
    }

    func addSelectionToStack() {
        for input in appliedRestoreItems() {
            state.addToStack(input)
        }
        showStack()
    }

    @discardableResult
    func pasteStackItem(id: UUID, plainTextOnly: Bool) -> Bool {
        if let input = state.stackRestoreItem(for: id) {
            return paste(restoreItems: [input], plainTextOnly: plainTextOnly)
        }
        // Saved UUID-only queues keep the writer's reload and deletion validation.
        return paste(ids: [id], plainTextOnly: plainTextOnly)
    }

    func consumeStackHead() {
        let previousIDs = state.stackItemIDs
        guard let first = previousIDs.first else { return }
        guard let index = state.stackIDs.firstIndex(of: first) else { return }
        state.stackIDs.remove(at: index)
        stackTableController?.didConsumeNativeHead(previousIDs: previousIDs, remaining: state.stackSnippetInputs)
    }

    func newTextItem() { showEditor(item: nil) }

    func renameHistory() {
        guard let name = prompt(title: "重命名", message: "", initial: store.preferences.historyTitle) else { return }
        store.preferences.historyTitle = name
        state.perform { try store.save() }
    }

    func renameItem(_ item: ClipboardItem) {
        guard let title = prompt(title: "重命名", message: "", initial: item.title, allowsEmpty: true) else { return }
        state.perform { try store.updateItem(id: item.id, title: title, text: nil) }
    }

    func clearHistory() {
        guard !store.localListMenuState(pinboardID: nil).isEmpty else {
            state.perform { try store.eraseHistory() }
            return
        }
        let alert = NSAlert()
        sharingPolicy.apply(to: alert.window)
        alert.messageText = "您确定要删除剪贴板历史记录吗？"
        alert.informativeText = "已固定的项目和 Pasto 不会被删除。此操作无法撤销。"
        let deleteButton = alert.addButton(withTitle: "删除历史")
        deleteButton.hasDestructiveAction = true
        deleteButton.keyEquivalent = ""
        let cancelButton = alert.addButton(withTitle: "取消")
        cancelButton.keyEquivalent = "\r"
        alert.window.defaultButtonCell = cancelButton.cell as? NSButtonCell
        if let settingsWindow, settingsWindow.isVisible {
            alert.beginSheetModal(for: settingsWindow) { [weak self] response in
                guard let self, response == .alertFirstButtonReturn else { return }
                self.state.perform { try self.store.eraseHistory() }
            }
        } else if alert.runModal() == .alertFirstButtonReturn { state.perform { try store.eraseHistory() } }
    }

    func copySelection(plainTextOnly: Bool) {
        let items = appliedRestoreItems()
        guard !items.isEmpty else { NSSound.beep(); return }
        performCopy {
            try store.writeToPasteboard(restoreItems: items, pasteboard: pasteboard,
                                        options: plainTextOnly ? .plainText : [])
        }
    }

    func copy(item: ClipboardItem, plainTextOnly: Bool) {
        performCopy {
            try store.writeToPasteboard(selectedItems: [item], pasteboard: pasteboard, plainTextOnly: plainTextOnly)
        }
    }

    func copy(input: ClipboardRestoreItem, plainTextOnly: Bool) {
        performCopy {
            try store.writeToPasteboard(restoreItems: [input], pasteboard: pasteboard,
                                        options: plainTextOnly ? .plainText : [])
        }
    }

    func copy(ids: [UUID], plainTextOnly: Bool) {
        guard !ids.isEmpty else { return }
        performCopy {
            try store.writeToPasteboard(ids: ids, pasteboard: pasteboard, plainTextOnly: plainTextOnly)
        }
    }

    func copyRecognizedImageText(item: ClipboardItem) {
        performCopy {
            try store.writeRecognizedImageTextToPasteboard(item: item, pasteboard: pasteboard)
        }
    }

    private func performCopy(_ write: () throws -> Void) {
        state.perform {
            try write()
            copiedItemsHandler?()
            hidePanel()
        }
    }

    func pasteSelection(plainTextOnly: Bool) {
        let items = appliedRestoreItems()
        guard !items.isEmpty else { return }
        _ = paste(restoreItems: items, plainTextOnly: plainTextOnly)
    }

    @discardableResult
    func paste(item: ClipboardItem, plainTextOnly: Bool) -> Bool {
        // Value-based legacy views retain their ID writer compatibility path.
        if let input = appliedRestoreItems(orderedIDs: [item.id]).first {
            return paste(restoreItems: [input], plainTextOnly: plainTextOnly)
        }
        return paste(ids: [item.id], plainTextOnly: plainTextOnly)
    }

    @discardableResult
    func paste(itemID: UUID, plainTextOnly: Bool) -> Bool {
        // 075a6c/06c60c use only the optional applied-item lookup.
        guard let input = appliedRestoreItems(orderedIDs: [itemID]).first else { return false }
        return paste(restoreItems: [input], plainTextOnly: plainTextOnly)
    }

    @discardableResult
    private func paste(restoreItems: [ClipboardRestoreItem], plainTextOnly: Bool, forceDirect: Bool = false) -> Bool {
        guard !restoreItems.isEmpty else { return false }
        if let pasteRestoreItemsHandler { return pasteRestoreItemsHandler(restoreItems, plainTextOnly, forceDirect) }
        let ids = restoreItems.map(\.id)
        if forceDirect {
            if let directPasteItemsHandler { return directPasteItemsHandler(ids, plainTextOnly) }
            presentError(NSError(domain: "Pasto", code: 1,
                userInfo: [NSLocalizedDescriptionKey: "粘贴服务尚未就绪，请使用“拷贝”后粘贴。 "]))
            return false
        }
        return paste(ids: ids, plainTextOnly: plainTextOnly)
    }

    @discardableResult
    func paste(ids: [UUID], plainTextOnly: Bool) -> Bool {
        guard !ids.isEmpty else { return false }
        if let pasteItemsHandler {
            return pasteItemsHandler(ids, plainTextOnly)
        }
        guard ids.count == 1, let id = ids.first, let pasteHandler else {
            presentError(NSError(domain: "Pasto", code: 1,
                                 userInfo: [NSLocalizedDescriptionKey: "粘贴服务尚未就绪，请使用“拷贝”后粘贴。 "]))
            return false
        }
        return pasteHandler(id, plainTextOnly)
    }

    private func previewSelection() {
        guard let id = state.collectionSelectionSnapshot().orderedIDs.last else { return }
        _ = showCollectionPreview(itemID: id)
    }

    @discardableResult
    private func showCollectionPreview(itemID: UUID) -> Bool {
        guard isPanelOrderedVisible, !isPanelClosing,
              let replicaPanel = loadedPanel as? ReplicaPanel,
              let collection = replicaPanel.collectionFocusTarget as? ReplicaNativeCollectionHost,
              collection.window === replicaPanel,
              let items = collection.appliedItems(for: state),
              let index = items.firstIndex(where: { $0.id == itemID }) else { return false }
        collection.previewItem(at: index) { [weak self] input, anchor in
            guard let self else { return }
            let popover = self.previewPopover ?? self.makePreviewPopover()
            self.previewPopover = popover
            if popover.isDisplayed {
                popover.close()
                return
            }
            popover.show(itemIdentity: input.previewIdentity, itemIdentifier: input.previewIdentifier, input: input,
                contentView: self.makePreviewContent(for: input), relativeTo: anchor)
        }
        return true
    }

    func showPreview(item: ClipboardItem, input: ClipboardRestoreItem? = nil) {
        if case nil = input, showCollectionPreview(itemID: item.id) { return }
        let input = input ?? appliedRestoreItems(orderedIDs: [item.id]).first
            ?? state.stackRestoreItem(for: item.id) ?? ClipboardRestoreItem(item: item)
        if let existing = previewRegistry.f_10008747c(itemIdentity: input.previewIdentity) {
            show(existing)
            return
        }
        let anchor: NSView?
        if isPanelOrderedVisible, !isPanelClosing, state.visibleItems.contains(where: { $0.id == item.id }),
           let replicaPanel = panel as? ReplicaPanel,
           let collection = replicaPanel.collectionFocusTarget as? ReplicaNativeCollectionHost,
           collection.window === panel {
            guard let cell = collection.previewAnchor(for: item.id) else { return }
            anchor = cell
        } else {
            anchor = previewAnchors[item.id]?.view
        }
        if let anchor, anchor.window != nil {
            let popover = previewPopover ?? makePreviewPopover()
            previewPopover = popover
            if popover.isDisplayed {
                popover.close()
                return
            }
            popover.show(itemIdentity: input.previewIdentity, itemIdentifier: input.previewIdentifier, input: input,
                contentView: makePreviewContent(for: input), relativeTo: anchor)
            return
        }
        let window = OriginalPreviewWindow()
        window.title = item.title.isEmpty ? item.kind.displayName : item.title
        let content = makePreviewContent(for: input)
        if let preview = content as? OriginalItemPreviewView {
            preview.onEditingStateChanged = { [weak self] editing in
                self?.previewRegistry.f_10008727c(isEditing: editing, itemIdentifier: input.previewIdentifier)
            }
        }
        window.contentView = content
        window.setContentSize(content.frame.size)
        sharingPolicy.apply(to: window)
        window.center()
        previewRegistry.f_100086c10(window: window, itemIdentity: input.previewIdentity,
            itemIdentifier: input.previewIdentifier, isEditing: false)
        show(window)
    }

    // 0x1000655cc filters the complete input before invoking each item's router.
    private func editItems(_ items: [ClipboardRestoreItem]) {
        let editable = items.filter { Self.allowsEditingInput($0) }
        guard !editable.isEmpty else { NSSound.beep(); return }
        for input in editable { presentEditingPreview(input: input) }
    }

    private static func allowsEditingInput(_ input: ClipboardRestoreItem) -> Bool {
        if let rawType = input.previewRawType() {
            return [1, 2, 4, 5].contains(rawType)
        }
        return allowsContentEditing(input.resolvedItem())
    }

    // 0x10031c2ec: offline lists have no CKShare permission branch.
    private static func allowsContentEditing(_ item: ClipboardItem) -> Bool {
        switch item.kind {
        case .image, .color, .link, .text, .richText: return true
        case .files, .unknown: return false
        }
    }

    // 0x10006bed8: capability and text selection gates precede routing and the task.
    private func writeAppliedSelection() -> Bool {
        guard OriginalWritingTools.isAvailable() else { return false }
        let items = appliedRestoreItems().filter {
            guard Self.allowsEditingInput($0) else { return false }
            if let rawType = $0.previewRawType() { return rawType == 5 }
            let item = $0.resolvedItem()
            return item.kind == .text || item.kind == .richText
        }
        guard !items.isEmpty else { return false }
        editItems(items)
        OriginalWritingTools.showAfterDelay()
        return true
    }

    // 0x1003bb280 → Router witness → 0x100003da0, with beginEditing=true.
    private func presentEditingPreview(input: ClipboardRestoreItem) {
        let window = OriginalPreviewWindow()
        window.animationBehavior = .documentWindow
        sharingPolicy.apply(to: window)
        let registry = previewRegistry
        let itemIdentifier = input.previewIdentifier
        registry.f_100086c10(window: window, itemIdentity: input.previewIdentity,
                           itemIdentifier: itemIdentifier, isEditing: true)
        let transition = OriginalPreviewWindowTransition(window: window)
        let windowIdentity = ObjectIdentifier(window)
        editorWindowTransitions[windowIdentity] = transition
        transition.onPresented = { [weak self] window in self?.positionEditingPreview(window) }
        transition.onDismissed = { [weak self] _ in
            _ = self?.editorWindowTransitions.removeValue(forKey: windowIdentity)
        }
        let preview = makeOriginalReplicaNativePreview(state: state, input: input)
        preview.onEndEditing = { window.close() }
        preview.onEditingStateChanged = { editing in
            registry.f_10008727c(isEditing: editing, itemIdentifier: input.previewIdentifier)
        }
        preview.f_10007be8c()
        let controller = NSViewController()
        controller.view = preview
        transition.present(controller)
        (preview.itemContentView as? OriginalPreviewEditableContent)?.focusPreviewEditing()
    }

    // 0x1000042b4: the registry already includes the newly presented window.
    private func positionEditingPreview(_ window: NSWindow) {
        window.center()
        guard let screen = window.screen else { return }
        let frame = screen.frame
        let offset = CGFloat(previewRegistry.windows.count * 30)
        var origin = NSPoint(x: window.frame.minX + offset, y: window.frame.minY - offset)
        if frame.maxX < origin.x + window.frame.width { origin.x = frame.maxX - window.frame.width }
        if origin.y < frame.minY { origin.y = frame.minY }
        window.setFrameOrigin(origin)
    }

    // f06c338: capture the visible cell offset before invoking onSelectList.
    private func revealSelectedItemInList() -> Bool {
        let lists = state.selectedItemTargetLists()
        guard !lists.isEmpty, let input = appliedRestoreItems().first else { return false }
        let collection = (panel as? ReplicaPanel)?.collectionFocusTarget as? ReplicaNativeCollectionHost
        let offset = collection?.horizontalOffsetForVisibleItem(input.id)
        state.pendingListFocus = ReplicaUIState.PendingListFocus(itemID: input.id,
            pinboardID: lists[0], horizontalOffset: offset)
        state.chooseListForItemReveal(lists[0])
        return true
    }

    // f228c78 -> f229130 / f228e1c: only a successful reveal calls the live delegate.
    fileprivate func revealSelection(endpointID: UUID, requestedIndex: Int, animated: Bool) {
        guard let replicaPanel = loadedPanel as? ReplicaPanel,
              let collection = replicaPanel.collectionFocusTarget as? ReplicaNativeCollectionHost,
              collection.window === panel else { return }
        collection.revealSelection(state: state, itemID: endpointID, animated: animated) { [weak self, weak collection] success in
            guard success, let self, let collection else { return }
            self.selectionDidReveal(requestedIndex: requestedIndex, collection: collection)
        }
    }

    // f075e3c resolves the requested index after completion, not the revealed endpoint.
    private func selectionDidReveal(requestedIndex: Int, collection: ReplicaNativeCollectionHost) {
        guard let items = collection.appliedItems(for: state), items.indices.contains(requestedIndex),
              let input = items[requestedIndex].restoreItem(),
              let anchor = collection.visibleSelectionAnchor(at: requestedIndex,
                  itemID: items[requestedIndex].id) else {
            NSSound.beep()
            return
        }
        let item = items[requestedIndex]
        if let popover = previewPopover, popover.isDisplayed {
            popover.show(itemIdentity: input.previewIdentity, itemIdentifier: input.previewIdentifier, input: input,
                contentView: makePreviewContent(for: input), relativeTo: anchor)
        }
    }

    func registerPreviewAnchor(for itemID: UUID, view: NSView) {
        previewAnchors[itemID] = WeakReplicaPreviewAnchor(view)
    }

    func removePreviewAnchor(for itemID: UUID, view: NSView) {
        if previewAnchors[itemID]?.view === view { previewAnchors.removeValue(forKey: itemID) }
    }

    private func makePreviewContent(for input: ClipboardRestoreItem) -> NSView {
        makeOriginalReplicaNativePreview(state: state, input: input)
    }

    private func makePreviewPopover() -> OriginalPreviewPopover {
        let preferenceStore = store
        let changes = preferenceStore.preferenceChanges
            .filter { $0.old.showDuringScreenSharing != $0.new.showDuringScreenSharing }
            .map { $0.new.showDuringScreenSharing }.eraseToAnyPublisher()
        let popover = OriginalPreviewPopover(registry: previewRegistry,
            isScreenSharingContentVisible: { preferenceStore.preferences.showDuringScreenSharing },
            visibilityChanges: changes)
        // 0x10007654c -> 0x10006be90: closing clears the owner's optional popover.
        popover.onWillClose = { [weak self] in self?.previewPopover = nil }
        popover.makeContentView = { [weak self] input in
            guard let self else { return nil }
            return makeOriginalReplicaNativePreview(state: self.state, input: input)
        }
        return popover
    }

    func showEditor(item: ClipboardItem?) {
        let windowID = UUID()
        let window = ReplicaEditorWindow(contentRect: NSRect(x: 0, y: 0, width: 500, height: 360),
                                         styleMask: [.borderless], backing: .buffered, defer: false)
        window.title = item == nil ? "新建文本" : "编辑文本"
        window.isReleasedWhenClosed = false
        window.isMovableByWindowBackground = true
        window.isOpaque = false
        window.backgroundColor = .clear
        window.hasShadow = true
        window.level = .floating
        sharingPolicy.apply(to: window)
        window.contentView = NSHostingView(rootView: ReplicaEditorView(state: state, item: item, close: { [weak self] in
            self?.itemWindows[windowID]?.close()
            self?.itemWindows.removeValue(forKey: windowID)
        }))
        window.center()
        itemWindows[windowID] = window
        show(window)
    }

    func createPinboard(assignSelection: Bool = false, selectionItems: [ClipboardRestoreItem]? = nil) {
        cancelPendingDeletion()
        let name = String(localized: OriginalPreviewLocalization.f_1001c6aa4())
        let ids = selectionItems?.map(\.id) ?? state.visibleItems.filter { state.selection.contains($0.id) }.map(\.id)
        state.perform {
            let board = try store.createPinboardTarget(name: name)
            if assignSelection {
                if let selectionItems {
                    try store.assign(items: selectionItems, to: board)
                } else {
                    try store.assign(orderedIDs: ids, to: board.id)
                }
            }
            // 039618/03b4c0: retain the created List across the delay; only the owner is weak.
            let target = board.listTarget
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) { [weak self, target] in
                self?.state.beginEditingListSubject.send(target)
            }
        }
    }

    func renamePinboard(_ board: Pinboard) {
        guard let name = prompt(title: "重命名 Pasto", message: "输入新的分组名称。", initial: board.name) else { return }
        state.perform { try store.renamePinboard(id: board.id, name: name) }
    }

    func removePinboard(_ target: ClipboardListTarget) {
        state.cancelItemDeletion()
        state.pinboardDeletionError = nil
        state.pendingPinboardDeletion = target
        // 0x1003c4f00: an empty local group is deleted without confirmation.
        // Nonempty confirmation stays inside the panel by user request, instead
        // of the original 0x100022ad0 → 0x1003b6cfc NSAlert.runModal presenter.
        if store.localListMenuState(target).isEmpty {
            confirmPinboardRemoval()
        } else {
            panel.makeFirstResponder(nil)
        }
    }

    func cancelPinboardRemoval() {
        state.pendingPinboardDeletion = nil
        state.pinboardDeletionError = nil
    }

    func cancelPendingDeletion() {
        cancelPinboardRemoval()
        state.cancelItemDeletion()
    }

    func confirmPinboardRemoval() {
        guard let target = state.pendingPinboardDeletion else { return }
        do {
            try store.removeList(target)
            cancelPinboardRemoval()
            // The native List snapshot chooses the adjacent surviving list.
        } catch {
            // Keep failures in the same confirmation rather than opening an alert.
            state.pinboardDeletionError = error.localizedDescription
        }
    }

    func exportArchive() {
        let chooser = NSSavePanel()
        sharingPolicy.apply(to: chooser)
        chooser.title = "导出剪贴板归档"
        chooser.nameFieldStringValue = "Pasto-archive.json"
        chooser.allowedContentTypes = [.json]
        if chooser.runModal() == .OK, let url = chooser.url {
            state.perform { try store.exportArchive(to: url) }
        }
    }

    func importArchive() {
        let chooser = NSOpenPanel()
        sharingPolicy.apply(to: chooser)
        chooser.title = "导入剪贴板归档"
        chooser.allowedContentTypes = [.json]
        chooser.allowsMultipleSelection = false
        if chooser.runModal() == .OK, let url = chooser.url {
            state.perform { try store.importArchive(from: url) }
            state.normalizeSelection()
        }
    }

    func migratePasteGroups() {
        guard !state.isMigratingPasteGroups else { return }
        hidePanel()
        NSApp.activate(ignoringOtherApps: true)
        let source: URL
        if let detected = PasteGroupMigration.defaultDatabaseURL {
            source = detected
        } else {
            let chooser = NSOpenPanel()
            sharingPolicy.apply(to: chooser)
            chooser.title = "选择 Paste 数据库"
            chooser.message = "未找到本机 Paste 数据。请选择 Paste 的 db.sqlite 文件；已安装的 Paste 将用于识别数据格式。"
            chooser.canChooseDirectories = false
            chooser.allowsMultipleSelection = false
            guard chooser.runModal() == .OK, let url = chooser.url else { return }
            source = url
        }
        state.isMigratingPasteGroups = true
        Task { @MainActor [weak self] in
            guard let self else { return }
            defer { self.state.isMigratingPasteGroups = false }
            do {
                let snapshot = try await Task.detached(priority: .userInitiated) {
                    try PasteGroupMigration.read(from: source)
                }.value
                let confirmation = NSAlert()
                self.sharingPolicy.apply(to: confirmation.window)
                confirmation.messageText = "从 Paste 迁移分组"
                guard !snapshot.pinboards.isEmpty else {
                    confirmation.informativeText = "未找到可迁移的本地分组。"
                    confirmation.addButton(withTitle: "好")
                    confirmation.runModal()
                    return
                }
                confirmation.informativeText = "发现 \(snapshot.pinboards.count) 个分组、\(snapshot.items.count) 个项目。\n将保留分组名称、颜色、排列顺序和项目内容。重复迁移不会重复添加，也不会覆盖 Pasto 已有的内容和设置。"
                if snapshot.unavailableItemCount > 0 {
                    confirmation.informativeText += "\n另有 \(snapshot.unavailableItemCount) 个项目的本地内容不可用，将跳过这些项目。"
                }
                confirmation.addButton(withTitle: "迁移")
                confirmation.addButton(withTitle: "取消")
                guard confirmation.runModal() == .alertFirstButtonReturn else { return }
                let result = try self.store.importPasteGroups(snapshot)
                self.state.normalizeSelection()
                let finished = NSAlert()
                self.sharingPolicy.apply(to: finished.window)
                finished.messageText = result.unavailableItems == 0 ? "迁移完成" : "迁移完成，部分项目已跳过"
                finished.informativeText = "已新增 \(result.addedGroups) 个分组、\(result.addedItems) 个项目。\n已存在：\(result.existingGroups) 个分组、\(result.existingItems) 个项目。"
                if result.unavailableItems > 0 {
                    finished.informativeText += "\n有 \(result.unavailableItems) 个项目未取得本地内容；在 Paste 中恢复内容后可重新迁移。"
                }
                finished.addButton(withTitle: "好")
                finished.runModal()
            } catch {
                self.presentError(error)
            }
        }
    }

    func presentError(_ error: Error) {
        let alert = NSAlert(error: error)
        sharingPolicy.apply(to: alert.window)
        alert.messageText = "操作未完成"
        alert.runModal()
    }

    private func prompt(title: String, message: String, initial: String, allowsEmpty: Bool = false) -> String? {
        let alert = NSAlert()
        sharingPolicy.apply(to: alert.window)
        alert.messageText = title
        alert.informativeText = message
        let input = NSTextField(string: initial)
        input.frame = .init(x: 0, y: 0, width: 300, height: 24)
        alert.accessoryView = input
        alert.addButton(withTitle: "确定")
        alert.addButton(withTitle: "取消")
        alert.window.initialFirstResponder = input
        guard alert.runModal() == .alertFirstButtonReturn else { return nil }
        let name = input.stringValue.trimmingCharacters(in: .whitespacesAndNewlines)
        return name.isEmpty && !allowsEmpty ? nil : name
    }

    private func restorePanelFrame() {
        if !panel.setFrameUsingName(panelFrameAutosaveName) {
            let storedHeight = store.preferences.panelHeight
            let height = storedHeight.isFinite && storedHeight > 0 ? storedHeight : 332
            if panel.frame.height != height {
                var frame = panel.frame
                frame.size.height = height
                panel.setFrame(frame, display: true, animate: false)
                panel.saveFrame(usingName: panelFrameAutosaveName)
            }
        }
        store.preferences.panelHeight = panel.frame.height
    }

    private func installPanelResizeHandle() {
        guard let content = panel.contentView else { return }
        let handle = ReplicaPanelResizeHandle()
        handle.translatesAutoresizingMaskIntoConstraints = false
        content.addSubview(handle)
        NSLayoutConstraint.activate([
            handle.topAnchor.constraint(equalTo: content.topAnchor),
            handle.leadingAnchor.constraint(equalTo: content.leadingAnchor),
            handle.trailingAnchor.constraint(equalTo: content.trailingAnchor),
            handle.heightAnchor.constraint(equalToConstant: 10)
        ])
        handle.onLiveResize = { [weak self] size in self?.resizePanel(size: size) }
        handle.onEndResize = { [weak self] in self?.finishPanelResize() }
        handle.onResetSize = { [weak self] in self?.resetPanelSize() }
        handle.onGestureFinished = { [weak self] in self?.isPanelResizing = false }
    }

    private func resizePanel(size: NSSize) {
        isPanelResizing = true
        let height: CGFloat
        if size.height < 252 {
            height = 252 - (252 - size.height).squareRoot().rounded(.toNearestOrAwayFromZero)
        } else if size.height > 412 {
            height = 412 + (size.height - 412).squareRoot().rounded(.toNearestOrAwayFromZero)
        } else {
            height = size.height
        }
        panel.setFrame(NSRect(origin: panel.frame.origin,
                              size: NSSize(width: size.width, height: height)), display: false)
    }

    private func finishPanelResize() {
        var frame = panel.frame
        frame.size.height = min(max(frame.height, 252), 412)
        panel.setFrame(frame, display: true, animate: true)
        isPanelResizing = false
        savePanelFrame()
    }

    private func resetPanelSize() {
        guard panel.frame.height != 332 else { return }
        var frame = panel.frame
        frame.size.height = 332
        panel.setFrame(frame, display: true, animate: true)
        isPanelResizing = false
        savePanelFrame()
    }

    private func savePanelFrame() {
        panel.saveFrame(usingName: panelFrameAutosaveName)
        store.preferences.panelHeight = panel.frame.height
        state.perform { try store.save() }
    }

    private func positionPanel() {
        guard !isPanelResizing, let screen = NSScreen.main else { return }
        let frame = screen.frame
        let storedHeight = store.preferences.panelHeight
        let height = storedHeight.isFinite && storedHeight > 0 ? storedHeight : 332
        panel.setFrame(.init(x: frame.minX, y: frame.minY,
                             width: frame.width, height: height), display: true)
    }

    private func applyAppearance() {
        let appearance: NSAppearance?
        switch store.preferences.appearance {
        case "light": appearance = NSAppearance(named: .aqua)
        case "dark": appearance = NSAppearance(named: .darkAqua)
        default: appearance = nil
        }
        NSApp.appearance = appearance
        loadedPanel?.appearance = appearance
        settingsWindow?.appearance = appearance
        stackWindow?.appearance = appearance
        itemWindows.values.forEach { $0.appearance = appearance }
        previewRegistry.windows.forEach { $0.appearance = appearance }
        if isPanelOrderedVisible { positionPanel() }
    }

    private func makeWindow<V: View>(title: String, size: NSSize, view: V) -> NSWindow {
        let window = NSWindow(contentRect: .init(origin: .zero, size: size),
                              styleMask: [.titled, .closable, .miniaturizable, .resizable],
                              backing: .buffered, defer: false)
        window.title = title
        window.isReleasedWhenClosed = false
        window.contentView = NSHostingView(rootView: view)
        sharingPolicy.apply(to: window)
        window.center()
        return window
    }

    private func show(_ window: NSWindow) {
        hidePanel()
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }

    private func appliedCollectionItems() -> [ClipboardCollectionEntry]? {
        guard let panel = loadedPanel,
              let collection = (panel as? ReplicaPanel)?.collectionFocusTarget as? ReplicaNativeCollectionHost,
              collection.window === panel else { return nil }
        return collection.appliedItems(for: state)
    }

    fileprivate func clearPanelFirstResponder() {
        loadedPanel?.makeFirstResponder(nil)
    }

    private func appliedSelectionItems() -> [ClipboardItem] {
        guard let panel = loadedPanel,
              let collection = (panel as? ReplicaPanel)?.collectionFocusTarget as? ReplicaNativeCollectionHost,
              collection.window === panel else { return [] }
        return collection.appliedSelectedItems(for: state,
            orderedIDs: state.collectionSelectionSnapshot().orderedIDs) ?? []
    }

    private func appliedRestoreItems(orderedIDs: [UUID]? = nil) -> [ClipboardRestoreItem] {
        guard let panel = loadedPanel,
              let collection = (panel as? ReplicaPanel)?.collectionFocusTarget as? ReplicaNativeCollectionHost,
              collection.window === panel else { return [] }
        return collection.appliedRestoreItems(for: state,
            orderedIDs: orderedIDs ?? state.collectionSelectionSnapshot().orderedIDs) ?? []
    }

    // 0x100064da0: filter first, deactivate once, then decode each accepted preview again.
    private func openAppliedSelection() {
        let selected = appliedSelectionItems()
        let accepted = selected.filter { item in
            if item.kind == .link { return true }
            guard let path = item.decodedFilePreviewMetadata?.paths.first else { return false }
            let url = URL(fileURLWithPath: path)
            let accessed = url.startAccessingSecurityScopedResource()
            url.stopAccessingSecurityScopedResource()
            let exists = FileManager.default.fileExists(atPath: path)
            return accessed && exists
        }
        guard !accepted.isEmpty else { NSSound.beep(); return }
        NSApp.deactivate()
        for item in accepted {
            if let link = item.decodedLinkPreviewMetadata {
                NSWorkspace.shared.open(link.url)
            } else if let files = item.decodedFilePreviewMetadata {
                guard let path = files.paths.first else { return }
                NSWorkspace.shared.open(URL(fileURLWithPath: path))
            }
        }
    }

    private func handleKey(_ event: NSEvent) -> Bool {
        if state.hasPendingDeletion {
            if event.keyCode == 53 { cancelPendingDeletion(); return true }
            let modifiers = event.modifierFlags.intersection([.command, .control, .option, .shift])
            if (event.keyCode == 36 || event.keyCode == 76), modifiers.isEmpty {
                if state.pendingItemDeletion != nil { state.confirmItemDeletion() }
                else { confirmPinboardRemoval() }
                return true
            }
            // Allow button focus navigation and normal app commands, but do not
            // pass copy/delete/navigation through to the covered card collection.
            if event.keyCode == 48 { return false }
            if event.keyCode == 49, panel.firstResponder !== (panel as? ReplicaPanel)?.collectionFocusTarget { return false }
            return !(modifiers == .command && event.charactersIgnoringModifiers == "q")
        }
        if event.keyCode == 53 {
            guard canDismissPanelForInteraction else { return false }
            cancelSearchOrPanel()
            return true
        }
        let modifiers = event.modifierFlags.intersection(.deviceIndependentFlagsMask)
        let command = modifiers.contains(.command)
        let shift = modifiers.contains(.shift)
        let isEditing = panel.firstResponder is NSTextView
        let key = event.charactersIgnoringModifiers?.lowercased() ?? ""

        let ownsCollectionFocus: Bool
        if let collection = (panel as? ReplicaPanel)?.collectionFocusTarget,
           collection.window === panel {
            ownsCollectionFocus = panel.firstResponder === collection
        } else {
            ownsCollectionFocus = false
        }
        let plainModifiers = NSEvent.ModifierFlags(rawValue: store.preferences.plainTextModifierRawValue)
        let plain = event.modifierFlags.isSuperset(of: plainModifiers)
        let signature = OriginalShortcutFunctions.f_1001e7d18(event)
        let quickPasteAction = OriginalCollectionShortcutActions.quickPasteAction(for: signature,
            quickPasteModifierRawValue: store.preferences.quickPasteModifierRawValue,
            plainTextModifierRawValue: store.preferences.plainTextModifierRawValue)

        func performQuickPaste(_ action: OriginalCollectionShortcutActions.QuickPasteAction) {
            guard let items = appliedCollectionItems() else { return }
            if items.indices.contains(action.index) {
                paste(itemID: items[action.index].id, plainTextOnly: action.options.contains(.plainTextAndLinks))
            }
            if let appliedItems = appliedCollectionItems() { state.selectFirstAppliedItem(items: appliedItems) }
        }

        if !ownsCollectionFocus {
            guard let quickPasteAction else { return false }
            performQuickPaste(quickPasteAction)
            return true
        }
        if !state.searchVisible {
            if store.preferences.previousPinboardShortcut?.matches(event) == true { state.switchBoard(-1); return true }
            if store.preferences.nextPinboardShortcut?.matches(event) == true { state.switchBoard(1); return true }
        }
        if !isEditing, let action = quickPasteAction {
            performQuickPaste(action)
            return true
        }
        if !isEditing, let options = OriginalCollectionShortcutActions.copyOptions(for: signature,
            plainTextModifierRawValue: store.preferences.plainTextModifierRawValue) {
            if previewPopover != nil {
                // 0x100069fe0 retains the owner and resolves its current popover at the deadline.
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) { [self] in
                    previewPopover?.performClose(self)
                }
                return true
            }
            copySelection(plainTextOnly: options.contains(.plainTextAndLinks))
            return true
        }
        if !isEditing, signature.keyCode == OriginalShortcutFunctions.f_1001e94d4("e"),
           signature.modifierRawValue == NSEvent.ModifierFlags.command.rawValue {
            editItems(appliedRestoreItems())
            return true
        }
        if !isEditing, signature.keyCode == OriginalShortcutFunctions.f_1001e94d4("e"),
           signature.modifierRawValue == NSEvent.ModifierFlags.command.union(.shift).rawValue {
            return writeAppliedSelection()
        }
        if !isEditing, signature.keyCode == OriginalShortcutFunctions.f_1001e94d4("v"),
           signature.modifierRawValue == NSEvent.ModifierFlags.command.rawValue {
            _ = paste(restoreItems: appliedRestoreItems(), plainTextOnly: false, forceDirect: true)
            return true
        }
        if !isEditing, signature.keyCode == OriginalShortcutFunctions.f_1001e94d4("o"),
           signature.modifierRawValue == NSEvent.ModifierFlags.command.rawValue {
            openAppliedSelection()
            return true
        }
        if !isEditing, signature.keyCode == OriginalShortcutFunctions.f_1001e94d4("r"),
           signature.modifierRawValue == NSEvent.ModifierFlags.command.rawValue {
            guard let collection = (panel as? ReplicaPanel)?.collectionFocusTarget as? ReplicaNativeCollectionHost,
                  collection.window === panel else { return false }
            return collection.renameSelection(state: state)
        }
        if !isEditing, signature.keyCode == OriginalShortcutFunctions.f_1001e94d4("g"),
           signature.modifierRawValue == NSEvent.ModifierFlags.command.rawValue {
            return revealSelectedItemInList()
        }
        if signature.keyCode == OriginalShortcutFunctions.f_1001e94d4("f"),
           signature.modifierRawValue == NSEvent.ModifierFlags.command.rawValue {
            if state.searchVisible, filterBrowserPopover?.isDisplayed == true {
                filterBrowserPopover?.close()
            } else {
                handleSearchCommand()
            }
            return true
        }
        if command {
            switch key {
            case "n": shift ? createPinboard() : newTextItem(); return true
            case ",": showSettings(); return true
            case "a" where !isEditing && !modifiers.contains(.control) && !modifiers.contains(.option):
                shift ? state.deselectAll() : state.selectAll(); return true
            default: break
            }
        }
        if event.keyCode == 49, !isEditing {
            previewSelection()
            return true
        }
        if !isEditing, let specialKey = event.specialKey {
            switch specialKey {
            case .carriageReturn, .enter:
                return OriginalSearchCommands.f_10004867c(selector: NSSelectorFromString("insertNewline:"),
                    onEnter: { [self] in pasteSelection(plainTextOnly: plain) }, onCancel: nil)
            default: break
            }
        }
        guard !isEditing else { return false }
        let navigation = OriginalCollectionNavigation.f_1002348a8(event)
        switch navigation {
        case .forward, .backward:
            let mode = OriginalOrderedSelection.mode(modifierFlags: event.modifierFlags.rawValue)
            guard mode != 1 else { return false }
            state.moveSelection(navigation == .forward ? 1 : -1, extending: mode == 2)
        case .first:
            state.moveSelectionToBoundary(last: false, extending: shift)
        case .last:
            state.moveSelectionToBoundary(last: true, extending: shift)
        case .unhandled:
            return false
        }
        return true
    }

    func cancelSearchOrPanel() {
        if state.hasPendingDeletion { cancelPendingDeletion(); return }
        guard canDismissPanelForInteraction else { return }
        if filterBrowserPopover?.isShown == true { filterBrowserPopover?.close() }
        if previewPopover?.isShown == true { previewPopover?.close() }
        // 0x100037704: cancel a search context before closing the main window.
        if !state.isCollectionSearchQueryEmpty {
            state.applySearchInput(nodes: [], text: "", filters: [])
            state.toolbarOwner?.f_10000e0ec()
            state.searchVisible = false
            panel.makeFirstResponder(nil)
            return
        }
        hidePanel()
    }
}
