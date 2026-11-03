"""Independent setter and its actual local consumer; no AppKit execution."""
from pathlib import Path
import hashlib,json,subprocess,sys,unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts/tests')]
from test_offline_p0_contracts import body
D=ROOT/'.local/p0-p1-parent-review/2026-11-03-independent-text-setter'
CORE='replica/Sources/PastoCore/OriginalSearchTextValue.swift'
UI='replica/Sources/Pasto/UI/ReplicaLinkPreviewContent.swift'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

class IndependentTextSetter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proof=json.loads((D/'contract.json').read_text())
        cls.base=json.loads((D/'baseline.json').read_text())
        cls.core=(ROOT/CORE).read_text();cls.ui=(ROOT/UI).read_text()
        cls.oldcore=(D/'before'/CORE).read_text();cls.oldui=(D/'before'/UI).read_text()
    def test_original_evidence_and_current_sources_are_fresh(self):
        for p,h in {**self.proof['source_inputs'],**self.proof['current_sources']}.items():
            self.assertEqual(sha(ROOT/p),h,p)
    def test_existing_plain_setter_is_reused_with_same_side_effect_and_no_return_value(self):
        self.assertIn('@MainActor func f_1000f733c(_ value: String) {',self.core)
        setter=body(self.core,'func f_1000f733c(')
        self.assertEqual(setter,body(self.oldcore,'func f_1000f733c('))
        self.assertEqual(setter.strip(),'{\n        string = value\n    }')
        self.assertEqual(body(self.core,'func f_1000f7254('),body(self.oldcore,'func f_1000f7254('))
    def test_real_link_editor_uses_setter_before_display_validation_and_focus(self):
        s=body(self.ui,'func beginPreviewEditing()')
        calls=['textView.f_1000f733c(currentURL()?.absoluteString ?? "")',
               'showContent(textView)','updateCanCommit()','window?.makeFirstResponder(textView)']
        positions=[s.index(t)for t in calls];self.assertEqual(positions,sorted(positions))
        self.assertIn('private let textView = NSTextView()',self.ui)
        self.assertIn('@MainActor\nfinal class ReplicaLinkPreviewContent',self.ui)
        old=body(self.oldui,'func beginPreviewEditing()')
        self.assertEqual(s,old.replace('textView.string = currentURL()?.absoluteString ?? ""',calls[0],1))
    def test_url_resolution_commit_and_error_handling_unchanged(self):
        for name in ['func cancelPreviewEditing()','func commitPreviewEditing()',
                     'static func normalizedURL(','private func currentURL()',
                     'private func updateCanCommit()','private func updateMetadata(']:
            self.assertEqual(body(self.ui,name),body(self.oldui,name),name)
    def test_only_one_callsite_and_two_documentation_lines_changed(self):
        self.assertEqual(self.ui,self.oldui.replace('textView.string = currentURL()?.absoluteString ?? ""',
                         'textView.f_1000f733c(currentURL()?.absoluteString ?? "")',1))
        lines=self.core.splitlines(keepends=True)
        self.assertEqual(''.join(x for x in lines if not x.lstrip().startswith('///')),self.oldcore)
        test='scripts/tests/test_p1_repair_native_link_creation.py'
        expected=(D/'before'/test).read_text().replace('textView.string = currentURL()?.absoluteString',
                    'textView.f_1000f733c(currentURL()?.absoluteString',1)
        self.assertEqual((ROOT/test).read_text(),expected)
        changed={p for p,h in self.base['files'].items()if sha(ROOT/p)!=h}
        self.assertEqual(changed,{CORE,UI,test})
        self.assertEqual(len([p for p in(ROOT/'replica/Sources').rglob('*')if p.is_file()]),249)
        self.assertEqual(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),self.base['head'])
    def test_resolution_is_user_authorized_adaptation_not_a_claim_of_recovered_symbols(self):
        self.assertEqual(self.proof['resolution'],'user_authorized_independent_implementation')
        self.assertTrue(self.proof['existing_body_reused'])
        for key in ['original_declaration_recovered','original_consumer_binding_recovered',
                    'full_original_function_equivalence_verified','compiled','framework_executed','network_used']:
            self.assertFalse(self.proof[key],key)

if __name__=='__main__':unittest.main()
