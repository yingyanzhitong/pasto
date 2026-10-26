import AppKit
import Carbon
import Foundation
import OSLog

public enum OriginalShortcutMonitorError: Error, CustomStringConvertible {
    case eventHandler(OSStatus)
    case hotKey(OSStatus)

    public var description: String {
        switch self {
        case let .eventHandler(status):
            return "Failed to install Carbon event handler (OSStatus: \(status))"
        case let .hotKey(status):
            return "Failed to register Carbon hot key (OSStatus: \(status))"
        }
    }
}

public struct OriginalShortcutDiagnostic {
    public enum Level { case information, warning, error }
    public let level: Level
    public let topic: String?
    public let message: String
    public let tags: [String: String]
    public let metadata: [String: Int]
    public let error: OriginalShortcutMonitorError?
}

private final class OriginalShortcutCarbonIDCounter {
    static let shared = OriginalShortcutCarbonIDCounter()
    private var value: UInt32 = 0
    private let lock = NSLock()

    func next() -> UInt32 {
        lock.lock()
        defer { lock.unlock() }
        precondition(value < UInt32.max)
        value += 1
        return value
    }
}

/// A successful registration is retained by the monitor's shortcut dictionary.
/// Removing the entry releases this object and unregisters its Carbon handle.
public final class OriginalShortcutRegistration {
    public let action: () -> Void
    public let identifier: UInt32
    public let status: OSStatus
    private var reference: EventHotKeyRef?

    public init(keyCode: Int, modifierRawValue: UInt, action: @escaping () -> Void) {
        self.action = action
        identifier = OriginalShortcutCarbonIDCounter.shared.next()
        precondition(keyCode >= 0 && keyCode <= Int(UInt32.max))
        let hotKey = EventHotKeyID(signature: 1, id: identifier)
        var reference: EventHotKeyRef?
        status = RegisterEventHotKey(UInt32(keyCode),
                                    OriginalShortcutFunctions.f_1001e7d58(modifierRawValue: modifierRawValue),
                                    hotKey, GetEventDispatcherTarget(), 0, &reference)
        self.reference = reference
    }

    private func f_1001eb110() {
        if let reference { UnregisterEventHotKey(reference) }
        reference = nil
    }

    deinit { f_1001eb110() }
}

/// The reference installs one dispatcher handler for all registered shortcuts,
/// allocates process-wide IDs and delivers a retained action on the main queue.
public final class OriginalGlobalShortcutMonitor {
    public static var shared: OriginalGlobalShortcutMonitor { OriginalDependencyValues().f_1001e7514() }

    public static func f_1001e752c() -> OriginalGlobalShortcutMonitor { OriginalGlobalShortcutMonitor() }
    private static let logger = Logger(subsystem: "Pasto", category: "shortcuts")
    private var handler: EventHandlerRef?
    private let lock = NSLock()
    private var registrations: [OriginalShortcutValue: OriginalShortcutRegistration] = [:]
    private let diagnostic: OriginalDependency<(OriginalShortcutDiagnostic) -> Void>

    public init() {
        self.diagnostic = OriginalDependency(\OriginalDependencyValues.shortcutDiagnostic)
        var specification = EventTypeSpec(eventClass: OSType(kEventClassKeyboard),
                                          eventKind: UInt32(kEventHotKeyPressed))
        let status = InstallEventHandler(GetEventDispatcherTarget(), { call, event, context in
            OriginalGlobalShortcutMonitor.f_1001ea96c(call, event, context)
        }, 1, &specification, Unmanaged.passUnretained(self).toOpaque(), &handler)
        if status != noErr {
            let failure = OriginalShortcutMonitorError.eventHandler(status)
            emit(OriginalShortcutDiagnostic(level: .error, topic: nil,
                message: failure.description, tags: [:], metadata: ["status": Int(status)], error: failure))
        }
    }

    private func emit(_ diagnostic: OriginalShortcutDiagnostic) {
        let write = self.diagnostic.f_1000da768()
        write(diagnostic)
    }

    static func writeDiagnostic(_ diagnostic: OriginalShortcutDiagnostic) {
        let message = diagnostic.message
        let metadata = String(describing: diagnostic.metadata)
        switch diagnostic.level {
        case .information: logger.info("\(message, privacy: .public)")
        case .warning: logger.warning("\(message, privacy: .public) \(metadata, privacy: .public)")
        case .error: logger.error("\(message, privacy: .public) \(metadata, privacy: .public)")
        }
    }

    @discardableResult
    public func f_1001eaa64(shortcut: KeyboardShortcut, action: @escaping () -> Void) -> OSStatus {
        f_1001eaa64(shortcut: OriginalShortcutValue(keyCode: Int(shortcut.keyCode),
            internalModifiers: shortcut.modifierRawValue), action: action)
    }

    @discardableResult
    public func f_1001eaa64(shortcut: OriginalShortcutValue, action: @escaping () -> Void) -> OSStatus {
        f_1001eae90(shortcut: shortcut)
        let registration = OriginalShortcutRegistration(keyCode: shortcut.keyCode,
            modifierRawValue: shortcut.internalModifiers, action: action)
        let modifiers = OriginalShortcutFunctions.f_1001e7d58(modifierRawValue: shortcut.internalModifiers)
        if registration.status == noErr {
            lock.lock()
            f_1001eb1e4(registration, for: shortcut)
            lock.unlock()
            emit(OriginalShortcutDiagnostic(level: .information, topic: "shortcuts",
                message: "registered carbonID=\(registration.identifier) keyCode=\(shortcut.keyCode) modifiers=\(modifiers)",
                tags: [:], metadata: [:], error: nil))
        } else {
            let failure = OriginalShortcutMonitorError.hotKey(registration.status)
            emit(OriginalShortcutDiagnostic(level: .error, topic: nil, message: failure.description,
                tags: [:], metadata: ["status": Int(registration.status), "carbon_key_code": Int(shortcut.keyCode),
                                     "carbon_modifiers": Int(modifiers)], error: failure))
        }
        return registration.status
    }

    public func f_1001eae90(shortcut: KeyboardShortcut) {
        f_1001eae90(shortcut: OriginalShortcutValue(keyCode: Int(shortcut.keyCode),
            internalModifiers: shortcut.modifierRawValue))
    }

    public func f_1001eae90(shortcut: OriginalShortcutValue) {
        lock.lock()
        let removed = f_1001eb160(shortcut)
        lock.unlock()
        if let removed {
            let modifiers = OriginalShortcutFunctions.f_1001e7d58(modifierRawValue: shortcut.internalModifiers)
            emit(OriginalShortcutDiagnostic(level: .information, topic: "shortcuts",
                message: "unregistered carbonID=\(removed.identifier) keyCode=\(shortcut.keyCode) modifiers=\(modifiers)",
                tags: [:], metadata: [:], error: nil))
            withExtendedLifetime(removed) {}
        }
    }

    private func f_1001eb160(_ shortcut: OriginalShortcutValue) -> OriginalShortcutRegistration? {
        registrations.removeValue(forKey: shortcut)
    }

    private func f_1001eb1e4(_ registration: OriginalShortcutRegistration, for shortcut: OriginalShortcutValue) {
        registrations[shortcut] = registration
    }

    public func f_1001ea338(_ event: EventRef) {
        guard GetEventClass(event) == OSType(kEventClassKeyboard) else { return }
        var identifier = EventHotKeyID()
        // The original ignores GetEventParameter's status and compares only ID,
        // retaining the zero-initialized value when the parameter cannot be read.
        _ = GetEventParameter(event, EventParamName(kEventParamDirectObject), EventParamType(typeEventHotKeyID),
                              nil, MemoryLayout<EventHotKeyID>.size, nil, &identifier)
        lock.lock()
        let action = registrations.values.first { $0.identifier == identifier.id }?.action
        lock.unlock()
        guard let action else {
            emit(OriginalShortcutDiagnostic(level: .warning, topic: nil,
                message: "Global shortcut event received with no matching handler",
                tags: ["source": "GlobalShortcutMonitor"], metadata: ["carbon_id": Int(identifier.id)], error: nil))
            return
        }
        emit(OriginalShortcutDiagnostic(level: .information, topic: "shortcuts",
            message: "fired carbonID=\(identifier.id)", tags: [:], metadata: [:], error: nil))
        DispatchQueue.main.async(execute: action)
    }

    public static func f_1001ea96c(_ call: EventHandlerCallRef?, _ event: EventRef?,
                                  _ context: UnsafeMutableRawPointer?) -> OSStatus {
        if let event, let context {
            let monitor = Unmanaged<OriginalGlobalShortcutMonitor>.fromOpaque(context).retain().takeRetainedValue()
            monitor.f_1001ea338(event)
            withExtendedLifetime(monitor) {}
        }
        return noErr
    }

    private func f_1001ea9b0() {
        if let handler { RemoveEventHandler(handler) }
        handler = nil
    }

    deinit { f_1001ea9b0() }
}
