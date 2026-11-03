import hashlib
import json
import struct
import subprocess
import unittest
from test_offline_p0_contracts import ROOT
from test_p0_p1_review_round2 import digest, fragment

class P0P1ReviewRound24(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((ROOT/'reports/replica/p0-p1-review-round24.json').read_text())
        cls.prior=json.loads((ROOT/'reports/replica/p0-p1-review-round23.json').read_text())
        cls.scope=json.loads((ROOT/cls.report['scope_manifest']).read_text())
        cls.proof=json.loads((ROOT/cls.report['static_proof']['path']).read_text())
        cls.boundary=json.loads((ROOT/cls.report['boundary_decisions']['path']).read_text())
        cls.binary=(ROOT/cls.proof['binary_path']).read_bytes()
        cls.rows={r['function_id']:r for r in cls.report['records']}
    def offset(self,a):
        s=next(s for s in self.proof['file_backed_segments']if s['vmaddr']<=a<s['vmaddr']+s['filesize'])
        return s['fileoff']+a-s['vmaddr']
    def word(self,a):return struct.unpack_from('<I',self.binary,self.offset(a))[0]
    def branch(self,a):
        w=self.word(a);self.assertEqual(w&0xfc000000,0x94000000);imm=w&0x3ffffff
        return a+(imm-(1<<26)if imm&(1<<25)else imm)*4

    def test_scope_four_preserves_old_records_and_adds_only_three_p1_leaves(self):
        self.assertEqual(self.scope['version'],4);self.assertEqual(self.scope['denominator'],649)
        self.assertEqual(self.scope['expansion']['added_function_ids'],['Paste:0x100206b5c','Paste:0x100207648','Paste:0x1003095bc'])
        for r in self.prior['records']:self.assertEqual(self.rows[r['function_id']],r)
        for fid in self.scope['expansion']['added_function_ids']:self.assertEqual(self.rows[fid]['priorities'],['P1'])

    def test_comparison_counts_do_not_claim_migration_complete(self):
        self.assertEqual(self.report['resolved_review_records'],647);self.assertEqual(self.report['resolved_comparison_percent'],99.69)
        self.assertEqual(self.report['outcomes'],dict(local_contract_consistent=494,difference_confirmed=144,user_adaptation_confirmed=9,unclosed=2))
        self.assertEqual(self.report['p1_additional_component']['resolved'],382)
        self.assertEqual(self.report['p1_additional_component']['denominator'],384)
        self.assertIsNone(self.report['full_priority_completion_percent'])
        self.assertTrue(self.report['scope_provisional'])
        self.assertFalse(any(r['full_function_migration_verified']for r in self.rows.values()))

    def test_all_report_and_candidate_inputs_are_fresh(self):
        for p,h in self.report['source_inputs'].items():self.assertEqual(digest(p),h,p)
        self.assertEqual(digest(self.report['scope_manifest']),self.report['scope_manifest_sha256'])
        self.assertEqual(digest(self.report['difference_backlog']['path']),self.report['difference_backlog']['sha256'])

    def test_new_fragments_and_real_source_literals(self):
        for fid in self.scope['expansion']['added_function_ids']:
            r=self.rows[fid]
            for ref in [dict(r['original'],function_id=fid)]+r.get('supporting_original_fragments',[]):
                f=fragment(ref['function_id'].split(':')[1],ref['path'])
                self.assertEqual(hashlib.sha256(f.encode()).hexdigest(),ref['sha256'])
            for ref in r['current_references']:
                self.assertEqual(digest(ref['path']),ref['sha256']);self.assertIn(ref['symbol'],(ROOT/ref['path']).read_text())

    def test_static_blocks_and_real_parent_calls(self):
        self.assertEqual(hashlib.sha256(self.binary).hexdigest(),self.proof['binary_sha256'])
        for b in self.proof['blocks']:
            data=self.binary[b['file_offset']:b['file_offset']+b['length']]
            self.assertEqual(data.hex(),b['bytes']);self.assertEqual(hashlib.sha256(data).hexdigest(),b['sha256'])
            self.assertEqual(self.offset(int(b['address'],16)),b['file_offset'])
        for edge in self.proof['production_calls']:
            for site in edge['call_sites']:self.assertEqual(self.branch(int(site,16)),int(edge['target'],16))

    def test_full_attribute_range_flag_and_callback_stop(self):
        self.assertEqual(self.word(0x1003095d4),0x52800028) # flag true
        self.assertEqual(self.word(0x100309688),0xd2800002) # range start zero
        self.assertEqual(self.word(0x10030968c),0xaa1503e3) # length from actual getter
        self.assertEqual(self.word(0x100309690),0xd2800004) # options zero
        self.assertEqual(self.word(0x100309ad4),0x3900011f) # false in captured flag
        self.assertEqual(self.word(0x100309adc),0x39000068) # stop true
        selectors={r['selector']for r in self.proof['selectors']}
        self.assertEqual(selectors,{'length','enumerateAttributesInRange:options:usingBlock:'})
        current=(ROOT/'replica/Sources/PastoCore/OriginalPreviewAttributedText.swift').read_text()
        for token in ['NSRange(location: 0, length: source.length)','var isUnattributed = true','if !attributes.isEmpty {','isUnattributed = false','stop.pointee = true']:self.assertIn(token,current)

    def test_rgb_actual_hex_format_constants_truncation_and_current_consumer(self):
        for a in [0x100206ca8,0x100206d20,0x100206d98]:
            self.assertEqual(self.word(a),0x528604a0);self.assertEqual(self.word(a+4),0x72af0640)
        self.assertEqual((0x3025|(0x7832<<16)).to_bytes(4,'little'),b'%02x')
        for a,w in [(0x100206c8c,0x9e780168),(0x100206d14,0x9e780128),(0x100206d8c,0x9e780108)]:self.assertEqual(self.word(a),w)
        source=(ROOT/'replica/Sources/Pasto/UI/OriginalPreviewColorFormatting.swift').read_text()
        for channel in ['red','green','blue']:self.assertIn('String(format: "%02x", Int('+channel+' * 255))',source)
        self.assertIn('if let rgb = color.usingColorSpace(.deviceRGB)',source)
        self.assertIn('return "#" + redText + greenText + blueText',source)
        self.assertNotIn('max(',source);self.assertNotIn('min(',source)

    def test_trait_conversion_preserves_explicit_remove_and_fallback_structure(self):
        original=fragment('0x100207648','decompiled/Paste/part-0171.c')
        for token in ['if ((param_2 & 1) == 0)','FUN_100207db8()','FUN_100208290()','fontDescriptorWithSymbolicTraits_(IVar6,(ulong)uVar1)','if (local_b8[0] != 0)']:self.assertIn(token,original)
        source=(ROOT/'replica/Sources/PastoCore/OriginalPreviewTextTraits.swift').read_text()
        for token in ['let remove = forceRemove || f_100208290(trait, in: f_100207db8(attributes))','if remove { result.removeValue(forKey: key) }','else { result[key] = 1 }','guard let font = attributes[.font] as? NSFont else { return result }','NSFont(descriptor: changed ?? descriptor, size: font.pointSize)','else { result.removeValue(forKey: .font) }']:self.assertIn(token,source)
        self.assertIn('普通类型属性字典',self.rows['Paste:0x100207648']['contract'])

    def test_boundary_corrects_duplicate_and_holds_unbound_domain(self):
        rows={r['function_id']:r for r in self.boundary['records']}
        self.assertEqual(rows['Paste:0x1003614c0']['decision'],'already_in_scope')
        self.assertEqual(self.rows['Paste:0x1003614c0']['status'],'difference_confirmed')
        self.assertEqual(rows['Paste:0x1003b9490']['decision'],'hold_domain')
        self.assertNotIn('Paste:0x1003b9490',self.rows)
        self.assertEqual(rows['Paste:0x100066570']['decision'],'support_only')
        self.assertFalse(self.boundary['full_original_priority_classification_complete'])
        self.assertEqual(self.boundary['candidate_count'],682)

    def test_production_and_head_remain_unchanged(self):
        baseline=json.loads((ROOT/'.local/p0-review/production-before.json').read_text());self.assertEqual(len(baseline),218)
        for p,h in baseline.items():self.assertEqual(digest(p),h,p)
        self.assertEqual(digest('replica/function-map.json'),'ea781c82f93e580a940f0804fa120e01e9030357d10aee157fe4a135143b8985')
        self.assertEqual(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'050e6878a5a52f96fe33aa40f48bb8a056cd0f05')
        for key in ['production_source_edited','function_map_modified','compiled','application_executed','network_used','committed','pushed']:self.assertFalse(self.report[key])
