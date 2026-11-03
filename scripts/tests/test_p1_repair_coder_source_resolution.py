"""Source equivalence of registered coder initializer; does not run NSCoder/AppKit."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from text_storage_owner_scope_contract import pre_text_storage_owner_history_bytes

class CoderSourceResolution(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ph=ROOT/'.local/p0-repair/phase-174';cls.p=json.loads((cls.ph/'coder-source-contract.json').read_text());cls.e=json.loads((ROOT/cls.p['machine_fields']).read_text());cls.s=(ROOT/'replica/Sources/PastoCore/OriginalSearchTextView.swift').read_text();cls.n={};exec((ROOT/'.local/p0-repair/phase-40/bind-contract.py').read_text().split("idx={r['address']",1)[0],cls.n)
 def word(self,a):return struct.unpack('<I',self.n['read'](a,4))[0]
 def ptr(self,a):
  v,c=self.n['reachable_pointer'](a);self.assertTrue(c['declared_chain_reachable']);self.assertFalse(v>>63);return self.n['base']+(v&((1<<36)-1))
 def test_original_fragments_machine_inputs_and_SDK_header_are_fresh(self):
  self.assertEqual(len(self.p['original_fragments']),10)
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for p,h in self.p['source_inputs'].items():self.assertEqual(hashlib.sha256(pre_text_storage_owner_history_bytes(Path(p))).hexdigest(),h,p)
  self.assertIn('- (nullable instancetype)initWithCoder:(NSCoder *)coder NS_DESIGNATED_INITIALIZER;',Path(self.p['SDK']['path']).read_text())
 def test_complete_original_420_byte_method_and_single_conditional_are_bound(self):
  m=self.e['machine'];b=self.n['read'](int(m['address'],16),int(m['end'],16)-int(m['address'],16));self.assertEqual(b.hex(),m['bytes']);self.assertEqual(len(b),420)
  words=struct.unpack('<105I',b);conditions=[0x10004430c+i*4 for i,w in enumerate(words)if w&0x7e000000 in [0x34000000,0x36000000]or w&0xff000010==0x54000000];self.assertEqual(conditions,[0x100044480]);self.assertEqual(words[-1],0xd65f03c0)
 def test_original_classlist_ro_and_coder_method_entry_are_real_reachable_pointers(self):
  self.assertEqual(self.ptr(0x100f45578),0x100f907e0);self.assertEqual(self.ptr(0x100f90800)&~7,0x100f90780);self.assertEqual(self.ptr(0x100f907a0),0x100c1ecb8)
  self.assertEqual(struct.unpack('<II',self.n['read'](0x100c1ecb8,8)),(0x8000000c,12));a=0x100c1ed2c;x,y,z=struct.unpack('<3i',self.n['read'](a,12));selector=self.ptr(a+x);self.assertEqual(self.n['read'](selector,15).split(b'\0')[0],b'initWithCoder:');self.assertEqual(self.n['read'](a+4+y,12).split(b'\0')[0],b'@24@0:8@16');self.assertEqual(a+8+z,0x1000444b0)
 def test_native_thunk_branches_to_same_method_with_coder_contract(self):
  w=self.word(0x100044550);self.assertEqual(w&0xfc000000,0x94000000);d=w&0x3ffffff;d=d-(1<<26)if d&(1<<25)else d;self.assertEqual(0x100044550+4*d,0x10004430c)
 def test_actual_three_ivar_names_offsets_sizes_and_order_are_not_guessed(self):
  values=self.e['ivar_list'];self.assertEqual(self.ptr(0x100f907b0),int(values['address'],16));self.assertEqual(values['count'],3);self.assertEqual(values['entry_size'],32)
  expected=[('canAcceptFocus',0x100fa8618,8,1),('preferredTypingAttributes',0x100fa8620,16,8),('$__lazy_storage_$_placeholderLabel',0x100fa8628,24,8)]
  self.assertEqual([(v['name'],int(v['offset_pointer'],16),v['offset'],v['size'])for v in values['fields']],expected)
  for r in values['fields']:
   p=int(r['entry'],16);name=self.ptr(p+8);self.assertEqual(self.n['read'](name,len(r['name'])+1).split(b'\0')[0].decode(),r['name']);self.assertEqual(struct.unpack('<I',self.n['read'](self.ptr(p),4))[0],r['offset'])
 def test_focus_true_dictionary_assignment_and_nil_lazy_store_precede_super(self):
  expected={0x100044344:0xf9430d08,0x100044348:0x52800029,0x10004434c:0x38286a89,0x100044354:0xf943111b,0x100044444:0xf83b6ab4,0x10004444c:0xf9431508,0x100044450:0xf8286abf}
  for a,w in expected.items():self.assertEqual(self.word(a),w)
  self.assertLess(max(expected),0x100044468);self.assertIn('public var canAcceptFocus = true',self.s);self.assertIn('private var storedPlaceholder: NSTextField?',self.s)
 def test_exact_two_dictionary_entries_use_color_slot_value_and_body_font(self):
  self.assertEqual(struct.unpack('<2Q',self.n['read'](0x100c236c0,16)),(2,4));self.assertEqual(self.word(0x1000443a0),0xf9400014)
  for a,target in [(0x10004439c,0x1001fe15c),(0x100044400,0x1001ff928)]:
   w=self.word(a);d=w&0x3ffffff;d=d-(1<<26)if d&(1<<25)else d;self.assertEqual(a+4*d,target)
  attrs=self.s.split('public var preferredTypingAttributes:',1)[1].split('private var storedPlaceholderText:',1)[0];self.assertIn('.foregroundColor: OriginalSearchAppearance.f_1001fec18()!',attrs);self.assertIn('.font: OriginalSearchAppearance.f_1001ff928()',attrs);self.assertEqual(attrs.count('OriginalSearchAppearance.'),2)
  appearance=(ROOT/'replica/Sources/PastoCore/OriginalSearchAppearance.swift').read_text();self.assertEqual(body(appearance,'public static func f_1001fec18(').strip(),'{ f_1001fe15c().pointee }');self.assertEqual(body(appearance,'public static func f_1001ff928(').strip(),'{ f_1001ff964(style: .body) }')
 def test_same_coder_and_dynamic_super_are_forwarded_in_real_machine(self):
  for a,w in {0x10004432c:0xaa1403f5,0x100044330:0xaa0003f3,0x100044454:0xa9005bf5,0x100044460:0x910003e0,0x100044464:0xaa1303e2}.items():self.assertEqual(self.word(a),w)
  self.assertEqual([r['symbol']for r in self.e['imports']],['_swift_getObjectType','_objc_msgSendSuper2','_objc_retainAutoreleasedReturnValue','_objc_release','_objc_release'])
 def test_super_result_or_nil_is_returned_after_ownership_cleanup(self):
  for a,w in {0x100044474:0xaa0003f4,0x100044480:0xb4000074,0x100044484:0xaa1403e0,0x10004448c:0xaa1403e0}.items():self.assertEqual(self.word(a),w)
  w=self.word(0x100044480);d=(w>>5)&0x7ffff;d=d-(1<<19)if d&(1<<18)else d;self.assertEqual(0x100044480+4*d,0x10004448c)
  self.assertEqual(body(self.s,'public required init?(coder:').strip(),'{\n        super.init(coder: coder)\n    }')
 def test_real_current_search_subclass_inherits_coder_without_invented_archive_action(self):
  editor=(ROOT/'replica/Sources/Pasto/UI/SearchEditor.swift').read_text();self.assertIn('final class SearchTextView: OriginalSearchTextView',editor);self.assertIn('SearchTextView(usingTextLayoutManager: true)',body(editor,'override func makeTextView('));self.assertNotIn('NSKeyedUnarchiver',editor);self.assertNotIn('init?(coder:',body(editor,'final class SearchTextView:'))
 def test_all247_production_sources_and_old_tests_are_unchanged(self):
  b=json.loads((self.ph/'baseline.json').read_text());self.assertEqual(len(b['production']),247)
  for p,h in {**b['production'],**b['tests']}.items():self.assertEqual(hashlib.sha256(pre_text_storage_owner_history_bytes(ROOT/p)).hexdigest(),h,p)
  self.assertEqual(hashlib.sha256((ROOT/'replica/function-map.json').read_bytes()).hexdigest(),b['function_map_sha256'])
 def test_resolution_scope_is_source_boundary_and_keeps_full_goal_and_other_unknown_open(self):
  self.assertTrue(self.p['source_contract_verified']);self.assertFalse(self.p['production_change_required']);self.assertFalse(self.p['full_function_migration_verified']);self.assertFalse(self.p['runtime_executed']);self.assertEqual(len(self.p['requirements']),7);self.assertIn('0f733c',self.p['remaining'][0]);self.assertIn('Broader original P0/P1',self.p['remaining'][1]);self.assertEqual(self.p['scope'],'single registered coder initialization boundary')
if __name__=='__main__':unittest.main()
