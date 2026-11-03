from item_order_scope_contract import without_list_route
"""Native private-list menu/count contracts; source checks only, no CoreData execution."""
import hashlib
import json
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from native_tab_list_delivery_scope_contract import pre_native_tab_list_delivery
from native_group_creation_result_scope_contract import pre_native_group_creation_result
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment


class LocalListMenuContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-58'
        cls.proof = json.loads((cls.phase / 'local-list-menu-contract.json').read_text())
        cls.lists = (ROOT / 'replica/Sources/PastoCore/ClipboardListPersistence.swift').read_text()
        cls.store = (ROOT / 'replica/Sources/PastoCore/ClipboardStore.swift').read_text()
        cls.persistence = (ROOT / 'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text()
        cls.panel = (ROOT / 'replica/Sources/Pasto/UI/PanelViews.swift').read_text()
        cls.ui = (ROOT / 'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
        cls.count = body(cls.lists, 'func menuState(for list:')
        cls.menu = body(cls.panel, 'private func localListMenu(')
        cls.original = {r['address']: original_fragment((ROOT / r['path']).read_text(), r['address'][2:])
                        for r in cls.proof['original_fragments']}

    def assertOrder(self, source, tokens):
        positions = [source.index(t) for t in tokens]
        self.assertEqual(positions, sorted(positions))

    def test_native_inputs_and_changed_sources_are_bound(self):
        self.assertEqual(len(self.proof['original_fragments']), 14)
        for row in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / row['path'])[row['address']]['sha256'], row['sha256'])
        for row in [self.proof['binary']] + self.proof['arm_disassemblies']:
            self.assertEqual(hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest(), row['sha256'])
        for path, digest in self.proof['current_sources'].items():
            frozen = (self.phase / 'after' / path).read_text()
            self.assertEqual(hashlib.sha256((self.phase / 'after' / path).read_bytes()).hexdigest(), digest)
            markers = {
                'replica/Sources/PastoCore/ClipboardListPersistence.swift': ['func menuState('],
                'replica/Sources/PastoCore/ClipboardPersistence.swift': ['func localListMenuState('],
                'replica/Sources/PastoCore/ClipboardStore.swift': ['public func localListMenuState('],
                'replica/Sources/Pasto/UI/PanelViews.swift': ['private var boardTabs:', 'private func localListMenu('],
                'replica/Sources/Pasto/UI/ReplicaUIController.swift': ['func clearHistory()', 'func removePinboard('],
            }[path]
            for marker in markers:
                current = body(pre_native_tab_list_delivery((ROOT / path).read_text()), marker)
                previous = body(frozen, marker)
                if marker == 'func menuState(':
                    old_head, _, old_tail = previous.partition('let request = NSFetchRequest<NSFetchRequestResult>(entityName: "Item")')
                    new_head, _, new_tail = current.partition('let request = PastoItemEntity.defaultFetchRequest()')
                    self.assertIn('PastoItemEntity.defaultFetchRequest()', current)
                    self.assertEqual((new_head, new_tail), (old_head, old_tail))
                else:
                    self.assertEqual(current, previous)

    def test_native_predicate_constants_decode_to_history_and_owner_not_cached_flags(self):
        for row in self.proof['predicate_constants']:
            def decode(first, second):
                second = int(second, 16)
                return (struct.pack('<Q', int(first, 16)) + struct.pack('<Q', second))[:(second >> 56) & 15].decode()
            self.assertEqual(decode(row['first_word'], row['second_word']), row['key'])
            self.assertEqual(decode(row['format_first_word'], row['format_second_word']), row['format'])
        self.assertEqual([(r['key'], r['format']) for r in self.proof['predicate_constants']],
                         [('timestamp', '%K != nil'), ('list', '%K == %@')])
        self.assertIn('FUN_100329088()', self.original['0x100325130'])
        self.assertIn('FUN_1003298a0(0,FUN_1003214a8)', self.original['0x100329088'])

    def test_empty_decision_keeps_native_context_and_error_fallback(self):
        self.assertOrder(self.count, ['list.value(forKey: "rawType")', 'guard let context = list.managedObjectContext',
                         'let request =', 'context.count(for: request)', 'return (rawType, count == 0)'])
        self.assertIn('else { return (nil, true) }', body(self.lists, 'func menuState(identifier:'))
        self.assertIn('else { return (rawType, true) }', self.count)
        self.assertIn('(try? context.count(for: request)) ?? 0', self.count)
        self.assertNotIn('count <= 0', self.count)
        words = {r['address']: int.from_bytes(bytes.fromhex(r['bytes']), 'little') for r in self.proof['count_error_ARM']}
        self.assertEqual(words['0x10032519c'], 0x52800020)  # mov w0,1
        self.assertEqual(words['0x1003251b8'], 0xf100029f)  # cmp x20,0
        self.assertEqual(words['0x1003251bc'], 0x1a9f17e0)  # cset w0,eq

    def test_count_uses_native_history_timestamp_and_owner_relationship(self):
        self.assertIn('PastoItemEntity.defaultFetchRequest()', self.count)
        self.assertIn('case 1: request.predicate = NSPredicate(format: "timestamp != nil")', self.count)
        self.assertIn('case 2: request.predicate = NSPredicate(format: "list == %@", list)', self.count)
        self.assertIn('default: return (rawType, true)', self.count)
        for extra in ['isDeleted', 'pinboardID', 'items.', 'fetchLimit', 'context.save', 'context.reset', 'context.rollback']:
            self.assertNotIn(extra, self.count)

    def test_actual_store_facade_serializes_count_without_transaction_or_context_reset(self):
        facade = body(self.store, 'public func localListMenuState(pinboardID:')
        self.assertIn('pinboardID?.uuidString ?? ClipboardListPersistence.historyIdentifier', facade)
        persist = body(self.persistence, 'func localListMenuState(identifier:')
        self.assertIn('context.performAndWait { lists.menuState(identifier: identifier) }', persist)
        for extra in ['perform {', 'commit(', 'save(', 'reset(', 'rollback(']:
            self.assertNotIn(extra, persist)

    def test_both_context_menu_providers_resolve_count_lazily(self):
        tabs = body(self.panel, 'private func boardTab(')
        self.assertIn('boardButton(target.name, board: board, target: target)', tabs)
        self.assertIn('tab.menuProvider = { localListMenu(for: target) }', tabs)
        self.assertNotIn('localListMenuState(', tabs)
        self.assertIn('state.store.localListMenuState(target)', self.menu)
        self.assertIn('menu.autoenablesItems = false', self.menu)

    def test_local_history_and_group_menu_gates_and_original_action_order(self):
        self.assertOrder(self.menu, ['title: "重命名"', 'let list =', 'if list.rawType == 1',
                         'if !list.isEmpty', 'title: "删除历史…"', 'else if list.rawType == 2',
                         'title: list.isEmpty ? "删除" : "删除…"', 'menu.addItem(.separator())', 'title: "颜色"'])
        for callback in ['requestTabRename(target)', 'state.controller?.clearHistory()',
                         'state.controller?.removePinboard(target)', 'state.store.updateListColor(target,']:
            self.assertIn(callback, self.menu)
        self.assertOrder(self.original['0x100021f00'], ['FUN_1000243ec', 'FUN_100024274', 'FUN_1000242c8', 'FUN_100024350'])

    def test_color_choices_preserve_actual_attribute_mapping_and_requested_named_dots(self):
        self.assertOrder(self.menu, ['target.colorCode.map { OriginalPinboardColor(canonicalColorCode: $0) }',
                         'for color in OriginalPinboardColor.allCases', 'title: colorName(color)',
                         'item.image = colorMenuImage(color)', 'item.state = selectedColor == color ? .on : .off'])
        self.assertIn('color.canonicalColorCode', self.menu)
        self.assertEqual(body(self.panel, 'private func colorMenuImage('),
                         body((self.phase / 'before/replica/Sources/Pasto/UI/PanelViews.swift').read_text(), 'private func colorMenuImage('))
        for name in ['红色', '橙色', '黄色', '绿色', '蓝色', '紫色', '粉色', '灰色']:
            self.assertIn(name, body(self.panel, 'private func colorName('))

    def test_delete_invocation_rechecks_managed_count_and_keeps_real_actions(self):
        clear = body(self.ui, 'func clearHistory()')
        self.assertOrder(clear, ['guard !store.localListMenuState(pinboardID: nil).isEmpty else',
                         'state.perform { try store.eraseHistory() }', 'return', 'let alert = NSAlert()',
                         'alert.runModal()'])
        remove = body(self.ui, 'func removePinboard(')
        self.assertOrder(remove, ['state.pendingPinboardDeletion = target',
                         'if store.localListMenuState(target).isEmpty',
                         'confirmPinboardRemoval()', 'panel.makeFirstResponder(nil)'])
        self.assertNotIn('store.items', clear + remove)
        self.assertIn('try store.removeList(target)', body(self.ui, 'func confirmPinboardRemoval()'))

    def test_original_error_branch_releases_then_directly_invokes_delete(self):
        words = {r['address']: struct.unpack('<I', bytes.fromhex(r['bytes']))[0]
                 for r in self.proof['count_error_ARM']}
        def branch(address):
            displacement = words[hex(address)] & ((1 << 26) - 1)
            if displacement & (1 << 25):
                displacement -= 1 << 26
            return address + displacement * 4
        for error, operation in [(0x1003c54c4, 0x1003c54e8), (0x1003c5130, 0x1003c5160)]:
            self.assertEqual(branch(error), 0x100bfc708)  # swift_errorRelease
            self.assertEqual(branch(operation), 0x1002ff310)
        self.assertIn('FUN_1003c5408', self.original['0x100024274'])
        self.assertIn('FUN_1003c4f00', self.original['0x1000242c8'])

    def test_unmatched_move_menu_actions_removed_but_drag_reorder_kept(self):
        self.assertNotIn('state.moveList(', self.menu)
        self.assertNotIn('func movePinboard(_ board: Pinboard, by offset: Int)', self.ui)
        self.assertIn('state.moveList(identifier: String(value.dropFirst(15)), to: target)', body(self.panel, 'private func boardTab('))
        self.assertIn('func moveList(identifier: String, to target: ClipboardListTarget)', self.ui)

    def test_creation_and_selection_models_are_not_silently_rewritten(self):
        for path, markers in {
            'replica/Sources/PastoCore/ClipboardStore.swift': ['private func insertPinboard(', 'private func normalize(', 'public func pinboardOwner('],
            'replica/Sources/PastoCore/ClipboardListPersistence.swift': ['func insertPinboard(', 'func project(', 'func synchronize('],
            'replica/Sources/Pasto/UI/ReplicaUIController.swift': [],
        }.items():
            current = pre_native_group_creation_result((ROOT / path).read_text())
            before = (self.phase / 'before' / path).read_text()
            for marker in markers:
                self.assertEqual(body(current, marker), body(before, marker))
        before_ui = (self.phase / 'before/replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
        self.assertEqual(without_list_route(body(self.ui, 'private func applySelectedList(')), body(before_ui, 'func chooseBoard('))
        self.assertFalse(self.proof['partial_unscored_repairs'][1]['implemented'])
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertEqual([r['function_id'] for r in self.proof['contracts']], ['Paste:0x100021f00'])
