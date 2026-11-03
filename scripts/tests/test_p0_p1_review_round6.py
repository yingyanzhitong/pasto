"""Read-only source/provenance checks; never compile or execute the applications."""
import hashlib
import json
import struct
import unittest
from collections import Counter

from test_offline_p0_contracts import ROOT, body
from test_p0_p1_review_round2 import digest, fragment
from test_p0_p1_review_round4 import target_of_bl


class P0P1ReviewRound6(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((ROOT / 'reports/replica/p0-p1-review-round6.json').read_text())
        cls.prior = json.loads((ROOT / 'reports/replica/p0-p1-review-round5.json').read_text())
        cls.rows = {row['function_id']: row for row in cls.report['records']}
        cls.proof = json.loads((ROOT / cls.report['static_proof']['path']).read_text())
        cls.binary = (ROOT / cls.proof['binary_path']).read_bytes()

    def test_only_previous_unknowns_change_without_inflating_migration(self):
        old = {row['function_id']: row for row in self.prior['records']}
        changed = set(self.report['round_delta']['reviewed_function_ids'])
        self.assertEqual(changed, {fid for fid, row in old.items() if row['status'] == 'unclosed'})
        self.assertEqual(len(changed), 40)
        self.assertEqual(set(self.rows), set(old))
        self.assertEqual(self.report['comparison_denominator'], 489)
        for fid in set(old) - changed:
            self.assertEqual(self.rows[fid], old[fid])
        counts = Counter(row['status'] for row in self.rows.values())
        self.assertEqual(dict(counts), self.report['outcomes'])
        resolved = len(self.rows) - counts['unclosed']
        self.assertEqual(resolved, self.report['resolved_review_records'])
        self.assertEqual(round(resolved / len(self.rows) * 100, 2), self.report['resolved_comparison_percent'])
        self.assertEqual(resolved - self.prior['resolved_review_records'], self.report['round_delta']['new_resolved'])
        self.assertIsNone(self.report['full_priority_completion_percent'])
        self.assertTrue(self.report['scope_provisional'])
        self.assertFalse(any(row['full_function_migration_verified'] for row in self.rows.values()))

    def test_all_sources_fragments_and_instruction_ranges_remain_bound(self):
        for path, sha in self.report['source_inputs'].items():
            self.assertEqual(digest(path), sha, path)
        self.assertEqual(digest(self.report['static_proof']['path']), self.report['static_proof']['sha256'])
        self.assertEqual(hashlib.sha256(self.binary).hexdigest(), self.proof['binary_sha256'])
        for fid in self.report['round_delta']['reviewed_function_ids']:
            row = self.rows[fid]
            for proof in [dict(row['original'], function_id=fid)] + row.get('supporting_original_fragments', []):
                address = proof.get('address') or proof['function_id'].split(':')[1]
                self.assertEqual(hashlib.sha256(fragment(address, proof['path']).encode()).hexdigest(), proof['sha256'])
            for ref in row['current_references']:
                self.assertEqual(digest(ref['path']), ref['sha256'])
                self.assertTrue(ref['symbol'] in (ROOT / ref['path']).read_text())

        def visit(value):
            if isinstance(value, dict):
                if 'slice_file_offset' in value and 'bytes' in value:
                    data = bytes.fromhex(value['bytes'])
                    offset = value['slice_file_offset']
                    self.assertEqual(self.binary[offset:offset + len(data)], data)
                for item in value.values():
                    visit(item)
            elif isinstance(value, list):
                for item in value:
                    visit(item)
        visit(self.proof)

    def test_clear_title_is_a_new_counterexample_not_the_retracted_source_claim(self):
        row = self.rows['Paste:0x100364ab4']
        self.assertEqual(row['status'], 'difference_confirmed')
        self.assertEqual(next(row for row in self.prior['records'] if row['function_id'].endswith('364ab4'))['status'], 'unclosed')
        support = {proof['function_id']: proof for proof in row['supporting_original_fragments']}
        original = fragment('0x1003bae08', support['Paste:0x1003bae08']['path'])
        self.assertIn('trimmingCharacters', original)
        self.assertIn('SVar11 = (String)ZEXT816(0)', original)
        self.assertIn('FUN_1002ff310(FUN_1003bbb10', original)
        setter = fragment('0x100364ab4', row['original']['path'])
        self.assertIn('pNVar7 = (NSString *)0x0', setter)
        self.assertIn('objc_stub::setTitle_(param_1,pNVar7)', setter)
        source = (ROOT / 'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
        prompt = body(source, 'private func prompt(title: String, message: String, initial: String) -> String?')
        self.assertIn('return name.isEmpty ? nil : name', prompt)
        rename = body(source, 'func renameItem(_ item: ClipboardItem)')
        self.assertLess(rename.index('guard let title = prompt'), rename.index('store.updateItem'))
        self.assertIn('撤回', row['evidence_note'])

    def test_native_title_nil_reaches_the_actual_setter_instruction(self):
        words = struct.unpack('<9I', bytes.fromhex(self.proof['clear_title'][1]['bytes']))
        self.assertEqual(words[3], 0xd2800014)  # mov x20,#0 for nil NSString
        self.assertEqual(words[4], 0xaa1303e0)  # self x19 -> x0
        self.assertEqual(words[5], 0xaa1403e2)  # nil x20 -> ObjC argument x2
        self.assertEqual(target_of_bl(0x100364bc8, words[6]), 0x100c0e340)
        original = fragment('0x1003bbb70', self.rows['Paste:0x100364ab4']['supporting_original_fragments'][5]['path'])
        self.assertIn('*param_1 = uVar1', original)
        self.assertIn('param_1[1] = uVar2', original)

    def test_restore_target_is_bound_to_history_repository_not_arbitrary_selected_group(self):
        proof = self.proof['history_repository']
        self.assertEqual(bytes.fromhex(proof['protocol_name']['bytes']), b'ListRepositoryProtocol\0')
        self.assertEqual(bytes.fromhex(proof['type_name']['bytes']), b'ListRepository\0')
        composite = struct.unpack('<3Q', bytes.fromhex(proof['composite']['bytes']))
        read_table = 0x100000000 + (composite[1] & ((1 << 36) - 1))
        self.assertEqual(int(proof['read_slot']['address'], 16), read_table + 0x28)
        pointer, = struct.unpack('<Q', bytes.fromhex(proof['read_slot']['bytes']))
        self.assertEqual(0x100000000 + (pointer & ((1 << 36) - 1)), 0x100368230)
        initializer = struct.unpack('<7I', bytes.fromhex(self.proof['history_initialization'][0]['bytes']))
        self.assertEqual(target_of_bl(0x10037b8ec, initializer[4]), 0x1002ff2ec)
        self.assertEqual(initializer[6], 0xf9005260)  # return -> manager+0xa0
        factory = struct.unpack('<3I', bytes.fromhex(self.proof['history_initialization'][3]['bytes']))
        self.assertEqual(factory[1], 0x52800022)  # rawType = 1, history
        self.assertEqual(target_of_bl(0x100368504, factory[2]), 0x100c0d560)
        self.assertEqual(self.rows['Paste:0x10037b620']['status'], 'unclosed')

    def test_original_query_keeps_weak_loaded_owner_across_await_until_publish_cleanup(self):
        begin, end = self.proof['query_owner']
        start_words = struct.unpack('<11I', bytes.fromhex(begin['bytes']))
        self.assertEqual(target_of_bl(0x10036025c, start_words[2]), 0x100bfcc30)
        self.assertEqual(start_words[3], 0xf90062c0)  # x0 strong owner -> frame+0xc0
        end_words = struct.unpack('<6I', bytes.fromhex(end['bytes']))
        self.assertEqual(end_words[1], 0xf94062d4)  # owner from frame+0xc0
        self.assertEqual(end_words[3], 0xaa1403e0)
        self.assertEqual(target_of_bl(0x1003607e8, end_words[4]), 0x100bfc9c0)
        row = self.rows['Paste:0x1003646a8']
        self.assertEqual(row['status'], 'local_contract_consistent')
        self.assertIn('Paste:0x1003607c4', {proof['function_id'] for proof in row['supporting_original_fragments']})
        source = body((ROOT / 'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text(),
                      'private func replaceQuery(with nodes: [OriginalSearchQueryNode])')
        self.assertIn('Task { [weak self]', source)
        self.assertLess(source.index('guard let self'), source.index('await'))
        self.assertIn('identifiers = found', source[source.index('await'):])
        self.assertIn('self.error = error', source[source.index('await'):])

    def test_zero_result_subject_connection_and_external_transaction_failure_stay_unknown(self):
        for address in ['360808', '3647d4', '368560']:
            self.assertEqual(self.rows['Paste:0x100' + address]['status'], 'unclosed')
        self.assertIn('连接', self.rows['Paste:0x100360808']['evidence_note'])
        self.assertNotEqual(self.rows['Paste:0x100368560']['status'], 'difference_confirmed')

    def test_search_timeout_compares_explicit_animation_not_layout_api_names(self):
        row = self.rows['Paste:0x100021b04']
        self.assertEqual(row['status'], 'difference_confirmed')
        supporting = {proof['function_id']: proof for proof in row['supporting_original_fragments']}
        original = fragment('0x10021cadc', supporting['Paste:0x10021cadc']['path'])
        self.assertIn('NSAnimationContext::runAnimationGroup_completionHandler_', original)
        panel = (ROOT / 'replica/Sources/Pasto/UI/PanelViews.swift').read_text()
        self.assertNotIn('withAnimation', panel)
        self.assertNotIn('.animation(', panel)
        controller = (ROOT / 'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
        closed = body(controller, 'private func beginClosedState()')
        timer = closed[closed.index('closedSearchTimer = Timer.scheduledTimer'):]
        self.assertIn('self.state.searchVisible = false', timer)
        self.assertNotIn('runAnimationGroup', timer)


if __name__ == '__main__':
    unittest.main()
