"""Four original transaction failure boundaries continue native editor cleanup without system dialogs."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from raw_data_nil_bridge_scope_contract import pre_raw_data_nil_bridge_bytes
from preview_commit_error_scope_contract import CHANGES,pre_preview_commit_error,pre_preview_commit_error_bytes
from text_edit_mode_scope_contract import pre_text_edit_mode
class PreviewCommitError(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.phase=ROOT/'.local/p0-repair/phase-158';cls.p=json.loads((cls.phase/'preview-commit-error-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.src={p:(ROOT/p).read_text()for p in cls.p['current_sources']};cls.commit={p:body(s,'func commitPreviewEditing()')for p,s in cls.src.items()};cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
 def test_twelve_original_fragments_and_binary_decoder_are_bound(self):
  self.assertEqual(len(self.p['original_fragments']),12)
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for k in ['binary','decoder']:
   r=self.p[k];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
 def test_real_swift_errorRelease_import_is_not_a_UI_or_reporting_stub(self):
  r=self.p['error_release_import'];self.assertEqual(r['symbol'],'_swift_errorRelease')
  for k in ['stub','pointer']:
   b=r[k];self.assertEqual(self.n['read'](int(b['address'],16),len(bytes.fromhex(b['bytes']))).hex(),b['bytes'])
  v,c=self.n['reachable_pointer'](int(r['pointer']['address'],16));self.assertEqual(c,r['chain']);self.assertTrue(v>>63);self.assertEqual(v&0xffffff,r['ordinal']);f=self.n['fixup'][0];h=struct.unpack('<7I',self.n['raw'][f:f+28]);entry=struct.unpack_from('<I',self.n['raw'],f+h[2]+4*r['ordinal'])[0];o=f+h[3]+(entry>>9);self.assertEqual(self.n['raw'][o:self.n['raw'].index(b'\0',o)].decode(),r['symbol'])
 def test_all_four_real_error_register_branches_join_normal_cleanup(self):
  self.assertEqual(len(self.p['contracts']),4)
  for row in self.p['contracts']:
   r=row['branch'];a=int(r['address'],16);b=self.n['read'](a,4);self.assertEqual(b.hex(),r['bytes']);w=int.from_bytes(b,'little');self.assertEqual(w&0xff00001f,0xb4000015);d=(w>>5)&0x7ffff;d=d-(1<<19)if d&(1<<18)else d;self.assertEqual(a+4*d,int(row['success_join'],16))
 def test_eight_transaction_release_calls_and_text_unconditional_refresh_are_actual_ARM(self):
  edges=[edge for r in self.p['contracts']for edge in [r['transaction_call'],r['error_release_call']]]+[self.p['text_refresh_call']];self.assertEqual(len(edges),9)
  for r in edges:
   a=int(r['address'],16);b=self.n['read'](a,4);self.assertEqual(b.hex(),r['bytes']);w=int.from_bytes(b,'little');self.assertEqual(w&0xfc000000,0x94000000);d=w&0x3ffffff;d=d-(1<<26)if d&(1<<25)else d;self.assertEqual(a+4*d,int(r['target'],16))
 def test_current_four_catches_consume_only_and_do_not_present_retry_or_rollback(self):
  for p,s in self.commit.items():
   catch=body(s,'catch');without_comments='\n'.join(line.split('//',1)[0]for line in catch.splitlines());self.assertEqual(''.join(without_comments.split()),'{}');self.assertNotIn('presentError',s)
   for t in ['throw error','Task {','rollback()','reset()','retry']:self.assertNotIn(t,catch)
   self.assertIn('state.normalizeSelection()',s)
 def test_text_image_link_and_color_cleanup_order_is_preserved_after_failures(self):
  text=next(s for p,s in self.commit.items()if'OriginalReplica'in p);self.assertLess(text.index('text.isEditable = false'),text.index('do {'));self.assertLess(text.index('catch'),text.index('reloadStoredContent()'));self.assertIn('updateTextPreviewItem(editInput, attributedString: content)',text)
  image=next(s for p,s in self.commit.items()if'ReplicaImage'in p);self.assertLess(image.index('catch'),image.index('finishEditing(reloadNativeImage: false)'));self.assertIn('updateImagePreviewItem(editInput',image)
  link=next(s for p,s in self.commit.items()if'ReplicaLink'in p);self.assertLess(link.index('catch'),link.index('showContent(readOnlyContent)'));self.assertLess(link.index('showContent(readOnlyContent)'),link.index('updateMetadata(currentURL())'))
  color=next(s for p,s in self.commit.items()if'ReplicaColor'in p);self.assertLess(color.index('editing = false'),color.index('guard let state'));self.assertLess(color.index('colorPanel.orderOut(nil)'),color.index('do {'));self.assertIn('updateColorItem(editInput, text: text)',color)
 def test_eight_neighbors_and_seven_shared_writer_observer_and_parent_callback_sources_unchanged(self):
  self.assertEqual(len(self.p['unchanged_methods']),8)
  for r in self.p['unchanged_methods']:self.assertEqual(hashlib.sha256(body(pre_text_edit_mode((ROOT/r['path']).read_text()),r['symbol']).encode()).hexdigest(),r['sha256'])
  self.assertEqual(len(self.p['shared_sources']),7)
  for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_raw_data_nil_bridge_bytes(ROOT/p)).hexdigest(),h)
 def test_four_exact_method_changes_reverse247_sources_and_do_not_claim_full_parent_migration(self):
  self.assertEqual(len(CHANGES),4);changed=[]
  for p,h in self.base['production'].items():
   if hashlib.sha256(pre_raw_data_nil_bridge_bytes(ROOT/p)).hexdigest()!=h:changed.append(p)
   self.assertEqual(hashlib.sha256(pre_preview_commit_error_bytes(ROOT/p)).hexdigest(),h)
  self.assertEqual(set(changed),set(self.p['current_sources']))
  for p in changed:self.assertEqual(pre_preview_commit_error((self.phase/'before'/p).read_text()),(self.phase/'before'/p).read_text())
  self.assertFalse(self.p['full_function_migration_verified']);self.assertFalse(self.p['runtime_executed']);self.assertEqual(self.p['conservative_groups_added'],1)
if __name__=='__main__':unittest.main()
