"""Read-only image rotation entry audit; no source repair or runtime tests."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from native_group_write_scope_contract import pre_native_group_write_bytes
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment

class ImageRotationRouteContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-104';cls.proof=json.loads((cls.phase/'image-rotation-route-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.image=(ROOT/'replica/Sources/Pasto/UI/ReplicaImagePreviewContent.swift').read_text();ns={};exec((ROOT/cls.proof['decoder']['path']).read_text().split("idx={r['address']",1)[0],ns);cls.ns=ns
    def original(self,a):
        r=next(r for r in self.proof['original_fragments']if r['address']==a);return original_fragment((ROOT/r['path']).read_text(),a[2:])
    def order(self,s,tokens):
        cursor=0
        for t in tokens:cursor=s.index(t,cursor)+len(t)
    def test_twenty_two_original_fragments_binary_decoder_and_current_methods_bound(self):
        self.assertEqual(len(self.proof['original_fragments']),22)
        for r in self.proof['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for r in [self.proof['binary'],self.proof['decoder']]:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
        self.assertEqual(len(self.proof['current_methods']),6)
        for r in self.proof['current_methods']:self.assertEqual(hashlib.sha256(body((ROOT/r['path']).read_text(),r['symbol']).encode()).hexdigest(),r['sha256'])
    def test_fifteen_actual_branch_calls_bind_separate_toolbar_and_generic_routes(self):
        self.assertEqual(len(self.proof['ARM_calls']),15)
        for r in self.proof['ARM_calls']:
            pc=int(r['address'],16);b=self.ns['read'](pc,4);self.assertEqual(b.hex(),r['bytes']);w=int.from_bytes(b,'little');self.assertEqual(w&0x7c000000,0x14000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(pc+4*d,int(r['target'],16))
    def test_toolbar_actual_function_arguments_resolve_to_step_handlers(self):
        rows=self.proof['toolbar_callback_pointers'];self.assertEqual([r['target']for r in rows],['0x1003e51b4','0x1003e53a0'])
        for r in rows:
            pc=int(r['address'],16);b=self.ns['read'](pc,8);self.assertEqual(b.hex(),r['bytes']);w,a=struct.unpack('<II',b);imm=((w>>5)&0x7ffff)*4+((w>>29)&3)
            if imm&(1<<20):imm-=1<<21
            self.assertEqual((pc&~4095)+(imm<<12)+((a>>10)&0xfff),int(r['target'],16));self.assertEqual(w&31,1);self.assertEqual(a&31,1)
        weak=self.original('0x10007abf4');self.order(weak,['_swift_unknownObjectWeakLoadStrong','if (param_1 != 0)','(*param_2)()'])
        attach=self.original('0x1003e50c8');self.assertIn('FUN_1003e75e4',attach);self.assertIn('FUN_1003e7604',attach)
    def test_async_descriptors_are_actual_relative_pointers_not_assumed_direct_calls(self):
        rows=self.proof['async_relative_descriptors'];self.assertEqual(len(rows),2)
        for r in rows:
            a=int(r['address'],16);b=self.ns['read'](a,8);self.assertEqual(b.hex(),r['bytes']);d,size=struct.unpack('<iI',b);self.assertEqual(a+d,int(r['target'],16));self.assertEqual(size,r['context_size'])
        self.assertIn('FUN_1003e5ef4',self.original('0x1003e77a0'))
    def test_actual_duration_instruction_immediates_decode_to_four_hundred_ms(self):
        value=0
        for r in self.proof['duration_words']:
            b=self.ns['read'](int(r['address'],16),4);self.assertEqual(b.hex(),r['bytes']);w=int.from_bytes(b,'little');self.assertEqual(w&31,8);opcode=w&0xff800000;shift=((w>>21)&3)*16;imm=((w>>5)&0xffff)<<shift
            if opcode==0xd2800000:value=imm
            else:self.assertEqual(opcode,0xf2800000);value=(value&~(0xffff<<shift))|imm
        self.assertEqual(value,400000000000000000);self.assertEqual(value//10**15,400);self.assertEqual(value,self.proof['duration_attoseconds'])
    def test_complete_call_inventory_distinguishes_toolbar_and_delayed_task_entry(self):
        self.assertEqual(len(self.proof['direct_call_inventories']),5)
        inventories={}
        for row in self.proof['direct_call_inventories']:
            actual=[]
            for pc in range(int(row['function'],16),int(row['end'],16),4):
                b=self.ns['read'](pc,4);w=int.from_bytes(b,'little')
                if w&0xfc000000!=0x94000000:continue
                d=w&0x3ffffff
                if d&0x2000000:d-=0x4000000
                actual.append(dict(address=hex(pc),bytes=b.hex(),target=hex(pc+4*d)))
            self.assertEqual(actual,row['calls']);inventories[row['function']]={r['target']for r in actual}
        for a in ['0x1003e51b4','0x1003e53a0']:self.assertNotIn('0x1003e6364',inventories[a]);self.assertNotIn('pendingCommitTask',self.original(a))
        self.assertIn('0x1003e6364',inventories['0x1003e4a54'])
    def test_existing_toolbar_steps_canvas_and_inverse_undo_are_reusable(self):
        right=body(self.image,'private func rotateRight()');left=body(self.image,'private func rotateLeft()');self.order(right,['quarterTurns + 1','next > 3 ? 0 : next','rotateDisplayedImage(degrees: -90)','editingUndoManager.registerUndo','self?.rotateLeft()']);self.order(left,['quarterTurns - 1','next < 0 ? 3 : next','rotateDisplayedImage(degrees: 90)','editingUndoManager.registerUndo','self?.rotateRight()'])
        canvas=body(self.image,'private func rotateDisplayedImage(');self.order(canvas,['zoomView.f_100240a18()','Self.f_100207054','zoomView.f_100240a64(rotated)','updateMetadataAndCommitState()'])
        for s in [right,left,canvas]:self.assertNotIn('Task',s);self.assertNotIn('sleep',s)
    def test_valid_default_quarter_turn_domain_wraps_and_inverse_restores_all_states(self):
        for q in range(4):
            right=0 if q+1>3 else q+1;left=3 if q-1<0 else q-1
            self.assertEqual(right,(q+1)%4);self.assertEqual(left,(q-1)%4);self.assertEqual((right-1)%4,q);self.assertEqual((left+1)%4,q)
        self.assertIn('lVar3 = lVar8 + 1',self.original('0x1003e51b4'));self.assertIn('lVar3 = lVar8 + -1',self.original('0x1003e53a0'))
    def test_generic_rotation_has_distinct_adapter_task_replace_and_inverse_entry(self):
        self.assertIn('FUN_1003e4a54(param_2)',self.original('0x1003df818'))
        s=self.original('0x1003e4a54');self.order(s,['FUN_100240a64','FUN_1003e597c','pendingCommitTask','Swift::Task::cancel','FUN_1003e6364','objc_stub::undoManager'])
        undo=self.original('0x1003e65c0');self.assertIn('FUN_1003e4a54(-param_3)',undo)
    def test_sleep_success_error_both_check_cancellation_before_same_continuation(self):
        for a in ['0x1003e60a8','0x1003e6108']:
            s=self.original(a);self.order(s,['_get_isCancelled','if (bVar1)','return;','FUN_1003e6178'])
        complete=self.original('0x1003e6038');self.assertIn('FUN_1003e60a8',complete);self.assertIn('FUN_1003e6108',complete)
    def test_delayed_callback_checks_weak_owner_and_reads_current_canvas_while_deinit_only_releases(self):
        s=self.original('0x1003e61e0');self.order(s,['_swift_unknownObjectWeakLoadStrong','if (lVar6 != 0)','pendingCommitTask) = 0','ZoomableImageView::image','FUN_1003bde74','FUN_1003bed20'])
        dtor=self.original('0x1003e6754');self.assertIn('pendingCommitTask',dtor);self.assertNotIn('Task::cancel',dtor)
        for a in ['0x1003e5cf0','0x1003e5dd4']:self.assertNotIn('pendingCommitTask',self.original(a))
    def test_no_production_changes_or_false_full_migration_and_gap_is_retained(self):
        files={str(p.relative_to(ROOT))for p in(ROOT/'replica/Sources').rglob('*')if p.is_file()};self.assertEqual(files,set(self.base['production']))
        for p,h in self.base['production'].items():self.assertEqual(hashlib.sha256(pre_native_group_write_bytes(ROOT/p)).hexdigest(),h)
        self.assertTrue(self.proof['production_unchanged']);self.assertEqual(self.proof['new_difference_records'],0);self.assertFalse(self.proof['full_function_migration_verified']);self.assertFalse(self.proof['runtime_executed'])
        self.assertEqual(len(self.proof['finite_comparison']),2)
        for t in ['Generic rotation','UndoManager ownership','error','04430c']:self.assertTrue(any(t in s for s in self.proof['remaining']),t)
