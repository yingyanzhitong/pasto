"""Static review and source guards; never compiles or runs either application."""
import hashlib
import json
import struct
import subprocess
import unittest
from collections import Counter

from test_offline_p0_contracts import ROOT, body


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def fragment(address, path):
    text = (ROOT / path).read_text()
    start = text.index('/* Address: ' + address + ' |')
    end = text.find('/* Address:', start + 1)
    return text[start:end if end != -1 else None].rstrip() + '\n'


def valid_word_cursor(source):
    required = ['range: cursor..<text.endIndex', 'else { break }',
                'try? candidate.boundingBox(for: range)', 'words.append(',
                'confidence: candidate.confidence', 'boundingBox: box?.boundingBox',
                'cursor = range.upperBound']
    return all(value in source for value in required) and source.index('words.append(') < source.index('cursor = range.upperBound')


class P0P1ReviewRound2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((ROOT / 'reports/replica/p0-p1-review-round2.json').read_text())
        cls.prior = json.loads((ROOT / 'reports/replica/p0-p1-review-round1.json').read_text())
        cls.scope = json.loads((ROOT / cls.report['scope_manifest']).read_text())
        cls.rows = {r['function_id']: r for r in cls.report['records']}
        cls.proof = json.loads((ROOT / cls.report['static_proof']['path']).read_text())

    def test_denominator_is_unchanged_and_all_records_have_only_one_address(self):
        report = self.report
        self.assertEqual(set(self.rows), {r['function_id'] for r in self.scope['functions']})
        self.assertEqual(len(self.rows), len(report['records']))
        self.assertEqual(report['comparison_denominator'], self.prior['comparison_denominator'])
        self.assertEqual(report['comparison_denominator'], len(self.rows))
        self.assertEqual(report['not_yet_reviewed'], 0)
        counts = Counter(r['status'] for r in self.rows.values())
        self.assertEqual(dict(counts), report['outcomes'])
        resolved = len(self.rows) - counts['unclosed']
        self.assertEqual(resolved, report['resolved_review_records'])
        self.assertEqual(report['resolved_comparison_percent'], round(resolved / len(self.rows) * 100, 2))
        self.assertEqual(report['p0_component']['resolved'] + report['p1_additional_component']['resolved'], resolved)
        self.assertTrue(report['scope_provisional'])
        self.assertIsNone(report['full_priority_completion_percent'])

    def test_delta_only_replaces_unclosed_or_adds_previously_pending_records(self):
        prior = {r['function_id']: r for r in self.prior['records']}
        delta = self.report['round_delta']
        changed = set(delta['reviewed_function_ids'])
        self.assertEqual(len(changed), delta['reviewed_addresses'])
        self.assertEqual(len(changed - set(prior)), delta['previously_pending'])
        for fid, row in self.rows.items():
            if fid not in changed:
                self.assertEqual(row, prior[fid])
            elif fid in prior:
                self.assertEqual(prior[fid]['status'], 'unclosed')
                self.assertEqual(row['previous_status'], 'unclosed')
            else:
                self.assertEqual(row['previous_status'], 'not_yet_reviewed')
            self.assertFalse(row['full_function_migration_verified'])

    def test_all_new_original_and_support_fragments_are_bound_to_exact_bodies(self):
        for fid in self.report['round_delta']['reviewed_function_ids']:
            row = self.rows[fid]
            proofs = [dict(row['original'], function_id=fid)] + row.get('supporting_original_fragments', [])
            for proof in proofs:
                address = proof.get('address') or proof['function_id'].split(':')[1]
                value = fragment(address, proof['path'])
                self.assertEqual(hashlib.sha256(value.encode()).hexdigest(), proof['sha256'], address)
            for ref in row['current_references']:
                self.assertEqual(digest(ref['path']), ref['sha256'])
                self.assertEqual(ref['symbol'] in (ROOT / ref['path']).read_text(), ref['present'])

    def test_inputs_stay_immutable_and_references_are_not_counted_as_full_migration(self):
        report = self.report
        proofs = dict(report['source_inputs'])
        proofs[report['scope_manifest']] = report['scope_manifest_sha256']
        proofs[report['static_proof']['path']] = report['static_proof']['sha256']
        for path, value in proofs.items():
            self.assertEqual(digest(path), value, path)
        for row in report['records']:
            self.assertFalse(row['full_function_migration_verified'])
            if row['status'] == 'local_contract_consistent':
                self.assertTrue(row['current_references'])
                self.assertTrue(all(ref['present'] for ref in row['current_references']))

    def test_static_symbol_getters_decode_real_addresses_and_string_values(self):
        proof = self.proof
        binary = (ROOT / proof['binary_path']).read_bytes()
        self.assertEqual(hashlib.sha256(binary).hexdigest(), proof['binary_sha256'])
        source = (ROOT / 'replica/Sources/PastoCore/OriginalSearchFilterSymbols.swift').read_text()
        self.assertEqual(len(proof['symbol_slots']), 11)
        for row in proof['symbol_slots']:
            for part in [row['instructions'], row['storage'], row['long_string_bytes']]:
                if part is None:
                    continue
                data = bytes.fromhex(part['bytes'])
                offset = part['slice_file_offset']
                self.assertEqual(binary[offset:offset + len(data)], data)
            adrp, add, ret = struct.unpack('<III', bytes.fromhex(row['instructions']['bytes']))
            self.assertEqual(adrp & 0x9f00001f, 0x90000000)
            self.assertEqual(add & 0xffc003ff, 0x91000000)
            self.assertEqual(ret, 0xd65f03c0)
            immediate = ((adrp >> 29) & 3) | (((adrp >> 5) & 0x7ffff) << 2)
            if immediate & (1 << 20):
                immediate -= 1 << 21
            page = int(row['instructions']['address'], 16) & ~0xfff
            target = page + (immediate << 12) + ((add >> 10) & 0xfff)
            self.assertEqual(target, int(row['storage']['address'], 16))
            lo, hi = struct.unpack('<QQ', bytes.fromhex(row['storage']['bytes']))
            if hi & (1 << 61):
                value = bytes.fromhex(row['storage']['bytes'])[:(hi >> 56) & 15].decode()
            else:
                data = row['long_string_bytes']
                self.assertEqual(int(data['address'], 16), 0x100000000 + (hi & ((1 << 36) - 1)) + 32)
                self.assertEqual(len(bytes.fromhex(data['bytes'])), lo & ((1 << 48) - 1))
                value = bytes.fromhex(data['bytes']).decode()
            self.assertEqual(value, row['value'])
            self.assertIn('"' + value + '"', source)
        self.assertIn('.pointee', source)

    def test_license_name_is_a_relative_metadata_pointer_not_a_guessed_gate(self):
        proof = self.proof['license_metadata']
        relative = proof['descriptor_name_relative']
        name = proof['name_bytes']
        binary = (ROOT / self.proof['binary_path']).read_bytes()
        for part in [relative, name]:
            data = bytes.fromhex(part['bytes'])
            offset = part['slice_file_offset']
            self.assertEqual(binary[offset:offset + len(data)], data)
        displacement, = struct.unpack('<i', bytes.fromhex(relative['bytes']))
        self.assertEqual(int(relative['address'], 16) + displacement, int(name['address'], 16))
        self.assertEqual(bytes.fromhex(name['bytes']), b'License\0')
        prior = self.proof['paywall_prior_report']
        self.assertEqual(digest(prior['path']), prior['sha256'])
        for address in ['0x1003b936c', '0x100066068']:
            self.assertEqual(self.rows['Paste:' + address]['status'], 'user_adaptation_confirmed')

    def test_only_explicit_free_color_and_inline_delete_requests_count_as_new_adaptations(self):
        delta = [self.rows[fid] for fid in self.report['round_delta']['reviewed_function_ids']]
        expected = {'Paste:' + address for address in ['0x1003b936c', '0x100066068', '0x100324a80',
                    '0x100022ad0', '0x1003b6cfc', '0x1003c4f00']}
        self.assertEqual({r['function_id'] for r in delta if r['status'] == 'user_adaptation_confirmed'}, expected)
        self.assertEqual(self.rows['Paste:0x100021f00']['status'], 'unclosed')
        self.assertEqual(self.rows['Paste:0x100039618']['status'], 'unclosed')

    def test_group_type_difference_is_not_mistaken_for_an_authorized_model_adaptation(self):
        row = self.rows['Paste:0x10031bc94']
        self.assertEqual(row['status'], 'difference_confirmed')
        current = body((ROOT / 'replica/Sources/PastoCore/ClipboardStore.swift').read_text(),
                       'func pinboardOwner(for item: ClipboardItem) -> Pinboard?')
        self.assertIn('pinboardOwnerID', current)
        self.assertNotIn('rawType', current)
        original = fragment('0x10031bc94', row['original']['path'])
        self.assertIn('FUN_1003250f0', original)
        helper = next(p for p in row['supporting_original_fragments'] if p['function_id'] == 'Paste:0x1003250f0')
        original_helper = fragment('0x1003250f0', helper['path'])
        self.assertIn('rawType', original_helper)
        self.assertIn('return IVar1 == 2;', original_helper)

    def test_monitor_guard_and_async_owner_lifetime_remain_explicit_differences(self):
        monitor = self.rows['Paste:0x100031978']
        owner = self.rows['Paste:0x1002f65e0']
        self.assertEqual(monitor['status'], 'difference_confirmed')
        self.assertEqual(owner['status'], 'difference_confirmed')
        browser = body((ROOT / '.local/p0-repair/phase-39/before/replica/Sources/Pasto/UI/FilterBrowser.swift').read_text(),
                       'private func installKeyboardMonitor()')
        self.assertLess(browser.index('guard keyboardMonitor == nil'), browser.index('NSEvent.addLocalMonitor'))
        history = body((ROOT / '.local/p0-repair/phase-39/before/replica/Sources/PastoCore/OriginalSearchInputHistory.swift').read_text(),
                       'func f_1002f60fc()')
        self.assertIn('Task { @MainActor [weak self]', history)
        original = fragment('0x1002f65e0', owner['original']['path'])
        self.assertIn('_swift_retain()', original)
        self.assertIn('0x20) = param_2', original)
        self.assertEqual(self.rows['Paste:0x1002f60fc']['status'], 'unclosed')
        self.assertEqual(self.rows['Paste:0x1002f6f0c']['status'], 'unclosed')

    def test_ocr_empty_input_and_vision_failure_keep_distinct_error_contracts(self):
        source = (ROOT / 'replica/Sources/PastoCore/OCR.swift').read_text()
        entry = body(source, 'func f_1002d4738(imageData: Data, maximumDimension: Int) throws -> RecognizedTextDocument')
        request = body(source, 'func f_1002d4830(imageData: Data, maximumDimension: Int) throws -> RecognizedTextDocument')
        self.assertIn('guard !imageData.isEmpty else { throw OCRError.invalidImageData }', entry)
        self.assertIn('try autoreleasepool', entry)
        self.assertIn('return RecognizedTextDocument(text: "", words: [])', request)
        self.assertIn('try handler.perform([request])', request)
        self.assertNotIn('try? handler.perform', request)
        self.assertIn('request.results ?? []', request)

    def test_ocr_range_guard_catches_repeated_word_and_missing_box_regressions(self):
        source = body((ROOT / 'replica/Sources/PastoCore/OCR.swift').read_text(),
                      'func f_1002d576c(observations: [VNRecognizedTextObservation]) -> [RecognizedWord]')
        self.assertTrue(valid_word_cursor(source))
        self.assertFalse(valid_word_cursor(source.replace('cursor = range.upperBound', 'cursor = text.startIndex')))
        self.assertFalse(valid_word_cursor(source.replace('range: cursor..<text.endIndex', 'range: text.startIndex..<text.endIndex')))
        self.assertFalse(valid_word_cursor(source.replace('else { break }', 'else { continue }')))
        self.assertFalse(valid_word_cursor(source.replace('try? candidate.boundingBox(for: range)', 'try! candidate.boundingBox(for: range)')))

    def test_rich_text_toggle_uses_first_run_and_preserves_explicit_undo_range(self):
        source = body((ROOT / 'replica/Sources/PastoCore/OriginalPreviewTextTraits.swift').read_text(),
                      'func f_1002072a0(_ trait: Trait, editor: NSTextView, range requestedRange: NSRange? = nil)')
        sequence = ['requestedRange ?? editor.selectedRange()', 'range.length < 1',
                    'storage.attributes(at: range.location', 'let forceRemove =', 'storage.beginEditing()',
                    'storage.enumerateAttributes', 'storage.endEditing()', 'registerUndo(withTarget: editor)']
        positions = [source.index(value) for value in sequence]
        self.assertEqual(positions, sorted(positions))
        self.assertIn('[weak editor]', source)
        self.assertIn('f_1002072a0(trait, editor: editor, range: range)', source)

    def test_production_tree_map_and_head_stay_at_review_baseline(self):
        before = json.loads((ROOT / '.local/p0-review/production-before.json').read_text())
        paths = {str(p.relative_to(ROOT)) for p in (ROOT / 'replica/Sources').rglob('*') if p.is_file()}
        self.assertEqual(paths, set(before))
        for path, value in before.items():
            self.assertEqual(digest(path), value)
        self.assertEqual(digest('replica/function-map.json'), self.report['function_map_sha256'])
        head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        self.assertEqual(head, self.report['head_revision'])
        for key in ['production_source_edited', 'function_map_modified', 'compiled', 'application_executed',
                    'network_used', 'committed', 'pushed']:
            self.assertFalse(self.report[key])
        self.assertTrue(self.report['goal_active'])
