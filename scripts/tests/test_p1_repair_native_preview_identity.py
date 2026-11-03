"""Native preview registry object-ID URI keys, actual source/Mach-O only."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment
from native_preview_identity_scope_contract import CHANGES,pre_native_preview_identity
from live_preview_identifier_scope_contract import pre_live_preview_identifier
class NativePreviewIdentityContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-136';cls.p=json.loads((cls.phase/'native-preview-identity-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.ui=pre_live_preview_identifier((ROOT/'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text());cls.handle=pre_live_preview_identifier((ROOT/'replica/Sources/PastoCore/ClipboardRestoreItem.swift').read_text());cls.identity=body(cls.handle,'public var previewIdentity:');cls.show=body(cls.ui,'func showPreview(item: ClipboardItem, input:');cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
    def order(self,s,seq):
        i=0
        for t in seq:i=s.index(t,i)+len(t)
    def original(self,a):
        r=next(r for r in self.p['original_fragments']if r['address']==a);return original_fragment((ROOT/r['path']).read_text(),a[2:])
    def test_seven_original_fragments_binary_and_decoder_hash_bound(self):
        self.assertEqual(len(self.p['original_fragments']),7)
        for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for k in ['binary','decoder']:
            r=self.p[k];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_fourteen_machine_words_bind_objectID_URL_AnyHashable_and_equality(self):
        self.assertEqual(len(self.p['ARM_words']),14)
        for r in self.p['ARM_words']:self.assertEqual(self.n['read'](int(r['address'],16),4).hex(),r['bytes'])
        self.assertEqual(self.n['read'](0x1000875a8,4).hex(),'4fc82d94');self.assertEqual(self.n['read'](0x1000875b4,4).hex(),'49c82d94')
    def test_actual_URIRepresentation_selector_reference_bound(self):
        r=self.p['selector'];v,c=self.n['reachable_pointer'](int(r['address'],16));self.assertEqual(hex(v),r['raw']);self.assertEqual(c,r['chain']);t=self.n['base']+(v&((1<<36)-1));self.assertEqual(t,int(r['target'],16));self.assertEqual(self.n['read'](t,70).split(b'\0')[0].decode(),'URIRepresentation')
    def test_external_hashable_witness_is_Foundation_URL_not_UUID_or_object_pointer(self):
        expected=['_$s10Foundation3URLVMa','_$s10Foundation3URLVSHAAMc'];self.assertEqual([r['symbol']for r in self.p['external_imports']],expected)
        for r in self.p['external_imports']:
            v,c=self.n['reachable_pointer'](int(r['address'],16));self.assertEqual(hex(v),r['raw']);self.assertEqual(c,r['chain']);f=self.n['fixup'][0];h=struct.unpack_from('<7I',self.n['raw'],f);self.assertEqual(h[5],1);w=struct.unpack_from('<I',self.n['raw'],f+h[2]+4*(v&0xffffff))[0];a=f+h[3]+(w>>9);self.assertEqual(self.n['raw'][a:self.n['raw'].index(b'\0',a)].decode(),r['symbol'])
    def test_original_lookup_and_registration_derive_URI_values_not_identifiers(self):
        self.assertIn('objc_stub::objectID',self.original('0x1003541f4'))
        for a in ['0x10008747c','0x100086c10']:
            s=self.original(a);self.order(s,['FUN_1003541f4()','objc_stub::URIRepresentation','Foundation::URL::__unconditionallyBridgeFromObjectiveC','Swift::AnyHashable::_init']);self.assertIn('Swift::AnyHashable::___infix',s)
    def test_native_handle_identity_is_URL_value_without_cache_lookup_or_projection(self):
        self.order(self.identity,['if let nativeObject','AnyHashable(nativeObject.objectID.uriRepresentation())','return AnyHashable(id)'])
        for t in ['ObjectIdentifier','absoluteString','uuidString','resolvedItem','context.fetch','existingObject','isDeleted','static let']:self.assertNotIn(t,self.identity)
    def test_legacy_handle_fallback_is_retained_without_native_identity_fabrication(self):
        legacy=body(self.handle,'public init(item: ClipboardItem)');self.assertIn('nativeObject = nil',legacy);self.assertIn('return AnyHashable(id)',self.identity);self.assertIn('Legacy',self.p['adaptations'][0])
    def test_provided_input_resolved_once_before_window_lookup(self):
        self.order(self.show,['if case nil = input, showCollectionPreview(itemID: item.id)','let input = input ?? appliedRestoreItems(orderedIDs: [item.id]).first','?? state.stackRestoreItem(for: item.id) ?? ClipboardRestoreItem(item: item)','previewRegistry.f_10008747c(itemIdentity: input.previewIdentity)','show(existing)'])
        self.assertEqual(self.show.count('let input = input ??'),1)
    def test_all_six_real_lookup_registration_and_popover_sites_share_identity(self):
        self.assertEqual(self.ui.count('itemIdentity: input.previewIdentity'),6)
        self.assertNotIn('itemIdentity: AnyHashable(item.id)',self.ui);self.assertNotIn('itemIdentity: AnyHashable(input.id)',self.ui)
        for marker in ['private func showCollectionPreview(','func showPreview(item: ClipboardItem, input:','private func presentEditingPreview(','private func selectionDidReveal(']:self.assertIn('itemIdentity: input.previewIdentity',body(self.ui,marker))
    def test_popover_detach_preserves_captured_key_and_does_not_recreate_UUID(self):
        pop=pre_live_preview_identifier((ROOT/'replica/Sources/PastoCore/OriginalPreviewPopover.swift').read_text());show=body(pop,'public func show(');detach=body(pop,'public func f_100029a80(');self.assertIn('self.itemIdentity = itemIdentity',show);self.assertIn('manager.f_100086c10(window: window, itemIdentity: itemIdentity,',detach);self.assertNotIn('AnyHashable(',detach)
    def test_registry_body_is_reused_without_new_equality_or_close_behavior(self):
        s=(ROOT/'replica/Sources/PastoCore/OriginalPreviewWindows.swift').read_text();self.assertIn('entries.first { $0.itemIdentity == itemIdentity }?.window',body(s,'public func f_10008747c('));self.order(body(s,'public func f_100086c10('),['f_10008747c(itemIdentity: itemIdentity)?.close()','entries.removeAll { $0.itemIdentity == itemIdentity }','entries.append(Entry(itemIdentity: itemIdentity'])
    def test_business_identifier_callbacks_remain_local_adapter_separate_from_key(self):
        old=(self.phase/'before/replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text();self.assertEqual(self.ui.count('itemIdentifier: item.id.uuidString'),old.count('itemIdentifier: item.id.uuidString'));self.assertEqual(self.ui.count('itemIdentifier: input.id.uuidString'),old.count('itemIdentifier: input.id.uuidString'));self.assertIn('itemIdentifier strings',self.p['adaptations'][1])
    def test_six_methods_and_six_shared_sources_unchanged(self):
        self.assertEqual(len(self.p['unchanged_methods']),6);self.assertEqual(len(self.p['shared_sources']),6)
        for r in self.p['unchanged_methods']:self.assertEqual(hashlib.sha256(body(pre_live_preview_identifier((ROOT/r['path']).read_text()),r['symbol']).encode()).hexdigest(),r['sha256'])
        for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_live_preview_identifier((ROOT/p).read_text()).encode()if p.endswith('.swift')else(ROOT/p).read_bytes()).hexdigest(),h)
    def test_two_sources_seven_hunks_preserve_all247_user_baseline_files(self):
        self.assertEqual(len(CHANGES),7);diff=[]
        for p,h in self.base['production'].items():
            b=(ROOT/p).read_bytes();b=pre_live_preview_identifier(b.decode()).encode()if p.endswith('.swift')else b
            if hashlib.sha256(b).hexdigest()!=h:diff.append(p)
            b=pre_native_preview_identity(b.decode()).encode()if p.endswith('.swift')else b;self.assertEqual(hashlib.sha256(b).hexdigest(),h)
        self.assertEqual(set(diff),set(self.p['current_sources']))
        for p,h in self.p['current_sources'].items():self.assertEqual(hashlib.sha256(pre_live_preview_identifier((ROOT/p).read_text()).encode()if p.endswith('.swift')else(ROOT/p).read_bytes()).hexdigest(),h)
    def test_other_show_body_and_supplied_guard_unchanged_after_exact_inverse(self):
        old=body((self.phase/'before/replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text(),'func showPreview(item: ClipboardItem, input:');self.assertEqual(pre_native_preview_identity(self.show),old);self.assertIn('if case nil = input, showCollectionPreview',self.show)
    def test_whole_P1_and_runtime_not_claimed_complete_by_new_key(self):
        self.assertFalse(self.p['runtime_executed']);self.assertFalse(self.p['full_function_migration_verified']);self.assertEqual(len(self.p['remaining']),3);self.assertIn('04430c/0f733c',self.p['remaining'][2])
if __name__=='__main__':unittest.main()
