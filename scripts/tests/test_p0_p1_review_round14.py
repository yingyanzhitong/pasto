"""P0/P1 boundary admissions and finite source/ARM contract regression guards."""
import hashlib
import json
import re
import struct
import unittest
from collections import Counter

from test_offline_p0_contracts import ROOT, body
from test_p0_p1_review_round2 import digest, fragment


class P0P1ReviewRound14(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((ROOT / 'reports/replica/p0-p1-review-round14.json').read_text())
        cls.prior = json.loads((ROOT / 'reports/replica/p0-p1-review-round13.json').read_text())
        cls.scope = json.loads((ROOT / cls.report['scope_manifest']).read_text())
        cls.old_scope = json.loads((ROOT / cls.prior['scope_manifest']).read_text())
        cls.rows = {r['function_id']:r for r in cls.report['records']}
        cls.proof = json.loads((ROOT / cls.report['static_proof']['path']).read_text())
        cls.binary = (ROOT / cls.proof['binary_path']).read_bytes()
        cls.boundary = json.loads((ROOT / cls.report['boundary_decisions']['path']).read_text())

    def word(self, address):
        for segment in self.proof['segments']:
            if segment['vmaddr'] <= address < segment['vmaddr'] + segment['filesize']:
                return struct.unpack_from('<I', self.binary, segment['fileoff'] + address - segment['vmaddr'])[0]
        self.fail(hex(address))

    def branch(self, address):
        value = self.word(address)
        self.assertEqual(value >> 26, 0b100101)
        immediate = value & 0x3ffffff
        return address + (immediate - (1 << 26) if immediate & (1 << 25) else immediate) * 4

    def test_candidate_decisions_cover_all_remaining_239_once_and_scope_is_superset(self):
        candidates = json.loads((ROOT / 'reports/replica/p0-p1-review-boundary-candidates-v1.json').read_text())
        old_ids = {r['function_id'] for r in self.old_scope['functions']}
        expected = {r['function_id'] for r in candidates['records']} - old_ids
        actual = [r['function_id'] for r in self.boundary['records']]
        self.assertEqual(Counter(actual), Counter({fid:1 for fid in expected}))
        self.assertEqual(len(actual), 239)
        decisions = {r['function_id']:r for r in self.boundary['records']}
        added = {fid for fid, r in decisions.items() if r['admission_decision'] == 'admit'}
        self.assertEqual(set(self.scope['expansion']['added_function_ids']), added)
        self.assertEqual({r['function_id'] for r in self.scope['functions']}, old_ids | added)
        self.assertFalse(old_ids & added)
        self.assertEqual(self.scope['predecessor']['sha256'], digest(self.scope['predecessor']['path']))
        self.assertTrue(self.scope['provisional'])
        self.assertFalse(self.scope['full_original_priority_classification_complete'])
        self.assertIsNone(self.report['full_priority_completion_percent'])
        self.assertFalse({'Paste:0x100ac35f8','Paste:0x100ac746c'} & set(self.rows))
        self.assertTrue(all(set(r['priorities']) <= {'P0','P1'} for r in self.scope['functions']))

    def test_new_and_revised_records_bind_complete_originals_and_literal_current_consumers(self):
        selected = set(self.report['round_delta']['reviewed_new_function_ids']) | set(self.report['round_delta']['revised_existing_function_ids'])
        self.assertTrue(selected)
        for fid in selected:
            row = self.rows[fid]
            references = [dict(row['original'], function_id=fid)] + row.get('supporting_original_fragments', [])
            for ref in references:
                address = ref.get('address') or ref['function_id'].split(':')[1]
                self.assertEqual(hashlib.sha256(fragment(address, ref['path']).encode()).hexdigest(), ref['sha256'], (fid,address))
            self.assertFalse(row['full_function_migration_verified'])
            self.assertTrue(row['current_references'])
            for ref in row['current_references']:
                self.assertEqual(digest(ref['path']), ref['sha256'])
                self.assertIn(ref['symbol'], (ROOT / ref['path']).read_text(), fid)
        revised = set(self.report['round_delta']['revised_existing_function_ids'])
        for previous in self.prior['records']:
            if previous['function_id'] not in revised: self.assertEqual(previous, self.rows[previous['function_id']])

    def test_all_evidence_inputs_scope_proof_and_decision_hashes_are_current(self):
        for path, sha in self.report['source_inputs'].items(): self.assertEqual(digest(path), sha, path)
        for item in [self.report['static_proof'], self.report['boundary_decisions']]:
            self.assertEqual(digest(item['path']), item['sha256'])
        self.assertEqual(digest(self.report['scope_manifest']), self.report['scope_manifest_sha256'])
        self.assertEqual(hashlib.sha256(self.binary).hexdigest(), self.proof['binary_sha256'])
        for field in ['history_only_refresh', 'valid_list_context_delivery', 'attachment_geometry', 'archive_error_to_optional_none']:
            for instruction in self.proof[field]:
                self.assertEqual(self.word(int(instruction['address'],16)), int(instruction['word'],16))

    def test_refresh_is_gated_by_history_type_and_orphan_removal_has_a_real_consumer(self):
        self.assertEqual(self.branch(0x100362f34), 0x100325110)
        # TBZ w0,bit0 -> epilogue, bypassing the bulk refresh path for non-History.
        instruction = self.word(0x100362f38)
        self.assertEqual(instruction & 0xfff8001f, 0x36000000)
        immediate = (instruction >> 5) & 0x3fff
        self.assertEqual(0x100362f38 + (immediate - 0x4000 if immediate & 0x2000 else immediate) * 4, 0x100362fe0)
        self.assertEqual(self.branch(0x100362ee0), 0x1003646ec)
        row = self.rows['Paste:0x10036299c']
        self.assertEqual(row['status'], 'local_contract_consistent')
        original = fragment('0x10036299c', row['original']['path'])
        self.assertIn('objc_stub::setList_((ID)self,0)', original)
        self.assertIn('FUN_1003646ec(puVar9)', original)
        current = body((ROOT/'replica/Sources/PastoCore/ClipboardStore.swift').read_text(), 'public func removePinboard(id: UUID) throws')
        self.assertIn('state.items[i].pinboardIDs.remove(id)', current)
        self.assertIn('!$0.isInHistory && $0.pinboardIDs.isEmpty', current)

    def test_valid_list_tag_return_is_delivered_to_model_and_invalid_domain_stays_excluded(self):
        self.assertEqual(self.branch(0x10007e12c), 0x1003b80f0)
        self.assertEqual(self.word(0x10007e130), 0xaa0003f4)  # retain returned tagged value in x20
        self.assertEqual(self.word(0x10007e14c), 0xaa1403e0)  # deliver that value in x0
        self.assertEqual(self.branch(0x10007e154), 0x100052734)
        self.assertEqual(self.rows['Paste:0x1003b80f0']['status'], 'local_contract_consistent')
        self.assertIn('invalid_native_raw_type_fallback', self.rows['Paste:0x1003b80f0']['coverage_boundaries']['not_verified'])
        self.assertEqual(self.rows['Paste:0x10007d0e0']['shared_difference_origin'], 'Paste:0x1002e00a0')
        self.assertEqual(self.rows['Paste:0x1002fc0ec']['status'], 'unclosed')

    def test_original_clear_icon_has_the_same_fallback_not_a_false_failure_difference(self):
        for name in ['primary', 'fallback']:
            value = self.proof['clear_image_names'][name]
            self.assertEqual(self.binary[value['file_offset']:value['file_offset']+value['length']].decode(), value['value'])
        self.assertEqual(self.proof['clear_image_names']['fallback']['value'], 'questionmark.square')
        row = self.rows['Paste:0x100042090']
        self.assertEqual(row['status'], 'local_contract_consistent')
        current = body((ROOT/'replica/Sources/PastoCore/OriginalSearchInputView.swift').read_text(), 'public func f_10004212c(_ button: NSButton)')
        self.assertEqual(current.count('systemSymbolName: "xmark.circle.fill"'), 2)
        self.assertIn('systemSymbolName: "questionmark.square", accessibilityDescription: nil)!', current)
        self.assertIn('FUN_1000f653c(0xd000000000000013,0x8000000100d8de20)', fragment('0x10004212c', 'decompiled/Paste/part-0024.c'))

    def test_archive_failure_releases_error_clears_error_register_and_returns_optional_none(self):
        self.assertEqual(self.branch(0x10036cdf4), 0x100bfc708)
        for address, word in [(0x10036cdf8,0xd2800016),(0x10036cdfc,0xd2800014),
                              (0x10036ce00,0xd2fe0017),(0x10036ce04,0xa9005e76),(0x10036ce20,0xaa1403f5)]:
            self.assertEqual(self.word(address), word)
        self.assertEqual(self.rows['Paste:0x10036cd4c']['status'], 'local_contract_consistent')
        current = (ROOT/'replica/Sources/PastoCore/OriginalSearchHistory.swift').read_text()
        self.assertIn('token.flatMap { try? NSKeyedArchiver.archivedData', current)
        self.assertIn('requiringSecureCoding: true', current)
        # A willThrow diagnostic alone must not be treated as propagation.
        original = fragment('0x10036cd4c', self.rows['Paste:0x10036cd4c']['original']['path'])
        self.assertIn('_swift_errorRelease(uVar2)', original)
        self.assertIn('0xf000000000000000', original)

    def test_focus_ring_difference_uses_local_sdk_enum_and_attachment_geometry_uses_actual_formula(self):
        enum = self.proof['focus_ring_enum'];text = (ROOT/enum['path']).read_text()
        self.assertEqual(digest(enum['path']), enum['sha256'])
        self.assertIn('NSFocusRingTypeNone = 1', text)
        self.assertIn('NSFocusRingTypeExterior = 2', text)
        self.assertEqual(self.rows['Paste:0x100042edc']['status'], 'difference_confirmed')
        current = (ROOT/'.local/p0-repair/phase-39/before/replica/Sources/PastoCore/OriginalSearchTextScroller.swift').read_text()
        self.assertIn('focusRingType = .none', current)
        self.assertEqual(self.word(0x1002f5dc0), 0x1e7a1000)  # FMOV d0,-0.25
        self.assertEqual(self.word(0x1002f5dc4), 0x1e600921)  # FMUL d1,d9,d0
        current = body((ROOT/'replica/Sources/PastoCore/OriginalSearchFilterView.swift').read_text(), 'public func f_1002f5d74() -> CGRect')
        self.assertIn('guard let view else { return .zero }', current)
        self.assertIn('CGRect(x: 0, y: size.height * -0.25, width: size.width, height: size.height)', current)

    def test_progress_counts_conclusions_not_admissions_and_production_is_unchanged(self):
        counts = Counter(r['status'] for r in self.rows.values())
        resolved = sum(counts[s] for s in ['local_contract_consistent','difference_confirmed','user_adaptation_confirmed'])
        self.assertEqual(dict(counts), self.report['outcomes'])
        self.assertEqual(self.report['comparison_denominator'], len(self.rows))
        self.assertEqual(self.report['resolved_review_records'], resolved)
        self.assertEqual(self.report['resolved_comparison_percent'], round(resolved/len(self.rows)*100,2))
        self.assertEqual(self.report['round_delta']['existing_newly_resolved'], 4)
        self.assertEqual(self.rows['Paste:0x1000f733c']['status'], 'unclosed')
        before = json.loads((ROOT/'.local/p0-review/production-before.json').read_text())
        actual = {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'replica/Sources').rglob('*') if p.is_file()}
        self.assertEqual(actual, before)
        self.assertEqual(digest('replica/function-map.json'), self.report['function_map_sha256'])
        for flag in ['production_source_edited','compiled','application_executed','committed','pushed']:
            self.assertFalse(self.report[flag])


if __name__ == '__main__': unittest.main()
