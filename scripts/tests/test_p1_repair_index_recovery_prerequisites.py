"""Local source/Mach-O contracts only; no defaults, database or native framework execution."""
import hashlib
import json
import re
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from snapshot_read_scope_contract import body, assert_history_queue_only
from test_p0_repair_checksum_routing import original_fragment
from test_p0_repair_identity import method_body


class IndexRecoveryPrerequisites(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-44'
        cls.proof = json.loads((cls.phase / 'recovery-prerequisites-contract.json').read_text())
        cls.history = (ROOT / 'replica/Sources/PastoCore/OriginalSearchHistory.swift').read_text()
        cls.persistence = (ROOT / 'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text()
        cls.index = (ROOT / 'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text()
        cls.fragments = {r['address']: original_fragment((ROOT / r['path']).read_text(), r['address'][2:])
                         for r in cls.proof['original_fragments']}

    def before(self, path):
        return (self.phase / 'before' / path).read_text()

    def test_all_original_fragments_have_unchanged_hashes(self):
        for row in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / row['path'])[row['address']]['sha256'], row['sha256'])

    def test_fixed_token_key_is_bound_to_binary_literal_and_both_config_producers(self):
        key = self.proof['token_key_binary']
        self.assertEqual(bytes.fromhex(key['bytes']).decode('ascii'), 'indexHistoryTokenData')
        self.assertEqual(key['length'], 21)
        for address in ['0x1003707a8', '0x100371394']:
            self.assertIn('0xd000000000000015,0x8000000100da3370', self.fragments[address])
        self.assertIn('standardUserDefaults', self.fragments['0x1002cd57c'])

    def test_actual_observer_uses_fixed_key_for_read_and_write_without_identity_gate(self):
        observe = body(self.history, 'func observe(_ consume:')
        self.assertIn('let key = "indexHistoryTokenData"', observe)
        self.assertIn('UserDefaults.standard.data(forKey: key)', observe)
        persist = body(observe, 'func persistToken()')
        self.assertIn('UserDefaults.standard.set(data, forKey: key)', persist)
        for forbidden in ['persistentStores', 'identity.map', 'history-token.', 'guard let key']:
            self.assertNotIn(forbidden, observe)

    def test_archive_catchup_notification_and_success_only_advancement_are_unchanged(self):
        path = 'replica/Sources/PastoCore/OriginalSearchHistory.swift'
        previous = self.before(path)
        assert_history_queue_only(self, self.history, previous, check_observe=False)
        current = body(self.history, 'func observe(_ consume:')
        self.assertIn('NSKeyedUnarchiver.unarchivedObject(ofClass: NSPersistentHistoryToken.self, from: data)', current)
        self.assertIn('NSKeyedArchiver.archivedData(withRootObject: $0, requiringSecureCoding: true)', current)
        self.assertLess(current.index('persistToken()\n'), current.index('await process()'))
        self.assertLess(current.index('await process()'), current.index('for await _ in notifications()'))

    def test_different_store_identities_share_original_slot_without_defaults_execution(self):
        observe = body(self.history, 'func observe(_ consume:')
        match = re.search(r'let key = "([^"]+)"', observe)
        self.assertIsNotNone(match)
        keys = [match[1] for _ in ['store-A', 'store-B', None]]
        self.assertEqual(keys, ['indexHistoryTokenData'] * 3)
        old = self.before('replica/Sources/PastoCore/OriginalSearchHistory.swift')
        self.assertIn('"pasto.search.history-token." + $0', old)

    def test_full_delete_uses_original_native_selector_on_the_owned_named_index(self):
        selector, = self.proof['native_selector_bindings']
        self.assertEqual(selector['selector'], 'deleteAllSearchableItemsWithCompletionHandler:')
        self.assertTrue(selector['chain']['declared_chain_reachable'])
        self.assertEqual(selector['chain']['pointer_format'], 6)
        self.assertIn('deleteAllSearchableItemsWithCompletionHandler_(self)', self.fragments['0x1002e267c'])
        self.assertIn('index = CSSearchableIndex(name: domain)', self.index)
        self.assertNotIn('CSSearchableIndex.default()', self.index)

    def test_sdk_declarations_confirm_availability_named_index_and_full_delete(self):
        sdk = self.proof['sdk']
        raw = Path(sdk['path']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), sdk['sha256'])
        for token in [b'+ (BOOL)isIndexingAvailable', b'initWithName:', b'deleteAllSearchableItemsWithCompletionHandler:']:
            self.assertIn(token, raw)

    def test_reset_waits_for_delete_completion_before_clearing_memory_and_reindexing(self):
        initialization = body(self.index, 'private func initializeIndexIfNeeded(')
        reset = method_body(initialization, 'if needsReset {')
        self.assertLess(reset.index('needsReset = false'), reset.index('try await clearIndex()'))
        clear = body(self.index, 'private func clearIndex()')
        order = ['try await withCheckedThrowingContinuation', 'index.deleteAllSearchableItems',
                 'continuation.resume(throwing: error)', 'indexed = [:]']
        offsets = [clear.index(t) for t in order]
        self.assertEqual(offsets, sorted(offsets))
        self.assertIn('else { continuation.resume() }', clear)
        self.assertNotIn('withDomainIdentifiers:', clear)
        self.assertNotIn('matchingIdentifiers(', clear)

    def test_original_id_fetch_error_sets_empty_array_then_resets_context(self):
        source = self.fragments['0x10036dc00']
        self.assertIn('"identifier IN %@"', source)
        self.assertIn('Error::get_localizedDescription()', source)
        self.assertIn('self.unknown = PTR___swiftEmptyArrayStorage_100eae0d8', source)
        self.assertLess(source.index('self.unknown = PTR___swiftEmptyArrayStorage_100eae0d8'),
                        source.index('objc_stub::reset(local_1d0)'))
        self.assertLess(source.index('objc_stub::reset(local_1d0)'), source.index('FUN_1002faafc()'))

    def test_native_id_fetch_catches_only_fetch_error_and_returns_empty_before_mapping(self):
        make = body(self.persistence, 'func searchIndexRecords(')
        fetch = body(make, 'do ')
        self.assertIn('objects = try context.fetch(request)', fetch)
        self.assertNotIn('decode(', fetch)
        failure = body(make, 'catch')
        self.assertIn('guard identifiers != nil else { throw error }', failure)
        self.assertIn('error.localizedDescription', failure)
        self.assertIn('return []', failure)
        self.assertLess(make.index('catch'), make.index('return try objects.map'))
        self.assertIn('let value = try ClipboardPersistence.decode(ClipboardItem.self, object)', make)
        self.assertNotIn('rollback', failure)

    def test_fetch_projection_reset_is_deferred_and_does_not_capture_objects_in_records(self):
        make = body(self.persistence, 'func searchIndexRecords(')
        self.assertIn('defer { context.reset() }', make)
        self.assertEqual(make.count('context.reset()'), 2)  # prior pre-fetch reset retained; original trailing reset added
        self.assertIn('objectID: object.objectID, kind: kind', make)
        self.assertIn('content: kind == .image ? nil : { reader.content() }', make)
        self.assertNotIn('context.save()', make)

    def test_availability_check_blocks_data_sdk_and_observer_but_is_not_claimed_full_worker_fix(self):
        drain = body(self.index, 'private func initializeIndexIfNeeded(')
        guard = 'if needsReset && !CSSearchableIndex.isIndexingAvailable() { throw IndexingError.unavailable }'
        check = drain.index(guard)
        for token in ['lastSourceIdentifier = current', 'try await indexInitialSnapshot(',
                      'try await clearIndex()', 'startHistoryObservation()']:
            self.assertLess(check, drain.index(token))
        self.assertIn('Self.writeSearchableItems(', body(self.index, 'private func indexInitialSnapshot('))
        self.assertIn('worker = Task { [weak self]', body(self.index, 'private func startWorker()'))
        row, = self.proof['partial_repairs']
        self.assertEqual(row['function_id'], 'Paste:0x1002efccc')
        self.assertIn('not scored closed', row['still_open'])
        self.assertNotIn(row['function_id'], [r['function_id'] for r in self.proof['contracts']])

    def test_binary_state_schema_is_five_fields_with_invalid_count_not_store_identifier(self):
        meta = self.proof['state_metadata']
        raw = (ROOT / meta['path']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), meta['sha256'])
        data = json.loads(raw)
        state, = [d for d in data['descriptors'] if d['name'] == 'IndexingState']
        self.assertEqual([f['name'] for f in state['fields']],
                         ['schemaVersion', 'totalItems', 'indexedItems', 'oldestTimestamp', 'invalidItems'])
        self.assertEqual(state['record_size'], 12)
        self.assertEqual(state['field_count'], 5)
        for i in [0, 1, 2, 4]:
            self.assertEqual(state['fields'][i]['type']['tokens'], [{'ascii': 'Si'}])
        date = state['fields'][3]['type']['tokens']
        self.assertEqual(date[0]['symbol'], '_$s10Foundation4DateVMn')
        self.assertTrue(date[0]['external_binding'])
        self.assertNotIn('pointer_target', date[0])
        self.assertEqual(date[1], {'ascii': 'Sg'})

    def test_actor_saved_state_and_store_id_are_separate_config_wrappers(self):
        meta = json.loads((ROOT / self.proof['state_metadata']['path']).read_text())
        actor, = [d for d in meta['descriptors'] if d['name'] == 'SpotlightIndexer']
        fields = {f['name']: f for f in actor['fields']}
        state = fields['_savedState']['type']['tokens']
        self.assertEqual(state[0]['nominal'], 'Config')
        self.assertEqual(state[2]['nominal'], 'IndexingState')
        self.assertEqual(state[-1], {'ascii': 'SgG'})
        store = fields['_indexedStoreID']['type']['tokens']
        self.assertEqual(store[0]['nominal'], 'Config')
        self.assertEqual(store[-1], {'ascii': 'ySSSgG'})
        self.assertIn('isRunning', fields)
        self.assertIn('changeObserverTask', fields)

    def test_persisted_state_key_paths_and_json_codec_are_bound_for_next_migration(self):
        keys = self.proof['state_metadata']['keys']
        self.assertEqual([row['key'] for row in keys], ['indexingState', 'indexedStoreID'])
        for row in keys:
            value, = struct.unpack('<i', bytes.fromhex(row['initializer_relative_bytes']))
            self.assertEqual(int(row['initializer_field'], 16) + value, int(row['initializer'], 16))
            words = [int(w, 16) for w in row['swift_small_string_words']]
            literal = struct.pack('<2Q', *words)[:(words[1] >> 56) & 15].decode('ascii')
            self.assertEqual(literal, row['key'])
        self.assertIn('JSONDecoder::_decode', self.fragments['0x1002cb960'])
        self.assertIn('JSONEncoder::_encode', self.fragments['0x1002cba94'])

    def test_state_recovery_is_not_faked_by_new_types_or_completion_markers(self):
        self.assertEqual(len(self.proof['contracts']), 3)
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertEqual(self.proof['function_map_markers_upgraded'], 0)
        self.assertNotIn('struct IndexingState', self.index)
        self.assertIn('private var needsReset = true', self.index)
        for row in self.proof['contracts']:
            self.assertFalse(row['full_function_migration_verified'])


if __name__ == '__main__':
    unittest.main()
