"""Source projection and provenance checks; no Swift, Core Data, SDK, or app execution."""
import hashlib
import itertools
import json
import re
import struct
import unittest
from test_offline_p0_contracts import ROOT
from snapshot_read_scope_contract import body

HISTORY = ROOT / 'replica/Sources/PastoCore/OriginalSearchHistory.swift'
DB = ROOT / 'replica/Sources/PastoCore/ClipboardPersistence.swift'
STORE = ROOT / 'replica/Sources/PastoCore/ClipboardStore.swift'
INDEX = ROOT / 'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift'


def token_follows_consumer(source):
    try:
        process = body(source, 'func process() async')
        tokens = ['guard !batch.isEmpty', 'try await consume(changes(in: batch))',
                  'if let next = batch.last?.token', 'token = next', 'persistToken()']
        return ([process.index(x) for x in tokens] == sorted(process.index(x) for x in tokens)
                and re.search(r'\btoken\s*=', process[:process.index('try await consume')]) is None)
    except (ValueError, IndexError):
        return False


def project_reducer(source, events):
    """Interpret only this reviewed set-operation subset, rejecting extra statements."""
    reducer = body(source, 'private func changes(in transactions:')
    second = reducer.index('switch change.changeType', reducer.index('switch change.changeType')+1)
    cases = re.findall(r'case \.(insert|update|delete):([\s\S]*?)(?=case |@unknown default:)', reducer[second:])
    if len(cases) != 3:
        raise ValueError('Unrecognized production reducer')
    actions = {}
    for kind, text in cases:
        parsed = []
        for line in text.strip().splitlines():
            match = re.fullmatch(r'\s*(?:(if !inserted.contains\(identifier\)) \{ )?(inserted|updated|deleted)\.(insert|remove)\(identifier\)( \})?\s*', line)
            if not match or bool(match[1]) != bool(match[4]):
                raise ValueError('Unrecognized reducer statement: '+line)
            parsed.append((bool(match[1]), match[2], match[3]))
        actions[kind] = parsed
    sets = {key:set() for key in ['inserted','updated','deleted']}
    for kind, identifier in events:
        if identifier is None: continue
        for conditional, target, operation in actions[kind]:
            if conditional and identifier in sets['inserted']:continue
            if operation == 'insert':sets[target].add(identifier)
            else:sets[target].discard(identifier)
    return sets


class SearchHistoryContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.history = HISTORY.read_text();cls.db=DB.read_text();cls.store=STORE.read_text();cls.index=INDEX.read_text()
        cls.report=json.loads((ROOT/'reports/replica/offline-migration-p0-round20.json').read_text())

    def test_history_options_and_delete_identity_are_enabled_for_local_item(self):
        for option in ['NSPersistentHistoryTrackingKey: true','NSPersistentStoreRemoteChangeNotificationPostOptionKey: true',
                       'NSMigratePersistentStoresAutomaticallyOption: true','NSInferMappingModelAutomaticallyOption: true']:
            self.assertIn(option,self.db)
        self.assertIn('if name == "Item" { key.preservesValueInHistoryOnDeletion = true }',self.db)
        self.assertIn('value.properties = [key] + attributes',self.db)

    def test_fetch_token_and_distant_past_branch_propagate_execution_errors(self):
        fetch=body(self.history,'private func transactions(after token:')
        for part in ['try context.performAndWait','if let token { request = .fetchHistory(after: token) }',
                     'else { request = .fetchHistory(after: Date.distantPast) }','try context.execute(request)',
                     'result?.result as? [NSPersistentHistoryTransaction] ?? []']:
            self.assertIn(part,fetch)
        self.assertNotIn('try?',fetch)

    def test_changes_flatten_transactions_filter_entity_and_resolve_live_or_deleted_identity(self):
        reducer=body(self.history,'private func changes(in transactions:')
        for part in ['transactions.flatMap({ $0.changes ?? [] })','change.changedObjectID.entity.name == "Item"',
                     'context.existingObject(with: change.changedObjectID)','change.tombstone?["key"] as? String',
                     'guard let identifier else { continue }']:
            self.assertIn(part,reducer)
        self.assertLess(reducer.index('case .insert, .update:'),reducer.index('context.existingObject'))
        self.assertNotIn('tombstone?["identifier"]',reducer) # vendor-to-Pasto model adaptation is explicit

    def test_production_set_projection_matches_original_transition_table_exhaustively(self):
        # Independent rule derived from the original raw 0/1/2 branches: update preserves pending insert.
        for length in range(1,6):
            for sequence in itertools.product(['insert','update','delete'],repeat=length):
                expected=None
                for event in sequence:
                    if event!='update' or expected!='insert':expected=event
                actual=project_reducer(self.history,[(x,'id') for x in sequence])
                target={'insert':'inserted','update':'updated','delete':'deleted'}[expected]
                self.assertEqual(actual,{k:({'id'} if k==target else set()) for k in actual},sequence)
        changed=self.history.replace('if !inserted.contains(identifier) { updated.insert(identifier) }','updated.insert(identifier)')
        self.assertNotEqual(project_reducer(changed,[('insert','id'),('update','id')]),
                            project_reducer(self.history,[('insert','id'),('update','id')]))

    def test_set_projection_keeps_identifiers_independent_and_skips_missing(self):
        events=[('insert','a'),('delete','b'),('update','a'),('insert','b'),('update','c'),('delete',None)]
        self.assertEqual(project_reducer(self.history,events),{'inserted':{'a','b'},'updated':{'c'},'deleted':set()})

    def test_empty_groups_omitted_and_delivery_order_is_insert_update_delete(self):
        reducer=body(self.history,'private func changes(in transactions:')
        tokens=['if !inserted.isEmpty { result.append(.inserted(Array(inserted))) }',
                'if !updated.isEmpty { result.append(.updated(Array(updated))) }',
                'if !deleted.isEmpty { result.append(.deleted(Array(deleted))) }']
        self.assertEqual([reducer.index(x) for x in tokens],sorted(reducer.index(x) for x in tokens))

    def test_notify_stream_is_unbounded_coordinator_scoped_and_removes_observer(self):
        notify=body(self.history,'private func notifications()')
        for part in ['reader.coordinator','AsyncStream(bufferingPolicy: .unbounded)',
                     'forName: .NSPersistentStoreRemoteChange, object: coordinator, queue: nil',
                     'continuation.yield(())','continuation.onTermination','NotificationCenter.default.removeObserver(observer)']:
            self.assertIn(part,notify)
        self.assertNotIn('Timer',notify)

    def test_secure_token_decode_encode_and_initial_catchup_precede_observation(self):
        observe=body(self.history,'func observe(_ consume:')
        for part in ['NSKeyedUnarchiver.unarchivedObject(ofClass: NSPersistentHistoryToken.self, from: data)',
                     'NSKeyedArchiver.archivedData(withRootObject: $0, requiringSecureCoding: true)',
                     'UserDefaults.standard.set(data, forKey: key)','let key = "indexHistoryTokenData"']:
            self.assertIn(part,observe)
        self.assertLess(observe.index('await process()'),observe.index('for await _ in notifications()'))
        self.assertIn('if let data = UserDefaults.standard.data(forKey: key)',observe)
        self.assertNotIn('guard let key',body(observe,'func persistToken()'))
        self.assertNotIn('guard let identity',observe) # unavailable identity must not disable the stream
        loop=body(observe,'for await _ in notifications()')
        self.assertLess(loop.index('guard !Task.isCancelled'),loop.index('await process()'))

    def test_token_advances_after_successful_consumer_even_with_no_item_changes(self):
        self.assertTrue(token_follows_consumer(self.history))
        process=body(self.history,'func process() async')
        self.assertNotIn('changes.isEmpty',process)
        self.assertNotIn('token =',process[process.index('catch is CancellationError'):])
        early=self.history.replace('try await consume(changes(in: batch))','token = nil\n                try await consume(changes(in: batch))')
        # A token mutation before consume must be rejected in addition to success-branch ordering.
        self.assertFalse(token_follows_consumer(early))
        moved=self.history.replace('try await consume(changes(in: batch))','if let next = batch.last?.token { token = next }; try await consume(changes(in: batch))')
        self.assertFalse(token_follows_consumer(moved))

    def test_serial_history_work_completes_after_sdk_and_propagates_failure(self):
        start=body(self.index,'private func startHistoryObservation()')
        self.assertIn('pendingHistory.append(HistoryWork(changes: changes)',start)
        self.assertIn('continuation.resume(throwing: error)',start)
        drain=body(self.index,'private func drain() async')
        self.assertIn('try await applyHistoryChanges(work.changes); work.complete(nil)',drain)
        self.assertIn('catch { work.complete(error) }',drain)
        self.assertLess(drain.index('pendingHistory.removeFirst()'),drain.index('applyHistoryChanges'))
        cleanup=body(self.index,'deinit')
        self.assertIn('historyTask?.cancel()',cleanup)
        self.assertIn('queryTask?.cancel()',cleanup)

    def test_history_sdk_writes_live_entities_and_updates_memory_only_after_await(self):
        apply=body(self.index,'private func applyHistoryChanges(_ changes:')
        for part in ['case .inserted(let identifiers), .updated(let identifiers):','try liveEntries(identifiers: identifiers)',
                     'guard !live.isEmpty else { continue }','index.indexSearchableItems(live.map(searchableItem))',
                     'try await deleteIdentifiers(identifiers)']:
            self.assertIn(part,apply)
        self.assertLess(apply.index('index.indexSearchableItems('),apply.index('for entry in live { indexed'))
        deletion=body(self.index,'private func deleteIdentifiers(')
        self.assertLess(deletion.index('index.deleteSearchableItems('),deletion.index('indexed.removeValue'))
        self.assertNotIn('catch',apply)

    def test_active_history_stream_prevents_old_snapshot_from_rewriting_incremental_state(self):
        drain=body(self.index,'private func drain() async')
        self.assertIn('let usesSnapshot = resettingIndex || historyTask == nil',drain)
        self.assertIn('let deleted = usesSnapshot ? Set(indexed.keys).subtracting(current.keys) : Set<UUID>()',drain)
        self.assertIn('usesSnapshot && indexed[$0.id] != $0',drain)
        self.assertIn('if usesSnapshot { indexed = current }',drain)
        self.assertIn('else { for entry in changedEntries { indexed[entry.id] = entry } }',drain)
        self.assertLess(drain.index('journalCompleted = true'),drain.index('startHistoryObservation()'))

    def test_full_and_targeted_rebuild_read_database_current_items_without_deleting_other_ids(self):
        drain=body(self.index,'private func drain() async')
        self.assertIn('if resettingIndex, store != nil { currentEntries = try liveEntries(identifiers: nil) }',drain)
        self.assertIn('try await reindexTargets(forcedIdentifiers)',drain)
        self.assertIn('try liveEntries(identifiers: Array(input[lowerBound..<upperBound]))',body(self.index,'private func reindexTargets('))
        self.assertIn('try store.searchItems(identifiers: identifiers)',body(self.index,'private func liveEntries('))
        self.assertIn('keys: identifiers',body(self.db,'func searchItems('))
        self.assertIn('try persistence.searchItems(identifiers: identifiers)',self.store)

    def test_original_selector_slots_and_event_output_tags_are_bound(self):
        proof=self.report['static_bindings']
        self.assertEqual(proof['pointer_format'],6)
        for row in proof['objc_selectors']:
            self.assertTrue(row['declared_chain_reachable'])
            raw,=struct.unpack('<Q',bytes.fromhex(row['slot_bytes']))
            self.assertEqual((raw&((1<<36)-1))+0x100000000,int(row['string_address'],16))
            self.assertEqual(bytes.fromhex(row['string_bytes']).decode(),row['selector'])
        self.assertEqual([x['selector'] for x in proof['objc_selectors']],
                         ['changeType','changedObjectID','changes','executeRequest:error:','existingObjectWithID:error:'])
        self.assertEqual(struct.unpack('<I',bytes.fromhex(proof['store_flags']['remote_true']['bytes']))[0],0x52800020)
        self.assertEqual(struct.unpack('<I',bytes.fromhex(proof['store_flags']['history_true']['bytes']))[0],0x52800020)
        self.assertEqual([x['kind'] for x in proof['event_output']],['inserted','updated','deleted'])
        self.assertEqual([x['tag'] for x in proof['event_output']],[0,1,2])
        self.assertEqual(struct.unpack('<I',bytes.fromhex(proof['event_output'][0]['bytes']))[0],0x3900a11f)
        self.assertEqual(struct.unpack('<2I',bytes.fromhex(proof['event_output'][1]['bytes'])),(0x52800029,0x3900a109))
        self.assertEqual(struct.unpack('<2I',bytes.fromhex(proof['event_output'][2]['bytes'])),(0x52800049,0x3900a109))
        entity=proof['item_entity_class']
        self.assertEqual(bytes.fromhex(entity['name_bytes']).decode(),'_TtC9PasteCore10ItemEntity')
        self.assertEqual(entity['pasto_entity_mapping'],'Item')

    def test_original_fragments_and_production_bindings_not_counted_as_complete(self):
        ledger=json.loads((ROOT/'replica/function-map.json').read_text())['functions']
        for row in self.report['functions']:
            text=(ROOT/row['original']['path']).read_text();a=row['function_id'].split(':')[1]
            start=text.index('/* Address: '+a+' |');end=text.find('/* Address:',start+1)
            self.assertEqual(hashlib.sha256((text[start:end if end!=-1 else None].rstrip()+'\n').encode()).hexdigest(),row['original']['sha256'])
            for ref in row['source_references']:self.assertIn(ref['symbol'],(ROOT/ref['path']).read_text())
            self.assertEqual(ledger[row['function_id']]['state'],'partial')
        self.assertEqual(self.report['new_fully_migrated_function_count'],0)
        self.assertFalse(self.report['module_complete'])
        self.assertTrue(self.report['remaining_differences'])


if __name__=='__main__':unittest.main()
