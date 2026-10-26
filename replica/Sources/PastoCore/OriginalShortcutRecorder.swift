import AppKit
import Combine
import Foundation

public enum OriginalShortcutRecorderState: Equatable, Hashable, Sendable {
    case assigned(OriginalShortcutValue)
    case recording(previous: OriginalShortcutValue?, candidate: OriginalShortcutValue?)
    case unassigned

    public static func f_1001f1ab4(_ lhs: Self, _ rhs: Self) -> Bool {
        switch (lhs, rhs) {
        case let (.assigned(a), .assigned(b)): return a == b
        case let (.recording(a, b), .recording(c, d)): return a == c && b == d
        case (.unassigned, .unassigned): return true
        default: return false
        }
    }

    public static func == (lhs: Self, rhs: Self) -> Bool { f_1001f1ab4(lhs, rhs) }

    public func f_1001f0558(into hasher: inout Hasher) {
        switch self {
        case let .assigned(shortcut):
            hasher.combine(1)
            hasher.combine(shortcut.keyCode)
            hasher.combine(shortcut.internalModifiers)
        case let .recording(previous, candidate):
            hasher.combine(2)
            Self.hashOptional(previous, into: &hasher)
            Self.hashOptional(candidate, into: &hasher)
        case .unassigned:
            hasher.combine(0)
        }
    }

    private static func hashOptional(_ shortcut: OriginalShortcutValue?, into hasher: inout Hasher) {
        guard let shortcut else { hasher.combine(0); return }
        hasher.combine(1)
        hasher.combine(shortcut.keyCode)
        hasher.combine(shortcut.internalModifiers)
    }

    public func hash(into hasher: inout Hasher) { f_1001f0558(into: &hasher) }

    public var previousShortcut: OriginalShortcutValue? {
        switch self {
        case let .assigned(value): return value
        case let .recording(previous, _): return previous
        case .unassigned: return nil
        }
    }

    public var isRecording: Bool {
        if case .recording = self { return true }
        return false
    }
}

public struct OriginalShortcutRecorderError: LocalizedError {
    public let message: String
    public var errorDescription: String? { message }
    public init(_ message: String) { self.message = message }
}

public enum OriginalShortcutRecorderValidationError: LocalizedError, Hashable, Sendable {
    case optionKey

    public var errorDescription: String? { f_1001f12cc() }

    public func f_1001f12cc() -> String {
        OriginalShortcutMessages.value("shortcut-recorder.error.option-key")
    }
}

/// The original recorder's model owns its event monitor and preserves the
/// previous value separately from the unfinished modifier/key candidate.
@MainActor
public final class OriginalShortcutRecorder: ObservableObject {
    @Published public private(set) var state: OriginalShortcutRecorderState
    @Published public private(set) var validationError: Error?
    public var onDetect: (OriginalShortcutValue?) -> Void
    private var eventMonitor: Any?
    private let validator: OriginalDependency<OriginalShortcutValidatorService>

    public init(shortcut: OriginalShortcutValue?, onDetect: @escaping (OriginalShortcutValue?) -> Void) {
        validationError = nil
        self.validator = OriginalDependency(\OriginalDependencyValues.shortcutValidator)
        eventMonitor = nil
        state = shortcut.map(OriginalShortcutRecorderState.assigned) ?? .unassigned
        self.onDetect = onDetect
    }

    deinit {
        // Swift 5 deinitializers are not guaranteed to execute on the UI actor.
        // Retain only the monitor handle when scheduling its final removal.
        if let eventMonitor {
            if Thread.isMainThread {
                MainActor.assumeIsolated { NSEvent.removeMonitor(eventMonitor) }
            } else {
                Task { @MainActor in NSEvent.removeMonitor(eventMonitor) }
            }
        }
    }

    public func f_1001f0460() -> OriginalShortcutRecorderState { state }
    public func f_1001f04e8() -> Error? { validationError }

    public func f_1001ee478() { validationError = nil }

    public func f_1001ee19c(_ shortcut: OriginalShortcutValue?) {
        state = shortcut.map(OriginalShortcutRecorderState.assigned) ?? .unassigned
    }

    /// Optional state is the original method's "keep current state" sentinel.
    public func f_1001f1150(newState: OriginalShortcutRecorderState?) {
        if let newState { state = newState }
        if let eventMonitor {
            NSEvent.removeMonitor(eventMonitor)
            self.eventMonitor = nil
        }
    }

    public func f_1001eff84() {
        if case let .recording(previous, _) = state {
            f_1001f1150(newState: previous.map(OriginalShortcutRecorderState.assigned) ?? .unassigned)
            return
        }
        state = .recording(previous: state.previousShortcut, candidate: nil)
        if let eventMonitor { NSEvent.removeMonitor(eventMonitor) }
        eventMonitor = NSEvent.addLocalMonitorForEvents(matching: [.keyDown, .flagsChanged]) { [weak self] event in
            guard let self else { return nil }
            return self.f_1001f132c(event)
        }
    }

    /// Action closure forwarded by the original recorder button.
    public func f_1001ef2bc() { f_1001eff84() }

    public func f_1001ef434() {
        onDetect(nil)
        f_1001f1150(newState: .unassigned)
    }

    /// Return the original event only on the two explicit pass-through paths.
    public func f_1001f132c(_ event: NSEvent) -> NSEvent? {
        let eventShortcut = OriginalShortcutFunctions.f_1001e7d18(event)
        let shortcut = OriginalShortcutValue(keyCode: Int(eventShortcut.keyCode),
                                              internalModifiers: eventShortcut.modifierRawValue)
        if [OriginalShortcutFunctions.f_1001e9610(), OriginalShortcutFunctions.f_1001e9624()]
            .contains(shortcut.keyCode), shortcut.internalModifiers == 0 {
            f_1001ef434()
            return nil
        }
        if shortcut.keyCode == OriginalShortcutFunctions.f_1001e95fc(), shortcut.internalModifiers == 0 {
            f_1001eff84()
            return nil
        }
        let closeKey = OriginalShortcutFunctions.f_1001e94d4("w")
        let quitKey = OriginalShortcutFunctions.f_1001e94d4("q")
        if shortcut.internalModifiers == NSEvent.ModifierFlags.command.rawValue,
           [Int(closeKey), Int(quitKey)].contains(shortcut.keyCode) {
            f_1001f1150(newState: .unassigned)
            return event
        }
        let key = OriginalShortcutFunctions.f_1001e7e50(keyCode: shortcut.keyCode)
        if key.isEmpty {
            state = .recording(previous: state.previousShortcut, candidate: shortcut)
            return nil
        }
        _ = validator.f_1000da768()
        guard OriginalShortcutFunctions.f_1001ebc2c(keyCode: shortcut.keyCode,
                                                  modifierRawValue: shortcut.internalModifiers) else {
            NSSound.beep()
            return event
        }
        let validate = validator.f_1000da768()
        if let failure = validate.validate(shortcut) {
            f_1001eff84()
            validationError = failure
            return nil
        }
        onDetect(shortcut)
        f_1001f1150(newState: .assigned(shortcut))
        if OriginalShortcutValidation.requiresOptionCompatibilityWarning(
            modifierRawValue: shortcut.internalModifiers,
            version: ProcessInfo.processInfo.operatingSystemVersion) {
            validationError = OriginalShortcutRecorderValidationError.optionKey
        }
        return nil
    }

    /// (modifier/status text, optional key text, whether key styling is active).
    public func f_1001f02d8() -> (String, String?, Bool) {
        let shortcut: OriginalShortcutValue
        switch state {
        case let .assigned(value): shortcut = value
        case let .recording(_, candidate):
            guard let candidate else {
                return (OriginalShortcutMessages.value("shortcut-recorder.status.recording"), nil, false)
            }
            let modifiers = OriginalShortcutFunctions.f_1001e9774(verbose: false,
                                                                 modifierRawValue: candidate.internalModifiers)
            let key = OriginalShortcutFunctions.f_1001e7e50(keyCode: candidate.keyCode)
            guard !(modifiers + key).isEmpty else {
                return (OriginalShortcutMessages.value("shortcut-recorder.status.recording"), nil, false)
            }
            shortcut = candidate
        case .unassigned:
            return (OriginalShortcutMessages.value("shortcut-recorder.none"), nil, false)
        }
        return (OriginalShortcutFunctions.f_1001e9774(verbose: false, modifierRawValue: shortcut.internalModifiers),
                OriginalShortcutFunctions.f_1001e7e50(keyCode: shortcut.keyCode), true)
    }

    public static var removeTitle: String { OriginalShortcutMessages.value("shortcut-recorder.action.remove") }

}
