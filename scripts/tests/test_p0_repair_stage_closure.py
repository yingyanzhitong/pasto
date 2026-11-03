"""Finite P0-stage closure and independent telemetry exclusion, static evidence only."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from native_search_content_scope_contract import pre_native_search_content,pre_native_search_content_bytes
from test_offline_p0_contracts import body
class P0StageClosureContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=json.loads((ROOT/'.local/p0-repair/phase-128/p0-stage-closure-contract.json').read_text());cls.ns={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.ns)
    def test_actual_original_source_fragments_and_static_inputs_bound(self):
        for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for key in ['binary','decoder','prior_report','prior2012_test_summary']:
            r=self.p[key];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_itemdata_dependency_keypath_getter_relative_pointer_and_two_tail_branches(self):
        r=self.p['keypath_getter'];a=int(r['address'],16);b=self.ns['read'](a,4);self.assertEqual(b.hex(),r['bytes']);self.assertEqual(a+struct.unpack('<i',b)[0],int(r['target'],16))
        for r in self.p['branches']:
            a=int(r['address'],16);b=self.ns['read'](a,4);self.assertEqual(b.hex(),r['bytes']);w=int.from_bytes(b,'little');self.assertEqual(w&0xfc000000,0x14000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(a+4*d,int(r['target'],16))
    def test_actual_factory_returns_witness_at_existential_slot_then_conformance_reaches_protocol(self):
        p=self.p['telemetry_protocol_binding'];r=p['witness'];v,c=self.ns['reachable_pointer'](int(r['address'],16));self.assertEqual(hex(v),r['raw']);self.assertEqual(c,r['chain']);self.assertEqual(self.ns['base']+(v&((1<<36)-1)),int(r['target'],16))
        for r in p['factory_witness_return']:self.assertEqual(self.ns['read'](int(r['address'],16),4).hex(),r['bytes'])
        a=0x10019b814;w=int.from_bytes(self.ns['read'](a,4),'little');v=int.from_bytes(self.ns['read'](a+4,4),'little');i=((w>>5)&0x7ffff)*4+((w>>29)&3)
        if i&0x100000:i-=0x200000
        self.assertEqual((a&~4095)+(i<<12)+((v>>10)&0xfff),0x100ebd5b0);self.assertEqual(int.from_bytes(self.ns['read'](0x10019b81c,4),'little'),0xa901a274)
    def test_protocol_parent_module_and_implementation_names_are_bound_by_real_relative_chain(self):
        p=self.p['telemetry_protocol_binding']
        for r in p['relative_pointers']:
            a=int(r['address'],16);b=self.ns['read'](a,4);self.assertEqual(b.hex(),r['bytes']);self.assertEqual(a+struct.unpack('<i',b)[0],int(r['target'],16))
        self.assertEqual([r['text']for r in p['names']],['Telemetry','PasteTelemetry','TelemetryImpl'])
        for r in p['names']:self.assertEqual(self.ns['read'](int(r['address'],16),len(r['text'])+1),r['text'].encode()+b'\0')
    def test_DI_provider_names_actual_telemetry_source_and_factory(self):
        r=next(r for r in self.p['original_fragments']if r['address']=='0x10019b694');s=source_fragments(ROOT/r['path'])['0x10019b694'];self.assertEqual(s['sha256'],r['sha256']);whole=(ROOT/r['path']).read_text();self.assertIn('PasteTelemetry/DI+PasteTelemetry.swift',whole);self.assertIn('FUN_10019b6f0',whole)
    def test_callback_uses_second_field_and_extras_dictionary_not_original_entity(self):
        for r in self.p['ARM_words']:self.assertEqual(self.ns['read'](int(r['address'],16),4).hex(),r['bytes'])
        self.assertEqual(int.from_bytes(self.ns['read'](0x10031b300,4),'little'),0xf9447508);self.assertEqual(int.from_bytes(self.ns['read'](0x10031b3a0,4),'little'),0xaa0003f9);self.assertEqual(int.from_bytes(self.ns['read'](0x10031b3b4,4),'little'),0xf94016c8)
        def movs(pcs):
            v=0
            for a in pcs:
                w=int.from_bytes(self.ns['read'](a,4),'little');v|=((w>>5)&0xffff)<<(16*((w>>21)&3))
            return v.to_bytes(8,'little')
        self.assertEqual(movs([0x10031b350,0x10031b354,0x10031b358])[:6],b'source');self.assertEqual((movs(list(range(0x10031b374,0x10031b384,4)))+movs(list(range(0x10031b388,0x10031b398,4))))[:14],b'item-data.read')
    def test_thirteen_actual_current_consumer_methods_and_all247_production_hashes_unchanged(self):
        self.assertEqual(len(self.p['source_refs']),13)
        for r in self.p['source_refs']:self.assertEqual(hashlib.sha256(body(pre_native_search_content((ROOT/r['path']).read_text()),r['symbol']).encode()).hexdigest(),r['sha256'])
        for p,h in self.p['current_production_hashes'].items():self.assertEqual(hashlib.sha256(pre_native_search_content_bytes(ROOT/p)).hexdigest(),h)
    def test_stage_close_has_all_five_modules_and_does_not_claim_full_migration(self):
        self.assertEqual(len(self.p['P0_stage_rows']),5);self.assertEqual(len({r['module']for r in self.p['P0_stage_rows']}),5);self.assertTrue(self.p['P0_confirmed_source_repair_stage_complete']);self.assertFalse(self.p['full_P0_completion']);self.assertFalse(self.p['full_function_migration_verified']);self.assertFalse(self.p['P1_implementation_changed']);self.assertFalse(self.p['runtime_executed']);self.assertEqual(self.p['next_stage'],'检查P1');self.assertEqual(len(self.p['remaining_boundaries']),3)
if __name__=='__main__':unittest.main()
