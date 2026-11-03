"""Reverse only reviewed118 writer-to-capture-state migration for older contracts."""
from capture_lifecycle_scope_contract import pre_capture_lifecycle
CHANGES = [['replica/Sources/PastoCore/OriginalPasteboard.swift',
  '    public let pasteboard: NSPasteboard\n'
  '    public private(set) var lastChangeCount: Int\n'
  '    public private(set) var lastWriteSucceeded = false\n'
  '\n'
  '    public init(pasteboard: NSPasteboard) {\n'
  '        self.pasteboard = pasteboard\n'
  '        self.lastChangeCount = pasteboard.changeCount\n'
  '    }\n',
  '    public let pasteboard: NSPasteboard\n'
  '    private let state: OriginalPasteboardCaptureState\n'
  '    public var lastChangeCount: Int { state.lastChangeCount }\n'
  '    public var lastWriteSucceeded: Bool { state.lastWriteSucceeded }\n'
  '\n'
  '    public init(pasteboard: NSPasteboard) {\n'
  '        self.pasteboard = pasteboard\n'
  '        self.state = OriginalPasteboardCaptureState.f_100378664(changeCount: 0, pasteboard: pasteboard)\n'
  '    }\n'],
 ['replica/Sources/PastoCore/OriginalPasteboard.swift',
  '{\n'
  '        let objects = items.map { item -> NSPasteboardItem in\n'
  '            let object = NSPasteboardItem()\n'
  '            for type in item.f_10037da6c() {\n'
  '                if let data = item.f_10037e5e0(forType: type) {\n'
  '                    object.setData(data as Data, forType: NSPasteboard.PasteboardType(type))\n'
  '                }\n'
  '            }\n'
  '            return object\n'
  '        }\n'
  '        pasteboard.clearContents()\n'
  '        lastWriteSucceeded = pasteboard.writeObjects(objects)\n'
  '        lastChangeCount = pasteboard.changeCount\n'
  '        OriginalPasteboardCaptureState.current(for: pasteboard)?.lastChangeCount = lastChangeCount\n'
  '    }',
  '{\n        state.f_10037875c(items)\n    }'],
 ['replica/Sources/PastoCore/OriginalPasteboardCaptureState.swift',
  '    public var lastChangeCount: Int\n    var persistChangeCount:',
  '    public var lastChangeCount: Int\n'
  '    public private(set) var lastWriteSucceeded = false\n'
  '    var persistChangeCount:'],
 ['replica/Sources/PastoCore/OriginalPasteboardCaptureState.swift',
  '    public static func register(_ state: OriginalPasteboardCaptureState) {\n',
  '    public func f_10037875c(_ items: [OriginalPasteboardItem]) {\n'
  '        let objects = items.map { item -> NSPasteboardItem in\n'
  '            let object = NSPasteboardItem()\n'
  '            for type in item.f_10037da6c() {\n'
  '                if let data = item.f_10037e5e0(forType: type) {\n'
  '                    object.setData(data as Data, forType: NSPasteboard.PasteboardType(type))\n'
  '                }\n'
  '            }\n'
  '            return object\n'
  '        }\n'
  '        pasteboard.clearContents()\n'
  '        lastWriteSucceeded = pasteboard.writeObjects(objects)\n'
  '        lastChangeCount = pasteboard.changeCount\n'
  '        Self.current(for: pasteboard)?.lastChangeCount = lastChangeCount\n'
  '    }\n'
  '\n'
  '    public static func register(_ state: OriginalPasteboardCaptureState) {\n'],
 ['replica/Sources/PastoCore/Pasteboard.swift',
  '        let writer = OriginalPasteboardWriter(pasteboard: pasteboard)\n'
  '        writer.f_10037875c(objects)\n',
  '        if let state = OriginalPasteboardCaptureState.current(for: pasteboard),\n'
  '           state.pasteboard === pasteboard {\n'
  '            state.f_10037875c(objects)\n'
  '        } else {\n'
  '            let writer = OriginalPasteboardWriter(pasteboard: pasteboard)\n'
  '            writer.f_10037875c(objects)\n'
  '        }\n']]

def pre_shared_pasteboard_state(source):
    source=pre_capture_lifecycle(source)
    for _,old,new in reversed(CHANGES):
        if new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    return source
