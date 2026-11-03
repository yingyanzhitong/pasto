"""Source and thin Mach-O bytes only. Never executes either application."""
import hashlib
import json
import struct
import unittest
from collections import Counter

from test_offline_p0_contracts import ROOT, body
from test_p0_p1_review_round2 import digest, fragment


def target_of_bl(address, word):
    if word >> 26 != 0b100101:
        raise ValueError('Not an ARM64 BL')
    immediate = word & 0x3ffffff
    if immediate & (1 << 25):
        immediate -= 1 << 26
    return address + immediate * 4


class P0P1ReviewRound4(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((ROOT / 'reports/replica/p0-p1-review-round4.json').read_text())
        cls.prior = json.loads((ROOT / 'reports/replica/p0-p1-review-round3.json').read_text())
        cls.rows = {r['function_id']: r for r in cls.report['records']}
        cls.proof = json.loads((ROOT / cls.report['static_proof']['path']).read_text())
        cls.binary = (ROOT / cls.proof['binary_path']).read_bytes()

    def test_reviewed_set_is_exactly_previous_unknown_set_without_new_denominator(self):
        report, prior = self.report, self.prior
        unknown = {r['function_id'] for r in prior['records'] if r['status'] == 'unclosed'}
        changed = set(report['round_delta']['reviewed_function_ids'])
        self.assertEqual(changed, unknown)
        self.assertEqual(len(changed), report['round_delta']['reviewed_addresses'])
        self.assertEqual(report['comparison_denominator'], prior['comparison_denominator'])
        self.assertEqual(set(self.rows), {r['function_id'] for r in prior['records']})
        counts = Counter(r['status'] for r in self.rows.values())
        self.assertEqual(dict(counts), report['outcomes'])
        resolved = len(self.rows) - counts['unclosed']
        self.assertEqual(resolved, report['resolved_review_records'])
        self.assertEqual(report['resolved_comparison_percent'], round(resolved / len(self.rows) * 100, 2))
        self.assertEqual(report['p0_component']['resolved'] + report['p1_additional_component']['resolved'], resolved)
        self.assertIsNone(report['full_priority_completion_percent'])
        self.assertTrue(report['scope_provisional'])
        old = {r['function_id']: r for r in prior['records']}
        for fid, row in self.rows.items():
            if fid not in changed:
                self.assertEqual(row, old[fid])
            self.assertFalse(row['full_function_migration_verified'])

    def test_immutable_inputs_exact_original_bodies_and_real_source_references(self):
        report = self.report
        for path, value in report['source_inputs'].items():
            self.assertEqual(digest(path), value, path)
        self.assertEqual(digest(report['static_proof']['path']), report['static_proof']['sha256'])
        for fid in report['round_delta']['reviewed_function_ids']:
            row = self.rows[fid]
            proofs = [dict(row['original'], function_id=fid)] + row.get('supporting_original_fragments', [])
            for proof in proofs:
                address = proof.get('address') or proof['function_id'].split(':')[1]
                actual = fragment(address, proof['path'])
                self.assertEqual(hashlib.sha256(actual.encode()).hexdigest(), proof['sha256'], address)
            for ref in row['current_references']:
                self.assertEqual(digest(ref['path']), ref['sha256'])
                self.assertEqual(ref['symbol'] in (ROOT / ref['path']).read_text(), ref['present'])

    def test_every_primary_static_byte_record_matches_the_original_slice(self):
        self.assertEqual(hashlib.sha256(self.binary).hexdigest(), self.proof['binary_sha256'])
        checked = []
        def visit(value):
            if isinstance(value, dict):
                if 'slice_file_offset' in value and 'bytes' in value:
                    offset = value['slice_file_offset']
                    data = bytes.fromhex(value['bytes'])
                    self.assertEqual(self.binary[offset:offset + len(data)], data, value['address'])
                    checked.append(value['address'])
                for item in value.values(): visit(item)
            elif isinstance(value, list):
                for item in value: visit(item)
        visit(self.proof)
        self.assertGreaterEqual(len(checked), 20)
        prior = self.proof['prior_metadata_proof']
        self.assertEqual(digest(prior['path']), prior['sha256'])

    def test_source_repository_conformance_and_witness_select_frontmost_producer(self):
        proof = self.proof['source_repository']
        def address(part): return int(part['address'], 16)
        conformance = proof['conformance']
        raw = bytes.fromhex(conformance['bytes'])
        base = address(conformance)
        self.assertEqual(base + struct.unpack_from('<i', raw, 0)[0], address(proof['protocol_descriptor']))
        self.assertEqual(base + 4 + struct.unpack_from('<i', raw, 4)[0], address(proof['type_descriptor']))
        witness = base + 8 + struct.unpack_from('<i', raw, 8)[0]
        slot = proof['witness_slot']
        self.assertEqual(witness + 0x10, address(slot))
        word, = struct.unpack('<Q', bytes.fromhex(slot['bytes']))
        self.assertEqual(word >> 63, 0)
        self.assertEqual(0x100000000 + (word & ((1 << 36) - 1)), int(proof['target'], 16))
        self.assertEqual(int(proof['target'], 16), 0x10035fbcc)
        for descriptor_key, name_key, expected in [('protocol_descriptor', 'protocol_name', b'AppRepositoryWriting\0'),
                                                  ('type_descriptor', 'type_name', b'AppRepository\0')]:
            descriptor = proof[descriptor_key]
            relative, = struct.unpack_from('<i', bytes.fromhex(descriptor['bytes']), 8)
            self.assertEqual(address(descriptor) + 8 + relative, address(proof[name_key]))
            self.assertEqual(bytes.fromhex(proof[name_key]['bytes']), expected)

    def test_objc_selector_pointers_resolve_icon_permanent_ids_and_identifier(self):
        expected = {'icon', 'obtainPermanentIDsForObjects:error:', 'setIdentifier:'}
        self.assertEqual({r['value'] for r in self.proof['objc_selectors']}, expected)
        for row in self.proof['objc_selectors']:
            instructions, slot, name = row['instructions'], row['slot'], row['name']
            adrp, ldr = struct.unpack('<II', bytes.fromhex(instructions['bytes']))
            self.assertEqual(adrp & 0x9f00001f, 0x90000001)  # ADRP x1
            self.assertEqual(ldr & 0xffc003ff, 0xf9400021)  # LDR x1,[x1,...]
            immediate = ((adrp >> 5) & 0x7ffff) * 4 + ((adrp >> 29) & 3)
            if immediate & (1 << 20): immediate -= 1 << 21
            pointer = (int(instructions['address'], 16) & ~4095) + (immediate << 12) + ((ldr >> 10) & 4095) * 8
            self.assertEqual(pointer, int(slot['address'], 16))
            raw, = struct.unpack('<Q', bytes.fromhex(slot['bytes']))
            self.assertEqual(0x100000000 + (raw & ((1 << 36) - 1)), int(name['address'], 16))
            self.assertEqual(bytes.fromhex(name['bytes']), row['value'].encode() + b'\0')

    def test_identifier_register_flow_uses_checksum_result_not_guessed_c_temporaries(self):
        first, second = self.proof['identifier_register_flow']
        a = int(first['address'], 16)
        words = struct.unpack('<11I', bytes.fromhex(first['bytes']))
        self.assertEqual(target_of_bl(a + 7 * 4, words[7]), 0x1003216bc)
        self.assertEqual(words[9], 0xaa0103f7)  # x23 = returned String bridge word x1
        self.assertEqual(words[10], 0xaa0003fa)  # x26 = returned String value word x0
        words = struct.unpack('<9I', bytes.fromhex(second['bytes']))
        self.assertEqual(words[:2], (0xaa1a03e0, 0xaa1703e1))  # x0/x1 from x26/x23
        self.assertEqual(target_of_bl(int(second['address'], 16) + 8 * 4, words[8]), 0x100c0c0e0)
        self.assertEqual(self.rows['Paste:0x100360d9c']['status'], 'difference_confirmed')
        models = (ROOT / 'replica/Sources/PastoCore/Models.swift').read_text()
        self.assertIn('public init(id: UUID = UUID(), createdAt: Date = Date()', models)
        capture = body((ROOT / 'replica/Sources/PastoCore/Pasteboard.swift').read_text(), 'func captureWithInsertionResult(')
        self.assertIn('addWithInsertionResult(ClipboardItem(title: ""', capture)
        self.assertNotIn('ClipboardItem(id:', capture)

    def test_class_object_and_model_factory_difference_has_actual_default_method_consumer(self):
        proof = self.proof['item_class']
        words = struct.unpack('<5Q', bytes.fromhex(proof['class_object']['bytes']))
        ro = (0x100000000 + (words[4] & ((1 << 36) - 1))) & ~7
        self.assertEqual(ro + 24, int(proof['name_pointer']['address'], 16))
        raw, = struct.unpack('<Q', bytes.fromhex(proof['name_pointer']['bytes']))
        self.assertEqual(0x100000000 + (raw & ((1 << 36) - 1)), int(proof['name']['address'], 16))
        self.assertEqual(bytes.fromhex(proof['name']['bytes']), b'_TtC9PasteCore10ItemEntity\0')
        row = self.rows['Paste:0x1003214a8']
        self.assertEqual(row['status'], 'difference_confirmed')
        factory = next(r for r in row['supporting_original_fragments'] if r['function_id'] == 'Paste:0x1003298a0')
        self.assertIn('_swift_getObjCClassFromMetadata()', fragment('0x1003298a0', factory['path']))
        current = (ROOT / 'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text()
        self.assertIn('value.managedObjectClassName = "NSManagedObject"', current)

    def test_missing_consumer_is_not_closed_and_parent_source_gate_is_not_guessed(self):
        self.assertEqual(self.rows['Paste:0x1000f733c']['status'], 'unclosed')
        source = (ROOT / 'replica/Sources/PastoCore/OriginalSourceApplication.swift').read_text()
        for value in ['app.bundleIdentifier', 'app.localizedName', 'app.icon']:
            self.assertIn(value, source)
        row = self.rows['Paste:0x10037b204']
        self.assertEqual(row['status'], 'unclosed')
        original = next(r for r in row['supporting_original_fragments'] if r['function_id'] == 'Paste:0x100311e3c')
        text = fragment('0x100311e3c', original['path'])
        self.assertLess(text.index('bundleIdentifier'), text.index('localizedName'))
        self.assertIn('FUN_100c034e0', text)
        self.assertIn('FUN_100310fb8', text)
        self.assertEqual(self.rows['Paste:0x10035ff00']['status'], 'local_contract_consistent')
        self.assertEqual(self.rows['Paste:0x1002e2e3c']['status'], 'local_contract_consistent')

    def test_delete_action_has_no_weak_controller_gate_before_single_item_store_write(self):
        row = self.rows['Paste:0x10006e95c']
        self.assertEqual(row['status'], 'difference_confirmed')
        original = fragment('0x10006e95c', row['original']['path'])
        self.assertIn('_swift_unknownObjectWeakLoadStrong()', original)
        self.assertIn('if (param_1 != 0)', original)
        source = (ROOT / 'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
        deletion = body(source, 'func deleteSelection()')
        confirm = body(source, 'func confirmItemDeletion()')
        self.assertIn('if ids.count < 2 { confirmItemDeletion() }', deletion)
        self.assertNotIn('guard let controller', deletion + confirm)
        self.assertIn('try store.delete(ids: request.ids', confirm)
        panel = (ROOT / 'replica/Sources/Pasto/UI/PanelViews.swift').read_text()
        self.assertIn('Button("删除", role: .destructive) { state.deleteSelection() }', panel)
