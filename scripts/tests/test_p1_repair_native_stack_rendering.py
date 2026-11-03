from native_restore_writer_scope_contract import pre_native_restore_writer
"""Stack row-demand native input/metadata contracts; source and ARM only."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from stack_table_drag_scope_contract import pre_stack_table_drag
from native_stack_rendering_scope_contract import CHANGES,pre_native_stack_rendering

class NativeStackRenderingContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-114';cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.proof=json.loads((cls.phase/'native-stack-rendering-contract.json').read_text());cls.src={Path(p).stem:pre_native_restore_writer((ROOT/p).read_text())for p in cls.proof['current_sources']};cls.ns={};exec((ROOT/cls.proof['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.ns)
    def order(self,s,tokens):
        cursor=0
        for t in tokens:cursor=s.index(t,cursor)+len(t)
    def test_ten_original_fragments_and_reused_proofs_current(self):
        self.assertEqual(len(self.proof['original_fragments']),10)
        for r in self.proof['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for r in [self.proof['binary'],self.proof['decoder']]+self.proof['reused_evidence']:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_thirteen_actual_row_cell_and_metadata_calls_bound(self):
        self.assertEqual(len(self.proof['ARM_calls']),13)
        for r in self.proof['ARM_calls']:
            pc=int(r['address'],16);data=self.ns['read'](pc,4);self.assertEqual(data.hex(),r['bytes']);w=int.from_bytes(data,'little');self.assertEqual(w&0x7c000000,0x14000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(pc+d*4,int(r['target'],16))
    def test_same_original_entity_array_slot_is_forwarded_to_cell(self):
        self.assertEqual(len(self.proof['ARM_words']),5)
        for r in self.proof['ARM_words']:self.assertEqual(self.ns['read'](int(r['address'],16),4).hex(),r['bytes'])
        self.assertIn(('0x100086658','0x1000519f8'),[(r['function'],r['target'])for r in self.proof['ARM_calls']])
    def test_five_real_table_outlet_and_preview_selectors_bound(self):
        self.assertEqual({r['selector']for r in self.proof['selectors']},{'makeViewWithIdentifier:owner:','setImage:','setMaximumNumberOfLines:','setStringValue:','rawPreview'})
        for r in self.proof['selectors']:
            a=int(r['pointer'],16);v,c=self.ns['reachable_pointer'](a);self.assertEqual(c,r['chain']);self.assertEqual(self.ns['read'](a,8).hex(),r['pointer_bytes']);t=self.ns['base']+(v&((1<<36)-1));o=self.ns['offset'](t);self.assertEqual(self.ns['raw'][o:self.ns['raw'].index(b'\0',o)].decode(),r['selector'])
    def test_table_stores_strong_ordered_native_handles_and_retains_legacy_API(self):
        s=self.src['OriginalStackTableController'];self.assertIn('private var snippetInputs: [ClipboardRestoreItem] = []',s);self.assertIn('public var snippets: [ClipboardItem]',s);self.assertIn('get { snippetInputs.map { $0.resolvedItem() } }',s);self.assertIn('set { snippetInputs = newValue.map { ClipboardRestoreItem(item: $0) } }',s);self.assertIn('public var makeCell: ((ClipboardItem, Int) -> NSView)?',s);self.assertIn('public var makeNativeCell: ((ClipboardRestoreItem, Int) -> NSView)?',s)
    def test_row_request_passes_current_handle_before_any_value_adapter(self):
        s=body(self.src['OriginalStackTableController'],'public func tableView(_ tableView: NSTableView, viewFor');self.order(s,['guard snippetInputs.indices.contains(row)','let input = snippetInputs[row]','if let makeNativeCell { return makeNativeCell(input, row) }','return makeCell?(input.resolvedItem(), row)'])
        for t in ['store.','UUID(','Set(','sorted','filter']:self.assertNotIn(t,s)
    def test_count_height_and_ID_access_never_decode_values(self):
        s=self.src['OriginalStackTableController'];self.assertIn('public var snippetIDs: [UUID] { snippetInputs.map(\\.id) }',s)
        for marker in ['public func f_100085230()','public func f_100083a20()','public func removeRow(']:
            v=body(s,marker);self.assertNotIn('resolvedItem',v);self.assertNotIn('snippets.',v)
        self.assertIn('min(10, max(1, snippetInputs.count))',body(s,'public func f_100083a20()'))
    def test_native_identity_compare_does_not_materialize_payload(self):
        s=body(self.src['OriginalStackTableController'],'private func sameInputs(');self.order(s,['guard lhs.count == rhs.count','zip(lhs, rhs).allSatisfy','if pair.0.hasNativeEntity || pair.1.hasNativeEntity','return pair.0.hasSameEntity(as: pair.1)','return pair.0.resolvedItem() == pair.1.resolvedItem()']);self.assertNotIn('Set(',s)
    def test_legacy_update_insert_and_head_methods_delegate_without_API_removal(self):
        s=self.src['OriginalStackTableController']
        for marker,target in [('public func updateSnippets(','updateNativeSnippets'),('public func didInsertSnippet(','didInsertNativeSnippet'),('public func didConsumeHead(','didConsumeNativeHead')]:
            v=body(s,marker);self.assertIn(target,v);self.assertIn('ClipboardRestoreItem(item: $0)',v)
    def test_native_updates_and_animations_keep_sequence_and_event_order(self):
        s=self.src['OriginalStackTableController'];v=body(s,'public func updateNativeSnippets(');self.order(v,['let preserveRemoval','animatedInputsAwaitingRefresh = nil','snippetInputs = values','tableView.reloadData()','f_100083a20()']);v=body(s,'public func didInsertNativeSnippet(');self.order(v,['guard updated.count','var priorIDs = updated.map','priorIDs.remove(at: index)','guard priorIDs == previousIDs','if snippetIDs == previousIDs','snippetInputs = updated','animatedInputsAwaitingRefresh = updated','context.duration = 0.15','f_100083a20()','tableView.insertRows']);v=body(s,'public func didConsumeNativeHead(');self.order(v,['Array(previousIDs.dropFirst()) == remaining.map','snippetInputs = remaining','animatedInputsAwaitingRefresh = remaining','context.duration = 0.15','tableView.animator().removeRows','tableView.scrollRowToVisible(0)','f_100083a20()'])
    def test_state_builds_inputs_in_queue_order_with_native_before_legacy(self):
        s=body(self.src['ReplicaUIController'],'var stackSnippetInputs:');self.order(s,['stackIDs.compactMap','if let input = stackRestoreInputs[id] { return input }','store.items.first','ClipboardRestoreItem(item: $0)'])
        for t in ['resolvedItem','Set(','unique','sorted','dictionary']:self.assertNotIn(t,s)
    def test_native_capture_and_selected_producers_enqueue_same_input_without_DTO(self):
        for marker in ['private func captureLatestItemIntoStack()','func addSelectionToStack()']:
            s=body(self.src['ReplicaUIController'],marker);self.assertIn('state.addToStack(input)',s);self.assertNotIn('resolvedItem()',s)
    def test_enqueue_preserves_previous_ID_snapshot_then_stores_input_and_notifies(self):
        s=body(self.src['ReplicaUIController'],'private func insertStackItem(');self.order(s,['let previousIDs = stackItemIDs','if let input { stackRestoreInputs[id] = input }','let append = store.preferences.stackReversed','let insertionIndex','stackIDs.insert(id','didInsertNativeSnippet','updated: stackSnippetInputs']);self.assertNotIn('resolvedItem',s)
    def test_reverse_and_consume_use_native_arrays(self):
        s=body(self.src['ReplicaUIController'],'func reverseStack()');self.assertIn('updateNativeSnippets(stackSnippetInputs)',s);s=body(self.src['ReplicaUIController'],'func consumeStackHead()');self.assertIn('didConsumeNativeHead(previousIDs: previousIDs, remaining: state.stackSnippetInputs)',s);self.assertNotIn('state.stackItems',s)
    def test_production_table_uses_native_callback_and_native_ID_snapshot(self):
        source=self.src['AuxiliaryViews'];a=source.index('struct ReplicaStackTable:');b=source.index('struct ReplicaSettingsView:',a);s=source[a:b];self.assertIn('controller.makeNativeCell =',s);self.assertIn('controller?.snippetIDs ?? []',s);self.assertIn('controller.updateNativeSnippets(state.stackSnippetInputs)',s);self.assertNotIn('controller.makeCell =',s);self.assertNotIn('state.stackItems',s)
    def test_native_icon_branch_reads_current_type_without_store_lookup(self):
        s=body(self.src['AuxiliaryViews'],'if let rawType = current.previewRawType()');self.assertIn('OriginalPasteboardContentKind(rawValue: UInt8(rawType))',s);self.assertNotIn('store.',s);self.assertNotIn('resolvedItem',s)
    def test_cell_keeps_native_input_and_outlet_update_order(self):
        s=self.src['OriginalStackSnippetCell'];self.assertIn('let input: ClipboardRestoreItem',s);v=body(s,'func updateNativeSnippet(');self.order(v,['if let imageView { imageView.image = nativeImageProvider(input) }','textField?.maximumNumberOfLines = 2','OriginalStackSnippetText.text(for: input)']);self.assertNotIn('resolvedItem',v);self.assertIn('view.updateNativeSnippet(input)',s)
    def test_native_metadata_getter_reads_only_current_rawPreview(self):
        s=body(self.src['ClipboardRestoreItem'],'public func previewMetadataData()');self.assertIn('nativeObject?.value(forKey: "rawPreview") as? Data',s)
        for t in ['decode','resolve','store','payload','identifier','UUID']:self.assertNotIn(t,s)
    def test_native_text_reads_preview_now_and_file_title_lazily(self):
        s=body(self.src['OriginalStackSnippetText'],'static func text(for input:');self.order(s,['guard input.hasNativeEntity','return f_100051ec8(input.resolvedItem())','return label(rawPreview: input.previewMetadataData())','input.previewTitle()!.title']);self.assertEqual(s.count('resolvedItem'),1);self.assertIn('return filesTitle(metadata.paths.count)',body(self.src['OriginalStackSnippetText'],'private static func label('))
    def test_label_format_branches_are_exact_legacy_reuse(self):
        s=body(self.src['OriginalStackSnippetText'],'private static func label(').replace('rawPreview','item.rawPreview').replace('return filesTitle(metadata.paths.count)','return OriginalPreviewTitles.f_100308f88(item.originalTitle,\n                    defaultTitle: defaultTitle(item, fileCount: metadata.paths.count))');p='replica/Sources/Pasto/UI/OriginalStackSnippetText.swift';self.assertEqual(s,body((self.phase/'before'/p).read_text(),'static func f_100051ec8('));self.assertEqual(hashlib.sha256(s.encode()).hexdigest(),self.proof['format_equivalence']['before_sha256'])
    def test_original_replica_layout_and_twelve_existing_methods_unchanged(self):
        self.assertEqual(len(self.proof['unchanged_methods']),12)
        for r in self.proof['unchanged_methods']:self.assertEqual(hashlib.sha256(body(pre_stack_table_drag((ROOT/r['path']).read_text()),r['symbol']).encode()).hexdigest(),r['sha256'])
        s=body(self.src['OriginalStackSnippetCell'],'\n    init(nativeImageProvider:');s=s[s.index('super.init(frame: .zero)'):];self.assertEqual(hashlib.sha256(s.encode()).hexdigest(),self.proof['layout_equivalence']['sha256'])
    def test_shared_sources_legacy_Swift_clients_and_twenty_six_hunks_bound(self):
        self.assertEqual(len(CHANGES),26)
        for p,h in {**self.proof['shared_sources'],**self.proof['legacy_test_sources']}.items():self.assertEqual(hashlib.sha256(pre_native_restore_writer((ROOT/p).read_text()).encode()).hexdigest(),h)
        for p,h in self.base['production'].items():
            data=(ROOT/p).read_bytes();data=pre_native_stack_rendering(data.decode()).encode()if p.endswith('.swift')else data;self.assertEqual(hashlib.sha256(data).hexdigest(),h)
        for p,h in self.proof['current_sources'].items():self.assertEqual(hashlib.sha256(pre_native_restore_writer((ROOT/p).read_text()).encode()).hexdigest(),h)
    def test_reversal_is_idempotent_and_native_queue_not_automatically_cleared(self):
        for p in self.proof['current_sources']:
            before=(self.phase/'before'/p).read_text();self.assertEqual(pre_native_stack_rendering((ROOT/p).read_text()),before);self.assertEqual(pre_native_stack_rendering(before),before)
        self.assertIn('do not infer automatic queue clearing',self.proof['remaining'][0])
    def test_only_valid_row_contracts_count_and_full_lifetime_stays_open(self):
        self.assertFalse(self.proof['full_function_migration_verified']);self.assertFalse(self.proof['runtime_executed']);self.assertEqual(self.proof['new_difference_records'],2);self.assertEqual(self.proof['new_conservative_groups'],1);self.assertEqual(len(self.proof['remaining']),4);self.assertIn('ID-only captureIntoStack remains unbound',self.proof['remaining'][1]);self.assertIn('Original Nib makeView reuse',self.proof['remaining'][2])

if __name__=='__main__':unittest.main()
