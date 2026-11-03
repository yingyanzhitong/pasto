"""Direct resolved selection reaches the real copy writer; static source checks only."""
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
from collection_membership_scope_contract import ENTRY_PATH, pre_collection_membership_bytes
from modal_restore_scope_contract import RESTORE_ITEM_PATH, pre_modal_restore, pre_modal_restore_bytes
from resolved_copy_scope_contract import pre_resolved_copy


class ResolvedCopyInputContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-76'
        cls.proof = json.loads((cls.phase / 'resolved-copy-contract.json').read_text())
        cls.base = json.loads((cls.phase / 'baseline.json').read_text())
        cls.paths = dict(writer='replica/Sources/PastoCore/Pasteboard.swift', ui='replica/Sources/Pasto/UI/ReplicaUIController.swift')
        cls.source = {k: pre_modal_restore((ROOT / p).read_text()) for k, p in cls.paths.items()}

    def before(self, key): return (self.phase / 'before' / self.paths[key]).read_text()

    def test_seven_original_functions_and_incoming_entity_sequence_ARM_are_bound(self):
        self.assertEqual(len(self.proof['original_fragments']), 7)
        for row in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / row['path'])[row['address']]['sha256'], row['sha256'])
        for row in [self.proof['binary'], self.proof['arm_disassembly']]:
            self.assertEqual(hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest(), row['sha256'])
        words = {int(r['address'], 16): struct.unpack('<I', bytes.fromhex(r['bytes']))[0] for r in self.proof['ARM_words']}
        self.assertEqual(words[0x10037a1b8], 0xa90102b3)
        self.assertEqual(0x10037a1d0 + (words[0x10037a1d0] & 0x3ffffff) * 4, 0x10038222c)

    def test_actual_two_source_files_and_after_snapshots_are_bound(self):
        for p, h in self.proof['current_sources'].items():
            self.assertEqual(hashlib.sha256(pre_modal_restore_bytes(ROOT / p)).hexdigest(), h)
            self.assertEqual(pre_modal_restore_bytes(ROOT / p), (self.phase / 'after' / p).read_bytes())

    def test_selected_overload_forwards_same_values_order_and_plain_option(self):
        entry = body(self.source['writer'], 'public func writeToPasteboard(selectedItems:')
        self.assertIn('ids: selectedItems.map(\\.id)', entry)
        self.assertIn('options: plainTextOnly ? .plainText : []', entry)
        self.assertIn('recognizedImageData: nil', entry)
        self.assertIn('resolvedSelection: selectedItems', entry)
        for token in ['reload()', 'Set(', '.sorted', '.filter', 'items.first', 'save(']:
            self.assertNotIn(token, entry)

    def test_resolved_branch_uses_input_without_reading_store(self):
        worker = body(self.source['writer'], 'private func writeToPasteboard(ids:')
        direct = body(worker, 'if let resolvedSelection')
        self.assertEqual(direct.strip(), '{\n            selected = resolvedSelection\n        }')
        self.assertLess(worker.index('guard !ids.isEmpty else { return }'), worker.index('if let resolvedSelection'))
        self.assertIn('resolvedSelection: [ClipboardItem]? = nil', self.source['writer'])

    def test_identifier_only_adapter_retains_reload_and_not_deleted_guard(self):
        worker = body(self.source['writer'], 'private func writeToPasteboard(ids:')
        fallback = worker.split('        } else {\n', 1)[1].split('        let selections =', 1)[0]
        order = ['try reload()', 'selected = try ids.map', 'items.first(where: { $0.id == id && !$0.isDeleted })',
                 'throw ClipboardStoreError.itemNotFound', 'return item']
        self.assertEqual([fallback.index(t) for t in order], sorted(fallback.index(t) for t in order))
        self.assertEqual(worker.count('try reload()'), 1)

    def test_processor_writer_save_failure_undo_and_notification_tail_is_identical(self):
        marker = '        let selections = try selected.map'
        current = body(self.source['writer'], 'private func writeToPasteboard(ids:')
        previous = body(self.before('writer'), 'private func writeToPasteboard(ids:')
        self.assertEqual(current[current.index(marker):], previous[previous.index(marker):])
        order = ['let restoration = try prepareHistoryRestore(selected)', 'writer.f_10037875c(objects)',
                 'try recordRestoredSelection(restoration)', 'removeAllActions()', 'NotificationCenter.default.post', 'didRestoreItem.send()']
        self.assertEqual([current.index(t) for t in order], sorted(current.index(t) for t in order))

    def test_actual_copy_selection_keeps_empty_beep_then_direct_resolved_write(self):
        copy = body(self.source['ui'], 'func copySelection(plainTextOnly:')
        order = ['let items = appliedSelectionItems()', 'guard !items.isEmpty else { NSSound.beep(); return }',
                 'performCopy {', 'store.writeToPasteboard(selectedItems: items,']
        self.assertEqual([copy.index(t) for t in order], sorted(copy.index(t) for t in order))
        self.assertNotIn('copy(ids:', copy)
        self.assertNotIn('items.map', copy)
        self.assertEqual(body(self.source['ui'], 'private func performCopy('), body(self.before('ui'), 'private func performCopy('))

    def test_other_copy_OCR_and_paste_modal_interfaces_are_unchanged(self):
        for signature in ['func copy(item:', 'func copy(ids:', 'func copyRecognizedImageText(',
                          'func pasteSelection(', 'func paste(item:', 'func paste(ids:']:
            self.assertEqual(body(self.source['ui'], signature), body(self.before('ui'), signature))
        p = 'replica/Sources/Pasto/AppMain.swift'
        self.assertEqual(hashlib.sha256(pre_modal_restore_bytes(ROOT / p)).hexdigest(), self.base['production'][p])

    def test_existing_history_preparation_and_native_transaction_are_unchanged(self):
        for p in ['replica/Sources/PastoCore/ClipboardStore.swift', 'replica/Sources/PastoCore/ClipboardPersistence.swift']:
            self.assertEqual(hashlib.sha256(pre_modal_restore_bytes(ROOT / p)).hexdigest(), self.base['production'][p])
        self.assertIn('try prepareHistoryRestore(selected)', self.source['writer'])

    def test_only_approved_input_and_copy_blocks_differ_from_previous_code(self):
        for key in self.paths:
            self.assertEqual(pre_resolved_copy(self.source[key]), self.before(key))

    def test_only_two_files_change_without_schema_or_package_changes(self):
        sha = lambda p: hashlib.sha256(pre_modal_restore_bytes(ROOT / p)).hexdigest()
        self.assertEqual({p for p, h in self.base['production'].items() if sha(p) != h}, set(self.paths.values()))
        self.assertEqual({str(p.relative_to(ROOT)) for p in (ROOT / 'replica/Sources').rglob('*') if p.is_file()} - {NATIVE_TITLE_PATH, ITEM_OBSERVATION_PATH} - {RESTORE_ITEM_PATH, ENTRY_PATH}, set(self.base['production']))
        for p in ['replica/Package.swift', 'package.json']:
            self.assertEqual(sha(p), self.base['other'][p])

    def test_direct_paste_and_full_entity_provider_gap_are_not_counted_complete(self):
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertEqual(self.proof['remaining_confirmed_differences'], ['Paste:0x1003544dc'])
        self.assertEqual(self.proof['repaired_finite_contracts'], [])
        self.assertTrue(any('permission-modal' in s for s in self.proof['remaining_work']))


if __name__ == '__main__':
    unittest.main()
