import AppKit
import Carbon
import PastoCore

@MainActor
final class GlobalHotKey {
    private var registeredShortcut: PastoCore.KeyboardShortcut?
    private var monitor: OriginalGlobalShortcutMonitor?
    var action: (() -> Void)?

    func register(keyCode: UInt32 = UInt32(kVK_ANSI_V), modifiers: NSEvent.ModifierFlags = [.command, .shift],
                  identifier: UInt32 = 1) -> OSStatus {
        unregister()
        // The external identifier belongs to the replica facade. The reference
        // allocates a process-wide Carbon ID for every registration attempt.
        _ = identifier
        let shortcut = PastoCore.KeyboardShortcut(keyCode: keyCode, modifierRawValue: modifiers.rawValue)
        let monitor = OriginalGlobalShortcutMonitor.shared
        self.monitor = monitor
        let status = monitor.f_1001eaa64(shortcut: shortcut) { [weak self] in self?.action?() }
        if status == noErr { registeredShortcut = shortcut }
        return status
    }

    func unregister() {
        if let registeredShortcut { monitor?.f_1001eae90(shortcut: registeredShortcut) }
        registeredShortcut = nil
    }
}
