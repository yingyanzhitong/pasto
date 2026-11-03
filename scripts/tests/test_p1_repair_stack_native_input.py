"""Stack captured entities and actual restore consumers, verified without native execution."""
from native_title_scope_contract import NEW_PATH as NATIVE_TITLE_PATH
from item_observation_scope_contract import NEW_PATH as ITEM_OBSERVATION_PATH
import hashlib
import json
from pathlib import Path
from entity_lookup_scope_contract import pre_entity_lookup
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment
from stack_native_input_scope_contract import CHANGES, pre_stack_native_inputs
from group_menu_input_scope_contract import pre_group_menu_input, pre_group_menu_input_bytes

class StackNativeInputContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-83'
        cls.proof=json.loads((cls.phase/'stack-native-input-contract.json').read_text())
        cls.base=json.loads((cls.phase/'baseline.json').read_text())
        cls.paths=dict(ui='replica/Sources/Pasto/UI/ReplicaUIController.swift',app='replica/Sources/Pasto/AppMain.swift',aux='replica/Sources/Pasto/UI/AuxiliaryViews.swift',panel='replica/Sources/Pasto/UI/PanelViews.swift')
        cls.source={k:pre_group_menu_input((ROOT/p).read_text())for k,p in cls.paths.items()}

    def before(self,key):return (self.phase/'before'/self.paths[key]).read_text()
    def original(self,address):
        r=next(r for r in self.proof['original_fragments']if r['address']==address)
        return original_fragment((ROOT/r['path']).read_text(),address[2:])

    def test_original_fragments_binary_and_real_calls_bound(self):
        self.assertEqual(len(self.proof['original_fragments']),10)
        for r in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        r=self.proof['binary'];raw=(ROOT/r['path']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),r['sha256'])
        self.assertEqual(len(self.proof['ARM_calls']),6)
        for r in self.proof['ARM_calls']:
            pc=int(r['address'],16);b=raw[pc-0x100000000:pc-0x100000000+4];self.assertEqual(b.hex(),r['bytes'])
            w=int.from_bytes(b,'little');self.assertEqual(w&0xfc000000,0x94000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(pc+d*4,int(r['target'],16))

    def test_original_producer_creates_collection_and_gets_first_entity(self):
        source=self.original('0x100363d58')
        self.assertLess(source.index('FUN_100329088()'),source.index('FUN_100365db4()'))
        self.assertGreaterEqual(source.count('_swift_allocObject()'),2)
        capture=self.original('0x10008339c');self.assertIn('FUN_1001b8054(&local_58,0,',capture)
        self.assertIn('if (local_58 == 0)',capture);self.assertIn('FUN_100089a18(_Var12,_Var12,local_58)',capture)
        indexed=self.original('0x1001b8054');self.assertIn('(param_4 + 0x18)',indexed);self.assertIn('(param_4 + 0x20)',indexed)

    def test_original_pop_preserves_entity_for_restoration(self):
        source=self.original('0x100083e58')
        self.assertLess(source.index('FUN_10008413c()'),source.index('FUN_100085a6c('))
        self.assertIn('*(long *)(puVar10 + 0x20) = lVar6',source)
        self.assertIn('FUN_100085a6c(puVar10)',source)
        self.assertIn('FUN_10037a144(param_1.unknown',self.original('0x100085a6c'))

    def test_all_four_production_and_seven_shared_source_inputs_bound(self):
        self.assertEqual(len(self.proof['current_sources']),4)
        self.assertEqual(len(self.proof['supporting_sources']),7)
        for group in ['current_sources','supporting_sources']:
            for p,h in self.proof[group].items():self.assertEqual(hashlib.sha256(pre_group_menu_input_bytes(ROOT/p)).hexdigest(),h)
        for p in self.proof['current_sources']:self.assertEqual(pre_group_menu_input_bytes(ROOT/p),(self.phase/'after'/p).read_bytes())

    def test_native_capture_uses_new_history_snapshot_and_required_entity_without_cache_join(self):
        source=body(self.source['ui'],'private func captureLatestItemIntoStack()')
        for t in ['guard isStackVisible','store.makeListCollection(pinboardID: nil)','let snapshot = collection.value','snapshot.identifiers.first','snapshot.itemReferences[identifier]','reference.requiredRestoreItem(id: identifier)','state.addToStack(input.resolvedItem(), restoreItem: input)']:self.assertIn(t,source)
        for t in ['store.items','store.search','captureIntoStack(id:','.async','listCollection?.value']:self.assertNotIn(t,source)
        self.assertIn('fatalError("Missing Stack item reference")',source)

    def test_shared_reference_and_restore_handle_hold_actual_entity(self):
        ref=pre_entity_lookup((ROOT/'replica/Sources/PastoCore/ClipboardCollectionItemReference.swift').read_text())
        source=body(ref,'public func requiredRestoreItem(id: UUID)')
        self.assertIn('context.existingObject(with: objectID)',source)
        self.assertIn('as? PastoItemEntity',source);self.assertIn('ClipboardRestoreItem(id: id, object: object)',source)
        restore=(ROOT/'replica/Sources/PastoCore/ClipboardRestoreItem.swift').read_text()
        source=body(restore,'init(id: UUID, object: PastoItemEntity)')
        self.assertIn('resolve = {',source);self.assertIn('ClipboardPersistence.item(object)',source)
        self.assertNotIn('[weak',source)

    def test_queue_keeps_native_inputs_until_last_duplicate_removed(self):
        source=self.source['ui']
        self.assertIn('private var stackRestoreInputs: [UUID: ClipboardRestoreItem] = [:]',source)
        start=source.index('@Published var stackIDs:');end=source.index('@Published var hotKeyStatusMessage',start);changed=source[start:end]
        self.assertLess(changed.index('let retainedIDs = Set(stackIDs)'),changed.index('guard oldValue != stackIDs'))
        self.assertIn('stackRestoreInputs.filter { retainedIDs.contains($0.key) }',changed)
        # Occurrence identity remains the array's order; retaining by ID does not collapse the array.
        ids=['A','B','A'];handles={'A':object(),'B':object()};a=handles['A']
        ids.pop(0);handles={k:v for k,v in handles.items()if k in set(ids)}
        self.assertIs(handles['A'],a);self.assertEqual(ids,['B','A'])
        ids.pop(1);handles={k:v for k,v in handles.items()if k in set(ids)}
        self.assertNotIn('A',handles)

    def test_native_item_precedes_legacy_cache_and_never_silently_drops_known_input(self):
        source=body(self.source['ui'],'func stackItem(for id: UUID)')
        self.assertLess(source.index('input.resolvedItem()'),source.index('store.items.first'))
        self.assertNotIn('try?',source)
        restore=body(self.source['ui'],'func stackRestoreItem(for id: UUID)')
        self.assertIn('stackRestoreInputs[id]',restore)
        self.assertNotIn('ClipboardRestoreItem(item:',restore)
        self.assertNotIn('stackItem(for:',restore)
        self.assertIn('stackIDs.compactMap { stackItem(for: $0) }',self.source['ui'])

    def test_native_input_is_registered_before_id_insertion_and_existing_direction_preserved(self):
        source=body(self.source['ui'],'func addToStack(')
        self.assertLess(source.index('let previousIDs'),source.index('stackRestoreInputs[item.id] = restoreItem'))
        self.assertLess(source.index('stackRestoreInputs[item.id] = restoreItem'),source.index('stackIDs.insert'))
        self.assertIn('stackIDs.insert(item.id, at: append ? stackIDs.count : 0)',source)
        old=body(self.before('ui'),'func addToStack(')
        expected=old.replace('let previousIDs = stackItems.map(\\.id)', 'let previousIDs = stackItemIDs', 1)
        expected=expected.replace('        let previousIDs = stackItemIDs\n', '        let previousIDs = stackItemIDs\n        if let restoreItem { stackRestoreInputs[item.id] = restoreItem }\n', 1)
        self.assertEqual(source,expected)

    def test_real_selection_menu_uses_applied_restore_handles_in_existing_order(self):
        self.assertIn('state.controller?.addSelectionToStack()',self.source['panel'])
        source=body(self.source['ui'],'func addSelectionToStack()')
        self.assertIn('for input in appliedRestoreItems()',source)
        self.assertLess(source.index('state.addToStack(input.resolvedItem(), restoreItem: input)'),source.index('showStack()'))
        self.assertNotIn('Set(',source)
        signature='private func appliedRestoreItems(orderedIDs:'
        self.assertEqual(body(self.source['ui'],signature),body(self.before('ui'),signature))

    def test_hotkey_keeps_handle_before_pop_and_passes_it_to_real_writer(self):
        source=self.source['app'];start=source.index('stackPasteHotKey.action =');end=source.index('configureGlobalHotKeys(force: true)',start);action=source[start:end]
        self.assertLess(action.index('stackRestoreItem(for: first)'),action.index('consumeStackHead()'))
        self.assertLess(action.index('consumeStackHead()'),action.index('self.paste(ids:'))
        self.assertIn('forceDirect: true, restoreItems: input.map { [$0] }',action)
        self.assertIn('stackItemIDs.first',action)
        self.assertNotIn('stackItems',action)
        self.assertIn('if NSApp.isActive',action)
        self.assertEqual(body(source,'private func paste(ids: [UUID]'),body(self.before('app'),'private func paste(ids: [UUID]'))

    def test_real_context_copy_and_paste_consume_current_queue_input(self):
        source=self.source['aux']
        self.assertIn('if let current = state.stackItem(for: item.id)',source)
        self.assertIn('copy(item: current, plainTextOnly: false)',source)
        self.assertIn('pasteStackItem(id: item.id, plainTextOnly: false)',source)
        router=body(self.source['ui'],'func pasteStackItem(id: UUID')
        self.assertIn('state.stackRestoreItem(for: id)',router)
        self.assertIn('paste(restoreItems: [input], plainTextOnly: plainTextOnly)',router)
        self.assertIn('return paste(ids: [id], plainTextOnly: plainTextOnly)',router)
        self.assertIn('controller?.removeRow(at: row, expectedIDs: expectedIDs)',source)

    def test_actual_row_mapping_accepts_native_input_absent_from_old_store_cache(self):
        self.assertIn('state.hasStackItem(state.stackIDs[index])',self.source['aux'])
        self.assertNotIn('state.store.items.contains { $0.id == state.stackIDs[index]',self.source['aux'])
        source=body(self.source['ui'],'func hasStackItem(_ id: UUID)')
        self.assertIn('stackRestoreInputs[id] != nil || store.items.contains',source)
        self.assertIn('visibleOffsets.map({ state.stackIDs[$0] }) == expectedIDs',self.source['aux'])

    def test_pop_reverse_notification_and_writer_bodies_unchanged(self):
        for signature in ['func reverseStack()','func captureIntoStack(id: UUID)','func showStack()']:
            self.assertEqual(body(self.source['ui'],signature),body(self.before('ui'),signature))
        for p,h in self.proof['supporting_sources'].items():self.assertEqual(h,self.base['production'][p])

    def test_only_reviewed_hunks_and_no_schema_or_package_change(self):
        self.assertEqual(len(CHANGES),22)
        for k in self.paths:self.assertEqual(pre_stack_native_inputs(self.source[k]),self.before(k))
        sha=lambda p:hashlib.sha256(pre_group_menu_input_bytes(ROOT/p)).hexdigest()
        self.assertEqual({p for p,h in self.base['production'].items()if sha(p)!=h},set(self.paths.values()))
        self.assertEqual({str(p.relative_to(ROOT))for p in (ROOT/'replica/Sources').rglob('*')if p.is_file()} - {NATIVE_TITLE_PATH, ITEM_OBSERVATION_PATH},set(self.base['production']))
        for p in ['replica/Package.swift','package.json']:self.assertEqual(sha(p),self.base['other'][p])

    def test_identity_only_checks_do_not_decode_native_stack_payloads(self):
        ui=self.source['ui']
        self.assertIn('var stackItemIDs: [UUID] { stackIDs.filter { hasStackItem($0) } }',ui)
        for signature in ['func hasStackItem(_ id: UUID)','func stackRestoreItem(for id: UUID)']:
            source=body(ui,signature)
            self.assertNotIn('resolvedItem()',source)
        consume=body(ui,'func consumeStackHead()')
        previous=body(self.before('ui'),'func consumeStackHead()')
        self.assertEqual(consume,previous.replace('state.stackItems.map(\\.id)','state.stackItemIDs',1))
        self.assertIn('max(1, state.stackItemIDs.count)',ui)
        self.assertIn('!ui.state.stackItemIDs.isEmpty',body(self.source['app'],'private func configureStackPasteShortcut()'))
        self.assertIn('max(1, state.stackItemIDs.count)',self.source['aux'])

    def test_legacy_queue_still_uses_id_writer_reload_and_deleted_check(self):
        source=(ROOT/'replica/Sources/PastoCore/Pasteboard.swift').read_text()
        self.assertIn('try reload()',source)
        self.assertIn('!$0.isDeleted',source)
        router=body(self.source['ui'],'func pasteStackItem(id: UUID')
        self.assertIn('return paste(ids: [id], plainTextOnly: plainTextOnly)',router)
        getter=body(self.source['ui'],'func stackRestoreItem(for id: UUID)')
        self.assertNotIn('ClipboardRestoreItem(item:',getter)

    def test_no_full_equivalence_or_completion_claim(self):
        self.assertFalse(self.proof['finite_difference_counter_changed'])
        self.assertFalse(self.proof['performance_measured'])
        self.assertTrue(any('Persisted UUID' in r for r in self.proof['remaining']))
        self.assertTrue(any('complete native entity/DI/ABI' in r for r in self.proof['remaining']))
        self.assertTrue(any('04430c' in r for r in self.proof['remaining']))
