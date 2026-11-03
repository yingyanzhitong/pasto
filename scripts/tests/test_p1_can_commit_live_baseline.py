"""Commit eligibility: native slot timing and current-source callback contracts only."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
D=ROOT/'.local/p0-p1-parent-review/2026-11-03-can-commit'
CORE='replica/Sources/PastoCore/OriginalPreviewAttributedText.swift'
UI='replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

class LiveBaselineContracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.p=json.loads((D/'contract.json').read_text());cls.base=json.loads((D/'baseline.json').read_text())
  cls.core=(ROOT/CORE).read_text();cls.ui=(ROOT/UI).read_text()
  cls.view=body(cls.ui,'private final class ReplicaInlineTextPreviewContent:')
  cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split('selectors=[]',1)[0],cls.n)
 def test_original_fragments_and_current_source_hashes(self):
  cache={};self.assertEqual(len(self.p['original_fragments']),15)
  for r in self.p['original_fragments']:
   path=ROOT/r['path']
   if path not in cache:cache[path]=source_fragments(path)
   self.assertEqual(cache[path][r['function_id'].split(':')[1]]['sha256'],r['sha256'])
  for k in ['binary','decoder']:
   self.assertEqual(sha(ROOT/self.p[k]['path']),self.p[k]['sha256'])
  for k in ['current_sources','shared_sources']:
   for p,h in self.p[k].items():self.assertEqual(sha(ROOT/p),h,p)
 def test_all_native_ranges_and_branch_targets(self):
  self.assertEqual(len(self.p['machine_ranges']),15);self.assertEqual(len(self.p['branches']),268)
  for r in self.p['machine_ranges']:
   data=self.n['read'](int(r['address'],16),int(r['end'],16)-int(r['address'],16))
   self.assertEqual(data.hex(),r['bytes']);self.assertEqual(hashlib.sha256(data).hexdigest(),r['sha256'])
  for r in self.p['branches']:
   pc=int(r['pc'],16);w=struct.unpack('<I',self.n['read'](pc,4))[0]
   self.assertEqual(hex(w),r['word']);v=w&0x3ffffff
   if v&(1<<25):v-=1<<26
   self.assertEqual(hex(pc+4*v),r['target'])
 def test_selector_and_import_names_rebound_from_fixups(self):
  self.assertEqual(len(self.p['selectors']),28);self.assertEqual(len(self.p['imports']),178)
  raw=self.n['raw'];fixup=self.n['fixup'][0];h=struct.unpack_from('<7I',raw,fixup)
  for r in self.p['selectors']+self.p['imports']:
   value,chain=self.n['reachable_pointer'](int(r['pointer'],16));self.assertEqual(chain,r['chain'])
   if 'ordinal'in r:
    self.assertTrue(value>>63);self.assertEqual(value&0xffffff,r['ordinal'])
    entry=struct.unpack_from('<I',raw,fixup+h[2]+4*r['ordinal'])[0];at=fixup+h[3]+(entry>>9)
    self.assertEqual(raw[at:raw.index(b'\0',at)].decode(),r['name'])
   else:
    self.assertFalse(value>>63);at=self.n['base']+(value&((1<<36)-1))
    self.assertEqual(hex(at),r['target']);self.assertEqual(self.n['read'](at,len(r['name'])+1),r['name'].encode()+b'\0')
 def test_native_enumeration_precedes_selected_slot_reload(self):
  rows=self.p['model_slot_instructions']
  self.assertEqual([r['word']for r in rows],['0x91008295','0xf9401280','0x942103d6','0x9100a295','0xf94002b4'])
  for r in rows:self.assertEqual(self.n['read'](int(r['address'],16),4).hex(),r['bytes'])
  calls={r['pc']:r['target']for r in self.p['branches']}
  self.assertEqual(calls['0x1003c0d28'],'0x100c01c80')
  selectors={r['stub']:r['name']for r in self.p['selectors']}
  self.assertEqual(selectors['0x100c01c80'],'enumerateAttributesInRange:options:usingBlock:')
 def test_real_editor_installs_callback_and_calls_model(self):
  r=self.p['installed_callback_pointer'][0];pc=int(r['address'],16)
  self.assertEqual(self.n['read'](pc,8).hex(),r['bytes'])
  a,b=struct.unpack('<2I',self.n['read'](pc,8));v=((a>>5)&0x7ffff)*4+((a>>29)&3)
  if v&(1<<20):v-=1<<21
  self.assertEqual((pc&~4095)+(v<<12)+((b>>10)&4095),0x1003ec380)
  edges={(r['function_id'],r['target'])for r in self.p['branches']}
  self.assertIn(('Paste:0x1003ec380','0x1003eb64c'),edges)
  self.assertIn(('Paste:0x1003eb64c','0x1003c0be0'),edges)
 def test_native_callback_nil_gate_saved_register_and_release_order(self):
  word=lambda pc:struct.unpack('<I',self.n['read'](pc,4))[0]
  self.assertEqual(word(0x1003eb69c),0xf94002f6) # saved callback x22
  w=word(0x1003eb6a0);self.assertEqual(w&0xff00001f,0xb4000016)
  v=(w>>5)&0x7ffff
  if v&(1<<18):v-=1<<19
  self.assertEqual(0x1003eb6a0+v*4,0x1003eb6f8) # nil skips model test, keeps existing footer tail
  calls={r['pc']:r['target']for r in self.p['branches']}
  self.assertEqual(calls['0x1003eb6d0'],'0x1003c0be0')
  self.assertEqual(calls['0x1003eb6dc'],'0x100bfc9c0')
  self.assertEqual(word(0x1003eb6e8),0xd63f02c0) # invokes saved x22 after VM release
  self.assertEqual(word(0x1003c0c40)&0xff00001f,0xb4000008) # candidate empty gate before baseline
 def test_empty_candidate_gate_before_baseline_and_lazy_selected_read(self):
  sig=self.core[self.core.index('public static func f_1003c0be0('):]
  sig=sig[:sig.index(' -> Bool')]
  self.assertIn('original: @autoclosure () -> NSAttributedString',sig)
  self.assertIn('editing: @autoclosure () -> NSAttributedString',sig)
  s=body(self.core,'public static func f_1003c0be0(')
  order=['guard !candidate.string.isEmpty','let isPlain = f_1003095bc(original())','return (isPlain ? editing() : original()) != candidate']
  self.assertEqual([s.index(x)for x in order],sorted(s.index(x)for x in order))
  self.assertEqual(s.count('original()'),2);self.assertEqual(s.count('editing()'),1)
 def test_current_callback_snapshot_precedes_comparison_and_is_invoked(self):
  s=body(self.view,'init(state: ReplicaUIState, item: ClipboardItem?, input: ClipboardRestoreItem?)')
  order=['contentObservation = document.$content.sink','guard let self, let onCanCommitEditing = self.onCanCommitEditing',
         'self.canCommit = OriginalPreviewAttributedText.f_1003c0be0(',
         'candidate: content, original: self.originalText, editing: self.editingText)',
         'onCanCommitEditing(self.canCommit)']
  self.assertEqual([s.index(x)for x in order],sorted(s.index(x)for x in order))
  self.assertNotIn('self.onCanCommitEditing?(self.canCommit)',s)
  self.assertIn('nativeTextModel?.originalText ?? fallbackOriginalText',self.view)
  self.assertIn('nativeTextModel?.editingText ?? fallbackEditingText',self.view)
 def test_only_two_small_source_changes_and_all_other_inputs_preserved(self):
  files=self.base['files'];prod={p:h for p,h in files.items()if p.startswith('replica/Sources/')}
  self.assertEqual(len(prod),248)
  self.assertEqual({p for p,h in prod.items()if sha(ROOT/p)!=h},{CORE,UI})
  current={str(p.relative_to(ROOT))for p in(ROOT/'replica/Sources').rglob('*')if p.is_file()}
  self.assertEqual(current,set(prod))
  for p,h in files.items():
   if p not in [CORE,UI]:self.assertEqual(sha(ROOT/p),h,p)
  before=(D/'before'/CORE).read_text();start=before.index('    public static func f_1003c0be0(');end=before.index('\n    /// PastePlatform',start)
  nowstart=self.core.index('    public static func f_1003c0be0(');nowend=self.core.index('\n    /// PastePlatform',nowstart)
  self.assertEqual(before[:start]+before[end:],self.core[:nowstart]+self.core[nowend:])
  before=(D/'before'/UI).read_text()
  expected=before.replace('guard let self else { return }\n                self.canCommit',
   'guard let self, let onCanCommitEditing = self.onCanCommitEditing else { return }\n                self.canCommit',1).replace('self.onCanCommitEditing?(self.canCommit)','onCanCommitEditing(self.canCommit)',1)
  self.assertEqual(expected,self.ui)
 def test_actual_text_transaction_rollback_and_reload_after_consumed_error(self):
  selectors=[r['name']for r in self.p['selectors']if r['function_id']=='Paste:0x100304108']
  self.assertEqual(selectors,['hasChanges','insertedObjects','updatedObjects','deletedObjects','validateForInsert:',
   'entity','name','objectID','description','validateForUpdate:','entity','name','objectID','description','rollback'])
  persistence=(ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text()
  commit=body(persistence,'func commit<T>(previous:')
  order=['var outcome = try operation(transaction)','if context.hasChanges','try OriginalObjCExceptionBridge.f_1002ff9c8 { try context.save() }',
   'let inserted = context.insertedObjects','let updated = context.updatedObjects','let deleted = context.deletedObjects',
   'try object.validateForInsert()','try object.validateForUpdate()','context.rollback()','throw error']
  self.assertEqual([commit.index(x)for x in order],sorted(commit.index(x)for x in order))
  text_commit=body(self.view,'func commitPreviewEditing()')
  self.assertLess(text_commit.index('catch {'),text_commit.index('reloadStoredContent()'))
  self.assertNotIn('presentError',text_commit)
  self.assertIn('nativeTextModel.reload()',body(self.view,'private func reloadStoredContent()'))
 def test_fixed_scope_no_support_function_inflation_or_full_claim(self):
  s=json.loads((ROOT/'reports/replica/p0-p1-review-scope-v6.json').read_text())
  self.assertEqual(s['denominator'],959)
  self.assertEqual([r['priority']for r in s['functions']if r['function_id']=='Paste:0x1003c0be0'],['P1'])
  self.assertEqual(self.p['primary_function_ids'],['Paste:0x1003c0be0'])
  self.assertFalse(self.p['full_function_migration_verified']);self.assertFalse(self.p['compiled']);self.assertFalse(self.p['framework_executed'])


def can_commit(candidate,original,editing,plain):
 if not candidate:return False
 is_plain=plain(original())
 return (editing()if is_plain else original())!=candidate

class ReadOrderTraceModels(unittest.TestCase):
 """Callable traces describe intended Swift lazy reads; no attributed-string runtime is executed."""
 def evaluate(self,candidate,initial,updated,is_plain):
  values=dict(initial);events=[]
  def original():events.append(('read','original',values['original']));return values['original']
  def editing():events.append(('read','editing',values['editing']));return values['editing']
  def plain(value):events.append(('enumerate',value));values.update(updated);return is_plain
  return can_commit(candidate,original,editing,plain),events
 def test_empty_candidate_does_not_read_either_baseline(self):
  result,events=self.evaluate('',{'original':'a','editing':'b'},{},True)
  self.assertFalse(result);self.assertEqual(events,[])
 def test_plain_reentrant_model_update_uses_new_editing_baseline(self):
  result,events=self.evaluate('new-edit',{'original':'old-plain','editing':'old-edit'},{'editing':'new-edit'},True)
  self.assertFalse(result);self.assertEqual(events,[('read','original','old-plain'),('enumerate','old-plain'),('read','editing','new-edit')])
 def test_rich_reentrant_update_rereads_original_not_old_enumerated_value(self):
  result,events=self.evaluate('new-rich',{'original':'old-rich','editing':'old-edit'},{'original':'new-rich'},False)
  self.assertFalse(result);self.assertEqual(events[-1],('read','original','new-rich'));self.assertNotIn(('read','editing','old-edit'),events)
 def test_unchanged_baselines_keep_existing_empty_plain_and_rich_behavior(self):
  for plain in [False,True]:
   for candidate in ['original','editing','changed','']:
    initial={'original':'original','editing':'editing'}
    actual,_=self.evaluate(candidate,initial,{},plain)
    self.assertEqual(actual,bool(candidate)and candidate!=initial['editing'if plain else'original'])
 def test_nil_callback_skips_comparison(self):
  events=[]
  def consume(callback):
   if callback is None:return
   events.append('compare');callback(True)
  consume(None);self.assertEqual(events,[])
 def test_callback_replaced_during_compare_invokes_original_snapshot(self):
  events=[];slot=[lambda value:events.append(('first',value))]
  callback=slot[0]
  def original():slot[0]=lambda value:events.append(('replacement',value));return'original'
  result=can_commit('changed',original,lambda:'editing',lambda _:False)
  callback(result)
  self.assertEqual(events,[('first',True)])

if __name__=='__main__':unittest.main()
