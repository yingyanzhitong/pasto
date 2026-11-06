import AppKit
import PastoCore

@main
struct SearchButtonHarness {
    struct Failure: Error, CustomStringConvertible { let description: String }

    static func require(_ condition: @autoclosure () -> Bool, line: UInt = #line) throws {
        if !condition() { throw Failure(description: "Search assertion failed at line \(line)") }
    }

    @MainActor static func main() {
        _ = NSApplication.shared
        NSApp.setActivationPolicy(.accessory)
        Task { @MainActor in
            do { try await run(); exit(0) }
            catch { print("Search regression failed: \(error)"); exit(1) }
        }
        NSApp.run()
    }

    @MainActor static func run() async throws {
        _ = NSApplication.shared
        guard let screen = NSScreen.main else { throw Failure(description: "No window-server screen") }
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: directory) }
        let board = NSPasteboard(name: .init("PastoSearchHarness-\(UUID().uuidString)"))
        defer { board.releaseGlobally() }
        let store = try ClipboardStore(directoryURL: directory)
        let matchingID = try store.add(ClipboardItem(plainText: "FIRST search fixture"))
        _ = try store.add(ClipboardItem(plainText: "SECOND search fixture"))
        let ui = ReplicaUIController(store: store)
        ui.pasteboard = board
        let panel = ui.panel
        defer { panel.orderOut(nil) }
        panel.setFrameOrigin(.init(x: screen.frame.maxX + 200, y: screen.frame.maxY + 200))
        ui.showPanel()
        panel.setFrameOrigin(.init(x: screen.frame.maxX + 200, y: screen.frame.maxY + 200))
        try await Task.sleep(for: .milliseconds(500))
        let content = panel.contentView!

        func descendants<T: NSView>(in view: NSView, of type: T.Type) -> [T] {
            (view as? T).map { [$0] } ?? view.subviews.flatMap { descendants(in: $0, of: type) }
        }
        guard let button = descendants(in: content, of: NSButton.self).first(where: {
            $0.accessibilityLabel() == "搜索剪贴板"
        }), let field = descendants(in: content, of: ReplicaSearchEditor.SearchField.self).first else {
            throw Failure(description: "Missing native search controls")
        }
        let editor = field.f_100045c2c().f_100041f9c()
        func key(_ code: UInt16, _ chars: String, _ modifiers: NSEvent.ModifierFlags = []) {
            panel.sendEvent(NSEvent.keyEvent(with: .keyDown, location: .zero, modifierFlags: modifiers,
                timestamp: 0, windowNumber: panel.windowNumber, context: nil, characters: chars,
                charactersIgnoringModifiers: chars, isARepeat: false, keyCode: code)!)
        }

        var activationMilliseconds: [Double] = []
        for _ in 0..<3 {
            try require(!ui.state.searchVisible && panel.isVisible)
            content.layoutSubtreeIfNeeded()
            // Test the center, icon, padding, and edges through the real panel hit tree.
            for x in [CGFloat(1), button.bounds.midX, button.bounds.maxX - 1] {
                for y in [CGFloat(1), button.bounds.midY, button.bounds.maxY - 1] {
                    let hit = content.hitTest(button.convert(.init(x: x, y: y), to: content.superview))
                    guard hit === button || hit?.isDescendant(of: button) == true else {
                        throw Failure(description: "Search button blocked by \(String(describing: hit)) at \(x),\(y)")
                    }
                }
            }
            let clickPoint = button.convert(.init(x: button.bounds.midX, y: button.bounds.midY), to: nil)
            func mouse(_ type: NSEvent.EventType) -> NSEvent {
                NSEvent.mouseEvent(with: type, location: clickPoint, modifierFlags: [],
                    timestamp: ProcessInfo.processInfo.systemUptime, windowNumber: panel.windowNumber,
                    context: nil, eventNumber: 1, clickCount: 1, pressure: 1)!
            }
            let mouseUp = mouse(.leftMouseUp)
            NSApp.postEvent(mouseUp, atStart: true)
            panel.sendEvent(mouse(.leftMouseDown))
            let elapsed = (ProcessInfo.processInfo.systemUptime - mouseUp.timestamp) * 1000
            guard ui.state.toolbarOwner?.searchBar.isActive == true, panel.firstResponder === editor else {
                throw Failure(description: "Search activation deferred after mouse action returned (\(elapsed) ms)")
            }
            activationMilliseconds.append(elapsed)
            try await Task.sleep(for: .milliseconds(300))
            try require(ui.state.searchVisible && panel.firstResponder === editor)
            let fieldHit = content.hitTest(field.convert(.init(x: 8, y: field.bounds.midY), to: content.superview))
            try require(fieldHit === field || fieldHit?.isDescendant(of: field) == true)
            editor.insertText("FIRST", replacementRange: editor.selectedRange())
            let deadline = Date().addingTimeInterval(10)
            while ui.state.visibleItems.map(\.id) != [matchingID], Date() < deadline {
                try await Task.sleep(for: .milliseconds(100))
            }
            guard ui.state.query == "FIRST", ui.state.visibleItems.map(\.id) == [matchingID] else {
                throw Failure(description: "Search input/result mismatch: query=\(ui.state.query), count=\(ui.state.visibleItems.count), failed=\(ui.state.searchFailed)")
            }
            ui.state.applySearchInput(nodes: [], text: "", filters: [])
            ui.state.searchVisible = false
            try await Task.sleep(for: .milliseconds(300))
            guard !ui.state.searchVisible, panel.isVisible, ui.state.isSearchQueryEmpty else {
                throw Failure(description: "Search reset mismatch: active=\(ui.state.searchVisible), panel=\(panel.isVisible), empty=\(ui.state.isSearchQueryEmpty)")
            }
            key(3, "f", .command)
            try await Task.sleep(for: .milliseconds(300))
            try require(ui.state.searchVisible && panel.firstResponder === editor)
            // The original action toggles an already-active empty search closed.
            _ = button.sendAction(button.action, to: button.target)
            try require(!ui.state.searchVisible && ui.state.toolbarOwner?.searchBar.isActive == false)
            try await Task.sleep(for: .milliseconds(300))
        }
        let report: [String: Any] = ["passed": true, "search_hit_checks": 27,
            "mouse_search_cycles": 3, "keyboard_search_cycles": 3,
            "synchronous_activation": true, "mouse_up_to_focus_ms": activationMilliseconds]
        print(String(data: try JSONSerialization.data(withJSONObject: report), encoding: .utf8)!)
    }
}
