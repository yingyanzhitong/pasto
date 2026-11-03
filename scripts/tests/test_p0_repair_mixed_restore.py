"""Reachable mixed native/legacy input, source-fidelity grouping and history targets; no runtime."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from local_device_scope_contract import pre_local_device
from test_offline_p0_contracts import body
from mixed_restore_scope_contract import CHANGES,pre_mixed_restore
class MixedRestoreContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-125';cls.p=json.loads((cls.phase/'mixed-restore-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.board=(ROOT/'replica/Sources/PastoCore/Pasteboard.swift').read_text();cls.repo=(ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text();cls.store=(ROOT/'replica/Sources/PastoCore/ClipboardStore.swift').read_text();cls.groups=body(cls.board,'private func nativeRestoreGroups(');cls.loop=body(cls.groups,'for input in inputs');cls.native=body(cls.loop,'if let object = input.nativeObject');cls.prepare=body(cls.repo,'func prepareHistoryRestore(inputs:');cls.ns={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.ns)
    def order(self,s,seq):
        p=0
        for t in seq:p=s.index(t,p)+len(t)
    def test_fourteen_original_fragments_and_binary_decoder_bound(self):
        self.assertEqual(len(self.p['original_fragments']),14)
        for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for r in [self.p['binary'],self.p['decoder']]:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_five_actual_raw_read_and_drag_call_targets(self):
        self.assertEqual(len(self.p['ARM_calls']),5)
        for r in self.p['ARM_calls']:
            a=int(r['address'],16);b=self.ns['read'](a,4);w=int.from_bytes(b,'little');self.assertEqual(b.hex(),r['bytes']);self.assertEqual(w&0x7c000000,0x14000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(a+4*d,int(r['target'],16))
    def test_raw_getter_bridge_error_releases_and_returns_empty_array(self):
        for r in self.p['ARM_words']:self.assertEqual(self.ns['read'](int(r['address'],16),4).hex(),r['bytes'])
        a=0x10031b250;w=int.from_bytes(self.ns['read'](a,4),'little');d=(w>>5)&0x7ffff
        if d&0x40000:d-=0x80000
        self.assertEqual(a+4*d,0x10031b3f0);self.assertEqual(int.from_bytes(self.ns['read'](0x10031b3e8,4),'little'),0xf9406c00)
    def test_real_secondary_membership_producer_can_merge_both_backends(self):
        s=body((ROOT/'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text(),'var visibleItems:');self.order(s,['let native = collectionEntries','let legacy = archived.filter { $0.pinboardOwnerID != pinboardID }','byID[$0.id] ?? ClipboardCollectionEntry(item: $0)','return merged + native.filter']);e=body((ROOT/'replica/Sources/PastoCore/ClipboardCollectionEntry.swift').read_text(),'public func restoreItem()');self.assertIn('reference.restoreItem(id: id)',e);self.assertIn('ClipboardRestoreItem(item: legacyItem)',e)
        archived=['native-A','legacy-B'];by_id={'native-A':'handle-A'};self.assertEqual([by_id.get(i,'legacy-'+i)for i in archived],['handle-A','legacy-legacy-B'])
    def test_applied_selection_and_drag_keep_entry_restore_handles(self):
        s=(ROOT/'replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift').read_text();self.assertIn('items[index].restoreItem()',body(s,'func appliedRestoreItems(for state:'));self.assertIn('applied[index].restoreItem()',body(s,'private func beginNativeDrag('))
    def test_typed_copy_drag_only_full_value_fallback_when_no_native_member_exists(self):
        copy=body(self.board,'public func writeToPasteboard(restoreItems:');drag=body(self.board,'public func dragPasteboardGroups(restoreItems selected:');self.assertIn('restoreItems.contains(where: { $0.nativeObject != nil })',copy);self.assertIn('selected.contains(where: { $0.nativeObject != nil })',drag)
        self.assertIn('return try nativeRestoreGroups(selected, options: options)',drag);self.assertIn('try nativeRestoreObjects(restoreItems, options: options)',copy)
        old=(self.phase/'before/replica/Sources/PastoCore/Pasteboard.swift').read_text();self.assertIn('guard restoreItems.allSatisfy({ $0.nativeObject != nil })',old);self.assertIn('guard selected.allSatisfy({ $0.nativeObject != nil })',old)
    def test_native_branch_never_resolves_DTO_and_preserves_image_then_plain_then_source_order(self):
        for token in ['resolvedItem','ordinaryRestoreRepresentations','item.payloads']:self.assertNotIn(token,self.native)
        self.order(self.native,['kind =','plain =','prepareNative(','Self.nativeRestoreRepresentations','items = plain ?','let application = object.value(forKey: "sourceApplication")','sourceBundleID ='])
    def test_native_branch_is_literal_prior_processing_with_declarations_relocated(self):
        old=body((self.phase/'before/replica/Sources/PastoCore/Pasteboard.swift').read_text(),'private func nativeRestoreGroups(');loop=body(old,'for input in inputs');s=loop[loop.index('            let kind ='):loop.index('            for item in items')].strip();s=s.replace('            let representations: [OriginalPasteboardItem]\n','').replace('let kind =','kind =',1).replace('let plain =','plain =',1).replace('let items =','items =',1).replace('let sourceBundleID =','sourceBundleID =',1);n='\n'.join(l[4:]if l.startswith('    ')else l for l in self.native[1:-1].split('\n')).strip();self.assertEqual(n,s);self.assertEqual(hashlib.sha256(n.encode()).hexdigest(),self.p['native_branch_equivalence']['sha256'])
    def test_legacy_copy_drag_formats_remain_distinct_and_explicit_load_label_matches_API(self):
        self.assertIn('if legacyCopy { return try Self.ordinaryRestoreRepresentations(for: item, plainTextProjection: plain) }',self.loop);self.assertIn('return try Self.originalPasteboardItems(from: item.payloads)',self.loop);self.assertIn('loadItems: read)',self.loop);self.assertIn('legacyCopy: true',body(self.board,'private func nativeRestoreObjects('));self.assertIn('legacyCopy: Bool = false',self.board)
    def test_aggregate_predicate_uses_native_raw_type_or_legacy_kind_without_native_DTO(self):
        s=body(self.groups,'inputs.contains');self.order(s,['if let rawType = input.previewRawType()','return rawType == 5 || rawType == 4','let item = input.resolvedItem()','item.kind == .text || item.kind == .richText || item.kind == .link'])
    def test_one_batch_common_flags_source_and_aggregation_suffix_is_unchanged(self):
        old=body((self.phase/'before/replica/Sources/PastoCore/Pasteboard.swift').read_text(),'private func nativeRestoreGroups(');marker='            for item in items';suffix=self.groups[self.groups.index(marker):];self.assertEqual(suffix,old[old.index(marker):]);self.assertEqual(hashlib.sha256(suffix.encode()).hexdigest(),self.p['per_item_flags_and_batch_aggregate_suffix_sha256']);self.assertEqual(self.groups.count('let combined ='),1)
    def test_mixed_branch_selection_model_keeps_native_away_from_fatal_value_resolver(self):
        inputs=[('native','A'),('legacy','B'),('native','C')];events=[]
        for kind,key in inputs:events.append(('native-data'if kind=='native'else'legacy-value',key))
        self.assertEqual(events,[('native-data','A'),('legacy-value','B'),('native-data','C')]);self.assertNotIn('resolvedItem',self.native);self.assertIn('if let object = input.nativeObject',self.loop)
    def test_pure_native_history_uses_original_target_delegate_without_legacy_fetch(self):
        self.order(self.prepare,['let nativeTargets:','if nativeTargets.count == inputs.count','return try prepareHistoryRestore(targets: nativeTargets)','let transaction = Transaction','context.performAndWait','prepareHistoryItems(legacyIDs)'])
    def test_mixed_history_registers_only_native_targets_for_metadata_only_commit(self):
        self.assertIn('nativeHistoryRestoreTargets: nativeTargets',self.prepare);s=body(self.prepare,'inputs.compactMap');self.assertIn('guard let object = input.nativeObject else { return nil }',s);self.assertIn('return (id: input.id, object: object)',s)
        self.assertNotIn('nativeHistoryRestoreTargets: targets',self.prepare)
    def test_legacy_history_bulk_preparation_and_combined_order_keep_duplicates(self):
        self.assertEqual(self.prepare.count('prepareHistoryItems('),1);self.assertIn('inputs.filter { $0.nativeObject == nil }.map(\.id)',self.prepare);self.order(self.prepare,['let legacyTargets:','var legacyIndex = 0','let targets:','if let object = input.nativeObject','defer { legacyIndex += 1 }','return legacyTargets[legacyIndex]'])
        inputs=[('native','A'),('legacy','B'),('native','A'),('legacy','B'),('legacy','C')];legacy=[('prepared',key)for kind,key in inputs if kind=='legacy'];i=0;out=[]
        for kind,key in inputs:
            if kind=='native':out.append(('same-object',key))
            else:out.append(legacy[i]);i+=1
        self.assertEqual([k for _,k in out],['A','B','A','B','C']);self.assertEqual(i,3)
    def test_native_targets_not_requeried_by_UUID_and_legacy_availability_guard_is_scoped(self):
        s=body(self.store,'func prepareHistoryRestore(_ selected: [ClipboardRestoreItem])');self.order(s,['let legacy = selected.filter { $0.nativeObject == nil }','if !legacy.isEmpty','let available = Set','guard legacy.allSatisfy','persistence.prepareHistoryRestore(inputs: selected)']);self.assertNotIn('nativeObject!',s);self.assertNotIn('resolvedItem',s)
    def test_prepare_still_occurs_after_write_count_and_errors_do_not_skip_undo_notify(self):
        s=body(self.board,'private func finishPasteboardWrite(');self.order(s,['state.f_10037875c(objects)','state.persistChangeCount?','let restoration = try prepareRestoration()','try recordRestoredSelection(restoration)','} catch {','removeAllActions()','NotificationCenter.default.post','didRestoreItem.send()']);self.assertNotIn('guard !objects.isEmpty',s)
    def test_existing_value_drag_write_and_history_methods_remain_exact(self):
        self.assertEqual(len(self.p['source_refs']),22)
        for r in self.p['source_refs']:self.assertEqual(hashlib.sha256(body(pre_local_device((ROOT/r['path']).read_text()),r['symbol']).encode()).hexdigest(),r['sha256'])
    def test_eight_shared_sources_protect_UI_producers_codec_and_grouping_core(self):
        self.assertEqual(len(self.p['shared_sources']),8)
        for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_local_device((ROOT/p).read_text()).encode()).hexdigest(),h)
    def test_audit_covers_five_P0_modules_and_separates_P1_compatibility_and_runtime(self):
        rows=self.p['audit_cases'];self.assertEqual(len(rows),9);self.assertTrue({'快捷键与选区','复制与直接粘贴','数据与删除安全','剪贴板采集与格式保真','面板生命周期与焦点'}.issubset({r['module']for r in rows}));self.assertIn('deferred_by_original_priority',{r['status']for r in rows});self.assertIn('compatibility_adaptation',{r['status']for r in rows});self.assertFalse(self.p['full_P0_completion'])
    def test_eight_hunks_reverse_all247_production_sources_and_no_user_changes_erased(self):
        self.assertEqual(len(CHANGES),8)
        for p,h in self.base['production'].items():
            b=(ROOT/p).read_bytes();b=pre_mixed_restore(b.decode()).encode()if p.endswith('.swift')else b;self.assertEqual(hashlib.sha256(b).hexdigest(),h)
    def test_exact_reversal_idempotent_and_full_migration_not_claimed(self):
        for p in self.p['current_sources']:
            old=(self.phase/'before'/p).read_text();self.assertEqual(pre_mixed_restore((ROOT/p).read_text()),old);self.assertEqual(pre_mixed_restore(old),old)
        self.assertEqual(self.p['new_difference_records'],0);self.assertFalse(self.p['full_function_migration_verified']);self.assertFalse(self.p['runtime_executed']);self.assertEqual(len(self.p['remaining']),3)
if __name__=='__main__':unittest.main()
