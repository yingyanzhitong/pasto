"""Compare actual method segments outside the explicitly migrated SDK-write boundary.

No synthetic Swift source is built. The removed inline block is restricted to its
exact callback/error template; call arguments and every outside character match.
"""
import re


def write_segments(source):
    result, arguments, end = [], [], 0
    pattern = re.compile(r'^([ \t]*)(?:try await withCheckedThrowingContinuation|_ = try await Self\.writeSearchableItems)', re.M)
    for match in pattern.finditer(source):
        if match.start() < end:
            continue
        if source[match.start():].lstrip().startswith('_ ='):
            finish = source.find('\n', match.start())
            if finish < 0:
                finish = len(source)
            line = source[match.start():finish].strip()
            prefix = '_ = try await Self.writeSearchableItems('
            suffix = ', index: resolveWriteIndex())'
            if not line.endswith(suffix):
                raise AssertionError('Unexpected SDK write helper arguments')
            argument = line[len(prefix):-len(suffix)]
        else:
            start = source.index('{', match.start())
            depth, finish = 1, start + 1
            while depth:
                if source[finish] == '{': depth += 1
                if source[finish] == '}': depth -= 1
                finish += 1
            block = source[match.start():finish]
            if 'index.indexSearchableItems(' not in block:
                continue
            argument = block.split('index.indexSearchableItems(', 1)[1].split(') { error in', 1)[0]
            expected = ('try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<Void, Error>) in '
                        'index.indexSearchableItems(' + argument + ') { error in '
                        'if let error { continuation.resume(throwing: error) } else { continuation.resume() } } }')
            if re.sub(r'\s+', ' ', block.strip()) != expected:
                raise AssertionError('Removed write block had additional behavior')
        if argument not in ['changed', '[item]', 'live.map { searchableItem($0, isUpdate: false) }']:
            raise AssertionError('Unreviewed write input')
        result.append(source[end:match.start()])
        arguments.append(argument)
        end = finish
    result.append(source[end:])
    return result, arguments


def assert_write_scope_only(test, current, previous):
    test.assertEqual(write_segments(current), write_segments(previous))


def assert_service_initializer_only(test, current_source, previous_source):
    from test_offline_p0_contracts import body
    previous = body(previous_source, 'init(directoryURL:')
    service = body(current_source, 'init(directoryURL:')
    current = body(current_source, 'init(service:')
    prefix, separator, old_tail = previous.partition('        nativeIdentifierFormatKey =')
    test.assertTrue(separator)
    test.assertEqual(service[:service.index('        index = CSSearchableIndex')], prefix)
    test.assertEqual(service[service.index('        index = CSSearchableIndex'):], '        index = CSSearchableIndex(name: domain)\n    }')
    test.assertTrue(current.startswith('{\n        domain = service.domain\n'))
    old_before, old_separator, old_after = (separator + old_tail).partition('        index = CSSearchableIndex(name: domain)\n')
    new_before, new_separator, new_after = current[len('{\n        domain = service.domain\n'):].partition('        index = service.index\n        resolveWriteIndex = { [weak service] in service?.index }\n')
    test.assertTrue(old_separator and new_separator)
    test.assertEqual((new_before, new_after), (old_before, old_after))


def assert_ui_service_composition_only(test, current, previous):
    old_field = '    private let searchIndex: ReplicaSearchIndex\n'
    new_field = '    private let searchService: ReplicaSpotlightService\n' + old_field
    old_call = '        searchIndex = ReplicaSearchIndex(directoryURL: store.directoryURL, store: store)\n'
    new_call = ('        let service = ReplicaSpotlightService(directoryURL: store.directoryURL)\n'
                '        searchService = service\n        searchIndex = ReplicaSearchIndex(service: service, store: store)\n')
    for value, token in [(previous, old_field), (previous, old_call), (current, new_field), (current, new_call)]:
        test.assertEqual(value.count(token), 1)
    old_prefix, old_rest = previous.split(old_field)
    new_prefix, new_rest = current.split(new_field)
    test.assertEqual((new_prefix, *new_rest.split(new_call)), (old_prefix, *old_rest.split(old_call)))
