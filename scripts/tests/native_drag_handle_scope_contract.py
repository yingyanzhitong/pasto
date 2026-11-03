# coding: utf-8
"""Reverse only reviewed120 native drag/source deltas for historical source contracts."""
from native_capture_lookup_scope_contract import pre_native_capture_lookup
CHANGES = [['replica/Sources/PastoCore/Pasteboard.swift',
  '    private func nativeRestoreObjects(_ inputs: [ClipboardRestoreItem],\n'
  '                                      options: OriginalPasteboardRestore.Options) -> '
  '[OriginalPasteboardItem] {\n'
  '        let multiple = inputs.count > 1\n'
  '        let aggregatesText = inputs.contains { $0.previewRawType() == 5 || $0.previewRawType() == 4 }\n'
  '        var groups: [[OriginalPasteboardItem]] = []\n'
  '        var contents: [NSAttributedString] = []\n'
  '        for input in inputs {\n'
  '            let object = input.nativeObject!\n'
  '            let kind = OriginalPasteboardContentKind(rawValue: UInt8(input.previewRawType()!))!\n'
  '            let plain = OriginalPasteboardRestore.usesPlainProjection(kind: kind, options: options)\n'
  '            let representations: [OriginalPasteboardItem]\n'
  '            if !plain, kind == .image {\n'
  '                representations = Self.imageRestore.prepareNative(\n'
  '                    sourceName: (object.value(forKey: "sourceApplication") as? '
  'NSManagedObject)?.value(forKey: "name") as? String,\n'
  '                    timestamp: object.value(forKey: "timestamp") as? Date) {\n'
  '                        Self.nativeRestoreRepresentations(for: object)\n'
  '                    }\n'
  '            } else {\n'
  '                representations = Self.nativeRestoreRepresentations(for: object)\n'
  '            }\n'
  '            let items = plain ? OriginalPasteboardRestore.f_10031bcdc(representations) : representations\n'
  '            let application = object.value(forKey: "sourceApplication") as? NSManagedObject\n'
  '            let sourceBundleID = application?.value(forKey: "bundleIdentifier") as? String\n'
  '            for item in items {\n'
  '                item.f_100383574(removingTypesContaining: ["com.microsoft.ole.source"])\n'
  '                item.f_10037c4a8(sourceBundleID ?? "", forType: "org.nspasteboard.source")\n'
  '                item.f_1003838bc()\n'
  '            }\n'
  '            if !multiple { return items }\n'
  '            if aggregatesText {\n'
  '                contents.append(contentsOf: items.compactMap { $0.f_10037d33c() })\n'
  '                groups.append([])\n'
  '            } else {\n'
  '                groups.append(items)\n'
  '            }\n'
  '        }\n'
  '        let combined = OriginalPasteboardRestore.f_100383a0c(separator: "\\n", contents: contents)\n'
  '        if combined.length > 0 {\n'
  '            let aggregate = OriginalPasteboardItem()\n'
  '            aggregate.f_1003838bc()\n'
  '            if !options.contains(.plainTextAndLinks), let data = '
  'OriginalPasteboardRestore.f_100381fdc(combined) {\n'
  '                aggregate.f_10037d8c8(data, forType: "public.rtf")\n'
  '            } else {\n'
  '                aggregate.f_10037c4a8(combined.string, forType: "public.utf8-plain-text")\n'
  '            }\n'
  '            groups.insert([aggregate], at: 0)\n'
  '        }\n'
  '        return groups.flatMap { $0 }\n'
  '    }',
  '    private func nativeRestoreObjects(_ inputs: [ClipboardRestoreItem],\n'
  '                                      options: OriginalPasteboardRestore.Options) -> '
  '[OriginalPasteboardItem] {\n'
  '        nativeRestoreGroups(inputs, options: options).flatMap { $0 }\n'
  '    }\n'
  '\n'
  '    private func nativeRestoreGroups(_ inputs: [ClipboardRestoreItem],\n'
  '                                     options: OriginalPasteboardRestore.Options) -> '
  '[[OriginalPasteboardItem]] {\n'
  '        let multiple = inputs.count > 1\n'
  '        let aggregatesText = inputs.contains { $0.previewRawType() == 5 || $0.previewRawType() == 4 }\n'
  '        var groups: [[OriginalPasteboardItem]] = []\n'
  '        var contents: [NSAttributedString] = []\n'
  '        for input in inputs {\n'
  '            let object = input.nativeObject!\n'
  '            let kind = OriginalPasteboardContentKind(rawValue: UInt8(input.previewRawType()!))!\n'
  '            let plain = OriginalPasteboardRestore.usesPlainProjection(kind: kind, options: options)\n'
  '            let representations: [OriginalPasteboardItem]\n'
  '            if !plain, kind == .image {\n'
  '                representations = Self.imageRestore.prepareNative(\n'
  '                    sourceName: (object.value(forKey: "sourceApplication") as? '
  'NSManagedObject)?.value(forKey: "name") as? String,\n'
  '                    timestamp: object.value(forKey: "timestamp") as? Date) {\n'
  '                        Self.nativeRestoreRepresentations(for: object)\n'
  '                    }\n'
  '            } else {\n'
  '                representations = Self.nativeRestoreRepresentations(for: object)\n'
  '            }\n'
  '            let items = plain ? OriginalPasteboardRestore.f_10031bcdc(representations) : representations\n'
  '            let application = object.value(forKey: "sourceApplication") as? NSManagedObject\n'
  '            let sourceBundleID = application?.value(forKey: "bundleIdentifier") as? String\n'
  '            for item in items {\n'
  '                item.f_100383574(removingTypesContaining: ["com.microsoft.ole.source"])\n'
  '                item.f_10037c4a8(sourceBundleID ?? "", forType: "org.nspasteboard.source")\n'
  '                item.f_1003838bc()\n'
  '            }\n'
  '            if !multiple { return [items] }\n'
  '            if aggregatesText {\n'
  '                contents.append(contentsOf: items.compactMap { $0.f_10037d33c() })\n'
  '                groups.append([])\n'
  '            } else {\n'
  '                groups.append(items)\n'
  '            }\n'
  '        }\n'
  '        let combined = OriginalPasteboardRestore.f_100383a0c(separator: "\\n", contents: contents)\n'
  '        if combined.length > 0 {\n'
  '            let aggregate = OriginalPasteboardItem()\n'
  '            aggregate.f_1003838bc()\n'
  '            if !options.contains(.plainTextAndLinks), let data = '
  'OriginalPasteboardRestore.f_100381fdc(combined) {\n'
  '                aggregate.f_10037d8c8(data, forType: "public.rtf")\n'
  '            } else {\n'
  '                aggregate.f_10037c4a8(combined.string, forType: "public.utf8-plain-text")\n'
  '            }\n'
  '            groups.insert([aggregate], at: 0)\n'
  '        }\n'
  '        return groups\n'
  '    }'],
 ['replica/Sources/PastoCore/Pasteboard.swift',
  '    public func writeToPasteboard(id: UUID, pasteboard: NSPasteboard, plainTextOnly: Bool = false) throws '
  '{\n',
  '    public func dragPasteboardGroups(restoreItems selected: [ClipboardRestoreItem],\n'
  '                                     options: OriginalPasteboardRestore.Options) throws -> '
  '[[OriginalPasteboardItem]] {\n'
  '        guard selected.allSatisfy({ $0.nativeObject != nil }) else {\n'
  '            return try dragPasteboardGroups(for: selected.map { $0.resolvedItem() }, options: options)\n'
  '        }\n'
  '        return nativeRestoreGroups(selected, options: options)\n'
  '    }\n'
  '\n'
  '    public func writeToPasteboard(id: UUID, pasteboard: NSPasteboard, plainTextOnly: Bool = false) throws '
  '{\n'],
 ['replica/Sources/PastoCore/ClipboardRestoreItem.swift',
  '    public var hasNativeEntity: Bool { nativeObject != nil }\n',
  '    public var hasNativeEntity: Bool { nativeObject != nil }\n'
  '\n'
  '    public func makeDragIdentifierSource() -> any OriginalDragItemIdentifierSource {\n'
  '        ClipboardDragIdentifierSource(object: nativeObject, fallback: id.uuidString)\n'
  '    }\n'],
 ['replica/Sources/PastoCore/ClipboardRestoreItem.swift',
  '    public func resolvedItem() -> ClipboardItem { resolve() }\n'
  '    public func observeItem() -> ClipboardItemObservation? { makeObservation() }\n'
  '}\n',
  '    public func resolvedItem() -> ClipboardItem { resolve() }\n'
  '    public func observeItem() -> ClipboardItemObservation? { makeObservation() }\n'
  '}\n'
  '\n'
  'private final class ClipboardDragIdentifierSource: OriginalDragItemIdentifierSource {\n'
  '    private let object: PastoItemEntity?\n'
  '    private let context: NSManagedObjectContext?\n'
  '    private let fallback: String\n'
  '\n'
  '    init(object: PastoItemEntity?, fallback: String) {\n'
  '        self.object = object\n'
  '        context = object?.managedObjectContext\n'
  '        self.fallback = fallback\n'
  '    }\n'
  '\n'
  '    var pasteboardIdentifier: String {\n'
  '        guard let object else { return fallback }\n'
  '        let fallback = self.fallback\n'
  '        let read = { (object.value(forKey: "nativeIdentifier") as? String) ?? fallback }\n'
  '        if let context { return context.performAndWait(read) }\n'
  '        return read()\n'
  '    }\n'
  '}\n'],
 ['replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift',
  '        let indexes = state.orderedSelectionIDs.filter { state.selection.contains($0) }.compactMap { '
  'positions[$0] }\n'
  '        let selected = indexes.map { renderedItem(at: $0) }\n',
  '        let requestedIndexes = state.orderedSelectionIDs.filter { state.selection.contains($0) '
  '}.compactMap { positions[$0] }\n'
  '        var indexes: [Int] = []\n'
  '        let selected = requestedIndexes.compactMap { index -> ClipboardRestoreItem? in\n'
  '            guard let input = applied[index].restoreItem() else { return nil }\n'
  '            indexes.append(index)\n'
  '            return input\n'
  '        }\n'],
 ['replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift',
  'let groups = try state.store.dragPasteboardGroups(for: selected, options: options)',
  'let groups = try state.store.dragPasteboardGroups(restoreItems: selected, options: options)'],
 ['replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift',
  'let sources: [any OriginalDragItemIdentifierSource] = selected.map { ReplicaNativeDragItemReference($0) }',
  'let sources: [any OriginalDragItemIdentifierSource] = selected.map { $0.makeDragIdentifierSource() }'],
 ['replica/Sources/Pasto/UI/ReplicaNativeCardCollection.swift',
  'private final class ReplicaNativeDragItemReference: OriginalDragItemIdentifierSource {\n'
  '    private let item: ClipboardItem\n'
  '    init(_ item: ClipboardItem) { self.item = item }\n'
  '    var pasteboardIdentifier: String { item.id.uuidString }\n'
  '}\n'
  '\n',
  '']]

def pre_native_drag_handle(source):
    source=pre_native_capture_lookup(source)
    for _,old,new in reversed(CHANGES):
        if not new:
            anchor = "/// Only the replica's local reorder marker is added; original grouped payload stays intact."
            if anchor in source and old not in source:
                assert source.count(anchor)==1
                source=source.replace(anchor,old+anchor,1)
        elif new in source:
            assert source.count(new)==1
            source=source.replace(new,old,1)
    return source
