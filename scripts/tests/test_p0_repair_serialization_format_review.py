"""Review actual original serialization preference edges without replacing already aligned code."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from item_creation_date_scope_contract import pre_item_creation_date,pre_item_creation_date_bytes
from test_p0_repair_checksum_routing import original_fragment
class SerializationFormatReview(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.phase=ROOT/'.local/p0-repair/phase-154';cls.p=json.loads((cls.phase/'serialization-format-review.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.sources={Path(p).stem:pre_item_creation_date((ROOT/p).read_text())for p in cls.p['current_sources']};cls.original={r['address']:original_fragment((ROOT/r['path']).read_text(),r['address'][2:])for r in cls.p['original_fragments']};cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
 def test_twelve_original_fragments_two_keypaths_and_eight_current_sources_bound(self):
  self.assertEqual(len(self.p['original_fragments']),12);self.assertEqual(len(self.p['current_sources']),8)
  for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
  for k in ['binary','decoder']:
   r=self.p[k];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
  for p,h in self.p['current_sources'].items():self.assertEqual(hashlib.sha256(pre_item_creation_date_bytes(ROOT/p)).hexdigest(),h)
 def test_actual_ItemData_keypath_getter_and_default_preference_getter_resolve_by_relative_pointer(self):
  for k in self.p['keypaths']:
   v=k['pattern'];self.assertEqual(self.n['read'](int(v['address'],16),len(bytes.fromhex(v['bytes']))).hex(),v['bytes']);g=k['getter_field'];a=int(g['address'],16);self.assertEqual(a+struct.unpack('<i',self.n['read'](a,4))[0],int(k['target'],16))
  self.assertIn('FUN_100316b18()',self.original['0x10031bb6c']);self.assertIn('FUN_1002fd760',self.original['0x100316b18']);self.assertIn('PasteCore/DI+PasteCore.swift',self.original['0x100316b18']);self.assertIn('DAT_100c404d8',self.original['0x1002fd760']);self.assertIn('FUN_100376734()',self.original['0x1002fdae4'])
 def test_original_preference_is_useBinaryPlist_false_Bool_not_network_or_feature_guess(self):
  values=[int(s,16).to_bytes(8,'little')for s in self.p['preference']['original_key_immediates']];self.assertEqual(b''.join(values)[:14],b'useBinaryPlist');s=self.original['0x100376734'];self.assertIn('local_11 = 0;',s);self.assertIn('type_metadata_for_Swift_Bool',s)
  model=self.sources['Models'];self.assertIn('useBinaryPlist: Bool = false',model);self.assertIn('decodeIfPresent(Bool.self, forKey: .useBinaryPlist) ?? false',model);self.assertIn('try values.encode(useBinaryPlist, forKey: .useBinaryPlist)',model)
 def test_original_Ghidra_removed_encode_error_paths_really_release_and_join_with_empty_data(self):
  words={int(r['address'],16):int.from_bytes(self.n['read'](int(r['address'],16),4),'little')for r in self.p['ARM_words']}
  for r in self.p['ARM_words']:self.assertEqual(self.n['read'](int(r['address'],16),4).hex(),r['bytes'])
  for a,target in [(0x10031aa70,0x10031ab30),(0x10031ab0c,0x10031ab48)]:
   w=words[a];self.assertEqual(w&0xff00001f,0xb4000015);d=(w>>5)&0x7ffff;d=d-(1<<19)if d&(1<<18)else d;self.assertEqual(a+4*d,target)
  for a in [0x10031aa84,0x10031ab20]:self.assertEqual(words[a],0xd2800013)
  for a in [0x10031aa8c,0x10031ab28]:self.assertEqual(words[a],0xd2f80016)
  self.assertEqual(words[0x10031aa90],0x52810028);self.assertEqual(words[0x10031ab58],0x528040a8)
 def test_current_codec_keeps_both_formats_error_empty_image_gate_and_compression_fallback(self):
  s=body(self.sources['OriginalPasteboardDataCodec'],'public static func f_10031a8e8(')
  for t in ['if useBinaryPlist','encoder.outputFormat = .binary','(try? encoder.encode(items)) ?? Data()','algorithm = COMPRESSION_LZFSE','(try? JSONEncoder().encode(items)) ?? Data()','algorithm = COMPRESSION_ZLIB','items.contains(where: { $0.f_10037d5c4() != nil })','return encoded','return f_10030f5c8(encoded, algorithm: algorithm) ?? encoded']:self.assertIn(t,s)
  self.assertLess(s.index('JSONEncoder'),s.index('items.contains'));self.assertLess(s.index('items.contains'),s.index('return f_10030f5c8'))
 def test_all_five_local_writer_paths_deliver_live_local_preference_not_hardcoded_format(self):
  self.assertEqual(len(self.p['preference']['consumer_paths']),5);store=self.sources['ClipboardStore'];self.assertEqual(store.count('useBinaryPlist: preferences.useBinaryPlist'),2);self.assertIn('useBinaryPlist: state.preferences.useBinaryPlist',self.sources['ClipboardPersistence']);self.assertIn('OriginalPasteboardDataCodec.f_10031a8e8(capturedItems, useBinaryPlist: preferences.useBinaryPlist)',self.sources['Pasteboard'])
  data=self.sources['ClipboardItemDataPersistence'];self.assertIn('decode(AppPreferences.self, from: bytes).useBinaryPlist',data);self.assertIn('useBinaryPlist: binaryPlist!',data);self.assertIn('OriginalPasteboardDataCodec.f_10031a8e8(items, useBinaryPlist: useBinaryPlist)',body(data,'func replace('));self.assertIn('local.useBinaryPlist != base.useBinaryPlist',store)
 def test_existing_four_methods_and_all247_sources_and_old_tests_are_reused_without_rewrite(self):
  for r in self.p['unchanged_methods']:self.assertEqual(hashlib.sha256(body(pre_item_creation_date((ROOT/r['path']).read_text()),r['symbol']).encode()).hexdigest(),r['sha256'])
  for p,h in self.base['production'].items():self.assertEqual(hashlib.sha256(pre_item_creation_date_bytes(ROOT/p)).hexdigest(),h)
  for p,h in self.base['tests'].items():self.assertEqual(hashlib.sha256((ROOT/'.local/p0-repair/phase-155/before'/p).read_bytes()).hexdigest(),h)
 def test_parameter_equivalence_does_not_claim_full_dependency_identity_or_entire_migration(self):
  self.assertEqual(self.p['production_changes'],0);self.assertEqual(self.p['new_difference_records'],0);self.assertFalse(self.p['full_function_migration_verified']);self.assertFalse(self.p['runtime_executed']);self.assertIn('DI',self.p['boundaries'][0]);self.assertIn('04430c/0f733c',self.p['boundaries'][1])
if __name__=='__main__':unittest.main()
