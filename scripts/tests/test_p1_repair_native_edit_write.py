"""Same captured entity for text commits, source/static checks only."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment
from native_edit_write_scope_contract import CHANGES,pre_native_edit_write
from native_title_write_scope_contract import pre_native_title_write,pre_native_title_write_bytes

class NativeEditWriteContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-91';cls.proof=json.loads((cls.phase/'native-edit-write-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text())
        cls.paths=dict(handle='replica/Sources/PastoCore/ClipboardRestoreItem.swift',store='replica/Sources/PastoCore/ClipboardStore.swift',adapter='replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift')
        cls.src={k:pre_native_title_write((ROOT/p).read_text())for k,p in cls.paths.items()};cls.worker=body(cls.src['store'],'private func updateTextPreviewItem(')
        ns={};exec((ROOT/cls.proof['decoder']['path']).read_text().split("idx={r['address']",1)[0],ns);cls.ns=ns
    def original(self,a):
        r=next(r for r in self.proof['original_fragments']if r['address']==a);return original_fragment((ROOT/r['path']).read_text(),a[2:])
    def before(self,k):return(self.phase/'before'/self.paths[k]).read_text()
    def order(self,s,tokens):
        p=[s.index(t)for t in tokens];self.assertEqual(p,sorted(p))

    def test_six_original_fragments_binary_and_existing_native_writer_evidence_bound(self):
        self.assertEqual(len(self.proof['original_fragments']),6)
        for r in self.proof['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for r in [self.proof['binary'],self.proof['decoder'],self.proof['reused_write_evidence']]:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])

    def test_actual_target_loads_and_indirect_writer_handoff_are_bound(self):
        self.assertEqual(len(self.proof['target_handoff_words']),6)
        rows={r['address']:r['bytes']for r in self.proof['target_handoff_words']}
        for r in self.proof['target_handoff_words']:self.assertEqual(self.ns['read'](int(r['address'],16),4).hex(),r['bytes'])
        self.assertEqual(rows['0x1003c0fe4'],'541f40f9');self.assertEqual(rows['0x1003c1088'],'531f40f9')
        for a in ['0x1003c105c','0x1003c1180']:self.assertEqual(rows[a],'00013fd6')
        source=self.original('0x1003c0e50');self.assertEqual(source.count('*(undefined8 *)(param_4 + 0x38)'),2)

    def test_real_writing_content_slot_targets_existing_entity_update_not_insertion_lookup(self):
        r=self.proof['writing_content_slot'];v,ch=self.ns['reachable_pointer'](int(r['address'],16));self.assertEqual(ch,r['chain']);self.assertEqual(self.ns['read'](int(r['address'],16),8).hex(),r['bytes']);self.assertEqual(hex(self.ns['base']+(v&((1<<36)-1))),r['target']);self.assertEqual(r['target'],'0x100363ff0')
        self.assertIn('FUN_100360ff8()',self.original('0x100363ff0'));self.assertNotIn('FUN_1003611b0',self.original('0x100363ff0'))

    def test_original_nil_checksum_short_circuits_all_writes_and_no_dates_or_metadata(self):
        source=self.original('0x100360ff8')
        self.order(source,['FUN_1003216bc(param_2)','if (uVar5 != 0)','objc_stub::setRawType_','objc_stub::setChecksum_','objc_stub::deleteObject_','objc_stub::setData_','FUN_100322504('])
        for token in ['Date::','setTimestamp_','setTitle_','setSourceApplication_','identifier','FUN_1003214c8']:self.assertNotIn(token,source)

    def test_handle_preserves_native_object_explicitly_and_legacy_has_none(self):
        self.assertIn('    let nativeObject: PastoItemEntity?',self.src['handle']);self.assertNotIn('public let nativeObject',self.src['handle'])
        native=body(self.src['handle'],'init(id: UUID, object: PastoItemEntity)');self.assertIn('nativeObject = object',native)
        legacy=body(self.src['handle'],'public init(item: ClipboardItem)');self.assertIn('nativeObject = nil',legacy)
        for marker in ['public func resolvedItem()','public func observeItem()']:self.assertEqual(body(self.src['handle'],marker),body(self.before('handle'),marker))

    def test_text_view_retains_edit_input_and_extracts_content_once_before_dispatch(self):
        s=self.src['adapter'];self.assertIn('private let editInput: ClipboardRestoreItem?',s)
        init=body(s,'init(state: ReplicaUIState, item: ClipboardItem, input: ClipboardRestoreItem?)');self.assertIn('editInput = input',init)
        commit=body(s,'func commitPreviewEditing()');self.assertEqual(commit.count('f_100212ccc(editor: text)'),1)
        self.order(commit,['text.isEditable = false','guard let state','let content = OriginalPreviewAttributedText.f_100212ccc(editor: text)','if let editInput','updateTextPreviewItem(editInput, attributedString: content)','} else {','updateTextPreviewItem(id: itemID, attributedString: content)','state.normalizeSelection()','catch { state.controller?.presentError(error) }','reloadStoredContent()'])
        self.assertNotIn('observeItem(',commit);self.assertNotIn('appliedRestoreItems',commit)

    def test_native_and_id_entrypoints_share_one_transaction_worker(self):
        id_entry=body(self.src['store'],'public func updateTextPreviewItem(id: UUID, attributedString:')
        native_entry=body(self.src['store'],'public func updateTextPreviewItem(_ input:')
        self.assertEqual(id_entry,'{\n        try updateTextPreviewItem(id: id, input: nil, attributedString: attributedString)\n    }')
        self.assertEqual(native_entry,'{\n        try updateTextPreviewItem(id: input.id, input: input, attributedString: attributedString)\n    }')
        self.assertEqual(self.worker.count('try mutateInTransaction'),1)
        for token in ['persistence.commit','save(','reset(','rollback(','Task','DispatchQueue']:self.assertNotIn(token,self.worker)

    def test_native_cache_miss_is_not_a_target_failure_and_checksum_precedes_any_change(self):
        self.order(self.worker,['let nativeObject = input?.nativeObject','var index = state.items.firstIndex','guard nativeObject != nil || index != nil else','OriginalTextPreviewSubmission.makeItem(attributedString)','guard let checksum = OriginalPasteboardChecksums.f_1003216bc(items, kind: nativeKind) else { return }','let target: (id: UUID, object: NSManagedObject)','input.resolvedItem()','state.items.append(item)','transaction.repository.replaceCapturedItemData('])
        self.assertEqual(self.worker.count('state.items.append(item)'),1)

    def test_native_target_uses_same_entity_current_metadata_and_no_id_lookup(self):
        native=body(self.worker,'if let nativeObject, let input')
        self.order(native,['target = (id: id, object: nativeObject)','item = input.resolvedItem()','if index == nil','index = state.items.count','state.items.append(item)'])
        for token in ['prepareHistoryItems','fetch(','existingObject(','Date()','state.items[index!]']:self.assertNotIn(token,native)
        self.assertIn('} else {\n                target = try transaction.repository.prepareHistoryItems([id]).first!\n                item = state.items[index!]\n            }',self.worker)

    def test_content_tail_and_preview_writer_order_preserved_except_native_clock(self):
        old=body(self.before('store'),'public func updateTextPreviewItem(');start='            item.payloads = payloads\n';end='            state.items[i] = item\n';a=old[old.index(start):old.index(end)+len(end)];b=self.worker[self.worker.index(start):self.worker.index(end)+len(end)]
        b=b.replace('            // Native content replacement preserves recency; retain the old value-only adapter\'s clock.\n            if nativeObject == nil { item.updatedAt = Date() }\n','            // Keep the local conflict clock; the native history timestamp is unchanged.\n            item.updatedAt = Date()\n')
        self.assertEqual(a,b)
        self.order(self.worker,['item.nativeChecksum = checksum','transaction.repository.replaceCapturedItemData(target,','item = Self.withPreviewMetadata(item,','return item.rawPreview','state.items[i] = item'])

    def test_native_edits_preserve_time_and_old_value_adapter_only_keeps_date(self):
        self.assertEqual(self.worker.count('Date()'),1)
        self.assertEqual(body(self.worker,'if nativeObject == nil'),'{ item.updatedAt = Date() }')
        for token in ['item.createdAt =','item.isInHistory =','item.title =','item.sourceName =','item.nativeIdentifier =']:self.assertNotIn(token,self.worker)
        self.assertIn('item = input.resolvedItem()',self.worker)

    def test_unchanged_local_merge_uses_content_difference_without_timestamp_winner(self):
        merge=body(self.src['store'],'private func merge(_ local:');payload=body(merge,'if local.payloads != base.payloads')
        self.assertIn('value.payloads = local.payloads',payload);self.assertNotIn('updatedAt',payload)
        generic=body(self.src['store'],'private func mergedEntities<');self.assertIn('for value in local where old[value.id] != value',generic)
        self.assertNotIn('updatedAt',generic)
        for r in self.proof['unchanged_business_methods']:
            current=body(pre_native_title_write((ROOT/r['path']).read_text()),r['symbol']);self.assertEqual(hashlib.sha256(current.encode()).hexdigest(),r['sha256']);self.assertEqual(current,body((self.phase/'before'/r['path']).read_text(),r['symbol']))

    def test_shared_native_primitive_and_commit_replacement_guard_unchanged(self):
        source=(ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text();replace=body(source,'func replaceCapturedItemData(')
        self.order(replace,['itemData.replace(on: target.object','replacedItemDataIDs.insert(target.id)'])
        commit=body(source,'func commit<T>(');self.assertIn('if !replacements.contains(item.id) && (old?.payloads != item.payloads',commit)
        self.assertIn('updatingKeys: replacements.map(\\.uuidString)',commit)
        self.assertNotIn('restoreHistoryItems',self.worker)

    def test_eight_reviewed_hunks_only_three_existing_production_files(self):
        self.assertEqual(len(CHANGES),8);sha=lambda p:hashlib.sha256(pre_native_title_write_bytes(ROOT/p)).hexdigest()
        files={str(p.relative_to(ROOT))for p in(ROOT/'replica/Sources').rglob('*')if p.is_file()};self.assertEqual(files,set(self.base['production']))
        self.assertEqual({p for p,h in self.base['production'].items()if sha(p)!=h},set(self.paths.values()))
        for key in self.paths:self.assertEqual(pre_native_edit_write(self.src[key]),self.before(key))
        for group in ['current_sources','shared_sources']:
            for p,h in self.proof[group].items():self.assertEqual(sha(p),h)
        for p,h in self.proof['shared_sources'].items():self.assertEqual(h,self.base['production'][p])
        for p in ['replica/Package.swift','package.json']:self.assertEqual(sha(p),self.base['other'][p])

    def test_full_generic_metadata_entity_di_and_nontext_routes_remain_open(self):
        self.assertFalse(self.proof['runtime_executed']);self.assertFalse(self.proof['full_function_migration_verified']);self.assertEqual(self.proof['new_difference_records'],0)
        for token in ['Generic Store','Ordinary/popover','mixing across','network runtime','3544dc']:self.assertTrue(any(token in r for r in self.proof['remaining']),token)
