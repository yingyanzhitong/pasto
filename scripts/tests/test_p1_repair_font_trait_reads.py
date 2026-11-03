"""Font descriptor reads/fallbacks and actual editing/Undo consumers: source/Mach-O only."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from font_trait_reads_scope_contract import CHANGES,HISTORICAL_TEST_CHANGES,pre_font_trait_reads,pre_font_trait_reads_bytes,pre_font_trait_reads_history_bytes
class FontTraitReadContracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ph=ROOT/'.local/p0-repair/phase-188';cls.p=json.loads((cls.ph/'font-trait-reads-contract.json').read_text());cls.b=json.loads((cls.ph/'baseline.json').read_text());cls.traits=(ROOT/'replica/Sources/PastoCore/OriginalPreviewTextTraits.swift').read_text();cls.text=(ROOT/'replica/Sources/PastoCore/OriginalPreviewAttributedText.swift').read_text();cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
 def order(self,s,tokens):
  cursor=0
  for t in tokens:cursor=s.index(t,cursor)+len(t)
 def test15_original_fragments_binary_and_decoder_are_fresh(self):
  self.assertEqual(len(self.p['original_fragments']),15)
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for k in ['binary','decoder']:
   r=self.p[k];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
 def test10_complete_ranges273_actual_direct_branches(self):
  self.assertEqual(len(self.p['machine_ranges']),10);self.assertEqual(len(self.p['branches']),273)
  for r in self.p['machine_ranges']:
   d=self.n['read'](int(r['address'],16),int(r['end'],16)-int(r['address'],16));self.assertEqual(d.hex(),r['bytes']);self.assertEqual(hashlib.sha256(d).hexdigest(),r['sha256'])
  for r in self.p['branches']:
   a=int(r['call'],16);w=struct.unpack('<I',self.n['read'](a,4))[0];self.assertEqual(hex(w),r['word']);v=w&0x3ffffff;v=v-(1<<26)if v&(1<<25)else v;self.assertEqual(hex(a+v*4),r['target'])
 def test29_actual_property_selectors_resolve_chained_pointer_bytes(self):
  self.assertEqual(len(self.p['selectors']),29)
  for r in self.p['selectors']:
   v,c=self.n['reachable_pointer'](int(r['pointer'],16));self.assertEqual(c,r['chain']);self.assertFalse(v>>63);dest=self.n['base']+(v&((1<<36)-1));self.assertEqual(hex(dest),r['target']);self.assertEqual(self.n['read'](dest,len(r['name'])+1),r['name'].encode()+b'\0')
 def test4_real_weak_and_actor_imports(self):
  self.assertEqual(len(self.p['imports']),4)
  for r in self.p['imports']:
   v,c=self.n['reachable_pointer'](int(r['pointer'],16));self.assertEqual(c,r['chain']);self.assertTrue(v>>63);f=self.n['fixup'][0];raw=self.n['raw'];h=struct.unpack_from('<7I',raw,f);e=struct.unpack_from('<I',raw,f+h[2]+4*(v&0xffffff))[0];o=f+h[3]+(e>>9);self.assertEqual(raw[o:raw.index(b'\0',o)].decode(),r['symbol'])
  self.assertIn('_swift_unknownObjectWeakLoadStrong',[r['symbol']for r in self.p['imports']])
 def test_native_property_read_counts_are_bound_per_original_function(self):
  p=self.p['native_getter_counts'];self.assertEqual([p[a]['fontDescriptor']for a in ['0x100207db8','0x100207648','0x1000f3f6c']],[2,3,2]);self.assertEqual([p[a]['symbolicTraits']for a in ['0x100207db8','0x100207648','0x1000f3f6c']],[2,1,0]);self.assertEqual(p['0x100207648']['fontDescriptorWithSymbolicTraits:'],2)
 def test_bold_italic_have_separate_descriptor_and_trait_reads(self):
  s=body(self.traits,'public static func f_100207db8(');self.assertEqual(s.count('font.fontDescriptor.symbolicTraits'),2);self.order(s,['font.fontDescriptor.symbolicTraits.contains(.bold)','result.insert(.bold)','font.fontDescriptor.symbolicTraits.contains(.italic)','result.insert(.italic)']);self.assertNotIn('let traits =',s);self.assertIn('underline == 1',s);self.assertIn('strike == 1',s)
 def test_toggle_reads_saved_traits_then_fresh_clear_descriptor(self):
  s=body(self.traits,'public static func f_100207648(');self.order(s,['let originalTraits = font.fontDescriptor.symbolicTraits','let cleared = OriginalPreviewAttributedText.descriptorWithTraits(font.fontDescriptor, traits: [])','let changed = cleared.flatMap { descriptor in','let mask:','let traits = remove ? originalTraits.subtracting(mask) : originalTraits.union(mask)','return OriginalPreviewAttributedText.descriptorWithTraits(descriptor, traits: traits)']);self.assertEqual(s.count('font.fontDescriptor'),3)
 def test_toggle_lazy_fallback_descriptor_precedes_point_size_and_nil_removes_font(self):
  s=body(self.traits,'public static func f_100207648(');self.order(s,['NSFont(descriptor: changed ?? font.fontDescriptor, size: font.pointSize)','result[.font] = changedFont','else { result.removeValue(forKey: .font) }']);self.assertIn('guard let font = attributes[.font] as? NSFont else { return result }',s);self.assertNotIn('changed ?? descriptor',s)
 def test_normalizer_rereads_only_on_descriptor_failure_and_nil_font_retains_input(self):
  s=body(self.text,'public static func f_1000f3f6c(');self.order(s,['let descriptor = font.fontDescriptor','let cleared = descriptorWithTraits(descriptor, traits: [])','let requested = cleared.flatMap { descriptorWithTraits($0, traits: traits) }','NSFont(descriptor: requested ?? font.fontDescriptor, size: font.pointSize) ?? font']);self.assertEqual(s.count('font.fontDescriptor'),2)
 def test_editor_normalization_actual_consumer_and_trait_action_bound(self):
  calls={r['call']:r['target']for r in self.p['branches']};self.assertIn('0x1000f3f6c',[r['target']for r in self.p['branches']if 0x1003c1860<=int(r['call'],16)<0x1003c1b00]);self.assertIn('0x1002072a0',[r['target']for r in self.p['branches']if 0x100213674<=int(r['call'],16)<0x1002136e4]);self.assertIn('0x100213674',[r['target']for r in self.p['branches']if 0x1002160c4<=int(r['call'],16)<0x1002160f0]);self.assertIn('f_1000f3f6c(font: f_1000f3ef4(), traits: traits)',body(self.text,'public static func f_1003c1860('))
 def test_current_recovered_toolbar_path_uses_same_four_traits_and_same_editor(self):
  doc=(ROOT/'replica/Sources/Pasto/UI/RichTextEditor.swift').read_text();s=body(doc,'func toggle(');start=s.index('if usesRecoveredContentEvents {');end=s.index('        view.window?',start);branch=s[start:end];self.assertIn('OriginalPreviewTextTraits.f_1002072a0(trait, editor: view)',branch);self.assertNotIn('makeFirstResponder',branch)
  adapter=(ROOT/'replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift').read_text();self.assertIn('document.usesRecoveredContentEvents = true',adapter)
  for v in ['bold','italic','underline','strikethrough']:self.assertIn('document?.toggle(.'+v+')',adapter)
 def test_existing_Undo_keeps_saved_range_and_registers_after_storage_nil_branch(self):
  s=body(self.traits,'public static func f_1002072a0(');self.order(s,['let range = requestedRange ?? editor.selectedRange()','if range.length < 1','else if let storage = editor.textStorage','storage.beginEditing()','storage.enumerateAttributes(in: range','storage.endEditing()','editor.undoManager?.registerUndo(withTarget: editor)','{ [weak editor] _ in','guard let editor else { return }','f_1002072a0(trait, editor: editor, range: range)']);self.assertNotIn('setSelectedRange',s)
 def test_existing_mixed_selection_and_run_attribute_transform_are_reused(self):
  s=body(self.traits,'public static func f_100207b54(');self.order(s,['let range = editor.selectedRange()','let content = OriginalPreviewAttributedText.f_1000f6ef8','range.location <= content.length','let end = range.location + range.length','end <= content.length, editor.selectedRange().length != 0','let selectedContent = OriginalPreviewAttributedText.f_1000f6ef8','enumerateAttributes(in: editor.selectedRange()','f_1002085e0','return traits','f_100207db8(editor.typingAttributes)']);s=body(self.traits,'public static func f_1002083e4(');self.order(s,['for key in attributes.keys { storage.removeAttribute','storage.addAttributes(f_100207648'])
 def test15_neighbor_methods8_shared_sources_unchanged(self):
  self.assertEqual(len(self.p['unchanged_methods']),15);self.assertEqual(len(self.p['shared_sources']),8)
  for r in self.p['unchanged_methods']:self.assertEqual(hashlib.sha256(body((ROOT/r['path']).read_text(),r['symbol']).encode()).hexdigest(),r['body_sha256'])
  for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),h)
 def test_three_exact_hunks247_source_inverse_and368_prior_python_preserved(self):
  self.assertEqual(len(CHANGES),3);self.assertEqual(CHANGES,json.loads((self.ph/'production-changes.json').read_text()));expected={}
  for p,old,new,count in CHANGES:
   if p not in expected:expected[p]=(self.ph/'before'/p).read_text()
   self.assertEqual(expected[p].count(old),count);expected[p]=expected[p].replace(old,new)
  self.assertEqual(len(expected),2)
  for p,h in self.b['production'].items():
   self.assertEqual(hashlib.sha256(pre_font_trait_reads_bytes(ROOT/p)).hexdigest(),h,p);old=(self.ph/'before'/p).read_bytes();self.assertEqual(pre_font_trait_reads(old.decode()).encode()if p.endswith('.swift')else old,old,p)
   if p in expected:self.assertEqual((ROOT/p).read_text(),expected[p])
  self.assertEqual(len(self.b['tests']),368);expected={};self.assertEqual(HISTORICAL_TEST_CHANGES,json.loads((self.ph/'test-scope-adjustments.json').read_text()))
  for p,old,new,count in HISTORICAL_TEST_CHANGES:
   if p not in expected:expected[p]=(self.ph/'before'/p).read_text()
   self.assertEqual(expected[p].count(old),count);expected[p]=expected[p].replace(old,new)
  for p,h in self.b['tests'].items():self.assertEqual((ROOT/p).read_text(),expected.get(p,(self.ph/'before'/p).read_text()),p);self.assertEqual(hashlib.sha256(pre_font_trait_reads_history_bytes(ROOT/p)).hexdigest(),h,p)
 def test_source_bound_property_reads_and_failure_models_keep_fresh_fallback(self):
  # Protocol trace model only: no font/Foundation execution or arbitrary subclass runtime claim.
  def run(clear_ok,apply_ok,create_ok,toggle):
   events=[];descriptors=iter(['traits','base','fallback']if toggle else['base','fallback'])
   def read():v=next(descriptors);events.append('descriptor:'+v);return v
   if toggle:read();events.append('symbolicTraits')
   base=read();events.append('clear:'+base);result=None
   if clear_ok:
    events.append('apply:cleared');result='changed'if apply_ok else None
   if result is None:result=read()
   events.extend(['pointSize','create:'+result]);return ('font:'+result if create_ok else None if toggle else'original-font'),events
  value,events=run(False,True,True,True);self.assertEqual(value,'font:fallback');self.assertEqual(events,['descriptor:traits','symbolicTraits','descriptor:base','clear:base','descriptor:fallback','pointSize','create:fallback']);self.assertEqual(run(True,False,False,True)[0],None);self.assertEqual(run(True,False,False,False)[0],'original-font');self.assertNotIn('descriptor:fallback',run(True,True,True,True)[1]);self.assertEqual(run(False,False,True,False)[0],'font:fallback')
 def test_independent_trait_model_and_saved_Undo_range_reuse(self):
  descriptors=iter([2,1]);observed=set();observed.add('bold')if next(descriptors)&2 else None;observed.add('italic')if next(descriptors)&1 else None;self.assertEqual(observed,{'bold','italic'});saved=(4,2);current=(0,0);undo=lambda:saved;self.assertEqual(undo(),(4,2));self.assertNotEqual(undo(),current);self.assertIn('range: range',body(self.traits,'public static func f_1002072a0('))
 def test_finite_records_do_not_claim_performance_or_all_functions(self):
  self.assertEqual([r['function_id']for r in self.p['contracts']],['Paste:0x100207db8','Paste:0x100207648','Paste:0x1000f3f6c']);self.assertEqual(len(self.p['finite_reuse']),4);self.assertFalse(self.p['runtime_executed']);self.assertFalse(self.p['full_function_migration_verified']);self.assertEqual(self.p['unchanged_production_files'],245);self.assertIn('0x1000f733c',self.p['remaining'][0])
if __name__=='__main__':unittest.main()
