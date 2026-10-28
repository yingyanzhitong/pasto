import AppKit
import Carbon
import Foundation
import PastoCore

// Local Carbon events only: no keyboard posting or pasteboard access.
@main
struct HotKeyHarness {
    struct Failure: Error, CustomStringConvertible { let description: String }
    @MainActor static func main() {
        do { try run() }
        catch {
            print(String(data: try! JSONSerialization.data(withJSONObject: ["status": "failed", "reason": String(describing: error)], options: [.sortedKeys]), encoding: .utf8)!)
            exit(1)
        }
    }
    @MainActor static func run() throws {
        NSApplication.shared.setActivationPolicy(.prohibited)
        var diagnostics: [OriginalShortcutDiagnostic] = []
        let overrides = OriginalDependencyOverrides()
        overrides.f_1000d83a8(\OriginalDependencyValues.shortcutDiagnostic) {
            { diagnostics.append($0) }
        }
        try OriginalDependencies.withOverrides(overrides) {
            func require(_ condition: Bool, _ message: String) throws {
                if !condition { throw Failure(description: message) }
            }
            func actualID() throws -> UInt32 {
                guard let message = diagnostics.last(where: { $0.message.hasPrefix("registered carbonID=") })?.message,
                      let token = message.split(separator: " ").first(where: { $0.hasPrefix("carbonID=") }),
                      let id = UInt32(token.dropFirst("carbonID=".count)) else {
                    throw Failure(description: "Successful registration did not emit its actual Carbon ID")
                }
                return id
            }
            func pump() { RunLoop.main.run(until: Date().addingTimeInterval(0.06)) }
            func deliver(_ id: UInt32, signature: UInt32 = 1) -> OSStatus {
                var event: EventRef?
                let status = CreateEvent(nil, OSType(kEventClassKeyboard), UInt32(kEventHotKeyPressed),
                    GetCurrentEventTime(), EventAttributes(kEventAttributeUserEvent), &event)
                guard status == noErr, let event else { return status }
                defer { ReleaseEvent(event) }
                var key = EventHotKeyID(signature: signature, id: id)
                let set = SetEventParameter(event, EventParamName(kEventParamDirectObject), EventParamType(typeEventHotKeyID),
                    MemoryLayout<EventHotKeyID>.size, &key)
                guard set == noErr else { return set }
                return SendEventToEventTarget(event, GetEventDispatcherTarget())
            }
            let first = GlobalHotKey(), replacement = GlobalHotKey(), second = GlobalHotKey()
            defer { first.unregister(); replacement.unregister(); second.unregister() }
            var firstCount = 0, replacementCount = 0, secondCount = 0
            first.action = { firstCount += 1 }
            replacement.action = { replacementCount += 1 }
            second.action = { secondCount += 1 }
            let candidates = [kVK_F18, kVK_F19, kVK_F20, kVK_F17, kVK_F16, kVK_F15, kVK_F14, kVK_F13].map(UInt32.init)
            guard let firstCode = candidates.first(where: { first.register(keyCode: $0, identifier: 41) == noErr }) else {
                print("{\"status\":\"blocked\",\"reason\":\"No unused function-key combination\"}"); exit(77)
            }
            let oldID = try actualID()
            guard let secondCode = candidates.first(where: { $0 != firstCode && second.register(keyCode: $0, identifier: 44) == noErr }) else {
                print("{\"status\":\"blocked\",\"reason\":\"No second unused function-key combination\"}"); exit(77)
            }
            let secondID = try actualID()
            try require(replacement.register(keyCode: firstCode, identifier: 42) == noErr, "Same-manager registration must replace the existing shortcut")
            let replacementID = try actualID()
            try require(deliver(oldID) == noErr, "Missing ID must still return noErr")
            pump()
            try require(firstCount == 0, "Replaced registration fired through its old ID")
            try require(deliver(replacementID) == noErr, "Replacement delivery failed")
            pump()
            try require(replacementCount == 1, "Replacement main-queue action did not execute")
            try require(first.register(keyCode: firstCode, identifier: 43) == noErr, "Re-registration failed")
            let currentID = try actualID()
            try require(Set([oldID, secondID, replacementID, currentID]).count == 4, "Registration attempts must allocate fresh process IDs")
            try require(deliver(currentID) == noErr && deliver(secondID) == noErr, "Registered event was not consumed")
            pump()
            try require(firstCount == 1 && secondCount == 1, "Current callback counts differ")
            try require(deliver(currentID, signature: 0x12345678) == noErr, "Other signature was not consumed")
            pump()
            try require(firstCount == 2, "Original routing compares ID only, not signature")
            first.unregister()
            try require(deliver(currentID) == noErr, "Removed ID must still be consumed")
            pump()
            try require(firstCount == 2, "Removed registration still invoked its action")
            try require(diagnostics.contains { $0.metadata["carbon_id"] == Int(oldID) }, "Missing-ID diagnostic was not emitted")
            let value: [String: Any] = ["status": "passed", "key_codes": [firstCode, secondCode],
                "actual_carbon_ids": [oldID, secondID, replacementID, currentID],
                "callbacks": ["first": firstCount, "replacement": replacementCount, "second": secondCount],
                "checks": ["replacement", "fresh IDs", "dispatcher target", "main async", "ID-only routing", "unregistered IDs"],
                "scope": "Isolated bundle/DI, temporary function-key registrations, synthetic Carbon events to this process. No real key input or clipboard access."]
            print(String(data: try JSONSerialization.data(withJSONObject: value, options: [.sortedKeys, .prettyPrinted]), encoding: .utf8)!)
        }
    }
}
