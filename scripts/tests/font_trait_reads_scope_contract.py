"""Reverse only phase188 original font descriptor getter and fallback ordering deltas."""
CHANGES = [['replica/Sources/PastoCore/OriginalPreviewTextTraits.swift', '            let traits = font.fontDescriptor.symbolicTraits\n            if traits.contains(.bold) { result.insert(.bold) }\n            if traits.contains(.italic) { result.insert(.italic) }', '            if font.fontDescriptor.symbolicTraits.contains(.bold) { result.insert(.bold) }\n            if font.fontDescriptor.symbolicTraits.contains(.italic) { result.insert(.italic) }', 1], ['replica/Sources/PastoCore/OriginalPreviewTextTraits.swift', '            let descriptor = font.fontDescriptor\n            let mask: NSFontDescriptor.SymbolicTraits = trait == .bold ? .bold : .italic\n            let traits = remove ? descriptor.symbolicTraits.subtracting(mask) : descriptor.symbolicTraits.union(mask)\n            let cleared = OriginalPreviewAttributedText.descriptorWithTraits(descriptor, traits: [])\n            let changed = cleared.flatMap { OriginalPreviewAttributedText.descriptorWithTraits($0, traits: traits) }\n            if let changedFont = NSFont(descriptor: changed ?? descriptor, size: font.pointSize) {', '            let originalTraits = font.fontDescriptor.symbolicTraits\n            let cleared = OriginalPreviewAttributedText.descriptorWithTraits(font.fontDescriptor, traits: [])\n            let changed = cleared.flatMap { descriptor in\n                let mask: NSFontDescriptor.SymbolicTraits = trait == .bold ? .bold : .italic\n                let traits = remove ? originalTraits.subtracting(mask) : originalTraits.union(mask)\n                return OriginalPreviewAttributedText.descriptorWithTraits(descriptor, traits: traits)\n            }\n            if let changedFont = NSFont(descriptor: changed ?? font.fontDescriptor, size: font.pointSize) {', 1], ['replica/Sources/PastoCore/OriginalPreviewAttributedText.swift', '        return NSFont(descriptor: requested ?? descriptor, size: font.pointSize) ?? font', '        return NSFont(descriptor: requested ?? font.fontDescriptor, size: font.pointSize) ?? font', 1]]

def pre_font_trait_reads(source):
    for _, old, new, count in reversed(CHANGES):
        if new in source:
            assert source.count(new) == count
            source = source.replace(new, old)
    return source

def pre_font_trait_reads_bytes(path):
    data = path.read_bytes()
    return pre_font_trait_reads(data.decode()).encode() if path.suffix == '.swift' else data

HISTORICAL_TEST_CHANGES = [['scripts/tests/text_edit_mode_scope_contract.py', 'def pre_text_edit_mode(source):\n', 'def pre_text_edit_mode(source):\n    from font_trait_reads_scope_contract import pre_font_trait_reads\n    source = pre_font_trait_reads(source)\n', 1], ['scripts/tests/text_edit_mode_scope_contract.py', '    data = pre_text_edit_mode_bytes(path)\n', '    from font_trait_reads_scope_contract import pre_font_trait_reads_history_bytes\n    data = pre_font_trait_reads_history_bytes(path)\n    if path.suffix == ".swift":\n        data = pre_text_edit_mode(data.decode()).encode()\n', 1], ['scripts/tests/test_p1_repair_text_edit_mode.py', 'class TextEditModeContracts', 'from font_trait_reads_scope_contract import pre_font_trait_reads_bytes, pre_font_trait_reads_history_bytes\nclass TextEditModeContracts', 1], ['scripts/tests/test_p1_repair_text_edit_mode.py', 'hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),h)', 'hashlib.sha256(pre_font_trait_reads_bytes(ROOT/p)).hexdigest(),h)', 1], ['scripts/tests/test_p1_repair_text_edit_mode.py', 'self.assertEqual((ROOT/p).read_text(),expected.get(p,', 'self.assertEqual(pre_font_trait_reads_history_bytes(ROOT/p).decode(),expected.get(p,', 1], ['scripts/tests/test_p1_repair_text_storage_owner.py', 'class TextStorageOwner', 'from font_trait_reads_scope_contract import pre_font_trait_reads\nclass TextStorageOwner', 1], ['scripts/tests/test_p1_repair_text_storage_owner.py', "body((ROOT/r['path']).read_text(),r['symbol'])", "body(pre_font_trait_reads((ROOT/r['path']).read_text()),r['symbol'])", 1]]

def pre_font_trait_reads_history_bytes(path):
    data = pre_font_trait_reads_bytes(path)
    if path.suffix != '.py':
        return data
    source = data.decode()
    for changed, old, new, count in reversed(HISTORICAL_TEST_CHANGES):
        if (path.as_posix() == changed or path.as_posix().endswith('/' + changed)) and new in source:
            assert source.count(new) == count
            source = source.replace(new, old)
    return source.encode()
