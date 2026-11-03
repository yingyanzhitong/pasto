# -*- coding: utf-8 -*-
"""Installed AppKit static dispatch, bounded normal consumers, and unchanged production."""
import hashlib
import json
import mmap
import struct
import subprocess
import unittest
from collections import Counter
from contextlib import ExitStack

from test_offline_p0_contracts import ROOT, body
from test_p0_p1_review_round2 import digest, fragment


class P0P1ReviewRound19(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((ROOT/'reports/replica/p0-p1-review-round19.json').read_text())
        cls.prior=json.loads((ROOT/'reports/replica/p0-p1-review-round18.json').read_text())
        cls.rows={x['function_id']:x for x in cls.report['records']}
        cls.proof=json.loads((ROOT/cls.report['static_proof']['path']).read_text())
        cls.appkit=json.loads((ROOT/cls.proof['installed_appkit']['path']).read_text())
        cls.index={x['address']:x for x in json.loads((ROOT/'reports/Paste/function-index.json').read_text())}
        cls.stack=ExitStack();cls.cache=[]
        for info in cls.appkit['cache_files']:
            f=cls.stack.enter_context(open(info['path'],'rb'))
            cls.cache.append(cls.stack.enter_context(mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)))
        cls.addClassCleanup(cls.stack.close)

    def native(self,a):return fragment(a,self.index[a]['file'])
    def cache_data(self,a,n):
        m=next(m for m in self.appkit['mappings']if m['vmaddr']<=a<m['vmaddr']+m['size'])
        o=m['fileoff']+a-m['vmaddr'];return self.cache[m['cache']][o:o+n]
    def word(self,a):return struct.unpack('<I',self.cache_data(a,4))[0]
    def qword(self,a):return struct.unpack('<Q',self.cache_data(a,8))[0]
    def pointer(self,a):return 0x180000000+(self.qword(a)&0xffffffff)
    def relative(self,a):return a+struct.unpack('<i',self.cache_data(a,4))[0]
    def cache_string(self,a):
        value=self.cache_data(a,512);stop=value.find(b'\0');self.assertGreaterEqual(stop,0)
        return value[:stop].decode()
    def branch(self,a,link=True):
        v=self.word(a);self.assertEqual(v&0xfc000000,0x94000000 if link else 0x14000000)
        imm=v&0x3ffffff;return a+(imm-(1<<26)if imm&(1<<25)else imm)*4
    def adrp(self,a):
        v=self.word(a);self.assertEqual(v&0x9f000000,0x90000000)
        imm=(((v>>5)&0x7ffff)<<2)|((v>>29)&3)
        if imm&(1<<20):imm-=1<<21
        return (a&~4095)+(imm<<12)

    def test_fixed_646_scope_only_11_previous_unknowns_revisited_and_no_full_migration_upgrade(self):
        old={x['function_id']:x for x in self.prior['records']};changed=set(self.report['round_delta']['reviewed_function_ids'])
        self.assertEqual(set(old),set(self.rows));self.assertEqual(len(self.rows),646)
        self.assertEqual(len(changed),11);self.assertEqual(self.report['round_delta']['scope_added'],0)
        self.assertEqual(self.report['scope_manifest_sha256'],self.prior['scope_manifest_sha256'])
        for fid in old:
            if fid in changed:self.assertEqual(old[fid]['status'],'unclosed')
            else:self.assertEqual(self.rows[fid],old[fid])
        self.assertEqual(self.report['round_delta']['newly_resolved'],5)
        self.assertFalse(any(x['full_function_migration_verified']for x in self.rows.values()))
        self.assertIsNone(self.report['full_priority_completion_percent'])

    def test_original_supporting_fragments_current_literals_and_static_inputs_remain_bound(self):
        for p,h in self.report['source_inputs'].items():self.assertEqual(digest(p),h,p)
        self.assertEqual(digest(self.report['static_proof']['path']),self.report['static_proof']['sha256'])
        self.assertEqual(digest(self.proof['installed_appkit']['path']),self.proof['installed_appkit']['sha256'])
        for fid in self.report['round_delta']['reviewed_function_ids']:
            row=self.rows[fid]
            for ref in [dict(row['original'],function_id=fid)]+row.get('supporting_original_fragments',[]):
                a=ref.get('address')or ref['function_id'].split(':')[1]
                self.assertEqual(hashlib.sha256(fragment(a,ref['path']).encode()).hexdigest(),ref['sha256'])
            for ref in row['current_references']:
                self.assertEqual(digest(ref['path']),ref['sha256']);self.assertIn(ref['symbol'],(ROOT/ref['path']).read_text())
            for ref in row.get('supporting_static_evidence',[]):self.assertEqual(digest(ref['path']),ref['sha256'])

    def test_installed_cache_uuid_mappings_and_every_selected_block_are_checked_without_loading_appkit(self):
        for i,info in enumerate(self.appkit['cache_files']):
            cache=self.cache[i];self.assertEqual(cache[:16],b'dyld_v1  arm64e\0')
            self.assertEqual(cache[88:104].hex(),info['uuid']);self.assertEqual(len(cache),info['size'])
            o,n=struct.unpack_from('<II',cache,16)
            actual=[struct.unpack_from('<QQQII',cache,o+j*32)[:3]for j in range(n)]
            expected=[(m['vmaddr'],m['size'],m['fileoff'])for m in self.appkit['mappings']if m['cache']==i]
            self.assertEqual(actual,expected)
        for block in self.appkit['blocks']:
            value=self.cache[block['cache']][block['file_offset']:block['file_offset']+block['length']]
            self.assertEqual(value.hex(),block['bytes'])
            self.assertEqual(hashlib.sha256(value).hexdigest(),block['sha256'])
            self.assertEqual(self.cache_data(int(block['address'],16),block['length']),value)
        self.assertEqual(self.appkit['system_version']['version'],'26.2')
        self.assertEqual(self.appkit['system_version']['build'],'25C56')
        self.assertIn('selected exact blocks only',self.appkit['cache_files'][0]['hash_scope'])

    def test_actual_nstextview_class_and_all_19_method_lists_have_one_selected_initializer_each(self):
        slot=int(self.appkit['class_slot'],16);cls=self.pointer(slot);ro=self.pointer(cls+32)&~7
        self.assertEqual(cls,int(self.appkit['class_address'],16));self.assertEqual(ro,int(self.appkit['class_ro'],16))
        self.assertEqual(self.cache_string(self.pointer(ro+24)),'NSTextView')
        array=self.pointer(ro+32)&~3;size,count=struct.unpack('<II',self.cache_data(array,8))
        self.assertEqual(size,8);self.assertEqual(count,19)
        selected={x['name']:x for x in self.appkit['selected_methods']}
        self.assertEqual(len(selected),5)
        targets={int(x['selector'],16):x['name']for x in selected.values()};found=Counter()
        base=int(self.appkit['selector_string_base'],16)
        for i in range(count):
            entry=array+8+i*size;raw=self.qword(entry);delta=raw>>16
            if delta&(1<<47):delta-=1<<48
            methods=entry+delta;flags,n=struct.unpack('<II',self.cache_data(methods,8))
            self.assertEqual(flags,0xc000000f)
            for j in range(n):
                a=methods+8+j*12;selector=base+self.word(a)
                if selector not in targets:continue
                name=targets[selector];found[name]+=1;record=selected[name]
                self.assertEqual(a,int(record['entry'],16));self.assertEqual(self.cache_string(selector),name)
                self.assertEqual(self.relative(a+8),int(record['imp'],16))
                self.assertEqual(self.cache_string(self.relative(a+4)),record['types'])
        self.assertEqual(found,Counter({name:1 for name in selected}))

    def test_dynamic_using_layout_manager_calls_private_frame_then_frame_text_container_with_self_receiver(self):
        self.assertEqual(self.branch(0x18551f934,link=False),0x185fbf3e0)
        self.assertEqual(self.branch(0x18551f834),0x186038900)
        self.assertEqual(self.word(0x18551f73c),0xaa0003f3)  # save self x0 in x19
        self.assertEqual(self.word(0x18551f81c),0xaa1303e0)  # self back in x0, not objc_super
        self.assertEqual(self.word(0x18551f830),0xaa1403e2)  # container x20 to argument x2
        expected=['_initWithFrame:usingTextLayoutManager:','initWithFrame:textContainer:']
        for info,name in zip(self.appkit['selector_stubs'],expected):
            stub=int(info['stub'],16);ldr=self.word(stub+4)
            self.assertEqual(ldr&31,1)
            slot=self.adrp(stub)+((ldr>>10)&4095)*8
            self.assertEqual(slot,int(info['slot'],16));self.assertEqual(self.cache_string(self.pointer(slot)),name)
            runtime_slot=self.adrp(stub+8)+((self.word(stub+12)>>10)&4095)
            self.assertEqual(runtime_slot,0x1ee9ad298)
            self.assertEqual(self.pointer(runtime_slot),0x18008d800)
            self.assertEqual(self.word(stub+16),0xf9400230);self.assertEqual(self.word(stub+20),0xd71f0a11)

    def test_runtime_export_trie_proves_objc_msgsend_target_is_separate_from_super2(self):
        proof=self.appkit['objc_runtime_exports'];trie=self.cache_data(int(proof['export_vmaddr'],16),proof['export_size'])
        def uleb(p):
            value=shift=0
            while True:
                ch=trie[p];p+=1;value|=(ch&127)<<shift
                if ch<128:return value,p
                shift+=7
        def lookup(name):
            node=0;rest=name.encode()
            while True:
                size,p=uleb(node);terminal=p
                if not rest:
                    self.assertGreater(size,0);flags,p=uleb(terminal);address,_=uleb(p)
                    self.assertEqual(flags,0);return int(proof['image'],16)+address
                p=terminal+size;n=trie[p];p+=1;target=None
                for _ in range(n):
                    end=trie.index(b'\0',p);edge=trie[p:end];child,p=uleb(end+1)
                    if rest.startswith(edge):target=(child,rest[len(edge):])
                self.assertIsNotNone(target);node,rest=target
        self.assertEqual(lookup('_objc_msgSend'),0x18008d800)
        self.assertEqual(lookup('_objc_msgSendSuper2'),0x18008da20)
        self.assertNotEqual(lookup('_objc_msgSend'),lookup('_objc_msgSendSuper2'))

    def test_frame_initializer_source_defaults_and_real_using_constructor_match_but_coder_remains_unknown(self):
        native=self.native('0x100044aec')
        self.assertIn('TextView::canAcceptFocus)',native);self.assertIn('= 1;',native)
        self.assertIn('___lazy_storage___placeholderLabel) = 0',native)
        self.assertIn('"initWithFrame:textContainer:"',native)
        self.assertIn('objc_stub::initUsingTextLayoutManager_(self,1)',self.native('0x100041f9c'))
        current=(ROOT/'replica/Sources/PastoCore/OriginalSearchTextView.swift').read_text()
        for value in ['public var canAcceptFocus = true','.foregroundColor: OriginalSearchAppearance.f_1001fec18()!','.font: OriginalSearchAppearance.f_1001ff928()','private var storedPlaceholder: NSTextField?']:
            self.assertIn(value,current)
        init=body(current,'public override init(frame frameRect: NSRect, textContainer container: NSTextContainer?)')
        self.assertIn('super.init(frame: frameRect, textContainer: container)',init)
        self.assertIn('OriginalSearchTextView(usingTextLayoutManager: true)',(ROOT/'replica/Sources/PastoCore/OriginalSearchInputView.swift').read_text())
        self.assertEqual(self.rows['Paste:0x100044aec']['status'],'local_contract_consistent')
        self.assertEqual(self.rows['Paste:0x10004430c']['status'],'unclosed')
        self.assertIn('other_OS_cache_versions',self.rows['Paste:0x100044aec']['coverage_boundaries']['not_verified'])

    def test_normal_context_reuse_and_canonical_history_consumers_do_not_claim_factory_side_effects_complete(self):
        native=self.native('0x1003594e4');self.assertIn('if (local_a0 == 0)',native)
        self.assertIn('(*param_4)(auStack_b8,auStack_78)',native)
        current=(ROOT/'replica/Sources/PastoCore/ClipboardStore.swift').read_text()
        self.assertIn('private let persistence: ClipboardPersistence',current)
        self.assertIn('persistence = try Self.withLock(directoryURL: directoryURL) { try ClipboardPersistence(directoryURL: directoryURL) }',current)
        self.assertIn('try persistence.commit(state, previous: remote)',current)
        restore=body(current,'func recordRestoredItems(_ ids: [UUID]) throws')
        self.assertIn('state.items[index].isInHistory = true',restore)
        self.assertIn('state.items[index].createdAt = timestamp',restore)
        self.assertIn('boardButton(state.store.preferences.historyTitle, board: nil)',(ROOT/'replica/Sources/Pasto/UI/PanelViews.swift').read_text())
        for fid in ['Paste:0x1003594e4','Paste:0x100368250']:
            self.assertEqual(self.rows[fid]['status'],'local_contract_consistent');self.assertFalse(self.rows[fid]['full_function_migration_verified'])
        row=self.rows['Paste:0x100368250'];self.assertTrue(any('permanentID' in x for x in row['coverage_boundaries']['not_verified']))
        self.assertTrue(any('单位' in x for x in row['coverage_boundaries']['not_verified']))

    def test_empty_candidate_menu_terminal_path_is_only_after_live_context_and_no_cancellation(self):
        native=self.native('0x100041190')
        self.assertIn('if ((bVar5) || (lVar19 = *(long *)(lVar21 + 0x10), lVar19 == 0))',native)
        self.assertIn('objc_stub::removeChildWindow_(self,IVar12)',native)
        self.assertIn('objc_stub::orderOut_(IVar12,0)',native)
        editor=(ROOT/'replica/Sources/Pasto/UI/SearchEditor.swift').read_text()
        update=body(editor,'private func updateSuggestions(_ field: SearchField, editor: SearchTextView)')
        self.assertIn('guard !entries.isEmpty, let manager = editor.textLayoutManager else',update)
        chain=update[update.index('let candidates ='):update.index('menu.show(')];self.assertNotIn('await ',chain)
        cleanup=body(editor,'func dismissSuggestions()');self.assertIn('suggestionMenu?.dismiss()',cleanup)
        self.assertIn('suggestionMenu = nil',cleanup)
        menu=(ROOT/'replica/Sources/Pasto/UI/ReplicaSearchSuggestionsMenu.swift').read_text()
        cleanup=body(menu,'func dismiss()');self.assertIn('removeChildWindow(self)',cleanup);self.assertIn('orderOut(nil)',cleanup)
        for fid in ['Paste:0x1000403f4','Paste:0x100041190']:
            self.assertEqual(self.rows[fid]['status'],'local_contract_consistent')
            self.assertIn('原建议数组与当前candidates均为空',self.rows[fid]['contract'])
        for fid in ['Paste:0x1002e1b54','Paste:0x1002f7d60']:
            self.assertEqual(self.rows[fid]['status'],'unclosed')

    def test_progress_and_frozen_production_ledger_head_and_exactly_seven_unknowns(self):
        counts=Counter(x['status']for x in self.rows.values());self.assertEqual(dict(counts),self.report['outcomes'])
        self.assertEqual(646-counts['unclosed'],639)
        self.assertEqual(self.report['resolved_comparison_percent'],round(639/646*100,2))
        self.assertEqual(self.report['p0_component']['resolved'],265)
        self.assertEqual(self.report['p1_additional_component']['unclosed'],7)
        before=json.loads((ROOT/'.local/p0-review/production-before.json').read_text())
        now={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in (ROOT/'replica/Sources').rglob('*')if p.is_file()}
        self.assertEqual(now,before);self.assertEqual(len(now),218)
        self.assertEqual(digest('replica/function-map.json'),self.report['function_map_sha256'])
        self.assertEqual(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'050e6878a5a52f96fe33aa40f48bb8a056cd0f05')
        for flag in ['production_source_edited','compiled','application_executed','committed','pushed']:self.assertFalse(self.report[flag])


if __name__=='__main__':unittest.main()
