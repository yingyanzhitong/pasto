"""Raw group filter String identity and native-name source contracts; no framework execution."""
from pathlib import Path
import hashlib,json,struct,sys,uuid,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from pinboard_filter_identity_scope_contract import CHANGES,pre_pinboard_filter_identity,pre_pinboard_filter_identity_history_bytes
from filter_model_query_scope_contract import pre_filter_model_query, pre_filter_model_query_bytes, pre_filter_model_query_history_bytes
from suggestion_filter_title_scope_contract import pre_suggestion_filter_title
class GroupFilterIdentity(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ph=ROOT/'.local/p0-repair/phase-176';cls.p=json.loads((cls.ph/'group-filter-identity-contract.json').read_text());cls.b=json.loads((cls.ph/'baseline.json').read_text());cls.editor=(ROOT/'replica/Sources/Pasto/UI/SearchEditor.swift').read_text();cls.browser=(ROOT/'replica/Sources/Pasto/UI/FilterBrowser.swift').read_text();cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
 def word(self,a):return struct.unpack('<I',self.n['read'](a,4))[0]
 def order(self,s,tokens):
  p=[s.index(t)for t in tokens];self.assertEqual(p,sorted(p))
 def adrp_add(self,a):
  x,y=struct.unpack('<2I',self.n['read'](a,8));self.assertEqual(x&0x9f000000,0x90000000);self.assertEqual(y&0xff000000,0x91000000);self.assertEqual(x&31,(y>>5)&31);v=((x>>5)&0x7ffff)*4+((x>>29)&3);v=v-(1<<21)if v&(1<<20)else v;return(a&~4095)+(v<<12)+((y>>10)&0xfff)
 def test_twenty_original_fragments_and_machine_input_provenance_are_fresh(self):
  self.assertEqual(len(self.p['original_fragments']),20)
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for k in ['binary','decoder']:
   r=self.p[k];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
 def test_seven_machine_ranges_and_real_ListsReading_slot20_are_bound(self):
  self.assertEqual(len(self.p['machine_ranges']),7)
  for r in self.p['machine_ranges']:
   data=self.n['read'](int(r['address'],16),int(r['end'],16)-int(r['address'],16));self.assertEqual(data.hex(),r['bytes']);self.assertEqual(hashlib.sha256(data).hexdigest(),r['sha256'])
  for r in self.p['pointers']:
   v,c=self.n['reachable_pointer'](int(r['address'],16));self.assertEqual(c,r['chain']);self.assertFalse(v>>63);self.assertEqual(hex(self.n['base']+(v&((1<<36)-1))),r['target'])
  self.assertEqual(self.word(0x10007d7d0),0xf9401308)
 def test_default_resolver_is_installed_at_actual_global_slot(self):
  self.assertEqual(self.adrp_add(0x10007d344),0x101057920);self.assertEqual(self.adrp_add(0x10007d350),0x10007d740);self.assertEqual(self.word(0x10007d358),0xa9007d09)
  self.assertEqual(self.p['default_resolver']['body'],'0x10007d78c')
 def test_title_resolver_passes_same_String_and_falls_back_to_original_value(self):
  expected={0x10007d7a4:0xaa0203f5,0x10007d7a8:0xaa0103f6,0x10007d7d4:0xaa1603e0,0x10007d7d8:0xaa1503e1,0x10007d7e4:0xd63f0100,0x1002ddca0:0xd63f02c0,0x1002ddcd0:0xaa1303e0,0x1002ddcd4:0xaa1503e1}
  for a,w in expected.items():self.assertEqual(self.word(a),w)
  for a,target in [(0x1002ddc80,0x1002ddcc8),(0x1002ddcb8,0x1002ddcc8)]:
   w=self.word(a);self.assertEqual(w&0x7e000000,0x34000000);v=(w>>5)&0x7ffff;v=v-(1<<19)if v&(1<<18)else v;self.assertEqual(a+4*v,target)
 def test_actual_native_name_selector_is_resolved_through_reachable_dyld_chain(self):
  r=self.p['name_selector'];x,y=struct.unpack('<2I',self.n['read'](int(r['stub'],16),8));v=((x>>5)&0x7ffff)*4+((x>>29)&3);v=v-(1<<21)if v&(1<<20)else v;p=(int(r['stub'],16)&~4095)+(v<<12)+((y>>10)&0xfff)*8;self.assertEqual(hex(p),r['pointer']);value,c=self.n['reachable_pointer'](p);self.assertEqual(c,r['chain']);self.assertEqual(self.n['read'](self.n['base']+(value&((1<<36)-1)),5),b'name\0')
 def test_original_fetch_error_is_consumed_into_empty_result_not_an_extra_alert(self):
  r=self.p['read_error_release'];v,c=self.n['reachable_pointer'](int(r['pointer'],16));self.assertEqual(c,r['chain']);self.assertTrue(v>>63);fo=self.n['fixup'][0];h=struct.unpack_from('<7I',self.n['raw'],fo);e=struct.unpack_from('<I',self.n['raw'],fo+h[2]+4*(v&0xffffff))[0];o=fo+h[3]+(e>>9);self.assertEqual(self.n['raw'][o:self.n['raw'].index(b'\0',o)].decode(),'_swift_errorRelease')
  self.assertEqual(self.word(0x10032af1c),0xb40000b5);self.assertEqual(self.word(0x10032af28),0x90005c20);self.assertEqual(self.word(0x10032af2c),0xf9406c00)
  lists=(ROOT/'replica/Sources/PastoCore/ClipboardListPersistence.swift').read_text();s=body(lists,'func tabList(identifier:');self.order(s,['identifier == %@','return (try? context.fetch(request))?.first']);self.assertNotIn('UUID',s)
 def test_selection_and_restored_query_parser_keep_String_payload_without_UUID_gate(self):
  self.assertIn('date(OriginalSearchDateFilter), pinboard(String)',self.editor);self.assertNotIn('pinboard(UUID)',self.editor);self.assertIn('case 5: selection = .pinboard(value)',self.editor);self.assertNotIn('UUID(uuidString: value)',self.editor)
 def test_browser_candidate_projection_and_query_encoding_preserve_raw_value(self):
  s=body(self.browser,'private static func filterBrowserSections(');p=s.index('let pinboards =');q=s.index('let dates =',p);group=s[p:q];self.assertIn('guard case let .filter(5, value) = node else { return nil }',group);self.assertIn('return .pinboard(value)',group)
  for t in ['UUID','Set(','lowercased','uppercased']:self.assertNotIn(t,group)
  node=body(self.browser,'var queryNode:');self.assertIn('case let .pinboard(id): value = id\n',node);self.assertNotIn('id.uuidString',node)
 def test_caption_uses_native_identifier_lookup_and_raw_fallback_including_empty_names(self):
  s=body(pre_suggestion_filter_title(self.browser),'static func chip(');p=s.index('case let .pinboard(id):');q=s.index('if image == nil',p);group=s[p:q];self.order(group,['value = id','title = store.tabListTarget(identifier: id)?.name ?? id']);self.assertNotIn('store.pinboards',group);self.assertNotIn('"Pasto"',group)
  backend=(ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text();s=body(backend,'func tabListTarget(identifier:');self.assertIn('context.performAndWait',s);self.assertIn('lists.tabList(identifier: identifier)',s)
 def test_real_query_toggle_uses_exact_query_node_without_new_identifier_adapter(self):
  s=body(body(self.browser,'private final class ReplicaFilterBrowserModel:'),'func toggleSearchFilter(');self.order(s,['let filter = selection.queryNode','if nodes.contains(filter)','nodes.removeAll { $0 == filter }','nodes.append(filter)','query = nodes','onQueryChanged(query)']);self.assertNotIn('UUID',s)
 def test_existing_available_filters_task_and_per_source_error_rules_are_reused(self):
  s=body(self.browser,'init(query:');self.assertIn('Task { @MainActor [self] in sections = load() }',s);self.assertIn('@Published private(set) var sections: [ReplicaFilterBrowser.Section] = []',self.browser)
  helper=(ROOT/'replica/Sources/PastoCore/OriginalSearchSuggestions.swift').read_text();s=body(helper,'public static func f_1002e00a0(');self.order(s,['provider()?.type("")','provider()?.app("")','provider()?.device("")','OriginalSearchDateRanges.f_1002d8ce0()','provider()?.pinboard("")']);self.assertIn('filters[5] = pinboards.map { $0.map { .filter(5, $0.identifier) } }',s)
 def test_unimplemented_coder_support_boundary_remains_fatal_and_not_counted_as_repair(self):
  v=next(v for v in self.p['finite_reuse']if v['function_id']=='Paste:0x100042908');self.assertFalse(v['business_migration_credit']);s=(ROOT/'replica/Sources/PastoCore/OriginalSearchInputView.swift').read_text();self.assertIn('fatalError("init(coder:) has not been implemented")',body(s,'public required init?(coder:'));index={x['address']:x for x in json.loads((ROOT/'reports/Paste/function-index.json').read_text())};text=(ROOT/index['0x10004493c']['file']).read_text();frag=source_fragments(ROOT/index['0x10004493c']['file'])['0x10004493c'];self.assertEqual(frag['sha256'],next(x['sha256']for x in self.p['original_fragments']if x['address']=='0x10004493c'))
 def test_seven_neighbor_methods_and_seven_shared_sources_preserve_prior_fixes(self):
  self.assertEqual(len(self.p['unchanged_methods']),7)
  for r in self.p['unchanged_methods']:self.assertEqual(hashlib.sha256(body(pre_filter_model_query((ROOT/r['path']).read_text()),r['symbol']).encode()).hexdigest(),r['body_sha256'])
  for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_filter_model_query_bytes(ROOT/p)).hexdigest(),h)
 def test_five_exact_hunks_reverse247_and_history_is_idempotent(self):
  self.assertEqual(len(CHANGES),5);changed=[]
  for p,h in self.b['production'].items():
   data=pre_filter_model_query_bytes(ROOT/p);old=(self.ph/'before'/p).read_bytes()
   if hashlib.sha256(data).hexdigest()!=h:changed.append(p)
   self.assertEqual(hashlib.sha256(pre_pinboard_filter_identity(data.decode()).encode()if p.endswith('.swift')else data).hexdigest(),h,p);self.assertEqual(pre_pinboard_filter_identity(old.decode()).encode()if p.endswith('.swift')else old,old,p)
  self.assertEqual(sorted(changed),sorted(self.p['current_sources']))
 def test_prior_test_edits_are_exactly_scoped_and_reversible(self):
  adjust=json.loads((self.ph/'test-scope-adjustments.json').read_text());expected={}
  for p,old,new,count in adjust:
   if p not in expected:expected[p]=(self.ph/'before'/p).read_text()
   self.assertEqual(expected[p].count(old),count);expected[p]=expected[p].replace(old,new)
  self.assertEqual(len(adjust),10);self.assertEqual(len(expected),4)
  for p,h in self.b['tests'].items():self.assertEqual(pre_filter_model_query_history_bytes(ROOT/p).decode(),expected.get(p,(self.ph/'before'/p).read_text()),p);self.assertEqual(hashlib.sha256(pre_pinboard_filter_identity_history_bytes(ROOT/p)).hexdigest(),h,p)
 def test_protocol_raw_identifiers_roundtrip_with_case_order_duplicates_and_non_UUID_values(self):
  values=['native.group','abcdefab-cdef-abcd-efab-cdefabcdefab','\u7ec4-\u7532','','native.group'];nodes=[(5,v)for v in values];selected=[v for tag,v in nodes if tag==5];self.assertEqual([(5,v)for v in selected],nodes)
  legacy=[]
  for v in values:
   try:legacy.append(str(uuid.UUID(v)).upper())
   except ValueError:pass
  self.assertNotEqual(legacy,values);self.assertEqual(legacy,['ABCDEFAB-CDEF-ABCD-EFAB-CDEFABCDEFAB'])
 def test_protocol_native_title_first_match_empty_name_missing_or_error_falls_back_raw(self):
  records=[('raw-id',''),('raw-id','later'),('other','Name')]
  def title(identifier,failed=False):
   matches=[]if failed else[name for value,name in records if value==identifier]
   return matches[0]if matches else identifier
  self.assertEqual(title('raw-id'),'');self.assertEqual(title('other'),'Name');self.assertEqual(title('missing'),'missing');self.assertEqual(title('raw-id',True),'raw-id')
 def test_finite_scope_does_not_claim_whole_function_or_native_setter_closure(self):
  self.assertFalse(self.p['runtime_executed']);self.assertFalse(self.p['full_function_migration_verified']);self.assertIn('0f733c',self.p['remaining'][0]);self.assertEqual(len(self.p['contracts']),2);self.assertFalse(self.p['finite_reuse'][0]['full_constructor_verified']);self.assertIn('normal installed local resolver',self.p['contracts'][1]['contract'])
if __name__=='__main__':unittest.main()
