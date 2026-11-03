"""P0 review provenance only; no compiler, application or network execution."""
import hashlib
import json
import struct
import test_p0_review_scope as previous


class P0ReviewRound3(previous.P0ReviewScope):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.prior = json.loads((previous.ROOT / 'reports/replica/p0-review-round2.json').read_text())
        cls.report = json.loads((previous.ROOT / 'reports/replica/p0-review-round3.json').read_text())

    def test_review_only_revisits_previous_unclosed_addresses(self):
        old = {r['function_id']: r for r in self.prior['records']}
        new = {r['function_id']: r for r in self.report['records']}
        unclosed = {key for key, row in old.items() if row['status'] == 'unclosed'}
        self.assertEqual(set(self.report['rereviewed_addresses']), unclosed)
        self.assertEqual(len(unclosed), 75)
        self.assertEqual(set(old), set(new))
        self.assertEqual(self.report['new_reviewed_addresses'], [])
        for key in set(old) - unclosed:
            self.assertEqual(old[key], new[key])
        self.assertEqual(self.report['new_conclusive_reviews'],
                         self.report['resolved_review_records'] - self.prior['resolved_review_records'])

    def test_inputs_previous_report_and_supporting_fragments_are_bound(self):
        report = self.report
        inputs = dict(report['source_inputs'])
        inputs[report['previous_round']] = report['previous_round_sha256']
        inputs[report['static_proof']['path']] = report['static_proof']['sha256']
        for path, digest in inputs.items():
            self.assertEqual(hashlib.sha256((previous.ROOT / path).read_bytes()).hexdigest(), digest, path)
        fragments = []
        for row in report['records']:
            fragments += row.get('supporting_original_fragments', [])
            proof = row.get('supporting_static_proof')
            if proof:
                self.assertEqual(hashlib.sha256((previous.ROOT / proof['path']).read_bytes()).hexdigest(),
                                 proof['sha256'])
        proof = json.loads((previous.ROOT / report['static_proof']['path']).read_text())
        fragments += proof['supporting_original_fragments']
        for row in fragments:
            text = (previous.ROOT / row['path']).read_text()
            address = row['function_id'].split(':')[1]
            start = text.index('/* Address: ' + address + ' |')
            end = text.find('/* Address:', start + 1)
            fragment = text[start:end if end != -1 else None].rstrip() + '\n'
            self.assertEqual(hashlib.sha256(fragment.encode()).hexdigest(), row['sha256'])

    def test_static_predicate_and_refresh_selector_bytes_match_the_original(self):
        proof = json.loads((previous.ROOT / self.report['static_proof']['path']).read_text())
        binary = (previous.ROOT / proof['binary_path']).read_bytes()
        self.assertEqual(hashlib.sha256(binary).hexdigest(), proof['binary_sha256'])
        refresh = proof['delete_history_refresh']
        rows = [proof['delete_permission_predicate']['instructions'],
                proof['copy_all_satisfy_predicate']['instructions']]
        rows += [refresh[key] for key in ['stub', 'selref', 'string']]
        for row in rows:
            value = bytes.fromhex(row['bytes'])
            offset = row['slice_file_offset']
            self.assertEqual(binary[offset:offset + len(value)], value)
        self.assertEqual(bytes.fromhex(refresh['string']['bytes']), b'refreshObject:mergeChanges:\0')
        raw, = struct.unpack('<Q', bytes.fromhex(refresh['selref']['bytes']))
        self.assertEqual((raw & ((1 << 36) - 1)) + 0x100000000, int(refresh['string']['address'], 16))
        self.assertFalse(proof['compiled'])
        self.assertFalse(proof['application_executed'])

    def test_primary_review_keeps_unproven_input_bridges_open(self):
        rows = {r['function_id']: r for r in self.report['records']}
        for address in ['0x10031bcdc', '0x10037a144', '0x10038222c', '0x100383df4', '0x100021b04']:
            self.assertEqual(rows['Paste:' + address]['status'], 'unclosed')
        self.assertEqual(rows['Paste:0x100021908']['status'], 'local_contract_consistent')
        self.assertEqual(rows['Paste:0x100322ae4']['status'], 'difference_confirmed')
        self.assertGreater(self.report['unclosed_review_records'], 0)
        self.assertLess(self.report['resolved_comparison_percent'], 100)
        self.assertIsNone(self.report['full_p0_completion_percent'])
