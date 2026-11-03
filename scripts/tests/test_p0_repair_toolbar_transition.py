"""Toolbar transition source/data contracts; no Swift/AppKit execution."""
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from native_list_name_color_scope_contract import pre_native_list_name_color
from native_tab_list_delivery_scope_contract import pre_native_tab_list_delivery
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment


class ToolbarTransitionContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-17'
        cls.native = (ROOT / 'replica/Sources/Pasto/UI/OriginalPanelToolbar.swift').read_text()
        cls.panel = (ROOT / 'replica/Sources/Pasto/UI/PanelViews.swift').read_text()
        cls.ui = (ROOT / 'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
        cls.editor = (ROOT / 'replica/Sources/Pasto/UI/SearchEditor.swift').read_text()
        cls.animation = (ROOT / 'replica/Sources/PastoCore/OriginalViewAnimation.swift').read_text()

    def original(self, address, part):
        return original_fragment((ROOT / f'decompiled/Paste/part-{part:04d}.c').read_text(), address[2:])

    def test_original_fragment_and_action_slot_bytes_are_bound(self):
        proof = json.loads((self.phase / 'search-close-animation-proof.json').read_text())
        for r in proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / r['path'])[r['address']]['sha256'], r['sha256'])
        binary = (ROOT / proof['original_binary']['path']).read_bytes()
        self.assertEqual(hashlib.sha256(binary).hexdigest(), proof['original_binary']['sha256'])
        r = proof['machine_evidence'][0]
        raw = binary[r['file_offset']:r['file_offset'] + r['length']]
        self.assertEqual(raw.hex(), r['hex'])
        self.assertEqual(hashlib.sha256(raw).hexdigest(), r['sha256'])
        # mov x6,#0; mov x7,#0: completion slots, not action slots.
        self.assertIn(bytes.fromhex('060080d2070080d2'), raw)

    def test_original_close_deactivates_before_action_and_has_nil_completion(self):
        close = self.original('0x10000e0ec', 6)
        ordered = ['_swift_unknownObjectWeakLoadStrong()', 'deactivateConstraints_',
                   'local_38 = 0', 'FUN_10021ccd4()',
                   'FUN_10021cadc(0,1,uVar2,1,thunk_FUN_10000ec20,auStack_50,0,0)']
        positions = [close.index(t) for t in ordered]
        self.assertEqual(positions, sorted(positions))
        action = self.original('0x10000e74c', 6)
        positions = [action.index(t) for t in ['SearchBar::isActive', 'FUN_10003e350()',
            'TabBar::isCollapsed', 'FUN_100095228()', 'FUN_10000ce94()', 'setHidden_', 'layoutSubtreeIfNeeded']]
        self.assertEqual(positions, sorted(positions))

    def test_real_close_uses_existing_animation_action_not_empty_wrapper(self):
        close = body(self.native, 'private func transitionToInactive()')
        ordered = ['NSLayoutConstraint.deactivate(activeSearchConstraints)',
                   'OriginalViewAnimation.f_10021cadc(duration: nil',
                   'timingFunction: OriginalViewAnimation.f_10021ccd4()', 'animated: true',
                   'animations: { self.f_10000e74c(false) }']
        positions = [close.index(t) for t in ordered]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn('completion:', close)
        self.assertNotIn('async', close)
        action = body(self.native, 'private func f_10000e74c(_ active: Bool)')
        positions = [action.index(t) for t in ['searchBar.setActive(active)', 'tabBar.setCollapsed(active)',
                                             'createButton.isHidden = active', 'layoutSubtreeIfNeeded()']]
        self.assertEqual(positions, sorted(positions))

    def test_shared_animation_helper_preserves_optional_duration_and_immediate_path(self):
        context = body(self.animation, 'public static func f_10021cd10(')
        self.assertIn('if let duration { context.duration = duration }', context)
        positions = [context.index(t) for t in ['context.timingFunction = timingFunction',
                                               'context.allowsImplicitAnimation = true', 'animations()']]
        self.assertEqual(positions, sorted(positions))
        helper = body(self.animation, 'public static func f_10021cadc(')
        immediate = body(helper, 'if !animated')
        self.assertLess(immediate.index('animations()'), immediate.index('completion?()'))
        self.assertIn('NSAnimationContext.runAnimationGroup', helper)
        self.assertNotRegex(self.native, r'duration:\s*0\.\d+')

    def test_active_constraints_have_four_original_endpoints_and_thresholds(self):
        original = self.original('0x10000e4c8', 6)
        self.assertIn('0x4079000000000000', original)  # Double 400
        self.assertIn('0x3fd0000000000000', original)  # Double 0.25
        tail = original[original.index('FUN_10000ce94()'):]
        self.assertLess(tail.index('trailingAnchor'), tail.index('FUN_10000ce08()'))
        self.assertLess(tail.index('FUN_10000ce08()'), tail.index('constraintEqualToAnchor_'))
        constraints = body(self.native, 'private func f_10000e4c8()')
        self.assertEqual(constraints.count('.constraint('), 4)
        for token in ['searchBar.centerXAnchor.constraint(equalTo: centerXAnchor)',
                      'greaterThanOrEqualToConstant: 400', 'widthAnchor, multiplier: 0.25',
                      'createButton.trailingAnchor.constraint(equalTo: tabBar.trailingAnchor)']:
            self.assertIn(token, constraints)
        self.assertNotIn('searchBar.trailingAnchor', constraints)

    def test_activation_replaces_constraints_and_initial_configuration_does_not_animate(self):
        activate = body(self.native, 'private func f_10000df98()')
        positions = [activate.index(t) for t in ['NSLayoutConstraint.deactivate(activeSearchConstraints)',
            'activeSearchConstraints = f_10000e4c8()', 'NSLayoutConstraint.activate(activeSearchConstraints)',
            'OriginalViewAnimation.f_10021cadc', 'self.f_10000e74c(true)']]
        self.assertEqual(positions, sorted(positions))
        configure = body(self.native, 'func configure(searchButton: AnyView')
        initial = body(configure, 'if !configured')
        self.assertIn('animated: false', initial)
        self.assertIn('self.f_10000e74c(active)', initial)
        self.assertIn('else if searchBar.isActive != active', configure)

    def test_default_priorities_are_not_fabricated_width_constraints(self):
        original = self.original('0x10000d884', 5)
        self.assertIn('FUN_1001f9678(0x437a0000)', original)
        self.assertIn('FUN_1001f9678(0x443b8000)', original)
        self.assertIn('centeredTabs.priority = NSLayoutConstraint.Priority(250)', self.native)
        self.assertIn('createLeading.priority = NSLayoutConstraint.Priority(750)', self.native)
        self.assertNotIn('greaterThanOrEqualToConstant: 250', self.native)
        self.assertIn('constant: -menuGap', self.native)
        self.assertIn('if #available(macOS 26, *) { menuGap = 8 } else { menuGap = 16 }', self.native)

    def test_search_intrinsic_forwards_button_and_only_menu_is_fixed_44(self):
        original = self.original('0x10003ed28', 23)
        self.assertIn('FUN_10003e4c0()', original)
        self.assertIn('intrinsicContentSize', original)
        self.assertIn('override var intrinsicContentSize: NSSize { button.fittingSize }', self.native)
        self.assertIn('heightAnchor.constraint(equalTo: button.heightAnchor)', self.native)
        self.assertNotIn('createButton.widthAnchor', self.native)
        self.assertNotIn('createButton.heightAnchor', self.native)
        self.assertIn('menuButton.widthAnchor.constraint(equalToConstant: 44)', self.native)
        self.assertIn('menuButton.heightAnchor.constraint(equalToConstant: 44)', self.native)

    def test_closed_timer_and_escape_reach_native_owner_after_clearing_query(self):
        for signature, prefix in [('private func beginClosedState()', 'self.'),
                                  ('func cancelSearchOrPanel()', '')]:
            consumer = body(self.ui, signature)
            clear = consumer.index(prefix + 'state.applySearchInput(nodes: [], text: "", filters: [])')
            native = consumer.index(prefix + 'state.toolbarOwner?.f_10000e0ec()')
            fallback = consumer.index(prefix + 'state.searchVisible = false', native)
            self.assertLess(clear, native)
            self.assertLess(native, fallback)
        before = (self.phase / 'before/replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
        old = body(before, 'private func beginClosedState()')
        self.assertNotIn('toolbarOwner?.f_10000e0ec()', old)
        self.assertIn('self.state.searchVisible = false', old)

    def test_owner_is_weak_and_dismantle_does_not_remove_replacement_owner(self):
        self.assertIn('weak var toolbarOwner: OriginalPanelToolbarView?', self.ui)
        self.assertIn('weak var state: ReplicaUIState?', self.native)
        make = body(self.native, 'func makeNSView(context: Context)')
        self.assertIn('state.toolbarOwner = view', make)
        dismantle = body(self.native, 'static func dismantleNSView(')
        self.assertIn('if coordinator.state?.toolbarOwner === view', dismantle)
        self.assertIn('view.onDismiss = nil', dismantle)

    def test_persistent_search_editor_cannot_request_focus_while_inactive(self):
        visuals = body(self.native, 'private func f_10003e350()')
        for token in ['button.alphaValue = isActive ? 0 : 1', 'fieldHost.alphaValue = isActive ? 1 : 0',
                      'field.canAcceptFocus = isActive', 'f_100041f9c().canAcceptFocus = field.canAcceptFocus']:
            self.assertIn(token, visuals)
        action = body(self.native, 'private func f_100040054()')
        active = body(action, 'if isActive')
        self.assertIn('guard isFilterPopoverDisplayed?() != true else { return }', active)
        self.assertIn('if let window { window.makeFirstResponder(editor) }', active)
        update = body(self.editor, 'func updateField(')
        self.assertNotIn('makeFirstResponder', update)
        self.assertNotIn('requestedFocus', self.editor)

    def test_native_reset_preserves_duplicate_query_delivery_without_equal_swiftui_writes(self):
        reset = body(self.editor, 'func clearInput(preserveHistory:')
        positions = [reset.index(t) for t in ['applyProgrammaticQuery([], field: field, editor: editor)',
                                            'if !preserveHistory { history.f_1002f6550() }']]
        self.assertEqual(positions, sorted(positions))
        action = body(self.native, 'private func f_100040054()')
        positions = [action.index(t) for t in ['coordinator.clearInput(preserveHistory: false',
            'coordinator.publishCurrentQuery()', 'window?.makeFirstResponder(nil)']]
        self.assertEqual(positions, sorted(positions))
        delivery = body(self.ui, 'func publishSearchInputFromEditor(')
        equal = body(delivery, 'if query == text, searchFilters == filters, searchQueryNodes == nodes')
        self.assertIn('searchInputChanged()', equal)
        self.assertNotIn('query =', equal)
        self.assertNotIn('searchFilters =', equal)

    def test_panel_uses_one_native_header_and_keeps_existing_group_actions(self):
        header = body(self.panel, 'private var header: some View')
        self.assertIn('OriginalPanelToolbar(state: state', header)
        self.assertNotIn('if searching', header)
        self.assertNotIn('GeometryReader', header)
        self.assertNotIn('let tabsWidth', header)
        for token in ['tabConfiguration: boardTab',
                      'createButton: AnyView(createPinboardButton)', 'menuButton: AnyView(trailingControls)']:
            self.assertIn(token, header)
        before = (self.phase / 'before/replica/Sources/Pasto/UI/PanelViews.swift').read_text()
        # Phase18 retains native cells instead of swapping two SwiftUI roots.
        # Preserve the business callbacks while verifying the new live consumer.
        old_button = body(before, 'private func boardButton(')
        new_button = body(self.panel, 'private func boardButton(')
        for signature in ['onCommit:', 'onEnd:']:
            self.assertEqual(body(pre_native_list_name_color(new_button), signature), body(old_button, signature))
        for signature in ['private func colorName(', 'private func colorMenuImage(', 'private func requestTabRename(']:
            self.assertEqual(body(pre_native_tab_list_delivery(self.panel), signature), body(before, signature))
        new_tabs = body(self.panel, 'private func boardTab(')
        self.assertIn('boardButton(target.name, board: board, target: target)', new_tabs)
        self.assertIn('tab.menuProvider = { localListMenu(for: target) }', new_tabs)
        self.assertIn('state.moveList(identifier: String(value.dropFirst(15)), to: target)', new_tabs)
        menu = body(self.panel, 'private func localListMenu(')
        for token in ['state.controller?.clearHistory()', 'requestTabRename(target)',
                      'state.store.updateListColor(target,', 'state.controller?.removePinboard(target)']:
            self.assertIn(token, menu)
        self.assertNotIn('state.movePinboard(board, by:', menu)

    def test_tab_cell_and_query_reset_contracts_are_not_falsely_marked_complete(self):
        self.assertIn('not claim the complete original toolbar', self.native)
        tabs = (ROOT / 'replica/Sources/Pasto/UI/OriginalPanelTabBar.swift').read_text()
        self.assertIn('shadow-overlay drawing is still a separate incomplete contract', tabs)
        proof = json.loads((ROOT / '.local/p0-repair/phase-18/tab-layout-root-contract.json').read_text())
        self.assertFalse(proof['full_function_migration_verified'])
        self.assertIn('Paste:0x100040054', [r['function_id'] for r in proof['retained_partial_contracts']])


if __name__ == '__main__':
    unittest.main()
