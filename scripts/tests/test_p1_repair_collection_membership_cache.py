"""Collection membership cache and pending-ID boundary; source/Mach-O/Python only."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from stack_close_session_scope_contract import pre_stack_close_session_bytes
from test_p0_repair_checksum_routing import original_fragment
from collection_membership_cache_scope_contract import CHANGES,pre_collection_membership_cache,pre_collection_membership_cache_bytes
from collection_snapshot_scheduler_scope_contract import pre_collection_snapshot_scheduler
from stack_cell_coder_scope_contract import pre_stack_cell_coder_bytes
class CollectionMembershipCache(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-143';cls.p=json.loads((cls.phase/'collection-membership-cache-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.path='replica/Sources/PastoCore/ClipboardSearchCollection.swift';cls.src=pre_collection_snapshot_scheduler((ROOT/cls.path).read_text());cls.before=(cls.phase/'before'/cls.path).read_text();cls.scopes={};cls.old={}
        for name,marker in [('search','public final class ClipboardSearchCollection'),('pinboard','public final class ClipboardPinboardCollection')]:cls.scopes[name]=body(cls.src,marker);cls.old[name]=body(cls.before,marker)
        cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
    def order(self,s,tokens):
        i=0
        for t in tokens:i=s.index(t,i)+len(t)
    def original(self,a):
        r=next(r for r in self.p['original_fragments']if r['address']==a);return original_fragment((ROOT/r['path']).read_text(),a[2:])
    def test_seventeen_original_fragments_binary_and_decoder_bound(self):
        self.assertEqual(len(self.p['original_fragments']),17)
        for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for k in ['binary','decoder']:
            r=self.p[k];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_actual_notification_keys_are_updated_and_refreshed(self):
        self.assertEqual({r['symbol']for r in self.p['notification_key_imports']},{'_NSUpdatedObjectsKey','_NSRefreshedObjectsKey'})
        for r in self.p['notification_key_imports']:
            v,c=self.n['reachable_pointer'](int(r['address'],16));self.assertEqual(hex(v),r['raw']);self.assertEqual(c,r['chain']);self.assertTrue(v>>63);f=self.n['fixup'][0];h=struct.unpack_from('<7I',self.n['raw'],f);self.assertEqual(h[5],1);w=struct.unpack_from('<I',self.n['raw'],f+h[2]+4*(v&0xffffff))[0];p=f+h[3]+(w>>9);self.assertEqual(self.n['raw'][p:self.n['raw'].index(b'\0',p)].decode(),r['symbol'])
    def test_real_native_class_metadata_binds_both_observer_type_filters(self):
        self.assertEqual({r['name']for r in self.p['native_classes']},{'_TtC9PasteCore10ListEntity','_TtC9PasteCore10ItemEntity'})
        for r in self.p['native_classes']:
            v,c=self.n['reachable_pointer'](int(r['address'],16)+32);self.assertEqual(hex(v),r['data_pointer']);self.assertEqual(c,r['data_chain']);ro=(self.n['base']+(v&((1<<36)-1)))&~7;self.assertEqual(ro,int(r['ro'],16));w,d=self.n['reachable_pointer'](ro+24);self.assertEqual(hex(w),r['name_pointer']);self.assertEqual(d,r['name_chain']);target=self.n['base']+(w&((1<<36)-1));self.assertEqual(self.n['read'](target,100).split(b'\0')[0].decode(),r['name'])
        self.assertIn('FUN_10032b0c8(0)',self.original('0x10036be08'));self.assertIn('FUN_1003214a8(0)',self.original('0x10036be40'))
    def test_eight_words_and_two_calls_bind_array_equality_guard_and_set_builder(self):
        self.assertEqual(len(self.p['ARM_words']),8);self.assertEqual(len(self.p['ARM_calls']),2)
        for r in self.p['ARM_words']:self.assertEqual(self.n['read'](int(r['address'],16),4).hex(),r['bytes'])
        for r in self.p['ARM_calls']:
            pc=int(r['address'],16);w=int.from_bytes(self.n['read'](pc,4),'little');self.assertEqual(w&0xfc000000,0x94000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(pc+4*d,int(r['target'],16))
    def test_original_flush_only_rebuilds_membership_for_changed_order_then_always_sends(self):
        s=self.original('0x100366b38');self.order(s,['+ 0x48) = 0','FUN_1003699b8','if ((uVar1 & 1) == 0)','+ 0x10) = uVar2','FUN_10036bf0c()','+ 0x40) = uVar1','CurrentValueSubject::send']);self.assertIn('Swift::Set::init(minimumCapacity)',self.original('0x10036bf0c'))
    def test_original_pending_path_uses_pending_ids_and_no_pending_uses_cached_set(self):
        for a in ['0x100366c6c','0x100366db8']:
            s=self.original(a);self.order(s,['+ 0x48)','if (puVar4 ==','+ 0x10)','+ 0x40)','FUN_10036bf0c()','FUN_100365478()','FUN_1003669fc(']);self.assertIn('puVar5 = puVar6',s)
        self.assertIn('objc_stub::objectID(*param_2)',self.original('0x100354680'))
    def test_both_actual_collections_own_empty_membership_cache(self):
        self.assertEqual(self.src.count('private var objectIDMembership: Set<NSManagedObjectID> = []'),2)
        for s in self.scopes.values():self.assertIn('private var objectIDMembership: Set<NSManagedObjectID> = []',s)
    def test_flush_cache_precedes_publication_without_suppressing_equal_id_events(self):
        for s in self.scopes.values():
            f=body(s,'private func flushPending()');self.order(f,['guard let value = pending','pending = nil','if objectIDs != value.ids','objectIDs = value.ids','objectIDMembership = Set(value.ids)','subject.send(']);conditional=body(f,'if objectIDs != value.ids');self.assertNotIn('subject.send',conditional);self.assertNotIn('return',conditional)
    def test_pending_optional_boundary_does_not_treat_empty_pending_as_old_cache(self):
        for s in self.scopes.values():
            f=body(s,'private func objectsDidChange(');self.order(f,['let ids = pending?.ids ?? objectIDs','let membership = pending.map { Set($0.ids) } ?? objectIDMembership','NSUpdatedObjectsKey','NSRefreshedObjectsKey','updated.union(refreshed)','intersection(membership)','receive(ids: ids, updated: changed)']);self.assertNotIn('Set(ids)',f);self.assertNotIn('!ids.isEmpty',f)
    def test_repeated_equal_ids_reuse_cache_but_keep_updated_snapshot_events(self):
        ids=['a','b'];cache=set(ids);allocations=1;publications=[]
        for updates in [{'a'},{'b'},set()]:
            next_ids=['a','b']
            if ids!=next_ids:ids=next_ids;cache=set(ids);allocations+=1
            publications.append((list(next_ids),updates))
        self.assertEqual(allocations,1);self.assertEqual(len(publications),3);self.assertEqual(publications[1][1],{'b'});self.assertEqual(cache,{'a','b'})
    def test_changed_order_rebuilds_even_when_membership_set_is_equal(self):
        previous=['a','b'];next_ids=['b','a'];self.assertNotEqual(previous,next_ids);self.assertEqual(set(previous),set(next_ids))
        for s in self.scopes.values():self.assertIn('if objectIDs != value.ids',body(s,'private func flushPending()'));self.assertNotIn('if objectIDMembership !=',s)
    def test_pending_insert_delete_and_empty_membership_never_use_old_set(self):
        committed={'a','b'};updates={'a','b','c'}
        for pending,expected in [(None,{'a','b'}),([],set()),(['b','c'],{'b','c'}),(['c'],{'c'})]:
            membership=committed if pending is None else set(pending);self.assertEqual(updates&membership,expected)
        for s in self.scopes.values():self.assertIn('pending.map { Set($0.ids) } ?? objectIDMembership',s)
    def test_local_UUID_and_reference_projection_after_cache_block_is_unchanged(self):
        new=body(self.scopes['search'],'private func flushPending()');old=body(self.old['search'],'private func flushPending()');marker='        let keys =';self.assertEqual(new[new.index(marker):],old[old.index(marker):]);self.assertIn('subject.send(Snapshot(identifiers:',new)
    def test_ten_initial_fetch_pending_receive_methods_delegate_and_three_sources_unchanged(self):
        self.assertEqual(len(self.p['unchanged_methods']),10)
        for r in self.p['unchanged_methods']:self.assertEqual(hashlib.sha256(body(self.scopes[r['scope']],r['symbol']).encode()).hexdigest(),r['sha256'])
        self.assertEqual(hashlib.sha256(self.src[self.src.index('/// 354800/354f90'):].encode()).hexdigest(),self.p['unchanged_delegate_sha256']);self.assertEqual(len(self.p['shared_sources']),3)
        for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_stack_close_session_bytes(ROOT/p)).hexdigest(),h)
    def test_three_count_bound_patterns_six_hunks_one_file_preserve247_files(self):
        self.assertEqual(len(CHANGES),3);self.assertEqual(sum(r[3]for r in CHANGES),6);paths={str(p.relative_to(ROOT))for p in(ROOT/'replica/Sources').rglob('*')if p.is_file()};self.assertEqual(paths,set(self.base['production']));changed=[]
        for p,h in self.base['production'].items():
            if hashlib.sha256(pre_stack_cell_coder_bytes(ROOT/p)).hexdigest()!=h:changed.append(p)
            self.assertEqual(hashlib.sha256(pre_collection_membership_cache_bytes(ROOT/p)).hexdigest(),h)
        self.assertEqual(changed,[self.path]);self.assertEqual(pre_collection_membership_cache(self.src),self.before);self.assertEqual(pre_collection_membership_cache(self.before),self.before);self.assertEqual(hashlib.sha256(self.src.encode()).hexdigest(),self.p['current_sources'][self.path])
    def test_finite_cache_contract_keeps_original_scheduler_model_and_runtime_unclaimed(self):
        self.assertEqual(self.p['function_id'],'Paste:0x100366b38');self.assertEqual(self.p['new_difference_records'],1);self.assertTrue(self.p['finite_contract_verified']);self.assertFalse(self.p['full_function_migration_verified']);self.assertFalse(self.p['runtime_executed']);self.assertEqual(len(self.p['adaptations']),2);self.assertIn('dispatcher',self.p['remaining'][0]);self.assertIn('04430c/0f733c',self.p['remaining'][1])
if __name__=='__main__':unittest.main()
