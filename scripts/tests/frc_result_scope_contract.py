"""Compare real method segments outside the explicit FRC result-source migration."""
import re
from native_tab_list_delivery_scope_contract import pre_native_tab_list_delivery
from test_offline_p0_contracts import body


def query_result_segments(source):
    # Every replaced block has one exact approved old/new shape; every other character is compared.
    alternatives = [
        ('                    identifiers = Set(try store.searchNativeItems(identifiers: Array(found)).map(\\.id))\n',
         '                    installResultSource(store.makeSearchCollection(identifiers: found))\n'),
        ('                    identifiers = Set(entries.filter { found.contains($0.searchIdentifier) }.map(\\.id))\n',
         '                    installResultSource(nil)\n                    orderedIdentifiers = entries.filter { found.contains($0.searchIdentifier) }.map(\\.id)\n                    identifiers = Set(orderedIdentifiers)\n'),
        ('                identifiers = []\n', '                installResultSource(nil)\n')]
    result, end = [], 0
    for old, new in alternatives:
        present = [(text, match) for text in [old, new] for match in re.finditer('^' + re.escape(text), source, re.M)]
        if len(present) != 1: raise AssertionError('Unreviewed FRC result block')
        text, match = present[0]
        start = match.start()
        if start < end: raise AssertionError('Unexpected FRC result block order')
        result.append(source[end:start]); end = start + len(text)
    result.append(source[end:])
    return result


def assert_query_result_only(test, current, previous):
    test.assertEqual(query_result_segments(current), query_result_segments(previous))


def assert_factory_addition_only(test, current, previous, public=False):
    from item_order_scope_contract import without_list_factory, without_order_persistence
    current = without_list_factory(current, public=True) if public else without_order_persistence(current)
    marker = ('public ' if public else '') + 'func makeSearchCollection('
    declaration = '    ' + marker
    start = current.index(declaration); block = body(current, marker)
    end = current.index(block, start) + len(block)
    end += 1 if public else 2
    test.assertEqual((current[:start], current[end:]), (previous[:start], previous[start:]))
    if public:
        test.assertEqual(block.strip(), '{\n        persistence.makeSearchCollection(identifiers: identifiers)\n    }')
    else:
        test.assertEqual(block.strip(), '{\n        guard !identifiers.isEmpty else { return nil }\n        return ClipboardSearchCollection(context: context, identifiers: identifiers)\n    }')


def ui_init_segments(source):
    from stack_close_session_scope_contract import pre_stack_close_session
    source=pre_stack_close_session(source)
    marker = '        searchIndex.onCollectionUpdate = '
    if marker not in source: return [source[:source.index('        installListSelectionDelivery()')], source[source.index('        installListSelectionDelivery()'):]]
    start = source.index(marker); block = body(source, 'searchIndex.onCollectionUpdate =')
    expected = '''{ [weak self] identifiers in
            guard let self, !self.isCollectionSearchQueryEmpty else { return }
            self.pendingCollectionChangedIDs.formUnion(identifiers)
            self.objectWillChange.send()
        }'''
    if block != expected: raise AssertionError('Unreviewed FRC UI callback')
    end = source.index(block, start) + len(block) + 1
    return [source[:start], source[end:]]


def assert_visible_order_only(test, current, previous):
    from collection_membership_scope_contract import pre_collection_membership
    current = pre_collection_membership(current)
    from item_order_scope_contract import assert_history_list_projection_only
    marker = '        let items = Dictionary(uniqueKeysWithValues: store.items.map { ($0.id, $0) })'
    head, sep, tail = current.rpartition(marker);test.assertTrue(sep)
    old_head, sep, old_tail = previous.partition('        return store.items.filter { item in')
    test.assertTrue(sep)
    if 'listCollection?.value.identifiers' in head:
        assert_history_list_projection_only(test, head, old_head)
    else:
        test.assertEqual(head, old_head)
    test.assertEqual(tail, '''
        return searchIndex.orderedIdentifiers.compactMap { identifier in
            guard let item = items[identifier], showDeleted ? item.isDeleted : !item.isDeleted else { return nil }
            return item
        }
    }''')
    test.assertIn('searchIndex.identifiers.contains(item.id)', old_tail)
    test.assertIn('return $0.createdAt > $1.createdAt', old_tail)


def assert_ui_frc_only(test, current, previous):
    from item_order_scope_contract import without_list_UI_insertions
    current = without_list_UI_insertions(current); previous = without_list_UI_insertions(previous)
    left = ui_init_segments(current); right = ui_init_segments(previous)
    test.assertEqual(left[0], right[0])
    a, b = left[1], right[1]
    current_body = body(a, 'var visibleItems:'); old_body = body(b, 'var visibleItems:')
    assert_visible_order_only(test, current_body, old_body)
    for current_part, previous_part in zip(a.split(current_body), b.split(old_body)):
        if 'private func installListSelectionDelivery()' in current_part:
            assert_list_context_only(test, current_part, previous_part)
        else:
            test.assertEqual(current_part, previous_part)


def list_context_segments(source):
    source = pre_native_tab_list_delivery(source)
    old = '                id = board.id\n'
    new = '''                // Published boards project the managed type; nil is the existing legacy-group adapter.
                let context = OriginalCollectionListContext.f_1003b80f0(identifier: identifier,
                    rawType: Int64(board.rawType ?? 2), historyIdentifier: { ClipboardStore.historyListIdentifier })
                switch context {
                case .pinboard: id = board.id
                case .history: id = nil
                }
'''
    matches = [(text, match) for text in [old, new] for match in re.finditer('^' + re.escape(text), source, re.M)]
    if len(matches) != 1: raise AssertionError('Unreviewed list context projection block')
    text, match = matches[0]
    return source[:match.start()], source[match.end():]


def assert_list_context_only(test, current, previous):
    test.assertEqual(list_context_segments(current), list_context_segments(previous))
