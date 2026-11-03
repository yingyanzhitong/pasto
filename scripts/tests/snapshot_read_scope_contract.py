from native_title_scope_contract import pre_native_title
from item_order_scope_contract import without_order_projection, without_order_commit
"""Locate real queue-confined producers through verified forwarding wrappers.
No synthesized Swift or replacement implementation is used by source assertions.
"""
from pathlib import Path
import re
from test_offline_p0_contracts import body as source_body
ROOT = Path(__file__).resolve().parents[2]
READER = ROOT / 'replica/Sources/PastoCore/ClipboardSnapshotReader.swift'
READ_NAMES = ['searchIndexIdentifiers', 'searchIndexRecords', 'searchItems', 'searchNativeItems', 'revision', 'read']

def body(source, marker):
    source = pre_native_title(source)
    # Static projection keeps the same actual body, now callable on a private queue.
    if marker.startswith('private func item(') and marker not in source:
        marker = marker.replace('private func item(', 'nonisolated static func item(', 1)
    if marker.startswith('private func documents(') and marker not in source and 'private let snapshotReader:' in source:
        return source_body(pre_native_title(READER.read_text()), marker)
    result = source_body(source, marker)
    if 'private let snapshotReader:' in source:
        for name in READ_NAMES:
            if marker.startswith('func ' + name + '('):
                assert 'try snapshotReader.' + name + '(' in result
                if name != 'revision':
                    assert re.fullmatch(r'\{\s*try snapshotReader\.' + name + r'\([^{}]*\)\s*\}', result)
                return source_body(pre_native_title(READER.read_text()), 'func ' + name + '(')
    if marker.startswith('private func transactions(') and 'try reader.transactions(after: token)' in result:
        assert result.strip() == '{\n        try reader.transactions(after: token)\n    }'
        return source_body(pre_native_title(READER.read_text()), 'func transactions(')
    return result

def projection_spelling(source):
    """Explicit read-move qualifiers/reset and the separately checked phase70 order metadata differ."""
    return without_order_projection(source).replace('ClipboardPersistence.decode(', 'decode(').replace('Self.decode(', 'decode(').replace('.map(ClipboardPersistence.item)', '.map(item)').replace('            defer { context.reset() }\n', '')

def commit_business_body(source):
    source = pre_native_title(source)
    result = source_body(source, 'func commit<T>(')
    added = '''                    // Store callers hold their existing cross-process lock through this save/cursor update.
                    viewHistoryToken = context.persistentStoreCoordinator?.currentPersistentHistoryToken(fromStores: nil)
                    viewRevision = root.value(forKey: "revision") as? UUID
'''
    return without_order_commit(result.replace(added, '', 1))


def assert_history_queue_only(test, current, previous, check_observe=True):
    """Real unchanged consumer/reducer/token lifecycle; moved producer checked separately."""
    for marker in (['func observe(_ consume:'] if check_observe else []) + ['func process() async']:
        test.assertEqual(source_body(current, marker), source_body(previous, marker))
    marker = 'private func changes('
    a = source_body(current, marker); b = source_body(previous, marker)
    def split(value):
        head, middle = value.split('case .insert, .update:', 1)
        producer, tail = middle.split('case .delete:', 1)
        return head, producer, tail
    ah, producer, at = split(a); bh, old, bt = split(b)
    test.assertEqual((ah, at), (bh, bt))
    test.assertIn('identifier = reader.searchIdentifier(for: change.changedObjectID)', producer)
    test.assertIn('context.existingObject(with: change.changedObjectID)', old)
    for marker in ['private func notifications()']:
        test.assertEqual(source_body(current, marker).replace('reader.coordinator', 'context.persistentStoreCoordinator'), source_body(previous, marker))
    fetched = body(current, 'private func transactions(')
    # Queue reset and its explanatory comment are the only history request body additions.
    fetched = fetched.replace('            // Snapshot projections and history IDs share this queue; no stale registered Item may escape a batch.\n            context.reset()\n', '', 1)
    test.assertEqual(fetched, source_body(previous, 'private func transactions('))
