# -*- coding: utf-8 -*-
"""Static incremental-selection and clear-history counterexamples, without app execution."""
import hashlib
import json
import struct
import subprocess
import unittest
from collections import Counter

from macho_imports import _chained_bindings
from test_offline_p0_contracts import ROOT, body
from test_p0_p1_review_round2 import digest, fragment


class P0P1ReviewRound22(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((ROOT/'reports/replica/p0-p1-review-round22.json').read_text())
        cls.prior=json.loads((ROOT/'reports/replica/p0-p1-review-round21.json').read_text())
        cls.proof=json.loads((ROOT/cls.report['static_proof']['path']).read_text())
        cls.rows={r['function_id']:r for r in cls.report['records']}
        cls.binary=(ROOT/cls.proof['binary_path']).read_bytes()
        cls.index={r['address']:r for r in json.loads((ROOT/'reports/Paste/function-index.json').read_text())}

    def offset(self,a):
        s=next(s for s in self.proof['file_backed_segments']if s['vmaddr']<=a<s['vmaddr']+s['filesize'])
        return s['fileoff']+a-s['vmaddr']
    def word(self,a):return struct.unpack_from('<I',self.binary,self.offset(a))[0]
    def pointer(self,a):return 0x100000000+(struct.unpack_from('<Q',self.binary,self.offset(a))[0]&((1<<36)-1))
    def branch(self,a):
        v=self.word(a);self.assertEqual(v&0xfc000000,0x94000000)
        imm=v&0x3ffffff
        if imm&(1<<25):imm-=1<<26
        return a+imm*4
    def native(self,a):return fragment(a,self.index[a]['file'])

    def test_fixed_scope_three_unknowns_revisited_and_others_preserved(self):
        old={r['function_id']:r for r in self.prior['records']};changed=set(self.report['round_delta']['reviewed_function_ids'])
        self.assertEqual(set(old),set(self.rows));self.assertEqual(len(self.rows),646);self.assertEqual(len(changed),3)
        self.assertEqual(self.report['scope_manifest_sha256'],self.prior['scope_manifest_sha256'])
        for fid in old:
            if fid in changed:self.assertEqual(old[fid]['status'],'unclosed')
            else:self.assertEqual(old[fid],self.rows[fid])
        self.assertFalse(any(r['full_function_migration_verified']for r in self.rows.values()))
        self.assertIsNone(self.report['full_priority_completion_percent'])

    def test_all_new_original_current_and_static_inputs_keep_exact_provenance(self):
        for p,h in self.report['source_inputs'].items():self.assertEqual(digest(p),h,p)
        for fid in self.report['round_delta']['reviewed_function_ids']:
            r=self.rows[fid]
            for ref in [dict(r['original'],function_id=fid)]+r.get('supporting_original_fragments',[]):
                self.assertEqual(hashlib.sha256(fragment(ref['function_id'].split(':')[1],ref['path']).encode()).hexdigest(),ref['sha256'])
            for ref in r['current_references']:
                self.assertEqual(digest(ref['path']),ref['sha256']);self.assertIn(ref['symbol'],(ROOT/ref['path']).read_text())
            for ref in r.get('supporting_static_evidence',[]):self.assertEqual(digest(ref['path']),ref['sha256'])

    def test_every_new_machine_block_is_checked_with_file_mapping_and_digest(self):
        self.assertEqual(hashlib.sha256(self.binary).hexdigest(),self.proof['binary_sha256'])
        for b in self.proof['blocks']:
            self.assertEqual(self.offset(int(b['address'],16)),b['file_offset'])
            data=self.binary[b['file_offset']:b['file_offset']+b['length']]
            self.assertEqual(data.hex(),b['bytes']);self.assertEqual(hashlib.sha256(data).hexdigest(),b['sha256'])

    def test_selected_offset_seeds_flow_through_removal_before_filtering(self):
        seed=self.native('0x1002258ac')
        self.assertIn('puVar2[uVar1 * 0x18 + 0x20] = 0',seed)
        self.assertIn('FUN_1001b2a0c(param_2,param_3,param_4,param_5,puVar2)',seed)
        pipeline=self.native('0x1001b2a0c')
        steps=['FUN_1001b2a90','FUN_1001b2cc0','FUN_1001b2fe4','FUN_1001b3404']
        self.assertEqual(sorted(steps,key=pipeline.index),steps)
        removed=self.native('0x1001b2a90')
        self.assertIn('uVar13 = 1;',removed);self.assertIn('puVar9[uVar6 * 0x18 + 0x20] = uVar13',removed)
        self.assertIn('puVar12[uVar3 * 0x18 + 0x20] = uVar4',self.native('0x1001b2cc0'))
        self.assertIn('cVar12 = cVar3;',self.native('0x1001b3404'))

    def test_removed_kind_is_dropped_and_final_empty_array_is_not_replaced_with_first_index(self):
        self.assertEqual(self.word(0x100224008),0x71000b1f)
        self.assertEqual(self.word(0x100224010),0x7100071f)
        filtered=self.native('0x100223f2c')
        self.assertIn("(cVar4 == '\\x02') || (cVar4 == '\\x01')",filtered)
        self.assertEqual(self.branch(0x100223740),0x1002258ac)
        self.assertEqual(self.branch(0x100223758),0x100223f2c)
        self.assertEqual(self.word(0x100223790),0x52800029)  # empty flag true
        self.assertEqual(self.word(0x1002237a4),0xa9002174)  # transformed indexes + count
        self.assertEqual(self.word(0x1002237ac),0x39006169)  # write empty flag
        self.assertEqual(self.branch(0x1002237b8),0x100228f6c)
        self.assertNotIn('FUN_100228c78',self.native('0x100228f6c'))

    def test_deleted_selected_item_counterexample_uses_default_current_fallback(self):
        case=self.proof['symbolic_counterexamples'][0]
        self.assertEqual(case['old_ids'],['A','B','C']);self.assertEqual(case['new_ids'],['A','C'])
        self.assertEqual(case['removed_offsets'],[1]);self.assertEqual(case['inserted_offsets'],[])
        selected_offsets=[case['old_ids'].index(x)for x in case['selected_old_ids']]
        transformed=[(1 if i in case['removed_offsets']else 0,i,i-sum(r<i for r in case['removed_offsets']))for i in selected_offsets]
        original=[new for kind,old,new in transformed if kind not in (1,2)and 0<=new<len(case['new_ids'])]
        retained=[x for x in case['selected_old_ids']if x in case['new_ids']]
        current=retained or [case['new_ids'][0]]
        self.assertEqual(original,case['expected_original_selected_offsets'])
        self.assertEqual(current,case['expected_current_selected_ids'])
        source=(ROOT/'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
        normalize=body(source,'func normalizeSelection()')
        self.assertIn('if ids.isEmpty, !allowsEmptySelection, let first = items.first { ids = [first.id] }',normalize)
        self.assertIn('var allowsEmptySelection = false',source)

    def test_query_singleton_initializer_loads_empty_storage_instead_of_owner_query(self):
        self.assertEqual(self.word(0x1002ddf50),0xf9406d08)  # load GOT +d8
        self.assertEqual(self.word(0x1002ddf58),0xf9048d28)  # store to global +918
        self.assertIn('DAT_101057918 = PTR___swiftEmptyArrayStorage',self.native('0x1002ddf4c'))
        reset=self.native('0x1002f7d60')
        self.assertIn('FUN_1002f7744(DAT_101057918,0)',reset)
        self.assertEqual(self.branch(0x1002f7d90),0x1002f7744)
        self.assertEqual(self.word(0x1002f7d94),0x36000093)  # mode0 continues to reset
        self.assertEqual(self.branch(0x1002f7dac),0x1002f6550)
        self.assertIn('empty',self.proof['historical_global_correction']['value'].lower())

    def test_clear_callback_selects_mode1_and_query_update_still_records_history(self):
        self.assertIn('FUN_100040c64()',self.native('0x100041bf0'))
        self.assertEqual(self.word(0x100040ca0),0x52800020)
        self.assertEqual(self.branch(0x100040ca4),0x1002f7d60)
        self.assertEqual(self.word(0x1002f7868),0x52800023)  # immediate true
        self.assertEqual(self.branch(0x1002f786c),0x1002f5e18)
        history=self.native('0x1002f5e18')
        self.assertIn('FUN_1002f5fe8()',history)
        self.assertIn('*(ulong *)(uVar6 + 0x10) = uVar2 + 1',history)
        self.assertIn('unaff_x20 + 0x18',history)  # redo may be cleared by recording

    def test_current_same_clear_button_flag_reaches_explicit_undo_reset(self):
        field=(ROOT/'replica/Sources/PastoCore/OriginalSearchField.swift').read_text()
        self.assertIn('input.onClear = { [weak self] in self?.f_100045e54() }',field)
        self.assertIn('public func f_100045e54() { onClear?(false) }',field)
        editor=(ROOT/'replica/Sources/Pasto/UI/SearchEditor.swift').read_text()
        self.assertIn('coordinator.clearInput(preserveHistory: preserveHistory, field: field, editor: editor)',editor)
        clear=body(editor,'func clearInput(preserveHistory: Bool, field: SearchField, editor: SearchTextView)')
        self.assertIn('if !preserveHistory { history.f_1002f6550() }',clear)
        current=(ROOT/'replica/Sources/PastoCore/OriginalSearchInputHistory.swift').read_text()
        reset=body(current,'public func f_1002f6550()')
        self.assertIn('undo.removeAll()',reset);self.assertIn('redo.removeAll()',reset)
        case=self.proof['symbolic_counterexamples'][1]
        native_undo=case['undo_before']+[case['query_before']]
        current_undo=[]
        self.assertIn(case['expected_original_undo_contains'],native_undo)
        self.assertEqual(current_undo,case['expected_current_undo'])

    def test_real_dyld_bindings_match_empty_array_storage_and_objc_msgsend(self):
        data=self.binary;cursor=32;segments=[];dylibs=[];chained=None
        for _ in range(struct.unpack_from('<I',data,16)[0]):
            cmd,size=struct.unpack_from('<II',data,cursor)
            if cmd==0x19:
                a,z,o,n=struct.unpack_from('<QQQQ',data,cursor+24)
                segments.append(dict(address=a,memory_size=z,offset=o,file_size=n))
            elif cmd in (0xC,0x80000018,0x8000001F,0x20,0x80000023):
                name,_,current,compat=struct.unpack_from('<IIII',data,cursor+8);end=data.index(b'\0',cursor+name,cursor+size)
                dylibs.append(dict(install_name=data[cursor+name:end].decode(),load_command=hex(cmd),current_version=current,compatibility_version=compat))
            elif cmd==0x80000034:chained=struct.unpack_from('<II',data,cursor+8)
            cursor+=size
        bindings,_=_chained_bindings(data,chained,segments,dylibs)
        for a in [0x100eae0d8,0x100ea81a8]:self.assertEqual(bindings[a],self.proof['selected_bindings'][hex(a)])
        self.assertEqual(bindings[0x100eae0d8]['symbol'],'__swiftEmptyArrayStorage')
        self.assertEqual(bindings[0x100ea81a8]['symbol'],'_objc_msgSend')

    def test_link_editor_actual_nstextview_message_does_not_upgrade_unreferenced_swift_setter(self):
        self.assertIn('_OBJC_CLASS___NSTextView',self.native('0x1003e836c'))
        self.assertIn('objc_stub::setText_((ID)self,pNVar4)',self.native('0x1003e944c'))
        self.assertEqual(self.branch(0x1003e9530),0x100c0e0e0)
        self.assertEqual(self.word(0x100c0e0e4),0xf9422021)
        p=self.pointer(0x100f8a440);o=self.offset(p);self.assertEqual(self.binary[o:o+9],b'setText:\0')
        self.assertEqual(self.rows['Paste:0x1000f733c']['status'],'unclosed')
        self.assertEqual(self.rows['Paste:0x10004430c']['status'],'unclosed')

    def test_progress_and_frozen_production_ledger_head_leave_two_unknowns(self):
        counts=Counter(r['status']for r in self.rows.values());self.assertEqual(dict(counts),self.report['outcomes'])
        self.assertEqual(counts,Counter(local_contract_consistent=491,difference_confirmed=144,user_adaptation_confirmed=9,unclosed=2))
        self.assertEqual(self.report['resolved_review_records'],644);self.assertEqual(self.report['resolved_comparison_percent'],round(644/646*100,2))
        self.assertEqual({fid for fid,r in self.rows.items()if r['status']=='unclosed'},{'Paste:0x10004430c','Paste:0x1000f733c'})
        before=json.loads((ROOT/'.local/p0-review/production-before.json').read_text())
        now={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in (ROOT/'replica/Sources').rglob('*')if p.is_file()}
        self.assertEqual(before,now);self.assertEqual(len(now),218)
        self.assertEqual(digest('replica/function-map.json'),self.report['function_map_sha256'])
        self.assertEqual(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),self.report['head_revision'])
        for flag in ['production_source_edited','function_map_modified','compiled','application_executed','network_used','committed','pushed']:self.assertFalse(self.report[flag])


if __name__=='__main__':unittest.main()
