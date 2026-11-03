"""Exact phase108 preview group menu deltas for historical source contracts only."""
from pathlib import Path
from native_unassign_scope_contract import pre_native_unassign
CHANGES = [['replica/Sources/PastoCore/ClipboardListPersistence.swift',
  '    public var name: String { nativeObject.value(forKey: "name") as? String ?? "" }',
  '    public var name: String { nativeObject.value(forKey: "name") as? String ?? "" }\n'
  '    public var colorCode: UInt64? {\n'
  '        OriginalPinboardAttributes.colorCode(from: nativeObject.value(forKey: "rawAttributes") '
  'as? Data)\n'
  '    }'],
 ['replica/Sources/PastoCore/ClipboardRestoreItem.swift',
  '    public func previewSharingContent() -> OriginalPreviewSharing.Content? {',
  '    // 31bc94/09e8a8: the checkmark uses the current native type2 owner, not legacy '
  'memberships.\n'
  '    public func isAssigned(to target: ClipboardPinboardTarget) -> Bool? {\n'
  '        guard let object = nativeObject else { return nil }\n'
  '        guard let owner = object.value(forKey: "list") as? NSManagedObject,\n'
  '              (owner.value(forKey: "rawType") as? NSNumber)?.int64Value == 2 else { return '
  'false }\n'
  '        return owner.isEqual(target.nativeObject)\n'
  '    }\n'
  '\n'
  '    public func previewSharingContent() -> OriginalPreviewSharing.Content? {'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '    private var sharingPicker: NSSharingServicePicker?\n'
  '    private let input: ClipboardRestoreItem?',
  '    private var sharingPicker: NSSharingServicePicker?\n'
  '    private var input: ClipboardRestoreItem?'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '        let receive: (ClipboardRestoreItem) -> Void = { [weak self, weak share] current in\n'
  '            guard let self else { return }\n'
  '            if current.isDeleted {',
  '        let receive: (ClipboardRestoreItem) -> Void = { [weak self, weak share] current in\n'
  '            guard let self else { return }\n'
  '            self.input = current\n'
  '            if current.isDeleted {'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '    private func showPinMenu(from button: NSButton) {',
  '    private func showNativePinMenu(from button: NSButton, input: ClipboardRestoreItem) {\n'
  '        guard let state else { return }\n'
  '        // 3c24a8/3c24b8 creates and reads a collection for each preview menu invocation.\n'
  '        let targets = state.store.makePinboardCollection().value\n'
  '        let menu = NSMenu()\n'
  '        for target in targets {\n'
  '            let entry = ReplicaPreviewActionMenuItem(title: target.name) { [weak self] in\n'
  '                guard let self, let state = self.state, let current = self.input else { return '
  '}\n'
  "                // 3c3590 reads the model's current item when the action runs.\n"
  '                state.perform { try state.store.assign(items: [current], to: target) }\n'
  '            }\n'
  '            entry.state = input.isAssigned(to: target) == true ? .on : .off\n'
  '            let color = target.colorCode.map { OriginalPinboardColor(canonicalColorCode: '
  '$0).color() } ?? .clear\n'
  '            entry.image = NSImage(size: NSSize(width: 12, height: 12), flipped: false) { bounds '
  'in\n'
  '                color.setFill()\n'
  '                NSBezierPath(ovalIn: bounds).fill()\n'
  '                return true\n'
  '            }\n'
  '            menu.addItem(entry)\n'
  '        }\n'
  '        menu.addItem(.separator())\n'
  '        menu.addItem(ReplicaPreviewActionMenuItem(title: '
  'OriginalSearchLocalization.text("pasto.action.create-group") + "...") { [weak self] in\n'
  '            self?.createPinboardForCurrentItem()\n'
  '        })\n'
  '        if input.previewPinboard()?.isPinned == true {\n'
  '            menu.addItem(ReplicaPreviewActionMenuItem(title: String(localized: '
  'OriginalPreviewLocalization.f_1001c4208())) { [weak self] in\n'
  '                guard let self, let state = self.state, let current = self.input else { return '
  '}\n'
  '                state.perform { try state.store.assign(items: [current], to: nil) }\n'
  '            })\n'
  '        }\n'
  '        menu.popUp(positioning: nil, at: NSPoint(x: -10, y: 0), in: button)\n'
  '    }\n'
  '\n'
  '    private func showPinMenu(from button: NSButton) {\n'
  '        if let input, input.hasNativeEntity {\n'
  '            showNativePinMenu(from: button, input: input)\n'
  '            return\n'
  '        }'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '    private func createPinboardForCurrentItem() {\n'
  '        guard let state else { return }\n'
  '        let alert = NSAlert()',
  '    private func createPinboardForCurrentItem() {\n'
  '        guard let state else { return }\n'
  '        if input?.hasNativeEntity == true {\n'
  '            state.perform {\n'
  '                let board = try state.store.createPinboard(name: String(localized: '
  'OriginalPreviewLocalization.f_1001c6aa4()))\n'
  '                guard let current = self.input else { return }\n'
  '                try state.store.assign(items: [current], to: board.id)\n'
  '            }\n'
  '            return\n'
  '        }\n'
  '        let alert = NSAlert()']]

def pre_preview_group_menu(source):
    source = pre_native_unassign(source)
    for _,old,new in reversed(CHANGES):
        if old.startswith(new) and old in source: continue
        if new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    return source

def pre_preview_group_menu_bytes(path):
    p=Path(path)
    return pre_preview_group_menu(p.read_text()).encode() if p.suffix=='.swift' else p.read_bytes()
