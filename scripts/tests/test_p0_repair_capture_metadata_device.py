"""Capture replacement old-content gate and native creation device; source/binary only."""
from pathlib import Path
import hashlib,json,plistlib,re,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from mixed_restore_scope_contract import pre_mixed_restore
from test_offline_p0_contracts import body
from source_entity_lifecycle_scope_contract import pre_source_entity_lifecycle
from new_capture_recovery_scope_contract import pre_new_capture_recovery
from capture_metadata_device_scope_contract import CHANGES,pre_capture_metadata_device
class CaptureMetadataDeviceContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-123';cls.p=json.loads((cls.phase/'capture-metadata-device-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.repo=pre_new_capture_recovery((ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text());cls.store=pre_new_capture_recovery((ROOT/'replica/Sources/PastoCore/ClipboardStore.swift').read_text());cls.sources=pre_new_capture_recovery((ROOT/'replica/Sources/PastoCore/ClipboardSourcePersistence.swift').read_text());cls.capture=body(cls.store,'func addWithInsertionResult(');cls.metadata=body(cls.repo,'private struct CapturedItemCompatibilityMetadata:');cls.value=body(cls.repo,'nonisolated static func capturedItemValue(');cls.apply=body(cls.sources,'func apply(');cls.ns={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.ns)
    def order(self,s,seq):
        p=0
        for t in seq:p=s.index(t,p)+len(t)
    def test_eight_original_fragments_and_reused_native_lookup_model_bound(self):
        self.assertEqual(len(self.p['original_fragments']),8)
        for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for p,h in self.p['reused_evidence'].items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),h)
    def test_binary_and_decoder_inputs_unchanged(self):
        for r in [self.p['binary'],self.p['decoder']]:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_all_sixtyfive_creation_update_direct_calls_bound(self):
        self.assertEqual(len(self.p['complete_call_inventory']),65)
        for r in self.p['complete_call_inventory']:
            a=int(r['address'],16);b=self.ns['read'](a,4);w=int.from_bytes(b,'little');self.assertEqual(b.hex(),r['bytes']);self.assertEqual(w&0xfc000000,0x94000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(a+4*d,int(r['target'],16))
    def test_eleven_real_selectors_bound_from_chained_selector_pointers(self):
        self.assertEqual(len(self.p['selectors']),11)
        for r in self.p['selectors']:
            a=int(r['pointer'],16);v,c=self.ns['reachable_pointer'](a);self.assertEqual(c,r['chain']);self.assertEqual(self.ns['read'](a,8).hex(),r['pointer_bytes']);t=self.ns['base']+(v&((1<<36)-1));o=self.ns['offset'](t);self.assertEqual(self.ns['raw'][o:self.ns['raw'].index(b'\0',o)].decode(),r['selector'])
    def test_original_creation_sets_device_while_update_sets_content_and_replaces_data(self):
        create=[r['selector']for r in self.p['selectors']if r['function']=='0x100360d9c'];update=[r['selector']for r in self.p['selectors']if r['function']=='0x100360ff8'];self.assertIn('setDevice:',create)
        for name in ['setDevice:','setTitle:','setList:']:self.assertNotIn(name,update)
        self.order(' '.join(update),['setRawType:','setChecksum:','data managedObjectContext deleteObject:','initWithContext:','setData:'])
    def test_metadata_subset_excludes_replaced_payload_dates_preview_and_source_app(self):
        fields=dict(re.findall(r'let (\w+): ([^\n]+)',self.metadata));self.assertEqual(set(fields),{'title','hasExplicitTitle','sourceIdentifier','sourceDevice','pinboardIDs'});self.assertEqual(fields['pinboardIDs'],'Set<UUID>');self.assertEqual(fields['sourceDevice'],'String')
        self.assertIn('Self.decode(CapturedItemCompatibilityMetadata.self, object)',self.value);self.assertNotIn('Self.decode(ClipboardItem.self',self.value)
    def test_value_starts_with_incoming_content_and_uses_retained_target_local_id(self):
        self.order(self.value,['let metadata =','var item = replacement','item.id = id','item.title = metadata.title','item.pinboardIDs = metadata.pinboardIDs','ClipboardItemTitlePersistence.project'])
        for t in ['payloads = metadata','kind = metadata','createdAt = metadata','updatedAt = metadata','rawPreview = metadata']:self.assertNotIn(t,self.value)
        self.assertIn('id: capturedTarget.id, replacingContentWith: item',self.capture)
    def test_no_required_old_data_preview_time_or_application_projection(self):
        for key in ['data','rawPasteboardItems','rawPreview','timestamp','localCreatedAt','updatedAt','sourceApplication']:self.assertNotIn('value(forKey: "'+key+'")',self.value)
        self.assertNotIn('ClipboardSourcePersistence.projectApplication',self.value);self.assertNotIn('projectNativePasteboardItems',self.value)
    def test_bad_replaced_fields_do_not_belong_to_compatibility_metadata_schema(self):
        fields=re.findall(r'let (\w+):',self.metadata);old={'title':'saved','sourceDevice':'old Mac','pinboardIDs':['board-A','board-B'],'payloads':37,'kind':'invalid-old-kind','createdAt':'bad-date','updatedAt':False,'rawPreview':[8],'sourceApplication':'bad-old-source'};blob=plistlib.dumps(old,fmt=plistlib.FMT_BINARY);decoded=plistlib.loads(blob);projected={k:decoded.get(k)for k in fields};self.assertEqual(projected['pinboardIDs'],['board-A','board-B']);self.assertEqual(projected['title'],'saved');self.assertNotIn('payloads',projected);self.assertNotIn('kind',projected)
    def test_native_title_owner_order_overlay_keeps_all_secondary_memberships(self):
        self.order(self.value,['item.pinboardIDs = metadata.pinboardIDs','item.pinboardOwnerID = nil','ClipboardItemTitlePersistence.project','== 2','item.pinboardOwnerID = owner','item.pinboardIDs.insert(owner)','ClipboardItemOrderPersistence.project'])
        for t in ['removeAll','intersection','pinboardIDs = [owner]','try? Self.decode']:self.assertNotIn(t,self.value)
    def test_image_analysis_compatibility_is_optional_and_incoming_value_wins(self):
        self.order(self.value,['if replacement.kind == .image','try? PropertyListSerialization.propertyList','dictionary["kind"] as? String == ClipboardKind.image.rawValue','dictionary["payloads"] as? [String: Data]','ClipboardStore.analysisPayloadKeys.contains(type) && item.payloads[type] == nil','item.payloads[type] = data'])
        s=(ROOT/'replica/Sources/PastoCore/OCR.swift').read_text();self.assertIn('nonisolated static let analysisPayloadKeys',s)
    def test_optional_OCR_merge_cannot_replace_incoming_values_or_abort_capture(self):
        self.assertIn('let payloads = dictionary["payloads"] as? [String: Data]',self.value);keys=['recognized','document'];previous={'recognized':b'old','public.png':b'old-image'};incoming={'recognized':b'new','public.png':b'new-image'}
        for k,v in previous.items():
            if k in keys and k not in incoming:incoming[k]=v
        self.assertEqual(incoming['recognized'],b'new');self.assertEqual(incoming['public.png'],b'new-image');self.assertIn('try?',self.value)
    def test_cache_hit_avoids_new_projection_and_cache_miss_uses_metadata_only(self):
        self.order(self.capture,['if let capturedTarget {','if let index = state.items.firstIndex','existingIndex = index','state.items.append(try ClipboardPersistence.capturedItemValue','existingIndex = state.items.count - 1']);self.assertNotIn('ClipboardPersistence.item(capturedTarget.object)',self.capture)
    def test_device_preserve_flag_is_native_query_hit_not_object_insertion_state(self):
        self.assertIn('applications: state.sourceApplications, preserveDevice: capturedTarget != nil',self.capture);self.assertNotIn('preserveDevice: !',self.capture);self.assertNotIn('preserveDevice: target!.object.isInserted',self.capture)
    def test_repository_passes_preserve_flag_and_tracks_source_write(self):
        s=body(self.repo,'func applyCapturedSources(');self.order(s,['try sources.apply(item, applications: applications, to: target.object, preserveDevice: preserveDevice)','sourcedItemIDs.insert(target.id)']);self.assertIn('applications: [SourceApplicationRecord], preserveDevice: Bool = false',self.repo)
    def test_source_application_update_runs_before_device_skip(self):
        self.order(self.apply,['if let identifier = item.sourceApplicationBundleID','source = try application(value)','object.setValue(source, forKey: "sourceApplication")','guard !preserveDevice else { return }','let device = try device(named: item.sourceDevice)','object.setValue(device, forKey: "device")'])
    def test_existing_device_relation_including_nil_or_same_name_other_entity_is_preserved(self):
        self.assertIn('guard !preserveDevice else { return }',self.apply);self.assertIn('preserveDevice: Bool = false',self.sources)
        def result(preserve,existing):return existing if preserve else 'resolved-current-name'
        self.assertIsNone(result(True,None));self.assertEqual(result(True,'old-device-UUID'),'old-device-UUID');self.assertEqual(result(False,None),'resolved-current-name')
    def test_source_apply_body_only_adds_device_guard_generic_default_unchanged(self):
        old=body((self.phase/'before/replica/Sources/PastoCore/ClipboardSourcePersistence.swift').read_text(),'func apply(');self.assertEqual(self.apply.replace('        guard !preserveDevice else { return }\n','',1),old);prefix=self.apply[:self.apply.index('        guard !preserveDevice')];self.assertEqual(hashlib.sha256(prefix.encode()).hexdigest(),self.p['application_branch_sha256'])
    def test_all_other_capture_update_and_timestamp_statements_reverse_exactly(self):
        old=(self.phase/'before/replica/Sources/PastoCore/ClipboardStore.swift').read_text();self.assertEqual(pre_capture_metadata_device(self.store),old)
    def test_eleven_methods_and_seven_shared_sources_preserved(self):
        self.assertEqual(len(self.p['unchanged_methods']),11)
        for r in self.p['unchanged_methods']:self.assertEqual(hashlib.sha256(body(pre_source_entity_lifecycle((ROOT/r['path']).read_text()),r['symbol']).encode()).hexdigest(),r['sha256'])
        self.assertEqual(len(self.p['shared_sources']),7)
        for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_mixed_restore((ROOT/p).read_text()).encode()).hexdigest(),h)
    def test_compat_metadata_errors_remain_explicit_without_empty_group_fallback(self):
        self.assertIn('let metadata = try Self.decode(',self.value);self.assertNotIn('let metadata = try?',self.value);self.assertNotIn('pinboardIDs = []',self.value);self.assertEqual(len(self.p['remaining']),3)
    def test_seven_exact_hunks_reverse_all247_production_files(self):
        self.assertEqual(len(CHANGES),7)
        for p,h in self.base['production'].items():
            b=(ROOT/p).read_bytes();b=pre_capture_metadata_device(b.decode()).encode()if p.endswith('.swift')else b;self.assertEqual(hashlib.sha256(b).hexdigest(),h)
    def test_reversal_idempotent_and_no_full_function_or_runtime_claim(self):
        for p in self.p['current_sources']:
            old=(self.phase/'before'/p).read_text();self.assertEqual(pre_capture_metadata_device((ROOT/p).read_text()),old);self.assertEqual(pre_capture_metadata_device(old),old)
        self.assertEqual(self.p['new_difference_records'],0);self.assertFalse(self.p['full_function_migration_verified']);self.assertFalse(self.p['runtime_executed'])
if __name__=='__main__':unittest.main()
