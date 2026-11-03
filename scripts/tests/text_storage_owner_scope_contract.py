"""Reverse phase175 strong editor and independent weak bridge-owner delivery only."""
CHANGES = [('replica/Sources/PastoCore/OriginalPreviewTextTraits.swift', '    private weak var editor: NSTextView?', '    private let editor: NSTextView', 1), ('replica/Sources/PastoCore/OriginalPreviewTextTraits.swift', '            Task { @MainActor [weak self] in self?.f_100213fe8() }', '            Task { @MainActor [weak self] in\n                _ = Self.deliverTraits(from: { [weak self] in self })\n            }', 1), ('replica/Sources/PastoCore/OriginalPreviewTextTraits.swift', '        guard let editor else { return true }\n        onTraitsChange?(OriginalPreviewTextTraits.f_100207b54(editor: editor))', '        let traits = OriginalPreviewTextTraits.f_100207b54(editor: editor)\n        onTraitsChange?(traits)', 1), ('replica/Sources/PastoCore/OriginalPreviewTextTraits.swift', '    public func f_100214704() {\n        if let editor { onTraitsChange?(OriginalPreviewTextTraits.f_100207b54(editor: editor)) }\n        // The original reloads its weak owner before invoking the content callback.\n        if let editor { onAttributedTextChange?(OriginalPreviewAttributedText.f_1000f6ef8(editor: editor)) }\n    }\n\n    public func f_10021453c() {\n        Task { @MainActor [weak self] in self?.f_100214704() }\n    }', '    public func f_100214704() {\n        Self.deliverStorageChange(from: { [weak self] in self })\n    }\n\n    private static func deliverStorageChange(from loadOwner: () -> OriginalPreviewTextStorageBridge?) {\n        _ = deliverTraits(from: loadOwner)\n        deliverContent(from: loadOwner)\n    }\n\n    // Separate calls end the first strong-owner scope before the second weak load (214998/2149a4).\n    @inline(never)\n    private static func deliverTraits(from loadOwner: () -> OriginalPreviewTextStorageBridge?) -> Bool {\n        guard let owner = loadOwner() else { return true }\n        return owner.f_100213fe8()\n    }\n\n    @inline(never)\n    private static func deliverContent(from loadOwner: () -> OriginalPreviewTextStorageBridge?) {\n        guard let owner = loadOwner(), let callback = owner.onAttributedTextChange else { return }\n        callback(OriginalPreviewAttributedText.f_1000f6ef8(editor: owner.editor))\n    }\n\n    public func f_10021453c() {\n        Task { @MainActor [weak self] in\n            Self.deliverStorageChange(from: { [weak self] in self })\n        }\n    }', 1)]

def pre_text_storage_owner(source):
    from pinboard_filter_identity_scope_contract import pre_pinboard_filter_identity
    source = pre_pinboard_filter_identity(source)
    for _, old, new, count in reversed(CHANGES):
        if new in source:
            assert source.count(new) == count
            source = source.replace(new, old)
    return source

def pre_text_storage_owner_bytes(path):
    data = path.read_bytes()
    return pre_text_storage_owner(data.decode()).encode() if path.suffix == '.swift' else data

HISTORICAL_TEST_CHANGES = [['scripts/tests/native_item_drop_scope_contract.py', 'def pre_native_item_drop(source):\n', 'def pre_native_item_drop(source):\n    from text_storage_owner_scope_contract import pre_text_storage_owner\n    source = pre_text_storage_owner(source)\n', 1], ['scripts/tests/test_p1_repair_native_item_drop.py', '\nclass NativeItemDrop', '\nfrom text_storage_owner_scope_contract import pre_text_storage_owner_bytes\n\nclass NativeItemDrop', 1], ['scripts/tests/test_p1_repair_native_item_drop.py', 'data=(ROOT/p).read_bytes();old=', 'data=pre_text_storage_owner_bytes(ROOT/p);old=', 1], ['scripts/tests/test_p1_repair_coder_source_resolution.py', '\nclass CoderSourceResolution', '\nfrom text_storage_owner_scope_contract import pre_text_storage_owner_history_bytes\n\nclass CoderSourceResolution', 1], ['scripts/tests/test_p1_repair_coder_source_resolution.py', 'hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),h,p)', 'hashlib.sha256(pre_text_storage_owner_history_bytes(ROOT/p)).hexdigest(),h,p)', 1]]

def pre_text_storage_owner_history_bytes(path):
    from pinboard_filter_identity_scope_contract import pre_pinboard_filter_identity_history_bytes
    data = pre_pinboard_filter_identity_history_bytes(path)
    if path.suffix == ".swift":
        data = pre_text_storage_owner(data.decode()).encode()
    if path.suffix != '.py':
        return data
    source = data.decode()
    for changed, old, new, count in reversed(HISTORICAL_TEST_CHANGES):
        if path.as_posix().endswith('/' + changed) and new in source:
            assert source.count(new) == count
            source = source.replace(new, old)
    return source.encode()
