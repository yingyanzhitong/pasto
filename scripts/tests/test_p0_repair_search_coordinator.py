"""Original/native query action contracts; no Swift/AppKit or Undo execution."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment


class SearchCoordinatorContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-19'
        cls.proof=json.loads((cls.phase/'search-root-contract.json').read_text())
        cls.native=(ROOT/'replica/Sources/Pasto/UI/OriginalPanelToolbar.swift').read_text()
        cls.editor=(ROOT/'replica/Sources/Pasto/UI/SearchEditor.swift').read_text()
        cls.ui=(ROOT/'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
        cls.panel=(ROOT/'replica/Sources/Pasto/UI/PanelViews.swift').read_text()
        cls.field=(ROOT/'replica/Sources/PastoCore/OriginalSearchField.swift').read_text()

    def original(self,a):
        r=next(r for r in self.proof['original_fragments'] if r['address']==a)
        return original_fragment((ROOT/r['path']).read_text(),a[2:])

    def test_original_fragments_and_reset_mode_machine_ranges_are_bound(self):
        for r in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        raw=(ROOT/self.proof['binary']['path']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),self.proof['binary']['sha256'])
        for r in self.proof['machine_ranges']:
            data=raw[r['file_offset']:r['file_offset']+r['length']]
            self.assertEqual(hashlib.sha256(data).hexdigest(),r['sha256'])
        self.assertEqual(raw[0x40ca0:0x40ca4].hex(),'20008052')  # w0=1
        self.assertEqual(raw[0x2f7d94:0x2f7d98].hex(),'93000036')  # mode0 continues reset
        self.assertEqual(raw[0x2f7868:0x2f786c].hex(),'23008052')  # immediate=true

    def test_native_field_and_coordinator_are_synchronously_retained_before_actions(self):
        configure=body(self.native,'func configure(button: AnyView, field specification:')
        positions=[configure.index(t) for t in ['ReplicaSearchEditor.Coordinator(specification)',
            'specification.makeField(coordinator: coordinator)','self.coordinator = coordinator',
            'self.field = field','fieldHost.addSubview(field)']]
        self.assertEqual(positions,sorted(positions))
        self.assertIn('if let field, let coordinator',configure)
        self.assertIn('specification.updateField(field, coordinator: coordinator)',configure)
        toolbar=body(self.native,'func configure(searchButton:')
        self.assertLess(toolbar.index('searchBar.configure('),toolbar.index('self.f_10000e74c(active)'))
        self.assertNotIn('NSViewRepresentable',self.editor)
        self.assertNotIn('updateFocusPermission(in:',self.native)

    def test_visual_focus_permissions_precede_nested_original_animation_action(self):
        original=self.original('0x10003e350')
        self.assertLess(original.index('setAlphaValue_'),original.index('SearchField::canAcceptFocus'))
        self.assertLess(original.index('SearchField::canAcceptFocus'),original.index('FUN_10021cadc'))
        self.assertIn('FUN_10021cadc(0,1,uVar5,1,FUN_100041b88,auStack_70,0,0)',original)
        action=body(self.native,'private func f_10003e350()')
        positions=[action.index(t) for t in ['button.alphaValue = isActive ? 0 : 1',
            'fieldHost.alphaValue = isActive ? 1 : 0','field.canAcceptFocus = isActive',
            'f_100041f9c().canAcceptFocus = field.canAcceptFocus','duration: nil','animated: true',
            'animations: { self.f_100040054() }']]
        self.assertEqual(positions,sorted(positions))
        self.assertNotIn('completion:',action)

    def test_active_popover_and_window_branches_only_request_focus(self):
        original=self.original('0x100040054')
        active=body(original,"if (param_1[_TtC5Paste9SearchBar::isActive] == (code)0x1)")
        self.assertIn('FilterBrowserPopover::isDisplayed',active)
        self.assertIn('if (self != 0)',active)
        self.assertIn('makeFirstResponder_',active)
        action=body(self.native,'private func f_100040054()')
        active=body(action,'if isActive')
        self.assertIn('guard isFilterPopoverDisplayed?() != true else { return }',active)
        self.assertIn('if let window { window.makeFirstResponder(editor) }',active)
        self.assertNotIn('clearInput(',active)
        self.assertNotIn('isActive = false',active)
        self.assertIn('[weak state = state]',self.native)
        self.assertIn('state?.controller?.filterBrowserPopover?.isDisplayed == true',self.native)

    def test_inactive_reset_then_extra_publication_then_resign_matches_original_order(self):
        original=self.original('0x100040054')
        order=['FUN_1002f7d60(0)','Combine::Published::_set_subscript','SearchBar::onResignKey']
        self.assertEqual([original.index(t) for t in order],sorted(original.index(t) for t in order))
        action=body(self.native,'private func f_100040054()')
        order=['coordinator.clearInput(preserveHistory: false','coordinator.publishCurrentQuery()',
               'window?.makeFirstResponder(nil)']
        self.assertEqual([action.index(t) for t in order],sorted(action.index(t) for t in order))
        self.assertNotIn('dismissing',action)
        self.assertIn('preconditionFailure("Search input coordinator is not installed")',self.native)

    def test_field_false_flag_is_preserved_and_bridge_selects_clear_mode1(self):
        self.assertIn('(*pcVar1)(0)',self.original('0x100045e54'))
        self.assertIn('FUN_1002f7d60(1)',self.original('0x100040c64'))
        self.assertIn('public func f_100045e54() { onClear?(false) }',self.field)
        factory=body(self.editor,'func makeField(coordinator:')
        clear=factory[factory.index('field.onClear ='):factory.index('field.onShowFilters =')]
        self.assertIn('] _ in',clear)
        self.assertIn('coordinator.clearInput(preserveHistory: true, field: field, editor: editor)',clear)
        before=(self.phase/'before/replica/Sources/Pasto/UI/SearchEditor.swift').read_text()
        self.assertIn('coordinator.clearInput(preserveHistory: preserveHistory, field: field, editor: editor)',before)

    def test_reset_keeps_original_equal_query_and_mode_dependent_history_branches(self):
        original=self.original('0x1002f7d60')
        order=['FUN_1002f7744(DAT_101057918,0)','if ((param_1 & 1) != 0)','FUN_1002f6550()']
        self.assertEqual([original.index(t) for t in order],sorted(original.index(t) for t in order))
        clear=body(self.editor,'func clearInput(preserveHistory:')
        self.assertLess(clear.index('applyProgrammaticQuery([]'),clear.index('if !preserveHistory'))
        self.assertIn('if !preserveHistory { history.f_1002f6550() }',clear)
        apply=body(self.editor,'private func replaceQuery(')
        self.assertIn('guard normalized != currentNodes else { return }',apply)
        self.assertLess(apply.index('guard normalized != currentNodes'),apply.index('history.f_1002f5e18'))
        self.assertNotIn('dismissSuggestions()',apply[:apply.index('guard normalized != currentNodes')])

    def test_programmatic_mode0_internal_history_editor_publish_suggestions_order(self):
        original=self.original('0x1002f7744')
        order=['*(ulong *)(unaff_x20 + 0x10) = uVar1','FUN_1002f5e18()',
               '(unaff_x20 + 0x28)', '(unaff_x20 + 0x18)', '(unaff_x20 + 0x38)']
        self.assertEqual([original.index(t) for t in order],sorted(original.index(t) for t in order))
        apply=body(self.editor,'private func replaceQuery(')
        order=['currentNodes = normalized','attributedString(normalized','history.f_1002f5e18(',
               'display(rendered, selection: selection','publishCurrentQuery()','dismissSuggestions()']
        self.assertEqual([apply.index(t) for t in order],sorted(apply.index(t) for t in order))
        self.assertIn('immediate: true',apply)
        programmatic=body(self.editor,'func applyProgrammaticQuery(')
        self.assertIn('suggestionsEnabled: false',programmatic)

    def test_filter_browser_real_consumer_reaches_native_coordinator_before_state(self):
        browser=(ROOT/'replica/Sources/Pasto/UI/FilterBrowser.swift').read_text()
        self.assertIn('model.toggleSearchFilter(selection)',browser)
        model=body(browser,'private final class ReplicaFilterBrowserModel:')
        toggle=body(model,'func toggleSearchFilter(')
        self.assertLess(toggle.index('query = nodes'),toggle.index('onQueryChanged(query)'))
        opening=body(browser,'func showFilterBrowser(')
        self.assertIn('[weak searchBar] query in searchBar?.applySearchQuery(query)',opening)
        self.assertNotIn('toolbarOwner',opening)
        native=self.native[self.native.index('final class OriginalPanelSearchBar:'):]
        entry=body(native,'func applySearchQuery(')
        self.assertIn('coordinator.applyProgrammaticQuery(nodes, field: field, editor: editor)',entry)
        self.assertIn('FUN_1002f7744(param_1,0)',self.original('0x100041860'))

    def test_duplicate_empty_queries_still_reach_real_subject_without_equal_view_writes(self):
        delivery=body(self.ui,'func publishSearchInputFromEditor(')
        equal=body(delivery,'if query == text, searchFilters == filters, searchQueryNodes == nodes')
        self.assertIn('searchInputChanged()',equal)
        self.assertNotIn('query =',equal)
        changed=body(self.ui,'private func searchInputChanged()')
        self.assertIn('searchQueryChanges.send(searchQueryNodes)',changed)
        publish=body(self.editor,'func publishCurrentQuery()')
        self.assertIn('parent.onInputChange(text, renderedFilters, currentNodes)',publish)
        self.assertNotIn('guard',publish[:publish.index('let text')])
        self.assertIn('state.publishSearchInputFromEditor(nodes: nodes, text: text, filters: filters)',self.panel)

    def test_old_focus_state_wrapper_removed_and_native_focus_retry_has_same_gate(self):
        self.assertNotIn('searchFocused',self.panel)
        self.assertNotIn('@Binding',self.editor)
        self.assertNotIn('requestedFocus',self.editor)
        self.assertNotIn('makeFirstResponder',body(self.editor,'func updateField('))
        self.assertIn('focusRequest: state.searchFocus',self.native)
        self.assertIn('else if active, focusChanged',self.native)
        request=body(self.native,'func requestFocus()')
        self.assertIn('if isActive { f_100040054() }',request)
        self.assertIn('view.searchBar.dismantleEditor()',self.native)

    def test_model_query_sink_filters_empty_before_synchronous_coordinator_delivery(self):
        original=self.original('0x10003e9bc')
        self.assertLess(original.index('Combine::Publisher::_filter()'),original.index('Combine::Publisher::_sink()'))
        predicate=self.original('0x10003fe8c')
        self.assertIn('FUN_1002ddcf0(uVar6)',predicate)
        self.assertIn('^ 0xffffffff',predicate)
        subscriber=self.original('0x10003ff40')
        self.assertLess(subscriber.index('FUN_10003e658()'),subscriber.index('FUN_1002f7744(uVar8,1)'))
        observe=body(self.native,'func observeQuery(')
        order=['publisher.prepend(initial)', '.filter { !OriginalSearchQuery.f_1002ddcf0($0) }',
               '.sink', 'self.f_10003e658()', 'coordinator.synchronizeQuery(nodes']
        self.assertEqual([observe.index(t) for t in order],sorted(observe.index(t) for t in order))
        self.assertNotIn('receive(on:',observe)
        self.assertNotIn('async',observe)
        self.assertNotIn('debounce',observe)
        synchronize=body(self.editor,'func synchronizeQuery(')
        self.assertIn('suggestionsEnabled: true',synchronize)
        bridge=body(self.native,'private func f_10003e658()')
        self.assertIn('guard isActive else { onActivate?(); return }',bridge)
        self.assertIn('if coordinator.isQueryEmpty { onDismiss?() }',bridge)
        self.assertIn('else { requestFocus() }',bridge)
        self.assertIn('queryObservation?.cancel()',self.native)

    def test_toolbar_action_real_child_order_and_scope_not_all_function_claim(self):
        action=body(self.native,'private func f_10000e74c(')
        order=['searchBar.setActive(active)','tabBar.setCollapsed(active)',
               'createButton.isHidden = active','layoutSubtreeIfNeeded()']
        self.assertEqual([action.index(t) for t in order],sorted(action.index(t) for t in order))
        self.assertEqual(len(self.proof['contracts']),4)
        self.assertTrue(all(not r['full_function_migration_verified'] for r in self.proof['contracts']))
        self.assertIn('Paste:0x1002f7744',[r['function_id'] for r in self.proof['retained_partial_contracts']])


if __name__=='__main__':unittest.main()
