"""Source/ledger/relative-function evidence only, without Swift or Spotlight execution."""
import hashlib
import json
import struct
import unittest
from test_offline_p0_contracts import ROOT, body

SOURCE = ROOT / 'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift'


def acknowledges_before_query(source):
    try:
        drain = body(source, 'private func drain() async')
        return (drain.index('requestAcknowledgements = []', drain.index('let completed = requestAcknowledgements'))
                < drain.index('completed.forEach { $0() }')
                and 'CSSearchQuery(queryString:' not in drain and 'matchingIdentifiers(' not in drain)
    except (ValueError, IndexError):
        return False


class IndexRebuildContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text()
        cls.report = json.loads((ROOT / 'reports/replica/offline-migration-p0-round16.json').read_text())

    def test_delegate_entry_points_preserve_all_versus_specific_requests(self):
        self.assertIn('rebuild(identifiers: nil, acknowledgementHandler)', self.source)
        self.assertIn('rebuild(identifiers: identifiers, acknowledgementHandler)', self.source)
        rebuild = body(self.source, 'nonisolated private func rebuild(identifiers:')
        specific = body(rebuild, 'if let identifiers')
        self.assertIn('reindexIdentifiers.append(contentsOf: identifiers.compactMap', specific)
        self.assertNotIn('needsReset = true', specific)
        self.assertIn('} else {\n                needsReset = true', rebuild)

    def test_targeted_identifier_projection_keeps_this_store_namespace(self):
        rebuild = body(self.source, 'nonisolated private func rebuild(identifiers:')
        self.assertIn('guard identifier.hasPrefix(domain + ":") else { return nil }', rebuild)
        self.assertIn('let localIdentifier = String(identifier.dropFirst(domain.count + 1))',rebuild)
        self.assertIn('return localIdentifier.isEmpty ? nil : localIdentifier',rebuild)
        self.assertIn('pending = requested', rebuild)
        self.assertNotIn('queryTask', rebuild)
        self.assertNotIn('replaceQuery', rebuild)
        self.assertLess(rebuild.index('acknowledgements.append(acknowledge)'), rebuild.index('startWorker()'))

    def test_targeted_items_are_forced_even_when_metadata_is_unchanged(self):
        drain = body(self.source, 'private func drain() async')
        self.assertIn('try await reindexTargets(forcedIdentifiers)',drain)
        self.assertNotIn('indexed[$0.id] !=',body(self.source,'private func reindexTargets('))
        self.assertIn('let deleted = usesSnapshot ? Set(indexed.keys).subtracting(current.keys) : Set<UUID>()', drain)
        self.assertIn('index.deleteSearchableItems(withDomainIdentifiers: [domain])', drain)
        self.assertIn('if needsReset {', drain)
        self.assertIn('index.indexSearchableItems(changed)', drain)

    def test_reentrant_requests_stay_in_next_batch_snapshot(self):
        drain = body(self.source, 'private func drain() async')
        # The earlier history-work queue has its own await; constrain this check to request capture.
        drain = drain[drain.index('guard let request = pending else { break }'):]
        capture = drain.index('let forcedIdentifiers = reindexIdentifiers')
        first_await = drain.index('try await')
        self.assertLess(capture, drain.index('reindexIdentifiers = []'))
        self.assertLess(drain.index('reindexIdentifiers = []'), first_await)
        self.assertLess(drain.index('var requestAcknowledgements = acknowledgements'), drain.index('acknowledgements = []'))
        self.assertLess(drain.index('acknowledgements = []'), first_await)
        self.assertNotIn('acknowledgements.forEach', drain)

    def test_success_acknowledges_index_operation_before_query_and_guard(self):
        self.assertTrue(acknowledges_before_query(self.source))
        drain = body(self.source, 'private func drain() async')
        self.assertLess(drain.index('try await initializeIndexIfNeeded(request)'), drain.index('completed.forEach'))
        self.assertIn('indexed = current', body(self.source, 'private func initializeIndexIfNeeded('))
        self.assertLess(drain.index('try await reindexTargets(forcedIdentifiers)'), drain.index('completed.forEach'))
        self.assertNotIn('CSSearchQuery(',drain)
        self.assertNotIn('queryTask',drain)
        old = self.source.replace('completed.forEach { $0() }', '// old: deferred until worker and search ended')
        self.assertFalse(acknowledges_before_query(old))

    def test_error_path_acknowledges_once_without_requesting_an_extra_reset(self):
        drain = body(self.source, 'private func drain() async')
        failure = drain[drain.rindex('} catch {'):drain.index('// The original delegate also acknowledges')]
        self.assertIn('logger.error(', failure)
        self.assertNotIn('needsReset =', failure)
        self.assertLess(drain.index(failure), drain.index('requestAcknowledgements.forEach'))
        self.assertEqual(drain.count('requestAcknowledgements.forEach { $0() }'), 1)
        self.assertEqual(drain.count('completed.forEach { $0() }'), 1)
        self.assertIn('requestAcknowledgements = []', drain)
        tail = drain[drain.index('worker = nil'):]
        self.assertNotIn('forEach', tail)

    def test_missing_owner_or_no_snapshot_acknowledges_without_enqueuing(self):
        rebuild = body(self.source, 'nonisolated private func rebuild(identifiers:')
        self.assertIn('Task { @MainActor [weak self]', rebuild)
        self.assertIn('guard let self else { acknowledge(); return }', rebuild)
        self.assertIn('guard let requested else { acknowledge(); return }', rebuild)
        self.assertLess(rebuild.index('guard let requested'), rebuild.index('acknowledgements.append'))

    def test_actual_async_descriptors_bind_distinct_all_and_identifier_work(self):
        rows = self.report['static_bindings']['async_function_descriptors']
        expected = {0x100c3ec18:0x1002f3cdc, 0x100c3ec00:0x1002f3c8c,
                    0x100c3e828:0x1002e4c4c, 0x100c3e818:0x1002e4b8c}
        self.assertEqual(len(rows), len(expected))
        for row in rows:
            address = int(row['address'],16)
            delta, frame = struct.unpack('<iI', bytes.fromhex(row['bytes']))
            self.assertEqual(address+delta, expected[address])
            self.assertEqual(frame, 32)
        self.assertNotEqual(expected[0x100c3ec18], expected[0x100c3ec00])

    def test_original_and_current_consumer_bindings_are_real(self):
        for row in self.report['functions']:
            address = row['function_id'].split(':')[1]
            source = (ROOT / row['original']['path']).read_text()
            start = source.index('/* Address: '+address+' |');end = source.find('/* Address:', start+1)
            fragment = source[start:end if end!=-1 else None].rstrip()+'\n'
            self.assertEqual(hashlib.sha256(fragment.encode()).hexdigest(), row['original']['sha256'])
            current=json.loads((ROOT/'replica/function-map.json').read_text())['functions'][row['function_id']]
            for ref in current['implementations']:
                self.assertIn(ref['symbol'], (ROOT / ref['path']).read_text())


if __name__ == '__main__':
    unittest.main()
