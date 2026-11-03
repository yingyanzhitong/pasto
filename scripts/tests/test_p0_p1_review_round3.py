"""No Swift/compiler/app execution: source, decompiler, and static image checks."""
import hashlib
import json
import struct
import unittest
from collections import Counter

from test_offline_p0_contracts import ROOT, body
from test_p0_p1_review_round2 import digest, fragment


def native_date_methods(source):
    ids = ['1002d7694', '1002d7a14', '1002d7db8', '1002d8300', '1002d8860']
    return [body(source, 'func f_' + address + '()') for address in ids]


class P0P1ReviewRound3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((ROOT / 'reports/replica/p0-p1-review-round3.json').read_text())
        cls.prior = json.loads((ROOT / 'reports/replica/p0-p1-review-round2.json').read_text())
        cls.rows = {r['function_id']: r for r in cls.report['records']}
        cls.proof = json.loads((ROOT / cls.report['static_proof']['path']).read_text())

    def test_counts_and_priorities_keep_the_same_unique_denominator(self):
        rows, report = self.rows, self.report
        self.assertEqual(len(rows), len(report['records']))
        self.assertEqual(set(rows), {r['function_id'] for r in self.prior['records']})
        counts = Counter(r['status'] for r in rows.values())
        self.assertEqual(dict(counts), report['outcomes'])
        resolved = len(rows) - counts['unclosed']
        self.assertEqual(resolved, report['resolved_review_records'])
        self.assertEqual(report['resolved_comparison_percent'], round(resolved / len(rows) * 100, 2))
        self.assertEqual(report['p0_component']['resolved'] + report['p1_additional_component']['resolved'], resolved)
        self.assertTrue(report['scope_provisional'])
        self.assertIsNone(report['full_priority_completion_percent'])
        self.assertFalse(any(r['full_function_migration_verified'] for r in rows.values()))

    def test_new_reviews_only_replace_previously_unclosed_addresses(self):
        old = {r['function_id']: r for r in self.prior['records']}
        delta = self.report['round_delta']
        changed = set(delta['reviewed_function_ids'])
        self.assertEqual(len(changed), delta['reviewed_addresses'])
        for fid, row in self.rows.items():
            if fid in changed:
                self.assertEqual(old[fid]['status'], 'unclosed')
                self.assertEqual(row['previous_status'], 'unclosed')
            else:
                self.assertEqual(row, old[fid])
        self.assertEqual(self.report['resolved_review_records'] - self.prior['resolved_review_records'], delta['new_resolved'])

    def test_new_fragments_and_current_consumers_remain_bound(self):
        for fid in self.report['round_delta']['reviewed_function_ids']:
            row = self.rows[fid]
            proofs = [dict(row['original'], function_id=fid)] + row.get('supporting_original_fragments', [])
            for proof in proofs:
                address = proof.get('address') or proof['function_id'].split(':')[1]
                actual = fragment(address, proof['path'])
                self.assertEqual(hashlib.sha256(actual.encode()).hexdigest(), proof['sha256'], address)
            for ref in row['current_references']:
                self.assertEqual(digest(ref['path']), ref['sha256'])
                self.assertEqual(ref['symbol'] in (ROOT / ref['path']).read_text(), ref['present'])
            if row['status'] == 'local_contract_consistent':
                self.assertTrue(row['current_references'])
                self.assertTrue(all(ref['present'] for ref in row['current_references']))

    def test_immutable_input_hashes_and_raw_bytes_match_the_real_slice(self):
        report = self.report
        for path, value in report['source_inputs'].items():
            self.assertEqual(digest(path), value, path)
        self.assertEqual(digest(report['static_proof']['path']), report['static_proof']['sha256'])
        binary = (ROOT / self.proof['binary_path']).read_bytes()
        self.assertEqual(hashlib.sha256(binary).hexdigest(), self.proof['binary_sha256'])
        for value in self.proof['byte_proofs']:
            data = bytes.fromhex(value['bytes'])
            offset = value['slice_file_offset']
            self.assertEqual(binary[offset:offset + len(data)], data, value['address'])
        for path, value in self.proof['source_reports'].items():
            self.assertEqual(digest(path), value)

    def test_date_functions_use_native_calendar_components_and_failures_not_duration_approximations(self):
        source = (ROOT / 'replica/Sources/PastoCore/OriginalSearchDateRanges.swift').read_text()
        today, yesterday, this_week, last_week, days = native_date_methods(source)
        self.assertIn('precondition(start < end)', source)
        self.assertIn('return start..<end', source)
        for value in [today, yesterday, days]:
            self.assertIn('Calendar.current.startOfDay(for: Date())', value)
        self.assertIn('value: 1, to: start)!', today)
        self.assertIn('value: -1, to: end)!', yesterday)
        for value in [this_week, last_week]:
            self.assertLess(value.index('let now = Date()'), value.index('Calendar.current.dateComponents'))
            self.assertIn('[.calendar, .yearForWeekOfYear, .weekOfYear]', value)
            self.assertIn('components.date!', value)
        self.assertIn('byAdding: .day, value: 7', this_week)
        self.assertIn('byAdding: .weekOfYear, value: -1', last_week)
        self.assertIn('value: -30, to: today)!', days)
        self.assertIn('value: 1, to: today)!', days)
        self.assertNotIn('addingTimeInterval', source)
        original = fragment('0x1002d8860', self.rows['Paste:0x1002d8860']['original']['path'])
        self.assertIn(',-0x1e,', original)
        self.assertIn('SoftwareBreakpoint', original)

    def test_optional_string_fields_are_proven_by_relative_metadata_records(self):
        binary = (ROOT / self.proof['binary_path']).read_bytes()
        fields = {r['name']: r for r in self.proof['metadata_fields']}
        for name in ['app', 'device', 'pinboard', 'content']:
            field = fields[name]
            record_address = int(field['record_address'], 16)
            raw = bytes.fromhex(field['record_bytes'])
            type_address = record_address + 4 + struct.unpack_from('<i', raw, 4)[0]
            name_address = record_address + 8 + struct.unpack_from('<i', raw, 8)[0]
            self.assertEqual(type_address, int(field['type_ref'], 16))
            offset = name_address - 0x100000000
            actual_name = binary[offset:binary.index(b'\0', offset)].decode()
            self.assertEqual(actual_name, name)
            type_data = bytes.fromhex(field['type_ref_bytes'])
            self.assertEqual(binary[type_address-0x100000000:type_address-0x100000000+len(type_data)], type_data)
            if name != 'content':
                self.assertTrue(type_data.startswith(b'SSSg'))  # Optional<String>
            else:
                self.assertIn(b'YbcSg', type_data)  # Optional @Sendable function

    def test_legacy_nil_device_and_multigroup_differences_are_not_marked_as_full_matches(self):
        for address in ['0x1003250f0', '0x10030e6bc', '0x100375210', '0x100375274', '0x100375244', '0x100371998']:
            self.assertEqual(self.rows['Paste:' + address]['status'], 'difference_confirmed')
        provider = (ROOT / 'replica/Sources/Pasto/UI/ReplicaSearchSuggestionSource.swift').read_text()
        ui = (ROOT / 'replica/Sources/Pasto/UI/ReplicaUIController.swift').read_text()
        self.assertIn('($0.rawType ?? 2) == 2', provider)
        self.assertIn('owner.rawType == 2 || owner.rawType == nil', ui)
        source = (ROOT / 'replica/Sources/Pasto/UI/ReplicaSearchIndex.swift').read_text()
        self.assertIn('let device: String', source)
        self.assertIn('attributes.setValue(entry.device as NSString', source)
        self.assertIn('let pinboards: [String]', source)
        self.assertIn('attributes.setValue(entry.pinboards as NSArray', source)
        self.assertIn('text = String(indexedText.prefix(5000))', source)

    def test_native_fetch_request_defaults_are_missing_from_current_factory_not_just_renamed(self):
        for address in ['0x1003298a0', '0x100329754']:
            self.assertEqual(self.rows['Paste:' + address]['status'], 'difference_confirmed')
        source = body((ROOT / 'replica/Sources/PastoCore/ClipboardPersistence.swift').read_text(),
                      'private func fetch(_ entity: String, keys: [String]? = nil)')
        self.assertIn('NSFetchRequest<NSManagedObject>(entityName: entity)', source)
        self.assertNotIn('fetchBatchSize', source)
        self.assertNotIn('sortDescriptors', source)
        original = fragment('0x1003298a0', self.rows['Paste:0x1003298a0']['original']['path'])
        self.assertIn('objc_stub::FUN_100c0bb60(self_00,0x14)', original)
        self.assertIn('objc_stub::setPredicate_', original)

    def test_popover_close_order_and_notification_name_are_bound_to_actual_consumers(self):
        source = (ROOT / 'replica/Sources/PastoCore/OriginalFilterBrowserPopover.swift').read_text()
        close = body(source, 'public func f_100008bc0()')
        steps = ['animates = true', 'isDisplayed = false', 'contentViewController = nil', 'onWillClose?()']
        positions = [close.index(value) for value in steps]
        self.assertEqual(positions, sorted(positions))
        self.assertIn('delegate = self', source)
        ui = (ROOT / 'replica/Sources/Pasto/UI/FilterBrowser.swift').read_text()
        self.assertIn('let popover = OriginalFilterBrowserPopover()', ui)
        self.assertIn('popover.onWillClose = { [weak self, weak field] in', ui)
        binary = (ROOT / self.proof['binary_path']).read_bytes()
        for part in self.proof['notification_name']:
            data = bytes.fromhex(part['bytes'])
            offset = part['slice_file_offset']
            self.assertEqual(binary[offset:offset + len(data)], data)
        data = bytes.fromhex(self.proof['notification_name'][1]['bytes'])
        self.assertEqual(data, b'mainWindowWillClose')

    def test_gray_colors_are_decoded_as_ieee_double_not_guessed_from_hex_digits(self):
        row = self.rows['Paste:0x1003de9a0']
        self.assertEqual(row['status'], 'local_contract_consistent')
        gray = next(r for r in row['supporting_original_fragments'] if r['function_id'] == 'Paste:0x1001fe354')
        original = fragment('0x1001fe354', gray['path'])
        channels = [(0x3fe1d1d1d1d1d1d2, 0x3fe1d1d1d1d1d1d2, 0x3fe2727272727272),
                    (0x3fe3131313131313, 0x3fe3131313131313, 0x3fe3b3b3b3b3b3b4)]
        values = []
        for color in channels:
            for word in color:
                self.assertIn(hex(word), original)
            rgb = [round(struct.unpack('<d', struct.pack('<Q', word))[0] * 255) for word in color]
            values.append(sum(channel << shift for channel, shift in zip(rgb, [16, 8, 0])))
        self.assertEqual(values, [0x8e8e93, 0x98989d])
        source = (ROOT / 'replica/Sources/PastoCore/OriginalPinboardColor.swift').read_text()
        self.assertIn('grayProvider = dynamicColor(light: 0x8e8e93, dark: 0x98989d)', source)
