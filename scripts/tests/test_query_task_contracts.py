"""Offline source ownership/cancellation contracts, without Swift or SDK execution."""
import hashlib
import json
import struct
import unittest
from test_offline_p0_contracts import ROOT, body
from test_search_pipeline_contracts import bounded_query_consumer

SOURCE=ROOT/'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift'


def independent_query(source):
    try:
        replace=body(source,'private func replaceQuery(with nodes:')
        drain=body(source,'private func drain() async')
        helper=body(source,'nonisolated private static func matchingIdentifiers(')
        return ('queryTask?.cancel()' in replace and 'queryTask = Task { [weak self]' in replace
                and replace.index('queryTask?.cancel()') < replace.index('queryTask = Task')
                and 'await Self.matchingIdentifiers(' in replace
                and all(x not in replace+helper for x in ['await drain(', 'await worker', 'pendingHistory', 'needsReset'])
                and all(x not in drain for x in ['CSSearchQuery(', 'matchingIdentifiers(', 'queryTask', 'identifiers =', 'self.error =']))
    except ValueError:
        return False


class QueryTaskContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=SOURCE.read_text()
        cls.report=json.loads((ROOT/'reports/replica/offline-migration-p0-round21.json').read_text())

    def test_query_task_has_no_index_worker_wait_and_index_worker_cannot_clear_results(self):
        self.assertTrue(independent_query(self.source))
        serial=self.source.replace('let found = try await Self.matchingIdentifiers(',
                                   'await drain(); let found = try await Self.matchingIdentifiers(')
        self.assertFalse(independent_query(serial))
        mixed=self.source.replace('private func drain() async {','private func drain() async {\n        identifiers = []')
        self.assertFalse(independent_query(mixed))

    def test_only_query_node_changes_replace_query_and_collection_entries_do_not(self):
        update=body(self.source,'func update(items:')
        gate=body(update,'if queryNodes != nodes')
        self.assertIn('queryNodes = nodes',gate)
        self.assertIn('replaceQuery(with: nodes)',gate)
        self.assertEqual(update.count('replaceQuery('),1)
        self.assertLess(update.index('if queryNodes != nodes'),update.index('if sourceItems != items'))
        self.assertNotIn('queryTask',body(self.source,'nonisolated private func rebuild('))

    def test_weak_owner_and_pre_cancel_guard_precede_sdk_query(self):
        replace=body(self.source,'private func replaceQuery(with nodes:')
        self.assertIn('guard let self, !Task.isCancelled else { return }',replace)
        self.assertLess(replace.index('guard let self, !Task.isCancelled'),replace.index('await Self.matchingIdentifiers'))
        self.assertIn('private var queryTask: Task<Void, Never>?',self.source)
        self.assertNotIn('private var activeQuery:',self.source)

    def test_cancelled_task_cannot_publish_success_or_ordinary_failure(self):
        replace=body(self.source,'private func replaceQuery(with nodes:')
        self.assertLess(replace.index('try Task.checkCancellation()'),replace.index('identifiers = found'))
        failure=replace[replace.index('} catch {'):]
        self.assertLess(failure.index('guard !Task.isCancelled else { return }'),failure.index('identifiers = []'))
        cancellation=body(replace,'catch is CancellationError')
        self.assertNotIn('identifiers =',cancellation)
        self.assertNotIn('onUpdate',cancellation)
        self.assertTrue(bounded_query_consumer(self.source))
        stale=self.source.replace('try Task.checkCancellation()\n                identifiers = found','identifiers = found')
        self.assertFalse(bounded_query_consumer(stale))

    def test_sdk_query_is_local_and_matching_runs_outside_main_actor(self):
        helper=body(self.source,'nonisolated private static func matchingIdentifiers(')
        self.assertIn('let query = CSSearchQuery(queryString: predicate, queryContext: context)',helper)
        self.assertIn('for try await result in query.results',helper)
        self.assertNotIn('indexed[',helper)
        self.assertNotIn('onUpdate',helper)
        self.assertIn('guard !predicate.isEmpty else { return [] }',helper)

    def test_retry_replaces_query_but_reindex_delegates_only_schedule_index_work(self):
        self.assertIn('replaceQuery(with: requested.nodes)',body(self.source,'func retry()'))
        rebuild=body(self.source,'nonisolated private func rebuild(')
        self.assertNotIn('replaceQuery(',rebuild)
        self.assertNotIn('queryTask',rebuild)
        self.assertIn('acknowledgements.append(acknowledge)',rebuild)
        cleanup=body(self.source,'deinit')
        self.assertIn('queryTask?.cancel()',cleanup)
        self.assertIn('historyTask?.cancel()',cleanup)

    def test_history_completion_and_index_ack_remain_owned_by_serial_worker(self):
        drain=body(self.source,'private func drain() async')
        self.assertIn('try await applyHistoryChanges(work.changes); work.complete(nil)',drain)
        self.assertIn('catch { work.complete(error) }',drain)
        self.assertLess(drain.index('indexed = current'),drain.index('completed.forEach'))
        self.assertIn('requestAcknowledgements.forEach { $0() }',drain)
        replace=body(self.source,'private func replaceQuery(with nodes:')
        self.assertNotIn('acknowledge',replace)
        self.assertNotIn('work.complete',replace)

    def test_original_query_task_descriptor_and_cancel_import_are_real(self):
        proof=self.report['static_bindings']
        descriptor=proof['query_task_descriptor']
        delta,frame=struct.unpack('<iI',bytes.fromhex(descriptor['bytes']))
        self.assertEqual(int(descriptor['address'],16)+delta,0x1003649ec)
        self.assertEqual(frame,32)
        load,=struct.unpack('<I',bytes.fromhex(proof['query_owner_task_load']['bytes']))
        self.assertEqual(load,0xf9402696)
        self.assertEqual(((load>>10)&4095)*8,0x48)
        word,=struct.unpack('<I',bytes.fromhex(proof['cancel_call']['bytes']))
        delta=word&((1<<26)-1)
        if delta&(1<<25):delta-=1<<26
        self.assertEqual(int(proof['cancel_call']['address'],16)+4*delta,0x100bf8490)
        self.assertEqual(proof['cancel_stub']['dyld_binding']['symbol'],'_$sScT6cancelyyF')
        self.assertEqual(proof['cancel_stub']['dyld_binding']['mechanism'],'LC_DYLD_CHAINED_FIXUPS')

    def test_original_fragments_current_consumers_and_gap_records_stay_honest(self):
        ledger=json.loads((ROOT/'replica/function-map.json').read_text())['functions']
        for row in self.report['functions']:
            text=(ROOT/row['original']['path']).read_text();a=row['function_id'].split(':')[1]
            start=text.index('/* Address: '+a+' |');end=text.find('/* Address:',start+1)
            self.assertEqual(hashlib.sha256((text[start:end if end!=-1 else None].rstrip()+'\n').encode()).hexdigest(),row['original']['sha256'])
            for ref in row['source_references']:self.assertIn(ref['symbol'],(ROOT/ref['path']).read_text())
            if row['status']=='original_actor_seed_gap_confirmed':
                self.assertEqual(row['source_references'],[])
                self.assertNotIn(row['function_id'],self.report['new_partial_bindings'])
            else:self.assertEqual(ledger[row['function_id']]['state'],'partial')
        self.assertEqual(self.report['new_fully_migrated_function_count'],0)
        self.assertFalse(self.report['module_complete'])
        self.assertTrue(self.report['remaining_differences'])


if __name__=='__main__':unittest.main()
