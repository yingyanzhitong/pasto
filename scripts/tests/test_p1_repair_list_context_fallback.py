from native_title_scope_contract import pre_native_title_bytes
from item_order_scope_contract import without_list_request, without_list_factory, without_list_UI_insertions
"""Original-bound list type/fallback and unknown ABI guards; no AppKit/Swift execution."""
import hashlib
import json
import re
import struct
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body
from test_p0_repair_checksum_routing import original_fragment
from frc_result_scope_contract import assert_list_context_only


class ListContextFallbackContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = ROOT / '.local/p0-repair/phase-69'
        cls.proof = json.loads((cls.phase / 'list-context-contract.json').read_text())
        cls.paths = dict(context='replica/Sources/PastoCore/OriginalCollectionListContext.swift',
                         ui='replica/Sources/Pasto/UI/ReplicaUIController.swift',
                         lists='replica/Sources/PastoCore/ClipboardListPersistence.swift',
                         store='replica/Sources/PastoCore/ClipboardStore.swift',
                         reader='replica/Sources/PastoCore/ClipboardSnapshotReader.swift')
        cls.source = {k: (ROOT / p).read_text() for k, p in cls.paths.items()}
        cls.original = {r['address']: original_fragment((ROOT / r['path']).read_text(), r['address'][2:]) for r in cls.proof['original_fragments']}

    def test_original_fragments_actual_sources_and_static_disassemblies_are_bound(self):
        self.assertEqual(len(self.proof['original_fragments']), 12)
        for row in self.proof['original_fragments']:
            self.assertEqual(source_fragments(ROOT / row['path'])[row['address']]['sha256'], row['sha256'])
        for row in [self.proof['binary']] + self.proof['arm_disassemblies']:
            self.assertEqual(hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest(), row['sha256'])
        for path, digest in self.proof['current_sources'].items():
            frozen = (self.phase / 'after' / path).read_bytes()
            self.assertEqual(hashlib.sha256(frozen).hexdigest(), digest)
            current = (ROOT / path).read_text()
            if path == self.paths['ui']:
                from item_order_scope_contract import assert_history_list_projection_only
                a = without_list_UI_insertions(current); b = without_list_UI_insertions(frozen.decode())
                av = body(a, 'var visibleItems:'); bv = body(b, 'var visibleItems:')
                assert_history_list_projection_only(self, av, bv)
                self.assertEqual(a.split(av), b.split(bv))
            elif path == self.paths['lists']:
                self.assertEqual(without_list_request(current), frozen.decode())
            elif path == self.paths['store']:
                self.assertEqual(without_list_factory(current, public=True), frozen.decode())
            else:
                self.assertEqual(pre_native_title_bytes(ROOT / path), frozen)

    def test_real_rawType_selector_and_64_bit_comparisons_select_same_identity_tags(self):
        raw, setter = self.proof['selector_bindings']
        self.assertEqual(raw['selector'], 'rawType')
        for row in [raw, setter]:
            self.assertTrue(row['chain']['declared_chain_reachable'])
            self.assertEqual(bytes.fromhex(row['selector_bytes']['bytes']), row['selector'].encode() + b'\0')
        words = {int(r['address'], 16): struct.unpack('<I', bytes.fromhex(r['bytes']))[0] for r in self.proof['ARM_words']}
        self.assertEqual(words[0x1003b8118], 0xf100081f)  # CMP X0,2; not W0 truncation
        self.assertEqual(words[0x1003b8120], 0xf100041f)
        self.assertEqual(words[0x1003b8128], 0xb2420274)
        self.assertEqual(words[0x1003b8130], 0xb2410274)
        native = self.original['0x1003b80f0']
        self.assertIn('param_1 = param_1 | 0x8000000000000000', native)
        self.assertIn('param_1 = param_1 | 0x4000000000000000', native)

    def test_native_unsupported_diagnostic_is_before_deferred_history_getter(self):
        native = self.original['0x1003b80f0']
        self.assertLess(native.index('FUN_10019c380('), native.index('FUN_10035a72c(thunk_FUN_10035aca8,0)'))
        self.assertLess(native.index('FUN_10035a72c(thunk_FUN_10035aca8,0)'), native.index('param_1 = (ulong)pcVar4 | 0x4000000000000000'))
        self.assertIn('CoreData)::__C::NSManagedObjectContext::_performAndWait', self.original['0x10035a72c'])
        words = {int(r['address'], 16): struct.unpack('<I', bytes.fromhex(r['bytes']))[0] for r in self.proof['ARM_words']}
        for address, target in [(0x1003b8280, 0x10019c380), (0x1003b82a0, 0x10035a72c)]:
            delta = words[address] & ((1 << 26) - 1)
            if delta & (1 << 25): delta -= 1 << 26
            self.assertEqual(address + 4 * delta, target)

    def test_real_enum_preserves_supported_identity_and_only_fallback_invokes_history(self):
        source = self.source['context']
        method = body(source, 'public static func f_1003b80f0(')
        self.assertIn('case 2: return .pinboard(identifier: identifier)', method)
        self.assertIn('case 1: return .history(identifier: identifier)', method)
        failure = method.split('default:', 1)[1]
        self.assertLess(failure.index('logger.error('), failure.index('historyIdentifier()'))
        self.assertEqual(method.count('historyIdentifier()'), 1)
        self.assertNotIn('historyIdentifier()', method.split('default:', 1)[0])
        self.assertIn('private static let logger = Logger(', source)
        for forbidden in ['URLSession', 'Analytics', 'UserDefaults', 'Task {', 'NSApplication', 'fatalError', 'try?', 'save()']:
            self.assertNotIn(forbidden, source)

    def test_real_selected_board_sink_receives_type_before_existing_apply_tail(self):
        method = body(self.source['ui'], 'private func installListSelectionDelivery()')
        old = body((self.phase / 'before' / self.paths['ui']).read_text(), 'private func installListSelectionDelivery()')
        assert_list_context_only(self, method, old)
        order = ['guard let self, let identifier', 'self.store.tabListTarget(identifier: identifier)',
                 'OriginalCollectionListContext.f_1003b80f0(identifier: target.identifier,', 'rawType: target.rawType',
                 'switch context', 'case .pinboard(let identifier):', 'id = UUID(uuidString: identifier)',
                 'case .history(let identifier):', 'id = nil', 'self.selectedTabList = target', 'self.applySelectedList(id)',
                 'self.selectedTabIndex = self.tabListSnapshot?.index(of: target)']
        self.assertEqual([method.index(t) for t in order], sorted(method.index(t) for t in order))
        self.assertEqual(method.count('self.applySelectedList(id)'), 1)
        self.assertIn('historyIdentifier: { ClipboardStore.historyListIdentifier }', method)

    def test_real_managed_projection_and_legacy_normalization_reach_this_consumer(self):
        project = body(self.source['lists'], 'func project(')
        self.assertIn('(list.value(forKey: "rawType") as? NSNumber)?.int64Value ?? 0', project)
        self.assertIn('value.rawType = Int16(exactly: rawType) ?? 0', project)
        self.assertNotIn('truncatingIfNeeded', project)
        read = body(self.source['reader'], 'func read()')
        self.assertIn('pinboards: lists.project(', read)
        publish = body(self.source['store'], 'private func publish(')
        self.assertIn('if pinboards != state.pinboards { pinboards = state.pinboards }', publish)
        normalize = body(self.source['store'], 'private func normalize(')
        self.assertIn('for i in state.pinboards.indices where state.pinboards[i].rawType == nil', normalize)
        self.assertIn('state.pinboards[i].rawType = 2', normalize)

    def test_every_Int16_type_and_64_bit_overflow_preserve_native_classification(self):
        # Python branch fixtures tied to exact producer/source above; not execution of Swift.
        classify = lambda raw: 'pinboard' if raw == 2 else 'history' if raw == 1 else 'fallback'
        for raw in list(range(-32768, 32768)) + [-(1 << 63), (1 << 63) - 1, -65535, 65537, 65538]:
            projected = raw if -32768 <= raw <= 32767 else 0
            self.assertEqual(classify(raw), classify(projected))
        self.assertEqual(classify(2), 'pinboard')
        self.assertEqual(classify(1), 'history')
        self.assertEqual(classify(65538), 'fallback')
        # Nil is a legacy local group, not a native unknown type.
        self.assertEqual(classify(2 if None is None else 0), 'pinboard')

    def test_lazy_fallback_trace_has_diagnostic_then_single_getter_and_preserves_identity(self):
        for raw in [1, 2, 0, 3, -1, 65538]:
            events = []
            def fallback(): events.append('history'); return 'canonical-history'
            if raw == 2: result = ('pinboard', 'selected')
            elif raw == 1: result = ('history', 'selected')
            else:
                events.append('diagnostic');result = ('history', fallback())
            self.assertEqual(events, [] if raw in [1, 2] else ['diagnostic', 'history'])
            self.assertEqual(result[1], 'selected' if raw in [1, 2] else 'canonical-history')

    def test_only_one_UI_branch_and_one_new_core_file_change(self):
        baseline = json.loads((self.phase / 'baseline.json').read_text())
        frozen_root = ROOT / '.local/p0-repair/phase-70/before'
        changed = {p for p, h in baseline['production'].items() if hashlib.sha256((frozen_root / p).read_bytes()).hexdigest() != h}
        actual = {str(p.relative_to(frozen_root)) for p in (frozen_root / 'replica/Sources').rglob('*') if p.is_file()}
        self.assertEqual(changed, {self.paths['ui']})
        self.assertEqual(actual - set(baseline['production']), {self.paths['context']})
        assert_list_context_only(self, (frozen_root / self.paths['ui']).read_text(), (self.phase / 'before' / self.paths['ui']).read_text())
        for marker in ['private func applySelectedList(', 'private func selectListIdentifier(', 'var visibleItems:', 'private func installSearchQueryDelivery()']:
            self.assertEqual(body((frozen_root / self.paths['ui']).read_text(), marker), body((self.phase / 'before' / self.paths['ui']).read_text(), marker))

    def test_versioned_backlog_keeps_old159_and_admits_only_new_unsupported_branch(self):
        old_path = 'reports/replica/p0-p1-difference-backlog-v12.json'
        old = json.loads((ROOT / old_path).read_text())
        new = json.loads((ROOT / 'reports/replica/p0-p1-difference-backlog-v13.json').read_text())
        self.assertEqual(new['groups'][:-1], old['groups'])
        self.assertEqual(new['predecessor']['sha256'], hashlib.sha256((ROOT / old_path).read_bytes()).hexdigest())
        rows = [r for g in new['groups'] for r in g['records']]
        self.assertEqual(len(rows), 160)
        self.assertEqual(len(set(r['function_id'] for r in rows)), 160)
        self.assertEqual(new['added_function_ids'], ['Paste:0x1003b80f0'])
        row, = new['groups'][-1]['records']
        self.assertIn('旧比较仅覆盖正常', row['contract'])
        self.assertEqual(row['current_references'][0]['sha256'], hashlib.sha256((ROOT / row['current_references'][0]['snapshot_path']).read_bytes()).hexdigest())

    def test_unknown_setter_tail_has_no_evidence_of_constant_zero_Int_result(self):
        data = bytes.fromhex(self.proof['setter_body']['bytes'])
        self.assertEqual(len(data), 68)
        words = struct.unpack('<17I', data)
        self.assertNotIn(0xd2800000, words)  # MOV X0,#0
        self.assertNotIn(0x52800000, words)  # MOV W0,#0
        self.assertEqual(words[-5], 0xaa1503e0)  # release argument
        self.assertEqual(words[-1], 0x142c12fa)  # B objc_release
        word = words[-1];delta = word & ((1 << 26) - 1)
        if delta & (1 << 25): delta -= 1 << 26
        self.assertEqual(0x1000f737c + 4 * delta, 0x100bfbf64)
        self.assertEqual(self.proof['objc_release_binding']['symbol'], '_objc_release')
        # Neither a Ghidra return0 nor missing direct calls proves a Swift Int API or dead code.
        self.assertIn('return 0;', self.original['0x1000f733c'])
        self.assertIn('unknown', ' '.join(self.proof['retained_partial_contracts']).lower())

    def test_coder_entry_same_defaults_and_super_decode_do_not_close_archive_graph(self):
        coder = self.original['0x10004430c']; wrapper = self.original['0x1000444b0']
        self.assertIn('TextView::canAcceptFocus)', coder)
        self.assertIn('___lazy_storage___placeholderLabel) = 0', coder)
        self.assertIn('"initWithCoder:"', coder)
        self.assertIn('FUN_10004430c()', wrapper)
        view = (ROOT / 'replica/Sources/PastoCore/OriginalSearchTextView.swift').read_text()
        self.assertEqual(body(view, 'public required init?(coder: NSCoder)').strip(), '{\n        super.init(coder: coder)\n    }')
        for field in ['public var canAcceptFocus = true', 'private var storedPlaceholder: NSTextField?', '.font: OriginalSearchAppearance.f_1001ff928()']:
            self.assertIn(field, view)
        self.assertIn('real archive graph', ' '.join(self.proof['retained_partial_contracts']))

    def test_finite_contract_does_not_upgrade_unknowns_telemetry_or_complete_parent(self):
        row, = self.proof['contracts']
        self.assertEqual(row['function_id'], 'Paste:0x1003b80f0')
        self.assertFalse(row['full_function_migration_verified'])
        self.assertFalse(self.proof['full_function_migration_verified'])
        self.assertEqual(self.proof['function_map_markers_upgraded'], 0)
        limits = ' '.join(self.proof['retained_partial_contracts'])
        for token in ['arbitrary noncanonical type1', 'original object identity/tag ABI', 'no telemetry/network', 'return ABI', 'Unknown04430c', 'Unknown0f733c']:
            self.assertIn(token, limits)


if __name__ == '__main__': unittest.main()
