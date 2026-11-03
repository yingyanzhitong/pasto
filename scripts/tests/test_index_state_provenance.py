"""Original-index-state provenance only; passing does not verify missing Pasto features."""
import hashlib
import json
import struct
import unittest
from test_offline_p0_contracts import ROOT


class IndexStateProvenance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((ROOT / 'reports/replica/offline-migration-p0-round18.json').read_text())
        cls.proof = cls.report['static_bindings']

    def test_original_indexing_state_has_five_distinct_fields(self):
        state = self.proof['indexing_state']
        raw = bytes.fromhex(state['descriptor_bytes'])
        self.assertEqual(struct.unpack_from('<I', raw)[0] & 31, 17)
        self.assertEqual(struct.unpack_from('<I', raw, 20)[0], 5)
        self.assertEqual(state['name'], 'IndexingState')
        self.assertEqual([x['name'] for x in state['fields']], [
            'schemaVersion', 'totalItems', 'indexedItems', 'oldestTimestamp', 'invalidItems'])
        for row in state['fields']:
            if row['name'] != 'oldestTimestamp':
                self.assertEqual(bytes.fromhex(row['type_ref_bytes'])[:2], b'Si')

    def test_oldest_timestamp_is_optional_foundation_date_and_matches_actual_field_slot(self):
        state = self.proof['indexing_state']
        row = state['fields'][3]
        raw = bytes.fromhex(row['type_ref_bytes'])
        self.assertEqual(raw[0], 2)
        self.assertEqual(raw[5:7], b'Sg')
        slot = int(row['type_ref'],16)+1+struct.unpack_from('<i',raw,1)[0]
        self.assertEqual(slot, int(state['oldest_timestamp_type']['indirect_slot'],16))
        prior = json.loads((ROOT / state['oldest_timestamp_type']['prior_bound_proof']).read_text())['static_bindings']
        self.assertEqual(prior['original_binary_sha256'], self.proof['original_binary_sha256'])
        self.assertEqual(prior['timestamp_type']['indirect_slot'], hex(slot))
        self.assertEqual(prior['timestamp_type']['slot_bytes'], state['oldest_timestamp_type']['slot_bytes'])
        self.assertEqual(prior['timestamp_type']['symbol'], '_$s10Foundation4DateVMn')
        descriptor = bytes.fromhex(state['descriptor_bytes'])
        self.assertEqual(struct.unpack_from('<I',descriptor,24)[0]*8+3*4, 0x1c)

    def test_schema_initializer_is_five_or_six_with_macos_26_4_boundary(self):
        words = struct.unpack('<13I', bytes.fromhex(self.proof['schema_initializer']['bytes']))
        self.assertEqual(words[2], 0x52800340)  # mov w0,#26
        self.assertEqual(words[3], 0x52800081)  # mov w1,#4
        self.assertEqual(words[4], 0xd2800002)  # mov x2,#0
        self.assertEqual(words[7], 0x528000a8)  # mov w8,#5
        self.assertEqual(words[8], 0x9a880508)  # increment when the OS predicate is true
        self.assertEqual(self.proof['schema_initializer']['old_schema'], 5)
        self.assertEqual(self.proof['schema_initializer']['macos_26_4_schema'], 6)

    def test_health_probe_uses_history_date_and_gaps_are_not_counted_as_migrated(self):
        probe = self.proof['health_probe']
        self.assertEqual(bytes.fromhex(probe['bytes']).decode(),
                         'contentModificationDate >= $time.iso(1970-01-01T00:00:00Z)')
        self.assertEqual(self.report['new_fully_migrated_function_count'], 0)
        self.assertEqual(self.report['new_partial_bindings'], [])
        self.assertFalse(self.report['production_source_edited'])
        self.assertFalse(self.report['module_complete'])
        for row in self.report['functions']:
            self.assertEqual(row['status'], 'original_contract_gap_confirmed')
            self.assertEqual(row['source_references'], [])

    def test_original_fragments_are_bound_and_next_work_retains_full_objective(self):
        for row in self.report['functions']:
            address = row['function_id'].split(':')[1]
            text = (ROOT / row['original']['path']).read_text()
            start = text.index('/* Address: '+address+' |');end = text.find('/* Address:',start+1)
            fragment = text[start:end if end!=-1 else None].rstrip()+'\n'
            self.assertEqual(hashlib.sha256(fragment.encode()).hexdigest(),row['original']['sha256'])
        self.assertEqual(self.report['next_module'], 'P0 data_and_persistence')
        self.assertTrue(self.report['remaining_differences'])
        self.assertTrue(self.report['goal_active'])


if __name__ == '__main__':
    unittest.main()
