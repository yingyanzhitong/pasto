"""Static evidence regressions. No native code, compiler, application or network."""
import hashlib
import json
import struct
import sys
import unittest
from collections import Counter

from test_offline_p0_contracts import ROOT, body
from test_p0_p1_review_round2 import digest, fragment
from test_p0_p1_review_round4 import target_of_bl


class P0P1ReviewRound5(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((ROOT / 'reports/replica/p0-p1-review-round5.json').read_text())
        cls.prior = json.loads((ROOT / 'reports/replica/p0-p1-review-round4.json').read_text())
        cls.rows = {r['function_id']: r for r in cls.report['records']}
        cls.proof = json.loads((ROOT / cls.report['static_proof']['path']).read_text())
        cls.binary = (ROOT / cls.proof['binary_path']).read_bytes()

    def test_all_previous_unknowns_and_one_explicit_retraction_keep_the_denominator(self):
        old = {r['function_id']: r for r in self.prior['records']}
        delta = self.report['round_delta']
        corrections = set(delta['adjudicated_previous_conclusions'])
        self.assertEqual(corrections, {'Paste:0x100364ab4'})
        changed = set(delta['reviewed_function_ids'])
        self.assertEqual(changed, {fid for fid, row in old.items() if row['status'] == 'unclosed'} | corrections)
        self.assertEqual(len(changed), delta['reviewed_addresses'])
        self.assertEqual(set(self.rows), set(old))
        self.assertEqual(self.report['comparison_denominator'], self.prior['comparison_denominator'])
        for fid in set(old) - changed:
            self.assertEqual(old[fid], self.rows[fid])
        counts = Counter(r['status'] for r in self.rows.values())
        self.assertEqual(dict(counts), self.report['outcomes'])
        resolved = len(self.rows) - counts['unclosed']
        self.assertEqual(resolved, self.report['resolved_review_records'])
        self.assertEqual(self.report['resolved_comparison_percent'], round(resolved / len(self.rows) * 100, 2))
        newly = sum(old[fid]['status'] == 'unclosed' and self.rows[fid]['status'] != 'unclosed' for fid in changed)
        withdrawn = sum(old[fid]['status'] != 'unclosed' and self.rows[fid]['status'] == 'unclosed' for fid in changed)
        self.assertEqual(newly, delta['newly_resolved'])
        self.assertEqual(withdrawn, delta['withdrawn_conclusions'])
        self.assertEqual(newly - withdrawn, delta['new_resolved'])
        self.assertIsNone(self.report['full_priority_completion_percent'])
        self.assertFalse(any(r['full_function_migration_verified'] for r in self.rows.values()))

    def test_input_fragments_and_real_source_consumers_are_bound(self):
        for path, value in self.report['source_inputs'].items():
            self.assertEqual(digest(path), value, path)
        self.assertEqual(digest(self.report['static_proof']['path']), self.report['static_proof']['sha256'])
        for fid in self.report['round_delta']['reviewed_function_ids']:
            row = self.rows[fid]
            for proof in [dict(row['original'], function_id=fid)] + row.get('supporting_original_fragments', []):
                address = proof.get('address') or proof['function_id'].split(':')[1]
                self.assertEqual(hashlib.sha256(fragment(address, proof['path']).encode()).hexdigest(), proof['sha256'])
            for ref in row['current_references']:
                self.assertEqual(digest(ref['path']), ref['sha256'])
                self.assertEqual(ref['symbol'] in (ROOT / ref['path']).read_text(), ref['present'])
            if row['status'] == 'local_contract_consistent':
                self.assertTrue(row['current_references'])
                self.assertTrue(all(ref['present'] for ref in row['current_references']))

    def test_raw_instruction_evidence_and_swift_error_import_match_actual_macho(self):
        self.assertEqual(hashlib.sha256(self.binary).hexdigest(), self.proof['binary_sha256'])
        def visit(value):
            if isinstance(value, dict):
                if 'slice_file_offset' in value and 'bytes' in value:
                    offset = value['slice_file_offset']; data = bytes.fromhex(value['bytes'])
                    self.assertEqual(self.binary[offset:offset + len(data)], data)
                for item in value.values(): visit(item)
            elif isinstance(value, list):
                for item in value: visit(item)
        visit(self.proof)
        sys.path.insert(0, str(ROOT / 'scripts'))
        from macho_imports import parse_macho
        stored = self.proof['error_release_import']
        actual = parse_macho(ROOT / self.proof['binary_path'])['stubs'][stored['address']]
        self.assertEqual(actual, stored)
        self.assertEqual(stored['symbol'], '_swift_errorRelease')

    def test_restore_error_branch_continues_to_undo_and_notification(self):
        part, undo, notify = self.proof['restore_failure']
        words = struct.unpack('<6I', bytes.fromhex(part['bytes']))
        address = int(part['address'], 16)
        self.assertEqual(words[0], 0xd2800015)  # mov x21,#0, Swift error result register
        self.assertEqual(target_of_bl(address + 4, words[1]), 0x1002ff310)
        self.assertEqual(words[2] & 0xff00001f, 0xb4000015)  # cbz x21
        immediate = (words[2] >> 5) & 0x7ffff
        if immediate & (1 << 18): immediate -= 1 << 19
        self.assertEqual(address + 8 + immediate * 4, 0x10037a5bc)
        self.assertEqual(words[3], 0xaa1503e0)  # mov x0,x21
        self.assertEqual(target_of_bl(address + 16, words[4]), int(self.proof['error_release_import']['address'], 16))
        undo_words = struct.unpack('<6I', bytes.fromhex(undo['bytes']))
        self.assertEqual(target_of_bl(int(undo['address'], 16) + 16, undo_words[4]), 0x100c08e80)
        notification_words = struct.unpack('<3I', bytes.fromhex(notify['bytes']))
        self.assertEqual(target_of_bl(int(notify['address'], 16) + 8, notification_words[2]), 0x100c07f00)
        self.assertEqual(self.rows['Paste:0x10037a144']['status'], 'difference_confirmed')
        source = body((ROOT / 'replica/Sources/PastoCore/Pasteboard.swift').read_text(),
                      'private func writeToPasteboard(ids: [UUID], pasteboard: NSPasteboard,')
        self.assertIn('try recordRestoredItems(ids)', source)
        tail = source[source.index('try recordRestoredItems(ids)'):]
        self.assertLess(tail.index('removeAllActions()'), tail.index('didRestoreItem.send()'))
        self.assertNotIn('catch', tail)

    def test_mutable_source_field_alias_retracts_the_old_title_only_interpretation(self):
        field_area, source_load, preserve_pointer, source_write = self.proof['source_tuple']
        words = struct.unpack('<6I', bytes.fromhex(field_area['bytes']))
        stp, store_source, pass_pointer, call, _, _ = words
        self.assertEqual(stp, 0xa900dff6)  # title x22/x23 -> [sp,#8]
        self.assertEqual(store_source, 0xf9000fe0)  # source x0 -> [sp,#24]
        self.assertEqual(pass_pointer, 0x910023e0)  # callback argument is sp+8
        self.assertEqual(call, 0xd63f02a0)  # blr x21
        self.assertEqual(struct.unpack('<2I', bytes.fromhex(preserve_pointer['bytes']))[0], 0xaa0003f3)  # x19 = argument
        write_words = struct.unpack('<3I', bytes.fromhex(source_write['bytes']))
        self.assertEqual(write_words[-1], 0xf9000a74)  # str x20,[x19,#16]
        title_base = (pass_pointer >> 10) & 4095
        callback_field = ((write_words[-1] >> 10) & 4095) * 8
        stored_source = ((store_source >> 10) & 4095) * 8
        self.assertEqual(title_base + callback_field, stored_source)
        self.assertEqual(struct.unpack_from('<I', bytes.fromhex(source_load['bytes']))[0], 0xf9400ff6)  # reload sp+24 after callback
        self.assertEqual(self.rows['Paste:0x100364ab4']['status'], 'unclosed')
        self.assertEqual(self.report['comparison_corrections'][0]['function_id'], 'Paste:0x100364ab4')

    def test_item_repository_slots_bind_content_update_before_source_callback(self):
        proof = self.proof['item_repository']
        descriptor = proof['conformance']; address = int(descriptor['address'], 16)
        raw = bytes.fromhex(descriptor['bytes'])
        witness = address + 8 + struct.unpack_from('<i', raw, 8)[0]
        self.assertEqual(bytes.fromhex(proof['protocol_name']['bytes']), b'ItemRepositoryWriting\0')
        targets = []
        for value in proof['slots']:
            slot = value['slot']
            self.assertEqual(int(slot['address'], 16), witness + value['offset'])
            pointer, = struct.unpack('<Q', bytes.fromhex(slot['bytes']))
            target = 0x100000000 + (pointer & ((1 << 36) - 1))
            self.assertEqual(target, int(value['target'], 16)); targets.append(target)
        self.assertEqual(targets, [0x100363fcc, 0x100364010, 0x100364014])
        row = self.rows['Paste:0x10037b034']
        original = fragment('0x10037b034', row['original']['path'])
        self.assertLess(original.index('(lVar7 + 0x10) + 0x10'), original.index('(lVar7 + 0x10) + 0x20'))
        source = body((ROOT / 'replica/Sources/PastoCore/Pasteboard.swift').read_text(),
                      'public func f_10037b034(_ items: [OriginalPasteboardItem]) throws -> Bool')
        self.assertLess(source.index('NSWorkspace.shared.frontmostApplication'), source.index('store.captureWithInsertionResult'))

    def test_group_fetch_and_front_insert_registers_use_real_binary_not_c_aliases(self):
        row = self.rows['Paste:0x1003620f8']
        self.assertEqual(row['status'], 'local_contract_consistent')
        self.assertEqual(row['arm_register_trace']['binary_sha256'], self.proof['binary_sha256'])
        for evidence in row['byte_evidence']:
            offset = int(evidence['file_offset_hex'], 16)
            data = self.binary[offset:offset + evidence['length_bytes']]
            self.assertEqual(hashlib.sha256(data).hexdigest(), evidence['sha256'])
        self.assertEqual(struct.unpack_from('<I', self.binary, 0x362118)[0], 0xaa0103fc)  # target x28=x1
        self.assertEqual(struct.unpack_from('<I', self.binary, 0x36211c)[0], 0xaa0003fb)  # input x27=x0
        self.assertEqual(struct.unpack_from('<I', self.binary, 0x36217c)[0], 0xaa0003f3)  # fetch result x19=x0
        self.assertEqual(target_of_bl(0x10036235c, struct.unpack_from('<I', self.binary, 0x36235c)[0]), 0x1000898fc)
        self.assertEqual(struct.unpack_from('<I', self.binary, 0x899c0)[0], 0xf90002b8)  # insert entity x24 at [x21]
        current = body((ROOT / 'replica/Sources/PastoCore/ClipboardStore.swift').read_text(),
                       'public func assign(orderedIDs: [UUID], to pinboardID: UUID?)')
        self.assertIn('seen.insert(id).inserted', current)
        self.assertIn('destination.insert(id, at: 0)', current)
        self.assertIn('重复', row['evidence_note'])  # valid unique production domain is explicit

    def test_empty_numeric_target_is_the_free_gate_adaptation_not_an_ax_failure(self):
        row = self.rows['Paste:0x10006c60c']
        self.assertEqual(row['status'], 'user_adaptation_confirmed')
        self.assertIn('Paywall', row['evidence_note'])
        supporting = {r['function_id']: r for r in row['supporting_original_fragments']}
        self.assertIn('Paste:0x10031c4c4', supporting)
        gate = supporting['Paste:0x10031c4c4']
        self.assertIn('allSatisfy', fragment('0x10031c4c4', gate['path']))
        original = fragment('0x10006c60c', row['original']['path'])
        self.assertLess(original.index('FUN_100066068'), original.index('FUN_100228c78'))
        self.assertEqual(self.rows['Paste:0x1000f733c']['status'], 'unclosed')
