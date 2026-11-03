"""Real modal restore routes and original binary evidence; source checks, no Swift execution."""
from native_title_scope_contract import NEW_PATH as NATIVE_TITLE_PATH
from item_observation_scope_contract import NEW_PATH as ITEM_OBSERVATION_PATH
import hashlib
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from collection_membership_scope_contract import pre_collection_membership, pre_collection_membership_bytes, ENTRY_PATH
from native_application_scope_contract import pre_native_application_bytes
from test_p0_repair_checksum_routing import original_fragment
from modal_restore_scope_contract import RESTORE_ITEM_PATH, pre_modal_restore, HUNKS


class ModalRestoreInputContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-77'
        cls.proof = json.loads((cls.phase / 'modal-restore-contract.json').read_text())
        cls.base = json.loads((cls.phase / 'baseline.json').read_text())
        cls.paths = dict(holder=RESTORE_ITEM_PATH,
            reference='replica/Sources/PastoCore/ClipboardCollectionItemReference.swift',
            writer='replica/Sources/PastoCore/Pasteboard.swift',
            ui='replica/Sources/Pasto/UI/ReplicaUIController.swift',
            host='replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift',
            app='replica/Sources/Pasto/AppMain.swift')
        cls.source = {k: pre_collection_membership((ROOT / p).read_text()) for k, p in cls.paths.items()}

    def before(self, key): return (self.phase / 'before' / self.paths[key]).read_text()
    def app_action(self): return body(self.source['app'], 'private func paste(ids: [UUID], plain: Bool, forceDirect: Bool = false,')

    def test_six_original_fragments_and_sixteen_machine_words_are_bound(self):
        self.assertEqual(len(self.proof['original_fragments']), 6)
        for r in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / r['path'])[r['address']]['sha256'], r['sha256'])
        raw = (ROOT / self.proof['binary']['path']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), self.proof['binary']['sha256'])
        self.assertEqual(len(self.proof['ARM_words']), 16)
        for r in self.proof['ARM_words']:
            a = int(r['address'], 16) - 0x100000000
            self.assertEqual(raw[a:a + 4].hex(), r['bytes'])
        r = self.proof['arm_disassembly']
        self.assertEqual(hashlib.sha256((ROOT / r['path']).read_bytes()).hexdigest(), r['sha256'])

    def test_modal_fallback_retains_incoming_entity_sequence_not_new_identifier_query(self):
        r = next(r for r in self.proof['original_fragments'] if r['address'] == '0x100066068')
        f = original_fragment((ROOT / r['path']).read_text(), '100066068')
        self.assertIn('local_e8 = param_1;', f)
        self.assertIn('FUN_1003b936c(puVar8,local_118,puVar3,puVar4)', f)
        self.assertLess(f.index('FUN_100ae4f8c()'), f.index('FUN_100066570(param_1,local_118)'))
        words = {int(r['address'], 16): struct.unpack('<I', bytes.fromhex(r['bytes']))[0] for r in self.proof['ARM_words']}
        self.assertEqual(words[0x100066094], 0xaa0003f6)  # incoming x0→x22
        self.assertEqual(words[0x1000662d8], 0xaa1603e0)  # fallback x22→x0
        for pc, target in [(0x1000662e8, 0x100066570), (0x100066354, 0x1003b936c),
                           (0x1000664a4, 0x100ae4f8c), (0x100066620, 0x1003b936c)]:
            word = words[pc];self.assertEqual(word >> 26, 0b100101)
            imm = word & 0x3ffffff
            if imm & 0x2000000: imm -= 0x4000000
            self.assertEqual(pc + imm * 4, target)

    def test_real_current_sources_and_frozen_after_snapshots_are_bound(self):
        self.assertEqual(set(self.paths.values()), set(self.proof['current_sources']))
        for p, h in self.proof['current_sources'].items():
            raw = pre_collection_membership_bytes(ROOT / p)
            self.assertEqual(hashlib.sha256(raw).hexdigest(), h)
            self.assertEqual(raw, (self.phase / 'after' / p).read_bytes())

    def test_entity_is_held_before_modal_without_eager_payload_decoding(self):
        holder = self.source['holder']
        self.assertIn('@MainActor\npublic struct ClipboardRestoreItem', holder)
        init = body(holder, 'init(id: UUID, object: PastoItemEntity)')
        closure = body(init, 'resolve =')
        self.assertIn('ClipboardPersistence.item(object)', closure)
        self.assertIn('fatalError("Missing restore item content")', closure)
        self.assertNotIn('ClipboardPersistence.item', init.replace(closure, ''))
        for token in ['weak ', 'unowned ', 'store.items', 'reload()', 'UUID()']:
            self.assertNotIn(token, holder)
        self.assertEqual(body(holder, 'public func resolvedItem()').strip(), '{ resolve() }')

    def test_reference_resolves_entity_class_once_then_retains_it(self):
        ref = body(self.source['reference'], 'public func requiredRestoreItem(id: UUID)')
        self.assertIn('(try? context.existingObject(with: objectID)) as? PastoItemEntity', ref)
        self.assertLess(ref.index('fatalError("Missing restore item")'), ref.index('return ClipboardRestoreItem(id: id, object: object)'))
        self.assertNotIn('ClipboardPersistence.item', ref)
        self.assertNotIn('item()', ref)

    def test_host_uses_applied_owner_order_and_live_reference_not_pending_values(self):
        f = body(self.source['host'], 'func appliedRestoreItems(for state:')
        order = ['self.state === state, state.collectionOwner === self', 'let positions =',
                 'orderedIDs.compactMap', 'guard let index = positions[identifier]',
                 'itemReferences[identifier]?.requiredRestoreItem(id: identifier)']
        self.assertEqual([f.index(t) for t in order], sorted(f.index(t) for t in order))
        self.assertIn('?? ClipboardRestoreItem(item: item)', f)  # explicit legacy row adapter
        for token in ['pendingSnapshot', 'drainCollectionSnapshots', 'state.visibleItems', 'renderedItem(', 'Set(orderedIDs']:
            self.assertNotIn(token, f)

    def test_controller_requires_real_loaded_panel_host_and_same_window(self):
        f = body(self.source['ui'], 'private func appliedRestoreItems(orderedIDs:')
        for token in ['loadedPanel', 'ReplicaNativeCollectionHost', 'collection.window === panel else { return [] }',
                      'collection.appliedRestoreItems(for: state,', 'state.collectionSelectionSnapshot().orderedIDs']:
            self.assertIn(token, f)
        self.assertNotIn('state.selectedItems', f)
        self.assertNotIn('state.visibleItems', f)

    def test_double_click_and_return_reach_retained_entity_route(self):
        f = body(self.source['ui'], 'func pasteSelection(plainTextOnly:')
        self.assertIn('let items = appliedRestoreItems()', f)
        self.assertLess(f.index('guard !items.isEmpty'), f.index('paste(restoreItems: items'))
        f = body(self.source['ui'], 'func paste(item:')
        self.assertLess(f.index('appliedRestoreItems(orderedIDs: [item.id])'), f.index('paste(restoreItems: [input]'))
        self.assertIn('return paste(ids: [item.id]', f)  # Stack/outside-applied compatibility
        mouse = body(self.source['host'], 'override func mouseDown(with event:')
        self.assertIn('if event.clickCount == 2', mouse)
        self.assertIn('paste(item: current[index]', mouse)
        self.assertIn('onEnter: { [self] in pasteSelection(plainTextOnly: plain) }', self.source['ui'])

    def test_command_v_keeps_exact_editing_modifier_gates_and_force_direct(self):
        f = body(self.source['ui'], 'private func handleKey(_ event: NSEvent)')
        sig = 'if !isEditing, signature.keyCode == OriginalShortcutFunctions.f_1001e94d4("v")'
        self.assertIn(sig + ',\n           signature.modifierRawValue == NSEvent.ModifierFlags.command.rawValue', f)
        route = body(f, sig)
        self.assertIn('paste(restoreItems: appliedRestoreItems(), plainTextOnly: false, forceDirect: true)', route)
        self.assertIn('return true', route)
        self.assertNotIn('Set(', route)

    def test_actual_app_wiring_passes_same_array_and_force_bit_to_existing_worker(self):
        f = body(self.source['app'], 'ui.pasteRestoreItemsHandler =')
        self.assertIn('restoreItems: items', f)
        self.assertIn('forceDirect: forceDirect', f)
        self.assertIn('ids: items.map(\\.id)', f)
        route = body(self.source['ui'], 'private func paste(restoreItems:')
        self.assertLess(route.index('guard !restoreItems.isEmpty'), route.index('pasteRestoreItemsHandler(restoreItems, plainTextOnly, forceDirect)'))
        self.assertIn('if let directPasteItemsHandler', route)
        self.assertIn('return paste(ids: ids', route)

    def test_permission_prefix_preference_target_and_setup_exit_are_unchanged(self):
        current = self.app_action()
        previous = body(self.before('app'), 'private func paste(ids:')
        self.assertEqual(current.split('        do {\n            if let restoreItems', 1)[0],
                         previous.split('        do { try store.writeToPasteboard', 1)[0])
        setup = body(current, 'if result == 2')
        for token in ['NSApp.deactivate()', 'OriginalEnableAccessibilityModal.run(requestOnShow: true)', 'return false']:
            self.assertIn(token, setup)
        self.assertNotIn('writeToPasteboard', setup)
        self.assertNotIn('resolvedItem', setup)
        self.assertLess(current.index('if result == 2'), current.index('if let restoreItems'))

    def test_lazy_content_is_read_only_after_modal_and_shared_writer_keeps_order(self):
        action = self.app_action()
        self.assertLess(action.index('OriginalPasteToOtherAppsModal.run()'), action.index('writeToPasteboard(restoreItems:'))
        worker = body(self.source['writer'], 'public func writeToPasteboard(restoreItems:')
        self.assertLess(worker.index('restoreItems.map { $0.resolvedItem() }'), worker.index('resolvedSelection: selected'))
        self.assertIn('ids: restoreItems.map(\\.id)', worker)
        self.assertIn('options: options', worker)
        for token in ['reload()', 'Set(', '.filter', '.sorted', 'store.items', 'save(']:
            self.assertNotIn(token, worker)
        route = body(action, 'if let restoreItems')
        self.assertIn('options: restoreOptions', route)

    def test_restoration_failure_focus_handoff_and_hide_tail_are_byte_identical(self):
        marker = '        catch {\n            pasteLogger.error("restore_failed'
        current = self.app_action();previous = body(self.before('app'), 'private func paste(ids:')
        self.assertEqual(current[current.index(marker):], previous[previous.index(marker):])
        f = body(self.source['writer'], 'private func writeToPasteboard(ids:')
        self.assertEqual(f, body(self.before('writer'), 'private func writeToPasteboard(ids:'))
        self.assertLess(f.index('writer.f_10037875c(objects)'), f.index('try recordRestoredSelection(restoration)'))
        self.assertLess(f.index('try recordRestoredSelection(restoration)'), f.index('removeAllActions()'))

    def test_only_reviewed_hunks_and_one_new_holder_change_production(self):
        self.assertEqual(len(HUNKS), 10)
        for key in ['reference', 'writer', 'ui', 'host', 'app']:
            self.assertEqual(pre_modal_restore(self.source[key]), self.before(key))
        files = {str(p.relative_to(ROOT)) for p in (ROOT / 'replica/Sources').rglob('*') if p.is_file()}
        self.assertEqual(files - {NATIVE_TITLE_PATH, ITEM_OBSERVATION_PATH} - set(self.base['production']), {RESTORE_ITEM_PATH, ENTRY_PATH})
        sha = lambda p: hashlib.sha256(pre_native_application_bytes(ROOT / p)).hexdigest()
        changed = {p for p, h in self.base['production'].items() if sha(p) != h}
        self.assertEqual(changed, set(self.paths.values()) - {RESTORE_ITEM_PATH})
        for p in ['replica/Package.swift', 'package.json']:
            self.assertEqual(sha(p), self.base['other'][p])

    def test_full_provider_and_performance_are_not_marked_complete(self):
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertEqual(self.proof['repaired_finite_contracts'], [])
        self.assertEqual(self.proof['remaining_confirmed_differences'], ['Paste:0x1003544dc'])
        self.assertTrue(any('metadata' in s for s in self.proof['remaining_work']))
        self.assertTrue(any('performance' in s for s in self.proof['remaining_work']))


if __name__ == '__main__': unittest.main()
