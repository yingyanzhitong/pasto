"""Explicit Stack occurrence deltas for earlier frozen source contracts.

Current duplicate insertion and row/consumer behavior is checked in test_p1_repair_stack_occurrences.
"""
from pathlib import Path
from stack_registration_scope_contract import pre_stack_registration

CHANGES = [('replica/Sources/PastoCore/OriginalStackTableController.swift',
  '    private var snippetsRevision: UInt = 0\n'
  '    private var animatedSnippetsAwaitingRefresh: [ClipboardItem]?\n'
  '    public var makeCell: ((ClipboardItem) -> NSView)?\n'
  '    public var removeSnippet: (([UUID], Int) -> Bool)?\n'
  '    public var removeActionTitle = ""\n',
  '    private var snippetsRevision: UInt = 0\n'
  '    private var animatedSnippetsAwaitingRefresh: [ClipboardItem]?\n'
  '    public var makeCell: ((ClipboardItem, Int) -> NSView)?\n'
  '    public var removeSnippet: (([UUID], Int) -> Bool)?\n'
  '    public var removeActionTitle = ""\n'),
 ('replica/Sources/PastoCore/OriginalStackTableController.swift',
  '        guard edge == .trailing else { return [] }\n'
  '        return [NSTableViewRowAction(style: .destructive, title: removeActionTitle) { [weak self] _, row '
  'in\n'
  '            guard let self, self.snippets.indices.contains(row), let removeSnippet = self.removeSnippet '
  'else { return }\n'
  '            let revision = self.snippetsRevision\n'
  '            guard removeSnippet(self.snippets.map(\\.id), row), self.snippetsRevision == revision else { '
  'return }\n'
  '            self.snippets.remove(at: row)\n'
  '            self.tableView.removeRows(at: IndexSet(integer: row), withAnimation: .slideUp)\n'
  '            self.f_100083a20()\n'
  '        }]\n'
  '    }\n'
  '\n',
  '        guard edge == .trailing else { return [] }\n'
  '        return [NSTableViewRowAction(style: .destructive, title: removeActionTitle) { [weak self] _, row '
  'in\n'
  '            guard let self else { return }\n'
  '            self.removeRow(at: row, expectedIDs: self.snippets.map(\\.id))\n'
  '        }]\n'
  '    }\n'
  '\n'
  '    public func removeRow(at row: Int, expectedIDs: [UUID]) {\n'
  '        guard snippets.map(\\.id) == expectedIDs, snippets.indices.contains(row),\n'
  '              let removeSnippet else { return }\n'
  '        let revision = snippetsRevision\n'
  '        guard removeSnippet(expectedIDs, row), snippetsRevision == revision else { return }\n'
  '        snippets.remove(at: row)\n'
  '        tableView.removeRows(at: IndexSet(integer: row), withAnimation: .slideUp)\n'
  '        f_100083a20()\n'
  '    }\n'
  '\n'),
 ('replica/Sources/PastoCore/OriginalStackTableController.swift',
  '    public func tableView(_ tableView: NSTableView, viewFor tableColumn: NSTableColumn?, row: Int) -> '
  'NSView? {\n'
  '        guard snippets.indices.contains(row) else { return nil }\n'
  '        return makeCell?(snippets[row])\n'
  '    }\n'
  '}\n',
  '    public func tableView(_ tableView: NSTableView, viewFor tableColumn: NSTableColumn?, row: Int) -> '
  'NSView? {\n'
  '        guard snippets.indices.contains(row) else { return nil }\n'
  '        return makeCell?(snippets[row], row)\n'
  '    }\n'
  '}\n'),
 ('replica/Sources/Pasto/UI/AuxiliaryViews.swift',
  '            return true\n'
  '        }\n'
  '        controller.makeCell = { item in\n'
  '            NSHostingView(rootView:\n'
  '                OriginalStackSnippetCellView(item: item, imageProvider: { item in\n'
  '                    OriginalStackCategoryIcons.image(for: state.store.originalContentKind(of: item))\n',
  '            return true\n'
  '        }\n'
  '        controller.makeCell = { [weak controller] item, row in\n'
  '            let expectedIDs = controller?.snippets.map(\\.id) ?? []\n'
  '            return NSHostingView(rootView:\n'
  '                OriginalStackSnippetCellView(item: item, imageProvider: { item in\n'
  '                    OriginalStackCategoryIcons.image(for: state.store.originalContentKind(of: item))\n'),
 ('replica/Sources/Pasto/UI/AuxiliaryViews.swift',
  '                    Button("粘贴") {\n'
  '                        if state.controller?.paste(item: item, plainTextOnly: false) == true {\n'
  '                            state.stackIDs.removeAll { $0 == item.id }\n'
  '                            if state.stackItems.isEmpty { state.controller?.hideStack() }\n'
  '                        }\n'
  '                    }\n'
  '                    Button("预览") { state.controller?.showPreview(item: item) }\n'
  '                    Button("移除") { state.stackIDs.removeAll { $0 == item.id } }\n'
  '                })\n'
  '        }\n',
  '                    Button("粘贴") {\n'
  '                        if state.controller?.paste(item: item, plainTextOnly: false) == true {\n'
  '                            controller?.removeRow(at: row, expectedIDs: expectedIDs)\n'
  '                            if state.stackItems.isEmpty { state.controller?.hideStack() }\n'
  '                        }\n'
  '                    }\n'
  '                    Button("预览") { state.controller?.showPreview(item: item) }\n'
  '                    Button("移除") { controller?.removeRow(at: row, expectedIDs: expectedIDs) }\n'
  '                })\n'
  '        }\n'),
 ('replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '\n'
  '    func addToStack(_ item: ClipboardItem) {\n'
  '        guard !stackIDs.contains(item.id) else { return }\n'
  '        let previousIDs = stackItems.map(\\.id)\n'
  '        let append = store.preferences.stackReversed\n',
  '\n'
  '    func addToStack(_ item: ClipboardItem) {\n'
  '        let previousIDs = stackItems.map(\\.id)\n'
  '        let append = store.preferences.stackReversed\n')]

def pre_stack_occurrences(source):
    source = pre_stack_registration(source)
    for path, previous, current in CHANGES:
        if current in source:
            assert source.count(current) == 1, path
            source = source.replace(current, previous, 1)
    return source


def pre_stack_occurrences_bytes(path):
    path = Path(path)
    value = path.read_bytes()
    return pre_stack_occurrences(value.decode()).encode() if path.suffix == '.swift' else value
