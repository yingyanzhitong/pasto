"""Static-source/provenance checks. No Swift/ObjC compilation or app execution."""
import hashlib
import json
import struct
import unittest
from collections import Counter

from test_offline_p0_contracts import ROOT, body
from test_p0_p1_review_round2 import digest, fragment
from test_p0_p1_review_round4 import target_of_bl


class P0P1ReviewRound8(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((ROOT / 'reports/replica/p0-p1-review-round8.json').read_text())
        cls.prior = json.loads((ROOT / 'reports/replica/p0-p1-review-round7.json').read_text())
        cls.rows = {row['function_id']: row for row in cls.report['records']}
        cls.proof = json.loads((ROOT / cls.report['static_proof']['path']).read_text())
        cls.binary = (ROOT / cls.proof['binary_path']).read_bytes()

    def test_p0_conclusion_coverage_is_not_full_priority_or_migration_completion(self):
        old = {row['function_id']: row for row in self.prior['records']}
        reviewed = set(self.report['round_delta']['reviewed_function_ids'])
        self.assertEqual(reviewed, {fid for fid, row in old.items() if row['status'] == 'unclosed'})
        self.assertEqual(len(reviewed), 16)
        self.assertEqual(set(self.rows), set(old))
        for fid in set(old) - reviewed:
            self.assertEqual(self.rows[fid], old[fid])
        counts = Counter(row['status'] for row in self.rows.values())
        self.assertEqual(dict(counts), self.report['outcomes'])
        self.assertEqual(self.report['resolved_review_records'], len(self.rows) - counts['unclosed'])
        self.assertEqual(self.report['resolved_comparison_percent'], round((len(self.rows) - counts['unclosed']) / 489 * 100, 2))
        self.assertEqual(self.report['p0_component']['resolved'], 243)
        self.assertEqual(self.report['p0_component']['unclosed'], 0)
        self.assertTrue(self.report['scope_provisional'])
        self.assertIsNone(self.report['full_priority_completion_percent'])
        self.assertFalse(any(row['full_function_migration_verified'] for row in self.rows.values()))
        self.assertFalse(self.report['production_source_edited'])

    def test_complete_fragments_real_references_and_instruction_ranges_are_bound(self):
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
                self.assertIn(ref['symbol'], (ROOT / ref['path']).read_text())
        def visit(value):
            if isinstance(value, dict):
                if 'slice_file_offset' in value and 'bytes' in value:
                    raw = bytes.fromhex(value['bytes']); offset = value['slice_file_offset']
                    self.assertEqual(self.binary[offset:offset + len(raw)], raw)
                for part in value.values(): visit(part)
            elif isinstance(value, list):
                for part in value: visit(part)
        visit(self.proof)

    def test_get_or_create_miss_passes_nil_identifier_to_the_real_creation_function(self):
        words = struct.unpack('<17I', bytes.fromhex(self.proof['miss_branch'][0]['bytes']))
        self.assertEqual(target_of_bl(0x1003611e4, words[2]), 0x1003214c8)
        self.assertEqual(words[4] & 0xff00001f, 0xb4000000)  # cbz x0, miss
        offset = (words[4] >> 5) & 0x7ffff
        if offset & (1 << 18): offset -= 1 << 19
        self.assertEqual(0x1003611ec + offset * 4, 0x10036120c)
        self.assertEqual(words[12], 0xd2800001)  # x0 already nil, x1 explicitly nil
        self.assertEqual(words[13], 0xaa1603e2)  # same content array x22 -> x2
        self.assertEqual(target_of_bl(0x100361218, words[15]), 0x100360d9c)
        row = self.rows['Paste:0x1003611b0']
        self.assertEqual(row['status'], 'difference_confirmed')
        self.assertEqual(row['shared_difference_origin'], 'Paste:0x100360d9c')
        self.assertIn('unknown_archive_identity_equivalence', row['coverage_boundaries']['not_verified'])

    def test_default_identifier_counterexample_uses_original_checksum_string_not_an_integer_guess(self):
        create, setter = self.proof['identifier_from_checksum']
        create_words = struct.unpack('<11I', bytes.fromhex(create['bytes']))
        self.assertEqual(target_of_bl(0x100360df4, create_words[7]), 0x1003216bc)
        self.assertEqual(create_words[9], 0xaa0103f7)  # checksum String x1 -> x23
        self.assertEqual(create_words[10], 0xaa0003fa)  # checksum String x0 -> x26
        setter_words = struct.unpack('<9I', bytes.fromhex(setter['bytes']))
        self.assertEqual(setter_words[:2], (0xaa1a03e0, 0xaa1703e1))
        self.assertEqual(target_of_bl(0x100360ef4, setter_words[8]), 0x100c0c0e0)
        format_words = struct.unpack('<4I', bytes.fromhex(self.proof['hex_format']['bytes']))
        low = (format_words[0] >> 5) & 0xffff
        high = (format_words[1] >> 5) & 0xffff
        self.assertEqual(struct.pack('<I', low | (high << 16)), b'%02x')
        case = self.proof['static_counterexample']
        self.assertEqual(hashlib.md5(case['input'].encode()).hexdigest(), case['original_identifier'])
        self.assertEqual(case['original_identifier'], 'd84e1a0775d13912d49cd129e7e579ba')
        self.assertFalse(case['original_app_executed'])
        self.assertFalse(case['swift_executed'])
        model = (ROOT / 'replica/Sources/PastoCore/Models.swift').read_text()
        self.assertIn('public init(id: UUID = UUID(),', model)
        persistence = (ROOT / 'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text()
        self.assertIn('entity: "Item", key: { $0.id.uuidString }', persistence)

    def test_actual_work_and_completion_descriptors_are_not_confused(self):
        work = self.proof['target_work']
        inner = work['inner_descriptor']; completion = work['completion_descriptor']
        rel, frame_size = struct.unpack('<iI', bytes.fromhex(inner['bytes']))
        self.assertEqual(int(inner['address'], 16) + rel, 0x1002f3c8c)
        self.assertEqual(frame_size, 32)
        rel, _ = struct.unpack('<iI', bytes.fromhex(completion['bytes']))
        self.assertEqual(int(completion['address'], 16) + rel, 0x1002eb754)
        force = struct.unpack('<7I', bytes.fromhex(work['force_branch']['bytes']))
        self.assertEqual(force[1], 0x52800021)  # w1=1
        self.assertEqual(force[-1] >> 26, 0b000101)  # B rather than BL
        immediate = force[-1] & 0x3ffffff
        if immediate & (1 << 25): immediate -= 1 << 26
        self.assertEqual(0x1002f2cfc + immediate * 4, 0x1002ea770)
        self.assertEqual(self.rows['Paste:0x1002f26a8']['status'], 'difference_confirmed')
        self.assertEqual(self.rows['Paste:0x1002f2690']['status'], 'local_contract_consistent')

    def test_excluded_network_menu_branches_do_not_resolve_the_offline_menu(self):
        row = self.rows['Paste:0x100021f00']
        self.assertEqual(row['status'], 'unclosed')
        self.assertTrue(row['excluded_original_branches'])
        self.assertIn('Cloud', json.dumps(row['excluded_original_branches'], ensure_ascii=False))
        for address in ['360808', '3647d4', '052734', '0f733c']:
            self.assertEqual(self.rows['Paste:0x100' + address]['status'], 'unclosed')

    def test_group_creation_difference_is_the_proven_local_operation_order(self):
        row = self.rows['Paste:0x100368560']
        self.assertEqual(row['status'], 'difference_confirmed')
        original = fragment('0x100368560', row['original']['path'])
        self.assertLess(original.index('objc_stub::initWithContext_'), original.index('Foundation::JSONEncoder::_encode'))
        source = body((ROOT / 'replica/Sources/PastoCore/ClipboardStore.swift').read_text(),
                      'private func insertPinboard(name: String, colorHex: String?) throws -> Pinboard')
        self.assertLess(source.index('.encoded('), source.index('Pinboard('))
        self.assertIn('不声称', row['evidence_note'])


if __name__ == '__main__':
    unittest.main()
