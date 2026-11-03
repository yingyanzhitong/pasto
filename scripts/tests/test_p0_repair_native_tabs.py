"""Native tab/collapse contracts from original C and ARM, not UI execution."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from native_list_name_color_scope_contract import pre_native_list_name_color
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment


class NativeTabsContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT/'.local/p0-repair/phase-18'
        cls.proof = json.loads((cls.phase/'tab-layout-root-contract.json').read_text())
        cls.tabs = (ROOT/'replica/Sources/Pasto/UI/OriginalPanelTabBar.swift').read_text()
        cls.cell = (ROOT/'replica/Sources/Pasto/UI/OriginalPinboardTabTitle.swift').read_text()
        cls.toolbar = (ROOT/'replica/Sources/Pasto/UI/OriginalPanelToolbar.swift').read_text()
        cls.panel = (ROOT/'replica/Sources/Pasto/UI/PanelViews.swift').read_text()

    def original(self, a):
        r = next(r for r in self.proof['original_fragments'] if r['address'] == a)
        return original_fragment((ROOT/r['path']).read_text(), a[2:])

    def test_canonical_fragments_and_inset_machine_range_are_bound(self):
        for r in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'], r['sha256'])
        raw = (ROOT/self.proof['binary']['path']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), self.proof['binary']['sha256'])
        for r in self.proof['machine_ranges']:
            data = raw[r['file_offset']:r['file_offset']+r['length']]
            self.assertEqual(hashlib.sha256(data).hexdigest(), r['sha256'])
        # fmov d4,#-17 ; movi v5.2d,#0 immediately before CGRectInset.
        self.assertEqual(raw[0x95ba0:0x95ba8].hex(), '0430761e05e4006f')

    def test_original_per_cell_state_sequence_matches_native_constraints(self):
        original = self.original('0x100095228')
        order = ['TabBarCell::isCollapsed', 'FUN_100078aa4()', 'Swift::_stdlib_isOSVersionAtLeast(0x1a,0,0)',
                 'FUN_1000789dc()', 'FUN_100078734()', 'objc_stub::setAlphaValue_']
        positions = [original.index(t) for t in order]
        self.assertEqual(positions, sorted(positions))
        collapse = body(self.cell, 'func setCollapsed(_ collapsed: Bool)')
        order = ['isCollapsed = collapsed', 'compactWidthConstraint.isActive = collapsed',
                 'labelTrailingConstraint.isActive = !collapsed', 'titleView.alphaValue = collapsed ? 0 : 1']
        positions = [collapse.index(t) for t in order]
        self.assertEqual(positions, sorted(positions))
        self.assertIn('if #available(macOS 26, *)', collapse)
        self.assertIn('else { compactWidthConstraint.isActive = false }', collapse)

    def test_constraints_target_real_cell_and_label_not_host_box(self):
        compact = self.original('0x100078aa4')
        self.assertIn('widthAnchor', compact)
        self.assertIn('heightAnchor', compact)
        self.assertIn('0x3ff0000000000000', compact)
        trailing = self.original('0x1000789dc')
        self.assertIn('0xc020000000000000', trailing)  # -8
        self.assertIn('widthAnchor.constraint(equalTo: heightAnchor, multiplier: 1)', self.cell)
        self.assertIn('titleView.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -8)', self.cell)
        self.assertIn('titleView.widthAnchor.constraint(lessThanOrEqualToConstant: 200)', self.cell)
        self.assertNotIn('historyIconView.frame =', self.cell)
        self.assertNotIn('titleView.frame =', self.cell)

    def test_same_key_keeps_native_cell_and_only_membership_reorders_stack(self):
        configure = body(self.tabs, 'private func applySnapshot(')
        self.assertIn('if fullReload || !moveSources.isEmpty', configure)
        self.assertIn('rebuildCells()', configure)
        self.assertIn('for index in keys.indices { configureCell(at: index) }', configure)
        cell = body(self.tabs, 'private func configureCell(')
        self.assertIn('configuration(target).configure(view)', cell)
        self.assertIn('view.setCollapsed(isCollapsed)', cell)
        collapse = body(self.tabs, 'private func f_100095228()')
        self.assertIn('stack.arrangedSubviews.compactMap { $0 as? OriginalPinboardTabView }', collapse)
        self.assertNotIn('OriginalPinboardTabView()', collapse)
        self.assertNotIn('rootView', self.tabs)

    def test_collapsed_path_scrolls_zero_and_returns_before_selection_dispatch(self):
        original = self.original('0x100095228')
        branch = original[original.index('LAB_1000956c0:'):]
        self.assertLess(branch.index('scrollRectToVisible_'), branch.index('TabBarCell::isSelected'))
        collapse = body(self.tabs, 'private func f_100095228()')
        branch = body(collapse, 'if isCollapsed')
        self.assertIn('_ = scrollRectToVisible(.zero)', branch)
        self.assertIn('return', branch)
        self.assertLess(collapse.index('if isCollapsed'), collapse.index('tabs.first(where:'))

    def test_expanded_dispatch_uses_weak_owner_strong_cell_and_no_extra_state_gate(self):
        collapse = body(self.tabs, 'private func f_100095228()')
        self.assertIn('guard let selected = tabs.first(where: { $0.isSelected }) else { return }', collapse)
        self.assertIn('DispatchQueue.main.async { [weak self, selected] in', collapse)
        self.assertIn('self?.f_100095ae8(selected)', collapse)
        async_body = collapse[collapse.index('DispatchQueue.main.async'):]
        self.assertNotIn('weak selected', async_body)
        self.assertNotIn('isCollapsed', async_body)
        self.assertNotIn('generation', async_body)
        self.assertNotIn('Task {', async_body)

    def test_expanded_inset_frame_read_at_execution_and_exact_animation(self):
        action = body(self.tabs, 'private func f_100095ae8(')
        order = ['cell.frame.insetBy(dx: -17, dy: 0)',
                 'OriginalViewAnimation.f_10021cadc(duration: 0.15',
                 'timingFunction: OriginalViewAnimation.f_10021ccd4()',
                 'animated: true', 'animations: { self.f_10009ac24(rect) }']
        positions = [action.index(t) for t in order]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn('completion:', action)
        self.assertIn('0x3fc3333333333333,0', self.original('0x100095ae8'))
        forwarding = body(self.tabs, 'override func scrollRectToVisible(')
        self.assertIn('scrollView.contentView.scrollRectToVisible(rect)', forwarding)
        self.assertIn('objc_stub::contentView', self.original('0x100051068'))

    def test_original_horizontal_spacing_content_inset_and_height(self):
        original = self.original('0x1000959e4')
        self.assertIn('setOrientation_(self,0)', original)
        self.assertIn('setSpacing_(self,0x4020000000000000)', original)
        self.assertIn('stack.orientation = .horizontal', self.tabs)
        self.assertIn('stack.spacing = 8', self.tabs)
        self.assertIn('height: 40', self.tabs)
        self.assertIn('field1_0x8 = 40.0', self.original('0x1000500d4'))
        self.assertIn('0x4018000000000000,0x401c000000000000,0x4018000000000000,0x401c000000000000',
                      self.original('0x100050f3c'))
        self.assertIn('NSRect(x: 7, y: 6', self.tabs)

    def test_selected_highlight_is_suppressed_during_collapse_but_hover_and_drag_remain(self):
        original = self.original('0x10007a078')
        self.assertIn('TabBarCell::isCollapsed', original)
        self.assertIn('TabBarCell::isDragDestination', original)
        draw = body(self.cell, 'override func draw(_ dirtyRect: NSRect)')
        self.assertIn('(isSelected && !isCollapsed) || isDragDestination', draw)
        self.assertIn('isHovered ? OriginalToolbarAppearance.borderAndHover()', draw)

    def test_existing_rename_and_color_actions_keep_their_state_store_consumers(self):
        before = (self.phase/'before/replica/Sources/Pasto/UI/PanelViews.swift').read_text()
        old = body(before, 'private func boardButton(')
        current = body(self.panel, 'private func boardButton(')
        for signature in ['onCommit:', 'onEnd:']:
            self.assertEqual(body(pre_native_list_name_color(current), signature), body(old, signature))
        title_before = (self.phase/'before/replica/Sources/Pasto/UI/OriginalPinboardTabTitle.swift').read_text()
        label = self.cell[self.cell.index('final class OriginalPinboardTabTitleView:'):]
        label_before = title_before[title_before.index('final class OriginalPinboardTabTitleView:'):]
        for signature in ['private func beginEditing()', 'private func cancelEditing()',
                          'private func commitEditing()', 'private func restoreInitialResponder()',
                          'func configure(title:', 'func controlTextDidChange(']:
            self.assertEqual(body(label, signature), body(label_before, signature))
        self.assertIn('view.setAccessibilityValue(isSelected)', self.cell)
        self.assertIn('override func accessibilityPerformPress()', self.cell)

    def test_native_menus_and_drag_do_not_remove_existing_local_group_operations(self):
        config = body(self.panel, 'private func boardTab(')
        for token in ['boardButton(target.name, board: board, target: target)',
                      'tab.menuProvider = { localListMenu(for: target) }', 'state.moveList(identifier: String(value.dropFirst(15)), to: target)']:
            self.assertIn(token, config)
        menu = body(self.panel, 'private func localListMenu(')
        for token in ['colorMenu.submenu = colors', 'item.image = colorMenuImage(color)',
                      'state.controller?.clearHistory()', 'state.controller?.removePinboard(target)']:
            self.assertIn(token, menu)
        self.assertIn('tab.dragString = "paste-pinboard:" + target.identifier', config)
        self.assertIn('override func menu(for event: NSEvent)', self.cell)
        self.assertIn('override func prepareForDragOperation', self.cell)
        self.assertIn('return onDropString?(value) ?? false', self.cell)
        self.assertIn('guard !titleView.isEditing, !isDragging, let dragString', self.cell)
        self.assertIn('NSDraggingItem(pasteboardWriter: writer)', self.cell)
        label = self.cell[self.cell.index('final class OriginalPinboardTabTitleView:'):]
        menu = body(label, 'override func menu(for event: NSEvent)')
        self.assertIn('field.isEditable ? super.menu(for: event) : superview?.menu(for: event)', menu)
        drag = body(label, 'override func mouseDragged(with event: NSEvent)')
        self.assertIn('if field.isEditable { super.mouseDragged(with: event) }', drag)
        self.assertIn('else { superview?.mouseDragged(with: event) }', drag)
        hit = body(label, 'override func hitTest(')
        self.assertIn('guard alphaValue > 0', hit)

    def test_live_toolbar_uses_native_stack_and_remaining_parent_contracts_stay_partial(self):
        self.assertIn('private let tabBar = OriginalPanelTabBar()', self.toolbar)
        self.assertIn('tabBar.observeLists(publisher, configuration: configuration', self.toolbar)
        self.assertIn('tabBar.setCollapsed(active)', self.toolbar)
        self.assertNotIn('OriginalPanelTabBarAdapter', self.toolbar)
        self.assertNotIn('historyControls', self.panel)
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertEqual(self.proof['new_counted_records'], [])
        self.assertIn('Paste:0x10000e74c', [r['function_id'] for r in self.proof['retained_partial_contracts']])


if __name__ == '__main__':
    unittest.main()
