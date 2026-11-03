"""Native capture live-prefix/weak delegate/cleanup contracts; no pasteboard or Swift execution."""
from pathlib import Path
import hashlib,json,re,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from native_drag_handle_scope_contract import pre_native_drag_handle
from capture_lifecycle_scope_contract import CHANGES,pre_capture_lifecycle

class CaptureLifecycleContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-119';cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.proof=json.loads((cls.phase/'capture-lifecycle-contract.json').read_text());cls.path='replica/Sources/PastoCore/Pasteboard.swift';cls.source=(ROOT/cls.path).read_text();cls.capture=body(cls.source,'private func synchronizePasteboard()');cls.before=body((cls.phase/'before'/cls.path).read_text(),'private func synchronizePasteboard()');cls.type_loop=body(cls.capture,'for type in rawItem.types');cls.inner=body(cls.capture,'\n            do ');cls.ns={};exec((ROOT/cls.proof['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.ns)
    def order(self,s,tokens):
        cursor=0
        for t in tokens:cursor=s.index(t,cursor)+len(t)
    def test_seven_original_fragments_and_prior_shared_state_proof_bound(self):
        self.assertEqual(len(self.proof['original_fragments']),7)
        for r in self.proof['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for p,h in self.proof['reused_evidence'].items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),h)
    def test_binary_decoder_and_eighteen_real_calls_bound(self):
        for r in [self.proof['binary'],self.proof['decoder']]:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
        self.assertEqual(len(self.proof['ARM_calls']),18)
        for r in self.proof['ARM_calls']:
            pc=int(r['address'],16);data=self.ns['read'](pc,4);w=int.from_bytes(data,'little');self.assertEqual(data.hex(),r['bytes']);self.assertEqual(w&0xfc000000,0x94000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(pc+d*4,int(r['target'],16))
    def test_thirty_native_field_weak_branch_budget_and_log_words_bound(self):
        self.assertEqual(len(self.proof['ARM_words']),30)
        for r in self.proof['ARM_words']:self.assertEqual(self.ns['read'](int(r['address'],16),4).hex(),r['bytes'])
    def test_original_nil_weak_branch_bypasses_type_filter_then_rejoins_data_read(self):
        pc=0x1003797a0;w=int.from_bytes(self.ns['read'](pc,4),'little');self.assertEqual(w&0xff000000,0xb4000000);self.assertEqual(w&31,0);d=(w>>5)&0x7ffff
        if d&0x40000:d-=0x80000
        self.assertEqual(pc+4*d,0x1003797d4);self.assertGreater(pc+4*d,0x1003797b4);self.assertIn(('0x1003797b4','0x10037c22c'),[(r['address'],r['target'])for r in self.proof['ARM_calls']])
    def test_original_append_and_callback_cleanup_use_same_owner_items_field(self):
        for pc in [0x1003795bc,0x100379d84,0x100379da4]:
            w=int.from_bytes(self.ns['read'](pc,4),'little');self.assertEqual((w>>5)&31,25);self.assertEqual((w>>10)&0xfff,0x28)
        w=int.from_bytes(self.ns['read'](0x100379e80,4),'little');self.assertEqual((w>>5)&31,25);self.assertEqual((w>>12)&0x1ff,0x28);self.assertLess(0x1003795c4,0x100379e68);self.assertLess(0x100379e68,0x100379e80);self.assertLess(0x100379e80,0x100379ed8)
    def test_completion_log_literal_decodes_from_actual_MOVZ_MOVK_words(self):
        value=0
        for pc in [0x100379eac,0x100379eb0,0x100379eb4,0x100379eb8]:
            w=int.from_bytes(self.ns['read'](pc,4),'little');shift=((w>>21)&3)*16;imm=(w>>5)&0xffff
            value=imm<<shift if w&0x7f800000==0x52800000 else (value&~(0xffff<<shift))|(imm<<shift)
        self.assertEqual(value.to_bytes(8,'little'),b'All done')
    def test_types_data_and_count_selectors_decode_from_actual_pointers(self):
        self.assertEqual({r['selector']for r in self.proof['selectors']},{'types','dataForType:','changeCount'})
        for r in self.proof['selectors']:
            a=int(r['pointer'],16);v,c=self.ns['reachable_pointer'](a);self.assertEqual(c,r['chain']);self.assertEqual(self.ns['read'](a,8).hex(),r['pointer_bytes']);t=self.ns['base']+(v&((1<<36)-1));o=self.ns['offset'](t);self.assertEqual(self.ns['raw'][o:self.ns['raw'].index(b'\0',o)].decode(),r['selector'])
    def test_remote_marker_is_in_original_capture_and_existing_policy_preserved(self):
        r=self.proof['remote_literal'];pc=int(r['ADRP_ADD'],16);self.assertEqual(self.ns['read'](pc,12).hex(),r['instruction_bytes']);self.assertEqual(self.ns['read'](int(r['character_address'],16),29),b'com.apple.is-remote-clipboard');self.order(self.type_loop,['permitsRemoteType','if let delegate = captureState.delegate','withExtendedLifetime(delegate)','f_10037c22c','rawItem.data(forType: type)'])
    def test_count_clear_permission_shouldRead_and_ordered_types_prefix_unchanged(self):
        prefix=self.capture[:self.capture.index('            var totalBytes = 0')];old=self.before[:self.before.index('            var totalBytes = 0')];self.assertEqual(prefix,old);self.assertEqual(hashlib.sha256(prefix.encode()).hexdigest(),self.proof['budget_equivalence']['prefix_sha256']);self.order(prefix,['lastChangeCount = pasteboard.changeCount','captureState.items = []','_ = pasteboard.types','permitsBackgroundRead','pasteboard.pasteboardItems','rawItems.flatMap','delegate.originalPasteboardShouldRead(allTypes)'])
    def test_each_type_takes_fresh_weak_delegate_and_holds_it_only_through_policy(self):
        branch=body(self.type_loop,'if let delegate = captureState.delegate');lease=body(branch,'withExtendedLifetime(delegate)');self.assertIn('OriginalPasteboardPolicies.f_10037c22c(type: type.rawValue, allTypes: allTypes)',lease);self.assertIn('guard shouldRead else { continue }',branch);self.assertNotIn('data(forType:',branch);self.assertEqual(self.type_loop.count('f_10037c22c'),1)
    def test_no_delegate_false_policy_counterexample_is_fixed_without_bypassing_remote_gate(self):
        old=body(self.before,'for type in rawItem.types');self.assertIn('guard OriginalPasteboardPolicies.permitsRemoteType',old);self.assertNotIn('captureState.delegate',old)
        self.assertIn('if let delegate = captureState.delegate',self.type_loop)
        cases=[(True,False,False,True),(True,True,False,False),(True,True,True,True),(False,False,False,False),(False,True,True,False)]
        def source_gate(source,remote,live,policy):
            loop=body(source,'for type in rawItem.types')
            calls_policy=live if 'if let delegate = captureState.delegate' in loop else True
            return remote and(not calls_policy or policy)
        for remote,live,policy,expected in cases:
            self.assertEqual(source_gate(self.capture,remote,live,policy),expected)
        self.assertFalse(source_gate(self.before,True,False,False))
        self.assertTrue(source_gate(self.capture,True,False,False))
    def test_live_state_receives_completed_nonempty_items_without_bulk_snapshot(self):
        self.assertIn('if !item.f_10037da6c().isEmpty { captureState.items.append(item) }',self.capture)
        for t in ['var snapshot:','snapshot.append','captureState.items = snapshot']:self.assertNotIn(t,self.capture)
        self.assertLess(self.capture.index('captureState.items.append(item)'),self.capture.index('Pasteboard sync completed'))
    def observed_prefixes(self,source,nonempty):
        dest=re.search(r'if !item\.f_10037da6c\(\)\.isEmpty \{ ([\w.]+)\.append\(item\) \}',source).group(1);visible=[];observed=[]
        for name,accepted in nonempty:
            observed.append(tuple(visible))
            if accepted and dest=='captureState.items':visible.append(name)
        return observed
    def test_subsequent_data_read_observes_completed_prefix_including_empty_item_skip(self):
        items=[('first',True),('empty',False),('third',True)];self.assertEqual(self.observed_prefixes(self.capture,items),[(),('first',),('first',)]);self.assertEqual(self.observed_prefixes(self.before,items),[(),(),()])
    def test_normal_and_nil_delegate_callback_scope_cleans_before_AllDone_log(self):
        self.assertIn('defer { captureState.items = [] }',self.inner);self.order(self.inner,['defer { captureState.items = [] }','Pasteboard sync completed','lastError = nil','if let delegate = captureState.delegate','delegate.originalPasteboardDidRead(captureState)']);self.assertNotIn('All done',self.inner);self.assertLess(self.capture.index(self.inner)+len(self.inner),self.capture.index('recordSynchronization("All done")'));self.assertIn('defer { captureState.items = [] }',self.before)
    def test_swift_throw_cleanup_and_lastError_compatibility_keeps_original_outer_catch(self):
        self.assertIn('try delegate.originalPasteboardDidRead(captureState)',self.inner);self.assertNotIn('catch',self.inner);self.assertEqual(body(self.capture,'\n        } catch '),body(self.before,'\n        } catch '));self.assertIn('lastError = error',body(self.capture,'\n        } catch '));self.assertEqual(self.capture.count('captureState.items = []'),2)
    def test_budget_code_is_exact_reuse_of_checked_accepted_only_accumulation(self):
        first='                    let size = totalBytes.addingReportingOverflow(data.count)';last='                    item.f_10037e6b0(data, forType: type.rawValue)';s=self.capture[self.capture.index(first):self.capture.index(last)+len(last)];old=self.before[self.before.index(first):self.before.index(last)+len(last)];self.assertEqual(s,old);self.assertEqual(hashlib.sha256(s.encode()).hexdigest(),self.proof['budget_equivalence']['sha256']);self.order(s,['addingReportingOverflow','precondition(!size.overflow','guard size.partialValue <= 0x40000000','continue','totalBytes = size.partialValue','item.f_10037e6b0'])
    def test_budget_boundary_and_skipped_oversized_representation_do_not_consume_capacity(self):
        cap=int(re.search(r'guard size.partialValue <= (0x[0-9a-f]+)',self.capture).group(1),16);self.assertEqual(cap,1<<30)
        def accepted(sizes):
            total=0;out=[]
            for n in sizes:
                if total+n<=cap:total+=n;out.append(n)
            return out,total
        self.assertEqual(accepted([cap,1,0]),([cap,0],cap));self.assertEqual(accepted([cap+1,3,cap-3]),([3,cap-3],cap));self.assertEqual(accepted([cap-1,2,1]),([cap-1,1],cap))
        lo=int.from_bytes(self.ns['read'](0x1003798fc,4),'little');hi=int.from_bytes(self.ns['read'](0x100379900,4),'little');threshold=((lo>>5)&0xffff)|(((hi>>5)&0xffff)<<16);self.assertEqual(threshold,cap+1)
    def test_raw_item_type_order_duplicates_and_nil_vs_empty_data_policy_unchanged(self):
        self.assertIn('let allTypes = rawItems.flatMap { $0.types.map(\\.rawValue) }',self.capture);self.order(self.capture,['for rawItem in rawItems','for type in rawItem.types','rawItem.data(forType: type)','captureState.items.append(item)']);self.assertIn('guard let data = rawItem.data(forType: type) else { continue }',self.type_loop)
        for t in ['Set(','sorted(','data.isEmpty','unique']:self.assertNotIn(t,self.capture)
    def test_eleven_shared_methods_and_six_sources_preserved(self):
        self.assertEqual(len(self.proof['unchanged_methods']),11)
        for r in self.proof['unchanged_methods']:self.assertEqual(hashlib.sha256(body((ROOT/r['path']).read_text(),r['symbol']).encode()).hexdigest(),r['sha256'])
        for p,h in {**self.proof['current_sources'],**self.proof['shared_sources']}.items():self.assertEqual(hashlib.sha256(pre_native_drag_handle((ROOT/p).read_text()).encode()).hexdigest(),h)
    def test_one_exact_method_delta_reverses_all247_production_files(self):
        self.assertEqual(len(CHANGES),1)
        for p,h in self.base['production'].items():
            data=(ROOT/p).read_bytes();data=pre_capture_lifecycle(data.decode()).encode()if p.endswith('.swift')else data;self.assertEqual(hashlib.sha256(data).hexdigest(),h)
    def test_reversal_idempotent_and_full_function_runtime_not_falsely_completed(self):
        old=(self.phase/'before'/self.path).read_text();self.assertEqual(pre_capture_lifecycle(self.source),old);self.assertEqual(pre_capture_lifecycle(old),old);self.assertEqual(self.proof['new_difference_records'],0);self.assertFalse(self.proof['full_function_migration_verified']);self.assertFalse(self.proof['runtime_executed']);self.assertEqual(len(self.proof['remaining']),4)

if __name__=='__main__':unittest.main()
