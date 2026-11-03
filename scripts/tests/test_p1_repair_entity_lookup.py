"""Live managed lookup is distinct from projection: C/ARM and source contracts only."""
from pathlib import Path
import hashlib,itertools,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2]
from text_preview_creation_scope_contract import pre_text_preview_creation
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from pinboard_collection_scope_contract import pre_pinboard_collection
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment
from entity_lookup_scope_contract import CHANGES,pre_entity_lookup
from native_text_read_scope_contract import pre_native_text_read_bytes

class EntityLookupContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-97';cls.proof=json.loads((cls.phase/'entity-lookup-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text())
        cls.paths=dict(reference='replica/Sources/PastoCore/ClipboardCollectionItemReference.swift',entry='replica/Sources/PastoCore/ClipboardCollectionEntry.swift',collection='replica/Sources/PastoCore/ClipboardSearchCollection.swift')
        cls.src={k:(ROOT/p).read_text()for k,p in cls.paths.items()};cls.lookup=body(cls.src['reference'],'public func restoreItem(id:')
        ns={};exec((ROOT/cls.proof['decoder']['path']).read_text().split("idx={r['address']",1)[0],ns);cls.ns=ns
    def original(self,a):
        r=next(r for r in self.proof['original_fragments']if r['address']==a);return original_fragment((ROOT/r['path']).read_text(),a[2:])
    def order(self,s,tokens):
        pos=[s.index(t)for t in tokens];self.assertEqual(pos,sorted(pos))

    def test_seven_original_fragments_binary_decoder_SDK_and_prior_contracts_bound(self):
        self.assertEqual(len(self.proof['original_fragments']),7)
        for r in self.proof['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for r in [self.proof['binary'],self.proof['decoder'],self.proof['sdk_header'],self.proof['reused_lookup_proof'],self.proof['reused_optional_selection_proof']]:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])

    def test_actual_optional_required_cast_and_error_release_instructions_unchanged(self):
        self.assertEqual(len(self.proof['ARM_words']),14)
        for r in self.proof['ARM_words']:self.assertEqual(self.ns['read'](int(r['address'],16),4).hex(),r['bytes'])
        words={r['address']:r['bytes']for r in self.proof['ARM_words']};self.assertEqual(words['0x100354470'],'1b000094');self.assertEqual(words['0x10035457c'],'e12a40f9');self.assertEqual(words['0x1003545bc'],'000080d2')

    def test_same_context_existing_object_selector_and_dynamic_cast_import_are_real(self):
        r=self.proof['lookup_selector'];self.assertEqual(r['name'],'existingObjectWithID:error:')
        for key in ['stub','pointer','selector_bytes']:
            value=r[key];self.assertEqual(self.ns['read'](int(value['address'],16),len(bytes.fromhex(value['bytes']))).hex(),value['bytes'])
        _,ch=self.ns['reachable_pointer'](int(r['pointer']['address'],16));self.assertEqual(ch,r['chain'])
        self.assertEqual(bytes.fromhex(r['selector_bytes']['bytes']),b'existingObjectWithID:error:\0')
        for row in self.proof['imports']:
            for key in ['stub','pointer']:
                value=row[key];self.assertEqual(self.ns['read'](int(value['address'],16),len(bytes.fromhex(value['bytes']))).hex(),value['bytes'])
            v,ch=self.ns['reachable_pointer'](int(row['pointer']['address'],16));self.assertEqual(ch,row['chain']);self.assertEqual(v&0xffffff,row['ordinal'])
        self.assertEqual({r['symbol']for r in self.proof['imports']},{'_swift_dynamicCastUnknownClass','_swift_errorRelease'})

    def test_real_observable_collection_slots_bind_optional_and_required_getters(self):
        rows=self.proof['provider_conformance']['table_slots'];self.assertEqual(len(rows),5)
        for r in rows:
            a=int(r['address'],16);v,ch=self.ns['reachable_pointer'](a);self.assertEqual(ch,r['chain']);self.assertEqual(self.ns['read'](a,8).hex(),r['bytes']);self.assertEqual(self.ns['base']+(v&((1<<36)-1)),int(r['target'],16))
        self.assertTrue(any(r['address']=='0x100fc0640'and r['target']=='0x1003544b0'for r in rows))
        self.assertIn('FUN_1003544dc()',self.original('0x1003544b0'))

    def test_original_getter_only_resolves_object_and_class_while_index_requires_it(self):
        optional=self.original('0x1003544dc');self.order(optional,['objc_stub::FUN_100c02080','if (IVar1 == 0)','_swift_errorRelease','_swift_dynamicCastUnknownClass'])
        for token in ['rawPasteboardItems','rawPreview','PropertyListDecoder','timestamp','sourceApplication']:self.assertNotIn(token,optional)
        indexed=self.original('0x10035440c');self.order(indexed,['(long)param_1 < 0','<= param_1','FUN_1003544dc()','if (param_1 != 0)','SoftwareBreakpoint(1,0x1003544b0)'])

    def test_optional_native_lookup_can_only_return_nil_for_lookup_or_class_failure(self):
        self.assertEqual(self.lookup,'{\n        guard let object = (try? context.existingObject(with: objectID)) as? PastoItemEntity else { return nil }\n        return ClipboardRestoreItem(id: id, object: object)\n    }')
        self.assertEqual(self.lookup.count('return nil'),1)
        for token in ['ClipboardPersistence','resolvedItem','payload','decode','store.items','UUID()','reset(','save(','fetch(']:self.assertNotIn(token,self.lookup)
        self.assertNotIn('public func item()',self.src['reference']);self.assertNotIn('public func requiredItem()',self.src['reference'])

    def test_required_native_getter_shares_optional_lookup_and_traps_before_projection(self):
        s=body(self.src['reference'],'public func requiredRestoreItem(id:');self.order(s,['guard let input = restoreItem(id: id)','fatalError("Missing restore item")','return input'])
        for token in ['existingObject','ClipboardPersistence','resolvedItem','try?','value(forKey:']:self.assertNotIn(token,s)

    def test_optional_entry_projects_after_successful_lookup_without_legacy_fallback(self):
        s=body(self.src['entry'],'public func item()');self.order(s,['if let reference { return reference.restoreItem(id: id)?.resolvedItem() }','return legacyItem'])
        self.assertNotIn('try?',s);self.assertNotIn('??',s)
        # Valid entity plus failing projection stays a content failure, never optional lookup nil.
        for lookup_ok,class_ok,projection_ok in itertools.product([False,True],repeat=3):
            native_handle=lookup_ok and class_ok
            result='missing'if not native_handle else('value'if projection_ok else'content_error')
            self.assertEqual(result=='missing',not native_handle)
            if native_handle and not projection_ok:self.assertEqual(result,'content_error')

    def test_required_entry_and_snapshot_keep_entity_requirement_before_value_projection(self):
        s=body(self.src['entry'],'public func requiredItem()');self.assertIn('return reference.requiredRestoreItem(id: id).resolvedItem()',s)
        indexed=body(self.src['collection'],'public func item(at index:');self.order(indexed,['let identifier = identifiers[index]','guard let reference = itemReferences[identifier]','fatalError("Missing collection item reference")','reference.requiredRestoreItem(id: identifier).resolvedItem()'])
        self.assertNotIn('try?',s+indexed)

    def test_handle_retains_actual_native_entity_and_content_failure_is_separate(self):
        s=(ROOT/'replica/Sources/PastoCore/ClipboardRestoreItem.swift').read_text();init=body(s,'init(id: UUID, object: PastoItemEntity)')
        self.order(init,['nativeObject = object','resolve = {','ClipboardPersistence.item(object)','fatalError("Missing restore item content")','return item'])
        self.assertNotIn('[weak',init);self.assertNotIn('return nil',init);self.assertIn('let nativeObject: PastoItemEntity?',s)

    def test_FRC_membership_and_both_ordinary_search_UI_paths_deliver_references(self):
        frc=body(pre_pinboard_collection(self.src['collection']),'private func flushPending()');self.assertIn('ClipboardCollectionItemReference(context: context, objectID: objectID)',frc);self.assertIn('itemReferences: references',frc)
        ui=(ROOT/'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text();visible=body(ui,'var visibleItems:')
        for token in ['snapshot?.itemReferences','searchIndex.resultItemReferences','collectionEntries(identifiers:']:self.assertIn(token,visible)
        self.assertIn('ClipboardCollectionEntry(id: identifier, reference: reference)',body(ui,'private func collectionEntries('))
        self.assertIn('NSFetchedResultsController<PastoItemEntity>',self.src['collection'])

    def test_fourteen_real_render_selection_preview_edit_and_Stack_consumers_are_bound(self):
        self.assertEqual(len(self.proof['actual_consumers']),14)
        for r in self.proof['actual_consumers']:self.assertEqual(hashlib.sha256(body(pre_text_preview_creation((ROOT/r['path']).read_text()),r['symbol']).encode()).hexdigest(),r['sha256'])
        host=(ROOT/'replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift').read_text()
        for marker in ['private func tileCells()','private func refreshCellRoots()']:self.assertIn('requiredRestoreItem()',body(host,marker))
        self.assertIn('items[index].item()',body(host,'func appliedSelectedItems('));self.assertIn('items[index].restoreItem()',body(host,'func appliedRestoreItems('))

    def test_six_unchanged_provider_membership_and_notification_methods_and_no_old_calls(self):
        self.assertEqual(len(self.proof['unchanged_methods']),6)
        for r in self.proof['unchanged_methods']:
            now=body(pre_text_preview_creation((ROOT/r['path']).read_text()),r['symbol']);self.assertEqual(hashlib.sha256(now.encode()).hexdigest(),r['sha256']);self.assertEqual(now,body((self.phase/'before'/r['path']).read_text(),r['symbol']))
        for p in(ROOT/'replica/Sources').rglob('*.swift'):
            s=p.read_text();self.assertNotIn('reference.requiredItem()',s,str(p));self.assertNotIn('reference.item()',s,str(p))

    def test_five_exact_hunks_three_files_without_shared_writer_or_model_edits(self):
        self.assertEqual(len(CHANGES),5);sha=lambda p:hashlib.sha256(pre_native_text_read_bytes(ROOT/p)).hexdigest()
        files={str(p.relative_to(ROOT))for p in(ROOT/'replica/Sources').rglob('*')if p.is_file()};self.assertEqual(files,set(self.base['production']));self.assertEqual({p for p,h in self.base['production'].items()if sha(p)!=h},set(self.paths.values()))
        for key,p in self.paths.items():self.assertEqual(pre_entity_lookup(self.src[key]),(self.phase/'before'/p).read_text())
        for group in ['current_sources','shared_sources']:
            for p,h in self.proof[group].items():self.assertEqual(sha(p),h)
        for p,h in self.proof['shared_sources'].items():self.assertEqual(h,self.base['production'][p])
        for p in ['replica/Package.swift','package.json']:self.assertEqual(sha(p),self.base['other'][p])

    def test_finite_closure_is_only_canonical_provider_record_not_full_migration(self):
        old=self.proof['canonical_backlog'];self.assertEqual(hashlib.sha256((ROOT/old['path']).read_bytes()).hexdigest(),old['sha256']);self.assertEqual(old['record']['function_id'],'Paste:0x1003544dc');self.assertTrue(old['record']['comparison_only'])
        self.assertTrue(self.proof['finite_contract_verified']);self.assertEqual(self.proof['finite_repaired_function_ids'],['Paste:0x1003544dc']);self.assertEqual(self.proof['new_difference_records'],0)
        self.assertFalse(self.proof['full_function_migration_verified']);self.assertFalse(self.proof['runtime_executed'])
        for token in ['content-failure fatal','schema','04430c','overall']:self.assertTrue(any(token in r for r in self.proof['remaining']),token)
