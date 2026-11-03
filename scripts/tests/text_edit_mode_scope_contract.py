"""Reverse only phase187 text editing begin/cancel display deltas."""
CHANGES = [['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift', '    func beginPreviewEditing() {\n        text.isEditable = true\n        reloadStoredContent()\n        window?.makeFirstResponder(text)\n    }', '    func beginPreviewEditing() {\n        text.isEditable = true\n        displayStoredModel()\n    }', 1], ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift', '    func cancelPreviewEditing() {\n        text.isEditable = false\n        reloadStoredContent()\n    }', '    func cancelPreviewEditing() {\n        text.isEditable = false\n        displayStoredModel()\n    }', 1]]

def pre_text_edit_mode(source):
    from font_trait_reads_scope_contract import pre_font_trait_reads
    source = pre_font_trait_reads(source)
    for _, old, new, count in reversed(CHANGES):
        if new in source:
            assert source.count(new) == count
            source = source.replace(new, old)
    return source

def pre_text_edit_mode_bytes(path):
    data = path.read_bytes()
    return pre_text_edit_mode(data.decode()).encode() if path.suffix == '.swift' else data

HISTORICAL_TEST_CHANGES = [['scripts/tests/suggestion_description_scope_contract.py', 'def pre_suggestion_description(source):\n', 'def pre_suggestion_description(source):\n    from text_edit_mode_scope_contract import pre_text_edit_mode\n    source = pre_text_edit_mode(source)\n', 1], ['scripts/tests/suggestion_description_scope_contract.py', '    data = pre_suggestion_description_bytes(path)\n', '    from text_edit_mode_scope_contract import pre_text_edit_mode_history_bytes\n    data = pre_text_edit_mode_history_bytes(path)\n    if path.suffix == ".swift":\n        data = pre_suggestion_description(data.decode()).encode()\n', 1], ['scripts/tests/test_p1_repair_suggestion_description.py', 'class SuggestionDescriptionContracts', 'from text_edit_mode_scope_contract import pre_text_edit_mode_bytes, pre_text_edit_mode_history_bytes\nclass SuggestionDescriptionContracts', 1], ['scripts/tests/test_p1_repair_suggestion_description.py', 'self.assertEqual((ROOT/p).read_text(),expected.get(p,', 'self.assertEqual(pre_text_edit_mode_history_bytes(ROOT/p).decode(),expected.get(p,', 1], ['scripts/tests/test_p1_repair_preview_commit_error.py', 'class PreviewCommitError', 'from text_edit_mode_scope_contract import pre_text_edit_mode\nclass PreviewCommitError', 1], ['scripts/tests/test_p1_repair_preview_commit_error.py', "body((ROOT/r['path']).read_text(),r['symbol'])", "body(pre_text_edit_mode((ROOT/r['path']).read_text()),r['symbol'])", 1]]

def pre_text_edit_mode_history_bytes(path):
    from font_trait_reads_scope_contract import pre_font_trait_reads_history_bytes
    data = pre_font_trait_reads_history_bytes(path)
    if path.suffix == ".swift":
        data = pre_text_edit_mode(data.decode()).encode()
    if path.suffix != '.py':
        return data
    source = data.decode()
    for changed, old, new, count in reversed(HISTORICAL_TEST_CHANGES):
        if (path.as_posix() == changed or path.as_posix().endswith('/' + changed)) and new in source:
            assert source.count(new) == count
            source = source.replace(new, old)
    return source.encode()
