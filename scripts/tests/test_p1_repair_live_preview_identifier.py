"""Event-time native identifier and late detach URI projections; source/Mach-O only."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment
from live_preview_identifier_scope_contract import CHANGES,pre_live_preview_identifier
from native_link_creation_scope_contract import pre_native_link_creation_bytes
class LivePreviewIdentifierContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-137';cls.p=json.loads((cls.phase/'live-preview-identifier-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.ui=(ROOT/'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text();cls.handle=(ROOT/'replica/Sources/PastoCore/ClipboardRestoreItem.swift').read_text();cls.pop=(ROOT/'replica/Sources/PastoCore/OriginalPreviewPopover.swift').read_text();cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
    def order(self,s,seq):
        i=0
        for t in seq:i=s.index(t,i)+len(t)
    def original(self,a):
        r=next(r for r in self.p['original_fragments']if r['address']==a);return original_fragment((ROOT/r['path']).read_text(),a[2:])
    def test_eleven_original_fragments_binary_decoder_and_previous_URI_evidence_bound(self):
        self.assertEqual(len(self.p['original_fragments']),11)
        for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for k in ['binary','decoder','reused_URI_evidence']:
            r=self.p[k];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_sixteen_actual_words_bind_callback_item_transport_identifier_and_registry_lookup(self):
        self.assertEqual(len(self.p['ARM_words']),16)
        for r in self.p['ARM_words']:self.assertEqual(self.n['read'](int(r['address'],16),4).hex(),r['bytes'])
        self.assertEqual(self.n['read'](0x10002990c,4).hex(),'e00315aa');self.assertEqual(self.n['read'](0x100029914,4).hex(),'da760194')
    def test_true_identifier_selector_not_local_UUID_accessor(self):
        r=self.p['selector'];v,c=self.n['reachable_pointer'](int(r['address'],16));self.assertEqual(hex(v),r['raw']);self.assertEqual(c,r['chain']);a=self.n['base']+(v&((1<<36)-1));self.assertEqual(a,int(r['target'],16));self.assertEqual(self.n['read'](a,70).split(b'\0')[0].decode(),'identifier')
    def test_original_callback_reads_identifier_from_item_then_updates_state(self):
        s=self.original('0x100004478');self.order(s,['objc_stub::identifier(param_3)','Swift::String::__unconditionallyBridgeFromObjectiveC','FUN_10008727c(param_1,SVar1.str,SVar1.bridgeObject)'])
        self.assertIn('*(undefined8 *)(unaff_x20 + 0x18)',self.original('0x10000458c'))
    def test_original_willshow_and_registration_read_item_not_cached_scalars(self):
        self.order(self.original('0x100029e6c'),['::isDisplayed) = 1','FUN_100029f60()','PreviewPopover::item','objc_stub::identifier','FUN_100087864()'])
        self.assertIn('objc_stub::identifier(param_2)',self.original('0x100086c10'))
    def test_handle_returns_current_native_string_verbatim_with_legacy_only_fallback(self):
        s=body(self.handle,'public var previewIdentifier:');self.order(s,['if let nativeObject','value(forKey: "nativeIdentifier") as? String','return identifier','return id.uuidString'])
        for t in ['UUID(uuidString','uppercased','lowercased','trimming','isEmpty','resolvedItem','static let','context.fetch']:self.assertNotIn(t,s)
    def test_all_UI_identifier_providers_use_input_projection(self):
        self.assertEqual(self.ui.count('input.previewIdentifier'),7)
        for t in ['itemIdentifier: item.id.uuidString','itemIdentifier: input.id.uuidString','let itemIdentifier = input.id.uuidString']:self.assertNotIn(t,self.ui)
        self.assertEqual(self.ui.count('itemIdentity: input.previewIdentity'),6)
    def test_UI_editing_callbacks_evaluate_input_on_each_event(self):
        show=body(self.ui,'func showPreview(item: ClipboardItem, input:');callback=body(show,'preview.onEditingStateChanged =');self.assertIn('itemIdentifier: input.previewIdentifier',callback)
        edit=body(self.ui,'private func presentEditingPreview(');callback=body(edit,'preview.onEditingStateChanged =');self.assertIn('itemIdentifier: input.previewIdentifier',callback);self.assertNotIn('itemIdentifier: itemIdentifier',callback)
    def test_willShow_reads_current_item_after_sharing_then_conditional_publication(self):
        s=body(self.pop,'public func f_100029e6c()');self.order(s,['isDisplayed = true','f_100029f60()','if let item','let itemIdentifier = item.previewIdentifier','self.itemIdentifier = itemIdentifier','if registry.popoverItemIdentifier != itemIdentifier','registry.popoverItemIdentifier = itemIdentifier','registry.f_100087864()'])
        self.assertNotIn('if let itemIdentifier, registry',s)
    def test_detach_guards_item_without_requiring_stale_identity_identifier_fields(self):
        s=body(self.pop,'public func f_100029a80(');self.assertIn('guard let item else { return nil }',s);self.assertNotIn('guard let itemIdentity',s)
        self.order(s,['makeContentView?(item)','preview.onEditingStateChanged','if beginEditing','preview.f_10007be8c()','manager.f_100086c10(window: window, itemIdentity: item.previewIdentity','itemIdentifier: item.previewIdentifier, isEditing: beginEditing)'])
    def test_detached_edit_callback_uses_captured_item_current_native_identifier(self):
        s=body(body(self.pop,'public func f_100029a80('),'preview.onEditingStateChanged =');self.assertIn('itemIdentifier: item.previewIdentifier',s);self.assertNotIn('itemIdentifier: itemIdentifier',s)
    def test_begin_edit_guard_derives_URI_at_callback_time(self):
        s=body(self.pop,'public func show(');callback=body(s,'preview.onBeginEditing =');self.assertIn('f_1000298b0(itemIdentity: input.previewIdentity)',callback);self.assertNotIn('itemIdentity: itemIdentity',callback)
        guard=body(self.pop,'public func f_1000298b0(');self.order(guard,['registry.f_10008747c(itemIdentity: itemIdentity) == nil','detachForEditing()'])
    def test_six_other_business_methods_and_six_sources_unchanged(self):
        self.assertEqual(len(self.p['unchanged_methods']),6);self.assertEqual(len(self.p['shared_sources']),6)
        for r in self.p['unchanged_methods']:self.assertEqual(hashlib.sha256(body((ROOT/r['path']).read_text(),r['symbol']).encode()).hexdigest(),r['sha256'])
        for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_native_link_creation_bytes(ROOT/p)).hexdigest(),h)
    def test_thirteen_exact_hunks_three_sources_preserve_all247_user_files(self):
        self.assertEqual(len(CHANGES),13);changed=[]
        for p,h in self.base['production'].items():
            b=pre_native_link_creation_bytes(ROOT/p)
            if hashlib.sha256(b).hexdigest()!=h:changed.append(p)
            b=pre_live_preview_identifier(b.decode()).encode()if p.endswith('.swift')else b;self.assertEqual(hashlib.sha256(b).hexdigest(),h)
        self.assertEqual(set(changed),set(self.p['current_sources']))
        for p,h in self.p['current_sources'].items():self.assertEqual(hashlib.sha256(pre_native_link_creation_bytes(ROOT/p)).hexdigest(),h)
    def test_key_and_identifier_remain_separate_no_query_or_persistence_side_effects(self):
        s=body(self.handle,'public var previewIdentifier:');self.assertNotIn('previewIdentity',s);self.assertNotIn('uriRepresentation',s)
        for text in [s,body(self.pop,'public func f_100029e6c()')]:
            for token in ['context.save','setValue(','Task {','DispatchQueue']:self.assertNotIn(token,text)
    def test_legacy_model_and_whole_P1_unknowns_not_claimed_fully_migrated(self):
        self.assertFalse(self.p['runtime_executed']);self.assertFalse(self.p['full_function_migration_verified']);self.assertEqual(len(self.p['adaptations']),2);self.assertEqual(len(self.p['remaining']),2);self.assertIn('04430c/0f733c',self.p['remaining'][1])
if __name__=='__main__':unittest.main()
