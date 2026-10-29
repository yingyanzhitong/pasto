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
        try require(!state.cloudSync.canSync && !state.cloudSync.isEnabled)
        state.cloudSync.start()
        state.cloudSync.setEnabled(true)
        try require(!state.cloudSync.isEnabled && !state.cloudSync.isBusy)
        try require(!state.originalCloudSync.canSync && !state.originalCloudSync.isEnabled)
        state.originalCloudSync.start()
        state.originalCloudSync.setEnabled(true)
        try require(!state.originalCloudSync.isEnabled && !state.originalCloudSync.isBusy)
        let cloudRow = NSHostingView(rootView: ICloudSyncGeneralRow(sync: state.originalCloudSync, drive: state.cloudSync))
        cloudRow.frame = NSRect(x: 0, y: 0, width: 430, height: 44)
        cloudRow.layoutSubtreeIfNeeded()
        try require(cloudRow.fittingSize.width > 0)
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
        func menuButtons(in view: NSView) -> [NSButton] {
            (view as? NSButton).map { [$0] } ?? view.subviews.flatMap { menuButtons(in: $0) }
        }
        let hostedButtons = menuButtons(in: ui.panel.contentView!)
        guard let more = hostedButtons.first(where: { $0.accessibilityIdentifier() == "panel-more-actions" || $0.accessibilityLabel() == "更多操作" }) else {
            throw Failure(description: "Missing more menu button: \(hostedButtons.map { "\(type(of: $0)) \($0.accessibilityLabel() ?? "") \($0.bounds)" })")
        }
        try require(more.bounds.width >= 44 && more.bounds.height >= 44)
        let content = ui.panel.contentView!
        let toolbarSearch = hostedButtons.first { $0.accessibilityLabel() == "搜索剪贴板" }!
        try require(abs(more.convert(more.bounds, to: content).midY
            - toolbarSearch.convert(toolbarSearch.bounds, to: content).midY) < 0.5)
        for step in 0..<64 {
            let angle = CGFloat(step) * .pi * 2 / 64
            let point = NSPoint(x: more.bounds.midX + cos(angle) * 21.5,
                                y: more.bounds.midY + sin(angle) * 21.5)
            let hit = content.hitTest(more.convert(point, to: content.superview))
            try require(hit === more || hit?.isDescendant(of: more) == true)
        }
        let resizePoint = NSPoint(x: 100, y: content.bounds.maxY - 1)
        try require(content.hitTest(content.convert(resizePoint, to: content.superview)) is ReplicaPanelResizeHandle)
        for x in [CGFloat(1), more.bounds.midX, more.bounds.maxX - 1] {
            for y in [CGFloat(1), more.bounds.midY, more.bounds.maxY - 1] {
                let hit = content.hitTest(more.convert(.init(x: x, y: y), to: content.superview))
                guard hit === more || hit?.isDescendant(of: more) == true else {
                    throw Failure(description: "More hit missing at \(x),\(y); bounds=\(more.bounds); frame=\(more.convert(more.bounds, to: content)); root=\(content.frame),\(content.bounds); hit=\(String(describing: hit)); hitFrame=\(String(describing: hit?.frame)); direct=\(String(describing: more.hitTest(more.convert(.init(x: x, y: y), to: more.superview))))")
                }
            }
        }
        // Search remains centered while the collapsed board strip grows to its
        // right; extra groups must scroll before reaching the more button.
        func searchFields(in view: NSView) -> [ReplicaSearchEditor.SearchField] {
            (view as? ReplicaSearchEditor.SearchField).map { [$0] }
                ?? view.subviews.flatMap { searchFields(in: $0) }
        }
        var extraGroups: [UUID] = []
        for groupCount in [1, 4, 13] {
            while store.pinboards.count < groupCount {
                extraGroups.append(try store.createPinboard(name: "Search layout \(store.pinboards.count)").id)
            }
            state.searchVisible = true
            for width: CGFloat in [1024, 1512, 2560] {
                ui.panel.setFrame(.init(x: screen.frame.maxX + 200, y: screen.frame.maxY + 200,
                    width: width, height: 332), display: true)
                try await Task.sleep(for: .milliseconds(100))
                content.layoutSubtreeIfNeeded()
                guard let field = searchFields(in: content).first,
                      let history = menuButtons(in: content).first(where: { $0.accessibilityLabel() == "返回剪贴板历史" }) else {
                    throw Failure(description: "Missing active search layout controls")
                }
                let fieldFrame = field.convert(field.bounds, to: content)
                let historyFrame = history.convert(history.bounds, to: content)
                let moreFrame = more.convert(more.bounds, to: content)
                try require(abs(fieldFrame.midX - content.bounds.midX) < 1)
                try require(abs(fieldFrame.width - max(400, (width - 16) * 0.25)) < 1)
                try require(abs(historyFrame.minX - fieldFrame.maxX - 8) < 1)
                try require(history.bounds.size == NSSize(width: 32, height: 32))
                let filters = field.f_100045730()
                try require(!filters.convert(filters.bounds, to: content).intersects(historyFrame))
                try require(moreFrame.minX > fieldFrame.maxX)
                for x in [CGFloat(1), more.bounds.midX, more.bounds.maxX - 1] {
                    for y in [CGFloat(1), more.bounds.midY, more.bounds.maxY - 1] {
                        let moreHit = content.hitTest(more.convert(.init(x: x, y: y), to: content.superview))
                        try require(moreHit === more || moreHit?.isDescendant(of: more) == true)
                    }
                }
            }
        }
        for id in extraGroups { try store.removePinboard(id: id) }
        state.searchVisible = false
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
        func saveFixtureScreenshot(_ view: NSView, name: String) throws {
            guard let path = ProcessInfo.processInfo.environment["PASTO_TEST_SCREENSHOT_DIRECTORY"] else { return }
            let folder = URL(fileURLWithPath: path, isDirectory: true)
            try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
            view.layoutSubtreeIfNeeded()
            let bitmap = view.bitmapImageRepForCachingDisplay(in: view.bounds)!
            view.cacheDisplay(in: view.bounds, to: bitmap)
            try bitmap.representation(using: .png, properties: [:])!.write(to: folder.appendingPathComponent(name + ".png"))
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
                    var chain: [String] = []
                    var ancestor: NSView? = cell
                    while let view = ancestor {
                        chain.append("\(type(of: view)): frame=\(view.frame) bounds=\(view.bounds) visible=\(view.visibleRect)")
                        ancestor = view.superview
                    }
                    throw Failure(description: "Tab hit area missing: \(name) at \(point); direct=\(String(describing: cell.hitTest(cell.convert(point, to: cell.superview)))); chain=\(chain)")
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
        state.chooseBoard(nil)
        ui.panel.contentView!.layoutSubtreeIfNeeded()
        let hoverTab = try tab(named: pin.name)
        func tabSnapshot(_ view: NSView) -> Data {
            let bitmap = view.bitmapImageRepForCachingDisplay(in: view.bounds)!
            view.cacheDisplay(in: view.bounds, to: bitmap)
            return bitmap.representation(using: .png, properties: [:])!
        }
        hoverTab.mouseExited(with: NSEvent.enterExitEvent(with: .mouseExited, location: .zero, modifierFlags: [],
            timestamp: 0, windowNumber: ui.panel.windowNumber, context: nil, eventNumber: 0, trackingNumber: 0, userData: nil)!)
        let withoutHover = tabSnapshot(hoverTab)
        hoverTab.mouseEntered(with: NSEvent.enterExitEvent(with: .mouseEntered, location: .zero, modifierFlags: [],
            timestamp: 0, windowNumber: ui.panel.windowNumber, context: nil, eventNumber: 0, trackingNumber: 0, userData: nil)!)
        try require(tabSnapshot(hoverTab) != withoutHover)
        try saveFixtureScreenshot(ui.panel.contentView!, name: "hover-panel")
        hoverTab.mouseExited(with: NSEvent.enterExitEvent(with: .mouseExited, location: .zero, modifierFlags: [],
            timestamp: 0, windowNumber: ui.panel.windowNumber, context: nil, eventNumber: 0, trackingNumber: 0, userData: nil)!)
        try require(tabSnapshot(hoverTab) == withoutHover)
        let editableTab = try tab(named: pin.name)
        let tabPanel = ui.panel as! ReplicaPanel
        editableTab.mouseDown(with: mouse(.leftMouseDown, cell: editableTab, point: .init(x: 1, y: 1), clicks: 2))
        try require(!editableTab.titleView.isEditing)
        let titlePoint = NSPoint(x: editableTab.titleView.frame.midX, y: editableTab.titleView.frame.midY)
        editableTab.titleView.mouseDown(with: mouse(.leftMouseDown, cell: editableTab, point: titlePoint, clicks: 2))
        guard editableTab.titleView.isEditing && editableTab.titleView.ownsEditor(in: tabPanel) else {
            throw Failure(description: "Inline double-click did not own editor; editing=\(editableTab.titleView.isEditing), responder=\(String(describing: tabPanel.firstResponder))")
        }
        let priorBoard = state.pinboardID
        editableTab.mouseUp(with: mouse(.leftMouseUp, cell: editableTab, point: .init(x: 1, y: 1)))
        try require(state.pinboardID == priorBoard)
        editableTab.titleView.cancelOperation(nil)
        try require(!editableTab.titleView.isEditing && tabPanel.tabTitleEditingOwner == nil)
        try require(tabHitChecks == 22)
        let countBeforeCreation = store.pinboards.count
        let selectionBeforeCreation = state.pinboardID
        ui.createPinboard()
        try require(store.pinboards.count == countBeforeCreation + 1)
        let newBoard = store.pinboards.last!
        try require(state.pinboardID == selectionBeforeCreation && newBoard.name == OriginalPinboardTitle.normalizedRename(""))
        try await Task.sleep(for: .milliseconds(350))
        ui.panel.contentView!.layoutSubtreeIfNeeded()
        let newTab = try tab(named: newBoard.name)
        try require(newTab.titleView.isEditing && newTab.titleView.ownsEditor(in: tabPanel))
        let editor = tabPanel.firstResponder as! NSTextView
        try require(editor.selectedRange().length == (newBoard.name as NSString).length)
        try saveFixtureScreenshot(ui.panel.contentView!, name: "inline-new-group")
        editor.insertText("Generated group rename", replacementRange: editor.selectedRange())
        let newField = newTab.titleView.subviews.first as! NSTextField
        _ = newTab.titleView.control(newField, textView: editor, doCommandBy: #selector(NSResponder.insertNewline(_:)))
        try require(store.pinboards.first { $0.id == newBoard.id }?.name == "Generated group rename")
        let capacity = OriginalHistoryCapacityControl(frame: .init(x: 0, y: 0, width: 420, height: 54))
        var capacityChanges: [Int] = []
        capacity.onCommit = { capacityChanges.append($0) }
        capacity.layoutSubtreeIfNeeded()
        try require(capacity.slider.numberOfTickMarks == 5 && !capacity.slider.allowsTickMarkValuesOnly)
        for index in 1...5 {
            capacity.slider.integerValue = index
            capacity.slider.sendAction(capacity.slider.action, to: capacity.slider.target)
        }
        try require(capacityChanges == [1, 7, 30, 365, 0])
        for (position, days) in [(1.5, 4), (2.5, 14), (3.5, 180), (4.5, 365), (5.5, 0)] {
            try require(OriginalHistoryCapacity.days(for: position) == days)
        }
        try require(OriginalHistoryCapacity.days(for: .nan) == nil && OriginalHistoryCapacity.days(for: 0) == nil)

        if ProcessInfo.processInfo.environment["PASTO_TEST_SCREENSHOT_DIRECTORY"] != nil {
            state.store.preferences.historyRetentionDays = 7
            let settingsWindow = NSPanel(contentRect: .init(x: 0, y: 0, width: 760, height: 640),
                styleMask: [.titled, .nonactivatingPanel], backing: .buffered, defer: false)
            let settingsView = NSHostingView(rootView: ReplicaSettingsView(state: state))
            settingsWindow.contentView = settingsView
            settingsWindow.setFrameOrigin(.init(x: screen.frame.maxX + 300, y: screen.frame.maxY + 300))
            settingsWindow.orderBack(nil)
            try await Task.sleep(for: .milliseconds(150))
            try saveFixtureScreenshot(settingsView, name: "history-retention")
            settingsWindow.orderOut(nil)
        }

        // Delete only synthetic groups. Confirmation is panel content, not a
        // separate window/modal; preserve the original empty/nonempty split.
        state.chooseBoard(nil)
        let windowsBeforeDeletion = Set(NSApp.windows.map(ObjectIdentifier.init))
        let emptyGroup = try store.createPinboard(name: "Empty deletion fixture")
        state.chooseBoard(emptyGroup.id)
        ui.removePinboard(emptyGroup)
        try require(!store.pinboards.contains { $0.id == emptyGroup.id })
        try require(state.pinboardID == nil && state.pendingPinboardDeletionID == nil && ui.panel.isVisible)
        let deleteGroup = try store.createPinboard(name: "Delete fixture")
        let retainedGroup = try store.createPinboard(name: "Retained fixture")
        let historyID = try store.add(ClipboardItem(plainText: "delete history fixture", pinboardIDs: [deleteGroup.id]))
        let onlyGroupID = try store.add(ClipboardItem(plainText: "delete only fixture", pinboardIDs: [deleteGroup.id], isInHistory: false))
        let sharedID = try store.add(ClipboardItem(plainText: "delete shared fixture", pinboardIDs: [deleteGroup.id, retainedGroup.id], isInHistory: false))
        state.chooseBoard(deleteGroup.id)
        ui.removePinboard(deleteGroup)
        try await Task.sleep(for: .milliseconds(100))
        try require(state.pendingPinboardDeletionID == deleteGroup.id && state.pinboardID == deleteGroup.id)
        try require(ui.panel.isVisible && NSApp.modalWindow == nil && ui.panel.sheets.isEmpty)
        try require(Set(NSApp.windows.map(ObjectIdentifier.init)) == windowsBeforeDeletion)
        try require(store.items.contains { $0.id == onlyGroupID })
        ui.panel.contentView!.layoutSubtreeIfNeeded()
        try saveFixtureScreenshot(ui.panel.contentView!, name: "inline-group-deletion")
        key(8, "c", .command)
        key(51, "", [])
        try require(ui.panel.isVisible && store.items.contains { $0.id == onlyGroupID })
        key(53, "", [])
        try require(state.pendingPinboardDeletionID == nil && ui.panel.isVisible)
        try require(store.pinboards.contains { $0.id == deleteGroup.id })
        ui.removePinboard(deleteGroup)
        ui.cancelPinboardRemoval()
        try require(state.pendingPinboardDeletionID == nil && ui.panel.isVisible)
        ui.removePinboard(deleteGroup)
        state.chooseBoard(retainedGroup.id)
        try require(state.pendingPinboardDeletionID == nil)
        func deletionSQL(_ sql: String) throws {
            let process = Process()
            process.executableURL = URL(fileURLWithPath: "/usr/bin/sqlite3")
            process.arguments = [directory.appendingPathComponent("clipboard.sqlite").path, sql]
            try process.run()
            process.waitUntilExit()
            try require(process.terminationStatus == 0)
        }
        state.chooseBoard(deleteGroup.id)
        ui.removePinboard(deleteGroup)
        try deletionSQL("CREATE TRIGGER reject_group_deletion BEFORE DELETE ON ZPINBOARD BEGIN SELECT RAISE(ABORT,'synthetic group deletion failure'); END;")
        ui.confirmPinboardRemoval()
        try require(state.pendingPinboardDeletionID == deleteGroup.id && state.pinboardDeletionError != nil)
        try require(state.pinboardID == deleteGroup.id && ui.panel.isVisible && NSApp.modalWindow == nil)
        try require(store.pinboards.contains { $0.id == deleteGroup.id } && store.items.contains { $0.id == onlyGroupID })
        try deletionSQL("DROP TRIGGER reject_group_deletion;")
        ui.cancelPinboardRemoval()
        state.chooseBoard(retainedGroup.id)
        ui.removePinboard(deleteGroup)
        key(36, "\r", [])
        try require(ui.panel.isVisible && state.pendingPinboardDeletionID == nil && state.pinboardID == retainedGroup.id)
        try require(!store.pinboards.contains { $0.id == deleteGroup.id })
        try require(store.items.contains { $0.id == historyID && $0.isInHistory && $0.pinboardIDs.isEmpty })
        try require(!store.items.contains { $0.id == onlyGroupID })
        try require(store.items.first { $0.id == sharedID }?.pinboardIDs == [retainedGroup.id])
        let afterDeletion = try ClipboardStore(directoryURL: directory)
        try require(!afterDeletion.pinboards.contains { $0.id == deleteGroup.id })
        try require(afterDeletion.items.contains { $0.id == historyID } && !afterDeletion.items.contains { $0.id == onlyGroupID })
        ui.removePinboard(retainedGroup)
        ui.confirmPinboardRemoval()
        try require(state.pinboardID == nil && state.pendingPinboardDeletionID == nil && ui.panel.isVisible)
        try require(!store.items.contains { $0.id == sharedID })
        ui.removePinboard(pin)
        ui.hidePanel()
        try require(state.pendingPinboardDeletionID == nil)
        try await waitForVisibility(false)
        try await presentOffscreen()
        try require(state.pendingPinboardDeletionID == nil && store.pinboards.contains { $0.id == pin.id })

        state.chooseBoard(nil)
        state.select(store.items.first { $0.id == first }!)
        let priorCopyDate = store.items.first { $0.id == first }!.updatedAt
        var copyFeedbackCount = 0
        var restoreNotifiedBeforeFeedback = false
        var savedBeforeFeedback = false
        let restoreSubscription = store.didRestoreItem.sink { restoreNotifiedBeforeFeedback = true }
        ui.copiedItemsHandler = {
            copyFeedbackCount += 1
            let reopened = try? ClipboardStore(directoryURL: directory)
            savedBeforeFeedback = restoreNotifiedBeforeFeedback
                && reopened?.items.first { $0.id == first }?.updatedAt == store.items.first { $0.id == first }?.updatedAt
        }
        key(8, "c", .command)
        try require(board.string(forType: .string) == "FIRST fixture")
        try require(ui.panel.isVisible && copyFeedbackCount == 1)
        try require(savedBeforeFeedback)
        try require(store.items.first { $0.id == first }!.updatedAt > priorCopyDate)
        try await waitForVisibility(false)
        restoreSubscription.cancel()
        let afterCopy = try ClipboardStore(directoryURL: directory)
        try require(afterCopy.items.first { $0.id == first }!.updatedAt > priorCopyDate)
        try await presentOffscreen()
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
        state.chooseBoard(nil)
        state.select(store.items.first { $0.id == first }!)
        let beforeInterruptedCopy = store.items.first { $0.id == first }!.updatedAt
        key(8, "c", .command)
        ui.copySelection(plainTextOnly: true)
        try require(copyFeedbackCount == 3)
        try require(store.items.first { $0.id == first }!.updatedAt > beforeInterruptedCopy)
        ui.showPanel()
        try require(store.items.first { $0.id == first }!.updatedAt > beforeInterruptedCopy)
        ui.panel.setFrameOrigin(.init(x: screen.frame.maxX + 200, y: screen.frame.maxY + 200))
        try await Task.sleep(nanoseconds: 350_000_000)
        try require(ui.panel.isVisible)
        ui.hidePanel()
        try await waitForVisibility(false)
        // Exercise the native card's actual double-click route, not only the
        // controller copy entry point or an injected delivery recorder.
        ui.pasteItemsHandler = { ids, plain in
            do {
                try store.writeToPasteboard(ids: ids, pasteboard: board, plainTextOnly: plain)
                ui.hidePanel()
                return true
            } catch { return false }
        }
        for _ in 0..<2 {
            try await presentOffscreen()
            state.chooseBoard(nil)
            state.select(store.items.first { $0.id == first }!)
            try await Task.sleep(for: .milliseconds(50))
            guard let collection = (ui.panel as? ReplicaPanel)?.collectionFocusTarget as? ReplicaNativeCollectionHost,
                  let cell = collection.previewAnchor(for: first) else {
                throw Failure(description: "Missing native double-click fixture cell")
            }
            let event = NSEvent.mouseEvent(with: .leftMouseDown,
                location: cell.convert(.init(x: cell.bounds.midX, y: cell.bounds.midY), to: nil),
                modifierFlags: [], timestamp: ProcessInfo.processInfo.systemUptime,
                windowNumber: ui.panel.windowNumber, context: nil, eventNumber: 1,
                clickCount: 2, pressure: 1)!
            collection.mouseDown(with: event)
            try await waitForVisibility(false)
            try require(board.string(forType: .string) == store.items.first { $0.id == first }!.plainText)
        }
        var focusTransitions: [String] = []
        var closeWasVisible = false
        ui.panelWillShow = { focusTransitions.append("remember") }
        ui.panelWillClose = { restore in
            focusTransitions.append(restore ? "restore" : "keep-preview")
            closeWasVisible = ui.panel.isVisible
        }
        ui.togglePanel()
        try await waitForVisibility(true)
        ui.panel.setFrameOrigin(.init(x: screen.frame.maxX + 200, y: screen.frame.maxY + 200))
        try await Task.sleep(for: .milliseconds(200))
        ui.togglePanel()
        try require(focusTransitions == ["remember", "restore"] && closeWasVisible)
        ui.hidePanel()
        try require(focusTransitions == ["remember", "restore"])
        try await waitForVisibility(false)
        let previewID = try store.add(ClipboardItem(plainText: "Detached preview focus fixture",
            pinboardIDs: [pin.id], isInHistory: false))
        ui.showPreview(item: store.items.first { $0.id == previewID }!)
        let detached = NSApp.windows.compactMap { $0 as? OriginalPreviewWindow }
        try require(!detached.isEmpty)
        ui.togglePanel()
        try await waitForVisibility(true)
        ui.panel.setFrameOrigin(.init(x: screen.frame.maxX + 200, y: screen.frame.maxY + 200))
        try await Task.sleep(for: .milliseconds(200))
        ui.togglePanel()
        try require(focusTransitions == ["remember", "restore", "remember", "keep-preview"])
        try await waitForVisibility(false)
        detached.forEach { $0.close() }
        print("{\"status\":\"passed\",\"passed\":true,\"checks\":[\"panel select/copy/deselect and original multi-text RTF/plain aggregation\",\"ordered multi-selection paste and custom quick/plain modifiers\",\"board navigation and original prepend/reverse Stack consumption\",\"pause/resume and native Stack rows\",\"NSItemProvider binary/HTML/Unicode and file paths; internal OCR excluded\",\"22 hosted tab hit points including icon/gaps/edges; release outside cancels; label-only double-click editing\",\"hover bitmap changes/restores; inline create/select-all/rename; native retention anchors and intermediate day/week/month mapping\",\"offscreen ordered panel visible before Escape; first Escape hides including search\",\"local outside-window click closes panel\",\"old closing completion cannot close a reopened panel\"],\"scope\":\"Isolated app ID/store/private pasteboard. Native offscreen windows and synthetic local events; no system keyboard posting, real cross-app paste or physical external-app click claim.\"}")
    }
}
