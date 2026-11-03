"""Original nullable NSData bridge is delegated to the same Foundation symbol; no framework execution."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from save_failure_rollback_scope_contract import pre_save_failure_rollback_bytes
from test_offline_p0_contracts import body
from raw_data_nil_bridge_scope_contract import CHANGES,pre_raw_data_nil_bridge,pre_raw_data_nil_bridge_bytes
class RawDataNilBridge(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.phase=ROOT/'.local/p0-repair/phase-159';cls.p=json.loads((cls.phase/'raw-data-nil-bridge-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.path=next(iter(cls.p['current_sources']));cls.s=(ROOT/cls.path).read_text();cls.read=body(cls.s,'static func readRepresentations(');cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n);cls.c={};p=ROOT/cls.p['installed_Foundation']['cache_decoder']['path'];text=p.read_text();exec(text[:text.index('blocks=[]')],cls.c)
 def test_five_original_fragments_binary_decoder_sdk_and_installed_OS_bound(self):
  self.assertEqual(len(self.p['original_fragments']),5)
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for k in ['binary','decoder','sdk','system_version']:
   r=self.p[k];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
  self.assertIn('public static func _unconditionallyBridgeFromObjectiveC(_ source: Foundation.NSData?) -> Foundation.Data',(ROOT/self.p['sdk']['path']).read_text())
 def test_Paste_bridge_call_and_true_dyld_import_match_installed_Foundation_export(self):
  call=self.p['original_bridge_call'];a=int(call['address'],16);b=self.n['read'](a,4);self.assertEqual(b.hex(),call['bytes']);w=int.from_bytes(b,'little');d=w&0x3ffffff;d=d-(1<<26)if d&(1<<25)else d;self.assertEqual(a+4*d,int(call['target'],16))
  r=self.p['original_import'];v,c=self.n['reachable_pointer'](int(r['pointer'],16));self.assertEqual(c,r['chain']);self.assertEqual(v&0xffffff,r['import_ordinal']);self.assertTrue(v>>63);f=self.n['fixup'][0];h=struct.unpack('<7I',self.n['raw'][f:f+28]);entry=struct.unpack_from('<I',self.n['raw'],f+h[2]+4*(v&0xffffff))[0];o=f+h[3]+(entry>>9);symbol=self.n['raw'][o:self.n['raw'].index(b'\0',o)].decode();self.assertEqual(symbol,r['symbol']);self.assertEqual(symbol,self.p['installed_Foundation']['export_symbol'])
 def test_real_cache_UUID_mappings_Foundation_header_and_entire_export_trie_bound(self):
  p=self.p['installed_Foundation'];self.assertEqual([{k:f[k]for k in ['path','uuid','size']}for f in self.c['files']],p['cache_files']);self.assertEqual(hashlib.sha256(self.c['data'](int(p['header_address'],16),p['header_size'])).hexdigest(),p['header_sha256']);blob=self.c['data'](int(p['trie_address'],16),p['trie_size']);self.assertEqual(hashlib.sha256(blob).hexdigest(),p['trie_sha256']);self.assertEqual(len(p['steps']),10)
  def leb(pos):
   v=0;shift=0
   while True:
    x=blob[pos];pos+=1;v|=(x&127)<<shift
    if x<128:return v,pos
    shift+=7
  name='';node=0
  for step in p['steps']:
   self.assertEqual(step['node'],node);length,q=leb(node);q+=length;count=blob[q];q+=1;edges=[]
   for _ in range(count):
    end=blob.index(0,q);edge=blob[q:end].decode();target,q=leb(end+1);edges.append((edge,target))
   self.assertIn((step['edge'],step['next_node']),edges);name+=step['edge'];node=step['next_node']
  self.assertEqual(name,p['export_symbol']);length,q=leb(node);self.assertGreater(length,0);flags,q=leb(q);relative,q=leb(q);self.assertEqual(flags,0);self.assertEqual(hex(int(p['image'],16)+relative),p['bridge_address'])
 def test_Foundation_nil_branch_returns_zero_payload_and_empty_Data_tag_before_return(self):
  p=self.p['installed_Foundation'];a=int(p['bridge_address'],16);b=self.c['data'](a,88);self.assertEqual(b.hex(),p['bridge_bytes']);w=struct.unpack_from('<I',b,20)[0];self.assertEqual(w&0xff00001f,0xb4000000);d=(w>>5)&0x7ffff;d=d-(1<<19)if d&(1<<18)else d;nil=20+4*d;self.assertEqual(nil,56);self.assertEqual(struct.unpack_from('<I',b,nil)[0],0xd2800013);self.assertEqual(struct.unpack_from('<I',b,nil+4)[0],0xd2f80014);self.assertEqual(struct.unpack_from('<I',b,nil+8)[0],0xaa1303e0);self.assertEqual(struct.unpack_from('<I',b,nil+12)[0],0xaa1403e1)
 def test_current_reader_uses_the_exact_optional_NSData_SDK_bridge_inside_exception_boundary(self):
  s=self.read;tokens=['OriginalObjCExceptionBridge.f_1002ffc68','let raw = data.value(forKey: "rawPasteboardItems") as? NSData','return Data._unconditionallyBridgeFromObjectiveC(raw)','catch let error as OriginalObjCExceptionError','diagnostics().f_1000d468c().f_1000d4e0c','return []','autoreleasepool { OriginalPasteboardDataCodec.f_10031aeec(raw) }'];pos=0
  for t in tokens:pos=s.index(t,pos)+len(t)
  self.assertNotIn('throw CocoaError',s);self.assertNotIn('guard let raw',s)
 def test_main_copy_and_private_search_still_receive_empty_representation_and_metadata_fallback(self):
  self.assertIn('return readRepresentations(from: data)',body(self.s,'static func readItems('));src=(ROOT/'replica/Sources/PastoCore/ClipboardSearchRecord.swift').read_text();self.assertIn('ClipboardItemDataPersistence.readRepresentations(from: data',body(src,'private func read<T>'));self.assertIn('if items.isEmpty { diagnoseEmptyRepresentations(for: object) }',body(src,'func content()'));self.assertIn('guard let value = text(',body(src,'static func nativeText('));codec=(ROOT/'replica/Sources/PastoCore/OriginalPasteboardDataCodec.swift').read_text();self.assertIn('decodeIfValid(data) ?? []',body(codec,'public static func f_10031aeec('))
 def test_three_neighbor_methods_and_five_shared_source_files_are_unchanged(self):
  for r in self.p['unchanged_methods']:self.assertEqual(hashlib.sha256(body((ROOT/r['path']).read_text(),r['symbol']).encode()).hexdigest(),r['sha256'])
  self.assertEqual(len(self.p['unchanged_methods']),3);self.assertEqual(len(self.p['shared_sources']),5)
  for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),h)
 def test_single_exact_bridge_delta_reverse247_files_without_runtime_or_full_completion_claim(self):
  self.assertEqual(len(CHANGES),1);changed=[]
  for p,h in self.base['production'].items():
   if hashlib.sha256(pre_save_failure_rollback_bytes(ROOT/p)).hexdigest()!=h:changed.append(p)
   self.assertEqual(hashlib.sha256(pre_raw_data_nil_bridge_bytes(ROOT/p)).hexdigest(),h)
  self.assertEqual(changed,[self.path]);self.assertEqual(pre_raw_data_nil_bridge((self.phase/'before'/self.path).read_text()),(self.phase/'before'/self.path).read_text());self.assertFalse(self.p['full_function_migration_verified']);self.assertFalse(self.p['runtime_executed'])
if __name__=='__main__':unittest.main()
