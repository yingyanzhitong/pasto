"""Original content-load warning gates; source/Mach-O checks, no framework execution."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from content_load_diagnostic_scope_contract import CHANGES,pre_content_load_diagnostic
from empty_data_diagnostic_scope_contract import pre_empty_data_diagnostic
class ContentLoadDiagnosticContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase=ROOT/'.local/p0-repair/phase-132';cls.p=json.loads((cls.phase/'content-load-diagnostic-contract.json').read_text());cls.base=json.loads((cls.phase/'baseline.json').read_text());cls.s=pre_empty_data_diagnostic((ROOT/cls.p['current_source']).read_text());cls.read=body(cls.s,'private func read<T>');cls.n={};exec((ROOT/cls.p['decoder']['path']).read_text().split("idx={r['address']",1)[0],cls.n)
    def order(self,s,seq):
        i=0
        for t in seq:i=s.index(t,i)+len(t)
    def test_eleven_original_fragments_and_binary_and_decoder_bound(self):
        self.assertEqual(len(self.p['original_fragments']),11)
        for r in self.p['original_fragments']:self.assertEqual(source_fragments(ROOT/r['path'])[r['address']]['sha256'],r['sha256'])
        for k in ['binary','decoder']:
            r=self.p[k];self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_actual_named_receiver_capture_chain_and_warning_level_words(self):
        for r in self.p['ARM_words']:self.assertEqual(self.n['read'](int(r['address'],16),4).hex(),r['bytes'])
        self.assertEqual(self.n['read'](0x100371e5c,4).hex(),'166102a9')
        self.assertEqual(self.n['read'](0x1000d4e04,4).hex(),'40008052')
    def test_name_and_two_messages_are_real_original_literals(self):
        for r in self.p['literals']:self.assertEqual(self.n['read'](int(r['address'],16),100).split(b'\0')[0].decode(),r['value'])
        for i in [0,1,2]:self.assertIn(self.p['literals'][i]['value'],self.s)
    def test_receiver_retained_by_reader_and_only_content_passes_it(self):
        self.assertIn('private let contentDiagnostics = OriginalNamedDiagnostic.f_1000d4624(name: "init(_:coordinator:)")',self.s)
        self.assertIn('read(contentDiagnostics: contentDiagnostics)',body(self.s,'func content()'))
        self.assertNotIn('contentDiagnostics',body(self.s,'func imageData()'))
        self.assertIn('contentDiagnostics: OriginalNamedDiagnostic? = nil,',self.s)
    def test_fetch_warning_is_only_inner_fetch_error_and_preserves_nil(self):
        self.order(self.read,['OriginalObjCExceptionBridge.withResult','let object: NSManagedObject','do { object = try context.existingObject(with: objectID) }','catch {','guard let contentDiagnostics else { throw error }','contentDiagnostics.f_1000d468c().f_1000d4df0("Failed to load item content: \\(error.localizedDescription)")','return nil','guard object.entity.name'])
        self.assertNotIn('f_1000d4e0c',self.read)
    def test_wrong_type_warning_precedes_nil_and_is_separate_from_deleted_data_guard(self):
        bad=body(self.read,'guard object.entity.name == "Item" else')
        self.order(bad,['contentDiagnostics?.f_1000d468c().f_1000d4df0("Failed to load item for content indexing: object not found")','return nil'])
        self.order(self.read,['guard object.entity.name','guard !object.isDeleted','object.value(forKey: "data")','readRepresentations','return try project(object, items)'])
    def test_images_and_outer_projection_errors_keep_existing_generic_error_tail(self):
        self.assertIn('guard let contentDiagnostics else { throw error }',self.read)
        old=body((self.phase/'before'/self.p['current_source']).read_text(),'private func read<T>')
        self.assertEqual(self.read[self.read.index('        } catch {\n            logger.error'):],old[old.index('        } catch {\n            logger.error'):])
    def test_raw_decoder_typed_projection_and_private_queue_are_not_reimplemented(self):
        self.assertEqual(self.read.count('NSManagedObjectContext('),1);self.assertIn('context.performAndWait',self.read)
        self.assertEqual(self.read.count('ClipboardItemDataPersistence.readRepresentations('),1)
        for t in ['Task {','DispatchQueue','context.save','context.reset','telemetry']:self.assertNotIn(t,self.read)
    def test_edit_commit_cancellation_and_native_projection_methods_reused_unchanged(self):
        self.assertEqual(len(self.p['unchanged_methods']),6)
        for r in self.p['unchanged_methods']:self.assertEqual(hashlib.sha256(body(pre_empty_data_diagnostic((ROOT/r['path']).read_text()),r['symbol']).encode()).hexdigest(),r['sha256'])
        view=(ROOT/'replica/Sources/PastoCore/OriginalItemPreviewView.swift').read_text()
        self.order(body(view,'public func f_10007c080()'),['editable.commitPreviewEditing()','previewHeader.isHidden = false','editorHeader.isHidden = true','onEditingStateChanged?(false)','onEndEditing?()'])
    def test_exact_four_hunks_reverse_all247_current_sources_to_frozen_user_baseline(self):
        self.assertEqual(len(CHANGES),4)
        for p,h in self.base['production'].items():
            b=(ROOT/p).read_bytes();b=pre_content_load_diagnostic(b.decode()).encode()if p.endswith('.swift')else b;self.assertEqual(hashlib.sha256(b).hexdigest(),h)
    def test_current_actual_source_digest_and_single_file_change(self):
        self.assertEqual(hashlib.sha256(self.s.encode()).hexdigest(),self.p['current_source_sha256'])
        diff=[p for p,h in self.base['production'].items()if hashlib.sha256(pre_empty_data_diagnostic((ROOT/p).read_text()).encode()if p.endswith('.swift')else(ROOT/p).read_bytes()).hexdigest()!=h];self.assertEqual(diff,[self.p['current_source']])
    def test_missing_empty_diagnostics_and_complete_function_are_not_marked_passed(self):
        self.assertEqual(len(self.p['remaining']),4);self.assertIn('confirmed missing',self.p['remaining'][0]);self.assertIn('not fixed',self.p['remaining'][0]);self.assertFalse(self.p['runtime_executed']);self.assertFalse(self.p['full_function_migration_verified'])
if __name__=='__main__':unittest.main()
