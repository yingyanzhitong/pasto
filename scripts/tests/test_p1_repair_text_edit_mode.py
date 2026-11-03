"""Actual Editable witnesses and held text-model transitions; static checks only."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from text_edit_mode_scope_contract import CHANGES,HISTORICAL_TEST_CHANGES,pre_text_edit_mode,pre_text_edit_mode_bytes,pre_text_edit_mode_history_bytes
from font_trait_reads_scope_contract import pre_font_trait_reads_bytes, pre_font_trait_reads_history_bytes
class TextEditModeContracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ph=ROOT/'.local/p0-repair/phase-187';cls.p=json.loads((cls.ph/'text-edit-mode-contract.json').read_text());cls.b=json.loads((cls.ph/'baseline.json').read_text());cls.source=(ROOT/'replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift').read_text();cls.content=body(cls.source,'private final class ReplicaInlineTextPreviewContent:');cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
 def word(self,a):return struct.unpack('<I',self.n['read'](a,4))[0]
 def test15_original_fragments_binary_and_decoder_fresh(self):
  self.assertEqual(len(self.p['original_fragments']),15)
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for key in ['binary','decoder']:
   r=self.p[key];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
 def test10_complete_machine_ranges119_direct_calls_bound(self):
  self.assertEqual(len(self.p['machine_ranges']),10);self.assertEqual(len(self.p['branches']),119)
  for r in self.p['machine_ranges']:
   d=self.n['read'](int(r['address'],16),int(r['end'],16)-int(r['address'],16));self.assertEqual(d.hex(),r['bytes']);self.assertEqual(hashlib.sha256(d).hexdigest(),r['sha256'])
  for r in self.p['branches']:
   a=int(r['call'],16);w=self.word(a);self.assertEqual(hex(w),r['word']);v=w&0x3ffffff;v=v-(1<<26)if v&(1<<25)else v;self.assertEqual(hex(a+v*4),r['target'])
 def test6_real_witness_slots_resolve_begin_cancel_commit_and_separate_focus(self):
  self.assertEqual(len(self.p['reader_slots']),6)
  for r in self.p['reader_slots']:
   a=int(r['address'],16);v,c=self.n['reachable_pointer'](a);self.assertEqual(c,r['chain']);self.assertFalse(v>>63);self.assertEqual(hex(self.n['base']+(v&((1<<36)-1))),r['target']);self.assertEqual(self.n['read'](a,8).hex(),r['bytes'])
  self.assertEqual([(r['address'],r['target'])for r in self.p['reader_slots'][1:5]],[('0x100ed0930','0x1003ec04c'),('0x100ed0938','0x1003ec054'),('0x100ed0940','0x1003ec0ac'),('0x100ed0948','0x1003ec13c')])
 def test_conformance_type_and_protocol_names_bound_by5_links_and5_metadata_ranges(self):
  self.assertEqual(len(self.p['relative_links']),5);self.assertEqual(len(self.p['metadata_ranges']),5)
  for r in self.p['relative_links']:
   a=int(r['address'],16);d=self.n['read'](a,4);v=struct.unpack('<i',d)[0];self.assertEqual(d.hex(),r['bytes']);self.assertEqual(hex(a+(v&~1 if r['indirect']else v)),r['target'])
  for r in self.p['metadata_ranges']:
   d=self.n['read'](int(r['address'],16),len(bytes.fromhex(r['bytes'])));self.assertEqual(d.hex(),r['bytes']);self.assertEqual(hashlib.sha256(d).hexdigest(),r['sha256'])
  self.assertEqual(self.n['read'](0x100c45f5c,9),b'Editable\0');self.assertEqual(self.n['read'](0x100c46330,20),b'TextItemContentView\0')
 def test_outer_begin_and_cancel_use_actual40_and48_witness_offsets(self):
  self.assertEqual(self.word(0x10007bf94),0xf94022c8);self.assertEqual(self.word(0x10007bfa4),0xd63f0100);self.assertEqual(len(self.p['cancel_witness_loads']),1)
  for r in self.p['cancel_witness_loads']:
   w=self.word(int(r['address'],16));self.assertEqual(hex(((w>>10)&0xfff)*8),'0x48');self.assertEqual(self.n['read'](int(r['address'],16),4).hex(),r['bytes'])
 def test_begin_and_cancel_pass_true_false_to_same_native_body(self):
  self.assertEqual(self.word(0x1003ec04c),0x52800022);self.assertEqual(self.word(0x1003ec054),0x52800002);calls={r['call']:r['target']for r in self.p['branches']};self.assertEqual(calls['0x1003ec050'],'0x1003ec05c');self.assertEqual(calls['0x1003ec058'],'0x1003ec05c')
 def test_native_common_body_only_sets_editability_then_redraws_held_model_and_colors(self):
  calls=[r['target']for r in self.p['branches']if 0x1003ec05c<=int(r['call'],16)<0x1003ec0ac];self.assertEqual([t for t in calls if t in ['0x1003eb208','0x1002131bc','0x1003eb330','0x1003eb4a8']],['0x1003eb208','0x1002131bc','0x1003eb330','0x1003eb4a8'])
  for t in ['0x1003c05d4','0x1003ec13c','0x100214474']:self.assertNotIn(t,calls)
 def test_begin_has_no_extra_entity_read_baseline_update_or_early_focus(self):
  self.assertEqual(body(self.content,'func beginPreviewEditing()'),'{\n        text.isEditable = true\n        displayStoredModel()\n    }')
 def test_cancel_does_not_force_entity_or_cache_refresh(self):
  self.assertEqual(body(self.content,'func cancelPreviewEditing()'),'{\n        text.isEditable = false\n        displayStoredModel()\n    }')
 def test_existing_display_still_selects_held_original_editing_and_colors_in_order(self):
  s=body(self.content,'private func displayStoredModel()');self.assertLess(s.index('OriginalPreviewAttributedText.f_1003eb330'),s.index('OriginalPreviewTextColors.f_1003eb4a8'));self.assertIn('original: originalText, editing: editingText, editor: text',s)
  core=(ROOT/'replica/Sources/PastoCore/OriginalPreviewAttributedText.swift').read_text();s=body(core,'public static func f_1003eb330(');self.assertEqual(s.count('editor.isEditable'),2);self.assertIn('editor.isEditable ? editing : original',s)
 def test_separate_focus_hook_remains_after_actual_window_presentation(self):
  s=body(self.content,'func focusPreviewEditing()');self.assertIn('window?.makeFirstResponder(text)',s);ui=(ROOT/'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text();s=body(ui,'private func presentEditingPreview(');self.assertLess(s.index('transition.present(controller)'),s.index('.focusPreviewEditing()'));self.assertIn('func focusPreviewEditing()', (ROOT/'replica/Sources/PastoCore/OriginalItemPreviewView.swift').read_text())
 def test_commit_reload_and_observer_updates_unchanged(self):
  before=(self.ph/'before/replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift').read_text()
  for sig in ['func commitPreviewEditing()','private func reloadStoredContent()','private func receiveStoredText(','private func replaceStoredText(']:self.assertEqual(body(self.content,sig),body(before,sig))
  self.assertIn('reloadStoredContent()',body(self.content,'func commitPreviewEditing()'));self.assertIn('replaceStoredText(text)\n        if !self.text.isEditable { displayStoredModel() }',body(self.content,'private func receiveStoredText('))
 def test12_neighbors12_shared_sources_unchanged(self):
  self.assertEqual(len(self.p['unchanged_methods']),12);self.assertEqual(len(self.p['shared_sources']),12)
  for r in self.p['unchanged_methods']:self.assertEqual(hashlib.sha256(body((ROOT/r['path']).read_text(),r['symbol']).encode()).hexdigest(),r['body_sha256'])
  for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_font_trait_reads_bytes(ROOT/p)).hexdigest(),h)
 def test_two_exact_hunks_one_file247_inverse_and366_historical_python_preserved(self):
  self.assertEqual(len(CHANGES),2);self.assertEqual(CHANGES,json.loads((self.ph/'production-changes.json').read_text()));expected={}
  for p,old,new,count in CHANGES:
   if p not in expected:expected[p]=(self.ph/'before'/p).read_text()
   self.assertEqual(expected[p].count(old),count);expected[p]=expected[p].replace(old,new)
  self.assertEqual(len(expected),1)
  for p,h in self.b['production'].items():
   self.assertEqual(hashlib.sha256(pre_text_edit_mode_bytes(ROOT/p)).hexdigest(),h,p);old=(self.ph/'before'/p).read_bytes();self.assertEqual(pre_text_edit_mode(old.decode()).encode()if p.endswith('.swift')else old,old,p)
   if p in expected:self.assertEqual((ROOT/p).read_text(),expected[p])
  self.assertEqual(len(self.b['tests']),366);expected={};self.assertEqual(HISTORICAL_TEST_CHANGES,json.loads((self.ph/'test-scope-adjustments.json').read_text()))
  for p,old,new,count in HISTORICAL_TEST_CHANGES:
   if p not in expected:expected[p]=(self.ph/'before'/p).read_text()
   self.assertEqual(expected[p].count(old),count);expected[p]=expected[p].replace(old,new)
  for p,h in self.b['tests'].items():self.assertEqual(pre_font_trait_reads_history_bytes(ROOT/p).decode(),expected.get(p,(self.ph/'before'/p).read_text()),p);self.assertEqual(hashlib.sha256(pre_text_edit_mode_history_bytes(ROOT/p)).hexdigest(),h,p)
 def test_source_bound_transition_model_does_not_read_pending_entity_state(self):
  def transition(editable,held,pending,notify=None):
   events=[('editable',editable)]
   if notify is not None:held=notify
   events.extend([('display',held[1]if editable else held[0]),('colors',held[0])]);return events
  held=('stored-rich','stored-edit');pending=('undelivered-new-rich','undelivered-new-edit');self.assertEqual(transition(True,held,pending),[('editable',True),('display','stored-edit'),('colors','stored-rich')]);self.assertEqual(transition(False,held,pending),[('editable',False),('display','stored-rich'),('colors','stored-rich')]);self.assertEqual(transition(True,held,pending,notify=pending)[1],('display','undelivered-new-edit'))
 def test_only_common_actual_contract_scored_and_full_migration_open(self):
  self.assertEqual([r['function_id']for r in self.p['contracts']],['Paste:0x1003ec05c']);self.assertEqual(self.p['unchanged_production_files'],246);self.assertFalse(self.p['runtime_executed']);self.assertFalse(self.p['full_function_migration_verified']);self.assertIn('0x1000f733c',self.p['remaining'][0])
if __name__=='__main__':unittest.main()
