"""Read-only source and binary-evidence checks; never execute the original/app."""
import hashlib
import json
import struct
import unittest
from collections import Counter

from test_offline_p0_contracts import ROOT, body
from test_p0_p1_review_round2 import digest, fragment
from test_p0_p1_review_round4 import target_of_bl


def pointer(raw):
    return 0x100000000 + (struct.unpack('<Q', raw)[0] & ((1 << 36) - 1))


def adrp_add(address, first, second):
    immediate = ((first >> 5) & 0x7ffff) * 4 + ((first >> 29) & 3)
    if immediate & (1 << 20): immediate -= 1 << 21
    return (address & ~4095) + (immediate << 12) + ((second >> 10) & 4095)


class P0P1ReviewRound9(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((ROOT / 'reports/replica/p0-p1-review-round9.json').read_text())
        cls.prior = json.loads((ROOT / 'reports/replica/p0-p1-review-round8.json').read_text())
        cls.rows = {row['function_id']: row for row in cls.report['records']}
        cls.proof = json.loads((ROOT / cls.report['static_proof']['path']).read_text())
        cls.binary = (ROOT / cls.proof['binary_path']).read_bytes()

    def test_denominator_and_p0_are_preserved_and_no_finite_match_claims_full_migration(self):
        old = {row['function_id']: row for row in self.prior['records']}
        reviewed = set(self.report['round_delta']['reviewed_function_ids'])
        self.assertEqual(reviewed, {fid for fid, row in old.items() if row['status'] == 'unclosed'})
        self.assertEqual(len(reviewed), 12)
        self.assertEqual(set(self.rows), set(old))
        for fid in set(old) - reviewed:
            self.assertEqual(old[fid], self.rows[fid])
        counts = Counter(row['status'] for row in self.rows.values())
        self.assertEqual(dict(counts), self.report['outcomes'])
        self.assertEqual(self.report['resolved_review_records'], len(self.rows) - counts['unclosed'])
        self.assertEqual(self.report['resolved_comparison_percent'], round((len(self.rows) - counts['unclosed']) / 489 * 100, 2))
        self.assertEqual(self.report['p0_component'], self.prior['p0_component'])
        self.assertTrue(self.report['scope_provisional'])
        self.assertIsNone(self.report['full_priority_completion_percent'])
        self.assertFalse(any(row['full_function_migration_verified'] for row in self.rows.values()))

    def test_primary_fragments_refs_supplement_and_file_backed_machine_bytes_are_bound(self):
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
            if row.get('supporting_static_review'):
                supplement = row['supporting_static_review']
                self.assertEqual(digest(supplement['path']), supplement['sha256'])
                for evidence in json.loads((ROOT / supplement['path']).read_text())['arm_evidence']:
                    self.assertEqual(digest(evidence['path']), evidence['sha256'])
        def visit(value):
            if isinstance(value, dict):
                if 'slice_file_offset' in value and 'bytes' in value:
                    raw = bytes.fromhex(value['bytes']); address = int(value['address'], 16)
                    segments = [segment for segment in self.proof['file_backed_segments']
                                if segment['vmaddr'] <= address and address + len(raw) <= segment['vmaddr'] + segment['filesize']]
                    self.assertEqual(len(segments), 1)
                    offset = segments[0]['fileoff'] + address - segments[0]['vmaddr']
                    self.assertEqual(offset, value['slice_file_offset'])
                    self.assertEqual(self.binary[offset:offset + len(raw)], raw)
                for part in value.values(): visit(part)
            elif isinstance(value, list):
                for part in value: visit(part)
        visit(self.proof)

    def test_original_index_record_metadata_has_real_deferred_fields_and_searchable_witness(self):
        proof = self.proof['searchable_record']
        self.assertEqual(bytes.fromhex(proof['type_name']['bytes']), b'SearchableItemEntity\0')
        self.assertEqual(bytes.fromhex(proof['protocol_name']['bytes']), b'SearchableItem\0')
        descriptor = proof['type_descriptor']; address = int(descriptor['address'], 16)
        field_relative = struct.unpack_from('<i', bytes.fromhex(descriptor['bytes']), 16)[0]
        self.assertEqual(address + 16 + field_relative, int(proof['field_descriptor']['address'], 16))
        self.assertEqual([field['value'] for field in proof['fields']],
                         ['id', 'type', 'title', 'content', 'app', 'imageData', 'timestamp', 'device', 'pinboard'])
        for field in proof['fields']:
            record = field['record']; raw = bytes.fromhex(record['bytes'])
            self.assertEqual(int(record['address'], 16) + 8 + struct.unpack_from('<i', raw, 8)[0], int(field['name']['address'], 16))
        conformance = proof['conformance']; relative = struct.unpack_from('<i', bytes.fromhex(conformance['bytes']))[0]
        self.assertEqual(relative & 1, 1)
        self.assertEqual(int(conformance['address'], 16) + (relative & ~1), int(proof['protocol_indirect_slot']['address'], 16))
        self.assertEqual(pointer(bytes.fromhex(proof['protocol_indirect_slot']['bytes'])), int(proof['protocol_descriptor']['address'], 16))
        self.assertEqual(pointer(bytes.fromhex(proof['content_witness']['bytes'])), 0x100375244)

    def test_sdk_consumer_invokes_deferred_content_while_current_entry_materializes_text(self):
        raw = bytes.fromhex(self.proof['deferred_content']['getter_consumer']['bytes'])
        words = struct.unpack('<10I', raw)
        self.assertEqual(words[0], 0xf9401f08)  # witness+0x38 -> x8
        self.assertEqual(words[4], 0xd63f0100)  # blr x8 obtains callback
        self.assertEqual(words[9], 0xd63f0000)  # blr x0 invokes callback later
        self.assertEqual(bytes.fromhex(self.proof['deferred_content']['selector_name']['bytes']), b'existingObjectWithID:error:\0')
        row = self.rows['Paste:0x1002faafc']
        self.assertEqual(row['status'], 'difference_confirmed')
        support = {item['function_id']: item for item in row['supporting_original_fragments']}
        callback = fragment('0x100372440', support['Paste:0x100372440']['path'])
        self.assertIn('initWithConcurrencyType_', callback)
        self.assertIn('NSManagedObjectContext::_performAndWait()', callback)
        current = (ROOT / 'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text()
        self.assertIn('let text: String', current)
        self.assertIn('text = String(indexedText.prefix(5000))', current)
        self.assertIn('attributes.textContent = entry.text', current)
        self.assertIn('runtime_interleaving_reproduction', row['coverage_boundaries']['not_verified'])

    def test_empty_result_uses_typed_map_to_empty_publisher_instead_of_raw_nil_delivery(self):
        proof = self.proof['result_collection']
        self.assertEqual(bytes.fromhex(proof['protocol_name']['bytes']), b'ObservableCollection\0')
        self.assertEqual(bytes.fromhex(proof['type_name']['bytes']), b'SearchResultsCollection\0')
        self.assertEqual(pointer(bytes.fromhex(proof['publisher_witness']['bytes'])), 0x100355854)
        dispatch = struct.unpack('<8I', bytes.fromhex(proof['witness_dispatch']['bytes']))
        self.assertEqual(dispatch[5], 0xf9401829)  # witness+0x30 -> x9
        self.assertEqual(dispatch[-1], 0xd63f0120)  # blr x9
        row = self.rows['Paste:0x100360808']
        self.assertEqual(row['status'], 'local_contract_consistent')
        support = {item['function_id']: item for item in row['supporting_original_fragments']}
        mapper = fragment('0x100355a98', support['Paste:0x100355a98']['path'])
        self.assertIn('if (*param_2 == 0)', mapper)
        self.assertIn('PTR___swiftEmptyArrayStorage', mapper)
        self.assertIn('Combine::Just::init', mapper)
        flow = fragment('0x100355874', support['Paste:0x100355874']['path'])
        self.assertIn('_map()', flow)
        self.assertIn('_switchToLatest()', flow)

    def test_filter_mode_public_query_publication_follows_render_in_original_slot_order(self):
        proof = self.proof['coordinator_slots']
        setup = struct.unpack('<22I', bytes.fromhex(proof['setup']['bytes']))
        self.assertEqual(adrp_add(0x10003f660, setup[4], setup[5]), 0x100041ba0)
        self.assertEqual(adrp_add(0x10003f668, setup[6], setup[7]), 0x100041ba8)
        self.assertEqual(adrp_add(0x10003f678, setup[10], setup[11]), 0x100041bb8)
        self.assertEqual(target_of_bl(0x10003f6a4, setup[-1]), 0x1002f7274)
        for name, offset in [('render', 0x28), ('publish', 0x18), ('suggestions', 0x38)]:
            values = struct.unpack('<' + str(len(bytes.fromhex(proof[name]['bytes'])) // 4) + 'I', bytes.fromhex(proof[name]['bytes']))
            self.assertEqual(((values[0] >> 15) & 127) * 8, offset)
            self.assertEqual(values[-1], 0xd63f0100)
        self.assertLess(int(proof['render']['address'], 16), int(proof['publish']['address'], 16))
        row = self.rows['Paste:0x1002f7744']
        self.assertEqual(row['status'], 'difference_confirmed')
        controller = (ROOT / 'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
        self.assertIn('@Published var query =', controller)
        update = body(controller, 'func applySearchInput(nodes: [OriginalSearchQueryNode], text: String,')
        self.assertIn('query = text', update)
        editor = body((ROOT / 'replica/Sources/Pasto/UI/SearchEditor.swift').read_text(),
                      'func updateContents(_ field: SearchField, editor: SearchTextView)')
        self.assertLess(editor.index('display(result,'), editor.index('history.f_1002f5e18'))

    def test_history_delete_menu_is_gated_by_nonempty_original_history(self):
        row = self.rows['Paste:0x100021f00']
        self.assertEqual(row['status'], 'difference_confirmed')
        values = struct.unpack('<10I', bytes.fromhex(self.proof['history_delete_gate']['bytes']))
        self.assertEqual(target_of_bl(0x1000221e4, values[0]), 0x100325110)  # history rawType
        self.assertEqual(target_of_bl(0x1000221f0, values[3]), 0x100325130)  # isEmpty
        self.assertEqual(values[4] & 0xff00001f, 0x36000000)  # tbz w0,#0, add menu only when nonempty
        panel = (ROOT / 'replica/Sources/Pasto/UI/PanelViews.swift').read_text()
        history_menu = panel[panel.index('boardButton(state.store.preferences.historyTitle'):panel.index('ForEach(state.store.pinboards.sorted')]
        self.assertIn('Button("删除历史…")', history_menu)
        self.assertNotIn('.disabled', history_menu)
        self.assertTrue(row['excluded_original_branches'])


if __name__ == '__main__':
    unittest.main()
