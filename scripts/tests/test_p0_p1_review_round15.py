"""Finite P0/P1 comparisons: immutable scope, capture fields, callback routing and errors."""
import hashlib
import json
import struct
import unittest
from collections import Counter

from test_offline_p0_contracts import ROOT, body
from test_p0_p1_review_round2 import digest, fragment


class P0P1ReviewRound15(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((ROOT/'reports/replica/p0-p1-review-round15.json').read_text())
        cls.prior=json.loads((ROOT/'reports/replica/p0-p1-review-round14.json').read_text())
        cls.rows={r['function_id']:r for r in cls.report['records']}
        cls.proof=json.loads((ROOT/cls.report['static_proof']['path']).read_text())
        cls.binary=(ROOT/cls.proof['binary_path']).read_bytes()

    def offset(self, address):
        for segment in self.proof['segments']:
            if segment['vmaddr']<=address<segment['vmaddr']+segment['filesize']:
                return segment['fileoff']+address-segment['vmaddr']
        self.fail(hex(address))

    def word(self, address):return struct.unpack_from('<I',self.binary,self.offset(address))[0]
    def qword(self, address):return struct.unpack_from('<Q',self.binary,self.offset(address))[0]
    def relative(self, address):return address+struct.unpack_from('<i',self.binary,self.offset(address))[0]
    def pointer(self, address):return 0x100000000+(self.qword(address)&((1<<36)-1))
    def string(self, address):
        start=self.offset(address);return self.binary[start:self.binary.index(b'\0',start)].decode()
    def branch(self, address):
        value=self.word(address);self.assertEqual(value>>26,0b100101)
        immediate=value&0x3ffffff
        return address+(immediate-(1<<26) if immediate&(1<<25) else immediate)*4

    def test_scope_stays_646_and_only_the_31_previously_unclosed_records_are_revisited(self):
        old={r['function_id']:r for r in self.prior['records']};changed=set(self.report['round_delta']['reviewed_function_ids'])
        self.assertEqual(set(self.rows),set(old));self.assertEqual(len(self.rows),646)
        self.assertEqual(len(changed),31);self.assertEqual(self.report['round_delta']['scope_added'],0)
        self.assertEqual(self.report['scope_manifest'],self.prior['scope_manifest'])
        self.assertEqual(self.report['scope_manifest_sha256'],self.prior['scope_manifest_sha256'])
        for fid in old:
            if fid in changed:
                self.assertEqual(old[fid]['status'],'unclosed')
                self.assertEqual(self.rows[fid]['previous_status'],'unclosed')
            else:self.assertEqual(self.rows[fid],old[fid])
        self.assertFalse(any(r['full_function_migration_verified'] for r in self.rows.values()))
        self.assertIsNone(self.report['full_priority_completion_percent'])

    def test_every_new_evidence_hash_body_and_current_literal_is_bound(self):
        for path,sha in self.report['source_inputs'].items():self.assertEqual(digest(path),sha,path)
        self.assertEqual(digest(self.report['static_proof']['path']),self.report['static_proof']['sha256'])
        self.assertEqual(hashlib.sha256(self.binary).hexdigest(),self.proof['binary_sha256'])
        for fid in self.report['round_delta']['reviewed_function_ids']:
            row=self.rows[fid]
            for ref in [dict(row['original'],function_id=fid)]+row.get('supporting_original_fragments',[]):
                address=ref.get('address') or ref['function_id'].split(':')[1]
                self.assertEqual(hashlib.sha256(fragment(address,ref['path']).encode()).hexdigest(),ref['sha256'],(fid,address))
            self.assertTrue(row['current_references'])
            for ref in row['current_references']:
                self.assertEqual(digest(ref['path']),ref['sha256'])
                self.assertIn(ref['symbol'],(ROOT/ref['path']).read_text(),fid)

    def test_capture_poll_timer_is_a_named_original_field_and_return_flow_is_a_query_not_poll(self):
        item=self.proof['capture_fields'];metadata=int(item['metadata'],16)
        nominal=self.pointer(metadata+0x40)
        self.assertEqual(nominal,int(item['nominal'],16))
        self.assertEqual(self.string(self.relative(nominal+8)),'Pasteboard')
        fields=self.relative(nominal+16);size,count=struct.unpack_from('<HI',self.binary,self.offset(fields)+10)
        _,vector=struct.unpack_from('<II',self.binary,self.offset(nominal)+36)
        actual={}
        for index in range(count):
            record=fields+16+index*size
            actual[self.string(self.relative(record+8))]=self.qword(metadata+vector*8+index*8)
        self.assertEqual(actual['pollTimer'],0x38);self.assertEqual(actual['syncTimer'],0x40)
        self.assertEqual(self.branch(0x10037aa1c),0x10037aa3c)
        self.assertEqual(self.word(0x10037aa20),0xf9401c13)  # LDR x19,[x0,#0x38]
        self.assertEqual(self.branch(0x100004b00),0x10037aa10)
        self.assertEqual(self.word(0x100004b1c),0x0a360108)  # BIC w8,w8,w22
        self.assertEqual(self.rows['Paste:0x100004ab8']['status'],'local_contract_consistent')
        self.assertIn('weak_owner_absent_optional_vs_bool',self.rows['Paste:0x100004ab8']['coverage_boundaries']['not_verified'])
        self.assertIn('return capture.pollTimer == nil',(ROOT/'replica/Sources/Pasto/AppMain.swift').read_text())

    def test_recorder_initial_values_are_consumed_by_actual_binding_state_object_and_view(self):
        text=(ROOT/'replica/Sources/PastoCore/OriginalShortcutRecorder.swift').read_text()
        initial=body(text,'public init(shortcut: OriginalShortcutValue?, onDetect: @escaping (OriginalShortcutValue?) -> Void)')
        for value in ['validationError = nil','eventMonitor = nil','state = shortcut.map(OriginalShortcutRecorderState.assigned) ?? .unassigned','self.onDetect = onDetect']:
            self.assertIn(value,initial)
        self.assertNotIn('addLocalMonitor',initial)
        view=(ROOT/'replica/Sources/PastoCore/OriginalShortcutRecorderView.swift').read_text()
        self.assertIn('_model = StateObject(wrappedValue: Self.f_1001eca94(shortcut))',view)
        self.assertIn('OriginalShortcutRecorder(shortcut: shortcut.wrappedValue)',view)
        self.assertIn('state: model.f_1001f0460()',view)
        self.assertEqual(self.rows['Paste:0x1001f06f8']['status'],'local_contract_consistent')

    def test_rename_wrapper_inherits_only_the_proven_clear_title_difference(self):
        row=self.rows['Paste:0x10006e0dc'];self.assertEqual(row['status'],'difference_confirmed')
        self.assertEqual(row['shared_difference_origin'],'Paste:0x1003bae08')
        native=fragment('0x10006e0dc',row['original']['path'])
        self.assertIn('if (param_3 != 0)',native)
        self.assertIn('FUN_1003bae08(param_1,param_2,param_4)',native)
        callee=fragment('0x1003bae08','decompiled/Paste/part-0294.c')
        self.assertIn('if ((uVar1 == 0) && (IVar4 = objc_stub::title(param_3), IVar4 != 0))',callee)
        self.assertIn('SVar11 = (String)ZEXT816(0)',callee)
        current=(ROOT/'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
        rename=body(current,'func renameItem(_ item: ClipboardItem)')
        self.assertIn('guard let title = prompt',rename)
        self.assertIn('return name.isEmpty ? nil : name',current)

    def test_text_configuration_focus_ring_difference_uses_same_sdk_enum_as_scroller(self):
        row=self.rows['Paste:0x100042fc8'];self.assertEqual(row['status'],'difference_confirmed')
        self.assertIn('objc_stub::setFocusRingType_(unaff_x20,2)',fragment('0x100042fc8',row['original']['path']))
        sdk=json.loads((ROOT/'reports/replica/p0-p1-review-round14-static-proof.json').read_text())['focus_ring_enum']
        header=(ROOT/sdk['path']).read_text()
        self.assertEqual(digest(sdk['path']),sdk['sha256'])
        self.assertIn('NSFocusRingTypeExterior = 2',header);self.assertIn('NSFocusRingTypeNone = 1',header)
        method=body((ROOT/'.local/p0-repair/phase-39/before/replica/Sources/PastoCore/OriginalSearchTextView.swift').read_text(),'public func f_100042fc8()')
        self.assertIn('focusRingType = .none',method)

    def test_history_optional_next_buffering_and_consumption_order_have_real_producers(self):
        next_result=fragment('0x10036e854','decompiled/Paste/part-0278.c')
        self.assertIn('BufferingPolicy_unbounded',next_result)
        self.assertIn('unaff_x22 + 0x100',next_result)
        gate=fragment('0x10036e968','decompiled/Paste/part-0278.c')
        self.assertIn('unaff_x22 + 0x100',gate);self.assertIn('_get_isCancelled',gate)
        current=(ROOT/'replica/Sources/PastoCore/OriginalSearchHistory.swift').read_text()
        self.assertIn('AsyncStream(bufferingPolicy: .unbounded)',current)
        self.assertIn('guard !Task.isCancelled else { break }',current)
        process=body(current,'func process() async')
        self.assertLess(process.index('guard !batch.isEmpty'),process.index('try await consume'))
        self.assertLess(process.index('try await consume'),process.index('token = next'))
        self.assertEqual(self.rows['Paste:0x10037063c']['status'],'unclosed')

    def test_history_clear_repository_dispatch_is_located_but_not_claimed_as_closed(self):
        proof=self.proof['history_clear_witness']
        self.assertEqual(self.pointer(int(proof['parent_slot'],16)),int(proof['child_table'],16))
        self.assertEqual(self.pointer(int(proof['method_slot'],16)),0x100369308)
        support={r['function_id']:r for r in self.rows['Paste:0x100024274']['supporting_original_fragments']}
        self.assertIn('FUN_100369328()',fragment('0x100369308',support['Paste:0x100369308']['path']))
        self.assertEqual(self.rows['Paste:0x100024274']['status'],'unclosed')
        self.assertEqual(self.rows['Paste:0x1003594e4']['status'],'unclosed')
        self.assertEqual(self.rows['Paste:0x100368250']['status'],'unclosed')
        self.assertEqual(self.rows['Paste:0x1002f7c14']['status'],'unclosed')
        native=fragment('0x1002f7c14',self.rows['Paste:0x1002f7c14']['original']['path'])
        self.assertIn('*(undefined1 *)(unaff_x20 + 0x70) = 1',native)
        self.assertIn('*(undefined1 *)(unaff_x20 + 0x70) = 0',native)

    def test_progress_and_unchanged_production_are_independently_recounted(self):
        counts=Counter(r['status'] for r in self.rows.values())
        resolved=sum(counts[s] for s in ['local_contract_consistent','difference_confirmed','user_adaptation_confirmed'])
        self.assertEqual(dict(counts),self.report['outcomes'])
        self.assertEqual(resolved,self.report['resolved_review_records'])
        self.assertEqual(self.report['resolved_comparison_percent'],round(resolved/646*100,2))
        self.assertEqual(self.report['round_delta']['newly_resolved'],resolved-self.prior['resolved_review_records'])
        before=json.loads((ROOT/'.local/p0-review/production-before.json').read_text())
        now={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'replica/Sources').rglob('*') if p.is_file()}
        self.assertEqual(now,before)
        self.assertEqual(digest('replica/function-map.json'),self.report['function_map_sha256'])
        for flag in ['production_source_edited','compiled','application_executed','committed','pushed']:
            self.assertFalse(self.report[flag])


if __name__=='__main__':unittest.main()
