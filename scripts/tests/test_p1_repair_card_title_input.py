"""Captured entity for visible-card title commits; source/static checks only."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment
from card_title_input_scope_contract import CHANGES,pre_card_title_input
from preview_entity_changes_scope_contract import pre_preview_entity_changes,pre_preview_entity_changes_bytes

class CardTitleInputContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-93';cls.proof=json.loads((cls.phase/'card-title-input-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text())
        cls.paths=dict(handle='replica/Sources/PastoCore/ClipboardRestoreItem.swift',host='replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift',panel='replica/Sources/Pasto/UI/PanelViews.swift',title='replica/Sources/Pasto/UI/ReplicaCardTitle.swift')
        cls.src={k:pre_preview_entity_changes((ROOT/p).read_text())for k,p in cls.paths.items()}
        ns={};exec((ROOT/cls.proof['decoder']['path']).read_text().split("idx={r['address']",1)[0],ns);cls.ns=ns
    def before(self,k):return(self.phase/'before'/self.paths[k]).read_text()
    def original(self,a):
        r=next(r for r in self.proof['original_fragments']if r['address']==a);return original_fragment((ROOT/r['path']).read_text(),a[2:])
    def order(self,s,tokens):
        p=[s.index(t)for t in tokens];self.assertEqual(p,sorted(p))

    def test_ten_original_fragments_and_prior_native_title_evidence_bound(self):
        self.assertEqual(len(self.proof['original_fragments']),10)
        for r in self.proof['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for r in [self.proof['binary'],self.proof['decoder']]+self.proof['reused_evidence']:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])

    def test_five_real_provider_and_callback_machine_calls_bound(self):
        self.assertEqual(len(self.proof['ARM_calls']),5)
        for r in self.proof['ARM_calls']:
            pc=int(r['address'],16);b=self.ns['read'](pc,4);self.assertEqual(b.hex(),r['bytes']);w=int.from_bytes(b,'little');self.assertEqual(w&0x7c000000,0x14000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(pc+4*d,int(r['target'],16))

    def test_original_successful_cell_captures_resolved_entity_and_callback_forwards_it(self):
        factory=self.original('0x10006dd84');self.order(factory,['FUN_1001b9698(local_80,param_2','if (local_80[0] == 0)','*(long *)(puVar5 + 0x18) = local_80[0]','(*pcVar11)(FUN_100074dc4,puVar5)'])
        self.assertIn('FUN_10006e0dc',self.original('0x100074dc4'));self.assertIn('FUN_1003bae08(param_1,param_2,param_4)',self.original('0x10006e0dc'))
        for token in ['fetch','identifier','UUID','existingObject']:self.assertNotIn(token,self.original('0x10006e0dc'))

    def test_handle_identity_compares_actual_native_object_not_payload_or_uuid_only(self):
        s=body(self.src['handle'],'public func hasSameEntity(')
        self.assertEqual(s,'{\n        if let nativeObject { return nativeObject === other.nativeObject }\n        return other.nativeObject == nil && id == other.id\n    }')
        for token in ['resolvedItem','ClipboardPersistence','Data','value(forKey:','fetch(']:self.assertNotIn(token,s)

    def test_visible_tile_resolves_one_input_and_supplies_same_handle_to_cell(self):
        s=body(self.src['host'],'private func tileCells()')
        self.order(s,['for index in desired.sorted()','let input = items[index].requiredRestoreItem()','let item = input.resolvedItem()','ReplicaNativeCardCell(owner: self, state: state, item: item, input: input','cell.update(state: state, item: item, input: input','if needsInsertion { document.addSubview(cell) }'])
        self.assertEqual(s.count('requiredRestoreItem()'),1);self.assertEqual(s.count('resolvedItem()'),1)
        for token in ['renderedItem(at:','store.items','makeListCollection','searchItems(']:self.assertNotIn(token,s)

    def test_focus_refresh_uses_current_entry_handle_without_extra_projection(self):
        s=body(self.src['host'],'private func refreshCellRoots()')
        self.order(s,['items.indices.contains(index) && cell.itemID == items[index].id','let input = items[index].requiredRestoreItem()','cell.update(state: state, item: input.resolvedItem(), input: input'])
        self.assertEqual(s.count('resolvedItem()'),1);self.assertNotIn('renderedItem(at:',s)

    def test_cell_keeps_input_before_initial_root_and_members_are_initialized(self):
        self.assertIn('private var titleInput: ClipboardRestoreItem',self.src['host'])
        s=body(self.src['host'],'init(owner: ReplicaNativeCollectionHost, state: ReplicaUIState, item: ClipboardItem, input:')
        self.order(s,['self.item = item','titleInput = input','super.init(frame: .zero)','updateRoot()'])
        self.assertIn('self.side = side',s);self.assertIn('absoluteIndex = index',s);self.assertIn('renderedSelection = state.selection.contains(item.id)',s)

    def test_same_uuid_new_entity_invalidates_root_before_updating_captured_input(self):
        s=body(self.src['host'],'func update(state: ReplicaUIState, item: ClipboardItem, input:')
        self.order(s,['if self.state !== state || !titleInput.hasSameEntity(as: input) { renderingSignature = nil }','self.state = state','self.item = item','titleInput = input','updateRoot()'])
        root=body(self.src['host'],'private func updateRoot()')
        self.order(root,['guard renderingSignature != signature else { return }','renderingSignature = signature','hosting.rootView = AnyView(ReplicaClipboardCard('])
        self.assertIn('nativeInteractions: true, titleInput: titleInput)',root)

    def test_root_preserves_visual_id_and_selection_parameters_with_additional_input(self):
        root=body(self.src['host'],'private func updateRoot()')
        for token in ['selectionOverride: renderedSelection','dimmingOverride: owner?.isDimmed ?? true','.id(item.id)','.preferredColorScheme(state.preferredScheme)','.environment(\\.controlActiveState, active)']:self.assertIn(token,root)
        self.assertIn('var titleInput: ClipboardRestoreItem? = nil',self.src['panel'])
        labels=body(self.src['panel'],'private var headerLabels:')
        self.assertIn('ReplicaCardTitle(state: state, itemID: item.id, input: titleInput, title: cardTitle',body(labels,'if nativeInteractions'))
        self.assertIn('Text(cardTitle)',labels)

    def test_representable_passes_input_to_every_title_view_configuration(self):
        s=self.src['title'];self.assertIn('var input: ClipboardRestoreItem? = nil',s)
        self.assertIn('view.configure(state: state, itemID: itemID, input: input, title: title, font: font, textColor: textColor)',body(s,'func updateNSView('))
        self.assertIn('input: ClipboardRestoreItem? = nil, title: String',s)

    def test_real_commit_closure_keeps_handle_and_uses_existing_native_title_api(self):
        s=body(self.src['title'],'func configure(');self.order(s,['self.itemID = itemID','label.onCommitEditing = { [weak state] title in','guard let state else { return }','if let input','state.store.updateItem(input, title: title)','} else {','state.store.updateItem(id: itemID, title: title, text: nil)'])
        for token in ['store.items','appliedRestoreItems(','UUID()','Date()','fetch(','observeItem(']:self.assertNotIn(token,s)
        store=(ROOT/'replica/Sources/PastoCore/ClipboardStore.swift').read_text();self.assertIn('ClipboardItemTitlePersistence.update(item, on: object)',body(store,'public func updateItem(_ input:'))

    def test_existing_focus_hit_testing_rename_trigger_and_managed_readers_unchanged(self):
        for r in self.proof['unchanged_methods']:
            s=body((ROOT/r['path']).read_text(),r['symbol']);self.assertEqual(hashlib.sha256(s.encode()).hexdigest(),r['sha256']);self.assertEqual(s,body((self.phase/'before'/r['path']).read_text(),r['symbol']))
        trigger=body(self.src['host'],'func renameSelection(');self.assertIn('cell.beginTitleEditing()',trigger)
        begin=body(self.src['host'],'func beginTitleEditing()');self.assertIn('title.beginEditing()',begin)

    def test_header_and_text_observers_have_different_delete_policy_and_header_was_not_changed(self):
        self.assertIn('Combine::Published::_set_subscript',self.original('0x1003c2780'));self.assertNotIn('isDeleted',self.original('0x1003c2780'))
        self.assertIn('objc_stub::isDeleted(param_1)',self.original('0x1003c04f0'))
        p='replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift';self.assertEqual(pre_preview_entity_changes_bytes(ROOT/p),(self.phase/'before'/p).read_bytes())
        self.assertTrue(any('Header model3c2780' in r for r in self.proof['remaining']))

    def test_fifteen_reviewed_hunks_four_existing_files_only(self):
        self.assertEqual(len(CHANGES),15);sha=lambda p:hashlib.sha256(pre_preview_entity_changes_bytes(ROOT/p)).hexdigest()
        files={str(p.relative_to(ROOT))for p in(ROOT/'replica/Sources').rglob('*')if p.is_file()};self.assertEqual(files,set(self.base['production']));self.assertEqual({p for p,h in self.base['production'].items()if sha(p)!=h},set(self.paths.values()))
        for key in self.paths:self.assertEqual(pre_card_title_input(self.src[key]),self.before(key))
        for group in ['current_sources','shared_sources']:
            for p,h in self.proof[group].items():self.assertEqual(sha(p),h)
        for p,h in self.proof['shared_sources'].items():self.assertEqual(h,self.base['production'][p])
        for p in ['replica/Package.swift','package.json']:self.assertEqual(sha(p),self.base['other'][p])

    def test_optional_unavailable_parent_branch_and_full_caller_remain_unclosed(self):
        self.assertFalse(self.proof['runtime_executed']);self.assertFalse(self.proof['full_function_migration_verified']);self.assertEqual(self.proof['new_difference_records'],0)
        factory=self.original('0x10006dd84');self.assertIn('if (local_80[0] == 0)',factory);self.assertIn('FUN_1003de76c(0)',factory)
        for token in ['unavailable-cell','producer/vtable','Legacy/card','Projection/decoder','3544dc']:self.assertTrue(any(token in r for r in self.proof['remaining']),token)
