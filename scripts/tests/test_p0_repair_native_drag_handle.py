"""Native drag optional input/group shape/current identifier; source and binary checks only."""
from pathlib import Path
import hashlib,json,re,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from native_capture_lookup_scope_contract import pre_native_capture_lookup
from test_offline_p0_contracts import body
from mixed_restore_scope_contract import pre_mixed_restore
from native_drag_handle_scope_contract import CHANGES,pre_native_drag_handle

class NativeDragHandleContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-120';cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.proof=json.loads((cls.phase/'native-drag-contract.json').read_text());cls.audit=json.loads((cls.phase/'p0-source-closure-audit.json').read_text());cls.src={Path(p).stem:pre_mixed_restore((ROOT/p).read_text())for p in cls.proof['current_sources']};cls.drag=body(cls.src['ReplicaNativeCardCollection'],'private func beginNativeDrag(');cls.group=body(cls.src['Pasteboard'],'private func nativeRestoreGroups(');cls.identifier=body(cls.src['ClipboardRestoreItem'],'var pasteboardIdentifier:');cls.ns={};exec((ROOT/cls.proof['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.ns)
    def order(self,s,tokens):
        cursor=0
        for t in tokens:cursor=s.index(t,cursor)+len(t)
    def test_twenty_original_drag_writer_processor_capture_selection_fragments_bound(self):
        self.assertEqual(len(self.proof['original_fragments']),20)
        for r in self.proof['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
    def test_binary_decoder_and_five_reused_proofs_model_resources_current(self):
        for r in [self.proof['binary'],self.proof['decoder']]:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
        self.assertEqual(len(self.proof['reused_evidence']),5)
        for p,h in self.proof['reused_evidence'].items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),h)
    def test_thirteen_actual_branch_targets_bound(self):
        self.assertEqual(len(self.proof['ARM_calls']),13)
        for r in self.proof['ARM_calls']:
            pc=int(r['address'],16);data=self.ns['read'](pc,4);w=int.from_bytes(data,'little');self.assertEqual(data.hex(),r['bytes']);self.assertEqual(w&0xfc000000,0x94000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(pc+d*4,int(r['target'],16))
    def test_sixteen_actual_input_group_entity_and_notification_sender_words_bound(self):
        self.assertEqual(len(self.proof['ARM_words']),16)
        for r in self.proof['ARM_words']:self.assertEqual(self.ns['read'](int(r['address'],16),4).hex(),r['bytes'])
    def test_processor_metadata_plus68_really_targets38222c(self):
        r=self.proof['processor_vtable'];self.assertEqual(self.ns['read'](int(r['accessor'],16),32).hex(),r['accessor_bytes']);a=int(r['materialization'],16);w=int.from_bytes(self.ns['read'](a,4),'little');v=int.from_bytes(self.ns['read'](a+4,4),'little');imm=((w>>5)&0x7ffff)*4+((w>>29)&3)
        if imm&0x100000:imm-=0x200000
        self.assertEqual((a&~4095)+(imm<<12)+((v>>10)&0xfff),int(r['metadata'],16));self.assertEqual(int(r['metadata'],16)+0x68,int(r['pointer'],16));p=int(r['pointer'],16);raw,c=self.ns['reachable_pointer'](p);self.assertEqual(c,r['chain']);self.assertEqual(self.ns['read'](p,8).hex(),r['pointer_bytes']);self.assertEqual(self.ns['base']+(raw&((1<<36)-1)),0x10038222c)
    def test_identifier_selector_and_writer_item_field_are_real(self):
        r=self.proof['identifier_selector'];a=int(r['pointer'],16);v,c=self.ns['reachable_pointer'](a);self.assertEqual(c,r['chain']);self.assertEqual(self.ns['read'](a,8).hex(),r['pointer_bytes']);t=self.ns['base']+(v&((1<<36)-1));o=self.ns['offset'](t);self.assertEqual(self.ns['raw'][o:self.ns['raw'].index(b'\0',o)].decode(),'identifier');r=self.proof['writer_item_ivar'];self.assertEqual(self.ns['read'](int(r['address'],16),8).hex(),r['bytes'])
    def test_special_type_literal_is_original_not_invented_UUID_marker(self):
        r=self.proof['item_id_literal'];self.assertEqual(self.ns['read'](int(r['ADRP_ADD'],16),12).hex(),r['instruction_bytes']);self.assertEqual(self.ns['read'](int(r['character_address'],16),25),b'com.wiheads.paste.item-id');s=(ROOT/'replica/Sources/PastoCore/OriginalNativeDragPasteboardWriter.swift').read_text();self.assertIn('"com.wiheads.paste.item-id"',s)
    def test_drag_resolves_optional_handles_and_matching_preview_indexes_from_applied_snapshot(self):
        self.order(self.drag,['guard let applied = appliedItems(for: state)','let positions =','let requestedIndexes = state.orderedSelectionIDs','var indexes: [Int] = []','requestedIndexes.compactMap','guard let input = applied[index].restoreItem() else { return nil }','indexes.append(index)','return input','dragPasteboardGroups(restoreItems: selected','selected.map { $0.makeDragIdentifierSource() }','zip(indexes, draggingWriters)'])
        for t in ['requiredRestoreItem','renderedItem(','resolvedItem(','state.visibleItems','state.selectedItems','.sorted','Set(']:self.assertNotIn(t,self.drag)
    def test_missing_provider_entry_is_skipped_without_preview_source_marker_shift(self):
        step=body(self.drag,'requestedIndexes.compactMap');self.order(step,['guard let input','return nil','indexes.append(index)','return input']);requested=[8,2,7];refs=['first',None,'last'];pairs=[(i,v)for i,v in zip(requested,refs)if v is not None];self.assertEqual([p[0]for p in pairs],[8,7]);self.assertEqual([p[1]for p in pairs],['first','last']);self.assertEqual(list(zip([p[0]for p in pairs],['writer-first','writer-last'])),[(8,'writer-first'),(7,'writer-last')])
    def test_grouped_native_processor_has_only_return_shape_changes_from_prior_flat_body(self):
        previous=body((self.phase/'before/replica/Sources/PastoCore/Pasteboard.swift').read_text(),'private func nativeRestoreObjects(');reconstructed=self.group.replace('if !multiple { return [items] }','if !multiple { return items }').replace('return groups\n','return groups.flatMap { $0 }\n');self.assertEqual(reconstructed,previous);self.assertEqual(hashlib.sha256(previous.encode()).hexdigest(),self.proof['group_equivalence']['previous_flat_body_sha256'])
    def test_copy_remains_flatten_wrapper_while_native_drag_returns_nested_groups(self):
        s=self.src['Pasteboard'];flat=body(s,'private func nativeRestoreObjects(');self.assertEqual(flat.strip(),'{\n        nativeRestoreGroups(inputs, options: options).flatMap { $0 }\n    }');drag=body(s,'public func dragPasteboardGroups(restoreItems selected:');self.assertIn('return nativeRestoreGroups(selected, options: options)',drag);self.assertNotIn('flatMap',drag);self.assertIn('if !multiple { return [items] }',self.group)
    def test_legacy_mixed_drag_fallback_and_old_for_label_are_retained(self):
        s=body(self.src['Pasteboard'],'public func dragPasteboardGroups(restoreItems selected:');self.order(s,['selected.allSatisfy({ $0.nativeObject != nil })','return try dragPasteboardGroups(for: selected.map { $0.resolvedItem() }, options: options)','return nativeRestoreGroups(selected, options: options)']);self.assertIn('public func dragPasteboardGroups(for selected: [ClipboardItem]',self.src['Pasteboard'])
        for t in ['writeToPasteboard','prepareHistoryRestore','recordRestored','reload(','save(']:self.assertNotIn(t,s)
    def test_local_marker_UUIDs_modifier_zip_and_writer_retention_remain(self):
        self.assertIn('ids: selected.map(\.id)',self.drag);self.assertIn('NSEvent.modifierFlags.isSuperset(of: plain)',self.drag);self.assertIn('writers(sources: sources, groups: groups)',self.drag);self.assertIn('zip(indexes, draggingWriters)',self.drag);s=(ROOT/'replica/Sources/PastoCore/OriginalNativeDragPasteboardWriter.swift').read_text();self.assertIn('private let source: any OriginalDragItemIdentifierSource',s);self.assertIn('return source.pasteboardIdentifier',s);self.assertIn('zip(sources, groups)',s)
    def test_identifier_factory_holds_native_object_context_and_legacy_UUID_only_as_fallback(self):
        s=self.src['ClipboardRestoreItem'];f=body(s,'public func makeDragIdentifierSource()');self.assertIn('ClipboardDragIdentifierSource(object: nativeObject, fallback: id.uuidString)',f);self.assertIn('private let object: PastoItemEntity?',s);self.assertIn('private let context: NSManagedObjectContext?',s);init=body(s,'init(object: PastoItemEntity?, fallback:');self.assertIn('context = object?.managedObjectContext',init);self.assertNotIn('value(forKey:',init)
    def test_identifier_requests_read_current_native_value_on_owning_queue_without_lookup_or_DTO(self):
        s=self.identifier;self.order(s,['guard let object else { return fallback }','let read = { (object.value(forKey: "nativeIdentifier") as? String) ?? fallback }','if let context { return context.performAndWait(read) }','return read()'])
        for t in ['resolvedItem','fetch','existingObject','UUID(','decode','save(','setValue','DispatchQueue','MainActor.assumeIsolated']:self.assertNotIn(t,s)
    def test_present_identifier_is_live_and_empty_string_is_not_replaced_with_UUID(self):
        key=re.search(r'object.value\(forKey: "([^"]+)"\)',self.identifier).group(1);self.assertEqual(key,'nativeIdentifier');self.assertIn('?? fallback',self.identifier);entity={key:'checksum-A'};fallback='local-UUID'
        def request():
            value=entity.get(key);return value if isinstance(value,str) else fallback
        self.assertEqual(request(),'checksum-A');entity[key]='checksum-B';self.assertEqual(request(),'checksum-B');entity[key]='';self.assertEqual(request(),'');entity[key]=None;self.assertEqual(request(),fallback)
        old=(self.phase/'before/replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift').read_text();self.assertIn('var pasteboardIdentifier: String { item.id.uuidString }',old);self.assertNotEqual('checksum-A',fallback)
    def test_old_private_UUID_snapshot_adapter_is_removed_from_production_drag(self):
        s=self.src['ReplicaNativeCardCollection'];self.assertNotIn('ReplicaNativeDragItemReference',s);self.assertIn('selected.map { $0.makeDragIdentifierSource() }',self.drag)
    def test_thirteen_shared_methods_and_six_sources_are_exact(self):
        self.assertEqual(len(self.proof['unchanged_methods']),13)
        for r in self.proof['unchanged_methods']:self.assertEqual(hashlib.sha256(body(pre_mixed_restore((ROOT/r['path']).read_text()),r['symbol']).encode()).hexdigest(),r['sha256'])
        for p,h in {**self.proof['current_sources'],**self.proof['shared_sources']}.items():self.assertEqual(hashlib.sha256(pre_native_capture_lookup((ROOT/p).read_text()).encode()).hexdigest(),h)
    def test_audit_separates_reusable_repairs_missing_source_and_runtime_only(self):
        self.assertEqual(self.audit['counts'],{'reusable_verified_finite':2,'confirmed_source_difference_repaired':2,'missing_source_evidence':5,'runtime_only_limitation':1});self.assertEqual(len(self.audit['rows']),10);self.assertTrue(self.audit['scope_is_partial']);self.assertFalse(self.audit['full_P0_completion']);self.assertIsNone(self.audit['full_priority_completion_percent'])
        for p,h in self.audit['source_inputs'].items():self.assertEqual(hashlib.sha256(pre_native_capture_lookup((ROOT/p).read_text()).encode()).hexdigest(),h)
        for r in self.audit['rows']:
            self.assertEqual(r['priority'],'P0')
            for m in r['current_methods']:self.assertEqual(hashlib.sha256(body(pre_native_capture_lookup((ROOT/m['path']).read_text()),m['symbol']).encode()).hexdigest(),m['sha256'])
    def test_old_feedback_label_is_withdrawn_and_real_selection_handoff_remains_pending(self):
        row=next(r for r in self.audit['rows']if r['id']=='selection.identifier_publication_service');self.assertEqual(row['status'],'missing_source_evidence');self.assertIn('Paste:0x1000679ac',row['original_function_ids']);self.assertIn('Paste:0x1000f2b18',row['original_function_ids']);self.assertIn(('0x1000679ac','0x1000f2b18'),[(r['function'],r['target'])for r in self.proof['ARM_calls']])
    def test_audit_storage_gap_is_concrete_and_does_not_remove_compatibility_blob(self):
        schema=json.loads((ROOT/'.local/p0-repair/phase-12/model-offline-schema.json').read_text());self.assertNotIn('content',schema['ItemEntity']);p=ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift';s=body(p.read_text(),'nonisolated static func item(');self.assertIn('var item = try Self.decode(ClipboardItem.self, object)',s);self.assertEqual(next(r for r in self.audit['rows']if r['id']=='storage.compatibility_decode_gate')['status'],'missing_source_evidence')
    def test_eight_hunks_reverse_all247_production_files_without_erasing_user_changes(self):
        self.assertEqual(len(CHANGES),8)
        for p,h in self.base['production'].items():
            data=(ROOT/p).read_bytes();data=pre_native_drag_handle(data.decode()).encode()if p.endswith('.swift')else data;self.assertEqual(hashlib.sha256(data).hexdigest(),h)
    def test_new_identifier_contract_is_bounded_no_full_nil_runtime_or_P0_completion_claim(self):
        self.assertEqual(self.proof['new_difference_records'],1);self.assertEqual(self.proof['new_conservative_groups'],1);self.assertFalse(self.proof['full_function_migration_verified']);self.assertFalse(self.proof['runtime_executed']);self.assertEqual(len(self.proof['remaining']),4)
        for p in self.proof['current_sources']:
            old=(self.phase/'before'/p).read_text();self.assertEqual(pre_native_drag_handle((ROOT/p).read_text()),old);self.assertEqual(pre_native_drag_handle(old),old)

if __name__=='__main__':unittest.main()
