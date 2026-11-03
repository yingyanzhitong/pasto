"""Stack table drag-permission override and installed base implementation; static only."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from appkit_cache_static import AppKitCacheStatic
from compiled_nib_static import decode_nib_archive,nib_string
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from stack_close_session_scope_contract import pre_stack_close_session_bytes
from test_p0_repair_checksum_routing import original_fragment
from stack_table_drag_scope_contract import CHANGES,pre_stack_table_drag,pre_stack_table_drag_bytes
class StackTableDrag(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-146';cls.p=json.loads((cls.phase/'stack-table-drag-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.path='replica/Sources/PastoCore/OriginalStackTableController.swift';cls.src=(ROOT/cls.path).read_text();cls.before=(cls.phase/'before'/cls.path).read_text();cls.subclass=body(cls.src,'private final class OriginalStackTableView: NSTableView');cls.cache=AppKitCacheStatic();cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
    @classmethod
    def tearDownClass(cls):cls.cache.close()
    def original(self,a):
        r=next(r for r in self.p['original_fragments']if r['address']==a);return original_fragment((ROOT/r['path']).read_text(),a[2:])
    def test_six_original_fragments_binary_and_static_decoders_bound(self):
        self.assertEqual(len(self.p['original_fragments']),6)
        for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for k in ['binary','decoder','appkit_decoder']:
            r=self.p[k];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_installed_system_and_cache_UUIDs_sizes_maps_are_unchanged(self):
        r=self.p['system'];self.assertEqual(hashlib.sha256(Path(r['path']).read_bytes()).hexdigest(),r['sha256']);self.assertEqual([dict(path=f['path'],uuid=f['uuid'],size=f['size'])for f in self.cache.files],self.p['cache_files']);self.assertEqual(self.cache.maps,self.p['mappings']);self.assertEqual(self.cache.class_list(),(0x1e6c36240,0x5050))
    def test_table_superclass_is_control_on_the_actual_cache_class_chain(self):
        table=self.cache.class_record('NSTableView');control=self.cache.class_record('NSControl');self.assertEqual(table,self.p['appkit_table_class']);self.assertEqual(control,self.p['appkit_control_class']);self.assertEqual(table['superclass'],control['address']);self.assertEqual(table['superclass_name'],'NSControl')
    def test_all_nine_table_method_lists_have_no_override(self):
        actual=self.cache.methods(self.p['appkit_table_class'],'mouseDownCanMoveWindow');self.assertEqual(actual,self.p['appkit_table_methods']);self.assertEqual(actual['list_count'],9);self.assertEqual(actual['matches'],[])
    def test_control_fifteen_lists_bind_same_selector_with_BOOL_encoding(self):
        actual=self.cache.methods(self.p['appkit_control_class'],'mouseDownCanMoveWindow');self.assertEqual(actual,self.p['appkit_control_methods']);self.assertEqual(actual['list_count'],15);self.assertEqual(len(actual['matches']),1);self.assertEqual(actual['matches'][0]['types'],'B16@0:8')
    def test_real_default_getter_is_exact_return_false_without_calls(self):
        r=self.p['appkit_control_methods']['matches'][0];b=self.cache.read(int(r['imp'],16),8);self.assertEqual(b.hex(),r['bytes']);self.assertEqual(struct.unpack('<II',b),(0x52800000,0xd65f03c0))
    def test_original_getter_returns_true_with_bound_ARM_return_and_actor_guard(self):
        for r in self.p['ARM_words']:self.assertEqual(self.n['read'](int(r['address'],16),4).hex(),r['bytes'])
        self.assertEqual(int.from_bytes(self.n['read'](0x1000a0b9c,4),'little'),0x52800020);self.assertEqual(int.from_bytes(self.n['read'](0x1000a0bac,4),'little'),0xd65f03c0);s=self.original('0x1000a0b2c');self.assertIn('return 1;',s);self.assertIn('MainActor::get_shared',s)
    def test_original_table_archive_really_names_dedicated_subclass(self):
        r=self.p['original_table_archive'];self.assertEqual(hashlib.sha256(Path(r['path']).read_bytes()).hexdigest(),r['sha256']);self.assertEqual(hashlib.sha256((ROOT/r['reused_proof']['path']).read_bytes()).hexdigest(),r['reused_proof']['sha256']);a=decode_nib_archive(Path(r['path']).read_bytes());d={k:(t,v)for k,t,v in a['rows'][r['object']]['values']};self.assertEqual(nib_string(a,d['NSClassName'][1]),'_TtC5Paste19PasteStackTableView')
    def test_actual_source_subclass_overrides_true_with_no_new_state_or_constructor(self):
        self.assertIn('@MainActor\nprivate final class OriginalStackTableView: NSTableView',self.src);self.assertIn('override var mouseDownCanMoveWindow: Bool { true }',self.subclass);self.assertEqual(self.subclass.count('override var'),1)
        for token in ['init(','private var','private let','Task','DispatchQueue','if ','isOpaque','selectedRow','super.mouseDownCanMoveWindow']:self.assertNotIn(token,self.subclass)
    def test_real_stack_producer_constructs_subclass_and_keeps_public_type(self):
        self.assertIn('public let tableView: NSTableView',self.src);s=body(self.src,'public override init()');self.assertIn('tableView = OriginalStackTableView(frame: .init(x: 0, y: 0, width: 264, height: 44))',s);self.assertNotIn('tableView = NSTableView(',s)
    def test_all_layout_and_table_configuration_are_exactly_same_after_type_substitution(self):
        new=body(self.src,'public override init()');old=body(self.before,'public override init()');self.assertEqual(new.replace('OriginalStackTableView(frame:','NSTableView(frame:'),old)
    def test_nonselectable_row_behavior_and_row_action_contracts_unchanged(self):
        self.assertEqual(body(self.src,'public func f_100085670('),'{ false }');self.assertIn('return 0;',self.original('0x100085670'));self.assertIn('guard edge == .trailing else { return [] }',body(self.src,'public func tableView(_ tableView: NSTableView, rowActionsForRow'))
    def test_window_background_drag_permission_already_enabled_and_not_replaced(self):
        window=(ROOT/'replica/Sources/PastoCore/OriginalStackFunctions.swift').read_text();self.assertIn('window?.isMovableByWindowBackground = true',body(window,'public func f_100011138()'));controller=(ROOT/'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text();self.assertIn('controller.f_100011138()',body(controller,'func showStack()'));self.assertNotIn('isMovableByWindowBackground',self.subclass)
    def test_twelve_operations_and_four_shared_consumers_stay_unchanged(self):
        self.assertEqual(len(self.p['unchanged_methods']),12)
        for r in self.p['unchanged_methods']:self.assertEqual(hashlib.sha256(body(self.src,r['symbol']).encode()).hexdigest(),r['sha256'])
        self.assertEqual(len(self.p['shared_sources']),4)
        for p,h in self.p['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_stack_close_session_bytes(ROOT/p)).hexdigest(),h)
    def test_two_exact_hunks_one_file_preserve247_sources_and_reverse_idempotently(self):
        self.assertEqual(len(CHANGES),2);changed=[];paths={str(p.relative_to(ROOT))for p in(ROOT/'replica/Sources').rglob('*')if p.is_file()};self.assertEqual(paths,set(self.base['production']))
        for p,h in self.base['production'].items():
            if hashlib.sha256(pre_stack_close_session_bytes(ROOT/p)).hexdigest()!=h:changed.append(p)
            self.assertEqual(hashlib.sha256(pre_stack_table_drag_bytes(ROOT/p)).hexdigest(),h)
        self.assertEqual(changed,[self.path]);self.assertEqual(pre_stack_table_drag(self.src),self.before);self.assertEqual(pre_stack_table_drag(self.before),self.before);self.assertEqual(hashlib.sha256(self.src.encode()).hexdigest(),self.p['current_sources'][self.path])
    def test_finite_getter_and_producer_do_not_claim_whole_drag_UI_or_other_ABI(self):
        self.assertEqual(self.p['function_id'],'Paste:0x1000a0b2c');self.assertEqual(self.p['new_difference_records'],1);self.assertFalse(self.p['full_function_migration_verified']);self.assertFalse(self.p['runtime_executed']);self.assertTrue(self.p['finite_contract_verified']);self.assertEqual(len(self.p['adaptations']),2);self.assertIn('04430c/0f733c',self.p['remaining'][1])
if __name__=='__main__':unittest.main()
