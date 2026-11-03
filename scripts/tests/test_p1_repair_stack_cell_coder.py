"""Original embedded NIB producer and Stack cell coder; no unarchiving/framework execution."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from compiled_nib_static import decode_nib_archive,nib_string
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment
from stack_cell_coder_scope_contract import CHANGES,pre_stack_cell_coder,pre_stack_cell_coder_bytes
from stack_table_drag_scope_contract import pre_stack_table_drag_bytes
class StackCellCoder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-145';cls.p=json.loads((cls.phase/'stack-cell-coder-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.path='replica/Sources/Pasto/UI/OriginalStackSnippetCell.swift';cls.src=(ROOT/cls.path).read_text();cls.coder=body(cls.src,'required init?(coder:');cls.outer=decode_nib_archive(Path(cls.p['embedded_cell']['outer_path']).read_bytes());e=cls.p['embedded_cell'];cls.blob=next(v for k,t,v in cls.outer['rows'][e['owner_object']]['values']if k==e['data_key']and t==8);cls.inner=decode_nib_archive(cls.blob);cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
    def original(self,a):
        r=next(r for r in self.p['original_fragments']if r['address']==a);return original_fragment((ROOT/r['path']).read_text(),a[2:])
    def test_eight_original_fragments_binary_and_both_static_decoders_bound(self):
        self.assertEqual(len(self.p['original_fragments']),8)
        for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for k in ['binary','decoder','archive_decoder']:
            r=self.p[k];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_installed_fat_arm64_slice_is_exact_original_decompiler_binary(self):
        r=self.p['installed_app'];raw=Path(r['binary_path']).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),r['binary_sha256']);self.assertEqual(raw[:4],b'\xca\xfe\xba\xbe');found=[]
        for i in range(struct.unpack_from('>I',raw,4)[0]):
            cpu,sub,off,size,align=struct.unpack_from('>5I',raw,8+i*20)
            if cpu==0x100000c:found.append(dict(offset=off,size=size,sha256=hashlib.sha256(raw[off:off+size]).hexdigest()))
        self.assertEqual(found,[r['arm64']]);self.assertEqual(found[0]['sha256'],self.p['binary']['sha256']);self.assertEqual(r['version'],'6.6.6');self.assertEqual(hashlib.sha256(Path(r['info_path']).read_bytes()).hexdigest(),r['info_sha256'])
    def test_two_top_level_nib_tables_decode_exact_bounds_and_counts(self):
        self.assertEqual(len(self.p['resources']),2)
        for r in self.p['resources']:self.assertEqual(hashlib.sha256(Path(r['path']).read_bytes()).hexdigest(),r['sha256']);self.assertEqual(decode_nib_archive(Path(r['path']).read_bytes())['counts'],r['counts'])
        self.assertEqual(self.outer['counts']['objects'],198)
    def test_nested_template_reachable_from_table_reusable_views_entry(self):
        e=self.p['embedded_cell'];path=e['reusable_views_path'];self.assertEqual(path,[13,60,62,63]);self.assertIn(('NSTableViewArchivedReusableViewsKey',10,path[1]),self.outer['rows'][path[0]]['values'])
        for a,b in zip(path[1:],path[2:]):self.assertTrue(any(t==10 and v==b for k,t,v in self.outer['rows'][a]['values']))
        self.assertEqual(hashlib.sha256(self.blob).hexdigest(),e['sha256']);self.assertEqual(self.inner['counts'],e['counts']);self.assertEqual(self.inner['counts']['objects'],84)
    def test_nested_class_swap_declares_real_cell_and_table_cell_superclass(self):
        r=self.inner['rows'][7];self.assertEqual(r['cls'],'NSClassSwapper');props={k:(t,v)for k,t,v in r['values']};self.assertEqual(nib_string(self.inner,props['NSClassName'][1]),'_TtC5Paste21PasteStackSnippetCell');self.assertEqual(nib_string(self.inner,props['NSOriginalClassName'][1]),'NSTableCellView')
    def test_image_and_text_outlets_are_connected_to_same_cell(self):
        outlets=self.p['embedded_cell']['outlets'];self.assertEqual({r['label']:r['destination_class']for r in outlets},dict(imageView='NSImageView',textField='NSTextField'))
        for r in outlets:
            self.assertEqual(r['source'],7);row=self.inner['rows'][r['object']];self.assertEqual(row['cls'],'NSNibOutletConnector');d={k:(t,v)for k,t,v in row['values']};self.assertEqual(d['NSSource'],(10,7));self.assertEqual(nib_string(self.inner,d['NSLabel'][1]),r['label']);self.assertEqual(self.inner['rows'][d['NSDestination'][1]]['cls'],r['destination_class'])
    def test_runtime_class_metadata_matches_nib_class_name(self):
        r=self.p['class_binding'];v,c=self.n['reachable_pointer'](int(r['address'],16)+32);self.assertEqual(hex(v),r['data_raw']);self.assertEqual(c,r['data_chain']);ro=(self.n['base']+(v&((1<<36)-1)))&~7;w,d=self.n['reachable_pointer'](ro+24);self.assertEqual(hex(w),r['name_raw']);self.assertEqual(d,r['name_chain']);a=self.n['base']+(w&((1<<36)-1));self.assertEqual(self.n['read'](a,100).split(b'\0')[0].decode(),self.p['embedded_cell']['class_name'])
    def test_selector_and_imports_bind_super_coder_and_parent_table_cell(self):
        r=self.p['selector'];v,c=self.n['reachable_pointer'](int(r['address'],16));self.assertEqual(hex(v),r['raw']);self.assertEqual(c,r['chain']);a=self.n['base']+(v&((1<<36)-1));self.assertEqual(self.n['read'](a,100).split(b'\0')[0].decode(),'initWithCoder:');self.assertEqual({r['symbol']for r in self.p['imports']},{'_objc_msgSendSuper2','_OBJC_CLASS_$_NSTableCellView'})
        for r in self.p['imports']:
            v,c=self.n['reachable_pointer'](int(r['address'],16));self.assertEqual(hex(v),r['raw']);self.assertEqual(c,r['chain']);f=self.n['fixup'][0];h=struct.unpack_from('<7I',self.n['raw'],f);w=struct.unpack_from('<I',self.n['raw'],f+h[2]+4*(v&0xffffff))[0];p=f+h[3]+(w>>9);self.assertEqual(self.n['raw'][p:self.n['raw'].index(b'\0',p)].decode(),r['symbol'])
    def test_nine_actual_ARM_words_and_original_nil_propagating_coder_body(self):
        self.assertEqual(len(self.p['ARM_words']),9)
        for r in self.p['ARM_words']:self.assertEqual(self.n['read'](int(r['address'],16),4).hex(),r['bytes'])
        s=self.original('0x100051bd8');self.assertIn('_objc_msgSendSuper2(&local_50,"initWithCoder:",param_3)',s);self.assertIn('return IVar6',s);self.assertIn('FUN_100086658(param_3,param_5)',self.original('0x100085324'));self.assertIn('makeViewWithIdentifier_owner_',self.original('0x100086658'))
    def test_current_coder_initializes_provider_then_forwards_without_fatal_or_layout(self):
        self.assertLess(self.coder.index('nativeImageProvider ='),self.coder.index('super.init(coder: coder)'))
        for token in ['fatalError','NSImageView(','NSTextField(','addSubview','NSLayoutConstraint','init(frame:','runModal','DispatchQueue','Task {']:self.assertNotIn(token,self.coder)
        self.assertEqual(self.coder.count('super.init(coder: coder)'),1)
    def test_native_category_provider_is_lazy_and_does_not_decode_old_item(self):
        provider=body(self.coder,'nativeImageProvider =');self.assertIn('input.previewRawType() ?? 0',provider);self.assertIn('OriginalStackCategoryIcons.image(for:',provider);self.assertIn('OriginalPasteboardContentKind(rawValue: UInt8(rawType)) ?? .unknown',provider)
        for token in ['resolvedItem','store.','ClipboardPersistence','self.','NSImage(']:self.assertNotIn(token,provider)
        self.assertNotIn('OriginalStackCategoryIcons',self.coder[self.coder.index('super.init(coder: coder)'):])
    def test_four_programmatic_provider_and_update_methods_remain_identical(self):
        self.assertEqual(len(self.p['unchanged_methods']),4)
        for r in self.p['unchanged_methods']:self.assertEqual(hashlib.sha256(body(self.src,r['symbol']).encode()).hexdigest(),r['sha256'])
        self.assertIn('self.nativeImageProvider = nativeImageProvider',body(self.src,'    init(nativeImageProvider:'))
    def test_existing_actual_update_checks_outlets_before_provider_and_text(self):
        s=body(self.src,'func updateNativeSnippet(');self.assertIn('if let imageView { imageView.image = nativeImageProvider(input) }',s);self.assertLess(s.index('nativeImageProvider(input)'),s.index('textField?.maximumNumberOfLines = 2'));self.assertIn('if let textField',s)
        self.assertIn('objc_stub::imageView(unaff_x20)',self.original('0x1000519f8'));self.assertIn('objc_stub::setMaximumNumberOfLines_(IVar1,2)',self.original('0x1000519f8'))
    def test_archive_decoder_rejects_bad_magic_truncated_and_invalid_table_offsets(self):
        for bad in [b'',b'not a nib',self.blob[:49]]:
            with self.assertRaises(ValueError):decode_nib_archive(bad)
        bad=bytearray(self.blob);struct.pack_into('<I',bad,46,len(bad)+1)
        with self.assertRaises(ValueError):decode_nib_archive(bytes(bad))
    def test_one_hunk_one_file_preserves247_sources_and_five_shared_consumers(self):
        self.assertEqual(len(CHANGES),1);changed=[];paths={str(p.relative_to(ROOT))for p in(ROOT/'replica/Sources').rglob('*')if p.is_file()};self.assertEqual(paths,set(self.base['production']))
        for p,h in self.base['production'].items():
            if hashlib.sha256(pre_stack_table_drag_bytes(ROOT/p)).hexdigest()!=h:changed.append(p)
            self.assertEqual(hashlib.sha256(pre_stack_cell_coder_bytes(ROOT/p)).hexdigest(),h)
        self.assertEqual(changed,[self.path]);old=(self.phase/'before'/self.path).read_text();self.assertEqual(pre_stack_cell_coder(self.src),old);self.assertEqual(pre_stack_cell_coder(old),old)
        for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_stack_table_drag_bytes(ROOT/p)).hexdigest(),h)
    def test_stack_archive_does_not_close_search_coder_or_full_nib_loading_parent(self):
        self.assertEqual(self.p['function_id'],'Paste:0x100051bd8');self.assertEqual(self.p['new_difference_records'],1);self.assertFalse(self.p['full_function_migration_verified']);self.assertFalse(self.p['runtime_executed']);self.assertTrue(self.p['finite_contract_verified']);self.assertEqual(len(self.p['adaptations']),2);self.assertIn('NIB',self.p['adaptations'][1]);self.assertIn('04430c/0f733c',self.p['remaining'][1])
if __name__=='__main__':unittest.main()
