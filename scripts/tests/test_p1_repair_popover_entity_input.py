"""Ordinary preview/detach captured entity: source and immutable ARM checks only."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2]
from text_preview_creation_scope_contract import pre_text_preview_creation
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment
from popover_entity_input_scope_contract import CHANGES,pre_popover_entity_input
from preview_index_retry_scope_contract import pre_preview_index_retry,pre_preview_index_retry_bytes

class PopoverEntityInputContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-95';cls.proof=json.loads((cls.phase/'popover-entity-input-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text())
        cls.paths=dict(ui='replica/Sources/Pasto/UI/ReplicaUIController.swift',popover='replica/Sources/PastoCore/OriginalPreviewPopover.swift',panel='replica/Sources/Pasto/UI/PanelViews.swift',stack='replica/Sources/Pasto/UI/AuxiliaryViews.swift')
        cls.src={k:pre_preview_index_retry((ROOT/p).read_text())for k,p in cls.paths.items()}
        ns={};exec((ROOT/cls.proof['decoder']['path']).read_text().split("idx={r['address']",1)[0],ns);cls.ns=ns
    def original(self,a):
        r=next(r for r in self.proof['original_fragments']if r['address']==a);return original_fragment((ROOT/r['path']).read_text(),a[2:])
    def order(self,s,tokens):
        pos=[s.index(t)for t in tokens];self.assertEqual(pos,sorted(pos))

    def test_original_fragments_machine_image_and_prior_header_proof_are_bound(self):
        self.assertEqual(len(self.proof['original_fragments']),11)
        for r in self.proof['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for r in [self.proof['binary'],self.proof['decoder']]+self.proof['reused_evidence']:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])

    def test_twelve_actual_machine_calls_bind_selection_show_and_same_entity_detach(self):
        self.assertEqual(len(self.proof['ARM_calls']),12)
        for r in self.proof['ARM_calls']:
            pc=int(r['address'],16);b=self.ns['read'](pc,4);self.assertEqual(b.hex(),r['bytes']);w=int.from_bytes(b,'little');self.assertEqual(w&0x7c000000,0x14000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(pc+4*d,int(r['target'],16))

    def test_real_popover_item_field_receives_input_and_detach_reads_same_offset(self):
        words={r['address']:r['bytes']for r in self.proof['ARM_words']}
        for a,b in words.items():self.assertEqual(self.ns['read'](int(a,16),4).hex(),b)
        self.assertEqual(words['0x100029670'],'f60300aa');self.assertEqual(words['0x100029680'],'966a28f8');self.assertEqual(words['0x100029aa8'],'956a68f8')
        field=self.proof['item_ivar'];self.assertEqual(self.ns['read'](int(field['address'],16),8).hex(),field['bytes']);self.assertEqual(int.from_bytes(bytes.fromhex(field['bytes']),'little'),field['offset']);self.assertEqual(field['offset'],0x48)
        self.assertEqual(words['0x100029678'],words['0x100029aa4'])

    def test_original_factory_stores_and_passes_same_entity_without_identifier_fetch(self):
        show=self.original('0x10002964c');self.order(show,['PreviewPopover::item) = param_5','FUN_10008747c()','FUN_1003c25dc(param_5','FUN_10007c994()'])
        detach=self.original('0x100029a80');self.order(detach,['PreviewPopover::item)','if (lVar7 == 0)','FUN_1003c25dc(lVar7','FUN_10007c994()','FUN_100086c10(IVar2,lVar7'])
        for s in [show,detach]:
            for token in ['identifier','fetch','UUID','cache']:self.assertNotIn(token,s)

    def test_space_passes_last_applied_entity_while_legacy_preview_has_explicit_fallback(self):
        key=body(self.src['ui'],'private func handleKey(');s=body(key,'if event.keyCode == 49, !isEditing')
        self.assertIn('if let input = appliedRestoreItems().last { showPreview(item: input.resolvedItem(), input: input) }',s)
        for token in ['store.items','appliedSelectionItems','DispatchQueue','Task']:self.assertNotIn(token,s)
        show=body(self.src['ui'],'func showPreview(item: ClipboardItem, input:')
        self.order(show,['previewRegistry.f_10008747c','let input = input ?? appliedRestoreItems(orderedIDs: [item.id]).first','?? state.stackRestoreItem(for: item.id) ?? ClipboardRestoreItem(item: item)','let anchor: NSView?','if popover.isDisplayed','popover.close()','popover.show('])

    def test_card_and_Stack_context_actions_supply_current_captured_handle(self):
        self.assertIn('Button("预览") { state.controller?.showPreview(item: item, input: titleInput) }',self.src['panel'])
        self.assertIn('Button("预览") { state.controller?.showPreview(item: item, input: state.stackRestoreItem(for: item.id)) }',self.src['stack'])
        self.assertEqual(self.src['panel'].count('showPreview('),1);self.assertEqual(self.src['stack'].count('showPreview('),1)

    def test_selection_completion_optionally_resolves_entity_before_anchor_and_beeps_on_failure(self):
        s=body(self.src['ui'],'private func selectionDidReveal(')
        self.order(s,['collection.appliedItems(for: state)','items.indices.contains(requestedIndex)','let input = items[requestedIndex].restoreItem()','collection.visibleSelectionAnchor(at: requestedIndex','NSSound.beep()','let item = items[requestedIndex]','input: input','makePreviewContent(for: input)'])
        self.assertNotIn('makePreviewContent(for: item)',s)
        original=self.original('0x100075e3c');self.order(original,['FUN_1001b9698(','CollectionView::visibleCells','FUN_10002964c('])

    def test_content_factory_type_and_all_production_calls_agree_on_entity_handle(self):
        factory=body(self.src['ui'],'private func makePreviewContent(for input: ClipboardRestoreItem)')
        self.assertIn('makeOriginalReplicaPreview(state: state, item: input.resolvedItem(), input: input)',factory)
        self.assertEqual(self.src['ui'].count('makePreviewContent(for: input)'),3)
        self.assertNotIn('makePreviewContent(for: item)',self.src['ui'])
        self.assertEqual(self.src['ui'].count('itemIdentifier: item.id.uuidString, input: input,'),2)

    def test_popover_retains_entity_before_close_of_existing_preview_and_does_not_clear_on_close(self):
        self.assertIn('private var item: ClipboardRestoreItem?',self.src['popover'])
        s=body(self.src['popover'],'public func show(itemIdentity:')
        self.order(s,['self.itemIdentifier = itemIdentifier','item = input','registry.f_10008747c(itemIdentity: itemIdentity)?.close()','preview.onBeginEditing','contentViewController = controller','show(relativeTo:'])
        self.assertNotIn('weak var item',self.src['popover']);self.assertNotIn('item = nil',body(self.src['popover'],'public func f_100029da8()'))

    def test_detach_factory_takes_stored_handle_without_cache_relookup(self):
        self.assertIn('public var makeContentView: ((_ input: ClipboardRestoreItem) -> OriginalItemPreviewView?)?',self.src['popover'])
        s=body(self.src['popover'],'public func f_100029a80(')
        self.order(s,['guard let itemIdentity, let itemIdentifier, let item','let window = OriginalPreviewWindow()','makeContentView?(item)','preview.onEndEditing','if beginEditing','manager.f_100086c10('])
        factory=body(self.src['ui'],'private func makePreviewPopover()')
        self.assertIn('popover.makeContentView = { [weak self] input in',factory);self.assertIn('makeOriginalReplicaPreview(state: self.state, item: input.resolvedItem(), input: input)',factory)
        for token in ['store.items','uuidString == identifier','appliedRestoreItems','itemIdentity, itemIdentifier']:self.assertNotIn(token,s+factory)

    def test_lifecycle_callbacks_window_registry_and_editing_entry_are_unchanged(self):
        self.assertEqual(len(self.proof['unchanged_methods']),7)
        for r in self.proof['unchanged_methods']:
            now=body(pre_text_preview_creation((ROOT/r['path']).read_text()),r['symbol']);self.assertEqual(hashlib.sha256(now.encode()).hexdigest(),r['sha256']);self.assertEqual(now,body((self.phase/'before'/r['path']).read_text(),r['symbol']))

    def test_fifteen_reviewed_hunks_four_files_no_shared_writer_or_version_edits(self):
        self.assertEqual(len(CHANGES),15);sha=lambda p:hashlib.sha256(pre_preview_index_retry_bytes(ROOT/p)).hexdigest()
        files={str(p.relative_to(ROOT))for p in(ROOT/'replica/Sources').rglob('*')if p.is_file()};self.assertEqual(files,set(self.base['production']));self.assertEqual({p for p,h in self.base['production'].items()if sha(p)!=h},set(self.paths.values()))
        for key,p in self.paths.items():self.assertEqual(pre_popover_entity_input(self.src[key]),(self.phase/'before'/p).read_text())
        for group in ['current_sources','shared_sources']:
            for p,h in self.proof[group].items():self.assertEqual(sha(p),h)
        for p,h in self.proof['shared_sources'].items():self.assertEqual(h,self.base['production'][p])
        for p in ['replica/Package.swift','package.json']:self.assertEqual(sha(p),self.base['other'][p])

    def test_original_missing_anchor_retry_is_not_mistaken_for_closed_presenting_contract(self):
        self.assertIn('FUN_10022c9c4(param_1,1,FUN_100076544',self.original('0x10006bb3c'))
        self.assertFalse(self.proof['full_function_migration_verified']);self.assertFalse(self.proof['runtime_executed']);self.assertEqual(self.proof['new_difference_records'],0)
        for token in ['asynchronous index-retry','registry identity','legacy DTO','3544dc']:self.assertTrue(any(token in r for r in self.proof['remaining']),token)
