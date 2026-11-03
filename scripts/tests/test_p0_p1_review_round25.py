import hashlib
import json
import struct
import subprocess
import unittest
from test_offline_p0_contracts import ROOT
from test_p0_p1_review_round2 import digest, fragment

class P0P1ReviewRound25(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((ROOT/'reports/replica/p0-p1-review-round25.json').read_text())
        cls.prior=json.loads((ROOT/'reports/replica/p0-p1-review-round24.json').read_text())
        cls.scope=json.loads((ROOT/cls.report['scope_manifest']).read_text())
        cls.proof=json.loads((ROOT/cls.report['static_proof']['path']).read_text())
        cls.boundary=json.loads((ROOT/cls.report['boundary_decisions']['path']).read_text())
        cls.rows={r['function_id']:r for r in cls.report['records']}
        cls.binary=(ROOT/cls.proof['binary_path']).read_bytes()
    def offset(self,a):
        s=next(s for s in self.proof['file_backed_segments']if s['vmaddr']<=a<s['vmaddr']+s['filesize']);return s['fileoff']+a-s['vmaddr']
    def word(self,a):return struct.unpack_from('<I',self.binary,self.offset(a))[0]
    def pointer(self,a):return 0x100000000+(struct.unpack_from('<Q',self.binary,self.offset(a))[0]&((1<<36)-1))
    def relative(self,a):return a+struct.unpack_from('<i',self.binary,self.offset(a))[0]
    def string(self,a):
        o=self.offset(a);return self.binary[o:self.binary.index(b'\0',o)].decode()

    def test_new_scope_keeps_old_records_and_admits_unknown_honestly(self):
        self.assertEqual(self.scope['version'],5);self.assertEqual(self.scope['denominator'],656)
        for r in self.prior['records']:self.assertEqual(r,self.rows[r['function_id']])
        self.assertEqual(len(self.scope['expansion']['added_function_ids']),7)
        self.assertEqual(self.rows['Paste:0x100383d90']['status'],'unclosed')
        self.assertNotIn('Paste:0x1003b9490',self.rows)

    def test_counts_are_finite_comparison_not_migration(self):
        self.assertEqual(self.report['resolved_review_records'],653);self.assertEqual(self.report['resolved_comparison_percent'],99.54)
        self.assertEqual(self.report['outcomes'],dict(local_contract_consistent=500,difference_confirmed=144,user_adaptation_confirmed=9,unclosed=3))
        self.assertEqual(self.report['p0_component']['denominator'],266)
        self.assertEqual(self.report['p1_additional_component']['denominator'],390)
        self.assertTrue(self.report['scope_provisional']);self.assertIsNone(self.report['full_priority_completion_percent'])
        self.assertFalse(any(r['full_function_migration_verified']for r in self.rows.values()))

    def test_all_bound_inputs_and_added_current_literals(self):
        for p,h in self.report['source_inputs'].items():self.assertEqual(digest(p),h,p)
        for fid in self.scope['expansion']['added_function_ids']:
            r=self.rows[fid]
            for ref in r['current_references']:
                self.assertEqual(digest(ref['path']),ref['sha256']);self.assertIn(ref['symbol'],(ROOT/ref['path']).read_text())

    def test_new_original_fragments_and_machine_blocks(self):
        for fid in self.scope['expansion']['added_function_ids']:
            r=self.rows[fid]
            for ref in [dict(r['original'],function_id=fid)]+r.get('supporting_original_fragments',[]):
                s=fragment(ref['function_id'].split(':')[1],ref['path']);self.assertEqual(hashlib.sha256(s.encode()).hexdigest(),ref['sha256'])
        self.assertEqual(hashlib.sha256(self.binary).hexdigest(),self.proof['binary_sha256'])
        for block in self.proof['blocks']:
            o=block['file_offset'];b=self.binary[o:o+block['length']]
            self.assertEqual(b.hex(),block['bytes']);self.assertEqual(hashlib.sha256(b).hexdigest(),block['sha256'])

    def test_analytics_class_field_method_and_protocol_binding(self):
        p=self.proof['analytics_binding'];m=int(p['class_metadata'],16);d=self.pointer(m+0x40)
        self.assertEqual(d,int(p['class_descriptor'],16));self.assertEqual(self.string(self.relative(d+8)),'ItemCollectionViewModel')
        self.assertEqual(self.pointer(int(p['method_slot'],16)),0x1003b9490)
        fields={r['name']:r for r in p['fields']}
        self.assertEqual(fields['analytics']['object_offset'],'0x38');self.assertEqual(fields['context']['object_offset'],'0x40')
        for r in p['symbolic_types']:
            encoded=int(r['encoded_address'],16);slot=self.relative(encoded+1);desc=self.pointer(slot)
            self.assertEqual(slot,int(r['indirect_slot'],16));self.assertEqual(self.string(self.relative(desc+8)),r['name'])
            module=self.relative(desc+4);self.assertEqual(self.string(self.relative(module+8)),r['module'])
        self.assertEqual(p['symbolic_types'][-1]['module'],'PasteAnalytics')
        self.assertEqual(self.word(0x1003b96c0),0xf9401f88) # analytics at owner+38
        self.assertEqual(self.word(0x1003b9760),0xf94012a8) # witness+20

    def test_analytics_exclusion_and_support_counts_do_not_inflate_progress(self):
        rows={r['function_id']:r for r in self.boundary['records']}
        self.assertEqual(rows['Paste:0x1003b9490']['decision'],'exclude')
        self.assertEqual(rows['Paste:0x1003b9490']['previous_decision'],'hold_domain')
        self.assertEqual(self.boundary['counts'],dict(admit=7,support_only=5,exclude=1))
        for fid in ['Paste:0x1002080e0','Paste:0x100208024','Paste:0x1002085e0','Paste:0x10021453c']:self.assertNotIn(fid,self.rows)

    def test_trait_projection_union_range_and_callback_order_sources(self):
        s=(ROOT/'replica/Sources/PastoCore/OriginalPreviewTextTraits.swift').read_text()
        for token in ['if let underline = attributes[.underlineStyle] as? Int, underline == 1','if let strike = attributes[.strikethroughStyle] as? Int, strike == 1','result.formUnion(traits)','if range.location <= content.length','if end <= content.length, editor.selectedRange().length != 0','for key in attributes.keys { storage.removeAttribute(key, range: range) }']:self.assertIn(token,s)
        native=fragment('0x1002083e4','decompiled/Paste/part-0171.c')
        self.assertLess(native.index('objc_stub::removeAttribute_range_'),native.index('FUN_100207648('))
        self.assertLess(native.index('FUN_100207648('),native.index('objc_stub::addAttributes_range_'))
        a=s.index('public func f_100214704()');z=s.index('public func f_10021453c()',a);method=s[a:z]
        self.assertLess(method.index('onTraitsChange?'),method.index('onAttributedTextChange?'))

    def test_async_descriptor_and_continuation_corrections(self):
        for r in self.proof['async_descriptors']:self.assertEqual(self.relative(int(r['address'],16)),int(r['target'],16))
        index={r['address']:r for r in json.loads((ROOT/'reports/Paste/function-index.json').read_text())}
        for a,target in [('0x100213f58','FUN_100213fe8'),('0x100214674','FUN_100214704')]:self.assertIn('_swift_task_switch('+target,fragment(a,index[a]['file']))
        self.assertIn('异步续体',self.rows['Paste:0x100213fe8']['primary_review_correction'])
        self.assertIn('不把异步continuation存储与同步Bool返回的ABI',self.rows['Paste:0x100213fe8']['contract'])
        self.assertIn('回调不销毁或重入',self.rows['Paste:0x100214704']['contract'])

    def test_image_dispatch_is_tail_result_and_still_unknown_mapping(self):
        self.assertEqual(self.word(0x100383dc0),0x1400000d)
        self.assertEqual(0x100383dc0+(self.word(0x100383dc0)&0x3ffffff)*4,0x100383df4)
        row=self.rows['Paste:0x100383d90'];self.assertEqual(row['status'],'unclosed')
        self.assertIn('并非保持原实体不变',row['contract']);self.assertIn('不能叫系统NSPasteboardItem',row['evidence_note'])

    def test_production_map_and_head_unchanged(self):
        baseline=json.loads((ROOT/'.local/p0-review/production-before.json').read_text());self.assertEqual(len(baseline),218)
        for p,h in baseline.items():self.assertEqual(digest(p),h,p)
        self.assertEqual(digest('replica/function-map.json'),'ea781c82f93e580a940f0804fa120e01e9030357d10aee157fe4a135143b8985')
        self.assertEqual(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'050e6878a5a52f96fe33aa40f48bb8a056cd0f05')
        for key in ['production_source_edited','function_map_modified','compiled','application_executed','network_used','committed','pushed']:self.assertFalse(self.report[key])
