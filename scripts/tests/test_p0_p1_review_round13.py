"""Read-only scope expansion, contract-source and provenance guards."""
import hashlib
import json
import struct
import unittest
from collections import Counter
from pathlib import Path

from test_offline_p0_contracts import ROOT, body
from test_p0_p1_review_round2 import digest, fragment


class P0P1ReviewRound13(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((ROOT / 'reports/replica/p0-p1-review-round13.json').read_text())
        cls.prior = json.loads((ROOT / 'reports/replica/p0-p1-review-round11.json').read_text())
        cls.scope = json.loads((ROOT / cls.report['scope_manifest']).read_text())
        cls.old_scope = json.loads((ROOT / 'reports/replica/p0-p1-review-scope-v1.json').read_text())
        cls.boundary = json.loads((ROOT / 'reports/replica/p0-p1-review-boundary-candidates-v1.json').read_text())
        cls.rows = {r['function_id']:r for r in cls.report['records']}

    def test_scope_is_a_versioned_superset_and_classification_never_becomes_automatic_completion(self):
        old = {r['function_id']:r for r in self.old_scope['functions']}
        new = {r['function_id']:r for r in self.scope['functions']}
        added = set(self.scope['expansion']['added_function_ids'])
        self.assertEqual(set(new), set(old) | added)
        self.assertFalse(set(old) & added)
        self.assertEqual(len(added), 64); self.assertEqual(len(new), 553)
        for fid in old: self.assertEqual(old[fid], new[fid])
        self.assertEqual(self.scope['predecessor']['sha256'], digest(self.scope['predecessor']['path']))
        self.assertEqual(self.scope['expansion']['comparison_status_on_admission'], 'not_yet_reviewed')
        self.assertEqual(self.scope['p0_count'], 256)
        self.assertEqual(self.scope['p1_additional_unique_count'], 297)
        self.assertTrue(self.scope['provisional'])
        self.assertFalse(self.scope['full_original_priority_classification_complete'])
        self.assertIsNone(self.report['full_priority_completion_percent'])
        self.assertFalse(any(r['full_function_migration_verified'] for r in self.rows.values()))
        self.assertFalse({'Paste:0x100ac35f8','Paste:0x100ac746c'} & set(new))

    def test_boundary_candidates_reproduce_both_sources_and_keep_unadmitted_addresses_out_of_denominator(self):
        for path, sha in self.boundary['source_inputs'].items(): self.assertEqual(digest(path), sha, path)
        old_ids = {r['function_id'] for r in self.prior['records']}
        supported = set()
        for row in self.prior['records']:
            for ref in row.get('supporting_original_fragments', []):
                supported.add(ref.get('function_id') or 'Paste:' + ref['address'])
        supported -= old_ids
        mapping = json.loads((ROOT / 'replica/function-map.json').read_text())['functions']
        prefixes = tuple(self.boundary['selection_rule']['mapped_path_prefixes'])
        mapped = {fid for fid, row in mapping.items() if fid.startswith('Paste:') and fid not in old_ids
                  and any(Path(ref['path']).name.startswith(prefixes) for ref in row.get('implementations', []))}
        actual = {r['function_id'] for r in self.boundary['records']}
        self.assertEqual(actual, supported | mapped)
        self.assertEqual((len(supported), len(mapped), len(supported & mapped), len(actual)), (167,142,6,303))
        self.assertTrue(all(r['classification'] == 'pending' and not r['full_function_migration_verified'] for r in self.boundary['records']))
        self.assertEqual(len(actual - set(self.scope['expansion']['added_function_ids'])), 239)

    def test_parallel_classification_partitions_are_disjoint_and_bind_complete_original_fragments(self):
        candidates = json.loads((ROOT / '.local/p0-review/p0-p1-round13-callee-candidates.json').read_text())['records']
        ids = {r['function_id'] for r in candidates}; collected = []
        sizes = []
        for part in ['p0','groups','search']:
            path = '.local/p0-review/p0-p1-round13-' + part + '-classification.json'
            data = json.loads((ROOT / path).read_text()); sizes.append(len(data['records']))
            for row in data['records']:
                fid = row['function_id']; collected.append(fid)
                ref = row['original']
                self.assertEqual(hashlib.sha256(fragment(fid.split(':')[1], ref['path']).encode()).hexdigest(), ref['sha256'])
                if part == 'search':
                    self.assertNotIn('role must be inferred', row['parent_chain_role'])
        self.assertEqual(sizes, [39,50,78])
        self.assertEqual(Counter(collected), Counter({fid:1 for fid in ids}))

    def test_new_addresses_are_actually_reviewed_and_unrelated_old_conclusions_remain_unchanged(self):
        old = {r['function_id']:r for r in self.prior['records']}
        added = set(self.scope['expansion']['added_function_ids'])
        repairs = set(self.report['round_delta']['current_reference_repairs'])
        self.assertEqual(repairs, {'Paste:0x1000b098c','Paste:0x1000b11ac'})
        self.assertEqual(set(self.rows), set(old) | added)
        self.assertEqual(set(self.report['round_delta']['reviewed_function_ids']), added)
        for fid in set(old) - repairs: self.assertEqual(self.rows[fid], old[fid])
        for fid in repairs:
            self.assertEqual(self.rows[fid]['status'], old[fid]['status'])
            self.assertEqual(self.rows[fid]['historical_current_references'], old[fid]['current_references'])
            self.assertTrue(all(r['present'] for r in self.rows[fid]['current_references']))
        self.assertFalse(any(self.rows[fid]['status'] == 'not_yet_reviewed' for fid in added))
        self.assertEqual(self.rows['Paste:0x1000f733c']['status'], 'unclosed')

    def test_all_input_hashes_original_bodies_and_actual_new_source_references_are_current(self):
        self.assertEqual(digest(self.report['scope_manifest']), self.report['scope_manifest_sha256'])
        for path, sha in self.report['source_inputs'].items(): self.assertEqual(digest(path), sha, path)
        for fid in self.scope['expansion']['added_function_ids']:
            row = self.rows[fid]
            for ref in [dict(row['original'],function_id=fid)] + row.get('supporting_original_fragments',[]):
                address = ref.get('address') or ref['function_id'].split(':')[1]
                self.assertEqual(hashlib.sha256(fragment(address, ref['path']).encode()).hexdigest(), ref['sha256'])
            self.assertTrue(row['current_references'])
            self.assertTrue(any(ref['path'].startswith('replica/Sources/') for ref in row['current_references']))
            for ref in row['current_references']:
                self.assertEqual(digest(ref['path']), ref['sha256'])
                self.assertTrue(ref['symbol'] in (ROOT / ref['path']).read_text(), (fid,ref['path'],ref['symbol']))

    def test_percentage_uses_553_and_counts_actual_conclusions_rather_than_admissions(self):
        counts = Counter(r['status'] for r in self.rows.values())
        resolved = sum(counts[s] for s in ['local_contract_consistent','difference_confirmed','user_adaptation_confirmed'])
        self.assertEqual(dict(counts), self.report['outcomes'])
        self.assertEqual(self.report['comparison_denominator'], 553)
        self.assertEqual(self.report['review_records'], 553)
        self.assertEqual(self.report['resolved_review_records'], resolved)
        self.assertEqual(self.report['resolved_comparison_percent'], round(resolved/553*100,2))
        self.assertEqual(self.report['round_delta']['newly_resolved'], resolved - 488)
        self.assertEqual(self.report['round_delta']['prior_denominator'], 489)
        self.assertEqual(self.report['round_delta']['new_denominator'], 553)
        self.assertEqual(self.report['not_yet_reviewed'], 0)

    def test_production_sources_and_function_map_are_unchanged(self):
        before = json.loads((ROOT / '.local/p0-review/production-before.json').read_text())
        now = {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
               for p in (ROOT / 'replica/Sources').rglob('*') if p.is_file()}
        self.assertEqual(now, before)
        self.assertEqual(digest('replica/function-map.json'), self.report['function_map_sha256'])
        self.assertFalse(self.report['production_source_edited'])
        self.assertFalse(self.report['compiled']); self.assertFalse(self.report['application_executed'])
        self.assertFalse(self.report['committed']); self.assertFalse(self.report['pushed'])

    def test_arm_return_values_and_error_recovery_are_bound_to_actual_instructions(self):
        proof = json.loads((ROOT / self.report['static_proof']['path']).read_text())
        self.assertEqual(digest(self.report['static_proof']['path']), self.report['static_proof']['sha256'])
        binary = (ROOT / proof['binary_path']).read_bytes()
        self.assertEqual(hashlib.sha256(binary).hexdigest(), proof['binary_sha256'])
        def offset(address):
            for segment in proof['segments']:
                if segment['vmaddr'] <= address < segment['vmaddr'] + segment['filesize']:
                    return segment['fileoff'] + address - segment['vmaddr']
            self.fail(hex(address))
        def word(address): return struct.unpack_from('<I', binary, offset(address))[0]
        def branch(address):
            instruction = word(address)
            self.assertEqual(instruction >> 26, 0b100101)
            immediate = instruction & 0x3ffffff
            return address + (immediate - (1 << 26) if immediate & (1 << 25) else immediate) * 4
        for section in ['permission_return', 'frc_fetch', 'fetch_error_recovery']:
            for instruction in proof[section]:
                address = int(instruction['address'], 16)
                self.assertEqual(offset(address), instruction['file_offset'])
                self.assertEqual(word(address), int(instruction['word'], 16))
        self.assertEqual(branch(0x1003ba56c), 0x100328f38)
        self.assertEqual(word(0x1003ba570), 0xaa0003f7)  # MOV x23,x0
        self.assertEqual(word(0x1003ba584), 0x120002e0)  # AND w0,w23,#1
        self.assertEqual(word(0x1003ba5a8), 0x52800020)  # MOV w0,#1
        self.assertEqual(branch(0x10036df18), 0x100bfc708)
        self.assertEqual(word(0x10036df1c), 0xd2800019)  # MOV x25,#0
        self.assertEqual(word(0x10036df28), 0x14000004)  # resume at 36df38
        self.assertEqual(proof['sdk_stubs']['0x100bfc708']['symbol'], '_swift_errorRelease')
        self.assertEqual(branch(0x100365f9c), 0x100c07c00)
        self.assertEqual(branch(0x10036633c), 0x100bf9cc0)
        self.assertIn('Never', proof['sdk_stubs']['0x100bf9cc0']['symbol'])
        slot = int(proof['selector']['slot'], 16)
        raw = struct.unpack_from('<Q', binary, offset(slot))[0]
        pointer = 0x100000000 + (raw & ((1 << 36) - 1))
        self.assertEqual(pointer, int(proof['selector']['cstring'], 16))
        self.assertEqual(binary[offset(pointer):offset(pointer)+14], b'performFetch:\0')

    def test_search_error_policy_differences_keep_real_current_throwing_consumer(self):
        for address in ['0x100365e18', '0x10036dc00']:
            self.assertEqual(self.rows['Paste:' + address]['status'], 'difference_confirmed')
        persistence = (ROOT / 'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text()
        search = body(persistence, 'func searchItems(identifiers: [String]?) throws -> [ClipboardItem]')
        self.assertIn('try', search)
        original = fragment('0x10036dc00', self.rows['Paste:0x10036dc00']['original']['path'])
        self.assertIn('_swift_errorRelease(unaff_x21)', original)
        self.assertIn('self.unknown = PTR___swiftEmptyArrayStorage_', original)
        self.assertIn('objc_stub::reset(local_1d0)', original)
        frc = fragment('0x100365e18', self.rows['Paste:0x100365e18']['original']['path'])
        self.assertIn('Swift::_assertionFailure', frc)
        self.assertIn('DifferenceFetchedResultsDelegate', frc)
        index = (ROOT / 'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text()
        self.assertIn('try store.searchItems', body(index, 'private func liveEntries(identifiers: [String]?) throws -> [Entry]'))
        self.assertIn('catch', body(index, 'private func drain() async'))

    def test_unproven_search_architecture_is_not_relabelled_as_user_adaptation(self):
        for address in ['0x1002e1b54', '0x1003b80f0', '0x100223430', '0x10022be98']:
            self.assertEqual(self.rows['Paste:' + address]['status'], 'unclosed')
        self.assertIn('不能证明属性为Published', self.rows['Paste:0x1002e1b54']['contract'])
        self.assertEqual(self.rows['Paste:0x1000242c8']['status'], 'user_adaptation_confirmed')
        self.assertEqual(self.rows['Paste:0x100325110']['status'], 'local_contract_consistent')


if __name__ == '__main__':
    unittest.main()
