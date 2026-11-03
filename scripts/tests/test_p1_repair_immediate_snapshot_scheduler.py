"""Default immediate snapshot scheduler: source/Mach-O only, no app/framework execution."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from list_insert_validation_scope_contract import pre_list_insert_validation
from test_p0_repair_checksum_routing import original_fragment
from collection_snapshot_scheduler_scope_contract import CHANGES,pre_collection_snapshot_scheduler,pre_collection_snapshot_scheduler_bytes
from stack_cell_coder_scope_contract import pre_stack_cell_coder_bytes
from snapshot_scheduler_static_inventory import snapshot_scheduler_inventory
class ImmediateSnapshotScheduler(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-144';cls.p=json.loads((cls.phase/'immediate-snapshot-scheduler-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.path='replica/Sources/PastoCore/ClipboardSearchCollection.swift';cls.src=(ROOT/cls.path).read_text();cls.before=(cls.phase/'before'/cls.path).read_text();cls.scopes={}
        for name,marker in [('search','public final class ClipboardSearchCollection'),('pinboard','public final class ClipboardPinboardCollection')]:cls.scopes[name]=body(cls.src,marker)
        cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
    def order(self,s,tokens):
        i=0
        for t in tokens:i=s.index(t,i)+len(t)
    def original(self,a):
        r=next(r for r in self.p['original_fragments']if r['address']==a);return original_fragment((ROOT/r['path']).read_text(),a[2:])
    def test_thirteen_original_fragments_binary_and_static_decoders_bound(self):
        self.assertEqual(len(self.p['original_fragments']),13)
        for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for k in ['binary','decoder','inventory_decoder']:
            r=self.p[k];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_real_keypath_component_targets_scheduler_factory(self):
        r=self.p['keypath_getter'];a=int(r['address'],16);b=self.n['read'](a,4);self.assertEqual(b.hex(),r['bytes']);self.assertEqual(a+struct.unpack('<i',b)[0],int(r['target'],16));s=self.original('0x100365e18');self.assertIn('puVar12 = &DAT_100c43020',s);self.assertIn('+ 0x60) = puVar12',s)
    def test_witness_slot_eight_is_direct_callback_function_not_context_getter(self):
        self.assertEqual(len(self.p['witness_slots']),2)
        for r in self.p['witness_slots']:
            v,c=self.n['reachable_pointer'](int(r['address'],16));self.assertEqual(hex(v),r['raw']);self.assertEqual(c,r['chain']);self.assertEqual(self.n['base']+(v&((1<<36)-1)),int(r['target'],16))
        self.assertEqual(self.p['witness_slots'][1]['target'],'0x10009df20');self.assertIn('(*param_1)()',self.original('0x10009df20'));self.assertNotIn('perform',self.original('0x10009df20'))
    def test_metadata_names_default_type_and_protocol_from_native_descriptors(self):
        r=self.p['metadata'];a=int(r['address'],16);self.assertEqual(int.from_bytes(self.n['read'](a,8),'little'),0x200);v,c=self.n['reachable_pointer'](a+8);self.assertEqual(hex(v),r['descriptor_pointer']);self.assertEqual(c,r['descriptor_chain']);descriptor=self.n['base']+(v&((1<<36)-1));self.assertEqual(descriptor,int(r['descriptor'],16));name=descriptor+8+struct.unpack('<i',self.n['read'](descriptor+8,4))[0];self.assertEqual(self.n['read'](name,100).split(b'\0')[0].decode(),'ImmediateSnapshotScheduler');self.assertEqual(self.n['read'](int(r['protocol_name_address'],16),100).split(b'\0')[0].decode(),'SnapshotScheduler')
    def test_all5450_static_conformances_decode_with_one_scheduler_match(self):
        actual=snapshot_scheduler_inventory(self.n);self.assertEqual(actual,self.p['static_conformance_inventory']);self.assertEqual(actual['conformance_count'],5450);self.assertEqual(actual['indirect_pointer_count'],2890);self.assertEqual(actual['unresolved'],0);self.assertEqual(actual['matches'],[dict(entry='0x100d702c0',conformance='0x100c4264c',protocol='0x100cac844')])
    def test_seven_actual_words_bind_scheduler_field60_and_witness_call(self):
        self.assertEqual(len(self.p['ARM_words']),7)
        for r in self.p['ARM_words']:self.assertEqual(self.n['read'](int(r['address'],16),4).hex(),r['bytes'])
        self.assertEqual(self.n['read'](0x100366aa8,4).hex(),'b43240f9');self.assertEqual(self.n['read'](0x100366ae8,4).hex(),'150740f9');self.assertEqual(self.n['read'](0x100366b04,4).hex(),'a0023fd6')
    def test_context_field58_is_separate_from_default_scheduler_field60(self):
        self.assertIn('+ 0x58) = puVar12',self.original('0x100365e18'));self.assertIn('FUN_10037631c()',self.original('0x10036c840'));self.assertIn('viewContext(',self.original('0x10035de70'))
        for a in ['0x10036c844','0x1002fd824']:
            s=self.original(a);self.assertIn('&DAT_100ecc180',s);self.assertIn('&PTR_PTR_100ecc190',s)
    def test_original_receive_stores_pending_before_first_only_scheduler_invocation(self):
        s=self.original('0x1003669fc');self.order(s,['+ 0x48) = param_1','+ 0x50) = param_2','if (lVar3 == 0)','FUN_1000da768(local_78)','(*pcVar2)(param_4,param_3,local_60,lStack_58)'])
    def test_current_both_receive_methods_publish_inline_after_storing_pending(self):
        for s in self.scopes.values():
            f=body(s,'private func receive(');self.order(f,['let schedulesDelivery = pending == nil','pending = (ids, (pending?.updated ?? []).union(updated))','if schedulesDelivery','flushPending()'])
            for t in ['context.perform','DispatchQueue','Task {','MainActor.assumeIsolated','async']:self.assertNotIn(t,f)
        self.assertIn('@MainActor\npublic final class ClipboardSearchCollection',self.src);self.assertIn('@MainActor\npublic final class ClipboardPinboardCollection',self.src)
    def test_default_model_observes_send_before_receive_returns(self):
        trace=[];pending=None
        def flush():
            nonlocal pending
            value=pending;pending=None;trace.append(('send',value))
        trace.append('enter');first=pending is None;pending=('ids',{'a'})
        if first:flush()
        trace.append('return');self.assertEqual(trace,['enter',('send',('ids',{'a'})),'return']);self.assertIsNone(pending)
    def test_reentrant_publication_clears_pending_before_nested_inline_delivery(self):
        trace=[];pending=None
        def receive(ids):
            nonlocal pending
            first=pending is None;pending=ids
            if first:
                value=pending;pending=None;trace.append(('send',value))
                if value=='a':receive('b')
                trace.append(('sent',value))
        receive('a');self.assertEqual(trace,[('send','a'),('send','b'),('sent','b'),('sent','a')]);self.assertIsNone(pending)
    def test_pending_merge_and_first_only_gate_are_unchanged_before_delivery(self):
        for name,s in self.scopes.items():
            new=body(s,'private func receive(');old=body(body(self.before,'public final class '+('ClipboardSearchCollection'if name=='search'else'ClipboardPinboardCollection')),'private func receive(');marker='        if schedulesDelivery';self.assertEqual(new[:new.index(marker)],old[:old.index(marker)])
    def test_weak_observation_and_original_cleanup_evidence_are_preserved_not_claimed_full(self):
        for s in self.scopes.values():
            init=body(s,'init(context: NSManagedObjectContext, request:');self.assertGreaterEqual(init.count('[weak self]'),2)
        self.assertIn('_swift_weakLoadStrong()',self.original('0x100366c14'));self.assertIn('objc_stub::removeObserver_',self.original('0x1003550fc'));self.assertIn('_swift_release',self.original('0x100355184'))
    def test_twelve_existing_fetch_flush_cache_observation_methods_delegate_and_sources_unchanged(self):
        self.assertEqual(len(self.p['unchanged_methods']),12)
        for r in self.p['unchanged_methods']:self.assertEqual(hashlib.sha256(body(self.scopes[r['scope']],r['symbol']).encode()).hexdigest(),r['sha256'])
        tail=self.src[self.src.index('/// 354800/354f90'):];self.assertEqual(hashlib.sha256(tail.encode()).hexdigest(),self.p['unchanged_delegate_sha256'])
        for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_stack_cell_coder_bytes(ROOT/p)).hexdigest(),h)
    def test_one_pattern_two_sites_one_file_and247_production_files_reverse_exactly(self):
        self.assertEqual(len(CHANGES),1);self.assertEqual(sum(c[3]for c in CHANGES),2);paths={str(p.relative_to(ROOT))for p in(ROOT/'replica/Sources').rglob('*')if p.is_file()};self.assertEqual(paths,set(self.base['production']));changed=[]
        for p,h in self.base['production'].items():
            if hashlib.sha256(pre_stack_cell_coder_bytes(ROOT/p)).hexdigest()!=h:changed.append(p)
            self.assertEqual(hashlib.sha256(pre_collection_snapshot_scheduler_bytes(ROOT/p)).hexdigest(),h)
        self.assertEqual(changed,[self.path]);self.assertEqual(pre_collection_snapshot_scheduler(self.src),self.before);self.assertEqual(pre_collection_snapshot_scheduler(self.before),self.before);self.assertEqual(hashlib.sha256(pre_list_insert_validation(self.src).encode()).hexdigest(),self.p['current_sources'][self.path])
    def test_default_only_contract_does_not_claim_external_scheduler_DI_or_runtime_timing(self):
        self.assertEqual(self.p['function_id'],'Paste:0x1003669fc');self.assertEqual(self.p['new_difference_records'],1);self.assertTrue(self.p['finite_contract_verified']);self.assertFalse(self.p['full_function_migration_verified']);self.assertFalse(self.p['runtime_executed']);self.assertEqual(len(self.p['adaptations']),2);self.assertIn('SnapshotScheduler',self.p['adaptations'][0]);self.assertIn('04430c/0f733c',self.p['remaining'][0])
if __name__=='__main__':unittest.main()
