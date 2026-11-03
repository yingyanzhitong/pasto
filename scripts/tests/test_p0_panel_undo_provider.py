"""Native/source contracts for the panel undo provider; never execute AppKit."""
from pathlib import Path
import hashlib, json, struct, sys, unittest, weakref

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
D = ROOT/'.local/p0-p1-parent-review/2026-11-03-focus-shortcuts'
UI = 'replica/Sources/Pasto/UI/ReplicaUIController.swift'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

class PanelUndoProvider(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = json.loads((D/'contract.json').read_text())
        cls.baseline = json.loads((D/'baseline.json').read_text())['files']
        cls.ui = (ROOT/UI).read_text()
        cls.n = {}
        exec((ROOT/cls.p['decoder']['path']).read_text().split('selectors=[]',1)[0],cls.n)

    def test_original_fragments_and_current_sources_are_bound(self):
        cache = {}
        for r in self.p['original_fragments']:
            path = ROOT/r['path']
            if path not in cache:
                cache[path] = source_fragments(path)
            self.assertEqual(cache[path][r['function_id'].split(':')[1]]['sha256'],r['sha256'])
        for path,h in self.p['current_sources'].items():
            self.assertEqual(sha(ROOT/path),h,path)
        for key in ['binary','decoder']:
            self.assertEqual(sha(ROOT/self.p[key]['path']),self.p[key]['sha256'])

    def test_complete_native_ranges_and_direct_branches_match_bytes(self):
        self.assertEqual(len(self.p['machine_ranges']),28)
        for r in self.p['machine_ranges']:
            data = self.n['read'](int(r['address'],16),int(r['end'],16)-int(r['address'],16))
            self.assertEqual(data.hex(),r['bytes'])
            self.assertEqual(hashlib.sha256(data).hexdigest(),r['sha256'])
        for r in self.p['branches']:
            pc = int(r['pc'],16)
            word = struct.unpack('<I',self.n['read'](pc,4))[0]
            self.assertEqual(hex(word),r['word'])
            relative = word & 0x3ffffff
            if relative & 1<<25:
                relative -= 1<<26
            self.assertEqual(hex(pc+relative*4),r['target'])

    def test_actual_window_and_controller_selectors_are_registered(self):
        methods = [m for c in self.p['native_window_method_tables'] for m in c['methods']]
        for name,address in [('undoManager','0x100018680'),('windowWillReturnUndoManager:','0x100077fe0')]:
            row = next(r for r in methods if r['selector']==name)
            entry = int(row['entry'],16)
            self.assertEqual(self.n['read'](entry,12).hex(),row['bytes'])
            self.assertEqual(hex(entry+8+struct.unpack('<i',self.n['read'](entry+8,4))[0]),address)

    def test_keypath_binds_the_existing_shared_undo_factory(self):
        r = self.p['keypath_getter']; pointer = int(r['pointer'],16)
        self.assertEqual(self.n['read'](pointer,4).hex(),r['bytes'])
        self.assertEqual(hex(pointer+struct.unpack('<i',self.n['read'](pointer,4))[0]),r['target'])
        for target in ['0x1002fd5cc','0x1002fd6fc']:
            self.assertTrue(any(r['target']==target for r in self.p['branches']))
        core = (ROOT/'replica/Sources/PastoCore/Pasteboard.swift').read_text()
        self.assertIn('public var pasteboardUndoManager: UndoManager { f_10037c4a4() }',core)
        self.assertIn('public func f_10037c4a4() -> UndoManager { f_1002fad30() }',core)
        self.assertIn('factory: Self.f_1002fd5e4',core)
        self.assertTrue(self.p['shared_dependency_field_offset']['runtime_offset_not_read_or_guessed'])

    def test_native_delegate_nil_branch_and_callback_result_are_not_decompiler_guesses(self):
        words = {pc:struct.unpack('<I',self.n['read'](pc,4))[0] for pc in
                 [0x100078064,0x100078088,0x10007808c,0x1000780b8,0x1000780bc]}
        self.assertEqual(words,{0x100078064:0xb4000276,0x100078088:0xd63f02c0,
                                0x10007808c:0xaa0003f4,0x1000780b8:0xd2800014,0x1000780bc:0xaa1403e0})

    def test_monitor_copies_action_before_unlock_and_diagnostic_reentry(self):
        monitor = (ROOT/'replica/Sources/PastoCore/OriginalGlobalShortcutMonitor.swift').read_text()
        method = body(monitor,'public func f_1001ea338(_ event: EventRef)')
        tokens = ['lock.lock()', 'let action = registrations.values.first { $0.identifier == identifier.id }?.action',
                  'lock.unlock()', 'guard let action else', 'DispatchQueue.main.async(execute: action)']
        positions = [method.index(t) for t in tokens]
        self.assertEqual(positions,sorted(positions))
        self.assertNotIn('DispatchQueue.main.async { registrations',method)

    def test_controller_getter_reads_the_dependency_each_time(self):
        controller = body(self.ui,'private final class ReplicaMainWindowController: NSWindowController')
        self.assertIn('OriginalDependency(\\OriginalDependencyValues.pasteboardUndoManager)',controller)
        self.assertIn('override var undoManager: UndoManager? { contentUndoManager.f_1000da768() }',controller)
        for token in ['UndoManager()','lazy var','window?.undoManager','NSWindow.undoManager']:
            self.assertNotIn(token,controller)

    def test_delegate_returns_nil_or_calls_current_provider_once(self):
        method = body(self.ui,'func windowWillReturnUndoManager(_ window: NSWindow)')
        self.assertEqual(method.strip(),'{ undoManagerRequested?() }')
        self.assertIn('var undoManagerRequested: (() -> UndoManager?)?',self.ui)

    def test_real_panel_installs_the_weak_controller_route(self):
        load = body(self.ui,'private func loadPanel()')
        tokens = ['let controller = ReplicaMainWindowController(window: panel)',
                  'mainWindowController = controller',
                  'panel.undoManagerRequested = { [weak controller] in controller?.undoManager }',
                  'panel.delegate = panel']
        positions = [load.index(t) for t in tokens]
        self.assertEqual(positions,sorted(positions))
        self.assertNotIn('mainWindowController = NSWindowController(window: panel)',load)

    def test_sdk_declares_nullable_delegate_result_and_responder_property(self):
        for path,h in self.p['sdk_headers'].items():
            self.assertEqual(sha(ROOT/path),h)
        window = next(p for p in self.p['sdk_headers'] if p.endswith('NSWindow.h'))
        responder = next(p for p in self.p['sdk_headers'] if p.endswith('NSResponder.h'))
        self.assertIn('- (nullable NSUndoManager *)windowWillReturnUndoManager:',(ROOT/window).read_text())
        self.assertIn('@property (nullable, readonly, strong) NSUndoManager *undoManager;',(ROOT/responder).read_text())

    def test_only_one_production_file_changed_and_old_tests_preserved(self):
        changed = [p for p,h in self.baseline.items() if sha(ROOT/p)!=h]
        self.assertEqual(changed,[UI])
        production = {p for p in self.baseline if p.startswith('replica/Sources/')}
        self.assertEqual(production,{str(p.relative_to(ROOT)) for p in (ROOT/'replica/Sources').rglob('*') if p.is_file()})

    def test_window_manager_patch_does_not_claim_all_undo_operations_work(self):
        persistence = ROOT/'replica/Sources/PastoCore/ClipboardPersistence.swift'
        self.assertEqual(sha(persistence),self.baseline[str(persistence.relative_to(ROOT))])
        self.assertIn('managedContext.undoManager = nil',persistence.read_text())
        self.assertFalse(self.p['compiled']); self.assertFalse(self.p['framework_executed'])
        self.assertFalse(self.p['full_function_migration_verified'])

class WeakProviderTrace(unittest.TestCase):
    def test_provider_reloads_and_does_not_keep_controller_alive(self):
        class Controller:
            manager = None
        owner = Controller(); owner.manager = object(); weak = weakref.ref(owner)
        def provider():
            current = weak()
            return current.manager if current else None
        first = provider(); owner.manager = object()
        self.assertIsNot(provider(),first)
        del owner
        self.assertIsNone(weak()); self.assertIsNone(provider())

if __name__ == '__main__':
    unittest.main()
