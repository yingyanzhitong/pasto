"""Native title model/projections/rename VM: source and binary checks only."""
import hashlib,json,plistlib,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment
from native_title_scope_contract import CHANGES,NEW_PATH,pre_native_title
from item_observation_scope_contract import NEW_PATH as ITEM_OBSERVATION_PATH
from text_submission_scope_contract import pre_text_submission, pre_text_submission_bytes

class NativeTitleContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-87'
        cls.proof=json.loads((cls.phase/'native-title-contract.json').read_text())
        cls.base=json.loads((cls.phase/'baseline.json').read_text())
        cls.paths=dict(p='replica/Sources/PastoCore/ClipboardPersistence.swift',s='replica/Sources/PastoCore/ClipboardStore.swift',r='replica/Sources/PastoCore/ClipboardSnapshotReader.swift')
        cls.src={k:pre_text_submission((ROOT/p).read_text())for k,p in cls.paths.items()};cls.title=(ROOT/NEW_PATH).read_text()
        ns={};exec((ROOT/cls.proof['decoder']['path']).read_text().split("idx={r['address']",1)[0],ns);cls.ns=ns
    def before(self,k):return(self.phase/'before'/self.paths[k]).read_text()
    def original(self,a):
        r=next(r for r in self.proof['original_fragments']if r['address']==a)
        return original_fragment((ROOT/r['path']).read_text(),a[2:])
    def tokens(self,source,tokens):
        for token in tokens:self.assertIn(token,source)

    def test_ten_original_fragments_and_supporting_artifacts_bound(self):
        self.assertEqual(len(self.proof['original_fragments']),10)
        for r in self.proof['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for r in [self.proof[k]for k in ['binary','decoder','reference_model','reused_repository_protocol','sdk_property']]:
            p=Path(r['path']);self.assertEqual(hashlib.sha256((p if p.is_absolute()else ROOT/p).read_bytes()).hexdigest(),r['sha256'])

    def test_original_mom_title_is_optional_indexed_string(self):
        r=self.proof['reference_model'];o=plistlib.loads((ROOT/r['path']).read_bytes())['$objects'];f=r['field'];t=o[f['property_object_index']];e=o[f['entity_object_index']]
        self.assertEqual(o[e['NSEntityName'].data],'ItemEntity');self.assertEqual(o[t['NSPropertyName'].data],'title')
        self.assertEqual(t['NSAttributeType'],700);self.assertTrue(t['NSIsOptional']);self.assertTrue(t['NSIndexedBySpotlight']);self.assertEqual(t['NSDefaultValue'].data,0)

    def test_real_writer_slot_selector_and_five_machine_calls_bound(self):
        p=self.proof['writing_title_slot'];v,ch=self.ns['reachable_pointer'](int(p['address'],16));self.assertEqual(ch,p['chain']);self.assertEqual(self.ns['read'](int(p['address'],16),8).hex(),p['bytes']);self.assertEqual(hex(self.ns['base']+(v&((1<<36)-1))),p['target'])
        s=self.proof['setter'];self.assertEqual(self.ns['read'](int(s['stub'],16),20).hex(),s['stub_bytes']);v,ch=self.ns['reachable_pointer'](int(s['pointer'],16));self.assertEqual(ch,s['chain']);target=self.ns['base']+(v&((1<<36)-1));self.assertEqual(hex(target),s['selector_address']);self.assertEqual(self.ns['read'](target,30).split(b'\0')[0],b'setTitle:')
        raw=(ROOT/self.proof['binary']['path']).read_bytes();self.assertEqual(len(self.proof['ARM_calls']),5)
        for r in self.proof['ARM_calls']:
            pc=int(r['address'],16);b=raw[pc-0x100000000:pc-0x100000000+4];self.assertEqual(b.hex(),r['bytes']);w=int.from_bytes(b,'little');self.assertEqual(w&0x7c000000,0x14000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(pc+d*4,int(r['target'],16))

    def test_original_vm_normalizes_and_setter_does_not_change_dates(self):
        self.tokens(self.original('0x1003bae08'),['FUN_100309008()','Swift::StringProtocol::trimmingCharacters','Foundation::CharacterSet::get_whitespacesAndNewlines','if ((uVar1 == 0) && (IVar4 = objc_stub::title(param_3), IVar4 != 0))','SVar11 = (String)ZEXT816(0)'])
        setter=self.original('0x100364ab4');self.assertIn('objc_stub::setTitle_(param_1,pNVar7)',setter);self.assertNotIn('Date::',setter);self.assertNotIn('timestamp',setter)
        self.assertIn('objc_stub::title(param_2)',self.original('0x100371998'))

    def test_schema_fields_match_original_shape_and_public_sdk_property(self):
        self.tokens(body(self.title,'static func addField(to model:'),['title.name = "title"','title.attributeType = .stringAttributeType','title.isOptional = true','title.isIndexedBySpotlight = true','model.entitiesByName["Item"]!.properties.append(title)','version.attributeType = .integer64AttributeType','version.isOptional = true','model.entitiesByName["State"]!.properties.append(version)'])
        self.assertIn('(getter=isIndexedBySpotlight) BOOL indexedBySpotlight',Path(self.proof['sdk_property']['path']).read_text());self.assertIn('if includeNativeTitle { ClipboardItemTitlePersistence.addField(to: model) }',self.src['p'])

    def test_legacy_model_recipes_preserve_eight_variants_and_prior_current(self):
        def calls(s):
            a=s.index('        let legacyCandidates = [\n');b=s.index('        // The older history-retention variants',a)
            return[l.strip().rstrip(',')for l in s[a:b].splitlines()if l.strip().startswith('makeModel(')]
        current=calls(self.src['p']);old=calls(self.before('p'));self.assertEqual(len(current),9);self.assertEqual(len(old),8)
        self.assertEqual(current[0],'makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, includeNativeTitle: false)');self.assertTrue(all('includeNativeTitle: false'in v for v in current));self.assertEqual([v.replace(', includeNativeTitle: false','')for v in current[1:]],old)

    def test_bootstrap_is_once_from_legacy_and_new_roots_skip_rebootstrap(self):
        source=body(self.title,'static func bootstrap(in context:');self.tokens(source,['guard (root.value(forKey: versionKey) as? NSNumber)?.int64Value != 1 else { return }','context.fetch(PastoItemEntity.defaultFetchRequest())','ClipboardPersistence.decode(ClipboardItem.self, object)','update(item, on: object)','root.setValue(Int64(1), forKey: versionKey)'])
        for token in ['object.setValue','reset()','delete(']:self.assertNotIn(token,source)
        b=body(self.src['p'],'private func bootstrapListsIfNeeded()');self.assertLess(b.index('ClipboardItemTitlePersistence.bootstrap'),b.index('context.save()'))
        c=body(self.src['p'],'func commit<T>(');self.assertIn('root.setValue(Int64(1), forKey: ClipboardItemTitlePersistence.versionKey)',body(c,'if root.isInserted'))

    def test_nil_projection_is_authoritative_and_generated_legacy_label_is_kept(self):
        self.tokens(body(self.title,'static func project(_ item:'),['if let title = object.value(forKey: "title") as? String','item.hasExplicitTitle = true','if item.originalTitle != nil { item.title = "" }','item.hasExplicitTitle = false'])
        cases=[('old',True,'new',('new',True)),('old',True,None,('',False)),('generated',False,None,('generated',False)),('',True,'',('',True))]
        for value,explicit,native,expected in cases:self.assertEqual((native,True)if native is not None else((''if explicit else value),False),expected)

    def test_setter_only_writes_unequal_optional_title_and_respects_mutation_intent(self):
        source=body(self.title,'static func update(_ item:');self.tokens(source,['let title = item.originalTitle','if (object.value(forKey: "title") as? String) != title','object.setValue(title, forKey: "title")']);self.assertNotIn('Date()',source)
        commit=body(self.src['p'],'func commit<T>(');self.assertIn('ClipboardItemTitlePersistence.update(item, on: object)',body(commit,'if object.isInserted || old?.originalTitle != item.originalTitle'))
        self.assertLess(commit.index('ClipboardItemTitlePersistence.update'),commit.index('old.map(contentForComparison)'))

    def test_title_only_change_does_not_encode_unchanged_archived_content(self):
        self.tokens(body(self.src['p'],'private func contentForComparison('),['var value = content(item)','value.title = ""','value.hasExplicitTitle = false'])
        self.assertEqual(body(self.src['p'],'private func content(_ item:'),body(self.before('p'),'private func content(_ item:'))
        c=body(self.src['p'],'func commit<T>(');self.tokens(c,['if old.map(contentForComparison) != contentForComparison(item)','object.setValue(try encode(content(item)), forKey: "content")']);self.assertNotIn('encode(contentForComparison(',c)

    def test_item_and_index_read_native_title_without_forcing_index_payloads(self):
        self.assertIn('ClipboardItemTitlePersistence.project(&item, from: object)',body(self.src['p'],'nonisolated static func item(_ object:'))
        index=body(self.src['r'],'func searchIndexRecords(');self.assertIn('ClipboardItemTitlePersistence.project(&value, from: object)',index);self.assertLess(index.index('ClipboardItemTitlePersistence.project'),index.index('ClipboardSearchRecord.make(value'));self.assertNotIn('ClipboardPersistence.item(object)',index)
        self.assertIn('lhs.title == rhs.title',(ROOT/'replica/Sources/PastoCore/ClipboardSearchRecord.swift').read_text())

    def test_common_title_vm_covers_inline_inputs_and_only_text_changes_content_clock(self):
        source=body(self.src['s'],'public func updateItem(id: UUID');title=body(source,'if let title')
        self.tokens(title,['let previousTitle = state.items[i].originalTitle','OriginalPreviewTitles.f_100308f88','OriginalPreviewTitles.f_100309008','if title != displayedTitle','title.trimmingCharacters(in: .whitespacesAndNewlines)','hasExplicitTitle = !normalized.isEmpty || previousTitle == nil'])
        self.assertEqual(source.count('Date()'),1);self.assertIn('Date()',body(source,'if let text'));self.assertNotIn('Date()',title)
        for p in ['replica/Sources/Pasto/UI/ReplicaCardTitle.swift','replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift']:self.assertIn('updateItem(id: item',(ROOT/p).read_text())
        for signature in ['public func assign(orderedIDs:','public func duplicateItem(id:','public func updateRichTextItem(id:']:self.assertEqual(body(self.src['s'],signature),body(self.before('s'),signature))

    def test_original_optional_blank_branches_are_distinct_from_nil_and_equal_display(self):
        cases=[(None,'Text','  name  ','name'),('old','old',' \n ',None),(None,'Text','',''),('','Text','',None),(None,'Text','Text',None),('old','old','old','old')]
        for previous,displayed,submitted,expected in cases:
            result=previous
            if submitted!=displayed:
                normalized=submitted.strip();result=None if not normalized and previous is not None else normalized
            self.assertEqual(result,expected)

    def test_reviewed_touched_files_schema_scope_and_shared_inputs_bound(self):
        self.assertEqual(len(CHANGES),12)
        for k in self.paths:self.assertEqual(pre_native_title(self.src[k]),self.before(k))
        sha=lambda p:hashlib.sha256(pre_text_submission_bytes(ROOT/p)).hexdigest();current={str(p.relative_to(ROOT))for p in (ROOT/'replica/Sources').rglob('*')if p.is_file()}
        self.assertEqual(current-{ITEM_OBSERVATION_PATH}-set(self.base['production']),{NEW_PATH});self.assertEqual({p for p,h in self.base['production'].items()if sha(p)!=h},set(self.paths.values()))
        for group in ['current_sources','shared_sources']:
            for p,h in self.proof[group].items():self.assertEqual(sha(p),h)
        for p,h in self.proof['shared_sources'].items():self.assertEqual(h,self.base['production'][p])
        for p in ['replica/Package.swift','package.json']:self.assertEqual(sha(p),self.base['other'][p])

    def test_no_native_database_execution_or_whole_entity_claim(self):
        self.assertFalse(self.proof['runtime_executed']);self.assertFalse(self.proof['full_function_migration_verified']);self.assertEqual(self.proof['new_difference_records'],0)
        self.assertTrue(any('CoreData migration/Swift compilation'in r for r in self.proof['remaining']));self.assertTrue(any('UUID Store facade'in r for r in self.proof['remaining']))
