"""Native text model observation: immutable evidence plus source-level contracts only."""
from pathlib import Path
from native_text_read_scope_contract import pre_native_text_read
import hashlib,itertools,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment
from item_observation_scope_contract import CHANGES,NEW_PATH,pre_item_observation
from edit_entity_input_scope_contract import pre_edit_entity_input,pre_edit_entity_input_bytes

class ItemObservationContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-89';cls.proof=json.loads((cls.phase/'item-observation-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text())
        cls.paths=dict(store='replica/Sources/PastoCore/ClipboardStore.swift',persistence='replica/Sources/PastoCore/ClipboardPersistence.swift',adapter='replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift')
        cls.sources={k:pre_edit_entity_input((ROOT/p).read_text())for k,p in cls.paths.items()};cls.observer=pre_native_text_read((ROOT/NEW_PATH).read_text());cls.consume=body(cls.observer,'private func consume(')
        start=cls.sources['adapter'].index('private final class ReplicaInlineTextPreviewContent:');end=cls.sources['adapter'].index('private final class ReplicaPreviewActionMenuItem:',start);cls.content=cls.sources['adapter'][start:end]
        ns={};exec((ROOT/cls.proof['decoder']['path']).read_text().split("idx={r['address']",1)[0],ns);cls.ns=ns
    def original(self,a):
        r=next(r for r in self.proof['original_fragments']if r['address']==a);return original_fragment((ROOT/r['path']).read_text(),a[2:])
    def before(self,key):return(self.phase/'before'/self.paths[key]).read_text()
    def order(self,s,tokens):
        p=[s.index(t)for t in tokens];self.assertEqual(p,sorted(p))

    def test_eleven_original_fragments_and_reused_context_evidence_bound(self):
        self.assertEqual(len(self.proof['original_fragments']),11)
        for r in self.proof['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for r in [self.proof['binary'],self.proof['decoder'],self.proof['reused_context_evidence']]:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])

    def test_original_eight_calls_and_five_state_words_bound(self):
        self.assertEqual(len(self.proof['ARM_calls']),8);self.assertEqual(len(self.proof['ARM_words']),5)
        for r in self.proof['ARM_calls']:
            pc=int(r['address'],16);b=self.ns['read'](pc,4);self.assertEqual(b.hex(),r['bytes']);w=int.from_bytes(b,'little');self.assertEqual(w&0x7c000000,0x14000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(pc+d*4,int(r['target'],16))
        for r in self.proof['ARM_words']:self.assertEqual(self.ns['read'](int(r['address'],16),4).hex(),r['bytes'])
        words={r['address']:r['bytes']for r in self.proof['ARM_words']};self.assertEqual(words['0x1003560bc'],'040080d2');self.assertEqual(words['0x1003c0510'],'80050037')

    def test_context_notification_and_event_order_use_real_import_bindings(self):
        rows=self.proof['context_bindings'];self.assertEqual(len(rows),5)
        self.assertEqual([(r['symbol'],r['event'])for r in rows[:-1]],[('_NSInsertedObjectsKey',0),('_NSUpdatedObjectsKey',2),('_NSDeletedObjectsKey',1),('_NSRefreshedObjectsKey',3)])
        self.assertEqual(rows[-1]['symbol'],'_NSManagedObjectContextObjectsDidChangeNotification')
        for r in rows:
            v,ch=self.ns['reachable_pointer'](int(r['pointer'],16));self.assertEqual(ch,r['chain']);self.assertEqual(self.ns['read'](int(r['pointer'],16),8).hex(),r['bytes']);self.assertEqual(v&0xffffff,r['ordinal'])

    def test_original_deleted_selector_early_return_and_initial_read_are_bound(self):
        r=self.proof['deleted_selector'];self.assertEqual(self.ns['read'](int(r['stub'],16),20).hex(),r['stub_bytes']);v,ch=self.ns['reachable_pointer'](int(r['pointer'],16));self.assertEqual(ch,r['chain']);target=self.ns['base']+(v&((1<<36)-1));self.assertEqual(hex(target),r['selector_address']);self.assertEqual(self.ns['read'](target,50).split(b'\0')[0],b'isDeleted')
        s=self.original('0x1003c04f0');self.order(s,['objc_stub::isDeleted(param_1)','if ((IVar1 & 1) == 0)','= param_1','FUN_1003c05d4()','(*pcVar4)()'])
        self.order(self.original('0x1003c0390'),['FUN_1003c1c84(','FUN_1003c05d4()'])
        self.assertIn('_swift_dynamicCastClassUnconditional',self.original('0x1003c2064'))

    def test_factory_resolves_same_view_context_once_without_reading_or_publishing_store(self):
        source=body(self.sources['persistence'],'func observeItem(identifier:')
        self.order(source,['context.performAndWait','PastoItemEntity.defaultFetchRequest()','NSPredicate(format: "key == %@", identifier)','request.fetchLimit = 1','guard let object = (try? context.fetch(request))?.first else { return nil }','ClipboardItemObservation(object: object)'])
        self.assertEqual(body(self.sources['store'],'public func observeItem(id:'),'{\n        persistence.observeItem(identifier: id.uuidString)\n    }')
        self.assertIn('NSManagedObjectContext(concurrencyType: .mainQueueConcurrencyType)',self.sources['persistence'])
        for t in ['reset(','snapshotReader','read()','publish(','context.save','newBackgroundContext']:self.assertNotIn(t,source)

    def test_observer_strongly_holds_entity_context_and_subscribes_without_initial_signal(self):
        self.assertIn('@MainActor\npublic final class ClipboardItemObservation',self.observer)
        for t in ['private let context: NSManagedObjectContext','private let objectID: NSManagedObjectID','private var object: PastoItemEntity','private var observation: AnyCancellable?']:self.assertIn(t,self.observer)
        init=body(self.observer,'init(object: PastoItemEntity)')
        self.order(init,['guard let context = object.managedObjectContext','self.context = context','self.object = object','objectID = object.objectID','.publisher(for: .NSManagedObjectContextObjectsDidChange, object: context)','.sink { [weak self]','MainActor.assumeIsolated { self?.consume(notification) }'])
        self.assertNotIn('onChange?',init)
        for t in ['Task','DispatchQueue','Timer','removeDuplicates','CurrentValueSubject','state.store']:self.assertNotIn(t,self.observer)
        self.assertIn('addObserverForName_object_queue_usingBlock_(IVar2,uVar3,param_1,0,aBlock)',self.original('0x100355fb8'))

    def test_native_dispatch_keeps_current_object_required_type_and_deleted_ignore(self):
        self.order(self.consume,['for key in [NSInsertedObjectsKey, NSUpdatedObjectsKey, NSDeletedObjectsKey, NSRefreshedObjectsKey]','notification.userInfo?[key] as? Set<NSManagedObject>','objects.first(where: { $0.objectID == objectID }) else { continue }','let currentItem = current as! PastoItemEntity','guard !currentItem.isDeleted else { return }','object = currentItem','if let value { onChange?(value) }','\n            return\n'])
        for t in ['as? PastoItemEntity','save(','reset(','fetch(','existingObject(','performClose','removeObserver','observation = nil']:self.assertNotIn(t,self.consume)
        self.assertEqual(self.consume.count('onChange?'),1)

    def test_every_overlap_dispatches_once_in_original_priority_and_deleted_event_is_not_a_close(self):
        keys=['NSInsertedObjectsKey','NSUpdatedObjectsKey','NSDeletedObjectsKey','NSRefreshedObjectsKey'];kind=[0,2,1,3]
        self.assertIn('['+', '.join(keys)+']',self.consume)
        for mask in itertools.product([False,True],repeat=4):
            original=next((kind[i]for i,present in enumerate(mask)if present),None)
            loop=[]
            for i,present in enumerate(mask):
                if present:loop.append(kind[i]);break
            self.assertEqual(loop,[]if original is None else[original])
        self.assertIn('guard !currentItem.isDeleted else { return }',self.consume)
        self.assertNotIn('key != NSDeletedObjectsKey',self.consume)

    def test_value_reads_retained_native_entity_without_store_cache_fallback(self):
        value=body(self.observer,'public var value:')
        self.assertEqual(value,'{\n        guard !object.isDeleted else { return nil }\n        return try? ClipboardPersistence.item(object)\n    }')
        for t in ['Store','fetch(','existingObject(','reset(','subject.value']:self.assertNotIn(t,value)

    def test_real_text_initializer_installs_source_then_reads_native_value_separately(self):
        source=body(self.content,'init(state: ReplicaUIState, item: ClipboardItem)')
        self.order(source,['let nativeSource = state.store.observeItem(id: item.id)','nativeItemObservation = nativeSource','if let nativeSource','initial = nativeSource.value.map(Self.attributedContent)','originalText = initial','OriginalPreviewAttributedText.normalizedEditingText(initial)'])
        self.assertIn('} else { initial = Self.attributedContent(item) }',source)
        install=source[source.index('        if let nativeSource {\n            nativeSource.onChange'):]
        self.order(install,['nativeSource.onChange = { [weak self] current in','self?.receiveStoredModel(current)','} else {','itemObservation = state.store.$items.sink'])
        self.assertNotIn('performClose',install)

    def test_baselines_refresh_during_editing_but_only_nonediting_redraws(self):
        receive=body(self.content,'private func receiveStoredModel(')
        self.order(receive,['replaceStoredModel(item)','if !text.isEditable { displayStoredModel() }'])
        self.assertNotIn('canCommit',receive);self.assertNotIn('window?',receive)
        for method in ['private func replaceStoredModel(','private func displayStoredModel(']:self.assertEqual(body(self.content,method),body(self.before('adapter'),method))
        self.order(self.original('0x1003eb8cc'),['FUN_100213188()','if ((uVar1 & 1) == 0)','FUN_1003eb330(0)','FUN_1003eb4a8()'])

    def test_reload_never_uses_store_value_when_native_source_is_present(self):
        source=body(self.content,'private func reloadStoredContent()')
        self.order(source,['if let nativeItemObservation { item = nativeItemObservation.value }','else { item = state?.store.items.first','guard let item else { return }','replaceStoredModel(item)','displayStoredModel()'])
        self.assertNotIn('??',source)
        fallback=body(self.content,'itemObservation = state.store.$items.sink')
        self.assertIn('!current.isDeleted else { return }',fallback);self.assertNotIn('performClose',fallback)

    def test_title_text_commit_and_schema_are_not_modified_by_observation(self):
        for marker in ['public func updateTextPreviewItem(','public func updateItem(','private func mutateInTransaction<T>(']:self.assertEqual(body(self.sources['store'],marker),body(self.before('store'),marker))
        for marker in ['func commit<T>(','private static func makeModel(']:self.assertEqual(body(self.sources['persistence'],marker),body(self.before('persistence'),marker))
        for marker in ['func commitPreviewEditing()','func beginPreviewEditing()','func cancelPreviewEditing()']:self.assertEqual(body(self.content,marker),body(self.before('adapter'),marker))

    def test_six_reviewed_deltas_three_old_files_and_one_new_observer_only(self):
        self.assertEqual(len(CHANGES),6);sha=lambda p:hashlib.sha256(pre_edit_entity_input_bytes(ROOT/p)).hexdigest()
        current={str(p.relative_to(ROOT))for p in(ROOT/'replica/Sources').rglob('*')if p.is_file()}
        self.assertEqual(current-set(self.base['production']),{NEW_PATH})
        self.assertEqual({p for p,h in self.base['production'].items()if sha(p)!=h},set(self.paths.values()))
        for k in self.paths:self.assertEqual(pre_item_observation(self.sources[k]),self.before(k))
        for group in ['current_sources','shared_sources']:
            for p,h in self.proof[group].items():self.assertEqual(sha(p),h)
        for p,h in self.proof['shared_sources'].items():self.assertEqual(h,self.base['production'][p])
        for p in ['replica/Package.swift','package.json']:self.assertEqual(sha(p),self.base['other'][p])

    def test_unknown_projection_errors_native_input_DI_and_full_lifecycle_remain_open(self):
        self.assertFalse(self.proof['runtime_executed']);self.assertFalse(self.proof['full_function_migration_verified']);self.assertEqual(self.proof['new_difference_records'],0)
        for text in ['UUID key','projection errors','Preview header','3544dc']:self.assertTrue(any(text in r for r in self.proof['remaining']),text)
