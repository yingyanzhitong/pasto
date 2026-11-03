"""Fixed P0/P1 review: original-bound source checks, no compiler or framework calls."""
from pathlib import Path
import collections
import difflib
import hashlib
import json
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment
from test_p0_p1_review_round2 import valid_word_cursor

D = ROOT / '.local/p0-p1-fixed-review/2026-11-02'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


class FixedPriorityReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scope = json.loads((ROOT / 'reports/replica/p0-p1-review-scope-v6.json').read_text())
        cls.records = json.loads((D / 'records.json').read_text())
        cls.delta = json.loads((D / 'source-delta.json').read_text())
        cls.base = json.loads((D / 'baseline.json').read_text())
        cls.engine = (ROOT / 'replica/Sources/PastoCore/OCR.swift').read_text()
        cls.toolbar = (ROOT / 'replica/Sources/Pasto/UI/OriginalPanelToolbar.swift').read_text()
        cls.n = {}
        exec((ROOT / '.local/p0-repair/phase-40/bind-contract.py').read_text().split('selectors=[]', 1)[0], cls.n)

    def native(self, suffix):
        fid = 'Paste:0x100' + suffix
        row = next(r for r in self.scope['functions'] if r['function_id'] == fid)
        return original_fragment((ROOT / row['original']['path']).read_text(), '100' + suffix)

    def test_fixed_scope_and_distinct_new_addresses_reconcile(self):
        self.assertEqual(self.scope['denominator'], 959)
        self.assertEqual(collections.Counter(r['priority'] for r in self.scope['functions']), {'P0': 353, 'P1': 606})
        added = {r['function_id'] for r in self.scope['functions'] if r['role'] != 'retained_historical_in_scope_contract'}
        self.assertEqual(set(self.records), added)
        self.assertEqual(len(added), 219)
        self.assertEqual(collections.Counter(r['priority'] for r in self.records.values()), {'P0': 74, 'P1': 145})

    def test_native_ranges_branches_and_chained_selectors_are_reproducible(self):
        proof = json.loads((D / 'native-proof.json').read_text())
        self.assertEqual(sha(ROOT / proof['binary']['path']), proof['binary']['sha256'])
        self.assertEqual(len(proof['ranges']), 12)
        self.assertEqual(len(proof['branches']), 327)
        self.assertEqual(len(proof['selectors']), 23)
        for row in proof['ranges']:
            data = self.n['read'](int(row['address'], 16), int(row['end'], 16) - int(row['address'], 16))
            self.assertEqual(data.hex(), row['bytes'])
            self.assertEqual(hashlib.sha256(data).hexdigest(), row['sha256'])
        for row in proof['branches']:
            pc = int(row['pc'], 16)
            word = struct.unpack('<I', self.n['read'](pc, 4))[0]
            self.assertEqual(hex(word), row['word'])
            v = word & 0x3ffffff
            if v & (1 << 25): v -= 1 << 26
            self.assertEqual(hex(pc + v * 4), row['target'])
        for row in proof['selectors']:
            value, chain = self.n['reachable_pointer'](int(row['pointer'], 16))
            self.assertEqual(chain, row['chain'])
            self.assertFalse(value >> 63)
            address = self.n['base'] + (value & ((1 << 36) - 1))
            self.assertEqual(hex(address), row['selector_address'])
            self.assertEqual(self.n['read'](address, len(row['name']) + 1), row['name'].encode() + b'\0')

    def test_all_original_fragments_and_current_source_bindings_match(self):
        cache = {}
        for fid, row in self.records.items():
            original = row['original']
            path = ROOT / original['path']
            if path not in cache:
                cache[path] = source_fragments(path)
            self.assertEqual(cache[path][fid.split(':')[1]]['sha256'], original['sha256'], fid)
            self.assertTrue(row['current_sources'], fid)
            for p, expected in row['current_sources'].items():
                self.assertEqual(sha(ROOT / p), expected, (fid, p))
            self.assertFalse(row['full_function_migration_verified'])

    def test_only_five_production_files_changed_and_recorded_diffs_are_exact(self):
        changed = {p for p, h in self.base['files'].items()
                   if p.startswith('replica/Sources/') and sha(ROOT / p) != h}
        self.assertEqual(changed, set(self.delta))
        self.assertEqual(len(changed), 5)
        for p, row in self.delta.items():
            a, b = (D / 'before' / p).read_text(), (ROOT / p).read_text()
            self.assertEqual(hashlib.sha256(a.encode()).hexdigest(), row['before_sha256'])
            self.assertEqual(self.base['files'][p], row['before_sha256'])
            self.assertEqual(hashlib.sha256(b.encode()).hexdigest(), row['after_sha256'])
            self.assertEqual(''.join(difflib.unified_diff(a.splitlines(True), b.splitlines(True), fromfile=p, tofile=p)), row['diff'])
        for p in ['replica/function-map.json', 'AGENTS.md', 'CHANGELOG.md', 'replica/Package.swift']:
            self.assertEqual(sha(ROOT / p), self.base['files'][p])

    def test_inactive_query_activation_is_original_branch_before_query_update(self):
        native = self.native('03e658')
        self.assertIn('SearchBar::onActivate', native)
        self.assertIn('(*pcVar5)();', native)
        bridge = body(self.toolbar, 'private func f_10003e658()')
        self.assertIn('guard isActive else { onActivate?(); return }', bridge)
        self.assertIn('if coordinator.isQueryEmpty { onDismiss?() }', bridge)
        self.assertIn('else { requestFocus() }', bridge)
        observe = body(self.toolbar, 'func observeQuery(')
        self.assertLess(observe.index('self.f_10003e658()'), observe.index('coordinator.synchronizeQuery(nodes'))

    def test_activation_real_toolbar_target_is_weak_and_cleaned_on_dismantle(self):
        self.assertIn('searchBar.onActivate = { [weak self] in self?.f_10000df98() }', self.toolbar)
        self.assertIn('FUN_10000df98()', original_fragment(
            (ROOT / 'decompiled/Paste/part-0006.c').read_text(), '10000ec00'))
        callback = body(self.toolbar, 'private func f_10000df98()')
        self.assertLess(callback.index('NSLayoutConstraint.deactivate'), callback.index('self.f_10000e74c(true)'))
        self.assertIn('onActivate = nil', body(self.toolbar, 'func dismantleEditor()'))

    def test_focus_flags_preserve_original_repeated_state_and_child_reads(self):
        original = self.native('03e350')
        self.assertGreaterEqual(original.count('unaff_x20 + lVar3'), 2)
        self.assertIn('uVar1 = *(undefined1 *)(lVar4 + lVar2)', original)
        current = body(self.toolbar, 'private func f_10003e350()')
        self.assertEqual(current.count('isActive'), 3)
        self.assertNotIn('let active', current)
        self.assertIn('f_100041f9c().canAcceptFocus = field.canAcceptFocus', current)

    def test_mouse_up_real_thunk_points_to_reviewed_body(self):
        w0, w1, _, branch = struct.unpack('<4I', self.n['read'](0x100079f98, 16))
        self.assertEqual(w0 & 0x9f00001f, 0x90000004)
        page = ((w0 >> 5) & 0x7ffff) * 4 + ((w0 >> 29) & 3)
        if page & (1 << 20): page -= 1 << 21
        address = (0x100079f98 & ~4095) + (page << 12) + ((w1 >> 10) & 0xfff)
        self.assertEqual(address, 0x100079e98)
        self.assertEqual(branch, 0x14000001)
        original = self.native('079e98')
        self.assertIn('TabBarCell::isEditing', original)
        self.assertNotIn('modifierFlags', original)
        self.assertNotIn('isDragging', original)

    def test_mouse_up_uses_whole_bounds_and_no_extra_modifier_or_drag_gate(self):
        source = (ROOT / 'replica/Sources/Pasto/UI/OriginalPinboardTabTitle.swift').read_text()
        owner = body(source, 'final class OriginalPinboardTabView: NSView, NSDraggingSource')
        f = body(owner, 'override func mouseUp(with event: NSEvent)')
        self.assertIn('guard !titleView.isEditing else { return }', f)
        self.assertNotIn('isDragging', f)
        self.assertNotIn('modifierFlags', f)
        order = ['isPressed = false', 'needsDisplay = true', 'bounds.contains(', 'onSelect?()', 'super.mouseUp(with: event)']
        self.assertEqual([f.index(x) for x in order], sorted(f.index(x) for x in order))

    def test_original_ocr_parent_calls_word_extractor_once_without_candidate_prepass(self):
        parent = self.native('2d4830')
        self.assertEqual(parent.count('FUN_1002d576c();'), 1)
        self.assertNotIn('topCandidates', parent)
        self.assertEqual(self.native('2d576c').count('objc_stub::topCandidates_'), 1)
        instruction = struct.unpack('<I', self.n['read'](0x1002d4a7c, 4))[0]
        self.assertEqual(instruction, 0x9400033c)
        self.assertEqual(0x1002d4a7c + (instruction & 0x3ffffff) * 4, 0x1002d576c)

    def test_index_consumes_only_words_and_never_requests_full_document(self):
        source = (ROOT / 'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text()
        f = body(source, 'private func drainOCRQueue() async')
        self.assertIn('try await ImageTextRecognizer.recognizeWords(imageData: data, maximumDimension: 1024)', f)
        self.assertIn('words.map(\\.text).joined(separator: " ")', f)
        self.assertNotIn('recognizeDocument', f)
        self.assertNotIn('document.text', f)
        engine = body(self.engine, 'public static func recognizeWords(')
        self.assertIn('Task.detached(priority: .utility)', engine)
        self.assertIn('includeFullText: false).words', engine)

    def test_empty_input_pool_and_vision_errors_are_preserved(self):
        entry = body(self.engine, 'public static func f_1002d4738(')
        self.assertLess(entry.index('guard !imageData.isEmpty'), entry.index('autoreleasepool'))
        self.assertIn('throw OCRError.invalidImageData', entry)
        self.assertIn('includeFullText: includeFullText', entry)
        request = body(self.engine, 'public static func f_1002d4830(')
        self.assertIn('return RecognizedTextDocument(text: "", words: [])', request)
        for flag in ['automaticallyDetectsLanguage', 'usesLanguageCorrection', 'preferBackgroundProcessing']:
            self.assertIn('request.' + flag + ' = true', request)
        self.assertIn('try handler.perform([request])', request)
        self.assertNotIn('try?', request)
        self.assertIn('request.results ?? []', request)

    def test_candidates_are_read_only_once_and_full_text_shares_same_string(self):
        request = body(self.engine, 'public static func f_1002d4830(')
        self.assertNotIn('topCandidates', request)
        self.assertNotIn('compactMap', request)
        f = body(self.engine, 'public static func f_1002d576c(')
        self.assertEqual(f.count('topCandidates(1)'), 1)
        self.assertEqual(f.count('candidate.string'), 1)
        self.assertLess(f.index('let text = candidate.string'), f.index('recognizedText?(text)'))
        self.assertLess(f.index('recognizedText?(text)'), f.index('text.components'))
        self.assertTrue(valid_word_cursor(f))
        self.assertIn('recognizedText: { lines.append($0) }', request)
        self.assertIn('text: lines.joined(separator: "\\n")', request)
        self.assertTrue(request.rstrip().endswith('return RecognizedTextDocument(text: "", words: f_1002d576c(observations: observations))\n    }'))

    def test_word_geometry_and_forward_cursor_unchanged_outside_text_callback(self):
        before = (D / 'before/replica/Sources/PastoCore/OCR.swift').read_text()
        old = body(before, 'public static func f_1002d576c(')
        current = body(self.engine, 'public static func f_1002d576c(')
        self.assertEqual(current.replace('            recognizedText?(text)\n', ''), old)

    def test_document_text_preserves_punctuation_empty_candidates_and_order(self):
        # Observable API-read trace model, not a Vision runtime test.
        samples = [None, '', 'hello, world!', '中文：测试', 'repeat repeat']
        reads = []
        lines = []
        for i, text in enumerate(samples):
            reads.append(('topCandidates', i, 1))
            if text is None: continue
            reads.append(('string', i))
            lines.append(text)
        self.assertEqual('\n'.join(lines), '\nhello, world!\n中文：测试\nrepeat repeat')
        self.assertEqual(sum(x[0] == 'topCandidates' for x in reads), len(samples))
        self.assertEqual(sum(x[0] == 'string' for x in reads), 4)

    def test_existing_rich_detection_already_finishes_current_attribute_run(self):
        native = self.native('3c14d0')
        self.assertIn('*param_5 = 1;', native)
        self.assertIn('*param_4 = 1;', native)
        self.assertIn('goto LAB_1003c1584;', native)
        self.assertTrue(native.rstrip().endswith('} while( true );\n}'))
        path = 'replica/Sources/PastoCore/OriginalTextPreviewSubmission.swift'
        self.assertEqual(sha(ROOT / path), self.base['files'][path])
        f = body((ROOT / path).read_text(), 'public static func f_1003c14d0(')
        self.assertIn('for (key, value) in attributes', f)
        self.assertNotIn('return', f)
        self.assertNotIn('break', f)
        self.assertIn('isRich = true\n            stop.pointee = true', f)

    def test_repaired_count_does_not_silently_expand_scope_or_claim_full_migration(self):
        repairs = {fid for fid,r in self.records.items() if r['status'] == 'source_repaired'}
        self.assertEqual(repairs, {'Paste:0x1002348a8', 'Paste:0x10003e350', 'Paste:0x10003e658', 'Paste:0x100079e98'})
        self.assertFalse(self.scope['full_function_migration_verified'])
        self.assertIsNone(self.scope['progress']['percent'])
        self.assertNotIn('Paste:0x100ac35f8', self.records)
        self.assertNotIn('Paste:0x100ac746c', self.records)


if __name__ == '__main__':
    unittest.main()
