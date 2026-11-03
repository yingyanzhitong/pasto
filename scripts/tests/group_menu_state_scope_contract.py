"""Reverse only two reviewed142 group-menu mixed state/icon hunks."""
CHANGES = [['replica/Sources/Pasto/UI/PanelViews.swift',
  '    @ViewBuilder private var contextMenu: some View {\n',
  '    // 09e8a8 snapshots off/on/mixed; the single writable source keeps each click one batch '
  'action.\n'
  '    private func pinboardMenuBindings(for target: ClipboardPinboardTarget,\n'
  '                                      items: [ClipboardRestoreItem]) -> [Binding<Bool>] {\n'
  '        let matched = items.filter { input in\n'
  '            input.isAssigned(to: target)\n'
  '                ?? (state.store.pinboardOwner(for: input.resolvedItem())?.id == target.id)\n'
  '        }.count\n'
  '        let assignment = Binding<Bool>(get: { matched == items.count },\n'
  '            set: { _ in state.assignItems(items, to: target) })\n'
  '        if matched > 0, matched < items.count { return [assignment, .constant(true)] }\n'
  '        return [assignment]\n'
  '    }\n'
  '\n'
  '    @ViewBuilder private var contextMenu: some View {\n'],
 ['replica/Sources/Pasto/UI/PanelViews.swift',
  '                ForEach(state.pinboardMenuTargets(), id: \\.id) { target in\n'
  '                    Button(target.name) { state.assignItems(groupItems, to: target) }\n'
  '                }\n',
  '                ForEach(state.pinboardMenuTargets(), id: \\.id) { target in\n'
  '                    Toggle(sources: pinboardMenuBindings(for: target, items: groupItems), isOn: '
  '\\.self) {\n'
  '                        Label {\n'
  '                            Text(target.name)\n'
  '                        } icon: {\n'
  '                            let color = target.colorCode.map { '
  'OriginalPinboardColor(canonicalColorCode: $0).color() } ?? .clear\n'
  '                            Image(nsImage: OriginalPinboardHeaderIcon.image(height: 12, shared: '
  'false, color: color))\n'
  '                        }\n'
  '                    }\n'
  '                }\n']]

def pre_group_menu_state(source):
    from collection_membership_cache_scope_contract import pre_collection_membership_cache
    source=pre_collection_membership_cache(source)
    for _,old,new in reversed(CHANGES):
        if new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    return source

def pre_group_menu_state_bytes(path):
    data=path.read_bytes()
    return pre_group_menu_state(data.decode()).encode()if path.suffix==".swift"else data
