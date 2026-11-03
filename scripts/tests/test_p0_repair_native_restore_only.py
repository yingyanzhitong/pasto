"""Native recency-only save: field mutation counterexamples and actual source/ARM binding."""
from postwrite_restore_scope_contract import pre_postwrite_restore
from pathlib import Path
import hashlib,itertools,json,re,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from save_failure_rollback_scope_contract import pre_save_failure_rollback
from test_offline_p0_contracts import body
from native_restore_only_scope_contract import CHANGES,pre_native_restore_only

class NativeRestoreOnlyContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-116';cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.proof=json.loads((cls.phase/'native-restore-only-contract.json').read_text());cls.path='replica/Sources/PastoCore/ClipboardPersistence.swift';cls.src=(ROOT/cls.path).read_text();cls.commit=body(cls.src,'func commit<T>(');cls.ns={};exec((ROOT/cls.proof['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.ns)
        cls.fast=body(cls.commit,'if !transaction.nativeHistoryRestoreTargets.isEmpty');cls.loop=body(cls.fast,'for item in state.items');cls.fields=re.findall(r'^    public var (\w+)(?:: [^\n{]+| = [^\n{]+)$',body((ROOT/'replica/Sources/PastoCore/Models.swift').read_text(),'public struct ClipboardItem:'),re.M)
        cls.mask=re.findall(r'restored\.(\w+) = item\.(\w+)',cls.loop)
    def order(self,s,tokens):
        cursor=0
        for t in tokens:cursor=s.index(t,cursor)+len(t)
    def test_original_eight_fragments_and_reused_native_timestamp_contracts_bound(self):
        self.assertEqual(len(self.proof['original_fragments']),8)
        for r in self.proof['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for p,h in self.proof['reused_evidence'].items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),h)
    def test_binary_and_decoder_are_actual_reviewed_inputs(self):
        for r in [self.proof['binary'],self.proof['decoder']]:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_complete_original_history_function_range_and_26_BLs_bound(self):
        inv=self.proof['ARM_call_inventory'];a=int(inv['function'],16);e=int(inv['end'],16);self.assertEqual(hashlib.sha256(self.ns['read'](a,e-a)).hexdigest(),inv['sha256']);actual=[]
        for pc in range(a,e,4):
            data=self.ns['read'](pc,4);w=int.from_bytes(data,'little')
            if w&0xfc000000!=0x94000000:continue
            d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            actual.append((hex(pc),data.hex(),hex(pc+d*4)))
        self.assertEqual(actual,[(r['address'],r['bytes'],r['target'])for r in inv['calls']]);self.assertEqual(len(actual),26)
    def test_original_reverse_Date_timestamp_cleanup_refresh_call_order(self):
        calls=self.proof['ARM_call_inventory']['calls'];targets=[r['target']for r in calls];expected=['0x100364108','0x100bf4c44','0x100c0e2c0','0x1003293c4','0x100363810','0x1003646ec','0x100328bb4','0x100c08be0'];self.assertEqual([targets.index(t)for t in expected],sorted(targets.index(t)for t in expected))
    def test_real_timestamp_selector_decoded_from_chained_pointer(self):
        r=self.proof['selector'];a=int(r['pointer'],16);v,c=self.ns['reachable_pointer'](a);self.assertEqual(c,r['chain']);self.assertEqual(self.ns['read'](a,8).hex(),r['pointer_bytes']);t=self.ns['base']+(v&((1<<36)-1));o=self.ns['offset'](t);self.assertEqual(self.ns['raw'][o:self.ns['raw'].index(b'\0',o)].decode(),'setTimestamp:')
    def test_only_native_preparation_registers_captured_targets(self):
        s=body(self.src,'func prepareHistoryRestore(targets:');self.assertIn('Transaction(context: context, nativeHistoryRestoreTargets: targets)',s);s=body(self.src,'func prepareHistoryRestore(ids:');self.assertIn('Transaction(context: context)',s);self.assertNotIn('nativeHistoryRestoreTargets:',s)
    def test_transaction_retains_targets_and_legacy_initializer_default_is_empty(self):
        self.assertIn('let nativeHistoryRestoreTargets: [(id: UUID, object: NSManagedObject)]',self.src);self.assertIn('nativeHistoryRestoreTargets: [(id: UUID, object: NSManagedObject)] = []',self.src);self.assertIn('self.nativeHistoryRestoreTargets = nativeHistoryRestoreTargets',self.src)
    def test_fast_path_requires_target_and_existing_baseline_before_mutating_anything(self):
        self.order(self.loop,['guard let object = targets[item.id], let old = before[item.id] else { continue }','var restored = old','guard restored == item else { continue }','object.setValue','restoredMetadataOnly.insert(item.id)']);self.assertNotIn('resolvedItem',self.loop)
    def test_mask_is_exactly_three_recency_fields_then_full_Equatable_comparison(self):
        self.assertEqual(self.mask,[('createdAt','createdAt'),('updatedAt','updatedAt'),('isInHistory','isInHistory')]);self.assertEqual(self.loop.count('guard restored == item'),1);self.assertNotIn('contentForComparison',self.fast);self.assertNotIn('pinboardOrder =',self.fast)
    def classify(self,old,new):
        copy=dict(old)
        for dest,source in self.mask:copy[dest]=new[source]
        return copy==new
    def test_every_combination_of_only_recency_changes_is_accepted(self):
        old={f:('baseline',f)for f in self.fields};self.assertEqual(len(self.fields),25)
        for bits in itertools.product([False,True],repeat=3):
            new=dict(old)
            for (f,_),changed in zip(self.mask,bits):
                if changed:new[f]=('changed',f)
            self.assertTrue(self.classify(old,new),bits)
    def test_every_other_stored_field_change_rejects_fast_path_even_with_recency_changes(self):
        old={f:('baseline',f)for f in self.fields};masked={f for f,_ in self.mask}
        for f in set(self.fields)-masked:
            new=dict(old);new.update({k:('now',k)for k in masked});new[f]=('edit',f);self.assertFalse(self.classify(old,new),f)
        self.assertTrue({'payloads','rawPreview','pinboardOrder','sourceApplicationSnapshot','hasSourceApplicationSnapshot','isDeleted','nativeIdentifier'}.issubset(self.fields))
    def test_native_overlay_writes_only_three_existing_compatibility_columns(self):
        self.assertEqual(re.findall(r'object.setValue\(.*?forKey: "([^"]+)"\)',self.loop),['localCreatedAt','updatedAt','inHistory'])
        for t in ['fetch','decode','encode','"data"','"rawPreview"','"list"','displayOrderInPinboard','"timestamp"','insertNewObject','delete(']:self.assertNotIn(t,self.loop)
    def test_missing_data_and_stale_preview_order_are_not_value_replayed_in_restore_only_overlay(self):
        fake={'data':None,'rawPreview':'native-newer','displayOrderInPinboard':19,'timestamp':'native-now','list':'native-owner'};initial=dict(fake);writes=re.findall(r'if old\.(\w+) != item\.\1 \{ object.setValue\(item\.\1, forKey: "([^"]+)"\) \}',self.loop);self.assertEqual(len(writes),3)
        old={f:('old',f)for f,_ in writes};new={f:('new',f)for f,_ in writes}
        for f,k in writes:
            if old[f]!=new[f]:fake[k]=new[f]
        for k,v in initial.items():self.assertEqual(fake[k],v,k)
    def test_filtered_items_removed_from_both_sides_never_invent_deletion(self):
        self.assertIn('state.items.filter { !restoredMetadataOnly.contains($0.id) }',self.commit);self.assertIn('previousItems.filter { !restoredMetadataOnly.contains($0.id) && !nativeRestoreWithoutValue.contains($0.id) }',self.commit);self.assertIn('update(itemValues, previous: itemPrevious, entity: "Item"',self.commit)
        for before,after,skip in [(['a','b'],['a','b'],{'a'}),(['a','b'],['a'],{'a'}),(['a'],['a','b'],{'a'}),(['a','b'],['b'],set())]:
            left={x for x in before if x not in skip};right={x for x in after if x not in skip};self.assertEqual(left-right,set(before)-set(after))
    def test_missing_value_restore_not_misclassified_as_removed_from_previous(self):
        self.assertIn('nativeRestoreWithoutValue = Set(targets.keys).subtracting(state.items.map(\.id))',self.fast)
        self.assertIn('!nativeRestoreWithoutValue.contains($0.id)',self.commit)
        for previous in [set(), {'restored'}, {'restored','other'}]:
            state=set();targets={'restored'};missing=targets-state
            old_removed=previous-state;new_removed=(previous-missing)-state
            self.assertNotIn('restored',new_removed)
            self.assertEqual(new_removed,old_removed-{'restored'})
            if 'restored' in previous:self.assertIn('restored',old_removed)
    def test_missing_value_gate_does_not_swallow_non_target_removal_or_real_edit(self):
        before={'restored','edited','deleted'};after={'edited'};targets={'restored','edited'}
        missing=targets-after;item_previous=before-missing
        self.assertEqual(item_previous-after,{'deleted'})
        self.assertIn('edited',item_previous);self.assertIn('edited',after)
        self.assertEqual((before-set())-after,{'restored','deleted'})
        self.assertIn('deletingKeys: deletingItemIDs.map(\.uuidString)',self.commit)
    def test_no_target_or_real_local_edit_preserves_generic_item_apply_and_save_suffix(self):
        historical=pre_save_failure_rollback(self.commit);suffix=historical[historical.index('                           deletingKeys: deletingItemIDs'):];old=body((self.phase/'before'/self.path).read_text(),'func commit<T>(');self.assertEqual(suffix,old[old.index('                           deletingKeys: deletingItemIDs'):]);self.assertEqual(hashlib.sha256(suffix.encode()).hexdigest(),self.proof['generic_apply_and_save_tail_sha256']);self.assertIn('restoredMetadataOnly.isEmpty ? state.items',self.commit);self.assertIn('restoredMetadataOnly.isEmpty && nativeRestoreWithoutValue.isEmpty ? previousItems',self.commit)
    def test_native_timestamp_loop_and_ten_existing_methods_unchanged(self):
        self.assertEqual(len(self.proof['unchanged_methods']),10)
        for r in self.proof['unchanged_methods']:self.assertEqual(hashlib.sha256(body(pre_postwrite_restore((ROOT/r['path']).read_text()),r['symbol']).encode()).hexdigest(),r['sha256'])
    def test_all_six_shared_sources_and_one_changed_file_bound(self):
        self.assertEqual(len(self.proof['shared_sources']),6);self.assertEqual(len(self.proof['current_sources']),1)
        for p,h in {**self.proof['shared_sources'],**self.proof['current_sources']}.items():self.assertEqual(hashlib.sha256(pre_postwrite_restore((ROOT/p).read_text()).encode()).hexdigest(),h)
    def test_three_exact_hunks_reverse_all_247_production_files_without_user_rollback(self):
        self.assertEqual(len(CHANGES),3)
        for p,h in self.base['production'].items():
            data=(ROOT/p).read_bytes();data=pre_native_restore_only(data.decode()).encode()if p.endswith('.swift')else data;self.assertEqual(hashlib.sha256(data).hexdigest(),h)
    def test_reversal_idempotent_and_no_full_function_or_runtime_claim(self):
        old=(self.phase/'before'/self.path).read_text();self.assertEqual(pre_native_restore_only(self.src),old);self.assertEqual(pre_native_restore_only(old),old);self.assertFalse(self.proof['full_function_migration_verified']);self.assertFalse(self.proof['runtime_executed']);self.assertEqual(self.proof['new_difference_records'],0);self.assertEqual(len(self.proof['remaining']),4)

if __name__=='__main__':unittest.main()
