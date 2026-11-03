"""Original Stack owner/close/empty constructor evidence; no application execution."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from list_insert_validation_scope_contract import pre_list_insert_validation_bytes
from test_p0_repair_checksum_routing import original_fragment
from stack_close_session_scope_contract import CHANGES,pre_stack_close_session,pre_stack_close_session_bytes

class StackCloseSession(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.phase=ROOT/'.local/p0-repair/phase-147';cls.proof=json.loads((cls.phase/'stack-close-session-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.path='replica/Sources/Pasto/UI/ReplicaUIController.swift';cls.s=(ROOT/cls.path).read_text();cls.before=(cls.phase/'before'/cls.path).read_text();cls.n={};exec((ROOT/cls.proof['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n);cls.orig={r['address']:original_fragment((ROOT/r['path']).read_text(),r['address'][2:])for r in cls.proof['original_fragments']}
 def ordered(self,s,tokens):
  pos=0
  for t in tokens:pos=s.index(t,pos)+len(t)
 def test_fourteen_original_fragments_and_two_binary_inputs_bound(self):
  self.assertEqual(len(self.proof['original_fragments']),14)
  for r in self.proof['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for r in [self.proof['binary'],self.proof['decoder']]:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
 def test_real_original_show_owns_slot_and_captures_weak_completion(self):
  s=self.orig['0x1000a85d8'];self.ordered(s,['if (*(long *)(unaff_x20 + 0xd8) == 0)','FUN_10001148c()','*(undefined8 *)(unaff_x20 + 0xd8) = uVar1','_swift_weakInit','FUN_100217e4c(&local_50,FUN_1000a9998'])
  s=self.orig['0x100217e4c'];self.ordered(s,['WindowController::completionHandler','*puVar1 = param_2','puVar1[1] = param_3','objc_stub::showWindow_'])
  self.assertIn('FUN_1000a85d8()',self.orig['0x1000a9534']);self.assertIn('objc_stub::close',self.orig['0x1000a9534'])
 def test_weak_callback_clears_exact_owner_slot_and_releases_old_controller(self):
  self.assertIn('FUN_1000a86c0()',self.orig['0x1000a9998'])
  self.ordered(self.orig['0x1000a86c0'],['_swift_weakLoadStrong()','if (param_2 != 0)','*(undefined8 *)(param_2 + 0xd8) = 0','_swift_release()'])
  words={v['address']:v['bytes']for v in self.proof['ARM_words']};self.assertEqual(words['0x1000a86dc'],'1f6c00f9');self.assertEqual(words['0x1000a86d8'],'136c40f9')
 def test_original_actual_parent_and_dynamic_close_slot_reach_core(self):
  self.assertEqual([v['target']for v in self.proof['metadata_slots']],['0x100f96570','0x1002182a4','0x1002182a4'])
  for r in self.proof['metadata_slots']:
   a=int(r['address'],16);v,_=self.n['reachable_pointer'](a);self.assertEqual(self.n['read'](a,8).hex(),r['bytes']);self.assertEqual(hex(self.n['base']+(v&((1<<36)-1))),r['target'])
  self.assertIn('+ 0x108)',self.orig['0x1002184dc'])
 def test_eighteen_ARM_words_and_actual_content_clear_selector_bound(self):
  self.assertEqual(len(self.proof['ARM_words']),18)
  for r in self.proof['ARM_words']:self.assertEqual(self.n['read'](int(r['address'],16),4).hex(),r['bytes'])
  r=self.proof['selector'];self.assertEqual(self.n['read'](int(r['stub'],16),12).hex(),r['stub_bytes']);self.assertEqual(self.n['read'](int(r['address'],16),8).hex(),r['bytes']);o=self.n['offset'](int(r['target'],16));self.assertEqual(self.n['raw'][o:self.n['raw'].index(b'\0',o)].decode(),'setContentViewController:')
 def test_original_nonmodal_close_precedes_callback_then_content_release(self):
  s=self.orig['0x1002182a4'];self.ordered(s,['_objc_msgSendSuper2(super,"close")','WindowController::completionHandler','(*pcVar4)(param_1)','*puVar1 = 0','objc_stub::setContentViewController_((ID)unaff_x20,0)'])
  self.ordered(self.orig['0x1000843a8'],['objc_stub::view','objc_stub::window(','objc_stub::windowController','objc_stub::close'])
 def test_original_constructor_and_destructor_bind_queue_to_content_lifetime(self):
  self.ordered(self.orig['0x100084f14'],['PasteStackViewController::snippets','PTR___swiftEmptyArrayStorage_','"initWithCoder:"'])
  self.ordered(self.orig['0x100083d18'],['_swift_bridgeObjectRelease','snippets','observer'])
  self.ordered(self.orig['0x100083bd0'],['FUN_1001eae90','NSNotificationCenter::removeObserver_','"dealloc"'])
 def test_actual_close_releases_native_window_then_owner_then_host_and_observer(self):
  s=body(self.s,'func hideStack()');self.ordered(s,['guard let closingController = stackWindowController','let closingWindow = stackWindow','closingController.close()','stackWindowController = nil','closingController.contentViewController = nil','closingWindow?.contentView = nil','stackWindow = nil','stackTableController = nil','NotificationCenter.default.removeObserver(stackCaptureObserver)','stackCaptureObserver = nil','if state.stackIDs.isEmpty { stackDidChange?() }','else { state.stackIDs.removeAll() }'])
  for t in ['orderOut','store.','save(','async','Task {','try ','clearHistory','delete']:self.assertNotIn(t,s)
 def test_session_queue_not_loaded_or_saved_but_direction_and_legacy_format_stay(self):
  self.assertNotIn('store.preferences.stackItemIDs',self.s)
  s=body(self.s,'@Published var stackIDs:');self.ordered(s,['let retainedIDs = Set(stackIDs)','stackRestoreInputs = stackRestoreInputs.filter','guard oldValue != stackIDs else','controller?.stackContentsChanged()']);self.assertNotIn('save',s)
  s=body(self.s,'func reverseStack()');self.ordered(s,['f_10008468c(&stackIDs)','stackReversed.toggle()','try store.save()'])
  model=(ROOT/'replica/Sources/PastoCore/Models.swift').read_text();self.assertIn('try values.encode(stackItemIDs, forKey: .stackItemIDs)',model)
 def test_twelve_unrelated_methods_and_six_shared_sources_stay_byte_identical(self):
  self.assertEqual(len(self.proof['unchanged_methods']),12);self.assertEqual(len(self.proof['shared_sources']),6)
  for r in self.proof['unchanged_methods']:self.assertEqual(hashlib.sha256(body(self.s,r['symbol']).encode()).hexdigest(),r['sha256'])
  for p,h in self.proof['shared_sources'].items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),h)
  self.assertIn('if stackWindow == nil',body(self.s,'func showStack()'));self.assertIn('stackCaptureObserver = NotificationCenter.default.addObserver',body(self.s,'func showStack()'))
 def test_three_exact_source_hunks_and_all247_file_reversal(self):
  self.assertEqual(len(CHANGES),3);self.assertEqual(pre_stack_close_session(self.s),self.before);self.assertEqual(pre_stack_close_session(self.before),self.before)
  changed=[]
  for p,h in self.base['production'].items():
   raw=pre_list_insert_validation_bytes(ROOT/p)
   if hashlib.sha256(raw).hexdigest()!=h:changed.append(p)
   self.assertEqual(hashlib.sha256(pre_stack_close_session_bytes(ROOT/p)).hexdigest(),h)
  self.assertEqual(changed,[self.path]);self.assertEqual(len(self.base['production']),247)
 def test_scope_does_not_claim_modal_UI_DI_or_full_lifecycle(self):
  self.assertFalse(self.proof['runtime_executed']);self.assertFalse(self.proof['full_function_migration_verified']);self.assertEqual(self.proof['new_difference_records'],1);self.assertEqual(len(self.proof['adaptations']),3);self.assertEqual(len(self.proof['remaining']),2)

if __name__=='__main__':unittest.main()
