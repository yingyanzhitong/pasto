import hashlib
import json
import struct
import subprocess
import unittest
from test_offline_p0_contracts import ROOT, body
from test_p0_p1_review_round2 import digest, fragment

class P0P1ReviewRound27(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((ROOT/'reports/replica/p0-p1-review-round27.json').read_text());cls.prior=json.loads((ROOT/'reports/replica/p0-p1-review-round26.json').read_text())
        cls.rows={r['function_id']:r for r in cls.report['records']};cls.proof=json.loads((ROOT/cls.report['static_proof']['path']).read_text());cls.binary=(ROOT/cls.proof['binary_path']).read_bytes()
        cls.backlog=json.loads((ROOT/cls.report['difference_backlog']['path']).read_text())
    def offset(self,a):
        s=next(s for s in self.proof['file_backed_segments']if s['vmaddr']<=a<s['vmaddr']+s['filesize']);return s['fileoff']+a-s['vmaddr']
    def word(self,a):return struct.unpack_from('<I',self.binary,self.offset(a))[0]
    def branch(self,a):
        w=self.word(a);self.assertEqual(w&0xfc000000,0x94000000);v=w&0x3ffffff;return a+(v-(1<<26)if v&(1<<25)else v)*4

    def test_fixed_scope_one_new_finite_difference(self):
        self.assertEqual(self.report['comparison_denominator'],656);self.assertEqual(self.report['resolved_review_records'],654);self.assertEqual(self.report['resolved_comparison_percent'],99.70)
        self.assertEqual(self.report['outcomes'],dict(local_contract_consistent=500,difference_confirmed=145,user_adaptation_confirmed=9,unclosed=2))
        self.assertEqual(self.rows['Paste:0x100383d90']['status'],'difference_confirmed')
        for r in self.prior['records']:
            if r['function_id']!='Paste:0x100383d90':self.assertEqual(r,self.rows[r['function_id']])
        self.assertIsNone(self.report['full_priority_completion_percent']);self.assertFalse(any(r['full_function_migration_verified']for r in self.rows.values()))

    def test_every_report_backlog_and_new_original_reference_is_fresh(self):
        for source in [self.report,self.backlog]:
            for p,h in source['source_inputs'].items():self.assertEqual(digest(p),h,p)
        r=self.rows['Paste:0x100383d90']
        for ref in [dict(r['original'],function_id=r['function_id'])]+r['supporting_original_fragments']:
            self.assertEqual(hashlib.sha256(fragment(ref['function_id'].split(':')[1],ref['path']).encode()).hexdigest(),ref['sha256'])
        for ref in r['current_references']:
            self.assertEqual(digest(ref['path']),ref['sha256']);self.assertIn(ref['symbol'],(ROOT/ref['path']).read_text())

    def test_machine_image_directory_call_precedes_both_entity_decode_paths(self):
        self.assertEqual(hashlib.sha256(self.binary).hexdigest(),self.proof['binary_sha256'])
        for b in self.proof['blocks']:
            v=self.binary[b['file_offset']:b['file_offset']+b['length']];self.assertEqual(v.hex(),b['bytes']);self.assertEqual(hashlib.sha256(v).hexdigest(),b['sha256'])
        for call in self.proof['direct_calls']:self.assertEqual(self.branch(int(call['address'],16)),int(call['target'],16))
        directory=int(self.proof['original_image_stage']['directory_call'],16)
        self.assertEqual(self.branch(directory),0x100384824)
        for call in self.proof['original_image_stage']['decode_wrapper_calls']:
            self.assertLess(directory,int(call,16));self.assertEqual(self.branch(int(call,16)),0x10031b218)

    def test_current_payload_decode_really_precedes_image_prepare(self):
        s=(ROOT/'replica/Sources/PastoCore/Pasteboard.swift').read_text()
        method=body(s,'private func writeToPasteboard(ids:')
        self.assertLess(method.index('try reload()'),method.index('Self.ordinaryRestoreRepresentations(for: item'))
        self.assertLess(method.index('Self.ordinaryRestoreRepresentations(for: item'),method.index('Self.imageRestore.prepare('))
        ordinary=body(s,'public nonisolated static func ordinaryRestoreRepresentations(')
        self.assertIn('try originalPasteboardItems(from: item.payloads)',ordinary)
        decoder=body(s,'public nonisolated static func originalPasteboardItems(')
        self.assertIn('OriginalPasteboardDataCodec.f_10031aeec(data)',decoder)

    def test_plain_bits_static_machine_and_source_matrix(self):
        self.assertEqual(self.word(0x1003825cc),0x7100151f);self.assertEqual(self.word(0x1003825f0),0x7100111f)
        self.assertEqual(self.word(0x100382600),0x37080148);self.assertEqual(self.word(0x100382624),0x3607ff08)
        source=(ROOT/'replica/Sources/PastoCore/OriginalPasteboardRestore.swift').read_text()
        self.assertIn('options.contains(kind == .text || kind == .link ? .plainTextAndLinks : .plainOtherContent)',source)
        self.assertEqual(len(self.proof['options_matrix']),28)
        for r in self.proof['options_matrix']:
            flag=2 if r['raw_type']in [4,5]else 1
            self.assertEqual(r['plain'],bool(r['options']&flag));self.assertEqual(r['image_prepare'],r['raw_type']==1 and not r['plain'])

    def test_reload_fastpath_and_actual_objc_boundary_are_retained(self):
        store=(ROOT/'replica/Sources/PastoCore/ClipboardStore.swift').read_text();persistence=(ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text()
        self.assertIn('if local == baseline, try revision() == diskRevision { return }',body(store,'public func reload()'))
        self.assertIn('try OriginalObjCExceptionBridge.withResult(operation)',body(persistence,'private func perform<T>('))
        objc=(ROOT/'replica/Sources/PastoObjC/PRObjCExceptionCatcher.m').read_text();self.assertIn('@catch (NSException *exception)',objc)
        r=self.rows['Paste:0x100383d90'];self.assertIn('未据此推断相同CoreData fault结果或普通PNG内容不同',r['contract'])

    def test_backlog_snapshot_exactly_matches_final_145_record_set(self):
        current={r['function_id']:r for r in self.report['records']if r['status']=='difference_confirmed'}
        grouped=[r for g in self.backlog['groups']for r in g['records']]
        self.assertEqual(len(grouped),145);self.assertEqual({r['function_id']:r for r in grouped},current)
        snapshot=json.loads((ROOT/self.backlog['source_report']['path']).read_text())
        self.assertEqual({r['function_id']:r for r in snapshot['records']},current)
        self.assertEqual(self.backlog['counts'],dict(difference_records=145,p0_records=64,p1_additional_records=81,conservative_groups=132,p0_primary_groups=59,p1_primary_groups=73))
        self.assertEqual(self.backlog['changes_since_v2']['new_function_ids'],['Paste:0x100383d90'])
        self.assertEqual(self.rows['Paste:0x100383d90']['difference_origin'],'Paste:0x100383d90')

    def test_bounded_value_contracts_do_not_replace_phase_or_migration_evidence(self):
        r=self.rows['Paste:0x100383d90'];self.assertEqual(len(r['finite_subcontracts_round27']),2)
        self.assertIn('阶段顺序',r['coverage_boundaries']);self.assertFalse(r['full_function_migration_verified'])
        before=json.loads((ROOT/'.local/p0-review/production-before.json').read_text());self.assertEqual(len(before),218)
        for p,h in before.items():self.assertEqual(digest(p),h,p)
        self.assertEqual(digest('replica/function-map.json'),'ea781c82f93e580a940f0804fa120e01e9030357d10aee157fe4a135143b8985')
        self.assertEqual(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'050e6878a5a52f96fe33aa40f48bb8a056cd0f05')
