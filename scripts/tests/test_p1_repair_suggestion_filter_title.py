"""Original raw filter titles and actual context consumers, source/ARM only."""
from pathlib import Path
import ast,hashlib,json,re,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from suggestion_filter_title_scope_contract import CHANGES,HISTORICAL_TEST_CHANGES,pre_suggestion_filter_title,pre_suggestion_filter_title_bytes,pre_suggestion_filter_title_history_bytes
from suggestion_filter_icon_scope_contract import pre_suggestion_filter_icon, pre_suggestion_filter_icon_bytes, pre_suggestion_filter_icon_history_bytes
class SuggestionFilterTitleContracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ph=ROOT/'.local/p0-repair/phase-184';cls.p=json.loads((cls.ph/'suggestion-filter-title-contract.json').read_text());cls.b=json.loads((cls.ph/'baseline.json').read_text());cls.core=pre_suggestion_filter_icon((ROOT/'replica/Sources/PastoCore/OriginalSearchSuggestions.swift').read_text());cls.caption=body(cls.core,'listName: (String) -> String? = { _ in nil }) -> String');cls.chip=body(pre_suggestion_filter_icon((ROOT/'replica/Sources/Pasto/UI/FilterBrowser.swift').read_text()),'static func chip(');cls.editor=(ROOT/'replica/Sources/Pasto/UI/SearchEditor.swift').read_text();cls.context=(ROOT/'replica/Sources/PastoCore/OriginalSearchInputContext.swift').read_text();cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
 def word(self,a):return struct.unpack('<I',self.n['read'](a,4))[0]
 def order(self,s,tokens):
  positions=[s.index(t)for t in tokens];self.assertEqual(positions,sorted(positions))
 def test14_original_fragments_and_prior_group_resolver_stay_bound(self):
  self.assertEqual(len(self.p['original_fragments']),14)
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for key in ['binary','decoder','prior_group_resolver']:
   r=self.p[key];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
 def test9_ranges_and213_direct_branches_use_current_binary(self):
  self.assertEqual(len(self.p['machine_ranges']),9);self.assertEqual(len(self.p['branches']),213)
  for r in self.p['machine_ranges']:
   d=self.n['read'](int(r['address'],16),int(r['end'],16)-int(r['address'],16));self.assertEqual(d.hex(),r['bytes']);self.assertEqual(hashlib.sha256(d).hexdigest(),r['sha256'])
  for r in self.p['branches']:
   a=int(r['call'],16);w=self.word(a);self.assertEqual(hex(w),r['word']);v=w&0x3ffffff;v=v-(1<<26)if v&(1<<25)else v;self.assertEqual(hex(a+4*v),r['target'])
 def test5_actual_string_bridge_append_and_retain_bindings(self):
  self.assertEqual(len(self.p['imports']),5)
  for r in self.p['imports']:
   v,chain=self.n['reachable_pointer'](int(r['pointer'],16));self.assertEqual(chain,r['chain']);self.assertTrue(v>>63);f=self.n['fixup'][0];raw=self.n['raw'];h=struct.unpack_from('<7I',raw,f);e=struct.unpack_from('<I',raw,f+h[2]+4*(v&0xffffff))[0];o=f+h[3]+(e>>9);self.assertEqual(raw[o:raw.index(b'\0',o)].decode(),r['symbol'])
  self.assertEqual(len({r['symbol']for r in self.p['imports'][1:4]}),1);self.assertIn('append',self.p['imports'][1]['symbol'])
 def test_real_NSString_length_selector_supports_UTF16_context_length(self):
  r=self.p['selectors'][0];self.assertEqual(r['name'],'length');v,chain=self.n['reachable_pointer'](int(r['pointer'],16));self.assertEqual(chain,r['chain']);self.assertFalse(v>>63);dest=self.n['base']+(v&((1<<36)-1));self.assertEqual(hex(dest),r['target']);self.assertEqual(self.n['read'](dest,7),b'length\0');self.assertIn('length = (value as NSString).length',self.context)
 def test_native_six_type_literals_are_raw_and_match_actual_provider(self):
  r=self.p['static_types'];data=self.n['read'](int(r['address'],16),0x80);self.assertEqual(data.hex(),r['bytes']);self.assertEqual(hashlib.sha256(data).hexdigest(),r['sha256']);self.assertEqual(struct.unpack_from('<QQ',data,0x10),(6,12));values=[]
  for off in range(0x20,0x80,16):
   v=struct.unpack_from('<Q',data,off+8)[0];self.assertEqual(v>>60,0xe);values.append(data[off:off+((v>>56)&15)].decode())
  self.assertEqual(values,r['values']);literal=re.search(r'let values = (\[[^\n]+\])',body(self.core,'public static func f_10030f3e0('))[1];self.assertEqual(ast.literal_eval(literal),values);self.assertEqual(values,['Unknown','Image','Color','File','Link','Text'])
 def test_native_caption_only_special_cases5_and3_and_nil_falls_back(self):
  for a,w in [(0x1002ddc34,0x7100151f),(0x1002ddc3c,0x71000d1f),(0x1002ddc50,0xb40003c1),(0x1002ddcb8,0xb4000097),(0x1002ddcd0,0xaa1303e0),(0x1002ddcd4,0xaa1503e1)]:self.assertEqual(self.word(a),w)
  self.assertIn('case 5: return listName(value) ?? value',self.caption);self.assertIn('case 3: return OriginalSearchDateEncoding.f_1002d8e9c(value) ?? value',self.caption);self.assertIn('default: return value',self.caption)
  for t in ['isEmpty','lowercased','displayName','trimming','UUID','Pasto']:self.assertNotIn(t,self.caption)
 def test_native_actual_menu_reads_icon_before_title_formatter(self):
  calls={r['call']:r['target']for r in self.p['branches']};self.assertEqual(calls['0x1000412a4'],'0x1000546e0');self.assertEqual(calls['0x1000412d4'],'0x1002dc9b8');self.assertEqual(calls['0x1002ddc4c'],'0x1002d8e9c');self.assertLess(0x1000412a4,0x1000412d4)
  self.order(self.chip,['if let rawValue','var image: NSImage?','switch selection','if image == nil','let title = OriginalSearchSuggestions.f_1002ddc10','return ReplicaSearchFilterChip']);self.assertNotIn('title = kind.displayName',self.chip)
 def test_actual_editor_delivers_exact_raw_value_to_shared_builder(self):
  s=body(self.editor,'private func chip(for node:');self.assertIn('guard case let .filter(kind, value) = node',s);self.assertIn('ReplicaFilterMatching.chip(selection, store: parent.store, rawValue: value)',s);self.assertIn('value = rawValue',body(self.chip,'if let rawValue'))
  raw=body(self.chip,'if let rawValue');self.assertNotIn('queryNode',raw);self.assertNotIn('lowercased',raw)
 def test_group_title_resolver_still_reads_same_native_String_identifier_once(self):
  tail=self.chip[self.chip.index('let title = OriginalSearchSuggestions.f_1002ddc10'):];self.assertIn('kind: selection.group, value: value',tail);self.assertIn('store.tabListTarget(identifier: $0)?.name',tail);self.assertEqual(self.chip.count('tabListTarget('),1)
  for t in ['store.pinboards','UUID(','.isEmpty','"Pasto"']:self.assertNotIn(t,tail)
 def test_context_inout_prefix_is_returned_not_discarded_as_Ghidra_scalar_zero(self):
  for a,w in [(0x1002f7a98,0x9100c3f4),(0x1002f7ab0,0x9100c3f4),(0x1002f7ac0,0x9100c3f4),(0x1002f7ae4,0xa9436bfb),(0x1002f7bd8,0xa901691b)]:self.assertEqual(self.word(a),w)
  self.assertIn('text = prefix + ":" + value',self.context);self.assertIn('length = 1',self.context);self.assertIn('anchorRange: NSRange(location: offset, length: length)',self.context)
 def test_actual_provider_input_is_original_node_not_caption_text(self):
  state=body((ROOT/'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text(),'func searchSuggestions(for context:');self.assertIn('searchIndex.suggestions(contextNode: context.nodes[context.nodeIndex], currentNodes: context.nodes)',state);self.assertNotIn('context.text',state)
  producer=body(self.core,'public static func f_1002df190(');self.assertIn('guard case let .text(text) = contextNode',producer);self.assertIn('OriginalSearchQueryNode.filter(kind, $0)',producer);self.assertIn('OriginalSearchDateEncoding.f_1002d9d2c',producer)
 def test14_neighbor_methods_and10_shared_sources_preserve_prior_fixes(self):
  self.assertEqual(len(self.p['unchanged_methods']),14)
  for r in self.p['unchanged_methods']:
   s=(ROOT/r['path']).read_text();s=body(s,r['scope'])if 'scope'in r else s;self.assertEqual(hashlib.sha256(body(s,r['symbol']).encode()).hexdigest(),r['body_sha256'])
  self.assertEqual(len(self.p['shared_sources']),10)
  for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_suggestion_filter_icon_bytes(ROOT/p)).hexdigest(),h)
 def test5_exact_hunks_restore247_sources_idempotently(self):
  self.assertEqual(len(CHANGES),5);self.assertEqual(CHANGES,json.loads((self.ph/'production-changes.json').read_text()));changed=[]
  for p,h in self.b['production'].items():
   if hashlib.sha256(pre_suggestion_filter_icon_bytes(ROOT/p)).hexdigest()!=h:changed.append(p)
   self.assertEqual(hashlib.sha256(pre_suggestion_filter_title_bytes(ROOT/p)).hexdigest(),h,p);old=(self.ph/'before'/p).read_bytes();self.assertEqual(pre_suggestion_filter_title(old.decode()).encode()if p.endswith('.swift')else old,old,p)
  self.assertEqual(set(changed),set(self.p['current_sources']));self.assertEqual(len(changed),3)
 def test14_history_patterns_restore360_frozen_Python_inputs(self):
  self.assertEqual(len(HISTORICAL_TEST_CHANGES),14);self.assertEqual(HISTORICAL_TEST_CHANGES,self.p['historical_test_changes']);expected={}
  for p,old,new,count in HISTORICAL_TEST_CHANGES:
   if p not in expected:expected[p]=(self.ph/'before'/p).read_text()
   self.assertEqual(expected[p].count(old),count);expected[p]=expected[p].replace(old,new)
  self.assertEqual(len(expected),6)
  for p,h in self.b['tests'].items():self.assertEqual(pre_suggestion_filter_icon_history_bytes(ROOT/p).decode(),expected.get(p,(self.ph/'before'/p).read_text()),p);self.assertEqual(hashlib.sha256(pre_suggestion_filter_title_history_bytes(ROOT/p)).hexdigest(),h,p)
 def test_protocol_caption_cases_preserve_case_empty_name_and_lazy_resolvers(self):
  # Protocol model for original branch table; no Swift/DateFormatter/CoreData execution.
  def caption(kind,value,date=lambda _:None,name=lambda _:None):
   resolved=name(value)if kind==5 else date(value)if kind==3 else value
   return value if resolved is None else resolved
  for kind in range(256):
   if kind in (3,5):continue
   for value in ['Text','text','TEXT','','opaque/id']:
    def fail(_):self.fail('unexpected resolver')
    self.assertEqual(caption(kind,value,date=fail,name=fail),value)
  for resolved in [None,'','name']:
   self.assertEqual(caption(5,'raw',name=lambda _:resolved),'raw'if resolved is None else resolved);self.assertEqual(caption(3,'raw',date=lambda _:resolved),'raw'if resolved is None else resolved)
 def test_protocol_context_scanning_includes_UTF16_empty_and_end_boundary(self):
  def scan(nodes,caret):
   offset=0
   for i,(text,is_filter)in enumerate(nodes):
    length=1 if is_filter else len(text.encode('utf-16-le'))//2
    if caret>=offset and caret-offset<length:return i,offset,length
    offset+=length
    if offset==caret:return i,offset-length,length
   return None
  self.assertIsNone(scan([],0));self.assertEqual(scan([('A😀',False),('id',True)],3),(0,0,3));self.assertEqual(scan([('A😀',False),('id',True)],4),(1,3,1));self.assertEqual(scan([('',False),('x',False)],0),(0,0,0));self.assertIsNone(scan([('x',False)],-1));self.assertIsNone(scan([('x',False)],2))
 def test_no_additional_layout_or_runtime_scope_is_claimed(self):
  self.assertFalse(self.p['runtime_executed']);self.assertFalse(self.p['full_function_migration_verified']);self.assertEqual([r['function_id']for r in self.p['contracts']],['Paste:0x1002dc9b8']);self.assertEqual(self.p['additional_contracts'][0]['function_id'],'Paste:0x1002ddc10');self.assertIn('0f733c',self.p['remaining'][0]);self.assertIn('query-array',self.p['remaining'][1])
if __name__=='__main__':unittest.main()
