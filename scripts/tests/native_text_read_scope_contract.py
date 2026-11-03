"""Exact native text raw-data read deltas for historical frozen contracts only."""
from pathlib import Path
from native_preview_header_scope_contract import pre_native_preview_header
CHANGES = [['replica/Sources/PastoCore/ClipboardItemObservation.swift',
  '    public var onChange: ((ClipboardItem) -> Void)?\n',
  '    public var onChange: ((ClipboardItem) -> Void)?\n'
  '    public var onTextChange: ((NSAttributedString) -> Void)?\n'],
 ['replica/Sources/PastoCore/ClipboardItemObservation.swift',
  '    // 356260 selects the event object by ID; 3c04f0 ignores deleted entities.\n',
  '    // 3c05d4 reads Item.data directly; unrelated archived value metadata is not a text dependency.\n'
  '    public var attributedText: NSAttributedString? {\n'
  '        guard !object.isDeleted else { return nil }\n'
  '        guard let data = object.value(forKey: "data") as? NSManagedObject else { return nil }\n'
  '        let raw: Data\n'
  '        do {\n'
  '            raw = try OriginalObjCExceptionBridge.f_1002ffc68 {\n'
  '                guard let raw = data.value(forKey: "rawPasteboardItems") as? Data else {\n'
  '                    throw CocoaError(.fileReadCorruptFile)\n'
  '                }\n'
  '                return raw\n'
  '            }\n'
  '        } catch is OriginalObjCExceptionError {\n'
  '            return NSAttributedString(string: "")\n'
  '        } catch { return nil }\n'
  '        let items = autoreleasepool { OriginalPasteboardDataCodec.f_10031aeec(raw) }\n'
  '        return items.first?.f_10037d33c() ?? NSAttributedString(string: "")\n'
  '    }\n'
  '\n'
  '    // 356260 selects the event object by ID; 3c04f0 ignores deleted entities.\n'],
 ['replica/Sources/PastoCore/ClipboardItemObservation.swift',
  '            if let value { onChange?(value) }\n',
  '            if let attributedText { onTextChange?(attributedText) }\n'
  '            // Retain the value adapter only for clients that request it.\n'
  '            if onChange != nil, let value { onChange?(value) }\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '            initial = nativeSource.value.map(Self.attributedContent) ?? NSAttributedString(string: "")',
  '            initial = nativeSource.attributedText ?? NSAttributedString(string: "")'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '            nativeSource.onChange = { [weak self] current in\n'
  '                self?.receiveStoredModel(current)\n'
  '            }\n',
  '            nativeSource.onTextChange = { [weak self] current in\n'
  '                self?.receiveStoredText(current)\n'
  '            }\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '        let item: ClipboardItem?\n'
  '        if let nativeItemObservation { item = nativeItemObservation.value }\n'
  '        else { item = state?.store.items.first(where: { $0.id == itemID }) }\n'
  '        guard let item else { return }\n'
  '        replaceStoredModel(item)\n'
  '        displayStoredModel()\n',
  '        if let nativeItemObservation {\n'
  '            guard let current = nativeItemObservation.attributedText else { return }\n'
  '            replaceStoredText(current)\n'
  '        } else {\n'
  '            guard let item = state?.store.items.first(where: { $0.id == itemID }) else { return }\n'
  '            replaceStoredModel(item)\n'
  '        }\n'
  '        displayStoredModel()\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '    private func receiveStoredModel(_ item: ClipboardItem) {\n',
  '    private func receiveStoredText(_ text: NSAttributedString) {\n'
  '        replaceStoredText(text)\n'
  '        if !self.text.isEditable { displayStoredModel() }\n'
  '    }\n'
  '\n'
  '    private func receiveStoredModel(_ item: ClipboardItem) {\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  '    private func replaceStoredModel(_ item: ClipboardItem) {\n'
  '        // Paste f_1003c04f0 refreshes both model values even while the editor is active.\n'
  '        originalText = Self.attributedContent(item)\n'
  '        editingText = OriginalPreviewAttributedText.normalizedEditingText(originalText)\n'
  '    }\n',
  '    private func replaceStoredModel(_ item: ClipboardItem) {\n'
  '        replaceStoredText(Self.attributedContent(item))\n'
  '    }\n'
  '\n'
  '    private func replaceStoredText(_ text: NSAttributedString) {\n'
  '        // Paste f_1003c04f0 refreshes both model values even while the editor is active.\n'
  '        originalText = text\n'
  '        editingText = OriginalPreviewAttributedText.normalizedEditingText(originalText)\n'
  '    }\n']]

def pre_native_text_read(source):
    source = pre_native_preview_header(source)
    for path, before, after in reversed(CHANGES):
        if after in source:
            assert source.count(after) == 1, path
            source = source.replace(after, before, 1)
    return source

def pre_native_text_read_bytes(path):
    data = Path(path).read_bytes()
    if str(path).endswith(".swift"):
        return pre_native_text_read(data.decode()).encode()
    return data
