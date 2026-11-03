"""Static comparison and provenance guards; no Swift build or app execution."""
import hashlib
import json
import struct
import unittest
from collections import Counter

from test_offline_p0_contracts import ROOT, body
from test_p0_p1_review_round2 import digest, fragment
from test_p0_p1_review_round4 import target_of_bl
from test_p0_p1_review_round9 import adrp_add, pointer
from macho_imports import parse_macho


class P0P1ReviewRound11(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((ROOT / 'reports/replica/p0-p1-review-round11.json').read_text())
        cls.prior = json.loads((ROOT / 'reports/replica/p0-p1-review-round10.json').read_text())
        cls.rows = {row['function_id']: row for row in cls.report['records']}
        cls.proof = json.loads((ROOT / cls.report['static_proof']['path']).read_text())
        cls.binary = (ROOT / cls.proof['binary_path']).read_bytes()

    def test_four_remaining_addresses_are_reviewed_without_rewriting_prior_conclusions(self):
        old = {row['function_id']: row for row in self.prior['records']}
        reviewed = set(self.report['round_delta']['reviewed_function_ids'])
        self.assertEqual(reviewed, {fid for fid, row in old.items() if row['status'] == 'unclosed'})
        self.assertEqual(len(reviewed), 4)
        self.assertEqual(set(old), set(self.rows))
        for fid in set(old) - reviewed: self.assertEqual(old[fid], self.rows[fid])
        counts = Counter(row['status'] for row in self.rows.values())
        self.assertEqual(dict(counts), self.report['outcomes'])
        self.assertEqual(self.report['resolved_review_records'], 489 - counts['unclosed'])
        self.assertEqual(self.report['resolved_comparison_percent'], round((489 - counts['unclosed']) / 489 * 100, 2))
        self.assertEqual(self.report['p0_component'], self.prior['p0_component'])
        self.assertTrue(self.report['scope_provisional'])
        self.assertIsNone(self.report['full_priority_completion_percent'])
        self.assertFalse(any(row['full_function_migration_verified'] for row in self.rows.values()))

    def test_sources_fragments_and_all_file_backed_machine_bytes_are_bound(self):
        for path, sha in self.report['source_inputs'].items(): self.assertEqual(digest(path), sha, path)
        self.assertEqual(digest(self.report['static_proof']['path']), self.report['static_proof']['sha256'])
        self.assertEqual(hashlib.sha256(self.binary).hexdigest(), self.proof['binary_sha256'])
        for fid in self.report['round_delta']['reviewed_function_ids']:
            row = self.rows[fid]
            for item in [dict(row['original'], function_id=fid)] + row.get('supporting_original_fragments', []):
                address = item.get('address') or item['function_id'].split(':')[1]
                self.assertEqual(hashlib.sha256(fragment(address, item['path']).encode()).hexdigest(), item['sha256'])
            for ref in row['current_references']:
                self.assertEqual(digest(ref['path']), ref['sha256'])
                self.assertIn(ref['symbol'], (ROOT / ref['path']).read_text())
            if row.get('supporting_binary_metadata'):
                item = row['supporting_binary_metadata']; self.assertEqual(digest(item['path']), item['sha256'])
        def visit(value):
            if isinstance(value, dict):
                if 'slice_file_offset' in value and 'bytes' in value:
                    raw = bytes.fromhex(value['bytes']); address = int(value['address'], 16)
                    matches = [s for s in self.proof['file_backed_segments']
                               if s['vmaddr'] <= address and address + len(raw) <= s['vmaddr'] + s['filesize']]
                    self.assertEqual(len(matches), 1)
                    offset = matches[0]['fileoff'] + address - matches[0]['vmaddr']
                    self.assertEqual(offset, value['slice_file_offset'])
                    self.assertEqual(self.binary[offset:offset + len(raw)], raw)
                for part in value.values(): visit(part)
            elif isinstance(value, list):
                for part in value: visit(part)
        visit(self.proof)

    def test_nominal_metadata_distinguishes_service_index_provider_and_six_model_fields(self):
        types = {t['value']: t for t in self.proof['nominal_types']}
        self.assertEqual(set(types), {'ItemCollectionViewModel', 'SearchService', 'SpotlightIndex', 'CoreDataSuggestionDataSource'})
        self.assertEqual([f['value'] for f in types['ItemCollectionViewModel']['fields']],
                         ['accessibilityService', 'osdService', 'router', 'syncManager',
                          '_isPasteAsPlainTextEnabled', '_isDirectPasteEnabled'])
        self.assertEqual([f['value'] for f in types['SearchService']['fields']], ['index', 'logger'])
        self.assertIn('suggestionDataSource', [f['value'] for f in types['SpotlightIndex']['fields']])
        self.assertEqual([f['value'] for f in types['CoreDataSuggestionDataSource']['fields']], ['managedObjectContext'])
        for item in types.values():
            self.assertEqual(pointer(bytes.fromhex(item['metadata_slot']['bytes'])), int(item['descriptor']['address'], 16))
            for field in item['fields']:
                raw = bytes.fromhex(field['record']['bytes'])
                self.assertEqual(int(field['record']['address'], 16) + 8 + struct.unpack_from('<i', raw, 8)[0], int(field['name']['address'], 16))

    def test_selected_list_callback_is_bound_to_compactmap_without_mapping_native_nil_to_history(self):
        item = self.proof['selected_list_compact_map']
        words = struct.unpack('<10I', bytes.fromhex(item['callback_install']['bytes']))
        self.assertEqual(adrp_add(0x10007e898, words[0], words[1]), 0x10007e088)
        self.assertEqual(target_of_bl(0x10007e8bc, words[-1]), 0x100bf55b0)
        actual = parse_macho(ROOT / self.proof['binary_path'])['stubs']['0x100bf55b0']
        for key, value in item['sdk_import'].items(): self.assertEqual(actual[key], value)
        self.assertIn('compactMap', actual['symbol'])
        row = self.rows['Paste:0x10007e088']
        self.assertEqual(row['status'], 'local_contract_consistent')
        self.assertIn('nil_selected_list_vs_current_history_mapping', row['coverage_boundaries']['not_verified'])
        owner = (ROOT / 'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
        self.assertIn('pinboardID = id', body(owner, 'func chooseBoard(_ id: UUID?)'))

    def test_two_preference_fallbacks_have_original_keypath_thunks_and_real_consumers(self):
        proof = self.proof['default_preferences']
        for name, target in [('plain_keypath_getter', 0x1000542b8), ('direct_keypath_getter', 0x1000542bc)]:
            item = proof[name]
            self.assertEqual(int(item['address'], 16) + struct.unpack('<i', bytes.fromhex(item['bytes']))[0], target)
        self.assertEqual(bytes.fromhex(proof['plain_key']['bytes']), b'isPasteAsPlainTextEnabled')
        self.assertEqual(bytes.fromhex(proof['direct_key']['bytes']), b'isDirectPasteEnabled')
        row = self.rows['Paste:0x100052734']
        self.assertEqual(row['status'], 'local_contract_consistent')
        support = {s['function_id']: s for s in row['supporting_original_fragments']}
        self.assertIn('local_11 = 0;', fragment('0x100070eb8', support['Paste:0x100070eb8']['path']))
        self.assertIn('local_11 = 1;', fragment('0x100091254', support['Paste:0x100091254']['path']))
        model = (ROOT / 'replica/Sources/PastoCore/Models.swift').read_text()
        self.assertIn('pasteToActiveApp: Bool = true, alwaysPastePlainText: Bool = false', model)
        app = (ROOT / 'replica/Sources/Pasto/AppMain.swift').read_text()
        paste = body(app, 'private func paste(ids: [UUID], plain: Bool, forceDirect: Bool = false)')
        self.assertIn('store.preferences.pasteToActiveApp', paste)
        self.assertIn('store.preferences.alwaysPastePlainText', paste)
        self.assertTrue(row['coverage_boundaries']['not_verified'])

    def test_provider_concrete_witness_and_startup_keypath_lead_to_existing_fetch_differences(self):
        proof = self.proof['suggestion_data_source']
        getter = proof['keypath_getter']
        self.assertEqual(int(getter['address'], 16) + struct.unpack('<i', bytes.fromhex(getter['bytes']))[0], 0x10007d73c)
        thunk = struct.unpack('<I', bytes.fromhex(proof['getter_thunk']['bytes']))[0]
        delta = thunk & 0x3ffffff
        if delta & (1 << 25): delta -= 1 << 26
        self.assertEqual(0x10007d73c + delta * 4, 0x1002fd914)
        witness = bytes.fromhex(proof['concrete_witness']['bytes'])
        self.assertEqual([pointer(witness[i:i + 8]) for i in range(8, 40, 8)],
                         [0x10030f380, 0x10030e6a8, 0x10030f3a0, 0x10030f3c0])
        row = self.rows['Paste:0x1002e00a0']
        self.assertEqual(row['status'], 'difference_confirmed')
        support = {s['function_id']: s for s in row['supporting_original_fragments']}
        self.assertIn('viewContext', fragment('0x1002fd99c', support['Paste:0x1002fd99c']['path']))
        for fid in ['Paste:0x10030e070', 'Paste:0x10030ed6c', 'Paste:0x10030e6bc']:
            self.assertEqual(self.rows[fid]['status'], 'difference_confirmed')

    def test_bounded_adr_and_twelve_instruction_adrp_add_scan_does_not_prove_unreachability(self):
        scan = self.proof['text_setter_extended_reference_scan']
        segment = next(s for s in self.proof['file_backed_segments'] if s['name'] == '__TEXT')
        target = int(scan['target'], 16); hits = []
        for offset in range(segment['fileoff'], segment['fileoff'] + segment['filesize'] - 52, 4):
            address = segment['vmaddr'] + offset - segment['fileoff']
            word = struct.unpack_from('<I', self.binary, offset)[0]
            if word & 0x9f000000 not in (0x10000000, 0x90000000): continue
            immediate = ((word >> 5) & 0x7ffff) * 4 + ((word >> 29) & 3)
            if immediate & (1 << 20): immediate -= 1 << 21
            if word & 0x9f000000 == 0x10000000:
                if address + immediate == target: hits.append(dict(kind='ADR', address=hex(address)))
                continue
            page = (address & ~4095) + (immediate << 12)
            if page != target & ~4095: continue
            for step in range(1, 13):
                second = struct.unpack_from('<I', self.binary, offset + step * 4)[0]
                if second & 0xffc00000 == 0x91000000 and ((second >> 5) & 31) == word & 31:
                    if page + ((second >> 10) & 4095) == target:
                        hits.append(dict(kind='ADRP_ADD', address=hex(address), second_address=hex(address + step * 4)))
        self.assertEqual(hits, scan['hits'])
        self.assertEqual(hits, [])
        self.assertIn('does_not_prove_no_inlined_consumer', scan['limits'])
        self.assertEqual(self.rows['Paste:0x1000f733c']['status'], 'unclosed')


if __name__ == '__main__':
    unittest.main()
