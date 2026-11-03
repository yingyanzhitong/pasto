"""Live source-application relation reaches real consumers; source/Mach-O checks only."""
from native_title_scope_contract import NEW_PATH as NATIVE_TITLE_PATH
from item_observation_scope_contract import NEW_PATH as ITEM_OBSERVATION_PATH
import hashlib
import json
from pathlib import Path
from entity_lookup_scope_contract import pre_entity_lookup
import re
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from supplied_input_scope_contract import pre_supplied_input_adapters, pre_supplied_input_adapters_bytes
from collection_membership_scope_contract import ENTRY_PATH, pre_collection_membership_bytes
from test_p0_repair_checksum_routing import original_fragment
from native_application_scope_contract import INSERTIONS, pre_native_application


class LiveApplicationProjectionContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-78'
        cls.proof = json.loads((cls.phase / 'live-application-contract.json').read_text())
        cls.base = json.loads((cls.phase / 'baseline.json').read_text())
        cls.paths = {k: 'replica/Sources/PastoCore/' + name + '.swift' for k, name in
                     [('model', 'Models'), ('source', 'ClipboardSourcePersistence'),
                      ('persistence', 'ClipboardPersistence'), ('store', 'ClipboardStore')]}
        cls.source = {k: pre_supplied_input_adapters((ROOT / p).read_text()) for k, p in cls.paths.items()}
        cls.project = body(cls.source['source'], 'nonisolated static func projectApplication(')

    def before(self, key): return (self.phase / 'before' / self.paths[key]).read_text()

    def test_original_fragments_binary_and_actual_six_call_branch_words_are_bound(self):
        self.assertEqual(len(self.proof['original_fragments']), 3)
        for r in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / r['path'])[r['address']]['sha256'], r['sha256'])
        raw = (ROOT / self.proof['binary']['path']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), self.proof['binary']['sha256'])
        self.assertEqual(len(self.proof['ARM_words']), 6)
        for r in self.proof['ARM_words']:
            a = int(r['address'], 16) - 0x100000000
            self.assertEqual(raw[a:a + 4].hex(), r['bytes'])
        for r in self.proof['arm_disassemblies'] + [self.proof['decoder'], self.proof['prior_model_proof']]:
            self.assertEqual(hashlib.sha256((ROOT / r['path']).read_bytes()).hexdigest(), r['sha256'])

    def test_three_real_selector_chains_bind_selected_relation_identifier_and_name(self):
        ns = {};p = ROOT / self.proof['decoder']['path']
        exec(p.read_text().split("idx={r['address']", 1)[0], ns)
        self.assertEqual([r['selector'] for r in self.proof['selectors']], ['sourceApplication', 'bundleIdentifier', 'name'])
        for r in self.proof['selectors']:
            a = int(r['stub_address'], 16)
            self.assertEqual(ns['read'](a, 20).hex(), r['stub_bytes'])
            value, chain = ns['reachable_pointer'](int(r['pointer_address'], 16))
            self.assertEqual(hex(value), r['pointer_raw']);self.assertEqual(chain, r['chain'])
            target = ns['base'] + (value & ((1 << 36) - 1))
            self.assertEqual(hex(target), r['selector_address'])
            off = ns['offset'](target);raw = ns['raw']
            self.assertEqual(raw[off:raw.index(b'\0', off)].decode(), r['selector'])

    def test_original_bundle_and_image_name_consumers_use_relation_with_nil_branch(self):
        fragments = {r['address']: original_fragment((ROOT / r['path']).read_text(), r['address'][2:])
                     for r in self.proof['original_fragments']}
        processor = fragments['0x10038222c'];image = fragments['0x100383df4']
        self.assertIn('objc_stub::sourceApplication((ID)local_138)', processor)
        self.assertLess(processor.index('if (local_100 == 0)'), processor.index('objc_stub::bundleIdentifier(local_100)'))
        self.assertIn('objc_stub::sourceApplication(param_1)', image)
        self.assertLess(image.index('if (IVar17 == 0)'), image.index('objc_stub::name(IVar17)'))
        words = {int(r['address'], 16): int.from_bytes(bytes.fromhex(r['bytes']), 'little') for r in self.proof['ARM_words']}
        for pc, target in [(0x100382718, 0x100c0ef60), (0x10038272c, 0x100bfea60),
                           (0x10038415c, 0x100c0ef60), (0x100384170, 0x100c07060)]:
            w = words[pc];self.assertEqual(w >> 26, 0b100101)
            delta = w & 0x3ffffff
            if delta & 0x2000000: delta -= 0x4000000
            self.assertEqual(pc + delta * 4, target)

    def test_original_model_has_optional_relation_and_required_name_identifier_color(self):
        model = self.proof['original_model']
        self.assertEqual(hashlib.sha256((ROOT / model['path']).read_bytes()).hexdigest(), model['sha256'])
        schema = model['schema'];relation = schema['ItemEntity']['fields']['sourceApplication']
        self.assertTrue(relation['NSIsOptional'])
        self.assertEqual(relation['_NSDestinationEntityName'], 'ApplicationEntity')
        fields = schema['ApplicationEntity']['fields']
        for k in ['bundleIdentifier', 'name', 'rawColor']: self.assertFalse(fields[k].get('NSIsOptional', False))
        self.assertEqual(fields['rawColor']['NSAttributeType'], 300)
        self.assertTrue(fields['rawIcon']['NSIsOptional'])

    def test_current_four_sources_and_after_snapshots_are_bound(self):
        self.assertEqual(set(self.proof['current_sources']), set(self.paths.values()))
        for p, h in self.proof['current_sources'].items():
            raw = pre_supplied_input_adapters_bytes(ROOT / p)
            self.assertEqual(hashlib.sha256(raw).hexdigest(), h)
            self.assertEqual(raw, (self.phase / 'after' / p).read_bytes())

    def test_authoritative_nil_clears_old_relation_without_fallback(self):
        p = self.project
        self.assertLess(p.index('item.hasSourceApplicationSnapshot = true'), p.index('guard let application'))
        self.assertIn('item.sourceApplicationRelationIsKnown = true', p)
        missing = body(p, 'guard let application =')
        self.assertIn('item.sourceApplicationSnapshot = nil', missing)
        self.assertIn('item.sourceApplicationBundleID = nil', missing)
        self.assertIn('return', missing)
        for token in ['sourceApplications', 'sourceBundleID', 'sourceName', 'first(where:', 'decode(', 'try?']:
            self.assertNotIn(token, p)

    def test_present_relation_reads_current_name_icon_and_unsigned_color_bits(self):
        p = self.project
        for token in ['application.value(forKey: "bundleIdentifier") as? String',
                      'application.value(forKey: "name") as? String',
                      'application.value(forKey: "rawColor") as? NSNumber',
                      'application.value(forKey: "rawIcon") as? Data',
                      'UInt64(bitPattern: color.int64Value)', 'item.sourceApplicationBundleID = identifier',
                      'SourceApplicationRecord(bundleIdentifier: identifier, name: name']:
            self.assertIn(token, p)
        self.assertIn('throw CocoaError(.fileReadCorruptFile)', p)
        self.assertNotIn('UInt64(color.int64Value)', p)
        for token in ['context.', 'Task {', 'save(', 'reload(', 'reset(', 'fetch(', 'Date()']:
            self.assertNotIn(token, p)

    def test_archive_keys_are_exactly_all_twenty_three_previous_stored_fields(self):
        old = body(self.before('model'), 'public struct ClipboardItem:')
        stored = set(re.findall(r'^    public var (\w+):[^\n{]+$', old, re.M))
        self.assertEqual(len(stored), 23)
        model = body(self.source['model'], 'public struct ClipboardItem:')
        coding = body(model, 'private enum CodingKeys: String, CodingKey')
        keys = set()
        for line in coding.splitlines():
            if line.strip().startswith('case '): keys.update(x.strip() for x in line.strip()[5:].split(','))
        self.assertEqual(keys, stored)
        for transient in ['sourceApplicationSnapshot', 'hasSourceApplicationSnapshot']:
            self.assertNotIn(transient, coding)
        self.assertIn('public var sourceApplicationSnapshot: SourceApplicationRecord? = nil', model)
        self.assertIn('public var hasSourceApplicationSnapshot = false', model)
        self.assertEqual(body(self.source['model'], 'public init(id: UUID = UUID(), nativeIdentifier:'),
                         body(self.before('model'), 'public init(id: UUID = UUID(), nativeIdentifier:'))

    def test_transient_source_snapshot_is_removed_before_content_equality_and_encoding(self):
        current = body(self.source['persistence'], 'private func content(_ item:')
        previous = body(self.before('persistence'), 'private func content(_ item:')
        self.assertEqual(pre_native_application(current), previous)
        for token in ['value.sourceApplicationSnapshot = nil', 'value.hasSourceApplicationSnapshot = false']:
            self.assertLess(current.index(token), current.index('return value'))
        commit = body(self.source['persistence'], 'func commit<T>(')
        self.assertEqual(commit, body(self.before('persistence'), 'func commit<T>('))
        self.assertIn('old.map(content) != content(item)', commit)
        self.assertIn('try encode(content(item))', commit)

    def test_shared_item_projection_adds_only_native_source_read_and_no_query(self):
        current = body(self.source['persistence'], 'nonisolated static func item(')
        previous = body(self.before('persistence'), 'nonisolated static func item(')
        line = '        try ClipboardSourcePersistence.projectApplication(&item, from: object)\n'
        self.assertEqual(current.count(line), 1)
        self.assertEqual(current.replace(line, '', 1), previous)
        self.assertLess(current.index(line), current.index('return item'))
        for token in ['context.', 'save(', 'reload()', 'fetch(', 'Task {']:
            self.assertNotIn(token, current)

    def test_actual_getter_prefers_native_snapshot_including_nil_before_legacy_lookup(self):
        current = body(self.source['store'], 'public func sourceApplication(for item:')
        previous = body(self.before('store'), 'public func sourceApplication(for item:')
        line = '        if item.hasSourceApplicationSnapshot { return item.sourceApplicationSnapshot }\n'
        self.assertEqual(current.replace(line, '', 1), previous)
        self.assertLess(current.index('if item.hasSourceApplicationSnapshot'), current.index('guard let identifier'))
        self.assertIn('sourceApplications.first { $0.bundleIdentifier == identifier }', current)
        self.assertNotIn('if let snapshot', current)  # nil is authoritative, not a cache miss

    def test_real_render_selection_and_modal_holder_use_same_shared_projection(self):
        reference = pre_entity_lookup((ROOT / 'replica/Sources/PastoCore/ClipboardCollectionItemReference.swift').read_text())
        holder = (ROOT / 'replica/Sources/PastoCore/ClipboardRestoreItem.swift').read_text()
        self.assertIn('ClipboardPersistence.item(object)', body(reference, 'public func item()'))
        self.assertIn('ClipboardPersistence.item(object)', body(holder, 'init(id: UUID, object:'))
        host = (ROOT / 'replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift').read_text()
        self.assertIn('requiredItem()', body(host, 'private func renderedItem(at index:'))
        self.assertIn('items[index].item()', body(host, 'func appliedSelectedItems(for state:'))
        entry = pre_entity_lookup((ROOT / 'replica/Sources/PastoCore/ClipboardCollectionEntry.swift').read_text())
        self.assertIn('if let reference { return reference.item() }', body(entry, 'public func item()'))

    def test_real_writer_icon_and_color_consumers_read_source_getter(self):
        writer = (ROOT / 'replica/Sources/PastoCore/Pasteboard.swift').read_text()
        f = body(writer, 'private func writeToPasteboard(ids:')
        for token in ['let application = sourceApplication(for: item)',
                      'imageRestore.prepare(sourceName: application?.name',
                      'sourceBundleID: application?.bundleIdentifier']:
            self.assertIn(token, f)
        panel = (ROOT / 'replica/Sources/Pasto/UI/PanelViews.swift').read_text()
        self.assertIn('if let application = store.sourceApplication(for: item)', panel)
        self.assertIn('SourceAppColor.color(application: store.sourceApplication(for: item))', panel)
        self.assertNotIn('item.sourceBundleID', f)

    def test_only_five_reviewed_insertions_change_four_existing_files_no_schema_or_UI_delta(self):
        self.assertEqual(len(INSERTIONS), 5)
        for key in self.paths:
            self.assertEqual(pre_native_application(self.source[key]), self.before(key))
        sha = lambda p: hashlib.sha256(pre_collection_membership_bytes(ROOT / p)).hexdigest()
        self.assertEqual({p for p, h in self.base['production'].items() if sha(p) != h}, set(self.paths.values()))
        files = {str(p.relative_to(ROOT)) for p in (ROOT / 'replica/Sources').rglob('*') if p.is_file()}
        self.assertEqual(files - {NATIVE_TITLE_PATH, ITEM_OBSERVATION_PATH} - {ENTRY_PATH}, set(self.base['production']))
        for p in ['replica/Package.swift', 'package.json']:
            self.assertEqual(sha(p), self.base['other'][p])

    def test_full_provider_unknowns_and_runtime_remain_unclosed(self):
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertEqual(self.proof['repaired_finite_contracts'], [])
        self.assertEqual(self.proof['remaining_confirmed_differences'], ['Paste:0x1003544dc'])
        self.assertTrue(any('metadata' in r for r in self.proof['remaining_work']))
        self.assertTrue(any('Unknown04430c/0f733c' in r for r in self.proof['remaining_work']))


if __name__ == '__main__': unittest.main()
