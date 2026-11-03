import hashlib
import json
import struct
import subprocess
import unittest
from test_offline_p0_contracts import ROOT
from test_p0_p1_review_round2 import digest, fragment

class P0P1ReviewRound26(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((ROOT/'reports/replica/p0-p1-review-round26.json').read_text());cls.prior=json.loads((ROOT/'reports/replica/p0-p1-review-round25.json').read_text())
        cls.proof=json.loads((ROOT/cls.report['static_proof']['path']).read_text());cls.binary=(ROOT/cls.proof['binary_path']).read_bytes();cls.rows={r['function_id']:r for r in cls.report['records']}
    def offset(self,a):
        s=next(s for s in self.proof['file_backed_segments']if s['vmaddr']<=a<s['vmaddr']+s['filesize']);return s['fileoff']+a-s['vmaddr']
    def branch(self,a):
        w=struct.unpack_from('<I',self.binary,self.offset(a))[0];self.assertEqual(w&0xfc000000,0x94000000);v=w&0x3ffffff;return a+(v-(1<<26)if v&(1<<25)else v)*4

    def test_no_counter_or_status_inflation(self):
        self.assertEqual(self.report['outcomes'],self.prior['outcomes']);self.assertEqual(self.report['resolved_review_records'],653)
        self.assertEqual(self.report['comparison_denominator'],656);self.assertEqual(self.report['resolved_comparison_percent'],99.54)
        self.assertEqual(self.rows['Paste:0x100383d90']['status'],'unclosed');self.assertIsNone(self.report['full_priority_completion_percent'])
        for r in self.prior['records']:
            if r['function_id']!='Paste:0x100383d90':self.assertEqual(r,self.rows[r['function_id']])

    def test_inputs_current_references_and_fragments_are_exact(self):
        for p,h in self.report['source_inputs'].items():self.assertEqual(digest(p),h,p)
        r=self.rows['Paste:0x100383d90']
        for ref in r['current_references']:
            self.assertEqual(digest(ref['path']),ref['sha256']);self.assertIn(ref['symbol'],(ROOT/ref['path']).read_text());self.assertNotIn('Cloud',ref['path'])
        for ref in r['supporting_original_fragments']:
            self.assertEqual(hashlib.sha256(fragment(ref['function_id'].split(':')[1],ref['path']).encode()).hexdigest(),ref['sha256'])

    def test_binary_getter_selector_and_direct_calls(self):
        p=self.proof['raw_items_getter'];slot=int(p['selector_slot'],16)
        a=0x100000000+(struct.unpack_from('<Q',self.binary,self.offset(slot))[0]&((1<<36)-1));o=self.offset(a)
        self.assertEqual(self.binary[o:self.binary.index(b'\0',o)],b'rawPasteboardItems')
        self.assertEqual(a,int(p['selector_address'],16))
        for edge in self.proof['direct_calls']:
            for site in edge['call_sites']:self.assertEqual(self.branch(int(site,16)),int(edge['target'],16))
        self.assertEqual(self.branch(0x10037b62c),0x10037ade4)

    def test_all_machine_blocks_match_original(self):
        self.assertEqual(hashlib.sha256(self.binary).hexdigest(),self.proof['binary_sha256'])
        for b in self.proof['blocks']:
            v=self.binary[b['file_offset']:b['file_offset']+b['length']];self.assertEqual(v.hex(),b['bytes']);self.assertEqual(hashlib.sha256(v).hexdigest(),b['sha256'])

    def test_local_capture_has_conditional_blob_and_single_item_fallback(self):
        s=(ROOT/'replica/Sources/PastoCore/Pasteboard.swift').read_text()
        self.assertIn('if capturedItems.count > 1 {\n            payloads[originalItemDataPayloadKey] = OriginalPasteboardDataCodec.f_10031a8e8(capturedItems, useBinaryPlist: preferences.useBinaryPlist)',s)
        self.assertIn('items = OriginalPasteboardDataCodec.f_10031aeec(data)',s)
        self.assertIn('object = OriginalPasteboardItem(types: try JSONDecoder().decode([String].self, from: data),',s)
        self.assertIn('case .text: kind = types.isDisjoint(with: richTypes) ? .text : .richText',s)

    def test_timestamp_false_difference_was_not_adopted(self):
        r=self.rows['Paste:0x100383d90'];correction=json.loads((ROOT/'.local/p0-review/p0-p1-round26-restore-time-correction.json').read_text())
        self.assertEqual(correction['records'][0]['previous_round26_status'],'difference_confirmed')
        self.assertEqual(correction['records'][0]['corrected_status'],'local_contract_consistent')
        self.assertEqual(r['finite_subcontracts_round26'][1]['conclusion'],'local_contract_consistent')
        self.assertEqual(self.report['outcomes']['difference_confirmed'],144)
        self.assertIn('37b620→37ade4固定History witness+28→3614c0→361ec0',r['finite_subcontracts_round26'][1]['evidence'])

    def test_cloud_export_and_image_entity_return_are_rejected_as_proof(self):
        r=self.rows['Paste:0x100383d90'];self.assertTrue(r['not_adopted_child_references'])
        self.assertIn('不属于本轮离线consumer',r['evidence_note']);self.assertIn('rawType=1尾调383df4返回表示数组',r['contract'])
        self.assertFalse(r['full_function_migration_verified'])

    def test_production_head_and_map_unchanged(self):
        before=json.loads((ROOT/'.local/p0-review/production-before.json').read_text());self.assertEqual(len(before),218)
        for p,h in before.items():self.assertEqual(digest(p),h,p)
        self.assertEqual(digest('replica/function-map.json'),'ea781c82f93e580a940f0804fa120e01e9030357d10aee157fe4a135143b8985')
        self.assertEqual(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'050e6878a5a52f96fe33aa40f48bb8a056cd0f05')
