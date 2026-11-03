"""Positive publisher-consumer scope evidence; no speculative keyboard wiring."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment
from native_link_creation_scope_contract import pre_native_link_creation_bytes
class TopmostConsumerScopeContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-138';cls.p=json.loads((cls.phase/'topmost-consumer-scope-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
    def original(self,a):
        r=next(r for r in self.p['original_fragments']if r['address']==a);return original_fragment((ROOT/r['path']).read_text(),a[2:])
    def test_twelve_original_fragments_binary_and_decoder_hash_bound(self):
        self.assertEqual(len(self.p['original_fragments']),12)
        for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for k in ['binary','decoder']:
            r=self.p[k];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_topmost_projected_publisher_enters_real_combine_pipeline(self):
        s=self.original('0x1000b0b20')
        for t in ['ItemPreviewWindowManager::_topmost','Published::_get_projectedValue','Publisher::_combineLatest','Publisher::_compactMap','Publisher::_removeDuplicates','Publisher::_sink']:self.assertIn(t,s)
        self.assertIn('FUN_1000b0b20()',self.original('0x1000b098c'));self.assertIn('::handoffSnapshotBuilder',self.original('0x1000b098c'))
    def test_eleven_ARM_words_and_sink_callback_ADRP_ADD_real_target(self):
        for r in self.p['ARM_words']:self.assertEqual(self.n['read'](int(r['address'],16),4).hex(),r['bytes'])
        r=self.p['sink_callback'];pc=int(r['ADRP'],16);w=int.from_bytes(self.n['read'](pc,4),'little');imm=((w>>29)&3)|(((w>>5)&0x7ffff)<<2)
        if imm&(1<<20):imm-=1<<21
        page=(pc&~0xfff)+(imm<<12);a=int.from_bytes(self.n['read'](int(r['ADD'],16),4),'little');target=page+(((a>>10)&0xfff)<<(12 if(a>>22)&1 else 0));self.assertEqual(target,int(r['target'],16))
    def test_callback_positive_source_file_and_handoff_activity_update_chain(self):
        self.assertIn('FUN_1000b1c94()',self.original('0x1000b26ac'));s=self.original('0x1000b1c94');self.assertIn('Paste/AppDelegate+Handoff.swift',s);self.assertIn('FUN_100af2cd0(&local_70)',s);self.assertIn('objc_stub::setUserInfo_',self.original('0x100af2cd0'))
    def test_sink_receiver_is_actual_NSUserActivity_import_not_name_guess(self):
        r=self.p['class_bind'];v,c=self.n['reachable_pointer'](int(r['address'],16));self.assertEqual(hex(v),r['raw']);self.assertEqual(c,r['chain']);f=self.n['fixup'][0];h=struct.unpack_from('<7I',self.n['raw'],f);self.assertEqual(h[5],1);w=struct.unpack_from('<I',self.n['raw'],f+h[2]+4*(v&0xffffff))[0];a=f+h[3]+(w>>9);self.assertEqual(self.n['raw'][a:self.n['raw'].index(b'\0',a)].decode(),'_OBJC_CLASS_$_NSUserActivity')
        self.assertIn('*(ID *)(unaff_x20 + 0x70) = self',self.original('0x100af2958'));self.assertIn('self = *(ID *)(unaff_x20 + 0x70)',self.original('0x100af2cd0'))
    def test_real_eligibleForHandoff_true_gate_is_excluded_not_whole_mixed_function(self):
        r=self.p['selector'];v,c=self.n['reachable_pointer'](int(r['address'],16));self.assertEqual(hex(v),r['raw']);self.assertEqual(c,r['chain']);a=self.n['base']+(v&((1<<36)-1));self.assertEqual(a,int(r['target'],16));self.assertEqual(self.n['read'](a,80).split(b'\0')[0].decode(),'setEligibleForHandoff:');self.assertIn('objc_stub::FUN_100c0b7e0(self,1)',self.original('0x100af2958'))
        ui=(ROOT/'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text();self.assertIn('panelWillClose?(previewRegistry.windows.isEmpty)',body(ui,'func hidePanel()'))
    def test_five_local_methods_and_all247_production_files_remain_unchanged(self):
        self.assertEqual(len(self.p['unchanged_methods']),5)
        for r in self.p['unchanged_methods']:self.assertEqual(hashlib.sha256(body((ROOT/r['path']).read_text(),r['symbol']).encode()).hexdigest(),r['sha256'])
        for p,h in self.base['production'].items():self.assertEqual(hashlib.sha256(pre_native_link_creation_bytes(ROOT/p)).hexdigest(),h)
        app=(ROOT/'replica/Sources/Pasto/AppMain.swift').read_text();s=body(app,'private func restorePanelApplication(');self.assertIn('defer { handoffPreviousApplication = nil }',s);self.assertIn('guard restore, let previous',s);self.assertIn('previous.activate(options: .activateIgnoringOtherApps)',s)
    def test_no_new_difference_or_whole_publisher_graph_or_runtime_claim(self):
        self.assertEqual(self.p['new_difference_records'],0);self.assertFalse(self.p['production_modified']);self.assertFalse(self.p['runtime_executed']);self.assertFalse(self.p['full_function_migration_verified']);self.assertIn('not proof no other',self.p['remaining'][0]);self.assertIn('cross-device subscription only',self.p['excluded_edge'])
if __name__=='__main__':unittest.main()
