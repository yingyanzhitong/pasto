"""Review accounting/provenance only; never runs either macOS application."""
import hashlib
import json
import struct
import unittest
from test_offline_p0_contracts import ROOT


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


class P0P1ReviewScope(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scope = json.loads((ROOT / 'reports/replica/p0-p1-review-scope-v1.json').read_text())
        cls.report = json.loads((ROOT / 'reports/replica/p0-p1-review-round1.json').read_text())

    def test_scope_is_unique_p0_p1_and_remains_provisional(self):
        scope = self.scope
        ids = {r['function_id'] for r in scope['functions']}
        self.assertEqual(len(ids), len(scope['functions']))
        self.assertEqual(scope['denominator'], len(ids))
        self.assertEqual(scope['p0_count'] + scope['p1_additional_unique_count'], len(ids))
        self.assertTrue(scope['provisional'])
        self.assertFalse(scope['full_original_priority_classification_complete'])
        self.assertTrue(scope['scope_evidence_gaps'])
        for row in scope['functions']:
            self.assertTrue(set(row['priorities']) <= {'P0', 'P1'})
            self.assertTrue(row['priorities'])

    def test_counts_exclude_pending_and_unclosed_and_do_not_duplicate_shared_addresses(self):
        report = self.report
        rows = report['records']
        self.assertEqual(len(rows), len({r['function_id'] for r in rows}))
        self.assertTrue({r['function_id'] for r in rows} <= {r['function_id'] for r in self.scope['functions']})
        resolved = sum(r['status'] != 'unclosed' for r in rows)
        self.assertEqual(resolved, report['resolved_review_records'])
        self.assertEqual(len(rows) + report['not_yet_reviewed'], report['comparison_denominator'])
        self.assertEqual(report['resolved_comparison_percent'], round(resolved / report['comparison_denominator'] * 100, 2))
        self.assertEqual(report['p0_component']['resolved'] + report['p1_additional_component']['resolved'], resolved)
        self.assertIsNone(report['full_priority_completion_percent'])
        self.assertFalse(any(r['full_function_migration_verified'] for r in rows))

    def test_original_fragments_and_current_references_remain_bound(self):
        cache = {}
        for row in self.report['records']:
            proof = row['original']
            text = cache.setdefault(proof['path'], (ROOT / proof['path']).read_text())
            address = row['function_id'].split(':')[1]
            start = text.index('/* Address: ' + address + ' |')
            end = text.find('/* Address:', start + 1)
            fragment = text[start:end if end != -1 else None].rstrip() + '\n'
            self.assertEqual(hashlib.sha256(fragment.encode()).hexdigest(), proof['sha256'])
            for ref in row['current_references']:
                if ref['present']:
                    self.assertIn(ref['symbol'], (ROOT / ref['path']).read_text())
                    self.assertEqual(digest(ref['path']), ref['sha256'])
            if row['status'] == 'local_contract_consistent':
                self.assertTrue(row['current_references'])
                self.assertTrue(all(ref['present'] for ref in row['current_references']))

    def test_input_and_component_reports_are_immutable(self):
        report = self.report
        inputs = dict(report['source_inputs'])
        inputs[report['scope_manifest']] = report['scope_manifest_sha256']
        inputs[report['static_proof']['path']] = report['static_proof']['sha256']
        for path, value in inputs.items():
            self.assertEqual(digest(path), value, path)
        p0 = json.loads((ROOT / 'reports/replica/p0-review-round4.json').read_text())
        for path, value in p0['source_inputs'].items():
            self.assertEqual(digest(path), value, path)

    def test_strict_p1_reuse_binds_every_source_not_only_the_implementation(self):
        binary = digest('.local/paste-arm64-static.bin')
        for row in self.report['records']:
            proof = row.get('strict_reuse_proof')
            if not proof or 'source_hashes_current' not in proof:
                continue
            self.assertEqual(proof['binary_sha256'], binary)
            prior = proof['prior_report']
            self.assertEqual(digest(prior['path']), prior['sha256'])
            self.assertTrue(proof['source_hashes_current'])
            self.assertEqual(proof['source_hashes_current'], proof['source_hashes_in_prior_report'])
            for path, value in proof['source_hashes_current'].items():
                self.assertEqual(digest(path), value)

    def test_machine_rounding_not_decompiler_cast_controls_the_date_conclusion(self):
        proof = json.loads((ROOT / self.report['static_proof']['path']).read_text())
        binary = (ROOT / proof['binary_path']).read_bytes()
        self.assertEqual(hashlib.sha256(binary).hexdigest(), proof['binary_sha256'])
        for row in proof['date_encoding'] + proof['transaction_dispatch']:
            value = bytes.fromhex(row['bytes'])
            offset = row['slice_file_offset']
            self.assertEqual(binary[offset:offset + len(value)], value)
        lower, upper, conversion, thunk = proof['date_encoding']
        self.assertEqual(struct.unpack('<I', bytes.fromhex(lower['bytes']))[0], 0x1e654008)
        self.assertEqual(struct.unpack('<I', bytes.fromhex(upper['bytes']))[0], 0x1e64c000)
        branch, = struct.unpack('<I', bytes.fromhex(thunk['bytes']))
        self.assertEqual(branch >> 26, 5)
        self.assertEqual(int(thunk['address'], 16) + (branch & 0x3ffffff) * 4, 0x1002d9d2c)
        rows = {r['function_id']: r for r in self.report['records']}
        for address in ['0x1002d9d2c', '0x1002d7368']:
            self.assertEqual(rows['Paste:' + address]['status'], 'local_contract_consistent')
        self.assertFalse(proof['application_executed'])

    def test_review_did_not_modify_production_or_enable_execution(self):
        before = json.loads((ROOT / '.local/p0-review/production-before.json').read_text())
        current = {str(p.relative_to(ROOT)) for p in (ROOT / 'replica/Sources').rglob('*') if p.is_file()}
        self.assertEqual(current, set(before))
        for path, value in before.items():
            self.assertEqual(digest(path), value)
        report = self.report
        self.assertEqual(digest('replica/function-map.json'), report['function_map_sha256'])
        for key in ['production_source_edited', 'function_map_modified', 'compiled', 'application_executed',
                    'network_used', 'committed', 'pushed']:
            self.assertFalse(report[key])
        self.assertTrue(report['goal_active'])
