from native_restore_writer_scope_contract import pre_native_restore_writer
"""Supplied copy/ID inputs and restore metadata epoch; source and Mach-O evidence only."""
from native_title_scope_contract import NEW_PATH as NATIVE_TITLE_PATH
from item_observation_scope_contract import NEW_PATH as ITEM_OBSERVATION_PATH
import hashlib
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from stack_occurrence_scope_contract import pre_stack_occurrences, pre_stack_occurrences_bytes
from supplied_input_scope_contract import CHANGES, pre_supplied_input_adapters


class SuppliedInputAdapterContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-80'
        cls.proof = json.loads((cls.phase / 'supplied-input-contract.json').read_text())
        cls.base = json.loads((cls.phase / 'baseline.json').read_text())
        cls.paths = dict(ui='replica/Sources/Pasto/UI/ReplicaUIController.swift', store='replica/Sources/PastoCore/ClipboardStore.swift')
        cls.source = {k: pre_stack_occurrences((ROOT / p).read_text()) for k, p in cls.paths.items()}
        cls.ui = cls.source['ui'];cls.store = cls.source['store']
        cls.prepare = body(cls.store, 'func prepareHistoryRestore(_ selected:')

    def before(self, key): return (self.phase / 'before' / self.paths[key]).read_text()

    def test_nine_repository_fragments_and_seven_prior_copy_fragments_are_bound(self):
        self.assertEqual(len(self.proof['original_fragments']), 9)
        for r in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / r['path'])[r['address']]['sha256'], r['sha256'])
        r = self.proof['original_copy_proof'];path = ROOT / r['path']
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), r['sha256'])
        copy = json.loads(path.read_text());self.assertEqual(len(copy['original_fragments']), 7)
        for r in copy['original_fragments']:
            self.assertEqual(source_fragments(ROOT / r['path'])[r['address']]['sha256'], r['sha256'])

    def test_binary_and_fourteen_actual_factory_transport_and_call_words_are_bound(self):
        r = self.proof['binary'];raw = (ROOT / r['path']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), r['sha256'])
        self.assertEqual(len(self.proof['ARM_words']), 14)
        for r in self.proof['ARM_words']:
            a = int(r['address'], 16) - 0x100000000
            self.assertEqual(raw[a:a + 4].hex(), r['bytes'])
        for r in self.proof['arm_disassemblies'] + [self.proof['decoder']]:
            self.assertEqual(hashlib.sha256((ROOT / r['path']).read_bytes()).hexdigest(), r['sha256'])

    def test_protocol_associated_writer_and_method_table_are_real_reachable_pointers(self):
        ns = {};p = ROOT / self.proof['decoder']['path']
        exec(p.read_text().split("idx={r['address']", 1)[0], ns)
        pointers = self.proof['pointers'];self.assertEqual(len(pointers), 4)
        for r in pointers:
            a = int(r['address'], 16);value, chain = ns['reachable_pointer'](a)
            self.assertEqual(ns['read'](a, 8).hex(), r['bytes'])
            self.assertEqual(hex(ns['base'] + (value & ((1 << 36) - 1))), r['target'])
            self.assertEqual(chain, r['chain'])
        self.assertEqual(pointers[1]['address'], '0x100eccae0')  # Protocol associated writer +0x10
        self.assertEqual(pointers[1]['target'], '0x100ecca50')
        self.assertEqual(pointers[3]['address'], '0x100ecca78')  # Writing +0x28
        self.assertEqual(pointers[3]['target'], '0x100364014')
        self.assertEqual([r['name'] for r in self.proof['conformances']], ['ItemRepositoryProtocol', 'ItemRepositoryWriting'])
        for r in self.proof['conformances']:
            a = int(r['address'], 16);data = ns['read'](a, 16)
            self.assertEqual(data.hex(), r['bytes'])
            self.assertEqual(hex(a + 8 + struct.unpack_from('<i', data, 8)[0]), r['table'])
            self.assertEqual(ns['read'](int(r['protocol_descriptor'], 16), 24).hex(), r['protocol_bytes'])
            start = ns['offset'](int(r['name_address'], 16));raw = ns['raw']
            self.assertEqual(raw[start:raw.index(b'\0', start)].decode(), r['name'])

    def test_factory_returned_witness_is_same_table_used_at_assignment_slot(self):
        words = {int(r['address'], 16): int.from_bytes(bytes.fromhex(r['bytes']), 'little') for r in self.proof['ARM_words']}
        self.assertEqual(words[0x100359500], 0xaa0303f7)  # x3 witness→x23
        self.assertEqual(words[0x100359510], 0xaa0803f6)  # hidden output x8→x22
        self.assertEqual(words[0x100359590], 0xa901ded9)  # metadata/witness→output+0x18/+0x20
        self.assertEqual(words[0x1003ba180], 0xf9400b65)  # associated writer at witness+0x10
        self.assertEqual(words[0x1003ba184], 0xf94014a8)  # method slot+0x28
        self.assertEqual(words[0x1003ba18c], 0xaa1903e0)  # preserved input→x0
        for pc, target in [(0x100357d10, 0x1003594e4), (0x1003ba168, 0x100357cf0), (0x100364024, 0x1003614c0)]:
            delta = words[pc] & 0x3ffffff
            if delta & 0x2000000: delta -= 0x4000000
            self.assertEqual(pc + delta * 4, target)

    def test_main_verified_read_only_inventory_binds_fifteen_current_method_bodies(self):
        r = self.proof['consumer_audit'];path = ROOT / r['path']
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), r['sha256'])
        audit = json.loads(path.read_text());self.assertEqual(len(audit['production_methods']), 15)
        for row in audit['production_methods']:
            from group_menu_input_scope_contract import pre_group_menu_input
            value = body(pre_group_menu_input((ROOT / row['path']).read_text()), row['symbol'])
            self.assertEqual(hashlib.sha256(value.encode()).hexdigest(), row['body_sha256'])

    def test_two_actual_source_files_and_after_snapshots_are_bound(self):
        self.assertEqual(set(self.proof['current_sources']), set(self.paths.values()))
        for p, h in self.proof['current_sources'].items():
            raw = pre_stack_occurrences_bytes(ROOT / p)
            self.assertEqual(hashlib.sha256(raw).hexdigest(), h)
            self.assertEqual(raw, (self.phase / 'after' / p).read_bytes())

    def test_single_copy_forwards_supplied_value_without_identifier_reconstruction(self):
        f = body(self.ui, 'func copy(item:')
        self.assertIn('performCopy {', f)
        self.assertIn('store.writeToPasteboard(selectedItems: [item], pasteboard: pasteboard, plainTextOnly: plainTextOnly)', f)
        for token in ['copy(ids:', 'store.items', 'reload()', '.map', 'Set(', 'requiredItem(']:
            self.assertNotIn(token, f)
        self.assertEqual(body(self.ui, 'private func performCopy('), body(self.before('ui'), 'private func performCopy('))
        self.assertEqual(body(self.ui, 'func copySelection('), body(self.before('ui'), 'func copySelection('))

    def test_real_stack_single_copy_callback_uses_shared_supplied_item_route(self):
        path = 'replica/Sources/Pasto/UI/AuxiliaryViews.swift';s = pre_stack_occurrences((ROOT / path).read_text())
        self.assertEqual(hashlib.sha256(s.encode()).hexdigest(), self.base['production'][path])
        stack = s[s.index('struct ReplicaStackTable:'):]
        self.assertIn('Button("复制") { state.controller?.copy(item: item, plainTextOnly: false) }', stack)
        self.assertIn('state.controller?.copy(item: item, plainTextOnly: false)', s)
        # Changing the shared P0/P1 writer does not edit the preview UI.
        self.assertEqual(pre_stack_occurrences_bytes(ROOT / path), (self.phase / 'before' / path).read_bytes())

    def test_set_adapter_preserves_cached_order_and_appends_all_unseen_requested_ids(self):
        f = body(self.store, 'public func assign(ids:')
        order = ['var ordered = items.filter { ids.contains($0.id) }.map(\\.id)',
                 'let cached = Set(ordered)', 'ordered += ids.subtracting(cached).sorted',
                 'try assign(orderedIDs: ordered, to: pinboardID)']
        self.assertEqual([f.index(t) for t in order], sorted(f.index(t) for t in order))
        self.assertIn('$0.uuidString < $1.uuidString', f)
        self.assertEqual(f.count('try assign('), 1)
        for token in ['ids.intersection', 'guard let item', 'throw ', 'mutate {', 'reload()']:
            self.assertNotIn(token, f)

    def test_actual_set_callers_supply_item_ids_to_transactional_ordered_assign(self):
        path = 'replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift';s = pre_stack_occurrences((ROOT / path).read_text())
        self.assertEqual(hashlib.sha256(s.encode()).hexdigest(), self.base['production'][path])
        for token in ['store.assign(ids: [self.itemID], to: board.id)', 'store.assign(ids: [itemID], to: board.id)']:
            self.assertIn(token, s)
        f = body(self.store, 'public func assign(orderedIDs:')
        self.assertEqual(f, body(self.before('store'), 'public func assign(orderedIDs:'))
        self.assertLess(f.index('try mutate { state in'), f.index('state.items.firstIndex'))
        self.assertIn('for id in orderedIDs where seen.insert(id).inserted', f)

    def test_preparation_refresh_is_revision_guarded_and_lock_scoped_before_availability_check(self):
        f = self.prepare;locked = body(f, 'return try withLock')
        self.assertLess(f.index('try validate(local)'), f.index('return try withLock'))
        self.assertIn('var state = local', locked);self.assertIn('var previous = baseline', locked)
        refresh = body(locked, 'if try revision() != diskRevision')
        order = ['previous = try latestState()', 'state = merge(local, onto: previous)', 'try validate(state)']
        self.assertEqual([refresh.index(t) for t in order], sorted(refresh.index(t) for t in order))
        self.assertLess(locked.index('if try revision() != diskRevision'), locked.index('let available = Set(state.items'))
        self.assertEqual(locked.count('latestState()'), 1)
        self.assertNotIn('latestState()', locked.replace(refresh, ''))
        self.assertNotIn('merge(local, onto: previous)', locked.replace(refresh, ''))

    def test_selected_order_and_values_are_not_reconstructed_during_metadata_refresh(self):
        f = self.prepare
        self.assertIn('guard selected.allSatisfy({ available.contains($0.id) })', f)
        self.assertIn('HistoryRestoreOperation(local: state, previous: previous,', f)
        self.assertIn('ids: selected.map(\\.id)', f)
        for token in ['selected =', 'Set(selected', 'selected.filter', 'selected.compactMap', 'selected.sorted', 'state.items.map']:
            self.assertNotIn(token, f)
        self.assertLess(f.index('guard selected.allSatisfy'), f.index('persistence.prepareHistoryRestore(ids:'))

    def test_revision_and_state_reads_use_private_snapshot_reader_not_held_view_context_reset(self):
        persistence = (ROOT / 'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text()
        for marker, token in [('func read() throws', 'snapshotReader.read()'), ('func revision() throws', 'snapshotReader.revision()')]:
            self.assertIn(token, body(persistence, marker))
        reader = (ROOT / 'replica/Sources/PastoCore/ClipboardSnapshotReader.swift').read_text()
        self.assertIn('NSManagedObjectContext(concurrencyType: .privateQueueConcurrencyType)', reader)
        self.assertNotIn('context.reset', self.prepare)
        self.assertNotIn('context.rollback', self.prepare)
        self.assertNotIn('save(', self.prepare)

    def test_post_writer_restore_keeps_prepared_state_transaction_and_targets_without_new_refresh(self):
        method = body(self.store, 'func recordRestoredSelection(')
        self.assertEqual(method, body(self.before('store'), 'func recordRestoredSelection('))
        for token in ['operation.native.targets.map(\\.id)', 'preparedRestore: operation']:
            self.assertIn(token, method)
        self.assertNotIn('latestState()', method)
        worker = body(self.store, 'private func mutateInTransaction<T>(')
        self.assertEqual(worker, body(self.before('store'), 'private func mutateInTransaction<T>('))
        for token in ['preparedRestore?.local ?? current', 'preparedRestore?.previous ?? latestState()',
                      'preparedRestore?.local ?? merge(local, onto: remote)', 'preparedRestore?.native.transaction']:
            self.assertIn(token, worker)
        path = 'replica/Sources/PastoCore/Pasteboard.swift'
        self.assertEqual(hashlib.sha256(pre_native_restore_writer((ROOT / path).read_text()).encode()).hexdigest(), self.base['production'][path])
        writer = body(pre_native_restore_writer((ROOT / path).read_text()), 'private func writeToPasteboard(ids:')
        self.assertLess(writer.index('prepareHistoryRestore(selected)'), writer.index('writer.f_10037875c(objects)'))
        self.assertLess(writer.index('writer.f_10037875c(objects)'), writer.index('recordRestoredSelection(restoration)'))

    def test_reusable_mutation_latest_state_merge_and_error_boundaries_are_unchanged(self):
        for marker in ['private func latestState()', 'private func merge(', 'private func mergedEntities<',
                       'public func updateItem(', 'public func duplicateItem(',
                       'public func delete(orderedIDs: [UUID], currentPinboardID:', 'public func assign(orderedIDs:']:
            self.assertEqual(body(self.store, marker), body(self.before('store'), marker))
        latest = body(self.store, 'private func latestState()')
        self.assertLess(latest.index('if try revision() == diskRevision { return baseline }'), latest.index('try persistence.read()'))
        worker = body(self.store, 'private func mutateInTransaction<T>(')
        self.assertLess(worker.index('let remote = try preparedRestore?.previous ?? latestState()'), worker.index('try change(&state, transaction)'))
        self.assertLess(worker.index('merge(local, onto: remote)'), worker.index('try change(&state, transaction)'))

    def test_other_ID_OCR_paste_and_original_group_selection_candidate_are_not_silently_rewritten(self):
        for marker in ['func copy(ids:', 'func copyRecognizedImageText(', 'func paste(item:',
                       'func assignSelection(', 'func createPinboard(']:
            self.assertEqual(body(self.ui, marker), body(self.before('ui'), marker))
        self.assertTrue(any('UI group selected-order' in r for r in self.proof['adaptations']))
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertEqual(self.proof['repaired_finite_contracts'], [])
        self.assertEqual(self.proof['remaining_confirmed_differences'], ['Paste:0x1003544dc'])

    def test_only_three_reviewed_method_bodies_change_two_existing_files(self):
        self.assertEqual(len(CHANGES), 3)
        for key in self.paths:
            self.assertEqual(pre_supplied_input_adapters(self.source[key]), self.before(key))
        sha = lambda p: hashlib.sha256(pre_stack_occurrences_bytes(ROOT / p)).hexdigest()
        self.assertEqual({p for p, h in self.base['production'].items() if sha(p) != h}, set(self.paths.values()))
        files = {str(p.relative_to(ROOT)) for p in (ROOT / 'replica/Sources').rglob('*') if p.is_file()}
        self.assertEqual(files - {NATIVE_TITLE_PATH, ITEM_OBSERVATION_PATH}, set(self.base['production']))
        for path in ['replica/Package.swift', 'package.json']:
            self.assertEqual(sha(path), self.base['other'][path])


if __name__ == '__main__': unittest.main()
