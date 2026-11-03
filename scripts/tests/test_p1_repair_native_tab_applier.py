"""Native tab snapshot/move contracts; Python/source/Mach-O checks only."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts/tests'),str(ROOT/'scripts')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from native_tab_applier_scope_contract import CHANGES,pre_native_tab_applier

from native_tab_source_renderer_scope_contract import pre_native_tab_source_renderer, pre_native_tab_source_renderer_bytes

class NativeTabApplier(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  # Replay this phase's reviewed renderer; phase171 checks the replacement production chain directly.
  cls.ph=ROOT/'.local/p0-repair/phase-169';cls.p=json.loads((cls.ph/'native-tab-applier-contract.json').read_text());cls.base=json.loads((cls.ph/'baseline.json').read_text());cls.bar=pre_native_tab_source_renderer((ROOT/'replica/Sources/Pasto/UI/OriginalPanelTabBar.swift').read_text());cls.ui=(ROOT/'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text();cls.toolbar=(ROOT/'replica/Sources/Pasto/UI/OriginalPanelToolbar.swift').read_text();cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
 def order(self,s,tokens):
  indexes=[s.index(t)for t in tokens];self.assertEqual(indexes,sorted(indexes))
 def test_actual_fragments_machine_ranges_and_binary_are_bound(self):
  self.assertEqual(len(self.p['original_fragments']),15)
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for k in ['binary','decoder']:
   r=self.p[k];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
  for r in self.p['machine_ranges']:
   a=int(r['start'],16);b=int(r['end'],16);self.assertEqual(hashlib.sha256(self.n['read'](a,b-a)).hexdigest(),r['sha256'])
 def test_actual_calls_and_flags_bind_the_local_mutation_drain_chain(self):
  calls={}
  for r in self.p['calls']:
   a=int(r['address'],16);raw=self.n['read'](a,4);self.assertEqual(raw.hex(),r['bytes']);w=int.from_bytes(raw,'little');self.assertEqual(w&0x7c000000,0x14000000);d=w&0x3ffffff;d=d-(1<<26)if d&(1<<25)else d;self.assertEqual(hex(a+4*d),r['target']);calls[a]=a+4*d
  self.assertEqual(calls[0x1001b9210],0x1001b9214);self.assertEqual(calls[0x1001b960c],0x1001b9b78)
  for r in self.p['words']:self.assertEqual(self.n['read'](int(r['address'],16),4).hex(),r['bytes'])
  self.assertEqual(int.from_bytes(self.n['read'](0x1001b91f8,4),'little'),0x39016e88)
  self.assertEqual(int.from_bytes(self.n['read'](0x1001b9600,4),'little'),0xa9007edf)
 def test_configure_coalesces_full_specs_and_flushes_only_initial_delivery(self):
  s=body(self.bar,'func configure(');self.order(s,['pendingTabs = tabs','scheduleSnapshotDrain()','if !hasAppliedSnapshot { drainSnapshots() }']);self.assertNotIn('applyTabs(tabs)',s)
  for t in ['private var pendingTabs: [OriginalPinboardTab]?','private var hasAppliedSnapshot = false']:self.assertIn(t,self.bar)
 def test_scheduler_uses_three_flags_weak_owner_and_main_queue_without_pending_gate(self):
  s=body(self.bar,'private func scheduleSnapshotDrain(');self.order(s,['guard !isApplyingSnapshots, !snapshotDrainScheduled, !isPerformingLocalMutation','snapshotDrainScheduled = true','DispatchQueue.main.async { [weak self]','MainActor.assumeIsolated { self?.drainSnapshots() }'])
  for t in ['pendingTabs','Generation','Task','asyncAfter']:self.assertNotIn(t,s)
 def test_drain_clears_before_render_and_rereads_pending_after_reentry(self):
  s=body(self.bar,'private func drainSnapshots(');self.order(s,['snapshotDrainScheduled = false','guard !isPerformingLocalMutation, !isApplyingSnapshots','isApplyingSnapshots = true','while !isPerformingLocalMutation, let tabs = pendingTabs','pendingTabs = nil','hasAppliedSnapshot = true','applyTabs(tabs)','isApplyingSnapshots = false'])
 def test_move_uses_displayed_object_identity_and_keeps_order_through_persistence(self):
  s=body(self.bar,'func moveList(');self.assertEqual(s.count('hasSameObjectID(as:'),2);self.order(s,['keys.firstIndex','isPerformingLocalMutation = true','persist(sourceIndex < destinationIndex ? destinationIndex + 1 : destinationIndex)','keys.remove(at: sourceIndex)','keys.insert(key, at: min(destinationIndex, keys.count))','isPerformingLocalMutation = false','scheduleSnapshotDrain()','stack.setViews(keys.compactMap','layoutSubtreeIfNeeded()','return true'])
  for t in ['tabListSnapshot','try?','sourceIndex != destinationIndex','max(0','UUID(']:self.assertNotIn(t,s)
 def test_real_UI_and_toolbar_deliver_same_target_and_consume_transaction_error(self):
  s=body(self.ui,'func moveList(identifier:');self.order(s,['store.tabListTarget(identifier: identifier)','toolbarOwner?.moveList(source, to: target, persist: { offset in','try? self.store.moveList(source, toOffset: offset)']);self.assertIn('}) ?? false',s);self.assertNotIn('tabListSnapshot',s);self.assertNotIn('destinationIndex',s)
  self.assertIn('tabBar.moveList(source, to: target, persist: persist)',body(self.toolbar,'func moveList('))
 def test_existing_renderer_is_retained_as_exact_adapter(self):
  old=body((self.ph/'before/replica/Sources/Pasto/UI/OriginalPanelTabBar.swift').read_text(),'func configure(');from native_tab_renderer_delivery_scope_contract import pre_native_tab_renderer_delivery
  new=body(pre_native_tab_renderer_delivery(self.bar),'private func applyTabs(');self.assertEqual(old,new)
  for sig in ['func beginEditingList(','func setCollapsed(','private func f_100095228(','private func f_100095ae8(','override func layout(']:self.assertEqual(body(self.bar,sig),body((self.ph/'before/replica/Sources/Pasto/UI/OriginalPanelTabBar.swift').read_text(),sig))
 def test_all_production_hunks_are_exact_and_inverse_is_historical_idempotent(self):
  self.assertEqual(len(CHANGES),5);changed=[]
  for p,h in self.base['production'].items():
   data=pre_native_tab_source_renderer_bytes(ROOT/p);old=(self.ph/'before'/p).read_bytes()
   if hashlib.sha256(data).hexdigest()!=h:changed.append(p)
   restored=pre_native_tab_applier(data.decode()).encode()if p.endswith('.swift')else data
   self.assertEqual(hashlib.sha256(restored).hexdigest(),h,p)
   self.assertEqual(pre_native_tab_applier(old.decode()).encode()if p.endswith('.swift')else old,old,p)
  self.assertEqual(sorted(changed),sorted(self.p['current_sources']))
 def test_all_move_positions_match_original_post_removal_insert_semantics(self):
  # Independent permutation oracle for SDK move offset versus original applier final index.
  for n in range(1,30):
   before=list(range(n))
   for source in range(n):
    for dest in range(n):
     offset=dest+1 if source<dest else dest
     persisted=before[:];item=persisted.pop(source);persisted.insert(offset-1 if source<offset else offset,item)
     applier=before[:];item=applier.pop(source);applier.insert(min(dest,len(applier)),item)
     self.assertEqual(applier,persisted);self.assertEqual(sorted(applier),before)
 def test_latest_snapshot_and_reentrant_delivery_state_table(self):
  # Protocol oracle: persistence must not expose pending data until the local move ends.
  for source,dest in [(0,2),(2,0),(1,1)]:
   displayed=['a','b','c'];pending=None;mutating=True;applying=False;seen=[]
   saved=displayed[:];item=saved.pop(source);saved.insert(dest,item)
   pending=saved[:];self.assertTrue(mutating);self.assertEqual(displayed,['a','b','c'])
   item=displayed.pop(source);displayed.insert(min(dest,len(displayed)),item);mutating=False
   applying=True
   while pending is not None and not mutating:
    incoming,pending=pending,None;displayed=incoming;seen.append(incoming)
    if len(seen)==1:pending=['new','a','c']
   applying=False;self.assertEqual(displayed,['new','a','c']);self.assertEqual(len(seen),2);self.assertFalse(applying)
 def test_unported_generic_diff_drag_geometry_and_full_completion_remain_explicit(self):
  self.assertFalse(self.p['finite_contract_completed']);self.assertFalse(self.p['full_function_migration_verified']);self.assertFalse(self.p['runtime_executed']);self.assertTrue(any('threshold300' in t for t in self.p['adaptations']))

if __name__=='__main__':unittest.main()
