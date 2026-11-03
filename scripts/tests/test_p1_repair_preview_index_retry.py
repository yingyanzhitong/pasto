"""Native collection preview retry: bound C/ARM and source checks, no app execution."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2]
from text_preview_creation_scope_contract import pre_text_preview_creation
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment
from preview_index_retry_scope_contract import CHANGES,pre_preview_index_retry
from entity_lookup_scope_contract import pre_entity_lookup_bytes
from native_preview_identity_scope_contract import pre_native_preview_identity

class PreviewIndexRetryContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-96';cls.proof=json.loads((cls.phase/'preview-index-retry-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text())
        cls.paths=dict(ui='replica/Sources/Pasto/UI/ReplicaUIController.swift',host='replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift')
        cls.src={k:(ROOT/p).read_text()for k,p in cls.paths.items()};cls.preview=body(cls.src['host'],'func previewItem(at index:')
        ns={};exec((ROOT/cls.proof['decoder']['path']).read_text().split("idx={r['address']",1)[0],ns);cls.ns=ns
    def original(self,a):
        r=next(r for r in self.proof['original_fragments']if r['address']==a);return original_fragment((ROOT/r['path']).read_text(),a[2:])
    def order(self,s,tokens):
        pos=[s.index(t)for t in tokens];self.assertEqual(pos,sorted(pos))

    def test_nine_original_fragments_binary_and_prior_geometry_inputs_bound(self):
        self.assertEqual(len(self.proof['original_fragments']),9)
        for r in self.proof['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for r in [self.proof['binary'],self.proof['decoder']]+self.proof['reused_evidence']:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])

    def test_nine_actual_calls_bind_optional_lookup_reveal_success_callback_and_retry(self):
        self.assertEqual(len(self.proof['ARM_calls']),9)
        for r in self.proof['ARM_calls']:
            pc=int(r['address'],16);b=self.ns['read'](pc,4);self.assertEqual(b.hex(),r['bytes']);w=int.from_bytes(b,'little');self.assertEqual(w&0x7c000000,0x14000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(pc+4*d,int(r['target'],16))
        calls=[r for r in self.proof['ARM_calls']if r['function']=='0x10022c9c4'];self.assertEqual(len(calls),2)

    def test_ARM_success_bit_and_weak_owner_gate_precede_same_index_retry(self):
        words={r['address']:r['bytes']for r in self.proof['ARM_words']}
        for a,b in words.items():self.assertEqual(self.ns['read'](int(a,16),4).hex(),b)
        self.assertEqual(words['0x10006be54'],'80010036');self.assertEqual(words['0x10006be64'],'000100b4');self.assertEqual(words['0x10006be58'],'f30302aa');self.assertEqual(words['0x10006be6c'],'e00313aa')
        s=self.original('0x10006be48');self.order(s,['if ((param_1 & 1) != 0)','_swift_unknownObjectWeakLoadStrong()','if (param_2 != 0)','FUN_10006bb3c(param_3)'])
        self.assertIn('FUN_10006be48(param_1,',self.original('0x100076544'))

    def test_original_resolves_optional_entity_and_visible_cell_before_toggle_or_reveal(self):
        s=self.original('0x10006bb3c');self.order(s,['FUN_1001b9698(','if (local_80[0] != 0)','_swift_beginAccess(unaff_x20 + _TtC7PasteUI14CollectionView::visibleCells','PreviewPopover::isDisplayed','objc_stub::close(self)','FUN_10002964c(local_80[0],uVar10)','FUN_10022c9c4(param_1,1,FUN_100076544'])
        self.assertIn('*(long *)(puVar7 + 0x18) = param_1',s)

    def test_host_uses_current_applied_index_and_optional_input_without_forcing_snapshot(self):
        self.order(self.preview,['guard let state, state.collectionOwner === self, window != nil','items.indices.contains(index)','items[index].restoreItem()','visibleSelectionAnchor(at: index, itemID: items[index].id)','present(input, anchor)','revealPrimaryCard(at: index, animated: true)'])
        for token in ['update(state:','drainCollectionSnapshots','tileCells()','renderedItem(','requiredItem(','requiredRestoreItem(','state.visibleItems','store.items','resolvedItem()']:self.assertNotIn(token,self.preview)

    def test_success_callback_holds_only_requested_index_and_reloads_weak_owner(self):
        callback=body(self.preview,'revealPrimaryCard(at: index, animated: true)')
        self.order(callback,['[weak self] success in','guard success else { return }','self?.previewItem(at: index, present: present)'])
        for token in ['input','itemID','UUID','state','ownerGeneration','asyncAfter','DispatchQueue','Task']:self.assertNotIn(token,callback)
        self.assertEqual(self.preview.count('items[index].restoreItem()'),1)

    def test_controller_native_route_uses_applied_index_and_hands_same_entity_to_popover(self):
        s=body(self.src['ui'],'private func showCollectionPreview(')
        self.order(s,['isPanelOrderedVisible, !isPanelClosing','loadedPanel as? ReplicaPanel','collection.window === replicaPanel','collection.appliedItems(for: state)','items.firstIndex(where: { $0.id == itemID })','collection.previewItem(at: index)','[weak self] input, anchor in','self.previewPopover = popover','if popover.isDisplayed','popover.close()','popover.show(','input: input','makePreviewContent(for: input)','return true'])
        for token in ['store.items','previewAnchor(','previewRegistry.f_10008747c','show(existing)','input.resolvedItem()','state.visibleItems']:self.assertNotIn(token,s)

    def test_space_enters_preview_by_last_selection_without_reading_DTO_content_first(self):
        selection=body(self.src['ui'],'private func previewSelection()');self.order(selection,['state.collectionSelectionSnapshot().orderedIDs.last','showCollectionPreview(itemID: id)'])
        key=body(self.src['ui'],'private func handleKey(');space=body(key,'if event.keyCode == 49, !isEditing');self.assertIn('previewSelection()',space)
        for token in ['appliedSelectionItems','appliedRestoreItems','resolvedItem','store.items']:self.assertNotIn(token,selection+space)
        self.assertIn('case 0x31:\n    return 2;',self.original('0x100219df4'))
        self.order(self.original('0x100069778'),['else if (uVar1 == 2)','thunk_FUN_10022b1cc()','FUN_10006bb3c(uVar18)'])

    def test_index_replacement_between_scroll_and_callback_is_not_old_entity_retry(self):
        # Separate source assertions bind the trace to a fresh items[index].restoreItem() on every retry.
        before=['A','B'];index=1;captured_old=before[index];after=['B','C'];self.assertEqual(after[index],'C');self.assertNotEqual(after[index],captured_old)
        self.assertIn('self?.previewItem(at: index, present: present)',self.preview);self.assertIn('let input = items[index].restoreItem()',self.preview)
        for success,owner in [(False,False),(False,True),(True,False),(True,True)]:
            expected=after[index]if success and owner else None
            retried=None
            if success:
                if owner:retried=after[index]
            self.assertEqual(retried,expected)

    def test_shared_geometry_keeps_immediate_intersection_and_animated_completion_contract(self):
        s=body(self.src['host'],'private func revealPrimaryCard(')
        self.order(s,['if card.intersects(clip.bounds)','scrollAnimator.setContentOffset(viewport.origin, in: clip, animated: animated)','completion?(true)','} else {','completion: completion)'])
        original=self.original('0x10022c9c4');self.order(original,['_CGRectIntersectsRect','if ((uVar3 & 1) == 0)','param_7,param_8','(*param_7)(1)'])
        self.assertNotIn('DispatchQueue',self.preview)

    def test_native_route_precedes_legacy_existing_window_and_legacy_body_otherwise_unchanged(self):
        marker='func showPreview(item: ClipboardItem, input:';now=body(pre_native_preview_identity(self.src['ui']),marker);before=body((self.phase/'before'/self.paths['ui']).read_text(),marker)
        prefix='\n        if case nil = input, showCollectionPreview(itemID: item.id) { return }';self.assertEqual(now.replace(prefix,'',1),before)
        self.order(now,['showCollectionPreview(itemID: item.id)','previewRegistry.f_10008747c','show(existing)'])
        for r in self.proof['unchanged_methods']:
            s=body(pre_text_preview_creation((ROOT/r['path']).read_text()),r['symbol']);self.assertEqual(hashlib.sha256(s.encode()).hexdigest(),r['sha256']);self.assertEqual(s,body((self.phase/'before'/r['path']).read_text(),r['symbol']))

    def test_three_reviewed_hunks_two_existing_files_and_shared_sources_unchanged(self):
        self.assertEqual(len(CHANGES),3);sha=lambda p:hashlib.sha256(pre_entity_lookup_bytes(ROOT/p)).hexdigest()
        files={str(p.relative_to(ROOT))for p in(ROOT/'replica/Sources').rglob('*')if p.is_file()};self.assertEqual(files,set(self.base['production']));self.assertEqual({p for p,h in self.base['production'].items()if sha(p)!=h},set(self.paths.values()))
        for key,p in self.paths.items():self.assertEqual(pre_preview_index_retry(self.src[key]),(self.phase/'before'/p).read_text())
        for group in ['current_sources','shared_sources']:
            for p,h in self.proof[group].items():self.assertEqual(sha(p),h)
        for p,h in self.proof['shared_sources'].items():self.assertEqual(h,self.base['production'][p])
        for p in ['replica/Package.swift','package.json']:self.assertEqual(sha(p),self.base['other'][p])

    def test_full_producer_ABI_reentrancy_and_legacy_boundaries_remain_explicit(self):
        self.assertFalse(self.proof['full_function_migration_verified']);self.assertFalse(self.proof['runtime_executed']);self.assertEqual(self.proof['new_difference_records'],0)
        for token in ['ownership/window','reentrancy','intersecting absent cell','Legacy','3544dc']:self.assertTrue(any(token in r for r in self.proof['remaining']),token)
