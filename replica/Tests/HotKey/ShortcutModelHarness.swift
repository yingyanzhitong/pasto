import AppKit
import Foundation
import PastoCore

@main
struct ShortcutModelHarness {
    struct Failure: Error, CustomStringConvertible { let description: String }
    static func main() {
        do { try run() }
        catch {
            print(String(data: try! JSONSerialization.data(withJSONObject: ["status": "failed", "reason": String(describing: error)]), encoding: .utf8)!)
            exit(1)
        }
    }
    static func require(_ condition: @autoclosure () -> Bool, line: UInt = #line) throws {
        if !condition() { throw Failure(description: "Shortcut assertion failed at line \(line)") }
    }
    static func run() throws {
        var checks = [String]()
        let decoder = JSONDecoder(), encoder = JSONEncoder()
        let defaults = try decoder.decode(AppPreferences.self, from: Data("{}".utf8))
        try require(defaults.historyShortcut == .historyDefault && defaults.stackShortcut == .stackDefault)
        try require(defaults.previousPinboardShortcut == .previousPinboardDefault && defaults.nextPinboardShortcut == .nextPinboardDefault)
        try require(defaults.quickPasteModifierRawValue == NSEvent.ModifierFlags.command.rawValue)
        try require(defaults.plainTextModifierRawValue == NSEvent.ModifierFlags.shift.rawValue)
        try require(defaults.showDuringScreenSharing && defaults.ignoreTransientContent)
        checks.append("legacy JSON missing fields receives evidence-backed defaults")

        var preferences = defaults
        preferences.historyShortcut = nil; preferences.stackShortcut = nil
        preferences.previousPinboardShortcut = nil; preferences.nextPinboardShortcut = nil
        let cleared = try encoder.encode(preferences)
        let json = try JSONSerialization.jsonObject(with: cleared) as! [String: Any]
        try require(json["historyShortcut"] is NSNull && json["stackShortcut"] is NSNull)
        try require(json["previousPinboardShortcut"] is NSNull && json["nextPinboardShortcut"] is NSNull)
        let reloadedCleared = try decoder.decode(AppPreferences.self, from: cleared)
        try require(reloadedCleared == preferences)
        checks.append("cleared shortcuts encode explicit null and remain disabled after reload")

        let custom = KeyboardShortcut(keyCode: 79, modifierRawValue: NSEvent.ModifierFlags([.control, .option]).rawValue)
        try require(custom.isValidGlobal && custom.displayName == "⌃⌥F18")
        preferences.historyShortcut = custom
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: false)
        defer { try? FileManager.default.removeItem(at: directory) }
        let file = directory.appendingPathComponent("preferences.json")
        try encoder.encode(preferences).write(to: file, options: .atomic)
        let reloadedCustom = try decoder.decode(AppPreferences.self, from: Data(contentsOf: file))
        try require(reloadedCustom == preferences)
        preferences = AppPreferences()
        try require(preferences == defaults)
        checks.append("custom recording persists to isolated disk fixture; reset restores defaults")

        try require(!KeyboardShortcut(keyCode: 0, modifierRawValue: 0).isValidGlobal)
        try require(!KeyboardShortcut(keyCode: 0, modifierRawValue: NSEvent.ModifierFlags.shift.rawValue).isValidGlobal)
        try require(KeyboardShortcut(keyCode: 55, modifierRawValue: NSEvent.ModifierFlags.command.rawValue).isValidGlobal)
        try require(KeyboardShortcut(keyCode: 53, modifierRawValue: NSEvent.ModifierFlags.command.rawValue).isValidGlobal)
        try require(KeyboardShortcut(keyCode: 999, modifierRawValue: NSEvent.ModifierFlags.command.rawValue).isValidGlobal)
        try require(KeyboardShortcut(keyCode: 79, modifierRawValue: 0).isValidGlobal)
        try require(KeyboardShortcut(keyCode: 90, modifierRawValue: 0).isValidGlobal)
        checks.append("original modifier predicate rejects bare/shift-only text; permits F1-F20 and Cmd/Ctrl/Option even for special key codes")

        let event = NSEvent.keyEvent(with: .keyDown, location: .zero, modifierFlags: [.control, .option, .capsLock], timestamp: 0,
                                    windowNumber: 0, context: nil, characters: "", charactersIgnoringModifiers: "", isARepeat: false, keyCode: 79)!
        try require(!custom.matches(event) && !KeyboardShortcut.historyDefault.matches(event))
        let filtered = NSEvent.keyEvent(with: .keyDown, location: .zero, modifierFlags: [.control, .option, .numericPad, .function], timestamp: 0,
                                    windowNumber: 0, context: nil, characters: "", charactersIgnoringModifiers: "", isARepeat: false, keyCode: 79)!
        try require(custom.matches(filtered))
        try require(KeyboardShortcut.historyDefault.displayName.hasPrefix("⇧⌘"))
        try require(KeyboardShortcut.stackDefault.displayName.hasPrefix("⇧⌘"))
        checks.append("event mask 0xff5f0000 preserves Caps Lock and removes numericPad/function; default labels retain modifier order")
        let value: [String: Any] = ["status": "passed", "checks": checks,
                                   "scope": "Isolated preference JSON/disk and synthetic NSEvent objects only; no global registration or clipboard access."]
        print(String(data: try JSONSerialization.data(withJSONObject: value, options: [.sortedKeys, .prettyPrinted]), encoding: .utf8)!)
    }
}
