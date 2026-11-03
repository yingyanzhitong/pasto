"""Explicit phase70 deltas for historical source contracts; actual new paths have separate tests."""
from native_title_scope_contract import pre_native_title
from test_offline_p0_contracts import body
from native_application_scope_contract import pre_native_application

ORDER_MODEL = '        if includeItemOrder { ClipboardItemOrderPersistence.addField(to: model) }\n'
ORDER_PROJECT = '        try ClipboardItemOrderPersistence.project(&item, from: object)\n'
ORDER_BOOTSTRAP = '            try ClipboardItemOrderPersistence.bootstrap(in: context, root: root)\n'
ORDER_UPDATE = '                    ClipboardItemOrderPersistence.update(item, on: object)\n'
ORDER_ROOT = '                    root.setValue(Int64(1), forKey: ClipboardItemOrderPersistence.versionKey)\n'
ORDER_CONTENT = '        value.pinboardOrder = nil\n'


def without_order_model(source):
    source = pre_native_title(source)
    return source.replace(ORDER_MODEL, '', 1)


def without_order_projection(source):
    source = pre_native_application(source)
    return source.replace(ORDER_PROJECT, '', 1).replace(ORDER_BOOTSTRAP, '', 1).replace(ORDER_CONTENT, '', 1)


def without_order_commit(source):
    source = pre_native_title(source)
    return source.replace(ORDER_UPDATE, '', 1).replace(ORDER_ROOT, '', 1)


def assert_order_migration_only(test, current, previous):
    current = pre_native_title(current)
    marker = '        let legacyCandidates = ['
    a, candidates = current.split(marker, 1); b, old_candidates = previous.split(marker, 1)
    current_rows, tail = candidates.split('\n        ]', 1); old_rows, old_tail = old_candidates.split('\n        ]', 1)
    test.assertEqual((a, tail), (b, old_tail))
    new_row = '\n            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, includeItemOrder: false),'
    test.assertTrue(current_rows.startswith(new_row))
    test.assertEqual(current_rows.count('includeItemOrder: false'), 8)
    test.assertEqual(current_rows[len(new_row):].replace(', includeItemOrder: false', ''), old_rows)


def without_list_route(source):
    return source.replace('        installListCollectionSource()\n', '', 1).replace('                self.installListCollectionSource()\n', '', 1)


def without_list_factory(source, public=False):
    source = pre_native_application(source)
    marker = ('public ' if public else '') + 'func makeListCollection('
    declaration = '    ' + marker
    if declaration not in source: return source
    start = source.index(declaration); block = body(source, marker)
    end = source.index(block, start) + len(block) + (1 if public else 2)
    return source[:start] + source[end:]


def without_list_request(source):
    from native_group_write_scope_contract import pre_native_group_write
    source = pre_native_group_write(source)
    marker = '    // 329088: history uses its timestamp; pinboard uses the Item\'s order, not the List\'s index.\n'
    if marker not in source: return source
    start = source.index(marker); actual = body(source, 'func itemRequest(for list:')
    end = source.index(actual, start) + len(actual) + 2
    return source[:start] + source[end:]


def without_list_UI_insertions(source):
    from live_item_render_scope_contract import pre_live_render
    source = pre_live_render(source)
    source = source.replace('    private var listCollection: ClipboardSearchCollection?\n    private var listCollectionObservation: AnyCancellable?\n', '', 1)
    declaration = '    private func installListCollectionSource()'
    if declaration in source:
        start = source.index(declaration); actual = body(source, 'private func installListCollectionSource()')
        end = source.index(actual, start) + len(actual) + 2
        source = source[:start] + source[end:]
    source = without_list_route(source)
    for comment in [
        '        // Until the managed collection source is migrated, only data/registry changes\n        // use this snapshot adapter. List colors/capacity have their own synchronous stream.\n',
        '        // Legacy value/registry adapters still refresh payload snapshots and selection.\n        // Managed list membership/order now arrives through its retained FRC source.\n']:
        source = source.replace(comment, '', 1)
    return source


def assert_history_list_projection_only(test, current, previous):
    signature = 'if isCollectionSearchQueryEmpty'
    current_history = body(current, signature); previous_history = body(previous, signature)
    test.assertEqual(current.split(current_history), previous.split(previous_history))
    if 'listCollection?.value.identifiers' not in previous_history:
        test.assertIn('store.items(in: pinboardID)', previous_history)
        for token in ['if showDeleted', 'listCollection?.value.identifiers ?? []', 'let native = identifiers.compactMap',
                      'let legacy = store.items(in: pinboardID).filter { $0.pinboardOwnerID != pinboardID }',
                      'Set(identifiers).union(legacy.map(\\.id))', 'return native']:
            test.assertIn(token, current_history)
    else:
        test.assertEqual(current_history, previous_history)


def without_order_persistence(source):
    source = without_list_factory(source)
    source = without_order_model(without_order_projection(without_order_commit(source)))
    source = source.replace('includeTypedItem: Bool = true,\n                                  includeItemOrder: Bool = true)', 'includeTypedItem: Bool = true)', 1)
    source = source.replace('            makeModel(includeNativeIdentity: true, preserveItemKeyInHistory: true, includeItemOrder: false),\n', '', 1)
    source = source.replace(', includeItemOrder: false', '')
    return source


def assert_common_FRC_ctor_only(test, current_source, previous_source):
    from collection_initial_ids_scope_contract import without_initial_ID_route
    current_source = without_initial_ID_route(current_source)
    old = body(previous_source, 'init(context: NSManagedObjectContext, identifiers:')
    current = body(current_source, 'init(context: NSManagedObjectContext, request:')
    start = '        controller = NSFetchedResultsController('
    old_common = old[old.index(start):]
    diagnostic = '''        if initial.count != identifiers.count {
            logger.error("Search found \\(identifiers.count) identifiers but fetched \\(initial.count) objects")
        }
'''
    test.assertEqual(current[current.index(start):], old_common.replace(diagnostic, '', 1))
    convenience = body(current_source, 'convenience init(context:')
    test.assertIn('PastoItemEntity.defaultFetchRequest()', convenience)
    test.assertIn('self.init(context: context, request: request)', convenience)
    test.assertIn('if objectIDs.count != identifiers.count', convenience)
