"""Pasto metadata adapter boundaries, native evidence and independent state traces."""
from pathlib import Path
import hashlib,json,struct,sys,unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
D=ROOT/'.local/p0-p1-parent-review/2026-11-03-undo-metadata'
P='replica/Sources/PastoCore/ClipboardPersistence.swift'
H='replica/Sources/PastoCore/OriginalContextUndo.swift'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

class UndoMetadataBoundary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=json.loads((D/'contract.json').read_text());cls.base=json.loads((D/'baseline.json').read_text())['files']
        cls.persistence=(ROOT/P).read_text();cls.helper=(ROOT/H).read_text();cls.n={}
        exec((ROOT/cls.p['decoder']['path']).read_text().split('selectors=[]',1)[0],cls.n)
    def order(self,s,tokens):
        values=[s.index(t)for t in tokens];self.assertEqual(values,sorted(values))
    def test_original_native_and_current_source_inputs_fresh(self):
        cache={}
        for r in self.p['reused_original_fragments']+self.p['preference_fragments']:
            p=ROOT/r['path']
            if p not in cache:cache[p]=source_fragments(p)
            self.assertEqual(cache[p][r['function_id'].split(':')[1]]['sha256'],r['sha256'])
        for key in ['binary','decoder','previous_native_proof']:
            r=self.p[key];self.assertEqual(sha(ROOT/r['path']),r['sha256'])
        for p,h in self.p['current_sources'].items():self.assertEqual(sha(ROOT/p),h,p)
    def test_native_ranges_and_preference_branches_match(self):
        for r in self.p['reused_machine_ranges']+self.p['preference_machine_ranges']:
            data=self.n['read'](int(r['address'],16),int(r['end'],16)-int(r['address'],16))
            self.assertEqual(data.hex(),r['bytes']);self.assertEqual(hashlib.sha256(data).hexdigest(),r['sha256'])
        self.assertEqual(len(self.p['preference_branches']),76)
        for r in self.p['preference_branches']:
            pc=int(r['pc'],16);w=struct.unpack('<I',self.n['read'](pc,4))[0]
            self.assertEqual(hex(w),r['word']);d=w&0x3ffffff
            if d&1<<25:d-=1<<26
            self.assertEqual(hex(pc+4*d),r['target'])
    def test_original_stack_preference_writer_uses_key_value_storage(self):
        records={r['function_id']:r for r in self.p['preference_fragments']}
        record=records['Paste:0x1002cac1c'];source=(ROOT/record['path']).read_text()
        start=source.index('/* Address: 0x1002cac1c |');end=source.find('/* Address:',start+1)
        source=source[start:end]
        self.assertIn('objc_stub::setObject_forKey_',source)
        self.assertIn('objc_stub::removeObjectForKey_',source)
        for token in ['registerUndo','beginUndoGrouping','NSManagedObjectContext']:self.assertNotIn(token,source)
    def test_public_sdk_declares_explicit_pending_change_processing_and_balanced_registration(self):
        for p,h in self.p['sdk_headers'].items():self.assertEqual(sha(ROOT/p),h)
        core=next(p for p in self.p['sdk_headers']if p.endswith('NSManagedObjectContext.h'))
        undo=next(p for p in self.p['sdk_headers']if p.endswith('NSUndoManager.h'))
        self.assertIn('contexts process changes to the object graph coalesced at the end of the event',(ROOT/core).read_text())
        self.assertIn('must be invoked an equal number of times',(ROOT/undo).read_text())
    def test_native_edits_flush_before_metadata_registration_is_disabled(self):
        s=body(self.persistence,'private static func withoutMetadataUndo(')
        self.order(s,['context.processPendingChanges()','let manager = context.undoManager',
                      'manager?.disableUndoRegistration()','defer {','try operation()'])
        self.assertEqual(s.count('context.processPendingChanges()'),2)
        defer=body(s,'defer')
        self.order(defer,['context.processPendingChanges()','manager?.enableUndoRegistration()'])
        self.assertNotIn('context.undoManager?.enableUndoRegistration()',s)
        self.assertNotIn('removeAllActions',s)
    def test_compatibility_root_writes_are_all_in_the_metadata_boundary(self):
        s=body(self.persistence,'func commit<T>(')
        start=s.index('try Self.withoutMetadataUndo(in: context)')
        block=body(s[start:],'try Self.withoutMetadataUndo(in: context)')
        for key in ['"key"','"version"','"preferences"','"cloudMetadata"','"cloudJournal"']:
            self.assertIn(key,block)
        self.assertIn('ClipboardSourcePersistence.versionKey',block)
        self.assertLess(s.index('try transaction.repository.lists.refreshHistoryIfNeeded()'),start)
        self.assertIn('Self.withoutMetadataUndo(in: context) { root.setValue(UUID(), forKey: "revision") }',s)
        self.assertLess(s.index('root.setValue(UUID(), forKey: "revision")'),s.index('try context.save()'))
    def test_undo_revision_is_fresh_and_updated_in_the_same_save_bridge(self):
        s=body(self.persistence,'private static func updateRevisionAfterUndo(')
        self.order(s,['NSFetchRequest<NSManagedObject>(entityName: "State")','request.fetchLimit = 2',
                      'let roots = try context.fetch(request)','guard roots.count == 1',
                      'withoutMetadataUndo(in: context) { roots[0].setValue(UUID(), forKey: "revision") }'])
        callback=body(self.persistence,'func configureUndoRegistration()')
        self.order(callback,['Self.undoContext(from: { self })','OriginalContextUndo.f_10035ca9c(context)',
                             'try Self.updateRevisionAfterUndo(in: context)'])
        self.assertNotIn('guard let self',callback)
        worker=body(self.helper,'static func f_10035e4d8(')
        self.order(worker,['guard context.hasChanges else { return }','try OriginalObjCExceptionBridge.f_1002ff9c8',
                           'try prepareForSave?()','try context.save()'])
        self.assertIn('prepareForSave: (() throws -> Void)? = nil',self.helper)
    def test_save_preparation_failure_uses_original_rollback_false_log_boundary(self):
        worker=body(self.helper,'static func f_10035e4d8(');failure=body(worker,'catch')
        self.order(failure,['context.rollback()','succeeded = false','diagnostics.f_1000d468c().f_1000d4e0c('])
        self.assertNotIn('throw',failure)
        wrapper=body(self.helper,'static func f_10035ca9c(')
        self.order(wrapper,['var succeeded = true','context.performAndWait','f_10035e4d8(context, succeeded: &succeeded, prepareForSave: prepareForSave)','return succeeded'])
    def test_revision_reader_and_store_refresh_gates_remain_unchanged(self):
        snapshot='replica/Sources/PastoCore/ClipboardSnapshotReader.swift';store='replica/Sources/PastoCore/ClipboardStore.swift'
        for p in [snapshot,store]:self.assertEqual(sha(ROOT/p),self.base[p])
        reader=(ROOT/snapshot).read_text();self.assertIn('request.propertiesToFetch = ["version", "revision"]',reader)
        self.assertIn('let revision = root["revision"] as? UUID',reader)
        source=(ROOT/store).read_text();self.assertIn('if local == baseline, try revision() == diskRevision { return }',source)
    def test_default_native_save_body_and_merge_bracket_still_preserve_their_contracts(self):
        s=body(self.persistence,'private func mergeViewChanges()')
        self.order(s,['context.undoManager?.disableUndoRegistration()',
                      'context.mergeChanges(fromContextDidSave:',
                      'context.undoManager?.enableUndoRegistration()'])
        before=(D/'before'/P).read_text()
        self.assertEqual(s,body(before,'private func mergeViewChanges()'))
        self.assertEqual(body(self.persistence,'private static func undoContext('),body(before,'private static func undoContext('))
    def test_only_two_recorded_files_changed_and_all_prior_tests_preserved(self):
        self.assertEqual({p for p,h in self.base.items()if sha(ROOT/p)!=h},{P,H})
        actual={str(p.relative_to(ROOT))for p in(ROOT/'replica/Sources').rglob('*')if p.is_file()}
        self.assertEqual(actual,{p for p in self.base if p.startswith('replica/Sources/')})
        self.assertEqual(len(actual),249)
    def test_adapter_fix_does_not_expand_native_scope_or_claim_framework_test(self):
        self.assertEqual(self.p['new_native_denominator_entries'],0)
        self.assertTrue(self.p['implementation_is_Pasto_compatibility_adapter'])
        self.assertFalse(self.p['compiled']);self.assertFalse(self.p['framework_executed'])
        self.assertFalse(self.p['full_function_migration_verified'])

class DeferredMetadataTrace(unittest.TestCase):
    """Specification model of delayed recording, not a substitute for CoreData execution."""
    class Store:
        def __init__(self):
            self.values={'item':'old','preferences':'p0','revision':'r0'}
            self.pending=[];self.undo=[];self.redo=[];self.disabled=0;self.disk=dict(self.values)
        @property
        def enabled(self):return self.disabled==0
        def write(self,key,value):
            old=self.values[key]
            if old!=value:self.values[key]=value;self.pending.append((key,old,value))
        def flush(self):
            if self.enabled:self.undo.extend(self.pending)
            self.pending=[]
        def metadata(self,operation):
            self.flush();self.disabled+=1
            try:operation()
            finally:self.flush();self.disabled-=1
        def save(self):self.flush();self.disk=dict(self.values)
    def test_preference_only_save_creates_no_user_undo_entry(self):
        s=self.Store();s.metadata(lambda:s.write('preferences','p1'));s.metadata(lambda:s.write('revision','r1'));s.save()
        self.assertEqual(s.undo,[]);self.assertEqual(s.disk['preferences'],'p1')
    def test_mixed_data_and_preference_save_records_only_native_data(self):
        s=self.Store();s.write('item','new');s.metadata(lambda:s.write('preferences','p1'));s.metadata(lambda:s.write('revision','r1'));s.save()
        self.assertEqual(s.undo,[('item','old','new')])
        self.assertEqual(s.disk,{'item':'new','preferences':'p1','revision':'r1'})
    def test_undo_keeps_current_preferences_and_changes_revision_for_other_readers(self):
        s=self.Store();s.write('item','new');s.metadata(lambda:s.write('preferences','p1'));s.metadata(lambda:s.write('revision','r1'));s.save()
        key,old,new=s.undo.pop();s.values[key]=old;s.redo.append((key,old,new))
        s.metadata(lambda:s.write('revision','r2'));s.save()
        self.assertEqual(s.disk,{'item':'old','preferences':'p1','revision':'r2'})
        self.assertEqual(s.redo,[('item','old','new')]);self.assertEqual(s.undo,[])
    def test_each_undo_redo_revision_differs_from_the_previous_commit(self):
        s=self.Store();seen=[s.disk['revision']]
        for value in ['r1','r2','r3','r4']:
            s.metadata(lambda:s.write('revision',value));s.save();self.assertNotEqual(seen[-1],s.disk['revision']);seen.append(value)
        self.assertEqual(s.undo,[])
    def test_throwing_metadata_operation_flushes_without_registering_and_reenables(self):
        s=self.Store();s.write('item','new')
        def failure():s.write('preferences','p1');raise ValueError('encode')
        with self.assertRaises(ValueError):s.metadata(failure)
        self.assertTrue(s.enabled);self.assertEqual(s.pending,[]);self.assertEqual(s.undo,[('item','old','new')])
    def test_preexisting_disable_scope_remains_disabled(self):
        s=self.Store();s.disabled=1;s.metadata(lambda:s.write('preferences','p1'))
        self.assertEqual(s.disabled,1);self.assertFalse(s.enabled);self.assertEqual(s.undo,[])
    def test_nested_metadata_scopes_balance_their_own_disables(self):
        s=self.Store()
        s.metadata(lambda:s.metadata(lambda:s.write('preferences','p1')))
        self.assertEqual(s.disabled,0);self.assertTrue(s.enabled);self.assertEqual(s.undo,[])

if __name__=='__main__':unittest.main()
