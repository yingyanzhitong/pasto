"""Exact phase101 nontext native write deltas, historical contract isolation only."""
from pathlib import Path
from nontext_preview_read_scope_contract import pre_nontext_preview_read
CHANGES = [['replica/Sources/PastoCore/ClipboardStore.swift',
  '    private func updateTextPreviewItem(id: UUID, input: ClipboardRestoreItem?, attributedString: '
  'NSAttributedString) throws {\n'
  '        try mutateInTransaction { state, transaction in\n',
  '    private func updateTextPreviewItem(id: UUID, input: ClipboardRestoreItem?, attributedString: '
  'NSAttributedString) throws {\n'
  '        try replacePreviewContent(id: id, input: input, plainText: attributedString.string) {\n'
  '            OriginalTextPreviewSubmission.makeItem(attributedString)\n'
  '        }\n'
  '    }\n'
  '\n'
  '    // All local content writers submit the captured entity through Writing +0x18 / 360ff8.\n'
  '    private func replacePreviewContent(id: UUID, input: ClipboardRestoreItem?, plainText: @autoclosure () '
  '-> String?,\n'
  '                                       makeRepresentation: () -> OriginalPasteboardItem) throws {\n'
  '        try mutateInTransaction { state, transaction in\n'],
 ['replica/Sources/PastoCore/ClipboardStore.swift',
  '            let representation = OriginalTextPreviewSubmission.makeItem(attributedString)\n',
  '            let representation = makeRepresentation()\n'],
 ['replica/Sources/PastoCore/ClipboardStore.swift',
  '            item.plainText = attributedString.string\n',
  '            item.plainText = plainText()\n'],
 ['replica/Sources/PastoCore/ClipboardStore.swift',
  '    public func updateImagePreviewItem(id: UUID, payloads: [String: Data]) throws {\n',
  '    public func updateImagePreviewItem(_ input: ClipboardRestoreItem, payloads: [String: Data]) throws {\n'
  '        guard input.nativeObject != nil else {\n'
  '            try updateImagePreviewItem(id: input.id, payloads: payloads)\n'
  '            return\n'
  '        }\n'
  '        let imageTypes = ["public.png", "public.jpeg", "public.heic", "public.tiff", "com.apple.icns", '
  '"com.compuserve.gif"]\n'
  '        let types = imageTypes.filter { payloads[$0] != nil }\n'
  '        guard !types.isEmpty || payloads.isEmpty else {\n'
  '            throw OriginalPasteboardItemCreationError.unsupportedContent\n'
  '        }\n'
  '        try replacePreviewContent(id: input.id, input: input, plainText: nil) {\n'
  '            OriginalPasteboardItem(types: types, dataByType: payloads)\n'
  '        }\n'
  '        startBackgroundTextRecognition(id: input.id)\n'
  '    }\n'
  '\n'
  '    public func updateImagePreviewItem(id: UUID, payloads: [String: Data]) throws {\n'],
 ['replica/Sources/PastoCore/ClipboardStore.swift',
  '    public func updateLinkItem(id: UUID, url: URL) throws {\n',
  '    public func updateLinkItem(_ input: ClipboardRestoreItem, url: URL) throws {\n'
  '        guard let object = input.nativeObject else {\n'
  '            try updateLinkItem(id: input.id, url: url)\n'
  '            return\n'
  '        }\n'
  '        let name: String?\n'
  '        if let previous = OriginalImagePreviewMetadataCodec.decodeLink(object.value(forKey: "rawPreview") '
  'as? Data) {\n'
  '            name = previous.name\n'
  '        } else { name = "" }\n'
  '        try replacePreviewContent(id: input.id, input: input, plainText: url.absoluteString) {\n'
  '            OriginalPasteboardItem.f_10037c7bc(url, title: name)\n'
  '        }\n'
  '    }\n'
  '\n'
  '    public func updateLinkItem(id: UUID, url: URL) throws {\n'],
 ['replica/Sources/PastoCore/ClipboardStore.swift',
  '    public func updateColorItem(id: UUID, text: String) throws {\n',
  '    public func updateColorItem(_ input: ClipboardRestoreItem, text: String) throws {\n'
  '        guard input.nativeObject != nil else {\n'
  '            try updateColorItem(id: input.id, text: text)\n'
  '            return\n'
  '        }\n'
  '        try replacePreviewContent(id: input.id, input: input, plainText: text) {\n'
  '            OriginalPasteboardItem.f_10037c6d4(text)\n'
  '        }\n'
  '    }\n'
  '\n'
  '    public func updateColorItem(id: UUID, text: String) throws {\n'],
 ['replica/Sources/Pasto/UI/ReplicaImagePreviewContent.swift',
  '    private let itemID: UUID\n'
  '    private let checkerboardView = OriginalImageCheckerboardView(frame: .zero)\n',
  '    private let itemID: UUID\n'
  '    private let editInput: ClipboardRestoreItem?\n'
  '    private let checkerboardView = OriginalImageCheckerboardView(frame: .zero)\n'],
 ['replica/Sources/Pasto/UI/ReplicaImagePreviewContent.swift',
  '    init(state: ReplicaUIState, item: ClipboardItem) {\n',
  '    init(state: ReplicaUIState, item: ClipboardItem, input: ClipboardRestoreItem? = nil) {\n'],
 ['replica/Sources/Pasto/UI/ReplicaImagePreviewContent.swift',
  '        itemID = item.id\n        super.init(frame: .zero)\n',
  '        itemID = item.id\n        editInput = input\n        super.init(frame: .zero)\n'],
 ['replica/Sources/Pasto/UI/ReplicaImagePreviewContent.swift',
  '                try state.store.updateImagePreviewItem(id: itemID, payloads: '
  'Self.encodedPayloads(image))\n',
  '                if let editInput {\n'
  '                    try state.store.updateImagePreviewItem(editInput, payloads: '
  'Self.encodedPayloads(image))\n'
  '                } else {\n'
  '                    try state.store.updateImagePreviewItem(id: itemID, payloads: '
  'Self.encodedPayloads(image))\n'
  '                }\n'],
 ['replica/Sources/Pasto/UI/ReplicaColorPreviewContent.swift',
  '    private let itemID: UUID\n    private let codeLabel = NSTextField(labelWithString: "")\n',
  '    private let itemID: UUID\n'
  '    private let editInput: ClipboardRestoreItem?\n'
  '    private let codeLabel = NSTextField(labelWithString: "")\n'],
 ['replica/Sources/Pasto/UI/ReplicaColorPreviewContent.swift',
  '    init(state: ReplicaUIState, item: ClipboardItem) {\n',
  '    init(state: ReplicaUIState, item: ClipboardItem, input: ClipboardRestoreItem? = nil) {\n'],
 ['replica/Sources/Pasto/UI/ReplicaColorPreviewContent.swift',
  '        itemID = item.id\n        super.init(frame: .zero)\n',
  '        itemID = item.id\n        editInput = input\n        super.init(frame: .zero)\n'],
 ['replica/Sources/Pasto/UI/ReplicaColorPreviewContent.swift',
  '            try state.store.updateColorItem(id: itemID,\n'
  '                text: OriginalPreviewColorFormatting.f_100206b5c(displayedColor).uppercased())\n',
  '            let text = OriginalPreviewColorFormatting.f_100206b5c(displayedColor).uppercased()\n'
  '            if let editInput { try state.store.updateColorItem(editInput, text: text) }\n'
  '            else { try state.store.updateColorItem(id: itemID, text: text) }\n'],
 ['replica/Sources/Pasto/UI/ReplicaLinkPreviewContent.swift',
  '    private let itemID: UUID\n    private let readOnlyContent: NSView\n',
  '    private let itemID: UUID\n'
  '    private let editInput: ClipboardRestoreItem?\n'
  '    private let readOnlyContent: NSView\n'],
 ['replica/Sources/Pasto/UI/ReplicaLinkPreviewContent.swift',
  '    init(state: ReplicaUIState, item: ClipboardItem) {\n',
  '    init(state: ReplicaUIState, item: ClipboardItem, input: ClipboardRestoreItem? = nil) {\n'],
 ['replica/Sources/Pasto/UI/ReplicaLinkPreviewContent.swift',
  '        itemID = item.id\n'
  '        readOnlyContent = makeReplicaReadOnlyPreviewContent(store: state.store, item: item)\n',
  '        itemID = item.id\n'
  '        editInput = input\n'
  '        readOnlyContent = makeReplicaReadOnlyPreviewContent(store: state.store, item: item)\n'],
 ['replica/Sources/Pasto/UI/ReplicaLinkPreviewContent.swift',
  '            try state.store.updateLinkItem(id: itemID, url: url)\n',
  '            if let editInput { try state.store.updateLinkItem(editInput, url: url) }\n'
  '            else { try state.store.updateLinkItem(id: itemID, url: url) }\n'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  'ReplicaImagePreviewContent(state: state, item: item)',
  'ReplicaImagePreviewContent(state: state, item: item, input: input)'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  'ReplicaColorPreviewContent(state: state, item: item)',
  'ReplicaColorPreviewContent(state: state, item: item, input: input)'],
 ['replica/Sources/Pasto/UI/OriginalReplicaPreviewAdapter.swift',
  'ReplicaLinkPreviewContent(state: state, item: item)',
  'ReplicaLinkPreviewContent(state: state, item: item, input: input)']]

def pre_nontext_edit_write(source):
    source=pre_nontext_preview_read(source)
    for _,old,new in reversed(CHANGES):
        if old.startswith(new) and old in source: continue
        if new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    return source

def pre_nontext_edit_write_bytes(path):
    p=Path(path)
    return pre_nontext_edit_write(p.read_text()).encode() if p.suffix=='.swift' else p.read_bytes()
