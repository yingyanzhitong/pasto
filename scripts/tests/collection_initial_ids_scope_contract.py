"""Delimit phase72's actual initial-ID route for earlier, frozen FRC contracts."""
from test_offline_p0_contracts import body


def without_initial_ID_route(source):
    from live_item_render_scope_contract import pre_live_render
    source = pre_live_render(source)
    old = '        let initial = (controller.fetchedObjects ?? []).map(\\.objectID)\n'
    new = '        let initial = initialObjectIDs()\n'
    if new not in source:
        return source
    if source.count(new) != 1 or old in source:
        raise AssertionError('Unreviewed initial-ID constructor replacement')
    start = source.index('    // 366344: a clean context')
    end = source.index('    // 3669fc:', start)
    methods = source[start:end]
    signatures = ['private func initialObjectIDs()', 'private func fetchInitialObjectIDs()',
                  'private func fetchedObjectID(at index:']
    for signature in signatures:
        declaration = '    ' + signature
        at = methods.index(declaration)
        method = body(methods, signature)
        stop = methods.index(method, at) + len(method)
        methods = methods[:at] + methods[stop:]
    remaining = [line.strip() for line in methods.splitlines() if line.strip() and not line.strip().startswith('//')]
    if remaining:
        raise AssertionError('Unexpected code beside three initial-ID methods')
    return (source[:start] + source[end:]).replace(new, old, 1)


def assert_initial_ID_route_only(test, current, previous):
    test.assertEqual(without_initial_ID_route(current), previous)
