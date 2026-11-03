# -*- coding: utf-8 -*-
"""Source-bound snapshot counterexample and original static producer/consumer evidence.

No application, SDK framework, or original executable is loaded or executed.
"""
import hashlib
import json
import struct
import subprocess
import unittest
from collections import Counter
from pathlib import Path

from macho_imports import _chained_bindings, parse_macho
from test_offline_p0_contracts import ROOT, body
from test_p0_p1_review_round2 import digest, fragment


class P0P1ReviewRound21(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((ROOT/'reports/replica/p0-p1-review-round21.json').read_text())
        cls.prior=json.loads((ROOT/'reports/replica/p0-p1-review-round20.json').read_text())
        cls.proof=json.loads((ROOT/cls.report['static_proof']['path']).read_text())
        cls.rows={r['function_id']:r for r in cls.report['records']}
        cls.binary=(ROOT/cls.proof['binary_path']).read_bytes()
        cls.index={r['address']:r for r in json.loads((ROOT/'reports/Paste/function-index.json').read_text())}

    def offset(self,a):
        s=next(s for s in self.proof['file_backed_segments']if s['vmaddr']<=a<s['vmaddr']+s['filesize'])
        return s['fileoff']+a-s['vmaddr']
    def word(self,a):return struct.unpack_from('<I',self.binary,self.offset(a))[0]
    def pointer(self,a):return 0x100000000+(struct.unpack_from('<Q',self.binary,self.offset(a))[0]&((1<<36)-1))
    def relative(self,a):return a+struct.unpack_from('<i',self.binary,self.offset(a))[0]
    def string(self,a):
        p=self.offset(a);end=self.binary.find(b'\0',p,p+512);self.assertGreaterEqual(end,0)
        return self.binary[p:end].decode()
    def branch(self,a,link=True):
        v=self.word(a);self.assertEqual(v&0xfc000000,0x94000000 if link else 0x14000000)
        imm=v&0x3ffffff
        if imm&(1<<25):imm-=1<<26
        return a+imm*4
    def native(self,a):return fragment(a,self.index[a]['file'])

    def test_six_previous_unknowns_revisited_with_scope_and_every_other_row_preserved(self):
        old={r['function_id']:r for r in self.prior['records']};changed=set(self.report['round_delta']['reviewed_function_ids'])
        self.assertEqual(set(old),set(self.rows));self.assertEqual(len(self.rows),646)
        self.assertEqual(len(changed),6);self.assertEqual(self.report['round_delta']['scope_added'],0)
        for fid in old:
            if fid in changed:self.assertEqual(old[fid]['status'],'unclosed')
            else:self.assertEqual(old[fid],self.rows[fid])
        self.assertEqual(self.report['scope_manifest_sha256'],self.prior['scope_manifest_sha256'])
        self.assertFalse(any(r['full_function_migration_verified']for r in self.rows.values()))
        self.assertIsNone(self.report['full_priority_completion_percent'])

    def test_all_new_fragments_current_references_and_static_inputs_are_bound_to_current_bytes(self):
        for p,h in self.report['source_inputs'].items():self.assertEqual(digest(p),h,p)
        self.assertEqual(digest(self.report['static_proof']['path']),self.report['static_proof']['sha256'])
        for fid in self.report['round_delta']['reviewed_function_ids']:
            r=self.rows[fid]
            for ref in [dict(r['original'],function_id=fid)]+r.get('supporting_original_fragments',[]):
                self.assertEqual(hashlib.sha256(fragment(ref['function_id'].split(':')[1],ref['path']).encode()).hexdigest(),ref['sha256'])
            for ref in r['current_references']:
                self.assertEqual(digest(ref['path']),ref['sha256']);self.assertIn(ref['symbol'],(ROOT/ref['path']).read_text())
            for ref in r.get('supporting_static_evidence',[]):self.assertEqual(digest(ref['path']),ref['sha256'])

    def test_every_new_selected_machine_block_is_exact_and_uses_macho_segment_file_mapping(self):
        self.assertEqual(hashlib.sha256(self.binary).hexdigest(),self.proof['binary_sha256'])
        for r in self.proof['blocks']:
            self.assertEqual(self.offset(int(r['address'],16)),r['file_offset'])
            data=self.binary[r['file_offset']:r['file_offset']+r['length']]
            self.assertEqual(data.hex(),r['bytes']);self.assertEqual(hashlib.sha256(data).hexdigest(),r['sha256'])

    def test_difference_sdk_calls_are_real_imports_and_not_decompiler_display_names(self):
        actual=parse_macho(ROOT/self.proof['binary_path'])['stubs']
        for r in self.proof['sdk_stubs']:self.assertEqual(actual[r['address']],r)
        for site,target,part in [(0x1001b5d00,0x100bf79f8,'difference4from'),(0x1001b5d1c,0x100bf9df8,'inferringMoves'),(0x1001b5d5c,0x100bf9de0,'removals'),(0x1001b5ea4,0x100bf9dc8,'insertions')]:
            self.assertEqual(self.branch(site),target);self.assertIn(part,actual[hex(target)]['symbol'])
        self.assertEqual(self.word(0x1001b5ce0),0xd10203a0)  # old array address fp-80
        self.assertEqual(self.word(0x1001b5ce4),0xd10283b4)  # receiver new array address fp-a0

    def test_insert_remove_move_destinations_and_return_slots_resolve_four_payloads(self):
        for setup,instruction,site,target in [(0x1001b5e60,0xd10183b4,0x1001b5e68,0x1001b0218),(0x1001b5fac,0xd101a3b4,0x1001b5fb8,0x1001b0218),(0x1001b5e70,0xd101c3b4,0x1001b5e7c,0x1001b02ec)]:
            self.assertEqual(self.word(setup),instruction);self.assertEqual(self.branch(site),target)
        self.assertEqual(self.word(0x1001b602c),0xf85a03b6)  # x22 = removal set fp-60
        self.assertEqual(self.word(0x1001b6030),0xf85903a2)  # x2 = moves fp-70
        self.assertEqual(self.word(0x1001b62b4),0xf85983a1)  # x1 = insertion set fp-68
        self.assertEqual(self.word(0x1001b62b8),0xaa1603e0)  # x0 = x22
        self.assertEqual([r['register']for r in self.proof['diff_outputs']],['x0','x1','x2','x3'])
        self.assertIn('Swift::Hasher::_combine',self.native('0x1001b02ec'))
        self.assertIn('*param_1 = param_2',self.native('0x1001b0218'))

    def test_301_genuinely_new_ids_force_threshold_without_assuming_a_minimal_difference_algorithm(self):
        case=self.proof['synthetic_case'];old=case['old_ids'];new=case['new_ids']
        self.assertEqual(old,['old']);self.assertEqual(len(new),302)
        self.assertEqual(new[-1],old[0]);self.assertNotEqual(new[0],case['prior_selected_id'])
        self.assertEqual(len(set(new)),len(new));fresh=set(new)-set(old)
        self.assertEqual(len(fresh),301)
        # New elements absent from the old collection cannot become associated moves.
        self.assertTrue(fresh.isdisjoint(old));self.assertGreater(len(fresh),300)
        insertion_offsets={i for i,value in enumerate(new)if value in fresh}
        self.assertEqual(len(insertion_offsets),301)
        self.assertEqual(self.word(0x1001b9cc4),0xeb1c011f)  # compare threshold with first-three count sum
        self.assertEqual(self.word(0x1001b9cc8),0x540001aa)  # >= retains payloads; strict > clears
        for i in range(4):self.assertEqual(self.word(0x1001b9cec+i*4),0xd2800016+i)
        self.assertEqual(case['kind'],'source_bound_symbolic_snapshot_case_not_binary_execution')

    def test_actual_data_source_is_self_and_count_reads_the_already_mutated_applier_items(self):
        cls=self.pointer(0x100f45600);self.assertEqual(cls,0x100f91308)
        ro=self.pointer(cls+32)&~7;self.assertEqual(self.string(self.pointer(ro+24)),'_TtC5Paste18ItemCollectionView')
        self.assertEqual(self.pointer(cls+0xe0),0x10022a6d0)
        self.assertEqual(self.word(0x100067458),0xf9407117)  # virtual setter +e0
        self.assertEqual(self.word(0x10006746c),0x911c2021)  # witness 0xeb2708 pageoff
        self.assertEqual(self.word(0x100067470),0xaa1503e0)  # self x21 as dataSource
        self.assertEqual(self.pointer(0x100eb2708),0x100c26c58)
        self.assertEqual(self.pointer(self.relative(0x100c26c58)-1),0x100ca8c94)
        self.assertEqual(self.string(self.relative(0x100ca8c94+8)),'CollectionViewDataSource')
        self.assertEqual(self.pointer(0x100eb2708+16),0x10006e188)
        self.assertIn('::applier',self.native('0x10006e188'))
        self.assertIn('*(undefined **)(lVar5 + 0x10)',self.native('0x10006e188'))
        self.assertIn('*(undefined8 *)(param_1 + 0x10) = param_2',self.native('0x1001b9db0'))

    def test_reload_selects_first_and_later_callbacks_are_bounded_without_handoff_or_neighbor_override(self):
        self.assertEqual(struct.unpack_from('<QQQ',self.binary,self.offset(0x100fb7710+16)),(1,2,0))
        self.assertIn('FUN_1000684f8()',self.native('0x1000765b8'))
        callback=self.native('0x1000684f8')
        self.assertIn('FUN_10006d620()',callback);self.assertIn('FUN_10006753c()',callback)
        self.assertIn('::pendingNeighborSelectionID',callback)
        self.assertIn('if (lVar8 == 0)',callback);self.assertIn('return 0;',callback)
        handoff=self.native('0x10006753c')
        self.assertIn('if (uVar18 >> 0x3e == 0) {\n    return;',handoff)
        badges=self.native('0x10006d620');self.assertNotIn('FUN_100228c78',badges)
        self.assertNotIn('cellSelectionManager',badges)

    def test_reload_tail_keeps_existing_nonnil_selection_manager_and_only_applies_cell_appearance(self):
        for ref in self.proof['reload_tail_review']['fragments']:
            source=fragment(ref['function_id'].split(':')[1],ref['path'])
            self.assertEqual(hashlib.sha256(source.encode()).hexdigest(),ref['sha256'])
            if ref['function_id']!='Paste:0x10022b1cc':
                self.assertNotIn('cellSelectionManager',source)
                self.assertNotIn('FUN_100228c78',source)
        getter=self.native('0x10022b1cc')
        self.assertIn('if (puVar3 == (undefined *)0x0)',getter)
        self.assertIn('_swift_bridgeObjectRetain()',getter)
        cell=self.native('0x100221610');self.assertIn('FUN_10022b1cc()',cell)
        self.assertIn('(**(code **)(lVar2 + 0x10))(lVar13 != 0,IVar8,lVar2)',cell)

    def test_current_snapshot_route_keeps_valid_previous_selection_in_the_same_symbolic_case(self):
        current=(ROOT/'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
        normalize=body(current,'func normalizeSelection()')
        self.assertIn('selection.contains($0) && visible.contains($0)',normalize)
        self.assertIn('primaryID.flatMap { ids.contains($0) ? $0 : nil }',normalize)
        self.assertIn('self?.normalizeSelection()',current[current.index('searchIndex.onUpdate ='):current.index('var searchQueryNodes:')])
        self.assertIn('selection = Set(ids)',body(current,'private func applyOrderedSelection(_ ids: [UUID], anchor: UUID?, primary: UUID?)'))
        host=(ROOT/'replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift').read_text()
        update=body(host,'func update(state: ReplicaUIState, cardSide: CGFloat)')
        self.assertIn('items = state.visibleItems',update);self.assertNotIn('applyOrderedSelection',update)
        case=self.proof['synthetic_case'];new=case['new_ids'];chosen=case['prior_selected_id']
        current_ids=[chosen]if chosen in new else [new[0]]
        original_ids=[new[0]]
        self.assertEqual(current_ids,['old']);self.assertNotEqual(current_ids,original_ids)

    def test_reload_difference_propagates_one_origin_and_leaves_incremental_contract_unknown(self):
        for fid in ['Paste:0x100223430','Paste:0x10022be98']:
            self.assertEqual(self.rows[fid]['status'],'difference_confirmed')
            self.assertEqual(self.rows[fid]['difference_origin'],'Paste:0x10022be98')
            self.assertFalse(self.rows[fid]['full_function_migration_verified'])
        self.assertEqual(self.rows['Paste:0x100223430']['shared_difference_origin'],'Paste:0x10022be98')
        self.assertEqual(self.rows['Paste:0x1002234e0']['status'],'unclosed')

    def test_source_setter_direct_calls_allow_repeated_setup_and_normal_live_source_use_only(self):
        scan=self.proof['direct_call_scan'];found={a:[]for a in scan['calls']}
        section=scan['section']
        for a in range(section['address'],section['address']+section['size'],4):
            v=self.word(a)
            if v&0xfc000000!=0x94000000:continue
            imm=v&0x3ffffff
            if imm&(1<<25):imm-=1<<26
            dest=hex(a+imm*4)
            if dest in found:found[dest].append(hex(a))
        self.assertEqual(found,scan['calls'])
        self.assertEqual(found['0x1002e1b54'],['0x10007d330'])
        self.assertEqual(len(found['0x10008e1dc']),3)
        self.assertIn('FUN_1002e1b54(&local_b0)',self.native('0x10007d0e0'))
        row=self.rows['Paste:0x1002e1b54'];self.assertEqual(row['status'],'local_contract_consistent')
        self.assertIn('不支持‘整个进程只安装一次’',row['evidence_note'])
        editor=(ROOT/'replica/Sources/Pasto/UI/SearchEditor.swift').read_text()
        update=body(editor,'private func updateSuggestions(_ field: SearchField, editor: SearchTextView)')
        self.assertIn('let store = self.parent.store',update)
        start=update.index('let provider =');stop=update.index('let entries =')
        self.assertNotIn('await ',update[start:stop]);self.assertIn('OriginalSearchSuggestions.f_1002df190',update[start:stop])

    def test_actual_text_category_uses_uikit_text_selector_but_does_not_prove_the_swift_entry_is_called(self):
        c=self.proof['text_category'];category=int(c['category'],16)
        self.assertEqual(self.pointer(int(c['list_entry'],16)),category)
        self.assertEqual(self.string(self.pointer(category)),'PastePlatform')
        self.assertEqual(self.pointer(category+16),0x100c117d8)
        self.assertEqual((self.word(0x100c117d8),self.word(0x100c117dc)),(0x8000000c,4))
        names=[]
        for r in c['methods']:
            entry=int(r['entry'],16);slot=self.relative(entry)
            name=self.string(self.pointer(slot));names.append(name)
            self.assertEqual(name,r['name']);self.assertEqual(hex(self.relative(entry+8)),r['imp'])
            self.assertEqual(self.string(self.relative(entry+4)),r['types'])
        self.assertEqual(names,['attributedText','setAttributedText:','text','setText:'])
        self.assertEqual(c['methods'][-1]['imp'],'0x1000f72a4')
        self.assertIn('objc_stub::setString_(param_1,param_3)',self.native('0x1000f72a4'))
        self.assertEqual(self.rows['Paste:0x1000f733c']['status'],'unclosed')

    def test_category_class_is_bound_by_dyld_chain_to_nstextview(self):
        data=self.binary;cursor=32;segments=[];dylibs=[];chained=None
        for _ in range(struct.unpack_from('<I',data,16)[0]):
            cmd,size=struct.unpack_from('<II',data,cursor)
            if cmd==0x19:
                addr,mem,off,length=struct.unpack_from('<QQQQ',data,cursor+24)
                segments.append(dict(address=addr,memory_size=mem,offset=off,file_size=length))
            elif cmd in (0xC,0x80000018,0x8000001F,0x20,0x80000023):
                name,_,current,compat=struct.unpack_from('<IIII',data,cursor+8)
                end=data.index(b'\0',cursor+name,cursor+size)
                dylibs.append(dict(install_name=data[cursor+name:end].decode(),load_command=hex(cmd),current_version=current,compatibility_version=compat))
            elif cmd==0x80000034:chained=struct.unpack_from('<II',data,cursor+8)
            cursor+=size
        bindings,_=_chained_bindings(data,chained,segments,dylibs)
        actual=bindings[0x100f4f330]
        self.assertEqual(actual,self.proof['text_category']['class_binding'])
        self.assertEqual(actual['symbol'],'_OBJC_CLASS_$_NSTextView')

    def test_progress_and_frozen_source_ledger_head_and_four_remaining_unknowns(self):
        counts=Counter(r['status']for r in self.rows.values());self.assertEqual(dict(counts),self.report['outcomes'])
        self.assertEqual(counts,Counter(local_contract_consistent=491,difference_confirmed=142,user_adaptation_confirmed=9,unclosed=4))
        self.assertEqual(self.report['resolved_review_records'],642);self.assertEqual(self.report['resolved_comparison_percent'],round(642/646*100,2))
        self.assertEqual({fid for fid,r in self.rows.items()if r['status']=='unclosed'},{'Paste:0x10004430c','Paste:0x1000f733c','Paste:0x1002234e0','Paste:0x1002f7d60'})
        before=json.loads((ROOT/'.local/p0-review/production-before.json').read_text())
        now={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in (ROOT/'replica/Sources').rglob('*')if p.is_file()}
        self.assertEqual(before,now);self.assertEqual(len(now),218)
        self.assertEqual(digest('replica/function-map.json'),self.report['function_map_sha256'])
        self.assertEqual(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),self.report['head_revision'])
        for flag in ['production_source_edited','function_map_modified','compiled','application_executed','network_used','committed','pushed']:self.assertFalse(self.report[flag])


if __name__=='__main__':unittest.main()
