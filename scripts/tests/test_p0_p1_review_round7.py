"""Source and static provenance checks; no compiler, app, SDK execution or network."""
import hashlib
import json
import struct
import unittest
from collections import Counter

from test_offline_p0_contracts import ROOT, body
from test_p0_p1_review_round2 import digest, fragment
from test_p0_p1_review_round4 import target_of_bl


class P0P1ReviewRound7(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((ROOT / 'reports/replica/p0-p1-review-round7.json').read_text())
        cls.prior = json.loads((ROOT / 'reports/replica/p0-p1-review-round6.json').read_text())
        cls.rows = {row['function_id']: row for row in cls.report['records']}
        cls.proof = json.loads((ROOT / cls.report['static_proof']['path']).read_text())
        cls.binary = (ROOT / cls.proof['binary_path']).read_bytes()

    def test_unknowns_only_and_finite_comparisons_do_not_become_full_migration(self):
        old = {row['function_id']: row for row in self.prior['records']}
        changed = set(self.report['round_delta']['reviewed_function_ids'])
        self.assertEqual(changed, {fid for fid, row in old.items() if row['status'] == 'unclosed'})
        self.assertEqual(len(changed), 32)
        self.assertEqual(set(self.rows), set(old))
        for fid in set(old) - changed:
            self.assertEqual(old[fid], self.rows[fid])
        counts = Counter(row['status'] for row in self.rows.values())
        self.assertEqual(dict(counts), self.report['outcomes'])
        self.assertEqual(self.report['resolved_review_records'], len(self.rows) - counts['unclosed'])
        self.assertEqual(self.report['resolved_comparison_percent'], round((len(self.rows) - counts['unclosed']) / 489 * 100, 2))
        self.assertEqual(self.report['round_delta']['new_resolved'],
                         self.report['resolved_review_records'] - self.prior['resolved_review_records'])
        self.assertTrue(self.report['scope_provisional'])
        self.assertIsNone(self.report['full_priority_completion_percent'])
        self.assertFalse(any(row['full_function_migration_verified'] for row in self.rows.values()))

    def test_each_primary_input_reference_and_instruction_range_is_hash_bound(self):
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
                    offset = value['slice_file_offset']; raw = bytes.fromhex(value['bytes'])
                    self.assertEqual(self.binary[offset:offset + len(raw)], raw)
                for part in value.values(): visit(part)
            elif isinstance(value, list):
                for part in value: visit(part)
        visit(self.proof)

    def test_restore_thunk_captures_and_forwards_the_unmodified_selection_and_manager(self):
        preserve, saved, capture, thunk = self.proof['restore_capture']
        self.assertEqual(struct.unpack('<3I', bytes.fromhex(preserve['bytes'])),
                         (0xaa1403fc, 0xaa0103f4, 0xaa0003f3))  # manager x28, selection x19
        self.assertEqual(struct.unpack('<3I', bytes.fromhex(saved['bytes']))[1], 0xf9000bf3)  # selection -> sp+16
        capture_words = struct.unpack('<7I', bytes.fromhex(capture['bytes']))
        self.assertEqual(capture_words[0], 0xf9400bf6)  # reload selection
        self.assertEqual(capture_words[1], 0xa90673f6)  # selection/manager -> closure slots
        self.assertEqual(target_of_bl(0x10037a5ac, capture_words[6]), 0x1002ff310)
        thunk_words = struct.unpack('<6I', bytes.fromhex(thunk['bytes']))
        self.assertEqual(thunk_words[2], 0xa9410a81)  # ldp x1,x2,[x20,#16]
        self.assertEqual(target_of_bl(0x10037b62c, thunk_words[3]), 0x10037ade4)
        self.assertEqual(thunk_words[-1], 0xd65f03c0)  # ret, no local filtering/catch branch
        row = self.rows['Paste:0x10037b620']
        self.assertEqual(row['status'], 'local_contract_consistent')
        self.assertIn('有限', row['contract'])
        current = body((ROOT / 'replica/Sources/PastoCore/Pasteboard.swift').read_text(),
                       'private func writeToPasteboard(ids: [UUID], pasteboard: NSPasteboard,')
        self.assertIn('let selected = try ids.map', current)
        self.assertIn('try recordRestoredItems(ids)', current)
        self.assertNotIn('ids.filter', current)

    def test_repository_cache_stores_the_callback_result_not_the_callback_address(self):
        row = self.rows['Paste:0x1003b8bfc']
        self.assertEqual(row['status'], 'unclosed')
        words = struct.unpack('<11I', bytes.fromhex(self.proof['cached_returned_object'][0]['bytes']))
        self.assertEqual(target_of_bl(0x1003b8c28, words[3]), 0x10035a864)
        self.assertEqual(words[4], 0xaa0003f3)  # return x0 -> x19
        self.assertEqual(words[6], 0xf9000a80)  # return x0 -> owner+16
        supporting = {proof['function_id']: proof for proof in row['supporting_original_fragments']}
        self.assertTrue({'Paste:0x10035a864', 'Paste:0x10035a89c', 'Paste:0x10035bb5c'} <= set(supporting))
        transaction = fragment('0x10035a89c', supporting['Paste:0x10035a89c']['path'])
        self.assertIn('NSManagedObjectContext::_performAndWait()', transaction)
        self.assertIn('return local_58', transaction)
        self.assertIn('不是', row['evidence_note'])

    def test_legacy_nil_pinboard_type_is_two_in_the_actual_compatibility_mapping(self):
        row = self.rows['Paste:0x1003b83c4']
        self.assertEqual(row['status'], 'local_contract_consistent')
        source = (ROOT / 'replica/Sources/Pasto/UI/ReplicaSearchSuggestionSource.swift').read_text()
        self.assertIn('($0.rawType ?? 2) == 2', source)
        actual = body((ROOT / 'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text(),
                      'func selectedItemTargetLists() -> [UUID?]')
        self.assertIn('let items = selectedItems', actual)
        self.assertIn('items.count == 1', actual)
        self.assertLess(actual.index('lists.append(nil)'), actual.index('store.pinboardOwner'))
        self.assertIn('owner.rawType == 2 || owner.rawType == nil', actual)
        self.assertIn('兼容', row['evidence_note'])

    def test_index_differences_bind_real_force_cancellation_and_persistent_state_branches(self):
        for address in ['2ea770', '2eaa10', '2f2280', '2f2648']:
            self.assertEqual(self.rows['Paste:0x100' + address]['status'], 'difference_confirmed')
        row = self.rows['Paste:0x1002ea770']
        support = {proof['function_id']: proof for proof in row['supporting_original_fragments']}
        builder = fragment('0x1002e3ce8', support['Paste:0x1002e3ce8']['path'])
        self.assertIn('setIsUpdate_', builder)
        source = (ROOT / 'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text()
        current_builder = body(source, 'private func searchableItem(_ entry: Entry) -> CSSearchableItem')
        self.assertNotIn('isUpdate', current_builder)
        target = body(source, 'private func reindexTargets(_ identifiers: [String]) async throws')
        self.assertIn('try Task.checkCancellation()', target)
        self.assertIn('if !journalCompleted { needsReset = true }', source)

    def test_unproved_consumers_identity_and_weak_lifetimes_are_not_called_full_matches(self):
        for address in ['3611b0', '360808', '3647d4', '0f733c']:
            self.assertEqual(self.rows['Paste:0x100' + address]['status'], 'unclosed')
        for address in ['041860', '041e08', '099adc']:
            row = self.rows['Paste:0x100' + address]
            self.assertFalse(row['full_function_migration_verified'])
            self.assertIn('weak_owner_deallocation_gate', row['coverage_boundaries']['not_verified'])
            self.assertEqual(row['coverage_boundaries']['covered'], ['live_owner_query_or_identifier_delivery'])
        checksum = (ROOT / 'replica/Sources/PastoCore/Pasteboard.swift').read_text()
        self.assertIn('encoder.encode(originalPasteboardItems(from: first))', checksum)
        self.assertIn('解码', self.rows['Paste:0x1003611b0']['evidence_note'])


if __name__ == '__main__':
    unittest.main()
