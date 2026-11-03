import hashlib
import json
import subprocess
import unittest
from collections import Counter

from test_offline_p0_contracts import ROOT
from test_p0_p1_review_round2 import digest, fragment

class P0P1ReviewRound23(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((ROOT/'reports/replica/p0-p1-review-round23.json').read_text())
        cls.prior=json.loads((ROOT/'reports/replica/p0-p1-review-round22.json').read_text())
        cls.backlog=json.loads((ROOT/cls.report['difference_backlog']['path']).read_text())
        cls.proof=json.loads((ROOT/cls.report['static_proof']['path']).read_text())

    def test_fixed_scope_and_no_false_progress(self):
        self.assertEqual(self.report['comparison_denominator'],646)
        self.assertEqual(self.report['resolved_review_records'],644)
        self.assertEqual(self.report['resolved_comparison_percent'],99.69)
        self.assertEqual(self.report['outcomes'],self.prior['outcomes'])
        self.assertEqual(self.report['round_delta']['newly_resolved'],0)
        self.assertTrue(self.report['scope_provisional'])
        self.assertIsNone(self.report['full_priority_completion_percent'])

    def test_only_two_unknown_records_have_new_evidence(self):
        old={r['function_id']:r for r in self.prior['records']}
        changed=set(self.report['round_delta']['reviewed_function_ids'])
        self.assertEqual(changed,{'Paste:0x10004430c','Paste:0x1000f733c'})
        for r in self.report['records']:
            self.assertFalse(r['full_function_migration_verified'])
            if r['function_id']in changed:self.assertEqual(r['status'],'unclosed')
            else:self.assertEqual(r,old[r['function_id']])

    def test_all_inputs_are_current(self):
        for source in [self.report,self.backlog,self.proof]:
            for p,h in source['source_inputs'].items():self.assertEqual(digest(p),h,p)

    def test_backlog_exactly_covers_current_differences_once(self):
        canonical={r['function_id']:r for r in self.prior['records']if r['status']=='difference_confirmed'}
        grouped=[r for g in self.backlog['groups']for r in g['records']]
        self.assertEqual(len(grouped),144)
        self.assertEqual(dict(Counter(r['function_id']for r in grouped)),{fid:1 for fid in canonical})
        for r in grouped:self.assertEqual(r,canonical[r['function_id']])
        self.assertEqual(self.backlog['counts'],dict(difference_records=144,p0_records=63,p1_additional_records=81,conservative_groups=131,p0_primary_groups=58,p1_primary_groups=73))

    def test_all_difference_original_fragments_and_current_literals(self):
        n=0; m=0
        for g in self.backlog['groups']:
            for r in g['records']:
                for ref in [dict(r['original'],function_id=r['function_id'])]+r.get('supporting_original_fragments',[]):
                    s=fragment(ref['function_id'].split(':')[1],ref['path'])
                    self.assertEqual(hashlib.sha256(s.encode()).hexdigest(),ref['sha256']);n+=1
                for ref in r['current_references']:
                    self.assertEqual(digest(ref['path']),ref['sha256'])
                    self.assertIn(ref['symbol'],(ROOT/ref['path']).read_text());m+=1
        self.assertEqual((n,m),(634,538))

    def test_grouping_uses_only_explicit_origins_or_verified_aliases(self):
        allowed={'shared_difference_origin','difference_origin','previously_verified_callback_alias'}
        for edge in self.backlog['accepted_edges']:self.assertIn(edge['basis'],allowed)
        self.assertEqual(len(self.backlog['related_only_candidates']),2)
        related={(e['source'],e['target'])for e in self.backlog['related_only_candidates']}
        self.assertEqual(related,{('Paste:0x10000e0ec','Paste:0x100021b04'),('Paste:0x10000e74c','Paste:0x100021b04')})
        for g in self.backlog['groups']:
            self.assertFalse(g['metric_eligible']);self.assertFalse(g['full_function_migration_verified'])

    def test_history_backlog_preserved_and_29_records_added(self):
        h=self.backlog['historical_backlog']
        self.assertEqual(digest(h['path']),h['sha256'])
        self.assertEqual(h['sha256'],'4aa1c7779f5663ff48e1922deef13a4066f9f782cbd67e26750081753881f01d')
        changes=self.backlog['changes_since_v1']
        self.assertEqual(changes['new_difference_records'],29)
        self.assertEqual(len(changes['new_function_ids']),29)
        self.assertEqual(changes['retired_function_ids'],[])

    def test_target_bytes_resources_and_limited_claims(self):
        p=self.proof;b=(ROOT/'.local/targets/Paste.arm64').read_bytes();raw=p['raw_target_bytes'];at=int(raw['file_offset'],16)
        self.assertEqual(b[at-16:at].hex(),raw['bytes_before_16'])
        self.assertEqual(b[at:at+80].hex(),raw['bytes_at_80'])
        for key in ['absolute64_hits','low36_payload_hits','tagged_rel32_hits']:self.assertEqual(p[key],[])
        for r in p['resources']:
            data=(ROOT/r['path']).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(),r['sha256'])
            for term in [b'SearchField',b'TextView',b'InputView']:self.assertNotIn(term,data)
        self.assertEqual(p['resolved_entries_added'],0)
        self.assertIn('No one-level indirect or general fixup decoder claim.',p['scan_definition'])

    def test_production_head_and_function_map_unchanged(self):
        before=json.loads((ROOT/'.local/p0-review/production-before.json').read_text())
        self.assertEqual(len(before),218)
        for p,h in before.items():self.assertEqual(digest(p),h,p)
        self.assertEqual(digest('replica/function-map.json'),'ea781c82f93e580a940f0804fa120e01e9030357d10aee157fe4a135143b8985')
        self.assertEqual(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'050e6878a5a52f96fe33aa40f48bb8a056cd0f05')
        for key in ['production_source_edited','function_map_modified','compiled','application_executed','network_used','committed','pushed']:self.assertFalse(self.report[key])
