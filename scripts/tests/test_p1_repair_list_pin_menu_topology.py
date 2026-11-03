"""Original local pin-submenu topology and actual unpin literal; static only."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from native_group_creation_result_scope_contract import pre_native_group_creation_result
from test_offline_p0_contracts import body
from list_pin_menu_topology_scope_contract import CHANGES,pre_list_pin_menu_topology
from group_menu_state_scope_contract import pre_group_menu_state_bytes

class ListPinMenuTopologyContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-111';cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.proof=json.loads((cls.phase/'list-pin-menu-topology-contract.json').read_text());cls.panel=(ROOT/'replica/Sources/Pasto/UI/PanelViews.swift').read_text();cls.ns={};exec((ROOT/cls.proof['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.ns)
    def test_twelve_original_fragments_and_static_inputs_current(self):
        self.assertEqual(len(self.proof['original_fragments']),12)
        for r in self.proof['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for r in [self.proof['binary'],self.proof['decoder'],self.proof['reference_resource']]+self.proof['reused_evidence']:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_eleven_real_calls_bind_submenu_and_ordinary_delete_separately(self):
        self.assertEqual(len(self.proof['ARM_calls']),11)
        for r in self.proof['ARM_calls']:
            pc=int(r['address'],16);data=self.ns['read'](pc,4);self.assertEqual(data.hex(),r['bytes']);w=int.from_bytes(data,'little');self.assertEqual(w&0x7c000000,0x14000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(pc+4*d,int(r['target'],16))
        self.assertIn(('0x100076150','0x10006e95c'),[(r['function'],r['target'])for r in self.proof['ARM_calls']])
    def test_actual_unpin_literal_character_pointer_is_not_bridge_pointer(self):
        r=self.proof['literal'];self.assertEqual(r['address'],'0x100d993f0');self.assertEqual(r['bridge_minus32'],'0x100d993d0');self.assertEqual(self.ns['read'](int(r['address'],16),20).decode(),'general.action.unpin');self.assertEqual(self.ns['read'](int(r['address'],16),20).hex(),r['bytes'])
        for r in self.proof['ARM_words']:self.assertEqual(self.ns['read'](int(r['address'],16),4).hex(),r['bytes'])
    def test_localization_helper_and_Chinese_label_bound(self):
        p=ROOT/'replica/Sources/PastoCore/OriginalPreviewLocalization.swift';s=body(p.read_text(),'public static func f_1001c4208()');self.assertIn('resource("general.action.unpin")',s);self.assertEqual(self.proof['reference_resource']['value'],'取消固定');self.assertEqual(self.proof['literal']['key'],self.proof['reference_resource']['key'])
    def test_target_create_unpin_are_in_one_submenu_and_keep_order(self):
        s=body(self.panel,'@ViewBuilder private var contextMenu:');a=s.index('Menu("添加到 Pasto")');sub=body(s[a:],'Menu("添加到 Pasto")');tokens=['ForEach(state.pinboardMenuTargets()','Toggle(sources: pinboardMenuBindings(for: target, items: groupItems)','Divider()','pasto.action.create-group','selectionItems: groupItems','if state.canUnassignItems(groupItems)','OriginalPreviewLocalization.f_1001c4208()','state.assignItems(groupItems, to: nil)'];cursor=0
        for t in tokens:cursor=sub.index(t,cursor)+len(t)
        self.assertEqual(sub.count('Divider()'),1)
        assignment=body(self.panel,'private func pinboardMenuBindings(')
        self.assertIn('set: { _ in state.assignItems(items, to: target) }',assignment)
        self.assertEqual(assignment.count('state.assignItems(items, to: target)'),1)
    def test_legacy_extra_root_remove_actions_gone(self):
        s=body(self.panel,'@ViewBuilder private var contextMenu:')
        for t in ['从此 Pasto 移除','从所有 Pasto 移除','store.unassign(ids:','assignSelection(to: nil)']:self.assertNotIn(t,s)
        a=s.index('Menu("添加到 Pasto")');sub=body(s[a:],'Menu("添加到 Pasto")');self.assertEqual(s.count('canUnassignItems'),sub.count('canUnassignItems'));self.assertEqual(s.count('state.assignItems(groupItems, to: nil)'),1)
    def test_current_context_delete_action_is_preserved_without_nil_assignment(self):
        s=body(self.panel,'@ViewBuilder private var contextMenu:');self.assertIn('Button("删除", role: .destructive) { state.deleteSelection() }',s);self.assertEqual(s.count('state.deleteSelection()'),1);self.assertNotIn('deleteSelection(to:',s)
    def test_captured_native_input_and_original_gate_preserved(self):
        s=body(self.panel,'@ViewBuilder private var contextMenu:');self.assertEqual(s.count('contextMenuRestoreItems()'),1);self.assertIn('let groupItems = state.controller?.contextMenuRestoreItems() ?? []',s);self.assertIn('state.canUnassignItems(groupItems)',s);self.assertIn('state.assignItems(groupItems, to: nil)',s)
    def test_five_shared_sources_and_six_consumer_methods_unchanged(self):
        self.assertEqual(len(self.proof['shared_sources']),5);self.assertEqual(len(self.proof['unchanged_methods']),6)
        for p,h in self.proof['shared_sources'].items():self.assertEqual(hashlib.sha256(pre_native_group_creation_result((ROOT/p).read_text()).encode()).hexdigest(),h);self.assertEqual(h,self.base['production'][p])
        for r in self.proof['unchanged_methods']:self.assertEqual(hashlib.sha256(body((ROOT/r['path']).read_text(),r['symbol']).encode()).hexdigest(),r['sha256'])
    def test_only_one_production_hunk_exactly_reverses(self):
        self.assertEqual(len(CHANGES),1)
        for p,h in self.base['production'].items():
            data=pre_group_menu_state_bytes(ROOT/p);data=pre_list_pin_menu_topology(data.decode()).encode()if p.endswith('.swift')else data;self.assertEqual(hashlib.sha256(data).hexdigest(),h)
        for p,h in self.proof['current_sources'].items():self.assertEqual(hashlib.sha256(pre_group_menu_state_bytes(ROOT/p)).hexdigest(),h)
    def test_reverse_is_idempotent_after_older_topology_restored(self):
        before=(self.phase/'before/replica/Sources/Pasto/UI/PanelViews.swift').read_text();self.assertEqual(pre_list_pin_menu_topology(self.panel),before);self.assertEqual(pre_list_pin_menu_topology(before),before)
    def test_finite_menu_does_not_certify_whole_constructor_or_runtime(self):
        self.assertFalse(self.proof['full_function_migration_verified']);self.assertFalse(self.proof['runtime_executed']);self.assertEqual(len(self.proof['remaining']),3);self.assertIn('Whole context-menu constructor06f41c',self.proof['remaining'][0]);self.assertIn('not all original app',self.proof['remaining'][0]);self.assertIn('Ordinary current-context Delete remains',self.proof['remaining'][1])

if __name__=='__main__':unittest.main()
