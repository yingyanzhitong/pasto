"""Source/provenance/delete-window projection only; no Swift or SDK execution."""
import hashlib
import json
import re
import struct
import unittest
from test_offline_p0_contracts import ROOT, body

SOURCE=ROOT/'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift'


def raw_delete_windows(source,identifiers,domain):
    helper=body(source,'private func deleteIdentifiers(')
    for required in ['to: identifiers.count, by: Self.deletionBatchSize',
                     'min(lowerBound + Self.deletionBatchSize, identifiers.count)',
                     'let input = identifiers[lowerBound..<upperBound]',
                     'let batch = input.map { domain + ":" + $0 }']:
        if required not in helper:raise ValueError('Unsupported delete projection')
    before_sdk=helper[:helper.index('index.deleteSearchableItems(')]
    if any(x in before_sdk for x in ['UUID(', 'compactMap', '.filter', 'Set(', 'sorted']):
        raise ValueError('Input filtering changes the native delete contract')
    cap=int(re.search(r'private static let deletionBatchSize = (\d+)',source)[1])
    return [[domain+':'+x for x in identifiers[i:min(i+cap,len(identifiers))]]
            for i in range(0,len(identifiers),cap)]


class DeleteIndexBatches(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=SOURCE.read_text();cls.helper=body(cls.source,'private func deleteIdentifiers(')
        cls.report=json.loads((ROOT/'reports/replica/offline-migration-p0-round23.json').read_text())

    def test_delete_cap_is_independently_bound_to_original_100_instructions(self):
        self.assertIn('private static let deletionBatchSize = 100',self.source)
        self.assertIn('by: Self.deletionBatchSize',self.helper)
        self.assertNotIn('indexingBatchSize',self.helper)
        self.assertNotIn('maximumResultCount',self.helper)
        p=self.report['static_bindings']
        self.assertEqual(struct.unpack('<I',bytes.fromhex(p['first_batch_limit']['bytes']))[0],0x52800c99)
        for key in ['first_advance','next_batch_advance']:
            word,=struct.unpack('<I',bytes.fromhex(p[key]['bytes']))
            self.assertEqual((word>>10)&4095,100)

    def test_projection_preserves_all_raw_ids_duplicates_order_and_empty_values(self):
        for n in [0,1,99,100,101,199,200,201,301]:
            ids=['' if i%9==0 else ('invalid/opaque' if i%7==0 else 'duplicate') for i in range(n)]
            chunks=raw_delete_windows(self.source,ids,'namespace')
            self.assertEqual(sum(chunks,[]),['namespace:'+x for x in ids])
            self.assertTrue(all(0<len(x)<=100 for x in chunks))
        altered=self.source.replace('let batch = input.map { domain + ":" + $0 }',
                                    'let batch = input.compactMap { UUID(uuidString: $0) }')
        with self.assertRaises(ValueError):raw_delete_windows(altered,['bad'],'namespace')

    def test_sdk_delete_is_awaited_sequentially_and_only_success_updates_local_cache(self):
        self.assertIn('try await withCheckedThrowingContinuation',self.helper)
        self.assertIn('index.deleteSearchableItems(withIdentifiers: batch)',self.helper)
        self.assertIn('continuation.resume(throwing: error)',self.helper)
        self.assertNotIn('catch',self.helper)
        for parallel in ['Task {','Task.detached','async let','withTaskGroup']:
            self.assertNotIn(parallel,self.helper)
        self.assertLess(self.helper.index('index.deleteSearchableItems('),self.helper.index('for identifier in input'))
        self.assertLess(self.helper.index('index.deleteSearchableItems('),self.helper.index('UUID(uuidString: identifier)'))
        self.assertLess(self.helper.index('UUID(uuidString: identifier)'),self.helper.index('indexed.removeValue'))

    def test_real_history_and_snapshot_consumers_share_delete_service(self):
        history=body(self.source,'private func applyHistoryChanges(')
        self.assertIn('case .deleted(let identifiers):\n                try await deleteIdentifiers(identifiers)',history)
        self.assertNotIn('UUID(',history)
        drain=body(self.source,'private func drain() async')
        self.assertIn('try await deleteIdentifiers(deleted.map(\.uuidString))',drain)
        self.assertEqual(self.source.count('index.deleteSearchableItems(withIdentifiers:'),1)
        self.assertIn('catch { work.complete(error) }',drain)

    def test_work_pointer_resolves_to_sdk_delete_and_not_targeted_reindex(self):
        p=self.report['static_bindings'];rows=p['work_descriptors']
        expected={0x100c3e910:0x1002ec058,0x100c3e920:0x1002ec108,
                  0x100c3e930:0x1002ec1c8,0x100c3e940:0x1002d7050}
        for row in rows:
            delta,frame=struct.unpack('<iI',bytes.fromhex(row['bytes']));a=int(row['address'],16)
            self.assertEqual(a+delta,expected[a]);self.assertEqual(frame,32)
        call=p['sdk_delete_call'];word,=struct.unpack('<I',bytes.fromhex(call['bytes']))
        delta=word&((1<<26)-1)
        if delta&(1<<25):delta-=1<<26
        self.assertEqual(int(call['address'],16)+delta*4,0x100c00fc0)
        selector=p['delete_selector']
        self.assertTrue(selector['declared_chain_reachable']);self.assertEqual(selector['pointer_format'],6)
        self.assertEqual(bytes.fromhex(selector['string_bytes']).decode(),'deleteSearchableItemsWithIdentifiers:completionHandler:')
        raw,=struct.unpack('<Q',bytes.fromhex(selector['slot_bytes']))
        self.assertEqual((raw&((1<<36)-1))+0x100000000,int(selector['string_address'],16))

    def test_original_fragments_and_live_bindings_remain_partial(self):
        ledger=json.loads((ROOT/'replica/function-map.json').read_text())['functions']
        for row in self.report['functions']:
            a=row['function_id'].split(':')[1];text=(ROOT/row['original']['path']).read_text()
            start=text.index('/* Address: '+a+' |');end=text.find('/* Address:',start+1)
            self.assertEqual(hashlib.sha256((text[start:end if end!=-1 else None].rstrip()+'\n').encode()).hexdigest(),row['original']['sha256'])
            for ref in row['source_references']:self.assertIn(ref['symbol'],(ROOT/ref['path']).read_text())
            self.assertEqual(ledger[row['function_id']]['state'],'partial')
        self.assertEqual(self.report['new_fully_migrated_function_count'],0)
        self.assertFalse(self.report['module_complete']);self.assertTrue(self.report['remaining_differences'])


if __name__=='__main__':unittest.main()
