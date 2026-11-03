"""Explicit phase-77 modal-input delta, reversed only for earlier frozen contracts.

Raw production and every new route are checked by test_p1_repair_modal_restore_input.
These literal hunks preserve the historical scope; they do not replace its evidence.
"""
from pathlib import Path
from native_application_scope_contract import pre_native_application

RESTORE_ITEM_PATH = 'replica/Sources/PastoCore/ClipboardRestoreItem.swift'

# path, previous source hunk, reviewed modal-input source hunk
HUNKS = [('replica/Sources/PastoCore/ClipboardCollectionItemReference.swift',
  '        return item\n    }\n}\n',
  '        return item\n'
  '    }\n'
  '\n'
  '    @MainActor public func requiredRestoreItem(id: UUID) -> ClipboardRestoreItem {\n'
  '        guard let object = (try? context.existingObject(with: objectID)) as? PastoItemEntity else {\n'
  '            fatalError("Missing restore item")\n'
  '        }\n'
  '        return ClipboardRestoreItem(id: id, object: object)\n'
  '    }\n'
  '}\n'),
 ('replica/Sources/PastoCore/Pasteboard.swift',
  '                             options: plainTextOnly ? .plainText : [], recognizedImageData: nil,\n'
  '                             resolvedSelection: selectedItems)\n'
  '    }\n'
  '\n',
  '                             options: plainTextOnly ? .plainText : [], recognizedImageData: nil,\n'
  '                             resolvedSelection: selectedItems)\n'
  '    }\n'
  '\n'
  '    public func writeToPasteboard(restoreItems: [ClipboardRestoreItem], pasteboard: NSPasteboard,\n'
  '                                 options: OriginalPasteboardRestore.Options) throws {\n'
  '        let selected = restoreItems.map { $0.resolvedItem() }\n'
  '        try writeToPasteboard(ids: restoreItems.map(\\.id), pasteboard: pasteboard, options: options,\n'
  '                             recognizedImageData: nil, resolvedSelection: selected)\n'
  '    }\n'
  '\n'),
 ('replica/Sources/Pasto/AppMain.swift',
  '            ui.directPasteItemsHandler = { [weak self] ids, plain in\n'
  '                self?.paste(ids: ids, plain: plain, forceDirect: true) ?? false\n'
  '            }\n'
  '            ui.panelDidShow = { [weak self] in self?.rememberPanelApplication() }\n',
  '            ui.directPasteItemsHandler = { [weak self] ids, plain in\n'
  '                self?.paste(ids: ids, plain: plain, forceDirect: true) ?? false\n'
  '            }\n'
  '            ui.pasteRestoreItemsHandler = { [weak self] items, plain, forceDirect in\n'
  '                self?.paste(ids: items.map(\\.id), plain: plain, forceDirect: forceDirect, restoreItems: '
  'items) ?? false\n'
  '            }\n'
  '            ui.panelDidShow = { [weak self] in self?.rememberPanelApplication() }\n'),
 ('replica/Sources/Pasto/AppMain.swift',
  '\n'
  '    @discardableResult\n'
  '    private func paste(ids: [UUID], plain: Bool, forceDirect: Bool = false) -> Bool {\n'
  '        let requestedTarget = targetApplication\n'
  '        let hasAccessibilityAccess = accessibilityService.f_100ae5e74()\n',
  '\n'
  '    @discardableResult\n'
  '    private func paste(ids: [UUID], plain: Bool, forceDirect: Bool = false,\n'
  '                       restoreItems: [ClipboardRestoreItem]? = nil) -> Bool {\n'
  '        let requestedTarget = targetApplication\n'
  '        let hasAccessibilityAccess = accessibilityService.f_100ae5e74()\n'),
 ('replica/Sources/Pasto/AppMain.swift',
  '        var restoreOptions: OriginalPasteboardRestore.Options = plain ? .plainText : []\n'
  '        if store.preferences.alwaysPastePlainText { restoreOptions.insert(.plainTextAndLinks) }\n'
  '        do { try store.writeToPasteboard(ids: ids, pasteboard: pasteboard, options: restoreOptions) }\n'
  '        catch {\n'
  '            pasteLogger.error("restore_failed code=\\((error as NSError).code, privacy: .public)")\n',
  '        var restoreOptions: OriginalPasteboardRestore.Options = plain ? .plainText : []\n'
  '        if store.preferences.alwaysPastePlainText { restoreOptions.insert(.plainTextAndLinks) }\n'
  '        do {\n'
  '            if let restoreItems {\n'
  '                try store.writeToPasteboard(restoreItems: restoreItems, pasteboard: pasteboard, options: '
  'restoreOptions)\n'
  '            } else {\n'
  '                try store.writeToPasteboard(ids: ids, pasteboard: pasteboard, options: restoreOptions)\n'
  '            }\n'
  '        }\n'
  '        catch {\n'
  '            pasteLogger.error("restore_failed code=\\((error as NSError).code, privacy: .public)")\n'),
 ('replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    var pasteItemsHandler: (([UUID], Bool) -> Bool)?\n'
  '    var directPasteItemsHandler: (([UUID], Bool) -> Bool)?\n'
  '    var copiedItemsHandler: (() -> Void)?\n'
  '    var panelDidShow: (() -> Void)?\n',
  '    var pasteItemsHandler: (([UUID], Bool) -> Bool)?\n'
  '    var directPasteItemsHandler: (([UUID], Bool) -> Bool)?\n'
  '    var pasteRestoreItemsHandler: (([ClipboardRestoreItem], Bool, Bool) -> Bool)?\n'
  '    var copiedItemsHandler: (() -> Void)?\n'
  '    var panelDidShow: (() -> Void)?\n'),
 ('replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '\n'
  '    func pasteSelection(plainTextOnly: Bool) {\n'
  '        let items = appliedSelectionItems()\n'
  '        guard !items.isEmpty else { return }\n'
  '        paste(ids: items.map(\\.id), plainTextOnly: plainTextOnly)\n'
  '    }\n'
  '\n'
  '    @discardableResult\n'
  '    func paste(item: ClipboardItem, plainTextOnly: Bool) -> Bool {\n'
  '        paste(ids: [item.id], plainTextOnly: plainTextOnly)\n'
  '    }\n'
  '\n',
  '\n'
  '    func pasteSelection(plainTextOnly: Bool) {\n'
  '        let items = appliedRestoreItems()\n'
  '        guard !items.isEmpty else { return }\n'
  '        _ = paste(restoreItems: items, plainTextOnly: plainTextOnly)\n'
  '    }\n'
  '\n'
  '    @discardableResult\n'
  '    func paste(item: ClipboardItem, plainTextOnly: Bool) -> Bool {\n'
  '        if let input = appliedRestoreItems(orderedIDs: [item.id]).first {\n'
  '            return paste(restoreItems: [input], plainTextOnly: plainTextOnly)\n'
  '        }\n'
  '        return paste(ids: [item.id], plainTextOnly: plainTextOnly)\n'
  '    }\n'
  '\n'
  '    @discardableResult\n'
  '    private func paste(restoreItems: [ClipboardRestoreItem], plainTextOnly: Bool, forceDirect: Bool = '
  'false) -> Bool {\n'
  '        guard !restoreItems.isEmpty else { return false }\n'
  '        if let pasteRestoreItemsHandler { return pasteRestoreItemsHandler(restoreItems, plainTextOnly, '
  'forceDirect) }\n'
  '        let ids = restoreItems.map(\\.id)\n'
  '        if forceDirect {\n'
  '            if let directPasteItemsHandler { return directPasteItemsHandler(ids, plainTextOnly) }\n'
  '            presentError(NSError(domain: "Pasto", code: 1,\n'
  '                userInfo: [NSLocalizedDescriptionKey: "粘贴服务尚未就绪，请使用“拷贝”后粘贴。 "]))\n'
  '            return false\n'
  '        }\n'
  '        return paste(ids: ids, plainTextOnly: plainTextOnly)\n'
  '    }\n'
  '\n'),
 ('replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '    }\n'
  '\n'
  '    // 0x100064da0: filter first, deactivate once, then decode each accepted preview again.\n'
  '    private func openAppliedSelection() {\n',
  '    }\n'
  '\n'
  '    private func appliedRestoreItems(orderedIDs: [UUID]? = nil) -> [ClipboardRestoreItem] {\n'
  '        guard let panel = loadedPanel,\n'
  '              let collection = (panel as? ReplicaPanel)?.collectionFocusTarget as? '
  'ReplicaNativeCollectionHost,\n'
  '              collection.window === panel else { return [] }\n'
  '        return collection.appliedRestoreItems(for: state,\n'
  '            orderedIDs: orderedIDs ?? state.collectionSelectionSnapshot().orderedIDs) ?? []\n'
  '    }\n'
  '\n'
  '    // 0x100064da0: filter first, deactivate once, then decode each accepted preview again.\n'
  '    private func openAppliedSelection() {\n'),
 ('replica/Sources/Pasto/UI/ReplicaUIController.swift',
  '        if !isEditing, signature.keyCode == OriginalShortcutFunctions.f_1001e94d4("v"),\n'
  '           signature.modifierRawValue == NSEvent.ModifierFlags.command.rawValue {\n'
  '            let appliedIDs = Set((appliedCollectionItems() ?? []).map(\\.id))\n'
  '            let ids = state.collectionSelectionSnapshot().orderedIDs.filter { appliedIDs.contains($0) }\n'
  '            if !ids.isEmpty {\n'
  '                if let directPasteItemsHandler { _ = directPasteItemsHandler(ids, false) }\n'
  '                else {\n'
  '                    presentError(NSError(domain: "Pasto", code: 1,\n'
  '                        userInfo: [NSLocalizedDescriptionKey: "粘贴服务尚未就绪，请使用“拷贝”后粘贴。 "]))\n'
  '                }\n'
  '            }\n'
  '            return true\n'
  '        }\n',
  '        if !isEditing, signature.keyCode == OriginalShortcutFunctions.f_1001e94d4("v"),\n'
  '           signature.modifierRawValue == NSEvent.ModifierFlags.command.rawValue {\n'
  '            _ = paste(restoreItems: appliedRestoreItems(), plainTextOnly: false, forceDirect: true)\n'
  '            return true\n'
  '        }\n'),
 ('replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift',
  '            guard let index = positions[identifier] else { return nil }\n'
  '            return renderedItem(at: index)\n'
  '        }\n'
  '    }\n',
  '            guard let index = positions[identifier] else { return nil }\n'
  '            return renderedItem(at: index)\n'
  '        }\n'
  '    }\n'
  '\n'
  '    func appliedRestoreItems(for state: ReplicaUIState, orderedIDs: [UUID]) -> [ClipboardRestoreItem]? {\n'
  '        guard self.state === state, state.collectionOwner === self else { return nil }\n'
  '        let positions = Dictionary(uniqueKeysWithValues: items.enumerated().map { ($0.element.id, '
  '$0.offset) })\n'
  '        return orderedIDs.compactMap { identifier in\n'
  '            guard let index = positions[identifier] else { return nil }\n'
  '            let item = items[index]\n'
  '            return itemReferences[identifier]?.requiredRestoreItem(id: identifier) ?? '
  'ClipboardRestoreItem(item: item)\n'
  '        }\n'
  '    }\n')]

def pre_modal_restore(source):
    source = pre_native_application(source)
    for path, previous, current in HUNKS:
        if current in source:
            assert source.count(current) == 1, path
            source = source.replace(current, previous, 1)
    return source


def pre_modal_restore_bytes(path):
    path = Path(path)
    value = path.read_bytes()
    return pre_modal_restore(value.decode()).encode() if path.suffix == '.swift' else value
