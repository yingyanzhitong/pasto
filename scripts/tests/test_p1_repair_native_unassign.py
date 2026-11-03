from native_restore_only_scope_contract import pre_native_restore_only
"""Native group unassign input, owner/orphan and compatibility-write contracts; static only."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from native_group_creation_result_scope_contract import pre_native_group_creation_result
from list_remove_menu_scope_contract import pre_list_remove_menu
from test_offline_p0_contracts import body
from native_unassign_scope_contract import CHANGES,pre_native_unassign,pre_native_unassign_bytes

class NativeUnassignContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-109';cls.proof=json.loads((cls.phase/'native-unassign-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.src={Path(p).stem:pre_native_restore_only((ROOT/p).read_text())for p in cls.proof['current_sources']};ns={};exec((ROOT/cls.proof['decoder']['path']).read_text().split("idx={r['address']",1)[0],ns);cls.ns=ns
    def order(self,s,tokens):
        cursor=0
        for t in tokens:cursor=s.index(t,cursor)+len(t)
    def test_seventeen_original_fragments_and_reused_native_proofs_bound(self):
        self.assertEqual(len(self.proof['original_fragments']),17)
        for r in self.proof['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for r in [self.proof['binary'],self.proof['decoder']]+self.proof['reused_evidence']:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_thirteen_actual_native_branches_bound(self):
        self.assertEqual(len(self.proof['ARM_calls']),13)
        for r in self.proof['ARM_calls']:
            pc=int(r['address'],16);b=self.ns['read'](pc,4);self.assertEqual(b.hex(),r['bytes']);w=int.from_bytes(b,'little');self.assertEqual(w&0x7c000000,0x14000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(pc+d*4,int(r['target'],16))
    def test_preview_VM_and_actual_writing_plus48_pointers_bound(self):
        self.assertEqual([(r['address'],r['target'])for r in self.proof['pointers']],[('0x100fc2e98','0x1003c3894'),('0x100ecca98','0x100364094')])
        for r in self.proof['pointers']:
            a=int(r['address'],16);v,chain=self.ns['reachable_pointer'](a);self.assertEqual(chain,r['chain']);self.assertEqual(self.ns['read'](a,8).hex(),r['bytes']);self.assertEqual(self.ns['base']+(v&((1<<36)-1)),int(r['target'],16))
    def test_six_real_ownership_timestamp_and_delete_selectors_bound(self):
        self.assertEqual({r['selector']for r in self.proof['selectors']},{'list','rawType','setList:','timestamp','managedObjectContext','deleteObject:'})
        for r in self.proof['selectors']:
            self.assertEqual(self.ns['read'](int(r['stub_address'],16),20).hex(),r['bytes']);self.assertEqual(self.ns['read'](int(r['pointer_address'],16),8).hex(),r['pointer_bytes']);self.assertEqual(self.ns['read'](int(r['selector_address'],16),len(r['selector'])+1),r['selector'].encode()+b'\0')
    def test_ten_actual_owner_orphan_and_own_context_words_bound(self):
        self.assertEqual(len(self.proof['ARM_words']),10)
        for r in self.proof['ARM_words']:self.assertEqual(self.ns['read'](int(r['address'],16),4).hex(),r['bytes']);self.assertEqual(int.from_bytes(bytes.fromhex(r['bytes']),'little'),int(r['word'],16))
    def test_complete_original_call_inventories_have_no_order_setter(self):
        self.assertEqual(len(self.proof['direct_call_inventories']),3)
        for r in self.proof['direct_call_inventories']:
            rows=[]
            for pc in range(int(r['function'],16),int(r['end'],16),4):
                w=int.from_bytes(self.ns['read'](pc,4),'little')
                if w&0xfc000000!=0x94000000:continue
                d=w&0x3ffffff
                if d&0x2000000:d-=0x4000000
                rows.append(dict(address=hex(pc),bytes=self.ns['read'](pc,4).hex(),target=hex(pc+d*4)))
            self.assertEqual(rows,r['calls']);self.assertNotIn('0x100c0b640',[x['target']for x in rows])
    def test_only_nil_target_with_all_native_items_enters_native_unassign(self):
        s=body(self.src['ClipboardStore'],'private func assign(items: [ClipboardRestoreItem], pinboardID:');self.order(s,['if pinboardID == nil, items.allSatisfy({ $0.nativeObject != nil })','try unassignNative(items: items)','return','guard let pinboardID, items.allSatisfy','try assign(orderedIDs: items.map(\\.id), to: pinboardID)'])
    def test_native_targets_keep_input_order_and_objects_without_UUID_resolution(self):
        s=body(self.src['ClipboardStore'],'private func unassignNative(');self.order(s,['try mutateInTransaction','repository.unassignItems(items.map { (id: $0.id, object: $0.nativeObject!) })','for target in affected'])
        for t in ['prepareHistoryItems','Set(items','items.sorted','resolvedItem()','restoringItemIDs:']:self.assertNotIn(t,s)
    def test_ownerless_and_non_group_items_exit_before_orphan_delete(self):
        s=body(self.src['ClipboardPersistence'],'func unassignItems(');self.order(s,['for target in targets','let object = target.object','guard let owner = object.value(forKey: "list")','int64Value == 2 else { continue }','if let currentOwner','if object.value(forKey: "timestamp") == nil','object.managedObjectContext?.delete(object)'])
    def test_current_owner_must_equal_target_before_clearing_relationship(self):
        s=body(self.src['ClipboardPersistence'],'func unassignItems(');self.order(s,['if let currentOwner = object.value(forKey: "list")','currentOwner.isEqual(owner)','object.setValue(nil, forKey: "list")','if object.value(forKey: "timestamp") == nil, object.value(forKey: "list") == nil'])
    def test_orphan_deletes_same_object_through_its_own_context(self):
        s=body(self.src['ClipboardPersistence'],'func unassignItems(');self.order(s,['if object.value(forKey: "timestamp") == nil, object.value(forKey: "list") == nil','object.managedObjectContext?.delete(object)','if object.isDeleted { alreadyDeletedItemIDs.insert(target.id) }']);self.assertNotIn('context.delete(object)',s);self.assertNotIn('context.delete(target',s)
    def test_business_sequence_never_deduplicates_and_does_not_set_time_or_order(self):
        s=body(self.src['ClipboardPersistence'],'func unassignItems(')
        for t in ['Set(','seen','sorted','targets.filter','targets.reversed','Date(','setTimestamp','displayOrderInPinboard','forKey: "timestamp")\n','forKey: "updatedAt"']:self.assertNotIn(t,s)
        self.assertEqual(s.count('object.setValue('),1);self.assertIn('affected.append(target)',s)
    def test_native_pass_finishes_before_any_compatibility_archive_decoder(self):
        s=body(self.src['ClipboardStore'],'private func unassignNative(');self.order(s,['let affected = transaction.repository.unassignItems','for target in affected','else { item = try ClipboardPersistence.item(target.object) }']);core=body(self.src['ClipboardPersistence'],'func unassignItems(')
        for t in ['decode','ClipboardItem','payload','contentForComparison','JSON','encode(']:self.assertNotIn(t,core)
    def test_deleted_objects_removed_before_live_cache_projection(self):
        s=body(self.src['ClipboardStore'],'private func unassignNative(');self.order(s,['if target.object.isDeleted','state.items.removeAll { $0.id == target.id }','continue','let index = state.items.firstIndex','var item: ClipboardItem'])
    def test_existing_cache_reused_and_missing_cache_is_explicit_decoder_adapter(self):
        s=body(self.src['ClipboardStore'],'private func unassignNative(');self.order(s,['if let index { item = state.items[index] }','else { item = try ClipboardPersistence.item(target.object) }','target.object.value(forKey: "list")','item.pinboardOwnerID = ownerID','item.pinboardIDs = [ownerID]','item.pinboardOwnerID = nil','item.pinboardIDs.removeAll()','ClipboardItemOrderPersistence.project(&item, from: target.object)','state.items[index] = item']);self.assertNotIn('Date(',s)
    def test_all_processed_native_ids_marked_for_relation_order_and_field_preservation(self):
        s=body(self.src['ClipboardPersistence'],'func unassignItems(');self.order(s,['assignedItemIDs.insert(target.id)','unassignedItemIDs.insert(target.id)','affected.append(target)']);self.assertIn('private(set) var alreadyDeletedItemIDs: Set<UUID> = []',self.src['ClipboardPersistence']);self.assertIn('private(set) var unassignedItemIDs: Set<UUID> = []',self.src['ClipboardPersistence'])
    def test_compatibility_apply_serializes_blob_then_returns_before_native_field_writes(self):
        s=body(self.src['ClipboardPersistence'],'func commit<T>(');a=s.index('if transaction.repository.unassignedItemIDs.contains(item.id)');b=s.index('if !sourced.contains(item.id)',a);part=s[a:b];self.order(part,['if old.map(contentForComparison) != contentForComparison(item)','object.setValue(try encode(content(item)), forKey: "content")','return'])
        for t in ['itemData.replace','sources.apply','rawPreview','timestamp','updatedAt','createdAt','checksum','forKey: "list"','ClipboardItemOrderPersistence.update']:self.assertNotIn(t,part)
    def test_already_deleted_ids_excluded_before_generic_fetch_and_delete(self):
        self.assertIn('updatingKeys: [String] = [], alreadyDeletedKeys: Set<String> = []',self.src['ClipboardPersistence']);s=body(self.src['ClipboardPersistence'],'func update<T: Equatable>');self.order(s,['orderedRemoved += previous.map(key)','orderedRemoved.removeAll { alreadyDeletedKeys.contains($0) }','let keys = changed.map(key) + orderedRemoved','guard !keys.isEmpty','try fetchObjects(entity, keys: keys)','for id in orderedRemoved'])
    def test_deletion_exclusion_is_passed_only_to_Item_compatibility_update(self):
        s=self.src['ClipboardPersistence'];self.assertEqual(s.count('alreadyDeletedKeys:'),2);start=s.index('transaction.repository.update(state.items');end=s.index('if !sourced.contains',start);self.assertIn('entity: "Item"',s[start:end]);self.assertIn('alreadyDeletedKeys: Set(transaction.repository.alreadyDeletedItemIDs.map(\\.uuidString))',s[start:end])
    def test_preview_current_handle_nil_consumer_now_reaches_native_branch_without_UI_change(self):
        p='replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift';s=(ROOT/p).read_text();self.assertIn('state.store.assign(items: [current], to: nil)',s);self.assertEqual(hashlib.sha256(pre_native_group_creation_result((ROOT/p).read_text()).encode()).hexdigest(),self.base['production'][p]);root=body(self.src['ClipboardStore'],'private func assign(items: [ClipboardRestoreItem], pinboardID:');self.assertIn('try unassignNative(items: items)',root)
    def test_seven_existing_assign_restore_and_legacy_delete_methods_unchanged(self):
        self.assertEqual(len(self.proof['unchanged_methods']),7)
        for r in self.proof['unchanged_methods']:
            s=body((ROOT/r['path']).read_text(),r['symbol']);self.assertEqual(s,body((self.phase/'before'/r['path']).read_text(),r['symbol']));self.assertEqual(hashlib.sha256(s.encode()).hexdigest(),r['sha256'])
    def test_eight_hunks_exactly_reverse_and_shared_sources_unchanged(self):
        self.assertEqual(len(CHANGES),8);self.assertEqual({r[0]for r in CHANGES},set(self.proof['current_sources']));files={str(p.relative_to(ROOT))for p in(ROOT/'replica/Sources').rglob('*')if p.is_file()};self.assertEqual(files,set(self.base['production']))
        for p,h in self.base['production'].items():self.assertEqual(hashlib.sha256(pre_native_unassign_bytes(ROOT/p)).hexdigest(),h)
        for p,h in self.proof['current_sources'].items():self.assertEqual(hashlib.sha256(pre_native_group_creation_result((ROOT/p).read_text()).encode()).hexdigest(),h);self.assertEqual(pre_native_unassign(pre_native_unassign((ROOT/p).read_text())),(self.phase/'before'/p).read_text())
        for p,h in self.proof['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_list_remove_menu((ROOT/p).read_text()).encode()).hexdigest(),h);self.assertEqual(h,self.base['production'][p])
    def test_two_finite_records_share_one_unassign_group_and_full_contract_remains_open(self):
        self.assertEqual(self.proof['new_difference_records'],2);self.assertEqual(self.proof['new_conservative_groups'],1);self.assertEqual({r['function_id']for r in self.proof['contracts']},{'Paste:0x100363a3c','Paste:0x10036299c'});self.assertFalse(self.proof['full_function_migration_verified']);self.assertFalse(self.proof['runtime_executed']);self.assertEqual(len(self.proof['remaining']),4)
    def test_cache_decoder_blob_performance_and_full_errors_are_not_falsely_certified(self):
        self.assertIn('Cache-miss survivors still require the existing DTO decoder',self.proof['remaining'][0]);self.assertIn('Compatibility content blob is still encoded',self.proof['remaining'][1]);self.assertIn('nil receiver is a no-op',self.proof['correction'])

if __name__=='__main__':unittest.main()
