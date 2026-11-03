"""Read-only difference inventory and Mach-O entrypoint evidence checks."""
import hashlib
import json
import struct
import unittest
from collections import Counter

from test_offline_p0_contracts import ROOT, body
from test_p0_p1_review_round2 import digest, fragment


def uleb(blob, cursor):
    result = shift = 0
    while True:
        byte = blob[cursor]; cursor += 1
        result |= (byte & 127) << shift
        if not byte & 128: return result, cursor
        shift += 7
        if shift > 63: raise ValueError('Invalid ULEB')


class P0P1ReviewRound12(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((ROOT / 'reports/replica/p0-p1-review-round12.json').read_text())
        cls.source = json.loads((ROOT / cls.report['source_report']['path']).read_text())
        cls.backlog = json.loads((ROOT / cls.report['difference_backlog']['path']).read_text())
        cls.rows = {row['function_id']: row for row in cls.source['records']}
        cls.proof = json.loads((ROOT / cls.report['static_proof']['path']).read_text())
        cls.binary = (ROOT / cls.proof['binary_path']).read_bytes()

    def test_snapshot_preserves_the_unclosed_setter_and_does_not_call_backlog_counts_progress(self):
        self.assertEqual(digest(self.report['source_report']['path']), self.report['source_report']['sha256'])
        for key in ['resolved_review_records', 'unclosed_review_records', 'resolved_comparison_percent',
                    'outcomes', 'p0_component', 'p1_additional_component']:
            self.assertEqual(self.report['snapshot'][key], self.source[key])
        self.assertEqual(self.report['unresolved_review']['status'], 'unclosed')
        self.assertFalse(self.report['unresolved_review']['full_function_migration_verified'])
        self.assertEqual(self.report['round_delta']['newly_resolved'], 0)
        self.assertEqual(self.report['snapshot']['resolved_review_records'], 488)
        self.assertEqual(self.report['snapshot']['resolved_comparison_percent'], 99.8)
        self.assertTrue(self.report['scope_provisional'])
        self.assertIsNone(self.report['full_priority_completion_percent'])

    def test_backlog_covers_all_differences_once_and_excludes_user_adaptations(self):
        self.assertEqual(digest(self.report['difference_backlog']['path']), self.report['difference_backlog']['sha256'])
        self.assertEqual(digest(self.backlog['source_report']['path']), self.backlog['source_report']['sha256'])
        for path, sha in self.backlog['source_inputs'].items(): self.assertEqual(digest(path), sha)
        selected = {fid: row for fid, row in self.rows.items() if row['status'] == 'difference_confirmed'}
        actual = [fid for group in self.backlog['groups'] for fid in group['function_ids']]
        self.assertEqual(Counter(actual), Counter({fid: 1 for fid in selected}))
        self.assertEqual(len(actual), 115)
        self.assertEqual(self.backlog['counts']['p0_records'], sum('P0' in r['priorities'] for r in selected.values()))
        self.assertEqual(self.backlog['counts']['p1_additional_records'], sum(r['priorities'] == ['P1'] for r in selected.values()))
        for group in self.backlog['groups']:
            self.assertEqual({r['function_id'] for r in group['records']}, set(group['function_ids']))
            self.assertEqual(group['priority'], 'P0' if any('P0' in selected[f]['priorities'] for f in group['function_ids']) else 'P1')
            for row in group['records']:
                original = selected[row['function_id']]
                for key in ['original', 'current_references', 'contract', 'evidence_note']:
                    self.assertEqual(row[key], original[key])
                # Two old snapshot entries explicitly carried a descriptive, absent symbol.
                # Preserve that historical data and require separately corrected literal consumers.
                for ref in row.get('verified_current_references', row['current_references']):
                    self.assertEqual(digest(ref['path']), ref['sha256'])
                    self.assertTrue(ref['symbol'] in (ROOT / ref['path']).read_text(), (row['function_id'], ref['path'], ref['symbol']))

    def test_grouping_uses_only_explicit_origins_and_the_verified_source_callback_aliases(self):
        selected = {fid: r for fid, r in self.rows.items() if r['status'] == 'difference_confirmed'}
        manual = self.backlog['manual_verified_grouping']
        self.assertEqual(len(manual), 1)
        manual_links = {fid: item['root_function_id'] for item in manual for fid in item['alias_function_ids']}
        self.assertEqual(set(manual_links), {'Paste:0x10037b204', 'Paste:0x10037c47c', 'Paste:0x10037c494'})
        def root(fid):
            seen = set()
            while fid in selected:
                target = manual_links.get(fid) or selected[fid].get('shared_difference_origin')
                if not target: return fid
                self.assertNotIn(fid, seen); seen.add(fid); fid = target
            return fid
        for group in self.backlog['groups']:
            self.assertEqual({root(fid) for fid in group['function_ids']}, {group['root_function_id']})
        self.assertEqual(len(self.backlog['groups']), 109)
        self.assertEqual(sum(g['priority'] == 'P0' for g in self.backlog['groups']), 53)
        # The parent candidate bridge references multiple distinct causes: do not union those roots.
        candidates = {g['root_function_id'] for g in self.backlog['groups']}
        self.assertTrue({'Paste:0x10030e070', 'Paste:0x10030ed6c', 'Paste:0x10030e6bc'} <= candidates)

    def test_source_sampling_aliases_bind_real_original_calls_and_current_sampling_before_capture(self):
        item = self.backlog['manual_verified_grouping'][0]
        support = {s['function_id']: s for s in item['supporting_original_fragments']}
        for fid, ref in support.items():
            self.assertEqual(hashlib.sha256(fragment(fid.split(':')[1], ref['path']).encode()).hexdigest(), ref['sha256'])
        self.assertIn('FUN_10037b034(', fragment('0x10037c47c', support['Paste:0x10037c47c']['path']))
        self.assertIn('FUN_10037b204()', fragment('0x10037c494', support['Paste:0x10037c494']['path']))
        operation = fragment('0x10037b034', support['Paste:0x10037b034']['path'])
        self.assertLess(operation.index('+ 0x10))();'), operation.index('FUN_10037c494'))
        current = (ROOT / 'replica/Sources/PastoCore/Pasteboard.swift').read_text()
        capture = body(current, 'public func f_10037b034(_ items: [OriginalPasteboardItem]) throws -> Bool')
        self.assertLess(capture.index('NSWorkspace.shared.frontmostApplication'), capture.index('store.captureWithInsertionResult'))
        for ref in item['current_references']: self.assertEqual(digest(ref['path']), ref['sha256'])

    def test_historical_focus_descriptions_are_replaced_by_verified_actual_callbacks_and_guards(self):
        corrections = {x['function_id']: x for x in self.backlog['current_reference_corrections']}
        self.assertEqual(set(corrections), {'Paste:0x1000b098c', 'Paste:0x1000b11ac'})
        app = (ROOT / 'replica/Sources/Pasto/AppMain.swift').read_text()
        show = body(app, 'private func rememberPanelApplication()')
        close = body(app, 'private func restorePanelApplication(restore: Bool)')
        self.assertIn('handoffPreviousApplication = targetApplication', show)
        self.assertIn('!previous.isTerminated', close)
        for fid, correction in corrections.items():
            ref = correction['original']
            self.assertEqual(hashlib.sha256(fragment(fid.split(':')[1], ref['path']).encode()).hexdigest(), ref['sha256'])
            original = self.rows[fid]
            old = [r for r in original['current_references'] if r['symbol'] == correction['old_descriptive_reference']]
            self.assertEqual(len(old), 1); self.assertFalse(old[0]['present'])
            for ref in correction['verified_current_references']:
                self.assertEqual(digest(ref['path']), ref['sha256'])
                self.assertTrue(ref['symbol'] in (ROOT / ref['path']).read_text(), ref['symbol'])
        original_show = fragment('0x1000b098c', corrections['Paste:0x1000b098c']['original']['path'])
        self.assertIn('IVar3 == 0 || iVar2 != (int)IVar4', original_show)
        original_close = fragment('0x1000b11ac', corrections['Paste:0x1000b11ac']['original']['path'])
        self.assertIn('activateWithOptions_', original_close)
        self.assertNotIn('isTerminated', original_close)

    def test_function_starts_proves_the_sixty_eight_byte_body_but_not_its_consumer(self):
        self.assertEqual(digest(self.report['static_proof']['path']), self.report['static_proof']['sha256'])
        self.assertEqual(hashlib.sha256(self.binary).hexdigest(), self.proof['binary_sha256'])
        proof = self.proof['function_starts']
        command = proof['load_command']; offset = command['command_offset']
        self.assertEqual(self.binary[offset:offset + len(bytes.fromhex(command['bytes']))], bytes.fromhex(command['bytes']))
        self.assertEqual(struct.unpack_from('<II', self.binary, offset + 8), (proof['file_offset'], proof['size']))
        blob = self.binary[proof['file_offset']:proof['file_offset'] + proof['size']]
        self.assertEqual(hashlib.sha256(blob).hexdigest(), proof['sha256'])
        starts = []; cursor = address = 0
        while cursor < len(blob):
            delta, cursor = uleb(blob, cursor)
            if not delta: break
            address += delta; starts.append(0x100000000 + address)
        self.assertEqual(len(starts), proof['count'])
        index = proof['target_index']
        self.assertEqual([hex(a) for a in starts[index - 1:index + 2]], [proof['previous'], proof['target'], proof['following']])
        self.assertEqual(starts[index + 1] - starts[index], 68)
        self.assertEqual(self.report['unresolved_review']['status'], 'unclosed')

    def test_export_trie_and_nlist_do_not_supply_a_named_entrypoint(self):
        proof = self.proof['exports']
        blob = self.binary[proof['file_offset']:proof['file_offset'] + proof['size']]
        self.assertEqual(hashlib.sha256(blob).hexdigest(), proof['sha256'])
        exports = []; visits = []
        def walk(cursor, prefix, path):
            self.assertNotIn(cursor, path); visits.append(cursor)
            size, payload = uleb(blob, cursor); end = payload + size
            if size:
                flags, payload = uleb(blob, payload)
                address = None
                if not flags & 8: address, payload = uleb(blob, payload)
                exports.append(dict(name=prefix, flags=flags, address=address))
            count = blob[end]; child_cursor = end + 1
            for _ in range(count):
                edge_end = blob.index(b'\0', child_cursor)
                edge = blob[child_cursor:edge_end].decode()
                child, child_cursor = uleb(blob, edge_end + 1)
                walk(child, prefix + edge, path | {cursor})
        walk(0, '', set())
        target = int(self.proof['target'], 16)
        matches = [e for e in exports if e['address'] is not None and e['flags'] & 3 in (0, 2)
                   and e['address'] == (target if e['flags'] & 3 == 2 else target - 0x100000000)]
        self.assertEqual(matches, proof['target_matches'])
        self.assertEqual(len(exports), proof['entry_count']); self.assertEqual(len(visits), proof['visited_nodes'])
        nlist = self.proof['nlist']; actual = []
        for i in range(nlist['symbol_count']):
            string_index, kind, section, desc, address = struct.unpack_from('<IBBHQ', self.binary, nlist['symbol_offset'] + i * 16)
            if address == target:
                off = nlist['string_offset'] + string_index
                actual.append(dict(name=self.binary[off:self.binary.index(b'\0', off)].decode(), kind=kind, section=section))
        self.assertEqual(actual, nlist['target_matches'])
        self.assertEqual(matches, []); self.assertEqual(actual, [])
        self.assertFalse(self.proof['full_function_migration_verified'])

    def test_full_reference_audit_binds_all_1223_entries_and_exposes_descriptions_as_descriptions(self):
        binding = self.report['structural_reference_audit']
        self.assertEqual(digest(binding['path']), binding['sha256'])
        audit = json.loads((ROOT / binding['path']).read_text())
        self.assertEqual(digest(audit['input']['path']), audit['input']['sha256'])
        cache = {}; total = present = sha_matches = 0; no_source = []
        classes = Counter()
        for fid, row in self.rows.items():
            has_source = False
            for ref in row['current_references']:
                if ref['path'] not in cache:
                    path = ROOT / ref['path']; raw = path.read_bytes()
                    cache[ref['path']] = (hashlib.sha256(raw).hexdigest(), raw.decode())
                sha, text = cache[ref['path']]
                found = ref['symbol'] in text
                is_source = ref['path'].startswith('replica/Sources/')
                kind = 'production_source' if is_source else 'report' if ref['path'].startswith('reports/') else 'decompiled'
                classes[kind] += 1; total += 1; present += found; sha_matches += sha == ref['sha256']
                has_source |= found and is_source
            if not has_source: no_source.append(fid)
        self.assertEqual(total, 1223); self.assertEqual(present, 1221); self.assertEqual(sha_matches, 1223)
        self.assertEqual(dict(classes), audit['summary']['path_counts'])
        self.assertEqual(sorted(no_source), audit['records_without_any_present_production_source_literal'])
        self.assertEqual(set(no_source), {c['function_id'] for c in self.backlog['current_reference_corrections']})


if __name__ == '__main__':
    unittest.main()
