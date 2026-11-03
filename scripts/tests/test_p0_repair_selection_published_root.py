"""Bind selection DI/keypath root to actual bytes; no framework or application execution."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from native_capture_lookup_scope_contract import pre_native_capture_lookup
class SelectionPublishedRootContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-121';cls.p=json.loads((cls.phase/'selection-published-root-contract.json').read_text());cls.ns={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.ns)
    def test_twelve_original_fragments_bound(self):
        self.assertEqual(len(self.p['original_fragments']),12)
        for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
    def test_binary_decoder_and_dispatch_inputs_unchanged(self):
        for k in ['decoder','binary','native_dispatch']:
            r=self.p[k];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_seven_signed_relative_pointers_are_actual_targets(self):
        self.assertEqual(len(self.p['relative_pointers']),7)
        for r in self.p['relative_pointers']:
            a=int(r['address'],16);b=self.ns['read'](a,4);self.assertEqual(b.hex(),r['bytes']);self.assertEqual(a+int.from_bytes(b,'little',signed=True),int(r['target'],16))
    def test_keypath_symbolic_root_is_ActiveSelection_not_original_view(self):
        self.assertEqual(self.ns['read'](0x100ce49b4,1),b'\x01');self.assertEqual(self.ns['read'](0x100c2d65a,16),b'ActiveSelection\0');self.assertEqual(self.ns['read'](0x100ce49ac,7),b'SaySSG\0');self.assertIn('not the original ItemCollectionView',self.p['root_correction'])
    def test_stored_wrapper_keypath_and_ivar_metadata_are_same(self):
        self.assertEqual(len(self.p['chained_pointers']),2)
        for r in self.p['chained_pointers']:
            a=int(r['address'],16);v,c=self.ns['reachable_pointer'](a);self.assertEqual(c,r['chain']);self.assertEqual(self.ns['read'](a,8).hex(),r['bytes']);self.assertEqual(self.ns['base']+(v&((1<<36)-1)),int(r['target'],16))
        self.assertEqual(self.ns['read'](0x100de3f30,17),b'_itemIdentifiers\0');self.assertEqual(0x100c2d634+int.from_bytes(self.ns['read'](0x100c2d634,4),'little',signed=True),0x100fae028)
    def test_actual_caller_reloads_DI_result_into_receiver(self):
        for r in self.p['ARM_words']:self.assertEqual(self.ns['read'](int(r['address'],16),4).hex(),r['bytes'])
        self.assertEqual(int.from_bytes(self.ns['read'](0x100067c48,4),'little'),0xf9401ff4)
        self.assertEqual(int.from_bytes(self.ns['read'](0x100067c4c,4),'little'),0xaa1603e0)
        self.assertEqual(int.from_bytes(self.ns['read'](0x100067c40,4),'little'),0x9100e3e8)
    def test_actual_DI_call_then_setter_targets_are_bound(self):
        self.assertEqual(len(self.p['ARM_calls']),2)
        for r in self.p['ARM_calls']:
            a=int(r['address'],16);b=self.ns['read'](a,4);w=int.from_bytes(b,'little');self.assertEqual(b.hex(),r['bytes']);self.assertEqual(w&0xfc000000,0x94000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(a+4*d,int(r['target'],16))
    def test_projected_getter_uses_same_ivar_metadata(self):
        words=[int.from_bytes(self.ns['read'](a,4),'little')for a in [0x1000f2c2c,0x1000f2c30]];a=0x1000f2c2c;w=words[0];imm=((w>>5)&0x7ffff)*4+((w>>29)&3)
        if imm&0x100000:imm-=0x200000
        self.assertEqual((a&~4095)+(imm<<12)+(((words[1]>>10)&0xfff)*8),0x100fae028)
    def test_no_production_source_or_web_version_changes_since120(self):
        base=json.loads((self.phase/'baseline.json').read_text())
        for p,h in base['production'].items():
            data=(ROOT/p).read_bytes();data=pre_native_capture_lookup(data.decode()).encode()if p.endswith('.swift')else data;self.assertEqual(hashlib.sha256(data).hexdigest(),h)
        for p in ['replica/Package.swift','package.json','replica/function-map.json']:self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),base['other'][p])
        web=json.loads((ROOT/'.local/download-links/change-report.json').read_text())
        for p,h in web['source_changes'].items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),h)
    def test_unknown_sink_is_not_counted_as_OSD_or_full_migration(self):
        self.assertEqual(self.p['new_difference_records'],0);self.assertFalse(self.p['production_changed']);self.assertFalse(self.p['full_P0_completion']);self.assertFalse(self.p['full_function_migration_verified']);self.assertFalse(self.p['runtime_executed']);self.assertIn('exact sink effect remains unbound',self.p['consumer_status'])
if __name__=='__main__':unittest.main()
