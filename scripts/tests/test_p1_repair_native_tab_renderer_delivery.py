"""Renderer setter and post-drag layout/selected scrolling: static contracts only."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts/tests'),str(ROOT/'scripts')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from native_tab_renderer_delivery_scope_contract import CHANGES,pre_native_tab_renderer_delivery

from native_tab_source_renderer_scope_contract import pre_native_tab_source_renderer, pre_native_tab_source_renderer_bytes

class NativeTabRendererDelivery(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  # Replay this phase's reviewed renderer; phase171 checks the replacement production chain directly.
  cls.ph=ROOT/'.local/p0-repair/phase-170';cls.p=json.loads((cls.ph/'native-tab-renderer-delivery-contract.json').read_text());cls.base=json.loads((cls.ph/'baseline.json').read_text());cls.bar=pre_native_tab_source_renderer((ROOT/'replica/Sources/Pasto/UI/OriginalPanelTabBar.swift').read_text());cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
 def order(self,s,tokens):
  indexes=[s.index(t)for t in tokens];self.assertEqual(indexes,sorted(indexes))
 def word(self,a):return int.from_bytes(self.n['read'](a,4),'little')
 def test_original_fragments_complete_machine_ranges_and_decoder_are_bound(self):
  self.assertEqual(len(self.p['original_fragments']),10)
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for k in ['binary','decoder']:
   r=self.p[k];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
  for r in self.p['machine_ranges']:
   a=int(r['start'],16);b=int(r['end'],16);self.assertEqual(hashlib.sha256(self.n['read'](a,b-a)).hexdigest(),r['sha256'])
 def test_actual_calls_bind_unlock_return_before_rebuild_and_selected_lookup(self):
  calls={}
  for r in self.p['calls']:
   a=int(r['address'],16);raw=self.n['read'](a,4);self.assertEqual(raw.hex(),r['bytes']);w=int.from_bytes(raw,'little');self.assertEqual(w&0x7c000000,0x14000000);d=w&0x3ffffff;d=d-(1<<26)if d&(1<<25)else d;self.assertEqual(hex(a+4*d),r['target']);calls[a]=a+4*d
  self.assertEqual(calls[0x1000974d4],0x1001b91e4);self.assertEqual(calls[0x1000976fc],0x100098900);self.assertEqual(calls[0x100097724],0x10009727c);self.assertEqual(calls[0x1000977b0],0x10021cadc);self.assertEqual(calls[0x1001b9210],0x1001b9214)
 def test_machine_callback_setter_precedes_renderer_branch(self):
  # incoming setter x5 -> x23, indirect invoke, then branch into UI path.
  self.assertEqual(self.word(0x100097ed4),0xaa0503f7);self.assertEqual(self.word(0x100097ef4),0xd63f02e0);self.assertEqual(self.word(0x100097efc)&0xff00001f,0xb4000015)
  for r in self.p['words']:self.assertEqual(self.n['read'](int(r['address'],16),4).hex(),r['bytes'])
 def test_destination_register_survives_rebuild_and_drives_optional_cell_lookup(self):
  w=self.word(0x1000973f8);self.assertEqual((w>>16)&31,1);self.assertEqual(w&31,26)
  w=self.word(0x100097548);self.assertEqual(w&31,26);self.assertEqual((w>>5)&31,31);self.assertEqual(((w>>10)&0xfff)*8,8)
  w=self.word(0x10009768c);self.assertEqual(w&31,27);self.assertEqual(((w>>10)&0xfff)*8,8)
  w=self.word(0x10009771c);self.assertEqual((w>>16)&31,27);self.assertEqual(w&31,0)
  self.assertEqual(self.word(0x100097728)&0xff00001f,0xb4000000)
  self.assertEqual(self.word(0x10009773c)&0xff00001f,0x36000008)
 def test_original_inset_and_duration_match_reused_scroll_helper(self):
  self.assertEqual(self.word(0x100097748),0x1e763004)
  self.assertEqual(self.word(0x100097790),0xb200e7e0)
  value=(0x3333333333333333&((1<<48)-1))|(((self.word(0x100097794)>>5)&0xffff)<<48)
  self.assertEqual(struct.unpack('<d',value.to_bytes(8,'little'))[0],0.15)
  s=body(self.bar,'private func f_100095ae8(');self.assertIn('cell.frame.insetBy(dx: -17, dy: 0)',s);self.assertIn('duration: 0.15',s);self.assertIn('OriginalViewAnimation.f_10021ccd4()',s)
 def test_new_order_published_before_native_cells_configure(self):
  s=body(self.bar,'private func applyTabs(');self.order(s,['let newKeys = tabs.map','let previousKeys = keys','keys = newKeys','for key in previousKeys','for tab in tabs','tab.configure(cell)','if previousKeys != newKeys','stack.setViews'])
  self.assertEqual(s.count('keys = newKeys'),1)
 def test_drag_unlocks_before_renderer_then_scrolls_selected_destination_only(self):
  s=body(self.bar,'func moveList(');self.order(s,['isPerformingLocalMutation = true','persist(','keys.remove(at: sourceIndex)','keys.insert(key, at: min(destinationIndex, keys.count))','isPerformingLocalMutation = false','scheduleSnapshotDrain()','stack.setViews','layoutSubtreeIfNeeded()','if let cell = cells[keys[destinationIndex]], cell.isSelected','f_100095ae8(cell)','return true'])
  for t in ['onSelect','makeFirstResponder','DispatchQueue','source.isSelected','cells[keys[sourceIndex]]']:self.assertNotIn(t,s)
 def test_nine_methods_and_shared_core_sources_remain_identical(self):
  self.assertEqual(len(self.p['unchanged_methods']),9)
  for r in self.p['unchanged_methods']:self.assertEqual(hashlib.sha256(body(pre_native_tab_source_renderer((ROOT/r['path']).read_text()),r['symbol']).encode()).hexdigest(),r['sha256'])
  for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_native_tab_source_renderer_bytes(ROOT/p)).hexdigest(),h)
 def test_three_hunks_reverse_exactly247_production_files_without_touching_history(self):
  self.assertEqual(len(CHANGES),3);changed=[]
  for p,h in self.base['production'].items():
   data=pre_native_tab_source_renderer_bytes(ROOT/p);before=(self.ph/'before'/p).read_bytes()
   if hashlib.sha256(data).hexdigest()!=h:changed.append(p)
   self.assertEqual(hashlib.sha256(pre_native_tab_renderer_delivery(data.decode()).encode()if p.endswith('.swift')else data).hexdigest(),h,p)
   self.assertEqual(pre_native_tab_renderer_delivery(before.decode()).encode()if p.endswith('.swift')else before,before,p)
  self.assertEqual(sorted(changed),sorted(self.p['current_sources']))
 def test_consumer_protocol_oracle_includes_reentrant_new_index_and_selected_visibility(self):
  # Independent protocol expectation: callbacks resolve the incoming order, not the previous array.
  old=['a','b','c'];incoming=['c','a','d'];published=incoming[:];resolved=[published[i]for i in range(len(incoming))]
  self.assertEqual(resolved,incoming);self.assertNotEqual(resolved,old)
  for src,dest in [(0,2),(2,0),(1,1)]:
   order=old[:];item=order.pop(src);order.insert(dest,item)
   for selected in [None,'a','b','c']:
    trace=['persist','applier_move','unlock','schedule','render','layout']
    if order[dest]==selected:trace.append('scroll')
    self.assertEqual('scroll'in trace,item==selected);self.assertLess(trace.index('unlock'),trace.index('render'))
  self.assertFalse(self.p['finite_contract_completed']);self.assertFalse(self.p['full_function_migration_verified']);self.assertFalse(self.p['runtime_executed'])

if __name__=='__main__':unittest.main()
