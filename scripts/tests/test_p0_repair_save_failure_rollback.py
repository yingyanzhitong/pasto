"""Actual source and original ARM save-error branch; no compilation/framework execution."""
import hashlib,json,struct,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts/tests'),str(ROOT/'scripts')]
from function_ledger import source_fragments
from text_setter_return_scope_contract import pre_text_setter_return_bytes
from test_offline_p0_contracts import body
from save_failure_rollback_scope_contract import CHANGES,pre_save_failure_rollback,pre_save_failure_rollback_bytes
class SaveFailureRollback(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ph=ROOT/'.local/p0-repair/phase-160';cls.p=json.loads((cls.ph/'save-failure-contract.json').read_text());cls.base=json.loads((cls.ph/'baseline.json').read_text());cls.path='replica/Sources/PastoCore/ClipboardPersistence.swift';cls.s=(ROOT/cls.path).read_text();cls.commit=body(cls.s,'func commit<T>(previous:');cls.save=body(cls.commit,'if context.hasChanges');cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
 def test_bound_original_fragments_binary_decoder_and_complete_transaction_machine_range(self):
  self.assertEqual(len(self.p['original_fragments']),7)
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for k in ['binary','decoder']:
   r=self.p[k];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
  r=self.p['code'];code=self.n['read'](int(r['start'],16),int(r['end'],16)-int(r['start'],16));self.assertEqual(hashlib.sha256(code).hexdigest(),r['sha256'])
 def test_complete_direct_call_inventory_includes_rollback_and_both_validation_calls(self):
  r=self.p['code'];actual=[]
  for a in range(int(r['start'],16),int(r['end'],16),4):
   b=self.n['read'](a,4);w=int.from_bytes(b,'little')
   if w&0xfc000000==0x94000000:
    d=w&0x3ffffff;d=d-(1<<26)if d&(1<<25)else d;actual.append(dict(address=hex(a),bytes=b.hex(),target=hex(a+d*4)))
  self.assertEqual(actual,self.p['calls']);self.assertEqual(len(actual),139)
  self.assertIn(dict(address='0x1003035c4',bytes='47182494',target='0x100c096e0'),actual)
 def test_true_objc_stubs_and_fixup_chains_bind_all15_selectors(self):
  for r in self.p['selectors']:
   a=int(r['address'],16);self.assertEqual(self.n['read'](a,4).hex(),r['bytes']);x,y=struct.unpack('<II',self.n['read'](int(r['stub'],16),8));self.assertEqual(x&0x9f00001f,0x90000001);self.assertEqual(y&0xffc003ff,0xf9400021);imm=((x>>5)&0x7ffff)*4+((x>>29)&3);imm=imm-(1<<21)if imm&(1<<20)else imm;p=(int(r['stub'],16)&~4095)+(imm<<12)+((y>>10)&0xfff)*8;self.assertEqual(hex(p),r['pointer']);v,c=self.n['reachable_pointer'](p);self.assertFalse(v>>63);self.assertEqual(c,r['chain']);dest=self.n['base']+(v&((1<<36)-1));self.assertEqual(hex(dest),r['selector_address']);self.assertEqual(self.n['read'](dest,100).split(b'\0')[0].decode(),r['selector'])
  self.assertEqual(len(self.p['selectors']),15);self.assertNotIn('validateForDelete:',[r['selector']for r in self.p['selectors']])
 def test_original_callback_error_no_changes_and_save_success_bypass_rollback(self):
  for r in self.p['branches']:
   a=int(r['address'],16);w=int.from_bytes(self.n['read'](a,4),'little');self.assertEqual(w.to_bytes(4,'little').hex(),r['bytes']);self.assertEqual(w&0x7e000000,0x34000000);d=(w>>5)&0x7ffff;d=d-(1<<19)if d&(1<<18)else d;self.assertEqual(hex(a+d*4),r['target']);self.assertEqual(bool(w&(1<<24)),r['nonzero']);self.assertEqual(w&31,r['register'])
  self.assertEqual([(r['register'],r['nonzero'])for r in self.p['branches']],[(21,True),(0,False),(21,False)])
 def test_original_error_saved_and_reloaded_after_rollback_not_validator_error(self):
  for r in self.p['critical_words']:self.assertEqual(self.n['read'](int(r['address'],16),4).hex(),r['bytes'])
  self.assertEqual(self.n['read'](0x100302bec,4).hex(),'f51700f9');self.assertEqual(self.n['read'](0x1003035c8,4).hex(),'f31740f9')
  r=self.p['imports'][0];v,c=self.n['reachable_pointer'](int(r['pointer'],16));self.assertEqual(c,r['chain']);self.assertTrue(v>>63);self.assertEqual(v&0xffffff,r['ordinal']);f=self.n['fixup'][0];h=struct.unpack('<7I',self.n['raw'][f:f+28]);e=struct.unpack_from('<I',self.n['raw'],f+h[2]+4*r['ordinal'])[0];o=f+h[3]+(e>>9);self.assertEqual(self.n['raw'][o:self.n['raw'].index(b'\0',o)].decode(),'_swift_willThrow')
 def test_current_only_save_catch_rolls_back_callback_and_compatibility_errors_propagate(self):
  outside=self.commit.replace(self.save,'');self.assertNotIn('catch',outside);self.assertNotIn('rollback()',outside);self.assertNotIn('context.reset',self.commit);self.assertNotIn('try?',self.commit)
  self.assertLess(self.commit.index('var outcome = try operation(transaction)'),self.commit.index('if context.hasChanges'))
  bridge=body(self.save,'try OriginalObjCExceptionBridge.f_1002ff9c8');self.assertEqual(bridge,'{ try context.save() }');self.assertEqual(self.save.count('context.rollback()'),1);self.assertEqual(self.save.count('throw error'),1)
  self.assertLess(self.save.index('context.rollback()'),self.save.index('throw error'));self.assertLess(self.save.index('throw error'),self.save.index('viewHistoryToken ='))
 def test_current_snapshot_diagnostics_validation_and_rollback_order_are_exact(self):
  tokens=['let inserted = context.insertedObjects','let updated = context.updatedObjects','let deleted = context.deletedObjects','Error saving managed object context','for object in inserted','try object.validateForInsert()','  Invalid inserted:','for object in updated','try object.validateForUpdate()','  Invalid updated:','context.rollback()','throw error']
  positions=[self.save.index(t)for t in tokens];self.assertEqual(positions,sorted(positions));self.assertEqual(self.save.count('.f_1000d468c().f_1000d4e0c('),3);self.assertNotIn('validateForDelete',self.save);self.assertNotIn('localizedDescription',self.save);self.assertNotIn('sorted',self.save)
  self.assertIn('private static let transactionDiagnostics = OriginalNamedDiagnostic.f_1000d4624(name: "DB")',self.s)
  for r in self.p['strings']:self.assertEqual(self.n['read'](int(r['address'],16),len(bytes.fromhex(r['bytes']))).hex(),r['bytes']);self.assertIn(r['text'],self.save)
  self.assertEqual(self.save.count('\\(object.entity.name ?? "?") \\(object.objectID) — \\(error)'),2)
 def test_store_still_publishes_only_after_success_and_retains_same_transaction_lifetime(self):
  store=(ROOT/'replica/Sources/PastoCore/ClipboardStore.swift').read_text();m=body(store,'private func mutateInTransaction<T>(historyAction:');tokens=['try persistence.commit(previous: remote','diskRevision = try revision()','publish(state)'];self.assertEqual([m.index(t)for t in tokens],sorted(m.index(t)for t in tokens));self.assertNotIn('catch',m);self.assertIn('withExtendedLifetime(transaction)',self.commit);self.assertEqual(self.commit.count('try context.performAndWait'),1)
 def test_native_List_validation_repair_remains_before_rollback_without_replacing_save_error(self):
  self.assertLess(self.save.index('try object.validateForInsert()'),self.save.index('context.rollback()'));s=(ROOT/'replica/Sources/PastoCore/OriginalManagedItem.swift').read_text();self.assertIn('override func validateForInsert()',s);self.assertIn('try super.validateForInsert()',s);self.assertNotIn('throw error',body(self.save,'for object in inserted'));self.assertNotIn('throw error',body(self.save,'for object in updated'))
 def test_surgical_three_deltas_reverse_all247_files_without_runtime_completion_claim(self):
  self.assertEqual(len(CHANGES),3);changed=[]
  for p,h in self.base['production'].items():
   if hashlib.sha256(pre_text_setter_return_bytes(ROOT/p)).hexdigest()!=h:changed.append(p)
   self.assertEqual(hashlib.sha256(pre_save_failure_rollback_bytes(ROOT/p)).hexdigest(),h)
  self.assertEqual(changed,[self.path]);self.assertEqual(pre_save_failure_rollback((self.ph/'before'/self.path).read_text()),(self.ph/'before'/self.path).read_text());self.assertFalse(self.p['runtime_executed']);self.assertFalse(self.p['full_function_migration_verified'])
if __name__=='__main__':unittest.main()
