"""Stack is an ordered occurrence queue, with source/binary evidence and no native execution."""
from native_title_scope_contract import NEW_PATH as NATIVE_TITLE_PATH
from item_observation_scope_contract import NEW_PATH as ITEM_OBSERVATION_PATH
from native_title_scope_contract import pre_native_title_bytes
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment
from stack_occurrence_scope_contract import CHANGES, pre_stack_occurrences
from stack_native_input_scope_contract import pre_stack_native_inputs, pre_stack_native_inputs_bytes


class StackOccurrenceContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-81'
        cls.proof = json.loads((cls.phase / 'stack-occurrence-contract.json').read_text())
        cls.base = json.loads((cls.phase / 'baseline.json').read_text())
        cls.paths = dict(ui='replica/Sources/Pasto/UI/ReplicaUIController.swift',
            table='replica/Sources/PastoCore/OriginalStackTableController.swift',
            view='replica/Sources/Pasto/UI/AuxiliaryViews.swift')
        cls.source = {k: pre_stack_native_inputs((ROOT / p).read_text()) for k, p in cls.paths.items()}
        cls.ui=cls.source['ui'];cls.table=cls.source['table'];cls.view=cls.source['view']

    def before(self, key): return (self.phase / 'before' / self.paths[key]).read_text()
    def original(self, address):
        r=next(r for r in self.proof['original_fragments'] if r['address']==address)
        return original_fragment((ROOT / r['path']).read_text(), address[2:])

    def test_eight_original_fragments_and_array_mutation_bytes_are_bound(self):
        self.assertEqual(len(self.proof['original_fragments']),8)
        for r in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / r['path'])[r['address']]['sha256'],r['sha256'])
        r=self.proof['binary'];raw=(ROOT/r['path']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),r['sha256'])
        self.assertEqual(len(self.proof['ARM_words']),8)
        for r in self.proof['ARM_words']:
            a=int(r['address'],16)-0x100000000;self.assertEqual(raw[a:a+4].hex(),r['bytes'])
        for r in self.proof['arm_disassemblies']:
            self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])

    def test_original_capture_inserts_exactly_one_occurrence_without_identity_filter(self):
        capture=self.original('0x10008339c');insert=self.original('0x100089a18');replace=self.original('0x1000898fc')
        self.assertIn('FUN_1001b8054(&local_58,0,',capture)
        self.assertIn('if (local_58 == 0)',capture)
        self.assertIn('FUN_100089a18(_Var12,_Var12,local_58)',capture)
        self.assertIn('lVar3 = 1 - (param_2 - param_1)',insert)
        self.assertIn('FUN_1000898fc(param_1,param_2,1,param_3)',insert)
        self.assertIn('*(long *)(puVar10 + 0x10) = lVar9 + lVar5',replace)
        self.assertIn('*puVar1 = param_4',replace)
        for f in [capture,insert,replace]: self.assertNotIn('isEqual_',f)
        words={int(r['address'],16):int.from_bytes(bytes.fromhex(r['bytes']),'little') for r in self.proof['ARM_words']}
        for pc,target in [(0x10008361c,0x100089a18),(0x100089ac4,0x1000898fc)]:
            d=words[pc]&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(pc+d*4,target)
        self.assertEqual(words[0x100089aa8],0x52800022)  # replace one object

    def test_original_head_and_arbitrary_row_remove_one_index_not_all_equal_entities(self):
        head=self.original('0x10008413c');row=self.original('0x10008499c');remove=self.original('0x100084bc4')
        self.assertIn('FUN_100089bec(0,1)',head)
        self.assertIn('FUN_100084bc4(param_1)',row)
        self.assertIn('lVar7 = *(ulong *)(uVar6 + 0x10) - 1',remove)
        self.assertIn('*(long *)(uVar6 + 0x10) = lVar7',remove)
        self.assertIn('_memmove',remove)
        self.assertNotIn('isEqual_',remove)

    def test_three_current_sources_and_frozen_after_snapshots_are_bound(self):
        self.assertEqual(set(self.proof['current_sources']),set(self.paths.values()))
        for p,h in self.proof['current_sources'].items():
            raw=pre_stack_native_inputs_bytes(ROOT/p);self.assertEqual(hashlib.sha256(raw).hexdigest(),h)
            self.assertEqual(raw,(self.phase/'after'/p).read_bytes())

    def test_add_to_stack_only_removes_old_dedup_guard_and_preserves_direction_and_animation(self):
        old=body(self.before('ui'),'func addToStack(');current=body(self.ui,'func addToStack(')
        guard='        guard !stackIDs.contains(item.id) else { return }\n'
        self.assertEqual(old.count(guard),1);self.assertEqual(current,old.replace(guard,'',1))
        self.assertIn('stackIDs.insert(item.id, at: append ? stackIDs.count : 0)',current)
        self.assertIn('updated: stackItems, at: insertionIndex',current)
        for token in ['Set(', '.contains(item.id)', '.removeAll']:
            self.assertNotIn(token,current)

    def test_value_stack_projection_and_preference_array_preserve_repeated_ids(self):
        stack=body(self.ui,'var stackItems:')
        self.assertIn('stackIDs.compactMap',stack)
        self.assertNotIn('Set(',stack)
        self.assertEqual(stack,body(self.before('ui'),'var stackItems:'))
        declaration=body(self.ui,'@Published var stackIDs:')
        self.assertIn('store.preferences.stackItemIDs = stackIDs',declaration)
        self.assertNotIn('Set(',declaration)
        models=(ROOT/'replica/Sources/PastoCore/Models.swift').read_text()
        self.assertIn('public var stackItemIDs: [UUID]',models)

    def test_actual_table_cell_factory_passes_numeric_row_alongside_item(self):
        self.assertIn('public var makeCell: ((ClipboardItem, Int) -> NSView)?',self.table)
        f=body(self.table,'public func tableView(_ tableView: NSTableView, viewFor')
        self.assertIn('snippets.indices.contains(row)',f)
        self.assertIn('return makeCell?(snippets[row], row)',f)
        self.assertIn('controller.makeCell = { [weak controller] item, row in',self.view)
        self.assertIn('let expectedIDs = controller?.snippets.map(\\.id) ?? []',self.view)

    def test_current_context_remove_and_paste_remove_captured_row_occurrence(self):
        stack=body(self.view,'struct ReplicaStackTable:')
        self.assertEqual(stack.count('controller?.removeRow(at: row, expectedIDs: expectedIDs)'),2)
        self.assertNotIn('stackIDs.removeAll',stack)
        self.assertIn('if state.controller?.paste(item: item, plainTextOnly: false) == true',stack)
        self.assertIn('Button("移除") { controller?.removeRow(at: row, expectedIDs: expectedIDs) }',stack)
        # Required declaration and all call labels match, including the indexed factory's two arguments.
        self.assertEqual(self.table.count('public func removeRow(at row: Int, expectedIDs: [UUID])'),1)
        self.assertNotIn('public func removeSnippet(at',self.table)

    def test_shared_remove_row_guards_snapshot_and_callback_revision_before_one_removal(self):
        f=body(self.table,'public func removeRow(at row:')
        order=['snippets.map(\\.id) == expectedIDs','snippets.indices.contains(row)',
               'let revision = snippetsRevision','removeSnippet(expectedIDs, row)',
               'snippetsRevision == revision','snippets.remove(at: row)',
               'tableView.removeRows(at: IndexSet(integer: row), withAnimation: .slideUp)','f_100083a20()']
        self.assertEqual([f.index(t) for t in order],sorted(f.index(t) for t in order))
        self.assertEqual(f.count('snippets.remove(at: row)'),1)
        self.assertNotIn('removeAll',f)
        self.assertNotIn('firstIndex',f)

    def test_native_trailing_action_delegates_same_row_helper_and_keeps_edge_gate(self):
        f=body(self.table,'public func tableView(_ tableView: NSTableView, rowActionsForRow')
        self.assertIn('guard edge == .trailing else { return [] }',f)
        self.assertIn('[weak self]',f)
        self.assertIn('self.removeRow(at: row, expectedIDs: self.snippets.map(\\.id))',f)
        self.assertNotIn('snippets.remove(at:',f)

    def test_existing_visible_offset_callback_removes_only_target_stack_index(self):
        # updateNSView is scoped to the actual Stack table, not other representables in this file.
        stack=body(self.view,'struct ReplicaStackTable:')
        callback=body(stack,'controller.removeSnippet =')
        self.assertIn('visibleOffsets.map({ state.stackIDs[$0] }) == expectedIDs',callback)
        self.assertIn('state.stackIDs.remove(at: visibleOffsets[row])',callback)
        self.assertNotIn('Set(',callback);self.assertNotIn('removeAll',callback)
        old=body(body(self.before('view'),'struct ReplicaStackTable:'),'controller.removeSnippet =')
        self.assertEqual(callback,old)

    def test_head_consumption_reverse_and_insert_remove_animations_are_unchanged(self):
        for marker in ['func consumeStackHead()', 'func reverseStack()', 'func captureIntoStack(', 'private func captureLatestItemIntoStack()']:
            self.assertEqual(body(self.ui,marker),body(self.before('ui'),marker))
        for marker in ['public func didConsumeHead(', 'public func didInsertSnippet(', 'public func updateSnippets(', 'public func f_100083a20()']:
            self.assertEqual(body(self.table,marker),body(self.before('table'),marker))
        head=body(self.ui,'func consumeStackHead()')
        self.assertIn('state.stackIDs.remove(at: index)',head)
        self.assertNotIn('removeAll',head)

    def test_OCR_expected_image_guards_are_reused_without_OCR_or_writer_edits(self):
        for p,h in self.proof['ocr_current_boundary']['source_hashes'].items():
            self.assertEqual(hashlib.sha256(pre_native_title_bytes(ROOT/p)).hexdigest(),h)
        ocr=(ROOT/'replica/Sources/PastoCore/OCR.swift').read_text()
        f=body(ocr,'public func recognizeImageDocument(')
        self.assertLess(f.index('try await ImageTextRecognizer.recognizeDocument(imageData: data)'),f.index('saveRecognizedDocument(id: id, document: document, expectedImageData: data)'))
        store=(ROOT/'replica/Sources/PastoCore/ClipboardStore.swift').read_text()
        save=body(store,'func saveRecognizedDocument(')
        self.assertIn('state.items[i].imageData == expectedImageData else { return }',save)
        writer=(ROOT/'replica/Sources/PastoCore/Pasteboard.swift').read_text()
        f=body(writer,'private func writeToPasteboard(ids:')
        self.assertIn('item.imageData == recognizedImageData else { throw RecognizedImageTextCopyError.imageChanged }',f)

    def test_new_backlog_preserves_all_old_records_and_adds_one_repaired_P1_finite_case(self):
        old=json.loads((ROOT/'reports/replica/p0-p1-difference-backlog-v16.json').read_text())
        new=json.loads((ROOT/'reports/replica/p0-p1-difference-backlog-v17.json').read_text())
        self.assertEqual(new['groups'][:-1],old['groups'])
        self.assertEqual(new['counts']['difference_records'],164)
        self.assertEqual(new['counts']['p0_records'],69)
        self.assertEqual(new['counts']['p1_additional_records'],95)
        group=new['groups'][-1];self.assertEqual(group['function_ids'],['Paste:0x10008339c'])
        self.assertTrue(group['records'][0]['repair']['verified_finite_contract'])
        self.assertEqual(self.proof['repaired_finite_contracts'],['Paste:0x10008339c'])
        self.assertEqual(self.proof['remaining_confirmed_differences'],['Paste:0x1003544dc'])
        self.assertFalse(new['full_function_migration_verified'])

    def test_only_six_reviewed_hunks_change_three_files_without_schema_or_package(self):
        self.assertEqual(len(CHANGES),6)
        for key in self.paths:self.assertEqual(pre_stack_occurrences(self.source[key]),self.before(key))
        from stack_registration_scope_contract import APP_PATH, pre_stack_registration
        def sha(p):
            raw=pre_stack_native_inputs_bytes(ROOT/p)
            if p == APP_PATH:
                raw=pre_stack_registration(raw.decode()).encode()
            return hashlib.sha256(raw).hexdigest()
        self.assertEqual({p for p,h in self.base['production'].items() if sha(p)!=h},set(self.paths.values()))
        self.assertEqual({str(p.relative_to(ROOT)) for p in (ROOT/'replica/Sources').rglob('*') if p.is_file()} - {NATIVE_TITLE_PATH, ITEM_OBSERVATION_PATH},set(self.base['production']))
        for p in ['replica/Package.swift','package.json']:
            self.assertEqual(sha(p),self.base['other'][p])

    def test_finite_duplicate_contract_does_not_claim_complete_Stack_or_live_provider(self):
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertTrue(any('lifetime' in r for r in self.proof['remaining_work']))
        self.assertTrue(any('Unknown04430c/0f733c' in r for r in self.proof['remaining_work']))
        self.assertTrue(any('in-memory' in r for r in self.proof['adaptations']))


if __name__=='__main__':unittest.main()
