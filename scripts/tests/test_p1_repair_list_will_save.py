"""List/Metadata willSave gates matched to native ARM branches, no CoreData execution."""
from pathlib import Path
import hashlib,itertools,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from source_entity_lifecycle_scope_contract import pre_source_entity_lifecycle_bytes
from item_shared_will_save_scope_contract import pre_item_shared_will_save
from list_will_save_scope_contract import CHANGES,pre_list_will_save,pre_list_will_save_bytes

class ListWillSave(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.phase=ROOT/'.local/p0-repair/phase-150';cls.p=json.loads((cls.phase/'list-will-save-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.path='replica/Sources/PastoCore/OriginalManagedItem.swift';cls.s=pre_item_shared_will_save((ROOT/cls.path).read_text());cls.before=(cls.phase/'before'/cls.path).read_text();cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n);cls.methods=[body(body(cls.s,c),'override func willSave()')for c in ['class PastoListEntity:','class PastoListMetadataEntity:']]
 def test_originals_binary_prior_hierarchy_and_SDK_declarations_are_bound(self):
  self.assertEqual(len(self.p['original_fragments']),3)
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for r in [self.p['binary'],self.p['decoder'],self.p['prior_evidence']]+self.p['sdk']:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
  prior=json.loads((ROOT/self.p['prior_evidence']['path']).read_text());parent=prior['original_classes'][-1];self.assertEqual(parent['address'],'0x100f98690');self.assertIn(('willSave','0x1003b4b94'),[(v['selector'],v['implementation'])for v in parent['methods']])
 def test_six_actual_selectors_and_twentyfour_instruction_words(self):
  self.assertEqual(len(self.p['selectors']),6)
  for r in self.p['selectors']:
   for key in ['stub','pointer','selector']:
    if key in r:
     v=r[key];self.assertEqual(self.n['read'](int(v['address'],16),len(bytes.fromhex(v['bytes']))).hex(),v['bytes'])
   self.assertEqual(bytes.fromhex(r['selector']['bytes']).rstrip(b'\0').decode(),r['name'])
  self.assertEqual(len(self.p['ARM_words']),24)
  for r in self.p['ARM_words']:self.assertEqual(self.n['read'](int(r['address'],16),4).hex(),r['bytes'])
 def test_original_author_and_updatedAt_small_strings_are_not_guessed(self):
  def small(addresses):return sum(((int.from_bytes(self.n['read'](a,4),'little')>>5)&65535)<<(16*i)for i,a in enumerate(addresses)).to_bytes(8,'little')
  self.assertEqual(small([0x1003b4a1c,0x1003b4a20,0x1003b4a24,0x1003b4a28]),b'syncAppl');self.assertEqual((int.from_bytes(self.n['read'](0x1003b4a14,4),'little')>>5)&65535,ord('y'))
  self.assertEqual(small([0x1003b4b24,0x1003b4b28,0x1003b4b2c,0x1003b4b30]),b'updatedA');self.assertEqual(((int.from_bytes(self.n['read'](0x1003b4b18,4),'little')>>5)&65535)-5,ord('t'))
 def test_actual_two_registered_classes_have_equal_callbacks_and_Item_unchanged(self):
  self.assertEqual(self.methods[0],self.methods[1]);self.assertEqual(self.s.count('override func willSave()'),2);self.assertEqual(body(self.s,'class PastoItemEntity:'),body(self.before,'class PastoItemEntity:'))
  model=(ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text();self.assertIn('NSStringFromClass(PastoListEntity.self)',model);self.assertIn('NSStringFromClass(PastoListMetadataEntity.self)',model)
 def test_callback_order_read_only_author_primitive_Date_and_super_tail(self):
  for s in self.methods:
   tokens=['let isSyncApply = managedObjectContext?.transactionAuthor == "syncApply"','if !isInserted && !isSyncApply && !changedValues().isEmpty','setPrimitiveValue(Date(), forKey: "updatedAt")','super.willSave()'];positions=[s.index(t)for t in tokens];self.assertEqual(positions,sorted(positions));self.assertTrue(s.rstrip().endswith('super.willSave()\n    }'))
   self.assertNotRegex(s,r'transactionAuthor\s*=(?!=)')
   for t in ['save(','async','Task','DispatchQueue','hasChanges','changedValuesForCurrentEvent','isDeleted','return','NotificationCenter','setValue(','CloudKit','FileManager']:self.assertNotIn(t,s)
 def test_source_boolean_gate_matches_actual_native_join_branches_exhaustively(self):
  expectedjoin=0x1003b4b5c
  for pc,reg in [(0x1003b4aa0,0),(0x1003b4aa4,23)]:
   w=int.from_bytes(self.n['read'](pc,4),'little');self.assertEqual(w&0x7f000000,0x37000000);self.assertEqual(w&31,reg);self.assertEqual((w>>19)&31,0);d=(w>>5)&0x3fff;d=d-(1<<14)if d&(1<<13)else d;self.assertEqual(pc+4*d,expectedjoin)
  pc=0x1003b4af4;w=int.from_bytes(self.n['read'](pc,4),'little');self.assertEqual(w&0x7f000000,0x34000000);self.assertEqual(w&31,22);d=(w>>5)&0x7ffff;d=d-(1<<19)if d&(1<<18)else d;self.assertEqual(pc+4*d,expectedjoin)
  terms=self.methods[0].split('        if ',1)[1].split(' {',1)[0].split(' && ');self.assertEqual(terms,['!isInserted','!isSyncApply','!changedValues().isEmpty'])
  for inserted,author,count in itertools.product([False,True],[None,'syncApply','local','syncapply'],[0,1,2]):
   sync=author=='syncApply';native_takes_update=not inserted and not sync and count!=0;values={'!isInserted':not inserted,'!isSyncApply':not sync,'!changedValues().isEmpty':count!=0};self.assertEqual(all(values[t]for t in terms),native_takes_update)
 def test_ten_old_methods_four_shared_sources_and_all247_file_inverse(self):
  self.assertEqual(len(self.p['unchanged_methods']),10)
  for r in self.p['unchanged_methods']:
   source=body(self.s,r['scope'])if r['scope']else self.s;self.assertEqual(hashlib.sha256(body(source,r['symbol']).encode()).hexdigest(),r['sha256'])
  for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_source_entity_lifecycle_bytes(ROOT/p)).hexdigest(),h)
  changed=[]
  for p,h in self.base['production'].items():
   if hashlib.sha256(pre_source_entity_lifecycle_bytes(ROOT/p)).hexdigest()!=h:changed.append(p)
   self.assertEqual(hashlib.sha256(pre_list_will_save_bytes(ROOT/p)).hexdigest(),h)
  self.assertEqual(changed,[self.path]);self.assertEqual(pre_list_will_save(self.s),self.before);self.assertEqual(pre_list_will_save(self.before),self.before)
 def test_one_shared_pattern_two_hunks_is_finite_not_all_Syncable_classes(self):
  self.assertEqual(len(CHANGES),1);self.assertEqual(CHANGES[0][3],2);self.assertEqual(self.p['function_id'],'Paste:0x1003b4984');self.assertFalse(self.p['runtime_executed']);self.assertFalse(self.p['full_function_migration_verified']);self.assertEqual(self.p['new_difference_records'],1);self.assertEqual(len(self.p['remaining']),2)

if __name__=='__main__':unittest.main()
