"""P0-only review accounting/provenance, never product execution."""
import hashlib
import json
import unittest
from test_offline_p0_contracts import ROOT


class P0ReviewScope(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scope=json.loads((ROOT/'reports/replica/p0-review-scope-v1.json').read_text())
        cls.report=json.loads((ROOT/'reports/replica/p0-review-round1.json').read_text())

    def test_scope_is_p0_only_and_explicitly_not_a_complete_original_inventory(self):
        allowed={'快捷键与选区','复制与直接粘贴','数据与删除安全','剪贴板采集与格式保真','面板生命周期与焦点'}
        self.assertEqual(set(self.scope['modules']),allowed)
        for row in self.scope['functions']:self.assertTrue(set(row['modules'])<=allowed)
        self.assertTrue(self.scope['provisional'])
        self.assertFalse(self.scope['full_original_priority_classification_complete'])
        self.assertIsNone(self.report['full_p0_completion_percent'])

    def test_counts_use_unique_current_p0_scope_and_unclosed_never_counts_as_resolved(self):
        ids={r['function_id'] for r in self.scope['functions']};rows=self.report['records']
        self.assertEqual(len(ids),len(self.scope['functions']))
        self.assertEqual(len({r['function_id'] for r in rows}),len(rows))
        self.assertTrue({r['function_id'] for r in rows}<=ids)
        resolved=sum(r['status']!='unclosed' for r in rows)
        self.assertEqual(resolved,self.report['resolved_review_records'])
        self.assertEqual(self.report['comparison_denominator'],len(ids))
        self.assertEqual(self.report['resolved_comparison_percent'],round(resolved/len(ids)*100,2))
        self.assertEqual(self.report['not_yet_reviewed']+len(rows),len(ids))
        self.assertFalse(any(r['full_function_migration_verified'] for r in rows))

    def test_original_fragments_and_resolved_current_references_are_bound(self):
        cache={}
        for row in self.report['records']:
            o=row['original'];a=row['function_id'].split(':')[1]
            if o['path'] not in cache:cache[o['path']]=(ROOT/o['path']).read_text()
            text=cache[o['path']];start=text.index('/* Address: '+a+' |');end=text.find('/* Address:',start+1)
            self.assertEqual(hashlib.sha256((text[start:end if end!=-1 else None].rstrip()+'\n').encode()).hexdigest(),o['sha256'])
            for ref in row['current_references']:
                p=ROOT/ref['path']
                if ref['present']:
                    self.assertIn(ref['symbol'],p.read_text())
                    self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),ref['sha256'])
            if row['status']=='local_contract_consistent':
                self.assertTrue(row['current_references'])
                self.assertTrue(all(r['present'] for r in row['current_references']))

    def test_strict_reused_contracts_validate_every_source_hash_and_original_binary(self):
        binary=hashlib.sha256((ROOT/'.local/paste-arm64-static.bin').read_bytes()).hexdigest()
        for row in self.report['records']:
            proof=row.get('strict_reuse_proof')
            if not proof:continue
            self.assertEqual(proof['binary_sha256'],binary)
            for path,digest in proof['source_sha256'].items():
                self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),digest)
            prior=proof['prior_review']
            self.assertEqual(hashlib.sha256((ROOT/prior['path']).read_bytes()).hexdigest(),prior['sha256'])

    def test_review_does_not_change_production_or_migration_ledger(self):
        before=json.loads((ROOT/'.local/p0-review/production-before.json').read_text())
        for p,h in before.items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),h)
        self.assertFalse(self.report['production_source_edited'])
        self.assertFalse(self.report['function_map_modified'])
        self.assertFalse(self.report['compiled']);self.assertFalse(self.report['network_used'])
        self.assertFalse(self.report['application_executed']);self.assertTrue(self.report['goal_active'])


if __name__=='__main__':unittest.main()
