"""Read-only source/provenance checks. No Swift build or application execution."""
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


class P0P1ReviewRound10(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((ROOT / 'reports/replica/p0-p1-review-round10.json').read_text())
        cls.prior = json.loads((ROOT / 'reports/replica/p0-p1-review-round9.json').read_text())
        cls.rows = {row['function_id']: row for row in cls.report['records']}
        cls.proof = json.loads((ROOT / cls.report['static_proof']['path']).read_text())
        cls.binary = (ROOT / cls.proof['binary_path']).read_bytes()

    def test_scope_and_previous_conclusions_remain_immutable(self):
        old = {row['function_id']: row for row in self.prior['records']}
        reviewed = set(self.report['round_delta']['reviewed_function_ids'])
        self.assertEqual(reviewed, {fid for fid, row in old.items() if row['status'] == 'unclosed'})
        self.assertEqual(len(reviewed), 7)
        self.assertEqual(set(old), set(self.rows))
        for fid in set(old) - reviewed:
            self.assertEqual(old[fid], self.rows[fid])
        counts = Counter(row['status'] for row in self.rows.values())
        self.assertEqual(dict(counts), self.report['outcomes'])
        self.assertEqual(self.report['resolved_review_records'], 489 - counts['unclosed'])
        self.assertEqual(self.report['p0_component'], self.prior['p0_component'])
        self.assertTrue(self.report['scope_provisional'])
        self.assertIsNone(self.report['full_priority_completion_percent'])
        self.assertFalse(any(row['full_function_migration_verified'] for row in self.rows.values()))

    def test_all_review_inputs_and_machine_bytes_are_bound(self):
        for path, sha in self.report['source_inputs'].items():
            self.assertEqual(digest(path), sha, path)
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

    def test_text_setter_has_real_objc_selector_and_tail_release_not_an_explicit_integer_return(self):
        setter = self.proof['text_setter']
        words = struct.unpack('<17I', bytes.fromhex(setter['body']['bytes']))
        self.assertEqual(target_of_bl(0x1000f7368, words[11]), 0x100c0de60)
        self.assertEqual(words[-1] & 0xfc000000, 0x14000000)  # tail B, not RET or a return-value write
        offset = words[-1] & 0x3ffffff
        if offset & (1 << 25): offset -= 1 << 26
        self.assertEqual(0x1000f737c + offset * 4, 0x100bfbf64)
        self.assertEqual(bytes.fromhex(setter['selector_name']['bytes']), b'setString:\0')
        actual = parse_macho(ROOT / self.proof['binary_path'])['stubs']
        for item in setter['sdk_imports']:
            for key, value in item.items(): self.assertEqual(actual[item['address']][key], value)
        self.assertEqual(actual['0x100bfbf64']['symbol'], '_objc_release')

    def test_unconnected_text_setter_is_not_counted_from_declaration_or_an_unrelated_preview(self):
        row = self.rows['Paste:0x1000f733c']
        self.assertEqual(row['status'], 'unclosed')
        occurrences = []
        for path in (ROOT / 'replica/Sources').rglob('*.swift'):
            occurrences.extend((path, line) for line in path.read_text().splitlines() if 'f_1000f733c' in line)
        self.assertEqual(len(occurrences), 1)
        self.assertIn('func f_1000f733c(', occurrences[0][1])
        editor = (ROOT / 'replica/Sources/Pasto/UI/SearchEditor.swift').read_text()
        display = body(editor, 'private func display(')
        self.assertIn('editor.textStorage?.setAttributedString(value)', display)
        self.assertIn('original_indirect_or_inlined_consumers', row['coverage_boundaries']['not_verified'])
        self.assertTrue(all(not item['hits'] for item in self.proof['bounded_reference_scan']))
        self.assertIn('negative_scan_does_not_prove_no_indirect_or_inlined_consumer', self.proof['scan_limits'])

    def test_bounded_reference_scan_recomputes_all_three_encodings_without_claiming_exhaustive_xrefs(self):
        target = 0x1000f733c
        summaries = {s['segment']: s for s in self.proof['bounded_reference_scan']}
        for segment in self.proof['file_backed_segments']:
            if not segment['filesize']: continue
            hits = []
            for offset in range(segment['fileoff'], segment['fileoff'] + segment['filesize'] - 4, 4):
                address = segment['vmaddr'] + offset - segment['fileoff']
                word = struct.unpack_from('<I', self.binary, offset)[0]
                if address + struct.unpack_from('<i', self.binary, offset)[0] == target:
                    hits.append(dict(kind='relative32', address=hex(address)))
                if segment['name'] == '__TEXT' and word & 0x7c000000 == 0x14000000:
                    delta = word & 0x3ffffff
                    if delta & (1 << 25): delta -= 1 << 26
                    if address + delta * 4 == target:
                        hits.append(dict(kind='direct_branch', address=hex(address)))
                if offset % 8 == 0 and offset + 8 <= len(self.binary):
                    raw = struct.unpack_from('<Q', self.binary, offset)[0]
                    if 0x100000000 + (raw & ((1 << 36) - 1)) == target:
                        hits.append(dict(kind='rebased_pointer64', address=hex(address)))
            self.assertEqual(hits, summaries[segment['name']]['hits'])

    def test_search_route_reuses_the_initialized_model_and_cached_provider_across_empty_query(self):
        proof = self.proof['search_channel_lifetime']
        init = struct.unpack('<8I', bytes.fromhex(proof['init_and_store']['bytes']))
        self.assertEqual(target_of_bl(0x10007e7ec, init[0]), 0x100052734)
        self.assertEqual(init[3], 0xf8286a60)  # result x0 -> MainVM[x19, searchViewModel offset]
        gate = struct.unpack('<20I', bytes.fromhex(proof['query_gate_and_get']['bytes']))
        self.assertEqual(target_of_bl(0x10007e024, gate[0]), 0x1002ddcf0)
        self.assertEqual(gate[1] & 0xff00001f, 0x36000000)  # nonempty branch
        self.assertIn(0xd2800015, gate)  # empty query -> nil optional x21
        self.assertIn(0xf8686ad5, gate)  # nonempty -> same MainVM field, not new allocation
        self.assertEqual(init[1:3], gate[10:12])  # exact same offset-slot ADRP/LDR pair
        callback = struct.unpack('<9I', bytes.fromhex(proof['map_callback']['bytes']))
        self.assertEqual(adrp_add(0x10007df1c, callback[0], callback[1]), 0x10007ee18)
        row = self.rows['Paste:0x1003b8bfc']
        self.assertEqual(row['status'], 'local_contract_consistent')
        support = {s['function_id']: s for s in row['supporting_original_fragments']}
        self.assertIn('FUN_10007df7c()', fragment('0x10007ee18', support['Paste:0x10007ee18']['path']))
        owner = (ROOT / 'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
        self.assertIn('private let searchIndex: ReplicaSearchIndex', owner)
        state_source = owner[:owner.index('final class ReplicaPanel:')]
        self.assertIn('searchIndex = ReplicaSearchIndex(directoryURL: store.directoryURL, store: store)', body(state_source, 'init(store: ClipboardStore)'))
        refresh = body(owner, 'private func refreshSearch()')
        self.assertIn('searchIndex.update(items: store.items, nodes: indexedSearchQueryNodes)', refresh)
        self.assertNotIn('ReplicaSearchIndex(', refresh)

    def test_new_result_channel_is_empty_before_any_query_completes_without_claiming_event_timing(self):
        row = self.rows['Paste:0x1003647d4']
        self.assertEqual(row['status'], 'local_contract_consistent')
        support = {s['function_id']: s for s in row['supporting_original_fragments']}
        getter = fragment('0x1003556e8', support['Paste:0x1003556e8']['path'])
        self.assertIn('CurrentValueSubject', getter)
        self.assertIn('PTR___swiftEmptyArrayStorage', getter)
        mapper = fragment('0x100355a98', support['Paste:0x100355a98']['path'])
        self.assertIn('if (*param_2 == 0)', mapper)
        self.assertIn('Combine::Just::init', mapper)
        index = (ROOT / 'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text()
        self.assertIn('private(set) var identifiers: Set<UUID> = []', index)
        owner = (ROOT / 'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
        visible = body(owner, 'var visibleItems: [ClipboardItem]')
        self.assertIn('searchIndex.identifiers.contains', visible)
        self.assertTrue(row['coverage_boundaries']['not_verified'])

    def test_drop_repository_dispatch_has_two_witness_levels_before_the_move_method(self):
        proof = self.proof['drop_repository_dispatch']
        repository = bytes.fromhex(proof['repository_witness']['bytes'])
        inherited = bytes.fromhex(proof['inherited_witness']['bytes'])
        self.assertEqual(pointer(repository[16:24]), int(proof['inherited_witness']['address'], 16))
        self.assertEqual(pointer(inherited[48:56]), 0x100364034)
        factory = struct.unpack('<9I', bytes.fromhex(proof['di_witness_install']['bytes']))
        self.assertEqual(adrp_add(0x100357d08, factory[6], factory[7]), 0x100eccad0)
        thunk = struct.unpack('<8I', bytes.fromhex(proof['move_thunk']['bytes']))
        self.assertTrue(any(target_of_bl(0x100364034 + i * 4, word) == 0x100362584
                            for i, word in enumerate(thunk) if word & 0xfc000000 == 0x94000000))
        instructions = struct.unpack('<9I', bytes.fromhex(proof['callsite']['bytes']))
        self.assertEqual(instructions[0], 0xf9400b86)  # witness[+0x10] -> inherited protocol witness
        self.assertEqual(instructions[1], 0xf94018c8)  # inherited[+0x30] -> implementation
        self.assertEqual(instructions[-1], 0xd63f0100)
        self.assertEqual(pointer(bytes.fromhex(proof['classlist_slot']['bytes'])), 0x100fc10d8)
        self.assertEqual(bytes.fromhex(proof['class_name']['bytes']), b'_TtC9PasteCore14ItemRepository\0')
        row = self.rows['Paste:0x10006f29c']
        self.assertEqual(row['status'], 'local_contract_consistent')
        self.assertIn('full_parent_contract', row['coverage_boundaries']['not_verified'])


if __name__ == '__main__':
    unittest.main()
