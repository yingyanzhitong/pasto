"""Native text-model parent chain: binary/source contracts, no framework execution."""
from pathlib import Path
import difflib
import gc
import hashlib
import json
import struct
import sys
import unittest
import weakref

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/tests')]
from function_ledger import source_fragments
from test_offline_p0_contracts import body

D = ROOT / '.local/p0-p1-parent-review/2026-11-03-text-model'
MODEL = 'replica/Sources/PastoCore/OriginalTextPreviewModel.swift'
UI = 'replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


class TextModelParentContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = json.loads((D / 'contract.json').read_text())
        cls.base = json.loads((D / 'baseline.json').read_text())
        cls.model = (ROOT / MODEL).read_text()
        cls.ui = (ROOT / UI).read_text()
        cls.view = body(cls.ui, 'private final class ReplicaInlineTextPreviewContent:')
        cls.before = body((D / 'before' / UI).read_text(), 'private final class ReplicaInlineTextPreviewContent:')
        cls.n = {}
        exec((ROOT / cls.p['decoder']['path']).read_text().split('selectors=[]', 1)[0], cls.n)

    def test_original_fragments_binary_and_current_sources_fresh(self):
        cache = {}
        self.assertEqual(len(self.p['original_fragments']), 13)
        for r in self.p['original_fragments']:
            path = ROOT / r['path']
            if path not in cache:
                cache[path] = source_fragments(path)
            self.assertEqual(cache[path][r['function_id'].split(':')[1]]['sha256'], r['sha256'])
        for k in ['binary', 'decoder']:
            self.assertEqual(sha(ROOT / self.p[k]['path']), self.p[k]['sha256'])
        for k in ['current_sources', 'shared_sources']:
            for path, h in self.p[k].items():
                self.assertEqual(sha(ROOT / path), h, path)

    def test_complete_native_ranges_and_all_direct_branches(self):
        self.assertEqual(len(self.p['machine_ranges']), 13)
        self.assertEqual(len(self.p['branches']), 252)
        for r in self.p['machine_ranges']:
            data = self.n['read'](int(r['address'], 16), int(r['end'], 16) - int(r['address'], 16))
            self.assertEqual(data.hex(), r['bytes'])
            self.assertEqual(hashlib.sha256(data).hexdigest(), r['sha256'])
        for r in self.p['branches']:
            pc = int(r['pc'], 16)
            w = struct.unpack('<I', self.n['read'](pc, 4))[0]
            self.assertEqual(hex(w), r['word'])
            v = w & 0x3ffffff
            if v & (1 << 25): v -= 1 << 26
            self.assertEqual(hex(pc + 4 * v), r['target'])

    def test_selector_and_import_fixup_chains(self):
        self.assertEqual(len(self.p['selectors']), 25)
        self.assertEqual(len(self.p['imports']), 168)
        raw = self.n['raw']
        fixup = self.n['fixup'][0]
        h = struct.unpack_from('<7I', raw, fixup)
        for r in self.p['selectors'] + self.p['imports']:
            value, chain = self.n['reachable_pointer'](int(r['pointer'], 16))
            self.assertEqual(chain, r['chain'])
            if 'ordinal' in r:
                self.assertTrue(value >> 63)
                self.assertEqual(value & 0xffffff, r['ordinal'])
                entry = struct.unpack_from('<I', raw, fixup + h[2] + 4 * r['ordinal'])[0]
                at = fixup + h[3] + (entry >> 9)
                self.assertEqual(raw[at:raw.index(b'\0', at)].decode(), r['name'])
            else:
                self.assertFalse(value >> 63)
                address = self.n['base'] + (value & ((1 << 36) - 1))
                self.assertEqual(hex(address), r['target'])
                self.assertEqual(self.n['read'](address, len(r['name']) + 1), r['name'].encode() + b'\0')

    def test_three_native_weak_reads_and_callback_after_model_release(self):
        imports = {r['pc']: r['name'] for r in self.p['imports'] if r['function_id'] == 'Paste:0x1003c04f0'}
        self.assertEqual([pc for pc, name in imports.items() if name == '_swift_weakLoadStrong'],
                         ['0x1003c0518', '0x1003c0548', '0x1003c0564'])
        self.assertEqual(imports['0x1003c0538'], '_swift_release')
        self.assertEqual(imports['0x1003c0540'], '_objc_release')
        self.assertEqual(imports['0x1003c05a0'], '_swift_release')
        self.assertEqual(self.n['read'](0x1003c0524, 4).hex(), '141c00f9')
        self.assertEqual(struct.unpack('<I', self.n['read'](0x1003c05a4, 4))[0], 0xd63f02a0)
        self.assertEqual(next(r['target'] for r in self.p['branches'] if r['pc'] == '0x1003c0554'), '0x1003c05d4')

    def test_independent_model_observes_before_first_reload(self):
        s = body(self.model, 'public init?(input: ClipboardRestoreItem)')
        self.assertLess(s.index('input.observeChanges'), s.index('reload()'))
        self.assertIn('[weak self]', s)
        self.assertNotIn('guard let self', s)
        for token in ['private var input:', 'private var observation:', 'public private(set) var originalText',
                      'public private(set) var editingText', 'public var item: ClipboardRestoreItem { input }']:
            self.assertIn(token, self.model)

    def test_deleted_event_exits_before_any_weak_phase(self):
        s = body(self.model, 'private static func receive(')
        phases = ['guard !current.isDeleted else { return }', 'replaceInputAndReleasePrevious(current, from: loadOwner)',
                  'reload(from: loadOwner)', 'let callback = changeCallback(from: loadOwner)', 'callback?()']
        self.assertEqual([s.index(x) for x in phases], sorted(s.index(x) for x in phases))
        self.assertNotIn('loadOwner()', s)
        self.assertNotIn('guard let owner', s)

    def test_each_phase_independently_loads_owner(self):
        for sig in ['private static func replaceInput(_', 'private static func reload(from', 'private static func changeCallback(from']:
            self.assertEqual(body(self.model, sig).count('loadOwner()'), 1)
        self.assertEqual(self.model.count('@inline(never)'), 4)
        self.assertIn('withExtendedLifetime(replaceInput(current, from: loadOwner)) {}', self.model)
        s = body(self.model, 'private static func replaceInput(_')
        self.assertLess(s.index('let previous = owner.input'), s.index('owner.input = current'))
        self.assertLess(s.index('owner.input = current'), s.index('return previous'))
        self.assertEqual(body(self.model, 'private static func changeCallback(from').strip(),
                         '{\n        guard let owner = loadOwner() else { return nil }\n        return owner.onChange\n    }')

    def test_reload_reads_current_first_representation_then_both_values(self):
        s = body(self.model, 'public func reload()')
        phases = ['input.nativeObject', 'ClipboardItemDataPersistence.readItems(from: object)',
                  'originalText = items.first?.f_10037d33c()', 'editingText = OriginalPreviewAttributedText.normalizedEditingText(originalText)']
        self.assertEqual([s.index(x) for x in phases], sorted(s.index(x) for x in phases))
        for token in ['resolvedItem()', 'observeItem()', 'Task', '.payloads', 'isEditable']:
            self.assertNotIn(token, self.model)

    def test_real_native_entry_reaches_new_model_without_dto_observer(self):
        s = body(self.ui, 'func makeOriginalReplicaNativePreview(')
        self.assertIn('makeReplicaTextPreview(state: state, item: nil, input: input)', s)
        s = body(self.view, 'init(state: ReplicaUIState, item: ClipboardItem?, input: ClipboardRestoreItem?)')
        self.assertIn('input.flatMap { OriginalTextPreviewModel(input: $0) }', s)
        self.assertIn('if nativeModel != nil { nativeSource = nil }', s)
        self.assertIn('initial = nativeModel.originalText', s)
        self.assertIn('nativeModel?.editingText ?? OriginalPreviewAttributedText.normalizedEditingText(initial)', s)

    def test_view_callback_is_weak_and_only_nonediting_redraws(self):
        s = body(self.view, 'init(state: ReplicaUIState, item: ClipboardItem?, input: ClipboardRestoreItem?)')
        self.assertIn('nativeModel.onChange = { [weak self] in\n                guard let self, !self.text.isEditable else { return }\n                self.displayStoredModel()', s)
        self.assertNotIn('isEditable', body(self.model, 'private static func receive('))
        self.assertIn('nativeTextModel?.originalText ?? fallbackOriginalText', self.view)
        self.assertIn('nativeTextModel?.editingText ?? fallbackEditingText', self.view)

    def test_commit_uses_updated_model_entity_and_preserves_cleanup(self):
        s = body(self.view, 'func commitPreviewEditing()')
        self.assertIn('if let editInput = nativeTextModel?.item ?? editInput', s)
        self.assertLess(s.index('updateTextPreviewItem(editInput'), s.index('reloadStoredContent()'))
        before = body(self.before, 'func commitPreviewEditing()')
        self.assertEqual(s.replace('if let editInput = nativeTextModel?.item ?? editInput', 'if let editInput'), before)
        s = body(self.view, 'private func reloadStoredContent()')
        self.assertLess(s.index('nativeTextModel.reload()'), s.index('displayStoredModel()'))

    def test_edit_transitions_focus_and_display_methods_unchanged(self):
        for sig in ['func beginPreviewEditing()', 'func cancelPreviewEditing()', 'func focusPreviewEditing()',
                    'private func displayStoredModel()', 'private func receiveStoredText(',
                    'private func receiveStoredModel(', 'private func replaceStoredModel(',
                    'private static func attributedContent(']:
            self.assertEqual(body(self.view, sig), body(self.before, sig), sig)

    def test_old_value_fallback_remains_separate(self):
        s = body(self.view, 'init(state: ReplicaUIState, item: ClipboardItem?, input: ClipboardRestoreItem?)')
        for token in ['else if let input { nativeSource = input.observeItem() }', 'state.store.observeItem(id: itemID)',
                      'nativeSource.onTextChange', 'state.store.$items.sink', 'self.receiveStoredModel(current)']:
            self.assertIn(token, s)
        self.assertIn('fallbackOriginalText = text', body(self.view, 'private func replaceStoredText('))

    def test_only_one_existing_production_changed_one_added_and_old_tests_preserved(self):
        files = self.base['files']
        production = {p: h for p, h in files.items() if p.startswith('replica/Sources/')}
        self.assertEqual(len(production), 247)
        changed = {p for p, h in production.items() if sha(ROOT / p) != h}
        self.assertEqual(changed, {UI})
        current = {str(p.relative_to(ROOT)) for p in (ROOT / 'replica/Sources').rglob('*') if p.is_file()}
        self.assertEqual(current - set(production), {MODEL})
        for p, h in files.items():
            if p != UI:
                self.assertEqual(sha(ROOT / p), h, p)

    def test_historical_neighbor_invariants_replaced_only_for_three_changed_methods(self):
        p = json.loads((ROOT / '.local/p0-repair/phase-187/text-edit-mode-contract.json').read_text())
        changed = set()
        for row in p['unchanged_methods']:
            now = body((ROOT / row['path']).read_text(), row['symbol'])
            if hashlib.sha256(now.encode()).hexdigest() != row['body_sha256']:
                changed.add(row['symbol'])
        self.assertEqual(changed, {'func commitPreviewEditing()', 'private func reloadStoredContent()',
                                   'private func replaceStoredText('})
        # All three have explicit native/fallback assertions above; the other nine retain their old bodies.
        self.assertEqual(len(p['unchanged_methods']) - len(changed), 9)

    def test_fixed_scope_not_inflated_by_support_functions(self):
        s = json.loads((ROOT / 'reports/replica/p0-p1-review-scope-v6.json').read_text())
        self.assertEqual(s['denominator'], 959)
        ids = [r['function_id'] for r in s['functions']]
        self.assertEqual(ids.count(self.p['primary_function_id']), 1)
        self.assertEqual(self.p['primary_function_id'], 'Paste:0x1003c04f0')
        for k in ['full_function_migration_verified', 'compiled', 'application_executed', 'framework_executed']:
            self.assertFalse(self.p[k])


class WeakPhaseTraceModels(unittest.TestCase):
    """Python lifetime witnesses describe intended source order, not Swift ARC runtime proof."""
    def run_trace(self, deleted=False, absent_at=None, editing=False):
        class Model:
            def __init__(self): self.item = 'old'; self.value = 'old'; self.on_change = None
        owner = Model()
        roots = [owner]
        ref = weakref.ref(owner)
        events = []
        del owner
        def load(phase):
            if phase == absent_at: roots.clear(); gc.collect()
            events.append(('weak', phase))
            return ref()
        def replace():
            owner = load('replace')
            if owner is None: return None
            previous = owner.item; owner.item = 'new'; events.append(('replace', owner.item))
            return previous
        def reload():
            owner = load('reload')
            if owner is None: return
            owner.value = owner.item; events.append(('reload', owner.value))
        def callback():
            owner = load('callback')
            if owner is None: return None
            return owner.on_change
        def display():
            if editing: return
            events.append(('display', 'new'))
        roots[0].on_change = display
        if deleted: return events, ref
        old = replace(); del old
        reload()
        change = callback()
        if change: change()
        return events, ref

    def test_deleted_candidate_never_loads_owner(self):
        events, _ = self.run_trace(deleted=True)
        self.assertEqual(events, [])

    def test_owner_absent_first_phase_still_attempts_later_phases(self):
        events, ref = self.run_trace(absent_at='replace')
        self.assertIsNone(ref())
        self.assertEqual(events, [('weak', 'replace'), ('weak', 'reload'), ('weak', 'callback')])

    def test_owner_lost_between_replace_and_reload_stops_only_missing_work(self):
        events, ref = self.run_trace(absent_at='reload')
        self.assertIsNone(ref())
        self.assertEqual(events, [('weak', 'replace'), ('replace', 'new'), ('weak', 'reload'), ('weak', 'callback')])

    def test_model_updates_even_when_editor_keeps_input(self):
        events, _ = self.run_trace(editing=True)
        self.assertIn(('reload', 'new'), events)
        self.assertNotIn(('display', 'new'), events)
        self.assertEqual(events[-1], ('weak', 'callback'))

    def test_copied_callback_does_not_retain_model(self):
        class Model: pass
        roots = [Model()]
        roots[0].callback = lambda: 'callback-result'
        ref = weakref.ref(roots[0])
        def copy():
            owner = ref()
            return owner.callback
        callback = copy()
        roots.clear(); gc.collect()
        self.assertIsNone(ref())
        self.assertEqual(callback(), 'callback-result')


if __name__ == '__main__':
    unittest.main()
