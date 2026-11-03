"""Source and original ARM64 batch contracts only; no Swift or Spotlight execution."""
import hashlib
import json
import re
import struct
import unittest
from test_offline_p0_contracts import ROOT, body
from test_search_pipeline_contracts import bounded_query_consumer

INDEX = ROOT / 'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift'
LOOP = 'for lowerBound in stride(from: 0, to: input.count, by: Self.indexingBatchSize)'


def constructs_per_batch(source):
    try:
        target = body(source, 'private func reindexTargets(')
        batch = body(target, LOOP)
        return ('try liveEntries(identifiers: Array(input[lowerBound..<upperBound]))' in batch
                and 'let changed = live.map(searchableItem)' in batch and 'index.indexSearchableItems(changed)' in batch
                and '.map(searchableItem)' not in target[:target.index(LOOP)]
                and 'liveEntries(' not in target[:target.index(LOOP)])
    except ValueError:
        return False


class IndexBatchContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = INDEX.read_text()
        cls.report = json.loads((ROOT / 'reports/replica/offline-migration-p0-round17.json').read_text())
        cls.drain = body(cls.source, 'private func drain() async')
        cls.target = body(cls.source, 'private func reindexTargets(')

    def test_index_batch_size_and_search_result_cap_are_independent_constants(self):
        self.assertIn('private static let indexingBatchSize = 100', self.source)
        self.assertIn('private static let maximumResultCount = 100', self.source)
        batch = body(self.target, LOOP)
        self.assertIn('by: Self.indexingBatchSize', self.target)
        self.assertNotIn('Self.indexingBatchSize', self.drain)
        self.assertLess(self.drain.index('let resettingIndex = needsReset'), self.drain.index('if needsReset {'))
        self.assertNotIn('maximumResultCount', batch)
        query = body(self.source, 'nonisolated private static func matchingIdentifiers(')
        self.assertNotIn('indexingBatchSize', query)

    def test_searchable_items_are_constructed_only_for_current_batch(self):
        self.assertTrue(constructs_per_batch(self.source))
        eager = self.source.replace('let input = identifiers.filter { !$0.isEmpty }',
                                    'let input = identifiers.filter { !$0.isEmpty }; let unused = entries.map(searchableItem)')
        self.assertFalse(constructs_per_batch(eager))
        self.assertNotIn('indexed[$0.id] !=',self.target)
        self.assertIn('try await reindexTargets(forcedIdentifiers)',self.drain)

    def test_range_uses_source_count_and_clamped_upper_bound(self):
        batch = body(self.target, LOOP)
        self.assertIn('let upperBound = min(lowerBound + Self.indexingBatchSize, input.count)', batch)
        self.assertIn('input[lowerBound..<upperBound]', batch)
        self.assertNotIn('found.count', batch)
        self.assertNotIn('changed.count', batch)
        self.assertNotIn('...upperBound', batch)

    def test_each_batch_checks_cancellation_before_conversion_and_sdk_call(self):
        batch = body(self.target, LOOP)
        self.assertLess(batch.index('try Task.checkCancellation()'), batch.index('.map(searchableItem)'))
        self.assertLess(batch.index('.map(searchableItem)'), batch.index('try await withCheckedThrowingContinuation'))
        self.assertIn('index.indexSearchableItems(changed)', batch)
        for parallel in ['Task {', 'Task.detached', 'withTaskGroup', 'async let']:
            self.assertNotIn(parallel, batch)

    def test_sdk_failure_propagates_out_of_loop_before_committing_entire_request(self):
        batch = body(self.target, LOOP)
        self.assertIn('if let error { continuation.resume(throwing: error) }', batch)
        self.assertIn('else { continuation.resume() }', batch)
        self.assertNotIn('catch', batch)
        self.assertNotIn('indexed = current', batch)
        loop_end = self.target.index('{', self.target.index(LOOP)) + len(batch)
        self.assertLess(loop_end,self.target.index('for entry in refreshed { indexed'))
        self.assertIn('if !journalCompleted { needsReset = true }', self.drain)

    def test_acknowledgements_wait_for_all_index_batches_but_precede_query(self):
        batch = body(self.target, LOOP)
        for acknowledgement in ['completed.forEach', 'requestAcknowledgements.forEach', 'journalCompleted = true']:
            self.assertNotIn(acknowledgement, batch)
        self.assertLess(self.drain.index('try await reindexTargets(forcedIdentifiers)'), self.drain.index('completed.forEach'))
        self.assertNotIn('CSSearchQuery(queryString:',self.drain)
        self.assertNotIn('matchingIdentifiers(',self.drain)

    def test_query_completion_check_cannot_be_replaced_by_earlier_index_check(self):
        self.assertTrue(bounded_query_consumer(self.source))
        missing_completion = self.source.replace('try Task.checkCancellation()\n        return found', 'return found')
        self.assertIn('try Task.checkCancellation()', missing_completion)
        self.assertFalse(bounded_query_consumer(missing_completion))

    def test_original_bytes_bind_100_limits_increment_and_cancellation_import(self):
        proof = self.report['static_bindings']
        first, = struct.unpack('<I', bytes.fromhex(proof['first_batch_limit']['bytes']))
        self.assertEqual(first, 0x52800c89)
        self.assertEqual((first>>5)&65535, 100)
        clamp = struct.unpack('<3I', bytes.fromhex(proof['first_batch_clamp']['bytes']))
        self.assertEqual(clamp, (0x52800c88,0xf101913f,0x9a88b128))
        increment = struct.unpack('<5I', bytes.fromhex(proof['next_batch_increment']['bytes']))
        self.assertEqual(increment[0], 0xb1019274)
        self.assertEqual((increment[0]>>10)&4095, 100)
        call = proof['next_batch_cancel_call']
        word, _ = struct.unpack('<2I', bytes.fromhex(call['bytes']))
        delta = word & ((1<<26)-1)
        if delta & (1<<25): delta -= 1<<26
        self.assertEqual(int(call['address'],16)+delta*4, int(call['target'],16))
        self.assertEqual(proof['cancellation_stub']['symbol'], '_$sScTss5NeverORszABRs_rlE11isCancelledSbvgZ')
        self.assertEqual(proof['cancellation_stub']['dyld_binding']['mechanism'], 'LC_DYLD_CHAINED_FIXUPS')

    def test_original_fragments_and_current_source_bindings_are_current(self):
        for row in self.report['functions']:
            text = (ROOT / row['original']['path']).read_text();address = row['function_id'].split(':')[1]
            start = text.index('/* Address: '+address+' |');end = text.find('/* Address:', start+1)
            fragment = text[start:end if end!=-1 else None].rstrip()+'\n'
            self.assertEqual(hashlib.sha256(fragment.encode()).hexdigest(), row['original']['sha256'])
            current=json.loads((ROOT/'replica/function-map.json').read_text())['functions'][row['function_id']]
            for ref in current['implementations']:
                self.assertIn(ref['symbol'], (ROOT / ref['path']).read_text())


if __name__ == '__main__':
    unittest.main()
