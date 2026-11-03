from shared_pasteboard_state_scope_contract import pre_shared_pasteboard_state
# coding: utf-8
"""Original/runtime *data* checks; never loads Foundation, Swift or an app."""
import hashlib,json,mmap,struct,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from macho_imports import _chained_bindings
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment

class ArchiveRuntimeNameContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-33'
        cls.proof=json.loads((cls.phase/'archive-runtime-name-contract.json').read_text())
        cls.item=pre_shared_pasteboard_state((ROOT/'replica/Sources/PastoCore/OriginalPasteboard.swift').read_text())
        cls.checksums=(ROOT/'replica/Sources/PastoCore/OriginalPasteboardChecksums.swift').read_text()

    def test_original_fragments_and_class_metadata_are_bound(self):
        for r in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        b=self.proof['original_binary'];raw=(ROOT/b['path']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),b['sha256'])
        for block in self.proof['original_blocks']:
            chunk=raw[block['file_offset']:block['file_offset']+block['length']]
            self.assertEqual(chunk.hex(),block['bytes'])
            self.assertEqual(hashlib.sha256(chunk).hexdigest(),block['sha256'])
        c=self.proof['original_class'];p=c['superclass_parse_input'];source=(ROOT/p['path']).read_bytes()
        self.assertEqual(hashlib.sha256(source).hexdigest(),p['sha256'])
        setup=json.loads(source);bindings,_=_chained_bindings(raw,setup['chained_range'],setup['segments'],setup['dylibs'])
        self.assertEqual(bindings[int(c['address'],16)+8],c['superclass_binding'])
        self.assertEqual(c['superclass_binding']['symbol'],'_OBJC_CLASS_$_NSObject')

    def test_original_has_no_custom_coder_class_method_and_uses_types_data(self):
        c=self.proof['original_class']
        self.assertEqual([x['name']for x in c['methods']],['initWithCoder:','encodeWithCoder:','init','.cxx_destruct'])
        self.assertFalse(c['custom_class_for_coder_overrides'])
        original=original_fragment((ROOT/'decompiled/Paste/part-0282.c').read_text(),'10037f520')
        self.assertIn('_TtC9PasteCore14PasteboardItem::types',original)
        self.assertIn('_TtC9PasteCore14PasteboardItem::dataByType',original)
        # Ghidra omits the bridged key literals; decode the bound MOVZ/MOVK
        # arguments from the real ARM body rather than inventing C constants.
        for key in ['types','data']:
            block=next(b for b in self.proof['original_blocks']if b['role']=='original '+key+' coding key')
            value=0
            for (w,)in struct.iter_unpack('<I',bytes.fromhex(block['bytes'])):
                if w&31:continue
                op=w&0x7f800000;shift=((w>>21)&3)*16;v=((w>>5)&0xffff)<<shift
                self.assertIn(op,[0x52800000,0x72800000])
                value=v if op==0x52800000 else (value&~(0xffff<<shift))|v
            self.assertEqual(value.to_bytes(8,'little').rstrip(b'\0').decode(),key)
        encode=body(self.item,'public func f_10037f520(with coder: NSCoder)')
        self.assertIn('forKey: "types"',encode);self.assertIn('forKey: "data"',encode)
        self.assertNotIn('forKey: "dataByType"',encode)

    def test_installed_framework_data_blocks_and_uuid_are_bound_without_loading(self):
        for i,cache in enumerate(self.proof['cache_files']):
            with Path(cache['path']).open('rb')as f:
                raw=mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)
                try:
                    self.assertEqual(raw[88:104].hex(),cache['uuid'])
                    for block in self.proof['blocks']:
                        if block['cache']!=i:continue
                        chunk=raw[block['file_offset']:block['file_offset']+block['length']]
                        self.assertEqual(chunk.hex(),block['bytes'])
                        self.assertEqual(hashlib.sha256(chunk).hexdigest(),block['sha256'])
                finally:raw.close()
        self.assertEqual({x['name']for x in self.proof['methods']},
                         {'encodeObject:forKey:','classNameForClass:','setClassName:forClass:',
                          'classForKeyedArchiver','classForArchiver','classForCoder'})

    def test_actual_archiver_name_and_classes_producers_use_class_get_name(self):
        def word(a):
            b=next(b for b in self.proof['blocks']if int(b['address'],16)<=a<int(b['address'],16)+b['length'])
            return struct.unpack_from('<I',bytes.fromhex(b['bytes']),a-int(b['address'],16))[0]
        def branch(a):
            w=word(a);self.assertEqual(w>>26,0b100101) # BL
            d=w&((1<<26)-1)
            if d&(1<<25):d-=1<<26
            return a+4*d
        self.assertEqual(branch(0x181d8b8c8),0x182786394)
        self.assertEqual(branch(0x181d8b90c),0x182786394)
        self.assertEqual(branch(0x1827863a8),0x18291a164)
        self.assertEqual(branch(0x1800a4a9c),0x180093d08)
        strings={bytes.fromhex(b['bytes']).rstrip(b'\0')for b in self.proof['blocks']if b['role'].startswith('bound string ')}
        self.assertTrue({b'$classname',b'$classes',b'classForArchiver',b'classForCoder'}<=strings)
        self.assertEqual(self.proof['runtime_exports']['class_getName'],'0x180093ce4')
        self.assertEqual(self.proof['runtime_exports']['objc_opt_class'],'0x1800a06e4')

    def test_original_swift_runtime_name_decodes_by_bound_module_class_format(self):
        mangled=self.proof['original_class']['name'];self.assertTrue(mangled.startswith('_TtC'))
        rest=mangled[4:];parts=[]
        for _ in range(2):
            n=0
            while n<len(rest)and rest[n].isdigit():n+=1
            length=int(rest[:n]);parts.append(rest[n:n+length]);rest=rest[n+length:]
        self.assertEqual(rest,'');self.assertEqual(parts,['PasteCore','PasteboardItem'])
        format_block=next(b for b in self.proof['blocks']if b['role']=='runtime demangled module.class format')
        self.assertEqual(bytes.fromhex(format_block['bytes']),b'%.*s.%.*s\0')
        self.assertEqual('.'.join(parts),self.proof['default_class_name'])
        self.assertEqual(self.proof['default_class_names'],['PasteCore.PasteboardItem','NSObject'])

    def test_actual_archived_type_gets_only_compatibility_runtime_name_annotation(self):
        marker='@objc(_TtC9PasteCore14PasteboardItem)\n'
        self.assertEqual(self.item.count(marker),1)
        self.assertIn(marker+'public final class OriginalPasteboardItem: NSObject, Codable, NSSecureCoding',self.item)
        checkpoint=(self.phase/'before/replica/Sources/PastoCore/OriginalPasteboard.swift').read_text()
        self.assertEqual(self.item.replace(marker,'',1),checkpoint)
        for token in ['classForKeyedArchiver','classForCoder','setClassName','NSClassFromString','objc_allocateClassPair']:
            self.assertNotIn(token,self.item)
        self.assertIn('public func encode(with coder: NSCoder)',self.item)
        self.assertIn('f_10037f520(with: coder)',body(self.item,'public func encode(with coder: NSCoder)'))

    def test_checksum_root_flags_fallback_and_algorithm_are_unchanged(self):
        checksum=body(self.checksums,'public static func f_100322ae4(')
        self.assertIn('NSKeyedArchiver.archivedData(withRootObject: items as NSArray,',checksum)
        self.assertIn('requiringSecureCoding: false',checksum)
        self.assertIn('?? Data()',checksum);self.assertIn('return checksum(data)',checksum)
        selector=body(self.checksums,'public static func f_1003216bc(')
        self.assertIn('case .unknown:\n            return f_100322ae4(items)',selector)
        self.assertIn('guard !paths.isEmpty else { return f_100322ae4(items) }',selector)
        for p in self.proof['current_sources']:
            if p.endswith('OriginalPasteboard.swift') or p.endswith('OriginalPasteboardArchive.swift'):continue
            current = ROOT / p
            if p.endswith('Pasteboard.swift'):
                current = ROOT / '.local/p0-repair/phase-34/before' / p
            self.assertEqual(current.read_bytes(),(self.phase/'before'/p).read_bytes())

    def test_decode_compatibility_and_codable_brand_contracts_are_preserved(self):
        archive=(ROOT/'replica/Sources/PastoCore/OriginalPasteboardArchive.swift').read_text()
        self.assertIn('forClassName: "PasteCore.PasteboardItem"',archive)
        self.assertIn('forClassName: "_TtC9PasteCore14PasteboardItem"',archive)
        for name in ['PastoCore.OriginalPasteboardItem','_TtC9PastoCore22OriginalPasteboardItem']:
            line='            decoder.setClass(OriginalPasteboardItem.self, forClassName: "'+name+'")\n'
            self.assertEqual(archive.count(line),1)
            archive=archive.replace(line,'',1)
        self.assertEqual(archive,(self.phase/'before/replica/Sources/PastoCore/OriginalPasteboardArchive.swift').read_text())
        self.assertIn('private enum CodingKeys: String, CodingKey { case types, dataByType }',self.item)
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertEqual(len(self.proof['retained_partial_contracts']),3)
        self.assertIsNone(self.proof['source_case']['before_explicit_runtime_name'])
        self.assertEqual(self.proof['source_case']['after_runtime_name'],self.proof['source_case']['original_runtime_name'])

if __name__=='__main__':unittest.main()
