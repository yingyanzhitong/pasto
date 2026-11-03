"""Captured native entity through editing routes; source/static checks, no UI execution."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment
from edit_entity_input_scope_contract import CHANGES,pre_edit_entity_input
from native_edit_write_scope_contract import pre_native_edit_write,pre_native_edit_write_bytes

class EditEntityInputContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-90';cls.proof=json.loads((cls.phase/'edit-entity-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text())
        cls.paths=dict(handle='replica/Sources/PastoCore/ClipboardRestoreItem.swift',ui='replica/Sources/Pasto/UI/ReplicaUIController.swift',adapter='replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift')
        cls.src={k:pre_native_edit_write((ROOT/p).read_text())for k,p in cls.paths.items()}
        ns={};exec((ROOT/cls.proof['decoder']['path']).read_text().split("idx={r['address']",1)[0],ns);cls.ns=ns
    def original(self,a):
        r=next(r for r in self.proof['original_fragments']if r['address']==a);return original_fragment((ROOT/r['path']).read_text(),a[2:])
    def before(self,key):return(self.phase/'before'/self.paths[key]).read_text()
    def order(self,s,tokens):
        positions=[s.index(t)for t in tokens];self.assertEqual(positions,sorted(positions))

    def test_ten_original_fragments_prior_router_and_observer_evidence_bound(self):
        self.assertEqual(len(self.proof['original_fragments']),10)
        for r in self.proof['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for r in [self.proof['binary'],self.proof['decoder'],self.proof['router_disassembly']]+self.proof['reused_evidence']:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])

    def test_eleven_direct_calls_and_one_actual_router_indirect_word_bound(self):
        self.assertEqual(len(self.proof['ARM_calls']),11)
        for r in self.proof['ARM_calls']:
            pc=int(r['address'],16);b=self.ns['read'](pc,4);self.assertEqual(b.hex(),r['bytes']);w=int.from_bytes(b,'little');self.assertEqual(w&0x7c000000,0x14000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(pc+d*4,int(r['target'],16))
        words=self.proof['router_indirect_words'];self.assertEqual(len(words),1)
        for r in words:
            b=self.ns['read'](int(r['address'],16),4);self.assertEqual(b.hex(),r['bytes']);self.assertEqual(int.from_bytes(b,'little')&0xfffffc1f,0xd63f0000)

    def test_original_filters_complete_input_and_forwards_same_element_to_router(self):
        s=self.original('0x1000655cc');self.order(s,['FUN_10031c2ec()','__appendElementAssumeUniqueAndCapacity(CVar8.unknown,uVar6)','if (lVar13 == 0)','NSSound::beep()','FUN_1003bb280(uVar6)'])
        self.assertIn('FUN_1003bb290(param_1,1)',self.original('0x1003bb280'))
        self.assertIn('(*pcVar6)(param_1,uVar5,param_2',self.original('0x1003bb290'))
        self.assertIn('FUN_1003c25dc(param_1,param_2',self.original('0x100003da0'))

    def test_original_observer_is_built_from_the_captured_entity_without_fetch(self):
        s=self.original('0x1003c1c84');self.order(s,['*(ID *)(unaff_x20 + 0x10) = param_1','objc_stub::managedObjectContext(param_1)','objc_stub::objectID(param_1)'])
        self.assertIn('FUN_1003c1c60(param_1',self.original('0x1003c25dc'))
        self.assertIn('*(undefined8 *)(unaff_x20 + 0x38) = param_1',self.original('0x1003c0390'))
        for token in ['fetch','existingObject','identifier']:self.assertNotIn(token,s)

    def test_native_handle_observer_factory_captures_the_same_object(self):
        native=body(self.src['handle'],'init(id: UUID, object: PastoItemEntity)')
        self.assertIn('private let makeObservation: () -> ClipboardItemObservation?',self.src['handle'])
        self.assertIn('makeObservation = { ClipboardItemObservation(object: object) }',native)
        self.assertIn('ClipboardPersistence.item(object)',native)
        self.assertEqual(body(self.src['handle'],'public func observeItem()'),'{ makeObservation() }')
        for token in ['UUID()','fetch(','existingObject(','store.','context.perform','Task','self.']:self.assertNotIn(token,body(native,'makeObservation ='))

    def test_legacy_handle_explicitly_returns_no_native_observer(self):
        legacy=body(self.src['handle'],'public init(item: ClipboardItem)')
        self.assertIn('resolve = { item }',legacy);self.assertIn('makeObservation = { nil }',legacy)
        self.assertNotIn('observeItem(id:',legacy);self.assertNotIn('ClipboardItemObservation(object:',legacy)

    def test_restore_content_resolver_and_existing_reference_lookup_are_preserved(self):
        before=self.before('handle')
        self.assertEqual(body(self.src['handle'],'public func resolvedItem()'),body(before,'public func resolvedItem()'))
        self.assertEqual(body(body(self.src['handle'],'init(id: UUID, object: PastoItemEntity)'),'resolve = {'),body(body(before,'init(id: UUID, object: PastoItemEntity)'),'resolve = {'))
        for marker in ['private func appliedRestoreItems(','private func appliedSelectionItems()','func contextMenuRestoreItems()','func paste(itemID:']:self.assertEqual(body(self.src['ui'],marker),body(self.before('ui'),marker))

    def test_real_command_e_uses_applied_handles_after_existing_owner_and_modifier_gates(self):
        s=body(self.src['ui'],'private func handleKey(_ event: NSEvent) -> Bool')
        signature='if !isEditing, signature.keyCode == OriginalShortcutFunctions.f_1001e94d4("e"),\n           signature.modifierRawValue == NSEvent.ModifierFlags.command.rawValue'
        b=body(s,signature);self.assertIn('editItems(appliedRestoreItems())',b);self.assertIn('return true',b);self.assertLess(s.index('if !ownsCollectionFocus'),s.index(signature))
        self.assertNotIn('appliedSelectionItems()',b)

    def test_filter_keeps_handle_array_order_and_finishes_before_any_window(self):
        s=body(self.src['ui'],'private func editItems(_ items: [ClipboardRestoreItem])')
        self.order(s,['let editable = items.filter { Self.allowsContentEditing($0.resolvedItem()) }','guard !editable.isEmpty else { NSSound.beep(); return }','for input in editable { presentEditingPreview(input: input) }'])
        for token in ['Set(','compactMap','state.selectedItems','store.items','UUID','lazy.']:self.assertNotIn(token,s)

    def test_writing_tools_retains_handle_after_text_only_filter_and_reuses_existing_routing(self):
        s=body(self.src['ui'],'private func writeAppliedSelection()')
        self.order(s,['guard OriginalWritingTools.isAvailable()','let items = appliedRestoreItems().filter','let item = $0.resolvedItem()','Self.allowsContentEditing(item) && (item.kind == .text || item.kind == .richText)','guard !items.isEmpty else { return false }','editItems(items)','OriginalWritingTools.showAfterDelay()'])
        self.assertNotIn('appliedSelectionItems()',s);self.assertNotIn('NSSound.beep',s)
        self.assertEqual(body(self.src['ui'],'private static func allowsContentEditing('),body(self.before('ui'),'private static func allowsContentEditing('))

    def test_router_keeps_registry_transition_and_edit_presentation_order(self):
        s=body(self.src['ui'],'private func presentEditingPreview(input: ClipboardRestoreItem)')
        self.order(s,['let item = input.resolvedItem()','let window = OriginalPreviewWindow()','window.animationBehavior = .documentWindow','registry.f_100086c10(','let transition = OriginalPreviewWindowTransition(window: window)','makeOriginalReplicaPreview(state: state, item: item, input: input)','preview.f_10007be8c()','controller.view = preview','transition.present(controller)','focusPreviewEditing()'])
        for token in ['preview.onEndEditing = { window.close() }','registry.f_10008727c(isEditing: editing, itemIdentifier: itemIdentifier)','editorWindowTransitions.removeValue(forKey: windowIdentity)']:self.assertIn(token,s)
        for token in ['hidePanel(','appliedRestoreItems(','store.observeItem','fetch(']:self.assertNotIn(token,s)

    def test_factories_forward_optional_handle_and_explicit_input_cannot_fall_through_uuid_lookup(self):
        s=self.src['adapter'];self.assertIn('if let textPreview = makeOriginalReplicaTextPreview(state: state, item: item, input: input)',s)
        self.assertIn('let content = ReplicaInlineTextPreviewContent(state: state, item: item, input: input)',s)
        init=body(s,'init(state: ReplicaUIState, item: ClipboardItem, input: ClipboardRestoreItem?)')
        self.order(init,['let nativeSource: ClipboardItemObservation?','if let input { nativeSource = input.observeItem() }','else { nativeSource = state.store.observeItem(id: item.id) }','nativeItemObservation = nativeSource'])
        self.assertNotIn('input?.observeItem() ??',init)
        self.assertEqual(s.count('input: ClipboardRestoreItem? = nil'),2)

    def test_observer_baseline_delivery_and_commit_paths_are_unchanged(self):
        for marker in ['private func reloadStoredContent()','private func receiveStoredModel(','private func replaceStoredModel(','func commitPreviewEditing()','private func displayStoredModel()']:self.assertEqual(body(self.src['adapter'],marker),body(self.before('adapter'),marker))
        self.assertIn('nativeSource.onChange = { [weak self] current in',self.src['adapter'])
        self.assertIn('itemObservation = state.store.$items.sink',self.src['adapter'])

    def test_fourteen_exact_hunks_only_three_files_and_244_others_unchanged(self):
        self.assertEqual(len(CHANGES),14);sha=lambda p:hashlib.sha256(pre_native_edit_write_bytes(ROOT/p)).hexdigest()
        current={str(p.relative_to(ROOT))for p in(ROOT/'replica/Sources').rglob('*')if p.is_file()}
        self.assertEqual(current,set(self.base['production']));self.assertEqual({p for p,h in self.base['production'].items()if sha(p)!=h},set(self.paths.values()))
        for key in self.paths:self.assertEqual(pre_edit_entity_input(self.src[key]),self.before(key))
        for group in ['current_sources','shared_sources']:
            for p,h in self.proof[group].items():self.assertEqual(sha(p),h)
        for p,h in self.proof['shared_sources'].items():self.assertEqual(h,self.base['production'][p])
        for p in ['replica/Package.swift','package.json']:self.assertEqual(sha(p),self.base['other'][p])

    def test_remaining_nontext_observation_ordinary_uuid_fallback_and_write_DI_are_explicit(self):
        self.assertFalse(self.proof['runtime_executed']);self.assertFalse(self.proof['full_function_migration_verified']);self.assertEqual(self.proof['new_difference_records'],0)
        for token in ['Ordinary/popover','other content kinds','performance claim','Store.$items','3544dc']:self.assertTrue(any(token in row for row in self.proof['remaining']),token)
