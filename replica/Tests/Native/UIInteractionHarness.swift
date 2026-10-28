import AppKit
import Foundation
import SwiftUI
import PastoCore

@main
struct UIInteractionHarness {
    struct Failure: Error, CustomStringConvertible { let description: String }
    @MainActor static func main() async {
        do { try await run() }
        catch {
            print(String(data: try! JSONSerialization.data(withJSONObject: ["status": "failed", "reason": String(describing: error)]), encoding: .utf8)!)
            exit(1)
        }
    }
    static func require(_ condition: @autoclosure () -> Bool, line: UInt = #line) throws {
        if !condition() { throw Failure(description: "UI assertion failed at line \(line)") }
    }
    @MainActor static func run() async throws {
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
        ui.pasteItemsHandler = { delivered.append(($0, $1)); return true }
        func key(_ code: UInt16, _ chars: String, _ modifiers: NSEvent.ModifierFlags) {
            let event = NSEvent.keyEvent(with: .keyDown, location: .zero, modifierFlags: modifiers,
                                        timestamp: 0, windowNumber: ui.panel.windowNumber,
                                        context: nil, characters: chars,
                                        charactersIgnoringModifiers: chars, isARepeat: false, keyCode: code)!
            ui.panel.sendEvent(event)
        }
        state.normalizeSelection()
        key(0, "a", .command)
        try require(state.selection == Set([first, second]))
        key(8, "c", .command)
        let ordered = state.selectedItems.compactMap(\.plainText)
        try require(ordered.count == state.selection.count)
        let aggregate = board.data(forType: .rtf).flatMap {
            try? NSAttributedString(data: $0, options: [.documentType: NSAttributedString.DocumentType.rtf], documentAttributes: nil).string
        }
        try require(board.pasteboardItems?.count == 1 && aggregate == ordered.joined(separator: "\n"))
        key(8, "c", [.command, .shift])
        try require(board.string(forType: .string) == ordered.joined(separator: "\n") && board.data(forType: .rtf) == nil)
        key(0, "a", [.command, .shift])
        state.normalizeSelection()
        try require(state.selection.isEmpty && state.primaryID == nil)
        let visible = state.visibleItems
        state.select(visible[0])
        state.select(visible[1], modifiers: .shift)
        try require(state.selection.count == 2)
        ui.pasteSelection(plainTextOnly: false)
        try require(delivered.last?.0 == visible.map(\.id) && delivered.last?.1 == false)
        store.preferences.quickPasteModifierRawValue = NSEvent.ModifierFlags.option.rawValue
        store.preferences.plainTextModifierRawValue = NSEvent.ModifierFlags.control.rawValue
        key(18, "1", [.option, .control])
        try require(delivered.last?.0 == [visible[0].id] && delivered.last?.1 == true)
        store.preferences.nextPinboardShortcut = KeyboardShortcut(keyCode: 124, modifierRawValue: NSEvent.ModifierFlags.option.rawValue)
        key(124, "", .option)
        try require(state.pinboardID == pin.id && state.visibleItems.map(\.id) == [first])
        state.chooseBoard(nil)
        state.addToStack(visible[0]); state.addToStack(visible[1]); state.addToStack(visible[0])
        let insertedStack = [visible[1].id, visible[0].id]
        try require(state.stackIDs == insertedStack)
        state.reverseStack()
        let reopened = try ClipboardStore(directoryURL: directory)
        try require(reopened.preferences.stackItemIDs == Array(insertedStack.reversed()))
        try require(reopened.preferences.stackReversed)
        ui.consumeStackHead()
        try require(state.stackIDs == [visible[1].id])
        for minutes in [15, 30, 60, 180, 480] {
            let start = Date()
            state.pauseMonitoring(minutes: minutes)
            try require(store.preferences.isMonitoringPaused)
            try require(abs(store.preferences.pauseUntil!.timeIntervalSince(start) - Double(minutes * 60)) < 1)
        }
        state.pauseMonitoring()
        try require(store.preferences.isMonitoringPaused && store.preferences.pauseUntil == nil)
        state.resumeMonitoring()
        try require(!store.preferences.isMonitoringPaused && store.preferences.pauseUntil == nil)
        state.searchVisible = false
        state.query = ""
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
        try require(rawDrag == bytes && htmlDrag == dragItem.payloads["public.html"])
        try require(String(data: textDrag, encoding: .utf8) == "Unicode drag 中文")
        try require(!provider.registeredTypeIdentifiers.contains { $0.hasPrefix("com.pastereplica.internal.") })
        let fileA = directory.appendingPathComponent("first 中文.txt")
        let fileB = directory.appendingPathComponent("second.txt")
        try Data("first".utf8).write(to: fileA)
        try Data("second".utf8).write(to: fileB)
        let representations = [fileA, fileB].map { ["public.file-url": Data($0.absoluteString.utf8)] }
        let filesItem = ClipboardItem(kind: .files, payloads: [
            "public.file-url": Data(fileA.absoluteString.utf8),
            "com.pastereplica.internal.items+json": try JSONEncoder().encode(representations)
        ])
        try require(itemFileURLs(filesItem) == [fileA, fileB])
        let fileProvider = itemDragProvider(filesItem)
        let filePaths = try await load(fileProvider, "NSFilenamesPboardType")
        let restoredPaths = try PropertyListSerialization.propertyList(from: filePaths, format: nil) as? [String]
        try require(restoredPaths == [fileA.path, fileB.path])
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
        try require(stackTable.numberOfRows == state.stackItems.count && stackTable.rowHeight == 44)
        try require(stackTable.delegate?.tableView?(stackTable, shouldSelectRow: 0) == false)
        try require(stackTable.view(atColumn: 0, row: 0, makeIfNecessary: true) != nil)
        try require(!ui.panel.isVisible)
        guard let screen = NSScreen.main else {
            print("{\"status\":\"blocked\",\"reason\":\"No window-server screen for visibility assertions\"}")
            exit(77)
        }
        func waitForVisibility(_ expected: Bool) async throws {
            let deadline = Date().addingTimeInterval(3)
            while ui.panel.isVisible != expected && Date() < deadline {
                try await Task.sleep(nanoseconds: 20_000_000)
            }
            try require(ui.panel.isVisible == expected)
        }
        func presentOffscreen() async throws {
            ui.showPanel()
            ui.panel.setFrameOrigin(.init(x: screen.frame.maxX + 200, y: screen.frame.maxY + 200))
            try await waitForVisibility(true)
            try await Task.sleep(nanoseconds: 250_000_000)
            try require(ui.panel.isVisible)
        }
        defer { ui.panel.orderOut(nil); stackWindow.orderOut(nil) }
        try await presentOffscreen()
        // Exercise the actual hosted tab hit tree, including transparent padding and icon/label gaps.
        func tabs(in view: NSView) -> [OriginalPinboardTabView] {
            (view as? OriginalPinboardTabView).map { [$0] } ?? view.subviews.flatMap { tabs(in: $0) }
        }
        func tab(named name: String) throws -> OriginalPinboardTabView {
            guard let result = tabs(in: ui.panel.contentView!).first(where: {
                ($0.titleView.subviews.first as? NSTextField)?.stringValue == name
            }) else { throw Failure(description: "Missing hosted tab \(name)") }
            return result
        }
        func mouse(_ type: NSEvent.EventType, cell: OriginalPinboardTabView, point: NSPoint,
                   clicks: Int = 1) -> NSEvent {
            NSEvent.mouseEvent(with: type, location: cell.convert(point, to: nil), modifierFlags: [],
                timestamp: ProcessInfo.processInfo.systemUptime, windowNumber: ui.panel.windowNumber,
                context: nil, eventNumber: 1, clickCount: clicks, pressure: 1)!
        }
        var tabHitChecks = 0
        for (name, id) in [(store.preferences.historyTitle, Optional<UUID>.none), (pin.name, Optional(pin.id))] {
            state.chooseBoard(id == nil ? pin.id : nil)
            try await Task.sleep(nanoseconds: 50_000_000)
            ui.panel.contentView!.layoutSubtreeIfNeeded()
            let cell = try tab(named: name)
            cell.layoutSubtreeIfNeeded()
            try require(cell.bounds.width > 30 && cell.bounds.height > 12)
            let points = [CGFloat(1), cell.bounds.midX, cell.bounds.maxX - 1].flatMap { x in
                [CGFloat(1), cell.bounds.midY, cell.bounds.maxY - 1].map { NSPoint(x: x, y: $0) }
            } + [NSPoint(x: 16, y: cell.bounds.midY), NSPoint(x: 26, y: cell.bounds.midY)]
            for point in points {
                state.chooseBoard(id == nil ? pin.id : nil)
                let content = ui.panel.contentView!
                guard let hit = content.hitTest(cell.convert(point, to: content.superview)),
                      hit === cell || hit.isDescendant(of: cell) else {
                    throw Failure(description: "Tab hit area missing at \(point) in \(cell.bounds)")
                }
                hit.mouseDown(with: mouse(.leftMouseDown, cell: cell, point: point))
                try require(state.pinboardID != id)
                hit.mouseUp(with: mouse(.leftMouseUp, cell: cell, point: point))
                try require(state.pinboardID == id)
                tabHitChecks += 1
            }
            state.chooseBoard(id == nil ? pin.id : nil)
            let inside = NSPoint(x: 1, y: cell.bounds.midY)
            cell.mouseDown(with: mouse(.leftMouseDown, cell: cell, point: inside))
            cell.mouseUp(with: mouse(.leftMouseUp, cell: cell, point: NSPoint(x: cell.bounds.maxX + 5, y: inside.y)))
            try require(state.pinboardID != id)
        }
        let editableTab = try tab(named: pin.name)
        let tabPanel = ui.panel as! ReplicaPanel
        editableTab.mouseDown(with: mouse(.leftMouseDown, cell: editableTab, point: .init(x: 1, y: 1), clicks: 2))
        try require(!editableTab.titleView.isEditing)
        let titlePoint = NSPoint(x: editableTab.titleView.frame.midX, y: editableTab.titleView.frame.midY)
        editableTab.titleView.mouseDown(with: mouse(.leftMouseDown, cell: editableTab, point: titlePoint, clicks: 2))
        try require(editableTab.titleView.isEditing && editableTab.titleView.ownsEditor(in: tabPanel))
        let priorBoard = state.pinboardID
        editableTab.mouseUp(with: mouse(.leftMouseUp, cell: editableTab, point: .init(x: 1, y: 1)))
        try require(state.pinboardID == priorBoard)
        editableTab.titleView.cancelOperation(nil)
        try require(!editableTab.titleView.isEditing && tabPanel.tabTitleEditingOwner == nil)
        try require(tabHitChecks == 22)
        key(53, "", [])
        try await waitForVisibility(false)
        state.searchVisible = true
        state.query = "missing search fixture"
        try await presentOffscreen()
        key(53, "", [])
        try await waitForVisibility(false)
        // User policy: the first Escape hides the panel, including active search.
        state.searchVisible = false
        state.query = ""
        try await presentOffscreen()
        let outside = NSWindow(contentRect: .init(x: screen.frame.maxX + 600, y: screen.frame.maxY + 600, width: 80, height: 80),
            styleMask: [.titled], backing: .buffered, defer: false)
        defer { outside.orderOut(nil) }
        let click = NSEvent.mouseEvent(with: .leftMouseDown, location: .init(x: 5, y: 5), modifierFlags: [],
            timestamp: ProcessInfo.processInfo.systemUptime, windowNumber: outside.windowNumber, context: nil,
            eventNumber: 1, clickCount: 1, pressure: 1)!
        NSApp.sendEvent(click)
        try await waitForVisibility(false)
        try await presentOffscreen()
        ui.hidePanel()
        ui.showPanel()
        ui.panel.setFrameOrigin(.init(x: screen.frame.maxX + 200, y: screen.frame.maxY + 200))
        try await Task.sleep(nanoseconds: 350_000_000)
        try require(ui.panel.isVisible)
        ui.hidePanel()
        try await waitForVisibility(false)
        print("{\"status\":\"passed\",\"passed\":true,\"checks\":[\"panel select/copy/deselect and original multi-text RTF/plain aggregation\",\"ordered multi-selection paste and custom quick/plain modifiers\",\"board navigation and original prepend/reverse Stack consumption\",\"pause/resume and native Stack rows\",\"NSItemProvider binary/HTML/Unicode and file paths; internal OCR excluded\",\"22 hosted tab hit points including icon/gaps/edges; release outside cancels; label-only double-click editing\",\"offscreen ordered panel visible before Escape; first Escape hides including search\",\"local outside-window click closes panel\",\"old closing completion cannot close a reopened panel\"],\"scope\":\"Isolated app ID/store/private pasteboard. Native offscreen windows and synthetic local events; no system keyboard posting, real cross-app paste or physical external-app click claim.\"}")
    }
}
