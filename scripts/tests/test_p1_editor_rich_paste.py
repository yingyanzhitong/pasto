"""Native/source contracts only: does not execute Swift, AppKit or the application."""
from pathlib import Path
import hashlib, json, struct, sys, unittest
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
D = ROOT/'.local/p0-p1-parent-review/2026-11-03-editor-paste'
P = 'replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift'
H = 'replica/Sources/PastoCore/OriginalPreviewAttributedText.swift'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

class EditorRichPaste(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proof=json.loads((D/'contract.json').read_text())
        cls.baseline=json.loads((D/'baseline.json').read_text())['files']
        cls.source=(ROOT/P).read_text(); cls.helper=(ROOT/H).read_text()
        cls.editor=body(cls.source,'private final class ReplicaInlinePreviewTextView:')
        cls.paste=body(cls.editor,'override func paste(')
        cls.n={};exec((ROOT/cls.proof['decoder']['path']).read_text().split('selectors=[]',1)[0],cls.n)
    def order(self,s,tokens):
        positions=[s.index(t)for t in tokens];self.assertEqual(positions,sorted(positions))
    def test_original_and_current_inputs_fresh(self):
        cache={}
        for r in self.proof['original_fragments']:
            p=ROOT/r['path']
            if p not in cache:cache[p]=source_fragments(p)
            self.assertEqual(cache[p][r['function_id'].split(':')[1]]['sha256'],r['sha256'])
        for key in ['binary','decoder']:
            r=self.proof[key];self.assertEqual(sha(ROOT/r['path']),r['sha256'])
        for p,h in self.proof['current_sources'].items():self.assertEqual(sha(ROOT/p),h)
    def test_native_ranges_and_branches_fresh(self):
        for r in self.proof['machine_ranges']:
            data=self.n['read'](int(r['address'],16),int(r['end'],16)-int(r['address'],16))
            self.assertEqual(data.hex(),r['bytes']);self.assertEqual(hashlib.sha256(data).hexdigest(),r['sha256'])
        for r in self.proof['branches']:
            pc=int(r['pc'],16);word=struct.unpack('<I',self.n['read'](pc,4))[0]
            self.assertEqual(hex(word),r['word']);v=word&0x3ffffff
            if v&1<<25:v-=1<<26
            self.assertEqual(hex(pc+4*v),r['target'])
    def test_actual_native_class_registers_paste_entry(self):
        c=self.proof['method_binding'][0];m=c['methods'][0]
        def ptr(a):
            v,chain=self.n['reachable_pointer'](a);self.assertFalse(v>>63)
            return self.n['base']+(v&((1<<36)-1))
        cls=ptr(int(c['classlist_slot'],16));self.assertEqual(hex(cls),c['class_address'])
        ro=ptr(cls+32)&~7;self.assertEqual(hex(ro),c['ro'])
        name=ptr(ro+24);self.assertEqual(self.n['read'](name,len(c['class_name'])+1),c['class_name'].encode()+b'\0')
        self.assertEqual(hex(ptr(ro+32)),c['method_list'])
        self.assertIn('PasteUI10TextEditor',c['class_name']);self.assertEqual(m['selector'],'paste:')
        self.assertEqual(m['types'],'v24@0:8@16');self.assertEqual(m['implementation'],'0x10021540c')
        a=int(m['entry'],16);data=self.n['read'](a,12);self.assertEqual(data.hex(),m['bytes'])
        x,y,z=struct.unpack('<iii',data);self.assertEqual(hex(a+8+z),m['implementation'])
        self.assertEqual(hex(a+x),m['selector_reference'])
        value,chain=self.n['reachable_pointer'](a+x);self.assertTrue(chain['declared_chain_reachable'])
        target=self.n['base']+(value&((1<<36)-1));self.assertEqual(self.n['read'](target,7),b'paste:\0')
    def test_actual_selector_import_names_and_callback_literals(self):
        raw=self.n['raw'];fixup=self.n['fixup'][0];header=struct.unpack_from('<7I',raw,fixup)
        for r in self.proof['calls']:
            value,chain=self.n['reachable_pointer'](int(r['pointer'],16));self.assertEqual(chain,r['chain'])
            if value>>63:
                entry=struct.unpack_from('<I',raw,fixup+header[2]+4*(value&0xffffff))[0]
                at=fixup+header[3]+(entry>>9)
            else:at=self.n['offset'](self.n['base']+(value&((1<<36)-1)))
            self.assertEqual(raw[at:raw.index(b'\0',at)].decode(),r['name'])
        for r in self.proof['callback_literals']:
            pc=int(r['pc'],16);data=self.n['read'](pc,8);self.assertEqual(data.hex(),r['bytes'])
            a,b=struct.unpack('<II',data);v=(((a>>5)&0x7ffff)<<2)|((a>>29)&3)
            if v&1<<20:v-=1<<21
            self.assertEqual(hex((pc&~4095)+(v<<12)+((b>>10)&4095)),r['target'])
    def test_original_three_storage_reads_two_undo_reads_and_order(self):
        calls=[x['name']for x in self.proof['calls']if x['function_id']=='Paste:0x100214e78'and x['selector_stub']]
        self.assertEqual(calls.count('textStorage'),3);self.assertEqual(calls.count('undoManager'),2)
        self.order('\n'.join(calls),['readObjectsForClasses:options:','beginUndoGrouping','beginEditing','selectedRange',
                     'initWithString:attributes:','enumerateAttributesInRange:options:usingBlock:',
                     'replaceCharactersInRange:withAttributedString:','endUndoGrouping'])
        self.assertTrue(any(x['name']=='_objc_msgSendSuper2'for x in self.proof['calls']if x['function_id']=='Paste:0x100214e78'))
    def test_real_editor_constructed_with_rich_text_and_undo(self):
        consumer=body(self.source,'private final class ReplicaInlineTextPreviewContent:')
        for s in ['text = ReplicaInlinePreviewTextView(frame: .zero)','text.isRichText = true','text.allowsUndo = true']:
            self.assertIn(s,consumer)
        key=body(self.editor,'override func performKeyEquivalent(')
        self.assertNotIn('case "v"',key);self.assertIn('super.performKeyEquivalent(with: event)',key)
    def test_read_only_first_attributed_object_with_system_fallback(self):
        self.assertIn('NSPasteboard.general.readObjects(forClasses: [NSAttributedString.self]',self.paste)
        self.assertIn('options: nil)?.first as? NSAttributedString else',self.paste)
        self.order(self.paste,['guard let source','super.paste(sender)','return','undoManager?.beginUndoGrouping()'])
        for wrong in ['compactMap','clearContents','writeObjects','isEditable','try?','catch','isEmpty']:
            self.assertNotIn(wrong,self.paste)
    def test_storage_and_undo_reads_not_cached_or_reordered(self):
        self.assertEqual(self.paste.count('textStorage'),3);self.assertEqual(self.paste.count('undoManager?'),2)
        self.order(self.paste,['undoManager?.beginUndoGrouping()','textStorage?.beginEditing()',
                    'if let storage = textStorage','let range = selectedRange()',
                    'normalizedEditingText(source)','storage.replaceCharacters(in: range, with: replacement)',
                    'textStorage?.endEditing()','undoManager?.endUndoGrouping()'])
        for wrong in ['guard let storage','defer','didChangeText','shouldChangeText','DispatchQueue','removeAllActions']:
            self.assertNotIn(wrong,self.paste)
    def test_normalization_reuses_existing_utf16_and_attribute_pipeline_unchanged(self):
        self.assertEqual(sha(ROOT/H),self.baseline[H])
        s=body(self.helper,'public static func normalizedEditingText(')
        self.order(s,['NSMutableAttributedString(string: source.string, attributes: [.font: f_1000f3ef4()])',
                     'result.beginEditing()','source.enumerateAttributes(in: f_100309700(source), options: [])',
                     'f_1003c1860(attributes: attributes, range: range, destination: result)',
                     'result.endEditing()','return result'])
        self.assertIn('NSRange(location: 0, length: source.length)',self.helper)
        run=body(self.helper,'public static func f_1003c1860(')
        self.assertIn('symbolicTraits.rawValue & 3',run)
        self.assertIn('key == .underlineStyle || key == .strikethroughStyle',run)
        for key in ['foregroundColor','backgroundColor','paragraphStyle','link','attachment']:
            self.assertNotIn('.'+key,run)
        self.assertEqual(struct.unpack('<I',self.n['read'](0x100215924,4))[0],0x120006c0)
    def test_original_paste_and_existing_normalizer_share_font_and_decoration_rules(self):
        for fid in ['Paste:0x100215840','Paste:0x1003c1860']:
            r=next(x for x in self.proof['original_fragments']if x['function_id']==fid)
            source=(ROOT/r['path']).read_text();a=source.index('/* Address: '+fid.split(':')[1]+' |');b=source.find('/* Address:',a+1)
            source=source[a:b]
            for token in ['NSFontAttributeName','NSUnderlineStyleAttributeName','NSStrikethroughStyleAttributeName',
                          'FUN_1000f3ef4','FUN_1000f3f6c','FUN_100215bf0','(uint)IVar3 & 3']:
                self.assertIn(token,source)
    def test_sdk_contracts_bound_without_compiler(self):
        for p,h in self.proof['sdk_headers'].items():self.assertEqual(sha(ROOT/p),h)
        self.assertFalse(self.proof['compiled']);self.assertFalse(self.proof['framework_executed'])
    def test_only_one_recorded_production_edit_and_old_tests_preserved(self):
        self.assertEqual({p for p,h in self.baseline.items()if sha(ROOT/p)!=h},{P})
        actual={str(p.relative_to(ROOT))for p in(ROOT/'replica/Sources').rglob('*')if p.is_file()}
        self.assertEqual(actual,{p for p in self.baseline if p.startswith('replica/Sources/')})
        self.assertEqual(len(actual),249)
        before=(D/'before'/P).read_text()
        begin=self.source.index('    // Paste 0x10021540c → 0x100214e78:')
        end=self.source.index('    override func validateUserInterfaceItem(',begin)
        self.assertEqual(self.source[:begin]+self.source[end:],before)
    def test_scope_admits_only_actual_business_entries_without_glue_inflation(self):
        self.assertEqual(set(self.proof['new_P1_candidates']),{'Paste:0x100214e78','Paste:0x10021540c','Paste:0x100215840'})
        self.assertFalse(self.proof['generic_callback_glue_in_denominator'])
        self.assertFalse(self.proof['full_function_migration_verified'])

if __name__ == '__main__':unittest.main()
