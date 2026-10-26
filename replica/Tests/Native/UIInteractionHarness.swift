import AppKit
import Foundation
import SwiftUI
import PastoCore

@main
struct UIInteractionHarness {
    @MainActor static func main() async throws {
        _ = NSApplication.shared
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: directory) }
        let board = NSPasteboard(name: .init("PastoUIHarness-\(UUID().uuidString)"))
        defer { board.releaseGlobally() }
        let store = try ClipboardStore(directoryURL: directory)
        let first = try store.add(ClipboardItem(plainText: "FIRST fixture"))
        let second = try store.add(ClipboardItem(plainText: "SECOND fixture"))
        let pin = try store.createPinboard(name: "fixture", colorHex: "#00AAFF")
        try store.assign(ids: [first], to: pin.id)
        let ui = ReplicaUIController(store: store)
        ui.pasteboard = board
        let state = ui.state
        var delivered: [([UUID], Bool)] = []
        ui.pasteItemsHandler = { delivered.append(($0, $1)) }
        func key(_ code: UInt16, _ chars: String, _ modifiers: NSEvent.ModifierFlags) {
            let event = NSEvent.keyEvent(with: .keyDown, location: .zero, modifierFlags: modifiers,
                                        timestamp: 0, windowNumber: ui.panel.windowNumber,
                                        context: nil, characters: chars,
                                        charactersIgnoringModifiers: chars, isARepeat: false, keyCode: code)!
            ui.panel.sendEvent(event)
        }
        state.normalizeSelection()
        key(0, "a", .command)
        precondition(state.selection == Set([first, second]))
        key(8, "c", .command)
        let ordered = state.selectedItems.map(\.plainText)
        precondition(board.pasteboardItems?.map { $0.string(forType: .string) } == ordered)
        key(0, "a", [.command, .shift])
        state.normalizeSelection()
        precondition(state.selection.isEmpty && state.primaryID == nil)
        let visible = state.visibleItems
        state.select(visible[0])
        state.select(visible[1], modifiers: .shift)
        precondition(state.selection.count == 2)
        ui.pasteSelection(plainTextOnly: false)
        precondition(delivered.last?.0 == visible.map(\.id) && delivered.last?.1 == false)
        store.preferences.quickPasteModifierRawValue = NSEvent.ModifierFlags.option.rawValue
        store.preferences.plainTextModifierRawValue = NSEvent.ModifierFlags.control.rawValue
        key(18, "1", [.option, .control])
        precondition(delivered.last?.0 == [visible[0].id] && delivered.last?.1 == true)
        store.preferences.nextPinboardShortcut = KeyboardShortcut(keyCode: 124, modifierRawValue: NSEvent.ModifierFlags.option.rawValue)
        key(124, "", .option)
        precondition(state.pinboardID == pin.id && state.visibleItems.map(\.id) == [first])
        state.chooseBoard(nil)
        state.addToStack(visible[0]); state.addToStack(visible[1]); state.addToStack(visible[0])
        precondition(state.stackIDs == visible.map(\.id))
        state.reverseStack()
        let reopened = try ClipboardStore(directoryURL: directory)
        precondition(reopened.preferences.stackItemIDs == visible.map(\.id).reversed())
        precondition(reopened.preferences.stackReversed)
        ui.consumeStackHead()
        precondition(state.stackIDs == [visible[0].id])
        for minutes in [15, 30, 60, 180, 480] {
            let start = Date()
            state.pauseMonitoring(minutes: minutes)
            precondition(store.preferences.isMonitoringPaused)
            precondition(abs(store.preferences.pauseUntil!.timeIntervalSince(start) - Double(minutes * 60)) < 1)
        }
        state.pauseMonitoring()
        precondition(store.preferences.isMonitoringPaused && store.preferences.pauseUntil == nil)
        state.resumeMonitoring()
        precondition(!store.preferences.isMonitoringPaused && store.preferences.pauseUntil == nil)
        state.searchVisible = true
        state.query = "missing search fixture"
        key(53, "", [])
        precondition(state.query.isEmpty && state.searchVisible)
        key(53, "", [])
        precondition(!state.searchVisible && !(ui.panel.firstResponder is NSTextView))
        func load(_ provider: NSItemProvider, _ type: String) async throws -> Data {
            try await withCheckedThrowingContinuation { continuation in
                provider.loadDataRepresentation(forTypeIdentifier: type) { data, error in
                    if let error { continuation.resume(throwing: error) }
                    else { continuation.resume(returning: data ?? Data()) }
                }
            }
        }
        let bytes = Data([0, 127, 255, 42])
        let dragItem = ClipboardItem(title: "drag fixture", plainText: "Unicode drag 中文", payloads: [
            "com.example.drag-fixture": bytes,
            "public.html": Data("<b>Unicode drag 中文</b>".utf8),
            "com.pastereplica.internal.recognized-text": Data("private index".utf8)
        ])
        let provider = itemDragProvider(dragItem)
        let rawDrag = try await load(provider, "com.example.drag-fixture")
        let htmlDrag = try await load(provider, "public.html")
        let textDrag = try await load(provider, "public.utf8-plain-text")
        precondition(rawDrag == bytes && htmlDrag == dragItem.payloads["public.html"])
        precondition(String(data: textDrag, encoding: .utf8) == "Unicode drag 中文")
        precondition(!provider.registeredTypeIdentifiers.contains { $0.hasPrefix("com.pastereplica.internal.") })
        let fileA = directory.appendingPathComponent("first 中文.txt")
        let fileB = directory.appendingPathComponent("second.txt")
        try Data("first".utf8).write(to: fileA)
        try Data("second".utf8).write(to: fileB)
        let representations = [fileA, fileB].map { ["public.file-url": Data($0.absoluteString.utf8)] }
        let filesItem = ClipboardItem(kind: .files, payloads: [
            "public.file-url": Data(fileA.absoluteString.utf8),
            "com.pastereplica.internal.items+json": try JSONEncoder().encode(representations)
        ])
        precondition(itemFileURLs(filesItem) == [fileA, fileB])
        let fileProvider = itemDragProvider(filesItem)
        let filePaths = try await load(fileProvider, "NSFilenamesPboardType")
        let restoredPaths = try PropertyListSerialization.propertyList(from: filePaths, format: nil) as? [String]
        precondition(restoredPaths == [fileA.path, fileB.path])
        state.addToStack(visible[1])
        let stackWindow = NSPanel(contentRect: .init(x: 0, y: 0, width: 264, height: 120),
                                           styleMask: [.borderless, .nonactivatingPanel], backing: .buffered, defer: false)
        let stackContent = NSHostingView(rootView: ReplicaStackView(state: state))
        stackWindow.contentView = stackContent
        stackContent.layoutSubtreeIfNeeded()
        try await Task.sleep(nanoseconds: 100_000_000)
        func tables(in view: NSView) -> [NSTableView] {
            (view as? NSTableView).map { [$0] } ?? view.subviews.flatMap { tables(in: $0) }
        }
        let stackTable = tables(in: stackContent).first!
        precondition(stackTable.numberOfRows == state.stackItems.count && stackTable.rowHeight == 44)
        precondition(stackTable.delegate?.tableView?(stackTable, shouldSelectRow: 0) == false)
        precondition(stackTable.view(atColumn: 0, row: 0, makeIfNecessary: true) != nil)
        precondition(!ui.panel.isVisible && NSApp.windows.allSatisfy { !$0.isVisible })
        print("{\"passed\":true,\"checks\":[\"panel event routing for select/copy/deselect\",\"multi-selection paste delivery order\",\"custom quick paste and plain text modifiers\",\"custom Pinboard navigation\",\"Escape clears query and then dismisses search\",\"Stack duplicate prevention, reverse persistence and queue consumption; all pause durations and resume; async NSItemProvider binary/HTML/Unicode loads; multi-file URLs and legacy paths; internal OCR data excluded\",\"hidden SwiftUI Stack hosts native NSTableView with actual rows/cells, rowHeight44 and delegate rejecting selection\"],\"scope\":\"Hidden native panel, synthetic key events, temporary store and private named pasteboard; no global hooks, visible windows or cross-application paste\"}")
    }
}
