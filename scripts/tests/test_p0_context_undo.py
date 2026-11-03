"""Current source and native-byte contracts; no CoreData/AppKit execution."""
from pathlib import Path
import hashlib,json,struct,sys,unittest,weakref
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
D=ROOT/'.local/p0-p1-parent-review/2026-11-03-context-undo'
P='replica/Sources/PastoCore/ClipboardPersistence.swift'
S='replica/Sources/PastoCore/ClipboardStore.swift'
H='replica/Sources/PastoCore/OriginalContextUndo.swift'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

class ContextUndoContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=json.loads((D/'contract.json').read_text())
        cls.base=json.loads((D/'baseline.json').read_text())['files']
        cls.persistence=(ROOT/P).read_text();cls.store=(ROOT/S).read_text();cls.helper=(ROOT/H).read_text()
        cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split('selectors=[]',1)[0],cls.n)
    def ordered(self,source,tokens):
        positions=[source.index(t)for t in tokens]
        self.assertEqual(positions,sorted(positions))
    def test_original_current_binary_and_helper_inputs_bound(self):
        cache={}
        for r in self.p['original_fragments']:
            path=ROOT/r['path']
            if path not in cache:cache[path]=source_fragments(path)
            self.assertEqual(cache[path][r['function_id'].split(':')[1]]['sha256'],r['sha256'])
        for path,h in self.p['current_sources'].items():self.assertEqual(sha(ROOT/path),h,path)
        for k in ['binary','decoder']:self.assertEqual(sha(ROOT/self.p[k]['path']),self.p[k]['sha256'])
    def test_native_ranges_distinguish_real_functions_from_selector_stubs(self):
        self.assertEqual(len(self.p['machine_ranges']),22)
        self.assertEqual(sum(r['boundary_kind']=='lc_function_start'for r in self.p['machine_ranges']),15)
        for r in self.p['machine_ranges']:
            data=self.n['read'](int(r['address'],16),int(r['end'],16)-int(r['address'],16))
            self.assertEqual(data.hex(),r['bytes']);self.assertEqual(hashlib.sha256(data).hexdigest(),r['sha256'])
        new=set(self.p['new_p0_candidates'])
        self.assertEqual(len(new),7)
        self.assertTrue(all(r['boundary_kind']=='lc_function_start'for r in self.p['machine_ranges']if r['function_id']in new))
    def test_all_direct_branch_displacements_are_bound(self):
        self.assertEqual(len(self.p['branches']),501)
        for r in self.p['branches']:
            pc=int(r['pc'],16);word=struct.unpack('<I',self.n['read'](pc,4))[0]
            self.assertEqual(hex(word),r['word']);v=word&0x3ffffff
            if v&1<<25:v-=1<<26
            self.assertEqual(hex(pc+v*4),r['target'])
    def test_real_notification_imports_are_undo_then_redo(self):
        raw=self.n['raw'];f=self.n['fixup'][0];header=struct.unpack_from('<7I',raw,f)
        self.assertEqual([r['name']for r in self.p['notifications']],['_NSUndoManagerDidUndoChangeNotification','_NSUndoManagerDidRedoChangeNotification'])
        for r in self.p['notifications']:
            value,chain=self.n['reachable_pointer'](int(r['pointer'],16))
            self.assertEqual(hex(value),r['word']);self.assertEqual(chain,r['chain']);self.assertTrue(value>>63)
            entry=struct.unpack_from('<I',raw,f+header[2]+(value&0xffffff)*4)[0];at=f+header[3]+(entry>>9)
            self.assertEqual(raw[at:raw.index(b'\0',at)].decode(),r['name'])
        header=self.p['sdk_undo_header'];self.assertEqual(sha(ROOT/header['path']),header['sha256'])
        source=(ROOT/header['path']).read_text()
        for name in ['NSUndoManagerDidUndoChangeNotification','NSUndoManagerDidRedoChangeNotification']:
            self.assertIn('FOUNDATION_EXPORT NSNotificationName const '+name,source)
    def test_keypath_and_notification_sink_are_actual_constructor_bindings(self):
        r=self.p['keypath_getter'];pc=int(r['pointer'],16)
        self.assertEqual(self.n['read'](pc,4).hex(),r['bytes'])
        self.assertEqual(hex(pc+struct.unpack('<i',self.n['read'](pc,4))[0]),r['target'])
        r=self.p['sink_callback_literal'];pc=int(r['pc'],16)
        a,b=struct.unpack('<II',self.n['read'](pc,8));self.assertEqual(self.n['read'](pc,8).hex(),r['bytes'])
        v=(((a>>5)&0x7ffff)<<2)|((a>>29)&3)
        if v&1<<20:v-=1<<21
        self.assertEqual(hex((pc&~4095)+(v<<12)+((b>>10)&0xfff)),r['target'])
    def test_error_rollback_and_false_flag_are_present_despite_decompiler_elision(self):
        self.assertEqual(struct.unpack('<I',self.n['read'](0x10035e524,4))[0],0x3900027f)
        self.assertTrue(any(r['pc']=='0x10035e520'and r['target']=='0x100c096e0'for r in self.p['branches']))
        self.assertEqual([r['name']for r in self.p['selectors'][:3]],['rollback','hasChanges','save:'])
    def test_initialization_finishes_root_migration_and_reload_before_undo_setup(self):
        initialize=body(self.store,'public init(directoryURL: URL) throws')
        self.ordered(initialize,['persistence = try Self.withLock','if try persistence.revision() == nil',
            'try persistence.commit(state, previous: nil)','try reload()','persistence.configureUndoRegistration()'])
        initialize=body(self.persistence,'init(directoryURL: URL) throws')
        self.assertIn('managedContext.undoManager = nil',initialize)
        self.assertNotIn('configureUndoRegistration()',initialize)
    def test_primary_context_installs_shared_manager_but_extensions_skip(self):
        s=body(self.persistence,'func configureUndoRegistration()')
        self.ordered(s,['guard !Bundle.main.bundlePath.hasSuffix(".appex") else { return }',
                        'context.undoManager = contentUndoManager.f_1000da768()',
                        '.NSUndoManagerDidUndoChange','.NSUndoManagerDidRedoChange','.sink'])
        self.assertEqual(s.count('contentUndoManager.f_1000da768()'),3)
        self.assertIn('OriginalDependency(\\OriginalDependencyValues.pasteboardUndoManager)',self.persistence)
        self.assertNotIn('UndoManager()',s);self.assertNotIn('removeAllActions',s)
        self.assertNotIn('UndoManager.didUndoChangeNotification',s)
    def test_one_retained_subscription_and_weak_owner_no_async_task(self):
        s=body(self.persistence,'func configureUndoRegistration()')
        self.assertIn('private var undoChangesObservation: AnyCancellable?',self.persistence)
        self.assertIn('undoChangesObservation =',s)
        self.assertIn('.sink { [weak self] _ in',s)
        self.ordered(s,['Self.undoContext(from: { self })','OriginalContextUndo.f_10035ca9c(context)'])
        for token in ['DispatchQueue','Task {','withLock','self?.save','guard let self']:self.assertNotIn(token,s)
    def test_context_projection_ends_owner_scope_before_save(self):
        self.assertIn('@inline(never)\n    private static func undoContext',self.persistence)
        s=body(self.persistence,'private static func undoContext(')
        self.assertEqual(s.strip(),'{\n        loadOwner()?.context\n    }')
    def test_synchronous_save_returns_true_for_unchanged_and_success_cases(self):
        s=body(self.helper,'static func f_10035ca9c(')
        self.ordered(s,['var succeeded = true','context.performAndWait','f_10035e4d8(context, succeeded: &succeeded)','return succeeded'])
        worker=body(self.helper,'static func f_10035e4d8(')
        self.ordered(worker,['guard context.hasChanges else { return }','try OriginalObjCExceptionBridge.f_1002ff9c8','try context.save()'])
    def test_save_error_rolls_back_marks_false_logs_and_is_consumed(self):
        s=body(self.helper,'static func f_10035e4d8(');failure=body(s,'catch')
        self.ordered(failure,['context.rollback()','succeeded = false','diagnostics.f_1000d468c().f_1000d4e0c('])
        self.assertIn('Error saving managed object context: ',failure)
        for token in ['throw','validateForInsert','validateForUpdate','removeAllActions']:self.assertNotIn(token,failure)
    def test_each_merge_brackets_registration_with_independent_manager_reads(self):
        s=body(self.persistence,'private func mergeViewChanges()')
        self.ordered(s,['context.performAndWait','for transaction in transactions',
            'context.undoManager?.disableUndoRegistration()',
            'context.mergeChanges(fromContextDidSave: transaction.objectIDNotification())',
            'context.undoManager?.enableUndoRegistration()','viewHistoryToken = token'])
        self.assertNotIn('let undoManager',s);self.assertNotIn('removeAllActions',s)
    def test_snapshot_reader_stays_without_undo(self):
        path='replica/Sources/PastoCore/ClipboardSnapshotReader.swift'
        self.assertEqual(sha(ROOT/path),self.base[path])
        self.assertIn('context.undoManager = nil',(ROOT/path).read_text())
    def test_merge_diagnoses_only_increased_pending_object_count(self):
        s=body(self.persistence,'private func mergeViewChanges()')
        self.ordered(s,['let before = context.insertedObjects.count + context.updatedObjects.count + context.deletedObjects.count',
            'context.undoManager?.disableUndoRegistration()',
            'context.mergeChanges(fromContextDidSave:',
            'context.undoManager?.enableUndoRegistration()',
            'let after = context.insertedObjects.count + context.updatedObjects.count + context.deletedObjects.count',
            'if before < after', 'Self.transactionDiagnostics.f_1000d468c().f_1000d4db8('])
        self.assertIn('[SYNC:MERGE] viewContext dirty objects:',s)
        self.assertNotIn('&+',s)
    def test_capture_and_restore_keep_the_existing_success_clear_boundary(self):
        source=(ROOT/'replica/Sources/PastoCore/Pasteboard.swift').read_text()
        s=body(source,'public func f_10037ae9c(')
        self.ordered(s,['created = try f_10037b034(items)','} catch {','return','undoManagerDependency.f_1000da768().removeAllActions()'])
        self.assertIn('Self.restoreUndoManager.f_1000da768().removeAllActions()',source)
    def test_only_two_existing_production_sources_changed_and_one_added(self):
        self.assertEqual({p for p,h in self.base.items()if sha(ROOT/p)!=h},{P,S})
        before={p for p in self.base if p.startswith('replica/Sources/')}
        after={str(p.relative_to(ROOT))for p in(ROOT/'replica/Sources').rglob('*')if p.is_file()}
        self.assertEqual(after-before,{H});self.assertFalse(before-after)
        self.assertEqual(len(before),248)
    def test_no_runtime_or_complete_undo_claim(self):
        self.assertFalse(self.p['compiled']);self.assertFalse(self.p['framework_executed'])
        self.assertFalse(self.p['full_function_migration_verified'])

class UndoSaveTraceModels(unittest.TestCase):
    def test_noop_success_and_failure_contracts(self):
        def model(changed,fail=False):
            calls=[];ok=True
            if changed:
                calls.append('save')
                if fail:calls+=['rollback','false','log'];ok=False
            return ok,calls
        self.assertEqual(model(False),(True,[]))
        self.assertEqual(model(True),(True,['save']))
        self.assertEqual(model(True,True),(False,['save','rollback','false','log']))
    def test_weak_owner_can_die_before_selected_context_is_saved(self):
        class Owner: pass
        owner=Owner();owner.context=object();weak=weakref.ref(owner)
        def select():
            current=weak()
            return current.context if current else None
        context=select();del owner
        self.assertIsNone(weak());self.assertIsNotNone(context);self.assertIsNone(select())
    def test_merge_enables_the_fresh_manager_after_reentry(self):
        calls=[];manager=['first']
        calls.append(('disable',manager[0]));manager[0]='second';calls.append(('enable',manager[0]))
        self.assertEqual(calls,[('disable','first'),('enable','second')])
    def test_merge_warning_gate_covers_decrease_equal_and_increase(self):
        for before,after,warning in [(4,3,False),(4,4,False),(4,5,True),(0,0,False),(0,1,True)]:
            self.assertEqual(before<after,warning)

if __name__=='__main__':unittest.main()
