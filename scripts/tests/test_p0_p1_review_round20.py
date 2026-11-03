# -*- coding: utf-8 -*-
"""Static boundary classification and the remaining search contracts; no app execution."""
import hashlib
import json
import struct
import subprocess
import unittest
from collections import Counter

from test_offline_p0_contracts import ROOT, body
from test_p0_p1_review_round2 import digest, fragment


class P0P1ReviewRound20(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((ROOT/'reports/replica/p0-p1-review-round20.json').read_text())
        cls.prior=json.loads((ROOT/'reports/replica/p0-p1-review-round19.json').read_text())
        cls.boundary=json.loads((ROOT/cls.report['boundary_decisions']['path']).read_text())
        cls.old_boundary=json.loads((ROOT/cls.boundary['prior_boundary']['path']).read_text())
        cls.proof=json.loads((ROOT/cls.report['static_proof']['path']).read_text())
        cls.binary=(ROOT/cls.proof['binary_path']).read_bytes()
        cls.rows={x['function_id']:x for x in cls.report['records']}
        cls.index={x['address']:x for x in json.loads((ROOT/'reports/Paste/function-index.json').read_text())}

    def native(self,a): return fragment(a,self.index[a]['file'])
    def offset(self,a):
        seg=next(x for x in self.proof['file_backed_segments']if x['vmaddr']<=a<x['vmaddr']+x['filesize'])
        return seg['fileoff']+a-seg['vmaddr']
    def pointer(self,a): return 0x100000000+(struct.unpack_from('<Q',self.binary,self.offset(a))[0]&((1<<36)-1))
    def relative(self,a): return a+struct.unpack_from('<i',self.binary,self.offset(a))[0]
    def string(self,a):
        o=self.offset(a);end=self.binary.find(b'\0',o,o+512);self.assertGreaterEqual(end,0)
        return self.binary[o:end].decode()
    def branch(self,a,link):
        word=struct.unpack_from('<I',self.binary,self.offset(a))[0]
        self.assertEqual(word&0xfc000000,0x94000000 if link else 0x14000000)
        delta=word&0x3ffffff
        if delta&(1<<25):delta-=1<<26
        return a+delta*4
    def word(self,a):return struct.unpack_from('<I',self.binary,self.offset(a))[0]

    def test_current_scope_and_all_frozen_rows_stay_separate_from_boundary_classification(self):
        old={r['function_id']:r for r in self.prior['records']}
        changed=set(self.report['round_delta']['reviewed_function_ids'])
        self.assertEqual(set(old),set(self.rows));self.assertEqual(len(old),646)
        self.assertEqual(self.report['scope_manifest_sha256'],self.prior['scope_manifest_sha256'])
        self.assertEqual(self.report['round_delta']['scope_added'],0)
        for fid in old:
            if fid in changed:self.assertEqual(old[fid]['status'],'unclosed')
            else:self.assertEqual(old[fid],self.rows[fid])
        self.assertFalse(any(r['full_function_migration_verified']for r in self.rows.values()))
        self.assertIsNone(self.report['full_priority_completion_percent'])

    def test_reclassified_candidates_preserve_every_nonheld_prior_decision_and_do_not_count_as_migration(self):
        old={r['function_id']:r for r in self.old_boundary['records']}
        new={r['function_id']:r for r in self.boundary['records']}
        self.assertEqual(set(old),set(new));self.assertEqual(len(new),239)
        held={fid for fid,r in old.items()if r['admission_decision']=='hold'}
        self.assertEqual(len(held),9);self.assertEqual(set(self.boundary['round_delta']['reviewed_function_ids']),held)
        for fid,r in new.items():
            if fid not in held:self.assertEqual(r,old[fid])
            else:
                self.assertFalse(r['comparison_record']);self.assertFalse(r['full_function_migration_verified'])
                self.assertEqual(r['previous_admission_decision'],'hold')
        self.assertEqual(Counter(r['admission_decision']for r in new.values()),Counter(admit=93,support_only=131,exclude=15))
        self.assertFalse(self.boundary['full_original_priority_classification_complete'])
        self.assertEqual(self.boundary['round_delta']['new_comparison_units'],0)

    def test_exact_static_blocks_and_all_new_original_source_and_sdk_references(self):
        self.assertEqual(hashlib.sha256(self.binary).hexdigest(),self.proof['binary_sha256'])
        for b in self.proof['blocks']:
            actual=self.binary[b['file_offset']:b['file_offset']+b['length']]
            self.assertEqual(actual.hex(),b['bytes']);self.assertEqual(hashlib.sha256(actual).hexdigest(),b['sha256'])
            self.assertEqual(self.offset(int(b['address'],16)),b['file_offset'])
        for path,h in self.report['source_inputs'].items():self.assertEqual(digest(path),h,path)
        records=[self.rows[fid]for fid in self.report['round_delta']['reviewed_function_ids']]
        records += [r for r in self.boundary['records']if r.get('review_round')==20]
        for r in records:
            for ref in [dict(r['original'],function_id=r['function_id'])]+r.get('supporting_original_fragments',[]):
                fid=ref['function_id'];self.assertEqual(hashlib.sha256(fragment(fid.split(':')[1],ref['path']).encode()).hexdigest(),ref['sha256'])
            for ref in r['current_references']:
                self.assertEqual(digest(ref['path']),ref['sha256']);self.assertIn(ref['symbol'],(ROOT/ref['path']).read_text())
            for ref in r.get('supporting_static_evidence',[]):self.assertEqual(digest(ref['path']),ref['sha256'])

    def test_input_view_coder_failure_helper_is_not_destructor_or_text_view_coder_initializer(self):
        self.assertEqual(self.branch(0x1000429a0,True),0x10004493c)
        coder=self.native('0x100042908');failed=self.native('0x10004493c');destroy=self.native('0x100042e60')
        self.assertIn('FUN_10004493c()',coder);self.assertIn('initWithCoder:',coder)
        self.assertIn('Swift::_assertionFailure',failed);self.assertIn('SoftwareBreakpoint',failed)
        self.assertIn('::onClear',failed);self.assertIn('FUN_100004550',destroy)
        self.assertNotIn('_assertionFailure',destroy)
        self.assertIn('"initWithCoder:"',self.native('0x10004430c'))
        self.assertEqual(self.rows['Paste:0x10004430c']['status'],'unclosed')
        current=(ROOT/'replica/Sources/PastoCore/OriginalSearchInputView.swift').read_text()
        self.assertIn('fatalError("init(coder:) has not been implemented")',body(current,'public required init?(coder: NSCoder)'))
        current=(ROOT/'replica/Sources/PastoCore/OriginalSearchTextView.swift').read_text()
        self.assertIn('super.init(coder: coder)',body(current,'public required init?(coder: NSCoder)'))

    def test_excluded_telemetry_registration_is_bound_to_actual_nominal_type_and_module(self):
        d=self.pointer(0x100fb3e58+0x40)
        self.assertEqual(d,0x100ca68e8);self.assertEqual(self.string(self.relative(d+8)),'TelemetryImpl')
        module=self.relative(d+4);self.assertEqual(self.string(self.relative(module+8)),'PasteTelemetry')
        self.assertIn('FUN_10019b6f0',self.native('0x10019b694'))
        self.assertIn('FUN_10019cf88()',self.native('0x10019b6f0'))
        self.assertIn('0x100fb3e58',self.native('0x10019cf88'))
        self.assertIn('(*param_1)(0)',self.native('0x1001e7580'))
        self.assertIn('param_3,0',self.native('0x1001e7580'))
        self.assertIn('FUN_1001e7580(FUN_1001eba28,6,FUN_1001e752c)',self.native('0x1001e7514'))
        self.assertIn('FUN_1001e7580(FUN_1001ec904,0xc,FUN_1001e75e4)',self.native('0x1001e7568'))

    def test_shortcut_forwarders_and_font_color_support_attach_to_existing_consumers(self):
        self.assertEqual(self.branch(0x1001ee744,False),0x1001ee604)
        self.assertEqual(self.branch(0x1001f0674,False),0x1001f0558)
        self.assertIn('FUN_100126a6c(&DAT_100fb63e0,&DAT_1010577c8,FUN_1001feab8)',self.native('0x1001fec18'))
        self.assertIn('_swift_once(param_1,param_3)',self.native('0x100126a6c'))
        self.assertIn('PTR__NSFontTextStyleBody_',self.native('0x1001ff928'))
        self.assertIn('NSFont::preferredFontForTextStyle_options_',self.native('0x1001ff964'))
        current=(ROOT/'replica/Sources/PastoCore/OriginalSearchTextView.swift').read_text()
        self.assertIn('OriginalSearchAppearance.f_1001fec18()!',current);self.assertIn('OriginalSearchAppearance.f_1001ff928()',current)

    def test_string_set_helper_removes_a_bucket_and_returns_optional_member_without_new_identity_claim(self):
        native=self.native('0x100370984')
        self.assertIn('FUN_100007cc4(uVar5)',native)
        self.assertIn('uVar7 = *puVar1;',native);self.assertIn('uVar8 = puVar1[1];',native)
        self.assertIn('uVar7 = 0;',native);self.assertIn('uVar8 = 0;',native)
        self.assertIn('*(long *)(lVar12 + 0x10) + -1',self.native('0x100007cc4'))
        self.assertIn('FUN_100370984(pcVar21,puVar19)',self.native('0x10036fa2c'))
        current=(ROOT/'replica/Sources/PastoCore/OriginalSearchHistory.swift').read_text()
        self.assertIn('updated.remove(identifier)',current);self.assertIn('inserted.remove(identifier)',current)
        self.assertEqual(self.rows['Paste:0x10036fa2c']['status'],'difference_confirmed')

    def test_provider_has_a_real_read_consumer_but_structure_alone_does_not_prove_observable_difference(self):
        self.assertEqual(self.rows['Paste:0x1002e1b54']['status'],'unclosed')
        current=(ROOT/'replica/Sources/Pasto/UI/SearchEditor.swift').read_text()
        update=body(current,'private func updateSuggestions(_ field: SearchField, editor: SearchTextView)')
        self.assertIn('let store = self.parent.store',update)
        start=update.index('let provider = OriginalSearchSuggestions.Provider(');stop=update.index('let entries =')
        self.assertIn('OriginalSearchSuggestions.f_1002df190',update[start:stop]);self.assertNotIn('await ',update[start:stop])
        self.assertEqual(self.rows['Paste:0x1002f7d60']['status'],'unclosed')
        cleanup=body(current,'static func dismantleNSView(_ field: SearchField, coordinator: Coordinator)')
        self.assertIn('dismissSuggestions()',cleanup);self.assertNotIn('f_1002f6550',cleanup)
        self.assertIn('if !preserveHistory { history.f_1002f6550() }',body(current,'func clearInput(preserveHistory: Bool, field: SearchField, editor: SearchTextView)'))

    def test_observable_collection_association_and_conformance_are_not_mistaken_for_sink_output_layout(self):
        protocol=0x100ca7104;conformance=0x100c425d0
        self.assertEqual(self.relative(conformance)-1,0x100ecc168)
        self.assertEqual(self.pointer(0x100ecc168),protocol)
        self.assertEqual(self.string(self.relative(protocol+8)),'ObservableCollection')
        self.assertEqual(self.string(self.relative(protocol+20)),'Element')
        self.assertEqual(struct.unpack_from('<II',self.binary,self.offset(protocol+12)),(1,6))
        self.assertEqual(self.relative(conformance+4),0x100cac7e8)
        self.assertEqual(self.string(self.relative(0x100cac7e8+8)),'SearchResultsCollection')
        self.assertEqual(self.relative(conformance+8),0x100fc0790)
        self.assertEqual(self.pointer(0x100fc0790+0x30),0x100355854)
        self.assertEqual(self.branch(0x100355864,True),0x100355874)
        self.assertEqual(self.proof['observable_collection']['associated_type_names'],['Element'])
        self.assertFalse(self.rows['Paste:0x100223430']['full_function_migration_verified'])

    def test_snapshot_applier_really_produces_initial_and_large_difference_reload_requests(self):
        self.assertEqual(self.branch(0x100067ef0,True),0x1001aeb1c)
        self.assertEqual(self.word(0x100067f0c),0xaa1403e1)
        self.assertEqual(self.branch(0x100067f14,True),0x10022338c)
        self.assertEqual(self.word(0x1001b8e38),0xb9005a7f)  # zero bytes +58..5b
        self.assertEqual(self.word(0x1001b8e2c),0x52802588)  # threshold 300
        self.assertEqual(self.word(0x1001b9ba4),0x39416a88)  # initial byte +5a
        for i in range(4):self.assertEqual(self.word(0x1001b9c74+i*4),0xd2800000+i)
        self.assertEqual(self.word(0x1001b9c84),0xd63f02c0)  # callback x22
        for i in range(4):self.assertEqual(self.word(0x1001b9cec+i*4),0xd2800016+i)
        self.assertEqual(self.branch(0x1001ba0d8,False),0x1001b9f80)
        self.assertEqual(self.branch(0x1002234dc,False),0x100223430)
        self.assertEqual(self.word(0x100223474),0xd63f0340)  # mutate before nil dispatch
        self.assertEqual(self.branch(0x1002234b8,True),0x10022be98)
        self.assertIn('FUN_1001b9db0',self.native('0x1001b9f80'))
        self.assertIn('*(undefined8 *)(param_1 + 0x10) = param_2;',self.native('0x1001b9db0'))
        wrapper=self.native('0x1001b8a94')
        self.assertIn('_swift_task_isCurrentExecutor()',wrapper)
        self.assertIn('(*(code *)param_2)(param_1)',wrapper)
        self.assertNotIn('OS_dispatch_queue::_async',wrapper)
        self.assertIn('OS_dispatch_queue::_async',self.native('0x1001b9214'))

    def test_reload_has_a_real_nonempty_count_and_first_index_state_not_an_empty_result_assumption(self):
        count,capacity,first=struct.unpack_from('<QQQ',self.binary,self.offset(0x100fb7710+16))
        self.assertEqual((count,capacity,first),(1,2,0))
        self.assertEqual(self.word(0x10022c104),0xf9400808)  # static array count
        self.assertEqual(self.word(0x10022c144),0xa9005560)  # array and dataSource count to selection manager
        native=self.native('0x10022be98')
        self.assertIn('(**(code **)(lVar16 + 0x10))()',native)
        self.assertIn('if (IVar12 == 0)',native)
        self.assertIn('objc_stub::setBounds_(IVar12,0,0)',native)
        current=(ROOT/'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
        normalize=body(current,'func normalizeSelection()')
        self.assertIn('selection.contains($0) && visible.contains($0)',normalize)
        self.assertIn('primaryID.flatMap { ids.contains($0) ? $0 : nil }',normalize)
        host=(ROOT/'replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift').read_text()
        self.assertIn('items = state.visibleItems',body(host,'func update(state: ReplicaUIState, cardSide: CGFloat)'))
        # These per-method facts alone do not establish a complete same-event counterexample.
        self.assertFalse(self.rows['Paste:0x10022be98']['full_function_migration_verified'])

    def test_progress_and_frozen_production_ledger_version_head_remain_explicit(self):
        counts=Counter(r['status']for r in self.rows.values());self.assertEqual(dict(counts),self.report['outcomes'])
        self.assertEqual(self.report['resolved_review_records'],646-counts['unclosed'])
        self.assertEqual(self.report['resolved_comparison_percent'],round((646-counts['unclosed'])/646*100,2))
        before=json.loads((ROOT/'.local/p0-review/production-before.json').read_text())
        now={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in (ROOT/'replica/Sources').rglob('*')if p.is_file()}
        self.assertEqual(now,before);self.assertEqual(len(now),218)
        self.assertEqual(digest('replica/function-map.json'),self.report['function_map_sha256'])
        self.assertEqual(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),self.report['head_revision'])
        for flag in ['production_source_edited','function_map_modified','compiled','application_executed','network_used','committed','pushed']:
            self.assertFalse(self.report[flag])


if __name__=='__main__':unittest.main()
