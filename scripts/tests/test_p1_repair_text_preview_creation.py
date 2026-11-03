"""Native text factory and edit eligibility: source/Mach-O checks only."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment
from text_preview_creation_scope_contract import CHANGES,pre_text_preview_creation
from nontext_edit_write_scope_contract import pre_nontext_edit_write,pre_nontext_edit_write_bytes

class TextPreviewCreationContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-100';cls.proof=json.loads((cls.phase/'text-preview-creation-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text())
        cls.paths=dict(handle='replica/Sources/PastoCore/ClipboardRestoreItem.swift',adapter='replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',controller='replica/Sources/Pasto/UI/ReplicaUIController.swift')
        cls.src={k:pre_nontext_edit_write((ROOT/p).read_text())for k,p in cls.paths.items()};cls.before={k:(cls.phase/'before'/p).read_text()for k,p in cls.paths.items()}
        ns={};exec((ROOT/cls.proof['decoder']['path']).read_text().split("idx={r['address']",1)[0],ns);cls.ns=ns
        s=cls.src['adapter'];cls.text=s[s.index('private final class ReplicaInlineTextPreviewContent:'):s.index('private final class ReplicaPreviewActionMenuItem:')];cls.header=s[s.index('private final class ReplicaInlinePreviewHeader:'):]
    def original(self,a):
        r=next(r for r in self.proof['original_fragments']if r['address']==a);return original_fragment((ROOT/r['path']).read_text(),a[2:])
    def order(self,s,tokens):
        pos=[s.index(t)for t in tokens];self.assertEqual(pos,sorted(pos))
    def test_original_fragments_binary_and_reused_sources_bound(self):
        self.assertEqual(len(self.proof['original_fragments']),19)
        for r in self.proof['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for r in [self.proof['binary'],self.proof['decoder']]+self.proof['reused_evidence']:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_eighteen_actual_calls_bind_factory_and_editing_consumers(self):
        self.assertEqual(len(self.proof['ARM_calls']),18)
        for r in self.proof['ARM_calls']:
            pc=int(r['address'],16);b=self.ns['read'](pc,4);self.assertEqual(b.hex(),r['bytes']);w=int.from_bytes(b,'little');self.assertEqual(w&0x7c000000,0x14000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(pc+4*d,int(r['target'],16))
    def test_inline_factory_passes_same_entity_to_text_model_and_observer(self):
        s=self.original('0x1003c3c90');self.order(s,['objc_stub::rawType(local_58)','if (uVar1 == 5)','FUN_1003c1fe0()','*(ID *)(IVar8 + 0x38) = local_58','FUN_1003c1c60(local_58,FUN_1003c1f34','FUN_1003c05d4()'])
        self.assertNotIn('FUN_1003c0390(',s);self.assertIn('does not directly call3c0390',self.proof['correction'])
        words={r['address']:r['bytes']for r in self.proof['ARM_words']};self.assertEqual(len(words),14)
        for a,b in words.items():self.assertEqual(self.ns['read'](int(a,16),4).hex(),b)
        self.assertEqual(words['0x1003c3ef4'],'d41e00f9');self.assertEqual(words['0x1003c3f40'],'e00314aa')
    def test_allowed_type_table_is_bound_to_real_ARM_data_load(self):
        r=self.proof['allowed_types'];a=0x10031c310;w=int.from_bytes(self.ns['read'](a,4),'little');imm=((w>>5)&0x7ffff)*4+((w>>29)&3)
        if imm&(1<<20):imm-=1<<21
        page=(a&~4095)+(imm<<12);load=int.from_bytes(self.ns['read'](a+4,4),'little');target=page+((load>>10)&0xfff)*4
        self.assertEqual(target,int(r['address'],16));data=self.ns['read'](target,4);self.assertEqual(data.hex(),r['bytes']);self.assertEqual(list(data),[1,2,4,5])
    def test_raw_type_getter_matches_original_unsigned_valid_range(self):
        s=body(self.src['handle'],'public func previewRawType()');self.order(s,['guard let object = nativeObject','object.value(forKey: "rawType")','(0...5).contains(rawType) ? rawType : 0'])
        for t in ['resolvedItem','ClipboardPersistence','store.','Date()','fetch(']:self.assertNotIn(t,s)
        self.assertIn('if (5 < IVar2)',self.original('0x10031eba8'))
        for raw in [-2**63,-1,0,1,2,3,4,5,6,255,2**63-1]:self.assertEqual(raw if 0<=raw<=5 else 0,raw if(raw&((1<<64)-1))<=5 else 0)
    def test_original_filter_checks_native_type_and_complete_input_before_routing(self):
        s=self.original('0x1000655cc');self.order(s,['FUN_10031c2ec()','FUN_1003bb280(']);self.assertIn('objc_stub::rawType',self.original('0x10031c2ec'))
        self.order(self.original('0x10006bed8'),['FUN_10031c2ec()','FUN_10031eba8()','FUN_1000655cc('])
    def test_native_edit_eligibility_does_not_resolve_DTO(self):
        s=body(self.src['controller'],'private static func allowsEditingInput(');self.order(s,['if let rawType = input.previewRawType()','return [1, 2, 4, 5].contains(rawType)','return allowsContentEditing(input.resolvedItem())'])
        self.assertNotIn('resolvedItem',body(s,'if let rawType = input.previewRawType()'))
        edit=body(self.src['controller'],'private func editItems(');self.order(edit,['items.filter { Self.allowsEditingInput($0) }','guard !editable.isEmpty','for input in editable','presentEditingPreview(input: input)']);self.assertNotIn('resolvedItem',edit)
    def test_writing_tools_preserves_capability_filter_route_task_order(self):
        s=body(self.src['controller'],'private func writeAppliedSelection()');self.order(s,['OriginalWritingTools.isAvailable()','appliedRestoreItems().filter','guard Self.allowsEditingInput($0)','if let rawType = $0.previewRawType() { return rawType == 5 }','let item = $0.resolvedItem()','guard !items.isEmpty','editItems(items)','OriginalWritingTools.showAfterDelay()'])
        self.assertNotIn('resolvedItem',s[:s.index('if let rawType = $0.previewRawType()')])
    def test_native_text_factory_routes_before_any_DTO_projection(self):
        s=body(self.src['adapter'],'func makeOriginalReplicaNativePreview(');self.order(s,['if input.previewRawType() == 5','makeReplicaTextPreview(state: state, item: nil, input: input)','return makeOriginalReplicaPreview(state: state, item: input.resolvedItem(), input: input)'])
        self.assertNotIn('resolvedItem',body(s,'if input.previewRawType() == 5'));self.assertNotIn('ClipboardItem(',s)
    def test_legacy_and_native_text_factories_share_identical_existing_builder(self):
        legacy=body(self.src['adapter'],'func makeOriginalReplicaTextPreview(');self.order(legacy,['if let rawType = input?.previewRawType()','else { isText = item.kind','guard isText','makeReplicaTextPreview(state: state, item: item, input: input)'])
        old=body(self.before['adapter'],'func makeOriginalReplicaTextPreview(').replace('    guard item.kind == .text || item.kind == .richText else { return nil }\n','');self.assertEqual(body(self.src['adapter'],'private func makeReplicaTextPreview('),old)
    def test_header_native_initialization_needs_identity_not_legacy_value(self):
        s=body(self.header,'init(state: ReplicaUIState, item: ClipboardItem?, input: ClipboardRestoreItem?)');self.order(s,['guard let itemID = input?.id ?? item?.id','self.itemID = itemID','self.input = input','super.init','itemObservation = input?.observeChanges(receive)','receive(input)'])
        self.assertNotIn('resolvedItem',s[:s.index('let receive:')]);self.assertIn('items.first(where: { $0.id == itemID })',s)
    def test_text_reads_native_observer_before_optional_legacy_resolution(self):
        s=body(self.text,'init(state: ReplicaUIState, item: ClipboardItem?, input: ClipboardRestoreItem?)');self.order(s,['guard let itemID = input?.id ?? item?.id','if let input { nativeSource = input.observeItem() }','else { nativeSource = state.store.observeItem(id: itemID) }','if let nativeSource','initial = nativeSource.attributedText','else if let item = item ?? input?.resolvedItem()','Self.attributedContent(item)','originalText = initial'])
        self.assertNotIn('resolvedItem',body(s,'if let nativeSource {\n            initial ='))
    def test_controller_native_preview_edit_and_detach_all_reach_same_factory(self):
        s=self.src['controller'];self.assertEqual(s.count('makeOriginalReplicaNativePreview('),3)
        preview=body(s,'private func makePreviewContent(');self.assertIn('makeOriginalReplicaNativePreview(state: state, input: input)',preview);self.assertNotIn('resolvedItem',preview)
        popover=body(s,'private func makePreviewPopover()');self.assertIn('makeOriginalReplicaNativePreview(state: self.state, input: input)',popover);self.assertNotIn('resolvedItem',popover)
        self.assertNotIn('makeOriginalReplicaPreview(',s)
    def test_edit_window_registration_and_transition_keep_same_input_identity(self):
        s=body(self.src['controller'],'private func presentEditingPreview(');self.order(s,['let window = OriginalPreviewWindow()','let itemIdentifier = input.id.uuidString','registry.f_100086c10(window: window, itemIdentity: AnyHashable(input.id)','OriginalPreviewWindowTransition(window: window)','makeOriginalReplicaNativePreview(state: state, input: input)','preview.f_10007be8c()','transition.present(controller)','focusPreviewEditing()'])
        self.assertNotIn('resolvedItem',s);self.assertNotIn('let item =',s)
    def test_text_UI_subscriptions_and_editor_behavior_after_initial_read_are_unchanged(self):
        marker='originalText = initial';new=body(self.text,'init(state: ReplicaUIState, item: ClipboardItem?, input: ClipboardRestoreItem?)');old=self.before['adapter'];old=old[old.index('private final class ReplicaInlineTextPreviewContent:'):old.index('private final class ReplicaPreviewActionMenuItem:')];old=body(old,'init(state: ReplicaUIState, item: ClipboardItem, input: ClipboardRestoreItem?)');self.assertEqual(new[new.index(marker):],old[old.index(marker):])
    def test_fifteen_existing_commit_observation_and_lifecycle_methods_remain_unchanged(self):
        self.assertEqual(len(self.proof['unchanged_methods']),15)
        for r in self.proof['unchanged_methods']:
            s=body(pre_nontext_edit_write((ROOT/r['path']).read_text()),r['symbol']);self.assertEqual(hashlib.sha256(s.encode()).hexdigest(),r['sha256']);self.assertEqual(s,body((self.phase/'before'/r['path']).read_text(),r['symbol']))
    def test_exact_delta_scope_and_historical_reversal_are_idempotent(self):
        self.assertEqual(len(CHANGES),18);sha=lambda p:hashlib.sha256(pre_nontext_edit_write_bytes(ROOT/p)).hexdigest();current={str(p.relative_to(ROOT))for p in(ROOT/'replica/Sources').rglob('*')if p.is_file()};self.assertEqual(current,set(self.base['production']))
        self.assertEqual({p for p,h in self.base['production'].items()if sha(p)!=h},set(self.paths.values()))
        for k,p in self.paths.items():self.assertEqual(pre_text_preview_creation(self.src[k]),self.before[k]);self.assertEqual(pre_text_preview_creation(self.before[k]),self.before[k]);self.assertEqual(sha(p),self.proof['current_sources'][p])
        for p,h in self.proof['shared_sources'].items():self.assertEqual(sha(p),h);self.assertEqual(h,self.base['production'][p])
    def test_two_finite_dependency_records_leave_full_factory_permissions_and_model_open(self):
        self.assertEqual(self.proof['new_difference_records'],2);self.assertEqual({r['function_id']for r in self.proof['contracts']},{'Paste:0x1003c3c90','Paste:0x10031c2ec'});self.assertTrue(self.proof['finite_contract_verified']);self.assertFalse(self.proof['full_function_migration_verified']);self.assertFalse(self.proof['runtime_executed'])
        for token in ['Nontext','Missing fields','Published','CloudShare','04430c']:self.assertTrue(any(token in s for s in self.proof['remaining']),token)
