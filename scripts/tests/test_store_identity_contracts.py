"""Offline source contracts only; no Core Data, Swift, app, or Spotlight execution."""
import hashlib
import json
import unittest
from test_offline_p0_contracts import ROOT, body

DB = 'replica/Sources/PastoCore/ClipboardPersistence.swift'
STORE = 'replica/Sources/PastoCore/ClipboardStore.swift'
INDEX = 'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift'


def has_nonnil_identity_guard(source):
    try:
        drain = body(source, 'private func drain() async')
        guard = body(drain, 'if let previous = lastSourceIdentifier, let current = request.sourceIdentifier, previous != current')
        return guard.strip() == '{\n                needsReset = true\n            }'
    except (ValueError, IndexError):
        return False


class StoreIdentityContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = (ROOT / DB).read_text()
        cls.store = (ROOT / STORE).read_text()
        cls.index = (ROOT / INDEX).read_text()
        cls.report = json.loads((ROOT / 'reports/replica/offline-migration-p0-round19.json').read_text())

    def test_identity_reads_first_persistent_store_without_writes_or_synthetic_revision(self):
        getter = body(self.db, 'var searchSourceIdentifier: String?')
        self.assertEqual(getter.strip(), '{\n        context.persistentStoreCoordinator?.persistentStores.first?.identifier\n    }')
        self.assertNotIn('UUID()', getter)
        self.assertNotIn('revision', getter)
        self.assertNotIn('save', getter)

    def test_store_forwards_identity_and_request_equality_contains_it(self):
        self.assertEqual(body(self.store, 'public var searchSourceIdentifier: String?').strip(),
                         '{ persistence.searchSourceIdentifier }')
        request = body(self.index, 'private struct Request: Equatable')
        self.assertIn('let sourceIdentifier: String?', request)
        update = body(self.index, 'func update(items:')
        self.assertLess(update.index('sourceIdentifier: store?.searchSourceIdentifier'),
                        update.index('guard requested != request'))
        self.assertIn('pending = request', update)

    def test_only_two_nonnil_unequal_identities_request_reset(self):
        self.assertTrue(has_nonnil_identity_guard(self.index))
        guard = 'if let previous = lastSourceIdentifier, let current = request.sourceIdentifier, previous != current'
        old = self.index.replace(guard, 'if lastSourceIdentifier != request.sourceIdentifier')
        self.assertFalse(has_nonnil_identity_guard(old))
        missing = self.index.replace('previous != current {\n                needsReset = true',
                                     'previous != current {\n                needsReset = false')
        self.assertFalse(has_nonnil_identity_guard(missing))

    def test_nonnil_identity_is_remembered_before_sdk_reset_and_nil_does_not_erase_it(self):
        drain = body(self.index, 'private func drain() async')
        remember = body(drain, 'if let current = request.sourceIdentifier')
        self.assertEqual(remember.strip(), '{ lastSourceIdentifier = current }')
        tokens = ['if let previous = lastSourceIdentifier',
                  'if let current = request.sourceIdentifier { lastSourceIdentifier = current }',
                  'let resettingIndex = needsReset', 'index.deleteSearchableItems(withDomainIdentifiers:']
        self.assertEqual([drain.index(x) for x in tokens], sorted(drain.index(x) for x in tokens))
        self.assertEqual(drain.count('lastSourceIdentifier ='), 1)
        self.assertIn('private var needsReset = true', self.index)

    def test_bound_original_fragments_and_real_consumers(self):
        for row in self.report['functions']:
            address = row['function_id'].split(':')[1]
            text = (ROOT / row['original']['path']).read_text()
            start = text.index('/* Address: '+address+' |');end = text.find('/* Address:',start+1)
            fragment = text[start:end if end!=-1 else None].rstrip()+'\n'
            self.assertEqual(hashlib.sha256(fragment.encode()).hexdigest(),row['original']['sha256'])
            for ref in row['source_references']:
                self.assertIn(ref['symbol'], (ROOT / ref['path']).read_text())

    def test_missing_persistent_state_and_history_stream_are_not_claimed_complete(self):
        self.assertFalse(self.report['module_complete'])
        self.assertEqual(self.report['new_fully_migrated_function_count'], 0)
        ledger = json.loads((ROOT / 'replica/function-map.json').read_text())['functions']
        for function_id in self.report['new_partial_bindings']:
            self.assertEqual(ledger[function_id]['state'],'partial')
            self.assertFalse(ledger[function_id]['code_ready'])
        for row in self.report['functions']:
            if row['status'] == 'original_contract_gap_confirmed':
                self.assertEqual(row['source_references'], [])
                self.assertNotIn(row['function_id'],self.report['new_partial_bindings'])
        self.assertTrue(self.report['remaining_differences'])


if __name__ == '__main__':
    unittest.main()
