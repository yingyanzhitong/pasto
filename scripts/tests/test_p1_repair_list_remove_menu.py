"""Captured list-menu removal and local-unshared eligibility; source/Mach-O only."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from native_tab_list_delivery_scope_contract import pre_native_tab_list_delivery
from native_group_creation_result_scope_contract import pre_native_group_creation_result
from list_pin_menu_topology_scope_contract import pre_list_pin_menu_topology
from test_offline_p0_contracts import body
from list_remove_menu_scope_contract import CHANGES,pre_list_remove_menu

class ListRemoveMenuContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-110';cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.proof=json.loads((cls.phase/'list-remove-menu-contract.json').read_text());cls.src={Path(p).stem:pre_list_pin_menu_topology((ROOT/p).read_text())for p in cls.proof['current_sources']};cls.ns={};exec((ROOT/cls.proof['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.ns)
    def test_original_fragments_binary_and_decoder_are_current(self):
        self.assertEqual(len(self.proof['original_fragments']),20)
        for r in self.proof['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for r in [self.proof['binary'],self.proof['decoder']]:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_sixteen_actual_branches_bound(self):
        self.assertEqual(len(self.proof['ARM_calls']),16)
        for r in self.proof['ARM_calls']:
            pc=int(r['address'],16);b=self.ns['read'](pc,4);self.assertEqual(b.hex(),r['bytes']);w=int.from_bytes(b,'little');self.assertEqual(w&0x7c000000,0x14000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(pc+d*4,int(r['target'],16))
    def test_stack_callback_input_and_context_words_match_original(self):
        self.assertEqual(len(self.proof['ARM_words']),18)
        for r in self.proof['ARM_words']:self.assertEqual(self.ns['read'](int(r['address'],16),4).hex(),r['bytes']);self.assertEqual(int.from_bytes(bytes.fromhex(r['bytes']),'little'),int(r['word'],16))
    def test_actual_predicate_and_remove_thunk_ADRP_targets_bound(self):
        self.assertEqual({r['target']for r in self.proof['ADRP_targets']},{'0x10009f574','0x1003ba374','0x1003ba390'})
        for r in self.proof['ADRP_targets']:
            a=int(r['address'],16);data=self.ns['read'](a,8);self.assertEqual(data.hex(),r['bytes']);w=int.from_bytes(data[:4],'little');v=int.from_bytes(data[4:],'little');imm=((w>>5)&0x7ffff)*4+((w>>29)&3)
            if imm&(1<<20):imm-=1<<21
            self.assertEqual((a&~4095)+(imm<<12)+((v>>10)&0xfff),int(r['target'],16))
    def test_one_build_time_input_shared_by_add_create_and_remove(self):
        s=body(self.src['PanelViews'],'@ViewBuilder private var contextMenu:');self.assertEqual(s.count('contextMenuRestoreItems()'),1);self.assertLess(s.index('let groupItems ='),s.index('Menu("添加到 Pasto")'));self.assertIn('state.assignItems(groupItems, to: target)',s);self.assertIn('selectionItems: groupItems',s);self.assertIn('state.assignItems(groupItems, to: nil)',s)
    def test_remove_all_click_does_not_re_read_selection_or_resolve_UUIDs(self):
        s=body(self.src['PanelViews'],'@ViewBuilder private var contextMenu:');a=s.index('if state.canUnassignItems(groupItems)');b=s.index('Button("添加到 Pasto Stack")',a);part=s[a:b];self.assertIn('Button("从所有 Pasto 移除") { state.assignItems(groupItems, to: nil) }',part)
        for t in ['assignSelection','state.selection','item.pinboardIDs','resolvedItem','map(','Set(']:self.assertNotIn(t,part)
    def test_remove_all_gate_independent_of_clicked_card_legacy_membership(self):
        s=body(self.src['PanelViews'],'@ViewBuilder private var contextMenu:');a=s.index('if !item.pinboardIDs.isEmpty, let board');b=s.index('if state.canUnassignItems');self.assertIn('\n            }\n            ',s[a:b]);self.assertIn('state.store.unassign(ids: state.selection, from: board)',s[a:b])
    def test_native_owner_boolean_reads_only_relationship_and_type(self):
        s=body(self.src['ClipboardRestoreItem'],'public func hasNativePinboardOwner()');self.assertIn('guard let object = nativeObject else { return nil }',s);self.assertIn('guard let owner = object.value(forKey: "list") as? NSManagedObject else { return false }',s);self.assertIn('int64Value == 2',s)
        for t in ['rawAttributes','rawPreview','resolvedItem','ClipboardPersistence','decode','payload','isDeleted','Set(']:self.assertNotIn(t,s)
    def test_history_nonempty_contains_conditions_and_legacy_adapter_explicit(self):
        s=body(self.src['ReplicaUIController'],'func canUnassignItems(');self.assertIn('let hasPinboardOwner = items.contains',s);self.assertIn('$0.hasNativePinboardOwner() ?? !$0.resolvedItem().pinboardIDs.isEmpty',s);self.assertIn('return pinboardID == nil && !showDeleted && !items.isEmpty && hasPinboardOwner',s);self.assertLess(s.index('items.contains'),s.index('return pinboardID'));self.assertNotIn('isCollectionSearchQueryEmpty',s)
    def test_history_context_mapping_does_not_depend_on_query(self):
        s=body(self.src['ReplicaUIController'],'private func installListSelectionDelivery()');self.assertIn('identifier == ClipboardStore.historyListIdentifier',s);self.assertIn('id = nil',s);self.assertIn('case .history: id = nil',s);s=body(self.src['ReplicaUIController'],'private func applySelectedList(');self.assertIn('pinboardID = id',s);self.assertIn('showDeleted = false',s)
    def test_local_group_schema_has_no_share_metadata(self):
        s=body((ROOT/'replica/Sources/PastoCore/ClipboardListPersistence.swift').read_text(),'static func addEntities(');self.assertIn('let list = entity("ListEntity")',s);self.assertIn('let metadata = entity("ListMetadataEntity")',s);self.assertIn('model.entities += [list, metadata]',s)
        for t in ['shareRecordData','CKShare','cloudKitZoneOwnerName']:self.assertNotIn(t,s)
    def test_native_assignment_consumer_and_repository_unchanged(self):
        for p,h in self.proof['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_native_group_creation_result((ROOT/p).read_text()).encode()).hexdigest(),h);self.assertEqual(h,self.base['production'][p])
        s=body((ROOT/'replica/Sources/PastoCore/ClipboardStore.swift').read_text(),'private func assign(items: [ClipboardRestoreItem], pinboardID:');self.assertIn('try unassignNative(items: items)',s)
    def test_existing_methods_unchanged(self):
        self.assertEqual(len(self.proof['unchanged_methods']),6)
        for r in self.proof['unchanged_methods']:self.assertEqual(hashlib.sha256(body(pre_native_tab_list_delivery((ROOT/r['path']).read_text()),r['symbol']).encode()).hexdigest(),r['sha256'])
    def test_five_exact_source_hunks_reverse_without_unrelated_changes(self):
        self.assertEqual(len(CHANGES),5)
        for p,h in self.base['production'].items():
            data=(ROOT/p).read_bytes();s=pre_list_remove_menu(pre_list_pin_menu_topology(data.decode()))if p.endswith('.swift')else None
            self.assertEqual(hashlib.sha256(s.encode()if s is not None else data).hexdigest(),h)
        for p,h in self.proof['current_sources'].items():self.assertEqual(hashlib.sha256(pre_list_pin_menu_topology((ROOT/p).read_text()).encode()).hexdigest(),h)
    def test_target_scoped_remove_and_full_parent_contracts_remain_open(self):
        self.assertEqual(len(self.proof['remaining']),4);self.assertIn('legacy target-scoped UUID',self.proof['remaining'][0]);self.assertIn('specialized only to local unshared',self.proof['remaining'][1]);self.assertEqual(len(self.proof['contracts']),2)

if __name__=='__main__':unittest.main()
