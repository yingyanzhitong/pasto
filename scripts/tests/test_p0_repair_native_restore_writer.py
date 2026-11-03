from shared_pasteboard_state_scope_contract import pre_shared_pasteboard_state
from native_restore_only_scope_contract import pre_native_restore_only
"""Native restore data/source/target flow; source and ARM checks without pasteboard execution."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from native_restore_writer_scope_contract import CHANGES,pre_native_restore_writer

class NativeRestoreWriterContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-115';cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.proof=json.loads((cls.phase/'native-restore-writer-contract.json').read_text());cls.src={Path(p).stem:pre_native_restore_only((ROOT/p).read_text())for p in cls.proof['current_sources']};cls.ns={};exec((ROOT/cls.proof['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.ns)
    def order(self,s,tokens):
        cursor=0
        for t in tokens:cursor=s.index(t,cursor)+len(t)
    def test_eleven_original_fragments_and_binary_inputs_current(self):
        self.assertEqual(len(self.proof['original_fragments']),11)
        for r in self.proof['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for r in [self.proof['binary'],self.proof['decoder']]:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_twenty_five_actual_calls_bind_processor_image_and_restore_transaction(self):
        self.assertEqual(len(self.proof['ARM_calls']),25)
        for r in self.proof['ARM_calls']:
            pc=int(r['address'],16);data=self.ns['read'](pc,4);self.assertEqual(data.hex(),r['bytes']);w=int.from_bytes(data,'little');self.assertEqual(w&0x7c000000,0x14000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(pc+d*4,int(r['target'],16))
    def test_six_real_native_source_data_type_selectors_bound(self):
        self.assertEqual({r['selector']for r in self.proof['selectors']},{'rawType','data','sourceApplication','bundleIdentifier','name','timestamp'})
        for r in self.proof['selectors']:
            a=int(r['pointer'],16);v,c=self.ns['reachable_pointer'](a);self.assertEqual(c,r['chain']);self.assertEqual(self.ns['read'](a,8).hex(),r['pointer_bytes']);t=self.ns['base']+(v&((1<<36)-1));o=self.ns['offset'](t);self.assertEqual(self.ns['raw'][o:self.ns['raw'].index(b'\0',o)].decode(),r['selector'])
    def test_restore_callback_is_ADRP_argument_to_transaction_not_direct_call(self):
        self.assertEqual(self.proof['transaction_callback'],'0x10037b620')
        for r in self.proof['callback_words']:self.assertEqual(self.ns['read'](int(r['address'],16),4).hex(),r['bytes'])
        a=0x10037a59c;w=int.from_bytes(self.ns['read'](a,4),'little');v=int.from_bytes(self.ns['read'](a+4,4),'little');imm=((w>>5)&0x7ffff)*4+((w>>29)&3)
        if imm&(1<<20):imm-=1<<21
        self.assertEqual((a&~4095)+(imm<<12)+((v>>10)&0xfff),0x10037b620)
    def test_native_facade_avoids_resolved_value_path_after_type_guard(self):
        s=body(self.src['Pasteboard'],'public func writeToPasteboard(restoreItems:');self.order(s,['guard !restoreItems.isEmpty','guard restoreItems.allSatisfy({ $0.nativeObject != nil })','let selected = restoreItems.map { $0.resolvedItem() }','return','let objects = nativeRestoreObjects(restoreItems','finishPasteboardWrite','prepareHistoryRestore(restoreItems)']);tail=s[s.index('let objects = nativeRestoreObjects'):]
        for t in ['resolvedItem','map(\\.id)','reload()','selectedItems:']:self.assertNotIn(t,tail)
    def test_mixed_value_inputs_keep_existing_selected_value_adapter(self):
        s=body(self.src['Pasteboard'],'public func writeToPasteboard(restoreItems:');v=s[s.index('guard restoreItems.allSatisfy'):s.index('let objects = nativeRestoreObjects')];self.assertIn('resolvedSelection: selected',v);self.assertIn('recognizedImageData: nil',v);self.assertNotIn('Set(',v)
    def test_native_representation_reader_uses_current_ItemData_and_existing_private_cleanup(self):
        s=body(self.src['Pasteboard'],'private static func nativeRestoreRepresentations(');self.assertIn('ClipboardItemDataPersistence.readItems(from: object) ?? []',s);self.assertIn('analysisPayloadKeys.union([multiItemPayloadKey, orderedTypesPayloadKey, originalItemDataPayloadKey])',s)
        for t in ['resolvedItem','ClipboardPersistence.item','payloads','plainText','kind','UUID','reload']:self.assertNotIn(t,s)
    def test_native_processor_preserves_input_order_duplicates_and_kind_prescan(self):
        s=body(self.src['Pasteboard'],'private func nativeRestoreObjects(');self.order(s,['let multiple = inputs.count > 1','let aggregatesText = inputs.contains { $0.previewRawType() == 5 || $0.previewRawType() == 4 }','for input in inputs','let object = input.nativeObject!','UInt8(input.previewRawType()!)'])
        for t in ['Set(','sorted','unique','resolvedItem','store.items','sourceApplication(for:']:self.assertNotIn(t,s)
    def test_each_entity_data_is_prepared_before_its_source_and_flags(self):
        s=body(self.src['Pasteboard'],'private func nativeRestoreObjects(');self.order(s,['for input in inputs','let object = input.nativeObject!','let plain =','let representations:','Self.nativeRestoreRepresentations(for: object)','let items = plain ?','let application = object.value(forKey: "sourceApplication")','let sourceBundleID =','for item in items','item.f_100383574','item.f_10037c4a8','item.f_1003838bc()','if !multiple { return items }'])
    def test_native_image_branch_defers_same_object_metadata(self):
        s=body(self.src['Pasteboard'],'private func nativeRestoreObjects(');a=s.index('if !plain, kind == .image');b=s.index('} else {',a);v=s[a:b];self.assertIn('Self.imageRestore.prepareNative(',v);self.assertIn('object.value(forKey: "sourceApplication")',v);self.assertIn('object.value(forKey: "timestamp") as? Date',v);self.assertIn('Self.nativeRestoreRepresentations(for: object)',v);self.assertNotIn('item.createdAt',v)
    def test_plain_mode_skips_image_preparation_and_uses_existing_string_projection(self):
        s=body(self.src['Pasteboard'],'private func nativeRestoreObjects(');self.assertIn('if !plain, kind == .image',s);self.assertIn('let items = plain ? OriginalPasteboardRestore.f_10031bcdc(representations) : representations',s);self.assertNotIn('allowsLegacyText',s)
    def test_native_source_bundle_comes_from_entity_and_nil_keeps_empty_string(self):
        s=body(self.src['Pasteboard'],'private func nativeRestoreObjects(');self.assertIn('application?.value(forKey: "bundleIdentifier") as? String',s);self.assertIn('sourceBundleID ?? "", forType: "org.nspasteboard.source"',s)
    def test_filter_and_aggregation_suffix_is_exact_value_processor_reuse(self):
        s=body(self.src['Pasteboard'],'private func nativeRestoreObjects(');s=s[s.index('            for item in items {'):].replace('OriginalPasteboardRestore.','').replace('sourceBundleID ??','selection.sourceBundleID ??').replace('["com.microsoft.ole.source"]','ignoredTypes').replace('if !multiple { return items }','if !multiple { return [items] }').replace('return groups.flatMap { $0 }','return groups');v=body((ROOT/'replica/Sources/PastoCore/OriginalPasteboardRestore.swift').read_text(),'public static func f_10038222c(');v=v[v.index('            for item in items {'):];self.assertEqual(s,v);self.assertEqual(hashlib.sha256(s.encode()).hexdigest(),self.proof['aggregate_equivalence']['sha256'])
    def test_native_image_prepares_directory_then_loads_data_then_deferred_formatter(self):
        s=body(self.src['OriginalPasteboardImageRestore'],'func prepareNative(');self.order(s,['let directory = f_100384824()','let items = try loadItems()','guard let directory else { return items }','return f_100383df4(items, sourceName: sourceName(), timestamp: timestamp(), directory: directory)']);self.assertIn('sourceName: @autoclosure () -> String?, timestamp: @autoclosure () -> Date?',self.src['OriginalPasteboardImageRestore'])
    def test_image_filename_evaluates_metadata_after_formatter_creation(self):
        s=body(self.src['OriginalPasteboardImageRestore'],'private func f_100383df4(');self.order(s,['let formatter = DateFormatter()','formatter.dateFormat =','let name = (sourceName() ?? "Pasto")','timestamp() ?? Date.now']);self.assertIn('timestamp: @autoclosure () -> Date?',self.src['OriginalPasteboardImageRestore'])
    def test_existing_public_value_APIs_remain_unchanged(self):
        self.assertEqual(len(self.proof['unchanged_methods']),12)
        for r in self.proof['unchanged_methods']:self.assertEqual(hashlib.sha256(body((ROOT/r['path']).read_text(),r['symbol']).encode()).hexdigest(),r['sha256'])
    def test_native_restore_preparation_holds_same_objects_without_cache_membership_gate(self):
        s=body(self.src['ClipboardStore'],'func prepareHistoryRestore(_ selected: [ClipboardRestoreItem])');self.assertIn('targets: selected.map { (id: $0.id, object: $0.nativeObject!) }',s)
        for t in ['available','resolvedItem','prepareHistoryRestore(ids:','items.first','prepareHistoryItems']:self.assertNotIn(t,s)
        self.assertIn('try validate(local)',s);self.assertIn('state = merge(local, onto: previous)',s)
    def test_legacy_availability_guard_retained_and_prepared_inputs_not_rejected_again(self):
        legacy=body(self.src['ClipboardStore'],'func prepareHistoryRestore(_ selected: [ClipboardItem])');self.assertIn('available.contains($0.id)',legacy);s=body(self.src['ClipboardStore'],'private func mutateInTransaction<T>(');self.assertIn('if preparedRestore == nil, !restoringItemIDs.isEmpty',s);self.assertIn('guard restoringItemIDs.allSatisfy({ available.contains($0) })',s)
    def test_persistence_native_target_wrapper_does_not_fetch_UUIDs(self):
        s=body(self.src['ClipboardPersistence'],'func prepareHistoryRestore(targets:');self.order(s,['let transaction = Transaction(context: context)','context.performAndWait','OriginalObjCExceptionBridge.withResult','HistoryRestoreSelection(transaction: transaction, targets: targets)'])
        for t in ['fetch','prepareHistoryItems','UUID','decode','map']:self.assertNotIn(t,s)
    def test_native_timestamp_pass_finishes_before_optional_cache_projection(self):
        s=body(self.src['ClipboardStore'],'private func mutateInTransaction<T>(');self.order(s,['let targets = try preparedRestore?.native.targets','for update in transaction.repository.restoreHistoryItems(targets)','guard let index = positions[update.id] else { continue }','state.items[index].createdAt = update.timestamp','state.items[index].updatedAt = update.timestamp','state.items[index].isInHistory = true']);self.assertNotIn('let index = positions[update.id]!',s)
    def test_shared_writer_tail_preserves_markers_write_save_error_Undo_and_notification(self):
        s=body(self.src['Pasteboard'],'private func finishPasteboardWrite(');v=s[s.index('        if let first = objects.first'):].replace('let restoration = try prepareRestoration()','let restoration = try prepareHistoryRestore(selected)');old=body((self.phase/'before/replica/Sources/PastoCore/Pasteboard.swift').read_text(),'private func writeToPasteboard(ids:');self.assertEqual(v,old[old.index('        if let first = objects.first'):]);self.assertEqual(hashlib.sha256(v.encode()).hexdigest(),self.proof['writer_tail_equivalence']['sha256'])
    def test_selection_and_Stack_copy_forward_handles_to_core_writer(self):
        s=body(self.src['ReplicaUIController'],'func copySelection(');self.assertIn('let items = appliedRestoreItems()',s);self.assertIn('store.writeToPasteboard(restoreItems: items',s);self.assertNotIn('appliedSelectionItems()',s);s=body(self.src['ReplicaUIController'],'func copy(input:');self.assertIn('store.writeToPasteboard(restoreItems: [input]',s);self.assertIn('Button("复制") { state.controller?.copy(input: input, plainTextOnly: false) }',self.src['AuxiliaryViews'])
    def test_legacy_copy_and_deactivation_order_preserved(self):
        s=body(self.src['ReplicaUIController'],'private func performCopy(');self.order(s,['try write()','copiedItemsHandler?()','hidePanel()']);self.assertIn('selectedItems: [item]',body(self.src['ReplicaUIController'],'func copy(item:'));self.assertIn('store.writeToPasteboard(ids: ids',body(self.src['ReplicaUIController'],'func copy(ids:'))
    def test_fourteen_hunks_exactly_reverse_all247_production_sources(self):
        self.assertEqual(len(CHANGES),14)
        for p,h in self.base['production'].items():
            data=(ROOT/p).read_bytes();data=pre_native_restore_writer(data.decode()).encode()if p.endswith('.swift')else data;self.assertEqual(hashlib.sha256(data).hexdigest(),h)
        for p,h in self.proof['current_sources'].items():self.assertEqual(hashlib.sha256(pre_native_restore_only((ROOT/p).read_text()).encode()).hexdigest(),h)
    def test_reversal_idempotent_and_five_shared_implementations_unchanged(self):
        for p in self.proof['current_sources']:
            old=(self.phase/'before'/p).read_text();self.assertEqual(pre_native_restore_writer((ROOT/p).read_text()),old);self.assertEqual(pre_native_restore_writer(old),old)
        for p,h in self.proof['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_shared_pasteboard_state((ROOT/p).read_text()).encode()).hexdigest(),h);self.assertEqual(h,self.base['production'][p])
    def test_full_metadata_faults_and_Stack_preview_are_not_falsely_certified(self):
        self.assertFalse(self.proof['full_function_migration_verified']);self.assertFalse(self.proof['runtime_executed']);self.assertEqual(self.proof['new_difference_records'],2);self.assertEqual(self.proof['new_conservative_groups'],1);self.assertEqual(len(self.proof['remaining']),4);self.assertIn('validates/merges',self.proof['remaining'][0]);self.assertIn('Stack preview context action is still DTO-based',self.proof['remaining'][1])

if __name__=='__main__':unittest.main()
