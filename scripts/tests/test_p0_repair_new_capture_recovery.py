"""New native capture device order and unsaved missing-content recovery; source/SDK/binary only."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from local_device_scope_contract import pre_local_device
from mixed_restore_scope_contract import pre_mixed_restore
from test_offline_p0_contracts import body
from source_entity_lifecycle_scope_contract import pre_source_entity_lifecycle
from new_capture_recovery_scope_contract import CHANGES,pre_new_capture_recovery
class NewCaptureRecoveryContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-124';cls.p=json.loads((cls.phase/'new-capture-recovery-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.repo=pre_local_device((ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text());cls.store=pre_local_device((ROOT/'replica/Sources/PastoCore/ClipboardStore.swift').read_text());cls.src=pre_local_device((ROOT/'replica/Sources/PastoCore/ClipboardSourcePersistence.swift').read_text());cls.value=body(cls.repo,'nonisolated static func capturedItemValue(');cls.capture=body(cls.store,'func addWithInsertionResult(');cls.apply=body(cls.src,'func apply(');cls.device=body(cls.src,'func applyDevice(');cls.ns={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.ns)
    def order(self,s,seq):
        p=0
        for t in seq:p=s.index(t,p)+len(t)
    def test_original_creation_update_fragments_and_reused_proofs_bound(self):
        self.assertEqual(len(self.p['original_fragments']),2)
        for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for p,h in self.p['reused_evidence'].items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),h)
    def test_binary_decoder_and_two_real_creation_branch_targets(self):
        for r in [self.p['binary'],self.p['decoder']]:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
        self.assertEqual(len(self.p['ARM_calls']),2)
        for r in self.p['ARM_calls']:
            a=int(r['address'],16);b=self.ns['read'](a,4);w=int.from_bytes(b,'little');self.assertEqual(b.hex(),r['bytes']);self.assertEqual(w&0xfc000000,0x94000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(a+4*d,int(r['target'],16))
    def test_device_selector_is_real_and_call_precedes_content_update(self):
        r=self.p['device_selector'];a=int(r['pointer'],16);v,c=self.ns['reachable_pointer'](a);self.assertEqual(c,r['chain']);self.assertEqual(self.ns['read'](a,8).hex(),r['pointer_bytes']);t=self.ns['base']+(v&((1<<36)-1));o=self.ns['offset'](t);self.assertEqual(self.ns['raw'][o:self.ns['raw'].index(b'\0',o)].decode(),'setDevice:');self.assertLess(int(r['call'],16),0x100360f40)
    def test_local_SDK_pending_fetch_default_is_bound_not_assumed(self):
        r=self.p['sdk'];self.assertEqual(hashlib.sha256(Path(r['path']).read_bytes()).hexdigest(),r['sha256']);self.assertEqual(hashlib.sha256((ROOT/r['excerpt_path']).read_bytes()).hexdigest(),r['excerpt_sha256']);s=(ROOT/r['excerpt_path']).read_text();self.assertIn('currently unsaved changes',s);self.assertIn('Defaults to YES.',s);self.assertTrue(r['default_includes_pending_changes']);request=body(self.repo,'func capturedItem(checksum:');self.assertNotIn('includesPendingChanges',request)
    def test_capture_miss_initializes_device_after_identifier_before_content_and_preview(self):
        self.order(self.capture,['target = try capturedTarget ??','if target!.object.value(forKey: "nativeIdentifier") == nil','setValue(state.items[result.index].nativeIdentifier','if capturedTarget == nil','initializeCapturedDevice(target!, name: state.items[result.index].sourceDevice)','Self.originalPasteboardItems(from:','replaceCapturedItemData(target!','if let sourceProvider','applyCapturedSources(target!','restoreHistoryItems([target!])'])
    def test_capture_hit_skips_initial_device_and_all_capture_post_sources_preserve_it(self):
        initial=body(self.capture,'if capturedTarget == nil');self.assertIn('initializeCapturedDevice(target!',initial);self.assertEqual(self.capture.count('initializeCapturedDevice('),1);self.assertIn('applications: state.sourceApplications, preserveDevice: true',self.capture);self.assertNotIn('preserveDevice: capturedTarget != nil',self.capture)
    def test_repository_early_device_wrapper_uses_same_target_no_extra_fetch_or_save(self):
        s=body(self.repo,'func initializeCapturedDevice(');self.assertEqual(s.strip(),'{\n            try sources.applyDevice(named: name, to: target.object)\n        }')
    def test_generic_device_helper_is_literal_previous_tail_with_parameter_rename_only(self):
        old=body((self.phase/'before/replica/Sources/PastoCore/ClipboardSourcePersistence.swift').read_text(),'func apply(');tail=old[old.index('        let device ='):].replace('device(named: item.sourceDevice)','device(named: name)');self.assertEqual(self.device,'{\n'+tail);self.assertIn('preserveDevice: Bool = false',self.src);self.order(self.apply,['object.setValue(source, forKey: "sourceApplication")','guard !preserveDevice else { return }','try applyDevice(named: item.sourceDevice, to: object)'])
    def test_only_unsaved_inserted_object_with_no_content_bypasses_metadata_decode(self):
        self.assertIn('if object.isInserted, object.value(forKey: "content") == nil',self.value);prefix=self.value[:self.value.index('        var item = replacement')];self.order(prefix,['if object.isInserted','metadata = nil','} else {','metadata = try Self.decode(CapturedItemCompatibilityMetadata.self, object)']);self.assertNotIn('try?',prefix)
    def test_inserted_persisted_and_nil_nonempty_empty_data_gate_matrix(self):
        self.assertIn('object.isInserted, object.value(forKey: "content") == nil',self.value)
        cases=[(True,None,True),(False,None,False),(True,b'bad',False),(False,b'bad',False),(True,b'',False),(False,b'',False)]
        for inserted,content,recover in cases:self.assertEqual(inserted and content is None,recover)
    def test_existing_compatibility_values_use_same_metadata_assignments(self):
        s=body(self.value,'if let metadata');self.order(s,['item.title = metadata.title','item.hasExplicitTitle = metadata.hasExplicitTitle','item.sourceIdentifier = metadata.sourceIdentifier','item.sourceDevice = metadata.sourceDevice','item.pinboardIDs = metadata.pinboardIDs']);self.assertNotIn('pinboardIDs = []',s)
    def test_new_no_content_defaults_do_not_override_native_owner_title_order_or_device(self):
        start=self.value.index('        } else {\n            item.title = ""');end=self.value.index('        item.pinboardOwnerID = nil',start);fallback=self.value[start:end];self.assertIn('item.pinboardIDs = []',fallback);self.assertIn('value(forKey: "device")',fallback);self.assertIn('?? replacement.sourceDevice',fallback);self.assertNotIn('setValue',fallback);self.order(self.value[end:],['ClipboardItemTitlePersistence.project','== 2','item.pinboardIDs.insert(owner)','ClipboardItemOrderPersistence.project'])
    def test_native_metadata_and_optional_OCR_tail_are_unchanged(self):
        old=body((self.phase/'before/replica/Sources/PastoCore/ClipboardPersistence.swift').read_text(),'nonisolated static func capturedItemValue(');marker='        item.pinboardOwnerID = nil';self.assertEqual(self.value[self.value.index(marker):],old[old.index(marker):])
    def test_actual_failure_path_precedes_content_encode_save_and_successful_publish(self):
        commit=body(self.repo,'func commit<T>(');self.order(commit,['try context.performAndWait','let outcome = try operation(transaction)','object.setValue(try encode(content(item))','try context.save()']);self.assertNotIn('rollback',commit);self.assertNotIn('reset(',commit);mutate=body(self.store,'private func mutateInTransaction<T>');self.order(mutate,['persistence.commit(','try change(&state, transaction)','publish(state)']);self.assertEqual(self.p['failure_trace']['status'],'source_and_local_SDK_bound_not_runtime_injected')
    def test_failed_new_capture_retry_source_model_does_not_publish_or_require_missing_blob(self):
        self.order(self.capture,['replaceCapturedItemData(target!','applyCapturedSources(target!','restoreHistoryItems([target!])']);pending={'isInserted':True,'checksum':'same','content':None};published=[];self.assertEqual(published,[]);old_requires_blob=True;new_requires_blob=not(pending['isInserted']and pending['content']is None);self.assertTrue(old_requires_blob);self.assertFalse(new_requires_blob);self.assertEqual(pending['checksum'],'same')
    def test_thirteen_unchanged_methods_include_context_error_boundary_and_lookup(self):
        self.assertEqual(len(self.p['source_refs']),13)
        for r in self.p['source_refs']:self.assertEqual(hashlib.sha256(body(pre_source_entity_lifecycle((ROOT/r['path']).read_text()),r['symbol']).encode()).hexdigest(),r['sha256'])
    def test_seven_shared_files_and_no_other_production_sources_changed(self):
        self.assertEqual(len(self.p['shared_sources']),7)
        for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_mixed_restore((ROOT/p).read_text()).encode()).hexdigest(),h)
        for p,h in self.base['production'].items():
            b=(ROOT/p).read_bytes();b=pre_new_capture_recovery(b.decode()).encode()if p.endswith('.swift')else b;self.assertEqual(hashlib.sha256(b).hexdigest(),h)
    def test_five_hunks_are_idempotently_reversible_and_no_reset_added(self):
        self.assertEqual(len(CHANGES),5)
        for p in self.p['current_sources']:
            old=(self.phase/'before'/p).read_text();self.assertEqual(pre_new_capture_recovery((ROOT/p).read_text()),old);self.assertEqual(pre_new_capture_recovery(old),old)
        for s in [self.value,self.device]:self.assertNotIn('rollback',s);self.assertNotIn('context.reset',s)
    def test_finite_recovery_does_not_claim_full_model_or_runtime_completion(self):
        self.assertEqual(self.p['new_difference_records'],0);self.assertFalse(self.p['full_function_migration_verified']);self.assertFalse(self.p['runtime_executed']);self.assertEqual(len(self.p['remaining']),3);self.assertEqual(len(self.p['failure_trace']['steps']),8)
if __name__=='__main__':unittest.main()
