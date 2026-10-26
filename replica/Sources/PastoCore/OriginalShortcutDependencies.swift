import AppKit

public final class OriginalShortcutValidatorService: Sendable {
    private init() {}

    public static func f_1001e75e4() -> OriginalShortcutValidatorService {
        OriginalShortcutValidatorService()
    }

    @MainActor
    public func validate(_ shortcut: OriginalShortcutValue) -> Error? {
        guard let message = OriginalShortcutValidation.f_1001ebce4(shortcut: shortcut, menu: NSApp.mainMenu)
        else { return nil }
        return OriginalShortcutRecorderError(message)
    }
}

public extension OriginalDependencyValues {
    static func f_1001e7580<Value>(line: UInt, factory: () -> Value) -> Value {
        OriginalDependencies.f_1000d80e0(file: "PasteShortcut/DI+PasteShortcut.swift", line: line, column: 19,
                                         factory: factory)
    }

    func f_1001e7514() -> OriginalGlobalShortcutMonitor {
        Self.f_1001e7580(line: 6, factory: OriginalGlobalShortcutMonitor.f_1001e752c)
    }

    var shortcutDiagnostic: (OriginalShortcutDiagnostic) -> Void {
        OriginalShortcutTelemetry.f_10019b694().localDiagnostic
    }

    var shortcutValidator: OriginalShortcutValidatorService {
        f_1001f1e64()
    }

    func f_1001f1e64() -> OriginalShortcutValidatorService {
        Self.f_1001e7580(line: 12) {
            OriginalShortcutValidatorService.f_1001e75e4()
        }
    }
}
