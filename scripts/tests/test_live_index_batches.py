"""Source projection/provenance tests only; no Swift, database, or SDK execution."""
import hashlib
import json
import re
import unittest
from test_offline_p0_contracts import ROOT, body

INDEX=ROOT/'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift'


def input_windows(source, identifiers):
    target=body(source,'private func reindexTargets(')
    if 'let input = identifiers.filter { !$0.isEmpty }' not in target:
        raise ValueError('Unsupported production filter')
    if 'to: input.count, by: Self.indexingBatchSize' not in target:
        raise ValueError('Unsupported input bound')
    if 'min(lowerBound + Self.indexingBatchSize, input.count)' not in target:
        raise ValueError('Unsupported clamp')
    cap=int(re.search(r'private static let indexingBatchSize = (\d+)',source)[1])
    values=[x for x in identifiers if x!='']
    return [values[i:min(i+cap,len(values))] for i in range(0,len(values),cap)]


class LiveIndexBatchContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=INDEX.read_text();cls.target=body(cls.source,'private func reindexTargets(')
        cls.report=json.loads((ROOT/'reports/replica/offline-migration-p0-round22.json').read_text())

    def test_target_request_retains_input_order_duplicates_and_nonempty_opaque_ids(self):
        self.assertIn('private var reindexIdentifiers: [String] = []',self.source)
        rebuild=body(self.source,'nonisolated private func rebuild(')
        self.assertIn('reindexIdentifiers.append(contentsOf: identifiers.compactMap',rebuild)
        self.assertIn('guard identifier.hasPrefix(domain + ":") else { return nil }',rebuild)
        self.assertIn('return localIdentifier.isEmpty ? nil : localIdentifier',rebuild)
        self.assertNotIn('UUID(',rebuild)
        self.assertNotIn('formUnion',rebuild)
        self.assertNotIn('Set(',self.target)
        self.assertNotIn('sorted',self.target)
        self.assertNotIn('trimming',self.target)

    def test_fetch_is_inside_each_input_slice_and_empty_fetch_does_not_end_loop(self):
        loop=body(self.target,'for lowerBound in stride(')
        self.assertNotIn('liveEntries(',self.target[:self.target.index('for lowerBound')])
        self.assertLess(loop.index('try Task.checkCancellation()'),loop.index('try liveEntries('))
        self.assertLess(loop.index('Array(input[lowerBound..<upperBound])'),loop.index('index.indexSearchableItems('))
        self.assertIn('if !live.isEmpty {',loop)
        self.assertNotIn('return',loop)
        self.assertNotIn('live.count',self.target)
        self.assertNotIn('refreshed.count',self.target)

    def test_input_projection_covers_boundaries_missing_batches_and_duplicates(self):
        for n in [0,1,99,100,101,199,200,201,299,300,301]:
            values=['' if i%41==0 else ('duplicate' if i%5==0 else 'id-'+str(i)) for i in range(n)]
            chunks=input_windows(self.source,values)
            self.assertEqual(sum(chunks,[]),[x for x in values if x!=''])
            self.assertTrue(all(0<len(x)<=100 for x in chunks))
        # Empty entity lookup must still allow the final input window to be fetched.
        ids=['missing']*100+['known']
        windows=input_windows(self.source,ids)
        self.assertEqual([len(x) for x in windows],[100,1])
        fetched=[[] if x[0]=='missing' else x for x in windows]
        self.assertEqual(fetched,[[],['known']])
        changed=self.source.replace('to: input.count, by: Self.indexingBatchSize','to: refreshed.count, by: Self.indexingBatchSize')
        with self.assertRaises(ValueError):input_windows(changed,ids)

    def test_sdk_error_escapes_before_entire_request_memory_commit_and_ack(self):
        loop=body(self.target,'for lowerBound in stride(')
        self.assertIn('continuation.resume(throwing: error)',loop)
        self.assertNotIn('catch',self.target)
        self.assertNotIn('indexed[',loop)
        self.assertLess(self.target.index('refreshed.append(contentsOf: live)'),self.target.index('for entry in refreshed { indexed'))
        drain=body(self.source,'private func drain() async')
        self.assertLess(drain.index('try await reindexTargets(forcedIdentifiers)'),drain.index('journalCompleted = true'))
        self.assertLess(drain.index('journalCompleted = true'),drain.index('completed.forEach'))
        self.assertIn('if !journalCompleted { needsReset = true }',drain)

    def test_full_reset_does_not_drop_pending_target_work_and_target_path_does_not_delete(self):
        drain=body(self.source,'private func drain() async')
        self.assertIn('if !forcedIdentifiers.isEmpty { try await reindexTargets(forcedIdentifiers) }',drain)
        self.assertLess(drain.index('if usesSnapshot { indexed = current }'),drain.index('try await reindexTargets('))
        self.assertNotIn('deleteSearchableItems',self.target)
        db=(ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text()
        fetch=body(db,'func searchItems(identifiers: [String]?)')
        self.assertIn('fetch("Item", keys: identifiers)',fetch)
        self.assertNotIn('UUID(',fetch)
        self.assertNotIn('compactMap',fetch)

    def test_original_and_current_bindings_remain_partial_and_unproven_routes_have_no_mapping(self):
        ledger=json.loads((ROOT/'replica/function-map.json').read_text())['functions']
        for row in self.report['functions']:
            text=(ROOT/row['original']['path']).read_text();a=row['function_id'].split(':')[1]
            start=text.index('/* Address: '+a+' |');end=text.find('/* Address:',start+1)
            self.assertEqual(hashlib.sha256((text[start:end if end!=-1 else None].rstrip()+'\n').encode()).hexdigest(),row['original']['sha256'])
            for ref in row['source_references']:self.assertIn(ref['symbol'],(ROOT/ref['path']).read_text())
            if row['status']=='routing_contract_gap_confirmed':
                self.assertEqual(row['source_references'],[])
            else:self.assertEqual(ledger[row['function_id']]['state'],'partial')
        self.assertFalse(self.report['module_complete'])
        self.assertEqual(self.report['new_fully_migrated_function_count'],0)
        self.assertTrue(self.report['remaining_differences'])


if __name__=='__main__':unittest.main()
