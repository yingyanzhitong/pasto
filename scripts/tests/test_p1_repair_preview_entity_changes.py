"""Preview entity notifications and delete consumer: source and ARM contracts only."""
from pathlib import Path
import hashlib,itertools,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment
from preview_entity_changes_scope_contract import CHANGES,pre_preview_entity_changes
from popover_entity_input_scope_contract import pre_popover_entity_input_bytes
from native_text_read_scope_contract import pre_native_text_read_bytes
from native_preview_header_scope_contract import pre_native_preview_header

class PreviewEntityChangeContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-94';cls.proof=json.loads((cls.phase/'preview-entity-changes-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text())
        cls.paths=dict(handle='replica/Sources/PastoCore/ClipboardRestoreItem.swift',adapter='replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift')
        cls.src={k:pre_native_preview_header((ROOT/p).read_text())for k,p in cls.paths.items()}
        cls.header=cls.src['adapter'][cls.src['adapter'].index('private final class ReplicaInlinePreviewHeader:'):]
        cls.init=body(cls.header,'init(state: ReplicaUIState, item: ClipboardItem, input: ClipboardRestoreItem?)')
        ns={};exec((ROOT/cls.proof['decoder']['path']).read_text().split("idx={r['address']",1)[0],ns);cls.ns=ns
    def original(self,a):
        r=next(r for r in self.proof['original_fragments']if r['address']==a);return original_fragment((ROOT/r['path']).read_text(),a[2:])
    def order(self,s,tokens):
        pos=[s.index(t)for t in tokens];self.assertEqual(pos,sorted(pos))

    def test_original_fragments_binary_decoder_and_reused_notifications_bound(self):
        self.assertEqual(len(self.proof['original_fragments']),15)
        for r in self.proof['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for r in [self.proof['binary'],self.proof['decoder']]+self.proof['reused_evidence']:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])

    def test_fourteen_actual_calls_reach_published_context_and_UI_consumer(self):
        self.assertEqual(len(self.proof['ARM_calls']),14)
        for r in self.proof['ARM_calls']:
            pc=int(r['address'],16);b=self.ns['read'](pc,4);self.assertEqual(b.hex(),r['bytes']);w=int.from_bytes(b,'little');self.assertEqual(w&0x7c000000,0x14000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(pc+4*d,int(r['target'],16))
        self.assertIn('FUN_10007b8cc()',self.original('0x10007d078'))
        self.assertIn('Combine::Published::init',self.original('0x100bf5550'))

    def test_initial_published_value_is_input_entity_not_decompiler_zero(self):
        words={r['address']:r['bytes']for r in self.proof['ARM_words']}
        expected={'0x1003c2604':'f60300aa','0x1003c261c':'e00700f9','0x1003c2620':'000080d2','0x1003c2638':'6802198b','0x1003c263c':'e0230091','0x1003c2640':'e10317aa','0x1003c2644':'c3cb2094'}
        for a,b in expected.items():self.assertEqual(words[a],b);self.assertEqual(self.ns['read'](int(a,16),4).hex(),b)
        # STR x0 [sp+8] occurs before metadata request zero; ADD x0 sp+8 is the Published.init argument.
        self.assertIn('does NOT initialize Published(nil)',self.proof['correction'])

    def test_actual_metadata_slot_and_descriptor_name_bind_publisher_to_UI(self):
        r=self.proof['metadata'];self.assertEqual(int(r['address'],16)+r['publisher_offset'],0x100fc2e30);self.assertEqual(r['publisher_offset'],0x88)
        for p in r['pointers']:
            a=int(p['address'],16);v,ch=self.ns['reachable_pointer'](a);self.assertEqual(self.ns['read'](a,8).hex(),p['bytes']);self.assertEqual(ch,p['chain']);self.assertEqual(self.ns['base']+(v&((1<<36)-1)),int(p['target'],16));self.assertEqual(v>>63,0)
        a=int(r['name_reference'],16);b=self.ns['read'](a,4);self.assertEqual(b.hex(),r['name_reference_bytes']);target=a+struct.unpack('<i',b)[0];self.assertEqual(target,int(r['name_address'],16));self.assertEqual(self.ns['read'](target,20).split(b'\0')[0],b'ItemPreviewViewModel')
        words={r['address']:r['bytes']for r in self.proof['ARM_words']};self.assertEqual(words['0x10007ce58'],'094540f9');self.assertEqual(words['0x10007ce64'],'20013fd6');self.assertEqual(words['0x10007ce98'],'00e00191')

    def test_model_observer_delivers_matching_entity_without_deleted_filter_or_projection(self):
        s=body(self.src['handle'],'public func observeChanges(')
        self.order(s,['guard let object = nativeObject else { return nil }','guard let context = object.managedObjectContext','let objectID = object.objectID','let id = self.id','.publisher(for: .NSManagedObjectContextObjectsDidChange, object: context)','.sink { [object, context]','MainActor.assumeIsolated','withExtendedLifetime((object, context))','for key in [NSInsertedObjectsKey, NSUpdatedObjectsKey, NSDeletedObjectsKey, NSRefreshedObjectsKey]','objects.first(where: { $0.objectID == objectID })','let item = current as! PastoItemEntity','consume(ClipboardRestoreItem(id: id, object: item))','\n                            return\n'])
        for token in ['isDeleted','resolvedItem','ClipboardPersistence','fetch(','existingObject','UUID()','removeDuplicates','Task','DispatchQueue','performClose','reset(','save(']:self.assertNotIn(token,s)
        self.assertEqual(s.count('consume('),1);self.assertNotIn('consume(',s[:s.index('.sink')])
        self.assertIn('public var isDeleted: Bool { nativeObject?.isDeleted ?? false }',self.src['handle'])

    def test_overlap_priority_and_once_only_dispatch_match_bound_context_events(self):
        old=json.loads((ROOT/'.local/p0-repair/phase-89/item-observation-contract.json').read_text());rows=old['context_bindings']
        self.assertEqual([(r['symbol'],r['event'])for r in rows[:-1]],[('_NSInsertedObjectsKey',0),('_NSUpdatedObjectsKey',2),('_NSDeletedObjectsKey',1),('_NSRefreshedObjectsKey',3)])
        for row in rows:
            a=int(row['pointer'],16);v,ch=self.ns['reachable_pointer'](a);self.assertEqual(ch,row['chain']);self.assertEqual(self.ns['read'](a,8).hex(),row['bytes']);self.assertEqual(v&0xffffff,row['ordinal'])
        kinds=[0,2,1,3]
        for flags in itertools.product([False,True],repeat=4):
            original=next((kinds[i]for i,present in enumerate(flags)if present),None)
            seen=[]
            for i,present in enumerate(flags):
                if present:seen.append(kinds[i]);break
            self.assertEqual(seen,[]if original is None else[original])

    def test_original_UI_deleted_gate_cancels_title_before_close_and_skips_header_update(self):
        s=self.original('0x10007b8cc');self.order(s,['objc_stub::isDeleted(IVar11)','if ((int)IVar6 != 0)','FUN_100011d28()','objc_stub::window(self)','objc_stub::performClose_(IVar11,0)','FUN_100011e00(IVar11)'])
        self.assertNotIn('isDeleted',self.original('0x1003c2780'))
        old=json.loads((ROOT/'.local/p0-repair/phase-89/item-observation-contract.json').read_text())['deleted_selector'];self.assertEqual(self.ns['read'](int(old['stub'],16),20).hex(),old['stub_bytes']);self.assertEqual(self.ns['read'](int(old['selector_address'],16),10).split(b'\0')[0],b'isDeleted')

    def test_real_native_header_consumer_reads_delete_before_payload_and_preserves_close_order(self):
        s=body(self.init,'let receive: (ClipboardRestoreItem) -> Void =')
        self.order(s,['guard let self else { return }','if current.isDeleted','self.titleLabel.f_100011d28()','self.window?.performClose(nil)','\n                return\n','update(current.resolvedItem())'])
        deleted=body(s,'if current.isDeleted');self.assertNotIn('resolvedItem',deleted);self.assertNotIn('store.',deleted)
        for token in ['hidePanel','Task','DispatchQueue','onClose?','store.items']:self.assertNotIn(token,s)

    def test_initial_and_later_signals_share_consumer_and_legacy_subscription_is_separate(self):
        self.order(self.init,['let receive: (ClipboardRestoreItem) -> Void','itemObservation = input?.observeChanges(receive)','if itemObservation != nil, let input','receive(input)','} else {','itemObservation = state.store.$items.sink','pinboardObservation = state.store.$pinboards.sink'])
        native=body(self.init,'if itemObservation != nil, let input');self.assertIn('receive(input)',native)
        for token in ['items.first','store.items','observeItem(id:']:self.assertNotIn(token,native)
        fallback=self.init[self.init.index('itemObservation = state.store.$items.sink'):];self.assertIn('items.first(where: { $0.id == item.id })',fallback)

    def test_both_real_factories_pass_input_into_header_and_text_observer_is_unchanged(self):
        self.assertEqual(self.src['adapter'].count('let header = ReplicaInlinePreviewHeader(state: state, item: item, input: input)'),2)
        for symbol in ['func makeOriginalReplicaPreview(','func makeOriginalReplicaTextPreview(']:self.assertIn('ReplicaInlinePreviewHeader(state: state, item: item, input: input)',body(self.src['adapter'],symbol))
        p='replica/Sources/PastoCore/ClipboardItemObservation.swift';self.assertEqual(hashlib.sha256(pre_native_text_read_bytes(ROOT/p)).hexdigest(),self.base['production'][p]);self.assertIn('guard !currentItem.isDeleted else { return }',(ROOT/p).read_text())

    def test_existing_header_rendering_is_shared_without_reordering_visual_operations(self):
        s=body(self.init,'let update: (ClipboardItem) -> Void =')
        self.order(s,['guard let self else { return }','OriginalPreviewTitles.f_100309008','field.f_10023b600(defaultTitle)','field.f_10023b214(OriginalPreviewTitles.f_100308f88','share?.isEnabled','self.refreshPinAppearance(current)'])
        before=(self.phase/'before'/self.paths['adapter']).read_text();header=before[before.index('private final class ReplicaInlinePreviewHeader:'):];old=body(header,'init(state: ReplicaUIState, item: ClipboardItem)')
        old=body(old[:old.index('pinboardObservation =')],'MainActor.assumeIsolated');old=old.replace('guard let self, let current = items.first(where: { $0.id == item.id }) else { return }','guard let self else { return }')
        self.assertEqual(''.join(s.replace('{ [weak self, weak share] current in', '{', 1).split()),''.join(old.split()))

    def test_native_observer_does_not_retain_view_and_original_actions_remain_unchanged(self):
        self.assertIn('let update: (ClipboardItem) -> Void = { [weak self, weak share] current in',self.init)
        self.assertIn('let receive: (ClipboardRestoreItem) -> Void = { [weak self] current in',self.init)
        for r in self.proof['unchanged_methods']:
            s=body(pre_native_preview_header((ROOT/r['path']).read_text()),r['symbol']);self.assertEqual(hashlib.sha256(s.encode()).hexdigest(),r['sha256']);self.assertEqual(s,body((self.phase/'before'/r['path']).read_text(),r['symbol']))

    def test_six_exact_hunks_only_two_files_and_no_package_or_shared_storage_changes(self):
        self.assertEqual(len(CHANGES),6);sha=lambda p:hashlib.sha256(pre_popover_entity_input_bytes(ROOT/p)).hexdigest()
        current={str(p.relative_to(ROOT))for p in(ROOT/'replica/Sources').rglob('*')if p.is_file()};self.assertEqual(current,set(self.base['production']));self.assertEqual({p for p,h in self.base['production'].items()if sha(p)!=h},set(self.paths.values()))
        for key,p in self.paths.items():self.assertEqual(pre_preview_entity_changes(self.src[key]),(self.phase/'before'/p).read_text())
        for group in ['current_sources','shared_sources']:
            for p,h in self.proof[group].items():self.assertEqual(sha(p),h)
        for p,h in self.proof['shared_sources'].items():self.assertEqual(h,self.base['production'][p])
        for p in ['replica/Package.swift','package.json']:self.assertEqual(sha(p),self.base['other'][p])

    def test_unmigrated_entrypoints_projection_and_full_model_boundaries_are_explicit(self):
        self.assertFalse(self.proof['full_function_migration_verified']);self.assertFalse(self.proof['runtime_executed']);self.assertEqual(self.proof['new_difference_records'],0)
        for token in ['Ordinary/popover','Published model','projection errors','Pinboard','3544dc']:self.assertTrue(any(token in r for r in self.proof['remaining']),token)
