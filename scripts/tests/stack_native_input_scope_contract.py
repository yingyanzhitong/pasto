"""Only the nine reviewed Stack native-input deltas, for frozen historical checks."""
from pathlib import Path
from group_menu_input_scope_contract import pre_group_menu_input

CHANGES = [['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    @Published var stackIDs: [UUID] = [] {\n        didSet {\n',
  '    private var stackRestoreInputs: [UUID: ClipboardRestoreItem] = [:]\n'
  '    @Published var stackIDs: [UUID] = [] {\n'
  '        didSet {\n'
  '            let retainedIDs = Set(stackIDs)\n'
  '            stackRestoreInputs = stackRestoreInputs.filter { retainedIDs.contains($0.key) }\n'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    var stackItems: [ClipboardItem] {\n'
  '        stackIDs.compactMap { id in store.items.first { $0.id == id && !$0.isDeleted } }\n'
  '    }\n',
  '    var stackItems: [ClipboardItem] {\n'
  '        stackIDs.compactMap { stackItem(for: $0) }\n'
  '    }\n'
  '\n'
  '    func hasStackItem(_ id: UUID) -> Bool {\n'
  '        stackRestoreInputs[id] != nil || store.items.contains { $0.id == id && !$0.isDeleted }\n'
  '    }\n'
  '\n'
  '    func stackItem(for id: UUID) -> ClipboardItem? {\n'
  '        if let input = stackRestoreInputs[id] { return input.resolvedItem() }\n'
  '        // UUID queues saved by older versions retain their existing value adapter.\n'
  '        return store.items.first { $0.id == id && !$0.isDeleted }\n'
  '    }\n'
  '\n'
  '    func stackRestoreItem(for id: UUID) -> ClipboardRestoreItem? {\n'
  '        if let input = stackRestoreInputs[id] { return input }\n'
  '        guard let item = stackItem(for: id) else { return nil }\n'
  '        return ClipboardRestoreItem(item: item)\n'
  '    }\n'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    func addToStack(_ item: ClipboardItem) {\n        let previousIDs = stackItems.map(\\.id)\n',
  '    func addToStack(_ item: ClipboardItem, restoreItem: ClipboardRestoreItem? = nil) {\n'
  '        let previousIDs = stackItems.map(\\.id)\n'
  '        if let restoreItem { stackRestoreInputs[item.id] = restoreItem }\n'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    private func captureLatestItemIntoStack() {\n'
  '        // 0x100083758 resolves the history list; 0x10008339c takes its first item.\n'
  '        guard let item = store.search(query: "").first else { return }\n'
  '        captureIntoStack(id: item.id)\n'
  '    }\n',
  '    private func captureLatestItemIntoStack() {\n'
  '        // 083758 -> 363d58 creates the history collection; 1b8054 reads its first entity.\n'
  '        guard isStackVisible, let collection = store.makeListCollection(pinboardID: nil) else { '
  'return }\n'
  '        let snapshot = collection.value\n'
  '        guard let identifier = snapshot.identifiers.first else { return }\n'
  '        guard let reference = snapshot.itemReferences[identifier] else { fatalError("Missing '
  'Stack item reference") }\n'
  '        let input = reference.requiredRestoreItem(id: identifier)\n'
  '        state.addToStack(input.resolvedItem(), restoreItem: input)\n'
  '    }\n'
  '\n'
  '    func addSelectionToStack() {\n'
  '        for input in appliedRestoreItems() {\n'
  '            state.addToStack(input.resolvedItem(), restoreItem: input)\n'
  '        }\n'
  '        showStack()\n'
  '    }\n'
  '\n'
  '    @discardableResult\n'
  '    func pasteStackItem(id: UUID, plainTextOnly: Bool) -> Bool {\n'
  '        guard let input = state.stackRestoreItem(for: id) else { return false }\n'
  '        return paste(restoreItems: [input], plainTextOnly: plainTextOnly)\n'
  '    }\n'],
 ['replica/Sources/Pasto/AppMain.swift',
  '                guard let first = self.ui.state.stackItems.first else { return }\n'
  '                self.targetApplication = NSWorkspace.shared.frontmostApplication\n'
  '                self.ui.consumeStackHead()\n'
  '                _ = self.paste(ids: [first.id], plain: false, forceDirect: true)\n',
  '                guard let first = self.ui.state.stackItems.first,\n'
  '                      let input = self.ui.state.stackRestoreItem(for: first.id) else { return '
  '}\n'
  '                self.targetApplication = NSWorkspace.shared.frontmostApplication\n'
  '                self.ui.consumeStackHead()\n'
  '                _ = self.paste(ids: [input.id], plain: false, forceDirect: true, restoreItems: '
  '[input])\n'],
 ['replica/Sources/Pasto/UI/AuxiliaryViews.swift',
  '                state.store.items.contains { $0.id == state.stackIDs[index] && !$0.isDeleted '
  '}\n',
  '                state.hasStackItem(state.stackIDs[index])\n'],
 ['replica/Sources/Pasto/UI/AuxiliaryViews.swift',
  '                    Button("复制") { state.controller?.copy(item: item, plainTextOnly: false) }\n',
  '                    Button("复制") {\n'
  '                        if let current = state.stackItem(for: item.id) {\n'
  '                            state.controller?.copy(item: current, plainTextOnly: false)\n'
  '                        }\n'
  '                    }\n'],
 ['replica/Sources/Pasto/UI/AuxiliaryViews.swift',
  '                        if state.controller?.paste(item: item, plainTextOnly: false) == true '
  '{\n',
  '                        if state.controller?.pasteStackItem(id: item.id, plainTextOnly: false) '
  '== true {\n'],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  '                for selected in state.selectedItems { state.addToStack(selected) }\n'
  '                state.controller?.showStack()\n',
  '                state.controller?.addSelectionToStack()\n'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    var stackItems: [ClipboardItem] {\n',
  '    var stackItemIDs: [UUID] { stackIDs.filter { hasStackItem($0) } }\n'
  '\n'
  '    var stackItems: [ClipboardItem] {\n'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    func stackRestoreItem(for id: UUID) -> ClipboardRestoreItem? {\n'
  '        if let input = stackRestoreInputs[id] { return input }\n'
  '        guard let item = stackItem(for: id) else { return nil }\n'
  '        return ClipboardRestoreItem(item: item)\n'
  '    }\n',
  '    func stackRestoreItem(for id: UUID) -> ClipboardRestoreItem? {\n'
  '        stackRestoreInputs[id]\n'
  '    }\n'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '        let previousIDs = stackItems.map(\\.id)\n',
  '        let previousIDs = stackItemIDs\n'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '        let previousIDs = state.stackItems.map(\\.id)\n',
  '        let previousIDs = state.stackItemIDs\n'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '            let height = CGFloat(32 + min(10, max(1, state.stackItems.count)) * 44)\n',
  '            let height = CGFloat(32 + min(10, max(1, state.stackItemIDs.count)) * 44)\n'],
 ['replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '        guard let input = state.stackRestoreItem(for: id) else { return false }\n'
  '        return paste(restoreItems: [input], plainTextOnly: plainTextOnly)\n',
  '        if let input = state.stackRestoreItem(for: id) {\n'
  '            return paste(restoreItems: [input], plainTextOnly: plainTextOnly)\n'
  '        }\n'
  "        // Saved UUID-only queues keep the writer's reload and deletion validation.\n"
  '        return paste(ids: [id], plainTextOnly: plainTextOnly)\n'],
 ['replica/Sources/Pasto/AppMain.swift',
  '                guard let first = self.ui.state.stackItems.first,\n'
  '                      let input = self.ui.state.stackRestoreItem(for: first.id) else { return '
  '}\n',
  '                guard let first = self.ui.state.stackItemIDs.first else { return }\n'
  '                let input = self.ui.state.stackRestoreItem(for: first)\n'],
 ['replica/Sources/Pasto/AppMain.swift',
  '                _ = self.paste(ids: [input.id], plain: false, forceDirect: true, restoreItems: '
  '[input])\n',
  '                _ = self.paste(ids: [first], plain: false, forceDirect: true, restoreItems: '
  'input.map { [$0] })\n'],
 ['replica/Sources/Pasto/AppMain.swift',
  '                if self.ui.state.stackItems.isEmpty { self.ui.hideStack() }\n',
  '                if self.ui.state.stackItemIDs.isEmpty { self.ui.hideStack() }\n'],
 ['replica/Sources/Pasto/AppMain.swift',
  '        let enabled = ui.isStackVisible && !ui.state.stackItems.isEmpty && !isRecordingHotKey\n',
  '        let enabled = ui.isStackVisible && !ui.state.stackItemIDs.isEmpty && '
  '!isRecordingHotKey\n'],
 ['replica/Sources/Pasto/UI/AuxiliaryViews.swift',
  '            if state.stackItems.isEmpty {\n',
  '            if state.stackItemIDs.isEmpty {\n'],
 ['replica/Sources/Pasto/UI/AuxiliaryViews.swift',
  '                    .frame(height: CGFloat(min(10, max(1, state.stackItems.count)) * 44))\n',
  '                    .frame(height: CGFloat(min(10, max(1, state.stackItemIDs.count)) * 44))\n'],
 ['replica/Sources/Pasto/UI/AuxiliaryViews.swift',
  '                            if state.stackItems.isEmpty { state.controller?.hideStack() }\n',
  '                            if state.stackItemIDs.isEmpty { state.controller?.hideStack() }\n']]

def pre_stack_native_inputs(source):
    source = pre_group_menu_input(source)
    for path, previous, current in reversed(CHANGES):
        if current in source:
            assert source.count(current) == 1, path
            source = source.replace(current, previous, 1)
    return source

def pre_stack_native_inputs_bytes(path):
    path = Path(path)
    value = path.read_bytes()
    return pre_stack_native_inputs(value.decode()).encode() if path.suffix == '.swift' else value
