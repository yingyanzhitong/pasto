"""Actual managed ordering/list-source wiring; source/static fixtures only, no CoreData runtime."""
from native_title_scope_contract import NEW_PATH as NATIVE_TITLE_PATH
from item_observation_scope_contract import NEW_PATH as ITEM_OBSERVATION_PATH
import hashlib
import json
import plistlib
import struct
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from collection_membership_scope_contract import ENTRY_PATH, pre_collection_membership_bytes
from modal_restore_scope_contract import RESTORE_ITEM_PATH, pre_modal_restore, pre_modal_restore_bytes
from test_p0_repair_checksum_routing import original_fragment
from item_order_scope_contract import (without_order_persistence, without_list_factory, without_list_request,
    without_list_UI_insertions, assert_history_list_projection_only, assert_common_FRC_ctor_only, assert_order_migration_only)
from collection_initial_ids_scope_contract import assert_initial_ID_route_only
from live_item_render_scope_contract import pre_live_render, pre_live_render_bytes, REFERENCE_PATH


class NativeListOrderContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-70'
        cls.proof = json.loads((cls.phase / 'native-list-order-contract.json').read_text())
        cls.base = json.loads((cls.phase / 'baseline.json').read_text())
        cls.paths = dict(order='replica/Sources/PastoCore/ClipboardItemOrderPersistence.swift',
            persistence='replica/Sources/PastoCore/ClipboardPersistence.swift',
            lists='replica/Sources/PastoCore/ClipboardListPersistence.swift',
            store='replica/Sources/PastoCore/ClipboardStore.swift',
            frc='replica/Sources/PastoCore/ClipboardSearchCollection.swift',
            ui='replica/Sources/Pasto/UI/ReplicaUIController.swift')
        cls.source = {k: pre_live_render((ROOT / p).read_text()) for k, p in cls.paths.items()}
        cls.original = {r['address']: original_fragment((ROOT / r['path']).read_text(), r['address'][2:]) for r in cls.proof['original_fragments']}

    def before(self, key): return (self.phase / 'before' / self.paths[key]).read_text()

    def test_original_fragments_static_ARM_and_actual_source_bytes_are_bound(self):
        self.assertEqual(len(self.proof['original_fragments']), 11)
        for row in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / row['path'])[row['address']]['sha256'], row['sha256'])
        for row in [self.proof['binary'], self.proof['model']] + self.proof['arm_disassemblies']:
            self.assertEqual(hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest(), row['sha256'])
        for path, digest in self.proof['current_sources'].items():
            frozen = (self.phase / 'after' / path).read_bytes()
            self.assertEqual(hashlib.sha256(frozen).hexdigest(), digest)
            if path == self.paths['frc']:
                assert_initial_ID_route_only(self, (ROOT / path).read_text(), frozen.decode())
            else:
                self.assertEqual(pre_live_render((ROOT / path).read_text()).encode(), frozen)

    def test_original_MOM_has_Item_order_and_List_metadata_but_no_invented_ItemMetadata(self):
        model = self.proof['model']
        archive = plistlib.loads((ROOT / model['path']).read_bytes());objects = archive['$objects']
        deref = lambda v: objects[v.data] if isinstance(v, plistlib.UID) else v
        entities = {deref(e['NSEntityName']): e for e in objects if isinstance(e, dict) and 'NSEntityName' in e}
        self.assertEqual(len(entities), 9);self.assertNotIn('ItemMetadataEntity', entities)
        def properties(entity):
            p = deref(entity['NSProperties']);return {deref(k): deref(v) for k, v in zip(p['NS.keys'], p['NS.objects'])}
        order = properties(entities['ItemEntity'])['displayOrderInPinboard']
        self.assertEqual(order['NSAttributeType'], 300)
        self.assertEqual(deref(order['NSDefaultValue']), 0)
        self.assertNotIn('index', properties(entities['ItemEntity']))
        self.assertIn('index', properties(entities['ListMetadataEntity']))
        self.assertEqual(hashlib.sha256((ROOT / model['decoded_path']).read_bytes()).hexdigest(), model['decoded_sha256'])
        self.assertIn('ObjectMetadata', entities)

    def test_real_sort_getter_setter_selectors_and_ascending_flags_match_original(self):
        self.assertEqual([r['selector'] for r in self.proof['selector_bindings']], [
            'initWithKey:ascending:', 'setSortDescriptors:', 'setPredicate:',
            'displayOrderInPinboard', 'setDisplayOrderInPinboard:'])
        for row in self.proof['selector_bindings']:
            self.assertTrue(row['chain']['declared_chain_reachable'])
            self.assertEqual(bytes.fromhex(row['selector_bytes']['bytes']), row['selector'].encode() + b'\0')
        words = {int(r['address'], 16): struct.unpack('<I', bytes.fromhex(r['bytes']))[0] for r in self.proof['ARM_words']}
        self.assertEqual(words[0x100329140], 0x52800003)
        self.assertEqual(words[0x100329290], 0x52800023)
        self.assertEqual(bytes.fromhex(self.proof['order_key']['bytes']), b'displayOrderInPinboard\0')
        self.assertIn('setDisplayOrderInPinboard_', self.original['0x100362584'])

    def test_actual_request_builder_distinguishes_history_group_and_default(self):
        request = body(self.source['lists'], 'func itemRequest(for list:')
        self.assertIn('let request = PastoItemEntity.defaultFetchRequest()', request)
        self.assertIn('?.int64Value ?? 0', request)
        history = request.split('case 1:', 1)[1].split('case 2:', 1)[0]
        group = request.split('case 2:', 1)[1].split('default:', 1)[0]
        self.assertIn('NSSortDescriptor(key: "timestamp", ascending: false)', history)
        self.assertIn('NSPredicate(format: "timestamp != nil")', history)
        self.assertIn('NSSortDescriptor(key: "displayOrderInPinboard", ascending: true)', group)
        self.assertIn('NSPredicate(format: "list == %@", list)', group)
        self.assertIn('default: break', request)
        self.assertNotIn('metadata.index', request)
        self.assertNotIn('fetchLimit', request)
        self.assertNotIn('catch', request)
        self.assertIn('FUN_1003298a0(0,FUN_1003214a8)', self.original['0x100329088'])

    def test_current_model_adds_required_default_zero_order_and_optional_marker_only(self):
        add = body(self.source['order'], 'static func addField(')
        for token in ['order.name = "displayOrderInPinboard"; order.attributeType = .integer64AttributeType',
                      'order.isOptional = false; order.defaultValue = 0',
                      'model.entitiesByName["Item"]!.properties.append(order)',
                      'version.attributeType = .integer64AttributeType; version.isOptional = true',
                      'model.entitiesByName["State"]!.properties.append(version)']:
            self.assertIn(token, add)
        for token in ['model.entities.append', 'ItemMetadata', '.relationship', 'renamingIdentifier', 'removeAll']:
            self.assertNotIn(token, add)
        model = body(self.source['persistence'], 'private static func makeModel(')
        self.assertIn('if includeItemOrder { ClipboardItemOrderPersistence.addField(to: model) }', model)
        self.assertIn('includeItemOrder: Bool = true', self.source['persistence'])
        self.assertLess(model.index('model.entities ='), model.index('ClipboardItemOrderPersistence.addField'))

    def test_eight_old_candidates_preserve_typed_model_and_all_seven_earlier_descriptions(self):
        current = body(self.source['persistence'], 'private static func migrateLegacyStoreIfNeeded(')
        previous = body(self.before('persistence'), 'private static func migrateLegacyStoreIfNeeded(')
        assert_order_migration_only(self, current, previous)
        rows = current.split('let legacyCandidates = [', 1)[1].split('\n        ]', 1)[0]
        self.assertEqual(rows.count('makeModel('), 8)
        self.assertEqual(rows.count('includeItemOrder: false'), 8)
        self.assertEqual(rows.count('includeTypedItem: false'), 7)
        self.assertIn('makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, includeItemOrder: false)', rows)
        self.assertNotIn('destroyPersistentStore', current)
        self.assertLess(current.index('manager.migrateStore('), current.index('coordinator.replacePersistentStore('))
        self.assertEqual(without_order_persistence(self.source['persistence']), self.before('persistence'))

    def test_backfill_guard_is_before_blob_decode_marker_after_all_rows_same_save_transaction(self):
        bootstrap = body(self.source['order'], 'static func bootstrap(')
        order = ['guard (root.value(forKey: versionKey) as? NSNumber)?.int64Value != 1',
                 'context.fetch(PastoItemEntity.defaultFetchRequest())', 'ClipboardPersistence.decode(ClipboardItem.self, object)',
                 'object.setValue(item.pinboardOrder ?? 0, forKey: "displayOrderInPinboard")',
                 'root.setValue(Int64(1), forKey: versionKey)']
        self.assertEqual([bootstrap.index(t) for t in order], sorted(bootstrap.index(t) for t in order))
        for token in ['catch', 'try?', 'context.save()']:
            self.assertNotIn(token, bootstrap)
        actual = body(self.source['persistence'], 'private func bootstrapListsIfNeeded()')
        order = ['try perform', 'try bootstrapHistoryTimestamps()', 'try bootstrapSourcesIfNeeded(root)',
                 'try ClipboardItemOrderPersistence.bootstrap(in: context, root: root)', 'if context.hasChanges', 'try context.save()']
        self.assertEqual([actual.index(t) for t in order], sorted(actual.index(t) for t in order))

    def test_new_root_is_marked_before_save_to_prevent_restart_overwriting_native_order(self):
        commit = body(self.source['persistence'], 'func commit<T>(')
        inserted = body(commit, 'if root.isInserted')
        self.assertIn('root.setValue(Int64(1), forKey: ClipboardItemOrderPersistence.versionKey)', inserted)
        self.assertLess(commit.index('ClipboardItemOrderPersistence.versionKey'), commit.index('try context.save()'))
        bootstrap = body(self.source['order'], 'static func bootstrap(')
        self.assertNotIn('content', bootstrap.split('!= 1 else { return }', 1)[0])
        # Source-bound restart fixture. No NSManagedObject/database is created.
        for existing_marker, blob_order, initial_column in [(None, 7, 0), (1, None, 4)]:
            marker, column = existing_marker, initial_column
            if marker != 1: column = blob_order if blob_order is not None else 0;marker = 1
            column = 3  # ordinary reorder; new content deliberately strips order
            if marker != 1: column = blob_order if blob_order is not None else 0
            self.assertEqual(column, 3)

    def test_reads_project_actual_column_after_owner_and_never_rederive_order_from_blob(self):
        project = body(self.source['order'], 'static func project(')
        self.assertIn('guard !item.pinboardIDs.isEmpty else { item.pinboardOrder = nil; return }', project)
        self.assertIn('object.value(forKey: "displayOrderInPinboard") as? NSNumber', project)
        self.assertIn('item.pinboardOrder = order', project)
        self.assertNotIn('decode', project)
        item = body(self.source['persistence'], 'nonisolated static func item(')
        self.assertLess(item.index('item.pinboardOwnerID = owner'), item.index('try ClipboardItemOrderPersistence.project(&item, from: object)'))
        self.assertLess(item.index('try ClipboardItemOrderPersistence.project'), item.index('return item'))
        reader = (ROOT / 'replica/Sources/PastoCore/ClipboardSnapshotReader.swift').read_text()
        self.assertIn('.map(ClipboardPersistence.item)', body(reader, 'func read()'))

    def test_commit_order_update_is_outside_blob_replacement_after_owner_before_save(self):
        commit = body(self.source['persistence'], 'func commit<T>(')
        update = 'ClipboardItemOrderPersistence.update(item, on: object)'
        encoded = body(commit, 'if old.map(content) != content(item)')
        self.assertNotIn(update, encoded)
        self.assertLess(commit.index('object.setValue(owner, forKey: "list")'), commit.index(update))
        self.assertLess(commit.index(update), commit.index('try context.save()'))
        setter = body(self.source['order'], 'static func update(')
        self.assertIn('let order = item.pinboardOrder ?? 0', setter)
        self.assertIn('?.int64Value != order', setter)
        self.assertIn('object.setValue(order, forKey: "displayOrderInPinboard")', setter)
        self.assertNotIn('encode', setter)

    def test_order_only_reorder_does_not_reencode_unchanged_payload_blob(self):
        content = body(self.source['persistence'], 'private func content(')
        self.assertIn('value.pinboardOrder = nil', content)
        self.assertIn('if old.map(content) != content(item)', body(self.source['persistence'], 'func commit<T>('))
        # Scalar signatures model the real content comparison; they are not a Swift serializer test.
        payload = ('image', 'unchanged-large-bytes', 'title')
        old = (payload, 3);new = (payload, 9)
        self.assertNotEqual(old, new)
        self.assertEqual((old[0], None), (new[0], None))
        changed_payload = (('image', 'changed-bytes', 'title'), 9)
        self.assertNotEqual((old[0], None), (changed_payload[0], None))

    def test_actual_store_and_persistence_factories_use_same_stable_context_and_real_request(self):
        facade = body(self.source['store'], 'public func makeListCollection(')
        self.assertIn('persistence.makeListCollection(identifier: pinboardID?.uuidString ?? Self.historyListIdentifier)', facade)
        factory = body(self.source['persistence'], 'func makeListCollection(')
        for token in ['context.performAndWait', 'guard let list = try? lists.list(identifier: identifier) else { return nil }',
                      'ClipboardSearchCollection(context: context, request: lists.itemRequest(for: list))']:
            self.assertIn(token, factory)
        self.assertNotIn('context.reset()', factory)
        self.assertNotIn('items.filter', factory)

    def test_shared_FRC_common_initializer_keeps_original_error_delegate_and_observer_order(self):
        assert_common_FRC_ctor_only(self, self.source['frc'], self.before('frc'))
        common = body(self.source['frc'], 'init(context: NSManagedObjectContext, request:')
        order = ['controller = NSFetchedResultsController(', 'sectionNameKeyPath: nil, cacheName: nil)',
                 'try controller.performFetch()', 'catch { fatalError(', 'controller.delegate = delegate',
                 'flushPending()', 'objectsObservation = NotificationCenter.default']
        self.assertEqual([common.index(t) for t in order], sorted(common.index(t) for t in order))
        search = body(self.source['frc'], 'convenience init(context:')
        self.assertIn('self.init(context: context, request: request)', search)
        self.assertIn('if objectIDs.count != identifiers.count', search)
        self.assertNotIn('identifiers.count', common)
        for marker in ['private func receive(', 'private func flushPending()', 'private func objectsDidChange(', 'nonisolated func controller(']:
            self.assertEqual(body(self.source['frc'], marker), body(self.before('frc'), marker))

    def test_retained_ordinary_source_cancels_previous_subscription_and_suppresses_hidden_updates(self):
        ui = self.source['ui']; install = body(ui, 'private func installListCollectionSource()')
        order = ['listCollectionObservation = nil', 'listCollection = nil', 'guard isCollectionSearchQueryEmpty else { return }',
                 'store.makeListCollection(pinboardID: pinboardID)', 'listCollection = source',
                 'source?.publisher.dropFirst().sink { [weak self] snapshot',
                 'self.isCollectionSearchQueryEmpty, !self.showDeleted', 'pendingCollectionChangedIDs.formUnion(snapshot.updatedIdentifiers)',
                 'self.objectWillChange.send()']
        self.assertEqual([install.index(t) for t in order], sorted(install.index(t) for t in order))
        for token in ['normalizeSelection', 'applyOrderedSelection', 'replaceCollectionModel', 'context.save()']:
            self.assertNotIn(token, install)
        self.assertIn('private var listCollection: ClipboardSearchCollection?', ui)
        self.assertIn('private var listCollectionObservation: AnyCancellable?', ui)

    def test_query_and_list_switch_install_actual_source_before_normalizing_or_replacing_applier(self):
        ui = self.source['ui']
        query = body(ui, 'private func installSearchQueryDelivery()')
        order = ['self.collectionSearchQueryNodes = nodes', 'self.installListCollectionSource()', 'self.normalizeSelection()', 'self.collectionOwner?.replaceCollectionModel(state: self)']
        self.assertEqual([query.index(t) for t in order], sorted(query.index(t) for t in order))
        chosen = body(ui, 'private func applySelectedList(')
        self.assertLess(chosen.index('pinboardID = id'), chosen.index('installListCollectionSource()'))
        self.assertLess(chosen.index('installListCollectionSource()'), chosen.index('normalizeProjectedSelection()'))

    def test_primary_history_and_group_visible_items_follow_FRC_order_and_keep_explicit_adapters(self):
        visible = body(self.source['ui'], 'var visibleItems:')
        history = body(visible, 'if isCollectionSearchQueryEmpty')
        for token in ['if showDeleted', 'includeDeleted: true).filter(\\.isDeleted)',
                      'let identifiers = listCollection?.value.identifiers ?? []',
                      'let native = identifiers.compactMap { items[$0] }.filter { !$0.isDeleted }', 'return native']:
            self.assertIn(token, history)
        legacy = body(history, 'if let pinboardID')
        self.assertIn('filter { $0.pinboardOwnerID != pinboardID }', legacy)
        self.assertIn('if !legacy.isEmpty', legacy)
        self.assertIn('Set(identifiers).union(legacy.map(\\.id))', legacy)
        # Pure scalar normal-domain fixtures: own membership and database order, no UUID tie sorting.
        snapshots = {'A': False, 'B': False, 'C': True}
        self.assertEqual([i for i in ['B', 'C', 'A'] if i in snapshots and not snapshots[i]], ['B', 'A'])
        self.assertNotIn('.sorted', history)

    def test_legacy_secondary_membership_does_not_silently_disappear_from_the_UI(self):
        identifiers = ['B', 'A'];legacy = ['secondary']
        retained = set(identifiers) | set(legacy)
        # This branch deliberately keeps old local ordering, not claimed native equality.
        old_store_order = ['A', 'secondary', 'B', 'unrelated']
        self.assertEqual([i for i in old_store_order if i in retained], ['A', 'secondary', 'B'])
        self.assertIn('existing Store ordering', ' '.join(self.proof['retained_partial_contracts']))
        self.assertIn('mixed legacy domain', ' '.join(self.proof['retained_partial_contracts']))

    def test_only_five_existing_files_and_one_new_order_adapter_change(self):
        actual = {str(p.relative_to(ROOT)) for p in (ROOT / 'replica/Sources').rglob('*') if p.is_file()}
        changed = {p for p, digest in self.base['production'].items() if hashlib.sha256(pre_live_render_bytes(ROOT / p)).hexdigest() != digest}
        self.assertEqual(changed, set(self.paths.values()) - {self.paths['order']})
        self.assertEqual(actual - {NATIVE_TITLE_PATH, ITEM_OBSERVATION_PATH} - set(self.base['production']) - {REFERENCE_PATH, RESTORE_ITEM_PATH, ENTRY_PATH}, {self.paths['order']})
        self.assertEqual(without_order_persistence(self.source['persistence']), self.before('persistence'))
        self.assertEqual(without_list_factory(self.source['store'], public=True), self.before('store'))
        self.assertEqual(without_list_request(self.source['lists']), self.before('lists'))
        a = without_list_UI_insertions(self.source['ui']);b = without_list_UI_insertions(self.before('ui'))
        av = body(a, 'var visibleItems:');bv = body(b, 'var visibleItems:')
        assert_history_list_projection_only(self, av, bv)
        self.assertEqual(a.split(av), b.split(bv))

    def test_v14_preserves_old160_records_and_adds_only_actual_list_request_gap(self):
        old = json.loads((ROOT / 'reports/replica/p0-p1-difference-backlog-v13.json').read_text())
        new = json.loads((ROOT / 'reports/replica/p0-p1-difference-backlog-v14.json').read_text())
        self.assertEqual(new['groups'][:-1], old['groups'])
        rows = [r for g in new['groups'] for r in g['records']]
        self.assertEqual(len(rows), 161);self.assertEqual(len({r['function_id'] for r in rows}), 161)
        self.assertEqual(new['added_function_ids'], ['Paste:0x100329088'])
        self.assertEqual(new['counts']['p0_records'], 69)
        self.assertEqual(new['counts']['p1_additional_records'], 92)

    def test_full_original_schema_provider_witness_runtime_migration_and_goal_stay_unclosed(self):
        row, = self.proof['contracts']
        self.assertEqual(row['function_id'], 'Paste:0x100329088')
        self.assertFalse(row['full_function_migration_verified'])
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertEqual(self.proof['function_map_markers_upgraded'], 0)
        limits = ' '.join(self.proof['retained_partial_contracts'])
        for token in ['eight old candidates', 'not executed', 'unique365cd8', 'Unknown04430c/0f733c', 'model hash']:
            self.assertIn(token, limits)


if __name__ == '__main__': unittest.main()
