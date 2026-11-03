"""Setter machine-code ownership tail and current no-result adaptation, not full Swift ABI proof."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts/tests'),str(ROOT/'scripts')]
from function_ledger import source_fragments
from native_list_creation_lifecycle_scope_contract import pre_native_list_creation_lifecycle_bytes
from test_offline_p0_contracts import body
from text_setter_return_scope_contract import CHANGES,pre_text_setter_return,pre_text_setter_return_bytes
class TextSetterReturn(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ph=ROOT/'.local/p0-repair/phase-161';cls.p=json.loads((cls.ph/'setter-return-contract.json').read_text());cls.base=json.loads((cls.ph/'baseline.json').read_text());cls.path=next(iter(cls.p['current_sources']));cls.s=(ROOT/cls.path).read_text();cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
 def test_original_fragments_binary_decoder_and_full68_byte_native_function_are_bound(self):
  self.assertEqual(len(self.p['original_fragments']),7)
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for k in ['binary','decoder','p0_save_proof']:
   r=self.p[k];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
  m=self.p['machine'];self.assertEqual(self.n['read'](int(m['address'],16),int(m['end'],16)-int(m['address'],16)).hex(),m['bytes']);self.assertEqual(len(bytes.fromhex(m['bytes'])),68)
 def test_native_String_bridge_release_and_tail_objc_release_are_true_imports(self):
  for r in self.p['imports']:
   a=int(r['address'],16);w=int.from_bytes(self.n['read'](a,4),'little');self.assertEqual(w&0xfc000000,0x94000000 if r['link']else 0x14000000);d=w&0x3ffffff;d=d-(1<<26)if d&(1<<25)else d;self.assertEqual(hex(a+4*d),r['stub']);v,c=self.n['reachable_pointer'](int(r['pointer'],16));self.assertEqual(c,r['chain']);self.assertTrue(v>>63);self.assertEqual(v&0xffffff,r['ordinal']);f=self.n['fixup'][0];h=struct.unpack('<7I',self.n['raw'][f:f+28]);e=struct.unpack_from('<I',self.n['raw'],f+h[2]+4*r['ordinal'])[0];o=f+h[3]+(e>>9);self.assertEqual(self.n['raw'][o:self.n['raw'].index(b'\0',o)].decode(),r['symbol'])
  self.assertEqual([r['symbol']for r in self.p['imports']], ['_$sSS10FoundationE19_bridgeToObjectiveCSo8NSStringCyF','_swift_bridgeObjectRelease','_objc_release']);self.assertFalse(self.p['imports'][-1]['link'])
 def test_true_setString_selector_uses_native_self_and_bridged_NSString(self):
  r=self.p['selector'];x,y=struct.unpack('<II',self.n['read'](int(r['stub'],16),8));self.assertEqual(x&0x9f00001f,0x90000001);self.assertEqual(y&0xffc003ff,0xf9400021);imm=((x>>5)&0x7ffff)*4+((x>>29)&3);imm=imm-(1<<21)if imm&(1<<20)else imm;p=(int(r['stub'],16)&~4095)+(imm<<12)+((y>>10)&0xfff)*8;self.assertEqual(hex(p),r['pointer']);v,c=self.n['reachable_pointer'](p);self.assertFalse(v>>63);self.assertEqual(c,r['chain']);dest=self.n['base']+(v&((1<<36)-1));self.assertEqual(self.n['read'](dest,40).split(b'\0')[0],b'setString:');self.assertEqual(self.n['read'](0x1000f7360,8).hex(),'e00314aae20315aa')
 def test_complete_instruction_inventory_has_no_integer_zero_result_and_ends_in_release_tail_branch(self):
  m=self.p['machine'];b=bytes.fromhex(m['bytes']);words=struct.unpack('<17I',b);self.assertEqual(words[-1]&0xfc000000,0x14000000);self.assertEqual(words[-5],0xaa1503e0);self.assertEqual(sum(w&0xfc000000==0x94000000 for w in words),3)
  for zero_result in [0xd2800000,0x52800000,0xaa1f03e0,0x2a1f03e0]:self.assertNotIn(zero_result,words)
 def test_current_helper_keeps_MainActor_and_setter_side_effect_but_removes_guessed_integer(self):
  self.assertIn('@MainActor func f_1000f733c(_ value: String) {',self.s);self.assertEqual(body(self.s,'func f_1000f733c(').strip(),'{\n        string = value\n    }');self.assertNotIn('-> Int',self.s);self.assertNotIn('return 0',self.s);self.assertNotIn('@discardableResult',self.s)
  for token in ['objc_release','Task','DispatchQueue','try?','catch','fatalError']:self.assertNotIn(token,self.s)
  before=(self.ph/'before'/self.path).read_text();self.assertEqual(body(self.s,'func f_1000f7254('),body(before,'func f_1000f7254('))
 def test_P0_failure_parent_keeps_error_consumption_Undo_notification_and_success_only_publication(self):
  for p,h in self.p['unchanged_sources'].items():self.assertEqual(hashlib.sha256(pre_native_list_creation_lifecycle_bytes(ROOT/p)).hexdigest(),h)
  paste=(ROOT/'replica/Sources/PastoCore/Pasteboard.swift').read_text();f=body(paste,'private func finishPasteboardWrite(');tokens=['writer.f_10037875c(objects)','persistChangeCount?','do {','try prepareRestoration()','try recordRestoredSelection(restoration)','} catch {','removeAllActions()','NotificationCenter.default.post','didRestoreItem.send()'];pos=[f.index(t)for t in tokens];self.assertEqual(pos,sorted(pos));self.assertNotIn('throw',body(f,'catch'));store=(ROOT/'replica/Sources/PastoCore/ClipboardStore.swift').read_text();m=body(store,'private func mutateInTransaction<T>(historyAction:');self.assertLess(m.index('try persistence.commit'),m.index('publish(state)'));self.assertNotIn('catch',m)
 def test_one_exact_delta_reverses_all247_files_without_touching_other_user_changes(self):
  self.assertEqual(len(CHANGES),1);changed=[]
  for p,h in self.base['production'].items():
   if hashlib.sha256(pre_native_list_creation_lifecycle_bytes(ROOT/p)).hexdigest()!=h:changed.append(p)
   self.assertEqual(hashlib.sha256(pre_text_setter_return_bytes(ROOT/p)).hexdigest(),h)
  self.assertEqual(changed,[self.path]);self.assertEqual(pre_text_setter_return((self.ph/'before'/self.path).read_text()),(self.ph/'before'/self.path).read_text())
 def test_partial_return_adaptation_does_not_claim_declaration_ABI_consumer_or_unknown_closure(self):
  self.assertFalse(self.p['runtime_executed']);self.assertFalse(self.p['full_function_migration_verified']);self.assertEqual(len(self.p['remaining']),3);self.assertIn('未恢复原Swift声明元数据',self.p['remaining'][0]);self.assertIn('unknown',self.p['remaining'][1]);r=json.loads((ROOT/'reports/replica/p0-p1-repair-round160.json').read_text());self.assertIn('Paste:0x1000f733c',r['unknown_function_ids'])
if __name__=='__main__':unittest.main()
