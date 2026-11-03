from native_restore_writer_scope_contract import pre_native_restore_writer
"""Command+O and applied copy selection: source and original-data checks only."""
import hashlib
import json
import struct
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from macho_imports import parse_macho
from test_offline_p0_contracts import body
from test_p0_repair_context_updates import chained_bindings


class OpenSelection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ui = pre_native_restore_writer((ROOT / 'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text())
        cls.method = body(cls.ui, 'private func openAppliedSelection()')

    def test_original_open_and_selection_index_fragments_are_bound(self):
        proof = json.loads((ROOT / '.local/p0-repair/phase-8/open-selection-proof.json').read_text())['records'][0]
        refs = [dict(proof['original'], function_id=proof['function_id'])] + proof['supporting_original_fragments']
        for ref in refs:
            self.assertEqual(source_fragments(ROOT / ref['path'])[ref['function_id'].split(':')[1]]['sha256'], ref['sha256'])
        descriptor = proof['descriptor_evidence']
        self.assertEqual(hashlib.sha256((ROOT / descriptor['path']).read_bytes()).hexdigest(), descriptor['sha256'])
        cases = {r['case_index']: r['name'] for r in descriptor['fields_in_declared_order']}
        self.assertEqual(cases[1], 'link')
        self.assertEqual(cases[4], 'files')

    def test_open_shortcut_is_exact_command_and_collection_owner_gated(self):
        handle = body(self.ui, 'private func handleKey(_ event: NSEvent) -> Bool')
        signature = 'if !isEditing, signature.keyCode == OriginalShortcutFunctions.f_1001e94d4("o")'
        command = body(handle, signature)
        self.assertLess(handle.index('if !ownsCollectionFocus'), handle.index(signature))
        self.assertIn('signature.modifierRawValue == NSEvent.ModifierFlags.command.rawValue', handle[handle.index(signature):handle.index(signature)+220])
        self.assertIn('openAppliedSelection()', command)
        self.assertIn('return true', command)

    def test_copy_and_open_resolve_ordered_selection_only_in_applied_snapshot(self):
        helper = body(self.ui, 'private func appliedSelectionItems()')
        self.assertIn('collection.appliedSelectedItems(for: state,', helper)
        self.assertIn('orderedIDs: state.collectionSelectionSnapshot().orderedIDs', helper)
        self.assertIn('collection.window === panel else { return [] }', helper)
        self.assertNotIn('visibleItems', helper)
        self.assertNotIn('store.items', helper)
        self.assertNotIn('.sorted', helper)
        self.assertNotIn('Array(Set', helper)
        self.assertIn('let selected = appliedSelectionItems()', self.method)
        copy = body(self.ui, 'func copySelection(plainTextOnly: Bool)')
        self.assertIn('let items = appliedSelectionItems()', copy)
        self.assertIn('guard !items.isEmpty else { NSSound.beep(); return }', copy)

    def test_link_eligibility_precedes_strict_first_file_preview_filter(self):
        accepted = body(self.method, 'let accepted = selected.filter')
        self.assertLess(accepted.index('item.kind == .link'), accepted.index('decodedFilePreviewMetadata'))
        self.assertIn('if item.kind == .link { return true }', accepted)
        self.assertIn('guard let path = item.decodedFilePreviewMetadata?.paths.first else { return false }', accepted)
        for forbidden in ['payloads', 'plainText', 'fileURLs', 'UTType', 'allSatisfy']:
            self.assertNotIn(forbidden, self.method)

    def test_original_security_scope_order_is_not_extended_around_open(self):
        accepted = body(self.method, 'let accepted = selected.filter')
        order = ['let accessed = url.startAccessingSecurityScopedResource()',
                 'url.stopAccessingSecurityScopedResource()',
                 'let exists = FileManager.default.fileExists(atPath: path)',
                 'return accessed && exists']
        self.assertEqual([accepted.index(t) for t in order], sorted(accepted.index(t) for t in order))
        self.assertNotIn('defer', accepted)
        self.assertNotIn('NSWorkspace', accepted)

    def test_empty_candidates_beep_without_deactivation_and_nonempty_open_redecodes_preview(self):
        guard = 'guard !accepted.isEmpty else { NSSound.beep(); return }'
        self.assertLess(self.method.index(guard), self.method.index('NSApp.deactivate()'))
        self.assertLess(self.method.index('NSApp.deactivate()'), self.method.index('for item in accepted'))
        loop = body(self.method, 'for item in accepted')
        self.assertIn('if let link = item.decodedLinkPreviewMetadata', loop)
        self.assertIn('NSWorkspace.shared.open(link.url)', loop)
        self.assertIn('else if let files = item.decodedFilePreviewMetadata', loop)
        self.assertIn('guard let path = files.paths.first else { return }', loop)
        self.assertIn('NSWorkspace.shared.open(URL(fileURLWithPath: path))', loop)
        self.assertNotIn('for path', loop)
        self.assertNotIn('hidePanel()', self.method)
        self.assertNotIn('URLSession', self.method)

    def test_rename_slot_is_bound_for_all_original_cell_types_without_inventing_a_handler(self):
        proof = json.loads((ROOT / '.local/p0-repair/phase-8/rename-key-root-supplement.json').read_text())
        data = (ROOT / proof['binary']['path']).read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), proof['binary']['sha256'])
        self.assertEqual(len(proof['slots']), 7)
        for slot in proof['slots']:
            raw, = struct.unpack_from('<Q', data, slot['slot_file_offset'])
            self.assertEqual(raw, int(slot['raw'], 16))
            self.assertEqual(0x100000000 + (raw & ((1 << 36) - 1)), 0x1003d868c)
            start = slot['name_file_offset']
            name = data[start:data.index(b'\0', start)].decode()
            self.assertEqual(name, slot['name'])
            self.assertTrue(name.endswith(slot['class']))
        for ref in proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / ref['path'])[ref['address']]['sha256'], ref['sha256'])
        # The typed target still needs the actual ItemCell title editor, not a guessed modal action.
        self.assertFalse(proof['compiled'])
        self.assertFalse(proof['executed'])

    def test_fixed_history_literal_uses_real_chained_pointer_and_matches_original_factory(self):
        proof = json.loads((ROOT / '.local/p0-repair/phase-8/history-identifier-root-proof.json').read_text())
        data = (ROOT / proof['binary']['path']).read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), proof['binary']['sha256'])
        raw, = struct.unpack_from('<Q', data, proof['slot_file_offset'])
        self.assertEqual(raw, int(proof['raw'], 16))
        runtime = (0x100000000 + (raw & ((1 << 36) - 1))) | (((raw >> 36) & 255) << 56)
        self.assertEqual(runtime, 0x8000000100da2350)
        self.assertEqual((runtime & 0x00ffffffffffffff) + 0x20, int(proof['payload_address'], 16))
        count, = struct.unpack_from('<Q', data, proof['count_file_offset'])
        self.assertEqual(count & 0xffffffffffff, 23)
        start = proof['payload_file_offset']
        self.assertEqual(data[start:start+23], b'sharedPasteboardHistory')
        self.assertEqual(proof['dyld_chain']['pointer_format'], 6)
        self.assertEqual(proof['dyld_chain']['visited_to_slot'][-1], proof['slot_address'])
        ref = proof['factory_original']
        self.assertEqual(source_fragments(ROOT / ref['path'])[ref['address']]['sha256'], ref['sha256'])
        self.assertIn('FUN_100368080(0xd000000000000017,0x8000000100da2350)',
                      (ROOT / ref['path']).read_text())

    def test_original_file_scope_bool_and_exists_branches_are_bound_to_real_imports(self):
        proof = json.loads((ROOT / '.local/p0-repair/phase-8/open-machine-proof.json').read_text())
        data = (ROOT / proof['binary']['path']).read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), proof['binary']['sha256'])
        for segment in proof['segments']:
            raw = data[segment['file_offset']:segment['file_offset'] + segment['length']]
            self.assertEqual(raw.hex(), segment['hex'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), segment['sha256'])
        symbols = parse_macho(ROOT / proof['binary']['path'])['stubs']
        for address, ref in proof['imports'].items():
            self.assertEqual(symbols[address]['symbol'], ref['symbol'])
            self.assertEqual(symbols[address]['dyld_binding']['symbol'], ref['symbol'])
        word = lambda address: struct.unpack_from('<I', data, address - 0x100000000)[0]
        self.assertEqual(word(0x10006516c), 0xb81343a0)  # stores startAccessing Bool, frame -cc
        self.assertEqual(word(0x1000651d8), 0x36000378)  # fileExists false rejects
        self.assertEqual(word(0x1000651e8), 0xb85343a8)  # reloads startAccessing Bool
        self.assertEqual(word(0x1000651ec), 0x3707f528)  # only true appends candidate

    def test_history_default_predicate_dispatches_to_category_nil_implementation(self):
        proof = json.loads((ROOT / '.local/p0-repair/phase-8/list-predicate-proof.json').read_text())
        data = (ROOT / proof['binary']['path']).read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), proof['binary']['sha256'])
        category = proof['category']
        bindings = chained_bindings(data)
        self.assertEqual(bindings[int(category['class_slot'], 16)]['symbol'], '_OBJC_CLASS_$_NSManagedObject')
        method = next(m for m in category['methods'] if m['selector'] == 'defaultPredicate')
        _, _, relative_imp = struct.unpack_from('<iii', data, method['entry_file_offset'])
        self.assertEqual(int(method['entry'], 16) + 8 + relative_imp, 0x10032c5c8)
        start = method['selector_file_offset']
        self.assertEqual(data[start:data.index(b'\0', start)], b'defaultPredicate')
        for ref in proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / ref['path'])[ref['address']]['sha256'], ref['sha256'])
        for segment in proof['machine_segments']:
            raw = data[segment['file_offset']:segment['file_offset']+segment['length']]
            self.assertEqual(hashlib.sha256(raw).hexdigest(), segment['sha256'])
        word = lambda address: struct.unpack_from('<I', data, address - 0x100000000)[0]
        self.assertEqual(word(0x10032c5c8), 0x17fffc66)  # B 32b760
        self.assertEqual(word(0x10032b760), 0xd2800000)  # MOV x0,#0 (nil)
        self.assertEqual(parse_macho(ROOT / proof['binary']['path'])['stubs']['0x100bfbe98']['symbol'],
                         '_objc_autoreleaseReturnValue')


if __name__ == '__main__':
    unittest.main()
