"""Cmd+E source contracts against original fragments and static Mach-O data."""
import hashlib
from edit_entity_input_scope_contract import pre_edit_entity_input
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body


class EditRouterContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ui = pre_edit_entity_input((ROOT / 'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text())
        cls.transition = (ROOT / 'replica/Sources/PastoCore/OriginalPreviewWindowTransition.swift').read_text()
        cls.preview = (ROOT / 'replica/Sources/PastoCore/OriginalItemPreviewView.swift').read_text()
        cls.content = (ROOT / 'replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift').read_text()
        cls.handle = body(cls.ui, 'private func handleKey(_ event: NSEvent) -> Bool')
        cls.route = body(cls.ui, 'private func presentEditingPreview(item: ClipboardItem)')

    def test_original_fragments_and_prior_production_router_binding(self):
        proof = json.loads((ROOT / '.local/p0-repair/phase-11/editor-root-contract.json').read_text())
        for record in proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / record['path'])[record['address']]['sha256'],
                             record['sha256'], record['address'])
        prior = proof['prior_router_proof']
        self.assertEqual(hashlib.sha256((ROOT / prior['path']).read_bytes()).hexdigest(), prior['sha256'])

    def test_original_allowlist_is_image_color_link_text(self):
        proof = json.loads((ROOT / '.local/p0-repair/phase-11/editor-root-contract.json').read_text())
        binary = (ROOT / '.local/paste-arm64-static.bin').read_bytes()
        record = proof['type_allowlist']
        self.assertEqual(hashlib.sha256(binary).hexdigest(), record['binary_sha256'])
        self.assertEqual(list(binary[record['file_offset']:record['file_offset'] + 4]), [1, 2, 4, 5])
        classification = (ROOT / 'replica/Sources/PastoCore/OriginalPasteboardClassification.swift').read_text()
        self.assertIn('case unknown = 0, image = 1, color = 2, files = 3, link = 4, text = 5', classification)
        eligibility = body(self.ui, 'private static func allowsContentEditing(_ item: ClipboardItem)')
        self.assertIn('case .image, .color, .link, .text, .richText: return true', eligibility)
        self.assertIn('case .files, .unknown: return false', eligibility)

    def test_command_e_is_exact_owner_gated_and_consumes_empty_selection(self):
        signature = ('if !isEditing, signature.keyCode == OriginalShortcutFunctions.f_1001e94d4("e"),\n'
                     '           signature.modifierRawValue == NSEvent.ModifierFlags.command.rawValue')
        edit = body(self.handle, signature)
        self.assertIn('signature.modifierRawValue == NSEvent.ModifierFlags.command.rawValue',
                      self.handle[self.handle.index(signature):self.handle.index(signature) + 220])
        self.assertIn('editItems(appliedSelectionItems())', edit)
        self.assertIn('return true', edit)
        self.assertLess(self.handle.index('if !ownsCollectionFocus'), self.handle.index(signature))

    def test_selection_comes_from_applied_items_in_order_with_missing_ids_omitted(self):
        selection = body(self.ui, 'private func appliedSelectionItems()')
        self.assertIn('collection.appliedSelectedItems(for: state,', selection)
        self.assertIn('orderedIDs: state.collectionSelectionSnapshot().orderedIDs', selection)
        self.assertNotIn('visibleItems', selection)
        self.assertNotIn('store.items', selection)

    def test_filter_finishes_before_any_route_and_empty_result_beeps(self):
        edit = body(self.ui, 'private func editItems(_ items: [ClipboardItem])')
        order = ['let editable = items.filter(Self.allowsContentEditing)',
                 'guard !editable.isEmpty else { NSSound.beep(); return }',
                 'for item in editable { presentEditingPreview(item: item) }']
        positions = [edit.index(t) for t in order]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn('Set(', edit)
        self.assertNotIn('state.selectedItems', edit)

    def test_registry_precedes_view_creation_and_edit_start_and_presentation(self):
        order = ['let window = OriginalPreviewWindow()', 'window.animationBehavior = .documentWindow',
                 'registry.f_100086c10(', 'let transition = OriginalPreviewWindowTransition(window: window)',
                 'makeOriginalReplicaPreview(', 'preview.f_10007be8c()', 'controller.view = preview',
                 'transition.present(controller)', 'focusPreviewEditing()']
        positions = [self.route.index(t) for t in order]
        self.assertEqual(positions, sorted(positions))
        self.assertIn('itemIdentity: AnyHashable(item.id)', self.route)
        self.assertIn('itemIdentifier: itemIdentifier, isEditing: true', self.route)

    def test_original_and_current_registration_replace_old_item_window(self):
        registry = (ROOT / 'replica/Sources/PastoCore/OriginalPreviewWindows.swift').read_text()
        register = body(registry, 'public func f_100086c10(window: OriginalPreviewWindow')
        order = ['f_10008747c(itemIdentity: itemIdentity)?.close()',
                 'entries.removeAll', 'entries.append', 'NotificationCenter.default.addObserver', 'f_100087864()']
        positions = [register.index(t) for t in order]
        self.assertEqual(positions, sorted(positions))

    def test_callbacks_close_the_session_and_update_its_identifier(self):
        self.assertIn('preview.onEndEditing = { window.close() }', self.route)
        self.assertIn('registry.f_10008727c(isEditing: editing, itemIdentifier: itemIdentifier)', self.route)
        self.assertNotIn('showPreview(', self.route)
        self.assertNotIn('previewPopover', self.route)
        self.assertNotIn('hidePanel()', self.route)

    def test_transition_retained_by_window_identity_until_close(self):
        self.assertIn('[ObjectIdentifier: OriginalPreviewWindowTransition]', self.ui)
        self.assertIn('let windowIdentity = ObjectIdentifier(window)', self.route)
        self.assertLess(self.route.index('editorWindowTransitions[windowIdentity] = transition'),
                        self.route.index('transition.present(controller)'))
        self.assertIn('transition.onDismissed = { [weak self] _ in', self.route)
        self.assertIn('editorWindowTransitions.removeValue(forKey: windowIdentity)', self.route)

    def test_transition_has_original_synchronous_present_order(self):
        present = body(self.transition, 'public func present(_ controller: NSViewController)')
        order = ['window.delegate = self', 'view.setFrameSize(controller.view.fittingSize)',
                 'window.contentViewController = controller', 'window.makeKeyAndOrderFront(nil)',
                 'window.orderFrontRegardless()', 'onPresented?(window)']
        positions = [present.index(t) for t in order]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn('DispatchQueue', present)
        self.assertNotIn('Task', present)
        self.assertIn('window.isReleasedWhenClosed = false', self.transition)

    def test_close_releases_content_before_owner_removal_callback(self):
        close = body(self.transition, 'public func windowWillClose(_ notification: Notification)')
        self.assertLess(close.index('window.contentViewController = nil'), close.index('onDismissed?(true)'))
        self.assertNotIn('orderOut', close)

    def test_focus_protocol_uses_text_override_and_noop_for_other_editable_types(self):
        self.assertIn('func focusPreviewEditing()', self.preview)
        self.assertIn('public extension OriginalPreviewEditableContent', self.preview)
        self.assertIn('func focusPreviewEditing() {}', self.preview)
        focus = body(self.content, 'func focusPreviewEditing()')
        self.assertIn('window?.makeFirstResponder(text)', focus)
        self.assertNotIn('selectAll', focus)
        for name in ['ReplicaImagePreviewContent', 'ReplicaColorPreviewContent', 'ReplicaLinkPreviewContent']:
            self.assertNotIn('func focusPreviewEditing()', (ROOT / f'replica/Sources/Pasto/UI/{name}.swift').read_text())
        self.assertEqual(self.route.count('preview.f_10007be8c()'), 1)

    def test_present_callback_cascades_count_including_the_current_window(self):
        position = body(self.ui, 'private func positionEditingPreview(_ window: NSWindow)')
        order = ['window.center()', 'guard let screen = window.screen else { return }',
                 'previewRegistry.windows.count * 30', 'x: window.frame.minX + offset, y: window.frame.minY - offset',
                 'if frame.maxX < origin.x + window.frame.width', 'if origin.y < frame.minY',
                 'window.setFrameOrigin(origin)']
        positions = [position.index(t) for t in order]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn('visibleFrame', position)
        self.assertIn('transition.onPresented = { [weak self] window in self?.positionEditingPreview(window) }', self.route)

    def test_earlier_focus_and_resign_fixes_still_drive_window_activation(self):
        resign = body(self.ui, 'private func panelDidResignKey()')
        self.assertIn('guard panel.sheets.isEmpty, NSApp.modalWindow == nil', resign)
        self.assertNotIn('DispatchQueue', resign)
        window = (ROOT / 'replica/Sources/PastoCore/OriginalPreviewWindows.swift').read_text()
        become = body(window, 'public override func becomeKey()')
        self.assertLess(become.index('NSApp.activate('), become.index('super.becomeKey()'))


if __name__ == '__main__':
    unittest.main()
