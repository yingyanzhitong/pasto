"""Review provenance and progress only; never executes either macOS app."""
import hashlib
import json
import struct
import test_p0_review_scope as previous


class P0ReviewRound2(previous.P0ReviewScope):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.prior = cls.report
        cls.report = json.loads((previous.ROOT / 'reports/replica/p0-review-round2.json').read_text())

    def test_round_delta_has_no_duplicate_or_out_of_scope_credit(self):
        report = self.report
        old = {r['function_id'] for r in self.prior['records']}
        new = {r['function_id'] for r in report['records']}
        self.assertEqual(set(report['new_reviewed_addresses']), new - old)
        self.assertEqual(len(report['new_reviewed_addresses']), 56)
        self.assertEqual(len(set(report['rereviewed_addresses'])), 4)
        self.assertTrue(set(report['rereviewed_addresses']) <= old)
        self.assertEqual(report['new_conclusive_reviews'],
                         report['resolved_review_records'] - self.prior['resolved_review_records'])
        self.assertEqual(report['not_yet_reviewed'], 0)
        self.assertGreater(report['unclosed_review_records'], 0)
        self.assertLess(report['resolved_comparison_percent'], 100)

    def test_previous_round_and_all_new_input_digests_remain_bound(self):
        report = self.report
        paths = dict(report['source_inputs'])
        paths[report['previous_round']] = report['previous_round_sha256']
        paths[report['scope_manifest']] = report['scope_manifest_sha256']
        paths[report['static_proof']['path']] = report['static_proof']['sha256']
        for path, digest in paths.items():
            self.assertEqual(hashlib.sha256((previous.ROOT / path).read_bytes()).hexdigest(), digest, path)

    def test_static_proof_bytes_belong_to_the_original_not_a_product_run(self):
        proof = json.loads((previous.ROOT / self.report['static_proof']['path']).read_text())
        binary = (previous.ROOT / proof['binary_path']).read_bytes()
        self.assertEqual(hashlib.sha256(binary).hexdigest(), proof['binary_sha256'])
        self.assertFalse(proof['compiled'])
        self.assertFalse(proof['application_executed'])
        rows = [proof['save_selector'][key] for key in ['stub', 'selref', 'string']]
        rows += [proof['nscoding_keys'][key] for key in ['types_load', 'data_load']]
        rows += [proof['cleanup_error_continue'][key] for key in ['branch', 'cleanup']]
        for row in rows:
            expected = bytes.fromhex(row['bytes'])
            start = row['slice_file_offset']
            self.assertEqual(binary[start:start + len(expected)], expected)
        self.assertEqual(bytes.fromhex(proof['save_selector']['string']['bytes']), b'save:\0')
        raw, = struct.unpack('<Q', bytes.fromhex(proof['save_selector']['selref']['bytes']))
        self.assertEqual((raw & ((1 << 36) - 1)) + 0x100000000,
                         int(proof['save_selector']['string']['address'], 16))

    def test_adjudication_preserves_unknowns_and_does_not_claim_function_migration(self):
        rows = {r['function_id']: r for r in self.report['records']}
        for address in ['0x100383df4', '0x100ae6428', '0x1003b936c']:
            self.assertEqual(rows['Paste:' + address]['status'], 'unclosed')
        self.assertFalse(any(r['full_function_migration_verified'] for r in rows.values()))
        self.assertIsNone(self.report['full_p0_completion_percent'])
