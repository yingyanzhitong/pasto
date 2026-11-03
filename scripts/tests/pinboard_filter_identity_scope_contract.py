"""Reverse phase176 raw String group filter identity and native name resolution only."""
CHANGES = [('replica/Sources/Pasto/UI/SearchEditor.swift', 'date(OriginalSearchDateFilter), pinboard(UUID)', 'date(OriginalSearchDateFilter), pinboard(String)', 1), ('replica/Sources/Pasto/UI/SearchEditor.swift', '            case 5:\n                guard let id = UUID(uuidString: value) else { return nil }\n                selection = .pinboard(id)', '            case 5: selection = .pinboard(value)', 1), ('replica/Sources/Pasto/UI/FilterBrowser.swift', '        case let .pinboard(id): value = id.uuidString\n', '        case let .pinboard(id): value = id\n', 1), ('replica/Sources/Pasto/UI/FilterBrowser.swift', '        case let .pinboard(id): title = store.pinboards.first { $0.id == id }?.name ?? "Pasto"', '        case let .pinboard(id):\n            value = id\n            title = store.tabListTarget(identifier: id)?.name ?? id', 1), ('replica/Sources/Pasto/UI/FilterBrowser.swift', '            guard case let .filter(5, value) = node, let id = UUID(uuidString: value) else { return nil }\n            return .pinboard(id)', '            guard case let .filter(5, value) = node else { return nil }\n            return .pinboard(value)', 1)]

def pre_pinboard_filter_identity(source):
    from filter_model_query_scope_contract import pre_filter_model_query
    source = pre_filter_model_query(source)
    for _, old, new, count in reversed(CHANGES):
        if new in source:
            assert source.count(new) == count
            source = source.replace(new, old)
    return source

def pre_pinboard_filter_identity_bytes(path):
    data = path.read_bytes()
    return pre_pinboard_filter_identity(data.decode()).encode() if path.suffix == '.swift' else data

HISTORICAL_TEST_CHANGES = [['scripts/tests/text_storage_owner_scope_contract.py', 'def pre_text_storage_owner(source):\n', 'def pre_text_storage_owner(source):\n    from pinboard_filter_identity_scope_contract import pre_pinboard_filter_identity\n    source = pre_pinboard_filter_identity(source)\n', 1], ['scripts/tests/text_storage_owner_scope_contract.py', '    data = pre_text_storage_owner_bytes(path)\n', '    from pinboard_filter_identity_scope_contract import pre_pinboard_filter_identity_history_bytes\n    data = pre_pinboard_filter_identity_history_bytes(path)\n    if path.suffix == ".swift":\n        data = pre_text_storage_owner(data.decode()).encode()\n', 1], ['scripts/tests/test_p1_repair_coder_source_resolution.py', 'hashlib.sha256(Path(p).read_bytes()).hexdigest(),h,p)', 'hashlib.sha256(pre_text_storage_owner_history_bytes(Path(p))).hexdigest(),h,p)', 1], ['scripts/tests/test_p1_repair_text_storage_owner.py', '\nclass TextStorageOwner', '\nfrom pinboard_filter_identity_scope_contract import pre_pinboard_filter_identity_bytes, pre_pinboard_filter_identity_history_bytes\n\nclass TextStorageOwner', 1], ['scripts/tests/test_p1_repair_text_storage_owner.py', 'data=(ROOT/p).read_bytes();old=', 'data=pre_pinboard_filter_identity_bytes(ROOT/p);old=', 1], ['scripts/tests/test_p1_repair_text_storage_owner.py', 'self.assertEqual((ROOT/p).read_text(),expected.get(p,', 'self.assertEqual(pre_pinboard_filter_identity_history_bytes(ROOT/p).decode(),expected.get(p,', 1], ['scripts/tests/test_p1_repair_suggestion_source_service.py', '\n\nclass SuggestionSourceServiceContracts', '\nfrom pinboard_filter_identity_scope_contract import pre_pinboard_filter_identity_bytes\n\nclass SuggestionSourceServiceContracts', 1], ['scripts/tests/test_p1_repair_suggestion_source_service.py', "self.assertEqual((ROOT / path).read_bytes(), (self.phase / 'after' / path).read_bytes())", "self.assertEqual(pre_pinboard_filter_identity_bytes(ROOT / path), (self.phase / 'after' / path).read_bytes())", 1], ['scripts/tests/test_p1_repair_suggestion_source_service.py', "self.assertEqual((ROOT / 'replica/Sources/Pasto/UI/SearchEditor.swift').read_bytes(),", "self.assertEqual(pre_pinboard_filter_identity_bytes(ROOT / 'replica/Sources/Pasto/UI/SearchEditor.swift'),", 1], ['scripts/tests/test_p1_repair_suggestion_source_service.py', "        self.assertIn('UUID(uuidString: value)', builder)", "        self.assertNotIn('UUID(uuidString: value)', builder)\n        self.assertIn('return .pinboard(value)', builder)", 1]]

def pre_pinboard_filter_identity_history_bytes(path):
    from filter_model_query_scope_contract import pre_filter_model_query_history_bytes
    data = pre_filter_model_query_history_bytes(path)
    if path.suffix == ".swift":
        data = pre_pinboard_filter_identity(data.decode()).encode()
    if path.suffix != '.py':
        return data
    source = data.decode()
    for changed, old, new, count in reversed(HISTORICAL_TEST_CHANGES):
        if (path.as_posix() == changed or path.as_posix().endswith('/' + changed)) and new in source:
            assert source.count(new) == count
            source = source.replace(new, old)
    return source.encode()
