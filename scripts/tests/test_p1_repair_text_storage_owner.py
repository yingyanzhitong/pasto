"""Original weak-owner delivery/owned-editor source and Mach-O checks, no AppKit execution."""
from pathlib import Path
import hashlib,json,struct,sys,weakref,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from text_storage_owner_scope_contract import CHANGES,pre_text_storage_owner,pre_text_storage_owner_history_bytes
from pinboard_filter_identity_scope_contract import pre_pinboard_filter_identity_bytes, pre_pinboard_filter_identity_history_bytes

from suggestion_filter_icon_scope_contract import pre_suggestion_filter_icon_bytes
from font_trait_reads_scope_contract import pre_font_trait_reads
class TextStorageOwner(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ph=ROOT/'.local/p0-repair/phase-175';cls.p=json.loads((cls.ph/'text-storage-owner-contract.json').read_text());cls.b=json.loads((cls.ph/'baseline.json').read_text());cls.path=next(iter(cls.p['current_sources']));cls.s=(ROOT/cls.path).read_text();cls.n={};exec((ROOT/'.local/p0-repair/phase-40/bind-contract.py').read_text().split("idx={r['address']",1)[0],cls.n)
 def word(self,a):return struct.unpack('<I',self.n['read'](a,4))[0]
 def order(self,s,tokens):
  positions=[s.index(t)for t in tokens];self.assertEqual(positions,sorted(positions))
 def test_original12_fragments_binary_and_delegate_SDK_are_bound(self):
  self.assertEqual(len(self.p['original_fragments']),12)
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  self.assertEqual(hashlib.sha256((ROOT/'.local/paste-arm64-static.bin').read_bytes()).hexdigest(),'871f00354fbb1c165d858a98e6d19d6f43cb9d3f9f958b3e07c7f07eb5c19afb');r=self.p['sdk_storage_delegate'];self.assertEqual(hashlib.sha256(Path(r['path']).read_bytes()).hexdigest(),r['sha256']);self.assertIn('@property (nullable, weak) id <NSTextStorageDelegate> delegate;',Path(r['path']).read_text())
 def test_six_indexed_machine_ranges_bind_actual_task_getter_release_and_continuations(self):
  self.assertEqual(len(self.p['machine_ranges']),6)
  for r in self.p['machine_ranges']:
   data=self.n['read'](int(r['address'],16),int(r['end'],16)-int(r['address'],16));self.assertEqual(data.hex(),r['bytes']);self.assertEqual(hashlib.sha256(data).hexdigest(),r['sha256'])
 def test_seven_true_imports_include_weak_init_two_weak_loads_and_owner_release(self):
  self.assertEqual(len(self.p['imports']),7)
  for r in self.p['imports']:
   a=int(r['address'],16);w=self.word(a);d=w&0x3ffffff;d=d-(1<<26)if d&(1<<25)else d;self.assertEqual(hex(a+4*d),r['stub']);x,y=struct.unpack('<2I',self.n['read'](int(r['stub'],16),8));imm=((x>>5)&0x7ffff)*4+((x>>29)&3);imm=imm-(1<<21)if imm&(1<<20)else imm;p=(int(r['stub'],16)&~4095)+(imm<<12)+((y>>10)&0xfff)*8;self.assertEqual(hex(p),r['pointer']);v,c=self.n['reachable_pointer'](p);self.assertEqual(c,r['chain']);self.assertTrue(v>>63);fo=self.n['fixup'][0];hdr=struct.unpack_from('<7I',self.n['raw'],fo);e=struct.unpack_from('<I',self.n['raw'],fo+hdr[2]+4*(v&0xffffff))[0];o=fo+hdr[3]+(e>>9);self.assertEqual(self.n['raw'][o:self.n['raw'].index(b'\0',o)].decode(),r['symbol'])
  self.assertEqual([r['symbol']for r in self.p['imports'][:4]],['_swift_unknownObjectWeakInit','_swift_unknownObjectWeakLoadStrong','_objc_release','_swift_unknownObjectWeakLoadStrong'])
 def test_first_owner_is_saved_then_released_before_second_owner_load(self):
  words={0x100214728:0xa94482d4,0x100214730:0x91004280,0x10021473c:0xaa0003f3,0x100214740:0xaa0003f4,0x100214994:0xaa1303e0,0x10021499c:0xf94026c8,0x1002149a0:0x91004100,0x1002149ac:0xaa0003f3,0x1002149e4:0xaa1303f4}
  for a,w in words.items():self.assertEqual(self.word(a),w)
  self.assertLess(0x100214998,0x1002149a4);self.assertEqual(self.word(0x1002149d4)&0x7e000000,0x34000000);self.assertEqual(self.word(0x100214a10),0xd63f02a0)
 def test_original_getter_owns_same_cached_editor_released_by_destructor(self):
  self.assertEqual(self.word(0x100212e10),0xf9479116);self.assertEqual(self.word(0x100212e44),0xf8366a93);self.assertEqual(self.word(0x100214518),0xf9479108);self.assertEqual(self.word(0x10021451c),0xf8686a60);self.assertEqual(self.p['owned_editor_ivar']['offset_global'],'0x100fb6f20')
  self.assertIn('private let editor: NSTextView',self.s);self.assertNotIn('weak var editor:',self.s);self.order(body(self.s,'public init(editor:'),['self.editor = editor','super.init()','f_100213780(editor: editor)'])
 def test_actual_storage_Task_uses_static_orchestration_and_weak_loader(self):
  s=body(self.s,'public func f_10021453c()');self.assertIn('Task { @MainActor [weak self] in',s);self.assertIn('Self.deliverStorageChange(from: { [weak self] in self })',s)
  for token in ['self?.f_100214704()','guard let self','Task.isCancelled']:self.assertNotIn(token,s)
  self.assertIn('Self.deliverStorageChange(from: { [weak self] in self })',body(self.s,'public func f_100214704()'))
 def test_traits_and_content_have_separate_noninlined_owner_scopes(self):
  s=body(self.s,'private static func deliverStorageChange(');self.order(s,['_ = deliverTraits(from: loadOwner)','deliverContent(from: loadOwner)']);self.assertNotIn('let owner',s)
  for name in ['deliverTraits','deliverContent']:self.assertIn('@inline(never)\n    private static func '+name,self.s)
  self.order(body(self.s,'private static func deliverTraits('),['guard let owner = loadOwner() else { return true }','return owner.f_100213fe8()'])
 def test_content_callback_is_snapshotted_after_second_load_and_before_content_getter(self):
  s=body(self.s,'private static func deliverContent(');self.order(s,['guard let owner = loadOwner(), let callback = owner.onAttributedTextChange else { return }','callback(OriginalPreviewAttributedText.f_1000f6ef8(editor: owner.editor))']);self.assertEqual(s.count('loadOwner()'),1)
  t=body(self.s,'public func f_100213fe8()');self.order(t,['let traits = OriginalPreviewTextTraits.f_100207b54(editor: editor)','onTraitsChange?(traits)','return false']);self.assertNotIn('guard let editor',t)
  init=body(self.s,'public init(editor:');self.assertIn('options: [.new]',init);self.assertIn('Self.deliverTraits(from: { [weak self] in self })',init);self.assertNotIn('self?.f_100213fe8()',init)
 def test_real_preview_consumer_and_six_neighbor_methods_are_unchanged(self):
  self.assertEqual(len(self.p['unchanged_methods']),6)
  for r in self.p['unchanged_methods']:self.assertEqual(hashlib.sha256(body(pre_font_trait_reads((ROOT/r['path']).read_text()),r['symbol']).encode()).hexdigest(),r['body_sha256'])
  for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_suggestion_filter_icon_bytes(ROOT/p)).hexdigest(),h)
  s=(ROOT/'replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift').read_text();self.order(s,['let bridge = OriginalPreviewTextStorageBridge(editor: text)','bridge.onTraitsChange =','bridge.onAttributedTextChange =','storageBridge = bridge']);self.assertIn('document.usesRecoveredContentEvents = true',s)
 def test_protocol_oracle_owner_destroyed_after_traits_skips_content_even_when_editor_survives(self):
  class Owner:pass
  view=object();events=[];root=[Owner()];root[0].editor=view;ref=weakref.ref(root[0]);root[0].on_traits=lambda:root.__setitem__(0,None)
  def traits():
   owner=ref()
   if owner is not None:events.append('traits');owner.on_traits()
  def content():
   owner=ref()
   if owner is not None:events.append('content')
  traits();self.assertIsNone(ref());content();self.assertEqual(events,['traits']);self.assertIsNotNone(view)
  # Previous instance-method Task held the bridge through both callbacks.
  root[0]=Owner();root[0].editor=view;ref=weakref.ref(root[0]);root[0].on_traits=lambda:root.__setitem__(0,None);held=ref();held.on_traits();self.assertIsNotNone(ref());self.assertIsNotNone(held.editor)
 def test_protocol_oracle_reloads_current_callback_after_reentrant_traits_change(self):
  class Owner:pass
  owner=Owner();root=[owner];ref=weakref.ref(owner);events=[];owner.callback=lambda:events.append('old');owner.traits=lambda:setattr(owner,'callback',lambda:events.append('new'))
  def traits():
   current=ref()
   if current is not None:current.traits()
  def content():
   current=ref()
   if current is not None:
    callback=current.callback
    if callback is not None:callback()
  traits();content();self.assertEqual(events,['new'])
 def test_protocol_oracle_missing_callback_skips_read_but_does_not_skip_traits_stage(self):
  counts={'loads':0,'traits':0,'reads':0};owner={'callback':None}
  def load():counts['loads']+=1;return owner
  def traits():
   current=load()
   if current is not None:counts['traits']+=1
  def content():
   current=load()
   if current is not None and current['callback']is not None:counts['reads']+=1
  traits();content();self.assertEqual(counts,dict(loads=2,traits=1,reads=0))
 def test_four_exact_source_hunks_reverse247_and_prior_test_edits_replay_exactly(self):
  self.assertEqual(len(CHANGES),4);self.assertEqual(len(self.b['production']),247);changed=[]
  for p,h in self.b['production'].items():
   data=pre_pinboard_filter_identity_bytes(ROOT/p);old=(self.ph/'before'/p).read_bytes()
   if hashlib.sha256(data).hexdigest()!=h:changed.append(p)
   inverse=pre_text_storage_owner(data.decode()).encode()if p.endswith('.swift')else data;self.assertEqual(hashlib.sha256(inverse).hexdigest(),h,p);self.assertEqual(pre_text_storage_owner(old.decode()).encode()if p.endswith('.swift')else old,old,p)
  self.assertEqual(changed,[self.path]);adjust=json.loads((self.ph/'test-scope-adjustments.json').read_text());expected={}
  for p,old,new,count in adjust:
   if p not in expected:expected[p]=(self.ph/'before'/p).read_text()
   self.assertEqual(expected[p].count(old),count);expected[p]=expected[p].replace(old,new)
  self.assertEqual(len(adjust),5);self.assertEqual(len(expected),3)
  for p,h in self.b['tests'].items():self.assertEqual(pre_pinboard_filter_identity_history_bytes(ROOT/p).decode(),expected.get(p,(self.ph/'before'/p).read_text()),p);self.assertEqual(hashlib.sha256(pre_text_storage_owner_history_bytes(ROOT/p)).hexdigest(),h,p)
 def test_source_boundary_keeps_native_setter_unknown_and_does_not_claim_framework_execution(self):
  self.assertFalse(self.p['runtime_executed']);self.assertFalse(self.p['full_function_migration_verified']);self.assertIn('0f733c',self.p['remaining'][0]);self.assertIn('Swift compiler ARC/MainActor private ABI',self.p['adaptations'][1]);self.assertEqual(self.p['production_files'],247)
if __name__=='__main__':unittest.main()
