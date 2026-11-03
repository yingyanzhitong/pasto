"""Reverse only phase182 menu preparation/placement deltas."""
CHANGES = [['replica/Sources/Pasto/UI/ReplicaSearchSuggestionsMenu.swift', '        guard let parent = anchorView.window else { return }\n        self.rows = rows\n        self.anchorView = anchorView\n        accept = onAccept\n        escape = onEscape\n        guard !rows.isEmpty else { dismiss(); return }\n        scroller.setRows(rows)\n        selectedIndex = nil\n        scroller.select(selectedIndex)', '        escape = onEscape\n        self.rows = rows\n        accept = onAccept\n        selectedIndex = nil\n        scroller.setRows(rows)\n        scroller.select(selectedIndex)\n        guard let parent = anchorView.window else { return }', 1], ['replica/Sources/Pasto/UI/ReplicaSearchSuggestionsMenu.swift', '        orderFront(nil)\n        installMonitors(parent: parent)', '        orderFront(nil)\n        self.anchorView = anchorView\n        installMonitors(parent: parent)', 1]]

def pre_suggestion_menu_prepare(source):
    from suggestion_list_lifecycle_scope_contract import pre_suggestion_list_lifecycle
    source = pre_suggestion_list_lifecycle(source)
    for _, old, new, count in reversed(CHANGES):
        if new in source:
            assert source.count(new) == count
            source = source.replace(new, old)
    return source

def pre_suggestion_menu_prepare_bytes(path):
    data = path.read_bytes()
    return pre_suggestion_menu_prepare(data.decode()).encode() if path.suffix == '.swift' else data

HISTORICAL_TEST_CHANGES = [['scripts/tests/suggestion_anchor_owner_scope_contract.py', 'def pre_suggestion_anchor_owner(source):\n', 'def pre_suggestion_anchor_owner(source):\n    from suggestion_menu_prepare_scope_contract import pre_suggestion_menu_prepare\n    source = pre_suggestion_menu_prepare(source)\n', 1], ['scripts/tests/suggestion_anchor_owner_scope_contract.py', '    data = pre_suggestion_anchor_owner_bytes(path)\n', '    from suggestion_menu_prepare_scope_contract import pre_suggestion_menu_prepare_history_bytes\n    data = pre_suggestion_menu_prepare_history_bytes(path)\n    if path.suffix == ".swift":\n        data = pre_suggestion_anchor_owner(data.decode()).encode()\n', 1], ['scripts/tests/test_p1_repair_suggestion_anchor_owner.py', 'class SuggestionAnchorOwnerContracts', 'from suggestion_menu_prepare_scope_contract import pre_suggestion_menu_prepare_bytes, pre_suggestion_menu_prepare_history_bytes\nclass SuggestionAnchorOwnerContracts', 1], ['scripts/tests/test_p1_repair_suggestion_anchor_owner.py', 'hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),h)', 'hashlib.sha256(pre_suggestion_menu_prepare_bytes(ROOT/p)).hexdigest(),h)', 1], ['scripts/tests/test_p1_repair_suggestion_anchor_owner.py', 'if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h:changed.append(p)', 'if hashlib.sha256(pre_suggestion_menu_prepare_bytes(ROOT/p)).hexdigest()!=h:changed.append(p)', 1], ['scripts/tests/test_p1_repair_suggestion_anchor_owner.py', 'self.assertEqual((ROOT/p).read_text(),expected.get(p,', 'self.assertEqual(pre_suggestion_menu_prepare_history_bytes(ROOT/p).decode(),expected.get(p,', 1]]

def pre_suggestion_menu_prepare_history_bytes(path):
    from suggestion_list_lifecycle_scope_contract import pre_suggestion_list_lifecycle_history_bytes
    data = pre_suggestion_list_lifecycle_history_bytes(path)
    if path.suffix == ".swift":
        data = pre_suggestion_menu_prepare(data.decode()).encode()
    if path.suffix != '.py':
        return data
    source = data.decode()
    for changed, old, new, count in reversed(HISTORICAL_TEST_CHANGES):
        if (path.as_posix() == changed or path.as_posix().endswith('/' + changed)) and new in source:
            assert source.count(new) == count
            source = source.replace(new, old)
    return source.encode()
