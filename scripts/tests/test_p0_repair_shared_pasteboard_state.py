from capture_lifecycle_scope_contract import pre_capture_lifecycle
"""Shared writer/poll instance and compatibility-facade contracts; source/ARM only."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from shared_pasteboard_state_scope_contract import CHANGES,pre_shared_pasteboard_state

class SharedPasteboardStateContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-118';cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.proof=json.loads((cls.phase/'shared-pasteboard-state-contract.json').read_text());cls.src={Path(p).stem:(ROOT/p).read_text()for p in cls.proof['current_sources']};cls.state=cls.src['OriginalPasteboardCaptureState'];cls.write=body(cls.state,'public func f_10037875c(');cls.facade=body(cls.src['OriginalPasteboard'],'public final class OriginalPasteboardWriter');cls.finish=body(cls.src['Pasteboard'],'private func finishPasteboardWrite(');cls.ns={};exec((ROOT/cls.proof['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.ns)
    def order(self,s,tokens):
        cursor=0
        for t in tokens:cursor=s.index(t,cursor)+len(t)
    def test_eight_original_initializer_writer_poll_lifecycle_fragments_current(self):
        self.assertEqual(len(self.proof['original_fragments']),8)
        for r in self.proof['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
    def test_binary_decoder_and_two_prior_proofs_current(self):
        for r in [self.proof['binary'],self.proof['decoder']]:self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
        for p,h in self.proof['reused_evidence'].items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),h)
    def test_thirteen_real_calls_bind_same_state_constructor_writer_count_poll_start(self):
        self.assertEqual(len(self.proof['ARM_calls']),13)
        for r in self.proof['ARM_calls']:
            pc=int(r['address'],16);data=self.ns['read'](pc,4);w=int.from_bytes(data,'little');self.assertEqual(data.hex(),r['bytes']);self.assertEqual(w&0xfc000000,0x94000000);d=w&0x3ffffff
            if d&0x2000000:d-=0x4000000
            self.assertEqual(pc+d*4,int(r['target'],16))
        self.assertEqual(sum(r['function']=='0x10037a028'for r in self.proof['ARM_calls']),2)
    def test_five_actual_selectors_decode_even_opaque_index_stub_names(self):
        self.assertEqual({r['selector']for r in self.proof['selectors']},{'generalPasteboard','changeCount','clearContents','writeObjects:','setData:forType:'})
        for r in self.proof['selectors']:
            a=int(r['pointer'],16);v,c=self.ns['reachable_pointer'](a);self.assertEqual(c,r['chain']);self.assertEqual(self.ns['read'](a,8).hex(),r['pointer_bytes']);t=self.ns['base']+(v&((1<<36)-1));o=self.ns['offset'](t);self.assertEqual(self.ns['raw'][o:self.ns['raw'].index(b'\0',o)].decode(),r['selector'])
    def test_fourteen_real_words_bind_native_shared_PB_and_count_fields(self):
        self.assertEqual(len(self.proof['ARM_words']),14)
        for r in self.proof['ARM_words']:self.assertEqual(self.ns['read'](int(r['address'],16),4).hex(),r['bytes'])
        for pc,offset in [(0x100378694,0x10),(0x100378734,0x30),(0x100378744,0x30),(0x100378a38,0x30),(0x10037a044,0x10),(0x10037a050,0x30)]:
            w=int.from_bytes(self.ns['read'](pc,4),'little');self.assertEqual(((w>>10)&0xfff)*8,offset)
    def test_actual_write_body_moves_without_reimplementing_representation_or_count_logic(self):
        p='replica/Sources/PastoCore/OriginalPasteboard.swift';old=body((self.phase/'before'/p).read_text(),'public func f_10037875c(');reconstructed=self.write.replace('Self.current(for: pasteboard)','OriginalPasteboardCaptureState.current(for: pasteboard)');self.assertEqual(reconstructed,old);self.assertEqual(hashlib.sha256(old.encode()).hexdigest(),self.proof['write_body_equivalence']['before_sha256'])
    def test_state_write_keeps_ordered_type_iteration_nil_data_and_empty_write_behavior(self):
        self.order(self.write,['items.map','for type in item.f_10037da6c()','if let data = item.f_10037e5e0(forType: type)','object.setData(','pasteboard.clearContents()','pasteboard.writeObjects(objects)','lastChangeCount = pasteboard.changeCount'])
        for t in ['guard !items.isEmpty','Set(','sorted(','filter(','if lastWriteSucceeded','throw','return false']:self.assertNotIn(t,self.write)
    def test_registered_branch_calls_that_state_without_allocating_writer_or_reading_initial_count(self):
        branch=body(self.finish,'if let state = OriginalPasteboardCaptureState.current(for: pasteboard),\n           state.pasteboard === pasteboard');self.assertIn('state.f_10037875c(objects)',branch)
        for t in ['OriginalPasteboardWriter(','.changeCount','f_100378664','register(','Timer','delegate']:self.assertNotIn(t,branch)
    def test_same_name_but_different_object_uses_supplied_object_and_keeps_legacy_count_sync(self):
        self.assertIn('state.pasteboard === pasteboard',self.finish)
        input_board=object();registered_board=object()
        self.assertIsNot(input_board,registered_board)
        chosen=registered_board if registered_board is input_board else input_board
        self.assertIs(chosen,input_board)
        self.assertIn('let writer = OriginalPasteboardWriter(pasteboard: pasteboard)',self.finish)
        self.assertIn('Self.current(for: pasteboard)?.lastChangeCount = lastChangeCount',self.write)
    def test_unregistered_branch_preserves_standalone_writer_for_supplied_pasteboard(self):
        self.assertIn('} else {\n            let writer = OriginalPasteboardWriter(pasteboard: pasteboard)\n            writer.f_10037875c(objects)',self.finish);self.assertIn('self.pasteboard = pasteboard',self.facade);self.assertIn('f_100378664(changeCount: 0, pasteboard: pasteboard)',self.facade)
    def test_facade_retains_old_public_init_and_readonly_status_via_private_state(self):
        self.assertIn('public init(pasteboard: NSPasteboard)',self.facade);self.assertIn('public let pasteboard: NSPasteboard',self.facade);self.assertIn('private let state: OriginalPasteboardCaptureState',self.facade);self.assertIn('public var lastChangeCount: Int { state.lastChangeCount }',self.facade);self.assertIn('public var lastWriteSucceeded: Bool { state.lastWriteSucceeded }',self.facade);self.assertIn('public private(set) var lastWriteSucceeded = false',self.state)
    def test_facade_has_no_second_count_storage_and_only_delegates_write(self):
        write=body(self.facade,'public func f_10037875c(');self.assertEqual(write.strip(),'{\n        state.f_10037875c(items)\n    }');self.assertNotIn('var lastChangeCount: Int\n',self.facade);self.assertNotIn('lastChangeCount =',self.facade);self.assertNotIn('pasteboard.changeCount',self.facade)
    def test_facade_zero_saved_count_initializer_reads_supplied_count_once_without_registration_or_timers(self):
        s=body(self.state,'private init(pasteboard:');self.assertIn('changeCount == 0 ? pasteboard.changeCount : changeCount',s);self.assertEqual(s.count('pasteboard.changeCount'),1);initial=body(self.facade,'public init(pasteboard:')
        for t in ['register(','current(for:','Timer','start(','delegate','persistChangeCount']:self.assertNotIn(t,initial)
        for p,h in self.proof['lazy_constructor_dependencies'].items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),h)
        diagnostic=(ROOT/'replica/Sources/PastoCore/OriginalLocalDiagnostics.swift').read_text()
        self.assertIn('self.cached = nil',body(diagnostic,'private init(name:'))
        self.assertEqual(body(diagnostic,'public static func f_1000d4624(').strip(),'{\n        OriginalNamedDiagnostic(name: name)\n    }')
        dependency=(ROOT/'replica/Sources/PastoCore/OriginalDependencies.swift').read_text()
        constructor=body(dependency,'public init(_ keyPath:')
        self.assertIn('cached = nil',constructor)
        self.assertIn('resolve = { Self.f_1000da760(keyPath) }',constructor)
    def test_external_facade_write_still_synchronizes_registered_monitor_count(self):
        self.order(self.write,['lastChangeCount = pasteboard.changeCount','Self.current(for: pasteboard)?.lastChangeCount = lastChangeCount']);self.assertNotIn('Self.register',self.write);self.assertNotIn('persistChangeCount',self.write)
    def test_state_weak_registry_delegate_and_same_name_compatibility_not_replaced_by_strong_pool(self):
        self.assertIn('private static var active: [NSPasteboard.Name: WeakState] = [:]',self.state);self.assertIn('weak var value: OriginalPasteboardCaptureState?',self.state);self.assertIn('public weak var delegate:',self.state);p='replica/Sources/PastoCore/OriginalPasteboardCaptureState.swift';old=(self.phase/'before'/p).read_text();self.assertEqual(body(self.state,'private final class WeakState'),body(old,'private final class WeakState'));self.assertNotIn('static var writers',self.state)
    def test_fourteen_existing_constructor_poll_start_stop_and_native_restore_methods_unchanged(self):
        self.assertEqual(len(self.proof['unchanged_methods']),14)
        for r in self.proof['unchanged_methods']:self.assertEqual(hashlib.sha256(body(pre_capture_lifecycle((ROOT/r['path']).read_text()),r['symbol']).encode()).hexdigest(),r['sha256'])
    def test_self_write_then_poll_uses_same_count_while_external_change_still_schedules(self):
        source=self.src['Pasteboard'];poll=body(source,'public func f_10037a028()')
        self.order(poll,['let count = pasteboard.changeCount','guard count != lastChangeCount else { return }','lastChangeCount = pasteboard.changeCount','syncTimer = Timer.scheduledTimer'])
        self.assertEqual(body(source,'private var pasteboard:'),'{ captureState.pasteboard }')
        self.assertIn('get { captureState.lastChangeCount }',source)
        self.assertIn('set { captureState.lastChangeCount = newValue }',source)
        self.assertIn('lastChangeCount = pasteboard.changeCount',self.write)
        active=body(self.finish,'if let state = OriginalPasteboardCaptureState.current(for: pasteboard),\n           state.pasteboard === pasteboard')
        self.assertIn('state.f_10037875c(objects)',active)
        self.assertNotIn('lastChangeCount =',active)
    def test_only_active_route_eliminates_constructor_count_read_not_actual_postwrite_count_read(self):
        p='replica/Sources/PastoCore/OriginalPasteboard.swift';old_init=body((self.phase/'before'/p).read_text(),'public init(pasteboard:');self.assertEqual(old_init.count('pasteboard.changeCount'),1);self.assertEqual(self.write.count('pasteboard.changeCount'),1);active=body(self.finish,'if let state = OriginalPasteboardCaptureState.current(for: pasteboard),\n           state.pasteboard === pasteboard');self.assertNotIn('init(',active);self.assertNotIn('Writer(',active)
    def test_postwrite_count_persistence_prepare_error_Undo_and_notification_tail_unchanged(self):
        start=self.finish.index('        if let state = OriginalPasteboardCaptureState.current(for: pasteboard)',self.finish.index('            writer.f_10037875c(objects)'));suffix=self.finish[start:];self.assertEqual(hashlib.sha256(suffix.encode()).hexdigest(),self.proof['postwrite_tail_sha256']);self.order(suffix,['state.persistChangeCount?(state.lastChangeCount)','do {','let restoration = try prepareRestoration()','try recordRestoredSelection(restoration)','} catch {','removeAllActions()','NotificationCenter.default.post(','didRestoreItem.send()'])
    def test_five_hunks_reverse_all247_production_sources_and_six_shared_implementations_remain_bound(self):
        self.assertEqual(len(CHANGES),5)
        for p,h in self.base['production'].items():
            data=(ROOT/p).read_bytes();data=pre_shared_pasteboard_state(data.decode()).encode()if p.endswith('.swift')else data;self.assertEqual(hashlib.sha256(data).hexdigest(),h)
        for p,h in {**self.proof['current_sources'],**self.proof['shared_sources']}.items():self.assertEqual(hashlib.sha256(pre_capture_lifecycle((ROOT/p).read_text()).encode()).hexdigest(),h)
    def test_reversal_idempotent_no_full_DI_or_runtime_latency_completion_claim(self):
        for p in self.proof['current_sources']:
            old=(self.phase/'before'/p).read_text();self.assertEqual(pre_shared_pasteboard_state((ROOT/p).read_text()),old);self.assertEqual(pre_shared_pasteboard_state(old),old)
        self.assertFalse(self.proof['full_function_migration_verified']);self.assertFalse(self.proof['runtime_executed']);self.assertEqual(self.proof['new_difference_records'],0);self.assertEqual(len(self.proof['remaining']),4)

if __name__=='__main__':unittest.main()
