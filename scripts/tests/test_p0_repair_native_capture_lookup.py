"""Native checksum lookup/retained capture target and original Handoff scope; source only."""
from pathlib import Path
import hashlib,json,re,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from capture_metadata_device_scope_contract import pre_capture_metadata_device
from native_capture_lookup_scope_contract import CHANGES,pre_native_capture_lookup
class NativeCaptureLookupContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-122';cls.p=json.loads((cls.phase/'native-capture-lookup-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.repo=pre_capture_metadata_device((ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text());cls.store=pre_capture_metadata_device((ROOT/'replica/Sources/PastoCore/ClipboardStore.swift').read_text());cls.lookup=body(cls.repo,'func capturedItem(checksum:');cls.capture=body(cls.store,'func addWithInsertionResult(');cls.ns={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.ns)
    def order(self,s,seq):
        p=0
        for t in seq:p=s.index(t,p)+len(t)
    def test_eighteen_original_fragments_are_bound(self):
        self.assertEqual(len(self.p['original_fragments']),18)
        for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
    def test_binary_decoder_prior_selection_and_checksum_evidence_unchanged(self):
        for r in [self.p['binary'],self.p['decoder']]:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
        for p,h in self.p['reused_evidence'].items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),h)
    def test_ten_real_direct_and_tail_call_targets(self):
        self.assertEqual(len(self.p['ARM_calls']),10)
        for r in self.p['ARM_calls']:
            a=int(r['address'],16);b=self.ns['read'](a,4);w=int.from_bytes(b,'little');self.assertEqual(b.hex(),r['bytes']);self.assertEqual(w&0x7c000000,0x14000000);self.assertEqual(bool(w&0x80000000),r['link']);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(a+d*4,int(r['target'],16))
    def test_original_fetch_error_branch_rejoins_shared_result_slot_store(self):
        for r in self.p['ARM_words']:self.assertEqual(self.ns['read'](int(r['address'],16),4).hex(),r['bytes'])
        a=0x10032af1c;w=int.from_bytes(self.ns['read'](a,4),'little');self.assertEqual(w&0xff00001f,0xb4000015);d=(w>>5)&0x7ffff
        if d&0x40000:d-=0x80000
        self.assertEqual(a+4*d,0x10032af30);self.assertEqual(int.from_bytes(self.ns['read'](0x10032af34,4),'little'),0xf9000260)
    def test_three_selectors_decode_actual_stubs_and_chained_pointers(self):
        self.assertEqual({r['selector']for r in self.p['selectors']},{'setFetchOffset:','setEligibleForHandoff:','setNeedsSave:'})
        for r in self.p['selectors']:
            a=int(r['pointer'],16);v,c=self.ns['reachable_pointer'](a);self.assertEqual(c,r['chain']);self.assertEqual(self.ns['read'](a,8).hex(),r['bytes']);t=self.ns['base']+(v&((1<<36)-1));o=self.ns['offset'](t);self.assertEqual(self.ns['raw'][o:self.ns['raw'].index(b'\0',o)].decode(),r['selector'])
    def test_nil_checksum_does_not_query_or_insert_or_decode(self):
        self.order(self.lookup,['guard let checksum else { return nil }','PastoItemEntity.defaultFetchRequest()','request.predicate','context.fetch(request)'])
        for t in ['insertNewObject','ClipboardPersistence.item','decode(','state.items']:self.assertNotIn(t,self.lookup)
    def test_native_lookup_uses_default_sort_batch_limit_one_and_offset_zero(self):
        self.order(self.lookup,['PastoItemEntity.defaultFetchRequest()','NSPredicate(format: "nativeChecksum == %@", checksum)','request.fetchLimit = 1','request.fetchOffset = 0','(try? context.fetch(request))?.first']);s=(ROOT/'replica/Sources/PastoCore/OriginalManagedItem.swift').read_text();self.assertIn('NSSortDescriptor(key: "timestamp", ascending: false)',s);self.assertIn('request.fetchBatchSize = 20',s)
        for t in ['Set(','sorted','fetchOffset = 1','nativeIdentifier ==','isDeleted','isInHistory']:self.assertNotIn(t,self.lookup)
    def test_fetch_failure_and_no_first_result_are_nil_but_bad_local_key_is_corrupt_error(self):
        self.order(self.lookup,['guard let object = (try? context.fetch(request))?.first else { return nil }','object.value(forKey: "key") as? String','UUID(uuidString: key)','throw CocoaError(.fileReadCorruptFile)','return (id: id, object: object)'])
    def test_recordCapture_queries_repository_before_state_resolution(self):
        self.order(self.capture,['if recordCapture {','knownPasteboardChecksum','let capturedTarget = recordCapture ? try transaction.repository.capturedItem(checksum: checksum) : nil','let existingIndex: Int?','if let capturedTarget','state.items.firstIndex(where: { $0.id == capturedTarget.id })','if let i = existingIndex'])
        self.assertNotIn('previous.nativeChecksum == checksum',self.capture)
    def test_native_hit_identity_wins_over_stale_cache_checksum_counterexample(self):
        old=(self.phase/'before/replica/Sources/PastoCore/ClipboardStore.swift').read_text();self.assertIn('return previous.nativeChecksum == checksum',old);self.assertIn('$0.id == capturedTarget.id',self.capture);cache=[dict(id='A',checksum='incoming'),dict(id='B',checksum='old')];native=dict(id='B',checksum='incoming');self.assertEqual(next(r['id']for r in cache if r['checksum']=='incoming'),'A');self.assertEqual(next(r['id']for r in cache if r['id']==native['id']),'B')
    def test_cache_miss_projects_same_fetched_entity_without_relookup_or_losing_legacy_fields(self):
        self.order(self.capture,['if let capturedTarget {','state.items.firstIndex(where: { $0.id == capturedTarget.id })','state.items.append(try ClipboardPersistence.item(capturedTarget.object))','existingIndex = state.items.count - 1'])
        projection=body(self.repo,'nonisolated static func item(');self.assertIn('var item = try Self.decode(ClipboardItem.self, object)',projection);self.assertIn('item.pinboardIDs.insert(owner)',projection)
    def test_non_capture_comparator_body_is_literal_prior_reuse(self):
        old=body((self.phase/'before/replica/Sources/PastoCore/ClipboardStore.swift').read_text(),'func addWithInsertionResult(');start='                if let checksum {\n                    let previousChecksum';end='                    && Self.hasSamePasteboardRepresentations(previous.payloads, item.payloads)';a=old[old.index(start):old.index(end)+len(end)];b=self.capture[self.capture.index(start):self.capture.index(end)+len(end)];self.assertEqual(a,b)
    def test_native_target_is_retained_through_data_preview_source_and_timestamp(self):
        self.order(self.capture,['target = try capturedTarget ?? transaction.repository.prepareHistoryItems','if target!.object.value(forKey: "nativeIdentifier") == nil','replaceCapturedItemData(target!','if let sourceProvider','applyCapturedSources(target!','restoreHistoryItems([target!])'])
        self.assertEqual(self.capture.count('prepareHistoryItems('),1);self.assertNotIn('capturedTarget.object.objectID',self.capture)
    def test_update_body_and_new_item_behavior_are_unchanged_beyond_target_selection(self):
        old=body((self.phase/'before/replica/Sources/PastoCore/ClipboardStore.swift').read_text(),'func addWithInsertionResult(');start='                let analysis =';end='            let target: (id: UUID, object: NSManagedObject)?';self.assertEqual(self.capture[self.capture.index(start):self.capture.index(end)],old[old.index(start):old.index(end)])
    def test_no_extra_dispatch_timer_save_or_fallback_query_in_native_lookup(self):
        for t in ['DispatchQueue','Task {','Timer','context.save','rollback','reset(','prepareHistoryItems','knownPasteboardChecksum','try context.fetch']:self.assertNotIn(t,self.lookup)
        self.assertIn('try? context.fetch',self.lookup)
    def test_ten_methods_and_seven_shared_files_are_exact(self):
        self.assertEqual(len(self.p['unchanged_methods']),10)
        for r in self.p['unchanged_methods']:self.assertEqual(hashlib.sha256(body(pre_capture_metadata_device((ROOT/r['path']).read_text()),r['symbol']).encode()).hexdigest(),r['sha256'])
        self.assertEqual(len(self.p['shared_sources']),7)
        for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_capture_metadata_device((ROOT/p).read_text()).encode()).hexdigest(),h)
    def test_original_sink_and_compactMap_callbacks_materialized_at_real_PC(self):
        self.assertEqual(len(self.p['materialized_callbacks']),2)
        for r in self.p['materialized_callbacks']:
            a=int(r['address'],16);b=self.ns['read'](a,8);self.assertEqual(b.hex(),r['bytes']);w=int.from_bytes(b[:4],'little');v=int.from_bytes(b[4:],'little');imm=((w>>5)&0x7ffff)*4+((w>>29)&3)
            if imm&0x100000:imm-=0x200000
            self.assertEqual((a&~4095)+(imm<<12)+((v>>10)&0xfff),int(r['target'],16))
    def test_only_Handoff_activity_subtree_is_excluded_local_focus_remains(self):
        r=self.p['network_scope_resolution'];self.assertIn('NSUserActivity',r['chain']);self.assertIn('setsEligibleForHandoff:true',r['chain']);self.assertIn('0b11ac',r['local_focus_retained']);self.assertFalse(r['local_selection_completion']);s=body((ROOT/'replica/Sources/Pasto/AppMain.swift').read_text(),'private func restorePanelApplication(');self.assertIn('previous.activate(options: .activateIgnoringOtherApps)',s)
    def test_four_reviewed_hunks_reverse_all247_sources_and_keep_old_snapshots(self):
        self.assertEqual(len(CHANGES),4)
        for p,h in self.base['production'].items():
            b=(ROOT/p).read_bytes();b=pre_native_capture_lookup(b.decode()).encode()if p.endswith('.swift')else b;self.assertEqual(hashlib.sha256(b).hexdigest(),h)
    def test_reversal_idempotent_and_contract_remains_finite_unscored(self):
        for p in self.p['current_sources']:
            before=(self.phase/'before'/p).read_text();self.assertEqual(pre_native_capture_lookup((ROOT/p).read_text()),before);self.assertEqual(pre_native_capture_lookup(before),before)
        self.assertEqual(self.p['new_difference_records'],0);self.assertFalse(self.p['full_function_migration_verified']);self.assertFalse(self.p['runtime_executed']);self.assertEqual(len(self.p['remaining']),3)
if __name__=='__main__':unittest.main()
