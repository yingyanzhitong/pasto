from shared_pasteboard_state_scope_contract import pre_shared_pasteboard_state
"""Source-bound copy transaction ordering/failure traces; no app/framework execution."""
from pathlib import Path
import hashlib,itertools,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from native_drag_handle_scope_contract import pre_native_drag_handle
from test_p0_repair_checksum_routing import original_fragment
from postwrite_restore_scope_contract import CHANGES,pre_postwrite_restore

class PostwriteRestoreContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-117';cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.proof=json.loads((cls.phase/'postwrite-transaction-contract.json').read_text());cls.path='replica/Sources/PastoCore/Pasteboard.swift';cls.src=pre_shared_pasteboard_state((ROOT/cls.path).read_text());cls.writer=body(cls.src,'private func finishPasteboardWrite(');cls.ns={};exec((ROOT/cls.proof['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.ns)
    def order(self,s,tokens):
        cursor=0
        for t in tokens:cursor=s.index(t,cursor)+len(t)
    def test_eight_original_fragments_and_two_prior_proofs_current(self):
        self.assertEqual(len(self.proof['original_fragments']),8)
        for r in self.proof['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for p,h in self.proof['reused_evidence'].items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),h)
    def test_binary_and_decoder_current(self):
        for r in [self.proof['binary'],self.proof['decoder']]:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_ten_actual_BLs_bind_writer_count_transaction_error_and_cleanup(self):
        self.assertEqual(len(self.proof['ARM_calls']),10)
        for r in self.proof['ARM_calls']:
            pc=int(r['address'],16);data=self.ns['read'](pc,4);w=int.from_bytes(data,'little');self.assertEqual(data.hex(),r['bytes']);self.assertEqual(w&0xfc000000,0x94000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(pc+d*4,int(r['target'],16))
    def test_three_real_selectors_are_defaults_setter_Undo_and_process_notification(self):
        self.assertEqual({r['selector']for r in self.proof['selectors']},{'setInteger:forKey:','removeAllActions','postNotificationName:object:'})
        for r in self.proof['selectors']:
            a=int(r['pointer'],16);v,c=self.ns['reachable_pointer'](a);self.assertEqual(c,r['chain']);self.assertEqual(self.ns['read'](a,8).hex(),r['pointer_bytes']);t=self.ns['base']+(v&((1<<36)-1));o=self.ns['offset'](t);self.assertEqual(self.ns['raw'][o:self.ns['raw'].index(b'\0',o)].decode(),r['selector'])
    def test_original_success_and_error_paths_converge_before_Undo(self):
        self.assertEqual(len(self.proof['ARM_words']),6)
        for r in self.proof['ARM_words']:self.assertEqual(self.ns['read'](int(r['address'],16),4).hex(),r['bytes'])
        pc=0x10037a5b0;w=int.from_bytes(self.ns['read'](pc,4),'little');self.assertEqual(w&0xff000000,0xb4000000);self.assertEqual(w&31,21);d=(w>>5)&0x7ffff
        if d&0x40000:d-=0x80000
        self.assertEqual(pc+4*d,0x10037a5bc);calls=self.proof['ARM_calls'];self.assertIn(('0x10037a5b8','0x100bfc708'),[(r['address'],r['target'])for r in calls]);self.assertLess(0x10037a5b8,0x10037a5d0)
    def test_callback_ADRP_ADD_passes_original_input_to_postwrite_transaction(self):
        a=0x10037a59c;w=int.from_bytes(self.ns['read'](a,4),'little');v=int.from_bytes(self.ns['read'](a+4,4),'little');imm=((w>>5)&0x7ffff)*4+((w>>29)&3)
        if imm&(1<<20):imm-=1<<21
        self.assertEqual((a&~4095)+(imm<<12)+((v>>10)&0xfff),0x10037b620)
        pcs=[int(r['address'],16)for r in self.proof['ARM_calls'][:8]];self.assertEqual(pcs,sorted(pcs))
    def test_prewrite37aa3c_is_writer_lazy_cache_not_history_transaction(self):
        r=next(r for r in self.proof['original_fragments']if r['address']=='0x10037aa3c');s=original_fragment((ROOT/r['path']).read_text(),'10037aa3c');self.assertIn('integerForKey_',s);self.assertIn('FUN_100378664',s)
        for t in ['FUN_1002ff310','performAndWait','FUN_10037ade4']:self.assertNotIn(t,s)
    def test_actual_writer_order_is_markers_write_count_then_caught_prepare_record(self):
        self.order(self.writer,['first.f_10037d8c8(Data(), forType: generatedType.rawValue)','let writer = OriginalPasteboardWriter','writer.f_10037875c(objects)','state.persistChangeCount?(state.lastChangeCount)','do {','let restoration = try prepareRestoration()','try recordRestoredSelection(restoration)','} catch {','removeAllActions()','NotificationCenter.default.post(','didRestoreItem.send()'])
    def test_preparation_and_record_errors_share_same_empty_catch_domain(self):
        caught=body(self.writer,'\n        do ');self.assertIn('let restoration = try prepareRestoration()',caught);self.assertIn('try recordRestoredSelection(restoration)',caught);self.assertLess(caught.index('prepareRestoration'),caught.index('recordRestoredSelection'));self.assertNotIn('writer.f_10037875c',caught);self.assertFalse(''.join(l.split('//',1)[0]for l in body(self.writer,'catch ').strip('{}\n ').splitlines()).strip());self.assertEqual(self.writer.count('prepareRestoration()'),1)
    def trace(self,source,fail=None):
        mapping={'write':'writer.f_10037875c(objects)','count':'state.persistChangeCount?(state.lastChangeCount)','prepare':'let restoration = try prepareRestoration()','record':'try recordRestoredSelection(restoration)','undo':'removeAllActions()','notify':'NotificationCenter.default.post(','legacyNotify':'didRestoreItem.send()'}
        actions=sorted((source.index(token),name)for name,token in mapping.items());do_start=source.index('do {');catch_start=source.index('} catch {');trace=[];failed=False
        for pos,name in actions:
            inside=do_start<pos<catch_start
            if failed and inside:continue
            trace.append(name)
            if name==fail:
                if inside:failed=True;trace.append('caught')
                else:trace.append('propagated');break
        return trace
    def test_success_trace_reaches_prepare_only_after_actual_write_and_count(self):
        self.assertEqual(self.trace(self.writer),['write','count','prepare','record','undo','notify','legacyNotify'])
    def test_preparation_failure_copies_content_skips_record_but_cleans_and_notifies(self):
        self.assertEqual(self.trace(self.writer,'prepare'),['write','count','prepare','caught','undo','notify','legacyNotify'])
    def test_record_or_save_failure_still_cleans_and_notifies_after_copy(self):
        self.assertEqual(self.trace(self.writer,'record'),['write','count','prepare','record','caught','undo','notify','legacyNotify'])
    def test_before_snapshot_reproduces_preparation_error_blocking_copy_and_Undo(self):
        old=body((self.phase/'before'/self.path).read_text(),'private func finishPasteboardWrite(');self.assertEqual(self.trace(old,'prepare'),['prepare','propagated']);self.assertNotEqual(self.trace(old,'prepare'),self.trace(self.writer,'prepare'))
    def test_same_input_facades_preprocessing_and_ten_actual_methods_unchanged(self):
        self.assertEqual(len(self.proof['unchanged_methods']),10)
        for r in self.proof['unchanged_methods']:self.assertEqual(hashlib.sha256(body(pre_native_drag_handle((ROOT/r['path']).read_text()),r['symbol']).encode()).hexdigest(),r['sha256'])
        native=body(self.src,'public func writeToPasteboard(restoreItems:');self.assertIn('try prepareHistoryRestore(restoreItems)',native);legacy=body(self.src,'private func writeToPasteboard(ids:');self.assertIn('try prepareHistoryRestore(selected)',legacy)
    def test_copy_consumer_still_hides_only_after_writer_returns_and_copied_callback(self):
        s=body((ROOT/'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text(),'private func performCopy(');self.order(s,['state.perform','try write()','copiedItemsHandler?()','hidePanel()']);self.assertNotIn('asyncAfter',s)
    def test_empty_representation_output_still_writes_and_no_async_wait_is_added(self):
        self.assertNotIn('guard !objects.isEmpty',self.writer);self.assertNotIn('return',self.writer)
        for t in ['Task {','DispatchQueue','asyncAfter','sleep','Timer.']:self.assertNotIn(t,self.writer)
    def test_only_preparation_statement_relocation_reconstructs_previous_method(self):
        old=body((self.phase/'before'/self.path).read_text(),'private func finishPasteboardWrite(');new=self.writer.replace('            let restoration = try prepareRestoration()\n','',1).replace('        let writer = OriginalPasteboardWriter','        let restoration = try prepareRestoration()\n        let writer = OriginalPasteboardWriter',1);self.assertEqual(new,old)
    def test_exact_one_hunk_reversal_preserves_all247_production_sources_and_six_shared_sources(self):
        self.assertEqual(len(CHANGES),1)
        for p,h in self.base['production'].items():
            data=(ROOT/p).read_bytes();data=pre_postwrite_restore(data.decode()).encode()if p.endswith('.swift')else data;self.assertEqual(hashlib.sha256(data).hexdigest(),h)
        for p,h in {**self.proof['current_sources'],**self.proof['shared_sources']}.items():self.assertEqual(hashlib.sha256(pre_shared_pasteboard_state((ROOT/p).read_text()).encode()).hexdigest(),h)
    def test_no_new_count_or_full_runtime_claim_and_reverse_idempotence(self):
        old=(self.phase/'before'/self.path).read_text();self.assertEqual(pre_postwrite_restore(self.src),old);self.assertEqual(pre_postwrite_restore(old),old);self.assertEqual(self.proof['new_difference_records'],0);self.assertFalse(self.proof['full_function_migration_verified']);self.assertFalse(self.proof['runtime_executed']);self.assertEqual(len(self.proof['remaining']),4)

if __name__=='__main__':unittest.main()
