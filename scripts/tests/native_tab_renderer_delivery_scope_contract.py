"""Reverse exactly phase170 renderer delivery/drag completion hunks for historical audits."""
CHANGES = [['replica/Sources/Pasto/UI/OriginalPanelTabBar.swift',
  '        let newKeys = tabs.map(\\.key)\n'
  '        let retainedKeys = Set(newKeys)\n'
  '        for key in keys where !retainedKeys.contains(key) {',
  '        let newKeys = tabs.map(\\.key)\n'
  '        let previousKeys = keys\n'
  '        // 097eb0 invokes the applier array setter before configuring any native cell.\n'
  '        keys = newKeys\n'
  '        let retainedKeys = Set(newKeys)\n'
  '        for key in previousKeys where !retainedKeys.contains(key) {',
  1],
 ['replica/Sources/Pasto/UI/OriginalPanelTabBar.swift',
  '        if keys != newKeys {\n'
  '            stack.setViews(newKeys.compactMap { cells[$0] }, in: .leading)\n'
  '            keys = newKeys\n'
  '        }',
  '        if previousKeys != newKeys {\n'
  '            stack.setViews(newKeys.compactMap { cells[$0] }, in: .leading)\n'
  '        }',
  1],
 ['replica/Sources/Pasto/UI/OriginalPanelTabBar.swift',
  '        // Existing NSStackView renderer adapter; 0973d8 rebuilds cells after its applier move.\n'
  '        stack.setViews(keys.compactMap { cells[$0] }, in: .leading)\n'
  '        invalidateIntrinsicContentSize()\n'
  '        needsLayout = true\n'
  '        isPerformingLocalMutation = false\n'
  '        scheduleSnapshotDrain()\n'
  '        return true',
  '        isPerformingLocalMutation = false\n'
  '        scheduleSnapshotDrain()\n'
  '        // 0973d8 rebuilds/layouts after 1b91e4 unlocks; retain the existing stack renderer adapter.\n'
  '        stack.setViews(keys.compactMap { cells[$0] }, in: .leading)\n'
  '        invalidateIntrinsicContentSize()\n'
  '        needsLayout = true\n'
  '        layoutSubtreeIfNeeded()\n'
  '        if let cell = cells[keys[destinationIndex]], cell.isSelected {\n'
  '            f_100095ae8(cell)\n'
  '        }\n'
  '        return true',
  1]]

def pre_native_tab_renderer_delivery(source):
    from native_tab_source_renderer_scope_contract import pre_native_tab_source_renderer
    source = pre_native_tab_source_renderer(source)
    for _,old,new,count in reversed(CHANGES):
        if new in source:
            assert source.count(new)==count
            source=source.replace(new,old)
    return source
