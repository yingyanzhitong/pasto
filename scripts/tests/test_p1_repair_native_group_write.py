"""Source/Mach-O contracts for captured local group moves; no native execution."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from group_target_scope_contract import pre_group_target,pre_group_target_bytes
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment
from native_group_write_scope_contract import CHANGES,pre_native_group_write,pre_native_group_write_bytes

class NativeGroupWriteContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-105';cls.proof=json.loads((cls.phase/'native-group-write-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.src={Path(p).stem:pre_group_target((ROOT/p).read_text())for p in cls.proof['current_sources']};ns={};exec((ROOT/cls.proof['decoder']['path']).read_text().split("idx={r['address']",1)[0],ns);cls.ns=ns
    def original(self,a):
        r=next(r for r in self.proof['original_fragments']if r['address']==a);return original_fragment((ROOT/r['path']).read_text(),a[2:])
    def order(self,s,tokens):
        cursor=0
        for token in tokens:cursor=s.index(token,cursor)+len(token)
    def test_original_fragments_binary_decoder_and_reused_repository_proofs_bound(self):
        self.assertEqual(len(self.proof['original_fragments']),16)
        for r in self.proof['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for r in [self.proof['binary'],self.proof['decoder']]+self.proof['reused_evidence']:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_eighteen_real_branch_targets_bound(self):
        self.assertEqual(len(self.proof['ARM_calls']),18)
        for r in self.proof['ARM_calls']:
            pc=int(r['address'],16);b=self.ns['read'](pc,4);self.assertEqual(b.hex(),r['bytes']);w=int.from_bytes(b,'little');self.assertEqual(w&0x7c000000,0x14000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(pc+4*d,int(r['target'],16))
    def test_default_repository_writing_group_slot_is_real_format6_chain(self):
        self.assertEqual(len(self.proof['pointers']),2)
        for r in self.proof['pointers']:
            a=int(r['address'],16);v,chain=self.ns['reachable_pointer'](a);self.assertEqual(chain,r['chain']);self.assertEqual(self.ns['read'](a,8).hex(),r['bytes']);self.assertEqual(self.ns['base']+(v&((1<<36)-1)),int(r['target'],16))
        self.assertEqual(self.proof['pointers'][1]['address'],'0x100ecca78');self.assertEqual(self.proof['pointers'][1]['target'],'0x100364014')
    def test_five_actual_objc_selector_stubs_bound(self):
        self.assertEqual({r['selector']for r in self.proof['selectors']},{'list','rawType','setList:','displayOrderInPinboard','setDisplayOrderInPinboard:'})
        for r in self.proof['selectors']:
            self.assertEqual(self.ns['read'](int(r['stub_address'],16),20).hex(),r['bytes']);self.assertEqual(self.ns['read'](int(r['pointer_address'],16),8).hex(),r['pointer_bytes']);self.assertEqual(self.ns['read'](int(r['selector_address'],16),len(r['selector'])+1),r['selector'].encode()+b'\0')
    def test_tail_array_proven_as_fetch_destination_not_ghidra_input_alias(self):
        rows={r['address']:r for r in self.proof['ARM_words']};self.assertEqual(len(rows),13)
        for r in rows.values():self.assertEqual(self.ns['read'](int(r['address'],16),4).hex(),r['bytes']);self.assertEqual(int.from_bytes(bytes.fromhex(r['bytes']),'little'),int(r['word'],16))
        for a,w in [('36211c','0xaa0003fb'),('36217c','0xaa0003f3'),('362188','0xf90017f3'),('362348','0x9100a3f4'),('362368','0xf94017f3'),('3624f0','0x8b150e68')]:self.assertEqual(rows['0x100'+a]['word'],w)
    def test_menu_keeps_captured_entities_through_store_assignment(self):
        s=body(self.src['ReplicaUIController'],'func assignItems(_ items: [ClipboardRestoreItem]');self.assertIn('withExtendedLifetime(items)',s);self.assertIn('try store.assign(items: items, to: id)',s);self.assertNotIn('items.map',s);self.assertNotIn('visibleItems',s)
    def test_create_group_prefers_captured_sequence_over_legacy_ids(self):
        s=body(self.src['ReplicaUIController'],'func createPinboard(');self.order(s,['try store.createPinboard','if assignSelection','if let selectionItems','try store.assign(items: selectionItems, to: board.id)','else','try store.assign(orderedIDs: ids, to: board.id)','DispatchQueue.main.asyncAfter']);self.assertIn('0.2',s)
    def test_native_route_enters_same_repository_transaction_without_target_id_refetch(self):
        s=body(self.src['ClipboardStore'],'public func assign(items: [ClipboardRestoreItem]');native=s[s.index('try mutateInTransaction'):];self.order(native,['lists.list(identifier: pinboardID.uuidString)','repository.assignItems(items.map { $0.nativeObject! }','for item in destination','state.items[index] = item']);self.assertNotIn('prepareHistoryItems',native);self.assertNotIn('resolvedItem()',native);self.assertNotIn('Set(',native)
    def test_mixed_value_nil_and_empty_inputs_keep_explicit_legacy_boundaries(self):
        s=body(self.src['ClipboardStore'],'public func assign(items: [ClipboardRestoreItem]');self.order(s,['guard let pinboardID, items.allSatisfy({ $0.nativeObject != nil })','try assign(orderedIDs: items.map(\\.id), to: pinboardID)','return','guard !items.isEmpty else { return }','try mutateInTransaction'])
    def test_native_fetch_failure_returns_before_any_mutation(self):
        s=body(self.src['ClipboardListPersistence'],'func moveItems(');self.order(s,['guard var destination = try? context.fetch(itemRequest(for: pinboard)) else { return [] }','let moving = items.filter','item.setValue(pinboard']);self.assertNotIn('throws',s)
    def test_same_group_owner_filter_finishes_before_mutation_and_keeps_duplicates(self):
        s=body(self.src['ClipboardListPersistence'],'func moveItems(');self.order(s,['let moving = items.filter','value(forKey: "list")','int64Value == 2','return !owner.isEqual(pinboard)','for item in moving','item.setValue(pinboard']);self.assertNotIn('Set',s);self.assertNotIn('seen',s);self.assertNotIn('unique',s)
    def test_moves_insert_at_zero_then_reorder_result_only_if_order_differs(self):
        s=body(self.src['ClipboardListPersistence'],'func moveItems(');self.order(s,['for item in moving','item.setValue(pinboard, forKey: "list")','destination.insert(item, at: 0)','for (index, item) in destination.enumerated()','int64Value != Int64(index)','item.setValue(Int64(index)','return destination']);self.assertNotIn('Date(',s);self.assertNotIn('timestamp',s)
    def test_native_group_fetch_uses_owner_and_original_order(self):
        s=body(self.src['ClipboardListPersistence'],'func itemRequest(');self.order(s,['case 2:','NSSortDescriptor(key: "displayOrderInPinboard", ascending: true)','NSPredicate(format: "list == %@", list)'])
    def test_cache_projection_occurs_after_move_and_replaces_old_membership(self):
        s=body(self.src['ClipboardPersistence'],'func assignItems(_ items: [PastoItemEntity]');self.order(s,['lists.moveItems(items, to: pinboard)','destination.map','ClipboardPersistence.item(object)','item.pinboardIDs = [owner]','assignedItemIDs.formUnion','return values']);self.assertIn('item.pinboardIDs.removeAll()',s)
    def test_generic_commit_cannot_repeat_native_owner_or_order_mutations(self):
        s=body(self.src['ClipboardPersistence'],'func commit<T>(');self.order(s,['if !transaction.repository.assignedItemIDs.contains(item.id),','object.isInserted || old?.pinboardOwnerID','object.setValue(owner, forKey: "list")','if !transaction.repository.assignedItemIDs.contains(item.id) {','ClipboardItemOrderPersistence.update(item, on: object)'])
    def test_eight_surgical_hunks_exactly_reverse_to_before_and_shared_sources_unchanged(self):
        self.assertEqual(len(CHANGES),8);self.assertEqual({r[0]for r in CHANGES},set(self.proof['current_sources']))
        for p,h in self.proof['current_sources'].items():
            s=pre_group_target((ROOT/p).read_text());old=(self.phase/'before'/p).read_text();self.assertEqual(hashlib.sha256(s.encode()).hexdigest(),h);self.assertEqual(pre_native_group_write(s),old);self.assertEqual(pre_native_group_write(old),old)
        for p,h in self.proof['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_group_target_bytes(ROOT/p)).hexdigest(),h);self.assertEqual(h,self.base['production'][p])
    def test_no_unrelated_production_change_and_legacy_functions_preserved(self):
        current={str(p.relative_to(ROOT))for p in(ROOT/'replica/Sources').rglob('*')if p.is_file()};self.assertEqual(current,set(self.base['production']))
        for p,h in self.base['production'].items():self.assertEqual(hashlib.sha256(pre_native_group_write_bytes(ROOT/p)).hexdigest(),h)
        p='replica/Sources/PastoCore/ClipboardStore.swift'
        for marker in ['public func assign(ids:','public func assign(orderedIDs:','public func unassign(ids:','public func reorderItems(']:self.assertEqual(body((ROOT/p).read_text(),marker),body((self.phase/'before'/p).read_text(),marker))
    def test_finite_scope_does_not_claim_whole_group_or_function_migration(self):
        self.assertFalse(self.proof['full_function_migration_verified']);self.assertFalse(self.proof['runtime_executed']);self.assertEqual(self.proof['new_difference_records'],1);self.assertEqual(self.proof['contracts'][0]['function_id'],'Paste:0x1003620f8');self.assertEqual(len(self.proof['remaining']),4);self.assertIn('Actual ARM',self.proof['correction'])

if __name__=='__main__':unittest.main()
