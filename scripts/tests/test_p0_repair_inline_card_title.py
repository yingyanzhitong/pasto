"""Original inline-title state transitions and actual panel/card wiring, source-only."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from card_title_input_scope_contract import pre_card_title_input


class InlineCardTitle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.core = (ROOT / 'replica/Sources/PastoCore/OriginalItemTitleLabel.swift').read_text()
        cls.view = (ROOT / 'replica/Sources/Pasto/UI/ReplicaCardTitle.swift').read_text()
        cls.ui = (ROOT / 'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
        cls.native = (ROOT / 'replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift').read_text()
        cls.panel = pre_card_title_input((ROOT / 'replica/Sources/Pasto/UI/PanelViews.swift').read_text())

    def test_original_transitions_and_routing_fragments_are_still_bound(self):
        proof = json.loads((ROOT / '.local/p0-repair/phase-9/title-edit-contract.json').read_text())
        for ref in proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / ref['path'])[ref['id'].split(':')[1]]['sha256'], ref['sha256'])
        proof = json.loads((ROOT / '.local/p0-repair/phase-9/rename-key-routing.json').read_text())['record']
        refs = [dict(proof['original'], function_id=proof['function_id'])] + proof['supporting_original_fragments']
        for ref in refs:
            address = ref['function_id'].split(':')[1].split('/')[0]
            self.assertEqual(source_fragments(ROOT / ref['path'])[address]['sha256'], ref['sha256'])

    def test_begin_snapshots_the_field_then_enables_and_queues_weak_current_window_focus(self):
        begin = body(self.core, 'public func f_1003d2488()')
        order = ['originalText = field.f_10023b1a4()', 'field.f_10023b414(true)', 'DispatchQueue.main.async']
        self.assertEqual([begin.index(t) for t in order], sorted(begin.index(t) for t in order))
        self.assertNotIn('makeFirstResponder', begin[:begin.index('DispatchQueue.main.async')])
        callback = body(begin, 'DispatchQueue.main.async')
        self.assertIn('[weak self]', callback)
        self.assertIn('let field = self.f_1003d1cc0()', callback)
        self.assertIn('field.window?.makeFirstResponder(field)', callback)
        self.assertNotIn('selectText', begin)

    def test_cancel_preserves_native_restore_abort_queue_order_without_direct_commit(self):
        cancel = body(self.core, 'public func f_1003d2838()')
        order = ['field.f_10023b414(false)', 'field.f_10023b214(originalText)',
                 'field.f_10023bfdc()', 'enqueueFocusClear()']
        self.assertEqual([cancel.index(t) for t in order], sorted(cancel.index(t) for t in order))
        self.assertNotIn('onCommitEditing', cancel)
        self.assertNotIn('makeFirstResponder', cancel)
        self.assertIn('f_1003d2838()', body(self.core, 'public override func cancelOperation('))

    def test_commit_disables_then_enqueues_clear_before_synchronous_callback(self):
        commit = body(self.core, 'public func f_1003d1dbc()')
        order = ['field.f_10023b414(false)', 'enqueueFocusClear()', 'onCommitEditing(field.f_10023b1a4() ?? "")']
        self.assertEqual([commit.index(t) for t in order], sorted(commit.index(t) for t in order))
        self.assertNotIn('DispatchQueue', commit)
        self.assertNotIn('makeFirstResponder', commit)
        clear = body(self.core, 'private func enqueueFocusClear()')
        self.assertIn('DispatchQueue.main.async { [weak self]', clear)
        self.assertIn('self?.f_1003d1cc0().window?.makeFirstResponder(nil)', clear)

    def test_platform_field_delegate_and_cancel_selector_have_real_consumers(self):
        field = body(self.core, 'public func f_1003d1cc0()')
        self.assertIn('field.onDidEndEditing = { [weak self] in self?.f_1003d1dbc() }', field)
        self.assertIn('field.f_10023adf0().delegate = self', field)
        end = body(self.core, 'public func controlTextDidEndEditing(')
        self.assertIn('f_1003d1cc0().controlTextDidEndEditing(obj)', end)
        command = body(self.core, 'public func control(_ control: NSControl,')
        self.assertIn('guard commandSelector == #selector(NSResponder.cancelOperation(_:)) else { return false }', command)
        self.assertIn('cancelOperation(nil)', command)
        self.assertNotIn('insertNewline', command)
        self.assertIn('label.mouseDown(with: event)', body(self.view, 'override func mouseDown('))

    def test_command_r_returns_false_for_empty_and_true_for_missing_last_visible_target(self):
        rename = body(self.native, 'func renameSelection(state: ReplicaUIState)')
        self.assertIn('self.state === state, state.collectionOwner === self', rename)
        self.assertIn('orderedIDs.last else { return false }', rename)
        self.assertIn('let cell = cells[index], cell.itemID == id else { return true }', rename)
        self.assertLess(rename.index('state.selectAppliedItem(at: index, items: items)'),
                        rename.index('cell.beginTitleEditing()'))
        self.assertNotIn('visibleItems', rename)
        self.assertNotIn('drainCollectionSnapshots()', rename)
        self.assertNotIn('NSSound', rename)
        self.assertNotIn('first {', rename)
        self.assertIn('selectIndex(index, mode: 0, items: items)', body(self.ui, 'func selectAppliedItem(at index:'))

    def test_r_route_is_exact_command_owner_gated_and_does_not_invoke_modal_rename(self):
        handle = body(self.ui, 'private func handleKey(_ event: NSEvent) -> Bool')
        signature = 'if !isEditing, signature.keyCode == OriginalShortcutFunctions.f_1001e94d4("r")'
        self.assertLess(handle.index('if !ownsCollectionFocus'), handle.index(signature))
        branch = body(handle, signature)
        self.assertIn('return collection.renameSelection(state: state)', branch)
        self.assertNotIn('renameItem(', branch)
        self.assertNotIn('prompt(', branch)
        self.assertNotIn('state.selectedItems', branch)

    def test_native_card_header_mounts_matching_title_and_preserves_hit_testing(self):
        labels = body(self.panel, 'private var headerLabels: some View')
        native = body(labels, 'if nativeInteractions')
        self.assertIn('ReplicaCardTitle(state: state, itemID: item.id, title: cardTitle', native)
        self.assertIn('font: headerTitleFont, textColor: NSColor(headerPrimaryColor)', native)
        lookup = body(self.native, 'func beginTitleEditing()')
        self.assertIn('var views = hosting.subviews', lookup)
        self.assertIn('title.itemID == item.id', lookup)
        self.assertIn('title.beginEditing()', lookup)
        self.assertIn('if view is ReplicaCardTitleView { return result }', self.native)

    def test_title_commit_reaches_current_item_persistence_and_model_updates_do_not_replace_unchanged_draft(self):
        configure = body(self.view, 'func configure(state: ReplicaUIState, itemID: UUID,')
        self.assertIn('label.onCommitEditing = { [weak state] title in', configure)
        self.assertIn('state.store.updateItem(id: itemID, title: title, text: nil)', configure)
        incoming = body(configure, 'if lastModelTitle != title')
        self.assertIn('lastModelTitle = title', incoming)
        self.assertIn('field.f_10023b214(title)', incoming)
        self.assertNotIn('originalText', configure)
        self.assertNotIn('onCommitEditing(', incoming)
        self.assertIn('label.isEditable = true', configure)

    def test_escape_bypass_is_editor_owned_and_does_not_remove_configured_numeric_exception(self):
        send = body(self.ui, 'override func sendEvent(_ event: NSEvent)')
        signature = 'if event.type == .keyDown, event.keyCode == 53,'
        branch = body(send, signature)
        self.assertIn('cardTitleEditingOwner?.ownsEditor(in: self) == true', send)
        self.assertIn('super.sendEvent(event)', branch)
        self.assertIn('return', branch)
        self.assertLess(send.index(signature), send.index('keyHandler?(event)'))
        handle = body(self.ui, 'private func handleKey(_ event: NSEvent) -> Bool')
        non_owner = body(handle, 'if !ownsCollectionFocus')
        self.assertIn('performQuickPaste(quickPasteAction)', non_owner)
        owner = body(self.view, 'func ownsEditor(in panel: ReplicaPanel)')
        self.assertIn('window === panel && label.isEditing', owner)
        self.assertIn('field.currentEditor() === panel.firstResponder', owner)


if __name__ == '__main__':
    unittest.main()
