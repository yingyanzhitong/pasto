"""Editor display model reads: source/native evidence without framework execution."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
D=ROOT/'.local/p0-p1-parent-review/2026-11-03-text-display'
CORE='replica/Sources/PastoCore/OriginalPreviewAttributedText.swift'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

class DisplayReadContracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.p=json.loads((D/'contract.json').read_text());cls.base=json.loads((D/'baseline.json').read_text())
  cls.core=(ROOT/CORE).read_text();cls.n={}
  exec((ROOT/cls.p['decoder']['path']).read_text().split('selectors=[]',1)[0],cls.n)
 def test_all_original_and_current_source_inputs_fresh(self):
  cache={};self.assertEqual(len(self.p['original_fragments']),13)
  for r in self.p['original_fragments']:
   path=ROOT/r['path']
   if path not in cache:cache[path]=source_fragments(path)
   self.assertEqual(cache[path][r['function_id'].split(':')[1]]['sha256'],r['sha256'])
  for k in ['binary','decoder']:self.assertEqual(sha(ROOT/self.p[k]['path']),self.p[k]['sha256'])
  for k in ['current_sources','shared_sources']:
   for p,h in self.p[k].items():self.assertEqual(sha(ROOT/p),h,p)
 def test_native_ranges_and_all_branch_targets(self):
  self.assertEqual(len(self.p['machine_ranges']),13);self.assertEqual(len(self.p['branches']),229)
  for r in self.p['machine_ranges']:
   data=self.n['read'](int(r['address'],16),int(r['end'],16)-int(r['address'],16))
   self.assertEqual(data.hex(),r['bytes']);self.assertEqual(hashlib.sha256(data).hexdigest(),r['sha256'])
  for r in self.p['branches']:
   pc=int(r['pc'],16);w=struct.unpack('<I',self.n['read'](pc,4))[0];self.assertEqual(hex(w),r['word'])
   v=w&0x3ffffff
   if v&(1<<25):v-=1<<26
   self.assertEqual(hex(pc+v*4),r['target'])
 def test_selector_and_import_fixups_reproduce_recorded_names(self):
  self.assertEqual(len(self.p['selectors']),28);self.assertEqual(len(self.p['imports']),141)
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
 def test_native_editability_reads_bracket_selected_and_probe_loads(self):
  edges={r['pc']:r['target']for r in self.p['branches']}
  self.assertEqual(edges['0x1003eb354'],'0x100213188');self.assertEqual(edges['0x1003eb3b8'],'0x100213188')
  self.assertEqual(edges['0x1003eb3ec'],'0x1003095bc');self.assertEqual(edges['0x1003eb484'],'0x100212e78')
  words={0x1003eb374:0x9100a314,0x1003eb37c:0x91008314,0x1003eb394:0xf9400280,
         0x1003eb3c8:0x37000576,0x1003eb3e0:0xf9401300}
  for pc,w in words.items():self.assertEqual(struct.unpack('<I',self.n['read'](pc,4))[0],w)
  self.assertLess(0x1003eb354,0x1003eb394);self.assertLess(0x1003eb394,0x1003eb3b8);self.assertLess(0x1003eb3b8,0x1003eb3e0)
  selector=next(r['name']for r in self.p['selectors']if r['function_id']=='Paste:0x100213188')
  self.assertEqual(selector,'isEditable')
 def test_live_baselines_only_requested_after_each_editability_read(self):
  tail=self.core[self.core.index('public static func f_1003eb330('):];sig=tail[:tail.index(' -> Int')]
  self.assertIn('original: @autoclosure () -> NSAttributedString',sig)
  self.assertIn('editing: @autoclosure () -> NSAttributedString',sig)
  s=body(self.core,'public static func f_1003eb330(')
  self.assertEqual(s.count('editor.isEditable'),2)
  self.assertIn('var displayed = editor.isEditable ? editing() : original()',s)
  self.assertIn('if !editor.isEditable, f_1003095bc(original())',s)
  order=['var displayed =','if !editor.isEditable','NSMutableAttributedString(attributedString: displayed)',
         'plain.removeAttribute(.foregroundColor','plain.removeAttribute(.backgroundColor','f_100212e78(displayed, editor: editor)']
  self.assertEqual([s.index(x)for x in order],sorted(s.index(x)for x in order))
  self.assertNotIn('displayed = original()',s)
 def test_all_real_display_consumers_keep_live_model_expressions(self):
  ui=(ROOT/'replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift').read_text()
  v=body(ui,'private final class ReplicaInlineTextPreviewContent:')
  s=body(v,'private func displayStoredModel()')
  self.assertIn('f_1003eb330(original: originalText, editing: editingText, editor: text)',s)
  self.assertLess(s.index('f_1003eb330'),s.index('f_1003eb4a8'))
  self.assertIn('nativeTextModel?.originalText ?? fallbackOriginalText',v)
  self.assertIn('nativeTextModel?.editingText ?? fallbackEditingText',v)
  for sig in ['func beginPreviewEditing()','func cancelPreviewEditing()']:
   self.assertIn('displayStoredModel()',body(v,sig));self.assertNotIn('reloadStoredContent()',body(v,sig))
  self.assertIn('guard let self, !self.text.isEditable else { return }\n                self.displayStoredModel()',v)
 def test_color_helper_is_an_unchanged_held_value_analysis(self):
  p='replica/Sources/PastoCore/OriginalPreviewTextColors.swift'
  self.assertEqual(sha(ROOT/p),self.base['files'][p])
  s=(ROOT/p).read_text()
  self.assertIn('f_1003eb4a8(original: NSAttributedString, editor:',s)
  s=body(s,'public static func f_1003eb4a8(')
  self.assertIn('f_1003095bc(original)',s)
  self.assertLess(s.index('editor.backgroundColor = background'),s.index('editor.textColor = foreground'))
  self.assertIn('if isPlain, !editor.isEditable',s)
 def test_only_one_method_changed_and_every_other_existing_file_preserved(self):
  files=self.base['files'];prod={p:h for p,h in files.items()if p.startswith('replica/Sources/')}
  self.assertEqual(len(prod),248)
  self.assertEqual({p for p,h in prod.items()if sha(ROOT/p)!=h},{CORE})
  current={str(p.relative_to(ROOT))for p in(ROOT/'replica/Sources').rglob('*')if p.is_file()}
  self.assertEqual(current,set(prod))
  for p,h in files.items():
   if p!=CORE:self.assertEqual(sha(ROOT/p),h,p)
  old=(D/'before'/CORE).read_text()
  before=body(old,'public static func f_1003eb330(');after=body(self.core,'public static func f_1003eb330(')
  expected=old.replace('f_1003eb330(original: NSAttributedString, editing: NSAttributedString,',
   'f_1003eb330(original: @autoclosure () -> NSAttributedString,\n                                  editing: @autoclosure () -> NSAttributedString,',1)
  expected=expected.replace(before,after,1)
  self.assertEqual(expected,self.core)
  self.assertEqual(body(old,'public static func f_1003c0be0('),body(self.core,'public static func f_1003c0be0('))
 def test_no_scope_growth_or_full_migration_claim(self):
  scope=json.loads((ROOT/'reports/replica/p0-p1-review-scope-v6.json').read_text())
  self.assertEqual(scope['denominator'],959)
  self.assertEqual([r['priority']for r in scope['functions']if r['function_id']=='Paste:0x1003eb330'],['P1'])
  self.assertEqual(self.p['primary_function_ids'],['Paste:0x1003eb330'])
  for k in ['full_function_migration_verified','compiled','framework_executed']:self.assertFalse(self.p[k])


def display_trace(states,values,on_editability=None,plain=True):
 events=[];states=iter(states)
 def editable():
  flag=next(states);events.append(('isEditable',flag))
  if on_editability:on_editability(values,len([r for r in events if r[0]=='isEditable']))
  return flag
 def read(key):events.append(('read',key,values[key]));return values[key]
 shown=read('editing')if editable()else read('original')
 if not editable():
  probe=read('original');events.append(('plain-test',probe))
  if plain:events.append(('remove-colors',shown))
 events.append(('display',shown))
 return events

class DisplayReadTraceModels(unittest.TestCase):
 """Python access-order witnesses; do not execute NSTextView or attributed strings."""
 def test_editable_twice_reads_only_editing(self):
  self.assertEqual(display_trace([True,True],dict(original='o',editing='e')),
   [('isEditable',True),('read','editing','e'),('isEditable',True),('display','e')])
 def test_noneditable_twice_reads_original_for_selection_and_probe(self):
  events=display_trace([False,False],dict(original='o',editing='e'))
  self.assertEqual(events,[('isEditable',False),('read','original','o'),('isEditable',False),('read','original','o'),('plain-test','o'),('remove-colors','o'),('display','o')])
 def test_first_read_reentrancy_updates_actual_selected_value(self):
  def update(values,n):
   if n==1:values['editing']='new-edit'
  events=display_trace([True,True],dict(original='o',editing='old-edit'),update)
  self.assertEqual(events[-1],('display','new-edit'))
 def test_second_read_changes_probe_but_does_not_replace_selected_string(self):
  def update(values,n):
   if n==2:values['original']='new-original';values['editing']='new-edit'
  events=display_trace([True,False],dict(original='o',editing='selected-edit'),update)
  self.assertIn(('plain-test','new-original'),events)
  self.assertIn(('remove-colors','selected-edit'),events)
  self.assertEqual(events[-1],('display','selected-edit'))
 def test_first_false_second_true_does_not_request_plain_probe(self):
  events=display_trace([False,True],dict(original='o',editing='e'))
  self.assertEqual(events,[('isEditable',False),('read','original','o'),('isEditable',True),('display','o')])
 def test_rich_probe_does_not_remove_colors(self):
  events=display_trace([False,False],dict(original='rich',editing='e'),plain=False)
  self.assertNotIn(('remove-colors','rich'),events);self.assertEqual(events[-1],('display','rich'))

if __name__=='__main__':unittest.main()
